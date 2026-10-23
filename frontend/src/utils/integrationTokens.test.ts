import { describe, it, expect } from "vitest";
import {
  MAX_INTEGRATION_TOKENS,
  canCreateToken,
  formatDateTimeBR,
  lastUsedLabel,
  maskedToken,
} from "./integrationTokens";

describe("tokens de integracao do Lumi (CR-058)", () => {
  it("formata o datetime do backend sem passar por Date (sem deslocar o fuso)", () => {
    expect(formatDateTimeBR("2026-10-23T14:05:12.123456")).toBe("23/10/2026 14:05");
    expect(formatDateTimeBR("2026-01-02T00:00:00")).toBe("02/01/2026 00:00");
  });

  it("ultimo uso ou nunca usado", () => {
    expect(lastUsedLabel(null)).toBe("nunca usado");
    expect(lastUsedLabel("2026-10-23T09:30:00")).toBe("último uso em 23/10/2026 09:30");
  });

  it("a lista mostra so o comeco do token", () => {
    expect(maskedToken("Ab3dEf9h")).toBe("mc_Ab3dEf9h…");
  });

  it("limite de tokens ativos igual ao do backend", () => {
    expect(MAX_INTEGRATION_TOKENS).toBe(5);
    expect(canCreateToken(4)).toBe(true);
    expect(canCreateToken(5)).toBe(false);
  });
});
