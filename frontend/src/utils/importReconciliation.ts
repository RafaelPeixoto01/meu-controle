// CR-057 (F07): conferencia da soma extraida com o total do documento (RN-053).
import type { ImportBatchSummary, ImportTransaction } from "../types";
import { formatBRL } from "./format";
import { decisionValor, type ReviewDecision } from "./importReview";

export type ReconciliationStatus = "confere" | "faltando" | "excedente";

export interface Reconciliation {
  status: ReconciliationStatus;
  extraido: number;
  documento: number;
  // Sempre positiva; o sentido esta no status
  diferenca: number;
}

const centavos = (valor: number) => Math.round(valor * 100);

/**
 * Soma dos debitos listados na revisao, com o valor EFETIVO de cada linha — o
 * editado pelo usuario quando houver. O `total_debitos_extraido` do lote e
 * fixo (o que a IA leu); sem recalcular aqui, corrigir na revisao um valor mal
 * lido deixaria o aviso aceso, e aviso que nao apaga treina o usuario a
 * ignora-lo. Conta toda linha de debito, marcada ou nao: compara-se o
 * documento, nao o que sera gravado.
 *
 * Null se alguma linha nao tem direcao (conferencia indisponivel, como no
 * backend). Soma em centavos inteiros para nao acumular ruido de float.
 */
export function liveDebitTotal(
  transacoes: ImportTransaction[],
  decisions: Record<string, ReviewDecision>
): number | null {
  if (transacoes.length === 0 || transacoes.some((tx) => tx.natureza === null)) return null;
  let total = 0;
  for (const tx of transacoes) {
    if (tx.natureza === "debito") total += centavos(decisionValor(tx, decisions[tx.id]));
  }
  return total / 100;
}

/**
 * Compara os debitos listados com o total impresso no documento. Null quando
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

  const diff = centavos(documento) - centavos(extraido);
  if (diff === 0) return { status: "confere", extraido, documento, diferenca: 0 };
  return {
    status: diff > 0 ? "faltando" : "excedente",
    extraido,
    documento,
    diferenca: Math.abs(diff) / 100,
  };
}

export interface ReconciliationMessage {
  alerta: boolean;
  titulo: string;
  detalhe: string;
}

/** Texto do aviso — separado do componente para os ramos serem testados. */
export function reconciliationMessage(r: Reconciliation): ReconciliationMessage {
  const totais =
    `Débitos listados ${formatBRL(r.extraido)} · ` +
    `total de débitos do documento ${formatBRL(r.documento)}.`;
  if (r.status === "confere") {
    return { alerta: false, titulo: "Conferido com o documento", detalhe: totais };
  }
  if (r.status === "faltando") {
    return {
      alerta: true,
      titulo: `Faltam ${formatBRL(r.diferenca)} em relação ao documento`,
      detalhe: `${totais} Alguma transação pode não ter sido lida — confira o PDF antes de confirmar.`,
    };
  }
  return {
    alerta: true,
    titulo: `A soma listada passa do documento em ${formatBRL(r.diferenca)}`,
    detalhe:
      `${totais} Pode haver uma transação lida em dobro ou um crédito (estorno, ` +
      `pagamento recebido) lido como débito — as entradas aparecem marcadas como "entrada".`,
  };
}
