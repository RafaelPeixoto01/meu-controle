// CR-047: testes dos helpers puros da revisao de importacao.
import { describe, it, expect } from "vitest";
import type { ImportBatch, ImportBatchSummary, ImportTransaction } from "../types";
import {
  buildConfirmPayload,
  buildInitialDecisions,
  describeInstallmentSeries,
  groupTransactions,
  monthsToFetchForMatches,
  nextStageForBatch,
  validateDecision,
  type ReviewDecision,
  // CR-053
  EMPTY_FILTER,
  applyBulkPatch,
  bulkIncludeTargetIds,
  bulkTargetIds,
  decisionValor,
  filterGroups,
  isFilterActive,
  matchesFilter,
  normalizeForSearch,
  isLearnedSuggestion, // CR-054
  learnedTitle, // CR-054
  sumTransactions,
  type ReviewGroupKey,
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
    origem_sugestao: null, // CR-054
    descricao_original: null, // CR-054
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
    erro_mensagem: null,
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
    // compra 15/07/2026, parcela 3/10: cria 8 parcelas, a ultima em abr/2027
    // (a parcela k e cobrada k-1 meses apos a compra)
    expect(describeInstallmentSeries(parcelaDecision())).toEqual({
      quantidade: 8,
      ultimoMes: "04/2027",
    });
  });

  it("rejeita total acima do teto do backend", () => {
    expect(validateDecision(parcelaDecision({ parcelaTotal: "200" }), CATEGORIAS)).toMatch(
      /120/
    );
  });

  it("retorna null para numeracao invalida", () => {
    expect(describeInstallmentSeries(parcelaDecision({ parcelaTotal: "1" }))).toBeNull();
  });
});

describe("nextStageForBatch (CR-052)", () => {
  function summary(status: ImportBatchSummary["status"]): ImportBatchSummary {
    return {
      id: "b1",
      filename: "fatura.pdf",
      banco_detectado: null,
      tipo_documento: null,
      status,
      erro_mensagem: null,
      created_at: "2026-08-22T10:00:00",
    };
  }

  it("mantem na tela de processamento enquanto a IA extrai", () => {
    expect(nextStageForBatch(summary("processando"))).toBe("processing");
  });

  it("abre a revisao quando a extracao termina", () => {
    expect(nextStageForBatch(summary("pendente_revisao"))).toBe("review");
  });

  it.each(["erro", "confirmado", "descartado"] as const)(
    "volta ao upload em estado terminal (%s)",
    (status) => {
      expect(nextStageForBatch(summary(status))).toBe("upload");
    }
  );

  it("sem lote, fica no upload", () => {
    expect(nextStageForBatch(null)).toBe("upload");
    expect(nextStageForBatch(undefined)).toBe("upload");
  });
});

// ========== CR-053: filtro, totais e edicao em massa ==========

describe("normalizeForSearch", () => {
  it.each([
    ["PADARIA", "padaria"],
    ["Alimentação", "alimentacao"],
    ["  UBER   *TRIP  ", "uber *trip"],
    ["Cartão de Crédito", "cartao de credito"],
    ["", ""],
  ])("normaliza %j em %j", (entrada, esperado) => {
    expect(normalizeForSearch(entrada)).toBe(esperado);
  });
});

