import { useMutation } from "@tanstack/react-query";
import { respondSession as respondSessionApi } from "../../services/apiSession";

export function useSubmitAnswer() {
  const { mutateAsync: submitAnswer, isPending } = useMutation({
    mutationFn: ({ sessionId, answer }) => respondSessionApi(sessionId, answer),

    onSuccess: () => {},

    onError: (error) => {
      console.error("Failed to submit answer:", error);
    },
  });

  return { submitAnswer, isPending };
}
