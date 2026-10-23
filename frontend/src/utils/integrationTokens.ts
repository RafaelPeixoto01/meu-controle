/** CR-058: regras de exibicao dos tokens de integracao do Lumi no Perfil. */

/** Igual ao limite do backend (RN-054). */
export const MAX_INTEGRATION_TOKENS = 5;

/**
 * "23/10/2026 13:25" no fuso do navegador. O backend manda UTC com o fuso (+00:00), entao a hora
 * e a mesma no PC e no Railway (que roda em UTC). `timeZone` existe para os testes.
 */
export function formatDateTimeBR(isoDateTime: string, timeZone?: string): string {
  const parts = new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
    timeZone,
  }).formatToParts(new Date(isoDateTime));
  const get = (type: Intl.DateTimeFormatPartTypes) => parts.find((p) => p.type === type)?.value ?? "";
  return `${get("day")}/${get("month")}/${get("year")} ${get("hour")}:${get("minute")}`;
}

/** Ultimo uso do token na lista. */
export function lastUsedLabel(lastUsedAt: string | null, timeZone?: string): string {
  return lastUsedAt ? `último uso em ${formatDateTimeBR(lastUsedAt, timeZone)}` : "nunca usado";
}

/** Como o token aparece na lista: so o comeco, nunca ele inteiro. */
export function maskedToken(prefix: string): string {
  return `mc_${prefix}…`;
}

export function canCreateToken(activeCount: number): boolean {
  return activeCount < MAX_INTEGRATION_TOKENS;
}
