import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { createRubric as createRubricApi } from "../../services/apiRubrics";

export function useCreateRubric() {
  const { mutateAsync: createRubric, isPending } = useMutation({
    mutationFn: ({ courseId, rubricPayload }) => createRubricApi(courseId, rubricPayload),

    onSuccess: (data) => {
      toast.success(data?.message || "Rubric saved successfully.");
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to create rubric.";

      toast.error(message);
    },
  });

  return { createRubric, isPending };
}
