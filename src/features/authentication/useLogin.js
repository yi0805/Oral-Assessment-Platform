import { useMutation, useQueryClient } from "@tanstack/react-query";

import { loginWithGoogle } from "../../services/apiAuth";
import { useNavigate } from "react-router";

export function useLogin() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { mutate: login, isPending } = useMutation({
    mutationFn: ({ accessToken }) => loginWithGoogle({ accessToken }),

    onSuccess: (data) => {
      queryClient.setQueryData(["user"], data.user);
      navigate("/home");
    },

    onError: (error) => {
      console.error("Failed to get JWT token:", error);
    },
  });

  return { login, isPending };
}
