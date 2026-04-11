import { useMutation } from "@tanstack/react-query";
import { uploadRubric as uploadRubricApi } from "../../services/apiRubrics";

export function useUploadRubric() {
  const { mutateAsync: uploadRubric, isPending } = useMutation({
    mutationFn: ({ courseId, file }) => uploadRubricApi(courseId, file),

    onSuccess: () => {},

    onError: (error) => {
      console.error("Failed to upload rubric:", error);
    },
  });

  return { uploadRubric, isPending };
}
