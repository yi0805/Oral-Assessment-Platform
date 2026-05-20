import api from "./api";

export async function getPendingReviews() {
  const response = await api.get("/pendingReviews");
  return response.data;
}

export async function getTranscript(sessionId) {
  const response = await api.get(`/transcript/${sessionId}`);
  return response.data;
}

export async function getMyAssessmentSessions(courseId) {
  const response = await api.get(`/courses/${courseId}/my-assessment-sessions`);
  return response.data;
}

export async function getMyAssessmentHistory(courseId) {
  const response = await api.get(`/courses/${courseId}/my-assessment-history`);
  return response.data;
}

export async function updatePendingReview(sessionId, studentId) {
  const response = await api.put(
    `/sessions/${sessionId}/${studentId}/release/session`,
  );
  return response.data;
}

export async function updateAllPendingReviews(assessments) {
  const response = await api.put("/sessions/release/allSessions", {
    assessments: assessments,
  });

  return response.data;
}

export async function updateReviewGrade(sessionId, grade) {
  const response = await api.put(`/sessions/${sessionId}/grade`, {
    grade: grade,
  });
  return response.data;
}

export async function approveAiSummary(sessionId) {
  const response = await api.post(`/sessions/${sessionId}/ai-summary/approve`);
  return response.data;
}

export async function approveAllAiSummaries(assessments) {
  const response = await api.post("/sessions/ai-summary/approve/all", {
    assessments: assessments,
  });
  return response.data;
}

export async function upsertReview(sessionId, finalGrade, comments) {
  const response = await api.put(`/sessions/${sessionId}/review`, {
    final_grade: finalGrade,
    comments: comments,
  });
  return response.data;
}

export async function startSession(assessmentConfigId, countReentry = false) {
  const response = await api.post(
    `/assessments/${assessmentConfigId}/sessions/start`,
    null,
    { params: { count_reentry: countReentry } },
  );
  return response.data;
}

export async function respondSession(sessionId, answerText) {
  const response = await api.post(`/sessions/${sessionId}/respond`, {
    answer_text: answerText,
  });
  return response.data;
}

const AUDIO_MIME_TO_EXT = {
  "audio/webm": "webm",
  "audio/ogg": "ogg",
  "audio/mp4": "m4a",
  "audio/mpeg": "mp3",
  "audio/mp3": "mp3",
  "audio/wav": "wav",
  "audio/x-wav": "wav",
  "audio/flac": "flac",
};

function inferAudioExtension(blob) {
  const baseType = (blob?.type || "").split(";")[0].trim().toLowerCase();
  return AUDIO_MIME_TO_EXT[baseType] || "webm";
}

// Issue #71 — transcribe-only endpoint for the edit-before-submit flow.
// Sends the recording to the backend, receives back just the transcript
// string, and does NOT advance the session or write to the Transcript
// table. The caller is responsible for showing the text to the student
// and triggering the standard /respond endpoint when they hit Submit.
export async function transcribeSessionAudio(sessionId, audioBlob) {
  const ext = inferAudioExtension(audioBlob);

  const formData = new FormData();
  formData.append("audio", audioBlob, `answer.${ext}`);

  const response = await api.post(
    `/sessions/${sessionId}/transcribe/audio`,
    formData,
  );

  // Backend always returns { transcript: string }. Coerce to a safe
  // string so downstream code can rely on .length / .trim() etc.
  return typeof response.data?.transcript === "string"
    ? response.data.transcript
    : "";
}

export async function completeSession(sessionId) {
  const response = await api.post(`/sessions/${sessionId}/complete`);
  return response.data;
}

export async function unpublishGrade(sessionId, studentId) {
  const response = await api.put(
    `/sessions/${sessionId}/${studentId}/unpublish/session`,
  );
  return response.data;
}

export async function recordBlurNotification(sessionId, blurCount) {
  const response = await api.post(`/sessions/${sessionId}/blur-notification`, {
    blur_count: blurCount,
  });
  return response.data;
}

export async function recordReconnectNotification(sessionId, disconnectCount) {
  const response = await api.post(
    `/sessions/${sessionId}/reconnect-notification`,
    {
      disconnect_count: disconnectCount,
    },
  );
  return response.data;
}

export async function getNotifications() {
  const response = await api.get("/notifications");
  return response.data;
}

export async function markNotificationRead(notificationId) {
  const response = await api.patch(`/notifications/${notificationId}/read`);
  return response.data;
}

export async function markAllNotificationsRead() {
  const response = await api.patch("/notifications/read-all");
  return response.data;
}
