import { useState } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { resetPassword } from "../services/authApi";

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token") || "";
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (newPassword !== confirmPassword) {
      setError("As senhas nao coincidem");
      return;
    }

    if (!token) {
      setError("Token de reset nao encontrado na URL");
      return;
    }

    setLoading(true);
    try {
      await resetPassword(token, newPassword);
      setSuccess(true);
      setTimeout(() => navigate("/login"), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao redefinir senha");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-6 sm:p-8">
      <div className="w-full max-w-[420px]">
        {/* Branding */}
        <div className="text-center mb-8 animate-fade-in-up">
          <svg className="w-12 h-12 mx-auto mb-3 text-primary" viewBox="0 0 48 48" fill="none">
            <rect x="6" y="16" width="36" height="24" rx="3" stroke="currentColor" strokeWidth="2" />
            <path d="M6 24h36" stroke="currentColor" strokeWidth="1.5" opacity="0.3" />
            <circle cx="34" cy="30" r="3" fill="currentColor" opacity="0.5" />
            <path d="M14 16V12a4 4 0 0 1 4-4h12a4 4 0 0 1 4 4v4" stroke="currentColor" strokeWidth="2" opacity="0.5" strokeLinecap="round" />
          </svg>
          <h1 className="text-2xl font-extrabold text-text tracking-tight">Meu Controle</h1>
        </div>

        {/* Form Card */}
        <div
          className="bg-surface rounded-2xl shadow-xl shadow-black/[0.04] border border-slate-100/80 p-8 sm:p-10 animate-fade-in-up"
          style={{ animationDelay: "0.1s" }}
        >
          <h2 className="text-2xl font-bold text-text text-center mb-6">Redefinir Senha</h2>

          {success ? (
            <div className="text-center">
              <div className="bg-green-50 border-l-4 border-green-500 text-green-700 p-4 rounded-r-xl mb-6 text-sm font-medium">
                Senha redefinida com sucesso! Redirecionando para login...
              </div>
              <Link
                to="/login"
                className="text-primary hover:text-primary-hover font-semibold transition-colors hover:underline underline-offset-4 decoration-primary/30"
              >
                Ir para login
              </Link>
            </div>
          ) : (
            <>
              {error && (
                <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-3 rounded-r-xl mb-5 text-sm font-medium">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="block text-sm font-semibold text-text-muted mb-1.5">Nova Senha</label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    minLength={6}
                    className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all duration-200"
                    placeholder="Minimo 6 caracteres"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-text-muted mb-1.5">Confirmar Nova Senha</label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    minLength={6}
                    className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all duration-200"
                    placeholder="Repita a nova senha"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-primary text-white py-3 rounded-xl hover:bg-primary-hover hover:shadow-lg hover:shadow-primary/25 active:scale-[0.98] disabled:opacity-50 disabled:hover:shadow-none font-bold tracking-wide transition-all duration-200 flex items-center justify-center gap-2"
                >
                  {loading && (
                    <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  )}
                  {loading ? "Redefinindo..." : "Redefinir Senha"}
                </button>
              </form>

              <div className="mt-6 text-center text-sm">
                <Link
                  to="/login"
                  className="text-primary hover:text-primary-hover font-semibold transition-colors hover:underline underline-offset-4 decoration-primary/30"
                >
                  Voltar para login
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
