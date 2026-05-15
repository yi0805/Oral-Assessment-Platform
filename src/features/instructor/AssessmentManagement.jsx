import { useState } from "react";
import { NavLink, useNavigate, useParams } from "react-router";

import { useCourses } from "../../hooks/useCourses";
import { useCourseAssessments } from "./useCourseAssessments";

export default function AssessmentManagement() {
  const navigate = useNavigate();
  const { courseId } = useParams();
  const [searchQuery, setSearchQuery] = useState("");

  const { courses } = useCourses();
  const course = courses.find((c) => String(c.id) === String(courseId));
  const { assessments, isLoading } = useCourseAssessments(courseId);

  const filtered = assessments.filter((a) =>
    a.title.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <div className="min-h-screen">
      <main className="ml-64 px-10 pb-12 pt-24">
        <div className="mb-4">
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
        </div>

        <div className="mb-8">
          <span className="mb-1 block text-xs font-bold uppercase tracking-[0.2em] text-outline">
            {course?.course_code} • {course?.course_name}
          </span>
          <h1 className="font-headline text-4xl font-extrabold tracking-tight text-on-surface">
            Assessments
          </h1>
          <p className="mt-2 text-sm text-on-surface-variant">
            Select an assessment to edit, or generate a new one.
          </p>
        </div>

        {isLoading ? (
          <p className="text-sm text-outline">Loading assessments…</p>
        ) : assessments.length === 0 ? (
          <div className="flex flex-col items-center rounded-xl border border-dashed border-outline-variant/30 bg-surface-container-low/40 p-12 text-center">
            <span
              className="material-symbols-outlined mb-3 text-4xl text-outline"
              style={{ verticalAlign: "middle" }}
            >
              assignment
            </span>
            <p className="text-sm font-bold text-on-surface">
              No assessments yet
            </p>
            <p className="mt-1 text-xs text-on-surface-variant">
              Use the button below to generate your first assessment.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <input
              className="w-full max-w-md rounded-xl border-none bg-surface-container-low px-4 py-2.5 text-sm text-on-surface placeholder:text-outline focus:ring-2 focus:ring-primary/20"
              placeholder="Search assessments…"
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />

            {filtered.length === 0 ? (
              <p className="py-3 text-sm text-outline">
                No assessments match &ldquo;{searchQuery}&rdquo;
              </p>
            ) : (
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
                {filtered.map((a) => (
                  <button
                    key={a.id}
                    type="button"
                    onClick={() =>
                      navigate(`/instructor/${courseId}/assessments/${a.id}`)
                    }
                    className="flex items-center justify-between rounded-xl border border-outline-variant/15 bg-surface-container-lowest px-5 py-4 text-left shadow-sm transition-all hover:border-primary/30 hover:shadow-md"
                  >
                    <p className="text-sm font-semibold text-on-surface">
                      {a.title}
                    </p>
                    <span
                      className={`ml-3 shrink-0 rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                        a.status === "published"
                          ? "bg-primary/10 text-primary"
                          : "bg-surface-container text-on-surface-variant"
                      }`}
                    >
                      {a.status === "published" ? "Published" : "Draft"}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      <div className="fixed bottom-8 right-8 z-50">
        <button
          className="group flex h-16 w-16 items-center justify-center rounded-2xl bg-primary text-on-primary shadow-2xl transition-all hover:bg-primary-dim active:scale-90"
          title="Generate new assessment"
          onClick={() =>
            navigate(`/instructor/${courseId}/assessments/generate`)
          }
        >
          <span className="material-symbols-outlined text-3xl transition-transform duration-300 group-hover:rotate-90">
            add
          </span>
        </button>
      </div>
    </div>
  );
}
