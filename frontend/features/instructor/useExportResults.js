import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { exportResultsCSV } from "../../services/apiCourse";

export function useExportResults() {
  const { mutate: exportResults, isPending } = useMutation({
    mutationFn: ({ courseId, assessmentConfigId }) =>
      exportResultsCSV(courseId, assessmentConfigId),
    onSuccess: (response) => {
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;

      const disposition = response.headers["content-disposition"] || "";
      const filenameMatch = disposition.match(/filename=(.+)/);
      link.setAttribute(
        "download",
        filenameMatch ? filenameMatch[1] : "results.csv",
      );

      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success("Results exported successfully.");
    },
    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to export results.";

      toast.error(message);
    },
  });

  return { exportResults, isPending };
}
