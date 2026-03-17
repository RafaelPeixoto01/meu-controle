import { Target, AlertTriangle, Lightbulb, TrendingUp, Brain, Sparkles } from "lucide-react";
import type { ScoreAction, AiRecomendacao } from "../../types";
import { formatBRL } from "../../utils/format";

interface MergedAction {
  fonte: "score" | "ia";
  acao: string;
  justificativa?: string;
  impacto_score: number;
  economia_mensal?: number;
  dificuldade?: string;
  tipo?: string;
}

interface ScoreActionsProps {
  acoes: ScoreAction[];
  aiRecomendacoes?: AiRecomendacao[];
}

const TIPO_CONFIG: Record<string, { icon: typeof Target; color: string }> = {
  "redução": { icon: Target, color: "#2563eb" },
  "oportunidade": { icon: TrendingUp, color: "#16a34a" },
  "alerta": { icon: AlertTriangle, color: "#d97706" },
  "ação": { icon: Lightbulb, color: "#8b5cf6" },
  "hábito": { icon: Lightbulb, color: "#8b5cf6" },
};

const DIFICULDADE_CONFIG: Record<string, { label: string; color: string }> = {
  "fácil": { label: "Fácil", color: "text-emerald-700 bg-emerald-50" },
  "moderada": { label: "Moderada", color: "text-amber-700 bg-amber-50" },
  "difícil": { label: "Difícil", color: "text-red-700 bg-red-50" },
};

function mergeActions(acoes: ScoreAction[], aiRecs?: AiRecomendacao[]): MergedAction[] {
  const merged: MergedAction[] = [];

  // Add AI recommendations first (higher quality)
  if (aiRecs) {
    for (const rec of aiRecs) {
      merged.push({
        fonte: "ia",
        acao: rec.acao,
        justificativa: rec.justificativa,
        impacto_score: rec.impacto_score_estimado,
        economia_mensal: rec.economia_estimada_mensal,
        dificuldade: rec.dificuldade,
      });
    }
  }

  // Add score actions that aren't covered by AI
  for (const acao of acoes) {
    const covered = merged.some((m) =>
      m.acao.toLowerCase().includes(acao.dimensao_alvo.replace("d1_", "").replace("d2_", "").replace("d3_", "").replace("d4_", ""))
    );
    if (!covered) {
      merged.push({
        fonte: "score",
        acao: acao.descricao,
        impacto_score: acao.impacto_estimado,
        tipo: acao.tipo,
      });
    }
  }

  // Sort by impact descending, limit to 5
  return merged.sort((a, b) => b.impacto_score - a.impacto_score).slice(0, 5);
}

export default function ScoreActions({ acoes, aiRecomendacoes }: ScoreActionsProps) {
  const merged = mergeActions(acoes, aiRecomendacoes);

  if (merged.length === 0) return null;

  return (
    <div className="bg-surface rounded-2xl shadow-sm border border-border p-5">
      <h3 className="text-sm font-semibold text-text mb-4">Como melhorar</h3>
      <div className="space-y-3">
        {merged.map((item, i) => {
          const isAi = item.fonte === "ia";
          const config = isAi
            ? { icon: Sparkles, color: "#8b5cf6" }
            : TIPO_CONFIG[item.tipo || "ação"] || TIPO_CONFIG["ação"];
          const Icon = config.icon;

          return (
            <div
              key={i}
              className="flex items-start gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100"
            >
              <div
                className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ backgroundColor: config.color + "15" }}
              >
                <Icon size={16} style={{ color: config.color }} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm text-text">{item.acao}</p>
                  {isAi && (
                    <span className="inline-flex items-center gap-0.5 text-[10px] font-semibold text-violet-700 bg-violet-100 px-1.5 py-0.5 rounded-full whitespace-nowrap">
                      <Brain size={10} />
                      IA
                    </span>
                  )}
                </div>
                {item.justificativa && (
                  <p className="text-xs text-text-muted mt-0.5">{item.justificativa}</p>
                )}
                <div className="flex flex-wrap items-center gap-2 mt-1.5">
                  {item.impacto_score > 0 && (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-success bg-success/10 px-2 py-0.5 rounded-full">
                      <TrendingUp size={10} />
                      ~{item.impacto_score} pontos
                    </span>
                  )}
                  {item.economia_mensal != null && item.economia_mensal > 0 && (
                    <span className="text-xs text-text-muted">
                      Economia: {formatBRL(item.economia_mensal)}/mês
                    </span>
                  )}
                  {item.dificuldade && DIFICULDADE_CONFIG[item.dificuldade] && (
                    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${DIFICULDADE_CONFIG[item.dificuldade].color}`}>
                      {DIFICULDADE_CONFIG[item.dificuldade].label}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
