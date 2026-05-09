"""
Audio streaming wrapper for AWS Transcribe Streaming.

Issue #72 — companion to ``audio_transcriber.py`` (batch). This module
exposes a small async API around AWS Transcribe Streaming
(``StartStreamTranscription``) so the upcoming WebSocket route
``/sessions/{id}/transcribe/stream`` can:

  * forward 16 kHz mono LE PCM frames from the browser to AWS as the
    student speaks, and
  * stream partial + final transcripts back to the browser within
    ~300 ms of the audio arriving.

This file is the **public API surface only** — every method raises
``NotImplementedError``. The AWS integration (``amazon-transcribe``
SDK calls, the result-handler wiring, error mapping) lands in the
next commit. Splitting the change in two keeps each PR small enough
to review and lets us land the WebSocket route against this contract
without waiting for the AWS code to be finished.

Intended call shape::

    async with TranscribeStreamer(region=settings.aws_region) as s:
        async def feed():
            async for frame in pcm_frames_from_websocket():
                await s.send_pcm(frame)
            await s.end_input()

        async def drain():
            async for result in s.results():
                await websocket.send_json({
                    "type": "partial" if result.is_partial else "final",
                    "text": result.text,
                })

        await asyncio.gather(feed(), drain())

The split between ``send_pcm`` (producer) and ``results`` (consumer)
mirrors AWS Transcribe Streaming's bidirectional model so a route
handler can run them as two concurrent tasks.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from types import TracebackType
from typing import AsyncIterator, Optional, Type

logger = logging.getLogger(__name__)

# AWS Transcribe Streaming expects raw signed 16-bit little-endian PCM.
# 16 kHz mono is the recommended rate for English speech models and
# matches what the client-side AudioWorklet (added in the frontend
# commits of issue #72) downsamples to before sending.
DEFAULT_SAMPLE_RATE_HZ = 16000


class TranscribeStreamError(RuntimeError):
    """
    Raised by :class:`TranscribeStreamer` when the underlying AWS
    streaming session fails in an unrecoverable way (connection error,
    auth failure, malformed audio, etc.).

    Recoverable conditions (transient network blips, rate-limit
    backoff) are handled internally where possible and never surface
    as ``TranscribeStreamError``.
    """


@dataclass(frozen=True)
class StreamResult:
    """
    A single result chunk yielded by :meth:`TranscribeStreamer.results`.

    Attributes:
        text: The transcribed text for this chunk.
        is_partial: ``True`` while AWS may still revise this text as
            more audio arrives. ``False`` once the chunk has been
            finalised and won't change. The caller typically renders
            partials in italic/grey and replaces them with the final
            text when ``is_partial`` flips to ``False``.
        timestamp: Monotonic seconds since the streamer was opened.
            Useful for time-to-first-partial measurements without
            having to coordinate clocks with AWS.
    """

    text: str
    is_partial: bool
    timestamp: float


class TranscribeStreamer:
    """
    Async wrapper around AWS Transcribe Streaming.

    Construct with the AWS region and (optionally) a non-default
    language code or sample rate, then use as an async context
    manager. Inside the ``async with`` block:

      * call :meth:`send_pcm` to forward audio frames;
      * iterate :meth:`results` to receive transcripts;
      * call :meth:`end_input` once the recording stops to flush the
        final results.

    The streamer can be driven from two concurrent ``asyncio`` tasks
    (one feeding audio in, one consuming results out) — the AWS SDK's
    bidirectional model supports this naturally.

    *Skeleton only* — every method raises :class:`NotImplementedError`
    until the AWS integration commit lands. Constructing the object
    and entering/exiting the context manager fail loudly so callers
    written against this contract can be type-checked but not yet run.
    """

    def __init__(
        self,
        *,
        region: str,
        language_code: str = "en-US",
        sample_rate_hz: int = DEFAULT_SAMPLE_RATE_HZ,
    ) -> None:
        """
        Capture configuration. No network calls happen here — the AWS
        connection is opened in :meth:`__aenter__`.

        Args:
            region: AWS region for the Transcribe endpoint
                (e.g. ``"ap-southeast-2"``). Use the same region as
                ``settings.aws_region`` to keep latency low.
            language_code: BCP-47 language tag understood by AWS
                Transcribe (default ``"en-US"``).
            sample_rate_hz: PCM sample rate of the frames you'll feed
                via :meth:`send_pcm`. Must match the actual rate the
                client encodes at; otherwise transcripts are garbled.
        """
        self._region = region
        self._language_code = language_code
        self._sample_rate_hz = sample_rate_hz
        # The actual AWS streaming objects (client, session handle,
        # result-handler task) are populated in __aenter__ once the
        # implementation commit lands.
        self._opened = False

    async def __aenter__(self) -> "TranscribeStreamer":
        """
        Open the AWS Transcribe streaming session and prepare the
        bidirectional channel.

        Raises :class:`TranscribeStreamError` if the connection cannot
        be established (auth failure, network error, etc.).
        """
        raise NotImplementedError(
            "TranscribeStreamer.__aenter__ is wired up in the next commit "
            "(issue #72)."
        )

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """
        Close the AWS streaming session and release resources. Called
        automatically when leaving the ``async with`` block. Idempotent
        — safe to call after :meth:`end_input` or after an error.
        """
        raise NotImplementedError(
            "TranscribeStreamer.__aexit__ is wired up in the next commit "
            "(issue #72)."
        )

    async def send_pcm(self, frame: bytes) -> None:
        """
        Forward one PCM frame to AWS.

        ``frame`` must be raw signed 16-bit little-endian samples at
        the configured ``sample_rate_hz``. Frames of arbitrary length
        are accepted; ~100 ms of audio per call (≈3200 bytes at
        16 kHz mono) is a good target — small enough for low latency,
        large enough to keep per-call overhead negligible.

        Raises :class:`TranscribeStreamError` if the streamer is
        closed or AWS rejects the frame.
        """
        raise NotImplementedError(
            "TranscribeStreamer.send_pcm is wired up in the next commit "
            "(issue #72)."
        )

    async def end_input(self) -> None:
        """
        Signal that no more frames will be sent.

        After this call AWS emits any remaining final results and then
        closes the result stream, causing :meth:`results` to terminate.
        Call this once the user stops recording, before awaiting the
        last results.

        Idempotent. Safe to call from a different task than
        :meth:`send_pcm`.
        """
        raise NotImplementedError(
            "TranscribeStreamer.end_input is wired up in the next commit "
            "(issue #72)."
        )

    def results(self) -> AsyncIterator[StreamResult]:
        """
        Return an async iterator over :class:`StreamResult` chunks as
        AWS produces them.

        The iterator terminates once :meth:`end_input` has been called
        *and* AWS has flushed all remaining results. Iterate it from a
        task separate from the one driving :meth:`send_pcm`::

            async for result in streamer.results():
                ...

        Multiple results with ``is_partial=True`` may cover the same
        span of audio — the most recent one supersedes earlier ones.
        Once a span is finalised AWS sends a single ``is_partial=False``
        result for it.
        """
        raise NotImplementedError(
            "TranscribeStreamer.results is wired up in the next commit "
            "(issue #72)."
        )
