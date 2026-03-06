import { useEffect, useState } from "react";
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
  totalPago: number;
  totalPendente: number;
  totalAtrasado: number;
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
  totalPago,
  totalPendente,
  totalAtrasado,
  year,
  month,
}: ExpenseTableProps) {
  const [showForm, setShowForm] = useState(false);
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null);
  const [deletingExpense, setDeletingExpense] = useState<Expense | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const allSelected = expenses.length > 0 && selectedIds.size === expenses.length;
  const someSelected = selectedIds.size > 0 && selectedIds.size < expenses.length;
  const selectedTotal = expenses
    .filter((e) => selectedIds.has(e.id))
    .reduce((sum, e) => sum + e.valor, 0);

  useEffect(() => {
    setSelectedIds(new Set());
  }, [year, month]);

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

  function handleDelete(deleteAllChecked: boolean = false) {
    if (!deletingExpense) return;
    deleteExpense.mutate({ id: deletingExpense.id, deleteAll: deleteAllChecked });
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

  function handleToggleSelect(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function handleSelectAll() {
    if (allSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(expenses.map((e) => e.id)));
    }
  }

  function handleClearSelection() {
    setSelectedIds(new Set());
  }

  return (
    <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 overflow-hidden">
      <div className="flex items-center justify-between px-3 py-3 sm:px-6 sm:py-4">
        <h3 className="text-base font-bold text-text uppercase tracking-wide">
          Despesas
        </h3>
        <button
          type="button"
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-primary text-white text-sm font-semibold rounded-xl
            hover:bg-primary-hover hover:shadow-md hover:shadow-primary/20 active:scale-[0.97]
            transition-all duration-150"
        >
          + Nova Despesa
        </button>
      </div>

      {selectedIds.size > 0 && (
        <div className="mx-3 sm:mx-6 mb-2 px-3 sm:px-4 py-2.5 bg-primary-50 border border-primary-light rounded-xl
          flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 animate-fade-in-up">
          <div className="flex items-center gap-2 sm:gap-4">
            <span className="text-sm font-semibold text-primary">
              {selectedIds.size} {selectedIds.size === 1 ? "item selecionado" : "itens selecionados"}
            </span>
            <span className="text-sm font-bold text-text tabular-nums">
              {formatBRL(selectedTotal)}
            </span>
          </div>
          <button
            type="button"
            onClick={handleClearSelection}
            className="px-3 py-1.5 text-xs font-semibold text-primary hover:bg-primary/10 rounded-lg
              transition-colors duration-100"
          >
            Limpar
          </button>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full min-w-[700px]">
          <thead>
            <tr className="bg-primary-50 border-y border-primary-light">
              <th className="w-10 px-3 py-3 text-center">
                <input
                  type="checkbox"
                  checked={allSelected}
                  ref={(el) => { if (el) el.indeterminate = someSelected; }}
                  onChange={handleSelectAll}
                  className="rounded text-primary border-border focus:ring-primary w-4 h-4 cursor-pointer"
                  aria-label="Selecionar todas as despesas"
                />
              </th>
              <th className="text-left px-3 py-3 sm:px-6 text-xs font-bold text-primary uppercase tracking-wide">
                Nome
              </th>
              <th className="text-right px-3 py-3 sm:px-6 text-xs font-bold text-primary uppercase tracking-wide">
                Valor
              </th>
              <th className="text-center px-3 py-3 sm:px-6 text-xs font-bold text-primary uppercase tracking-wide">
                Parcela
              </th>
              <th className="text-center px-3 py-3 sm:px-6 text-xs font-bold text-primary uppercase tracking-wide">
                Venc.
              </th>
              <th className="text-center px-3 py-3 sm:px-6 text-xs font-bold text-primary uppercase tracking-wide">
                Status
              </th>
              <th className="text-center px-3 py-3 sm:px-6 text-xs font-bold text-primary uppercase tracking-wide">
                Acoes
              </th>
            </tr>
          </thead>
          <tbody>
            {expenses.map((expense, index) => (
              <tr
                key={expense.id}
                className={`border-b border-slate-100 hover:bg-primary-50/50 transition-colors duration-100
                  ${selectedIds.has(expense.id) ? "bg-primary-50/70" : index % 2 === 1 ? "bg-slate-50/50" : ""}`}
              >
                <td className="px-3 py-3.5 text-center">
                  <input
                    type="checkbox"
                    checked={selectedIds.has(expense.id)}
                    onChange={() => handleToggleSelect(expense.id)}
                    className="rounded text-primary border-border focus:ring-primary w-4 h-4 cursor-pointer"
                    aria-label={`Selecionar ${expense.nome}`}
                  />
                </td>
                <td className="px-3 py-3.5 sm:px-6 font-medium text-text">
                  {expense.nome}
                </td>
                <td className="px-3 py-3.5 sm:px-6 text-right text-text-muted tabular-nums font-medium">
                  {formatBRL(expense.valor)}
                </td>
                <td className="px-3 py-3.5 sm:px-6 text-center text-text-muted text-sm">
                  {formatParcela(expense.parcela_atual, expense.parcela_total)}
                </td>
                <td className="px-3 py-3.5 sm:px-6 text-center text-text-muted text-sm tabular-nums">
                  {formatDateBR(expense.vencimento)}
                </td>
                <td className="px-3 py-3.5 sm:px-6 text-center">
                  <StatusBadge
                    status={expense.status}
                    onClick={() => handleStatusToggle(expense)}
                  />
                </td>
                <td className="px-3 py-3.5 sm:px-6 text-center">
                  <div className="flex justify-center gap-1">
                    <button
                      type="button"
                      onClick={() => setEditingExpense(expense)}
                      className="px-1.5 py-1 sm:px-2.5 text-primary hover:bg-primary/10 rounded-lg text-sm font-semibold
                        transition-colors duration-100"
                    >
                      Editar
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDuplicate(expense.id)}
                      className="px-1.5 py-1 sm:px-2.5 text-text-muted hover:bg-slate-100 hover:text-text rounded-lg text-sm font-semibold
                        transition-colors duration-100"
                    >
                      Duplicar
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeletingExpense(expense)}
                      className="px-1.5 py-1 sm:px-2.5 text-danger hover:bg-danger/10 rounded-lg text-sm font-semibold
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
                <td colSpan={7} className="px-6 py-14 text-center">
                  <p className="text-text-muted text-base font-medium">
                    Nenhuma despesa cadastrada
                  </p>
                  <p className="text-text-muted/60 text-sm mt-1">
                    Clique em "+ Nova Despesa" para adicionar
                  </p>
                </td>
              </tr>
            )}
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-slate-200 bg-pago-bg/50">
              <td />
              <td className="px-3 py-2.5 sm:px-6 text-sm font-semibold text-pago">
                Pago
              </td>
              <td className="px-3 py-2.5 sm:px-6 text-right text-sm font-semibold text-pago tabular-nums">
                {formatBRL(totalPago)}
              </td>
              <td colSpan={4} />
            </tr>
            <tr className="bg-pendente-bg/50">
              <td />
              <td className="px-3 py-2.5 sm:px-6 text-sm font-semibold text-pendente">
                Pendente
              </td>
              <td className="px-3 py-2.5 sm:px-6 text-right text-sm font-semibold text-pendente tabular-nums">
                {formatBRL(totalPendente)}
              </td>
              <td colSpan={4} />
            </tr>
            <tr className="bg-atrasado-bg/50">
              <td />
              <td className="px-3 py-2.5 sm:px-6 text-sm font-semibold text-atrasado">
                Atrasado
              </td>
              <td className="px-3 py-2.5 sm:px-6 text-right text-sm font-semibold text-atrasado tabular-nums">
                {formatBRL(totalAtrasado)}
              </td>
              <td colSpan={4} />
            </tr>
            <tr className="bg-slate-50 border-t-2 border-slate-200">
              <td />
              <td className="px-3 py-3.5 sm:px-6 font-bold text-text">
                Total Despesas
              </td>
              <td className="px-3 py-3.5 sm:px-6 text-right font-bold text-text tabular-nums">
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
        checkboxLabel={
          (deletingExpense?.parcela_total && deletingExpense.parcela_total > 1) || deletingExpense?.recorrente
            ? deletingExpense?.recorrente
              ? "Excluir simultaneamente todas as despesas recorrentes com este nome"
              : "Excluir simultaneamente todas as parcelas desta despesa"
            : undefined
        }
        onConfirm={handleDelete}
        onCancel={() => setDeletingExpense(null)}
      />
    </div>
  );
}
