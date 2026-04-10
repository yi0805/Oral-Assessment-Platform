import { useMutation } from "@tanstack/react-query";
import { completeSession as completeSessionApi } from "../../services/apiSession";

export function useCompleteAssessment() {
  const { mutateAsync: completeAssessment, isPending } = useMutation({
    mutationFn: ({ sessionId }) => completeSessionApi(sessionId),

    onSuccess: () => {},

    onError: (error) => {
      console.error("Failed to complete assessment:", error);
    },
  });

  return { completeAssessment, isPending };
}
