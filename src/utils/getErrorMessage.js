export function getErrorMessage(err, fallback = "Something went wrong.") {
  return err?.response?.data?.detail || err?.message || fallback;
}
