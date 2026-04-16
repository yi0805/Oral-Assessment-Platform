import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { importStudentsCSV } from "../../services/apiCourse";

export function useImportStudents() {
  const queryClient = useQueryClient();

  const { mutate: importStudents, isPending } = useMutation({
    mutationFn: ({ courseId, file }) => importStudentsCSV(courseId, file),
    onSuccess: (data) => {
      toast.success(`${data.newly_enrolled} student(s) newly enrolled.`);

      queryClient.invalidateQueries({ queryKey: ["courses"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to import students.";

      toast.error(message);
    },
  });

  return { importStudents, isPending };
}
