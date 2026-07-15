import { describe, it, expect } from "vitest";
import {
  getCurrentMonthRef,
  getMonthName,
  getMonthLabel,
  getPreviousMonth,
  getNextMonth,
} from "./date";

describe("getMonthName", () => {
  it("retorna os nomes corretos nas extremidades", () => {
    expect(getMonthName(1)).toBe("Janeiro");
    expect(getMonthName(12)).toBe("Dezembro");
  });

  it("retorna Marco sem acento (convencao do projeto)", () => {
    expect(getMonthName(3)).toBe("Marco");
  });
});

describe("getMonthLabel", () => {
  it("combina nome do mes e ano", () => {
    expect(getMonthLabel(2026, 7)).toBe("Julho 2026");
  });
});

describe("getPreviousMonth", () => {
  it("decrementa o mes dentro do mesmo ano", () => {
    expect(getPreviousMonth(2026, 7)).toEqual({ year: 2026, month: 6 });
  });

  it("vira o ano em janeiro", () => {
    expect(getPreviousMonth(2026, 1)).toEqual({ year: 2025, month: 12 });
  });
});

describe("getNextMonth", () => {
  it("incrementa o mes dentro do mesmo ano", () => {
    expect(getNextMonth(2026, 7)).toEqual({ year: 2026, month: 8 });
  });

  it("vira o ano em dezembro", () => {
    expect(getNextMonth(2026, 12)).toEqual({ year: 2027, month: 1 });
  });
});

describe("getCurrentMonthRef", () => {
  it("retorna ano e mes 1-indexado do momento atual", () => {
    const now = new Date();
    expect(getCurrentMonthRef()).toEqual({
      year: now.getFullYear(),
      month: now.getMonth() + 1,
    });
  });
});
