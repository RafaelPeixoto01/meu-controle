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
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-bold text-gray-800 mb-5">
          {initialData ? "Editar Receita" : "Nova Receita"}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nome
            </label>
            <input
              type="text"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              required
              maxLength={255}
              placeholder="Ex: Salario"
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5
                focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary
                transition-colors duration-150"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
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
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5
                focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary
                transition-colors duration-150 tabular-nums"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Data de Recebimento
            </label>
            <input
              type="date"
              value={data}
              onChange={(e) => setData(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5
                focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary
                transition-colors duration-150"
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
            <label htmlFor="recorrente-income" className="text-sm text-gray-700">
              Recorrente (repete todo mes)
            </label>
          </div>
          <div className="flex justify-end gap-3 pt-3 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 text-gray-600 border border-gray-300 rounded-lg
                hover:bg-gray-50 active:bg-gray-100
                transition-colors duration-150 font-medium"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-5 py-2.5 bg-primary text-white rounded-lg font-medium
                hover:bg-primary-hover active:bg-blue-800
                transition-colors duration-150"
            >
              Salvar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
