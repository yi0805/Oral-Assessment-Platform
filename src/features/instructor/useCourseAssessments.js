import { useQuery } from "@tanstack/react-query";
import { getCourseAssessments } from "../../services/apiCourse";

export function useCourseAssessments(courseId) {
  const { data: assessments = [], isLoading } = useQuery({
    queryKey: ["courseAssessments", courseId],
    queryFn: () => getCourseAssessments(courseId),
    enabled: !!courseId,
  });

  return { assessments, isLoading };
}
