import api from "./api";

export async function loginWithGoogle({ accessToken }) {
  const response = await api.post("/auth/google/login", null, {
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

export async function updateUserName(newUsername) {
  const response = await api.put(
    `/users/updateUsername?new_username=${encodeURIComponent(newUsername)}`
  );

  return response.data;
}

export async function updateUserPicture(uploadFile) {
  const formData = new FormData();
  formData.append("file", uploadFile);

  const response = await api.put(
    "/users/updatePicture", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      }
    });

  return response.data;
}