import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { questionGenerate as questionGenerateApi } from "../../services/apiQuestion";
import { getErrorMessage } from "../../utils/getErrorMessage";

export function useQuestionGenerate() {
  const queryClient = useQueryClient();

  const { mutateAsync: questionGenerate, isPending } = useMutation({
    mutationFn: ({
      courseId,
      materialId,
      rubricId,
      assessmentName,
      numQuestions,
      totalTime,
      releaseTime,
      dueTime,
    }) =>
      questionGenerateApi(
        courseId,
        materialId,
        rubricId,
        assessmentName,
        totalTime,
        numQuestions,
        releaseTime,
        dueTime,
      ),

    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["courseAssessments", variables.courseId],
      });
      toast.success(data?.message || "Create assessment successfully.");
    },

    onError: (error) => {
      toast.error(getErrorMessage(error, "Failed to create assessment."));
    },
  });

  return { questionGenerate, isPending };
}
