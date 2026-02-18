import { useState, useEffect } from "react";
import type { DailyExpense, DailyExpenseCreate } from "../types";
import { useDailyExpensesCategories } from "../hooks/useDailyExpenses";

interface DailyExpenseFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: DailyExpenseCreate) => void;
  initialData?: DailyExpense | null;
}

function getTodayISO(): string {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export default function DailyExpenseFormModal({
  isOpen,
  onClose,
  onSubmit,
  initialData,
}: DailyExpenseFormModalProps) {
  const { data: categoriesData } = useDailyExpensesCategories();

  const [descricao, setDescricao] = useState("");
  const [valor, setValor] = useState("");
  const [data, setData] = useState(getTodayISO());
  const [selectedCategoria, setSelectedCategoria] = useState("");
  const [subcategoria, setSubcategoria] = useState("");
  const [metodoPagamento, setMetodoPagamento] = useState("");

  useEffect(() => {
    if (isOpen) {
      if (initialData) {
        setDescricao(initialData.descricao);
        setValor(String(initialData.valor));
        setData(initialData.data);
        setSelectedCategoria(initialData.categoria);
        setSubcategoria(initialData.subcategoria);
        setMetodoPagamento(initialData.metodo_pagamento);
      } else {
        setDescricao("");
        setValor("");
        setData(getTodayISO());
        setSelectedCategoria("");
        setSubcategoria("");
        setMetodoPagamento("");
      }
    }
  }, [isOpen, initialData]);

  if (!isOpen) return null;

  const categorias = categoriesData?.categorias ?? {};
  const metodosPagamento = categoriesData?.metodos_pagamento ?? [];
  const subcategorias = selectedCategoria
    ? categorias[selectedCategoria] ?? []
    : [];

  function handleCategoriaChange(cat: string) {
    setSelectedCategoria(cat);
    setSubcategoria("");
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit({
      descricao,
      valor: Number(valor),
      data,
      subcategoria,
      metodo_pagamento: metodoPagamento,
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
          {initialData ? "Editar Gasto" : "Novo Gasto"}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-text-muted mb-1.5">
              Descricao
            </label>
            <input
              type="text"
              value={descricao}
              onChange={(e) => setDescricao(e.target.value)}
              required
              maxLength={255}
              placeholder="Ex: Compras no mercado"
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
              Data
            </label>
            <input
              type="date"
              value={data}
              onChange={(e) => setData(e.target.value)}
              required
              className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50
                focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white
                transition-all duration-200"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-text-muted mb-1.5">
                Categoria
              </label>
              <select
                value={selectedCategoria}
                onChange={(e) => handleCategoriaChange(e.target.value)}
                required
                className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50
                  focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white
                  transition-all duration-200"
              >
                <option value="">Selecione...</option>
                {Object.keys(categorias).map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-text-muted mb-1.5">
                Subcategoria
              </label>
              <select
                value={subcategoria}
                onChange={(e) => setSubcategoria(e.target.value)}
                required
                disabled={!selectedCategoria}
                className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50
                  focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white
                  transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <option value="">Selecione...</option>
                {subcategorias.map((sub) => (
                  <option key={sub} value={sub}>
                    {sub}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-text-muted mb-1.5">
              Metodo de Pagamento
            </label>
            <select
              value={metodoPagamento}
              onChange={(e) => setMetodoPagamento(e.target.value)}
              required
              className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50
                focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white
                transition-all duration-200"
            >
              <option value="">Selecione...</option>
              {metodosPagamento.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
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
