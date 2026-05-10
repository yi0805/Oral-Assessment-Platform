import { useMatch } from "react-router";

export function useActiveCourseId() {
  const dashboard = useMatch("/instructor/:courseId/dashboard");
  const users = useMatch("/instructor/:courseId/users");
  const assessments = useMatch("/instructor/:courseId/assessments");
  return (
    dashboard?.params.courseId ??
    users?.params.courseId ??
    assessments?.params.courseId ??
    null
  );
}
