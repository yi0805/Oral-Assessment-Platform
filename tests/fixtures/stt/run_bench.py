"""
STT latency benchmark harness — issue #72 follow-up.

Measures both the streaming (ttfp) and batch (end-to-end total) AWS
Transcribe paths against the 8 fresh recordings of
"testing 1, testing 2, ... testing 10" sitting next to this script.

Methodology:
  * 1 trial per recording per path = 8 matched datapoints (baseline parity).
  * 3 extra trials on each of recordings 1 and 2 per path = 6 spread trials.
  * Streaming uses 16 kHz mono LE16 PCM (ffmpeg decode of the .m4a clips).
  * Streaming pacing is real-time: one ~100 ms PCM frame every ~100 ms of
    wall clock, on a monotonic deadline so jitter doesn't accumulate.
  * Streaming wrapper is imported from production (app.utils.audio_streamer)
    so the ttfp metric matches what the production WebSocket route logs.
  * Batch path mirrors app.utils.audio_transcriber: start_job, poll at 1 s,
    fetch transcript JSON, with the same submit/poll/fetch decomposition.
  * No .env files are read; AWS profile and region are passed in directly.

Cost: 28 AWS Transcribe jobs (14 streaming + 14 batch), ~10 s of audio
each. Total audio time ~5 min streaming + ~5 min batch ≈ USD 0.20.
"""
from __future__ import annotations

import asyncio
import json
import os
import statistics
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import boto3
import httpx
import imageio_ffmpeg
from botocore.exceptions import BotoCoreError, ClientError

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.utils.audio_streamer import TranscribeStreamer, TranscribeStreamError  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

AWS_PROFILE = "uoa-sso"
AWS_REGION = "ap-southeast-2"
S3_BUCKET = "team8-project20-materials"
SAMPLE_RATE_HZ = 16000
FRAME_MS = 100
FRAME_BYTES = SAMPLE_RATE_HZ * 2 * FRAME_MS // 1000  # 16-bit mono LE @ 100ms
POLL_INTERVAL_S = 1.0  # matches settings.transcribe_poll_interval_seconds default
BATCH_MAX_WAIT_S = 60 * 5

S3_KEY_PREFIX = "stt-bench"

FIXTURES_DIR = Path(__file__).resolve().parent
RECORDINGS = sorted(p for p in FIXTURES_DIR.glob("*.m4a") if p.is_file())

# Spread trials: extra trials on first 2 recordings, per path.
SPREAD_RECORDING_INDEXES = [0, 1]
SPREAD_TRIALS_PER_RECORDING = 3

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def _bootstrap_aws_env_credentials() -> str:
    """Export short-lived static credentials from the SSO profile into
    env vars before any boto3 / amazon-transcribe call.

    botocore's SSO refresh path doesn't work reliably from a script — the
    AWS CLI does. So we shell out to ``aws configure export-credentials``
    once at start-up, set the three env vars, and the rest of the run
    uses the env-var credential chain (which both boto3 and the
    amazon-transcribe CRT resolver read natively).
    """
    out = subprocess.run(
        ["aws", "configure", "export-credentials",
         "--profile", AWS_PROFILE, "--format", "process"],
        capture_output=True, text=True, check=True,
    ).stdout
    creds = json.loads(out)
    os.environ["AWS_ACCESS_KEY_ID"] = creds["AccessKeyId"]
    os.environ["AWS_SECRET_ACCESS_KEY"] = creds["SecretAccessKey"]
    os.environ["AWS_SESSION_TOKEN"] = creds["SessionToken"]
    os.environ.pop("AWS_PROFILE", None)
    return creds.get("Expiration", "unknown")


# ---------------------------------------------------------------------------
# Result records
# ---------------------------------------------------------------------------

@dataclass
class StreamingTrial:
    recording: str
    trial: int
    ttfp: Optional[float]
    ttfr: Optional[float]
    partials: int
    finals: int
    duration: float
    transcript: str
    error: Optional[str] = None


