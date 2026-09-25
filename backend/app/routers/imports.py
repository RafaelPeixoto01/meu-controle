"""CR-046 (F07): Router de importacao de extratos/faturas em PDF via IA."""
import logging
import os
from datetime import date, datetime

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.ai_analysis import DEFAULT_MODEL
from app.database import get_db, get_session_factory
from app.auth import get_current_user
from app.models import DailyExpense, ExpenseStatus, ImportBatch, User
from app.rate_limit import limiter
from app.categories import EXPENSE_CATEGORIES, is_valid_payment_method
from app.schemas import (
    ImportBatchResponse,
    ImportBatchSummary,
    ImportConfirmRequest,
    ImportConfirmResponse,
    ImportHistoryItem,
    ImportHistoryPage,
    ImportUndoPreview,
    ImportUndoResponse,
    ImportUploadResponse,
)
from app import crud, import_service, import_undo, services
from app.utils import add_months

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/imports", tags=["imports"])


@router.post("", response_model=ImportUploadResponse, status_code=202)
@limiter.limit("5/minute")
def upload_import(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    session_factory=Depends(get_session_factory),
    current_user: User = Depends(get_current_user),
):
    """
    CR-052 (RN-047): upload de extrato/fatura em PDF. Valida o arquivo, grava o
    lote em `processando` e responde 202 na hora — a interpretacao pela IA roda
    em BackgroundTasks e o frontend acompanha por `GET /api/imports/{id}`.

    O PDF e processado em memoria e descartado (RN-043).
    """
    # 1. Feature flag / API key (padrao F06: indisponibilidade nunca e 5xx)
    if not import_service.is_import_enabled():
        response.status_code = 200
        return ImportUploadResponse(
            status="indisponivel", reason="Importação de extratos está desabilitada"
        )
    if not os.getenv("ANTHROPIC_API_KEY"):
        response.status_code = 200
        return ImportUploadResponse(
            status="indisponivel",
            reason="Importação não configurada. Configure ANTHROPIC_API_KEY.",
        )

    # 2. Validacoes do arquivo (extensao, tamanho, magic bytes)
    filename = os.path.basename(file.filename or "")
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Apenas arquivos PDF são aceitos")

    pdf_bytes = file.file.read(import_service.MAX_PDF_SIZE_BYTES + 1)
    if len(pdf_bytes) > import_service.MAX_PDF_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo excede o limite de 10MB")
    if not pdf_bytes.startswith(b"%PDF-"):
        raise HTTPException(status_code=422, detail="Arquivo não é um PDF válido")

    # 3. Persistir o lote vazio e devolver o controle ao usuario. `modelo` e
    # NOT NULL e ja e conhecido aqui (vem do env); a task o reescreve com o
    # valor que a API efetivamente usou.
    batch = ImportBatch(
        user_id=current_user.id,
        filename=filename[:255],
        status="processando",
        modelo=os.getenv("CLAUDE_MODEL", DEFAULT_MODEL),
    )
    crud.create_import_batch(db, batch)  # commit antes de a task enxergar a linha

    # 4. Interpretacao via IA fora do request (RN-047)
    background_tasks.add_task(
        import_service.process_import_batch,
        session_factory,
        batch.id,
        current_user.id,
        pdf_bytes,
    )

    return ImportUploadResponse(
        status="disponivel",
        batch=ImportBatchResponse.model_validate(batch),
    )


@router.get("", response_model=ImportHistoryPage)
def get_import_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    CR-056: historico de lotes do usuario, de todos os status, mais recentes
    primeiro — antes, um lote confirmado saia do /pending e sumia da interface.
    """
    batches, total = crud.get_import_history(db, current_user.id, page, page_size)
    # RN-048 tambem aqui: o historico nao pode mostrar para sempre um lote
    # orfao em 'processando' que o /pending ja resolveria como erro.
    # Lista (e nao gerador) para resolver TODOS, nao parar no primeiro.
    if any([import_service.resolve_stale_batch(db, b) for b in batches]):
        db.commit()

    contagens = crud.count_import_transactions_by_status(
        db, current_user.id, [b.id for b in batches]
    )
    items = []
    for batch in batches:
        por_status = contagens.get(batch.id, {})
        items.append(ImportHistoryItem(
            **ImportBatchSummary.model_validate(batch).model_dump(),
            total_transacoes=sum(por_status.values()),
            confirmadas=por_status.get("confirmada", 0),
            descartadas=por_status.get("descartada", 0),
            duplicadas=por_status.get("duplicada", 0),
            revertidas=por_status.get("revertida", 0),
            pode_desfazer=import_undo.undo_blocker(batch) is None,
        ))
    return ImportHistoryPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/pending", response_model=list[ImportBatchSummary])
def get_pending_imports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lotes do usuario aguardando alguma acao: `pendente_revisao` (retomada da
    revisao) e `processando` (CR-052 — o usuario pode sair da pagina durante a
    extracao e reencontrar o lote aqui).
    """
    batches = crud.get_pending_import_batches(db, current_user.id)
    resolvidos = [b for b in batches if import_service.resolve_stale_batch(db, b)]
    if resolvidos:
        db.commit()  # RN-048
        batches = [b for b in batches if b not in resolvidos]
    return batches


