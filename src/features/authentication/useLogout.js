import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { logoutWithGoogle } from "../../services/apiAuth";

export function useLogout() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const { mutate: logout, isPending } = useMutation({
    mutationFn: logoutWithGoogle,
    onSuccess: () => {
      Object.keys(sessionStorage)
        .filter((key) => key.startsWith("assessment_reentry_"))
        .forEach((key) => sessionStorage.removeItem(key));

      queryClient.removeQueries();
      navigate("/login", { replace: true });
    },
    onError: (error) => {
      console.error("Failed to logout:", error);
    },
  });

  return { logout, isPending };
}
