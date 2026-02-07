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
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="px-5 py-4">
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Saldo Livre
        </h3>
        <div className="flex items-baseline justify-between mb-3">
          <div className="text-sm text-gray-500">Receitas</div>
          <div className="text-base font-semibold text-gray-700">
            {formatBRL(totalReceitas)}
          </div>
        </div>
        <div className="flex items-baseline justify-between">
          <div className="text-sm text-gray-500">Despesas</div>
          <div className="text-base font-semibold text-gray-700">
            - {formatBRL(totalDespesas)}
          </div>
        </div>
      </div>
      <div
        className={`px-5 py-4 flex items-baseline justify-between border-t ${
          isPositive
            ? "bg-success/10 text-success-dark border-success/20"
            : "bg-danger/10 text-danger border-danger/20"
        }`}
      >
        <div className="text-sm font-bold uppercase tracking-wide">Saldo</div>
        <div className="text-2xl font-bold">{formatBRL(saldoLivre)}</div>
      </div>
    </div>
  );
}
