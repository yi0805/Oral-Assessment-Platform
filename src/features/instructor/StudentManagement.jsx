import { useEffect, useRef, useState } from "react";
import { NavLink, useParams } from "react-router";

import { useCourses } from "../../hooks/useCourses";
import { useDashboard } from "./useDashboard";
import { useImportStudents } from "./useImportStudents";
import { useExportResults } from "./useExportResults";
import { useEnrolUser } from "./useEnrolUser";
import { useEnrolledUser } from "./useEnrolledUsers";
import { useDeleteEnrolment } from "./useDeleteEnrolment";
import Spinner from "../../ui/Spinner";

export default function StudentManagement() {
  const { courseId } = useParams();
  const [csvFile, setCsvFile] = useState(null);
  const fileInputRef = useRef(null);

  const [selectedAssessment, setSelectedAssessment] = useState("");

  const [upiAdd, setUpiAdd] = useState("");
  const [upiRemove, setUpiRemove] = useState("");
  const [role, setRole] = useState("student");

  const [currentPage, setCurrentPage] = useState(1);
  const { courses } = useCourses();
  const course = courses.find((c) => String(c.id) === String(courseId));

  const { dashboard = [], isLoading: isDashboardLoading } =
    useDashboard(courseId);
  const { enrolledUsers = [], isLoading: isUsersLoading } =
    useEnrolledUser(courseId);

  const { importStudents, isPending: isImporting } = useImportStudents();
  const { exportResults, isPending: isExporting } = useExportResults();

  const { enrolUser, isPending: isEnroling } = useEnrolUser();
  const { deleteEnrolment, isPending: isDeleting } = useDeleteEnrolment();

  useEffect(() => {
    setSelectedAssessment("");
  }, [courseId]);

  const rowsPerPage = 10;
  const totalPages = Math.max(1, Math.ceil(enrolledUsers.length / rowsPerPage));

  useEffect(() => {
    if (currentPage > totalPages) setCurrentPage(totalPages);
  }, [totalPages, currentPage]);

  const endIndex = currentPage * rowsPerPage;
  const startIndex = endIndex - rowsPerPage;
  const currentRows = enrolledUsers.slice(startIndex, endIndex);

  if (isUsersLoading) return <Spinner />;

  function goToPage(page) {
    setCurrentPage(page);
  }

  function goToPrevPage() {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  }

  function goToNextPage() {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  }

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

          <span className="mb-1 block text-xs font-bold uppercase tracking-[0.2em] text-outline">
            {course?.course_code} • {course?.course_name}
          </span>
          <h1 className="font-headline text-4xl font-extrabold tracking-tight text-on-surface">
            Users Management
          </h1>
          <p className="mt-2 text-sm text-on-surface-variant">
            Manage course enrolments and export assessment results.
          </p>
        </header>

        <div className="mb-8">
          <section className="rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
            <h2 className="mb-6 flex items-center gap-2 text-xl font-bold text-on-surface">
              <span
                className="material-symbols-outlined text-primary"
                data-icon="person"
                style={{ verticalAlign: "middle" }}
              >
                groups
              </span>
              Enrolled Users
            </h2>
            <p className="mb-6 text-sm text-on-surface-variant">
              A list of users enrolled to the course
            </p>

            <div className="space-y-4">
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low">
                      <th className="px-8 py-4 text-left text-[10px] font-bold uppercase tracking-[0.1em] text-outline-variant">
                        Full Name
                      </th>
                      <th className="px-8 py-4 text-left text-[10px] font-bold uppercase tracking-[0.1em] text-outline-variant">
                        UPI
                      </th>
                      <th className="px-8 py-4 text-left text-[10px] font-bold uppercase tracking-[0.1em] text-outline-variant">
                        Role
                      </th>
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-outline-variant/20">
                    {currentRows.length === 0 ? (
                      <tr>
                        <td colSpan="3" className="px-6 py-10 text-center">
                          <div className="flex flex-col items-center justify-center gap-2 text-on-surface-variant">
                            <span className="material-symbols-outlined text-3xl opacity-60">
                              fact_check
                            </span>
                            <p className="text-sm font-medium">
                              No users enrolled in this course.
                            </p>
                          </div>
                        </td>
                      </tr>
                    ) : (
                      currentRows.map((user, index) => (
                        <tr
                          key={user.upi || index}
                          className="transition-colors hover:bg-surface-container-low/30"
                        >
                          <td className="px-6 py-4 font-mono text-xs">
                            {user.full_name || (
                              <span className="text-outline">
                                Pending registration
                              </span>
                            )}
                          </td>
                          <td className="px-6 py-4 font-mono text-xs">
                            {user.upi}
                          </td>
                          <td className="px-6 py-4">
                            {user.role ? (
                              <span
                                className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium capitalize ${
                                  user.role === "instructor"
                                    ? "bg-primary/10 text-primary"
                                    : "bg-secondary/10 text-secondary"
                                }`}
                              >
                                {user.role}
                              </span>
                            ) : (
                              <span className="text-xs text-outline">—</span>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {totalPages > 1 && (
                <div className="flex gap-2">
                  <span className="text-xs font-medium text-on-surface-variant">
                    Showing {startIndex + 1}-
                    {Math.min(endIndex, enrolledUsers.length)} of{" "}
                    {enrolledUsers.length} users
                  </span>
                  <div className="flex gap-2">
                    <button
                      className="rounded p-2 text-outline transition-colors hover:bg-surface-container"
                      onClick={goToPrevPage}
                      disabled={currentPage === 1}
                    >
                      <span className="material-symbols-outlined text-sm">
                        chevron_left
                      </span>
                    </button>

                    {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                      (page) => (
                        <button
                          className={`rounded p-2 px-4 text-sm font-bold transition-colors hover:bg-surface-container ${currentPage === page ? "text-on-surface" : "text-outline"}`}
                          key={page}
                          onClick={() => goToPage(page)}
                        >
                          {page}
                        </button>
                      ),
                    )}

                    <button
                      className="rounded p-2 text-outline transition-colors hover:bg-surface-container"
                      onClick={goToNextPage}
                      disabled={currentPage === totalPages}
                    >
                      <span className="material-symbols-outlined text-sm">
                        chevron_right
                      </span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </section>
        </div>

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
              <p className="mb-4 text-[13px] font-bold uppercase tracking-wider text-on-surface-variant">
                Add user
              </p>

              <div className="grid grid-cols-1 gap-3 md:grid-cols-6">
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

                <div className="space-y-2 md:col-span-4">
                  <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                    UPI
                  </label>
                  <input
                    className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/20"
                    placeholder="e.g. jcle890 (from jcle890@gmail.com)"
                    type="text"
                    value={upiAdd}
                    onChange={(e) => setUpiAdd(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleEnrol()}
                  />
                </div>
              </div>

              <div className="mt-3">
                <button
                  className={`inline-flex items-center justify-center gap-2 rounded-xl px-6 py-2 font-headline text-sm font-bold shadow-sm transition-all duration-200 active:scale-95 ${
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
              <p className="mb-4 text-[13px] font-bold uppercase tracking-wider text-on-surface-variant">
                Remove user
              </p>

              <div className="space-y-2">
                <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                  UPI
                </label>
                <input
                  className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/20"
                  placeholder="e.g. jcle890 (from jcle890@gmail.com)"
                  type="text"
                  value={upiRemove}
                  onChange={(e) => setUpiRemove(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleDelete()}
                />
              </div>

              <div className="mt-3">
                <button
                  className={`inline-flex items-center justify-center gap-2 rounded-xl px-6 py-2 font-headline text-sm font-bold shadow-sm transition-all duration-200 active:scale-95 ${
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
