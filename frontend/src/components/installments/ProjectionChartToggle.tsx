import { useState } from "react";
import { BarChart3, GanttChart } from "lucide-react";
import ProjectionStackedChart from "./ProjectionStackedChart";
import ProjectionGantt from "./ProjectionGantt";
import type { InstallmentProjectionResponse } from "../../types";

interface ProjectionChartToggleProps {
  data: InstallmentProjectionResponse;
}

type ChartView = "projection" | "timeline";

export default function ProjectionChartToggle({ data }: ProjectionChartToggleProps) {
  const [view, setView] = useState<ChartView>("projection");

  return (
    <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 p-5 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-text-muted uppercase tracking-wide">
          {view === "projection" ? "Projeção 12 Meses" : "Timeline de Parcelas"}
        </h3>
        <div className="flex bg-slate-100 rounded-lg p-0.5">
          <button
            onClick={() => setView("projection")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              view === "projection"
                ? "bg-white text-primary shadow-sm"
                : "text-text-muted hover:text-text"
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Projeção</span>
          </button>
          <button
            onClick={() => setView("timeline")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              view === "timeline"
                ? "bg-white text-primary shadow-sm"
                : "text-text-muted hover:text-text"
            }`}
          >
            <GanttChart className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Timeline</span>
          </button>
        </div>
      </div>

      {view === "projection" ? (
        <ProjectionStackedChart
          projecao={data.projecao_mensal}
          parcelas={data.parcelas}
          rendaAtual={data.renda_atual}
        />
      ) : (
        <ProjectionGantt
          projecao={data.projecao_mensal}
          parcelas={data.parcelas}
        />
      )}
    </div>
  );
}
