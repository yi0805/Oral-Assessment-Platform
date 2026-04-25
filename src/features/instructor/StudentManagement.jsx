import { useEffect, useRef, useState } from "react";
import { NavLink } from "react-router";

import { useCourses } from "../../hooks/useCourses";
import { useDashboard } from "./useDashboard";
import { useImportStudents } from "./useImportStudents";
import { useExportResults } from "./useExportResults";
import { useEnrolUser } from "./useEnrolUser";
import { useDeleteEnrolment } from "./useDeleteEnrolment";

import Spinner from "../../ui/Spinner";

export default function StudentManagement() {
  const [courseId, setCourseId] = useState("");
  const [csvFile, setCsvFile] = useState(null);
  const fileInputRef = useRef(null);

  const [selectedAssessment, setSelectedAssessment] = useState("");

  const [upiAdd, setUpiAdd] = useState("");
  const [upiRemove, setUpiRemove] = useState("");
  const [role, setRole] = useState("student");

  const { courses, isLoading } = useCourses();
  const { dashboard = [], isLoading: isDashboardLoading } =
    useDashboard(courseId);

  const { importStudents, isPending: isImporting } = useImportStudents();
  const { exportResults, isPending: isExporting } = useExportResults();

  const { enrolUser, isPending: isEnroling } = useEnrolUser();
  const { deleteEnrolment, isPending: isDeleting } = useDeleteEnrolment();

  useEffect(() => {
    if (courses.length > 0 && !courseId) {
      setCourseId(courses[0].id);
    }
  }, [courses, courseId]);

  useEffect(() => {
    setSelectedAssessment("");
  }, [courseId]);

  if (isLoading) return <Spinner />;

  const hasCourses = courses.length > 0;

  const canImport = Boolean(courseId && csvFile && !isImporting);
  const canEnrol = Boolean(courseId && upiAdd.trim() && !isEnroling);
  const canDelete = Boolean(courseId && upiRemove.trim() && !isDeleting);
  const canExport = Boolean(selectedAssessment && !isExporting);

  function handleImport() {
    if (!canImport) return;
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

  function handleEnrol() {
    if (!canEnrol) return;

    enrolUser(
      { courseId, upi: upiAdd.trim(), role },
      { onSuccess: () => setUpiAdd("") },
    );
  }

  function handleDelete() {
    if (!canDelete) return;

    deleteEnrolment(
      { courseId, upi: upiRemove.trim(), role: "" },
      { onSuccess: () => setUpiRemove("") },
    );
  }

  function handleExport() {
    if (!canExport) return;

    exportResults({ courseId, assessmentConfigId: selectedAssessment });
  }

  return (
    <div className="min-h-screen">
      <main className="ml-64 px-10 pb-12 pt-24">
        <header className="mb-10">
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
        </header>

        <section className="mb-8 rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
          <h2 className="mb-6 flex items-center gap-2 text-xl font-bold text-on-surface">
            <span
              className="material-symbols-outlined text-primary"
              data-icon="school"
              style={{ verticalAlign: "middle" }}
            >
              school
            </span>
            Select Course
          </h2>

          {hasCourses ? (
            <div className="space-y-2">
              <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                Course
              </label>
              <div className="relative max-w-lg">
                <select
                  className="w-full cursor-pointer appearance-none rounded-xl border-none bg-surface-container-low px-4 py-3 pr-10 text-on-surface transition-all focus:outline-none focus:ring-2 focus:ring-primary/20"
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
          ) : (
            <div className="flex flex-col items-center rounded-xl border border-dashed border-outline-variant/30 bg-surface-container-low/40 p-8 text-center">
              <span
                className="material-symbols-outlined mb-2 text-3xl text-outline"
                data-icon="menu_book"
                style={{ verticalAlign: "middle" }}
              >
                menu_book
              </span>

              <p className="text-base font-bold text-on-surface">
                No courses yet
              </p>

              <p className="mt-1 text-xs text-on-surface-variant">
                Create a course first to manage enrolments.
              </p>
            </div>
          )}
        </section>

        <div className="mb-8 grid grid-cols-1 gap-8 lg:grid-cols-2">
          <section className="rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
            <h2 className="mb-6 flex items-center gap-2 text-xl font-bold text-on-surface">
              <span
                className="material-symbols-outlined text-primary"
                data-icon="upload_file"
                style={{ verticalAlign: "middle" }}
              >
                upload_file
              </span>
              Bulk Import (CSV)
            </h2>
            <p className="mb-6 text-sm text-on-surface-variant">
              Upload a CSV with a single <strong>UPI</strong> column to
              bulk-enrol students.
            </p>

            <div className="flex flex-col items-center rounded-xl border-2 border-dashed border-outline-variant/30 bg-surface-container-low/60 p-6 text-center">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-surface-container-lowest shadow-sm">
                <span
                  className="material-symbols-outlined text-2xl text-primary"
                  data-icon="csv"
                  style={{ verticalAlign: "middle" }}
                >
                  csv
                </span>
              </div>
              <h3 className="text-base font-bold text-on-surface">
                Student CSV
              </h3>

              <p className="mb-4 mt-1 text-[11px] text-on-surface-variant">
                Single &quot;UPI&quot; column with student identifiers.
              </p>

              {csvFile && (
                <div className="mb-3 flex w-full max-w-xs items-center gap-3 rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-3 text-left shadow-sm">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-tertiary/10 text-tertiary">
                    <span
                      className="material-symbols-outlined text-xl"
                      data-icon="description"
                      style={{ verticalAlign: "middle" }}
                    >
                      description
                    </span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-on-surface">
                      {csvFile.name}
                    </p>
                    <p className="text-[10px] text-outline">
                      {(csvFile.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                  <button
                    type="button"
                    aria-label="Remove file"
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

              <label className="block w-full max-w-xs cursor-pointer">
                <input
                  ref={fileInputRef}
                  className="hidden"
                  type="file"
                  accept=".csv"
                  onChange={(e) => setCsvFile(e.target.files[0] || null)}
                />
                <div className="rounded-xl border border-outline-variant/20 bg-surface-container-lowest py-2.5 text-center text-xs font-bold text-primary transition-all hover:bg-primary/5">
                  {csvFile ? "Replace File" : "Browse Files"}
                </div>
              </label>

              <button
                className={`mt-6 inline-flex items-center justify-center gap-2 rounded-xl px-8 py-3 font-headline text-sm font-bold shadow-sm transition-all duration-200 active:scale-95 ${
                  canImport
                    ? "bg-primary text-on-primary hover:bg-primary-dim"
                    : "cursor-not-allowed bg-surface-container text-outline"
                }`}
                disabled={!canImport}
                onClick={handleImport}
              >
                <span
                  className="material-symbols-outlined text-base"
                  data-icon={isImporting ? "progress_activity" : "cloud_upload"}
                  style={{ verticalAlign: "middle" }}
                >
                  {isImporting ? "progress_activity" : "cloud_upload"}
                </span>
                {isImporting ? "Importing…" : "Import Students"}
              </button>
            </div>
          </section>

          <section className="rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
            <h2 className="mb-6 flex items-center gap-2 text-xl font-bold text-on-surface">
              <span
                className="material-symbols-outlined text-primary"
                data-icon="person"
                style={{ verticalAlign: "middle" }}
              >
                person
              </span>
              Manage Individual Enrolment
            </h2>

            <div className="mb-6">
              <p className="mb-4 text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">
                Add user
              </p>

              <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
                <div className="space-y-2 md:col-span-2">
                  <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                    Enrol as
                  </label>

                  <div className="relative">
                    <select
                      className="w-full cursor-pointer appearance-none rounded-xl border-none bg-surface-container-low px-4 py-3 pr-10 text-on-surface transition-all focus:outline-none focus:ring-2 focus:ring-primary/20"
                      value={role}
                      onChange={(e) => setRole(e.target.value)}
                    >
                      <option value="student">Student</option>
                      <option value="instructor">Instructor</option>
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

                <div className="space-y-2 md:col-span-3">
                  <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                    UPI
                  </label>
                  <input
                    className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/20"
                    placeholder="e.g. john.doe (from john.doe@gmail.com)"
                    type="text"
                    value={upiAdd}
                    onChange={(e) => setUpiAdd(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleEnrol()}
                  />
                </div>
              </div>

              <div className="mt-4">
                <button
                  className={`inline-flex items-center justify-center gap-2 rounded-xl px-8 py-3 font-headline text-sm font-bold shadow-sm transition-all duration-200 active:scale-95 ${
                    canEnrol
                      ? "bg-primary text-on-primary hover:bg-primary-dim"
                      : "cursor-not-allowed bg-surface-container text-outline"
                  }`}
                  disabled={!canEnrol}
                  onClick={handleEnrol}
                >
                  <span
                    className="material-symbols-outlined text-base"
                    data-icon={isEnroling ? "progress_activity" : "person_add"}
                    style={{ verticalAlign: "middle" }}
                  >
                    {isEnroling ? "progress_activity" : "person_add"}
                  </span>
                  {isEnroling ? "Enroling…" : "Enrol User"}
                </button>
              </div>
            </div>

            <hr className="my-6 border-outline-variant/30" />

            <div>
              <p className="mb-4 text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">
                Remove user
              </p>

              <div className="space-y-2">
                <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                  UPI
                </label>
                <input
                  className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/20"
                  placeholder="e.g. john.doe (from john.doe@gmail.com)"
                  type="text"
                  value={upiRemove}
                  onChange={(e) => setUpiRemove(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleDelete()}
                />
              </div>

              <div className="mt-4">
                <button
                  className={`inline-flex items-center justify-center gap-2 rounded-xl px-8 py-3 font-headline text-sm font-bold shadow-sm transition-all duration-200 active:scale-95 ${
                    canDelete
                      ? "bg-error text-on-error hover:bg-error-dim"
                      : "cursor-not-allowed bg-surface-container text-outline"
                  }`}
                  disabled={!canDelete}
                  onClick={handleDelete}
                >
                  <span
                    className="material-symbols-outlined text-base"
                    data-icon={
                      isDeleting ? "progress_activity" : "person_remove"
                    }
                    style={{ verticalAlign: "middle" }}
                  >
                    {isDeleting ? "progress_activity" : "person_remove"}
                  </span>
                  {isDeleting ? "Removing…" : "Delete Enrolment"}
                </button>
              </div>
            </div>
          </section>
        </div>

        <section className="rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
          <h2 className="mb-6 flex items-center gap-2 text-xl font-bold text-on-surface">
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
            <div className="relative max-w-md">
              {isDashboardLoading ? (
                <p className="px-4 py-3 text-sm text-outline">
                  Loading assessments…
                </p>
              ) : dashboard.length === 0 ? (
                <p className="px-4 py-3 text-sm text-outline">
                  No assessments found for this course.
                </p>
              ) : (
                <>
                  <select
                    className="w-full cursor-pointer appearance-none rounded-xl border-none bg-surface-container-low px-4 py-3 pr-10 text-on-surface transition-all focus:outline-none focus:ring-2 focus:ring-primary/20"
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
            className={`inline-flex items-center justify-center gap-2 rounded-xl px-8 py-3 font-headline text-sm font-bold shadow-sm transition-all duration-200 active:scale-95 ${
              canExport
                ? "bg-secondary text-on-secondary hover:bg-secondary-dim"
                : "cursor-not-allowed bg-surface-container text-outline"
            }`}
            disabled={!canExport}
            onClick={handleExport}
          >
            <span
              className="material-symbols-outlined text-base"
              data-icon={isExporting ? "progress_activity" : "download"}
              style={{ verticalAlign: "middle" }}
            >
              {isExporting ? "progress_activity" : "download"}
            </span>
            {isExporting ? "Exporting…" : "Export CSV"}
          </button>
        </section>
      </main>
    </div>
  );
}
