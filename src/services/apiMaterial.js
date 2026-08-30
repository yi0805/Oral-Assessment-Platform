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

export async function uploadGithubRepo(courseId, url, ref) {
  const response = await api.post(
    `/courses/${courseId}/materials/github`,
    { url, ref },
  );

  return response.data;
}

export async function getMaterialStatus(courseId, materialId) {
  const response = await api.get(
    `/courses/${courseId}/materials/${materialId}/status`,
  );
  return response.data;
}

export async function retryMaterialProcessing(courseId, materialId) {
  const response = await api.post(
    `/courses/${courseId}/materials/${materialId}/retry`,
  );
  return response.data;
}
