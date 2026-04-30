export default function ConfirmModal({ title, message, confirmLabel = "Confirm", onConfirm, onCancel, isLoading = false }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-sm rounded-2xl bg-surface p-8 shadow-2xl">
        <h2 className="text-lg font-bold text-on-surface">{title}</h2>
        <p className="mt-2 text-sm text-on-surface-variant">{message}</p>

        <div className="mt-6 flex justify-end gap-3">
          <button
            className="rounded-xl border border-outline-variant bg-transparent px-5 py-2.5 text-sm font-bold text-on-surface-variant transition-all hover:bg-surface-container active:scale-[0.98]"
            onClick={onCancel}
            disabled={isLoading}
          >
            Cancel
          </button>
          <button
            className="rounded-xl bg-error px-5 py-2.5 text-sm font-bold text-on-error shadow-md transition-all hover:opacity-90 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? "Deleting…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
