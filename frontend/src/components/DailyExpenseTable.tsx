import { useState } from "react";
import type {
  DailyExpense,
  DailyExpenseCreate,
  DailyExpenseDaySummary,
} from "../types";
import { formatBRL, formatDateFull } from "../utils/format";
import {
  useCreateDailyExpense,
  useUpdateDailyExpense,
  useDeleteDailyExpense,
} from "../hooks/useDailyExpenses";
import DailyExpenseFormModal from "./DailyExpenseFormModal";
import ConfirmDialog from "./ConfirmDialog";

interface DailyExpenseTableProps {
  dias: DailyExpenseDaySummary[];
  totalMes: number;
  year: number;
  month: number;
}

export default function DailyExpenseTable({
  dias,
  totalMes,
  year,
  month,
}: DailyExpenseTableProps) {
  const [showForm, setShowForm] = useState(false);
  const [editingExpense, setEditingExpense] = useState<DailyExpense | null>(
    null
  );
  const [deletingExpense, setDeletingExpense] = useState<DailyExpense | null>(
    null
  );

  const createDailyExpense = useCreateDailyExpense(year, month);
  const updateDailyExpense = useUpdateDailyExpense();
  const deleteDailyExpense = useDeleteDailyExpense();

  function handleCreate(data: DailyExpenseCreate) {
    createDailyExpense.mutate(data);
  }

  function handleEdit(data: DailyExpenseCreate) {
    if (!editingExpense) return;
    updateDailyExpense.mutate({ id: editingExpense.id, data });
    setEditingExpense(null);
  }

  function handleDelete() {
    if (!deletingExpense) return;
    deleteDailyExpense.mutate(deletingExpense.id);
    setDeletingExpense(null);
  }

  const isEmpty = dias.length === 0;

  return (
    <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 overflow-hidden">
      <div className="flex items-center justify-between px-6 py-4">
        <h3 className="text-base font-bold text-text uppercase tracking-wide">
          Gastos Diarios
        </h3>
        <button
          type="button"
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-primary text-white text-sm font-semibold rounded-xl
            hover:bg-primary-hover hover:shadow-md hover:shadow-primary/20 active:scale-[0.97]
            transition-all duration-150"
        >
          + Novo Gasto
        </button>
      </div>

      <div className="overflow-x-auto">
        {isEmpty ? (
          <div className="px-6 py-14 text-center">
            <p className="text-text-muted text-base font-medium">
              Nenhum gasto diario registrado
            </p>
            <p className="text-text-muted/60 text-sm mt-1">
              Clique em "+ Novo Gasto" para adicionar
            </p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="bg-primary-50 border-y border-primary-light">
                <th className="text-left px-6 py-3 text-xs font-bold text-primary uppercase tracking-wide">
                  Descricao
                </th>
                <th className="text-right px-6 py-3 text-xs font-bold text-primary uppercase tracking-wide">
                  Valor
                </th>
                <th className="text-center px-6 py-3 text-xs font-bold text-primary uppercase tracking-wide">
                  Subcategoria
                </th>
                <th className="text-center px-6 py-3 text-xs font-bold text-primary uppercase tracking-wide">
                  Pagamento
                </th>
                <th className="text-center px-6 py-3 text-xs font-bold text-primary uppercase tracking-wide">
                  Acoes
                </th>
              </tr>
            </thead>
            <tbody>
              {dias.map((dia) => (
                <DayGroup
                  key={dia.data}
                  dia={dia}
                  onEdit={setEditingExpense}
                  onDelete={setDeletingExpense}
                />
              ))}
            </tbody>
            <tfoot>
              <tr className="bg-slate-50 border-t-2 border-slate-200">
                <td className="px-6 py-3.5 font-bold text-text">
                  Total do Mes
                </td>
                <td className="px-6 py-3.5 text-right font-bold text-text tabular-nums">
                  {formatBRL(totalMes)}
                </td>
                <td colSpan={3} />
              </tr>
            </tfoot>
          </table>
        )}
      </div>

      <DailyExpenseFormModal
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        onSubmit={handleCreate}
      />

      <DailyExpenseFormModal
        isOpen={editingExpense !== null}
        onClose={() => setEditingExpense(null)}
        onSubmit={handleEdit}
        initialData={editingExpense}
      />

      <ConfirmDialog
        isOpen={deletingExpense !== null}
        title="Excluir Gasto"
        message={`Tem certeza que deseja excluir "${deletingExpense?.descricao}"?`}
        onConfirm={handleDelete}
        onCancel={() => setDeletingExpense(null)}
      />
    </div>
  );
}

interface DayGroupProps {
  dia: DailyExpenseDaySummary;
  onEdit: (expense: DailyExpense) => void;
  onDelete: (expense: DailyExpense) => void;
}

function DayGroup({ dia, onEdit, onDelete }: DayGroupProps) {
  return (
    <>
      <tr className="bg-slate-100/70 border-t border-slate-200">
        <td
          colSpan={4}
          className="px-6 py-2.5 text-sm font-bold text-text"
        >
          {formatDateFull(dia.data)}
        </td>
        <td className="px-6 py-2.5 text-right text-sm font-semibold text-text-muted tabular-nums">
          {formatBRL(dia.subtotal)}
        </td>
      </tr>
      {dia.gastos.map((gasto, index) => (
        <tr
          key={gasto.id}
          className={`border-b border-slate-100 hover:bg-primary-50/50 transition-colors duration-100
            ${index % 2 === 1 ? "bg-slate-50/50" : ""}`}
        >
          <td className="px-6 py-3.5 font-medium text-text">
            {gasto.descricao}
          </td>
          <td className="px-6 py-3.5 text-right text-text-muted tabular-nums font-medium">
            {formatBRL(gasto.valor)}
          </td>
          <td className="px-6 py-3.5 text-center">
            <span className="inline-block px-2.5 py-1 bg-primary-50 text-primary text-xs font-semibold rounded-lg">
              {gasto.subcategoria}
            </span>
          </td>
          <td className="px-6 py-3.5 text-center text-text-muted text-sm">
            {gasto.metodo_pagamento}
          </td>
          <td className="px-6 py-3.5 text-center">
            <div className="flex justify-center gap-1">
              <button
                type="button"
                onClick={() => onEdit(gasto)}
                className="px-2.5 py-1 text-primary hover:bg-primary/10 rounded-lg text-sm font-semibold
                  transition-colors duration-100"
              >
                Editar
              </button>
              <button
                type="button"
                onClick={() => onDelete(gasto)}
                className="px-2.5 py-1 text-danger hover:bg-danger/10 rounded-lg text-sm font-semibold
                  transition-colors duration-100"
              >
                Excluir
              </button>
            </div>
          </td>
        </tr>
      ))}
    </>
  );
}
