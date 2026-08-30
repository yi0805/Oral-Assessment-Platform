import { useState } from "react";
import { NavLink, useParams } from "react-router";
import toast from "react-hot-toast";

import { useCourses } from "../../hooks/useCourses";
import { useUploadMaterial } from "./useUploadMaterial";
import { useUploadGithubRepo } from "./useUploadGithubRepo";
import { useCreateRubric } from "./useCreateRubric";
import { useQuestionGenerate } from "./useQuestionGenerate";
import { useDeleteQuestion } from "./useDeleteQuestion";
import { useUpdateQuestion } from "./useUpdateQuestion";
import { usePublishAssessment } from "./usePublishAssessment";
import {
  getMaterialStatus,
  retryMaterialProcessing,
} from "../../services/apiMaterial";
import { getQuestionSupportingContext } from "../../services/apiQuestion";
import { getErrorMessage } from "../../utils/getErrorMessage";

import AssessmentConfigForm from "./AssessmentConfigForm";
import RubricEditor from "./RubricEditor";
import {
  isAssessmentConfigValid,
  isRubricValid,
  makeBlankRubricRow,
  rubricTotal,
} from "./assessmentFormUtils";

const GITHUB_URL_RE = /^https?:\/\/github\.com\/[^/\s]+\/[^/\s#?]+/i;
const isValidGithubUrl = (u) => GITHUB_URL_RE.test((u || "").trim());

function GeneratePanel() {
  const { courseId } = useParams();
  const { courses } = useCourses();
  const course = courses.find((c) => String(c.id) === String(courseId));
  const [materialFiles, setMaterialFiles] = useState([]);

  const [source, setSource] = useState("pdf");
  const [githubUrl, setGithubUrl] = useState("");
  const [githubRef, setGithubRef] = useState("");

  const [assessmentConfigId, setAssessmentConfigId] = useState(null);
  const [assessmentName, setAssessmentName] = useState("");

  const [numQuestions, setNumQuestions] = useState("");
  const [assessmentTime, setAssessmentTime] = useState("");
  const [bufferTime, setBufferTime] = useState("");

  const [releaseTime, setReleaseTime] = useState(null);
  const [dueTime, setDueTime] = useState(null);

  const [githubUrlTouched, setGithubUrlTouched] = useState(false);

  const [phase, setPhase] = useState("setup");
  const [statusMessage, setStatusMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const [questions, setQuestions] = useState([]);
  const [materialStates, setMaterialStates] = useState([]);
  const [supportingContexts, setSupportingContexts] = useState({});

  const [editingId, setEditingId] = useState(null);
  const [editText, setEditText] = useState("");

  const [sessionsCreated, setSessionsCreated] = useState(0);

  const [rubricRows, setRubricRows] = useState([makeBlankRubricRow()]);

  const { uploadMaterial } = useUploadMaterial();
  const { uploadGithubRepo } = useUploadGithubRepo();
  const { createRubric } = useCreateRubric();

  const { questionGenerate } = useQuestionGenerate();

  const { updateQuestion } = useUpdateQuestion();
  const { deleteQuestion } = useDeleteQuestion();
  const { publishAssessment } = usePublishAssessment();

  const githubUrlError =
    source === "github" && githubUrl && !isValidGithubUrl(githubUrl)
      ? "Must be a github.com HTTPS URL."
      : "";

  const materialReady =
    (source === "pdf" &&
      materialFiles.length > 0 &&
      materialFiles.length <= 5) ||
    (source === "github" && isValidGithubUrl(githubUrl));

  const configValid = isAssessmentConfigValid({
    assessmentName,
    numQuestions,
    assessmentTime,
    bufferTime,
  });

  const isValid = configValid && materialReady && isRubricValid(rubricRows);

  function updateMaterialStates(nextStatuses) {
    setMaterialStates((previous) => {
      const byId = new Map(previous.map((item) => [item.id, item]));
      nextStatuses.forEach((item) => byId.set(item.id, { ...byId.get(item.id), ...item }));
      return [...byId.values()];
    });
  }

  async function waitForMaterialsReady(materials) {
    for (let attempt = 0; attempt < 120; attempt += 1) {
      const statuses = await Promise.all(
        materials.map(({ id }) => getMaterialStatus(courseId, id)),
      );
      updateMaterialStates(statuses);

      if (statuses.some(({ processing_status: state }) => state === "failed")) {
        throw new Error(
          "One or more materials could not be processed. Retry the failed material before generating questions.",
        );
      }
      if (statuses.some((material) => material.is_processing_stale)) {
        throw new Error(
          "Processing appears to have been interrupted. Retry the material before generating questions.",
        );
      }
      if (statuses.every(({ processing_status: state }) => state === "ready")) {
        return statuses;
      }

      setStatusMessage("Processing material. Question generation will start when it is ready...");
      await new Promise((resolve) => setTimeout(resolve, 1500));
    }
    throw new Error("Material processing is taking longer than expected. Please try again shortly.");
  }

  async function handleRetryMaterial(materialId) {
    try {
      setLoading(true);
      const status = await retryMaterialProcessing(courseId, materialId);
      updateMaterialStates([status]);
      toast.success("Material processing retry started.");
    } catch (error) {
      toast.error(getErrorMessage(error, "Could not restart material processing."));
    } finally {
      setLoading(false);
    }
  }

  async function handleViewSupportingContext(questionId) {
    try {
      const context = await getQuestionSupportingContext(questionId);
      setSupportingContexts((previous) => ({ ...previous, [questionId]: context }));
    } catch (error) {
      toast.error(getErrorMessage(error, "Supporting context is unavailable."));
    }
  }

  async function handleSubmit() {
    try {
      setLoading(true);
      setStatusMessage(
        source === "github"
          ? "Importing GitHub repository..."
          : "Uploading material...",
      );

      const uploadedMaterials = [];
      if (source === "pdf") {
        for (const file of materialFiles) {
          const uploaded = await uploadMaterial({ courseId, file });
          uploadedMaterials.push({ ...uploaded, filename: file.name });
          updateMaterialStates(uploadedMaterials);
        }
      } else {
        const uploaded = await uploadGithubRepo({
          courseId,
          url: githubUrl.trim(),
          ref: githubRef.trim() || null,
        });
        uploadedMaterials.push({ ...uploaded, filename: "GitHub repository" });
        updateMaterialStates(uploadedMaterials);
      }

      const readyMaterials = await waitForMaterialsReady(uploadedMaterials);
      const materialIds = readyMaterials.map(({ id }) => id);

      setStatusMessage("Creating rubric...");
      const rubricPayload = {
        total_points: rubricTotal(rubricRows),
        criteria_data: rubricRows.map((row) => ({
          title: row.title,
          description: row.description,
          max_points: Number(row.max_points),
        })),
      };
      const rubricResponse = await createRubric({
        courseId,
        rubricPayload,
      });
      const RubricId = rubricResponse.id;

      const release = releaseTime?.toISOString();
      const due = dueTime?.toISOString();

      setStatusMessage("Generating questions with AI...");
      const updateResponse = await questionGenerate({
        courseId,
        materialIds,
        rubricId: RubricId,
        assessmentName,
        numQuestions: Number(numQuestions),
        totalTime: Number(assessmentTime),
        bufferTime: bufferTime === "" ? 0 : Number(bufferTime),
        releaseTime: release,
        dueTime: due,
      });

      setQuestions(updateResponse.questions);
      setAssessmentConfigId(updateResponse.assessment_config);
      setPhase("review");
    } catch (error) {
      toast.error(getErrorMessage(error, "Could not generate questions."));
    } finally {
      setStatusMessage("");
      setLoading(false);
    }
  }

  async function handleDelete(questionId) {
    try {
      setLoading(true);
      await deleteQuestion({ questionId });
      setQuestions((prev) => prev.filter((q) => q.id !== questionId));
    } finally {
      setLoading(false);
    }
  }

  async function handleUpdate(questionId, questionText) {
    try {
      setLoading(true);
      await updateQuestion({ questionId, questionText });
      setQuestions((prev) =>
        prev.map((q) =>
          q.id === questionId ? { ...q, question_text: questionText } : q,
        ),
      );
    } finally {
      setLoading(false);
    }
  }

  async function handlePublish() {
    try {
      setLoading(true);
      setStatusMessage("Publishing assessment...");

      const response = await publishAssessment({
        courseId,
        assessmentConfigId,
      });

      setSessionsCreated(response.sessions_created);
      setPhase("published");
    } finally {
      setStatusMessage("");
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen">
      <main className="px-10 pb-12 pt-24">
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
            Generate Assessment
          </h1>
          <p className="mt-2 text-sm text-on-surface-variant">
            Upload material and let AI generate questions for a new assessment.
          </p>
        </div>

        {statusMessage && (
          <div className="mb-6 flex items-center gap-3 rounded-xl border border-primary/20 bg-primary/5 p-4 text-sm text-primary">
            <span className="material-symbols-outlined animate-spin text-lg">
              progress_activity
            </span>

            {statusMessage}
          </div>
        )}

        {materialStates.length > 0 && phase === "setup" && (
          <div className="mb-6 rounded-xl border border-outline-variant/15 bg-surface-container-low p-4">
            <p className="mb-3 text-sm font-bold text-on-surface">Material processing</p>
            <div className="space-y-2">
              {materialStates.map((material) => (
                <div key={material.id} className="text-sm">
                  <div className="flex items-center justify-between gap-3">
                    <span className="min-w-0 truncate text-on-surface-variant">
                      {material.filename || "Material"}
                    </span>
                    <div className="flex shrink-0 items-center gap-2">
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-semibold ${
                        material.processing_status === "ready"
                          ? "bg-primary/10 text-primary"
                          : material.processing_status === "failed" || material.is_processing_stale
                            ? "bg-error/10 text-error"
                            : "bg-surface-container-high text-on-surface-variant"
                      }`}
                    >
                      {material.processing_status === "ready"
                        ? "Ready"
                        : material.processing_status === "failed"
                          ? "Failed"
                          : material.is_processing_stale
                            ? "Interrupted"
                          : "Processing"}
                    </span>
                    {(material.processing_status === "failed" || material.is_processing_stale) && (
                      <button
                        type="button"
                        className="rounded-lg px-2 py-1 text-xs font-bold text-primary hover:bg-primary/10"
                        onClick={() => handleRetryMaterial(material.id)}
                        disabled={loading}
                      >
                        Retry
                      </button>
                    )}
                    </div>
                  </div>
                  {material.is_processing_stale && (
                    <p className="text-xs text-error">
                      Processing appears to have been interrupted.
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {phase === "published" && (
          <div className="mb-8 rounded-xl border border-primary/20 bg-primary/5 p-8 text-center">
            <span className="material-symbols-outlined mb-4 text-5xl text-primary">
              check_circle
            </span>

            <h2 className="mb-2 text-2xl font-bold text-primary">
              Assessment Published
            </h2>

            <p className="text-on-surface-variant">
              {sessionsCreated} student{sessionsCreated !== 1 ? "s" : ""} can
              now take this assessment.
            </p>
          </div>
        )}

        {phase === "setup" && (
          <div className="grid grid-cols-12 items-start gap-6">
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
                bufferTime={bufferTime}
                onBufferTimeChange={setBufferTime}
                releaseTime={releaseTime}
                onReleaseTimeChange={setReleaseTime}
                dueTime={dueTime}
                onDueTimeChange={setDueTime}
              />
            </div>

            <div className="col-span-12 flex flex-col gap-4 lg:col-span-6">
              <div
                className="flex rounded-xl bg-surface-container-low p-1"
                role="tablist"
                aria-label="Material source"
              >
                <button
                  type="button"
                  role="tab"
                  aria-selected={source === "pdf"}
                  onClick={() => setSource("pdf")}
                  className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-bold transition-all ${
                    source === "pdf"
                      ? "bg-surface-container-lowest text-primary shadow-sm"
                      : "text-on-surface-variant hover:text-on-surface"
                  }`}
                >
                  <span className="material-symbols-outlined text-lg">
                    picture_as_pdf
                  </span>
                  PDF Upload
                </button>

                <button
                  type="button"
                  role="tab"
                  aria-selected={source === "github"}
                  onClick={() => setSource("github")}
                  className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-bold transition-all ${
                    source === "github"
                      ? "bg-surface-container-lowest text-primary shadow-sm"
                      : "text-on-surface-variant hover:text-on-surface"
                  }`}
                >
                  <span className="material-symbols-outlined text-lg">
                    code
                  </span>
                  GitHub Repo
                </button>
              </div>

              {source === "pdf" ? (
                <section className="flex flex-1 flex-col rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
                  <div className="mb-6 flex items-start gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <span
                        className="material-symbols-outlined text-xl"
                        data-icon="upload_file"
                        style={{ verticalAlign: "middle" }}
                      >
                        upload_file
                      </span>
                    </div>

                    <div>
                      <h3 className="text-xl font-bold text-on-surface">
                        Assessment Material
                      </h3>

                      <p className="mt-1 max-w-md text-xs text-on-surface-variant">
                        Upload a PDF of the source material — we&apos;ll use it
                        to generate every question.
                      </p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <label className="block cursor-pointer">
                      <input
                        className="hidden"
                        type="file"
                        accept=".pdf"
                        multiple
                        onChange={(e) => {
                          const incoming = Array.from(e.target.files || []);

                          setMaterialFiles((prev) => {
                            const seen = new Set(
                              prev.map((f) => `${f.name}:${f.size}`),
                            );

                            const additions = incoming.filter(
                              (f) => !seen.has(`${f.name}:${f.size}`),
                            );

                            return [...prev, ...additions].slice(0, 5);
                          });
                          e.target.value = "";
                        }}
                      />

                      <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-outline-variant/30 bg-surface-container-low px-6 py-10 text-center transition-colors hover:border-primary/40 hover:bg-primary/5">
                        <span
                          className="material-symbols-outlined mb-2 text-3xl text-primary"
                          data-icon="cloud_upload"
                          style={{ verticalAlign: "middle" }}
                        >
                          cloud_upload
                        </span>

                        <p className="text-sm font-bold text-primary">
                          {materialFiles.length === 0
                            ? "Click to browse PDFs"
                            : `Add more PDFs (${materialFiles.length}/5)`}
                        </p>

                        <p className="mt-1 text-[11px] text-outline">
                          PDF only · Up to 5 files · Max 50 MB each
                        </p>
                      </div>
                    </label>

                    {materialFiles.length > 0 && (
                      <div className="space-y-2">
                        {materialFiles.map((file, index) => (
                          <div
                            key={`${file.name}-${file.size}-${index}`}
                            className="flex items-center gap-3 rounded-xl border border-outline-variant/10 bg-surface-container-low p-4 text-left"
                          >
                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-error/10 text-error">
                              <span
                                className="material-symbols-outlined text-2xl"
                                data-icon="picture_as_pdf"
                                style={{ verticalAlign: "middle" }}
                              >
                                picture_as_pdf
                              </span>
                            </div>

                            <div className="min-w-0 flex-1">
                              <p className="truncate text-sm font-semibold text-on-surface">
                                {file.name}
                              </p>

                              <p className="text-xs text-outline">
                                {(file.size / 1024 / 1024).toFixed(1)} MB
                              </p>
                            </div>

                            <button
                              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-on-surface-variant transition-colors hover:bg-error/10 hover:text-error"
                              onClick={() =>
                                setMaterialFiles((prev) =>
                                  prev.filter((_, i) => i !== index),
                                )
                              }
                              aria-label={`Remove ${file.name}`}
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
                        ))}
                      </div>
                    )}
                  </div>
                </section>
              ) : (
                <section className="flex flex-1 flex-col rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
                  <div className="mb-6 flex items-start gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <span
                        className="material-symbols-outlined text-xl"
                        data-icon="hub"
                        style={{ verticalAlign: "middle" }}
                      >
                        hub
                      </span>
                    </div>

                    <div>
                      <h3 className="text-xl font-bold text-on-surface">
                        GitHub Repository
                      </h3>

                      <p className="mt-1 max-w-md text-xs text-on-surface-variant">
                        Paste a public GitHub repo URL — we&apos;ll import its
                        markdown, docs, and source files to generate questions.
                      </p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="space-y-2">
                      <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                        Repository URL
                      </label>

                      <input
                        className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all placeholder:text-outline focus:ring-2 focus:ring-primary/20"
                        type="url"
                        inputMode="url"
                        autoComplete="off"
                        spellCheck="false"
                        placeholder="https://github.com/owner/repo"
                        value={githubUrl}
                        onChange={(e) => setGithubUrl(e.target.value)}
                        onBlur={() => setGithubUrlTouched(true)}
                      />

                      {githubUrlTouched && githubUrlError && (
                        <p className="ml-1 text-xs font-medium text-error">
                          {githubUrlError}
                        </p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                        Branch{" "}
                        <span className="font-normal text-outline">
                          (optional)
                        </span>
                      </label>

                      <input
                        className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all placeholder:text-outline focus:ring-2 focus:ring-primary/20"
                        type="text"
                        autoComplete="off"
                        spellCheck="false"
                        placeholder="main"
                        value={githubRef}
                        onChange={(e) => setGithubRef(e.target.value)}
                      />
                    </div>

                    <p className="text-[11px] text-outline">
                      Public repos only · Up to 2 MB of text (markdown, docs,
                      source)
                    </p>
                  </div>
                </section>
              )}
            </div>

            <div className="col-span-12">
              <RubricEditor rows={rubricRows} onRowsChange={setRubricRows} />
            </div>

            <div className="col-span-12">
              <div className="flex items-center justify-between rounded-xl border border-primary/10 bg-primary/5 p-6">
                <div className="flex items-center gap-4">
                  <div className="rounded-lg bg-primary/10 p-3 text-primary">
                    <span
                      className="material-symbols-outlined"
                      data-icon="auto_awesome"
                      style={{ verticalAlign: "middle" }}
                    >
                      auto_awesome
                    </span>
                  </div>

                  <div>
                    <p className="text-sm font-bold text-primary">
                      AI Question Generation
                    </p>

                    <p className="text-[11px] text-on-surface-variant">
                      Update questions based on material
                    </p>
                  </div>
                </div>

                <button
                  className="rounded-xl bg-primary px-6 py-3 text-sm font-bold tracking-tight text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={!isValid || loading}
                  onClick={handleSubmit}
                >
                  {loading ? "Processing..." : "Generate Questions"}
                </button>
              </div>
            </div>
          </div>
        )}

        {phase === "review" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-on-surface">
                Review Generated Questions ({questions.length})
              </h2>
              <div className="flex-row-reverse">
                <NavLink
                  className="rounded-xl bg-primary px-8 py-3 text-sm font-bold text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-[0.98] disabled:opacity-50"
                  to={`/instructor/${courseId}/assessments`}
                  onClick={() => {
                    toast.success("Assessment saved successfully.");
                  }}
                >
                  <span>Save Assessment</span>
                </NavLink>
                <button
                  className="ml-3 rounded-xl bg-primary px-8 py-3 text-sm font-bold text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-[0.98] disabled:opacity-50"
                  onClick={handlePublish}
                  disabled={loading || questions.length === 0}
                >
                  {loading ? "Working..." : "Publish & Release"}
                </button>
              </div>
            </div>

            <p className="text-sm text-on-surface-variant">
              Review the AI-generated questions below. You can edit or delete
              any question before publishing.
            </p>

            <div className="space-y-4">
              {questions.map((question, index) => (
                <div
                  key={question.id}
                  className="rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-sm"
                >
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                      Question {index + 1}
                      {question.difficulty && (
                        <span className="ml-2 rounded bg-primary/10 px-2 py-0.5 text-[10px] font-semibold text-primary">
                          {question.difficulty}
                        </span>
                      )}
                    </span>

                    <div className="flex gap-2">
                      {editingId !== question.id && (
                        <>
                          {question.generation_provenance && (
                            <button
                              className="rounded-lg px-3 py-1 text-xs font-bold text-primary transition-all hover:bg-primary/10"
                              onClick={() => handleViewSupportingContext(question.id)}
                            >
                              View supporting context
                            </button>
                          )}
                          <button
                            className="rounded-lg px-3 py-1 text-xs font-bold text-primary transition-all hover:bg-primary/10"
                            onClick={() => {
                              setEditingId(question.id);
                              setEditText(question.question_text);
                            }}
                          >
                            Edit
                          </button>

                          <button
                            className="rounded-lg px-3 py-1 text-xs font-bold text-error transition-all hover:bg-error/10"
                            onClick={() => handleDelete(question.id)}
                          >
                            Delete
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {editingId === question.id ? (
                    <div className="space-y-3">
                      <textarea
                        className="min-h-[80px] w-full resize-none rounded-xl border border-outline-variant/30 bg-surface-container-low px-4 py-3 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                        value={editText}
                        onChange={(e) => setEditText(e.target.value)}
                      />

                      <div className="flex gap-2">
                        <button
                          className="rounded-lg bg-primary px-4 py-1.5 text-xs font-bold text-on-primary"
                          onClick={() => {
                            handleUpdate(question.id, editText);
                            setEditingId(null);
                          }}
                        >
                          Save
                        </button>

                        <button
                          className="rounded-lg px-4 py-1.5 text-xs font-bold text-on-surface-variant hover:bg-surface-container-high"
                          onClick={() => setEditingId(null)}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm leading-relaxed text-on-surface">
                      {question.question_text}
                    </p>
                  )}

                  {question.learning_objective && (
                    <p className="mt-2 text-[11px] text-on-surface-variant">
                      Objective: {question.learning_objective}
                    </p>
                  )}

                  {supportingContexts[question.id] && (
                    <div className="mt-4 rounded-xl bg-surface-container-low p-4 text-sm">
                      <p className="font-bold text-on-surface">
                        Supporting context used for generation
                      </p>
                      <p className="mt-1 text-xs text-on-surface-variant">
                        {supportingContexts[question.id].model &&
                          `Model: ${supportingContexts[question.id].model}`}
                        {supportingContexts[question.id].generated_at &&
                          ` · Generated: ${new Date(supportingContexts[question.id].generated_at).toLocaleString()}`}
                      </p>
                      <div className="mt-3 space-y-3">
                        {supportingContexts[question.id].contexts.map((context) => (
                          <div key={context.chunk_id} className="rounded-lg bg-surface-container-lowest p-3">
                            <p className="mb-1 text-xs font-semibold text-on-surface-variant">
                              {context.material_filename} · section {context.chunk_index + 1}
                            </p>
                            <p className="whitespace-pre-wrap text-on-surface">{context.text}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {questions.length === 0 && (
              <div className="rounded-xl border-2 border-dashed border-outline-variant/20 p-12 text-center">
                <p className="text-sm text-on-surface-variant">
                  All questions have been deleted. Go back to generate new ones.
                </p>

                <button
                  className="mt-4 rounded-xl bg-primary px-6 py-2 text-sm font-bold text-on-primary"
                  onClick={() => setPhase("setup")}
                >
                  Back to Setup
                </button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default GeneratePanel;
