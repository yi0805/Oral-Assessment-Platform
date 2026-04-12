import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateAllPendingReviews } from "../../services/apiSession";
import toast from "react-hot-toast";

export function useReleaseAllResults() {
  const queryClient = useQueryClient();

  const { mutate: releaseAllResults, isPending } = useMutation({
    mutationFn: ({ assessments }) => updateAllPendingReviews(assessments),
    onSuccess: (data) => {
      toast.success(data?.message || "All results released successfully.");

      queryClient.invalidateQueries({ queryKey: ["pendingReviews"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to release all results.";

      toast.error(message);
    },
  });

  return { releaseAllResults, isPending };
}
