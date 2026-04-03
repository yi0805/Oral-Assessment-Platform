import { useQuery } from "@tanstack/react-query";
import { getCourses } from "../services/apiCourse";

export function useCourses() {
  const {
    data: courses = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["courses"],
    queryFn: getCourses,
  });

  return { courses, isLoading, isError };
}
