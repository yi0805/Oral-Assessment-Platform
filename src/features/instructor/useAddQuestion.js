import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { addQuestion as addQuestionApi } from "../../services/apiQuestion";

export function useAddQuestion() {
  const queryClient = useQueryClient();

  const { mutateAsync: addQuestion, isPending } = useMutation({
    mutationFn: ({ assessmentConfigId, questionText }) =>
      addQuestionApi(assessmentConfigId, questionText),

    onSuccess: (_data, variables) => {
      toast.success("Question added successfully.");

      queryClient.invalidateQueries({
        queryKey: ["questions", variables.assessmentConfigId],
      });
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to add question.";

      toast.error(message);
    },
  });

  return { addQuestion, isPending };
}