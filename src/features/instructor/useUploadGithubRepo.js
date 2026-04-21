import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { uploadGithubRepo as uploadGithubRepoApi } from "../../services/apiMaterial";

export function useUploadGithubRepo() {
  const { mutateAsync: uploadGithubRepo, isPending } = useMutation({
    mutationFn: ({ courseId, url, ref }) =>
      uploadGithubRepoApi(courseId, url, ref),

    onSuccess: (data) => {
      toast.success(data?.message || "GitHub repo imported successfully.");
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to import repository.";

      toast.error(message);
    },
  });

  return { uploadGithubRepo, isPending };
}