describe("matchesFilter", () => {
  const tx = makeTx({ id: "tx-1", descricao: "PADARIA STELLA*SP" });
  const decision = (descricao: string): ReviewDecision =>
    buildInitialDecisions(makeBatch([makeTx({ id: "tx-1", descricao })]))["tx-1"];

  it("query vazia casa tudo", () => {
    expect(matchesFilter(tx, decision("qualquer"), "")).toBe(true);
    expect(matchesFilter(tx, decision("qualquer"), "   ")).toBe(true);
  });

  it("casa a descricao original da IA", () => {
    expect(matchesFilter(tx, decision("Padaria Stella"), "stella*sp")).toBe(true);
  });

  it("casa a descricao editada pelo usuario", () => {
    expect(matchesFilter(tx, decision("Padaria da esquina"), "esquina")).toBe(true);
  });

  it("e insensivel a acento e caixa", () => {
    const comAcento = makeTx({ id: "tx-1", descricao: "MERCADO ALIMENTAÇÃO" });
    expect(matchesFilter(comAcento, undefined, "alimentacao")).toBe(true);
    expect(matchesFilter(comAcento, undefined, "ALIMENTAÇÃO")).toBe(true);
  });

  it("nao casa o que nao existe em nenhuma das duas descricoes", () => {
    expect(matchesFilter(tx, decision("Padaria Stella"), "netshoes")).toBe(false);
  });

  it("funciona sem decisao (linha ainda nao inicializada)", () => {
    expect(matchesFilter(tx, undefined, "padaria")).toBe(true);
  });
});

describe("filterGroups", () => {
  const padaria = makeTx({ id: "t1", descricao: "PADARIA STELLA" });
  const uber = makeTx({ id: "t2", descricao: "UBER *TRIP" });
  const luz = makeTx({
    id: "t3",
    descricao: "ENEL LUZ",
    classificacao: "match_planejado",
    expense_id_sugerido: "e1",
  });
  const duplicada = makeTx({ id: "t4", descricao: "UBER *TRIP", status: "duplicada" });
  const batch = makeBatch([padaria, uber, luz, duplicada]);
  const groups = groupTransactions(batch);
  const decisions = buildInitialDecisions(batch);

  it("sem filtro, devolve todos os grupos intactos", () => {
    const out = filterGroups(groups, decisions, EMPTY_FILTER);
    expect(out.novos.map((t) => t.id)).toEqual(["t1", "t2"]);
    expect(out.matches.map((t) => t.id)).toEqual(["t3"]);
    expect(out.duplicadas.map((t) => t.id)).toEqual(["t4"]);
  });

  it("filtra por texto atravessando todos os grupos", () => {
    const out = filterGroups(groups, decisions, { query: "uber", grupos: [] });
    expect(out.novos.map((t) => t.id)).toEqual(["t2"]);
    expect(out.matches).toEqual([]);
    expect(out.duplicadas.map((t) => t.id)).toEqual(["t4"]);
  });

  it("filtra por grupo", () => {
    const out = filterGroups(groups, decisions, { query: "", grupos: ["matches"] });
    expect(out.matches.map((t) => t.id)).toEqual(["t3"]);
    expect(out.novos).toEqual([]);
    expect(out.duplicadas).toEqual([]);
  });

  it("combina texto e grupo", () => {
    const out = filterGroups(groups, decisions, { query: "uber", grupos: ["novos"] });
    expect(out.novos.map((t) => t.id)).toEqual(["t2"]);
    expect(out.duplicadas).toEqual([]);
  });

  it("nao muta nem os grupos nem as decisoes", () => {
    const antes = JSON.stringify({ groups, decisions });
    filterGroups(groups, decisions, { query: "uber", grupos: ["novos"] });
    expect(JSON.stringify({ groups, decisions })).toBe(antes);
  });
});

describe("isFilterActive", () => {
  it.each([
    [{ query: "", grupos: [] as ReviewGroupKey[] }, false],
    [{ query: "   ", grupos: [] as ReviewGroupKey[] }, false],
    [{ query: "uber", grupos: [] as ReviewGroupKey[] }, true],
    [{ query: "", grupos: ["novos"] as ReviewGroupKey[] }, true],
  ])("%j resulta em %s", (filtro, esperado) => {
    expect(isFilterActive(filtro)).toBe(esperado);
  });
});

