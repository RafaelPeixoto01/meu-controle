// CR-057: testes da conferencia de total (RN-053).
import { describe, it, expect } from "vitest";
import type { ImportTransaction } from "../types";
import type { ReviewDecision } from "./importReview";
import { liveDebitTotal, reconcile, reconciliationMessage } from "./importReconciliation";

function lote(documento: number | null, extraido: number | null) {
  return { total_debitos_documento: documento, total_debitos_extraido: extraido };
}

function tx(id: string, valor: number, natureza: ImportTransaction["natureza"]): ImportTransaction {
  return {
    id, data: "2026-07-28", descricao: id, valor, classificacao: "gasto_diario",
    motivo_ignorar: null, natureza, expense_id_sugerido: null, categoria: null,
    subcategoria: null, metodo_pagamento: null, parcela_atual: null, parcela_total: null,
    origem_sugestao: null, descricao_original: null, status: "pendente",
  };
}

function decisao(valor: string, incluida = true): ReviewDecision {
  return {
    incluida, acao: "criar_gasto_diario", descricao: "", valor, data: "", categoria: "",
    subcategoria: "", metodoPagamento: "", expenseId: "", parcelaAtual: "", parcelaTotal: "",
  };
}

// Normaliza o espaco nao separavel que o Intl poe entre "R$" e o numero
const plain = (s: string) => s.replace(/\s/g, " ");

describe("reconcile", () => {
  it("confere quando os totais batem ao centavo", () => {
    expect(reconcile(lote(3412.9, 3412.9))).toEqual({
      status: "confere", extraido: 3412.9, documento: 3412.9, diferenca: 0,
    });
  });

  it("faltando quando o documento soma mais do que foi listado", () => {
    const r = reconcile(lote(3412.9, 3389.4));
    expect(r?.status).toBe("faltando");
    expect(r?.diferenca).toBe(23.5);
  });

  it("excedente quando a lista passa do documento", () => {
    const r = reconcile(lote(100, 150.25));
    expect(r?.status).toBe("excedente");
    expect(r?.diferenca).toBe(50.25);
  });

  it("um centavo de diferenca ja e divergencia", () => {
    expect(reconcile(lote(10.01, 10))?.status).toBe("faltando");
  });

  it("ruido de ponto flutuante nao vira divergencia", () => {
    expect(reconcile(lote(0.3, 0.1 + 0.2))?.status).toBe("confere");
  });

  it("indisponivel quando qualquer total e nulo", () => {
    expect(reconcile(lote(null, 10))).toBeNull();
    expect(reconcile(lote(10, null))).toBeNull();
    expect(reconcile(lote(null, null))).toBeNull();
  });
});

describe("liveDebitTotal", () => {
  it("soma so os debitos, marcados ou nao, com o valor da IA", () => {
    const txs = [tx("a", 23.5, "debito"), tx("b", 100, "debito"), tx("c", 2500, "credito")];
    const decisions = { a: decisao("23.50"), b: decisao("100", false), c: decisao("2500") };
    expect(liveDebitTotal(txs, decisions)).toBe(123.5);
  });

  it("usa o valor corrigido na revisao — o aviso apaga ao corrigir (code review #1)", () => {
    const txs = [tx("a", 25.3, "debito")]; // IA leu 25,30; o documento diz 23,50
    expect(reconcile(lote(23.5, liveDebitTotal(txs, { a: decisao("25.30") })))?.status).toBe("excedente");
    expect(reconcile(lote(23.5, liveDebitTotal(txs, { a: decisao("23.50") })))?.status).toBe("confere");
  });

  it("valor editado invalido cai no valor da IA (mesma regra do subtotal)", () => {
    expect(liveDebitTotal([tx("a", 10, "debito")], { a: decisao("abc") })).toBe(10);
  });

  it("sem direcao em alguma linha, ou lote vazio: indisponivel", () => {
    expect(liveDebitTotal([tx("a", 10, "debito"), tx("b", 5, null)], {})).toBeNull();
    expect(liveDebitTotal([], {})).toBeNull();
  });

  it("soma em centavos, sem ruido de float", () => {
    expect(liveDebitTotal([tx("a", 0.1, "debito"), tx("b", 0.2, "debito")], {})).toBe(0.3);
  });
});

describe("reconciliationMessage (code review #7)", () => {
  it("confere nao e alerta", () => {
    const msg = reconciliationMessage(reconcile(lote(10, 10))!);
    expect(msg.alerta).toBe(false);
    expect(msg.titulo).toBe("Conferido com o documento");
  });

  it("faltando aponta transacao nao lida", () => {
    const msg = reconciliationMessage(reconcile(lote(424.62, 379.62))!);
    expect(msg.alerta).toBe(true);
    expect(plain(msg.titulo)).toBe("Faltam R$ 45,00 em relação ao documento");
    expect(msg.detalhe).toMatch(/não ter sido lida/);
  });

  it("excedente aponta duplicidade ou credito lido como debito e diz como achar", () => {
    const msg = reconciliationMessage(reconcile(lote(100, 150))!);
    expect(msg.alerta).toBe(true);
    expect(plain(msg.titulo)).toBe("A soma listada passa do documento em R$ 50,00");
    expect(msg.detalhe).toMatch(/crédito .* lido como débito/);
    expect(msg.detalhe).toMatch(/"entrada"/);
  });
});
