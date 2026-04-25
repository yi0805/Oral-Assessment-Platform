import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { updateUserPicture } from "../../services/apiAuth";

export function useUpdatePicture() {
  const queryClient = useQueryClient();

  const { mutate: uploadFile, isPending: isUpdatingPic, isError } = useMutation({
    mutationFn: updateUserPicture,
    onSuccess: (data) => {
      toast.success(data.message || "Picture updated successfully");

      queryClient.invalidateQueries({ queryKey: ["user"] });
    },
    onError: (error) => {
      const message =
        error?.response?.data?.detail ||
        error.message ||
        "Failed to update user full name.";

      toast.error(message);
    },
  });

  return { uploadFile, isUpdatingPic, isError };
}