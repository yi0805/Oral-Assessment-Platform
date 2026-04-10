import { useQuery } from "@tanstack/react-query";
import { getMyAssessmentHistory } from "../../services/apiSession";

export function useAssessmentHistory(courseId) {
  const {
    data: history = null,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["assessmentHistory", courseId],
    queryFn: () => getMyAssessmentHistory(courseId),
    enabled: !!courseId,
  });

  return { history, isLoading, isError };
}
