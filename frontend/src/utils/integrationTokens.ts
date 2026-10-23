/** CR-058: regras de exibicao dos tokens de integracao do Lumi no Perfil. */

/** Igual ao limite do backend (RN-054). */
export const MAX_INTEGRATION_TOKENS = 5;

/** "23/10/2026 14:05" a partir do datetime do backend (sem fuso: hora local do servidor). */
export function formatDateTimeBR(isoDateTime: string): string {
  const [datePart, timePart = ""] = isoDateTime.split("T");
  const [year, month, day] = datePart.split("-");
  return `${day}/${month}/${year} ${timePart.slice(0, 5)}`.trim();
}

/** Ultimo uso do token na lista. */
export function lastUsedLabel(lastUsedAt: string | null): string {
  return lastUsedAt ? `último uso em ${formatDateTimeBR(lastUsedAt)}` : "nunca usado";
}

/** Como o token aparece na lista: so o comeco, nunca ele inteiro. */
export function maskedToken(prefix: string): string {
  return `mc_${prefix}…`;
}

export function canCreateToken(activeCount: number): boolean {
  return activeCount < MAX_INTEGRATION_TOKENS;
}
