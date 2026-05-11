import { useCallback, useEffect, useRef, useState } from "react";

import { startAudioRecorder } from "./audioRecorder";
import { useAudioContext } from "./useAudioContext";
import { useStreamingTranscribe } from "./useStreamingTranscribe";
import { useTranscribeAudio } from "./useTranscribeAudio";

// Orchestration hook for the student streaming-transcription flow.
// Combines the two single-responsibility hooks added earlier in
// issue #72:
//
//   * useAudioContext        — produces 16 kHz Int16 LE PCM frames
//                              from the mic via the AudioWorklet.
//   * useStreamingTranscribe — owns the WebSocket to the streaming
//                              backend route and surfaces partial /
//                              final transcripts as React state.
//
// Plus, since commit 20 of issue #72, a parallel MediaRecorder that
// buffers a webm/opus copy of the same audio. If the WebSocket dies
// mid-stream (AWS hiccup, network blip, server flag flip), the
// buffered blob is replayed through the existing useTranscribeAudio
// mutation as a graceful fallback. The student gets a transcript
// either way; they never have to re-record.
//
// Public contract:
//
//   const {
//     status, partial, final, error, isSupported,
//     start, stop, cancel, reset,
//   } = useStudentSpeechStream();
//
//   await start(sessionId);           // opens WS + parallel recorder, then mic
//   // ...PCM frames stream automatically while status === "streaming"
//   const transcript = await stop();  // flushes server, returns final
//
// Status transitions:
//
//   idle ──start()──▶ connecting ──ws open──▶ streaming
//   streaming ──stop()──▶ stopping ──ws close──▶ idle
//   streaming ──ws error──▶ stopping ──batch transcribe──▶ idle  (fallback)
//   (no fallback available) ──error──▶ error
//   error / streaming / stopping ──cancel()──▶ idle  (no flush)
//
// stop() returns a Promise that resolves with the accumulated final
// transcript once the server has flushed and closed (or once the
// fallback has produced a batch transcript). cancel() is the abandon
// path — used when the student navigates away or hits Esc.

// Cap the buffered audio at 25 MB to mirror the upload limit enforced
// by the batch route's transcribe_response_audio handler. In practice
// Opus encoding keeps a 5-minute clip under 1 MB, so this is mostly a
// belt-and-braces guard against a stuck recording.
const FALLBACK_BYTES_LIMIT = 25 * 1024 * 1024;

