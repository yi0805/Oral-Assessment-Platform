import { useQuery } from "@tanstack/react-query";

import { getJoinRequests } from "../../services/apiCourse";

export function useJoinRequests({ enabled = true } = {}) {
  const {
    data = { pending_for_review: [], my_results: [] },
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["joinRequests"],
    queryFn: getJoinRequests,
    enabled,
  });

  return {
    pendingForReview: data.pending_for_review,
    myResults: data.my_results,
    isLoading,
    isError,
  };
}
