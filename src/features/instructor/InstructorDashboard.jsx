import { NavLink, useParams } from "react-router";
import { useEffect, useState } from "react";

import { useDashboard } from "./useDashboard";
import { useReleaseAllResults } from "./useReleaseAllResults";

import { useCourses } from "../../hooks/useCourses";

import Spinner from "../../ui/Spinner";
import DashboardTable from "../../ui/DashboardTable";

export default function InstructorDashboard() {
  const { courseId } = useParams();
  const { dashboard = [], isLoading } = useDashboard(courseId);
  const { courses } = useCourses();

  const [searchValue, setSearchValue] = useState("");
  const [selectedAssessment, setSelectedAssessment] = useState("");

  const [grades, setGrades] = useState({});
  const { releaseAllResults } = useReleaseAllResults();

  useEffect(() => {
    if (!dashboard.length) return;

    setSelectedAssessment((current) =>
      current ? current : dashboard[0].assessment_config_id,
    );
  }, [dashboard]);

  useEffect(() => {
    if (!dashboard.length) return;

    setGrades((prev) => {
      const next = { ...prev };
      for (const assessment of dashboard) {
        for (const student of assessment.students || []) {
          if (student.final_grade != null) {
            next[student.session_id] = String(student.final_grade);
          }
        }
      }
      return next;
    });
  }, [dashboard]);

  if (isLoading) return <Spinner />;

  const course = courses.find(
    (course) => String(course.id) === String(courseId),
  );

  const assessment = dashboard.find(
    (item) => item.assessment_config_id === selectedAssessment,
  );

  const students = assessment?.students || [];

  const reviewStudents = students.filter(
    (student) => student.status === "review",
  );

  const filteredStudents = students.filter((student) =>
    student.student_name.toLowerCase().includes(searchValue.toLowerCase()),
  );

  const aiAverageScore = assessment?.ai_average_score ?? "-";
  const publishedAverageScore = assessment?.published_average_score ?? "-";

  const submittedCount = assessment?.submitted_count ?? 0;
  const totalStudents = assessment?.total_students ?? 0;

  const completionRate = totalStudents
    ? Math.round((submittedCount / totalStudents) * 100)
    : 0;

  function handleGradeChange(sessionId, grade) {
    setGrades((prev) => ({
      ...prev,
      [sessionId]: grade,
    }));
  }

  function isValidGrade(grade) {
    if (grade == null || String(grade).trim() === "") return false;

    const numericGrade = Number(grade);
    return (
      Number.isInteger(numericGrade) && numericGrade >= 0 && numericGrade <= 100
    );
  }

  const canPublishAll =
    reviewStudents.length > 0 &&
    reviewStudents.every((student) =>
      isValidGrade(grades[student.session_id] ?? ""),
    );

  function handlePublishAll() {
    const assessments = reviewStudents.map((student) => ({
      session_id: student.session_id,
      student_id: student.student_id,
    }));

    releaseAllResults({ assessments });
  }



  return (
    <div className="min-h-screen">
      <main className="px-10 pb-12 pt-24">
        <div className="mb-12 flex flex-col justify-between gap-6 md:flex-row md:items-end">
          <div>
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
              Assessment Dashboard
            </h1>

            <p className="mt-2 text-sm text-on-surface-variant">
              Overview of class assessment activity.
            </p>
          </div>

          <div className="relative min-w-[320px]">
            <label className="mb-1.5 ml-1 block text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">
              Select Assessment
            </label>

            <div className="relative">
              <select
                className="w-full cursor-pointer appearance-none rounded-xl border border-outline-variant/20 bg-surface-container-lowest px-10 py-3 font-headline text-sm font-semibold text-on-surface transition-colors hover:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                value={selectedAssessment}
                onChange={(e) => setSelectedAssessment(e.target.value)}
              >                
                {dashboard.length > 1 ? "" : <option value="No Assessment Selected">No Assessment Selected</option>}

                {dashboard.map((assessment) => (
                  <option
                    key={assessment.assessment_config_id}
                    value={assessment.assessment_config_id}
                  >
                    {assessment.assessment_title}
                  </option>
                ))}
              </select>

              <span className="material-symbols-outlined pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-primary">
                description
              </span>

              <span className="material-symbols-outlined pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-outline group-hover:text-primary">
                expand_more
              </span>
            </div>
          </div>
        </div>

        <div className="mb-12 grid grid-cols-1 gap-6 md:grid-cols-4">
          <div className="relative overflow-hidden rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-4 shadow-sm md:col-span-2">
            <div className="relative z-10">
              <p className="mb-4 text-xs font-bold uppercase tracking-wider text-outline-variant">
                Score Overview
              </p>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-0">
                <div className="md:pr-4">
                  <p className="mb-2 text-[11px] font-bold uppercase tracking-wider text-outline-variant">
                    Average Score
                  </p>

                  <div className="flex items-baseline gap-2">
                    <span className="font-headline text-4xl font-extrabold text-primary">
                      {aiAverageScore}
                    </span>
                    <span className="text-base font-bold text-outline">
                      / 100
                    </span>
                  </div>

                  <div className="mt-3 flex w-fit items-center gap-2 rounded-lg bg-tertiary-container px-2 py-1 text-xs font-semibold text-on-tertiary-container">
                    <span className="material-symbols-outlined text-xs">
                      auto_awesome
                    </span>
                    Calculated by AI
                  </div>
                </div>

                <div className="border-t border-outline-variant/30 pt-4 md:border-l md:border-t-0 md:pl-4 md:pt-0">
                  <p className="mb-2 text-[11px] font-bold uppercase tracking-wider text-outline-variant">
                    Official Avg. Score
                  </p>

                  <div className="flex items-baseline gap-2">
                    <span className="font-headline text-4xl font-extrabold text-secondary">
                      {publishedAverageScore}
                    </span>
                    <span className="text-base font-bold text-outline">
                      / 100
                    </span>
                  </div>

                  <div className="mt-3 flex w-fit items-center gap-2 rounded-lg bg-secondary-container px-2 py-1 text-xs font-semibold text-on-secondary-container">
                    <span className="material-symbols-outlined text-xs">
                      verified
                    </span>
                    Finalized Score
                  </div>
                </div>
              </div>
            </div>

            <div className="pointer-events-none absolute inset-0">
              <div className="absolute inset-y-0 left-0 w-1/2">
                <span className="material-symbols-outlined absolute -bottom-5 right-4 text-[90px] opacity-5">
                  grade
                </span>
              </div>

              <div className="absolute inset-y-0 right-0 w-1/2">
                <span className="material-symbols-outlined absolute -bottom-5 right-4 text-[90px] opacity-5">
                  check_circle
                </span>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-sm md:col-span-1">
            <p className="mb-4 text-xs font-bold uppercase tracking-wider text-outline-variant">
              Submissions
            </p>

            <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-end sm:gap-3">
              <div className="flex min-w-0 items-baseline gap-2">
                <span className="font-headline text-5xl font-extrabold text-on-surface">
                  {submittedCount}
                </span>

                <span className="text-lg font-bold text-outline">/</span>
              </div>

              <div className="inline-flex w-fit min-w-0 max-w-full shrink-0 items-center gap-1 rounded-full bg-secondary-container px-2.5 py-1 text-xs font-semibold text-on-secondary-container sm:mb-1 sm:gap-1 sm:px-3 sm:text-sm">
                <span className="material-symbols-outlined shrink-0 text-[14px] sm:text-[16px]">
                  groups
                </span>

                <span className="truncate">{totalStudents} enrolments</span>
              </div>
            </div>

            <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-surface-container">
              <div
                className="h-full rounded-full bg-primary"
                style={{ width: `${completionRate}%` }}
              ></div>
            </div>

            <p className="mt-2 text-[10px] font-medium text-on-surface-variant">
              {completionRate}% Completion rate
            </p>
          </div>

          <div className="flex flex-col justify-between rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-sm md:col-span-1">
            <div>
              <p className="mb-2 text-xs font-bold uppercase tracking-wider text-outline-variant">
                Pending Markings
              </p>

              <p className="font-body text-sm leading-relaxed text-on-surface-variant">
                {reviewStudents.length} students' scores pending for manual review before release.
              </p>
            </div>

            <button
              className={`mt-4 w-full rounded-xl py-3 font-headline text-sm font-bold shadow-sm transition-all duration-200 active:scale-95 ${
                canPublishAll
                  ? "bg-secondary text-on-secondary hover:bg-secondary-dim"
                  : "cursor-not-allowed bg-surface-container text-outline"
              }`}
              disabled={!canPublishAll}
              onClick={() => {
                handlePublishAll();
              }}
            >
              Release All Scores
            </button>
          </div>
        </div>

        <div className="overflow-hidden rounded-xl border border-outline-variant/10 bg-surface-container-lowest shadow-sm">
          <div className="flex items-center justify-between border-b border-surface-container px-8 py-6">
            <h3 className="font-headline text-lg font-bold text-on-surface">
              Submissions Overview
            </h3>

            <div className="flex gap-4">
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-sm text-outline">
                  search
                </span>

                <input
                  className="w-64 rounded-lg border border-outline-variant/20 bg-surface py-2 pl-10 pr-4 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                  placeholder="Filter students..."
                  type="text"
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                />
              </div>
            </div>
          </div>

          <DashboardTable
            filteredStudents={filteredStudents}
            isValidGrade={isValidGrade}
            grades={grades}
            onGradeChange={handleGradeChange}
          />
        </div>
      </main>
    </div>
  );
}