@router.get("/{batch_id}", response_model=ImportBatchResponse)
def get_import_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Detalhes de um lote com suas transacoes. E tambem o canal de polling do
    processamento assincrono (CR-052).
    """
    batch = crud.get_import_batch_by_id(db, batch_id, current_user.id)
    if not batch:
        raise HTTPException(status_code=404, detail="Lote de importação não encontrado")
    if import_service.resolve_stale_batch(db, batch):
        db.commit()  # RN-048
    return batch


@router.post("/{batch_id}/confirm", response_model=ImportConfirmResponse)
def confirm_import(
    batch_id: str,
    payload: ImportConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Aplica as decisoes revisadas: cria gastos diarios (mes da data da compra, RN-039),
    atualiza gastos planejados (status Pago + valor real, RN-040) e descarta o resto.
    Transacoes do lote ausentes do payload sao descartadas, exceto as 'duplicada',
    que permanecem assim para auditoria. Operacao atomica.
    """
    batch = crud.get_import_batch_by_id(db, batch_id, current_user.id)
    if not batch:
        raise HTTPException(status_code=404, detail="Lote de importação não encontrado")
    if batch.status != "pendente_revisao":
        raise HTTPException(status_code=409, detail="Lote não está pendente de revisão")

    tx_by_id = {t.id: t for t in batch.transacoes}
    decisions = {}
    for d in payload.transacoes:
        if d.id not in tx_by_id:
            raise HTTPException(
                status_code=422, detail=f"Transação {d.id} não pertence ao lote"
            )
        decisions[d.id] = d

    criados = 0
    planejados_criados = 0  # CR-049
    atualizados = 0
    descartadas = 0
    expenses_ja_atualizados: set[str] = set()
    series_ja_criadas: set[tuple] = set()  # CR-049
    # CR-054: regras carregadas UMA vez — o laco abaixo pode ter 80 linhas, e a
    # sessao roda com autoflush=False (duas linhas do mesmo estabelecimento nao
    # se enxergariam num SELECT por linha e colidiriam na unique constraint)
    regras_do_usuario = crud.get_import_rules_map(db, current_user.id)
    padroes_aprendidos: set[str] = set()
    # CR-056 (ADR-022): tudo o que este confirm gravar, para o undo desfazer
    diario = import_undo.EffectJournal(batch)

    for tx in batch.transacoes:
        decision = decisions.get(tx.id)
        if decision is None and tx.status == "duplicada":
            continue  # duplicada nao resgatada permanece 'duplicada' (auditoria)
        acao = decision.acao if decision else "descartar"

        if acao == "descartar":
            tx.status = "descartada"
            descartadas += 1

        elif acao == "criar_gasto_diario":
            descricao = (decision.descricao or tx.descricao).strip()
            if not descricao:
                raise HTTPException(
                    status_code=422, detail=f"Transação {tx.id}: descrição vazia"
                )
            valor = decision.valor if decision.valor is not None else float(tx.valor)
            data_tx = decision.data or tx.data
            categoria = decision.categoria or tx.categoria
            subcategoria = decision.subcategoria or tx.subcategoria
            metodo = decision.metodo_pagamento or tx.metodo_pagamento

            # Par categoria+subcategoria validado junto: subcategorias se repetem
            # entre categorias, entao derivar so da subcategoria seria ambiguo
            if (
                categoria not in EXPENSE_CATEGORIES
                or subcategoria not in EXPENSE_CATEGORIES.get(categoria, [])
            ):
                raise HTTPException(
                    status_code=422,
                    detail=f"Transação {tx.id}: categoria/subcategoria inválidas",
                )
            if not metodo or not is_valid_payment_method(metodo):
                raise HTTPException(
                    status_code=422,
                    detail=f"Transação {tx.id}: método de pagamento inválido",
                )

            gasto = DailyExpense(
                user_id=current_user.id,
                mes_referencia=date(data_tx.year, data_tx.month, 1),  # RN-039
                descricao=descricao,
                valor=valor,
                data=data_tx,
                categoria=categoria,
                subcategoria=subcategoria,
                metodo_pagamento=metodo,
            )
            db.add(gasto)
            db.flush()
            tx.daily_expense_id_criado = gasto.id
            tx.status = "confirmada"
            criados += 1
            diario.criado(tx, gasto)

            # CR-054 (RN-049): aprende a decisao do usuario para este padrao.
            # A chave sai do texto que veio do DOCUMENTO, nunca da descricao
            # editada: o extrato do mes seguinte trara o descritor de novo, e
            # uma regra indexada por "Padaria Stella" jamais casaria com
            # "PG *PADARIA STELLA*SP 15/08".
            #
            # `descricao_original` e obrigatorio aqui e nao um detalhe: se a
            # linha ja chegou renomeada por uma regra, `tx.descricao` E o nome
            # aprendido, e aprender dele criaria uma regra paralela — a original
            # nunca mais receberia correcao. Fallback para o historico anterior.
            texto_documento = tx.descricao_original or tx.descricao
            padrao = import_service.normalize_pattern(texto_documento)
            # Uma linha ja aprendida neste mesmo confirm nao reprocessa: `hits`
            # deve contar confirmacoes do padrao, nao linhas da fatura — senao
            # 6 corridas de Uber num mes superariam um padrao recorrente de 5
            # meses na ordenacao que o few-shot vai usar
            if padrao and padrao not in padroes_aprendidos:
                padroes_aprendidos.add(padrao)
                crud.upsert_import_rule(
                    db,
                    regras_do_usuario,
                    current_user.id,
                    padrao,
                    # So aprende o nome se o usuario REALMENTE reescreveu. Sem
                    # esta guarda, aceitar o descritor como veio gravaria a data
                    # do mes corrente ("...12/07") como nome sugerido, e o mes
                    # seguinte chegaria renomeado com a data velha.
                    descricao_sugerida=descricao if descricao != texto_documento else None,
                    categoria=categoria,
                    subcategoria=subcategoria,
                    metodo_pagamento=metodo,
                )

        elif acao == "criar_planejado_parcelado":
            # CR-049: materializa a compra parcelada como serie de gastos planejados
            descricao = (decision.descricao or tx.descricao).strip()
            if not descricao:
                raise HTTPException(
                    status_code=422, detail=f"Transação {tx.id}: descrição vazia"
                )
            valor = decision.valor if decision.valor is not None else float(tx.valor)
            data_tx = decision.data or tx.data
            # Sem fallback para o palpite da IA: a revisao pode ter limpado a
            # categoria de proposito, e o par so chega aqui quando completo
            categoria = decision.categoria
            subcategoria = decision.subcategoria

            # Categoria e opcional em Expense, mas se vier tem que ser um par valido
            if categoria or subcategoria:
                if (
                    categoria not in EXPENSE_CATEGORIES
                    or subcategoria not in EXPENSE_CATEGORIES.get(categoria, [])
                ):
                    raise HTTPException(
                        status_code=422,
                        detail=f"Transação {tx.id}: categoria/subcategoria inválidas",
                    )

            # RN-045: `data` e a data da COMPRA; a parcela N e cobrada N-1 meses
            # depois dela. Sem esse offset a serie inteira nasceria deslocada
            # para tras (parcela 3 de uma compra de maio cairia em maio).
            offset = decision.parcela_atual - 1
            venc_parcela = add_months(data_tx, offset)

            # Duas linhas do mesmo lote apontando para a mesma serie colapsariam
            # numa despesa so (a segunda sobrescreveria o valor da primeira e
            # perderia suas parcelas futuras) — espelha a guarda do planejado
            serie_key = (descricao, decision.parcela_atual, decision.parcela_total, venc_parcela)
            if serie_key in series_ja_criadas:
                raise HTTPException(
                    status_code=422,
                    detail=f"Transação {tx.id}: esta parcela já foi criada por outra "
                           "transação deste lote",
                )
            series_ja_criadas.add(serie_key)

            efeitos_serie = services.SeriesEffects()  # CR-056
            expense_atual, criadas = services.create_expense_with_installments(
                db,
                user_id=current_user.id,
                mes_referencia=date(venc_parcela.year, venc_parcela.month, 1),
                nome=descricao,
                valor=valor,
                vencimento=venc_parcela,
                categoria=categoria,
                subcategoria=subcategoria,
                parcela_atual=decision.parcela_atual,
                parcela_total=decision.parcela_total,
                recorrente=False,
                # RN-044: a parcela desta fatura ja foi cobrada
                status_primeira=ExpenseStatus.PAGO.value,
                skip_existing=True,  # RN-046
                efeitos=efeitos_serie,
            )
            db.flush()
            tx.expense_id_criado = expense_atual.id
            tx.status = "confirmada"
            planejados_criados += criadas
            # CR-056: a parcela conciliada pela RN-046 ja existia — o undo a
            # restaura, nunca a apaga (o `expense_id_criado` acima nao distingue)
            if efeitos_serie.conciliada is not None:
                diario.conciliado(
                    tx,
                    efeitos_serie.conciliada,
                    efeitos_serie.status_anterior,
                    efeitos_serie.valor_anterior,
                )
            for criada in efeitos_serie.criadas:
                diario.criado(tx, criada)

        elif acao == "atualizar_planejado":
            expense_id = decision.expense_id or tx.expense_id_sugerido
            if not expense_id:
                raise HTTPException(
                    status_code=422,
                    detail=f"Transação {tx.id}: expense_id é obrigatório para atualizar planejado",
                )
            expense = crud.get_expense_by_id(db, expense_id, current_user.id)
            if not expense:
                raise HTTPException(status_code=404, detail="Despesa planejada não encontrada")
            if expense.id in expenses_ja_atualizados:
                raise HTTPException(
                    status_code=422,
                    detail=f"Transação {tx.id}: gasto planejado {expense.id} já foi "
                           "atualizado por outra transação deste lote",
                )
            # CR-055 (D3): conciliar algo ja pago remarcaria Pago e sobrescreveria
            # o valor real ja registrado, sem deixar rastro. A UI ja esconde os
            # pagos do dropdown; isto alinha o contrato da API ao que ela permite.
            #
            # DEPOIS da guarda de lote acima, e nao antes: a primeira conciliacao
            # ja deixou o Expense em Pago na sessao, entao checar aqui primeiro
            # faria duas linhas apontando para o mesmo planejado ABERTO
            # reportarem "ja esta pago" — mensagem errada, e a guarda especifica
            # viraria codigo morto.
            if expense.status == ExpenseStatus.PAGO.value:
                raise HTTPException(
                    status_code=422,
                    detail=f"Transação {tx.id}: o gasto planejado já está pago",
                )
            expenses_ja_atualizados.add(expense.id)

            # CR-056: estado de antes da conciliacao, que o undo restaura
            diario.conciliado(tx, expense, expense.status, float(expense.valor))
            expense.status = ExpenseStatus.PAGO.value  # RN-040
            expense.valor = decision.valor if decision.valor is not None else float(tx.valor)
            tx.expense_id_atualizado = expense.id
            tx.status = "confirmada"
            atualizados += 1

    # Depois da ultima alteracao do laco: a assinatura e a do estado final
    diario.gravar(db)
    batch.status = "confirmado"
    batch.confirmado_em = datetime.now()  # CR-056: marca o lote como desfazivel
    db.commit()

    return ImportConfirmResponse(
        gastos_diarios_criados=criados,
        planejados_criados=planejados_criados,
        planejados_atualizados=atualizados,
        descartadas=descartadas,
    )


