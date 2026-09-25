// CR-057: testes da conferencia de total (RN-053).
import { describe, it, expect } from "vitest";
import { reconcile } from "./importReconciliation";

function lote(documento: number | null, extraido: number | null) {
  return { total_debitos_documento: documento, total_debitos_extraido: extraido };
}

describe("reconcile", () => {
  it("confere quando os totais batem ao centavo", () => {
    expect(reconcile(lote(3412.9, 3412.9))).toEqual({
      status: "confere", extraido: 3412.9, documento: 3412.9, diferenca: 0,
    });
  });

  it("faltando quando o documento soma mais do que foi extraido", () => {
    const r = reconcile(lote(3412.9, 3389.4));
    expect(r?.status).toBe("faltando");
    expect(r?.diferenca).toBe(23.5);
  });

  it("excedente quando a extracao passa do documento", () => {
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
