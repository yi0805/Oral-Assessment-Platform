export async function loginWithGoogle({ accessToken }) {
  const response = await fetch(
    "http://localhost:8000/api/v1/auth/google/login",
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      credentials: "include",
    },
  );

  if (!response.ok) {
    throw new Error("Failed to get JWT token");
  }

  return response.json();
}

export async function logoutWithGoogle() {
  const response = await fetch(
    "http://localhost:8000/api/v1/auth/google/logout",
    {
      method: "POST",
      credentials: "include",
    },
  );

  if (!response.ok) {
    throw new Error("Failed to logout");
  }

  return response.json();
}

export async function getCurrentUser() {
  const response = await fetch("http://localhost:8000/api/v1/auth/google/me", {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Failed to get user info");
  }

  return response.json();
}
