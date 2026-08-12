// CR-047: testes dos helpers puros da revisao de importacao.
import { describe, it, expect } from "vitest";
import type { ImportBatch, ImportTransaction } from "../types";
import {
  buildConfirmPayload,
  buildInitialDecisions,
  groupTransactions,
  monthsToFetchForMatches,
  validateDecision,
  type ReviewDecision,
} from "./importReview";

function makeTx(overrides: Partial<ImportTransaction>): ImportTransaction {
  return {
    id: "tx-1",
    data: "2026-07-28",
    descricao: "PADARIA STELLA",
    valor: 23.5,
    classificacao: "gasto_diario",
    motivo_ignorar: null,
    expense_id_sugerido: null,
    categoria: "Alimentação",
    subcategoria: "Padaria",
    metodo_pagamento: "Cartão de Crédito",
    status: "pendente",
    ...overrides,
  };
}

function makeBatch(transacoes: ImportTransaction[]): ImportBatch {
  return {
    id: "batch-1",
    filename: "fatura.pdf",
    banco_detectado: "Nubank",
    tipo_documento: "fatura",
    status: "pendente_revisao",
    created_at: "2026-08-12T10:00:00",
    transacoes,
  };
}

const CATEGORIAS = {
  "Alimentação": ["Padaria", "Supermercado"],
  "Lazer e Entretenimento": ["Streaming"],
};

describe("groupTransactions", () => {
  it("agrupa por classificacao, com duplicadas em grupo proprio", () => {
    const batch = makeBatch([
      makeTx({ id: "a", classificacao: "gasto_diario" }),
      makeTx({ id: "b", classificacao: "match_planejado", expense_id_sugerido: "e1" }),
      makeTx({ id: "c", classificacao: "ignorar", motivo_ignorar: "receita" }),
      makeTx({ id: "d", classificacao: "gasto_diario", status: "duplicada" }),
    ]);
    const groups = groupTransactions(batch);
    expect(groups.novos.map((t) => t.id)).toEqual(["a"]);
    expect(groups.matches.map((t) => t.id)).toEqual(["b"]);
    expect(groups.ignoradas.map((t) => t.id)).toEqual(["c"]);
    expect(groups.duplicadas.map((t) => t.id)).toEqual(["d"]);
  });
});

describe("buildInitialDecisions", () => {
  it("inclui pendentes por padrao; ignoradas e duplicadas nascem desmarcadas", () => {
    const batch = makeBatch([
      makeTx({ id: "a" }),
      makeTx({ id: "b", classificacao: "ignorar" }),
      makeTx({ id: "c", status: "duplicada" }),
    ]);
    const decisions = buildInitialDecisions(batch);
    expect(decisions["a"].incluida).toBe(true);
    expect(decisions["b"].incluida).toBe(false);
    expect(decisions["c"].incluida).toBe(false);
  });

  it("match com expense_id sugerido nasce como atualizar_planejado", () => {
    const batch = makeBatch([
      makeTx({ id: "m", classificacao: "match_planejado", expense_id_sugerido: "e1" }),
    ]);
    const decision = buildInitialDecisions(batch)["m"];
    expect(decision.acao).toBe("atualizar_planejado");
    expect(decision.expenseId).toBe("e1");
  });

  it("campos nulos viram string vazia para os inputs", () => {
    const batch = makeBatch([
      makeTx({ id: "n", categoria: null, subcategoria: null, metodo_pagamento: null }),
    ]);
    const decision = buildInitialDecisions(batch)["n"];
    expect(decision.categoria).toBe("");
    expect(decision.subcategoria).toBe("");
    expect(decision.metodoPagamento).toBe("");
  });
});

