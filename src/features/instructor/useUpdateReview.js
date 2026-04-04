import { useMutation } from "@tanstack/react-query";
import { upsertReview } from "../../services/apiSession";

export function useUpdateReview() {
  const { mutate: updateReview, isPending } = useMutation({
    mutationFn: ({ sessionId, finalGrade, comments }) =>
      upsertReview(sessionId, finalGrade, comments),
    onSuccess: () => {},
    onError: (error) => {
      console.error("Failed to update review:", error);
    },
  });

  return { updateReview, isPending };
}
