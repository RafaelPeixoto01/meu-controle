// CR-047: testes dos helpers puros da revisao de importacao.
import { describe, it, expect } from "vitest";
import type { ImportBatch, ImportTransaction } from "../types";
import {
  buildConfirmPayload,
  buildInitialDecisions,
  describeInstallmentSeries,
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
    parcela_atual: null,
    parcela_total: null,
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
    parcelaAtual: "",
    parcelaTotal: "",
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
  it("inclui mes atual, anterior e meses de TODAS as transacoes (sem duplicar)", () => {
    const batch = makeBatch([
      makeTx({ id: "a", classificacao: "match_planejado", data: "2026-06-10", expense_id_sugerido: "e1" }),
      makeTx({ id: "b", classificacao: "match_planejado", data: "2026-06-20", expense_id_sugerido: "e2" }),
      // gasto_diario tambem entra: o usuario pode reclassificar a linha
      // para "Pagar gasto planejado" na revisao
      makeTx({ id: "c", classificacao: "gasto_diario", data: "2025-01-01" }),
    ]);
    const months = monthsToFetchForMatches(batch, new Date(2026, 7, 12)); // ago/2026
    expect(months).toContainEqual({ year: 2026, month: 8 });
    expect(months).toContainEqual({ year: 2026, month: 7 });
    expect(months).toContainEqual({ year: 2026, month: 6 }); // jun nao duplica
    expect(months).toContainEqual({ year: 2025, month: 1 });
    expect(months).toHaveLength(4);
  });
});

// ========== CR-049: compras parceladas ==========

function makeParcelamento(overrides: Partial<ImportTransaction> = {}): ImportTransaction {
  return makeTx({
    id: "p1",
    data: "2026-07-15",
    descricao: "Netshoes",
    valor: 149.9,
    classificacao: "parcelamento",
    categoria: "Compras Pessoais",
    subcategoria: "Roupas",
    parcela_atual: 3,
    parcela_total: 10,
    ...overrides,
  });
}

function parcelaDecision(overrides: Partial<ReviewDecision> = {}): ReviewDecision {
  return {
    incluida: true,
    acao: "criar_planejado_parcelado",
    descricao: "Netshoes",
    valor: "149.90",
    data: "2026-07-15",
    categoria: "",
    subcategoria: "",
    metodoPagamento: "",
    expenseId: "",
    parcelaAtual: "3",
    parcelaTotal: "10",
    ...overrides,
  };
}

describe("groupTransactions (parcelamentos)", () => {
  it("separa parcelamentos em grupo proprio", () => {
    const batch = makeBatch([
      makeTx({ id: "a" }),
      makeParcelamento(),
      makeParcelamento({ id: "p2", status: "duplicada" }),
    ]);
    const groups = groupTransactions(batch);
    expect(groups.parcelamentos.map((t) => t.id)).toEqual(["p1"]);
    expect(groups.novos.map((t) => t.id)).toEqual(["a"]);
    // duplicada continua tendo precedencia sobre a classificacao
    expect(groups.duplicadas.map((t) => t.id)).toEqual(["p2"]);
  });
});

describe("buildInitialDecisions (parcelamentos)", () => {
  it("parcelamento numerado nasce como serie de parcelas", () => {
    const decisions = buildInitialDecisions(makeBatch([makeParcelamento()]));
    expect(decisions.p1.acao).toBe("criar_planejado_parcelado");
    expect(decisions.p1.parcelaAtual).toBe("3");
    expect(decisions.p1.parcelaTotal).toBe("10");
    expect(decisions.p1.incluida).toBe(true);
  });

  it("parcelamento sem numeracao cai para gasto diario", () => {
    const batch = makeBatch([makeParcelamento({ parcela_atual: null, parcela_total: null })]);
    const decisions = buildInitialDecisions(batch);
    expect(decisions.p1.acao).toBe("criar_gasto_diario");
    expect(decisions.p1.parcelaAtual).toBe("");
  });
});

describe("validateDecision (parcelamentos)", () => {
  it("aceita serie valida sem exigir categoria nem metodo", () => {
    expect(validateDecision(parcelaDecision(), CATEGORIAS)).toBeNull();
  });

  it.each([
    ["parcelaTotal", { parcelaTotal: "1" }],
    ["sem numeracao", { parcelaAtual: "", parcelaTotal: "" }],
    ["nao inteiro", { parcelaAtual: "2.5" }],
  ])("rejeita numeracao invalida: %s", (_label, patch) => {
    expect(validateDecision(parcelaDecision(patch), CATEGORIAS)).toMatch(/numeração|Parcela/);
  });

  it("rejeita parcela atual maior que o total", () => {
    expect(validateDecision(parcelaDecision({ parcelaAtual: "11" }), CATEGORIAS)).toMatch(
      /entre 1 e o total/
    );
  });

  it("rejeita par categoria/subcategoria incoerente", () => {
    const decision = parcelaDecision({ categoria: "Alimentação", subcategoria: "Streaming" });
    expect(validateDecision(decision, CATEGORIAS)).toMatch(/não pertence/);
  });
});

describe("buildConfirmPayload (parcelamentos)", () => {
  it("envia numeracao e omite categoria quando o par esta incompleto", () => {
    const batch = makeBatch([makeParcelamento()]);
    const payload = buildConfirmPayload(batch, { p1: parcelaDecision() });
    expect(payload.transacoes).toEqual([
      {
        id: "p1",
        acao: "criar_planejado_parcelado",
        descricao: "Netshoes",
        valor: 149.9,
        data: "2026-07-15",
        parcela_atual: 3,
        parcela_total: 10,
      },
    ]);
  });

  it("inclui categoria quando o par esta completo", () => {
    const batch = makeBatch([makeParcelamento()]);
    const decision = parcelaDecision({ categoria: "Alimentação", subcategoria: "Padaria" });
    const payload = buildConfirmPayload(batch, { p1: decision });
    expect(payload.transacoes[0]).toMatchObject({
      categoria: "Alimentação",
      subcategoria: "Padaria",
    });
  });
});

describe("describeInstallmentSeries", () => {
  it("calcula quantas parcelas e ate quando", () => {
    expect(describeInstallmentSeries(parcelaDecision())).toEqual({
      quantidade: 8,
      ultimoMes: "02/2027",
    });
  });

  it("retorna null para numeracao invalida", () => {
    expect(describeInstallmentSeries(parcelaDecision({ parcelaTotal: "1" }))).toBeNull();
  });
});
