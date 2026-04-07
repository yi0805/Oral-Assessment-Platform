import { useMutation } from "@tanstack/react-query";
import { updateNow as updateNowApi } from "../../services/apiQuestion";

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

    onSuccess: () => {},

    onError: (error) => {
      console.error("Failed to update now:", error);
    },
  });

  return { updateNow, isPending };
}
