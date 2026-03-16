import ViewSelector from "../components/ViewSelector";
import ScoreGauge from "../components/score/ScoreGauge";
import ScoreDimensionBreakdown from "../components/score/ScoreDimensionBreakdown";
import ScoreHistoryChart from "../components/score/ScoreHistoryChart";
import ScoreActions from "../components/score/ScoreActions";
import ScoreConservativeNote from "../components/score/ScoreConservativeNote";
import { useHealthScore } from "../hooks/useHealthScore";

export default function ScoreDetailView() {
  const { score, history, isLoading, isError, error } = useHealthScore();

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
          {/* Gauge principal */}
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

          {/* Breakdown das dimensoes */}
          <ScoreDimensionBreakdown dimensoes={score.dimensoes} />

          {/* Cenario conservador */}
          <ScoreConservativeNote
            cenario={score.cenario_conservador}
            scoreAtual={score.score.total}
          />

          {/* Ações sugeridas */}
          <ScoreActions acoes={score.acoes} />

          {/* Histórico */}
          <ScoreHistoryChart historico={history?.historico || []} />
        </div>
      )}
    </div>
  );
}
