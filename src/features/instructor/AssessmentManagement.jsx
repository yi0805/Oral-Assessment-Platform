import { useEffect, useState } from "react";

import { useCourses } from "../../hooks/useCourses";
import Spinner from "../../ui/Spinner";
import GeneratePanel from "./UploadMaterial";
import EditPanel from "./EditAssessment";

export default function AssessmentManagement() {
  const [tab, setTab] = useState("edit");
  const [courseId, setCourseId] = useState("");

  const { courses, isLoading } = useCourses();

  useEffect(() => {
    if (courses.length > 0 && !courseId) {
      setCourseId(courses[0].id);
    }
  }, [courses, courseId]);

  if (isLoading) return <Spinner />;

  return (
    <div className="min-h-screen">
      <main className="ml-64 px-10 pb-12 pt-24">
        <div className="mb-8">
          <h1 className="font-headline text-4xl font-extrabold tracking-tight text-on-surface">
            Assessments
          </h1>
          <p className="mt-2 text-sm text-on-surface-variant">
            Generate a new assessment or edit an existing one.
          </p>
        </div>

        {/* Course selector */}
        <div className="mb-6">
          <div className="group relative w-72">
            <select
              className="w-full cursor-pointer appearance-none rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
              value={courseId}
              onChange={(e) => setCourseId(e.target.value)}
              disabled={courses.length === 0}
            >
              {courses.length === 0 ? (
                <option>No courses available</option>
              ) : (
                courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.course_code || "Unknown Course"}
                  </option>
                ))
              )}
            </select>
            <span
              className="material-symbols-outlined pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-on-surface-variant"
              style={{ verticalAlign: "middle" }}
            >
              expand_more
            </span>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-8 flex w-fit gap-1 rounded-xl bg-surface-container-low p-1">
          {[
            { id: "edit", label: "Edit Existing" },
            { id: "generate", label: "Generate New" },
          ].map(({ id, label }) => (
            <button
              key={id}
              type="button"
              onClick={() => setTab(id)}
              className={`rounded-lg px-5 py-2 text-sm font-bold transition-all ${
                tab === id
                  ? "bg-surface text-on-surface shadow-sm"
                  : "text-on-surface-variant hover:text-on-surface"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Panel content */}
        {courseId && tab === "edit" && (
          <EditPanel key={courseId} courseId={courseId} courses={courses} />
        )}
        {courseId && tab === "generate" && (
          <GeneratePanel key={courseId} courseId={courseId} courses={courses} />
        )}
      </main>
    </div>
  );
}
