// CR-047 (F07): helpers puros do estado de revisao de uma importacao.
// Mantidos fora dos componentes para permitir teste unitario (Vitest).
import type {
  ImportBatch,
  ImportConfirmDecision,
  ImportConfirmRequest,
  ImportTransaction,
} from "../types";

// Decisao editavel de uma transacao na tela de revisao.
// Campos numericos ficam como string para bind direto nos inputs.
export interface ReviewDecision {
  incluida: boolean;
  acao: "criar_gasto_diario" | "atualizar_planejado" | "criar_planejado_parcelado";
  descricao: string;
  valor: string;
  data: string;
  categoria: string;
  subcategoria: string;
  metodoPagamento: string;
  expenseId: string;
  parcelaAtual: string; // CR-049
  parcelaTotal: string; // CR-049
}

export interface ReviewGroups {
  novos: ImportTransaction[];
  matches: ImportTransaction[];
  parcelamentos: ImportTransaction[]; // CR-049
  ignoradas: ImportTransaction[];
  duplicadas: ImportTransaction[];
}

export function groupTransactions(batch: ImportBatch): ReviewGroups {
  const groups: ReviewGroups = {
    novos: [],
    matches: [],
    parcelamentos: [],
    ignoradas: [],
    duplicadas: [],
  };
  for (const tx of batch.transacoes) {
    if (tx.status === "duplicada") {
      groups.duplicadas.push(tx);
    } else if (tx.classificacao === "match_planejado") {
      groups.matches.push(tx);
    } else if (tx.classificacao === "parcelamento") {
      groups.parcelamentos.push(tx);
    } else if (tx.classificacao === "ignorar") {
      groups.ignoradas.push(tx);
    } else {
      groups.novos.push(tx);
    }
  }
  return groups;
}

// CR-049: quantas parcelas serao criadas e ate quando — usado na previa da
// revisao, para o usuario conferir antes de gravar uma serie inteira.
export function describeInstallmentSeries(
  decision: ReviewDecision
): { quantidade: number; ultimoMes: string } | null {
  const atual = Number(decision.parcelaAtual);
  const total = Number(decision.parcelaTotal);
  if (!Number.isInteger(atual) || !Number.isInteger(total)) return null;
  if (total <= 1 || atual < 1 || atual > total) return null;

  const [ano, mes] = decision.data.split("-").map(Number);
  if (!ano || !mes) return null;

  const quantidade = total - atual + 1;
  const ultimo = new Date(ano, mes - 1 + (quantidade - 1), 1);
  const ultimoMes = `${String(ultimo.getMonth() + 1).padStart(2, "0")}/${ultimo.getFullYear()}`;
  return { quantidade, ultimoMes };
}

export function buildInitialDecisions(batch: ImportBatch): Record<string, ReviewDecision> {
  const decisions: Record<string, ReviewDecision> = {};
  for (const tx of batch.transacoes) {
    const isMatch = tx.classificacao === "match_planejado" && !!tx.expense_id_sugerido;
    // CR-049: parcelamento so nasce como serie se a IA numerou a parcela
    const isParcelamento =
      tx.classificacao === "parcelamento" && !!tx.parcela_atual && !!tx.parcela_total;
    let acao: ReviewDecision["acao"] = "criar_gasto_diario";
    if (isMatch) acao = "atualizar_planejado";
    else if (isParcelamento) acao = "criar_planejado_parcelado";

    decisions[tx.id] = {
      // Ignoradas e duplicadas nascem desmarcadas (resgataveis na revisao)
      incluida: tx.status === "pendente" && tx.classificacao !== "ignorar",
      acao,
      descricao: tx.descricao,
      valor: String(tx.valor),
      data: tx.data,
      categoria: tx.categoria ?? "",
      subcategoria: tx.subcategoria ?? "",
      metodoPagamento: tx.metodo_pagamento ?? "",
      expenseId: tx.expense_id_sugerido ?? "",
      parcelaAtual: tx.parcela_atual ? String(tx.parcela_atual) : "",
      parcelaTotal: tx.parcela_total ? String(tx.parcela_total) : "",
    };
  }
  return decisions;
}

