import { describe, it, expect } from "vitest";
import {
  formatBRL,
  formatParcela,
  formatDateBR,
  formatDateBRWithYear,
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

describe("formatDateBRWithYear", () => {
  it("formata data ISO como DD/MM/AAAA", () => {
    expect(formatDateBRWithYear("2027-02-22")).toBe("22/02/2027");
  });

  it("nao desloca o dia por fuso horario (CR-051)", () => {
    // new Date("2027-02-22") seria 22/02 00:00 UTC = 21/02 21:00 em UTC-3
    expect(formatDateBRWithYear("2027-02-22")).not.toBe("21/02/2027");
    expect(formatDateBRWithYear("2026-01-01")).toBe("01/01/2026");
  });

  it("retorna string vazia para null", () => {
    expect(formatDateBRWithYear(null)).toBe("");
  });
});
