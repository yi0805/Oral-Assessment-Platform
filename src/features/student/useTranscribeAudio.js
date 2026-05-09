import { useMutation } from "@tanstack/react-query";

import { transcribeSessionAudio as transcribeSessionAudioApi } from "../../services/apiSession";

// Issue #71 — Stage 1 of the edit-before-submit flow.
//
// Wraps the transcribe-only API call as a React Query mutation so the UI
// can show a loading indicator (`isPending`) while the backend runs the
// STT pipeline. The mutation resolves to the transcript string; the
// component is responsible for routing it into the answer textarea.
//
// Note: this hook does NOT persist anything. The DB write only happens
// when the student clicks "Submit Answer", via the existing useSubmitAnswer.
export function useTranscribeAudio() {
  const { mutateAsync: transcribeAudio, isPending } = useMutation({
    mutationFn: ({ sessionId, audioBlob }) =>
      transcribeSessionAudioApi(sessionId, audioBlob),
  });

  return { transcribeAudio, isPending };
}
