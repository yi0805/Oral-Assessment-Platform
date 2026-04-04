import { useMutation } from "@tanstack/react-query";
import { updateReviewGrade } from "../../services/apiSession";

export function useGrading() {
  const { mutate: updateGrade, isPending } = useMutation({
    mutationFn: ({ sessionId, grade }) => updateReviewGrade(sessionId, grade),
    onSuccess: () => {},
    onError: (error) => {
      console.error("Failed to update review grade:", error);
    },
  });

  return { updateGrade, isPending };
}
