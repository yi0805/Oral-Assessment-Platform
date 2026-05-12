import { useCallback, useEffect, useRef, useState } from "react";

// React hook that owns the AudioContext + MediaStreamSource +
// AudioWorkletNode lifecycle and delivers Int16 LE PCM frames from the
// microphone to a consumer-supplied callback.
//
// Issue #72. Loaded by useStreamingTranscribe (added later) which
// forwards each frame over a WebSocket to the streaming-transcribe
// route. The PCM-capture concern is separated from the WebSocket
// concern so each piece can be reasoned about and replaced in
// isolation.
//
// Public contract:
//
//   const { start, stop, status, error, isSupported } = useAudioContext({
//     onPcmFrame: (arrayBuffer) => { /* ~3200 bytes @ 16kHz Int16 LE */ },
//   });
//
// - start(): async. Opens the mic, creates the AudioContext, loads the
//   PCM-downsampling worklet, and begins delivering ~100 ms ArrayBuffer
//   batches of 16 kHz mono Int16 LE samples to onPcmFrame. Must be
//   called from inside a user gesture (browser AudioContext policy) —
//   wire it to a button click, not an effect.
// - stop(): async. Tears the pipeline down. Idempotent.
// - status: "idle" | "starting" | "capturing" | "error".
// - error: the last Error from start() / stop(), or null.
// - isSupported: false if the browser lacks AudioContext or
//   getUserMedia — check before showing a record button.

const WORKLET_URL = "/stt-pcm-worklet.js";
const PROCESSOR_NAME = "stt-pcm-processor";

// [STT Instrumentation - issue #72] Same opt-in pattern as the WS
// hook — only publishes when the stt_debug localStorage flag is set,
// so production sessions don't carry around an event dispatcher for
// stats nobody is reading.
function publishAudioCtxStats(updater) {
  if (typeof window === "undefined") return;
  try {
    if (window.localStorage.getItem("stt_debug") !== "1") return;
  } catch {
    return;
  }
  const prev = window.__sttAudioCtxStats || {
    framesPosted: 0,
    bytesPosted: 0,
    ctxState: "idle",
    lastFrameAt: null,
  };
  const next = updater(prev);
  window.__sttAudioCtxStats = next;
  window.dispatchEvent(new CustomEvent("stt:audio-stats", { detail: next }));
}

function detectSupport() {
  if (typeof window === "undefined") return false;
  const AC = window.AudioContext || window.webkitAudioContext;
  return (
    typeof AC === "function" &&
    typeof navigator !== "undefined" &&
    !!navigator.mediaDevices &&
    typeof navigator.mediaDevices.getUserMedia === "function"
  );
}

