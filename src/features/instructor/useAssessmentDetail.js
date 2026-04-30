import { useQuery } from "@tanstack/react-query";
import { getAssessmentDetail } from "../../services/apiCourse";

export function useAssessmentDetail(courseId, assessmentConfigId) {
  const { data: assessment, isLoading } = useQuery({
    queryKey: ["assessmentDetail", courseId, assessmentConfigId],
    queryFn: () => getAssessmentDetail(courseId, assessmentConfigId),
    enabled: !!(courseId && assessmentConfigId),
  });

  return { assessment, isLoading };
}
