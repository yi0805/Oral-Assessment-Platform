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

Implementation notes
~~~~~~~~~~~~~~~~~~~~
The :mod:`amazon_transcribe` SDK is callback-driven — you subclass
``TranscriptResultStreamHandler`` and override
``handle_transcript_event``. To present a Pythonic async iterator
instead, this module bridges those callbacks into an
``asyncio.Queue``: a small internal handler pushes
:class:`StreamResult` objects onto the queue, and :meth:`results`
yields them out. The handler runs on its own task spawned in
:meth:`__aenter__` and torn down in :meth:`__aexit__`.

AWS credentials come from the standard botocore credential chain
(env vars, ``~/.aws/credentials``, instance profile, etc.). For local
SSO development with a named profile, set ``AWS_PROFILE`` in your
shell before starting uvicorn — the streaming SDK does *not* read
``settings.aws_profile_name`` directly the way the batch path does.

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

import asyncio
import logging
import time
from dataclasses import dataclass
from types import TracebackType
from typing import Any, AsyncIterator, Optional, Type

from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent

logger = logging.getLogger(__name__)

# Internal sentinel pushed onto the result queue by the handler task
# when the AWS output stream closes. ``results()`` uses it to know when
# to terminate cleanly.
_END_OF_RESULTS: Any = object()

# AWS Transcribe Streaming expects raw signed 16-bit little-endian PCM.
# 16 kHz mono is the recommended rate for English speech models and
# matches what the client-side AudioWorklet (added in the frontend
# commits of issue #72) downsamples to before sending.
DEFAULT_SAMPLE_RATE_HZ = 16000


def fmt_optional_seconds(t: Optional[float]) -> str:
    """Format an Optional[float] of seconds for the [STT timings] line.

    None → "-" so the streaming log line stays single-token-per-field
    and grep-able. Concrete values get the same 3-decimal "X.XXXs"
    format the rest of the issue #72 instrumentation uses.

    Exported (rather than the conventional ``_``-prefixed private name)
    because the WebSocket route in ``app.api.routes.sessions`` imports
    it to format ttfp/ttfr in its own log line.
    """
    return f"{t:.3f}s" if t is not None else "-"


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


