import { AlertCircle, AlertTriangle, Info, X } from "lucide-react";
import type { Alerta } from "../../types";
import { formatBRL } from "../../utils/format";

interface AlertItemProps {
  alerta: Alerta;
  variant?: "compact" | "full";
  onDismiss?: (id: string) => void;
  onAction?: (alerta: Alerta) => void;
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

export default function AlertItem({ alerta, variant = "full", onDismiss, onAction }: AlertItemProps) {
  const config = SEVERITY_CONFIG[alerta.severidade] || SEVERITY_CONFIG.informativo;
  const Icon = config.icon;

  return (
    <div className={`flex items-start gap-3 p-3 rounded-xl border ${config.bg} ${config.border}`}>
      <Icon size={18} className={`flex-shrink-0 mt-0.5 ${config.iconColor}`} />
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium ${config.titleColor}`}>{alerta.titulo}</p>
        {variant === "full" && alerta.descricao && (
          <p className="text-xs text-text-muted mt-1">{alerta.descricao}</p>
        )}
        {variant === "full" && (alerta.impacto_mensal || alerta.impacto_anual) && (
          <div className="flex gap-3 mt-2 text-xs text-text-muted">
            {alerta.impacto_mensal != null && alerta.impacto_mensal > 0 && (
              <span>Impacto: {formatBRL(alerta.impacto_mensal)}/mês</span>
            )}
            {alerta.impacto_anual != null && alerta.impacto_anual > 0 && (
              <span>{formatBRL(alerta.impacto_anual)}/ano</span>
            )}
          </div>
        )}
        {alerta.acao && onAction && (
          <button
            type="button"
            onClick={() => onAction(alerta)}
            className={`mt-2 text-xs font-semibold ${config.titleColor} hover:underline`}
          >
            {alerta.acao.label}
          </button>
        )}
      </div>
      {onDismiss && alerta.id && (
        <button
          type="button"
          onClick={() => onDismiss(alerta.id!)}
          className="flex-shrink-0 text-text-muted hover:text-text p-0.5"
          title="Dispensar alerta"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}
