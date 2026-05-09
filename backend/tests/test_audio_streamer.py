"""
Unit tests for the streaming wrapper in ``backend/app/utils/audio_streamer.py``.

These tests focus on the contract of :class:`TranscribeStreamer` and
its private bridge :class:`_ResultPump`. The ``amazon-transcribe`` SDK
is mocked at the module-import level so the tests don't hit AWS.

Two pieces are exercised in isolation:

  * ``_ResultPump.handle_transcript_event`` — translation of an
    SDK-shaped ``TranscriptEvent`` into one or more :class:`StreamResult`
    objects pushed onto an :class:`asyncio.Queue`.
  * ``TranscribeStreamer`` — open / send / end / drain lifecycle.

Issue #72.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_event(text: str, *, is_partial: bool, alternatives: list[str] | None = None):
    """
    Build a fake ``TranscriptEvent`` shaped like what the SDK delivers.

    The real SDK class has nested ``transcript.results[].alternatives[]``
    attributes; ``SimpleNamespace`` is enough for the wrapper to walk it.
    """
    if alternatives is None:
        alternatives = [text]
    alts = [SimpleNamespace(transcript=t) for t in alternatives]
    result = SimpleNamespace(alternatives=alts, is_partial=is_partial)
    transcript = SimpleNamespace(results=[result])
    return SimpleNamespace(transcript=transcript)


@pytest.fixture
def fake_aws_stream():
    """A fake stream object as returned by ``start_stream_transcription``."""
    input_stream = MagicMock()
    input_stream.send_audio_event = AsyncMock()
    input_stream.end_stream = AsyncMock()
    return SimpleNamespace(
        input_stream=input_stream,
        output_stream=MagicMock(),
    )


@pytest.fixture
def fake_aws_client(fake_aws_stream):
    client = MagicMock()
    client.start_stream_transcription = AsyncMock(return_value=fake_aws_stream)
    return client


@pytest.fixture
def patched_streamer(monkeypatch, fake_aws_client):
    """
    Patch ``TranscribeStreamingClient`` so :meth:`TranscribeStreamer.__aenter__`
    constructs our fake instead of a real AWS client.

    Also patches ``_ResultPump.handle_events`` to a no-op by default so
    tests that don't care about the handler task don't hang. Tests that
    *do* care can re-patch it on a per-test basis.
    """
    from app.utils import audio_streamer

    monkeypatch.setattr(
        audio_streamer,
        "TranscribeStreamingClient",
        MagicMock(return_value=fake_aws_client),
    )

    async def noop_handle_events(self):  # pragma: no cover — overridden in some tests
        return None

    monkeypatch.setattr(
        audio_streamer._ResultPump, "handle_events", noop_handle_events
    )
    return audio_streamer


# ---------------------------------------------------------------------------
# _ResultPump translation
# ---------------------------------------------------------------------------


async def test_result_pump_translates_partial_event():
    from app.utils.audio_streamer import _ResultPump, StreamResult

    queue: asyncio.Queue = asyncio.Queue()
    pump = _ResultPump(MagicMock(), queue, t_start=0.0)

    await pump.handle_transcript_event(_make_event("hello", is_partial=True))

    result = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert isinstance(result, StreamResult)
    assert result.text == "hello"
    assert result.is_partial is True
    assert result.timestamp >= 0


async def test_result_pump_translates_final_event():
    from app.utils.audio_streamer import _ResultPump, StreamResult

    queue: asyncio.Queue = asyncio.Queue()
    pump = _ResultPump(MagicMock(), queue, t_start=0.0)

    await pump.handle_transcript_event(
        _make_event("hello world", is_partial=False)
    )

    result = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert isinstance(result, StreamResult)
    assert result.text == "hello world"
    assert result.is_partial is False


async def test_result_pump_picks_first_alternative():
    """
    AWS sorts alternatives by descending confidence. The wrapper takes
    only the first one.
    """
    from app.utils.audio_streamer import _ResultPump

    queue: asyncio.Queue = asyncio.Queue()
    pump = _ResultPump(MagicMock(), queue, t_start=0.0)

    await pump.handle_transcript_event(
        _make_event(
            "ignored",
            is_partial=False,
            alternatives=["best guess", "second guess", "third guess"],
        )
    )

    result = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert result.text == "best guess"


async def test_result_pump_handles_empty_alternatives():
    """
    Defensive: AWS occasionally emits a result with no alternatives
    (e.g. a heartbeat event). The wrapper should still produce a
    :class:`StreamResult` with an empty string rather than crashing.
    """
    from app.utils.audio_streamer import _ResultPump

    queue: asyncio.Queue = asyncio.Queue()
    pump = _ResultPump(MagicMock(), queue, t_start=0.0)

    empty_result = SimpleNamespace(alternatives=[], is_partial=True)
    transcript = SimpleNamespace(results=[empty_result])
    event = SimpleNamespace(transcript=transcript)

    await pump.handle_transcript_event(event)

    result = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert result.text == ""
    assert result.is_partial is True


# ---------------------------------------------------------------------------
# TranscribeStreamer lifecycle
# ---------------------------------------------------------------------------


async def test_aenter_starts_stream_with_correct_params(
    patched_streamer, fake_aws_client
):
    async with patched_streamer.TranscribeStreamer(
        region="ap-southeast-2",
        language_code="en-NZ",
        sample_rate_hz=16000,
    ):
        pass

    fake_aws_client.start_stream_transcription.assert_awaited_once_with(
        language_code="en-NZ",
        media_sample_rate_hz=16000,
        media_encoding="pcm",
    )


async def test_send_pcm_forwards_frame_to_aws(
    patched_streamer, fake_aws_stream
):
    chunk = b"\x00\x01" * 1600  # 3200 bytes ≈ 100 ms at 16 kHz mono LE16

    async with patched_streamer.TranscribeStreamer(region="us-east-1") as s:
        await s.send_pcm(chunk)

    fake_aws_stream.input_stream.send_audio_event.assert_awaited_once_with(
        audio_chunk=chunk
    )


async def test_end_input_is_idempotent(patched_streamer, fake_aws_stream):
    """
    ``end_input`` should be safe to call multiple times — the second
    call must not raise and must not re-invoke the SDK. The implicit
    ``end_input`` from ``__aexit__`` likewise must not double-call.
    """
    async with patched_streamer.TranscribeStreamer(region="us-east-1") as s:
        await s.end_input()
        await s.end_input()
        await s.end_input()

    # __aexit__ also tries end_input but our flag short-circuits it,
    # so the SDK only sees a single call across the whole lifecycle.
    assert fake_aws_stream.input_stream.end_stream.await_count == 1


# ---------------------------------------------------------------------------
# End-to-end: open, simulate AWS pushing events, drain results
# ---------------------------------------------------------------------------


async def test_full_lifecycle_yields_partial_then_final(
    monkeypatch, patched_streamer
):
    """
    With a fake ``handle_events`` that pushes a partial then a final
    event, ``results()`` should yield two :class:`StreamResult` objects
    in order and then terminate cleanly.
    """
    from app.utils.audio_streamer import _ResultPump, StreamResult

    async def fake_handle_events(self):
        # Simulate AWS delivering a streaming partial as the user is
        # mid-utterance, then the finalised version once they pause.
        await self.handle_transcript_event(
            _make_event("testing one two", is_partial=True)
        )
        await self.handle_transcript_event(
            _make_event("testing one two three", is_partial=False)
        )

    monkeypatch.setattr(_ResultPump, "handle_events", fake_handle_events)

    received: list[StreamResult] = []

    async with patched_streamer.TranscribeStreamer(region="us-east-1") as s:
        await s.send_pcm(b"\x00" * 320)
        await s.end_input()
        async for result in s.results():
            received.append(result)

    assert len(received) == 2

    assert received[0].text == "testing one two"
    assert received[0].is_partial is True

    assert received[1].text == "testing one two three"
    assert received[1].is_partial is False

    # Timestamps are monotonic seconds since the streamer was opened —
    # both must be non-negative and the final must arrive after the
    # partial.
    assert received[0].timestamp >= 0
    assert received[1].timestamp >= received[0].timestamp


async def test_results_terminates_when_no_events_arrive(patched_streamer):
    """
    If AWS closes the output stream without ever delivering an event
    (e.g. a stream that gets cut before any speech is recognised),
    ``results()`` should terminate cleanly without yielding anything.
    """
    received = []

    async with patched_streamer.TranscribeStreamer(region="us-east-1") as s:
        await s.end_input()
        async for result in s.results():
            received.append(result)

    assert received == []
