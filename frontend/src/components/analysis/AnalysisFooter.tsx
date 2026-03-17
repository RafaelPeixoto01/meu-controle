interface AnalysisFooterProps {
  modelo: string;
  generatedAt: string;
  mesReferencia: string;
}

export default function AnalysisFooter({ modelo, generatedAt, mesReferencia }: AnalysisFooterProps) {
  const formattedDate = new Date(generatedAt).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className="text-center text-xs text-text-muted/60 py-2 space-y-1">
      <p>
        Análise gerada por IA ({modelo}) em {formattedDate} — ref. {mesReferencia}
      </p>
      <p>
        Esta análise é uma sugestão automatizada. Consulte um profissional para decisões financeiras importantes.
      </p>
    </div>
  );
}
