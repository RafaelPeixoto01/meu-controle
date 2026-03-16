import { Target, AlertTriangle, Lightbulb, TrendingUp } from "lucide-react";
import type { ScoreAction } from "../../types";

interface ScoreActionsProps {
  acoes: ScoreAction[];
}

const TIPO_CONFIG: Record<string, { icon: typeof Target; color: string }> = {
  "redução": { icon: Target, color: "#2563eb" },
  "oportunidade": { icon: TrendingUp, color: "#16a34a" },
  "alerta": { icon: AlertTriangle, color: "#d97706" },
  "ação": { icon: Lightbulb, color: "#8b5cf6" },
  "hábito": { icon: Lightbulb, color: "#8b5cf6" },
};

export default function ScoreActions({ acoes }: ScoreActionsProps) {
  if (acoes.length === 0) return null;

  return (
    <div className="bg-surface rounded-2xl shadow-sm border border-border p-5">
      <h3 className="text-sm font-semibold text-text mb-4">Como melhorar</h3>
      <div className="space-y-3">
        {acoes.map((acao) => {
          const config = TIPO_CONFIG[acao.tipo] || TIPO_CONFIG["ação"];
          const Icon = config.icon;

          return (
            <div
              key={acao.prioridade}
              className="flex items-start gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100"
            >
              <div
                className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ backgroundColor: config.color + "15" }}
              >
                <Icon size={16} style={{ color: config.color }} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-text">{acao.descricao}</p>
                {acao.impacto_estimado > 0 && (
                  <span className="inline-flex items-center gap-1 mt-1.5 text-xs font-medium text-success bg-success/10 px-2 py-0.5 rounded-full">
                    <TrendingUp size={10} />
                    ~{acao.impacto_estimado} pontos
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
