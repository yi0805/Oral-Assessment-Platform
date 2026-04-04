import { useQuery } from "@tanstack/react-query";
import { getTranscript } from "../../services/apiSession";

export function useTranscript(sessionId) {
  const {
    data: transcript,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["transcript", sessionId],
    queryFn: () => getTranscript(sessionId),
    enabled: !!sessionId,
  });

  return { transcript, isLoading, isError };
}
