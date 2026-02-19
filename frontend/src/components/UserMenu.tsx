import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function UserMenu() {
  const { user, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  if (!user) return null;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 text-white/90 hover:text-white font-semibold
          px-3 py-1.5 rounded-lg hover:bg-white/10 transition-all duration-150"
      >
        {user.nome}
        <svg className={`w-3.5 h-3.5 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 mt-2 w-48 bg-surface rounded-xl shadow-xl shadow-black/10
            border border-slate-100/80 py-1.5 z-50 overflow-hidden">
            <Link
              to="/installments"
              className="flex items-center gap-2.5 px-4 py-2.5 text-text-muted hover:text-text
                hover:bg-primary-50 transition-colors duration-100 text-sm font-medium"
              onClick={() => setIsOpen(false)}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
              Parcelas
            </Link>
            <Link
              to="/profile"
              className="flex items-center gap-2.5 px-4 py-2.5 text-text-muted hover:text-text
                hover:bg-primary-50 transition-colors duration-100 text-sm font-medium"
              onClick={() => setIsOpen(false)}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              Perfil
            </Link>
            <div className="border-t border-slate-100 my-1" />
            <button
              onClick={() => { logout(); setIsOpen(false); }}
              className="flex items-center gap-2.5 w-full text-left px-4 py-2.5 text-text-muted hover:text-danger
                hover:bg-red-50 transition-colors duration-100 text-sm font-medium"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Sair
            </button>
          </div>
        </>
      )}
    </div>
  );
}
