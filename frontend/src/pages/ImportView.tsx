// CR-047 (F07): pagina /import — fluxo upload → processando → revisao → resultado.
// CR-052: a extracao roda em background no servidor; o estagio "processing"
// acompanha o lote por polling em vez de segurar o request do upload.
import { useEffect, useState } from "react";
import ViewSelector from "../components/ViewSelector";
import ImportUpload from "../components/imports/ImportUpload";
import ImportProcessing from "../components/imports/ImportProcessing";
import ImportReview from "../components/imports/ImportReview";
import ImportResult from "../components/imports/ImportResult";
import {
  useConfirmImport,
  useDiscardImport,
  useImportBatch,
  useMatchTargets,
  usePendingImports,
  useUploadImport,
} from "../hooks/useImports";
import { nextStageForBatch, type ImportStage } from "../utils/importReview";
import type { ImportBatch, ImportConfirmRequest, ImportConfirmResponse } from "../types";

export default function ImportView() {
  const [stage, setStage] = useState<ImportStage>("upload");
  const [batchId, setBatchId] = useState<string | null>(null);
  const [batch, setBatch] = useState<ImportBatch | null>(null);
  const [filename, setFilename] = useState<string | null>(null);
  const [result, setResult] = useState<ImportConfirmResponse | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const pendingQuery = usePendingImports();
  const uploadMutation = useUploadImport();
  const confirmMutation = useConfirmImport();
  const discardMutation = useDiscardImport();
  const pollQuery = useImportBatch(batchId, stage === "processing");
  const matchTargetsQuery = useMatchTargets(stage === "review" ? batch : null);

  // CR-052: o lote em processamento decide sozinho o proximo estagio. Sai da
  // tela quando a extracao termina (→ revisao) ou falha (→ upload com aviso).
  //
  // Efeito, e nao valor derivado: ao entrar na revisao o lote e *copiado* para
  // o state e o polling e desligado, de modo que um refetch posterior nao troque
  // o objeto por baixo da ImportReview e descarte as edicoes do usuario.
  // (useQuery da v5 nao tem onSuccess — reagir ao dado que chega e via effect.)
  const polled = pollQuery.data;
  useEffect(() => {
    if (stage !== "processing" || !polled) return;
    const next = nextStageForBatch(polled);
    if (next === "processing") return;

    if (next === "review") {
      setBatch(polled);
    } else {
      setNotice(polled.erro_mensagem || "Não foi possível processar o documento.");
      setBatchId(null);
    }
    setStage(next);
  }, [stage, polled]);

  function handleUpload(file: File) {
    setNotice(null);
    setFilename(file.name);
    uploadMutation.mutate(file, {
      onSuccess: (response) => {
        // 202: o lote nasce em 'processando' e so tem metadados aqui
        if (response.status === "disponivel" && response.batch) {
          setBatchId(response.batch.id);
          setStage("processing");
        } else {
          setNotice(response.reason || "Não foi possível processar o documento.");
        }
      },
      onError: (error) => {
        setNotice(error.message || "Erro ao enviar o arquivo.");
      },
    });
  }

  function handleResume(id: string) {
    setNotice(null);
    const pending = pendingQuery.data?.find((b) => b.id === id);
    setBatchId(id);
    setFilename(pending?.filename ?? null);
    // Lote ainda em extracao volta para o polling; pronto para revisao cai no
    // effect acima assim que a primeira leitura chegar
    setStage("processing");
  }

  function handleDiscard(id: string) {
    setNotice(null);
    discardMutation.mutate(id, {
      onSuccess: () => {
        if (batchId === id) {
          setBatch(null);
          setBatchId(null);
          setStage("upload");
        }
      },
      onError: (error) => {
        // Nao sair da revisao em caso de falha — preserva as edicoes do usuario;
        // o erro aparece no rodape da revisao (ou no aviso do upload)
        setNotice(error.message || "Erro ao descartar a importação.");
      },
    });
  }

  function handleConfirm(payload: ImportConfirmRequest) {
    if (!batch) return;
    confirmMutation.mutate(
      { batchId: batch.id, data: payload },
      {
        onSuccess: (response) => {
          setResult(response);
          setBatchId(null);
          setStage("result");
        },
      }
    );
  }

  function handleImportAnother() {
    setBatch(null);
    setBatchId(null);
    setFilename(null);
    setResult(null);
    setNotice(null);
    confirmMutation.reset();
    uploadMutation.reset();
    setStage("upload");
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 pb-12 space-y-6">
      <ViewSelector />

      {stage === "upload" && (
        <ImportUpload
          isUploading={uploadMutation.isPending}
          notice={notice}
          pendingBatches={pendingQuery.data ?? []}
          isResuming={discardMutation.isPending}
          onUpload={handleUpload}
          onResume={handleResume}
          onDiscard={handleDiscard}
        />
      )}

      {stage === "processing" && (
        <ImportProcessing
          batch={polled}
          filename={filename}
          error={notice ?? pollQuery.error?.message ?? null}
          isDiscarding={discardMutation.isPending}
          onDiscard={() => batchId && handleDiscard(batchId)}
        />
      )}

      {stage === "review" && batch && (
        <ImportReview
          batch={batch}
          matchTargets={matchTargetsQuery.data ?? {}}
          isConfirming={confirmMutation.isPending}
          confirmError={
            confirmMutation.error?.message ?? discardMutation.error?.message ?? null
          }
          onConfirm={handleConfirm}
          onDiscard={() => handleDiscard(batch.id)}
          isDiscarding={discardMutation.isPending}
        />
      )}

      {stage === "result" && result && (
        <ImportResult result={result} onImportAnother={handleImportAnother} />
      )}
    </div>
  );
}
