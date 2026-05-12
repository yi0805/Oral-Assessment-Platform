import { useCallback, useEffect, useRef, useState } from "react";

// React hook that owns the WebSocket connection to the streaming
// transcription route (/api/sessions/{id}/transcribe/stream, added in
// the earlier backend commit of issue #72) and surfaces partial /
// final transcripts as React state.
//
// This hook is *only* the WebSocket lifecycle. It doesn't know how to
// produce PCM frames — that's useAudioContext's job. The two are
// combined into one consumer-facing hook (useStudentSpeechStream) in
// the next commit. Keeping them separate makes each easier to test
// and replace.
//
// Public contract:
//
//   const {
//     partial, final, isStreaming, error,
//     connect, sendPcm, sendStop, disconnect, reset,
//   } = useStreamingTranscribe();
//
//   await connect(sessionId);     // opens WS, resolves on handshake
//   sendPcm(pcmArrayBuffer);      // forwards a binary frame
//   sendStop();                   // sends {"type":"stop"} text frame
//   disconnect();                 // closes WS without waiting
//   reset();                      // clears partial/final/error state
//
// State:
//   partial      — latest partial transcript (replaced as AWS revises)
//   final        — accumulated final transcripts joined with spaces
//   isStreaming  — true between WS open and close
//   error        — last Error from the connection or AWS, or null
//
// Server protocol (mirrors backend route handler comment):
//   server -> client (JSON text):
//     {"type":"partial","text":"...","timestamp":float}
//     {"type":"final",  "text":"...","timestamp":float}
//     {"type":"error",  "message":"..."}
//   client -> server:
//     binary PCM frames
//     {"type":"stop"} text frame, OR socket close

function buildStreamUrl(sessionId) {
  // Reuse the same base URL as the axios client — that way, a single
  // VITE_API_URL env var controls both HTTP and WS endpoints in
  // production. The base already includes the "/api" prefix.
  const httpBase =
    import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";
  // http -> ws, https -> wss. Anything else is a misconfiguration the
  // WebSocket constructor will reject loudly.
  const wsBase = httpBase.replace(/^http/i, "ws");
  return `${wsBase}/sessions/${sessionId}/transcribe/stream`;
}

// [STT Instrumentation - issue #72] Bumps the per-window stream-stats
// snapshot read by SttDebugOverlay. Stays a no-op for users without
// the debug flag — checks the localStorage gate before publishing so
// production sessions don't accumulate stats dicts that no one reads.
function publishStreamStats(updater) {
  if (typeof window === "undefined") return;
  try {
    if (window.localStorage.getItem("stt_debug") !== "1") return;
  } catch {
    return;
  }
  const prev = window.__sttStreamStats || {
    framesSent: 0,
    bytesSent: 0,
    sendSkippedNotOpen: 0,
    lastSendAt: null,
    wsState: "idle",
  };
  const next = updater(prev);
  window.__sttStreamStats = next;
  window.dispatchEvent(new CustomEvent("stt:stream-stats", { detail: next }));
}

