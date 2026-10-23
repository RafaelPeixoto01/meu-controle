import { useState } from "react";
import ConfirmDialog from "./ConfirmDialog";
import { useIntegrationTokens } from "../hooks/useIntegrationTokens";
import type { IntegrationToken } from "../types";
import {
  MAX_INTEGRATION_TOKENS,
  canCreateToken,
  formatDateTimeBR,
  lastUsedLabel,
  maskedToken,
} from "../utils/integrationTokens";

/**
 * CR-058 (RF-22): secao "Integracoes" do Perfil — gerar, listar e revogar os tokens
 * que o Lumi usa para lancar e consultar gastos. O token aparece uma vez so e
 * fica so na memoria da pagina (nunca no localStorage).
 */
export default function IntegrationTokens() {
  const { tokens, isLoading, isError, create, isCreating, revoke, isRevoking } =
    useIntegrationTokens();
  const [name, setName] = useState("Lumi");
  const [newToken, setNewToken] = useState<{ id: string; token: string } | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const [toRevoke, setToRevoke] = useState<IntegrationToken | null>(null);

  const canCreate = canCreateToken(tokens.length);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setCopied(false);
    try {
      const created = await create(name.trim() || "Lumi");
      setNewToken({ id: created.id, token: created.token });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao gerar o token");
    }
  }

  async function handleCopy() {
    if (!newToken) return;
    try {
      await navigator.clipboard.writeText(newToken.token);
      setCopied(true);
    } catch {
      setError("Não deu para copiar. Selecione o token e copie manualmente.");
    }
  }

  async function handleRevoke() {
    const target = toRevoke;
    if (!target) return;
    setToRevoke(null); // fecha o dialogo antes da chamada: um segundo clique nao manda outro DELETE
    setError("");
    if (newToken?.id === target.id) setNewToken(null); // nao deixar copiar um token revogado
    try {
      await revoke(target.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao revogar o token");
    }
  }

  return (
    <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 p-7 mt-6">
      <h3 className="text-base font-bold text-text uppercase tracking-wide mb-2">Integrações</h3>
      <p className="text-sm text-text-muted mb-5">
        O Lumi, seu companion de voz, usa um token para lançar e consultar seus gastos. Ele só
        acessa o necessário, e você pode revogar o acesso a qualquer momento.
      </p>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-3 rounded-r-xl mb-5 text-sm font-medium">
          {error}
        </div>
      )}

      {newToken && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-5" role="status">
          <p className="text-sm font-semibold text-amber-800 mb-2">
            Guarde agora: este token não aparece de novo.
          </p>
          <code className="block break-all text-sm bg-white border border-amber-200 rounded-lg p-2 mb-3 select-all">
            {newToken.token}
          </code>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleCopy}
              className="px-4 py-2 bg-primary text-white rounded-xl font-semibold text-sm
                hover:bg-primary-hover active:scale-[0.98] transition-all duration-150"
            >
              {copied ? "Copiado!" : "Copiar"}
            </button>
            <button
              type="button"
              onClick={() => {
                setNewToken(null);
                setCopied(false);
              }}
              className="px-4 py-2 text-text-muted border border-border rounded-xl font-semibold text-sm
                hover:bg-slate-50 active:scale-[0.98] transition-all duration-150"
            >
              Fechar
            </button>
          </div>
        </div>
      )}

      {isLoading ? (
        <p className="text-sm text-text-muted mb-5">Carregando…</p>
      ) : isError ? (
        <p className="text-sm text-red-700 mb-5">Não deu para carregar as integrações.</p>
      ) : tokens.length === 0 ? (
        <p className="text-sm text-text-muted mb-5">Nenhuma integração ativa.</p>
      ) : (
        <ul className="divide-y divide-slate-100 mb-5">
          {tokens.map((token) => (
            <li key={token.id} className="flex items-center justify-between gap-3 py-3">
              <div className="min-w-0">
                <p className="text-text font-medium">
                  {token.name} <span className="text-text-muted font-mono text-sm">{maskedToken(token.prefix)}</span>
                </p>
                <p className="text-xs text-text-muted">
                  criado em {formatDateTimeBR(token.created_at)} · {lastUsedLabel(token.last_used_at)}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setToRevoke(token)}
                disabled={isRevoking}
                className="px-3 py-1.5 text-red-700 border border-red-200 rounded-lg text-sm font-semibold
                  hover:bg-red-50 disabled:opacity-50 transition-all duration-150"
              >
                Revogar
              </button>
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={handleCreate} className="flex flex-col sm:flex-row gap-3">
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={40}
          aria-label="Nome do token"
          className="flex-1 border border-border rounded-xl px-4 py-2.5 text-text bg-slate-50/50
            focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white
            transition-all duration-200"
        />
        <button
          type="submit"
          disabled={!canCreate || isCreating}
          title={canCreate ? undefined : `Limite de ${MAX_INTEGRATION_TOKENS} tokens ativos`}
          className="px-5 py-2.5 bg-primary text-white rounded-xl font-semibold
            hover:bg-primary-hover hover:shadow-md hover:shadow-primary/20
            active:scale-[0.98] disabled:opacity-50 transition-all duration-150"
        >
          {isCreating ? "Gerando..." : "Gerar token para o Lumi"}
        </button>
      </form>
      {!canCreate && (
        <p className="text-xs text-text-muted mt-2">
          Limite de {MAX_INTEGRATION_TOKENS} tokens ativos: revogue um para gerar outro.
        </p>
      )}

      <ConfirmDialog
        isOpen={toRevoke !== null}
        title="Revogar token"
        confirmLabel="Revogar"
        message={`O token "${toRevoke?.name ?? ""}" deixa de funcionar na hora, e o Lumi perde o acesso até receber um token novo.`}
        onConfirm={() => void handleRevoke()}
        onCancel={() => setToRevoke(null)}
      />
    </div>
  );
}
