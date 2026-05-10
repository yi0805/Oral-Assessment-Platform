import { useCallback, useEffect, useRef, useState } from "react";

import { useAudioContext } from "./useAudioContext";
import { useStreamingTranscribe } from "./useStreamingTranscribe";

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
// This hook wires the audio hook's onPcmFrame callback directly to
// the WebSocket hook's sendPcm so frames flow with no glue code in
// the page component, and exposes a single status-state-machine API
// that StudentAssessment.jsx can consume in the next commit.
//
// Public contract:
//
//   const {
//     status, partial, final, error, isSupported,
//     start, stop, cancel, reset,
//   } = useStudentSpeechStream();
//
//   await start(sessionId);           // opens WS, then opens mic
//   // ...PCM frames stream automatically while status === "streaming"
//   const transcript = await stop();  // flushes server, returns final
//
// Status transitions:
//
//   idle ──start()──▶ connecting ──ws open──▶ streaming
//   streaming ──stop()──▶ stopping ──ws close──▶ idle
//   (any state) ──error──▶ error
//   error / streaming / stopping ──cancel()──▶ idle  (no flush)
//
// stop() returns a Promise that resolves with the accumulated final
// transcript once the server has flushed and closed the socket.
// cancel() is the abandon path — used when the student navigates away
// or hits "discard recording".

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

  const [status, setStatus] = useState("idle");

  // Pending stop()/cancel() promise resolvers, plus the latest known
  // `final` value snapshotted into a ref so the resolver can read it
  // without going through state (which may be stale by the time the
  // close event lands).
  const stopResolverRef = useRef(null);
  const stopRejecterRef = useRef(null);
  const finalRef = useRef("");

  useEffect(() => {
    finalRef.current = final;
  }, [final]);

  // When the WS connection ends, resolve any pending stop() Promise.
  // This fires whether the close was triggered by sendStop (clean
  // path) or by a server-side error (the server closes after sending
  // the "error" message).
  useEffect(() => {
    if (!isStreaming && stopResolverRef.current) {
      const resolve = stopResolverRef.current;
      stopResolverRef.current = null;
      stopRejecterRef.current = null;
      // Only step down to idle if we were in "stopping" — error state
      // wins, and the error-watcher effect below will have already
      // moved us to "error".
      setStatus((s) => (s === "stopping" ? "idle" : s));
      resolve(finalRef.current);
    }
  }, [isStreaming]);

  // Surface either hook's error into the orchestrator's status. Also
  // rejects any pending stop() Promise so callers don't hang forever
  // when the WS dies mid-flush.
  useEffect(() => {
    const err = wsError || audioError;
    if (!err) return;

    setStatus("error");

    if (stopRejecterRef.current) {
      const reject = stopRejecterRef.current;
      stopResolverRef.current = null;
      stopRejecterRef.current = null;
      reject(err);
    }
  }, [wsError, audioError]);

  const start = useCallback(
    async (sessionId) => {
      setStatus("connecting");
      try {
        await connectWs(sessionId);
      } catch (err) {
        setStatus("error");
        throw err;
      }
      try {
        await startAudio();
      } catch (err) {
        // WS opened but mic permission/init failed. Roll back the
        // socket so we don't leave a half-built session.
        disconnectWs();
        setStatus("error");
        throw err;
      }
      setStatus("streaming");
    },
    [connectWs, startAudio, disconnectWs],
  );

  const stop = useCallback(async () => {
    setStatus("stopping");

    // Always stop the mic first — no point sending more frames the
    // server is about to ignore anyway.
    await stopAudio();

    // If the WS is already closed (server errored out, network blip,
    // etc.) there's nothing to wait for. Return whatever final we have.
    if (!isStreaming) {
      setStatus((s) => (s === "stopping" ? "idle" : s));
      return finalRef.current;
    }

    // Tell the server to flush remaining results and close. The
    // close handler in useStreamingTranscribe flips isStreaming to
    // false, which fires the effect above and resolves this Promise.
    sendStop();

    return new Promise((resolve, reject) => {
      stopResolverRef.current = resolve;
      stopRejecterRef.current = reject;
    });
  }, [stopAudio, isStreaming, sendStop]);

  const cancel = useCallback(() => {
    // Hard abandon: stop the mic, drop the WS without flushing, and
    // resolve any pending stop() with whatever final we already have.
    stopAudio();
    disconnectWs();
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
    setStatus("idle");
  }, [resetWs]);

  return {
    status,
    partial,
    final,
    error: wsError || audioError,
    isSupported,
    start,
    stop,
    cancel,
    reset,
  };
}
