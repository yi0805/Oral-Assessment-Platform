import api from "./api";

export async function uploadRubric(courseId, file) {
  const rubForm = new FormData();
  rubForm.append("file", file);

  const response = await api.post(
    `/courses/${courseId}/rubrics/upload`,
    rubForm,
  );

  return response.data;
}
