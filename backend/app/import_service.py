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
import re
import time
import unicodedata
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app import crud
from app.ai_analysis import DEFAULT_MODEL, AiRefusalError, _parse_ai_json, extract_response_text
from app.categories import EXPENSE_CATEGORIES, PAYMENT_METHODS, is_valid_payment_method
from app.models import ExpenseStatus, ImportTransaction

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

# CR-052: um lote em 'processando' por mais que isso perdeu a BackgroundTasks
# (restart do container) e e resolvido como 'erro' na leitura (RN-048).
#
# O teto precisa ficar ACIMA do pior caso da extracao, senao a leitura marcaria
# como 'erro' uma task ainda viva e o `_claim_batch` jogaria fora a extracao ja
# paga. Pior caso: o retry do `call_import_api` (3 tentativas) multiplica o do
# SDK Anthropic (max_retries=2, tambem 3 tentativas), cada uma limitada por
# IMPORT_TIMEOUT_SECONDS=180s → 9 x 180s ≈ 27 min.
STALE_PROCESSING_MINUTES = 30

# CR-054: intermediarios de pagamento que prefixam o nome real do estabelecimento
# na fatura ("PG *PADARIA STELLA"). Removidos da chave de match para que a mesma
# loja gere a mesma regra tenha a cobranca passado por maquininha ou gateway.
# So sao removidos quando seguidos de "*" — sem esse marcador, "pg"/"pp" podem
# ser as iniciais do proprio estabelecimento.
ACQUIRER_PREFIXES = (
    "pg", "pag", "pags", "pagseguro", "pagsegur", "pagbank",
    "mp", "mercadopago", "mercpago", "mercadolivre",
    "stone", "cielo", "getnet", "sumup", "picpay", "pp", "paypal", "ebw", "ifd",
)
# Mais longo primeiro: a alternancia do `re` e leftmost-first, entao "pag" antes
# de "pagseguro" dependeria de backtracking para casar o prefixo inteiro.
ACQUIRER_PREFIX_RE = re.compile(
    r"^(?:" + "|".join(sorted(ACQUIRER_PREFIXES, key=len, reverse=True)) + r")\s*\*+\s*"
)

# CR-054: marca a procedencia da sugestao que chega ao staging. Nulo = palpite
# da IA (comportamento anterior); "aprendido" = regra do proprio usuario.
ORIGEM_APRENDIDO = "aprendido"

# CR-055 (RN-050): classificacao produzida SO pela deteccao deterministica do
# backend — de proposito fora de CLASSIFICACOES_VALIDAS, para que a IA nunca
# consiga emiti-la. O prompt nao conhece esse valor.
CLASSIFICACAO_JA_LANCADO = "ja_lancado"

# Um planejado ja pago so e apontado quando o valor bate dentro desta tolerancia
# E a data cai dentro desta janela em torno do vencimento. Ambos deliberadamente
# estreitos: a linha e sinalizada em silencio, e sinalizar demais treina o
# usuario a ignorar o grupo — o mesmo raciocinio do D1 do CR-054.
# Tolerancia ABSOLUTA, em reais. Era relativa (2%) e isso a tornava muito mais
# larga do que "centavos de arredondamento" nos valores altos: num aluguel de
# R$ 3.000 a janela virava R$ 60, engolindo compras sem relacao nenhuma.
PAID_MATCH_VALUE_TOLERANCE = 1.00
PAID_MATCH_WINDOW_DAYS = 7

# CR-054: descritores genericos que NAO identificam estabelecimento — o que os
# distingue entre si e justamente a parte numerica que `normalize_pattern`
# remove ("PIX ENVIADO 12/07" e "PIX ENVIADO 19/07" colapsam em "pix enviado").
# Sem esta lista, confirmar um unico Pix criaria uma regra coringa que no mes
# seguinte renomearia e recategorizaria TODOS os Pix — o mesmo falso positivo
# silencioso que o D1 evitou ao recusar match por prefixo.
PADROES_GENERICOS = frozenset({
    "pix", "pix enviado", "pix recebido", "pix transferencia", "transferencia",
    "transferencia enviada", "transferencia recebida", "ted", "doc", "saque",
    "deposito", "compra", "compra cartao", "compra no debito", "compra credito",
    "pagamento", "pagamento de fatura", "pagamento recebido", "debito automatico",
    "tarifa", "tarifa bancaria", "juros", "iof", "estorno", "anuidade",
})


