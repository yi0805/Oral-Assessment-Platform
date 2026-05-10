import { useState } from "react";
import { NavLink, useNavigate, useParams } from "react-router";

import { useCourses } from "../../hooks/useCourses";
import GeneratePanel from "./UploadMaterial";
import EditPanel from "./EditAssessment";

export default function AssessmentManagement() {
  const navigate = useNavigate();
  const [tab, setTab] = useState("edit");
  const { courseId } = useParams();

  const { courses } = useCourses();

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
          <h1 className="font-headline text-4xl font-extrabold tracking-tight text-on-surface">
            Assessments
          </h1>
          <p className="mt-2 text-sm text-on-surface-variant">
            Generate a new assessment or edit an existing one.
          </p>
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
        {tab === "edit" && (
          <EditPanel
            key={courseId}
            courseId={courseId}
            courses={courses}
            onSwitchCourse={(nextId) =>
              navigate(`/instructor/${nextId}/assessments`)
            }
          />
        )}
        {tab === "generate" && (
          <GeneratePanel key={courseId} courseId={courseId} courses={courses} />
        )}
      </main>
    </div>
  );
}
