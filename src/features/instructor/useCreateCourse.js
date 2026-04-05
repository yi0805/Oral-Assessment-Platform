import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createCourse as createCourseApi } from "../../services/apiCourse";

export function useCreateCourse() {
  const queryClient = useQueryClient();

  const { mutate: createCourse, isPending } = useMutation({
    mutationFn: ({ course_code, course_name, description }) =>
      createCourseApi(course_code, course_name, description),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["courses"] });
    },
    onError: (error) => {
      console.error("Failed to create course:", error);
    },
  });

  return { createCourse, isPending };
}
