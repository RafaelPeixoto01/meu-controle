// CR-056: testes dos helpers puros do historico e do desfazer.
import { describe, it, expect } from "vitest";
import type { ImportHistoryItem, ImportUndoItem, ImportUndoResponse } from "../types";
import {
  BATCH_STATUS_LABEL,
  canResume,
  describeUndoResult,
  groupUndoItems,
  restoreDetail,
  summarizeHistoryItem,
  totalPages,
  undoChangesNothing,
  undoItemKind,
} from "./importHistory";

function makeItem(overrides: Partial<ImportHistoryItem> = {}): ImportHistoryItem {
  return {
    id: "b1",
    filename: "fatura.pdf",
    banco_detectado: "Nubank",
    tipo_documento: "fatura",
    status: "confirmado",
    erro_mensagem: null,
    created_at: "2026-09-01T10:00:00",
    confirmado_em: "2026-09-01T10:05:00",
    revertido_em: null,
    total_transacoes: 0,
    confirmadas: 0,
    descartadas: 0,
    duplicadas: 0,
    revertidas: 0,
    pode_desfazer: true,
    ...overrides,
  };
}

function makeUndoItem(overrides: Partial<ImportUndoItem> = {}): ImportUndoItem {
  return {
    entidade: "gasto_diario",
    efeito: "criado",
    acao: "remover",
    descricao: "Padaria Stella",
    valor: 23.5,
    data: "2026-07-28",
    parcela_atual: null,
    parcela_total: null,
    status_anterior: null,
    valor_anterior: null,
    ...overrides,
  };
}

const ZERO: ImportUndoResponse = {
  gastos_diarios_removidos: 0,
  planejados_removidos: 0,
  planejados_restaurados: 0,
  preservados: 0,
  ja_removidos: 0,
};

describe("BATCH_STATUS_LABEL", () => {
  it("rotula o status novo do CR-056", () => {
    expect(BATCH_STATUS_LABEL.revertido.label).toBe("Desfeito");
  });
});

describe("summarizeHistoryItem", () => {
  it("lista so os contadores nao zerados, no singular e no plural", () => {
    const item = makeItem({ total_transacoes: 5, confirmadas: 3, descartadas: 1, duplicadas: 1 });
    expect(summarizeHistoryItem(item)).toBe("3 lançadas · 1 descartada · 1 duplicada");
  });

  it("lote desfeito mostra as desfeitas", () => {
    const item = makeItem({ status: "revertido", total_transacoes: 2, revertidas: 2 });
    expect(summarizeHistoryItem(item)).toBe("2 desfeitas");
  });

  it("lote em revisao, sem decisao, mostra o total extraido", () => {
    const item = makeItem({ status: "pendente_revisao", total_transacoes: 42 });
    expect(summarizeHistoryItem(item)).toBe("42 transações");
  });

  it("lote sem transacoes (erro) fica vazio", () => {
    expect(summarizeHistoryItem(makeItem({ status: "erro" }))).toBe("");
  });
});

describe("canResume", () => {
  it("so lotes que ainda pedem acao", () => {
    expect(canResume(makeItem({ status: "pendente_revisao" }))).toBe(true);
    expect(canResume(makeItem({ status: "processando" }))).toBe(true);
    expect(canResume(makeItem({ status: "confirmado" }))).toBe(false);
    expect(canResume(makeItem({ status: "revertido" }))).toBe(false);
  });
});

describe("totalPages", () => {
  it("arredonda para cima e nunca e zero", () => {
    expect(totalPages(0, 10)).toBe(1);
    expect(totalPages(10, 10)).toBe(1);
    expect(totalPages(11, 10)).toBe(2);
  });
});

describe("groupUndoItems", () => {
  it("agrupa na ordem remover → restaurar → manter → ja removido, sem secoes vazias", () => {
    const secoes = groupUndoItems([
      makeUndoItem({ acao: "ja_removido" }),
      makeUndoItem({ acao: "remover" }),
      makeUndoItem({ acao: "preservar" }),
      makeUndoItem({ acao: "remover" }),
    ]);
    expect(secoes.map((s) => s.acao)).toEqual(["remover", "preservar", "ja_removido"]);
    expect(secoes[0].itens).toHaveLength(2);
  });

  it("previa vazia nao gera secoes", () => {
    expect(groupUndoItems([])).toEqual([]);
  });
});

describe("undoChangesNothing", () => {
  it("true quando so ha itens mantidos ou ja removidos", () => {
    expect(undoChangesNothing({ ...ZERO, preservados: 2, ja_removidos: 1 })).toBe(true);
  });

  it("false quando algo seria removido ou restaurado", () => {
    expect(undoChangesNothing({ ...ZERO, planejados_restaurados: 1 })).toBe(false);
    expect(undoChangesNothing({ ...ZERO, gastos_diarios_removidos: 1 })).toBe(false);
  });
});

describe("undoItemKind", () => {
  it("distingue gasto, parcela e planejado", () => {
    expect(undoItemKind(makeUndoItem())).toBe("Gasto diário");
    expect(
      undoItemKind(makeUndoItem({ entidade: "planejado", parcela_atual: 5, parcela_total: 10 }))
    ).toBe("Parcela 5 de 10");
    expect(undoItemKind(makeUndoItem({ entidade: "planejado" }))).toBe("Planejado");
  });
});

describe("restoreDetail", () => {
  it("descreve o estado para onde o planejado volta", () => {
    const item = makeUndoItem({
      entidade: "planejado", efeito: "conciliado", acao: "restaurar",
      status_anterior: "Pendente", valor_anterior: 200,
    });
    // Intl usa espaco nao separavel entre "R$" e o numero
    expect(restoreDetail(item)?.replace(/\s/g, " ")).toBe("volta para Pendente · R$ 200,00");
  });

  it("nulo fora da restauracao", () => {
    expect(restoreDetail(makeUndoItem())).toBeNull();
    // conciliado mantido nao volta para lugar nenhum
    expect(
      restoreDetail(makeUndoItem({ acao: "preservar", status_anterior: "Pendente" }))
    ).toBeNull();
  });
});

describe("describeUndoResult", () => {
  it("resume os contadores nao zerados", () => {
    expect(
      describeUndoResult({ ...ZERO, gastos_diarios_removidos: 1, planejados_removidos: 8, preservados: 1 })
    ).toBe(
      "Importação desfeita: 1 gasto diário removido · 8 planejados removidos · 1 lançamento mantido."
    );
  });

  it("sem nenhum efeito, so confirma o undo", () => {
    expect(describeUndoResult(ZERO)).toBe("Importação desfeita.");
  });
});
