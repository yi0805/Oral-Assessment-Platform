export function formatDeadline(isoString) {
  if (!isoString) return null;
  return new Date(isoString).toLocaleString("en-US", {
    month: "long",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}
