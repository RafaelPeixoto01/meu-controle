// CR-047 (F07): passo final — resumo do que foi gravado.
import { useNavigate } from "react-router-dom";
import { CheckCircle2 } from "lucide-react";
import type { ImportConfirmResponse } from "../../types";

interface ImportResultProps {
  result: ImportConfirmResponse;
  onImportAnother: () => void;
}

export default function ImportResult({ result, onImportAnother }: ImportResultProps) {
  const navigate = useNavigate();

  return (
    <div className="bg-surface rounded-2xl shadow-sm border border-slate-100/80 p-10
      flex flex-col items-center gap-5 text-center">
      <CheckCircle2 className="h-12 w-12 text-success" />
      <div>
        <p className="font-bold text-text text-lg">Importação concluída</p>
        <p className="text-sm text-text-muted mt-1">
          {result.gastos_diarios_criados}{" "}
          {result.gastos_diarios_criados === 1 ? "gasto diário criado" : "gastos diários criados"} ·{" "}
          {result.planejados_atualizados}{" "}
          {result.planejados_atualizados === 1 ? "planejado pago" : "planejados pagos"} ·{" "}
          {result.descartadas}{" "}
          {result.descartadas === 1 ? "transação descartada" : "transações descartadas"}
        </p>
      </div>
      <div className="flex flex-wrap justify-center gap-3">
        <button
          type="button"
          onClick={() => navigate("/daily-expenses")}
          className="px-5 py-2.5 bg-primary text-white rounded-xl font-semibold
            hover:bg-primary-hover transition-all duration-150"
        >
          Ver Gastos Diários
        </button>
        <button
          type="button"
          onClick={() => navigate("/")}
          className="px-5 py-2.5 text-text-muted border border-border rounded-xl font-semibold
            hover:bg-slate-50 transition-all duration-150"
        >
          Ver Gastos Planejados
        </button>
        <button
          type="button"
          onClick={onImportAnother}
          className="px-5 py-2.5 text-primary border border-primary/30 rounded-xl font-semibold
            hover:bg-primary/5 transition-all duration-150"
        >
          Importar outro arquivo
        </button>
      </div>
    </div>
  );
}
