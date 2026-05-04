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
  const response = await api.post(
    `/sessions/${sessionId}/ai-summary/approve`,
  );
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

export async function startSession(assessmentConfigId) {
  const response = await api.post(
    `/assessments/${assessmentConfigId}/sessions/start`,
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

export async function respondSessionAudio(sessionId, audioBlob) {
  const ext = inferAudioExtension(audioBlob);

  const formData = new FormData();
  formData.append("audio", audioBlob, `answer.${ext}`);

  const response = await api.post(
    `/sessions/${sessionId}/respond/audio`,
    formData,
  );

  return response.data;
}

export async function completeSession(sessionId) {
  const response = await api.post(`/sessions/${sessionId}/complete`);
  return response.data;
}
