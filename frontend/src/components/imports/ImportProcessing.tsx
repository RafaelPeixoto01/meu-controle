// CR-052 (F07): estagio de processamento assincrono — o lote ja esta no
// servidor e a extracao roda em background; a tela so acompanha o polling.
import { FileWarning, Loader2 } from "lucide-react";
import type { ImportBatchSummary } from "../../types";

interface ImportProcessingProps {
  batch: ImportBatchSummary | undefined;
  filename: string | null;
  error: string | null; // falha do polling (rede/sessao), nao do lote
  isDiscarding: boolean;
  onDiscard: () => void;
}

export default function ImportProcessing({
  batch,
  filename,
  error,
  isDiscarding,
  onDiscard,
}: ImportProcessingProps) {
  const nome = batch?.filename ?? filename;
  // So afirma "interpretando" com o status na mao: ao retomar um lote do banner
  // a primeira leitura ainda nao chegou, e ele pode estar apenas pronto para
  // abrir — anunciar extracao ali ofereceria um "Cancelar" destrutivo por engano
  const extraindo = batch?.status === "processando";

  return (
    <div
      className="bg-surface rounded-2xl shadow-sm border border-slate-100/80 p-10
        flex flex-col items-center gap-4 text-center"
      data-testid="import-processing"
    >
      <Loader2 className="h-10 w-10 text-primary animate-spin" />
      <div>
        <p className="font-bold text-text">
          {extraindo ? "Interpretando o documento..." : "Carregando importação..."}
        </p>
        {nome && <p className="text-sm text-text-muted mt-1 truncate max-w-xs">{nome}</p>}
        {extraindo && (
          <p className="text-sm text-text-muted mt-2 max-w-md">
            A IA está lendo as transações do PDF. Isso pode levar até 3 minutos em
            faturas grandes — <strong className="font-semibold">você pode fechar esta página</strong>:
            o processamento continua no servidor, e o lote fica aqui esperando a
            revisão quando terminar.
          </p>
        )}
      </div>

      {extraindo && (
        <button
          type="button"
          disabled={isDiscarding}
          onClick={onDiscard}
          className="px-4 py-2 text-text-muted border border-border rounded-lg text-sm font-semibold
            hover:bg-slate-50 transition-all duration-150 disabled:opacity-50"
        >
          Cancelar importação
        </button>
      )}

      {error && (
        <div className="flex items-start gap-2 bg-red-50 border border-red-100 rounded-xl px-4 py-3 text-left max-w-md">
          <FileWarning className="h-5 w-5 text-danger shrink-0 mt-0.5" />
          <p className="text-sm text-danger">{error}</p>
        </div>
      )}
    </div>
  );
}
