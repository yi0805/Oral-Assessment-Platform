import { useState } from "react";

import DateTimePicker from "../../ui/DateTimePicker";
import {
  MAX_QUESTIONS,
  MAX_TIME_MIN,
  validateAssessmentName,
  validateAssessmentTime,
  validateNumQuestions,
} from "./assessmentFormUtils";

export default function AssessmentConfigForm({
  courses,
  courseId,
  onCourseIdChange,
  assessmentName,
  onAssessmentNameChange,
  numQuestions,
  onNumQuestionsChange,
  assessmentTime,
  onAssessmentTimeChange,
  releaseTime,
  onReleaseTimeChange,
  dueTime,
  onDueTimeChange,
  disabled = false,
  disableCourseSelect = false,
  onlyDueDate = false,
  releaseHelperText = "Leave blank to default to now → 30 days from now.",
}) {
  const [touched, setTouched] = useState({
    assessmentName: false,
    numQuestions: false,
    assessmentTime: false,
  });

  const assessmentNameError = validateAssessmentName(assessmentName);
  const numQuestionsError = validateNumQuestions(numQuestions);
  const assessmentTimeError = validateAssessmentTime(assessmentTime);

  function markTouched(field) {
    setTouched((current) => ({ ...current, [field]: true }));
  }

  return (
    <section className="rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
      <h2 className="mb-6 flex items-center gap-2 text-xl font-bold">
        <span
          className="material-symbols-outlined text-primary"
          data-icon="description"
          style={{ verticalAlign: "middle" }}
        >
          description
        </span>
        Assessment Parameters
      </h2>

      <form className="space-y-6">
        <div className="space-y-2">
          <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
            Select Course
          </label>

          <div className="group relative">
            <select
              className="w-full cursor-pointer appearance-none rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
              value={courseId}
              disabled={disableCourseSelect}
              onChange={(e) => onCourseIdChange(e.target.value)}
            >
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.course_code || "Unknown Course"}
                </option>
              ))}
            </select>

            <span
              className="material-symbols-outlined pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-on-surface-variant"
              data-icon="expand_more"
              style={{ verticalAlign: "middle" }}
            >
              expand_more
            </span>
          </div>
        </div>

        <div className="space-y-2">
          <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
            Assessment Name
          </label>

          <input
            className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all placeholder:text-outline focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
            placeholder="e.g. A1 Intro to Python"
            type="text"
            value={assessmentName}
            disabled={disabled || onlyDueDate}
            onChange={(e) => onAssessmentNameChange(e.target.value)}
            onBlur={() => markTouched("assessmentName")}
          />

          {touched.assessmentName && assessmentNameError && (
            <p className="ml-1 text-xs font-medium text-error">
              {assessmentNameError}
            </p>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
              Number of Questions
            </label>

            <input
              className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all placeholder:text-outline focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
              min={1}
              max={MAX_QUESTIONS}
              step={1}
              placeholder="e.g. 15"
              type="number"
              value={numQuestions}
              disabled={disabled || onlyDueDate}
              onChange={(e) => onNumQuestionsChange(e.target.value)}
              onBlur={() => markTouched("numQuestions")}
            />

            {touched.numQuestions && numQuestionsError && (
              <p className="ml-1 text-xs font-medium text-error">
                {numQuestionsError}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
              Total Timer (mins)
            </label>

            <input
              className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all placeholder:text-outline focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
              min={1}
              max={MAX_TIME_MIN}
              step={0.5}
              placeholder="e.g. 30"
              type="number"
              value={assessmentTime}
              disabled={disabled || onlyDueDate}
              onChange={(e) => onAssessmentTimeChange(e.target.value)}
              onBlur={() => markTouched("assessmentTime")}
            />

            {touched.assessmentTime && assessmentTimeError && (
              <p className="ml-1 text-xs font-medium text-error">
                {assessmentTimeError}
              </p>
            )}
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="grid grid-cols-2 gap-4">
            <DateTimePicker
              label="Release Date"
              value={releaseTime}
              onChange={onReleaseTimeChange}
              disabled={disabled || onlyDueDate}
            />

            <DateTimePicker
              label="Due date"
              value={dueTime}
              onChange={onDueTimeChange}
              minDate={releaseTime}
              disabled={disabled}
            />
          </div>

          {releaseHelperText && (
            <p className="ml-1 text-[11px] text-outline">{releaseHelperText}</p>
          )}
        </div>
      </form>
    </section>
  );
}
