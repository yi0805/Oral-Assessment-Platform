import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { uploadRubric as uploadRubricApi } from "../../services/apiRubrics";

export function useUploadRubric() {
  const { mutateAsync: uploadRubric, isPending } = useMutation({
    mutationFn: ({ courseId, file }) => uploadRubricApi(courseId, file),

    onSuccess: (data) => {
      toast.success(data?.message || "Rubric uploaded successfully.");
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to upload rubric.";

      toast.error(message);
    },
  });

  return { uploadRubric, isPending };
}
