import { useMutation } from "@tanstack/react-query";
import { publishAssessment as publishAssessmentApi } from "../../services/apiQuestion";
import toast from "react-hot-toast";

export function usePublishAssessment() {
  const { mutateAsync: publishAssessment, isPending } = useMutation({
    mutationFn: ({ courseId, assessmentConfigId }) =>
      publishAssessmentApi(courseId, assessmentConfigId),
    onSuccess: (data) => {
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
