import { useMatch } from "react-router";

export function useActiveCourseId() {
  return useMatch("/instructor/:courseId/*")?.params.courseId ?? null;
}
