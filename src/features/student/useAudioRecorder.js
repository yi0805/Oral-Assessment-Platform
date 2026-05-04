import { useCallback, useEffect, useRef, useState } from "react";

const PREFERRED_MIME_TYPES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/ogg;codecs=opus",
  "audio/ogg",
  "audio/mp4",
];

function pickSupportedMimeType() {
  if (typeof window === "undefined") return null;
  if (typeof window.MediaRecorder === "undefined") return null;

  for (const type of PREFERRED_MIME_TYPES) {
    if (window.MediaRecorder.isTypeSupported(type)) return type;
  }

  return "";
}

export function useAudioRecorder() {
  const [status, setStatus] = useState("idle"); 
  const [error, setError] = useState(null);

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const stopResolverRef = useRef(null);

  const isSupported =
    typeof navigator !== "undefined" &&
    !!navigator.mediaDevices &&
    typeof navigator.mediaDevices.getUserMedia === "function" &&
    typeof window !== "undefined" &&
    typeof window.MediaRecorder !== "undefined";

  const releaseStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  const cleanup = useCallback(() => {
    releaseStream();
    mediaRecorderRef.current = null;
    chunksRef.current = [];
    stopResolverRef.current = null;
  }, [releaseStream]);

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

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
      streamRef.current = stream;

      const mimeType = pickSupportedMimeType();
      const recorder =
        mimeType && mimeType.length > 0
          ? new window.MediaRecorder(stream, { mimeType })
          : new window.MediaRecorder(stream);

      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.addEventListener("dataavailable", (event) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      });

      recorder.addEventListener("stop", () => {
        const blobType = recorder.mimeType || mimeType || "audio/webm";
        const blob = new Blob(chunksRef.current, { type: blobType });

        const resolver = stopResolverRef.current;
        cleanup();
        setStatus("idle");

        if (resolver) resolver(blob);
      });

      recorder.addEventListener("error", (event) => {
        const recorderErr =
          event && event.error
            ? event.error
            : new Error("MediaRecorder failed.");
        setError(recorderErr);
        setStatus("error");

        const resolver = stopResolverRef.current;
        cleanup();
        if (resolver) resolver(null);
      });

      recorder.start();
      setStatus("recording");
    } catch (err) {
      cleanup();
      setError(err);
      setStatus("error");
      throw err;
    }
  }, [cleanup, isSupported]);

  const stop = useCallback(() => {
    return new Promise((resolve) => {
      const recorder = mediaRecorderRef.current;

      if (!recorder || recorder.state === "inactive") {
        resolve(null);
        return;
      }

      stopResolverRef.current = resolve;
      recorder.stop();
    });
  }, []);

  const reset = useCallback(() => {
    cleanup();
    setError(null);
    setStatus("idle");
  }, [cleanup]);

  return { status, error, isSupported, start, stop, reset };
}
