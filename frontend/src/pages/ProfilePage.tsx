import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { updateProfile, changePassword } from "../services/authApi";

export default function ProfilePage() {
  const { user, updateUser } = useAuth();
  const accessToken = localStorage.getItem("access_token") || "";

  const [editing, setEditing] = useState(false);
  const [nome, setNome] = useState(user?.nome || "");
  const [email, setEmail] = useState(user?.email || "");
  const [profileError, setProfileError] = useState("");
  const [profileSuccess, setProfileSuccess] = useState("");
  const [profileLoading, setProfileLoading] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState("");
  const [passwordLoading, setPasswordLoading] = useState(false);

  async function handleProfileSubmit(e: React.FormEvent) {
    e.preventDefault();
    setProfileError("");
    setProfileSuccess("");
    setProfileLoading(true);
    try {
      const updated = await updateProfile({ nome, email }, accessToken);
      updateUser(updated);
      setProfileSuccess("Perfil atualizado com sucesso");
      setEditing(false);
    } catch (err) {
      setProfileError(err instanceof Error ? err.message : "Erro ao atualizar perfil");
    } finally {
      setProfileLoading(false);
    }
  }

  async function handlePasswordSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPasswordError("");
    setPasswordSuccess("");

    if (newPassword !== confirmPassword) {
      setPasswordError("As senhas nao coincidem");
      return;
    }

    setPasswordLoading(true);
    try {
      await changePassword(currentPassword, newPassword, accessToken);
      setPasswordSuccess("Senha alterada com sucesso");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setPasswordError(err instanceof Error ? err.message : "Erro ao alterar senha");
    } finally {
      setPasswordLoading(false);
    }
  }

  if (!user) return null;

  return (
    <div className="max-w-lg mx-auto py-8 px-4">
      <h2 className="text-2xl font-bold text-text mb-6">Meu Perfil</h2>

      {/* Secao Perfil */}
      <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 p-7 mb-6">
        <h3 className="text-base font-bold text-text uppercase tracking-wide mb-5">
          Informacoes Pessoais
        </h3>

        {profileError && (
          <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-3 rounded-r-xl mb-5 text-sm font-medium">
            {profileError}
          </div>
        )}
        {profileSuccess && (
          <div className="bg-green-50 border-l-4 border-green-500 text-green-700 p-3 rounded-r-xl mb-5 text-sm font-medium">
            {profileSuccess}
          </div>
        )}

        {editing ? (
          <form onSubmit={handleProfileSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-text-muted mb-1.5">Nome</label>
              <input
                type="text"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                required
                className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50
                  placeholder:text-slate-400
                  focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white
                  transition-all duration-200"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-text-muted mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50
                  placeholder:text-slate-400
                  focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white
                  transition-all duration-200"
              />
            </div>
            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={profileLoading}
                className="px-6 py-2.5 bg-primary text-white rounded-xl font-semibold
                  hover:bg-primary-hover hover:shadow-md hover:shadow-primary/20
                  active:scale-[0.98] disabled:opacity-50
                  transition-all duration-150"
              >
                {profileLoading ? "Salvando..." : "Salvar"}
              </button>
              <button
                type="button"
                onClick={() => { setEditing(false); setNome(user.nome); setEmail(user.email); }}
                className="px-5 py-2.5 text-text-muted border border-border rounded-xl
                  hover:bg-slate-50 active:bg-slate-100 active:scale-[0.98]
                  transition-all duration-150 font-semibold"
              >
                Cancelar
              </button>
            </div>
          </form>
        ) : (
          <div>
            <div className="space-y-3 mb-5">
              <div className="flex items-baseline gap-2">
                <span className="text-sm font-semibold text-text-muted w-14">Nome:</span>
                <span className="text-text font-medium">{user.nome}</span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-sm font-semibold text-text-muted w-14">Email:</span>
                <span className="text-text font-medium">{user.email}</span>
              </div>
            </div>
            <button
              onClick={() => setEditing(true)}
              className="px-5 py-2.5 bg-primary text-white rounded-xl font-semibold
                hover:bg-primary-hover hover:shadow-md hover:shadow-primary/20
                active:scale-[0.98]
                transition-all duration-150"
            >
              Editar
            </button>
          </div>
        )}
      </div>

      {/* Secao Trocar Senha (backend rejeita para usuarios Google-only via RN-018) */}
      <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 p-7">
        <h3 className="text-base font-bold text-text uppercase tracking-wide mb-5">
          Trocar Senha
        </h3>

        {passwordError && (
          <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-3 rounded-r-xl mb-5 text-sm font-medium">
            {passwordError}
          </div>
        )}
        {passwordSuccess && (
          <div className="bg-green-50 border-l-4 border-green-500 text-green-700 p-3 rounded-r-xl mb-5 text-sm font-medium">
            {passwordSuccess}
          </div>
        )}

        <form onSubmit={handlePasswordSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-text-muted mb-1.5">Senha Atual</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
              className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50
                focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white
                transition-all duration-200"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-text-muted mb-1.5">Nova Senha</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={6}
              className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50
                focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white
                transition-all duration-200"
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
              className="w-full border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50
                focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white
                transition-all duration-200"
            />
          </div>
          <div className="pt-2">
            <button
              type="submit"
              disabled={passwordLoading}
              className="px-6 py-2.5 bg-primary text-white rounded-xl font-semibold
                hover:bg-primary-hover hover:shadow-md hover:shadow-primary/20
                active:scale-[0.98] disabled:opacity-50
                transition-all duration-150"
            >
              {passwordLoading ? "Alterando..." : "Alterar Senha"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
