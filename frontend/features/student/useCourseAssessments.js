import { useQuery } from "@tanstack/react-query";
import { getMyAssessmentSessions } from "../../services/apiSession";

export function useCourseAssessments(courseId) {
  const {
    data: assessments = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["CourseAssessments", courseId],
    queryFn: () => getMyAssessmentSessions(courseId),
    enabled: !!courseId,
  });

  return { assessments, isLoading, isError };
}
