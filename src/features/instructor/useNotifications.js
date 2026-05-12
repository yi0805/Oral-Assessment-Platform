import { useQuery } from "@tanstack/react-query";

import { getNotifications } from "../../services/apiSession";

export function useNotifications({ enabled = true } = {}) {
  const {
    data: notifications = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["notifications"],
    queryFn: getNotifications,
    enabled,
  });

  return { notifications, isLoading, isError };
}
