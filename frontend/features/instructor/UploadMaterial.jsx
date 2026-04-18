import { useEffect, useState } from "react";

import { useCourses } from "../../hooks/useCourses";
import { useUploadMaterial } from "./useUploadMaterial";
import { useCreateRubric } from "./useCreateRubric";
import { useQuestionGenerate } from "./useQuestionGenerate";
import { useDeleteQuestion } from "./useDeleteQuestion";
import { useUpdateQuestion } from "./useUpdateQuestion";
import { usePublishAssessment } from "./usePublishAssessment";

import Spinner from "../../ui/Spinner";
import DateTimePicker from "../../ui/DateTimePicker";

function UpdateMaterial() {
  const [materialFile, setMaterialFile] = useState(null);
  const [courseId, setCourseId] = useState("");

  const [assessmentConfigId, setAssessmentConfigId] = useState(null);
  const [assessmentName, setAssessmentName] = useState("");

  const [numQuestions, setNumQuestions] = useState("");
  const [assessmentTime, setAssessmentTime] = useState("");

  const [show, setShow] = useState(false);
  const [selectedDate, setSelectedDate] = useState(null);
  const [releaseTime, setReleaseTime] = useState(null);
  const [dueTime, setDueTime] = useState(null);
  
  const [touched, setTouched] = useState({
    assessmentName: false,
    numQuestions: false,
    assessmentTime: false,
  });

  const [phase, setPhase] = useState("setup");
  const [statusMessage, setStatusMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const [questions, setQuestions] = useState([]);

  const [editingId, setEditingId] = useState(null);
  const [editText, setEditText] = useState("");

  const [sessionsCreated, setSessionsCreated] = useState(0);

  const [rubricRows, setRubricRows] = useState([
    { title: "", description: "", max_points: 0 }
  ]);
  const totalPoints = rubricRows.reduce(
    (sum, row) => sum + (Number(row.max_points) || 0), 0
  );

  const { courses, isLoading } = useCourses();

  const { uploadMaterial } = useUploadMaterial();
  const { createRubric } = useCreateRubric();

  const { questionGenerate } = useQuestionGenerate();

  const { updateQuestion } = useUpdateQuestion();
  const { deleteQuestion } = useDeleteQuestion();
  const { publishAssessment } = usePublishAssessment();

  useEffect(() => {
    if (courses.length > 0 && !courseId) {
      setCourseId(courses[0].id);
    }
  }, [courses, courseId]);

  if (isLoading) return <Spinner />;

  const num = Number(numQuestions);
  const max_q = 50
  const time = Number(assessmentTime);
  const max_time = 120

  const assessmentNameError =
    assessmentName.trim() === "" ? "Assessment name is required." : "";

  const numQuestionsError =
    numQuestions === ""
      ? "Number of questions is required."
      : !Number.isInteger(num)
        ? "Must be a whole number."
        : num < 1 || num > max_q
          ? "Must be between 1 and " + str(max_q) + "."
          : "";

  const assessmentTimeError =
    assessmentTime === ""
      ? "Assessment time is required."
      : !Number.isFinite(time)
        ? "Must be a number."
        : time < 1 || time > max_time
          ? "Must be between 1 and " + str(max_time) + "."
          : "";

  const isRubricValid = 
    rubricRows.every(r => 
      r.title.trim() !== "" && 
      r.description.trim() !== "" && 
      r.max_points > 0
    );

  const isValid =
    !numQuestionsError &&
    !assessmentTimeError &&
    !assessmentNameError &&
    materialFile&&
    isRubricValid;

  async function handleSubmit() {
    try {
      setLoading(true);
      setStatusMessage("Uploading material...");

      const MaterialId = await uploadMaterial({
        courseId,
        file: materialFile,
      });

      setStatusMessage("Creating rubric...");
      const rubricPayload = {
        total_points: totalPoints,
        criteria_data: rubricRows.map(row => ({
          title: row.title,
          description: row.description,
          max_points: Number(row.max_points)
        }))
      };
      const rubricResponse = await createRubric({
        courseId,
        rubricPayload
      });
      const RubricId = rubricResponse.id;

      console.log({
        releaseTime,
        dueTime,
      });

      const release = releaseTime?.toISOString();
      const due = dueTime?.toISOString();
      
      setStatusMessage("Generating questions with AI...");
      const updateResponse = await questionGenerate({
        courseId,
        materialId: MaterialId,
        rubricId: RubricId,
        assessmentName,
        numQuestions,
        totalTime: time,
        releaseTime: release,
        dueTime: due, 
      });

      setQuestions(updateResponse.questions);
      setAssessmentConfigId(updateResponse.assessment_config);
      setPhase("review");
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

  function handleAddRow() {
    setRubricRows([
      ...rubricRows,
      { title: "", description: "", maxpoints: 0 },
    ]);
  }

  function handleRemoveRow(index) {
    if (rubricRows.length > 1) {
      setRubricRows(rubricRows.filter((_, i) => i !== index));
    }
  }

  function handleRowChange(index, field, value) {
    const updatedRows = rubricRows.map((row, i) => {
      if (i === index) {
        if (field === "max_points") {
          if (value === "") return { ...row, [field]: 0 };
          const numericValue = parseFloat(value);
          return { ...row, [field]: Math.max(0, numericValue) };
        }
        return { ...row, [field]: value };
      }
      return row;
    });
    setRubricRows(updatedRows);
  }

  return (
    <div className="min-h-screen">
      <main className="ml-64 min-h-screen pt-16">
        <div className="mx-auto max-w-6xl px-8 py-12">
          <div className="mb-10">
            <h1 className="text-4xl font-extrabold tracking-tight text-on-background">
              New Assessment Setup
            </h1>
          </div>

          {statusMessage && (
            <div className="mb-6 flex items-center gap-3 rounded-xl border border-primary/20 bg-primary/5 p-4 text-sm text-primary">
              <span className="material-symbols-outlined animate-spin text-lg">
                progress_activity
              </span>

              {statusMessage}
              <button
                className="ml-4 font-bold underline"
                onClick={() => {
                  setStatusMessage("");
                  setLoading(false);
                }}
              >
                Dismiss
              </button>
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
              <div className="col-span-12 space-y-6 lg:col-span-5">
                <section className="h-full rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
                  <h2 className="mb-6 flex items-center gap-2 text-xl font-bold">
                    <span
                      className="material-symbols-outlined text-primary"
                      data-icon="description"
                      style={{ verticalAlign: "middle" }}
                    >
                      description
                    </span>
                    Assessment Parameters
                  </h2>

                  <form className="space-y-6">
                    <div className="space-y-2">
                      <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                        Select Course
                      </label>

                      <div className="group relative">
                        <select
                          className="w-full cursor-pointer appearance-none rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all focus:ring-2 focus:ring-primary/20"
                          value={courseId}
                          onChange={(e) => setCourseId(e.target.value)}
                        >
                          {courses.map((c) => (
                            <option key={c.id} value={c.id}>
                              {c.course_code || "Unknown Course"}
                            </option>
                          ))}
                        </select>

                        <span
                          className="material-symbols-outlined pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-on-surface-variant"
                          data-icon="expand_more"
                          style={{ verticalAlign: "middle" }}
                        >
                          expand_more
                        </span>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                        Assessment Name
                      </label>

                      <input
                        className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all placeholder:text-outline focus:ring-2 focus:ring-primary/20"
                        placeholder="e.g. A1 Intro to Python"
                        type="text"
                        value={assessmentName}
                        onChange={(e) => setAssessmentName(e.target.value)}
                        onBlur={() =>
                          setTouched((current) => ({
                            ...current,
                            assessmentName: true,
                          }))
                        }
                      />

                      {touched.assessmentName && assessmentNameError && (
                        <p className="ml-1 text-xs font-medium text-error">
                          {assessmentNameError}
                        </p>
                      )}
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="space-y-2">
                        <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                          No. of Questions
                        </label>
                        <input
                          className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all placeholder:text-outline focus:ring-2 focus:ring-primary/20"
                          min={1}
                          max={max_q}
                          step={1}
                          placeholder="e.g. 15"
                          type="number"
                          value={numQuestions}
                          onChange={(e) => setNumQuestions(e.target.value)}
                          onBlur={() =>
                            setTouched((current) => ({
                              ...current,
                              numQuestions: true,
                            }))
                          }
                        />
                        {touched.numQuestions && numQuestionsError && (
                          <p className="ml-1 text-xs font-medium text-error">
                            {numQuestionsError}
                          </p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                          Total Timer (mins)
                        </label>
                        <input
                          className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all placeholder:text-outline focus:ring-2 focus:ring-primary/20"
                          min={1}
                          max={max_time}
                          step={0.5}
                          placeholder="e.g. 30"
                          type="number"
                          value={assessmentTime}
                          onChange={(e) => setAssessmentTime(e.target.value)}
                          onBlur={() =>
                            setTouched((current) => ({
                              ...current,
                              assessmentTime: true,
                            }))
                          }
                        />
                        {touched.assessmentTime && assessmentTimeError && (
                          <p className="ml-1 text-xs font-medium text-error">
                            {assessmentTimeError}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2 ">
                      <DateTimePicker
                        label="Release Date"
                        value={releaseTime}
                        onChange={setReleaseTime}
                      />

                      <DateTimePicker
                        label="Due date"
                        value={dueTime}
                        onChange={setDueTime}
                        minDate={releaseTime}
                      />
                    </div>
                    
                  </form>
                </section>
              </div>

              <div className="col-span-12 space-y-6 lg:col-span-7">
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                  <section className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-outline-variant/30 bg-surface-container-low p-6 text-center">
                    <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-surface-container-lowest shadow-sm">
                      <span
                        className="material-symbols-outlined text-2xl text-primary"
                        data-icon="upload_file"
                        style={{ verticalAlign: "middle" }}
                      >
                        upload_file
                      </span>
                    </div>
                    <h1 className="mb-1 text-base font-bold">Assessment PDF</h1>
                    <p className="mb-4 px-2 text-[13px] text-on-surface-variant">
                      Upload the source material or a previous assessment to
                      refine your questions.
                    </p>

                    <div className="w-full space-y-3">
                      {materialFile && (
                        <div className="flex items-center gap-3 rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-3 text-left shadow-sm">
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-error/10 text-error">
                            <span
                              className="material-symbols-outlined text-xl"
                              data-icon="picture_as_pdf"
                              style={{ verticalAlign: "middle" }}
                            >
                              picture_as_pdf
                            </span>
                          </div>

                          <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-semibold">
                              {materialFile.name}
                            </p>

                            <p className="text-[9px] text-outline">
                              {(materialFile.size / 1024 / 1024).toFixed(1)} MB
                            </p>
                          </div>

                          <button
                            className="text-on-surface-variant transition-colors hover:text-error"
                            onClick={() => setMaterialFile(null)}
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
                      )}

                      <label className="block cursor-pointer">
                        <input
                          className="hidden"
                          type="file"
                          accept=".pdf"
                          onChange={(e) =>
                            setMaterialFile(e.target.files[0] || null)
                          }
                        />

                        <div className="w-full rounded-xl border border-outline-variant/20 bg-white py-2.5 text-center text-xs font-bold text-primary transition-all hover:bg-primary/5">
                          Browse Files
                        </div>
                      </label>
                    </div>
                  </section>

                  {/* <section className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-outline-variant/30 bg-surface-container-low p-6 text-center">
                    <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-surface-container-lowest shadow-sm">
                      <span
                        className="material-symbols-outlined text-2xl text-secondary"
                        data-icon="rule"
                        style={{ verticalAlign: "middle" }}
                      >
                        rule
                      </span>
                    </div>

                    <h3 className="mb-1 text-base font-bold">
                      Assessment Rubrics
                    </h3>

                    <p className="mb-4 px-2 text-[11px] text-on-surface-variant">
                      Upload evaluation criteria for precise grading.
                    </p>

                    <div className="w-full space-y-3">
                      {rubricFile && (
                        <div className="flex items-center gap-3 rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-3 text-left shadow-sm">
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-secondary/10 text-secondary">
                            <span className="material-symbols-outlined text-xl">
                              picture_as_pdf
                            </span>
                          </div>

                          <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-semibold">
                              {rubricFile.name}
                            </p>

                            <p className="text-[9px] text-outline">
                              {(rubricFile.size / 1024 / 1024).toFixed(1)} MB
                            </p>
                          </div>

                          <button
                            className="text-on-surface-variant transition-colors hover:text-error"
                            onClick={() => setRubricFile(null)}
                          >
                            <span className="material-symbols-outlined text-lg">
                              close
                            </span>
                          </button>
                        </div>
                      )}

                      <label className="block cursor-pointer">
                        <input
                          className="hidden"
                          type="file"
                          accept=".pdf"
                          onChange={(e) =>
                            setRubricFile(e.target.files[0] || null)
                          }
                        />

                        <div className="w-full rounded-xl border border-outline-variant/20 bg-white py-2.5 text-center text-xs font-bold text-primary transition-all hover:bg-primary/5">
                          Browse Files
                        </div>
                      </label>
                    </div>
                  </section> */}
                </div>

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

                <button
                  className="rounded-xl bg-primary px-8 py-3 text-sm font-bold text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-[0.98] disabled:opacity-50"
                  onClick={handlePublish}
                  disabled={loading || questions.length === 0}
                >
                  {loading ? "Working..." : "Publish Assessment"}
                </button>
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
                  </div>
                ))}
              </div>

              {questions.length === 0 && (
                <div className="rounded-xl border-2 border-dashed border-outline-variant/20 p-12 text-center">
                  <p className="text-sm text-on-surface-variant">
                    All questions have been deleted. Go back to generate new
                    ones.
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

          {phase === "setup" && (
            <div className="mt-6 grid grid-cols-12 gap-6">
              <div className="col-span-12">
                <section className="rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
                  <div className="mb-6 flex items-center justify-between">
                    <h2 className="flex items-center gap-2 text-xl font-bold">
                      <span className="material-symbols-outlined text-secondary">
                        assignment
                      </span>
                      Grading Rubric
                    </h2>
                    
                    {/* show total points */}
                    <div className="flex items-center gap-4">
                      <span className="text-sm font-medium text-on-surface-variant">
                        Total Points: <span className="font-bold text-primary">{totalPoints}</span>
                      </span>
                      <button
                        type="button"
                        onClick={handleAddRow}
                        className="flex items-center gap-1 rounded-lg bg-secondary/10 px-4 py-2 text-sm font-bold text-secondary transition-all hover:bg-secondary/20"
                      >
                        <span className="material-symbols-outlined text-sm">add</span>
                        Add Criterion
                      </button>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left">
                      <thead>
                        <tr className="text-xs font-bold uppercase tracking-wider text-outline">
                          <th className="pb-4 pr-4">Criterion Title</th>
                          <th className="pb-4 pr-4">Description</th>
                          <th className="w-24 pb-4 pr-4 text-center">Points</th>
                          <th className="w-12 pb-4"></th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-outline-variant/10">
                        {rubricRows.map((row, index) => (
                          <tr key={index} className="group">
                            <td className="py-4 pr-4 align-top w-1/4">
                              <input
                                className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-sm transition-all focus:ring-2 focus:ring-secondary/20"
                                placeholder="e.g. Accuracy"
                                value={row.title}
                                onChange={(e) => handleRowChange(index, "title", e.target.value)}
                              />
                            </td>
                            <td className="py-4 pr-4 align-top">
                              <textarea
                                className="min-h-[44px] w-full resize-none rounded-xl border-none bg-surface-container-low px-4 py-3 text-sm transition-all focus:ring-2 focus:ring-secondary/20"
                                placeholder="Describe what a perfect score looks like..."
                                rows={4}
                                value={row.description}
                                onChange={(e) => handleRowChange(index, "description", e.target.value)}
                              />
                            </td>
                            <td className="py-4 pr-4 align-top">
                              <input
                                className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-center text-sm font-bold transition-all focus:ring-2 focus:ring-secondary/20"
                                type="number"
                                min="0"
                                value={row.max_points}
                                onChange={(e) => handleRowChange(index, "max_points", e.target.value)}
                              />
                            </td>
                            <td className="py-4 align-top text-right">
                              <button
                                onClick={() => handleRemoveRow(index)}
                                className="mt-2 text-outline transition-colors hover:text-error group-hover:opacity-100 md:opacity-0"
                              >
                                <span className="material-symbols-outlined text-lg">delete</span>
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              </div>
            </div>
          )}  
        </div>
      </main>
    </div>
  );
}

export default UpdateMaterial;
