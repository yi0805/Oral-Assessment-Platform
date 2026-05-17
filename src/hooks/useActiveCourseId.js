import { useMatch } from "react-router";

export function useActiveCourseId() {
  const dashboard = useMatch("/instructor/:courseId/dashboard");
  const users = useMatch("/instructor/:courseId/users");
  const assessments = useMatch("/instructor/:courseId/assessments");
  const assessmentEdit = useMatch("/instructor/:courseId/assessments/:assessmentId");
  const assessmentGenerate = useMatch("/instructor/:courseId/assessments/generate");
  return (
    dashboard?.params.courseId ??
    users?.params.courseId ??
    assessments?.params.courseId ??
    assessmentEdit?.params.courseId ??
    assessmentGenerate?.params.courseId ??
    null
  );
}
