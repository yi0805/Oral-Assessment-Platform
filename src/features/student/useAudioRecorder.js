import { useCallback, useEffect, useRef, useState } from "react";

import {
  isRecordingSupported,
  startAudioRecorder,
} from "./audioRecorder";

// Thin React wrapper around the framework-agnostic recorder in
// audioRecorder.js. Owns only the React state (status, error) and the
// useRef-based handle; all MediaRecorder lifecycle, mime-type
// negotiation, and stop-promise plumbing live in audioRecorder.js so
// the streaming flow (added later in #72) can reuse them.
//
// This split is a pure refactor — the public contract { status, error,
// isSupported, start, stop, reset } is unchanged. stop() still resolves
// with the recorded Blob (or null if the recorder errored).

export function useAudioRecorder() {
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState(null);

  // Holds the handle returned by startAudioRecorder while a recording
  // is in flight. Cleared on stop / dispose / unmount.
  const handleRef = useRef(null);

  const isSupported = isRecordingSupported();

  const cleanup = useCallback(() => {
    if (handleRef.current) {
      handleRef.current.dispose();
      handleRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  const start = useCallback(async () => {
    if (!isSupported) {
      const err = new Error(
        "Audio recording is not supported in this browser.",
      );
      setError(err);
      setStatus("error");
      throw err;
    }

    try {
      setError(null);
      handleRef.current = await startAudioRecorder({
        onError: (recorderErr) => {
          // Mirror the original useAudioRecorder behaviour: a recorder
          // error mid-stream surfaces as { status: "error", error }
          // and the handle is dropped so subsequent stop() resolves
          // null.
          setError(recorderErr);
          setStatus("error");
          handleRef.current = null;
        },
      });
      setStatus("recording");
    } catch (err) {
      cleanup();
      setError(err);
      setStatus("error");
      throw err;
    }
  }, [cleanup, isSupported]);

  const stop = useCallback(async () => {
    const handle = handleRef.current;
    if (!handle) return null;

    const blob = await handle.stop();
    handleRef.current = null;
    // Only return to "idle" if the recorder didn't error mid-stop —
    // the onError callback above may have already moved us to "error",
    // and that takes precedence.
    setStatus((s) => (s === "error" ? s : "idle"));
    return blob;
  }, []);

  const reset = useCallback(() => {
    cleanup();
    setError(null);
    setStatus("idle");
  }, [cleanup]);

  return { status, error, isSupported, start, stop, reset };
}
