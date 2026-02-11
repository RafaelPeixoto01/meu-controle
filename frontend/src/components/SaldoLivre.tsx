import { formatBRL } from "../utils/format";

interface SaldoLivreProps {
  totalReceitas: number;
  totalDespesas: number;
  saldoLivre: number;
}

export default function SaldoLivre({
  totalReceitas,
  totalDespesas,
  saldoLivre,
}: SaldoLivreProps) {
  const isPositive = saldoLivre >= 0;

  return (
    <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 overflow-hidden">
      <div className="px-6 py-5">
        <h3 className="text-sm font-bold text-text-muted uppercase tracking-wide mb-4">
          Saldo Livre
        </h3>
        <div className="flex items-baseline justify-between mb-3">
          <div className="text-sm text-text-muted font-medium">Receitas</div>
          <div className="text-base font-semibold text-success tabular-nums">
            {formatBRL(totalReceitas)}
          </div>
        </div>
        <div className="flex items-baseline justify-between">
          <div className="text-sm text-text-muted font-medium">Despesas</div>
          <div className="text-base font-semibold text-danger tabular-nums">
            - {formatBRL(totalDespesas)}
          </div>
        </div>
      </div>
      <div
        className={`px-6 py-5 flex items-baseline justify-between border-t-2 ${
          isPositive
            ? "bg-success/[0.06] text-success-dark border-success/20"
            : "bg-danger/[0.06] text-danger border-danger/20"
        }`}
      >
        <div className="text-sm font-bold uppercase tracking-wide">Saldo</div>
        <div className="text-2xl font-extrabold tabular-nums">{formatBRL(saldoLivre)}</div>
      </div>
    </div>
  );
}
