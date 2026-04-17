import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { questionGenerate as questionGenerateApi } from "../../services/apiQuestion";

export function useQuestionGenerate() {
  const { mutateAsync: questionGenerate, isPending } = useMutation({
    mutationFn: ({
      courseId,
      materialId,
      rubricId,
      assessmentName,
      numQuestions,
      totalTime,
      releaseTime,
      dueTime
    }) =>
      questionGenerateApi(
        courseId,
        materialId,
        rubricId,
        assessmentName,
        totalTime,
        numQuestions,
        releaseTime,
        dueTime
      ),

    onSuccess: (data) => {
      toast.success(data?.message || "Create assessment successfully.");
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to create assessment.";

      toast.error(message);
    },
  });

  return { questionGenerate, isPending };
}
