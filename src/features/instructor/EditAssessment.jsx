import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import { useCourseAssessments } from "./useCourseAssessments";
import { useAssessmentDetail } from "./useAssessmentDetail";
import { useUpdateAssessment } from "./useUpdateAssessment";
import { usePublishAssessment } from "./usePublishAssessment";
import { useDeleteAssessment } from "./useDeleteAssessment";
import { useCopyAssessment } from "./useCopyAssessment";
import { useRubric } from "./useRubric";
import { useUpdateRubric } from "./useUpdateRubric";

import ConfirmModal from "../../ui/ConfirmModal";
import CopyAssessmentModal from "./CopyAssessmentModal";
import AssessmentConfigForm from "./AssessmentConfigForm";
import RubricEditor from "./RubricEditor";
import QuestionEditor from "./QuestionEditor";
import {
  MAX_QUESTIONS,
  isAssessmentConfigValid,
  isRubricValid,
  rubricTotal,
} from "./assessmentFormUtils";

function rubricToRows(rubric) {
  return (rubric?.criteria_data ?? []).map((item) => ({
    title: item.title ?? "",
    description: item.description ?? "",
    max_points: Number(item.max_points) || 0,
  }));
}

function snapshotKey({ form, rubricRows }) {
  return JSON.stringify({
    form: {
      ...form,
      releaseTime: form.releaseTime ? form.releaseTime.toISOString() : null,
      dueTime: form.dueTime ? form.dueTime.toISOString() : null,
    },
    rubricRows,
  });
}