def is_import_enabled() -> bool:
    return os.getenv("IMPORT_ENABLED", "true").lower() == "true"


def normalize_description(descricao: str) -> str:
    """Normaliza descricao para fingerprint: lowercase + espacos colapsados."""
    return " ".join(descricao.lower().split())


def normalize_pattern(descricao: str) -> str:
    """
    CR-054: chave de match da memoria de categorizacao.

    Diferente de `normalize_description` — que NAO pode mudar, porque alimenta
    os fingerprints ja persistidos (RN-042) — esta funcao busca um padrao
    ESTAVEL ENTRE MESES. O mesmo estabelecimento aparece com data e codigo de
    sequencia variaveis a cada fatura:

        "PG *PADARIA STELLA*SP 12/07"  ─┐
        "PG *PADARIA STELLA*SP 15/08"  ─┴─►  "padaria stella sp"

    Sem isso o match exato quase nunca casaria e a memoria nasceria inerte.
    """
    texto = descricao.lower().strip()

    # 1. Intermediario/adquirente colado ao nome (o "*" e o marcador; exigi-lo
    #    evita comer o inicio de um nome que por acaso comece com "pg"/"pp")
    for _ in range(2):  # "PG *PAGSEGURO *LOJA" tem dois niveis
        novo = ACQUIRER_PREFIX_RE.sub("", texto, count=1)
        if novo == texto:
            break
        texto = novo

    # 2. Acentos: "acai" e "açaí" sao o mesmo estabelecimento
    texto = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )

    # 3. Pontuacao vira separador ("12/07" → "12 07", isolando os digitos)
    texto = re.sub(r"[^a-z0-9]+", " ", texto)

    # 4. Tokens puramente numericos sao data/sequencia — a parte instavel
    tokens = [t for t in texto.split() if not t.isdigit()]
    padrao = " ".join(tokens)[:255].strip()

    # Descritor sem nenhuma parte alfabetica (so numeros) perderia tudo aqui;
    # nesse caso o texto original ja e a chave mais estavel disponivel
    padrao = padrao or normalize_description(descricao)[:255]

    # Descritor generico nao vira chave: ele nao identifica estabelecimento
    # nenhum, e a regra pegaria transacoes sem relacao entre si
    return "" if padrao in PADROES_GENERICOS else padrao


def compute_fingerprint(
    user_id: str,
    data_tx: date,
    valor: float,
    descricao: str,
    parcela_atual: int | None = None,
    parcela_total: int | None = None,
) -> str:
    """
    Fingerprint de deduplicacao (RN-042): sha256(user|data|valor|descricao normalizada).

    CR-049: parcelas da mesma compra compartilham data (a da compra), valor e
    descricao ja limpa da numeracao — sem a numeracao no fingerprint, a parcela
    do mes seguinte nasceria marcada como duplicada. Transacoes sem parcela
    mantem a formula original (fingerprints antigos continuam validos).
    """
    raw = f"{user_id}|{data_tx.isoformat()}|{float(valor):.2f}|{normalize_description(descricao)}"
    if parcela_atual and parcela_total:
        raw += f"|{parcela_atual}/{parcela_total}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ========== Contexto do prompt ==========

def _expenses_in_window(db: Session, user_id: str, hoje: date, statuses: tuple[str, ...]) -> list:
    """
    Gastos planejados do usuario na janela da importacao, filtrados por status.
    Janela: PENDING_EXPENSES_MONTHS_BACK meses para tras ate o mes seguinte.

    CR-055: extraido de `collect_open_expenses` para que a coleta dos ja pagos
    use exatamente a mesma janela — duas copias divergiriam na primeira vez que
    alguem mexesse no numero de meses.
    """
    mes = date(hoje.year, hoje.month, 1)
    meses = []
    # mes seguinte
    next_month = (mes.replace(day=28) + timedelta(days=4)).replace(day=1)
    meses.append(next_month)
    check = mes
    for _ in range(PENDING_EXPENSES_MONTHS_BACK + 1):
        meses.append(check)
        check = (check - timedelta(days=1)).replace(day=1)

    encontrados = []
    for m in meses:
        for e in crud.get_expenses_by_month(db, m, user_id):
            if e.status in statuses:
                encontrados.append(e)
    return encontrados


