import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateAllPendingReviews } from "../../services/apiSession";

export function useReleaseAllResults() {
  const queryClient = useQueryClient();

  const { mutate: releaseAllResults, isPending } = useMutation({
    mutationFn: ({ assessments }) => updateAllPendingReviews(assessments),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pendingReviews"] });
    },
    onError: (error) => {
      console.error("Failed to release all results:", error);
    },
  });

  return { releaseAllResults, isPending };
}
