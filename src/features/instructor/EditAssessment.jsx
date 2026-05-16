import { useEffect, useState } from "react";
import { NavLink, useNavigate, useParams } from "react-router";
import toast from "react-hot-toast";

import { useCourses } from "../../hooks/useCourses";
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
import PageNotFound from "../../pages/PageNotFound";
import Spinner from "../../ui/Spinner";
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

export default function EditAssessment() {
  const navigate = useNavigate();
  const { courseId, assessmentId } = useParams();

  const { courses } = useCourses();
  const course = courses.find((c) => String(c.id) === String(courseId));

  const [assessmentName, setAssessmentName] = useState("");
  const [numQuestions, setNumQuestions] = useState("");
  const [assessmentTime, setAssessmentTime] = useState("");
  const [releaseTime, setReleaseTime] = useState(null);
  const [dueTime, setDueTime] = useState(null);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [confirmingPublish, setConfirmingPublish] = useState(false);
  const [copyModalOpen, setCopyModalOpen] = useState(false);
  const [rubricRows, setRubricRows] = useState([]);
  const [initialSnapshot, setInitialSnapshot] = useState(null);
  const [initializedFor, setInitializedFor] = useState(null);

  const {
    assessment,
    isLoading: isDetailLoading,
    isError: isDetailError,
  } = useAssessmentDetail(courseId, assessmentId);
  const { updateAssessment, isPending: isSaving } = useUpdateAssessment();
  const { publishAssessment, isPending: isPublishing } = usePublishAssessment();
  const { deleteAssessment, isDeleting } = useDeleteAssessment();
  const { copyAssessment, isCopying } = useCopyAssessment();
  const { rubric, isLoading: isRubricLoading } = useRubric(assessmentId);
  const { updateRubric, isPending: isSavingRubric } = useUpdateRubric();

  useEffect(() => {
    setConfirmingDelete(false);
    setCopyModalOpen(false);
  }, [assessmentId]);

  useEffect(() => {
    if (!assessment || !rubric) return;
    if (initializedFor === assessmentId) return;

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
    setInitializedFor(assessmentId);
  }, [assessment, rubric, assessmentId, initializedFor]);

  if (isDetailError) {
    return <PageNotFound />;
  }

  if (isDetailLoading) {
    return <Spinner />;
  }

  const isPublished = assessment?.status === "published";
  const formEnabled =
    !isDetailLoading && !isSaving && !isPublishing && !isDeleting;

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
        assessmentConfigId: assessmentId,
        payload: {
          title: assessmentName,
          total_time_minute: Math.round(Number(assessmentTime)),
          main_question_num: Number(numQuestions),
          release_time: releaseTime?.toISOString() ?? null,
          due_time: dueTime?.toISOString() ?? null,
        },
      });
      await updateRubric({
        assessmentConfigId: assessmentId,
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
    if (isPublishing || isSaving) return;
    try {
      await updateAssessment({
        courseId,
        assessmentConfigId: assessmentId,
        payload: {
          title: assessmentName,
          total_time_minute: Math.round(Number(assessmentTime)),
          main_question_num: Number(numQuestions),
          release_time: releaseTime?.toISOString() ?? null,
          due_time: dueTime?.toISOString() ?? null,
        },
      });
      await updateRubric({
        assessmentConfigId: assessmentId,
        rubricPayload: {
          total_points: rubricTotal(rubricRows),
          criteria_data: rubricRows.map((row) => ({
            title: row.title,
            description: row.description,
            max_points: Number(row.max_points),
          })),
        },
      });
      await publishAssessment({
        courseId,
        assessmentConfigId: assessmentId,
      });
    } catch {
      //
    } finally {
      setConfirmingPublish(false);
    }
  }

  function handleUpdatePublished() {
    if (!canUpdatePublished) return;
    updateAssessment({
      courseId,
      assessmentConfigId: assessmentId,
      payload: {
        title: assessmentName,
        due_time: dueTime?.toISOString() ?? null,
      },
    });
  }

  async function handleCopy({ targetCourseId, title }) {
    await copyAssessment({
      courseId,
      assessmentConfigId: assessmentId,
      targetCourseId,
      title,
    });
    setCopyModalOpen(false);
    navigate(`/instructor/${targetCourseId}/assessments`);
  }

  async function handleDelete() {
    await deleteAssessment({
      courseId,
      assessmentConfigId: assessmentId,
    });
    setConfirmingDelete(false);
    navigate(`/instructor/${courseId}/assessments`);
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

      {confirmingPublish && (
        <ConfirmModal
          title="Publish Assessment"
          message={`Are you sure you want to publish the assessment "${assessment?.title}"? Once published, the students gain access to it and only the name and due date can be changed. This action cannot be undone.`}
          confirmLabel="Yes, Publish"
          loadingLabel="Publishing…"
          tone="primary"
          isLoading={isSaving || isSavingRubric || isPublishing}
          onConfirm={handlePublish}
          onCancel={() => setConfirmingPublish(false)}
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

      <div className="min-h-screen">
        <main className="ml-64 px-10 pb-12 pt-24">
          <div className="mb-4">
            <NavLink
              className="group mb-4 inline-flex items-center gap-2 text-xs font-bold text-outline-variant transition-colors hover:text-primary"
              to={`/instructor/${courseId}/assessments`}
            >
              <span className="material-symbols-outlined text-sm transition-transform group-hover:-translate-x-1">
                arrow_back
              </span>
              <span className="font-body uppercase tracking-widest">
                Back to Assessments
              </span>
            </NavLink>
          </div>

          <div className="mb-8">
            <span className="mb-1 block text-xs font-bold uppercase tracking-[0.2em] text-outline">
              {course?.course_code} • {course?.course_name}
            </span>
            <h1 className="font-headline text-4xl font-extrabold tracking-tight text-on-surface">
              {assessment?.title ?? "Edit Assessment"}
            </h1>
            {assessment &&
              (isPublished ? (
                <span className="mt-2 inline-block rounded-md bg-primary/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-primary">
                  Published
                </span>
              ) : (
                <span className="mt-2 inline-block rounded-md bg-surface-container px-3 py-1 text-xs font-bold uppercase tracking-wider text-on-surface-variant">
                  Draft
                </span>
              ))}
          </div>

          <div className="grid grid-cols-12 gap-6">
            <div className="col-span-12 space-y-6 lg:col-span-8">
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

            {!isRubricLoading && (
              <div className="col-span-12">
                <RubricEditor
                  rows={rubricRows}
                  onRowsChange={setRubricRows}
                  disabled={!formEnabled || isPublished}
                />
              </div>
            )}

            {!isPublished && (
              <div className="col-span-12">
                <QuestionEditor
                  assessmentConfigId={assessmentId}
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
                <div>
                  <p className="text-sm font-bold text-primary">
                    {isPublished
                      ? "Update Published Assessment"
                      : "Publish Draft Assessment"}
                    {isDirty && !isPublished && (
                      <span className="ml-2 text-xs font-medium text-on-surface-variant">
                        • Unsaved changes
                      </span>
                    )}
                  </p>
                  <p className="text-[11px] text-on-surface-variant">
                    {isPublished
                      ? "Copy published assessments and update name and due date of published assessments."
                      : "Change assessment parameters, copy and delete assessments and publish to students."}
                  </p>
                </div>

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
                        onClick={() => setConfirmingPublish(true)}
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
              </div>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
