import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { markAllNotificationsRead } from "../../services/apiSession";

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();

  const { mutate: markAllRead, isPending } = useMutation({
    mutationFn: markAllNotificationsRead,

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to mark notifications as read.";

      toast.error(message);
    },
  });

  return { markAllRead, isPending };
}
