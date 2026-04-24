import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { updateUserName } from "../../services/apiAuth";

export function useUpdateName() {
  const queryClient = useQueryClient();

  const { mutate: updateName, isPending, isError } = useMutation({
    mutationFn: updateUserName,
    onSuccess: (data) => {
      toast.success(data.message || "Name updated successfully");

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

  return { updateName, isPending, isError };
}