// CR-053 (F07): um grupo da revisao de importacao (novos / conciliacoes /
// parceladas / ignoradas / duplicadas). Extraido do ImportReview junto com a
// linha, para que o componente principal fique so com estado e layout.
import type { Expense, ImportTransaction } from "../../types";
import type { ReviewDecision } from "../../utils/importReview";
import ImportReviewRow from "./ImportReviewRow";

export interface ImportReviewGroupProps {
  titulo: string;
  hint: string | null;
  itens: ImportTransaction[];
  decisions: Record<string, ReviewDecision>;
  errors: Record<string, string>;
  categorias: Record<string, string[]>;
  metodosPagamento: string[];
  matchTargets: Record<string, Expense>;
  onChange: (txId: string, patch: Partial<ReviewDecision>) => void;
}

export default function ImportReviewGroup({
  titulo,
  hint,
  itens,
  decisions,
  errors,
  categorias,
  metodosPagamento,
  matchTargets,
  onChange,
}: ImportReviewGroupProps) {
  if (itens.length === 0) return null;

  return (
    <section className="space-y-2">
      <div>
        <h3 className="font-bold text-text">
          {titulo} <span className="text-text-muted font-semibold">({itens.length})</span>
        </h3>
        {hint && <p className="text-xs text-text-muted">{hint}</p>}
      </div>
      <div className="space-y-2">
        {itens.map((tx) => {
          const decision = decisions[tx.id];
          if (!decision) return null;
          return (
            <ImportReviewRow
              key={tx.id}
              tx={tx}
              decision={decision}
              error={errors[tx.id]}
              categorias={categorias}
              metodosPagamento={metodosPagamento}
              matchTargets={matchTargets}
              onChange={onChange}
            />
          );
        })}
      </div>
    </section>
  );
}
