import { useState, useEffect } from "react";
import type { Expense, ExpenseCreate } from "../types";
import { useExpenseCategories } from "../hooks/useExpenses";

interface ExpenseFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ExpenseCreate) => void;
  initialData?: Expense | null;
}

export default function ExpenseFormModal({
  isOpen,
  onClose,
  onSubmit,
  initialData,
}: ExpenseFormModalProps) {
  const { data: categoriesData } = useExpenseCategories();

  const [nome, setNome] = useState("");
  const [valor, setValor] = useState("");
  const [vencimento, setVencimento] = useState("");
  const [parcelaAtual, setParcelaAtual] = useState("");
  const [parcelaTotal, setParcelaTotal] = useState("");
  const [recorrente, setRecorrente] = useState(true);
  const [parcelaError, setParcelaError] = useState("");
  const [selectedCategoria, setSelectedCategoria] = useState("");
  const [subcategoria, setSubcategoria] = useState("");

  useEffect(() => {
    if (isOpen) {
      setParcelaError("");
      if (initialData) {
        setNome(initialData.nome);
        setValor(String(initialData.valor));
        setVencimento(initialData.vencimento);
        setParcelaAtual(
          initialData.parcela_atual !== null
            ? String(initialData.parcela_atual)
            : ""
        );
        setParcelaTotal(
          initialData.parcela_total !== null
            ? String(initialData.parcela_total)
            : ""
        );
        setRecorrente(initialData.recorrente);
        setSelectedCategoria(initialData.categoria ?? "");
        setSubcategoria(initialData.subcategoria ?? "");
      } else {
        setNome("");
        setValor("");
        setVencimento("");
        setParcelaAtual("");
        setParcelaTotal("");
        setRecorrente(true);
        setSelectedCategoria("");
        setSubcategoria("");
      }
    }
  }, [isOpen, initialData]);

  if (!isOpen) return null;

  const hasParcelas = parcelaAtual !== "" || parcelaTotal !== "";
  const categorias = categoriesData?.categorias ?? {};
  const subcategorias = selectedCategoria
    ? categorias[selectedCategoria] ?? []
    : [];

  function handleCategoriaChange(cat: string) {
    setSelectedCategoria(cat);
    setSubcategoria("");
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setParcelaError("");

    const atual = parcelaAtual !== "" ? Number(parcelaAtual) : null;
    const total = parcelaTotal !== "" ? Number(parcelaTotal) : null;

    if (atual !== null && total !== null && atual > total) {
      setParcelaError("Parcela atual deve ser menor ou igual ao total.");
      return;
    }

    onSubmit({
      nome,
      valor: Number(valor),
      vencimento,
      parcela_atual: atual,
      parcela_total: total,
      recorrente: hasParcelas ? recorrente : recorrente,
      subcategoria: subcategoria || null,
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
          {initialData ? "Editar Despesa" : "Nova Despesa"}
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
              placeholder="Ex: Aluguel"
              className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50
                placeholder:text-slate-400
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
              Vencimento
            </label>
            <input
              type="date"
              value={vencimento}
              onChange={(e) => setVencimento(e.target.value)}
              required
              className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50
                focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white
                transition-all duration-200"
            />
          </div>
          <div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-text-muted mb-1.5">
                  Parcela Atual
                </label>
                <input
                  type="number"
                  value={parcelaAtual}
                  onChange={(e) => {
                    setParcelaAtual(e.target.value);
                    setParcelaError("");
                  }}
                  min="1"
                  placeholder="Ex: 5"
                  className={`w-full border rounded-xl px-4 py-3 text-text bg-slate-50/50
                    placeholder:text-slate-400
                    focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white
                    transition-all duration-200
                    ${parcelaError ? "border-danger" : "border-border"}`}
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-text-muted mb-1.5">
                  Total Parcelas
                </label>
                <input
                  type="number"
                  value={parcelaTotal}
                  onChange={(e) => {
                    setParcelaTotal(e.target.value);
                    setParcelaError("");
                  }}
                  min="1"
                  placeholder="Ex: 11"
                  className={`w-full border rounded-xl px-4 py-3 text-text bg-slate-50/50
                    placeholder:text-slate-400
                    focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white
                    transition-all duration-200
                    ${parcelaError ? "border-danger" : "border-border"}`}
                />
              </div>
            </div>
            {parcelaError && (
              <p className="text-danger text-sm mt-1.5 font-medium">{parcelaError}</p>
            )}
          </div>
          <div className="flex items-center gap-2.5">
            <input
              type="checkbox"
              id="recorrente"
              checked={recorrente}
              onChange={(e) => setRecorrente(e.target.checked)}
              disabled={hasParcelas}
              className="h-4 w-4 accent-primary rounded"
            />
            <label
              htmlFor="recorrente"
              className={`text-sm font-medium ${hasParcelas ? "text-slate-400" : "text-text-muted"}`}
            >
              Recorrente (repete todo mês)
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
