import api from "./api";

export async function uploadRubric(courseId, file, assessmentName) {
  const rubForm = new FormData();
  rubForm.append("file", file);
  rubForm.append("title", `${assessmentName} - Rubric`);

  const response = await api.post(
    `/courses/${courseId}/rubrics/upload`,
    rubForm,
  );

  return response.data;
}
