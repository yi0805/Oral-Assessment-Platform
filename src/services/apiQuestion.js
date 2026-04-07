import api from "./api";

export async function updateNow(
  courseId,
  materialId,
  rubricId,
  assessmentName,
  numQuestions,
  totalTime,
) {
  const response = await api.post(`/courses/${courseId}/update-now`, {
    material_ids: [materialId],
    rubric_id: rubricId,
    assessment_title: assessmentName,
    num_main_questions: numQuestions,
    total_time_minutes: totalTime,
    max_followups_per_main: 3,
    followup_enabled: true,
  });
  return response.data;
}
