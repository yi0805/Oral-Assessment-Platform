import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { createJoinRequest } from "../../services/apiCourse";

export function useCreateJoinRequest() {
  const queryClient = useQueryClient();

  const { mutate: requestJoin, isPending } = useMutation({
    mutationFn: (courseId) => createJoinRequest(courseId),

    onSuccess: (data) => {
      toast.success(data?.message || "Join request submitted.");
      queryClient.invalidateQueries({ queryKey: ["joinRequests"] });
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to submit join request.";

      toast.error(message);
    },
  });

  return { requestJoin, isPending };
}