describe("decisionValor", () => {
  const tx = makeTx({ id: "t1", valor: 23.5 });
  const comValor = (valor: string): ReviewDecision => ({
    ...buildInitialDecisions(makeBatch([tx]))["t1"],
    valor,
  });

  it.each([
    ["42.90", 42.9],
    ["", 23.5],
    ["abc", 23.5],
    ["0", 23.5],
    ["-5", 23.5],
  ])("valor %j resulta em %s", (valor, esperado) => {
    expect(decisionValor(tx, comValor(valor))).toBe(esperado);
  });

  it("sem decisao, usa o valor da IA", () => {
    expect(decisionValor(tx, undefined)).toBe(23.5);
  });
});

describe("sumTransactions", () => {
  const t1 = makeTx({ id: "t1", valor: 10.1 });
  const t2 = makeTx({ id: "t2", valor: 20.2 });
  const ignorada = makeTx({ id: "t3", valor: 99, classificacao: "ignorar" });
  const batch = makeBatch([t1, t2, ignorada]);
  const decisions = buildInitialDecisions(batch);

  it("soma todas quando onlyIncluded nao e pedido", () => {
    expect(sumTransactions(batch.transacoes, decisions)).toBe(129.3);
  });

  it("soma so as incluidas quando pedido (ignorada nasce desmarcada)", () => {
    expect(sumTransactions(batch.transacoes, decisions, { onlyIncluded: true })).toBe(30.3);
  });

  it("usa o valor editado", () => {
    const editado = { ...decisions, t1: { ...decisions.t1, valor: "100" } };
    expect(sumTransactions([t1, t2], editado)).toBe(120.2);
  });

  it("lista vazia soma zero", () => {
    expect(sumTransactions([], decisions)).toBe(0);
  });
});

describe("bulkTargetIds", () => {
  const t1 = makeTx({ id: "t1", descricao: "UBER A" });
  const t2 = makeTx({ id: "t2", descricao: "UBER B" });
  const ignorada = makeTx({ id: "t3", descricao: "UBER C", classificacao: "ignorar" });
  const batch = makeBatch([t1, t2, ignorada]);
  const groups = groupTransactions(batch);
  const decisions = buildInitialDecisions(batch);

  it("pega so as incluidas", () => {
    expect(bulkTargetIds(groups, decisions)).toEqual(["t1", "t2"]);
  });

  it("respeita o filtro aplicado antes", () => {
    const visiveis = filterGroups(groups, decisions, { query: "uber a", grupos: [] });
    expect(bulkTargetIds(visiveis, decisions)).toEqual(["t1"]);
  });

  it("linha resgatada pelo usuario entra no alvo", () => {
    const resgatada = { ...decisions, t3: { ...decisions.t3, incluida: true } };
    expect(bulkTargetIds(groups, resgatada)).toEqual(["t1", "t2", "t3"]);
  });

  it("nenhuma incluida devolve lista vazia", () => {
    const nenhuma = Object.fromEntries(
      Object.entries(decisions).map(([id, d]) => [id, { ...d, incluida: false }])
    );
    expect(bulkTargetIds(groups, nenhuma)).toEqual([]);
  });
});