// Valida uma decisao incluida; retorna mensagem de erro ou null se ok.
export function validateDecision(
  decision: ReviewDecision,
  categorias: Record<string, string[]>
): string | null {
  const valor = Number(decision.valor);
  if (!decision.valor || Number.isNaN(valor) || valor <= 0) {
    return "Valor deve ser um número maior que zero";
  }
  if (decision.acao === "atualizar_planejado") {
    if (!decision.expenseId) return "Selecione o gasto planejado a conciliar";
    return null;
  }
  if (!decision.descricao.trim()) return "Descrição é obrigatória";
  if (!decision.data) return "Data é obrigatória";

  // CR-049: serie de parcelas — categoria e opcional em gastos planejados,
  // mas se informada tem que formar par valido; a numeracao e obrigatoria.
  if (decision.acao === "criar_planejado_parcelado") {
    const atual = Number(decision.parcelaAtual);
    const total = Number(decision.parcelaTotal);
    if (!Number.isInteger(atual) || !Number.isInteger(total) || total <= 1) {
      return "Informe a numeração da parcela (ex: 3 de 10)";
    }
    if (atual < 1 || atual > total) {
      return "Parcela atual deve estar entre 1 e o total";
    }
    if (decision.categoria || decision.subcategoria) {
      const subs = categorias[decision.categoria];
      if (!subs || !subs.includes(decision.subcategoria)) {
        return "Subcategoria não pertence à categoria selecionada";
      }
    }
    return null;
  }

  if (!decision.categoria || !decision.subcategoria) {
    return "Categoria e subcategoria são obrigatórias";
  }
  const subcategorias = categorias[decision.categoria];
  if (!subcategorias || !subcategorias.includes(decision.subcategoria)) {
    return "Subcategoria não pertence à categoria selecionada";
  }
  if (!decision.metodoPagamento) return "Método de pagamento é obrigatório";
  return null;
}

// Monta o payload do POST /imports/{id}/confirm.
// Transacoes nao incluidas sao omitidas: o backend descarta as pendentes e
// mantem as duplicadas como 'duplicada' (contrato do CR-046).
export function buildConfirmPayload(
  batch: ImportBatch,
  decisions: Record<string, ReviewDecision>
): ImportConfirmRequest {
  const transacoes: ImportConfirmDecision[] = [];
  for (const tx of batch.transacoes) {
    const decision = decisions[tx.id];
    if (!decision || !decision.incluida) continue;

    if (decision.acao === "atualizar_planejado") {
      transacoes.push({
        id: tx.id,
        acao: "atualizar_planejado",
        expense_id: decision.expenseId,
        valor: Number(decision.valor),
      });
    } else if (decision.acao === "criar_planejado_parcelado") {
      transacoes.push({
        id: tx.id,
        acao: "criar_planejado_parcelado",
        descricao: decision.descricao.trim(),
        valor: Number(decision.valor),
        data: decision.data,
        // Categoria e opcional no gasto planejado: so envia o par completo
        ...(decision.categoria && decision.subcategoria
          ? { categoria: decision.categoria, subcategoria: decision.subcategoria }
          : {}),
        parcela_atual: Number(decision.parcelaAtual),
        parcela_total: Number(decision.parcelaTotal),
      });
    } else {
      transacoes.push({
        id: tx.id,
        acao: "criar_gasto_diario",
        descricao: decision.descricao.trim(),
        valor: Number(decision.valor),
        data: decision.data,
        categoria: decision.categoria,
        subcategoria: decision.subcategoria,
        metodo_pagamento: decision.metodoPagamento,
      });
    }
  }
  return { transacoes };
}

// Meses (year, month) que precisam ser consultados para exibir os gastos
// planejados candidatos a conciliacao: meses de TODAS as transacoes (o usuario
// pode reclassificar qualquer linha para "Pagar gasto planejado") + atual e anterior.
export function monthsToFetchForMatches(
  batch: ImportBatch,
  today: Date = new Date()
): { year: number; month: number }[] {
  const keys = new Set<string>();
  const add = (year: number, month: number) => keys.add(`${year}-${month}`);

  add(today.getFullYear(), today.getMonth() + 1);
  const prev = new Date(today.getFullYear(), today.getMonth() - 1, 1);
  add(prev.getFullYear(), prev.getMonth() + 1);

  for (const tx of batch.transacoes) {
    const [year, month] = tx.data.split("-").map(Number);
    if (year && month) add(year, month);
  }

  return [...keys].map((key) => {
    const [year, month] = key.split("-").map(Number);
    return { year, month };
  });
}
