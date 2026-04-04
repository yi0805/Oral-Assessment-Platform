import api from "./api";

export async function getPendingReviews() {
  const response = await api.get("/pendingReviews");
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
