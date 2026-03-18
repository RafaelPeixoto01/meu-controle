import { X, Bell } from "lucide-react";
import type { Alerta } from "../../types";
import AlertItem from "./AlertItem";

interface AlertsModalProps {
  alertas: Alerta[];
  onClose: () => void;
  onDismiss: (id: string) => void;
  onAction: (alerta: Alerta) => void;
}

export default function AlertsModal({ alertas, onClose, onDismiss, onAction }: AlertsModalProps) {
  const ativos = alertas.filter((a) => a.status === "ativo");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-surface rounded-2xl shadow-xl border border-border w-full max-w-lg mx-4 max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border">
          <div className="flex items-center gap-2">
            <Bell size={18} className="text-primary" />
            <h2 className="text-base font-semibold text-text">
              Todos os Alertas ({ativos.length})
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-text-muted hover:text-text p-1"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-3">
          {ativos.length === 0 ? (
            <p className="text-center text-text-muted text-sm py-8">
              Nenhum alerta ativo.
            </p>
          ) : (
            ativos.map((alerta, i) => (
              <AlertItem
                key={alerta.id || i}
                alerta={alerta}
                variant="full"
                onDismiss={onDismiss}
                onAction={onAction}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
