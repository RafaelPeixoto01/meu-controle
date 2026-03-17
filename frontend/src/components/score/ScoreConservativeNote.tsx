import { AlertTriangle } from "lucide-react";
import type { ConservativeScenario } from "../../types";
import { formatBRL } from "../../utils/format";

interface ScoreConservativeNoteProps {
  cenario: ConservativeScenario | null;
  scoreAtual: number;
}

export default function ScoreConservativeNote({
  cenario,
  scoreAtual,
}: ScoreConservativeNoteProps) {
  if (!cenario) return null;

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4">
      <div className="flex items-start gap-3">
        <AlertTriangle size={18} className="text-warning flex-shrink-0 mt-0.5" />
        <div>
          <h4 className="text-sm font-semibold text-amber-900">
            Cenário conservador
          </h4>
          <p className="text-sm text-amber-800 mt-1">
            Se todas as parcelas pendentes forem ativadas, seu score cairia de{" "}
            <span className="font-semibold">{scoreAtual}</span> para{" "}
            <span className="font-semibold">{cenario.score}</span> (
            {cenario.classificacao}).
          </p>
          {cenario.parcelas_pendentes.length > 0 && (
            <div className="mt-2 space-y-1">
              {cenario.parcelas_pendentes.map((p, i) => (
                <div key={i} className="text-xs text-amber-700">
                  {p.descricao}: {formatBRL(p.valor_estimado_mensal)}/mês (
                  {p.total_parcelas}x)
                </div>
              ))}
            </div>
          )}
          <p className="text-xs text-amber-600 mt-2">{cenario.impacto}</p>
        </div>
      </div>
    </div>
  );
}
