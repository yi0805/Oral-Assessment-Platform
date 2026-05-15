// Framework-agnostic MediaRecorder wrapper.
//
// Issue #72. Split out of useAudioRecorder.js so two callers can share
// the mic-stream lifecycle, mime-type negotiation, and stop-promise
// plumbing without each owning its own MediaRecorder code:
//
//   1. useAudioRecorder.js — the React hook used by the existing
//      batch-upload flow (StudentAssessment).
//   2. useStreamingTranscribe.js (added later in #72) — the
//      streaming-with-batch-fallback flow needs to buffer the same
//      MediaRecorder blob in case the WebSocket path fails.
//
// This module is pure JS, no React. It is a true refactor — the public
// behaviour of useAudioRecorder must not change.

const PREFERRED_MIME_TYPES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/ogg;codecs=opus",
  "audio/ogg",
  "audio/mp4",
];

/**
 * Return the highest-priority MIME type the browser's MediaRecorder
 * actually supports, or "" to mean "let the browser pick", or null if
 * MediaRecorder doesn't exist at all (SSR / very old browser).
 */
function pickSupportedMimeType() {
  if (typeof window === "undefined") return null;
  if (typeof window.MediaRecorder === "undefined") return null;

  for (const type of PREFERRED_MIME_TYPES) {
    if (window.MediaRecorder.isTypeSupported(type)) return type;
  }

  return "";
}

/**
 * True if the browser exposes both getUserMedia and MediaRecorder.
 * Use this from feature-detection paths that need to short-circuit
 * before importing the recorder.
 */
export function isRecordingSupported() {
  return (
    typeof navigator !== "undefined" &&
    !!navigator.mediaDevices &&
    typeof navigator.mediaDevices.getUserMedia === "function" &&
    typeof window !== "undefined" &&
    typeof window.MediaRecorder !== "undefined"
  );
}

/**
 * Open the microphone and start recording.
 *
 * Resolves to a handle:
 *   .mimeType: string            negotiated container/codec
 *   .stop(): Promise<Blob|null>  stops cleanly; resolves with the
 *                                recorded blob, or null if a recorder
 *                                error occurred mid-recording (matches
 *                                the historical useAudioRecorder
 *                                contract — error is also surfaced via
 *                                the onError callback).
 *   .dispose(): void             cancel without waiting; releases the
 *                                mic stream and any pending stop()
 *                                promise resolves with null.
 *
 * Options:
 *   onError(err): called if the underlying MediaRecorder emits an
 *     "error" event AFTER recording has started. Errors thrown by
 *     getUserMedia / unsupported-browser checks reject the returned
 *     Promise directly instead.
 *
 * Throws synchronously-via-rejection if recording isn't supported,
 * if the user denies the mic prompt, or if MediaRecorder construction
 * fails.
 */
export async function startAudioRecorder({ onError } = {}) {
  if (!isRecordingSupported()) {
    throw new Error("Audio recording is not supported in this browser.");
  }

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mimeType = pickSupportedMimeType();
  const recorder =
    mimeType && mimeType.length > 0
      ? new window.MediaRecorder(stream, { mimeType })
      : new window.MediaRecorder(stream);

  const chunks = [];
  let stopResolve = null;

  function releaseStream() {
    stream.getTracks().forEach((track) => track.stop());
  }

  recorder.addEventListener("dataavailable", (event) => {
    if (event.data && event.data.size > 0) {
      chunks.push(event.data);
    }
  });

  recorder.addEventListener("stop", () => {
    const blobType = recorder.mimeType || mimeType || "audio/webm";
    const blob = new Blob(chunks, { type: blobType });
    releaseStream();

    if (stopResolve) {
      stopResolve(blob);
      stopResolve = null;
    }
  });

  recorder.addEventListener("error", (event) => {
    const err =
      event && event.error
        ? event.error
        : new Error("MediaRecorder failed.");
    releaseStream();

    if (onError) onError(err);

    // Match useAudioRecorder's original behaviour: resolve stop() with
    // null rather than reject so consumers can treat "no blob" uniformly
    // (the error itself is delivered through onError above).
    if (stopResolve) {
      stopResolve(null);
      stopResolve = null;
    }
  });

  recorder.start();

  return {
    mimeType: recorder.mimeType || mimeType || "audio/webm",

    stop() {
      return new Promise((resolve) => {
        if (recorder.state === "inactive") {
          resolve(null);
          return;
        }
        stopResolve = resolve;
        recorder.stop();
      });
    },

    dispose() {
      try {
        if (recorder.state !== "inactive") {
          recorder.stop();
        }
      } catch {
        // Recorder may already be transitioning to inactive — fine.
      }
      releaseStream();
      if (stopResolve) {
        stopResolve(null);
        stopResolve = null;
      }
    },
  };
}
