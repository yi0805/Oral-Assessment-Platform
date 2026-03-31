import { useLocation, NavLink } from "react-router";
import { useState } from "react";

import getAssessmentsByCourse from "../../utils/getAssessmentsByCourse";
import DashboardTable from "../../ui/DashboardTable";

export default function InstructorDashboard() {
  const { state } = useLocation();
  const course = state?.course || [];

  const assessments = getAssessmentsByCourse(course.id);
  console.log(assessments);

  const assessmentOptions = [
    ...new Set(assessments.map((item) => item.assessment)),
  ];
  const [selectedAssessment, setSelectedAssessment] = useState(
    assessmentOptions[0] || "",
  );

  const selectedAssessmentResults = assessments.filter(
    (item) => item.assessment === selectedAssessment,
  );

  const averageGrade =
    selectedAssessmentResults.reduce(
      (sum, item) => sum + parseFloat(item.grade),
      0,
    ) / selectedAssessmentResults.length;

  console.log(selectedAssessmentResults);

  return (
    <div className="min-h-screen">
      <main className="ml-64 px-10 pb-12 pt-24">
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
              {course.id}
            </span>
            <h1 className="font-headline text-4xl font-extrabold tracking-tight text-on-surface">
              Assessment Dashboard
            </h1>
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
                {assessmentOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
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
          <div className="relative overflow-hidden rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-sm md:col-span-1">
            <div className="relative z-10">
              <p className="mb-4 text-xs font-bold uppercase tracking-wider text-outline-variant">
                Average Score
              </p>
              <div className="flex items-baseline gap-2">
                <span className="font-headline text-5xl font-extrabold text-primary">
                  {averageGrade}
                </span>
                <span className="text-lg font-bold text-outline">/ 10</span>
              </div>

              <div className="mt-4 flex w-fit items-center gap-2 rounded-lg bg-tertiary-container px-2 py-1 text-xs font-semibold text-on-tertiary-container">
                <span className="material-symbols-outlined text-xs">
                  auto_awesome
                </span>
                Calculated by AI
              </div>
            </div>
            <div className="absolute -bottom-4 -right-4 opacity-5">
              <span className="material-symbols-outlined text-[120px]">
                grade
              </span>
            </div>
          </div>
          <div className="rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-sm md:col-span-1">
            <p className="mb-4 text-xs font-bold uppercase tracking-wider text-outline-variant">
              Submissions
            </p>
            <div className="flex items-baseline gap-2">
              <span className="font-headline text-5xl font-extrabold text-on-surface">
                {selectedAssessmentResults.length}
              </span>
              <span className="text-lg font-bold text-outline">/xxxxx</span>
            </div>
            <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-surface-container">
              <div
                className="h-full rounded-full bg-primary"
                style={{ width: "94%" }}
              ></div>
            </div>
            <p className="mt-2 text-[10px] font-medium text-on-surface-variant">
              xxxxxx Completion rate
            </p>
          </div>

          <div className="flex flex-col justify-between rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-sm md:col-span-1">
            <div>
              <p className="mb-2 text-xs font-bold uppercase tracking-wider text-outline-variant">
                Publication Status
              </p>
              <p className="font-body text-sm leading-relaxed text-on-surface-variant">
                xxxx scores pending manual review before release.
              </p>
            </div>
            <button className="mt-4 w-full rounded-xl bg-secondary py-3 font-headline text-sm font-bold text-on-secondary shadow-sm transition-all duration-200 hover:bg-secondary-dim active:scale-95">
              Publish All Scores
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
                />
              </div>
              <button className="flex items-center gap-2 rounded-lg border border-outline-variant/20 px-4 py-2 text-sm font-semibold text-on-surface-variant transition-colors hover:bg-surface-container">
                <span className="material-symbols-outlined text-sm">
                  filter_list
                </span>
                Sort
              </button>
            </div>
          </div>

          <DashboardTable
            selectedAssessmentResults={selectedAssessmentResults}
          />
        </div>
      </main>
    </div>
  );
}