def collect_open_expenses(db: Session, user_id: str, hoje: date | None = None) -> list:
    """Gastos planejados Pendente/Atrasado da janela (candidatos a conciliacao)."""
    hoje = hoje or date.today()
    return _expenses_in_window(
        db, user_id, hoje, (ExpenseStatus.PENDENTE.value, ExpenseStatus.ATRASADO.value)
    )


def _to_paid_candidates(expenses: list) -> list[dict]:
    """
    CR-055: candidatos ja pagos como dados puros, e nao entidades.

    Mesmo motivo do CR-054: `process_import_batch` fecha a sessao antes de
    chamar a IA, e objetos ORM desanexados dependeriam de os atributos
    continuarem carregados minutos depois. Mantem `detect_already_paid` pura e
    testavel sem banco.
    """
    return [
        {
            "id": e.id,
            "nome": e.nome,
            "valor": float(e.valor),
            "vencimento": e.vencimento,
        }
        for e in expenses
    ]


def collect_paid_expenses(db: Session, user_id: str, hoje: date | None = None) -> list[dict]:
    """
    CR-055: gastos planejados ja PAGOS da mesma janela — candidatos da RN-050.

    Eles nunca entram no prompt nem sao conciliaveis; servem so para a deteccao
    deterministica sinalizar uma transacao que ja foi lancada.
    """
    hoje = hoje or date.today()
    return _to_paid_candidates(
        _expenses_in_window(db, user_id, hoje, (ExpenseStatus.PAGO.value,))
    )


def collect_match_context(
    db: Session, user_id: str, hoje: date | None = None
) -> tuple[list, list[dict]]:
    """
    CR-055: (planejados em aberto, candidatos ja pagos) numa varredura so.

    `collect_open_expenses` e `collect_paid_expenses` percorrem a MESMA janela
    de 5 meses, cada uma com uma query por mes. Chamar as duas dobraria os
    round-trips dentro do trecho de sessao que o CR-052 mantem curto de
    proposito. Aqui a janela e lida uma vez e particionada em memoria.
    """
    hoje = hoje or date.today()
    todos = _expenses_in_window(
        db,
        user_id,
        hoje,
        (
            ExpenseStatus.PENDENTE.value,
            ExpenseStatus.ATRASADO.value,
            ExpenseStatus.PAGO.value,
        ),
    )
    abertos = [
        e
        for e in todos
        if e.status in (ExpenseStatus.PENDENTE.value, ExpenseStatus.ATRASADO.value)
    ]
    pagos = [e for e in todos if e.status == ExpenseStatus.PAGO.value]
    return abertos, _to_paid_candidates(pagos)


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


