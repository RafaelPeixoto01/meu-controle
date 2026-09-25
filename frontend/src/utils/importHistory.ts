// CR-056 (F07): helpers puros do historico de importacoes e do desfazer.
import type {
  ImportBatchStatus,
  ImportHistoryItem,
  ImportUndoAcao,
  ImportUndoItem,
  ImportUndoPreview,
  ImportUndoResponse,
} from "../types";
import { formatBRL } from "./format";

export type StatusTone = "success" | "muted" | "danger" | "warning" | "info";

export const BATCH_STATUS_LABEL: Record<ImportBatchStatus, { label: string; tone: StatusTone }> = {
  processando: { label: "Processando", tone: "info" },
  pendente_revisao: { label: "Em revisão", tone: "warning" },
  confirmado: { label: "Confirmado", tone: "success" },
  descartado: { label: "Descartado", tone: "muted" },
  erro: { label: "Erro", tone: "danger" },
  revertido: { label: "Desfeito", tone: "muted" },
};

function plural(n: number, singular: string, pluralForm: string): string {
  return `${n} ${n === 1 ? singular : pluralForm}`;
}

/** "38 lançadas · 3 descartadas · 1 duplicada" — omite os contadores zerados. */
export function summarizeHistoryItem(item: ImportHistoryItem): string {
  const partes: string[] = [];
  // Lote ainda em revisao: nada foi decidido, entao o que informa e o total
  // extraido (as duplicadas ja vem marcadas desde a extracao)
  const emAberto = canResume(item);
  if (emAberto && item.total_transacoes) {
    partes.push(plural(item.total_transacoes, "transação", "transações"));
  }
  if (item.confirmadas) partes.push(plural(item.confirmadas, "lançada", "lançadas"));
  if (item.revertidas) partes.push(plural(item.revertidas, "desfeita", "desfeitas"));
  if (item.descartadas) partes.push(plural(item.descartadas, "descartada", "descartadas"));
  if (item.duplicadas) partes.push(plural(item.duplicadas, "duplicada", "duplicadas"));
  return partes.join(" · ");
}

/** Lote que ainda pede acao do usuario — reaproveita o fluxo de retomada. */
export function canResume(item: ImportHistoryItem): boolean {
  return item.status === "pendente_revisao" || item.status === "processando";
}

export function totalPages(total: number, pageSize: number): number {
  return Math.max(1, Math.ceil(total / pageSize));
}

// ========== Previa do desfazer ==========

export interface UndoSection {
  acao: ImportUndoAcao;
  titulo: string;
  descricao: string;
  itens: ImportUndoItem[];
}

const SECTION_COPY: Record<ImportUndoAcao, { titulo: string; descricao: string }> = {
  remover: {
    titulo: "Será removido",
    descricao: "Lançamentos criados por esta importação.",
  },
  restaurar: {
    titulo: "Será restaurado",
    descricao: "Planejados que a importação marcou como pagos voltam ao estado anterior.",
  },
  preservar: {
    titulo: "Será mantido",
    descricao: "Alterados depois da importação — o desfazer não mexe neles.",
  },
  ja_removido: {
    titulo: "Já removido",
    descricao: "Você já apagou estes lançamentos.",
  },
};

const SECTION_ORDER: ImportUndoAcao[] = ["remover", "restaurar", "preservar", "ja_removido"];

/** Agrupa a previa por acao, na ordem de leitura, sem secoes vazias. */
export function groupUndoItems(itens: ImportUndoItem[]): UndoSection[] {
  return SECTION_ORDER.map((acao) => ({
    acao,
    ...SECTION_COPY[acao],
    itens: itens.filter((i) => i.acao === acao),
  })).filter((s) => s.itens.length > 0);
}

/**
 * Aviso para quando o undo so mudaria o status do lote, ou null se ele remove
 * ou restaura algo. Distingue o lote que nunca gravou nada (tudo descartado no
 * confirm) do lote cujos lancamentos foram todos alterados ou apagados depois.
 */
export function undoEmptyMessage(preview: ImportUndoPreview): string | null {
  const mudaAlgo =
    preview.gastos_diarios_removidos > 0 ||
    preview.planejados_removidos > 0 ||
    preview.planejados_restaurados > 0;
  if (mudaAlgo) return null;
  if (preview.itens.length === 0) {
    return (
      "Esta importação não gravou nenhum lançamento (todas as transações foram " +
      "descartadas). O lote será apenas marcado como desfeito."
    );
  }
  return (
    "Nada a remover nem restaurar: todos os lançamentos foram alterados ou " +
    "apagados depois da importação. O lote será apenas marcado como desfeito."
  );
}

/** Rotulo do tipo do lancamento na previa: "Gasto diário", "Parcela 5 de 10", "Planejado". */
export function undoItemKind(item: ImportUndoItem): string {
  if (item.entidade === "gasto_diario") return "Gasto diário";
  if (item.parcela_atual !== null && item.parcela_total !== null) {
    return `Parcela ${item.parcela_atual} de ${item.parcela_total}`;
  }
  return "Planejado";
}

/** Linha extra da restauracao: "volta para Pendente · R$ 200,00". */
export function restoreDetail(item: ImportUndoItem): string | null {
  if (item.acao !== "restaurar" || !item.status_anterior) return null;
  const valor = item.valor_anterior !== null ? ` · ${formatBRL(item.valor_anterior)}` : "";
  return `volta para ${item.status_anterior}${valor}`;
}

/** Frase do resultado do undo, para o aviso exibido depois de executar. */
export function describeUndoResult(r: ImportUndoResponse): string {
  const partes: string[] = [];
  if (r.gastos_diarios_removidos) {
    partes.push(plural(r.gastos_diarios_removidos, "gasto diário removido", "gastos diários removidos"));
  }
  if (r.planejados_removidos) {
    partes.push(plural(r.planejados_removidos, "planejado removido", "planejados removidos"));
  }
  if (r.planejados_restaurados) {
    partes.push(plural(r.planejados_restaurados, "planejado restaurado", "planejados restaurados"));
  }
  if (r.preservados) {
    partes.push(plural(r.preservados, "lançamento mantido", "lançamentos mantidos"));
  }
  if (r.ja_removidos) {
    partes.push(plural(r.ja_removidos, "já removido", "já removidos"));
  }
  return partes.length
    ? `Importação desfeita: ${partes.join(" · ")}.`
    : "Importação desfeita.";
}
