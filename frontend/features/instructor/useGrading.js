import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { updateReviewGrade } from "../../services/apiSession";

export function useGrading() {
  const { mutate: updateGrade, isPending } = useMutation({
    mutationFn: ({ sessionId, grade }) => updateReviewGrade(sessionId, grade),
    onSuccess: (data) => {
      toast.success(data?.message || "Grade updated successfully.");
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to update grade.";

      toast.error(message);
    },
  });

  return { updateGrade, isPending };
}