@dataclass
class BatchTrial:
    recording: str
    trial: int
    submit: float
    poll: float
    poll_count: int
    fetch: float
    total: float
    transcript: str
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Decode helper
# ---------------------------------------------------------------------------

def decode_to_pcm(path: Path) -> bytes:
    """Decode an m4a (or any ffmpeg-supported) file to raw 16 kHz mono LE16 PCM."""
    cmd = [
        FFMPEG,
        "-loglevel", "error",
        "-i", str(path),
        "-f", "s16le",
        "-acodec", "pcm_s16le",
        "-ac", "1",
        "-ar", str(SAMPLE_RATE_HZ),
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, check=True)
    return proc.stdout


def audio_duration_seconds(pcm: bytes) -> float:
    return len(pcm) / (SAMPLE_RATE_HZ * 2)  # 2 bytes per sample, mono


# ---------------------------------------------------------------------------
# Streaming trial
# ---------------------------------------------------------------------------

async def run_streaming_trial(
    recording_label: str,
    trial: int,
    pcm: bytes,
) -> StreamingTrial:
    """Stream one recording's PCM through TranscribeStreamer at real time."""
    transcript_parts: list[str] = []
    error: Optional[str] = None
    streamer: Optional[TranscribeStreamer] = None

    try:
        async with TranscribeStreamer(
            region=AWS_REGION,
            sample_rate_hz=SAMPLE_RATE_HZ,
        ) as s:
            streamer = s

            async def feed() -> None:
                # Real-time pacing on a monotonic deadline. The first frame
                # goes immediately; each subsequent frame is held until its
                # scheduled tick so jitter in send_pcm does not accumulate.
                t0 = time.monotonic()
                idx = 0
                while idx * FRAME_BYTES < len(pcm):
                    chunk = pcm[idx * FRAME_BYTES:(idx + 1) * FRAME_BYTES]
                    target = t0 + idx * (FRAME_MS / 1000)
                    delay = target - time.monotonic()
                    if delay > 0:
                        await asyncio.sleep(delay)
                    await s.send_pcm(chunk)
                    idx += 1
                await s.end_input()

            async def drain() -> None:
                async for r in s.results():
                    if not r.is_partial:
                        transcript_parts.append(r.text)

            await asyncio.gather(feed(), drain())

        ttfp = streamer.time_to_first_partial
        ttfr = streamer.time_to_first_final
        partials = streamer.partial_count
        finals = streamer.final_count

    except TranscribeStreamError as exc:
        error = f"TranscribeStreamError: {exc}"
        ttfp = ttfr = None
        partials = finals = 0

    duration = (streamer._stats.get("first_final_at") or 0.0) if streamer else 0.0
    transcript = " ".join(transcript_parts).strip()

    return StreamingTrial(
        recording=recording_label,
        trial=trial,
        ttfp=ttfp,
        ttfr=ttfr,
        partials=partials,
        finals=finals,
        duration=duration,
        transcript=transcript,
        error=error,
    )


# ---------------------------------------------------------------------------
# Batch trial
# ---------------------------------------------------------------------------

