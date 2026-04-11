import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { createCourse as createCourseApi } from "../../services/apiCourse";

export function useCreateCourse() {
  const queryClient = useQueryClient();

  const { mutate: createCourse, isPending } = useMutation({
    mutationFn: ({ course_code, course_name, description }) =>
      createCourseApi(course_code, course_name, description),
    onSuccess: (data) => {
      toast.success(data?.message || "Course created successfully.");
      queryClient.invalidateQueries({ queryKey: ["courses"] });
    },
    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to create course.";

      toast.error(message);
    },
  });

  return { createCourse, isPending };
}
