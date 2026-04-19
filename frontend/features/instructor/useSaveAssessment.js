import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { saveAssessment as saveAssessmentApi } from "../../services/apiQuestion";

export function useSaveAssessment() {
  const { mutateAsync: saveAssessment, isPending } = useMutation({
    mutationFn: ({ courseId, assessmentConfigId }) =>
      saveAssessmentApi(courseId, assessmentConfigId),

    onSuccess: (data) => {
      toast.success(data?.message || "Assessment saved successfully.");
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to save assessment as draft.";

      toast.error(message);
    },
  });

  return { saveAssessment, isPending };
}