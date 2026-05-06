import { useState } from "react";


export default function CopyAssessmentModal({
  assessment,
  courses,
  currentCourseId,
  isCopying,
  onConfirm,
  onCancel,
}) {
  const [title, setTitle] = useState(`Copy of ${assessment?.title ?? ""}`);
  const [targetCourseId, setTargetCourseId] = useState(currentCourseId);

  function handleConfirm() {
    if (!title.trim() || !targetCourseId) return;
    onConfirm({ targetCourseId, title: title.trim() });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl bg-surface p-8 shadow-2xl">
        <h2 className="text-lg font-bold text-on-surface">Copy Assessment</h2>
        <p className="mt-1 text-sm text-on-surface-variant">
          A new draft will be created in the selected course.
        </p>

        <div className="mt-6 space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-on-surface-variant">
              Title
            </label>
            <input
              type="text"
              className="w-full rounded-xl border-none bg-surface-container-low px-4 py-2.5 text-sm text-on-surface placeholder:text-outline focus:ring-2 focus:ring-primary/20 disabled:opacity-50"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={isCopying}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-on-surface-variant">
              Target Course
            </label>
            <div className="group relative">
              <select
                className="w-full cursor-pointer appearance-none rounded-xl border-none bg-surface-container-low px-4 py-2.5 text-sm text-on-surface focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-50"
                value={targetCourseId}
                onChange={(e) => setTargetCourseId(e.target.value)}
                disabled={isCopying}
              >
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.course_code || "Unknown Course"}
                    {c.id === currentCourseId ? " (current)" : ""}
                  </option>
                ))}
              </select>
              <span
                className="material-symbols-outlined pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-on-surface-variant"
                style={{ verticalAlign: "middle" }}
              >
                expand_more
              </span>
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            className="rounded-xl border border-outline-variant bg-transparent px-5 py-2.5 text-sm font-bold text-on-surface-variant transition-all hover:bg-surface-container active:scale-[0.98] disabled:opacity-50"
            onClick={onCancel}
            disabled={isCopying}
          >
            Cancel
          </button>
          <button
            className="rounded-xl bg-primary px-5 py-2.5 text-sm font-bold text-on-primary shadow-md transition-all hover:bg-primary-dim active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
            onClick={handleConfirm}
            disabled={isCopying || !title.trim()}
          >
            {isCopying ? "Copying…" : "Copy"}
          </button>
        </div>
      </div>
    </div>
  );
}
