import { Wallet, TrendingDown, CreditCard, ShoppingCart } from "lucide-react";
import { formatBRL } from "../../utils/format";

interface KeyIndicatorsProps {
  saldoLivre: number;
  percentualComprometimento: number;
  totalParcelasFuturas: number;
  totalGastosDiarios: number;
}

export default function KeyIndicators({
  saldoLivre,
  percentualComprometimento,
  totalParcelasFuturas,
  totalGastosDiarios,
}: KeyIndicatorsProps) {
  const isPositive = saldoLivre >= 0;
  const comprometimentoAlto = percentualComprometimento > 80;
  const comprometimentoMedio = percentualComprometimento > 60;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
      {/* Saldo Livre */}
      <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 p-4 sm:p-5">
        <div className="flex items-center gap-2 mb-3">
          <div className={`p-2 rounded-xl ${isPositive ? "bg-success/10" : "bg-danger/10"}`}>
            <Wallet className={`w-4 h-4 sm:w-5 sm:h-5 ${isPositive ? "text-success" : "text-danger"}`} />
          </div>
          <span className="text-xs sm:text-sm font-medium text-text-muted">Saldo Livre</span>
        </div>
        <div className={`text-lg sm:text-2xl font-extrabold tabular-nums ${isPositive ? "text-success-dark" : "text-danger"}`}>
          {formatBRL(saldoLivre)}
        </div>
      </div>

      {/* % Comprometimento */}
      <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 p-4 sm:p-5">
        <div className="flex items-center gap-2 mb-3">
          <div className={`p-2 rounded-xl ${comprometimentoAlto ? "bg-danger/10" : comprometimentoMedio ? "bg-warning/10" : "bg-primary/10"}`}>
            <TrendingDown className={`w-4 h-4 sm:w-5 sm:h-5 ${comprometimentoAlto ? "text-danger" : comprometimentoMedio ? "text-warning" : "text-primary"}`} />
          </div>
          <span className="text-xs sm:text-sm font-medium text-text-muted">Comprometimento</span>
        </div>
        <div className={`text-lg sm:text-2xl font-extrabold tabular-nums ${comprometimentoAlto ? "text-danger" : comprometimentoMedio ? "text-warning" : "text-primary"}`}>
          {percentualComprometimento.toFixed(1)}%
        </div>
        <div className="mt-2 h-2 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${comprometimentoAlto ? "bg-danger" : comprometimentoMedio ? "bg-warning" : "bg-primary"}`}
            style={{ width: `${Math.min(percentualComprometimento, 100)}%` }}
          />
        </div>
      </div>

      {/* Parcelas Futuras */}
      <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 p-4 sm:p-5">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-2 rounded-xl bg-accent-light">
            <CreditCard className="w-4 h-4 sm:w-5 sm:h-5 text-accent" />
          </div>
          <span className="text-xs sm:text-sm font-medium text-text-muted">Parcelas Futuras</span>
        </div>
        <div className="text-lg sm:text-2xl font-extrabold tabular-nums text-accent">
          {formatBRL(totalParcelasFuturas)}
        </div>
      </div>

      {/* Gastos Diários */}
      <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 p-4 sm:p-5">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-2 rounded-xl bg-warning/10">
            <ShoppingCart className="w-4 h-4 sm:w-5 sm:h-5 text-warning" />
          </div>
          <span className="text-xs sm:text-sm font-medium text-text-muted">Gastos Diários</span>
        </div>
        <div className="text-lg sm:text-2xl font-extrabold tabular-nums text-warning">
          {formatBRL(totalGastosDiarios)}
        </div>
      </div>
    </div>
  );
}
