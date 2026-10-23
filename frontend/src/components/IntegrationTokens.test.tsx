import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import IntegrationTokens from "./IntegrationTokens";
import type { IntegrationToken } from "../types";

// CR-058: secao "Integracoes" do Perfil. Sem Testing Library: react-dom + act no jsdom.
(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const hook = {
  tokens: [] as IntegrationToken[],
  isLoading: false,
  isError: false,
  create: vi.fn(),
  isCreating: false,
  revoke: vi.fn(),
  isRevoking: false,
};

vi.mock("../hooks/useIntegrationTokens", () => ({ useIntegrationTokens: () => hook }));

function token(id: string, prefix = "Ab3dEf9h"): IntegrationToken {
  return { id, name: "Lumi", prefix, created_at: "2026-10-23T16:25:00Z", last_used_at: null };
}

let container: HTMLDivElement;
let root: Root;

async function render() {
  await act(async () => root.render(<IntegrationTokens />));
}

function button(name: string, scope: ParentNode = container): HTMLButtonElement {
  const found = Array.from(scope.querySelectorAll("button")).find((b) => b.textContent === name);
  if (!found) throw new Error(`botão "${name}" não encontrado`);
  return found;
}

async function click(element: HTMLElement) {
  await act(async () => element.dispatchEvent(new MouseEvent("click", { bubbles: true })));
}

beforeEach(() => {
  hook.tokens = [];
  hook.create.mockReset();
  hook.revoke.mockReset();
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(async () => {
  await act(async () => root.unmount());
  container.remove();
});

describe("IntegrationTokens (CR-058)", () => {
  it("sem tokens, diz que nao ha integracao ativa", async () => {
    await render();
    expect(container.textContent).toContain("Nenhuma integração ativa.");
  });

  it("mostra o token gerado uma vez so e o esconde ao fechar", async () => {
    hook.create.mockResolvedValue({ ...token("t1"), token: "mc_segredo-de-teste" });
    await render();

    await click(button("Gerar token para o Lumi"));

    expect(hook.create).toHaveBeenCalledWith("Lumi");
    expect(container.querySelector("code")?.textContent).toBe("mc_segredo-de-teste");
    expect(container.textContent).toContain("Guarde agora");
    await click(button("Fechar"));
    expect(container.querySelector("code")).toBeNull();
    expect(container.textContent).not.toContain("mc_segredo-de-teste");
  });

  it("lista so o comeco do token e revoga com uma confirmacao, uma vez so", async () => {
    hook.tokens = [token("t1")];
    hook.revoke.mockResolvedValue(undefined);
    await render();
    expect(container.textContent).toContain("mc_Ab3dEf9h…");
    expect(container.textContent).toContain("nunca usado");

    await click(button("Revogar"));
    const dialog = document.querySelector("[role=dialog]") as HTMLElement;
    expect(dialog.textContent).toContain("deixa de funcionar na hora");
    await click(button("Revogar", dialog));

    expect(hook.revoke).toHaveBeenCalledTimes(1);
    expect(hook.revoke).toHaveBeenCalledWith("t1");
    expect(document.querySelector("[role=dialog]")).toBeNull(); // fechado antes da resposta
  });

  it("revogar o token recem-gerado tira ele da tela", async () => {
    hook.create.mockResolvedValue({ ...token("t1"), token: "mc_segredo-de-teste" });
    hook.revoke.mockResolvedValue(undefined);
    await render();
    await click(button("Gerar token para o Lumi"));
    hook.tokens = [token("t1")];
    await render();

    await click(button("Revogar"));
    await click(button("Revogar", document.querySelector("[role=dialog]") as HTMLElement));

    expect(container.querySelector("code")).toBeNull();
  });

  it("com 5 tokens ativos, o botao de gerar fica desligado", async () => {
    hook.tokens = ["a", "b", "c", "d", "e"].map((id) => token(id));
    await render();
    expect(button("Gerar token para o Lumi").disabled).toBe(true);
    expect(container.textContent).toContain("Limite de 5 tokens ativos");
  });
});
