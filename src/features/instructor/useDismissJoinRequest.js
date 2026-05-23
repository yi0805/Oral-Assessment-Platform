import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { dismissJoinRequest } from "../../services/apiCourse";

export function useDismissJoinRequest() {
  const queryClient = useQueryClient();

  const { mutate: dismiss, isPending } = useMutation({
    mutationFn: (requestId) => dismissJoinRequest(requestId),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["joinRequests"] });
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to dismiss join request.";

      toast.error(message);
    },
  });

  return { dismiss, isPending };
}
