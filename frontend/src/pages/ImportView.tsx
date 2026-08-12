// CR-047 (F07): pagina /import — fluxo upload → processando → revisao → resultado.
import { useState } from "react";
import ViewSelector from "../components/ViewSelector";
import ImportUpload from "../components/imports/ImportUpload";
import ImportReview from "../components/imports/ImportReview";
import ImportResult from "../components/imports/ImportResult";
import {
  useConfirmImport,
  useDiscardImport,
  useMatchTargets,
  usePendingImports,
  useUploadImport,
} from "../hooks/useImports";
import { fetchImportBatch } from "../services/api";
import type { ImportBatch, ImportConfirmRequest, ImportConfirmResponse } from "../types";

type Stage = "upload" | "review" | "result";

export default function ImportView() {
  const [stage, setStage] = useState<Stage>("upload");
  const [batch, setBatch] = useState<ImportBatch | null>(null);
  const [result, setResult] = useState<ImportConfirmResponse | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [isResuming, setIsResuming] = useState(false);

  const pendingQuery = usePendingImports();
  const uploadMutation = useUploadImport();
  const confirmMutation = useConfirmImport();
  const discardMutation = useDiscardImport();
  const matchTargetsQuery = useMatchTargets(stage === "review" ? batch : null);

  function handleUpload(file: File) {
    setNotice(null);
    uploadMutation.mutate(file, {
      onSuccess: (response) => {
        if (response.status === "disponivel" && response.batch) {
          setBatch(response.batch);
          setStage("review");
        } else {
          setNotice(response.reason || "Não foi possível processar o documento.");
        }
      },
      onError: (error) => {
        setNotice(error.message || "Erro ao enviar o arquivo.");
      },
    });
  }

  async function handleResume(batchId: string) {
    setNotice(null);
    setIsResuming(true);
    try {
      const resumed = await fetchImportBatch(batchId);
      setBatch(resumed);
      setStage("review");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Erro ao retomar a importação.");
    } finally {
      setIsResuming(false);
    }
  }

  function handleDiscard(batchId: string) {
    setNotice(null);
    discardMutation.mutate(batchId, {
      onSuccess: () => {
        if (batch?.id === batchId) {
          setBatch(null);
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
          setStage("result");
        },
      }
    );
  }

  function handleImportAnother() {
    setBatch(null);
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
          isResuming={isResuming || discardMutation.isPending}
          onUpload={handleUpload}
          onResume={handleResume}
          onDiscard={handleDiscard}
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