class _ResultPump(TranscriptResultStreamHandler):
    """
    Internal bridge between the SDK's callback-driven handler and an
    :class:`asyncio.Queue`.

    The SDK calls :meth:`handle_transcript_event` for every transcript
    event delivered over the bidirectional stream. We translate each
    event into one or more :class:`StreamResult` objects and push them
    onto a queue that :meth:`TranscribeStreamer.results` drains.
    """

    def __init__(
        self,
        transcript_result_stream: Any,
        queue: "asyncio.Queue[Any]",
        t_start: float,
        stats: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(transcript_result_stream)
        self._queue = queue
        self._t_start = t_start
        # Shared mutable dict owned by the TranscribeStreamer — see the
        # _stats initialiser there for the schema. Pump increments
        # counters and records the first-result timestamps as events
        # arrive; the streamer / route read them at __aexit__ time.
        self._stats = stats

    async def handle_transcript_event(
        self,
        transcript_event: TranscriptEvent,
    ) -> None:
        for result in transcript_event.transcript.results:
            text = ""
            if result.alternatives:
                # AWS sorts alternatives by descending confidence — the
                # first one is the most likely transcription.
                text = result.alternatives[0].transcript or ""

            is_partial = bool(result.is_partial)
            elapsed = time.monotonic() - self._t_start

            # [STT Instrumentation - issue #72] Record stats so the
            # route can log time-to-first-partial / time-to-first-final
            # alongside outcome + duration in one structured line.
            if self._stats is not None:
                if is_partial:
                    self._stats["partial_count"] += 1
                    if self._stats["first_partial_at"] is None:
                        self._stats["first_partial_at"] = elapsed
                else:
                    self._stats["final_count"] += 1
                    if self._stats["first_final_at"] is None:
                        self._stats["first_final_at"] = elapsed

            await self._queue.put(
                StreamResult(
                    text=text,
                    is_partial=is_partial,
                    timestamp=elapsed,
                )
            )


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

    Internally a background task drives the SDK's event loop and
    pushes :class:`StreamResult` objects onto an :class:`asyncio.Queue`
    that :meth:`results` drains. If the background task fails, the
    exception is re-raised the next time :meth:`results` is awaited
    so the caller doesn't have to plumb error handling separately.
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
        # AWS streaming state — populated in __aenter__.
        self._client: Optional[TranscribeStreamingClient] = None
        self._stream: Any = None
        self._queue: Optional["asyncio.Queue[Any]"] = None
        self._handler_task: Optional[asyncio.Task[None]] = None
        # If the handler task fails, the exception is stored here and
        # re-raised by results() once the queue drains. Keeping it on
        # the instance (rather than enqueuing it directly) makes
        # results() easier to reason about — it sees a single sentinel
        # value rather than two distinct ones.
        self._handler_error: Optional[BaseException] = None
        self._t_start: Optional[float] = None
        self._opened = False
        self._input_ended = False
        # [STT Instrumentation - issue #72] Stats are mutated by the
        # _ResultPump as transcript events arrive and read by the
        # route (and by __aexit__ for the phase=streamer log line).
        # Stored as a plain dict rather than separate fields so we can
        # share the same object reference with the pump without a
        # back-pointer or weakref.
        self._stats: dict[str, Any] = {
            "first_partial_at": None,  # seconds since open, or None
            "first_final_at": None,    # seconds since open, or None
            "partial_count": 0,
            "final_count": 0,
        }

    async def __aenter__(self) -> "TranscribeStreamer":
        """
        Open the AWS Transcribe streaming session and prepare the
        bidirectional channel.

        Raises :class:`TranscribeStreamError` if the connection cannot
        be established (auth failure, network error, etc.).
        """
        try:
            self._client = TranscribeStreamingClient(region=self._region)
            self._stream = await self._client.start_stream_transcription(
                language_code=self._language_code,
                media_sample_rate_hz=self._sample_rate_hz,
                media_encoding="pcm",
            )
        except Exception as exc:  # noqa: BLE001 — wrap any SDK error
            logger.exception(
                "[TranscribeStream] start_stream_transcription failed"
            )
            raise TranscribeStreamError(
                f"Could not open AWS Transcribe stream: {exc}"
            ) from exc

        self._t_start = time.monotonic()
        self._queue = asyncio.Queue()
        pump = _ResultPump(
            self._stream.output_stream,
            self._queue,
            self._t_start,
            stats=self._stats,
        )
        self._handler_task = asyncio.create_task(self._run_handler(pump))
        self._opened = True
        logger.info(
            "[TranscribeStream] opened region=%s lang=%s rate=%dHz",
            self._region,
            self._language_code,
            self._sample_rate_hz,
        )
        return self

    async def _run_handler(self, pump: _ResultPump) -> None:
        """
        Drive the SDK's event loop on a background task. Pushes
        :data:`_END_OF_RESULTS` onto the queue when AWS closes the
        output stream so :meth:`results` knows to stop iterating.

        Cancellation propagates so :meth:`__aexit__` can tear the task
        down quickly if the route hits an error mid-stream.
        """
        try:
            await pump.handle_events()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 — surface via results()
            self._handler_error = exc
            logger.exception("[TranscribeStream] handler task failed")
        finally:
            # Always signal results() to terminate, even on cancellation.
            # Default asyncio.Queue is unbounded, so put_nowait can't
            # block or raise QueueFull in practice.
            assert self._queue is not None
            try:
                self._queue.put_nowait(_END_OF_RESULTS)
            except asyncio.QueueFull:  # pragma: no cover
                pass

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
        # Best-effort end_stream so AWS can flush remaining results.
        if (
            self._opened
            and self._stream is not None
            and not self._input_ended
        ):
            try:
                await self._stream.input_stream.end_stream()
            except Exception:  # noqa: BLE001
                logger.warning(
                    "[TranscribeStream] failed to end input on exit",
                    exc_info=True,
                )
            finally:
                self._input_ended = True

        # Cancel the handler task if it's still running. handle_events()
        # naturally returns once AWS closes the output stream after
        # end_stream(), so on the happy path the cancel is a no-op.
        if self._handler_task is not None and not self._handler_task.done():
            self._handler_task.cancel()
            try:
                await self._handler_task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass

        self._opened = False

        # [STT Instrumentation - issue #72] One grep-able timing line
        # per streamer lifecycle. Companion to the route's
        # ``phase=stream`` line — same pattern as audio_transcriber.py
        # emitting ``phase=transcribe`` alongside the route's
        # ``phase=route``. ``ttfp`` and ``ttfr`` are "-" when no result
        # of that kind arrived during the session (e.g. AWS closed
        # before any speech was recognised).
        if self._t_start is not None:
            total = time.monotonic() - self._t_start
            logger.info(
                "[STT timings] phase=streamer ttfp=%s ttfr=%s "
                "partials=%d finals=%d total=%.3fs",
                fmt_optional_seconds(self._stats["first_partial_at"]),
                fmt_optional_seconds(self._stats["first_final_at"]),
                self._stats["partial_count"],
                self._stats["final_count"],
                total,
            )
        else:
            logger.info("[TranscribeStream] closed (never opened)")

    # ------------------------------------------------------------------
    # Public stats accessors — read-only views over the shared dict that
    # the result pump mutates. Used by the WebSocket route to extend
    # its ``phase=stream`` log line with ttfp / partials / finals.
    # ------------------------------------------------------------------

    @property
    def time_to_first_partial(self) -> Optional[float]:
        """Monotonic seconds from open to the first ``is_partial=True``
        result, or ``None`` if none ever arrived."""
        return self._stats["first_partial_at"]

    @property
    def time_to_first_final(self) -> Optional[float]:
        """Monotonic seconds from open to the first ``is_partial=False``
        result, or ``None`` if none ever arrived."""
        return self._stats["first_final_at"]

    @property
    def partial_count(self) -> int:
        """Total number of ``is_partial=True`` results received."""
        return self._stats["partial_count"]

    @property
    def final_count(self) -> int:
        """Total number of ``is_partial=False`` results received."""
        return self._stats["final_count"]

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
        if not self._opened or self._stream is None:
            raise TranscribeStreamError(
                "send_pcm called on a closed streamer"
            )
        if self._input_ended:
            raise TranscribeStreamError(
                "send_pcm called after end_input()"
            )
        try:
            await self._stream.input_stream.send_audio_event(
                audio_chunk=frame
            )
        except Exception as exc:  # noqa: BLE001
            raise TranscribeStreamError(f"send_pcm failed: {exc}") from exc

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
        if (
            not self._opened
            or self._stream is None
            or self._input_ended
        ):
            return
        try:
            await self._stream.input_stream.end_stream()
        finally:
            self._input_ended = True

    async def results(self) -> AsyncIterator[StreamResult]:
        """
        Async generator yielding :class:`StreamResult` chunks as AWS
        produces them.

        The iterator terminates once :meth:`end_input` has been called
        *and* AWS has flushed all remaining results. Iterate it from a
        task separate from the one driving :meth:`send_pcm`::

            async for result in streamer.results():
                ...

        Multiple results with ``is_partial=True`` may cover the same
        span of audio — the most recent one supersedes earlier ones.
        Once a span is finalised AWS sends a single ``is_partial=False``
        result for it.

        Raises :class:`TranscribeStreamError` if the background handler
        task crashed (e.g. AWS dropped the connection mid-stream).
        """
        if self._queue is None:
            raise TranscribeStreamError(
                "results() called before __aenter__"
            )

        while True:
            item = await self._queue.get()
            if item is _END_OF_RESULTS:
                if self._handler_error is not None:
                    raise TranscribeStreamError(
                        f"AWS streaming handler failed: {self._handler_error}"
                    ) from self._handler_error
                return
            yield item
