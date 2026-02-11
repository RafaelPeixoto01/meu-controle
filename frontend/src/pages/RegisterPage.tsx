import { useState } from "react";
import { Link, useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function RegisterPage() {
  const { register, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("As senhas nao coincidem");
      return;
    }

    setLoading(true);
    try {
      await register({ nome, email, password });
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar conta");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] flex">
      {/* Branding Panel — Desktop Only */}
      <div className="hidden lg:flex lg:w-[480px] xl:w-[520px] relative overflow-hidden flex-col justify-center items-center p-12 shrink-0">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600 via-blue-500 to-violet-500" />
        <div className="absolute -top-24 -right-24 w-96 h-96 rounded-full bg-violet-400/20 blur-[100px]" />
        <div className="absolute -bottom-32 -left-24 w-96 h-96 rounded-full bg-sky-300/20 blur-[100px]" />
        <div className="absolute top-1/2 left-1/3 w-72 h-72 rounded-full bg-blue-300/10 blur-[80px]" />
        <div className="absolute top-16 right-16 w-24 h-24 rounded-full border-2 border-white/15 animate-float" />
        <div className="absolute bottom-20 left-10 w-16 h-16 rounded-full bg-white/10 animate-float-reverse" />
        <div className="absolute top-1/3 left-16 w-12 h-12 rounded-2xl bg-white/10 rotate-12 animate-float-slow" />
        <div className="absolute bottom-1/3 right-20 w-20 h-12 rounded-xl bg-white/[0.08] -rotate-6 animate-float-reverse" />

        <div className="relative z-10 text-center text-white">
          <svg className="w-16 h-16 mx-auto mb-6 drop-shadow-lg" viewBox="0 0 48 48" fill="none">
            <rect x="6" y="16" width="36" height="24" rx="3" stroke="white" strokeWidth="2" />
            <path d="M6 24h36" stroke="white" strokeWidth="1.5" opacity="0.4" />
            <circle cx="34" cy="30" r="3" fill="white" opacity="0.7" />
            <path d="M14 16V12a4 4 0 0 1 4-4h12a4 4 0 0 1 4 4v4" stroke="white" strokeWidth="2" opacity="0.7" strokeLinecap="round" />
          </svg>
          <h1 className="text-4xl font-extrabold tracking-tight mb-3 drop-shadow-sm">
            Meu Controle
          </h1>
          <p className="text-lg text-white/75 font-medium max-w-xs mx-auto leading-relaxed">
            Comece a organizar suas finanças agora
          </p>
        </div>
      </div>

      {/* Form Panel */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-8">
        <div className="w-full max-w-[420px]">
          {/* Mobile Branding */}
          <div className="lg:hidden text-center mb-8 animate-fade-in-up">
            <svg className="w-12 h-12 mx-auto mb-3 text-primary" viewBox="0 0 48 48" fill="none">
              <rect x="6" y="16" width="36" height="24" rx="3" stroke="currentColor" strokeWidth="2" />
              <path d="M6 24h36" stroke="currentColor" strokeWidth="1.5" opacity="0.3" />
              <circle cx="34" cy="30" r="3" fill="currentColor" opacity="0.5" />
              <path d="M14 16V12a4 4 0 0 1 4-4h12a4 4 0 0 1 4 4v4" stroke="currentColor" strokeWidth="2" opacity="0.5" strokeLinecap="round" />
            </svg>
            <h1 className="text-2xl font-extrabold text-text tracking-tight">Meu Controle</h1>
            <p className="text-text-muted text-sm mt-1 font-medium">Crie sua conta gratuita</p>
          </div>

          {/* Form Card */}
          <div
            className="bg-surface rounded-2xl shadow-xl shadow-black/[0.04] border border-slate-100/80 p-8 sm:p-10 animate-fade-in-up"
            style={{ animationDelay: "0.1s" }}
          >
            <h2 className="text-2xl font-bold text-text text-center mb-6">Criar Conta</h2>

            {error && (
              <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-3 rounded-r-xl mb-5 text-sm font-medium">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-text-muted mb-1.5">Nome</label>
                <input
                  type="text"
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  required
                  className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all duration-200"
                  placeholder="Seu nome"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-text-muted mb-1.5">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all duration-200"
                  placeholder="seu@email.com"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-text-muted mb-1.5">Senha</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all duration-200"
                  placeholder="Minimo 6 caracteres"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-text-muted mb-1.5">Confirmar Senha</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  minLength={6}
                  className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all duration-200"
                  placeholder="Repita a senha"
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
                {loading ? "Criando conta..." : "Criar Conta"}
              </button>
            </form>

            <div className="mt-6 text-center text-sm text-text-muted">
              Já tem conta?{" "}
              <Link
                to="/login"
                className="text-primary hover:text-primary-hover font-semibold transition-colors hover:underline underline-offset-4 decoration-primary/30"
              >
                Entrar
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
