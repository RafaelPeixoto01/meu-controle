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
  const updateIncome = useUpdateIncome(year, month);
  const deleteIncome = useDeleteIncome(year, month);

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
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4">
        <h3 className="text-base font-bold text-gray-800 uppercase tracking-wide">
          Receitas
        </h3>
        <button
          type="button"
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-primary text-white text-sm font-medium rounded-lg
            hover:bg-primary-hover active:bg-blue-800
            transition-colors duration-150"
        >
          + Nova Receita
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-y border-gray-200">
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Nome
              </th>
              <th className="text-right px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Valor
              </th>
              <th className="text-center px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Data
              </th>
              <th className="text-center px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Acoes
              </th>
            </tr>
          </thead>
          <tbody>
            {incomes.map((income, index) => (
              <tr
                key={income.id}
                className={`border-b border-gray-100 hover:bg-blue-50/50 transition-colors duration-100
                  ${index % 2 === 1 ? "bg-gray-50/50" : ""}`}
              >
                <td className="px-5 py-3 font-medium text-gray-900">
                  {income.nome}
                </td>
                <td className="px-5 py-3 text-right text-gray-700 tabular-nums">
                  {formatBRL(income.valor)}
                </td>
                <td className="px-5 py-3 text-center text-gray-500 text-sm tabular-nums">
                  {formatDateBR(income.data)}
                </td>
                <td className="px-5 py-3 text-center">
                  <div className="flex justify-center gap-1">
                    <button
                      type="button"
                      onClick={() => setEditingIncome(income)}
                      className="px-2 py-1 text-primary hover:bg-primary/10 rounded text-sm font-medium
                        transition-colors duration-100"
                    >
                      Editar
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeletingIncome(income)}
                      className="px-2 py-1 text-danger hover:bg-danger/10 rounded text-sm font-medium
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
                <td colSpan={4} className="px-5 py-12 text-center">
                  <p className="text-gray-400 text-base">
                    Nenhuma receita cadastrada
                  </p>
                  <p className="text-gray-400 text-sm mt-1">
                    Clique em "+ Nova Receita" para adicionar
                  </p>
                </td>
              </tr>
            )}
          </tbody>
          <tfoot>
            <tr className="bg-gray-100 border-t-2 border-gray-200">
              <td className="px-5 py-3 font-bold text-gray-800">
                Total Receitas
              </td>
              <td className="px-5 py-3 text-right font-bold text-gray-800 tabular-nums">
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