def detect_already_paid(transacoes: list[dict], paid_expenses: list[dict]) -> list[dict]:
    """
    CR-055 (RN-050): sinaliza transacoes que correspondem a um gasto planejado
    JA PAGO, para que confirmar a importacao nao lance o mesmo valor duas vezes.

    O furo que isso fecha: `collect_open_expenses` so oferece candidatos
    Pendente/Atrasado, entao um planejado ja quitado a mao chega a revisao como
    gasto diario novo, marcado, indistinguivel de uma compra de verdade. A dedup
    por fingerprint (RN-042) nao ajuda — ela compara com transacoes IMPORTADAS,
    nunca com lancamentos criados manualmente.

    Escopo (D7): so `gasto_diario`. `match_planejado` ja achou alvo em aberto,
    `parcelamento` e coberto pela RN-046 (que concilia parcela paga em vez de
    duplicar) e `ignorar` esta fora por definicao.

    Um planejado so pode ser reivindicado por UMA transacao do lote, e a
    atribuicao e resolvida **globalmente**: todos os pares viaveis do lote sao
    ordenados por proximidade (data, depois diferenca de valor) e o melhor par
    do lote inteiro e casado primeiro.

    Isso nao e detalhe de estilo. Percorrer as transacoes em ordem e casar a
    primeira que couber inverte o CR: com um planejado "Energia R$ 187,32" e um
    lote contendo "SUPERMERCADO R$ 186,60" (2 dias antes) e "CEMIG R$ 187,32"
    (no vencimento), o supermercado reivindicaria o alvo e seria silenciado,
    enquanto a CEMIG — a duplicata de verdade — chegaria marcada e seria
    importada. Perde-se um gasto legitimo E cria-se a contagem dupla.

    A ordenacao final inclui indice e id justamente para ser estavel: testes e
    revisoes precisam de resultado reproduzivel.
    """
    if not paid_expenses:
        return transacoes

    pares: list[tuple[int, float, int, str]] = []
    for idx, tx in enumerate(transacoes):
        if tx["classificacao"] != "gasto_diario":
            continue
        for candidato in paid_expenses:
            dist = abs((tx["data"] - candidato["vencimento"]).days)
            if dist > PAID_MATCH_WINDOW_DAYS:
                continue
            delta = abs(tx["valor"] - candidato["valor"])
            if delta > PAID_MATCH_VALUE_TOLERANCE:
                continue
            pares.append((dist, delta, idx, candidato["id"]))

    pares.sort()

    transacoes_usadas: set[int] = set()
    candidatos_usados: set[str] = set()
    for _dist, _delta, idx, candidato_id in pares:
        if idx in transacoes_usadas or candidato_id in candidatos_usados:
            continue
        transacoes_usadas.add(idx)
        candidatos_usados.add(candidato_id)
        transacoes[idx]["classificacao"] = CLASSIFICACAO_JA_LANCADO
        transacoes[idx]["expense_id_sugerido"] = candidato_id

    return transacoes


def _apply_rule(
    regra: dict,
    descricao: str,
    categoria: str | None,
    subcategoria: str | None,
    metodo: str | None,
    tipo_documento: str | None = None,
) -> tuple[str, str | None, str | None, str | None, bool]:
    """
    CR-054: sobrepoe o palpite da IA com a decisao que o usuario ja tomou para
    este padrao. A regra vence mesmo quando a IA devolveu um par valido — o
    ponto da memoria e justamente parar de recorrigir o mesmo erro todo mes.

    Cada campo e revalidado aqui, e nao so na escrita (D7): `categories.py`
    pode ter perdido uma subcategoria desde que a regra foi gravada, e uma
    regra defasada nao pode injetar par invalido no staging.
    """
    aplicou = False

    sugerida = (regra.get("descricao_sugerida") or "").strip()[:255]
    if sugerida:
        descricao = sugerida
        aplicou = True

    r_categoria = regra.get("categoria")
    r_subcategoria = regra.get("subcategoria")
    if (
        r_categoria in EXPENSE_CATEGORIES
        and r_subcategoria in EXPENSE_CATEGORIES.get(r_categoria, [])
    ):
        categoria = r_categoria
        subcategoria = r_subcategoria
        aplicou = True

    # Numa fatura o meio de pagamento e propriedade do DOCUMENTO, nao do
    # historico: a compra esta ali porque foi no cartao. Uma regra aprendida
    # num extrato (ex.: "Pix" na padaria) sobrescreveria o "Cartão de Crédito"
    # que a validacao acabou de derivar do tipo do documento, e o usuario
    # teria que recorrigir todo mes — o oposto do objetivo da memoria.
    if tipo_documento != "fatura":
        r_metodo = regra.get("metodo_pagamento")
        if r_metodo and is_valid_payment_method(r_metodo):
            metodo = r_metodo
            aplicou = True

    return descricao, categoria, subcategoria, metodo, aplicou


