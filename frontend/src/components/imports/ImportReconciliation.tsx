// CR-057 (F07): aviso da conferencia com o documento no topo da revisao
// (RN-053). Informativo — nao bloqueia o confirm.
import { AlertTriangle, CheckCircle2 } from "lucide-react";
import { reconcile, reconciliationMessage } from "../../utils/importReconciliation";

interface ImportReconciliationProps {
  documento: number | null; // total de debitos impresso no documento
  listado: number | null; // debitos na revisao, com os valores ja corrigidos
}

export default function ImportReconciliation({ documento, listado }: ImportReconciliationProps) {
  const r = reconcile({ total_debitos_documento: documento, total_debitos_extraido: listado });
  // Sem total impresso, sem direcao em alguma linha, ou lote antigo: nada a conferir
  if (!r) return null;
  const msg = reconciliationMessage(r);

  if (!msg.alerta) {
    return (
      <p
        data-testid="import-reconciliation"
        className="flex items-start gap-2 text-sm text-success-dark bg-pago-bg/60 rounded-xl px-3 py-2 mt-3"
      >
        <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
        <span>
          {msg.titulo}: {msg.detalhe}
        </span>
      </p>
    );
  }

  return (
    <div
      role="alert"
      data-testid="import-reconciliation"
      className="flex items-start gap-2 text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2 mt-3"
    >
      <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
      <div>
        <p className="font-semibold">{msg.titulo}</p>
        <p>{msg.detalhe}</p>
      </div>
    </div>
  );
}
