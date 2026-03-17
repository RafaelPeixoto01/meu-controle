import { Target, TrendingUp, Trophy } from "lucide-react";
import type { AiMetas } from "../../types";
import { formatBRL } from "../../utils/format";

interface MetasSugeridasProps {
  metas: AiMetas;
}

const META_CONFIG = [
  { key: "curto_prazo" as const, label: "Curto prazo", icon: Target, color: "#2563eb" },
  { key: "medio_prazo" as const, label: "Médio prazo", icon: TrendingUp, color: "#7c3aed" },
  { key: "longo_prazo" as const, label: "Longo prazo", icon: Trophy, color: "#ca8a04" },
];

export default function MetasSugeridas({ metas }: MetasSugeridasProps) {
  return (
    <div className="bg-surface rounded-2xl shadow-sm border border-border p-5">
      <h3 className="text-sm font-semibold text-text mb-4">Metas sugeridas</h3>
      <div className="space-y-3">
        {META_CONFIG.map(({ key, label, icon: Icon, color }) => {
          const meta = metas[key];
          if (!meta) return null;

          return (
            <div
              key={key}
              className="p-3 rounded-xl bg-slate-50 border border-slate-100"
            >
              <div className="flex items-center gap-2 mb-2">
                <div
                  className="w-7 h-7 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: color + "15" }}
                >
                  <Icon size={14} style={{ color }} />
                </div>
                <span className="text-xs font-semibold text-text-muted uppercase tracking-wide">
                  {label}
                </span>
              </div>
              <p className="text-sm text-text font-medium">{meta.descricao}</p>
              <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-text-muted">
                {meta.valor_alvo > 0 && <span>Alvo: {formatBRL(meta.valor_alvo)}</span>}
                <span>{meta.prazo_meses} {meta.prazo_meses === 1 ? "mês" : "meses"}</span>
              </div>
              <p className="text-xs text-primary mt-2">
                Primeiro passo: {meta.primeiro_passo}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
