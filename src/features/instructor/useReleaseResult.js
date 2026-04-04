import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updatePendingReview } from "../../services/apiSession";

export function useReleaseResult() {
  const queryClient = useQueryClient();

  const { mutate: releaseResult, isPending } = useMutation({
    mutationFn: ({ sessionId, studentId }) =>
      updatePendingReview(sessionId, studentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pendingReviews"] });
    },
    onError: (error) => {
      console.error("Failed to release result:", error);
    },
  });

  return { releaseResult, isPending };
}
