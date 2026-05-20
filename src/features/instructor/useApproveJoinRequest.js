import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { approveJoinRequest } from "../../services/apiCourse";

export function useApproveJoinRequest() {
  const queryClient = useQueryClient();

  const { mutate: approve, isPending } = useMutation({
    mutationFn: (requestId) => approveJoinRequest(requestId),

    onSuccess: (data) => {
      toast.success(data?.message || "Join request approved.");
      queryClient.invalidateQueries({ queryKey: ["joinRequests"] });
      queryClient.invalidateQueries({ queryKey: ["courses"] });
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to approve join request.";

      toast.error(message);
    },
  });

  return { approve, isPending };
}
