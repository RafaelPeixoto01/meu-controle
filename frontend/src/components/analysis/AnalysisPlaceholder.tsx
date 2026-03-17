import { Brain, AlertCircle, RefreshCw } from "lucide-react";

interface AnalysisPlaceholderProps {
  status: "loading" | "indisponivel" | "erro";
  reason?: string;
  onRetry?: () => void;
}

export default function AnalysisPlaceholder({ status, reason, onRetry }: AnalysisPlaceholderProps) {
  if (status === "loading") {
    return (
      <div className="bg-surface rounded-2xl shadow-sm border border-border p-6">
        <div className="flex flex-col items-center justify-center py-6">
          <div className="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin mb-4" />
          <p className="text-text-muted text-sm">Gerando análise com IA...</p>
          <p className="text-text-muted/60 text-xs mt-1">Isso pode levar alguns segundos</p>
        </div>
      </div>
    );
  }

  if (status === "erro") {
    return (
      <div className="bg-surface rounded-2xl shadow-sm border border-border p-6">
        <div className="flex flex-col items-center justify-center py-6">
          <AlertCircle size={32} className="text-danger mb-3" />
          <p className="text-text font-medium text-sm">Erro na análise</p>
          <p className="text-text-muted text-xs mt-1 text-center max-w-xs">
            {reason || "Não foi possível gerar a análise. Tente novamente mais tarde."}
          </p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-4 flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
            >
              <RefreshCw size={14} />
              Tentar novamente
            </button>
          )}
        </div>
      </div>
    );
  }

  // indisponivel
  return (
    <div className="bg-surface rounded-2xl shadow-sm border border-border p-6">
      <div className="flex flex-col items-center justify-center py-6">
        <Brain size={32} className="text-text-muted/40 mb-3" />
        <p className="text-text font-medium text-sm">Análise indisponível</p>
        <p className="text-text-muted text-xs mt-1 text-center max-w-xs">
          {reason || "Dados insuficientes para gerar análise por IA."}
        </p>
      </div>
    </div>
  );
}
