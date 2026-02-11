import type { ExpenseStatus } from "../types";

interface StatusBadgeProps {
  status: ExpenseStatus;
  onClick: () => void;
}

const statusStyles: Record<ExpenseStatus, string> = {
  Pendente: "bg-pendente-bg text-pendente border border-pendente/30",
  Pago: "bg-pago-bg text-pago border border-pago/30",
  Atrasado: "bg-atrasado-bg text-atrasado border border-atrasado/30",
};

export default function StatusBadge({ status, onClick }: StatusBadgeProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-3.5 py-1 text-xs font-bold cursor-pointer
        transition-all duration-150 hover:shadow-md hover:scale-105
        active:scale-95 focus:outline-none focus:ring-2 focus:ring-primary/30
        ${statusStyles[status]}`}
    >
      {status}
    </button>
  );
}
