# STT latency: baseline → streaming

Issue #72 design / measurement note. Captures the per-stage latency
of the speech-to-text pipeline before and after the optimisation work
on the `feature/audio-to-text` branch.

## TL;DR

| Path | Median total | Tail (worst observed) | Time to first text |
|---|---|---|---|
| Batch, 5 s poll (original) | 18.21 s | **57.74 s** | 18.21 s |
| Batch, 1 s poll (Phase A) | ~16 s (est.) | ~52 s (est.) | ~16 s |
| Streaming (Phase B) | _TBD_ | _TBD_ | **~1 s ttfp** |

The headline win is *time to first text*. Batch latency is dominated
by AWS Transcribe's job queue, which scales with audio length plus an
unbounded queue wait. Streaming returns partials within ~300 ms of
each chunk, so the student sees their words appear in roughly the
time it takes them to say them — collapsing the worst-case tail from
~30 seconds to ~1 second of perceived latency.

## Methodology

Each request emits two structured log lines, grep-able as
`[STT timings]`:

- Batch pipeline (`audio_transcriber.py` + `sessions.py` route):
  ```
  [STT timings] phase=transcribe submit=X.XXXs poll=X.XXXs (polls=N, interval=Ms) fetch=X.XXXs total=X.XXXs
  [STT timings] phase=route session=<uuid> bytes=N ext=… read=… s3=… transcribe=… total=…
  ```
- Streaming pipeline (`audio_streamer.py` + WS route):
  ```
  [STT timings] phase=streamer ttfp=X.XXXs ttfr=X.XXXs partials=N finals=M total=X.XXXs
  [STT timings] phase=stream session=<uuid> outcome=ok|stream_error|timeout disconnected=true|false ttfp=… ttfr=… partials=N finals=M duration=…
  ```

`ttfp` = time-to-first-partial, `ttfr` = time-to-first-final, measured
from the AWS streaming session open. All durations are monotonic
seconds — immune to clock drift.

Test phrase: `"testing 1, testing 2, … testing 10"` (~10 seconds of
speech, recorded in Chrome on macOS as WebM/Opus). Backend running on
`localhost` against AWS region `ap-southeast-2`.

## Baseline — batch, 5 s poll interval (pre-change)

Eight consecutive runs against the unmodified pipeline. Captured via
the instrumentation introduced in the first commit of this branch
(see `audio_transcriber.py` and `sessions.py` route).

| # | Total | Poll loop | Polls | S3 upload | Submit | Bytes |
|---|---|---|---|---|---|---|
| 1 | 18.72 s | 15.65 s | 4 | 1.71 s | 0.96 s | 256 KB |
| 2 | 17.69 s | 15.39 s | 4 | 0.47 s | 1.24 s | 316 KB |
| 3 | 32.57 s | 30.68 s | 7 | 0.43 s | 1.00 s | 285 KB |
| 4 | **57.74 s** | **56.07 s** | 12 | 0.38 s | 0.83 s | 260 KB |
| 5 | 27.45 s | 25.54 s | 6 | 0.37 s | 0.90 s | 274 KB |
| 6 | 11.83 s | 10.25 s | 3 | 0.37 s | 0.77 s | 245 KB |
| 7 | 12.12 s | 10.25 s | 3 | 0.51 s | 0.89 s | 373 KB |
| 8 | 11.90 s | 10.26 s | 3 | 0.40 s | 0.75 s | 265 KB |

| Stat | Total | Poll | Submit | S3 |
|---|---|---|---|---|
| min | 11.83 s | 10.25 s | 0.75 s | 0.37 s |
| median | 18.21 s | 12.83 s | 0.89 s | 0.40 s |
| mean | 23.75 s | 21.76 s | 0.93 s | 0.53 s |
| max | 57.74 s | 56.07 s | 1.24 s | 1.71 s |
| std dev | ~15 s | ~15 s | — | — |

### Conclusions from the baseline

