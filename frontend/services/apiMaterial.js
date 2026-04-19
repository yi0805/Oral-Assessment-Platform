import api from "./api";

export async function uploadMaterial(courseId, file) {
  const matForm = new FormData();
  matForm.append("file", file);

  const response = await api.post(
    `/courses/${courseId}/materials/upload`,
    matForm,
  );

  return response.data;
}
