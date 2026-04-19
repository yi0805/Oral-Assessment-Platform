import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { approveAiSummary } from "../../services/apiSession";

export function useApproveAiGrade() {
  const queryClient = useQueryClient();

  const { mutate: approveAiGrade, isPending } = useMutation({
    mutationFn: ({ sessionId }) => approveAiSummary(sessionId),

    onSuccess: (data) => {
      toast.success(data?.message || "AI grade approved and released.");

      queryClient.invalidateQueries({ queryKey: ["transcript"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["pendingReviews"] });
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to approve AI grade.";

      toast.error(message);
    },
  });

  return { approveAiGrade, isPending };
}
