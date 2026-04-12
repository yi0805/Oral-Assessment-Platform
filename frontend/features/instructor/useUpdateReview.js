import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { upsertReview } from "../../services/apiSession";

export function useUpdateReview() {
  const queryClient = useQueryClient();

  const { mutate: updateReview, isPending } = useMutation({
    mutationFn: ({ sessionId, finalGrade, comments }) =>
      upsertReview(sessionId, finalGrade, comments),
    onSuccess: (data) => {
      toast.success(data?.message || "Review updated successfully.");

      queryClient.invalidateQueries({ queryKey: ["transcript"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["pendingReviews"] });
      toast.success("Review updated successfully!");
    },
    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to update review.";

      toast.error(message);
    },
  });

  return { updateReview, isPending };
}
