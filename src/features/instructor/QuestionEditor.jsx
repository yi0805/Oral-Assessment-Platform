import { useState } from "react";

import Spinner from "../../ui/Spinner";
import ConfirmModal from "../../ui/ConfirmModal";
import { useQuestions } from "./useQuestion";
import { useAddQuestion } from "./useAddQuestion";
import { useUpdateQuestion } from "./useUpdateQuestion";
import { useDeleteQuestion } from "./useDeleteQuestion";

export default function QuestionEditor({
  assessmentConfigId,
  mainQuestionNum,
  disabled = false,
  onQuestionAdded,
}) {
  const { questions, isLoading } = useQuestions(assessmentConfigId);

  const { addQuestion, isPending: isAdding } = useAddQuestion();
  const { updateQuestion, isPending: isUpdating } = useUpdateQuestion();
  const { deleteQuestion, isPending: isDeleting } = useDeleteQuestion();

  const [editingId, setEditingId] = useState(null);
  const [editText, setEditText] = useState("");

  const [isAddOpen, setIsAddOpen] = useState(false);
  const [newText, setNewText] = useState("");

  const [pendingDelete, setPendingDelete] = useState(null);

  const poolSize = questions.length;
  const isUnderfilled = mainQuestionNum > 0 && poolSize < mainQuestionNum;

  function startEdit(question) {
    setEditingId(question.id);
    setEditText(question.question_text);
  }

  function cancelEdit() {
    setEditingId(null);
    setEditText("");
  }

  async function saveEdit() {
    if (!editText.trim()) return;

    await updateQuestion({
      questionId: editingId,
      questionText: editText,
      assessmentConfigId,
    });

    cancelEdit();
  }

  function handleDelete(question) {
    if (disabled || isDeleting) return;
    setPendingDelete(question);
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    await deleteQuestion({
      questionId: pendingDelete.id,
      assessmentConfigId,
    });
    setPendingDelete(null);
  }

  async function handleAdd() {
    if (!newText.trim() || isAdding) return;

    await addQuestion({
      assessmentConfigId,
      questionText: newText.trim(),
    });

    onQuestionAdded?.(poolSize + 1);

    setNewText("");
    setIsAddOpen(false);
  }

  return (
    <section className="rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
      {pendingDelete && (
        <ConfirmModal
          title="Delete Question"
          message={`Are you sure you want to delete this question? This cannot be undone.\n\n"${pendingDelete.question_text}"`}
          confirmLabel="Yes, Delete"
          isLoading={isDeleting}
          onConfirm={confirmDelete}
          onCancel={() => setPendingDelete(null)}
        />
      )}

      <div className="mb-6 flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <span
              className="material-symbols-outlined text-xl"
              data-icon="quiz"
              style={{ verticalAlign: "middle" }}
            >
              quiz
            </span>
          </div>

          <div>
            <h2 className="text-xl font-bold text-on-surface">
              Questions ({poolSize})
            </h2>

            <p className="mt-1 max-w-md text-xs text-on-surface-variant">
              Manually add, edit, or remove questions in the assessment pool.
            </p>
          </div>
        </div>

        {!disabled && !isAddOpen && (
          <button
            type="button"
            onClick={() => setIsAddOpen(true)}
            className="inline-flex items-center gap-2 rounded-xl bg-primary/10 px-4 py-2 text-sm font-bold text-primary transition-all hover:bg-primary/20"
          >
            <span className="material-symbols-outlined text-base">add</span>
            Add Question
          </button>
        )}
      </div>

      {isUnderfilled && (
        <div className="mb-4 flex items-start gap-3 rounded-xl border border-error/15 bg-error-container/30 p-4">
          <span
            className="material-symbols-outlined text-error"
            style={{ fontVariationSettings: '"FILL" 1' }}
          >
            warning
          </span>

          <p className="text-xs text-on-background">
            The assessment is configured for{" "}
            <span className="font-bold">{mainQuestionNum}</span> questions but
            the pool only has <span className="font-bold">{poolSize}</span>. Add
            more questions, or lower the question count in the form above before
            publishing.
          </p>
        </div>
      )}

      {isLoading ? (
        <Spinner />
      ) : (
        <div className="space-y-3">
          {questions.map((question, index) => (
            <div
              key={question.id}
              className="rounded-xl border border-outline-variant/15 bg-surface-container-lowest p-5 transition-all hover:border-outline-variant/40"
            >
              <div className="flex items-start gap-4">
                <div className="mt-1 flex shrink-0 flex-col items-center gap-1">
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 font-headline text-sm font-bold text-primary">
                    {String(index + 1).padStart(2, "0")}
                  </span>

                  {!disabled && editingId !== question.id && (
                    <button
                      type="button"
                      className="rounded-lg px-2 py-0.5 text-xs font-bold text-error transition-all hover:bg-error/10 disabled:opacity-50"
                      onClick={() => handleDelete(question)}
                      disabled={isDeleting}
                    >
                      Delete
                    </button>
                  )}
                </div>

                <div className="min-w-0 flex-1">
                  {editingId === question.id ? (
                    <div className="space-y-3">
                      <textarea
                        className="min-h-[80px] w-full resize-y rounded-xl border-none bg-surface-container-low px-4 py-3 text-sm leading-relaxed text-on-surface focus:ring-2 focus:ring-primary/20"
                        value={editText}
                        onChange={(e) => setEditText(e.target.value)}
                      />

                      <div className="flex gap-2">
                        <button
                          type="button"
                          className="rounded-lg bg-primary px-4 py-1.5 text-xs font-bold text-on-primary disabled:opacity-50"
                          onClick={saveEdit}
                          disabled={isUpdating || !editText.trim()}
                        >
                          {isUpdating ? "Saving…" : "Save"}
                        </button>

                        <button
                          type="button"
                          className="rounded-lg px-4 py-1.5 text-xs font-bold text-on-surface-variant hover:bg-surface-container-high"
                          onClick={cancelEdit}
                          disabled={isUpdating}
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
                </div>

                {!disabled && editingId !== question.id && (
                  <div className="flex shrink-0 gap-2">
                    <button
                      type="button"
                      className="rounded-lg px-3 py-1 text-xs font-bold text-primary transition-all hover:bg-primary/10"
                      onClick={() => startEdit(question)}
                    >
                      Edit
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}

          {!disabled && isAddOpen && (
            <div className="rounded-xl border-2 border-dashed border-primary/30 bg-primary/5 p-5">
              <div className="flex items-start gap-4">
                <span className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 font-headline text-sm font-bold text-primary">
                  {String(poolSize + 1).padStart(2, "0")}
                </span>

                <div className="min-w-0 flex-1 space-y-3">
                  <textarea
                    className="min-h-[80px] w-full resize-y rounded-xl border-none bg-surface-container-low px-4 py-3 text-sm leading-relaxed text-on-surface focus:ring-2 focus:ring-primary/20"
                    placeholder="Type the new question…"
                    value={newText}
                    onChange={(e) => setNewText(e.target.value)}
                    autoFocus
                  />

                  <div className="flex gap-2">
                    <button
                      type="button"
                      className="rounded-lg bg-primary px-4 py-1.5 text-xs font-bold text-on-primary disabled:opacity-50"
                      onClick={handleAdd}
                      disabled={isAdding || !newText.trim()}
                    >
                      {isAdding ? "Adding…" : "Add"}
                    </button>

                    <button
                      type="button"
                      className="rounded-lg px-4 py-1.5 text-xs font-bold text-on-surface-variant hover:bg-surface-container-high"
                      onClick={() => {
                        setIsAddOpen(false);
                        setNewText("");
                      }}
                      disabled={isAdding}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {questions.length === 0 && !isAddOpen && (
            <div className="rounded-xl border-2 border-dashed border-outline-variant/30 p-8 text-center">
              <p className="text-sm text-on-surface-variant">
                No questions in the pool yet.
              </p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
