import { useState } from "react";
import type { Income, IncomeCreate } from "../types";
import { formatBRL, formatDateBR } from "../utils/format";
import {
  useCreateIncome,
  useUpdateIncome,
  useDeleteIncome,
} from "../hooks/useIncomes";
import IncomeFormModal from "./IncomeFormModal";
import ConfirmDialog from "./ConfirmDialog";

interface IncomeTableProps {
  incomes: Income[];
  totalReceitas: number;
  year: number;
  month: number;
}

export default function IncomeTable({
  incomes,
  totalReceitas,
  year,
  month,
}: IncomeTableProps) {
  const [showForm, setShowForm] = useState(false);
  const [editingIncome, setEditingIncome] = useState<Income | null>(null);
  const [deletingIncome, setDeletingIncome] = useState<Income | null>(null);

  const createIncome = useCreateIncome(year, month);
  const updateIncome = useUpdateIncome();
  const deleteIncome = useDeleteIncome();

  function handleCreate(data: IncomeCreate) {
    createIncome.mutate(data);
  }

  function handleEdit(data: IncomeCreate) {
    if (!editingIncome) return;
    updateIncome.mutate({ id: editingIncome.id, data });
    setEditingIncome(null);
  }

  function handleDelete() {
    if (!deletingIncome) return;
    deleteIncome.mutate(deletingIncome.id);
    setDeletingIncome(null);
  }

  return (
    <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 overflow-hidden">
      <div className="flex items-center justify-between px-6 py-4">
        <h3 className="text-base font-bold text-text uppercase tracking-wide">
          Receitas
        </h3>
        <button
          type="button"
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-primary text-white text-sm font-semibold rounded-xl
            hover:bg-primary-hover hover:shadow-md hover:shadow-primary/20 active:scale-[0.97]
            transition-all duration-150"
        >
          + Nova Receita
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-primary-50 border-y border-primary-light">
              <th className="text-left px-6 py-3 text-xs font-bold text-primary uppercase tracking-wide">
                Nome
              </th>
              <th className="text-right px-6 py-3 text-xs font-bold text-primary uppercase tracking-wide">
                Valor
              </th>
              <th className="text-center px-6 py-3 text-xs font-bold text-primary uppercase tracking-wide">
                Data
              </th>
              <th className="text-center px-6 py-3 text-xs font-bold text-primary uppercase tracking-wide">
                Acoes
              </th>
            </tr>
          </thead>
          <tbody>
            {incomes.map((income, index) => (
              <tr
                key={income.id}
                className={`border-b border-slate-100 hover:bg-primary-50/50 transition-colors duration-100
                  ${index % 2 === 1 ? "bg-slate-50/50" : ""}`}
              >
                <td className="px-6 py-3.5 font-medium text-text">
                  {income.nome}
                </td>
                <td className="px-6 py-3.5 text-right text-text-muted tabular-nums font-medium">
                  {formatBRL(income.valor)}
                </td>
                <td className="px-6 py-3.5 text-center text-text-muted text-sm tabular-nums">
                  {formatDateBR(income.data)}
                </td>
                <td className="px-6 py-3.5 text-center">
                  <div className="flex justify-center gap-1">
                    <button
                      type="button"
                      onClick={() => setEditingIncome(income)}
                      className="px-2.5 py-1 text-primary hover:bg-primary/10 rounded-lg text-sm font-semibold
                        transition-colors duration-100"
                    >
                      Editar
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeletingIncome(income)}
                      className="px-2.5 py-1 text-danger hover:bg-danger/10 rounded-lg text-sm font-semibold
                        transition-colors duration-100"
                    >
                      Excluir
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {incomes.length === 0 && (
              <tr>
                <td colSpan={4} className="px-6 py-14 text-center">
                  <p className="text-text-muted text-base font-medium">
                    Nenhuma receita cadastrada
                  </p>
                  <p className="text-text-muted/60 text-sm mt-1">
                    Clique em "+ Nova Receita" para adicionar
                  </p>
                </td>
              </tr>
            )}
          </tbody>
          <tfoot>
            <tr className="bg-slate-50 border-t-2 border-slate-200">
              <td className="px-6 py-3.5 font-bold text-text">
                Total Receitas
              </td>
              <td className="px-6 py-3.5 text-right font-bold text-text tabular-nums">
                {formatBRL(totalReceitas)}
              </td>
              <td colSpan={2} />
            </tr>
          </tfoot>
        </table>
      </div>

      <IncomeFormModal
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        onSubmit={handleCreate}
      />

      <IncomeFormModal
        isOpen={editingIncome !== null}
        onClose={() => setEditingIncome(null)}
        onSubmit={handleEdit}
        initialData={editingIncome}
      />

      <ConfirmDialog
        isOpen={deletingIncome !== null}
        title="Excluir Receita"
        message={`Tem certeza que deseja excluir "${deletingIncome?.nome}"?`}
        onConfirm={handleDelete}
        onCancel={() => setDeletingIncome(null)}
      />
    </div>
  );
}
