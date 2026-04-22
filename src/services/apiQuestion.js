import api from "./api";

export async function questionGenerate(
  courseId,
  materialId,
  rubricId,
  assessmentName,
  totalTime,
  numQuestions,
  releaseTime,
  dueTime,
) {
  const response = await api.post(`/courses/${courseId}/generate-question`, {
    material_id: materialId,
    rubric_id: rubricId,
    assessment_title: assessmentName,
    total_time_minutes: totalTime,
    num_main_questions: numQuestions,
    release_time: releaseTime,
    due_time: dueTime,
  });
  return response.data;
}

export async function updateQuestion(questionId, questionText) {
  const response = await api.put(`/questions/${questionId}`, {
    question_text: questionText,
  });
  return response.data;
}

export async function deleteQuestion(questionId) {
  const response = await api.delete(`/questions/${questionId}`);

  return response.data;
}

export async function publishAssessment(courseId, assessmentConfigId) {
  const response = await api.post(
    `/courses/${courseId}/assessments/${assessmentConfigId}/release`,
  );
  return response.data;
}
