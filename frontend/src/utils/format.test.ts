import { describe, it, expect } from "vitest";
import {
  formatBRL,
  formatParcela,
  formatDateBR,
  formatDateFull,
} from "./format";

describe("formatBRL", () => {
  // Intl pt-BR separa "R$" do valor com espaco nao-quebravel (U+00A0)
  it("formata valor com centavos", () => {
    expect(formatBRL(1234.56)).toBe("R$ 1.234,56");
  });

  it("formata zero", () => {
    expect(formatBRL(0)).toBe("R$ 0,00");
  });

  it("formata valor negativo", () => {
    expect(formatBRL(-99.9)).toBe("-R$ 99,90");
  });
});

describe("formatParcela", () => {
  it("formata 'X de Y'", () => {
    expect(formatParcela(3, 10)).toBe("3 de 10");
  });

  it("retorna vazio quando atual e null", () => {
    expect(formatParcela(null, 10)).toBe("");
  });

  it("retorna vazio quando total e null", () => {
    expect(formatParcela(3, null)).toBe("");
  });
});

describe("formatDateBR", () => {
  it("converte ISO para DD/MM", () => {
    expect(formatDateBR("2026-01-05")).toBe("05/01");
  });

  it("retorna vazio para null", () => {
    expect(formatDateBR(null)).toBe("");
  });
});

describe("formatDateFull", () => {
  it("formata DD/MM com dia da semana capitalizado em pt-BR", () => {
    // 2026-01-05 e uma segunda-feira
    expect(formatDateFull("2026-01-05")).toBe("05/01 - Segunda-feira");
  });

  it("usa a data local (nao UTC) — sem deslocamento de um dia", () => {
    // Construida via new Date(y, m-1, d): imune ao fuso do runner
    expect(formatDateFull("2026-07-09")).toBe("09/07 - Quinta-feira");
  });
});
