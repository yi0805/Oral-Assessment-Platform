import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { updateRubric as updateRubricApi } from "../../services/apiRubrics";

export function useUpdateRubric() {
  const queryClient = useQueryClient();

  const { mutateAsync: updateRubric, isPending } = useMutation({
    mutationFn: ({ assessmentConfigId, rubricPayload }) =>
      updateRubricApi(assessmentConfigId, rubricPayload),

    onSuccess: (data, variables) => {
      toast.success("Rubric updated successfully.");

      queryClient.invalidateQueries({
        queryKey: ["rubric", variables.assessmentConfigId],
      });
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to update rubric.";

      toast.error(message);
    },
  });

  return { updateRubric, isPending };
}