import { Bell, Settings, CheckCircle } from "lucide-react";
import type { Alerta, AlertasResumo } from "../../types";
import AlertItem from "./AlertItem";

interface AlertsCardProps {
  alertas: Alerta[];
  resumo: AlertasResumo | null;
  onDismiss: (id: string) => void;
  onAction: (alerta: Alerta) => void;
  onViewAll: () => void;
  onSettings: () => void;
}

export default function AlertsCard({
  alertas,
  resumo,
  onDismiss,
  onAction,
  onViewAll,
  onSettings,
}: AlertsCardProps) {
  const ativos = alertas.filter((a) => a.status === "ativo");
  const top3 = ativos.slice(0, 3);

  return (
    <div className="bg-surface rounded-2xl shadow-sm border border-border p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Bell size={18} className="text-primary" />
          <h3 className="text-sm font-semibold text-text">Alertas</h3>
          {resumo && resumo.total_ativos > 0 && (
            <span className="text-xs text-text-muted">({resumo.total_ativos})</span>
          )}
        </div>
        <button
          type="button"
          onClick={onSettings}
          className="text-text-muted hover:text-text p-1"
          title="Configurar alertas"
        >
          <Settings size={16} />
        </button>
      </div>

      {top3.length === 0 ? (
        <div className="flex flex-col items-center py-6 text-text-muted">
          <CheckCircle size={32} className="mb-2 text-emerald-500" />
          <p className="text-sm font-medium">Tudo em dia!</p>
          <p className="text-xs mt-1">Nenhum alerta ativo no momento.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {top3.map((alerta, i) => (
            <AlertItem
              key={alerta.id || i}
              alerta={alerta}
              variant="compact"
              onDismiss={onDismiss}
              onAction={onAction}
            />
          ))}
        </div>
      )}

      {ativos.length > 3 && (
        <button
          type="button"
          onClick={onViewAll}
          className="mt-4 w-full text-center text-xs font-semibold text-primary hover:underline"
        >
          Ver todos ({ativos.length})
        </button>
      )}
    </div>
  );
}
