import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { unpublishGrade } from "../../services/apiSession";

export function useUnpublish() {
  const queryClient = useQueryClient();

  const { mutate: unpublish, isPending } = useMutation({
    mutationFn: ({ sessionId, studentId }) =>
      unpublishGrade(sessionId, studentId),

    onSuccess: (data) => {
      toast.success(data?.message || "Result unpublished successfully.");

      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["pendingReviews"] });
      queryClient.invalidateQueries({ queryKey: ["transcript"] });
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to unpublish result.";

      toast.error(message);
    },
  });

  return { unpublish, isPending };
}
