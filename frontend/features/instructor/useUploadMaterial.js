import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { uploadMaterial as uploadMaterialApi } from "../../services/apiMaterial";

export function useUploadMaterial() {
  const { mutateAsync: uploadMaterial, isPending } = useMutation({
    mutationFn: ({ courseId, file }) => uploadMaterialApi(courseId, file),

    onSuccess: (data) => {
      toast.success(data?.message || "Material uploaded successfully.");
    },

    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to upload material.";

      toast.error(message);
    },
  });

  return { uploadMaterial, isPending };
}
