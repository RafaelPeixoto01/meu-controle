// CR-057 (F07): aviso da conferencia com o documento no topo da revisao
// (RN-053). Informativo — nao bloqueia o confirm.
import { AlertTriangle, CheckCircle2 } from "lucide-react";
import type { ImportBatchSummary } from "../../types";
import { formatBRL } from "../../utils/format";
import { reconcile } from "../../utils/importReconciliation";

interface ImportReconciliationProps {
  batch: ImportBatchSummary;
}

export default function ImportReconciliation({ batch }: ImportReconciliationProps) {
  const r = reconcile(batch);
  // Sem total impresso (ou lote antigo): nao ha o que conferir
  if (!r) return null;

  const totais = `Débitos extraídos ${formatBRL(r.extraido)} · total de débitos do documento ${formatBRL(r.documento)}`;

  if (r.status === "confere") {
    return (
      <p
        data-testid="import-reconciliation"
        className="flex items-start gap-2 text-sm text-success-dark bg-pago-bg/60 rounded-xl px-3 py-2 mt-3"
      >
        <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
        <span>Conferido com o documento: {totais}.</span>
      </p>
    );
  }

  const faltando = r.status === "faltando";
  return (
    <div
      role="alert"
      data-testid="import-reconciliation"
      className="flex items-start gap-2 text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2 mt-3"
    >
      <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
      <div>
        <p className="font-semibold">
          {faltando
            ? `Faltam ${formatBRL(r.diferenca)} em relação ao documento`
            : `A soma extraída passa do documento em ${formatBRL(r.diferenca)}`}
        </p>
        <p>
          {totais}.{" "}
          {faltando
            ? "Alguma transação pode não ter sido lida — confira o PDF antes de confirmar."
            : "Pode haver uma transação lida em dobro ou um crédito lido como débito."}
        </p>
      </div>
    </div>
  );
}
