import { useQuery } from "@tanstack/react-query";

import { getJoinRequests } from "../../services/apiCourse";

export function useJoinRequests({ enabled = true } = {}) {
  const {
    data = { pending_for_review: [], my_pending: [], my_results: [] },
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["joinRequests"],
    queryFn: getJoinRequests,
    enabled,
  });

  return {
    pendingForReview: data.pending_for_review,
    myPending: data.my_pending,
    myResults: data.my_results,
    isLoading,
    isError,
  };
}
