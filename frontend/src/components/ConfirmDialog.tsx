interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({
  isOpen,
  title,
  message,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      role="dialog"
      aria-modal="true"
      onClick={onCancel}
    >
      <div
        className="bg-white rounded-xl shadow-xl p-6 w-full max-w-sm mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-bold text-gray-900 mb-2">{title}</h3>
        <p className="text-gray-500 mb-6">{message}</p>
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2.5 text-gray-600 border border-gray-300 rounded-lg
              hover:bg-gray-50 active:bg-gray-100
              transition-colors duration-150 font-medium"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="px-4 py-2.5 bg-danger text-white rounded-lg font-semibold
              hover:bg-danger-hover active:bg-red-800
              transition-colors duration-150"
          >
            Excluir
          </button>
        </div>
      </div>
    </div>
  );
}
