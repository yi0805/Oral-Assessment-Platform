import { useEffect, useState } from "react";
import { NavLink } from "react-router";

import { useCourses } from "../../hooks/useCourses";
import { useCourseAssessments } from "./useCourseAssessments";
import { useAssessmentDetail } from "./useAssessmentDetail";
import { useUpdateAssessment } from "./useUpdateAssessment";
import { usePublishAssessment } from "./usePublishAssessment";
import { useDeleteAssessment } from "./useDeleteAssessment";

import Spinner from "../../ui/Spinner";
import ConfirmModal from "../../ui/ConfirmModal";
import AssessmentConfigForm from "./AssessmentConfigForm";
import { isAssessmentConfigValid } from "./assessmentFormUtils";

const STATUS_STYLES = {
  published:
    "bg-primary/10 text-primary",
  draft:
    "bg-surface-container text-on-surface-variant",
};

function StatusBadge({ status }) {
  const label = status === "published" ? "Published" : "Draft";
  const className = STATUS_STYLES[status] ?? STATUS_STYLES.draft;
  return (
    <span
      className={`ml-2 rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${className}`}
    >
      {label}
    </span>
  );
}

export default function EditAssessment() {
  const [courseId, setCourseId] = useState("");
  const [selectedAssessmentId, setSelectedAssessmentId] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const [assessmentName, setAssessmentName] = useState("");
  const [numQuestions, setNumQuestions] = useState("");
  const [assessmentTime, setAssessmentTime] = useState("");
  const [releaseTime, setReleaseTime] = useState(null);
  const [dueTime, setDueTime] = useState(null);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  const { courses, isLoading: isCoursesLoading } = useCourses();
  const { assessments, isLoading: isAssessmentsLoading } =
    useCourseAssessments(courseId);
  const { assessment, isLoading: isDetailLoading } = useAssessmentDetail(
    courseId,
    selectedAssessmentId,
  );
  const { updateAssessment, isPending: isSaving } = useUpdateAssessment();
  const { publishAssessment, isPending: isPublishing } = usePublishAssessment();
  const { deleteAssessment, isDeleting } = useDeleteAssessment();

  useEffect(() => {
    if (courses.length > 0 && !courseId) {
      setCourseId(courses[0].id);
    }
  }, [courses, courseId]);

  useEffect(() => {
    setSelectedAssessmentId("");
    setAssessmentName("");
    setNumQuestions("");
    setAssessmentTime("");
    setReleaseTime(null);
    setDueTime(null);
    setSearchQuery("");
  }, [courseId]);

  useEffect(() => {
    setConfirmingDelete(false);
  }, [selectedAssessmentId]);

  useEffect(() => {
    if (!assessment) return;
    setAssessmentName(assessment.title);
    setNumQuestions(String(assessment.main_question_num));
    setAssessmentTime(String(assessment.total_time_minute));
    setReleaseTime(
      assessment.release_time ? new Date(assessment.release_time) : null,
    );
    setDueTime(assessment.due_time ? new Date(assessment.due_time) : null);
  }, [assessment]);

  if (isCoursesLoading) return <Spinner />;

  const hasCourses = courses.length > 0;
  const filteredAssessments = assessments.filter((a) =>
    a.title.toLowerCase().includes(searchQuery.toLowerCase()),
  );
  const isPublished = assessment?.status === "published";
  const formEnabled =
    !!selectedAssessmentId && !isDetailLoading && !isSaving && !isPublishing && !isDeleting;
  const canSave =
    formEnabled &&
    isAssessmentConfigValid({ assessmentName, numQuestions, assessmentTime });
  const canRepublish = formEnabled;

  function handleSave() {
    if (!canSave) return;
    updateAssessment({
      courseId,
      assessmentConfigId: selectedAssessmentId,
      payload: {
        title: assessmentName,
        total_time_minute: Math.round(Number(assessmentTime)),
        main_question_num: Number(numQuestions),
        release_time: releaseTime?.toISOString() ?? null,
        due_time: dueTime?.toISOString() ?? null,
      },
    });
  }

  function handlePublish() {
    if (!selectedAssessmentId || isPublishing) return;
    publishAssessment({ courseId, assessmentConfigId: selectedAssessmentId });
  }

  function handleRepublish() {
    if (!canRepublish) return;
    updateAssessment({
      courseId,
      assessmentConfigId: selectedAssessmentId,
      payload: { due_time: dueTime?.toISOString() ?? null },
    });
  }

  async function handleDelete() {
    await deleteAssessment({ courseId, assessmentConfigId: selectedAssessmentId });
    setSelectedAssessmentId("");
    setConfirmingDelete(false);
  }

  return (
    <div className="min-h-screen">
      {confirmingDelete && (
        <ConfirmModal
          title="Delete Assessment"
          message={`Are you sure you want to delete "${assessment?.title}"? This action cannot be undone.`}
          confirmLabel="Yes, Delete"
          isLoading={isDeleting}
          onConfirm={handleDelete}
          onCancel={() => setConfirmingDelete(false)}
        />
      )}
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
            Edit Assessment
          </h1>

          <p className="mt-2 text-sm text-on-surface-variant">
            Select an assessment and update its details.
          </p>
        </div>

        {!hasCourses ? (
          <div className="flex flex-col items-center rounded-xl border border-dashed border-outline-variant/30 bg-surface-container-low/40 p-12 text-center">
            <span
              className="material-symbols-outlined mb-2 text-3xl text-outline"
              style={{ verticalAlign: "middle" }}
            >
              menu_book
            </span>
            <p className="text-base font-bold text-on-surface">
              No courses yet
            </p>
            <p className="mt-1 text-xs text-on-surface-variant">
              Create a course first to edit assessments.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-12 items-start gap-6">
            <div className="col-span-12 space-y-6 lg:col-span-6">
              <AssessmentConfigForm
                courses={courses}
                courseId={courseId}
                onCourseIdChange={setCourseId}
                assessmentName={assessmentName}
                onAssessmentNameChange={setAssessmentName}
                numQuestions={numQuestions}
                onNumQuestionsChange={setNumQuestions}
                assessmentTime={assessmentTime}
                onAssessmentTimeChange={setAssessmentTime}
                releaseTime={releaseTime}
                onReleaseTimeChange={setReleaseTime}
                dueTime={dueTime}
                onDueTimeChange={setDueTime}
                disabled={!formEnabled}
                onlyDueDate={isPublished}
                releaseHelperText=""
              />
            </div>

            <div className="col-span-12 lg:col-span-6">
              <section className="rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
                <div className="mb-6 flex items-start gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <span
                      className="material-symbols-outlined text-xl"
                      style={{ verticalAlign: "middle" }}
                    >
                      edit_note
                    </span>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-on-surface">
                      Select Assessment
                    </h3>
                    <p className="mt-1 max-w-md text-xs text-on-surface-variant">
                      Choose an assessment to edit. Both draft and published
                      assessments are shown.
                    </p>
                  </div>
                </div>

                {isAssessmentsLoading ? (
                  <p className="px-1 py-3 text-sm text-outline">
                    Loading assessments…
                  </p>
                ) : assessments.length === 0 ? (
                  <div className="flex flex-col items-center rounded-xl border border-dashed border-outline-variant/30 bg-surface-container-low/40 p-8 text-center">
                    <span
                      className="material-symbols-outlined mb-2 text-3xl text-outline"
                      style={{ verticalAlign: "middle" }}
                    >
                      assignment
                    </span>
                    <p className="text-sm font-bold text-on-surface">
                      No assessments yet
                    </p>
                    <p className="mt-1 text-xs text-on-surface-variant">
                      Generate an assessment for this course first.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <input
                      className="w-full rounded-xl border-none bg-surface-container-low px-4 py-2.5 text-sm text-on-surface placeholder:text-outline focus:ring-2 focus:ring-primary/20"
                      placeholder="Search assessments…"
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />

                    {filteredAssessments.length === 0 ? (
                      <p className="px-1 py-3 text-center text-xs text-outline">
                        No assessments match &ldquo;{searchQuery}&rdquo;
                      </p>
                    ) : (
                      <div className="space-y-2">
                        {filteredAssessments.map((a) => {
                          const isSelected = a.id === selectedAssessmentId;
                          return (
                            <button
                              key={a.id}
                              type="button"
                              onClick={() => setSelectedAssessmentId(a.id)}
                              className={`flex w-full items-center justify-between rounded-xl border px-4 py-3.5 text-left transition-all ${
                                isSelected
                                  ? "border-primary/30 bg-primary/5 ring-2 ring-primary/20"
                                  : "border-outline-variant/15 bg-surface-container-low hover:border-outline-variant/40"
                              }`}
                            >
                              <span className="text-sm font-semibold text-on-surface">
                                {a.title}
                              </span>
                              <StatusBadge status={a.status} />
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}

                {isDetailLoading && selectedAssessmentId && (
                  <p className="mt-4 px-1 text-xs text-outline">
                    Loading details…
                  </p>
                )}
              </section>
            </div>

            <div className="col-span-12">
              <div className="flex items-center justify-between rounded-xl border border-primary/10 bg-primary/5 p-6">
                <div className="flex items-center gap-4">
                  <div>
                    <p className="text-sm font-bold text-primary">
                      {isPublished ? "Republish Assessment" : "Save Changes"}
                    </p>
                    <p className="text-[11px] text-on-surface-variant">
                      {!selectedAssessmentId
                        ? "Select an assessment above to begin editing."
                        : isPublished
                          ? "Update the due date and republish to students."
                          : "Save your changes after changing the assesment parameters then publish it to make it visible to students."}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {isPublished ? (
                    <button
                      className="rounded-xl bg-primary px-6 py-3 text-sm font-bold tracking-tight text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
                      disabled={!canRepublish || isSaving}
                      onClick={handleRepublish}
                    >
                      {isSaving ? "Saving…" : "Republish Assessment"}
                    </button>
                  ) : (
                    <>
                      {selectedAssessmentId && (
                          <button
                            className="flex items-center gap-1.5 rounded-xl border border-error/40 bg-transparent px-4 py-2.5 text-sm font-bold text-error transition-all hover:bg-error/10 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
                            disabled={isSaving || isPublishing}
                            onClick={() => setConfirmingDelete(true)}
                          >
                            <span className="material-symbols-outlined text-base" style={{ verticalAlign: "middle" }}>
                              delete
                            </span>
                            Delete
                          </button>
                      )}

                      <button
                        className="rounded-xl border border-primary bg-transparent px-6 py-3 text-sm font-bold tracking-tight text-primary transition-all hover:bg-primary/10 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
                        disabled={isPublishing || isSaving}
                        onClick={handlePublish}
                      >
                        {isPublishing ? "Publishing…" : "Publish Assessment"}
                      </button>

                      <button
                        className="rounded-xl bg-primary px-6 py-3 text-sm font-bold tracking-tight text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
                        disabled={!canSave || isSaving || isPublishing}
                        onClick={handleSave}
                      >
                        {isSaving ? "Saving…" : "Save Assessment"}
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