def validate_ai_result(
    resultado: dict,
    valid_expense_ids: set[str],
    rules: dict[str, dict] | None = None,
    paid_expenses: list[dict] | None = None,
) -> dict:
    """
    Sanitiza o JSON da IA: descarta transacoes malformadas e normaliza campos.

    - data invalida, valor <= 0 ou descricao vazia → transacao descartada
    - classificacao desconhecida → vira gasto_diario
    - match_planejado com expense_id fora da lista de planejados em aberto → vira gasto_diario
    - parcelamento sem numeracao coerente (CR-049) → vira gasto_diario
    - par categoria/subcategoria invalido → ambos None (usuario define na revisao)
    - metodo_pagamento invalido → None; fatura sem metodo → "Cartão de Crédito"
    - CR-054: `rules` (memoria do usuario) sobrepoe a sugestao da IA em
      gasto_diario e marca a transacao como 'aprendido'
    - CR-055: `paid_expenses` reclassifica como 'ja_lancado' o gasto diario que
      corresponde a um planejado ja pago (RN-050)
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

        # CR-054: a memoria so atua em gasto_diario (D4). Em 'parcelamento' a
        # descricao precisa continuar sendo a que a IA limpou da numeracao — e
        # ela que casa a parcela com a serie ja criada (RN-046); um nome
        # aprendido no lugar quebraria a conciliacao. 'match_planejado' e
        # 'ignorar' nao usam categoria/metodo.
        descricao_original = descricao
        origem_sugestao = None
        if rules and classificacao == "gasto_diario":
            padrao = normalize_pattern(descricao)
            regra = rules.get(padrao) if padrao else None
            if regra is not None:
                descricao, categoria, subcategoria, metodo, aplicou = _apply_rule(
                    regra, descricao, categoria, subcategoria, metodo, tipo_documento
                )
                if aplicou:
                    origem_sugestao = ORIGEM_APRENDIDO

        transacoes_limpas.append({
            "data": data_tx,
            "descricao": descricao,
            # Persistida: o fingerprint (RN-042) e a realimentacao da memoria no
            # confirm dependem do texto do documento, nunca do nome aprendido
            "descricao_original": descricao_original,
            "origem_sugestao": origem_sugestao,
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

    # CR-055 depois do CR-054 (D6): a memoria ja preencheu categoria/metodo, e
    # a reclassificacao preserva esses campos — assim, se o usuario resgatar a
    # linha, ela sai valida sem retrabalho.
    transacoes_limpas = detect_already_paid(transacoes_limpas, paid_expenses or [])

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

    CR-054: usa 'descricao_original' — o texto como veio do documento. O
    fingerprint PRECISA ser calculado sobre ele: quando uma regra aprendida
    renomeia a transacao, usar o nome novo faria o mesmo documento reimportado
    gerar outro hash e escapar da dedup, permitindo lancar o gasto duas vezes.
    """
    for tx in transacoes:
        descricao_fingerprint = tx.get("descricao_original") or tx["descricao"]
        tx["fingerprint"] = compute_fingerprint(
            user_id,
            tx["data"],
            tx["valor"],
            descricao_fingerprint,
            tx.get("parcela_atual"),
            tx.get("parcela_total"),
        )

    fingerprints = [tx["fingerprint"] for tx in transacoes]
    confirmados = crud.get_confirmed_fingerprints(db, user_id, fingerprints)

    for tx in transacoes:
        tx["status"] = "duplicada" if tx["fingerprint"] in confirmados else "pendente"
    return transacoes


# ========== Processamento assincrono (CR-052) ==========

def resolve_stale_batch(db: Session, batch) -> bool:
    """
    RN-048: lote preso em 'processando' ha mais de STALE_PROCESSING_MINUTES vira
    'erro' na leitura. Um restart do container mata a BackgroundTasks em voo e
    deixaria o lote em 'processando' para sempre; resolver na leitura evita um
    job de limpeza dedicado. Retorna True se mudou algo (o chamador commita).
    """
    if batch.status != "processando":
        return False
    limite = datetime.now() - timedelta(minutes=STALE_PROCESSING_MINUTES)
    if batch.created_at > limite:
        return False

    batch.status = "erro"
    batch.erro_mensagem = "O processamento foi interrompido. Envie o arquivo novamente."
    return True


