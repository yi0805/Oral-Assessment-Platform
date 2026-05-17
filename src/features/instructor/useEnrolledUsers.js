import { useQuery } from "@tanstack/react-query";

import { listEnrolledUser } from "../../services/apiCourse";

export function useEnrolledUser(courseId) {
  const {
    data: enrolledUsers = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["enrolledUsers", courseId],
    queryFn: () => listEnrolledUser(courseId),
    enabled: !!courseId,
  });

  return { enrolledUsers, isLoading, isError };
}