describe("validateDecision", () => {
  const base: ReviewDecision = {
    incluida: true,
    acao: "criar_gasto_diario",
    descricao: "Padaria",
    valor: "23.50",
    data: "2026-07-28",
    categoria: "Alimentação",
    subcategoria: "Padaria",
    metodoPagamento: "Pix",
    expenseId: "",
  };

  it("aceita decisao valida de gasto diario", () => {
    expect(validateDecision(base, CATEGORIAS)).toBeNull();
  });

  it.each([
    [{ valor: "" }, "Valor"],
    [{ valor: "0" }, "Valor"],
    [{ valor: "abc" }, "Valor"],
    [{ descricao: "  " }, "Descrição"],
    [{ data: "" }, "Data"],
    [{ categoria: "" }, "Categoria"],
    [{ subcategoria: "Streaming" }, "Subcategoria"],
    [{ metodoPagamento: "" }, "Método"],
  ])("rejeita %o", (patch, expectedPrefix) => {
    const error = validateDecision({ ...base, ...patch }, CATEGORIAS);
    expect(error).not.toBeNull();
    expect(error).toContain(expectedPrefix);
  });

  it("atualizar_planejado exige expense_id, mas nao categoria", () => {
    const match: ReviewDecision = {
      ...base,
      acao: "atualizar_planejado",
      categoria: "",
      subcategoria: "",
      expenseId: "",
    };
    expect(validateDecision(match, CATEGORIAS)).toContain("planejado");
    expect(validateDecision({ ...match, expenseId: "e1" }, CATEGORIAS)).toBeNull();
  });
});

describe("buildConfirmPayload", () => {
  it("monta payload so com as incluidas, no formato de cada acao", () => {
    const batch = makeBatch([
      makeTx({ id: "a" }),
      makeTx({ id: "b", classificacao: "match_planejado", expense_id_sugerido: "e1", valor: 187.32 }),
      makeTx({ id: "c", classificacao: "ignorar" }),
    ]);
    const decisions = buildInitialDecisions(batch);
    decisions["a"].descricao = "  Padaria da esquina  ";
    decisions["a"].metodoPagamento = "Pix";

    const payload = buildConfirmPayload(batch, decisions);
    expect(payload.transacoes).toHaveLength(2);

    const [gasto, match] = payload.transacoes;
    expect(gasto).toEqual({
      id: "a",
      acao: "criar_gasto_diario",
      descricao: "Padaria da esquina",
      valor: 23.5,
      data: "2026-07-28",
      categoria: "Alimentação",
      subcategoria: "Padaria",
      metodo_pagamento: "Pix",
    });
    expect(match).toEqual({
      id: "b",
      acao: "atualizar_planejado",
      expense_id: "e1",
      valor: 187.32,
    });
  });

  it("ignoradas resgatadas entram no payload", () => {
    const batch = makeBatch([makeTx({ id: "c", classificacao: "ignorar" })]);
    const decisions = buildInitialDecisions(batch);
    decisions["c"].incluida = true;
    const payload = buildConfirmPayload(batch, decisions);
    expect(payload.transacoes).toHaveLength(1);
    expect(payload.transacoes[0].acao).toBe("criar_gasto_diario");
  });
});

describe("monthsToFetchForMatches", () => {
  it("inclui mes atual, anterior e meses das transacoes match (sem duplicar)", () => {
    const batch = makeBatch([
      makeTx({ id: "a", classificacao: "match_planejado", data: "2026-06-10", expense_id_sugerido: "e1" }),
      makeTx({ id: "b", classificacao: "match_planejado", data: "2026-06-20", expense_id_sugerido: "e2" }),
      makeTx({ id: "c", classificacao: "gasto_diario", data: "2025-01-01" }),
    ]);
    const months = monthsToFetchForMatches(batch, new Date(2026, 7, 12)); // ago/2026
    expect(months).toContainEqual({ year: 2026, month: 8 });
    expect(months).toContainEqual({ year: 2026, month: 7 });
    expect(months).toContainEqual({ year: 2026, month: 6 });
    expect(months).toHaveLength(3); // jun nao duplica; mes de gasto_diario nao entra
  });
});
