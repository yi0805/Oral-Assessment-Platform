import { useState } from "react";

import {
  RUBRIC_TOTAL_POINTS,
  makeBlankRubricRow,
  rubricTotal,
  validateRubricRow,
} from "./assessmentFormUtils";

export default function RubricEditor({ rows, onRowsChange, disabled = false }) {
  const [touched, setTouched] = useState(false);

  const totalPoints = rubricTotal(rows);
  const totalPointsValid = totalPoints === RUBRIC_TOTAL_POINTS;

  const rowErrors = rows.map(validateRubricRow);

  function markTouched() {
    setTouched(true);
  }

  function handleAddRow() {
    if (disabled) return;

    onRowsChange([...rows, makeBlankRubricRow()]);
  }

  function handleRemoveRow(index) {
    if (disabled || rows.length === 1) return;

    onRowsChange(rows.filter((_, i) => i !== index));
  }

  function handleRowChange(index, field, value) {
    if (disabled) return;

    const updatedRows = rows.map((row, i) => {
      if (i !== index) return row;

      if (field === "max_points") {
        if (value === "") return { ...row, max_points: 0 };

        const numericValue = parseInt(value, 10);
        if (!Number.isFinite(numericValue)) return row;

        return { ...row, max_points: Math.max(0, numericValue) };
      }

      return { ...row, [field]: value };
    });

    onRowsChange(updatedRows);
  }

  return (
    <section className="rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
      <div className="mb-8 flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <span
              className="material-symbols-outlined text-xl"
              data-icon="assignment"
              style={{ verticalAlign: "middle" }}
            >
              assignment
            </span>
          </div>

          <div>
            <h2 className="text-xl font-bold text-on-surface">
              Grading Rubric
            </h2>

            <p className="mt-1 max-w-md text-xs text-on-surface-variant">
              Define how the AI evaluates responses. Each criterion&apos;s
              points act as its percentage weight — must total{" "}
              {RUBRIC_TOTAL_POINTS}.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-5 rounded-xl border border-outline-variant/10 bg-surface-container-low px-5 py-3">
          <div className="flex items-baseline gap-1">
            <span
              className={`font-headline text-3xl font-extrabold leading-none tracking-tight ${
                totalPointsValid
                  ? "text-primary"
                  : totalPoints > RUBRIC_TOTAL_POINTS
                    ? "text-error"
                    : "text-on-surface"
              }`}
            >
              {totalPoints}
            </span>

            <span className="text-sm font-bold text-outline">
              / {RUBRIC_TOTAL_POINTS}
            </span>
          </div>

          <div className="h-9 w-px bg-outline-variant/30" />

          <div className="min-w-[132px]">
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-container-high">
              <div
                className={`h-full rounded-full transition-all duration-300 ${
                  totalPointsValid
                    ? "bg-primary"
                    : totalPoints > RUBRIC_TOTAL_POINTS
                      ? "bg-error"
                      : "bg-primary/50"
                }`}
                style={{
                  width: `${Math.min(
                    100,
                    (totalPoints / RUBRIC_TOTAL_POINTS) * 100,
                  )}%`,
                }}
              />
            </div>

            <p
              className={`mt-1.5 text-[10px] font-bold uppercase tracking-widest ${
                totalPointsValid
                  ? "text-primary"
                  : totalPoints > RUBRIC_TOTAL_POINTS
                    ? "text-error"
                    : "text-on-surface-variant"
              }`}
            >
              {totalPointsValid
                ? "Ready"
                : totalPoints > RUBRIC_TOTAL_POINTS
                  ? `${totalPoints - RUBRIC_TOTAL_POINTS} over`
                  : `${RUBRIC_TOTAL_POINTS - totalPoints} remaining`}
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {rows.map((row, index) => {
          const errors = rowErrors[index];
          const showErrors = touched;
          const hasAnyError =
            showErrors &&
            (errors.title || errors.description || errors.max_points);

          return (
            <div
              key={index}
              className={`group relative rounded-xl border p-5 transition-all ${
                hasAnyError
                  ? "border-error/30 bg-error/[0.02]"
                  : "border-outline-variant/15 hover:border-outline-variant/40"
              }`}
            >
              <div className="flex items-start gap-4">
                <div className="mt-1 flex shrink-0 flex-col items-center gap-1">
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 font-headline text-sm font-bold text-primary">
                    {String(index + 1).padStart(2, "0")}
                  </span>

                  {!disabled && (
                    <button
                      type="button"
                      onClick={() => handleRemoveRow(index)}
                      disabled={rows.length === 1}
                      className="flex h-9 w-9 items-center justify-center rounded-lg text-outline transition-all hover:bg-error/10 hover:text-error disabled:cursor-not-allowed disabled:opacity-20 md:opacity-0 md:group-hover:opacity-100"
                      aria-label="Remove criterion"
                    >
                      <span className="material-symbols-outlined text-lg">
                        delete
                      </span>
                    </button>
                  )}
                </div>

                <div className="min-w-0 flex-1 space-y-3">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
                    <div className="min-w-0 flex-1">
                      <input
                        className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-sm font-semibold text-on-surface transition-all placeholder:font-normal placeholder:text-outline focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
                        placeholder="Criterion title (e.g. Accuracy)"
                        value={row.title}
                        disabled={disabled}
                        onChange={(e) =>
                          handleRowChange(index, "title", e.target.value)
                        }
                        onBlur={markTouched}
                      />

                      {showErrors && errors.title && (
                        <p className="ml-1 mt-1 text-xs font-medium text-error">
                          {errors.title}
                        </p>
                      )}
                    </div>

                    <div className="sm:w-36">
                      <div className="flex items-center gap-0 rounded-xl bg-surface-container-low pr-3 transition-all focus-within:ring-2 focus-within:ring-primary/20">
                        <input
                          className="w-full min-w-0 rounded-xl border-none bg-transparent px-4 py-3 text-right text-sm font-bold text-on-surface focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
                          type="number"
                          min="0"
                          step="1"
                          value={row.max_points}
                          disabled={disabled}
                          onChange={(e) =>
                            handleRowChange(index, "max_points", e.target.value)
                          }
                          onBlur={markTouched}
                        />

                        <span className="text-[10px] font-bold uppercase tracking-widest text-outline">
                          pts
                        </span>
                      </div>

                      {showErrors && errors.max_points && (
                        <p className="ml-1 mt-1 text-xs font-medium text-error">
                          {errors.max_points}
                        </p>
                      )}
                    </div>
                  </div>

                  <div>
                    <textarea
                      className="min-h-[72px] w-full resize-y rounded-xl border-none bg-surface-container-low px-4 py-3 text-sm leading-relaxed text-on-surface transition-all placeholder:text-outline focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
                      placeholder="Describe what a perfect answer looks like. What should the student demonstrate?"
                      rows={2}
                      value={row.description}
                      disabled={disabled}
                      onChange={(e) =>
                        handleRowChange(index, "description", e.target.value)
                      }
                      onBlur={markTouched}
                    />

                    {showErrors && errors.description && (
                      <p className="ml-1 mt-1 text-xs font-medium text-error">
                        {errors.description}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {!disabled && (
        <button
          type="button"
          onClick={handleAddRow}
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl border-2 border-dashed border-outline-variant/30 bg-transparent py-3.5 text-sm font-bold text-on-surface-variant transition-all hover:border-primary/40 hover:bg-primary/5 hover:text-primary"
        >
          <span className="material-symbols-outlined text-base">add</span>
          Add criterion
        </button>
      )}
    </section>
  );
}
