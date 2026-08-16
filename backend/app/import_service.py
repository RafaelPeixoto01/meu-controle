"""
CR-046 (F07): Servico de importacao de extratos/faturas em PDF via IA.

Monta o prompt com o contexto do usuario (categorias validas + gastos planejados
em aberto), envia o PDF para a API Claude (document block nativo), valida o JSON
retornado e calcula fingerprints para deduplicacao (RN-042).

O PDF e processado em memoria e nunca persistido (RN-043).
Reutiliza os padroes de retry/parse do servico de analise F06 (ai_analysis).
"""
import base64
import hashlib
import json
import logging
import os
import time
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app import crud
from app.ai_analysis import DEFAULT_MODEL, AiRefusalError, _parse_ai_json, extract_response_text
from app.categories import EXPENSE_CATEGORIES, PAYMENT_METHODS, is_valid_payment_method
from app.models import ExpenseStatus

import anthropic as anthropic_sdk

logger = logging.getLogger(__name__)

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts")

MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
# CR-049: "parcelamento" = compra parcelada detectada na fatura sem gasto
# planejado correspondente; vira uma serie de Expense na confirmacao.
CLASSIFICACOES_VALIDAS = {"gasto_diario", "match_planejado", "parcelamento", "ignorar"}

# Janela de gastos planejados enviados no prompt: extratos/faturas cobrem
# tipicamente o mes anterior; 3 meses para tras + mes seguinte da margem.
PENDING_EXPENSES_MONTHS_BACK = 3


def is_import_enabled() -> bool:
    return os.getenv("IMPORT_ENABLED", "true").lower() == "true"


def normalize_description(descricao: str) -> str:
    """Normaliza descricao para fingerprint: lowercase + espacos colapsados."""
    return " ".join(descricao.lower().split())


def compute_fingerprint(user_id: str, data_tx: date, valor: float, descricao: str) -> str:
    """Fingerprint de deduplicacao (RN-042): sha256(user|data|valor|descricao normalizada)."""
    raw = f"{user_id}|{data_tx.isoformat()}|{float(valor):.2f}|{normalize_description(descricao)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ========== Contexto do prompt ==========

def collect_open_expenses(db: Session, user_id: str, hoje: date | None = None) -> list:
    """
    Gastos planejados Pendente/Atrasado dos ultimos meses (candidatos a match).
    Janela: PENDING_EXPENSES_MONTHS_BACK meses para tras ate o mes seguinte.
    """
    hoje = hoje or date.today()
    mes = date(hoje.year, hoje.month, 1)
    meses = []
    # mes seguinte
    next_month = (mes.replace(day=28) + timedelta(days=4)).replace(day=1)
    meses.append(next_month)
    check = mes
    for _ in range(PENDING_EXPENSES_MONTHS_BACK + 1):
        meses.append(check)
        check = (check - timedelta(days=1)).replace(day=1)

    abertos = []
    for m in meses:
        for e in crud.get_expenses_by_month(db, m, user_id):
            if e.status in (ExpenseStatus.PENDENTE.value, ExpenseStatus.ATRASADO.value):
                abertos.append(e)
    return abertos


def _format_categories() -> str:
    lines = []
    for categoria, subcategorias in EXPENSE_CATEGORIES.items():
        lines.append(f"- {categoria}: {', '.join(subcategorias)}")
    return "\n".join(lines)


def _format_open_expenses(expenses: list) -> str:
    if not expenses:
        return "Nenhum gasto planejado em aberto."
    lines = []
    for e in expenses:
        parcela = f" (parcela {e.parcela_atual}/{e.parcela_total})" if e.parcela_total else ""
        lines.append(
            f"- id={e.id} | {e.nome}{parcela} | R$ {float(e.valor):.2f} | "
            f"vencimento {e.vencimento.isoformat()} | status {e.status}"
        )
    return "\n".join(lines)


