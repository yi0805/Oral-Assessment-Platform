import { useQuery } from "@tanstack/react-query";
import { getPendingReviews } from "../../services/apiSession";

export function usePendingReviews() {
  const {
    data: pendingReviews = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["pendingReviews"],
    queryFn: getPendingReviews,
  });

  return { pendingReviews, isLoading, isError };
}
