import api from "./api";

export async function uploadMaterial(courseId, file, assessmentName) {
  const matForm = new FormData();
  matForm.append("file", file);
  matForm.append("title", `${assessmentName} - Material`);

  const response = await api.post(
    `/courses/${courseId}/materials/upload`,
    matForm,
  );

  return response.data;
}