def build_import_prompts(open_expenses: list) -> tuple[str, str]:
    """Carrega templates e interpola categorias, metodos e gastos planejados em aberto."""
    with open(os.path.join(PROMPTS_DIR, "import_extraction_system.txt"), encoding="utf-8") as f:
        system_prompt = f.read()
    with open(os.path.join(PROMPTS_DIR, "import_extraction_user.txt"), encoding="utf-8") as f:
        user_template = f.read()

    replacements = {
        "categorias": _format_categories(),
        "metodos_pagamento": ", ".join(PAYMENT_METHODS),
        "gastos_planejados": _format_open_expenses(open_expenses),
        "data_hoje": date.today().isoformat(),
    }
    user_prompt = user_template
    for key, value in replacements.items():
        user_prompt = user_prompt.replace(f"{{{{{key}}}}}", str(value))

    return system_prompt, user_prompt


# ========== Cliente Anthropic (PDF document block) ==========

def call_import_api(pdf_bytes: bytes, system_prompt: str, user_prompt: str) -> dict:
    """
    Envia o PDF + prompt para a API Claude e retorna o JSON extraido + metadata.
    Mesmo padrao de retry/backoff do F06 (ai_analysis.call_anthropic_api).
    Raises Exception em caso de erro apos os retries.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY não configurada")

    model = os.getenv("CLAUDE_MODEL", DEFAULT_MODEL)
    timeout_seconds = int(os.getenv("IMPORT_TIMEOUT_SECONDS", "180"))

    client = anthropic_sdk.Anthropic(api_key=api_key, timeout=timeout_seconds)
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("ascii")

    start_time = time.time()
    max_retries = 2
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            # CR-048: sem `temperature` (rejeitado com 400 na geracao atual).
            # Thinking fica ligado com `effort: low`: desligar no Opus 5 pode
            # vazar tags XML internas no texto e quebrar o parse do JSON, e
            # baixar o effort e a forma recomendada de conter custo e latencia
            # numa tarefa mecanica de extracao.
            # max_tokens cobre raciocinio + JSON somados — fatura grande gera
            # muitas transacoes.
            response = client.messages.create(
                model=model,
                max_tokens=16000,
                thinking={"type": "adaptive"},
                output_config={"effort": "low"},
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_b64,
                                },
                            },
                            {"type": "text", "text": user_prompt},
                        ],
                    }
                ],
            )

            elapsed_ms = int((time.time() - start_time) * 1000)
            raw_text = extract_response_text(response)
            resultado = _parse_ai_json(raw_text)

            return {
                "resultado": resultado,
                "tokens_input": response.usage.input_tokens,
                "tokens_output": response.usage.output_tokens,
                "modelo": model,
                "tempo_processamento_ms": elapsed_ms,
            }

        except AiRefusalError:
            raise  # CR-048: recusa e deterministica — retry so gastaria chamadas

        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(f"Import JSON parse error on attempt {attempt + 1}: {e}")
            if attempt < max_retries:
                time.sleep(1 * (attempt + 1))
                continue
            raise ValueError(f"IA retornou JSON inválido após {max_retries + 1} tentativas") from e

        except Exception as e:
            last_error = e
            logger.warning(f"Import API error on attempt {attempt + 1}: {e}")
            if attempt < max_retries:
                time.sleep(2 * (attempt + 1))
                continue
            raise

    raise last_error  # safety net


# ========== Validacao do resultado da IA ==========

def _parse_parcelas(tx: dict) -> tuple[int | None, int | None]:
    """
    CR-049: le e valida o par parcela_atual/parcela_total de uma transacao.

    Retorna (None, None) se a numeracao nao for coerente — o que rebaixa a
    classificacao para gasto_diario. Exige inteiros com total > 1 e
    1 <= atual <= total; "1/1" nao e parcelamento, e uma compra a vista.
    """
    try:
        atual = int(tx.get("parcela_atual"))
        total = int(tx.get("parcela_total"))
    except (TypeError, ValueError):
        return None, None
    if total <= 1 or atual < 1 or atual > total:
        return None, None
    return atual, total


def validate_ai_result(resultado: dict, valid_expense_ids: set[str]) -> dict:
    """
    Sanitiza o JSON da IA: descarta transacoes malformadas e normaliza campos.

    - data invalida, valor <= 0 ou descricao vazia → transacao descartada
    - classificacao desconhecida → vira gasto_diario
    - match_planejado com expense_id fora da lista de planejados em aberto → vira gasto_diario
    - parcelamento sem numeracao coerente (CR-049) → vira gasto_diario
    - par categoria/subcategoria invalido → ambos None (usuario define na revisao)
    - metodo_pagamento invalido → None; fatura sem metodo → "Cartão de Crédito"
    """
    banco = str(resultado.get("banco") or "")[:50] or None
    tipo_documento = resultado.get("tipo_documento")
    if tipo_documento not in ("extrato", "fatura"):
        tipo_documento = None

    transacoes_limpas = []
    for tx in resultado.get("transacoes") or []:
        if not isinstance(tx, dict):
            continue
        try:
            data_tx = date.fromisoformat(str(tx.get("data")))
        except (TypeError, ValueError):
            continue
        try:
            valor = round(float(tx.get("valor")), 2)
        except (TypeError, ValueError):
            continue
        descricao = str(tx.get("descricao") or "").strip()[:255]
        if valor <= 0 or not descricao:
            continue

        classificacao = tx.get("classificacao")
        if classificacao not in CLASSIFICACOES_VALIDAS:
            classificacao = "gasto_diario"

        expense_id = tx.get("expense_id")
        if classificacao == "match_planejado":
            if not expense_id or str(expense_id) not in valid_expense_ids:
                classificacao = "gasto_diario"
                expense_id = None
        else:
            expense_id = None

        # CR-049: parcelamento sem numeracao coerente nao vira serie de parcelas —
        # rebaixa para gasto_diario e deixa o usuario decidir na revisao
        parcela_atual, parcela_total = _parse_parcelas(tx)
        if classificacao == "parcelamento" and parcela_total is None:
            classificacao = "gasto_diario"
        if classificacao != "parcelamento":
            parcela_atual = parcela_total = None

        categoria = tx.get("categoria")
        subcategoria = tx.get("subcategoria")
        if (
            categoria not in EXPENSE_CATEGORIES
            or subcategoria not in EXPENSE_CATEGORIES.get(categoria, [])
        ):
            categoria = None
            subcategoria = None

        metodo = tx.get("metodo_pagamento")
        if metodo is not None and not is_valid_payment_method(metodo):
            metodo = None
        if metodo is None and tipo_documento == "fatura":
            metodo = "Cartão de Crédito"

        motivo = str(tx.get("motivo_ignorar") or "").strip()[:255] or None
        if classificacao != "ignorar":
            motivo = None

        transacoes_limpas.append({
            "data": data_tx,
            "descricao": descricao,
            "valor": valor,
            "classificacao": classificacao,
            "expense_id_sugerido": str(expense_id) if expense_id else None,
            "categoria": categoria,
            "subcategoria": subcategoria,
            "metodo_pagamento": metodo,
            "motivo_ignorar": motivo,
            "parcela_atual": parcela_atual,
            "parcela_total": parcela_total,
        })

    return {
        "banco": banco,
        "tipo_documento": tipo_documento,
        "transacoes": transacoes_limpas,
    }


def mark_duplicates(db: Session, user_id: str, transacoes: list[dict]) -> list[dict]:
    """
    Calcula fingerprint de cada transacao e marca como 'duplicada' as que ja
    foram confirmadas em lotes anteriores (RN-042). Adiciona chaves
    'fingerprint' e 'status' em cada dict.
    """
    for tx in transacoes:
        tx["fingerprint"] = compute_fingerprint(user_id, tx["data"], tx["valor"], tx["descricao"])

    fingerprints = [tx["fingerprint"] for tx in transacoes]
    confirmados = crud.get_confirmed_fingerprints(db, user_id, fingerprints)

    for tx in transacoes:
        tx["status"] = "duplicada" if tx["fingerprint"] in confirmados else "pendente"
    return transacoes
