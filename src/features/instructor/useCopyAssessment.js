import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { copyAssessmentConfig } from "../../services/apiCourse";

export function useCopyAssessment() {
  const queryClient = useQueryClient();

  const { mutateAsync: copyAssessment, isPending: isCopying } = useMutation({
    mutationFn: ({ courseId, assessmentConfigId, targetCourseId, title }) =>
      copyAssessmentConfig(courseId, assessmentConfigId, targetCourseId, title),

    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["courseAssessments", variables.targetCourseId],
      });
      toast.success(`Assessment copied successfully.`);
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to copy assessment.";
      toast.error(message);
    },
  });

  return { copyAssessment, isCopying };
}