export default function EditPanel({ courseId, courses }) {
  const [selectedAssessmentId, setSelectedAssessmentId] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const [assessmentName, setAssessmentName] = useState("");
  const [numQuestions, setNumQuestions] = useState("");
  const [assessmentTime, setAssessmentTime] = useState("");
  const [releaseTime, setReleaseTime] = useState(null);
  const [dueTime, setDueTime] = useState(null);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [copyModalOpen, setCopyModalOpen] = useState(false);
  const [rubricRows, setRubricRows] = useState([]);
  const [initialSnapshot, setInitialSnapshot] = useState(null);
  const [initializedFor, setInitializedFor] = useState(null);

  const { assessments, isLoading: isAssessmentsLoading } =
    useCourseAssessments(courseId);
  const { assessment, isLoading: isDetailLoading } = useAssessmentDetail(
    courseId,
    selectedAssessmentId,
  );
  const { updateAssessment, isPending: isSaving } = useUpdateAssessment();
  const { publishAssessment, isPending: isPublishing } = usePublishAssessment();
  const { deleteAssessment, isDeleting } = useDeleteAssessment();
  const { copyAssessment, isCopying } = useCopyAssessment();
  const { rubric, isLoading: isRubricLoading } =
    useRubric(selectedAssessmentId);
  const { updateRubric, isPending: isSavingRubric } = useUpdateRubric();

  useEffect(() => {
    setSelectedAssessmentId("");
    setAssessmentName("");
    setNumQuestions("");
    setAssessmentTime("");
    setReleaseTime(null);
    setDueTime(null);
    setSearchQuery("");
    setRubricRows([]);
    setInitialSnapshot(null);
    setInitializedFor(null);
  }, [courseId]);

  useEffect(() => {
    setConfirmingDelete(false);
    setCopyModalOpen(false);
  }, [selectedAssessmentId]);

  useEffect(() => {
    if (!assessment || !rubric) return;
    if (initializedFor === selectedAssessmentId) return;

    const form = {
      assessmentName: assessment.title ?? "",
      numQuestions:
        assessment.main_question_num != null
          ? String(assessment.main_question_num)
          : "",
      assessmentTime:
        assessment.total_time_minute != null
          ? String(assessment.total_time_minute)
          : "",
      releaseTime: assessment.release_time
        ? new Date(assessment.release_time)
        : null,
      dueTime: assessment.due_time ? new Date(assessment.due_time) : null,
    };
    const rows = rubricToRows(rubric);

    setAssessmentName(form.assessmentName);
    setNumQuestions(form.numQuestions);
    setAssessmentTime(form.assessmentTime);
    setReleaseTime(form.releaseTime);
    setDueTime(form.dueTime);
    setRubricRows(rows);
    setInitialSnapshot(snapshotKey({ form, rubricRows: rows }));
    setInitializedFor(selectedAssessmentId);
  }, [assessment, rubric, selectedAssessmentId, initializedFor]);

  const hasCourses = courses.length > 0;
  const filteredAssessments = assessments.filter((a) =>
    a.title.toLowerCase().includes(searchQuery.toLowerCase()),
  );
  const isPublished = assessment?.status === "published";
  const formEnabled =
    !!selectedAssessmentId &&
    !isDetailLoading &&
    !isSaving &&
    !isPublishing &&
    !isDeleting;

  const currentSnapshot = snapshotKey({
    form: {
      assessmentName,
      numQuestions,
      assessmentTime,
      releaseTime,
      dueTime,
    },
    rubricRows,
  });

  const isDirty =
    initialSnapshot != null && currentSnapshot !== initialSnapshot;
  const rubricValid = rubricRows.length > 0 && isRubricValid(rubricRows);

  const canSave =
    formEnabled &&
    isAssessmentConfigValid({ assessmentName, numQuestions, assessmentTime }) &&
    isDirty &&
    rubricValid &&
    !isSavingRubric;
  const canUpdatePublished = formEnabled;

  async function handleSave() {
    if (!canSave) return;
    const snapshotAtSubmit = currentSnapshot;
    try {
      await updateAssessment({
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
      await updateRubric({
        assessmentConfigId: selectedAssessmentId,
        rubricPayload: {
          total_points: rubricTotal(rubricRows),
          criteria_data: rubricRows.map((row) => ({
            title: row.title,
            description: row.description,
            max_points: Number(row.max_points),
          })),
        },
      });
      setInitialSnapshot(snapshotAtSubmit);
    } catch {
      //
    }
  }

  async function handlePublish() {
    if (!selectedAssessmentId || isPublishing) return;
    try {
      await updateAssessment({
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
      await updateRubric({
        assessmentConfigId: selectedAssessmentId,
        rubricPayload: {
          total_points: rubricTotal(rubricRows),
          criteria_data: rubricRows.map((row) => ({
            title: row.title,
            description: row.description,
            max_points: Number(row.max_points),
          })),
        },
      });
      publishAssessment({ courseId, assessmentConfigId: selectedAssessmentId });
    } catch {
      //
    }
  }

  function handleUpdatePublished() {
    if (!canUpdatePublished) return;
    updateAssessment({
      courseId,
      assessmentConfigId: selectedAssessmentId,
      payload: { 
        title: assessmentName, 
        due_time: dueTime?.toISOString() ?? null 
      },
    });
  }

  async function handleCopy({ targetCourseId, title }) {
    await copyAssessment({
      courseId,
      assessmentConfigId: selectedAssessmentId,
      targetCourseId,
      title,
    });
    setCopyModalOpen(false);
  }

  async function handleDelete() {
    await deleteAssessment({
      courseId,
      assessmentConfigId: selectedAssessmentId,
    });
    setSelectedAssessmentId("");
    setConfirmingDelete(false);
  }

  return (
    <>
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

      {copyModalOpen && (
        <CopyAssessmentModal
          assessment={assessment}
          courses={courses}
          currentCourseId={courseId}
          isCopying={isCopying}
          onConfirm={handleCopy}
          onCancel={() => setCopyModalOpen(false)}
        />
      )}

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
          <div className="grid grid-cols-12 gap-6">
            <div className="col-span-12 space-y-6 lg:col-span-6">
              <AssessmentConfigForm
                courses={courses}
                courseId={courseId}
                onCourseIdChange={() => {}}
                hideCourseSelect={true}
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
              <section className="h-full rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
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
                              <span
                                className={`ml-2 rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                                  a.status === "published"
                                    ? "bg-primary/10 text-primary"
                                    : "bg-surface-container text-on-surface-variant"
                                }`}
                              >
                                {a.status === "published"
                                  ? "Published"
                                  : "Draft"}
                              </span>
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

            {selectedAssessmentId && !isDetailLoading && !isRubricLoading && (
              <div className="col-span-12">
                <RubricEditor
                  rows={rubricRows}
                  onRowsChange={setRubricRows}
                  disabled={!formEnabled || isPublished}
                />
              </div>
            )}

            {selectedAssessmentId && !isDetailLoading && !isPublished && (
              <div className="col-span-12">
                <QuestionEditor
                  assessmentConfigId={selectedAssessmentId}
                  mainQuestionNum={Number(numQuestions) || 0}
                  disabled={!formEnabled}
                  onQuestionAdded={(newPoolSize) => {
                    const current = Number(numQuestions);
                    if (
                      current === newPoolSize - 1 &&
                      newPoolSize <= MAX_QUESTIONS
                    ) {
                      setNumQuestions(String(newPoolSize));
                      toast.success(
                        `Question count updated to ${newPoolSize}.`,
                      );
                    }
                  }}
                />
              </div>
            )}

            <div className="col-span-12">
              <div className="flex items-center justify-between rounded-xl border border-primary/10 bg-primary/5 p-6">
                <div className="flex items-center gap-4">
                  <div>
                    <p className="text-sm font-bold text-primary">
                      {!selectedAssessmentId
                        ? "Start Editing"
                        : isPublished
                          ? "Update Published Assessment"
                          : "Publish Draft Assessment"}
                      {isDirty && !isPublished && selectedAssessmentId && (
                        <span className="ml-2 text-xs font-medium text-on-surface-variant">
                          • Unsaved changes
                        </span>
                      )}
                    </p>
                    <p className="text-[11px] text-on-surface-variant">
                      {!selectedAssessmentId
                        ? "Select an assessment above to begin editing."
                        : isPublished
                          ? "Update name and due date of the published assessment."
                          : "Change assessment parameters and publish to students."}
                    </p>
                  </div>
                </div>

                {selectedAssessmentId && (
                  <div className="flex items-center gap-3">
                    {isPublished ? (
                      <>
                        <button
                          type="button"
                          aria-label="Copy assessment"
                          title="Copy assessment"
                          className="flex h-11 w-11 items-center justify-center rounded-xl border border-outline-variant/40 bg-transparent text-on-surface-variant transition-all hover:bg-surface-container active:scale-[0.95] disabled:cursor-not-allowed disabled:opacity-50"
                          disabled={isCopying}
                          onClick={() => setCopyModalOpen(true)}
                        >
                          <span
                            className="material-symbols-outlined text-xl"
                            style={{ verticalAlign: "middle" }}
                          >
                            content_copy
                          </span>
                        </button>

                        <button
                          className="rounded-xl bg-primary px-6 py-3 text-sm font-bold tracking-tight text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
                          disabled={!canUpdatePublished || isSaving}
                          onClick={handleUpdatePublished}
                        >
                          {isSaving ? "Saving…" : "Update"}
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          type="button"
                          aria-label="Delete assessment"
                          title="Delete assessment"
                          className="flex h-11 w-11 items-center justify-center rounded-xl border border-error/30 bg-transparent text-error transition-all hover:bg-error/10 active:scale-[0.95] disabled:cursor-not-allowed disabled:opacity-50"
                          disabled={isSaving || isPublishing || isCopying}
                          onClick={() => setConfirmingDelete(true)}
                        >
                          <span
                            className="material-symbols-outlined text-xl"
                            style={{ verticalAlign: "middle" }}
                          >
                            delete
                          </span>
                        </button>

                        <button
                          type="button"
                          aria-label="Copy assessment"
                          title="Copy assessment"
                          className="flex h-11 w-11 items-center justify-center rounded-xl border border-outline-variant/40 bg-transparent text-on-surface-variant transition-all hover:bg-surface-container active:scale-[0.95] disabled:cursor-not-allowed disabled:opacity-50"
                          disabled={isSaving || isPublishing || isCopying}
                          onClick={() => setCopyModalOpen(true)}
                        >
                          <span
                            className="material-symbols-outlined text-xl"
                            style={{ verticalAlign: "middle" }}
                          >
                            content_copy
                          </span>
                        </button>

                        <div
                          aria-hidden="true"
                          className="mx-1 h-8 w-px bg-outline-variant/30"
                        />

                        <button
                          className="rounded-xl border border-primary bg-transparent px-6 py-3 text-sm font-bold tracking-tight text-primary transition-all hover:bg-primary/10 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
                          disabled={isPublishing || isSaving}
                          onClick={handlePublish}
                        >
                          {isPublishing ? "Publishing…" : "Publish"}
                        </button>

                        <button
                          className="rounded-xl bg-primary px-6 py-3 text-sm font-bold tracking-tight text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
                          disabled={!canSave || isSaving || isPublishing}
                          onClick={handleSave}
                        >
                          {isSaving ? "Saving…" : "Save"}
                        </button>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
    </>
  );
}