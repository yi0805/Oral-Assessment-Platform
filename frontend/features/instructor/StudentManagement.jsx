import { useEffect, useRef, useState } from "react";
import { NavLink } from "react-router";

import { useCourses } from "../../hooks/useCourses";
import { useDashboard } from "./useDashboard";
import { useImportStudents } from "./useImportStudents";
import { useExportResults } from "./useExportResults";

import Spinner from "../../ui/Spinner";

export default function StudentManagement() {
  const [courseId, setCourseId] = useState("");

  const [csvFile, setCsvFile] = useState(null);
  const fileInputRef = useRef(null);

  const { courses, isLoading } = useCourses();
  const [selectedAssessment, setSelectedAssessment] = useState("");

  const { importStudents, isPending: isImporting } = useImportStudents();
  const { exportResults, isPending: isExporting } = useExportResults();

  const { dashboard = [], isLoading: isDashboardLoading } =
    useDashboard(courseId);

  useEffect(() => {
    if (courses.length > 0 && !courseId) {
      setCourseId(courses[0].id);
    }
  }, [courses, courseId]);

  useEffect(() => {
    setSelectedAssessment("");
  }, [courseId]);

  if (isLoading) return <Spinner />;

  function handleImport() {
    if (!courseId || !csvFile) return;

    importStudents(
      { courseId, file: csvFile },
      {
        onSuccess: () => {
          setCsvFile(null);
          if (fileInputRef.current) fileInputRef.current.value = "";
        },
      },
    );
  }

  function handleExport() {
    if (!courseId || !selectedAssessment) return;

    exportResults({ courseId, assessmentConfigId: selectedAssessment });
  }

  return (
    <div className="min-h-screen">
      <main className="ml-64 px-10 pb-12 pt-24">
        <div className="mb-10">
          <NavLink
            className="group mb-4 inline-flex items-center gap-2 text-xs font-bold text-outline-variant transition-colors hover:text-primary"
            to="/home"
          >
            <span className="material-symbols-outlined text-sm transition-transform group-hover:-translate-x-1">
              arrow_back
            </span>

            <span className="font-body uppercase tracking-widest">
              Back to Courses
            </span>
          </NavLink>

          <h1 className="font-headline text-4xl font-extrabold tracking-tight text-on-surface">
            Student Management
          </h1>

          <p className="mt-2 text-sm text-on-surface-variant">
            Manage course enrolments and export assessment results.
          </p>
        </div>

        <section className="mb-8 rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
          <h2 className="mb-6 flex items-center gap-2 text-xl font-bold">
            <span
              className="material-symbols-outlined text-primary"
              data-icon="school"
              style={{ verticalAlign: "middle" }}
            >
              school
            </span>
            Select Course
          </h2>

          <div className="space-y-2">
            <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
              Course
            </label>

            <div className="group relative max-w-md">
              <select
                className="w-full cursor-pointer appearance-none rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all focus:ring-2 focus:ring-primary/20"
                value={courseId}
                onChange={(e) => setCourseId(e.target.value)}
              >
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.course_code} — {c.course_name}
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
        </section>

        <section className="mb-8 rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
          <h2 className="mb-6 flex items-center gap-2 text-xl font-bold">
            <span
              className="material-symbols-outlined text-primary"
              data-icon="upload_file"
              style={{ verticalAlign: "middle" }}
            >
              upload_file
            </span>
            Import Students
          </h2>

          <p className="mb-6 text-sm text-on-surface-variant">
            Upload a CSV file with a <strong>UPI</strong> column to bulk-enrol
            students into the selected course.
          </p>

          <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-outline-variant/30 bg-surface-container-low p-8 text-center">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-surface-container-lowest shadow-sm">
              <span
                className="material-symbols-outlined text-2xl text-primary"
                data-icon="csv"
                style={{ verticalAlign: "middle" }}
              >
                csv
              </span>
            </div>

            <h3 className="mb-1 text-base font-bold">Student CSV</h3>

            <p className="mb-4 px-2 text-[11px] text-on-surface-variant">
              CSV must contain a single &quot;UPI&quot; column with student
              identifiers.
            </p>

            <div className="w-full max-w-xs space-y-3">
              {csvFile && (
                <div className="flex items-center gap-3 rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-3 text-left shadow-sm">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-tertiary/10 text-tertiary">
                    <span
                      className="material-symbols-outlined text-xl"
                      data-icon="description"
                      style={{ verticalAlign: "middle" }}
                    >
                      description
                    </span>
                  </div>

                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold">
                      {csvFile.name}
                    </p>

                    <p className="text-[9px] text-outline">
                      {(csvFile.size / 1024).toFixed(1)} KB
                    </p>
                  </div>

                  <button
                    className="text-on-surface-variant transition-colors hover:text-error"
                    onClick={() => {
                      setCsvFile(null);
                      if (fileInputRef.current) fileInputRef.current.value = "";
                    }}
                  >
                    <span
                      className="material-symbols-outlined text-lg"
                      data-icon="close"
                      style={{ verticalAlign: "middle" }}
                    >
                      close
                    </span>
                  </button>
                </div>
              )}

              <label className="block cursor-pointer">
                <input
                  ref={fileInputRef}
                  className="hidden"
                  type="file"
                  accept=".csv"
                  onChange={(e) => setCsvFile(e.target.files[0] || null)}
                />

                <div className="w-full rounded-xl border border-outline-variant/20 bg-white py-2.5 text-center text-xs font-bold text-primary transition-all hover:bg-primary/5">
                  Browse Files
                </div>
              </label>
            </div>

            <button
              className={`mt-6 rounded-xl px-8 py-3 font-headline text-sm font-bold shadow-sm transition-all duration-200 active:scale-95 ${
                csvFile && courseId && !isImporting
                  ? "bg-primary text-on-primary hover:bg-primary-dim"
                  : "cursor-not-allowed bg-surface-container text-outline"
              }`}
              disabled={!csvFile || !courseId || isImporting}
              onClick={handleImport}
            >
              {isImporting ? "Importing..." : "Import Students"}
            </button>
          </div>
        </section>

        <section className="rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
          <h2 className="mb-6 flex items-center gap-2 text-xl font-bold">
            <span
              className="material-symbols-outlined text-secondary"
              data-icon="download"
              style={{ verticalAlign: "middle" }}
            >
              download
            </span>
            Export Results
          </h2>

          <p className="mb-6 text-sm text-on-surface-variant">
            Download a CSV of published assessment results containing student
            UPI, comments, and final grade.
          </p>

          <div className="mb-6 space-y-2">
            <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
              Select Assessment
            </label>

            <div className="group relative max-w-md">
              {isDashboardLoading ? (
                <p className="px-4 py-3 text-sm text-outline">
                  Loading assessments...
                </p>
              ) : dashboard.length === 0 ? (
                <p className="px-4 py-3 text-sm text-outline">
                  No assessments found for this course.
                </p>
              ) : (
                <>
                  <select
                    className="w-full cursor-pointer appearance-none rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all focus:ring-2 focus:ring-primary/20"
                    value={selectedAssessment}
                    onChange={(e) => setSelectedAssessment(e.target.value)}
                  >
                    <option value="">Choose an assessment</option>
                    {dashboard.map((item) => (
                      <option
                        key={item.assessment_config_id}
                        value={item.assessment_config_id}
                      >
                        {item.assessment_title}
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
                </>
              )}
            </div>
          </div>

          <button
            className={`rounded-xl px-8 py-3 font-headline text-sm font-bold shadow-sm transition-all duration-200 active:scale-95 ${
              selectedAssessment && !isExporting
                ? "bg-secondary text-on-secondary hover:bg-secondary-dim"
                : "cursor-not-allowed bg-surface-container text-outline"
            }`}
            disabled={!selectedAssessment || isExporting}
            onClick={handleExport}
          >
            <span className="inline-flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">
                download
              </span>
              Export CSV
            </span>
          </button>
        </section>
      </main>
    </div>
  );
}
