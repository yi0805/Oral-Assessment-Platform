import { useMutation, useQueryClient } from "@tanstack/react-query";

import { upsertReview } from "../../services/apiSession";

export function useUpdateReview() {
  const queryClient = useQueryClient();

  const { mutate: updateReview, isPending } = useMutation({
    mutationFn: ({ sessionId, finalGrade, comments }) =>
      upsertReview(sessionId, finalGrade, comments),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transcript"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["pendingReviews"] });
    },
    onError: (error) => {
      console.error("Failed to update review:", error);
    },
  });

  return { updateReview, isPending };
}
