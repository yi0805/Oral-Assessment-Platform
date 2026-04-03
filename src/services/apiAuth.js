import api from "./api";

export async function loginWithGoogle({ accessToken }) {
  const response = await api.get("/auth/google/login", {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  return response.data;
}

export async function logoutWithGoogle() {
  const response = await api.post("/auth/google/logout");

  return response.data;
}

export async function getCurrentUser() {
  const response = await api.get("/auth/google/me");

  return response.data;
}
