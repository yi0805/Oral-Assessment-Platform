import { useQuery } from "@tanstack/react-query";
import { getDashboard } from "../../services/apiCourse";

export function useDashboard(courseId) {
  const {
    data: dashboard,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["dashboard", courseId],
    queryFn: () => getDashboard(courseId),
    enabled: !!courseId,
  });

  return { dashboard, isLoading, isError };
}
