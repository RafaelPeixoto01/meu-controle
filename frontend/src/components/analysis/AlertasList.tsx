import { AlertCircle, AlertTriangle, Info } from "lucide-react";
import type { AiAlerta } from "../../types";
import { formatBRL } from "../../utils/format";

interface AlertasListProps {
  alertas: AiAlerta[];
}

const SEVERITY_CONFIG = {
  critico: {
    icon: AlertCircle,
    bg: "bg-red-50",
    border: "border-red-200",
    iconColor: "text-red-600",
    titleColor: "text-red-800",
  },
  atencao: {
    icon: AlertTriangle,
    bg: "bg-amber-50",
    border: "border-amber-200",
    iconColor: "text-amber-600",
    titleColor: "text-amber-800",
  },
  informativo: {
    icon: Info,
    bg: "bg-blue-50",
    border: "border-blue-200",
    iconColor: "text-blue-600",
    titleColor: "text-blue-800",
  },
};

export default function AlertasList({ alertas }: AlertasListProps) {
  if (alertas.length === 0) return null;

  return (
    <div className="bg-surface rounded-2xl shadow-sm border border-border p-5">
      <h3 className="text-sm font-semibold text-text mb-4">Alertas</h3>
      <div className="space-y-3">
        {alertas.map((alerta, i) => {
          const config = SEVERITY_CONFIG[alerta.tipo] || SEVERITY_CONFIG.informativo;
          const Icon = config.icon;

          return (
            <div
              key={i}
              className={`flex items-start gap-3 p-3 rounded-xl border ${config.bg} ${config.border}`}
            >
              <Icon size={18} className={`flex-shrink-0 mt-0.5 ${config.iconColor}`} />
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium ${config.titleColor}`}>
                  {alerta.titulo}
                </p>
                <p className="text-xs text-text-muted mt-1">{alerta.descricao}</p>
                {(alerta.impacto_mensal > 0 || alerta.impacto_anual > 0) && (
                  <div className="flex gap-3 mt-2 text-xs text-text-muted">
                    {alerta.impacto_mensal > 0 && (
                      <span>Impacto: {formatBRL(alerta.impacto_mensal)}/mês</span>
                    )}
                    {alerta.impacto_anual > 0 && (
                      <span>{formatBRL(alerta.impacto_anual)}/ano</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
