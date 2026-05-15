"""
Audio transcription utility using AWS Transcribe.

Starts a transcription job against an audio file already stored in S3
(the same bucket used by the materials pipeline), polls until the job
finishes, then downloads and parses the JSON transcript.

Poll-interval rationale (issue #72)
-----------------------------------
This module uses AWS Transcribe's *batch* API: submit a job, then call
``GetTranscriptionJob`` repeatedly until ``COMPLETED``. Total latency
is therefore ``submit_time + N * poll_interval + fetch_time`` where N
depends on how long AWS takes — a value we cannot observe except by
polling for it.

Per-stage instrumentation across 8 sample recordings (~10s of speech,
"testing 1 … testing 10", WebM/Opus, ap-southeast-2) showed the poll
loop dominated end-to-end latency:

    metric              | value
    --------------------|----------------
    median total        | 18.21s
    poll-loop median    | 12.83s  (70%+ of total in every run)
    poll-loop range     | 10.25s – 56.07s
    polls per run       | 3 – 12
    s3 upload median    | 0.40s
    submit-job median   | 0.89s
    transcript fetch    | 0.22s

Audio size did *not* correlate with latency (a 373 KB clip ran in
12.1s while a 260 KB clip in the same batch took 57.7s), confirming
the variance comes from AWS-side queue/processing time rather than
anything we control client-side.

Because AWS Transcribe regularly finishes between two of our sleep
ticks, an interval of ``T`` seconds wastes up to ``T - 1`` seconds of
pure idle wait per request. The original interval was 5s, costing as
much as ~4s on every short clip. Dropping the default to 1s narrows
that worst-case waste to ~1s while only marginally increasing API
call volume (``GetTranscriptionJob`` is rate-limited generously and
costs nothing meaningful).

The interval is exposed as ``settings.transcribe_poll_interval_seconds``
(env var ``TRANSCRIBE_POLL_INTERVAL_SECONDS``) so different
deployments / regions can override the default without a code change.

This is an interim optimisation. The longer-term fix tracked under
issue #72 is to switch the student answer path to AWS Transcribe
*Streaming* (``StartStreamTranscription``), which removes the batch
queue entirely and returns partial results within ~300ms. The work
here only smooths out the worst case of the existing batch pipeline.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from uuid import uuid4

import boto3
import httpx
from botocore.exceptions import BotoCoreError, ClientError, ProfileNotFound

from app.core.config import settings

logger = logging.getLogger(__name__)

# AWS Transcribe supported media formats
# https://docs.aws.amazon.com/transcribe/latest/dg/how-input.html
SUPPORTED_AUDIO_EXTENSIONS = {"amr", "flac", "m4a", "mp3", "mp4", "ogg", "wav", "webm"}

# Poll tuning.
# The interval is read from settings.transcribe_poll_interval_seconds so
# different deployments / regions can tune without a code change. See
# issue #72 for the measurements that motivate the 1s default — the
# original 5s value left the loop idling for up to 4s on answers AWS
# had already finished.
_MAX_WAIT_SECONDS = 60 * 30  # 30 minutes upper bound


@dataclass
class TranscribeResult:
    text: str
    job_name: str
    language_code: str


def is_audio_extension(extension: str) -> bool:

    return extension.lower() in SUPPORTED_AUDIO_EXTENSIONS


def _get_transcribe_client():

    try:
        session = boto3.Session(
            profile_name=settings.aws_profile_name,
            region_name=settings.aws_region,
        )
        return session.client("transcribe")

    except ProfileNotFound as exc:
        raise RuntimeError(
            f"AWS profile '{settings.aws_profile_name}' was not found. "
            "Run aws configure sso or set AWS_PROFILE_NAME in .env correctly."
        ) from exc


def transcribe_audio_from_s3(
    storage_key: str,
    extension: str,
    *,
    language_code: str = "en-US",
) -> TranscribeResult:
    """
    Run AWS Transcribe on an audio file stored at s3://<s3_bucket_name>/<storage_key>.

    Returns the plain-text transcript. Raises RuntimeError on failure.
    """
    ext = extension.lower()

    if not is_audio_extension(ext):
        raise RuntimeError(f"Unsupported audio format for transcription: {ext}")

    if not settings.s3_bucket_name:
        raise RuntimeError("S3_BUCKET_NAME is required for audio transcription")

    client = _get_transcribe_client()

    job_name = f"material-transcribe-{uuid4().hex}"
    media_uri = f"s3://{settings.s3_bucket_name}/{storage_key}"

    logger.info("[Transcribe] Starting job %s for %s", job_name, media_uri)

    # [STT Instrumentation - issue #72]
    # Track three sub-phases of the AWS-side work so the issue thread can
    # see exactly where the time is going: (a) the StartTranscriptionJob
    # API call itself, (b) job queue+processing time as observed by our
    # poll loop, (c) transcript JSON fetch from the presigned URL.
    _t_submit_start = time.monotonic()

    try:
        client.start_transcription_job(
            TranscriptionJobName=job_name,
            LanguageCode=language_code,
            MediaFormat=ext,
            Media={"MediaFileUri": media_uri},
        )

    except (BotoCoreError, ClientError) as exc:
        logger.exception("[Transcribe] Failed to start job for %s", storage_key)
        raise RuntimeError(f"Could not start transcription job: {exc}") from exc

    _t_submit_end = time.monotonic()
    _submit_seconds = _t_submit_end - _t_submit_start

    # Poll for completion
    deadline = time.monotonic() + _MAX_WAIT_SECONDS
    transcript_uri: str | None = None
    _poll_count = 0

    try:
        while True:
            try:
                response = client.get_transcription_job(TranscriptionJobName=job_name)

            except (BotoCoreError, ClientError) as exc:
                raise RuntimeError(f"Could not poll transcription job: {exc}") from exc

            _poll_count += 1
            job = response["TranscriptionJob"]
            status = job["TranscriptionJobStatus"]

            if status == "COMPLETED":
                transcript_uri = job["Transcript"]["TranscriptFileUri"]
                break

            if status == "FAILED":
                reason = job.get("FailureReason", "unknown")
                raise RuntimeError(f"Transcription job failed: {reason}")

            if time.monotonic() >= deadline:
                raise RuntimeError(
                    f"Transcription job did not complete within {_MAX_WAIT_SECONDS} seconds"
                )

            time.sleep(settings.transcribe_poll_interval_seconds)

        _t_poll_end = time.monotonic()
        _poll_seconds = _t_poll_end - _t_submit_end

        # Fetch and parse the transcript JSON (AWS-hosted presigned URL)
        _t_fetch_start = time.monotonic()
        try:
            with httpx.Client(timeout=60.0) as http:
                resp = http.get(transcript_uri)
                resp.raise_for_status()
                payload = resp.json()

        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Could not fetch transcript JSON: {exc}") from exc

        _fetch_seconds = time.monotonic() - _t_fetch_start

        try:
            transcripts = payload["results"]["transcripts"]
            text = " ".join(t.get("transcript", "") for t in transcripts).strip()

        except (KeyError, TypeError) as exc:
            raise RuntimeError(f"Unexpected transcript JSON shape: {exc}") from exc

        if not text:
            raise RuntimeError("Transcription returned empty text")

        logger.info(
            "[Transcribe] Job %s completed (%d chars, lang=%s)",
            job_name, len(text), language_code,
        )
        # [STT Instrumentation - issue #72] Single grep-able line.
        logger.info(
            "[STT timings] phase=transcribe submit=%.3fs poll=%.3fs (polls=%d, interval=%ds) fetch=%.3fs total=%.3fs",
            _submit_seconds,
            _poll_seconds,
            _poll_count,
            settings.transcribe_poll_interval_seconds,
            _fetch_seconds,
            _submit_seconds + _poll_seconds + _fetch_seconds,
        )

        return TranscribeResult(text=text, job_name=job_name, language_code=language_code)

    finally:
        # Always attempt to delete the Transcribe job, including on poll timeout
        # or polling exception, so jobs never accumulate in the AWS account.
        try:
            client.delete_transcription_job(TranscriptionJobName=job_name)

        except (BotoCoreError, ClientError):
            logger.warning("[Transcribe] Could not delete job %s (non-fatal)", job_name)
