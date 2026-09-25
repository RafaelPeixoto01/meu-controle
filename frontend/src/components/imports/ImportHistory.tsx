// CR-056 (F07): "Importacoes anteriores" — historico paginado dos lotes, com
// o desfazer dos confirmados. Antes, um lote confirmado sumia da interface.
import { useState } from "react";
import { CheckCircle2, History, Loader2 } from "lucide-react";
import type { ImportHistoryItem } from "../../types";
import { HISTORY_PAGE_SIZE, useImportHistory } from "../../hooks/useImports";
import {
  BATCH_STATUS_LABEL,
  canResume,
  describeUndoResult,
  summarizeHistoryItem,
  totalPages,
  type StatusTone,
} from "../../utils/importHistory";
import ImportUndoDialog from "./ImportUndoDialog";

interface ImportHistoryProps {
  onResume: (batchId: string) => void;
}

const TONE_CLASS: Record<StatusTone, string> = {
  success: "bg-pago-bg text-pago",
  warning: "bg-pendente-bg text-pendente",
  danger: "bg-atrasado-bg text-atrasado",
  info: "bg-primary-light text-primary",
  muted: "bg-slate-100 text-text-muted",
};

const TIPO_LABEL: Record<string, string> = { fatura: "Fatura", extrato: "Extrato" };

function formatDateTime(iso: string): string {
  // Mesmo tratamento do AnalysisFooter: o backend grava datetime naive, lido
  // aqui como horario local do browser
  return new Date(iso).toLocaleString("pt-BR", {
    day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

export default function ImportHistory({ onResume }: ImportHistoryProps) {
  const [page, setPage] = useState(1);
  const [undoTarget, setUndoTarget] = useState<ImportHistoryItem | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const history = useImportHistory(page);

  const data = history.data;
  // Sem nenhum lote, a secao nao aparece: a tela de upload fica limpa no
  // primeiro uso
  if (!data || data.total === 0) {
    return history.error ? (
      <p className="text-sm text-danger">Não foi possível carregar o histórico de importações.</p>
    ) : null;
  }

  const pages = totalPages(data.total, HISTORY_PAGE_SIZE);

  return (
    <section className="bg-surface rounded-2xl shadow-sm border border-slate-100/80 p-5 space-y-3">
      <div className="flex items-center justify-between gap-2">
        <h2 className="font-bold text-text flex items-center gap-2">
          <History className="h-5 w-5 text-text-muted" />
          Importações anteriores
        </h2>
        {history.isFetching && <Loader2 className="h-4 w-4 text-text-muted animate-spin" />}
      </div>

      {notice && (
        <p
          role="status"
          className="flex items-start gap-2 text-sm text-success-dark bg-pago-bg/60 rounded-xl px-3 py-2"
        >
          <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
          {notice}
        </p>
      )}

      <ul className="divide-y divide-slate-100">
        {data.items.map((item) => {
          const status = BATCH_STATUS_LABEL[item.status] ?? { label: item.status, tone: "muted" };
          const resumo = summarizeHistoryItem(item);
          const origem = [item.banco_detectado, item.tipo_documento && TIPO_LABEL[item.tipo_documento]]
            .filter(Boolean)
            .join(" · ");
          return (
            <li
              key={item.id}
              data-testid="import-history-item"
              className="flex flex-wrap items-center justify-between gap-2 py-3"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-text truncate">{item.filename}</p>
                <p className="text-xs text-text-muted">
                  {formatDateTime(item.created_at)}
                  {origem ? ` · ${origem}` : ""}
                  {resumo ? ` · ${resumo}` : ""}
                </p>
                {item.status === "erro" && item.erro_mensagem && (
                  <p className="text-xs text-danger mt-0.5">{item.erro_mensagem}</p>
                )}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${TONE_CLASS[status.tone]}`}>
                  {status.label}
                </span>
                {canResume(item) && (
                  <button
                    type="button"
                    onClick={() => onResume(item.id)}
                    className="px-3 py-1.5 bg-primary text-white rounded-lg text-xs font-semibold
                      hover:bg-primary-hover transition-all duration-150"
                  >
                    Abrir
                  </button>
                )}
                {item.pode_desfazer && (
                  <button
                    type="button"
                    onClick={() => {
                      setNotice(null);
                      setUndoTarget(item);
                    }}
                    className="px-3 py-1.5 text-danger border border-danger/30 rounded-lg text-xs font-semibold
                      hover:bg-danger/5 transition-all duration-150"
                  >
                    Desfazer
                  </button>
                )}
              </div>
            </li>
          );
        })}
      </ul>

      {pages > 1 && (
        <div className="flex items-center justify-between pt-1">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="px-3 py-1.5 text-text-muted border border-border rounded-lg text-xs font-semibold
              hover:bg-slate-50 disabled:opacity-40"
          >
            Anterior
          </button>
          <span className="text-xs text-text-muted">
            Página {page} de {pages}
          </span>
          <button
            type="button"
            disabled={page >= pages}
            onClick={() => setPage((p) => p + 1)}
            className="px-3 py-1.5 text-text-muted border border-border rounded-lg text-xs font-semibold
              hover:bg-slate-50 disabled:opacity-40"
          >
            Próxima
          </button>
        </div>
      )}

      {undoTarget && (
        <ImportUndoDialog
          batch={undoTarget}
          onClose={() => setUndoTarget(null)}
          onDone={(result) => {
            setUndoTarget(null);
            setNotice(describeUndoResult(result));
          }}
        />
      )}
    </section>
  );
}
