import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { fetchMonthlySummary, deleteExpense } from "./api";

// Response minima compativel com o que request() consome
function makeResponse(status: number, body?: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () =>
      body === undefined
        ? Promise.reject(new Error("no body"))
        : Promise.resolve(body),
  } as Response;
}

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  fetchMock.mockReset();
  localStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("request — header de autenticacao (CR-002)", () => {
  it("envia Authorization Bearer quando ha token no localStorage", async () => {
    localStorage.setItem("access_token", "tok-123");
    fetchMock.mockResolvedValueOnce(makeResponse(200, { total: 1 }));

    await fetchMonthlySummary(2026, 7);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/months/2026/7",
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer tok-123" }),
      })
    );
  });

  it("nao envia Authorization sem token", async () => {
    fetchMock.mockResolvedValueOnce(makeResponse(200, { total: 1 }));

    await fetchMonthlySummary(2026, 7);

    const headers = fetchMock.mock.calls[0][1].headers as Record<string, string>;
    expect(headers.Authorization).toBeUndefined();
  });
});

describe("request — interceptor 401 (CR-002)", () => {
  it("faz refresh, persiste o novo token e refaz a request original", async () => {
    localStorage.setItem("access_token", "tok-velho");
    fetchMock
      .mockResolvedValueOnce(makeResponse(401)) // request original
      .mockResolvedValueOnce(makeResponse(200, { access_token: "tok-novo" })) // refresh
      .mockResolvedValueOnce(makeResponse(200, { total: 42 })); // retry

    const result = await fetchMonthlySummary(2026, 7);

    expect(result).toEqual({ total: 42 });
    expect(localStorage.getItem("access_token")).toBe("tok-novo");
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/auth/refresh",
      expect.objectContaining({ method: "POST" })
    );
    // Retry usa o token novo
    const retryHeaders = fetchMock.mock.calls[2][1].headers as Record<string, string>;
    expect(retryHeaders.Authorization).toBe("Bearer tok-novo");
  });

  it("com refresh falho: remove o token e lanca 'Sessão expirada'", async () => {
    localStorage.setItem("access_token", "tok-velho");
    fetchMock
      .mockResolvedValueOnce(makeResponse(401)) // request original
      .mockResolvedValueOnce(makeResponse(401)); // refresh nega

    await expect(fetchMonthlySummary(2026, 7)).rejects.toThrow(
      "Sessão expirada"
    );
    expect(localStorage.getItem("access_token")).toBeNull();
  });

  it("401 sem token nao tenta refresh — vira erro HTTP normal", async () => {
    fetchMock.mockResolvedValueOnce(makeResponse(401, { detail: "Não autenticado" }));

    await expect(fetchMonthlySummary(2026, 7)).rejects.toThrow("Não autenticado");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});

describe("request — tratamento de erros e respostas", () => {
  it("lanca o detail do backend em resposta nao-ok", async () => {
    fetchMock.mockResolvedValueOnce(
      makeResponse(400, { detail: "Valor inválido" })
    );

    await expect(fetchMonthlySummary(2026, 7)).rejects.toThrow("Valor inválido");
  });

  it("lanca 'HTTP <status>' quando o corpo de erro nao e JSON", async () => {
    fetchMock.mockResolvedValueOnce(makeResponse(500));

    await expect(fetchMonthlySummary(2026, 7)).rejects.toThrow("HTTP 500");
  });

  it("resolve undefined em 204 No Content", async () => {
    fetchMock.mockResolvedValueOnce(makeResponse(204));

    await expect(deleteExpense("exp-1")).resolves.toBeUndefined();
  });
});
