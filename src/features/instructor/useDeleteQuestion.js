import { useMutation, useQueryClient } from "@tanstack/react-query";
import { deleteQuestion as deleteQuestionApi } from "../../services/apiQuestion";
import toast from "react-hot-toast";

export function useDeleteQuestion() {
  const queryClient = useQueryClient();

  const { mutateAsync: deleteQuestion, isPending } = useMutation({
    mutationFn: ({ questionId }) => deleteQuestionApi(questionId),

    onSuccess: (data, variables) => {
      toast.success(data?.message || "Question deleted successfully.");

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
        "Failed to delete question.";

      toast.error(message);
    },
  });

  return { deleteQuestion, isPending };
}