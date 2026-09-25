// CR-056 (F07): previa e confirmacao do desfazer de um lote (RN-051).
// A lista vem do backend (`undo-preview`) e mostra exatamente o que o undo
// fara — o usuario ve o que sera removido ANTES de executar.
import { Loader2, Undo2 } from "lucide-react";
import type { ImportHistoryItem, ImportUndoResponse } from "../../types";
import { useUndoImport, useUndoPreview } from "../../hooks/useImports";
import { formatBRL, formatDateBRWithYear } from "../../utils/format";
import {
  groupUndoItems,
  restoreDetail,
  undoChangesNothing,
  undoItemKind,
  type UndoSection,
} from "../../utils/importHistory";

interface ImportUndoDialogProps {
  batch: ImportHistoryItem;
  onClose: () => void;
  onDone: (result: ImportUndoResponse) => void;
}

const SECTION_TONE: Record<UndoSection["acao"], string> = {
  remover: "text-danger",
  restaurar: "text-primary",
  preservar: "text-text-muted",
  ja_removido: "text-text-muted",
};

export default function ImportUndoDialog({ batch, onClose, onDone }: ImportUndoDialogProps) {
  const preview = useUndoPreview(batch.id);
  const undo = useUndoImport();
  const secoes = preview.data ? groupUndoItems(preview.data.itens) : [];
  const busy = undo.isPending;

  function handleConfirm() {
    undo.mutate(batch.id, { onSuccess: onDone });
  }

  return (
    <div
      className="fixed inset-0 bg-black/40 backdrop-blur-[2px] flex items-center justify-center z-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="undo-dialog-title"
      onClick={busy ? undefined : onClose}
    >
      <div
        className="bg-surface rounded-2xl shadow-2xl shadow-black/10 border border-slate-100/80
          p-6 w-full max-w-lg mx-4 max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 id="undo-dialog-title" className="text-lg font-bold text-text">
          Desfazer importação
        </h3>
        <p className="text-sm text-text-muted mt-1 truncate">{batch.filename}</p>

        <div className="mt-4 overflow-y-auto min-h-0 flex-1 space-y-4">
          {preview.isLoading && (
            <div className="flex items-center gap-2 text-sm text-text-muted py-6 justify-center">
              <Loader2 className="h-4 w-4 animate-spin" /> Calculando o que será desfeito...
            </div>
          )}

          {preview.error && (
            <p className="text-sm text-danger bg-red-50 border border-red-100 rounded-xl px-4 py-3">
              {preview.error.message}
            </p>
          )}

          {preview.data && undoChangesNothing(preview.data) && (
            <p className="text-sm text-text-muted bg-slate-50 rounded-xl px-4 py-3">
              Nada a remover nem restaurar: todos os lançamentos foram alterados ou
              apagados depois da importação. O lote será apenas marcado como desfeito.
            </p>
          )}

          {secoes.map((secao) => (
            <section key={secao.acao} data-testid={`undo-section-${secao.acao}`}>
              <p className={`text-sm font-semibold ${SECTION_TONE[secao.acao]}`}>
                {secao.titulo} ({secao.itens.length})
              </p>
              <p className="text-xs text-text-muted mb-2">{secao.descricao}</p>
              <ul className="divide-y divide-slate-100 border border-slate-100 rounded-xl">
                {secao.itens.map((item, i) => {
                  const detalhe = restoreDetail(item);
                  return (
                    <li key={i} className="flex items-start justify-between gap-3 px-3 py-2 text-sm">
                      <span className="min-w-0">
                        <span className="block text-text truncate">{item.descricao}</span>
                        <span className="block text-xs text-text-muted">
                          {undoItemKind(item)}
                          {item.data ? ` · ${formatDateBRWithYear(item.data)}` : ""}
                          {detalhe ? ` · ${detalhe}` : ""}
                        </span>
                      </span>
                      <span className="shrink-0 font-medium text-text tabular-nums">
                        {formatBRL(item.valor)}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </section>
          ))}
        </div>

        {undo.error && (
          <p className="text-sm text-danger mt-3">{undo.error.message}</p>
        )}

        <div className="flex justify-end gap-3 mt-5">
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            className="px-5 py-2.5 text-text-muted border border-border rounded-xl
              hover:bg-slate-50 active:scale-[0.98] transition-all duration-150 font-semibold
              disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={busy || !preview.data}
            className="px-5 py-2.5 bg-danger text-white rounded-xl font-semibold
              hover:bg-danger-hover hover:shadow-md hover:shadow-danger/20 active:scale-[0.98]
              transition-all duration-150 disabled:opacity-50 flex items-center gap-2"
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Undo2 className="h-4 w-4" />}
            Desfazer importação
          </button>
        </div>
      </div>
    </div>
  );
}
