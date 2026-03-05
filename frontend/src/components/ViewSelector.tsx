import { useNavigate, useLocation } from "react-router-dom";

export default function ViewSelector() {
  const navigate = useNavigate();
  const location = useLocation();
  const activeView =
    location.pathname === "/daily-expenses"
      ? "diarios"
      : location.pathname === "/installments"
        ? "parcelas"
        : "planejados";

  return (
    <div className="flex items-center justify-center gap-1 bg-slate-100 rounded-xl p-1 overflow-x-auto">
      <button
        type="button"
        onClick={() => {
          if (activeView !== "planejados") navigate("/");
        }}
        className={`px-3 py-2 sm:px-5 rounded-lg text-xs sm:text-sm font-semibold transition-all duration-150 whitespace-nowrap
          ${activeView === "planejados"
            ? "bg-surface text-primary shadow-sm"
            : "text-text-muted hover:text-text"
          }`}
      >
        Gastos Planejados
      </button>
      <button
        type="button"
        onClick={() => {
          if (activeView !== "diarios") navigate("/daily-expenses");
        }}
        className={`px-3 py-2 sm:px-5 rounded-lg text-xs sm:text-sm font-semibold transition-all duration-150 whitespace-nowrap
          ${activeView === "diarios"
            ? "bg-surface text-primary shadow-sm"
            : "text-text-muted hover:text-text"
          }`}
      >
        Gastos Diários
      </button>
      <button
        type="button"
        onClick={() => {
          if (activeView !== "parcelas") navigate("/installments");
        }}
        className={`px-3 py-2 sm:px-5 rounded-lg text-xs sm:text-sm font-semibold transition-all duration-150 whitespace-nowrap
          ${activeView === "parcelas"
            ? "bg-surface text-primary shadow-sm"
            : "text-text-muted hover:text-text"
          }`}
      >
        Parcelas
      </button>
    </div>
  );
}
