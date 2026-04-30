import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { updateAssessmentConfig } from "../../services/apiCourse";

export function useUpdateAssessment() {
  const queryClient = useQueryClient();

  const { mutateAsync: updateAssessment, isPending } = useMutation({
    mutationFn: ({ courseId, assessmentConfigId, payload }) =>
      updateAssessmentConfig(courseId, assessmentConfigId, payload),
    onSuccess: (_, { courseId, assessmentConfigId }) => {
      queryClient.invalidateQueries({
        queryKey: ["assessmentDetail", courseId, assessmentConfigId],
      });
      queryClient.invalidateQueries({
        queryKey: ["courseAssessments", courseId],
      });
      toast.success("Assessment updated successfully.");
    },
    onError: () => {
      toast.error("Failed to update assessment.");
    },
  });

  return { updateAssessment, isPending };
}
