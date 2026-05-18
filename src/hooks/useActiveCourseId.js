import { useMatch } from "react-router";

export function useActiveCourseId() {
  const dashboard = useMatch("/instructor/:courseId/dashboard");
  const users = useMatch("/instructor/:courseId/users");
  const assessments = useMatch("/instructor/:courseId/assessments");
  const assessmentEdit = useMatch("/instructor/:courseId/assessments/:assessmentId");
  const assessmentGenerate = useMatch("/instructor/:courseId/assessments/generate");

  const studentRoot = useMatch("/student/:courseId");
  const studentAssessments = useMatch("/student/:courseId/assessments");
  const studentGraded = useMatch("/student/:courseId/gradedAssessments");

  return (
    dashboard?.params.courseId ??
    users?.params.courseId ??
    assessments?.params.courseId ??
    assessmentEdit?.params.courseId ??
    assessmentGenerate?.params.courseId ??
    studentAssessments?.params.courseId ??
    studentGraded?.params.courseId ??
    studentRoot?.params.courseId ??
    null
  );
}