export function useStreamingTranscribe() {
  const [partial, setPartial] = useState("");
  const [final, setFinal] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);

  // Live WebSocket. Cleared on close / disconnect / unmount.
  const wsRef = useRef(null);

  const reset = useCallback(() => {
    setPartial("");
    setFinal("");
    setError(null);
  }, []);

  const disconnect = useCallback(() => {
    const ws = wsRef.current;
    if (ws) {
      try {
        if (
          ws.readyState === WebSocket.OPEN ||
          ws.readyState === WebSocket.CONNECTING
        ) {
          ws.close();
        }
      } catch {
        /* peer may already be gone */
      }
      wsRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const connect = useCallback(
    (sessionId) => {
      // Tear down any prior connection so we never have two sockets
      // pointing at the same hook.
      disconnect();
      reset();
      // Reset the per-session stat snapshot so a fresh recording is
      // countable from zero in the debug overlay.
      publishStreamStats(() => ({
        framesSent: 0,
        bytesSent: 0,
        sendSkippedNotOpen: 0,
        lastSendAt: null,
        wsState: "connecting",
      }));

      return new Promise((resolve, reject) => {
        const url = buildStreamUrl(sessionId);

        let ws;
        try {
          ws = new WebSocket(url);
        } catch (err) {
          setError(err);
          reject(err);
          return;
        }
        // We send and receive binary as ArrayBuffer (default would be
        // Blob in some browsers, which is awkward to forward straight
        // to .send()).
        ws.binaryType = "arraybuffer";
        wsRef.current = ws;

        // Track whether the connect() promise has already settled so
        // error/close handlers can decide whether to reject or just
        // update state.
        let settled = false;

        ws.addEventListener("open", () => {
          setIsStreaming(true);
          if (!settled) {
            settled = true;
            resolve();
          }
        });

        ws.addEventListener("message", (event) => {
          // Only JSON text frames are expected from the server.
          if (typeof event.data !== "string") return;

          let msg;
          try {
            msg = JSON.parse(event.data);
          } catch {
            return;
          }

          if (msg.type === "partial") {
            // Each partial replaces the previous one for the same
            // span — AWS revises the text as more audio arrives.
            setPartial(typeof msg.text === "string" ? msg.text : "");
          } else if (msg.type === "final") {
            // Final results aren't cumulative across utterances —
            // AWS emits one per natural pause. Join them with a
            // space so the textarea ends up with a readable string.
            const piece = typeof msg.text === "string" ? msg.text : "";
            if (piece) {
              setFinal((prev) => (prev ? `${prev} ${piece}` : piece));
            }
            // The span just finalised, so the matching partial is no
            // longer "in flight".
            setPartial("");
          } else if (msg.type === "error") {
            setError(
              new Error(
                typeof msg.message === "string"
                  ? msg.message
                  : "stream_error",
              ),
            );
          } else if (msg.type === "timeout") {
            // Server-enforced per-stream duration cap reached
            // (stt_streaming_max_seconds, default 300s). The route
            // sends this frame and then closes 1008 with reason
            // "session_timeout". Surface as an error so the
            // orchestrator's fallback path picks up the buffered
            // audio and the mic gets released — without this branch
            // the timeout frame was being dropped and the client
            // left the mic open.
            const maxSeconds = Number(msg.max_seconds);
            const detail =
              Number.isFinite(maxSeconds) && maxSeconds > 0
                ? `Recording stopped automatically after ${maxSeconds} seconds.`
                : "Recording stopped automatically after the maximum duration.";
            const err = new Error(detail);
            err.code = "session_timeout";
            setError(err);
          }
        });

        ws.addEventListener("error", () => {
          // The browser deliberately hides the reason for security;
          // close handler usually fires immediately after with a more
          // useful code/reason.
          const err = new Error("WebSocket error");
          setError(err);
          if (!settled) {
            settled = true;
            reject(err);
          }
        });

        ws.addEventListener("close", (event) => {
          wsRef.current = null;
          setIsStreaming(false);

          if (!settled) {
            // Closed before "open" → handshake rejected (auth, feature
            // flag off, validation, etc.).
            settled = true;
            const reason = event.reason || "no reason";
            const err = new Error(
              `WebSocket closed before open (code ${event.code}): ${reason}`,
            );
            setError(err);
            reject(err);
            return;
          }

          // Already-open WS closed with a non-clean code. Without
          // surfacing this the orchestrator can't tell the difference
          // between a clean server-side shutdown (after the final has
          // been flushed) and an abnormal close that should trigger
          // the batch fallback + release the mic. 1000 (normal) and
          // 1005 (no status — what the browser reports when the close
          // frame omits a code) are treated as clean; anything else
          // becomes an error.
          if (event.code !== 1000 && event.code !== 1005) {
            const reason = event.reason || "no reason";
            const err = new Error(
              `WebSocket closed abnormally (code ${event.code}): ${reason}`,
            );
            // Tag session_timeout closes specifically so the consumer
            // can show a friendlier message than the generic close
            // string — the "timeout" JSON frame may also have arrived
            // and set this already, in which case setError is a no-op
            // on re-render.
            if (event.reason === "session_timeout") {
              err.code = "session_timeout";
            }
            setError(err);
          }
        });
      });
    },
    [disconnect, reset],
  );

  const sendPcm = useCallback((arrayBuffer) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      // Track these misses so the debug overlay can distinguish
      // "worklet not producing" from "worklet producing but WS not
      // ready" — both cause the same frames=0 server-side outcome.
      publishStreamStats((prev) => ({
        ...prev,
        sendSkippedNotOpen: prev.sendSkippedNotOpen + 1,
        wsState: ws ? ["connecting", "open", "closing", "closed"][ws.readyState] : "no-ws",
      }));
      return false;
    }
    try {
      ws.send(arrayBuffer);
      const bytes =
        arrayBuffer && typeof arrayBuffer.byteLength === "number"
          ? arrayBuffer.byteLength
          : 0;
      publishStreamStats((prev) => ({
        ...prev,
        framesSent: prev.framesSent + 1,
        bytesSent: prev.bytesSent + bytes,
        lastSendAt: Date.now(),
        wsState: "open",
      }));
      return true;
    } catch {
      // send() can throw if the socket entered CLOSING between the
      // readyState check and the call. Treat the same as "not sent".
      publishStreamStats((prev) => ({
        ...prev,
        sendSkippedNotOpen: prev.sendSkippedNotOpen + 1,
        wsState: "send-threw",
      }));
      return false;
    }
  }, []);

  const sendStop = useCallback(() => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    try {
      ws.send(JSON.stringify({ type: "stop" }));
    } catch {
      /* see sendPcm */
    }
  }, []);

  // Always tear down the socket on unmount so navigating away from
  // the assessment doesn't leave a dangling AWS stream connection.
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    partial,
    final,
    isStreaming,
    error,
    connect,
    sendPcm,
    sendStop,
    disconnect,
    reset,
  };
}
