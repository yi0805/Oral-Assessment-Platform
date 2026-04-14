import { useMutation } from "@tanstack/react-query";
import { questionGenerate as questionGenerateApi } from "../../services/apiQuestion";
import toast from "react-hot-toast";

export function useQuestionGenerate() {
  const { mutateAsync: questionGenerate, isPending } = useMutation({
    mutationFn: ({
      courseId,
      materialId,
      rubricId,
      assessmentName,
      numQuestions,
      totalTime,
    }) =>
      questionGenerateApi(
        courseId,
        materialId,
        rubricId,
        assessmentName,
        totalTime,
        numQuestions,
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
