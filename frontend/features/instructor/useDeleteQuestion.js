import { useMutation } from "@tanstack/react-query";
import { deleteQuestion as deleteQuestionApi } from "../../services/apiQuestion";
import toast from "react-hot-toast";

export function useDeleteQuestion() {
  const { mutateAsync: deleteQuestion, isPending } = useMutation({
    mutationFn: ({ questionId }) => deleteQuestionApi(questionId),

    onSuccess: (data) => {
      toast.success(data?.message || "Question deleted successfully.");
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to update question.";

      toast.error(message);
    },
  });

  return { deleteQuestion, isPending };
}
