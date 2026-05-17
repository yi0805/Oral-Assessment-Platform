import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { deleteEnrolment as deleteEnrolmentApi } from "../../services/apiCourse";

export function useDeleteEnrolment() {
  const queryClient = useQueryClient();

  const { mutate: deleteEnrolment, isPending } = useMutation({
    mutationFn: ({ courseId, upi, role }) => deleteEnrolmentApi(courseId, upi, role),
    onSuccess: (data, { courseId }) => {
      toast.success(data.message || "Enrolment delete successful");

      queryClient.invalidateQueries({ queryKey: ["courses"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["enrolledUsers", courseId] });
    },
    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to delete enrolment.";

      toast.error(message);
    },
  });

  return { deleteEnrolment, isPending };
}