import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { publishAssessment as publishAssessmentApi } from "../../services/apiQuestion";

export function usePublishAssessment() {
  const queryClient = useQueryClient();

  const { mutateAsync: publishAssessment, isPending } = useMutation({
    mutationFn: ({ courseId, assessmentConfigId }) =>
      publishAssessmentApi(courseId, assessmentConfigId),

    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["courseAssessments", variables.courseId] });
      queryClient.invalidateQueries({ queryKey: ["assessmentDetail", variables.courseId, variables.assessmentConfigId] });
      toast.success(data?.message || "Assessment published successfully.");
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to publish assessment.";

      toast.error(message);
    },
  });

  return { publishAssessment, isPending };
}