def run_batch_trial(
    recording_label: str,
    trial: int,
    file_path: Path,
    s3,
    transcribe,
) -> BatchTrial:
    """Upload .m4a to S3, run a batch transcription job, capture timings."""
    s3_key = f"{S3_KEY_PREFIX}/{uuid.uuid4().hex}.m4a"
    job_name = f"stt-bench-{uuid.uuid4().hex}"

    submit = poll = fetch = 0.0
    poll_count = 0
    transcript = ""
    error: Optional[str] = None

    try:
        # Upload (cost not part of baseline's "total" — the baseline only
        # measured the AWS-side submit+poll+fetch, see audio_transcriber.py
        # comment block).
        with open(file_path, "rb") as fp:
            s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=fp.read())

        media_uri = f"s3://{S3_BUCKET}/{s3_key}"

        # Submit
        t = time.monotonic()
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            LanguageCode="en-US",
            MediaFormat="m4a",
            Media={"MediaFileUri": media_uri},
        )
        submit = time.monotonic() - t

        # Poll
        t_poll_start = time.monotonic()
        deadline = t_poll_start + BATCH_MAX_WAIT_S
        transcript_uri: Optional[str] = None
        while True:
            resp = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            poll_count += 1
            job = resp["TranscriptionJob"]
            status = job["TranscriptionJobStatus"]
            if status == "COMPLETED":
                transcript_uri = job["Transcript"]["TranscriptFileUri"]
                break
            if status == "FAILED":
                raise RuntimeError(
                    f"Transcription job failed: {job.get('FailureReason', 'unknown')}"
                )
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    f"Transcription did not complete within {BATCH_MAX_WAIT_S}s"
                )
            time.sleep(POLL_INTERVAL_S)
        poll = time.monotonic() - t_poll_start

        # Fetch transcript JSON
        t = time.monotonic()
        with httpx.Client(timeout=60.0) as http:
            r = http.get(transcript_uri)
            r.raise_for_status()
            payload = r.json()
        fetch = time.monotonic() - t

        transcripts = payload["results"]["transcripts"]
        transcript = " ".join(t.get("transcript", "") for t in transcripts).strip()

    except (BotoCoreError, ClientError, httpx.HTTPError, RuntimeError) as exc:
        error = f"{type(exc).__name__}: {exc}"

    finally:
        # Clean up Transcribe job and S3 object
        try:
            transcribe.delete_transcription_job(TranscriptionJobName=job_name)
        except (BotoCoreError, ClientError):
            pass
        try:
            s3.delete_object(Bucket=S3_BUCKET, Key=s3_key)
        except (BotoCoreError, ClientError):
            pass

    total = submit + poll + fetch
    return BatchTrial(
        recording=recording_label,
        trial=trial,
        submit=submit,
        poll=poll,
        poll_count=poll_count,
        fetch=fetch,
        total=total,
        transcript=transcript,
        error=error,
    )


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------

