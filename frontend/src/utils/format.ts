const brlFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

/** Formata numero como moeda brasileira: R$ 1.234,56 */
export function formatBRL(value: number): string {
  return brlFormatter.format(value);
}

/** Formata parcela como "X de Y" ou string vazia se nao aplicavel */
export function formatParcela(
  atual: number | null,
  total: number | null
): string {
  if (atual === null || total === null) return "";
  return `${atual} de ${total}`;
}

/** Formata data ISO (YYYY-MM-DD) para DD/MM */
export function formatDateBR(isoDate: string | null): string {
  if (!isoDate) return "";
  const [, month, day] = isoDate.split("-");
  return `${day}/${month}`;
}
