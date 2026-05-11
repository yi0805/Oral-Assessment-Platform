export function getErrorMessage(err, fallback = "Something went wrong.") {
  const detail = err?.response?.data?.detail;

  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const field = Array.isArray(d?.loc) ? d.loc.slice(1).join(".") : "";
        return field
          ? `${field}: ${d?.msg ?? "invalid"}`
          : (d?.msg ?? "invalid");
      })
      .join("; ");
  }

  return detail || err?.message || fallback;
}
