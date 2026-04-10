import { useMutation } from "@tanstack/react-query";
import { uploadMaterial as uploadMaterialApi } from "../../services/apiMaterial";

export function useUploadMaterial() {
  const { mutateAsync: uploadMaterial, isPending } = useMutation({
    mutationFn: ({ courseId, file, assessmentName }) =>
      uploadMaterialApi(courseId, file, assessmentName),

    onSuccess: () => {},

    onError: (error) => {
      console.error("Failed to upload material:", error);
    },
  });

  return { uploadMaterial, isPending };
}
