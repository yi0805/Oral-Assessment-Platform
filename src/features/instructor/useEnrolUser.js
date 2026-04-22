import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { enrolUser as enrolUserApi } from "../../services/apiCourse";

export function useEnrolUser() {
  const queryClient = useQueryClient();

  const { mutate: enrolUser, isPending } = useMutation({
    mutationFn: ({ courseId, upi }) => enrolUserApi(courseId, upi),
    onSuccess: (data) => {
      toast.success(data.message || "User enrolment successful");

      queryClient.invalidateQueries({ queryKey: ["courses"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to enrol user.";

      toast.error(message);
    },
  });

  return { enrolUser, isPending };
}