def _claim_batch(db: Session, batch_id: str, user_id: str):
    """
    Relê o lote e só o devolve se ainda estiver 'processando'.

    Entre o inicio e o fim da extracao o usuario pode ter descartado o lote;
    escrever nele depois disso desfaria uma decisao ja tomada — vale tanto para
    o resultado quanto para a mensagem de erro.
    """
    batch = crud.get_import_batch_by_id(db, batch_id, user_id)
    if batch is None:
        logger.warning(f"Lote {batch_id} desapareceu durante o processamento")
        return None
    if batch.status != "processando":
        logger.info(
            f"Lote {batch_id} saiu de 'processando' durante a extração "
            f"(status={batch.status}); resultado descartado"
        )
        return None
    return batch


def _finish_with_error(session_factory, batch_id: str, user_id: str, mensagem: str) -> None:
    db = session_factory()
    try:
        batch = _claim_batch(db, batch_id, user_id)
        if batch is None:
            return
        batch.status = "erro"
        batch.erro_mensagem = mensagem[:255]
        db.commit()
    finally:
        db.close()


def process_import_batch(session_factory, batch_id: str, user_id: str, pdf_bytes: bytes) -> None:
    """
    CR-052: extracao do PDF fora do request (BackgroundTasks do FastAPI).

    O lote ja existe em 'processando' quando esta funcao roda; aqui ele caminha
    para 'pendente_revisao' (com as transacoes) ou 'erro' (com o motivo).

    A sessao e aberta em dois trechos curtos, com a chamada a IA entre eles: a
    extracao leva minutos e segurar uma conexao do pool em transacao por todo
    esse tempo esgotaria o pool e exporia a task a
    `idle_in_transaction_session_timeout` no PostgreSQL.

    RN-043 preservada: `pdf_bytes` chega pela closure da task e vive so em
    memoria — nao e gravado em disco, banco nem log.
    """
    # 1. Contexto do prompt (sessao curta)
    db = session_factory()
    try:
        if _claim_batch(db, batch_id, user_id) is None:
            return
        # CR-055: abertos e ja pagos saem da mesma varredura da janela
        open_expenses, paid_expenses = collect_match_context(db, user_id)
        valid_ids = {e.id for e in open_expenses}
        system_prompt, user_prompt = build_import_prompts(open_expenses)
        rules = crud.get_import_rules_data(db, user_id)  # CR-054
    except Exception:
        logger.error(f"Falha ao montar o contexto do lote {batch_id}", exc_info=True)
        db.rollback()
        db.close()
        _finish_with_error(
            session_factory, batch_id, user_id, "Não foi possível preparar a importação"
        )
        return
    finally:
        db.close()

    # 2. Chamada a IA — sem conexao de banco presa
    try:
        api_result = call_import_api(pdf_bytes, system_prompt, user_prompt)
        parsed = validate_ai_result(api_result["resultado"], valid_ids, rules, paid_expenses)
    except Exception as e:
        logger.error(f"Erro ao interpretar importação {batch_id}: {e}", exc_info=True)
        _finish_with_error(
            session_factory,
            batch_id,
            user_id,
            f"Não foi possível interpretar o documento: {type(e).__name__}",
        )
        return

    if not parsed["transacoes"]:
        _finish_with_error(
            session_factory, batch_id, user_id, "Nenhuma transação foi identificada no documento"
        )
        return

    # 3. Persistir o staging (sessao curta)
    db = session_factory()
    try:
        batch = _claim_batch(db, batch_id, user_id)
        if batch is None:
            return

        # Dedup (RN-042) + persistir staging (RN-038)
        transacoes = mark_duplicates(db, user_id, parsed["transacoes"])

        batch.banco_detectado = parsed["banco"]
        batch.tipo_documento = parsed["tipo_documento"]
        batch.tokens_input = api_result.get("tokens_input")
        batch.tokens_output = api_result.get("tokens_output")
        batch.modelo = api_result["modelo"]
        batch.tempo_processamento_ms = api_result.get("tempo_processamento_ms")
        for tx in transacoes:
            batch.transacoes.append(ImportTransaction(user_id=user_id, **tx))
        batch.status = "pendente_revisao"
        db.commit()
    except Exception:
        # Task nao tem quem trate a excecao: logar e nao deixar a sessao suja
        logger.error(f"Falha ao gravar o lote {batch_id}", exc_info=True)
        db.rollback()
    finally:
        db.close()
