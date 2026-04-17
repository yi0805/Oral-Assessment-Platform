import api from "./api";

export async function createRubric(courseId, rubricPayload) {
  const response = await api.post(`/courses/${courseId}/rubrics`, rubricPayload);
  return response.data;
}

export async function getRubric(assessmentConfigId) {
  const response = await api.get(`/assessments/${assessmentConfigId}/rubric`);
  return response.data;
}

export async function updateRubric(assessmentConfigId, rubricPayload) {
  const response = await api.put(`/assessments/${assessmentConfigId}/rubric`, rubricPayload);
  return response.data;
}