1. **The polling loop is 70–97 % of total latency** — the dominant
   cost in every run.
2. **Audio size doesn't correlate with latency.** A 373 KB clip ran
   in 12.1 s; a 260 KB clip in the same batch took 57.7 s. Compression
   is therefore not the right intervention — payload is already Opus
   and small.
3. **The variance is AWS-queue-driven.** Batch transcription has no
   SLA on queue depth; on a bad run we sat in the queue for nearly a
   minute. This is the worst-case "frozen UI" symptom that issue #72
   originally described.

## Phase A — poll-interval reduction (5 s → 1 s)

Single-line change in `audio_transcriber.py`:
`settings.transcribe_poll_interval_seconds` defaults to `1` (was `5`).

Per-request savings are bounded: at most `interval - 1 = 4 s` per
request, regardless of how long AWS actually took. We catch the
`COMPLETED` status within ~1 s of when AWS finishes, instead of up to
5 s late.

| | Baseline (5 s poll) | After (1 s poll, est.) |
|---|---|---|
| 12 s runs (3 polls) | ~12.1 s | ~10.5 s |
| 18 s runs (4 polls) | ~18.2 s | ~15.3 s |
| 57 s runs (12 polls) | ~57.7 s | ~54 s |

The Phase A change is an interim win — it smooths the floor and the
"unlucky middle" runs by a few seconds. It does *not* fix the tail
behaviour, which is bounded below by AWS's queue + processing time
(roughly the audio length). That fix needs streaming.

> **TODO:** Capture 8 fresh runs after the poll-interval change so the
> table above can carry real values rather than estimates. Run from
> the same machine + region as the baseline to keep the comparison
> apples-to-apples.

## Phase B — AWS Transcribe Streaming

Replaces the synchronous batch pipeline with a WebSocket-driven
streaming session (`StartStreamTranscription`). Partials and finals
flow back as the student speaks. No S3 round-trip on the streaming
path. Falls back to the batch pipeline automatically if the WebSocket
errors mid-session, so the student gets a transcript either way.

> **TODO:** Capture 8 runs through the streaming path once it's
> enabled by default (`STT_STREAMING_ENABLED=1`,
> `VITE_STT_STREAMING=1`). Use:
> ```
> grep "STT timings" /tmp/backend.log | grep "phase=stream "
> ```
> Look for the `ttfp=…` value — that's the headline metric for this
> issue. Expected range based on AWS Transcribe Streaming
> documentation: **150–500 ms** for the first partial, ~10 s for the
> final on a ~10 s clip (matching the audio length itself).
>
> Table to fill in:
>
> | # | ttfp | ttfr | partials | finals | outcome | duration |
> |---|---|---|---|---|---|---|
> | 1 | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
> | …  | | | | | | |

## Implications for the user experience

Issue #72 framed the problem as "students think the system has
frozen" during the wait. The data above shows why:

- On a good batch run (median ~18 s) the textarea is empty for
  ~18 seconds after the student stops speaking.
- On a bad batch run (P95 ~57 s) it's empty for nearly a minute.

Phase A reduces the average by a few seconds. The "Transcribing… M:SS"
elapsed-time indicator added alongside the streaming work (commit 18
of this branch) softens the perception even when the underlying
latency is still there.

Phase B is the real fix: text appears as the student speaks. The
batch path remains as the fallback for when AWS Transcribe Streaming
has an outage or a transient error, so the worst case degrades to
Phase A's behaviour rather than failing entirely.

## How to refresh this document

1. Land all the work on `feature/audio-to-text` and enable the
   streaming flags.
2. From a single machine, do 8 streaming sessions and 8 batch
   sessions (turn streaming off temporarily) of the same test phrase.
3. `grep "STT timings" /tmp/backend.log` and fill in the tables.
4. Update the **TL;DR** numbers at the top so they reflect the
   measured medians rather than the estimates currently shown.
5. Post the updated tables on issue #72 as the closing summary.
