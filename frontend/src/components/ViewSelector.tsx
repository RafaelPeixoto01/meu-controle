import { useNavigate, useLocation } from "react-router-dom";

type ViewId = "dashboard" | "planejados" | "diarios" | "parcelas" | "score";

const VIEWS: { id: ViewId; label: string; path: string }[] = [
  { id: "dashboard", label: "Dashboard", path: "/dashboard" },
  { id: "planejados", label: "Gastos Planejados", path: "/" },
  { id: "diarios", label: "Gastos Diários", path: "/daily-expenses" },
  { id: "parcelas", label: "Parcelas", path: "/installments" },
  { id: "score", label: "Score", path: "/score" },
];

function getActiveView(pathname: string): ViewId {
  if (pathname === "/dashboard") return "dashboard";
  if (pathname === "/daily-expenses") return "diarios";
  if (pathname === "/installments") return "parcelas";
  if (pathname === "/score") return "score";
  return "planejados";
}

export default function ViewSelector() {
  const navigate = useNavigate();
  const location = useLocation();
  const activeView = getActiveView(location.pathname);

  return (
    <div className="flex items-center justify-start sm:justify-center gap-1 bg-slate-100 rounded-xl p-1 overflow-x-auto">
      {VIEWS.map((view) => (
        <button
          key={view.id}
          type="button"
          onClick={() => {
            if (activeView !== view.id) navigate(view.path);
          }}
          className={`px-3 py-2 sm:px-5 rounded-lg text-xs sm:text-sm font-semibold transition-all duration-150 whitespace-nowrap
            ${activeView === view.id
              ? "bg-surface text-primary shadow-sm"
              : "text-text-muted hover:text-text"
            }`}
        >
          {view.label}
        </button>
      ))}
    </div>
  );
}
