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

export async function completeSession(sessionId) {
  const response = await api.post(`/sessions/${sessionId}/complete`);
  return response.data;
}
