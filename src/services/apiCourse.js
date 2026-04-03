import api from "./api";

export async function getCourses() {
  const response = await api.get("/courses");
  return response.data;
}
