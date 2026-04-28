import { useMutation } from "@tanstack/react-query";

import { respondSessionAudio as respondSessionAudioApi } from "../../services/apiSession";

export function useSubmitAudioAnswer() {
  const { mutateAsync: submitAudioAnswer, isPending } = useMutation({
    mutationFn: ({ sessionId, audioBlob }) =>
      respondSessionAudioApi(sessionId, audioBlob),
  });

  return { submitAudioAnswer, isPending };
}
