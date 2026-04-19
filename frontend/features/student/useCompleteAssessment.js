import { useMutation, useQueryClient } from "@tanstack/react-query";

import { completeSession as completeSessionApi } from "../../services/apiSession";

export function useCompleteAssessment() {
  const queryClient = useQueryClient();

  const { mutateAsync: completeAssessment, isPending } = useMutation({
    mutationFn: ({ sessionId }) => completeSessionApi(sessionId),

    onSuccess: (_data, { courseId }) => {
      queryClient.invalidateQueries({
        queryKey: ["CourseAssessments", courseId],
      });
    },
  });

  return { completeAssessment, isPending };
}
