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
      <h2 className="text-2xl font-bold mb-6">Meu Perfil</h2>

      {/* Secao Perfil */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">Informacoes Pessoais</h3>

        {profileError && (
          <div className="bg-red-50 text-red-600 p-3 rounded mb-4 text-sm">{profileError}</div>
        )}
        {profileSuccess && (
          <div className="bg-green-50 text-green-600 p-3 rounded mb-4 text-sm">{profileSuccess}</div>
        )}

        {editing ? (
          <form onSubmit={handleProfileSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nome</label>
              <input
                type="text"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                required
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={profileLoading}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 font-medium"
              >
                {profileLoading ? "Salvando..." : "Salvar"}
              </button>
              <button
                type="button"
                onClick={() => { setEditing(false); setNome(user.nome); setEmail(user.email); }}
                className="bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300 font-medium"
              >
                Cancelar
              </button>
            </div>
          </form>
        ) : (
          <div>
            <p className="mb-2"><span className="font-medium">Nome:</span> {user.nome}</p>
            <p className="mb-4"><span className="font-medium">Email:</span> {user.email}</p>
            <button
              onClick={() => setEditing(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 font-medium"
            >
              Editar
            </button>
          </div>
        )}
      </div>

      {/* Secao Trocar Senha (backend rejeita para usuarios Google-only via RN-018) */}
      <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Trocar Senha</h3>

          {passwordError && (
            <div className="bg-red-50 text-red-600 p-3 rounded mb-4 text-sm">{passwordError}</div>
          )}
          {passwordSuccess && (
            <div className="bg-green-50 text-green-600 p-3 rounded mb-4 text-sm">{passwordSuccess}</div>
          )}

          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Senha Atual</label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nova Senha</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={6}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Confirmar Nova Senha</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={6}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              type="submit"
              disabled={passwordLoading}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 font-medium"
            >
              {passwordLoading ? "Alterando..." : "Alterar Senha"}
            </button>
          </form>
        </div>
    </div>
  );
}
