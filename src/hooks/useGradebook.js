import { useContext } from "react";

import { GradebookContext } from "../context/GradebookContext";

export function useGradebook() {
  const ctx = useContext(GradebookContext);
  if (!ctx) {
    throw new Error("useGradebook must be used within GradebookProvider");
  }
  return ctx;
}
