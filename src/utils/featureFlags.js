// Feature flags read from Vite env vars at build time.
//
// To toggle a flag locally, set the corresponding VITE_* var in .env.local
// and restart the dev server. Unset / unknown values default to OFF.

function readBoolFlag(value) {
  if (value == null) return false;
  const v = String(value).trim().toLowerCase();
  return v === "true" || v === "1" || v === "yes" || v === "on";
}

/**
 * Issue #71 — Audio transcription edit-before-submit flow.
 *
 * When ENABLED, audio recordings are transcribed and shown in the answer
 * input for the student to review and correct before the answer is saved
 * to the Transcript table. The DB write only happens on "Submit Answer".
 *
 * When DISABLED (default), the legacy behavior is preserved: the audio
 * recording is sent to the backend in a single request that both
 * transcribes and persists the answer.
 *
 * Env var: VITE_ENABLE_EDIT_BEFORE_SUBMIT
 */
export function isEditBeforeSubmitEnabled() {
  return readBoolFlag(import.meta.env.VITE_ENABLE_EDIT_BEFORE_SUBMIT);
}
