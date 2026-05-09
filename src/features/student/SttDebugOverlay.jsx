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

  useEffect(() => {
    if (!enabled) return undefined;

    // Auto-flip the localStorage flag so the API layer starts logging.
    try {
      window.localStorage.setItem("stt_debug", "1");
    } catch {
      /* localStorage unavailable — overlay still renders, no logs */
    }

    if (window.__sttLastTimings) {
      setTimings(window.__sttLastTimings);
    }

    function handler(event) {
      setTimings(event.detail);
    }
    window.addEventListener("stt:timings", handler);
    return () => window.removeEventListener("stt:timings", handler);
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
      {timings ? (
        <>
          <div>round-trip: {timings.requestRoundTripMs} ms</div>
          <div>blob: {timings.blobSizeKB} KB</div>
          <div>type: {timings.blobType}</div>
          <div>ext: {timings.ext}</div>
          <div style={{ opacity: 0.7, marginTop: 4 }}>
            check backend logs for [STT timings]
          </div>
        </>
      ) : (
        <div style={{ opacity: 0.8 }}>
          waiting for first transcription…
        </div>
      )}
    </div>
  );
}
