import { useMutation } from "@tanstack/react-query";
import { deleteQuestion as deleteQuestionApi } from "../../services/apiQuestion";

export function useDeleteQuestion() {
  const { mutateAsync: deleteQuestion, isPending } = useMutation({
    mutationFn: ({ questionId }) => deleteQuestionApi(questionId),
    onSuccess: () => {},

    onError: (error) => {
      console.error("Failed to delete question:", error);
    },
  });

  return { deleteQuestion, isPending };
}