@router.delete("/{batch_id}", status_code=204)
def discard_import_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Descarta um lote pendente de revisao."""
    batch = crud.get_import_batch_by_id(db, batch_id, current_user.id)
    if not batch:
        raise HTTPException(status_code=404, detail="Lote de importação não encontrado")
    if batch.status == "confirmado":
        raise HTTPException(status_code=409, detail="Lote já confirmado não pode ser descartado")
    # CR-056: descartar reescreveria o historico de um lote que ja foi desfeito
    if batch.status == "revertido":
        raise HTTPException(status_code=409, detail="Lote já desfeito não pode ser descartado")

    batch.status = "descartado"
    for tx in batch.transacoes:
        if tx.status == "pendente":
            tx.status = "descartada"
    db.commit()


def _get_undoable_batch(db: Session, batch_id: str, user_id: str) -> ImportBatch:
    batch = crud.get_import_batch_by_id(db, batch_id, user_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Lote de importação não encontrado")
    motivo = import_undo.undo_blocker(batch)
    if motivo:
        raise HTTPException(status_code=409, detail=motivo)
    return batch


@router.get("/{batch_id}/undo-preview", response_model=ImportUndoPreview)
def preview_undo_import(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    CR-056: o que o undo faria agora, item a item (RN-051). Nao altera nada;
    o POST recalcula o plano no momento da execucao.
    """
    batch = _get_undoable_batch(db, batch_id, current_user.id)
    passos = import_undo.plan_undo(db, batch)
    return ImportUndoPreview(
        **import_undo.summarize(passos),
        itens=import_undo.describe(passos),
    )


@router.post("/{batch_id}/undo", response_model=ImportUndoResponse)
def undo_import(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    CR-056 (RN-051/RN-052): desfaz um lote confirmado. Remove o que ele criou,
    restaura os planejados que ele conciliou e preserva o que foi alterado
    depois. Atomico: um commit so ao final.
    """
    batch = _get_undoable_batch(db, batch_id, current_user.id)
    passos = import_undo.plan_undo(db, batch)
    contadores = import_undo.apply_undo(db, batch, passos)
    db.commit()
    return ImportUndoResponse(**contadores)
