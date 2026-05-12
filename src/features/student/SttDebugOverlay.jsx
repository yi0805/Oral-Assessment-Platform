// [STT Instrumentation - issue #72]
//
// Tiny debug overlay that renders the most recent STT timing reading from
// `window.__sttLastTimings` (populated by transcribeSessionAudio in
// services/apiSession.js). Gated behind the `?debugStt=1` query param so
// it never appears for real users — and it gates itself again on the
// `stt_debug` localStorage flag so the underlying logs only fire when
// requested.
//
// Remove this file (and its import in StudentAssessment.jsx) once issue
// #72 is closed.

import { useEffect, useState } from "react";

function isEnabled() {
  if (typeof window === "undefined") return false;
  try {
    const params = new URLSearchParams(window.location.search);
    return params.get("debugStt") === "1";
  } catch {
    return false;
  }
}

export default function SttDebugOverlay() {
  const [enabled] = useState(isEnabled);
  const [timings, setTimings] = useState(null);
  const [streamStats, setStreamStats] = useState(null);
  const [audioStats, setAudioStats] = useState(null);

  useEffect(() => {
    if (!enabled) return undefined;

    // Auto-flip the localStorage flag so the API layer starts logging.
    try {
      window.localStorage.setItem("stt_debug", "1");
    } catch {
      /* localStorage unavailable — overlay still renders, no logs */
    }

    if (window.__sttLastTimings) setTimings(window.__sttLastTimings);
    if (window.__sttStreamStats) setStreamStats(window.__sttStreamStats);
    if (window.__sttAudioCtxStats) setAudioStats(window.__sttAudioCtxStats);

    function batchHandler(event) {
      setTimings(event.detail);
    }
    function streamHandler(event) {
      setStreamStats(event.detail);
    }
    function audioHandler(event) {
      setAudioStats(event.detail);
    }
    window.addEventListener("stt:timings", batchHandler);
    window.addEventListener("stt:stream-stats", streamHandler);
    window.addEventListener("stt:audio-stats", audioHandler);
    return () => {
      window.removeEventListener("stt:timings", batchHandler);
      window.removeEventListener("stt:stream-stats", streamHandler);
      window.removeEventListener("stt:audio-stats", audioHandler);
    };
  }, [enabled]);

  if (!enabled) return null;

  return (
    <div
      style={{
        position: "fixed",
        bottom: 12,
        right: 12,
        zIndex: 9999,
        padding: "8px 12px",
        background: "rgba(17, 24, 39, 0.92)",
        color: "#f9fafb",
        fontFamily:
          'ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace',
        fontSize: 12,
        lineHeight: 1.5,
        borderRadius: 6,
        boxShadow: "0 6px 16px rgba(0,0,0,0.25)",
        maxWidth: 280,
      }}
      data-testid="stt-debug-overlay"
    >
      <div style={{ fontWeight: 600, marginBottom: 4 }}>
        STT debug (issue #72)
      </div>

      <div style={{ fontWeight: 600, marginTop: 4 }}>audio worklet</div>
      {audioStats ? (
        <>
          <div>posted: {audioStats.framesPosted} frames</div>
          <div>bytes: {audioStats.bytesPosted}</div>
          <div>ctx: {audioStats.ctxState}</div>
          <div>
            peak: {audioStats.peakAmpEver ?? 0}
            {audioStats.peakAmpEver != null && audioStats.peakAmpEver < 500 && (
              <span style={{ color: "#fca5a5" }}> (silent!)</span>
            )}
          </div>
        </>
      ) : (
        <div style={{ opacity: 0.7 }}>not recording yet</div>
      )}

      <div style={{ fontWeight: 600, marginTop: 6 }}>ws → server</div>
      {streamStats ? (
        <>
          <div>sent: {streamStats.framesSent} frames</div>
          <div>bytes: {streamStats.bytesSent}</div>
          <div>state: {streamStats.wsState}</div>
          {streamStats.sendSkippedNotOpen > 0 && (
            <div style={{ color: "#fca5a5" }}>
              skipped: {streamStats.sendSkippedNotOpen}
            </div>
          )}
        </>
      ) : (
        <div style={{ opacity: 0.7 }}>not connected yet</div>
      )}

      <div style={{ fontWeight: 600, marginTop: 6 }}>last batch</div>
      {timings ? (
        <>
          <div>round-trip: {timings.requestRoundTripMs} ms</div>
          <div>blob: {timings.blobSizeKB} KB</div>
          <div>type: {timings.blobType}</div>
          <div>ext: {timings.ext}</div>
        </>
      ) : (
        <div style={{ opacity: 0.7 }}>no batch yet</div>
      )}

      <div style={{ opacity: 0.7, marginTop: 6 }}>
        check backend logs for [STT timings]
      </div>
    </div>
  );
}