export function useStudentSpeechStream() {
  // Destructure up-front so callback deps can reference only the
  // stable functions instead of the parent objects (which re-create
  // each render).
  const {
    partial,
    final,
    isStreaming,
    error: wsError,
    connect: connectWs,
    sendPcm,
    sendStop,
    disconnect: disconnectWs,
    reset: resetWs,
  } = useStreamingTranscribe();

  const {
    error: audioError,
    isSupported,
    start: startAudio,
    stop: stopAudio,
  } = useAudioContext({ onPcmFrame: sendPcm });

  const { transcribeAudio } = useTranscribeAudio();

  const [status, setStatus] = useState("idle");

  // Fallback-only state. fallbackFinal holds the transcript produced
  // by the batch path; fallbackPhase tracks whether we're in the
  // middle of running it ("pending"), have finished it successfully
  // ("ok"), or finished it with an error ("failed"). "none" is the
  // happy path where streaming worked end-to-end.
  const [fallbackFinal, setFallbackFinal] = useState("");
  const [fallbackPhase, setFallbackPhase] = useState("none");

  // Pending stop()/cancel() promise resolvers, plus the latest known
  // `final` value snapshotted into a ref so the resolver can read it
  // without going through state (which may be stale by the time the
  // close event lands).
  const stopResolverRef = useRef(null);
  const stopRejecterRef = useRef(null);
  const finalRef = useRef("");

  // Fallback bookkeeping. recorderRef holds the handle returned by
  // startAudioRecorder (the framework-agnostic factory we extracted
  // in commit 12). sessionIdRef captures the id at start() time so
  // the fallback transcribe call can be made from inside the WS-error
  // effect without re-plumbing it. fallbackTriggeredRef prevents
  // re-entry if the effect fires more than once on the same error.
  const recorderRef = useRef(null);
  const sessionIdRef = useRef(null);
  const fallbackTriggeredRef = useRef(false);

  useEffect(() => {
    finalRef.current = final;
  }, [final]);

  // Unified "WS state change" effect. Runs whenever wsError /
  // audioError / isStreaming flips. Priority order:
  //   1. WS error AND a parallel recorder is available → run the
  //      batch fallback. This is the whole point of this commit.
  //   2. Some error AND no fallback available → surface it the same
  //      way the pre-fallback orchestrator did.
  //   3. WS closed cleanly (no error) AND someone is awaiting stop()
  //      → resolve their Promise with the WS final.
  //
  // The single-effect design is deliberate: declaring two effects on
  // the same set of deps invites order-of-execution bugs (the
  // resolver effect would race the error effect and could resolve
  // stop() with an empty string before the fallback got a chance to
  // produce a transcript).
  useEffect(() => {
    // ---------- 1. WS error → fallback ----------
    if (
      wsError &&
      recorderRef.current &&
      sessionIdRef.current &&
      !fallbackTriggeredRef.current
    ) {
      fallbackTriggeredRef.current = true;
      setFallbackPhase("pending");
      setStatus("stopping");
      // Clear the underlying WS-hook error synchronously so the
      // orchestrator's `error` field stops surfacing it on the very
      // next render — keeps the brief "error flashes then recovers"
      // UX from leaking out to the consumer.
      resetWs();

      const recorder = recorderRef.current;
      recorderRef.current = null;
      const sessionId = sessionIdRef.current;

      (async () => {
        try {
          // Stop the mic / WebSocket pipeline; we won't be sending
          // any more PCM frames.
          await stopAudio();

          const blob = await recorder.stop();
          if (!blob || blob.size === 0) {
            throw new Error("Streaming fallback: no audio captured.");
          }
          if (blob.size > FALLBACK_BYTES_LIMIT) {
            throw new Error(
              "Streaming fallback: recording is too long (>25 MB).",
            );
          }

          const transcript = await transcribeAudio({
            sessionId,
            audioBlob: blob,
          });
          const text = typeof transcript === "string" ? transcript : "";

          setFallbackFinal(text);
          finalRef.current = text;
          setFallbackPhase("ok");
          setStatus("idle");

          if (stopResolverRef.current) {
            const resolve = stopResolverRef.current;
            stopResolverRef.current = null;
            stopRejecterRef.current = null;
            resolve(text);
          }
        } catch (fallbackErr) {
          setFallbackPhase("failed");
          setStatus("error");

          if (stopRejecterRef.current) {
            const reject = stopRejecterRef.current;
            stopResolverRef.current = null;
            stopRejecterRef.current = null;
            reject(fallbackErr);
          }
        }
      })();
      return;
    }

    // ---------- 2. Error with no fallback → surface it ----------
    const err = wsError || audioError;
    if (err && !fallbackTriggeredRef.current) {
      setStatus("error");

      if (stopRejecterRef.current) {
        const reject = stopRejecterRef.current;
        stopResolverRef.current = null;
        stopRejecterRef.current = null;
        reject(err);
      }
      return;
    }

    // ---------- 3. Clean close → resolve any pending stop() ----------
    if (!isStreaming && stopResolverRef.current && !fallbackTriggeredRef.current) {
      const resolve = stopResolverRef.current;
      stopResolverRef.current = null;
      stopRejecterRef.current = null;
      setStatus((s) => (s === "stopping" ? "idle" : s));
      resolve(finalRef.current);
    }
  }, [wsError, audioError, isStreaming, resetWs, stopAudio, transcribeAudio]);

  const start = useCallback(
    async (sessionId) => {
      setStatus("connecting");
      setFallbackFinal("");
      setFallbackPhase("none");
      fallbackTriggeredRef.current = false;
      sessionIdRef.current = sessionId;

      // 1. Open the parallel batch recorder first. Best effort — if
      // it fails (mic blocked, codec unsupported) we proceed without
      // the fallback safety net but streaming may still work.
      try {
        recorderRef.current = await startAudioRecorder();
      } catch {
        recorderRef.current = null;
      }

      // 2. Open the WebSocket.
      try {
        await connectWs(sessionId);
      } catch (err) {
        // WS won't open at all. No frames captured yet, so the
        // parallel recorder's blob would be near-empty — dispose it
        // and surface the connect error.
        if (recorderRef.current) {
          try {
            recorderRef.current.dispose();
          } catch {
            /* recorder may already be torn down */
          }
          recorderRef.current = null;
        }
        setStatus("error");
        throw err;
      }

      // 3. Open the AudioContext / worklet pipeline.
      try {
        await startAudio();
      } catch (err) {
        // WS opened but mic permission / AudioContext init failed.
        // Roll the socket back and dispose the parallel recorder so
        // we don't leave half-built sessions hanging around.
        disconnectWs();
        if (recorderRef.current) {
          try {
            recorderRef.current.dispose();
          } catch {
            /* recorder may already be torn down */
          }
          recorderRef.current = null;
        }
        setStatus("error");
        throw err;
      }

      setStatus("streaming");
    },
    [connectWs, startAudio, disconnectWs],
  );

  const stop = useCallback(async () => {
    // If the fallback effect has already kicked in (WS errored
    // before the user hit stop), install a resolver and let the
    // fallback IIFE finish it — don't fire our own stop sequence.
    if (fallbackTriggeredRef.current) {
      return new Promise((resolve, reject) => {
        stopResolverRef.current = resolve;
        stopRejecterRef.current = reject;
      });
    }

    setStatus("stopping");
    await stopAudio();

    // Streaming completed without needing the fallback — drop the
    // parallel recorder so we don't leak it past this session.
    if (recorderRef.current) {
      try {
        recorderRef.current.dispose();
      } catch {
        /* recorder may already be torn down */
      }
      recorderRef.current = null;
    }

    if (!isStreaming) {
      setStatus((s) => (s === "stopping" ? "idle" : s));
      return finalRef.current;
    }

    sendStop();

    return new Promise((resolve, reject) => {
      stopResolverRef.current = resolve;
      stopRejecterRef.current = reject;
    });
  }, [stopAudio, isStreaming, sendStop]);

  const cancel = useCallback(() => {
    // Hard abandon: stop the mic, drop the WS without flushing, drop
    // the parallel recorder, and resolve any pending stop() with
    // whatever final we already have.
    stopAudio();
    disconnectWs();
    if (recorderRef.current) {
      try {
        recorderRef.current.dispose();
      } catch {
        /* recorder may already be torn down */
      }
      recorderRef.current = null;
    }
    fallbackTriggeredRef.current = false;
    setStatus("idle");

    if (stopResolverRef.current) {
      const resolve = stopResolverRef.current;
      stopResolverRef.current = null;
      stopRejecterRef.current = null;
      resolve(finalRef.current);
    }
  }, [stopAudio, disconnectWs]);

  const reset = useCallback(() => {
    resetWs();
    setFallbackFinal("");
    setFallbackPhase("none");
    fallbackTriggeredRef.current = false;
    setStatus("idle");
  }, [resetWs]);

  // Final-transcript merge: prefer fallbackFinal if we have one (the
  // batch path overwrites the partial WS state in that branch),
  // otherwise expose the WS final unchanged.
  const exposedFinal = fallbackFinal || final;

  // Error suppression: while the fallback is pending or has succeeded
  // we don't want to also bother the consumer with the WS error that
  // triggered it. If the fallback itself failed, surface the original
  // error (set on `error` state via the error-watcher branch).
  const exposedError =
    fallbackPhase === "pending" || fallbackPhase === "ok"
      ? null
      : wsError || audioError;

  return {
    status,
    partial,
    final: exposedFinal,
    error: exposedError,
    isSupported,
    start,
    stop,
    cancel,
    reset,
  };
}
