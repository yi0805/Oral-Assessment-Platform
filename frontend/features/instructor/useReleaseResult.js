import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { updatePendingReview } from "../../services/apiSession";

export function useReleaseResult() {
  const queryClient = useQueryClient();

  const { mutate: releaseResult, isPending } = useMutation({
    mutationFn: ({ sessionId, studentId }) =>
      updatePendingReview(sessionId, studentId),
    onSuccess: (data) => {
      toast.success(data?.message || "Result released successfully.");
      queryClient.invalidateQueries({ queryKey: ["pendingReviews"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to release result.";

      toast.error(message);
    },
  });

  return { releaseResult, isPending };
}
