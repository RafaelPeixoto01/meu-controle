import { useState } from "react";
import type { Expense, ExpenseCreate, ExpenseStatus } from "../types";
import { formatBRL, formatParcela, formatDateBR } from "../utils/format";
import {
  useCreateExpense,
  useUpdateExpense,
  useDeleteExpense,
  useDuplicateExpense,
} from "../hooks/useExpenses";
import StatusBadge from "./StatusBadge";
import ExpenseFormModal from "./ExpenseFormModal";
import ConfirmDialog from "./ConfirmDialog";

interface ExpenseTableProps {
  expenses: Expense[];
  totalDespesas: number;
  year: number;
  month: number;
}

function getNextStatus(current: ExpenseStatus): ExpenseStatus {
  if (current === "Pago") return "Pendente";
  return "Pago";
}

export default function ExpenseTable({
  expenses,
  totalDespesas,
  year,
  month,
}: ExpenseTableProps) {
  const [showForm, setShowForm] = useState(false);
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null);
  const [deletingExpense, setDeletingExpense] = useState<Expense | null>(null);

  const createExpense = useCreateExpense(year, month);
  const updateExpense = useUpdateExpense();
  const deleteExpense = useDeleteExpense();
  const duplicateExpense = useDuplicateExpense();

  function handleCreate(data: ExpenseCreate) {
    createExpense.mutate(data);
  }

  function handleEdit(data: ExpenseCreate) {
    if (!editingExpense) return;
    updateExpense.mutate({ id: editingExpense.id, data });
    setEditingExpense(null);
  }

  function handleDelete() {
    if (!deletingExpense) return;
    deleteExpense.mutate(deletingExpense.id);
    setDeletingExpense(null);
  }

  function handleStatusToggle(expense: Expense) {
    const newStatus = getNextStatus(expense.status);
    updateExpense.mutate({
      id: expense.id,
      data: { status: newStatus },
    });
  }

  function handleDuplicate(expenseId: string) {
    duplicateExpense.mutate(expenseId);
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4">
        <h3 className="text-base font-bold text-gray-800 uppercase tracking-wide">
          Despesas
        </h3>
        <button
          type="button"
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-primary text-white text-sm font-medium rounded-lg
            hover:bg-primary-hover active:bg-blue-800
            transition-colors duration-150"
        >
          + Nova Despesa
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
                Parcela
              </th>
              <th className="text-center px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Venc.
              </th>
              <th className="text-center px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Status
              </th>
              <th className="text-center px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Acoes
              </th>
            </tr>
          </thead>
          <tbody>
            {expenses.map((expense, index) => (
              <tr
                key={expense.id}
                className={`border-b border-gray-100 hover:bg-blue-50/50 transition-colors duration-100
                  ${index % 2 === 1 ? "bg-gray-50/50" : ""}`}
              >
                <td className="px-5 py-3 font-medium text-gray-900">
                  {expense.nome}
                </td>
                <td className="px-5 py-3 text-right text-gray-700 tabular-nums">
                  {formatBRL(expense.valor)}
                </td>
                <td className="px-5 py-3 text-center text-gray-500 text-sm">
                  {formatParcela(expense.parcela_atual, expense.parcela_total)}
                </td>
                <td className="px-5 py-3 text-center text-gray-500 text-sm tabular-nums">
                  {formatDateBR(expense.vencimento)}
                </td>
                <td className="px-5 py-3 text-center">
                  <StatusBadge
                    status={expense.status}
                    onClick={() => handleStatusToggle(expense)}
                  />
                </td>
                <td className="px-5 py-3 text-center">
                  <div className="flex justify-center gap-1">
                    <button
                      type="button"
                      onClick={() => setEditingExpense(expense)}
                      className="px-2 py-1 text-primary hover:bg-primary/10 rounded text-sm font-medium
                        transition-colors duration-100"
                    >
                      Editar
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDuplicate(expense.id)}
                      className="px-2 py-1 text-gray-500 hover:bg-gray-100 hover:text-gray-700 rounded text-sm font-medium
                        transition-colors duration-100"
                    >
                      Duplicar
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeletingExpense(expense)}
                      className="px-2 py-1 text-danger hover:bg-danger/10 rounded text-sm font-medium
                        transition-colors duration-100"
                    >
                      Excluir
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {expenses.length === 0 && (
              <tr>
                <td colSpan={6} className="px-5 py-12 text-center">
                  <p className="text-gray-400 text-base">
                    Nenhuma despesa cadastrada
                  </p>
                  <p className="text-gray-400 text-sm mt-1">
                    Clique em "+ Nova Despesa" para adicionar
                  </p>
                </td>
              </tr>
            )}
          </tbody>
          <tfoot>
            <tr className="bg-gray-100 border-t-2 border-gray-200">
              <td className="px-5 py-3 font-bold text-gray-800">
                Total Despesas
              </td>
              <td className="px-5 py-3 text-right font-bold text-gray-800 tabular-nums">
                {formatBRL(totalDespesas)}
              </td>
              <td colSpan={4} />
            </tr>
          </tfoot>
        </table>
      </div>

      <ExpenseFormModal
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        onSubmit={handleCreate}
      />

      <ExpenseFormModal
        isOpen={editingExpense !== null}
        onClose={() => setEditingExpense(null)}
        onSubmit={handleEdit}
        initialData={editingExpense}
      />

      <ConfirmDialog
        isOpen={deletingExpense !== null}
        title="Excluir Despesa"
        message={`Tem certeza que deseja excluir "${deletingExpense?.nome}"?`}
        onConfirm={handleDelete}
        onCancel={() => setDeletingExpense(null)}
      />
    </div>
  );
}
