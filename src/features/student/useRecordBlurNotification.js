import { useMutation } from "@tanstack/react-query";

import { recordBlurNotification as recordBlurNotificationApi } from "../../services/apiSession";

export function useRecordBlurNotification() {
  const { mutateAsync: recordBlurNotification, isPending } = useMutation({
    mutationFn: ({ sessionId, blurCount }) =>
      recordBlurNotificationApi(sessionId, blurCount),
  });

  return { recordBlurNotification, isPending };
}
