import { useState, useEffect } from "react";
import { Link, useNavigate, Navigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function LoginPage() {
  const { login, loginWithGoogle, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleClientId, setGoogleClientId] = useState("");

  // Fetch Google Client ID from backend (runtime, not build-time)
  useEffect(() => {
    fetch("/api/config")
      .then((r) => r.json())
      .then((data) => setGoogleClientId(data.google_client_id || ""))
      .catch(() => {});
  }, []);

  // CR-002: Google OAuth callback — captura code da URL
  useEffect(() => {
    const code = searchParams.get("code");
    if (code) {
      setLoading(true);
      loginWithGoogle(code)
        .then(() => navigate("/"))
        .catch((err) => setError(err instanceof Error ? err.message : "Erro no login com Google"))
        .finally(() => setLoading(false));
    }
  }, [searchParams, loginWithGoogle, navigate]);

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login({ email, password });
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao fazer login");
    } finally {
      setLoading(false);
    }
  }

  function handleGoogleLogin() {
    if (!googleClientId) {
      setError("Google OAuth nao configurado");
      return;
    }
    const redirectUri = `${window.location.origin}/login`;
    const scope = "openid email profile";
    const url = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${googleClientId}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code&scope=${encodeURIComponent(scope)}`;
    window.location.href = url;
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] flex">
      {/* Branding Panel — Desktop Only */}
      <div className="hidden lg:flex lg:w-[480px] xl:w-[520px] relative overflow-hidden flex-col justify-center items-center p-12 shrink-0">
        {/* Base gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600 via-blue-500 to-violet-500" />

        {/* Gradient mesh for depth */}
        <div className="absolute -top-24 -right-24 w-96 h-96 rounded-full bg-violet-400/20 blur-[100px]" />
        <div className="absolute -bottom-32 -left-24 w-96 h-96 rounded-full bg-sky-300/20 blur-[100px]" />
        <div className="absolute top-1/2 left-1/3 w-72 h-72 rounded-full bg-blue-300/10 blur-[80px]" />

        {/* Floating decorative shapes */}
        <div className="absolute top-16 right-16 w-24 h-24 rounded-full border-2 border-white/15 animate-float" />
        <div className="absolute bottom-20 left-10 w-16 h-16 rounded-full bg-white/10 animate-float-reverse" />
        <div className="absolute top-1/3 left-16 w-12 h-12 rounded-2xl bg-white/10 rotate-12 animate-float-slow" />
        <div className="absolute bottom-1/3 right-20 w-20 h-12 rounded-xl bg-white/[0.08] -rotate-6 animate-float-reverse" />
        <div className="absolute top-28 left-1/3 w-4 h-4 rounded-full bg-white/25 animate-pulse-soft" />
        <div
          className="absolute bottom-36 right-1/3 w-3 h-3 rounded-full bg-white/30 animate-pulse-soft"
          style={{ animationDelay: "1.5s" }}
        />

        {/* Content */}
        <div className="relative z-10 text-center text-white">
          <svg className="w-16 h-16 mx-auto mb-6 drop-shadow-lg" viewBox="0 0 48 48" fill="none">
            <rect x="6" y="16" width="36" height="24" rx="3" stroke="white" strokeWidth="2" />
            <path d="M6 24h36" stroke="white" strokeWidth="1.5" opacity="0.4" />
            <circle cx="34" cy="30" r="3" fill="white" opacity="0.7" />
            <path
              d="M14 16V12a4 4 0 0 1 4-4h12a4 4 0 0 1 4 4v4"
              stroke="white"
              strokeWidth="2"
              opacity="0.7"
              strokeLinecap="round"
            />
          </svg>
          <h1 className="text-4xl font-extrabold tracking-tight mb-3 drop-shadow-sm">
            Meu Controle
          </h1>
          <p className="text-lg text-white/75 font-medium max-w-xs mx-auto leading-relaxed">
            Suas finanças sob controle, de um jeito simples e visual
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
              <path
                d="M14 16V12a4 4 0 0 1 4-4h12a4 4 0 0 1 4 4v4"
                stroke="currentColor"
                strokeWidth="2"
                opacity="0.5"
                strokeLinecap="round"
              />
            </svg>
            <h1 className="text-2xl font-extrabold text-text tracking-tight">
              Meu Controle
            </h1>
            <p className="text-text-muted text-sm mt-1 font-medium">
              Suas finanças sob controle
            </p>
          </div>

          {/* Form Card */}
          <div
            className="bg-surface rounded-2xl shadow-xl shadow-black/[0.04] border border-slate-100/80 p-8 sm:p-10 animate-fade-in-up"
            style={{ animationDelay: "0.1s" }}
          >
            <h2 className="text-2xl font-bold text-text text-center mb-6">Entrar</h2>

            {error && (
              <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-3 rounded-r-xl mb-5 text-sm font-medium">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-text-muted mb-1.5">
                  Email
                </label>
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
                <label className="block text-sm font-semibold text-text-muted mb-1.5">
                  Senha
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all duration-200"
                  placeholder="••••••"
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
                {loading ? "Entrando..." : "Entrar"}
              </button>
            </form>

            {/* Divider */}
            <div className="flex items-center gap-4 my-6">
              <div className="flex-1 h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent" />
              <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">ou</span>
              <div className="flex-1 h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent" />
            </div>

            {/* Google OAuth */}
            <button
              onClick={handleGoogleLogin}
              className="w-full bg-white border-2 border-slate-200 text-text py-3 rounded-xl hover:border-slate-300 hover:bg-slate-50 hover:shadow-sm active:scale-[0.98] font-semibold transition-all duration-200 flex items-center justify-center gap-3"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  fill="#EA4335"
                />
              </svg>
              Entrar com Google
            </button>

            {/* Links */}
            <div className="mt-6 text-center space-y-2.5">
              <Link
                to="/forgot-password"
                className="text-sm text-primary hover:text-primary-hover font-semibold transition-colors inline-block hover:underline underline-offset-4 decoration-primary/30"
              >
                Esqueci minha senha
              </Link>
              <div className="text-sm text-text-muted">
                Não tem conta?{" "}
                <Link
                  to="/register"
                  className="text-primary hover:text-primary-hover font-semibold transition-colors hover:underline underline-offset-4 decoration-primary/30"
                >
                  Criar conta
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
