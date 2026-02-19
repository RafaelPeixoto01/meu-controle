import { useState, useEffect } from "react";

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  checkboxLabel?: string;
  onConfirm: (isChecked: boolean) => void;
  onCancel: () => void;
}

export default function ConfirmDialog({
  isOpen,
  title,
  message,
  checkboxLabel,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const [isChecked, setIsChecked] = useState(false);

  useEffect(() => {
    if (isOpen) setIsChecked(false);
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/40 backdrop-blur-[2px] flex items-center justify-center z-50"
      role="dialog"
      aria-modal="true"
      onClick={onCancel}
    >
      <div
        className="bg-surface rounded-2xl shadow-2xl shadow-black/10 border border-slate-100/80
          p-7 w-full max-w-sm mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-bold text-text mb-2">{title}</h3>
        <p className="text-text-muted mb-6">{message}</p>

        {checkboxLabel && (
          <label className="flex items-center gap-2 mb-6 cursor-pointer text-sm font-medium text-danger bg-danger/5 p-3 rounded-xl border border-danger/10">
            <input
              type="checkbox"
              checked={isChecked}
              onChange={(e) => setIsChecked(e.target.checked)}
              className="rounded text-danger border-danger/30 focus:ring-danger w-4 h-4"
            />
            {checkboxLabel}
          </label>
        )}

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-5 py-2.5 text-text-muted border border-border rounded-xl
              hover:bg-slate-50 active:bg-slate-100 active:scale-[0.98]
              transition-all duration-150 font-semibold"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={() => onConfirm(isChecked)}
            className="px-5 py-2.5 bg-danger text-white rounded-xl font-semibold
              hover:bg-danger-hover hover:shadow-md hover:shadow-danger/20
              active:scale-[0.98]
              transition-all duration-150"
          >
            Excluir
          </button>
        </div>
      </div>
    </div>
  );
}
