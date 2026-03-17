import { CheckCircle2 } from "lucide-react";
import type { AiBomComportamento } from "../../types";

interface BonsComportamentosProps {
  comportamentos: AiBomComportamento[];
}

export default function BonsComportamentos({ comportamentos }: BonsComportamentosProps) {
  if (comportamentos.length === 0) return null;

  return (
    <div className="bg-surface rounded-2xl shadow-sm border border-border p-5">
      <h3 className="text-sm font-semibold text-text mb-4">Bons comportamentos</h3>
      <div className="space-y-3">
        {comportamentos.map((item, i) => (
          <div
            key={i}
            className="flex items-start gap-3 p-3 rounded-xl bg-emerald-50 border border-emerald-100"
          >
            <CheckCircle2 size={18} className="flex-shrink-0 mt-0.5 text-emerald-600" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-emerald-800">
                {item.comportamento}
              </p>
              <p className="text-xs text-emerald-700/70 mt-1">
                {item.mensagem_reforco}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
