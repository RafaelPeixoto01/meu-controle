import { AlertCircle, AlertTriangle, Info, X } from "lucide-react";
import type { Alerta } from "../../types";

interface AlertBannerProps {
  alertas: Alerta[];
  onDismiss?: (id: string) => void;
  onAction?: (alerta: Alerta) => void;
}

const SEVERITY_ORDER = { critico: 0, atencao: 1, informativo: 2 } as const;

const BANNER_CONFIG = {
  critico: {
    icon: AlertCircle,
    bg: "bg-red-50",
    border: "border-red-200",
    iconColor: "text-red-600",
    textColor: "text-red-800",
  },
  atencao: {
    icon: AlertTriangle,
    bg: "bg-amber-50",
    border: "border-amber-200",
    iconColor: "text-amber-600",
    textColor: "text-amber-800",
  },
  informativo: {
    icon: Info,
    bg: "bg-blue-50",
    border: "border-blue-200",
    iconColor: "text-blue-600",
    textColor: "text-blue-800",
  },
};

export default function AlertBanner({ alertas, onDismiss, onAction }: AlertBannerProps) {
  if (alertas.length === 0) return null;

  // Mostrar o mais severo
  const sorted = [...alertas].sort(
    (a, b) => (SEVERITY_ORDER[a.severidade] ?? 2) - (SEVERITY_ORDER[b.severidade] ?? 2)
  );
  const alerta = sorted[0];
  const config = BANNER_CONFIG[alerta.severidade] || BANNER_CONFIG.informativo;
  const Icon = config.icon;

  return (
    <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border ${config.bg} ${config.border}`}>
      <Icon size={18} className={`flex-shrink-0 ${config.iconColor}`} />
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium ${config.textColor}`}>{alerta.titulo}</p>
        {alerta.acao && onAction && (
          <button
            type="button"
            onClick={() => onAction(alerta)}
            className={`text-xs font-semibold ${config.textColor} hover:underline mt-0.5`}
          >
            {alerta.acao.label}
          </button>
        )}
      </div>
      {alertas.length > 1 && (
        <span className={`text-xs ${config.textColor} whitespace-nowrap`}>
          +{alertas.length - 1} alerta{alertas.length - 1 > 1 ? "s" : ""}
        </span>
      )}
      {onDismiss && alerta.id && (
        <button
          type="button"
          onClick={() => onDismiss(alerta.id!)}
          className="flex-shrink-0 text-text-muted hover:text-text p-0.5"
          title="Dispensar"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}
