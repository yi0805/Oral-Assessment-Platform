import { useQuery } from "@tanstack/react-query";
import { getAssessmentDetail } from "../../services/apiCourse";

export function useAssessmentDetail(courseId, assessmentConfigId) {
  const {
    data: assessment,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["assessmentDetail", courseId, assessmentConfigId],
    queryFn: () => getAssessmentDetail(courseId, assessmentConfigId),
    enabled: !!(courseId && assessmentConfigId),
    retry: false,
  });

  return { assessment, isLoading, isError };
}
