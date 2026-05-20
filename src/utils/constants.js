export const courseCodeRegex = /^[A-Z]+\s\d+$/;

export const termOptions = ["S1", "S2"];

export function getYearOptions(now = new Date()) {
  const currentYear = now.getFullYear();
  return [currentYear, currentYear + 1];
}

export function getDefaultTerm(now = new Date()) {
  return now.getMonth() + 1 <= 6 ? "S1" : "S2";
}

export function formatTermLabel(term) {
  // "2026S1" -> "2026 S1"
  if (typeof term !== "string" || term.length < 5) return term;
  return `${term.slice(0, 4)} ${term.slice(4)}`;
}

// Groups courses into [{ term, items }]
export function groupCoursesByTerm(courses) {
  const groups = [];
  const seen = new Map();
  for (const course of courses) {
    if (!seen.has(course.term)) {
      const group = { term: course.term, items: [] };
      seen.set(course.term, group);
      groups.push(group);
    }
    seen.get(course.term).items.push(course);
  }
  return groups;
}
