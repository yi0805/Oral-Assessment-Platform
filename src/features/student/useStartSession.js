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
    queryFn: async () => {
      const markerKey = `assessment_reentry_${assessmentConfigId}`;
      const isReentry = !sessionStorage.getItem(markerKey);

      const data = await startSessionApi(assessmentConfigId, isReentry);
      sessionStorage.setItem(markerKey, "1");
      return data;
    },
    enabled: !!assessmentConfigId,
    refetchOnWindowFocus: false,
    retry: 1,
    staleTime: Infinity,
    gcTime: 0,
  });

  return { session, isLoading, isFetching, error, refetch };
}
