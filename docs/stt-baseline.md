# STT latency: baseline → streaming

Issue #72 design / measurement note. Captures the per-stage latency
of the speech-to-text pipeline before and after the optimisation work
on the `feature/audio-to-text` branch.

## TL;DR

| Path                                                   | Median total | Tail (worst observed) | Time to first text |
| ------------------------------------------------------ | ------------ | --------------------- | ------------------ |
| Batch, 5 s poll (original baseline, ~10 s clips)       | 18.21 s      | **57.74 s**           | 18.21 s            |
| Batch, 1 s poll (re-measured 2026-05-17, ~8.4 s clips) | 7.79 s       | 8.13 s                | 7.79 s             |
| Streaming (re-measured 2026-05-17, ~8.4 s clips)       | 8.73 s ttfr  | 9.29 s ttfr           | **1.85 s ttfp**    |

The headline win is _time to first text_. Batch latency is dominated
by AWS Transcribe's job queue, which scales with audio length plus an
unbounded queue wait. Streaming returns partials within ~2 s of the
session opening (~1.85 s median ttfp on the 2026-05-17 re-measurement),
so the student sees their words appear roughly in real time as they
speak rather than after a multi-second wait.

The original 5 s-poll row stands as the historical baseline; the
1 s-poll and Streaming rows are the matched-pair re-measurement
described under [Re-measurement — 2026-05-17](#re-measurement--2026-05-17).
Three caveats on direct comparison: (1) the new clips are slightly
shorter (~8.4 s vs the baseline's ~10 s); (2) AWS-side queue depth
varies hour-to-hour, so the absence of a 50 s+ tail in 14 trials does
not mean the original tail is gone; (3) the 1 s poll row is now
measured rather than estimated, and the gap from the historical 18.21 s
median reflects both the poll-interval change and AWS-side speedup
between the two runs.

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

| #   | Total       | Poll loop   | Polls | S3 upload | Submit | Bytes  |
| --- | ----------- | ----------- | ----- | --------- | ------ | ------ |
| 1   | 18.72 s     | 15.65 s     | 4     | 1.71 s    | 0.96 s | 256 KB |
| 2   | 17.69 s     | 15.39 s     | 4     | 0.47 s    | 1.24 s | 316 KB |
| 3   | 32.57 s     | 30.68 s     | 7     | 0.43 s    | 1.00 s | 285 KB |
| 4   | **57.74 s** | **56.07 s** | 12    | 0.38 s    | 0.83 s | 260 KB |
| 5   | 27.45 s     | 25.54 s     | 6     | 0.37 s    | 0.90 s | 274 KB |
| 6   | 11.83 s     | 10.25 s     | 3     | 0.37 s    | 0.77 s | 245 KB |
| 7   | 12.12 s     | 10.25 s     | 3     | 0.51 s    | 0.89 s | 373 KB |
| 8   | 11.90 s     | 10.26 s     | 3     | 0.40 s    | 0.75 s | 265 KB |

| Stat    | Total   | Poll    | Submit | S3     |
| ------- | ------- | ------- | ------ | ------ |
| min     | 11.83 s | 10.25 s | 0.75 s | 0.37 s |
| median  | 18.21 s | 12.83 s | 0.89 s | 0.40 s |
| mean    | 23.75 s | 21.76 s | 0.93 s | 0.53 s |
| max     | 57.74 s | 56.07 s | 1.24 s | 1.71 s |
| std dev | ~15 s   | ~15 s   | —      | —      |

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

|                      | Baseline (5 s poll) | After (1 s poll, est.) |
| -------------------- | ------------------- | ---------------------- |
| 12 s runs (3 polls)  | ~12.1 s             | ~10.5 s                |
| 18 s runs (4 polls)  | ~18.2 s             | ~15.3 s                |
| 57 s runs (12 polls) | ~57.7 s             | ~54 s                  |

The Phase A change is an interim win — it smooths the floor and the
"unlucky middle" runs by a few seconds. It does _not_ fix the tail
behaviour, which is bounded below by AWS's queue + processing time
(roughly the audio length). That fix needs streaming.

The Phase A row in the TL;DR was replaced with measured numbers on
2026-05-17; see [Re-measurement — 2026-05-17](#re-measurement--2026-05-17).

## Phase B — AWS Transcribe Streaming

Replaces the synchronous batch pipeline with a WebSocket-driven
streaming session (`StartStreamTranscription`). Partials and finals
flow back as the student speaks. No S3 round-trip on the streaming
path. Falls back to the batch pipeline automatically if the WebSocket
errors mid-session, so the student gets a transcript either way.

Real numbers captured 2026-05-17 — see
[Re-measurement — 2026-05-17](#re-measurement--2026-05-17) below.

## Re-measurement — 2026-05-17

The TL;DR Phase A and Phase B rows are populated from a single
matched-pair run on 2026-05-17 against 8 fresh recordings of the same
test phrase, with both paths exercised on the identical inputs.

### Methodology notes

- **Fresh recordings.** The 8 baseline `.webm` files from the original
  run were not preserved, so 8 new recordings of `"testing 1, testing
2, … testing 10"` were captured in m4a/AAC (Windows Voice Recorder
  on the same machine as the rest of this project). Distinct takes,
  median audio length 8.4 s (range 8.06–8.96 s), slightly shorter than
  the original baseline's ~10 s.
- **ffmpeg decode.** AWS Transcribe Streaming wants raw 16 kHz mono
  signed 16-bit LE PCM (see `audio_streamer.py:160`). The m4a files
  are decoded once to PCM at start-up via `ffmpeg -f s16le -ac 1 -ar
16000`. Treated as a documented format conversion, not a change to
  the audio content — AWS still receives the same speech. The batch
  path uses the m4a directly via S3.
- **Real-time pacing on the streaming path.** Each ~100 ms PCM frame
  (3,200 bytes) is held until its scheduled wall-clock tick on a
  monotonic deadline, so the harness sends one frame every 100 ms of
  real time rather than bursting the whole clip. This matches the
  rate at which the production frontend's AudioWorklet emits frames.
- **Production streamer used.** The harness imports
  `app.utils.audio_streamer.TranscribeStreamer` and reads
  `time_to_first_partial` / `time_to_first_final` from its instance
  properties, so the measured `ttfp` is exactly the value the
  production `[STT timings] phase=streamer` log line reports.
- **1 s poll for batch.** Matches the current production default
  (`settings.transcribe_poll_interval_seconds = 1`).
- **Trial count.** 1 trial per recording per path = 8 matched
  datapoints per path (matching the original baseline shape). Plus
  3 extra trials on each of the first 2 recordings per path = 6
  spread trials per path. 28 AWS Transcribe sessions total.
- **AWS region:** `ap-southeast-2`. Backend on `localhost`. AWS
  credentials sourced from the `uoa-sso` profile via `aws configure
export-credentials`.
- **Harness lives at** `tests/fixtures/stt/run_bench.py`. Raw per-trial
  output in `tests/fixtures/stt/bench_results.json`. The 8 `.m4a`
  recordings used as inputs are not tracked in the repo (binary blobs
  containing the author's voice); available on request from the
  author if you need to reproduce the matched-pair run.

### Streaming — measured

Per-trial `ttfp` (seconds since the streaming session opened), all
14 trials:

| Recording         | Audio (s) | trial 1 | trial 2 | trial 3 | trial 4 |
| ----------------- | --------- | ------- | ------- | ------- | ------- |
| Recording (2).m4a | 8.49      | 2.041   | 2.050   | 2.046   | 2.073   |
| Recording (3).m4a | 8.06      | 1.849   | 1.874   | 1.856   | 1.864   |
| Recording (4).m4a | 8.38      | 1.837   | –       | –       | –       |
| Recording (5).m4a | 8.62      | 1.836   | –       | –       | –       |
| Recording (6).m4a | 8.96      | 1.904   | –       | –       | –       |
| Recording (7).m4a | 8.32      | 1.787   | –       | –       | –       |
| Recording (8).m4a | 8.41      | 1.847   | –       | –       | –       |
| Recording.m4a     | 8.30      | 2.062   | –       | –       | –       |

| Stat   | ttfp matched (n=8) | ttfp spread (n=6) | ttfp all (n=14) | ttfr matched (n=8) |
| ------ | ------------------ | ----------------- | --------------- | ------------------ |
| min    | 1.787 s            | 1.856 s           | 1.787 s         | 8.319 s            |
| median | 1.848 s            | 1.960 s           | 1.869 s         | 8.733 s            |
| mean   | 1.895 s            | 1.960 s           | 1.923 s         | 8.764 s            |
| max    | 2.062 s            | 2.073 s           | 2.073 s         | 9.293 s            |

Within-recording variance is very small (Recording (2) ttfp std-dev
across 4 trials ≈ 0.015 s; Recording (3) ≈ 0.011 s), so the
cross-recording spread (~1.79–2.07 s) is dominated by per-clip
characteristics (silence at the start, vocal energy) rather than
network jitter.

### Batch — measured

Per-trial total wall time (submit + poll + fetch), all 14 trials:

| Recording         | trial 1 | trial 2 | trial 3 | trial 4 |
| ----------------- | ------- | ------- | ------- | ------- |
| Recording (2).m4a | 7.526 s | 8.057 s | 8.063 s | 7.228 s |
| Recording (3).m4a | 8.130 s | 8.112 s | 8.073 s | 9.179 s |
| Recording (4).m4a | 7.038 s | –       | –       | –       |
| Recording (5).m4a | 7.099 s | –       | –       | –       |
| Recording (6).m4a | 8.053 s | –       | –       | –       |
| Recording (7).m4a | 6.961 s | –       | –       | –       |
| Recording (8).m4a | 8.119 s | –       | –       | –       |
| Recording.m4a     | 8.089 s | –       | –       | –       |

| Stat   | matched (n=8) | spread (n=6) | all (n=14) |
| ------ | ------------- | ------------ | ---------- |
| min    | 6.961 s       | 7.228 s      | 6.961 s    |
| median | 7.790 s       | 8.068 s      | 8.060 s    |
| mean   | 7.627 s       | 8.119 s      | 7.838 s    |
| max    | 8.130 s       | 9.179 s      | 9.179 s    |

Batch totals are dramatically lower than the original 5 s-poll
baseline (median 18.21 s, tail 57.74 s). Two factors:

1. **Poll interval dropped from 5 s to 1 s.** The doc's earlier
   estimate for Phase A was median ~16 s, which the re-measurement
   now bounds at 7.79 s median. The estimate was conservative.
2. **AWS-side queue capacity appears materially better than at the
   original baseline date.** Even subtracting the maximum poll-interval
   saving (~4 s per request) from the historical 18.21 s does not
   reach 7.79 s; the remaining gap is AWS-side processing speedup
   between the two run dates. The original baseline doc explicitly
   notes "the variance is AWS-queue-driven."

The matched-pair conclusion still holds: on the **same 8 clips, same
day, same machine**, streaming time-to-first-text is **1.85 s
median** vs batch end-to-end **7.79 s median** — a ~4× reduction in
how long the student stares at an empty textarea, with the streaming
path also delivering visible partials throughout rather than a
single final at the end.

### Notes on the tail

This re-measurement saw no batch run longer than 9.18 s in 14 trials.
The original baseline's 57.74 s tail (and the doc's prior
"unbounded queue wait" framing) is not refuted by 14 lucky-day
trials — it is a low-probability event tied to AWS Transcribe queue
depth, which the doc itself flagged as out of our control. The
streaming path remains the architectural fix for that tail because
it bypasses the batch queue entirely.

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
