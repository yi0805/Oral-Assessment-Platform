import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { approveAllAiSummaries } from "../../services/apiSession";

export function useApproveAllAiGrades() {
  const queryClient = useQueryClient();

  const { mutate: approveAllAiGrades, isPending } = useMutation({
    mutationFn: ({ assessments }) => approveAllAiSummaries(assessments),

    onSuccess: (data) => {
      toast.success(data?.message || "All AI grades approved successfully.");

      queryClient.invalidateQueries({ queryKey: ["pendingReviews"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["transcript"] });
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to approve all AI grades.";

      toast.error(message);
    },
  });

  return { approveAllAiGrades, isPending };
}
