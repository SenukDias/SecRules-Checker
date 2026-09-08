import { AlertTriangle } from "lucide-react";

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Confirm",
  danger = false,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onCancel}>
      <div
        className="card w-full max-w-sm p-6"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start gap-3 mb-4">
          <span
            className="flex items-center justify-center w-10 h-10 rounded-full shrink-0"
            style={{ background: danger ? "#ef444422" : "#e8620c22" }}
          >
            <AlertTriangle size={20} color={danger ? "#ef4444" : "#e8620c"} />
          </span>
          <div>
            <h3 id="confirm-dialog-title" className="font-semibold text-lg">
              {title}
            </h3>
            <p className="text-sm text-rulescope-muted mt-1">{message}</p>
          </div>
        </div>
        <div className="flex justify-end gap-2">
          <button className="btn-secondary bg-rulescope-surfaceAlt hover:bg-rulescope-border" onClick={onCancel}>
            Cancel
          </button>
          <button
            className="px-4 py-2 rounded-lg font-semibold text-white transition-colors"
            style={{ background: danger ? "#ef4444" : "#e8620c" }}
            onClick={onConfirm}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
