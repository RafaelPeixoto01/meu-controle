// CR-053 (F07): um grupo da revisao de importacao (novos / conciliacoes /
// parceladas / ignoradas / duplicadas). Extraido do ImportReview junto com a
// linha, para que o componente principal fique so com estado e layout.
import type { Expense, ImportTransaction } from "../../types";
import { sumTransactions, type ReviewDecision } from "../../utils/importReview";
import { formatBRL } from "../../utils/format";
import ImportReviewRow from "./ImportReviewRow";

export interface ImportReviewGroupProps {
  titulo: string;
  hint: string | null;
  itens: ImportTransaction[];
  /** Quantas linhas o grupo tem sem filtro — base do "X de N" (CR-053) */
  totalItens: number;
  filtroAtivo: boolean;
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
  totalItens,
  filtroAtivo,
  decisions,
  errors,
  categorias,
  metodosPagamento,
  matchTargets,
  onChange,
}: ImportReviewGroupProps) {
  // Sem filtro, grupo vazio some (comportamento do CR-047). Com filtro ativo ele
  // fica visivel dizendo que nao casou nada — some-lo esconderia o motivo.
  if (totalItens === 0) return null;

  // onlyIncluded para os cinco subtotais somarem exatamente o total do cabecalho:
  // sem isso, Ignoradas/Duplicadas exibiriam em negrito dinheiro que nao entra.
  const subtotal = sumTransactions(itens, decisions, { onlyIncluded: true });

  return (
    <section className="space-y-2">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3">
        <div>
          <h3 className="font-bold text-text">
            {titulo}{" "}
            <span className="text-text-muted font-semibold">
              ({filtroAtivo ? `${itens.length} de ${totalItens}` : totalItens})
            </span>
          </h3>
          {hint && <p className="text-xs text-text-muted">{hint}</p>}
        </div>
        {itens.length > 0 && (
          <span className="text-sm font-bold text-text tabular-nums">{formatBRL(subtotal)}</span>
        )}
      </div>
      {itens.length === 0 && (
        <p className="text-xs text-text-muted italic px-1">
          Nenhuma linha deste grupo corresponde ao filtro.
        </p>
      )}
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