export function useAudioContext({ onPcmFrame } = {}) {
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState(null);

  // Latest-callback ref. The worklet message handler always calls the
  // freshest onPcmFrame even when the caller passes a new function on
  // every render. Re-wiring the worklet on each render would tear down
  // the active capture session — that's the opposite of what we want.
  const onPcmFrameRef = useRef(onPcmFrame);
  useEffect(() => {
    onPcmFrameRef.current = onPcmFrame;
  }, [onPcmFrame]);

  // Live audio pipeline. Cleared in stop() / on unmount.
  const audioCtxRef = useRef(null);
  const streamRef = useRef(null);
  const sourceNodeRef = useRef(null);
  const workletNodeRef = useRef(null);

  const isSupported = detectSupport();

  const stop = useCallback(async () => {
    // Tear down in reverse construction order. Each step is wrapped
    // because any may throw on a partially-built pipeline (e.g. start()
    // failed halfway through).
    if (workletNodeRef.current) {
      try {
        workletNodeRef.current.port.onmessage = null;
      } catch {
        /* port may already be closed */
      }
      try {
        workletNodeRef.current.disconnect();
      } catch {
        /* node may not be connected */
      }
      workletNodeRef.current = null;
    }
    if (sourceNodeRef.current) {
      try {
        sourceNodeRef.current.disconnect();
      } catch {
        /* node may not be connected */
      }
      sourceNodeRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch {
          /* track may already be stopped */
        }
      });
      streamRef.current = null;
    }
    if (audioCtxRef.current) {
      try {
        await audioCtxRef.current.close();
      } catch {
        /* context may already be closed */
      }
      audioCtxRef.current = null;
    }
    setStatus("idle");
  }, []);

  const start = useCallback(async () => {
    if (!isSupported) {
      const err = new Error(
        "Real-time audio capture is not supported in this browser.",
      );
      setError(err);
      setStatus("error");
      throw err;
    }

    setStatus("starting");
    setError(null);

    try {
      // 1. Open the mic. Throws on permission-denied / no-device.
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
      streamRef.current = stream;

      // 2. Create the AudioContext. Some Safari versions still ship
      // webkitAudioContext; the fallback is harmless if both exist.
      const Ctx = window.AudioContext || window.webkitAudioContext;
      const ctx = new Ctx();
      audioCtxRef.current = ctx;

      // Some browsers (Safari, sometimes Chrome on iOS) start the
      // context suspended even inside a user gesture. resume() is a
      // no-op when the context is already running.
      if (ctx.state === "suspended") {
        await ctx.resume();
      }

      // 3. Load the PCM-downsampling worklet (public/stt-pcm-worklet.js
      // from the previous commit). addModule() throws on 404, network
      // error, or syntax error inside the worklet.
      await ctx.audioWorklet.addModule(WORKLET_URL);

      // 4. Build the node graph: mic → worklet → destination.
      const source = ctx.createMediaStreamSource(stream);
      sourceNodeRef.current = source;

      const worklet = new AudioWorkletNode(ctx, PROCESSOR_NAME);
      workletNodeRef.current = worklet;

      // The worklet posts ArrayBuffers of Int16 LE PCM. Forward each
      // batch to the latest onPcmFrame callback.
      worklet.port.onmessage = (event) => {
        const cb = onPcmFrameRef.current;
        const data = event.data;
        const bytes =
          data && typeof data.byteLength === "number" ? data.byteLength : 0;
        // Peak-amplitude check: lets the overlay distinguish "mic
        // captured real speech" (peakAmp ~ 5000-30000) from "mic
        // captured silence" (peakAmp ~ 0). Silent audio is the most
        // likely reason AWS would close a stream early without
        // returning any transcripts. Iterating 1600 samples is
        // negligible at 10 frames/sec.
        let peakAmp = 0;
        if (data && data.byteLength) {
          const samples = new Int16Array(data);
          for (let i = 0; i < samples.length; i++) {
            const v = samples[i] < 0 ? -samples[i] : samples[i];
            if (v > peakAmp) peakAmp = v;
          }
        }
        publishAudioCtxStats((prev) => ({
          ...prev,
          framesPosted: prev.framesPosted + 1,
          bytesPosted: prev.bytesPosted + bytes,
          lastFrameAt: Date.now(),
          ctxState: ctx.state,
          peakAmp,
          // Rolling max so the overlay shows the loudest sample seen
          // during the whole session — answers "did the mic EVER pick
          // up speech" without the user having to watch live.
          peakAmpEver: Math.max(prev.peakAmpEver || 0, peakAmp),
        }));
        if (cb) cb(data);
      };

      // Listen for AudioContext state changes — Chrome will sometimes
      // re-suspend a context if focus shifts during recording, which
      // silently stops the worklet from producing frames. The overlay
      // surfaces this so we can tell the difference between "user
      // stopped quickly" and "context died mid-recording".
      ctx.onstatechange = () => {
        publishAudioCtxStats((prev) => ({ ...prev, ctxState: ctx.state }));
      };
      publishAudioCtxStats((prev) => ({
        ...prev,
        framesPosted: 0,
        bytesPosted: 0,
        lastFrameAt: null,
        ctxState: ctx.state,
        peakAmp: 0,
        peakAmpEver: 0,
      }));

      source.connect(worklet);
      // Connecting the worklet's output to destination keeps it in the
      // active audio graph so process() actually fires. The worklet
      // never writes to its outputs, so destination receives silence —
      // no audible playback, no feedback risk.
      worklet.connect(ctx.destination);

      setStatus("capturing");
    } catch (err) {
      // Roll back any half-built pipeline state before surfacing.
      await stop();
      setError(err);
      setStatus("error");
      throw err;
    }
  }, [isSupported, stop]);

  // Clean up on unmount so navigating away from the assessment can't
  // leak an open mic stream.
  useEffect(() => {
    return () => {
      stop();
    };
  }, [stop]);

  return { start, stop, status, error, isSupported };
}
