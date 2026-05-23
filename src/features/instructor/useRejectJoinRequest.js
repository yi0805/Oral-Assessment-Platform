import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { rejectJoinRequest } from "../../services/apiCourse";

export function useRejectJoinRequest() {
  const queryClient = useQueryClient();

  const { mutate: reject, isPending } = useMutation({
    mutationFn: (requestId) => rejectJoinRequest(requestId),

    onSuccess: (data) => {
      toast.success(data?.message || "Join request rejected.");
      queryClient.invalidateQueries({ queryKey: ["joinRequests"] });
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to reject join request.";

      toast.error(message);
    },
  });

  return { reject, isPending };
}
