import { describe, it, expect } from "vitest";
import {
  MAX_INTEGRATION_TOKENS,
  canCreateToken,
  formatDateTimeBR,
  lastUsedLabel,
  maskedToken,
} from "./integrationTokens";

const SAO_PAULO = "America/Sao_Paulo";

describe("tokens de integracao do Lumi (CR-058)", () => {
  it("converte o UTC do backend para o fuso de quem ve (Railway roda em UTC)", () => {
    expect(formatDateTimeBR("2026-10-23T16:25:12.123456Z", SAO_PAULO)).toBe("23/10/2026 13:25");
    expect(formatDateTimeBR("2026-10-23T16:25:12+00:00", SAO_PAULO)).toBe("23/10/2026 13:25");
    expect(formatDateTimeBR("2026-01-02T02:00:00Z", SAO_PAULO)).toBe("01/01/2026 23:00");
  });

  it("ultimo uso ou nunca usado", () => {
    expect(lastUsedLabel(null)).toBe("nunca usado");
    expect(lastUsedLabel("2026-10-23T12:30:00Z", SAO_PAULO)).toBe("último uso em 23/10/2026 09:30");
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
