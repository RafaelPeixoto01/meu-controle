// CR-057 (F07): conferencia da soma extraida com o total do documento (RN-053).
import type { ImportBatchSummary } from "../types";

export type ReconciliationStatus = "confere" | "faltando" | "excedente";

export interface Reconciliation {
  status: ReconciliationStatus;
  extraido: number;
  documento: number;
  // Sempre positiva; o sentido esta no status
  diferenca: number;
}

/**
 * Compara os debitos extraidos com o total impresso no documento. Null quando
 * a conferencia nao existe (documento sem total, direcao ausente em alguma
 * transacao, ou lote anterior ao CR-057) — nesse caso a revisao nao mostra nada.
 *
 * Compara em centavos inteiros: os valores impressos sao exatos, entao
 * qualquer diferenca de um centavo e real, e somar em float poderia deixar
 * 0.30000000000000004 onde o documento diz 0,30.
 */
export function reconcile(
  batch: Pick<ImportBatchSummary, "total_debitos_documento" | "total_debitos_extraido">
): Reconciliation | null {
  const documento = batch.total_debitos_documento;
  const extraido = batch.total_debitos_extraido;
  if (documento === null || extraido === null) return null;

  const centavos = Math.round(documento * 100) - Math.round(extraido * 100);
  if (centavos === 0) return { status: "confere", extraido, documento, diferenca: 0 };
  return {
    status: centavos > 0 ? "faltando" : "excedente",
    extraido,
    documento,
    diferenca: Math.abs(centavos) / 100,
  };
}
