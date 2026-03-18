import { X, Settings } from "lucide-react";
import type { ConfiguracaoAlertas } from "../../types";
import { useState, useEffect } from "react";

interface AlertsSettingsProps {
  config: ConfiguracaoAlertas;
  onClose: () => void;
  onSave: (data: Partial<ConfiguracaoAlertas>) => void;
  isSaving: boolean;
}

const TOGGLE_FIELDS: { key: keyof ConfiguracaoAlertas; label: string }[] = [
  { key: "alerta_atrasadas", label: "Despesas atrasadas" },
  { key: "alerta_parcelas_encerrando", label: "Parcelas encerrando" },
  { key: "alerta_score", label: "Variação do score" },
  { key: "alerta_comprometimento", label: "Comprometimento alto" },
  { key: "alerta_parcela_ativada", label: "Parcela ativada" },
  { key: "alerta_ia", label: "Alertas da IA" },
];

export default function AlertsSettings({ config, onClose, onSave, isSaving }: AlertsSettingsProps) {
  const [local, setLocal] = useState<ConfiguracaoAlertas>(config);

  useEffect(() => {
    setLocal(config);
  }, [config]);

  function handleToggle(key: keyof ConfiguracaoAlertas) {
    setLocal((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  function handleSave() {
    onSave(local);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />

      <div className="relative bg-surface rounded-2xl shadow-xl border border-border w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border">
          <div className="flex items-center gap-2">
            <Settings size={18} className="text-primary" />
            <h2 className="text-base font-semibold text-text">Configurar Alertas</h2>
          </div>
          <button type="button" onClick={onClose} className="text-text-muted hover:text-text p-1">
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 space-y-5">
          {/* Antecedência de vencimento */}
          <div>
            <label className="text-sm font-medium text-text">
              Antecedência de vencimento (dias)
            </label>
            <select
              value={local.antecedencia_vencimento}
              onChange={(e) =>
                setLocal((prev) => ({
                  ...prev,
                  antecedencia_vencimento: Number(e.target.value),
                }))
              }
              className="mt-1 w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
            >
              {[1, 2, 3, 5, 7].map((d) => (
                <option key={d} value={d}>{d} dia{d > 1 ? "s" : ""}</option>
              ))}
            </select>
          </div>

          {/* Limiar de comprometimento */}
          <div>
            <label className="text-sm font-medium text-text">
              Limiar de comprometimento (%)
            </label>
            <select
              value={local.limiar_comprometimento}
              onChange={(e) =>
                setLocal((prev) => ({
                  ...prev,
                  limiar_comprometimento: Number(e.target.value),
                }))
              }
              className="mt-1 w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
            >
              {[30, 40, 50, 60, 70, 80, 90].map((p) => (
                <option key={p} value={p}>{p}%</option>
              ))}
            </select>
          </div>

          {/* Toggles */}
          <div className="space-y-3">
            <p className="text-sm font-medium text-text">Tipos de alerta</p>
            {TOGGLE_FIELDS.map(({ key, label }) => (
              <label key={key} className="flex items-center justify-between cursor-pointer">
                <span className="text-sm text-text">{label}</span>
                <button
                  type="button"
                  onClick={() => handleToggle(key)}
                  className={`relative w-10 h-5 rounded-full transition-colors ${
                    local[key] ? "bg-primary" : "bg-slate-300"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${
                      local[key] ? "translate-x-5" : ""
                    }`}
                  />
                </button>
              </label>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-5 border-t border-border">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm text-text-muted hover:text-text"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving}
            className="px-4 py-2 text-sm font-semibold text-white bg-primary hover:bg-primary/90 rounded-lg disabled:opacity-50"
          >
            {isSaving ? "Salvando..." : "Salvar"}
          </button>
        </div>
      </div>
    </div>
  );
}