describe("applyBulkPatch", () => {
  const t1 = makeTx({ id: "t1" });
  const t2 = makeTx({ id: "t2" });
  const t3 = makeTx({ id: "t3" });
  const base = buildInitialDecisions(makeBatch([t1, t2, t3]));

  it("aplica categoria e subcategoria juntas", () => {
    const out = applyBulkPatch(base, ["t1", "t2"], {
      categoria: "Lazer e Entretenimento",
      subcategoria: "Streaming",
    });
    expect(out.t1.categoria).toBe("Lazer e Entretenimento");
    expect(out.t1.subcategoria).toBe("Streaming");
    expect(out.t2.subcategoria).toBe("Streaming");
  });

  it("categoria sozinha zera a subcategoria (cascata)", () => {
    const out = applyBulkPatch(base, ["t1"], { categoria: "Lazer e Entretenimento" });
    expect(out.t1.categoria).toBe("Lazer e Entretenimento");
    expect(out.t1.subcategoria).toBe("");
  });

  it("subcategoria sozinha nao mexe na categoria", () => {
    const out = applyBulkPatch(base, ["t1"], { subcategoria: "Supermercado" });
    expect(out.t1.categoria).toBe("Alimentação");
    expect(out.t1.subcategoria).toBe("Supermercado");
  });

  it("aplica metodo de pagamento sem tocar na categoria", () => {
    const out = applyBulkPatch(base, ["t1"], { metodoPagamento: "Pix" });
    expect(out.t1.metodoPagamento).toBe("Pix");
    expect(out.t1.subcategoria).toBe("Padaria");
  });

  it("aplica acao criar_gasto_diario", () => {
    const comMatch = {
      ...base,
      t1: { ...base.t1, acao: "atualizar_planejado" as const, expenseId: "e1" },
    };
    const out = applyBulkPatch(comMatch, ["t1"], { acao: "criar_gasto_diario" });
    expect(out.t1.acao).toBe("criar_gasto_diario");
  });

  it("aplica incluida em lote nos dois sentidos", () => {
    const desmarcada = applyBulkPatch(base, ["t1"], { incluida: false });
    expect(desmarcada.t1.incluida).toBe(false);
    expect(applyBulkPatch(desmarcada, ["t1"], { incluida: true }).t1.incluida).toBe(true);
  });

  it("nao toca em ids fora da lista", () => {
    const out = applyBulkPatch(base, ["t1"], { metodoPagamento: "Pix" });
    expect(out.t2).toBe(base.t2);
    expect(out.t3).toBe(base.t3);
  });

  it("nao muta o objeto original", () => {
    const antes = JSON.stringify(base);
    applyBulkPatch(base, ["t1", "t2"], { categoria: "Lazer e Entretenimento" });
    expect(JSON.stringify(base)).toBe(antes);
  });

  it("patch vazio ou sem ids devolve o mesmo objeto", () => {
    expect(applyBulkPatch(base, [], { metodoPagamento: "Pix" })).toBe(base);
    expect(applyBulkPatch(base, ["t1"], {})).toBe(base);
    expect(applyBulkPatch(base, ["t1"], { categoria: undefined })).toBe(base);
  });

  it("id inexistente e ignorado sem quebrar", () => {
    const out = applyBulkPatch(base, ["nao-existe"], { metodoPagamento: "Pix" });
    expect(out["nao-existe"]).toBeUndefined();
  });
});

describe("bulkIncludeTargetIds (finding do code review)", () => {
  const nova = makeTx({ id: "t1", descricao: "PADARIA" });
  const ignorada = makeTx({ id: "t2", descricao: "SALARIO", classificacao: "ignorar" });
  const duplicada = makeTx({ id: "t3", descricao: "PADARIA", status: "duplicada" });
  const groups = groupTransactions(makeBatch([nova, ignorada, duplicada]));

  it("marcar em lote inclui ignoradas mas NAO duplicadas", () => {
    // Duplicada costuma vir com categoria/metodo completos: passaria na validacao
    // e seria regravada, dobrando o lancamento.
    expect(bulkIncludeTargetIds(groups)).toEqual(["t1", "t2"]);
  });

  it("resgate de duplicada continua linha a linha", () => {
    expect(bulkIncludeTargetIds(groups)).not.toContain("t3");
  });

  it("respeita o filtro aplicado antes", () => {
    const decisions = buildInitialDecisions(makeBatch([nova, ignorada, duplicada]));
    const visiveis = filterGroups(groups, decisions, { query: "salario", grupos: [] });
    expect(bulkIncludeTargetIds(visiveis)).toEqual(["t2"]);
  });
});

