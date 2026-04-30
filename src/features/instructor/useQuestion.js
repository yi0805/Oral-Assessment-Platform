import { useQuery } from "@tanstack/react-query";

import { listQuestions } from "../../services/apiQuestion";

export function useQuestions(assessmentConfigId) {
  const {
    data: questions = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["questions", assessmentConfigId],
    queryFn: () => listQuestions(assessmentConfigId),
    enabled: !!assessmentConfigId,
  });

  return { questions, isLoading, isError };
}