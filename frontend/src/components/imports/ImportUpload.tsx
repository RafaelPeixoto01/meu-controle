// CR-047 (F07): passo de upload do fluxo de importacao.
import { useRef, useState } from "react";
import { FileUp, FileWarning, Loader2 } from "lucide-react";
import type { ImportBatchSummary } from "../../types";

const MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024; // espelha o limite do backend (CR-046)

interface ImportUploadProps {
  isUploading: boolean;
  notice: string | null; // mensagem de indisponivel/erro vinda do backend
  pendingBatches: ImportBatchSummary[];
  isResuming: boolean;
  onUpload: (file: File) => void;
  onResume: (batchId: string) => void;
  onDiscard: (batchId: string) => void;
}

export default function ImportUpload({
  isUploading,
  notice,
  pendingBatches,
  isResuming,
  onUpload,
  onResume,
  onDiscard,
}: ImportUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [clientError, setClientError] = useState<string | null>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = ""; // permite re-selecionar o mesmo arquivo
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setClientError("Apenas arquivos PDF são aceitos.");
      return;
    }
    if (file.size > MAX_PDF_SIZE_BYTES) {
      setClientError("O arquivo excede o limite de 10MB.");
      return;
    }
    setClientError(null);
    onUpload(file);
  }

  if (isUploading) {
    return (
      <div className="bg-surface rounded-2xl shadow-sm border border-slate-100/80 p-10
        flex flex-col items-center gap-4 text-center">
        <Loader2 className="h-10 w-10 text-primary animate-spin" />
        <div>
          <p className="font-bold text-text">Interpretando o documento...</p>
          <p className="text-sm text-text-muted mt-1">
            A IA está lendo as transações do PDF. Isso pode levar até 1 minuto e meio —
            não feche esta página.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {pendingBatches.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 space-y-3">
          <p className="text-sm font-semibold text-amber-800">
            Você tem {pendingBatches.length === 1 ? "uma importação pendente" : `${pendingBatches.length} importações pendentes`} de revisão:
          </p>
          {pendingBatches.map((batch) => (
            <div
              key={batch.id}
              className="flex flex-wrap items-center justify-between gap-2 bg-white/60 rounded-xl px-3 py-2"
            >
              <span className="text-sm text-text truncate">
                {batch.filename}
                {batch.banco_detectado ? ` — ${batch.banco_detectado}` : ""}
              </span>
              <span className="flex gap-2">
                <button
                  type="button"
                  disabled={isResuming}
                  onClick={() => onResume(batch.id)}
                  className="px-3 py-1.5 bg-primary text-white rounded-lg text-xs font-semibold
                    hover:bg-primary-hover transition-all duration-150 disabled:opacity-50"
                >
                  Retomar revisão
                </button>
                <button
                  type="button"
                  disabled={isResuming}
                  onClick={() => onDiscard(batch.id)}
                  className="px-3 py-1.5 text-text-muted border border-border rounded-lg text-xs font-semibold
                    hover:bg-slate-50 transition-all duration-150 disabled:opacity-50"
                >
                  Descartar
                </button>
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="bg-surface rounded-2xl shadow-sm border border-slate-100/80 p-10
        flex flex-col items-center gap-4 text-center">
        <div className="h-14 w-14 rounded-2xl bg-primary/10 flex items-center justify-center">
          <FileUp className="h-7 w-7 text-primary" />
        </div>
        <div>
          <p className="font-bold text-text text-lg">Importar extrato ou fatura</p>
          <p className="text-sm text-text-muted mt-1 max-w-md">
            Envie o PDF do extrato da conta ou da fatura do cartão (Nubank, Itaú,
            Mercado Pago...). As transações serão interpretadas e você revisa tudo
            antes de gravar.
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleFileChange}
          className="hidden"
          data-testid="import-file-input"
        />
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="px-6 py-3 bg-primary text-white rounded-xl font-semibold
            hover:bg-primary-hover hover:shadow-md hover:shadow-primary/20
            active:scale-[0.98] transition-all duration-150"
        >
          Selecionar PDF
        </button>
        <p className="text-xs text-slate-400">Somente PDF, até 10MB.</p>

        {(clientError || notice) && (
          <div className="flex items-start gap-2 bg-red-50 border border-red-100 rounded-xl px-4 py-3 text-left max-w-md">
            <FileWarning className="h-5 w-5 text-danger shrink-0 mt-0.5" />
            <p className="text-sm text-danger">{clientError || notice}</p>
          </div>
        )}
      </div>
    </div>
  );
}
