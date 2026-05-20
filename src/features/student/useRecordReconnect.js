import { useMutation } from "@tanstack/react-query";

import { recordReconnectNotification as recordReconnectNotificationApi } from "../../services/apiSession";

export function useRecordReconnect() {
  const { mutateAsync: recordReconnectNotification, isPending } = useMutation({
    mutationFn: ({ sessionId, disconnectCount }) =>
      recordReconnectNotificationApi(sessionId, disconnectCount),
  });

  return { recordReconnectNotification, isPending };
}
