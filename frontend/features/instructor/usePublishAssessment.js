import { useMutation } from "@tanstack/react-query";
import { publishAssessment as publishAssessmentApi } from "../../services/apiQuestion";

export function usePublishAssessment() {
  const { mutateAsync: publishAssessment, isPending } = useMutation({
    mutationFn: ({ courseId, assessmentConfigId }) =>
      publishAssessmentApi(courseId, assessmentConfigId),
    onSuccess: () => {},

    onError: (error) => {
      console.error("Failed to publish assessment:", error);
    },
  });

  return { publishAssessment, isPending };
}
