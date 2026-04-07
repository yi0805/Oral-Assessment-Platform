import { useMutation } from "@tanstack/react-query";
import { updateQuestion as updateQuestionApi } from "../../services/apiQuestion";

export function useUpdateQuestion() {
  const { mutateAsync: updateQuestion, isPending } = useMutation({
    mutationFn: ({ questionId, questionText }) =>
      updateQuestionApi(questionId, questionText),
    onSuccess: () => {},

    onError: (error) => {
      console.error("Failed to update question:", error);
    },
  });

  return { updateQuestion, isPending };
}
