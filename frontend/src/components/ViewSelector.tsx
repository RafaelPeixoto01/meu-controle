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
    <div className="flex items-center justify-center gap-1 bg-slate-100 rounded-xl p-1">
      <button
        type="button"
        onClick={() => {
          if (activeView !== "planejados") navigate("/");
        }}
        className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all duration-150
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
        className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all duration-150
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
        className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all duration-150
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
