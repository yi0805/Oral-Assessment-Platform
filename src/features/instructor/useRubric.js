import { useQuery } from "@tanstack/react-query";

import { getRubric } from "../../services/apiRubrics";

export function useRubric(assessmentConfigId) {
  const {
    data: rubric,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["rubric", assessmentConfigId],
    queryFn: () => getRubric(assessmentConfigId),
    enabled: !!assessmentConfigId,
  });

  return { rubric, isLoading, isError };
}