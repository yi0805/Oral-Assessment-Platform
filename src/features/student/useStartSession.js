import { useMutation } from "@tanstack/react-query";
import { startSession as startSessionApi } from "../../services/apiSession";

export function useStartSession() {
  const { mutateAsync: startSession, isPending } = useMutation({
    mutationFn: ({ assessmentConfigId }) => startSessionApi(assessmentConfigId),

    onSuccess: () => {},

    onError: (error) => {
      console.error("Failed to start session:", error);
    },
  });

  return { startSession, isPending };
}
