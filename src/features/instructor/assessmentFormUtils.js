export const MAX_QUESTIONS = 50;
export const MAX_TIME_MIN = 120;
export const MAX_BUFFER_MIN = 30;
export const RUBRIC_TOTAL_POINTS = 100;

export function makeBlankRubricRow() {
  return { title: "", description: "", max_points: 0 };
}

export function validateAssessmentName(name) {
  return (name ?? "").trim() === "" ? "Assessment name is required." : "";
}

export function validateNumQuestions(value) {
  if (value === "" || value == null) return "Number of questions is required.";

  const n = Number(value);
  if (!Number.isInteger(n)) return "Must be a whole number.";
  if (n < 1 || n > MAX_QUESTIONS)
    return `Must be between 1 and ${MAX_QUESTIONS}.`;

  return "";
}

export function validateAssessmentTime(value) {
  if (value === "" || value == null) return "Assessment time is required.";

  const t = Number(value);
  if (!Number.isFinite(t)) return "Must be a number.";
  if (t < 1 || t > MAX_TIME_MIN)
    return `Must be between 1 and ${MAX_TIME_MIN}.`;

  return "";
}

export function validateBufferTime(value) {
  // blank/null means no buffer (defaults to 0 on the backend).
  if (value === "" || value == null) return "";

  const t = Number(value);
  if (!Number.isInteger(t)) return "Must be a whole number.";

  if (t < 0 || t > MAX_BUFFER_MIN)
    return `Must be between 0 and ${MAX_BUFFER_MIN}.`;

  return "";
}

export function validateRubricRow(row) {
  return {
    title: row.title.trim() === "" ? "Required." : "",
    description: row.description.trim() === "" ? "Required." : "",
    max_points: !(Number(row.max_points) > 0) ? "Must be greater than 0." : "",
  };
}

export function rubricTotal(rows) {
  return rows.reduce((sum, r) => sum + (Number(r.max_points) || 0), 0);
}

export function isRubricValid(rows) {
  if (rubricTotal(rows) !== RUBRIC_TOTAL_POINTS) return false;

  return rows.every((row) => {
    const errors = validateRubricRow(row);
    return !errors.title && !errors.description && !errors.max_points;
  });
}

export function isAssessmentConfigValid({
  assessmentName,
  numQuestions,
  assessmentTime,
  bufferTime,
}) {
  return (
    !validateAssessmentName(assessmentName) &&
    !validateNumQuestions(numQuestions) &&
    !validateAssessmentTime(assessmentTime) &&
    !validateBufferTime(bufferTime)
  );
}
