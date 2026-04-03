import api from "./api";

export async function getPendingReviews() {
  const response = await api.get("/pendingReviews");
  return response.data;
}
