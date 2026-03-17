import ViewSelector from "../components/ViewSelector";
import ScoreGauge from "../components/score/ScoreGauge";
import ScoreDimensionBreakdown from "../components/score/ScoreDimensionBreakdown";
import ScoreHistoryChart from "../components/score/ScoreHistoryChart";
import ScoreActions from "../components/score/ScoreActions";
import ScoreConservativeNote from "../components/score/ScoreConservativeNote";
import DiagnosticoCard from "../components/analysis/DiagnosticoCard";
import AlertasList from "../components/analysis/AlertasList";
import BonsComportamentos from "../components/analysis/BonsComportamentos";
import MetasSugeridas from "../components/analysis/MetasSugeridas";
import GastosRecorrentes from "../components/analysis/GastosRecorrentes";
import MensagemMotivacional from "../components/analysis/MensagemMotivacional";
import AnalysisPlaceholder from "../components/analysis/AnalysisPlaceholder";
import AnalysisFooter from "../components/analysis/AnalysisFooter";
import { useHealthScore } from "../hooks/useHealthScore";
import { useAiAnalysis } from "../hooks/useAiAnalysis";

export default function ScoreDetailView() {
  const { score, history, isLoading, isError, error } = useHealthScore();
  const { analysis, isLoading: aiLoading, isError: aiError, refetch: aiRefetch } = useAiAnalysis();

  const aiDisponivel = analysis?.status === "disponivel" && analysis.resultado;
  const aiResult = analysis?.resultado;

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 pb-12 space-y-6">
      <ViewSelector />

      {isLoading && (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin mb-4" />
          <p className="text-text-muted text-sm">Calculando score...</p>
        </div>
      )}

      {isError && (
        <div className="text-center py-12">
          <p className="text-danger font-medium">
            {error?.message || "Erro ao calcular score"}
          </p>
          <p className="text-text-muted text-sm mt-1">
            Verifique sua conexão e tente novamente.
          </p>
        </div>
      )}

      {score && (
        <div className="space-y-6 animate-fade-in-up">
          {/* 1. Gauge principal */}
          <div className="bg-surface rounded-2xl shadow-sm border border-border p-6 flex justify-center">
            <ScoreGauge
              total={score.score.total}
              classificacao={score.score.classificacao}
              cor={score.score.cor}
              mensagem={score.score.mensagem}
              mensagemContextual={score.score.mensagem_contextual}
              variacao={score.score.variacao_mes_anterior}
            />
          </div>

          {/* 2. Diagnóstico da IA */}
          {aiLoading && <AnalysisPlaceholder status="loading" />}
          {aiError && (
            <AnalysisPlaceholder
              status="erro"
              reason="Não foi possível carregar a análise."
              onRetry={() => aiRefetch()}
            />
          )}
          {!aiLoading && !aiError && analysis?.status === "indisponivel" && (
            <AnalysisPlaceholder status="indisponivel" reason={analysis.reason} />
          )}
          {!aiLoading && !aiError && analysis?.status === "erro" && (
            <AnalysisPlaceholder
              status="erro"
              reason={analysis.reason}
              onRetry={() => aiRefetch()}
            />
          )}
          {aiDisponivel && aiResult && (
            <DiagnosticoCard diagnostico={aiResult.diagnostico} />
          )}

          {/* 3. Breakdown das dimensões */}
          <ScoreDimensionBreakdown dimensoes={score.dimensoes} />

          {/* 4. Cenário conservador */}
          <ScoreConservativeNote
            cenario={score.cenario_conservador}
            scoreAtual={score.score.total}
          />

          {/* 5. Alertas */}
          {aiDisponivel && aiResult && (
            <AlertasList alertas={aiResult.alertas} />
          )}

          {/* 6. Ações sugeridas (mescladas: score + IA) */}
          <ScoreActions
            acoes={score.acoes}
            aiRecomendacoes={aiDisponivel && aiResult ? aiResult.recomendacoes : undefined}
          />

          {/* 7. Bons comportamentos */}
          {aiDisponivel && aiResult && (
            <BonsComportamentos comportamentos={aiResult.bons_comportamentos} />
          )}

          {/* 8. Metas sugeridas */}
          {aiDisponivel && aiResult && (
            <MetasSugeridas metas={aiResult.metas} />
          )}

          {/* 9. Gastos recorrentes disfarçados */}
          {aiDisponivel && aiResult && (
            <GastosRecorrentes gastos={aiResult.gastos_recorrentes_disfarcados} />
          )}

          {/* 10. Mensagem motivacional */}
          {aiDisponivel && aiResult && (
            <MensagemMotivacional mensagem={aiResult.mensagem_motivacional} />
          )}

          {/* 11. Histórico */}
          <ScoreHistoryChart historico={history?.historico || []} />

          {/* 12. Footer da análise */}
          {aiDisponivel && analysis.modelo && analysis.generated_at && analysis.mes_referencia && (
            <AnalysisFooter
              modelo={analysis.modelo}
              generatedAt={analysis.generated_at}
              mesReferencia={analysis.mes_referencia}
            />
          )}
        </div>
      )}
    </div>
  );
}
