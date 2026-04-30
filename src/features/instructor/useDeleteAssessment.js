import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { deleteAssessmentConfig } from "../../services/apiCourse";

export function useDeleteAssessment() {
  const queryClient = useQueryClient();

  const { mutateAsync: deleteAssessment, isPending: isDeleting } = useMutation({
    mutationFn: ({ courseId, assessmentConfigId }) =>
      deleteAssessmentConfig(courseId, assessmentConfigId),

    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["courseAssessments", variables.courseId] });
      toast.success(data?.message || "Assessment deleted successfully.");
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to delete assessment.";
      toast.error(message);
    },
  });

  return { deleteAssessment, isDeleting };
}
