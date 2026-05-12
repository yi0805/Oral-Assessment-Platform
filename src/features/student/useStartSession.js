import { useQuery } from "@tanstack/react-query";

import { startSession as startSessionApi } from "../../services/apiSession";

export function useStartSession(assessmentConfigId) {
  const {
    data: session,
    isLoading,
    isFetching,
    error,
    refetch,
  } = useQuery({
    queryKey: ["startSession", assessmentConfigId],
    queryFn: () => startSessionApi(assessmentConfigId),
    enabled: !!assessmentConfigId,
    refetchOnWindowFocus: false,
    retry: 1,
    staleTime: Infinity,
    gcTime: 0,
  });

  return { session, isLoading, isFetching, error, refetch };
}
