import { useMutation, useQueryClient } from "@tanstack/react-query";

import { updateQuestion as updateQuestionApi } from "../../services/apiQuestion";
import toast from "react-hot-toast";

export function useUpdateQuestion() {
  const queryClient = useQueryClient();

  const { mutateAsync: updateQuestion, isPending } = useMutation({
    mutationFn: ({ questionId, questionText }) =>
      updateQuestionApi(questionId, questionText),

    onSuccess: (data, variables) => {
      toast.success(data?.message || "Question updated successfully.");

      if (variables.assessmentConfigId) {
        queryClient.invalidateQueries({
          queryKey: ["questions", variables.assessmentConfigId],
        });
      }
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to update question.";

      toast.error(message);
    },
  });

  return { updateQuestion, isPending };
}