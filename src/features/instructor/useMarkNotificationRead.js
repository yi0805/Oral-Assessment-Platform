import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { markNotificationRead } from "../../services/apiSession";

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();

  const { mutate: markRead, isPending } = useMutation({
    mutationFn: (notificationId) => markNotificationRead(notificationId),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to mark notification as read.";

      toast.error(message);
    },
  });

  return { markRead, isPending };
}
