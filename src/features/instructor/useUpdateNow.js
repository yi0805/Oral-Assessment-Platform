import { useMutation } from "@tanstack/react-query";
import { updateNow as updateNowApi } from "../../services/apiQuestion";
import toast from "react-hot-toast";

export function useUpdateNow() {
  const { mutateAsync: updateNow, isPending } = useMutation({
    mutationFn: ({
      courseId,
      materialId,
      rubricId,
      assessmentName,
      numQuestions,
      totalTime,
    }) =>
      updateNowApi(
        courseId,
        materialId,
        rubricId,
        assessmentName,
        numQuestions,
        totalTime,
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

  return { updateNow, isPending };
}
