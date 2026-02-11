import { useState, useEffect } from "react";
import type { Income, IncomeCreate } from "../types";

interface IncomeFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: IncomeCreate) => void;
  initialData?: Income | null;
}

export default function IncomeFormModal({
  isOpen,
  onClose,
  onSubmit,
  initialData,
}: IncomeFormModalProps) {
  const [nome, setNome] = useState("");
  const [valor, setValor] = useState("");
  const [data, setData] = useState("");
  const [recorrente, setRecorrente] = useState(true);

  useEffect(() => {
    if (isOpen) {
      if (initialData) {
        setNome(initialData.nome);
        setValor(String(initialData.valor));
        setData(initialData.data ?? "");
        setRecorrente(initialData.recorrente);
      } else {
        setNome("");
        setValor("");
        setData("");
        setRecorrente(true);
      }
    }
  }, [isOpen, initialData]);

  if (!isOpen) return null;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit({
      nome,
      valor: Number(valor),
      data: data || null,
      recorrente,
    });
    onClose();
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 bg-black/40 backdrop-blur-[2px] flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-surface rounded-2xl shadow-2xl shadow-black/10 border border-slate-100/80
          p-7 w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-bold text-text mb-6">
          {initialData ? "Editar Receita" : "Nova Receita"}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-text-muted mb-1.5">
              Nome
            </label>
            <input
              type="text"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              required
              maxLength={255}
              placeholder="Ex: Salario"
              className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50
                placeholder:text-slate-400
                focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white
                transition-all duration-200"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-text-muted mb-1.5">
              Valor (R$)
            </label>
            <input
              type="number"
              value={valor}
              onChange={(e) => setValor(e.target.value)}
              required
              min="0.01"
              step="0.01"
              placeholder="0,00"
              className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50
                placeholder:text-slate-400 tabular-nums
                focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white
                transition-all duration-200"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-text-muted mb-1.5">
              Data de Recebimento
            </label>
            <input
              type="date"
              value={data}
              onChange={(e) => setData(e.target.value)}
              className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50
                focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white
                transition-all duration-200"
            />
          </div>
          <div className="flex items-center gap-2.5">
            <input
              type="checkbox"
              id="recorrente-income"
              checked={recorrente}
              onChange={(e) => setRecorrente(e.target.checked)}
              className="h-4 w-4 accent-primary rounded"
            />
            <label htmlFor="recorrente-income" className="text-sm font-medium text-text-muted">
              Recorrente (repete todo mes)
            </label>
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 text-text-muted border border-border rounded-xl
                hover:bg-slate-50 active:bg-slate-100 active:scale-[0.98]
                transition-all duration-150 font-semibold"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-6 py-2.5 bg-primary text-white rounded-xl font-semibold
                hover:bg-primary-hover hover:shadow-md hover:shadow-primary/20
                active:scale-[0.98]
                transition-all duration-150"
            >
              Salvar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