def fmt_stats(values: list[float]) -> str:
    if not values:
        return "no data"
    return (
        f"n={len(values)}  "
        f"median={statistics.median(values):.3f}s  "
        f"mean={statistics.mean(values):.3f}s  "
        f"min={min(values):.3f}s  "
        f"max={max(values):.3f}s"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> int:
    print(f"Repo root: {REPO_ROOT}")
    print(f"ffmpeg:    {FFMPEG}")
    print(f"AWS:       profile={AWS_PROFILE} region={AWS_REGION} bucket={S3_BUCKET}")
    print(f"Recordings ({len(RECORDINGS)}):")
    for i, p in enumerate(RECORDINGS, 1):
        print(f"  [{i}] {p.name}  ({p.stat().st_size:,} bytes)")
    print()
    if len(RECORDINGS) != 8:
        print(f"WARNING: expected 8 recordings, found {len(RECORDINGS)}")

    # Decode all upfront so the streaming trial loop doesn't pay decode cost
    print("Decoding to PCM 16 kHz mono LE16 ...")
    pcm_by_recording: dict[str, bytes] = {}
    for p in RECORDINGS:
        pcm = decode_to_pcm(p)
        pcm_by_recording[p.name] = pcm
        print(f"  {p.name}: {len(pcm):,} bytes "
              f"({audio_duration_seconds(pcm):.2f}s audio)")
    print()

    expires_at = _bootstrap_aws_env_credentials()
    print(f"AWS env-var credentials exported (expire {expires_at})")

    session = boto3.Session(region_name=AWS_REGION)
    s3 = session.client("s3")
    transcribe = session.client("transcribe")

    # ---- Trial schedule ----
    # Matched: one trial per recording per path.
    # Spread: extra trials per path on the recordings at SPREAD_RECORDING_INDEXES.
    schedule: list[tuple[str, int, Path]] = []
    for rec in RECORDINGS:
        schedule.append((rec.name, 1, rec))
    for idx in SPREAD_RECORDING_INDEXES:
        rec = RECORDINGS[idx]
        for trial in range(2, 2 + SPREAD_TRIALS_PER_RECORDING):
            schedule.append((rec.name, trial, rec))

    print(f"Trial schedule: {len(schedule)} trials per path "
          f"({len(RECORDINGS)} matched + "
          f"{len(SPREAD_RECORDING_INDEXES) * SPREAD_TRIALS_PER_RECORDING} spread)")
    print()

    # ---- Streaming pass ----
    print("=" * 72)
    print("STREAMING PASS")
    print("=" * 72)
    streaming_results: list[StreamingTrial] = []
    for label, trial, path in schedule:
        print(f"[stream] {label} trial={trial} ...", end=" ", flush=True)
        r = await run_streaming_trial(label, trial, pcm_by_recording[label])
        streaming_results.append(r)
        if r.error:
            print(f"ERROR {r.error}")
        else:
            print(
                f"ttfp={r.ttfp:.3f}s "
                f"ttfr={(r.ttfr if r.ttfr is not None else float('nan')):.3f}s "
                f"partials={r.partials} finals={r.finals} "
                f"transcript={r.transcript[:60]!r}"
            )

    print()
    print("=" * 72)
    print("BATCH PASS")
    print("=" * 72)
    batch_results: list[BatchTrial] = []
    for label, trial, path in schedule:
        print(f"[batch ] {label} trial={trial} ...", end=" ", flush=True)
        r = run_batch_trial(label, trial, path, s3, transcribe)
        batch_results.append(r)
        if r.error:
            print(f"ERROR {r.error}")
        else:
            print(
                f"total={r.total:.3f}s "
                f"submit={r.submit:.3f}s "
                f"poll={r.poll:.3f}s (polls={r.poll_count}) "
                f"fetch={r.fetch:.3f}s "
                f"transcript={r.transcript[:60]!r}"
            )

    # ---- Summary ----
    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)

    matched_stream = [r for r in streaming_results if r.trial == 1 and r.ttfp is not None]
    matched_batch = [r for r in batch_results if r.trial == 1 and r.error is None]
    spread_stream = [r for r in streaming_results if r.trial > 1 and r.ttfp is not None]
    spread_batch = [r for r in batch_results if r.trial > 1 and r.error is None]

    print("\nStreaming ttfp (matched, 1 trial per recording):")
    print(f"  {fmt_stats([r.ttfp for r in matched_stream])}")
    print("Streaming ttfp (spread, extra trials on first 2 recordings):")
    print(f"  {fmt_stats([r.ttfp for r in spread_stream])}")
    print("Streaming ttfp (all trials):")
    print(f"  {fmt_stats([r.ttfp for r in streaming_results if r.ttfp is not None])}")

    print("\nBatch total (matched, 1 trial per recording):")
    print(f"  {fmt_stats([r.total for r in matched_batch])}")
    print("Batch total (spread, extra trials on first 2 recordings):")
    print(f"  {fmt_stats([r.total for r in spread_batch])}")
    print("Batch total (all trials):")
    print(f"  {fmt_stats([r.total for r in batch_results if r.error is None])}")

    # Dump JSON for the doc update
    out = {
        "run_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "region": AWS_REGION,
        "sample_rate_hz": SAMPLE_RATE_HZ,
        "frame_ms": FRAME_MS,
        "poll_interval_s": POLL_INTERVAL_S,
        "recordings": [p.name for p in RECORDINGS],
        "streaming": [r.__dict__ for r in streaming_results],
        "batch": [r.__dict__ for r in batch_results],
    }
    out_path = FIXTURES_DIR / "bench_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