describe("applyBulkPatch: par categoria+subcategoria (finding do code review)", () => {
  // Categoria sozinha invalidaria um parcelado que era valido com as duas vazias.
  // A toolbar so monta o patch com o par completo; este teste fixa o contrato.
  const parcelado = makeTx({
    id: "p1", classificacao: "parcelamento", parcela_atual: 3, parcela_total: 10,
    categoria: null, subcategoria: null,
  });
  const base = buildInitialDecisions(makeBatch([parcelado]));

  it("parcelado sem categoria e valido antes do lote", () => {
    expect(validateDecision(base.p1, CATEGORIAS)).toBeNull();
  });

  it("par completo mantem o parcelado valido", () => {
    const out = applyBulkPatch(base, ["p1"], {
      categoria: "Alimentação",
      subcategoria: "Padaria",
    });
    expect(validateDecision(out.p1, CATEGORIAS)).toBeNull();
  });

  it("categoria sozinha invalidaria — por isso a toolbar exige o par", () => {
    const out = applyBulkPatch(base, ["p1"], { categoria: "Alimentação" });
    expect(validateDecision(out.p1, CATEGORIAS)).not.toBeNull();
  });
});

// ========== CR-054: memoria de categorizacao ==========

describe("isLearnedSuggestion", () => {
  it("marca a linha cuja sugestao veio de uma regra do usuario", () => {
    expect(isLearnedSuggestion(makeTx({ origem_sugestao: "aprendido" }))).toBe(true);
  });

  it("nao marca o palpite da IA", () => {
    expect(isLearnedSuggestion(makeTx({ origem_sugestao: null }))).toBe(false);
  });

  it("nao marca transacao anterior a memoria (campo ausente no historico)", () => {
    expect(isLearnedSuggestion({ origem_sugestao: null })).toBe(false);
  });

  it("valor desconhecido nao vira badge", () => {
    // O tipo literal impede isso em compilacao, mas o JSON vem da rede: se o
    // backend renomear o sentinela, o badge tem que sumir e nao virar `true`
    const inesperado = { origem_sugestao: "ia" } as unknown as ImportTransaction;
    expect(isLearnedSuggestion(inesperado)).toBe(false);
  });
});

describe("learnedTitle", () => {
  it("mostra o descritor do documento quando a regra renomeou a linha", () => {
    const title = learnedTitle(
      makeTx({ descricao: "Padaria Stella", descricao_original: "PG *PADARIA STELLA*SP 15/08" })
    );
    expect(title).toContain("No documento: PG *PADARIA STELLA*SP 15/08");
  });

  it("omite a linha extra quando o nome nao mudou", () => {
    const title = learnedTitle(
      makeTx({ descricao: "PADARIA STELLA", descricao_original: "PADARIA STELLA" })
    );
    expect(title).not.toContain("No documento");
  });

  it("omite a linha extra no historico sem descricao_original", () => {
    expect(learnedTitle(makeTx({ descricao_original: null }))).not.toContain("No documento");
  });
});

describe("matchesFilter com descricao renomeada (CR-054)", () => {
  it("acha a linha pelo texto do documento apos a regra renomea-la", () => {
    const tx = makeTx({
      descricao: "Padaria Stella",
      descricao_original: "PG *PADARIA STELLA*SP 15/08",
    });
    // o usuario esta lendo o PDF e busca pelo que ve la
    expect(matchesFilter(tx, undefined, "PADARIA STELLA*SP")).toBe(true);
  });

  it("continua achando pelo nome exibido", () => {
    const tx = makeTx({
      descricao: "Padaria Stella",
      descricao_original: "PG *PADARIA STELLA*SP 15/08",
    });
    expect(matchesFilter(tx, undefined, "stella")).toBe(true);
  });

  it("nao casa texto que nao esta em nenhum dos campos", () => {
    const tx = makeTx({ descricao: "Padaria Stella", descricao_original: "PG *PADARIA*SP" });
    expect(matchesFilter(tx, undefined, "posto")).toBe(false);
  });
});
