import { useState } from "react";
import { NavLink, useNavigate, useParams } from "react-router";

import { useCourses } from "../../hooks/useCourses";
import { useCourseAssessments } from "./useCourseAssessments";
import Spinner from "../../ui/Spinner";

function formatDueDate(iso) {
  if (!iso) return null;
  return new Date(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

function sortByDueThenTitle(items) {
  return [...items].sort((a, b) => {
    if (a.due_time && !b.due_time) return -1;
    if (!a.due_time && b.due_time) return 1;
    if (a.due_time && b.due_time) {
      const diff = new Date(a.due_time) - new Date(b.due_time);
      if (diff !== 0) return diff;
    }
    return a.title.localeCompare(b.title);
  });
}

export default function AssessmentManagement() {
  const navigate = useNavigate();
  const { courseId } = useParams();
  const [searchQuery, setSearchQuery] = useState("");

  const { courses } = useCourses();
  const course = courses.find((c) => String(c.id) === String(courseId));
  const { assessments, isLoading } = useCourseAssessments(courseId);

  if (isLoading) return <Spinner />;

  const filtered = assessments.filter((a) =>
    a.title.toLowerCase().includes(searchQuery.toLowerCase()),
  );
  const drafts = sortByDueThenTitle(
    filtered.filter((a) => a.status !== "published"),
  );
  const published = sortByDueThenTitle(
    filtered.filter((a) => a.status === "published"),
  );

  const sections = [
    { label: "Published", items: published },
    { label: "Drafts", items: drafts },
  ];

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

        {assessments.length === 0 ? (
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
              <div className="space-y-6">
                {sections.map(({ label, items }) =>
                  items.length === 0 ? null : (
                    <section key={label}>
                      <div className="mb-2 flex items-baseline gap-2 px-1">
                        <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-outline">
                          {label}
                        </span>

                        <span className="text-[11px] font-semibold text-outline-variant">
                          · {items.length}
                        </span>
                      </div>

                      <ul className="space-y-2">
                        {items.map((a) => {
                          const isPublished = a.status === "published";
                          const dueLabel = formatDueDate(a.due_time);
                          return (
                            <li key={a.id}>
                              <button
                                type="button"
                                onClick={() =>
                                  navigate(
                                    `/instructor/${courseId}/assessments/${a.id}`,
                                  )
                                }
                                className="group flex w-full items-center gap-4 rounded-xl border border-outline-variant/15 bg-surface-container-lowest px-5 py-3.5 text-left shadow-sm transition-all hover:border-primary/30 hover:shadow-md"
                              >
                                <span
                                  className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
                                    isPublished
                                      ? "bg-primary/10 text-primary"
                                      : "bg-surface-container text-on-surface-variant"
                                  }`}
                                >
                                  <span
                                    className="material-symbols-outlined text-lg"
                                    style={{ verticalAlign: "middle" }}
                                  >
                                    {isPublished
                                      ? "assignment_turned_in"
                                      : "edit_note"}
                                  </span>
                                </span>

                                <p className="min-w-0 flex-1 truncate text-sm font-semibold text-on-surface">
                                  {a.title}
                                </p>

                                <div className="hidden items-center gap-5 text-[10px] font-bold uppercase tracking-wider text-on-surface-variant md:flex">
                                  {a.main_question_num != null && (
                                    <span className="inline-flex items-center gap-1">
                                      <span
                                        className="material-symbols-outlined text-[15px]"
                                        style={{ verticalAlign: "middle" }}
                                      >
                                        quiz
                                      </span>
                                      {a.main_question_num} questions
                                    </span>
                                  )}

                                  {a.total_time_minute != null && (
                                    <span className="inline-flex items-center gap-1">
                                      <span
                                        className="material-symbols-outlined text-[15px]"
                                        style={{ verticalAlign: "middle" }}
                                      >
                                        schedule
                                      </span>
                                      {a.total_time_minute} min
                                    </span>
                                  )}

                                  {dueLabel && (
                                    <span className="inline-flex items-center gap-1">
                                      <span
                                        className="material-symbols-outlined text-[15px]"
                                        style={{ verticalAlign: "middle" }}
                                      >
                                        event
                                      </span>
                                      Due {dueLabel}
                                    </span>
                                  )}
                                </div>

                                <span
                                  className="material-symbols-outlined shrink-0 text-on-surface-variant transition-transform group-hover:translate-x-1"
                                  style={{ verticalAlign: "middle" }}
                                >
                                  chevron_right
                                </span>
                              </button>
                            </li>
                          );
                        })}
                      </ul>
                    </section>
                  ),
                )}
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
