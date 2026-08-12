"""CR-046 (F07): Router de importacao de extratos/faturas em PDF via IA."""
import logging
import os
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import DailyExpense, ExpenseStatus, ImportBatch, ImportTransaction, User
from app.rate_limit import limiter
from app.categories import EXPENSE_CATEGORIES, is_valid_payment_method
from app.schemas import (
    ImportBatchResponse,
    ImportBatchSummary,
    ImportConfirmRequest,
    ImportConfirmResponse,
    ImportUploadResponse,
)
from app import crud, import_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/imports", tags=["imports"])


@router.post("", response_model=ImportUploadResponse, status_code=201)
@limiter.limit("5/minute")
def upload_import(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload de extrato/fatura em PDF: valida, interpreta via IA e grava lote em
    staging (`pendente_revisao`). O PDF e processado em memoria e descartado (RN-043).
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

    # 3. Interpretar via IA
    try:
        open_expenses = import_service.collect_open_expenses(db, current_user.id)
        system_prompt, user_prompt = import_service.build_import_prompts(open_expenses)
        api_result = import_service.call_import_api(pdf_bytes, system_prompt, user_prompt)

        valid_ids = {e.id for e in open_expenses}
        parsed = import_service.validate_ai_result(api_result["resultado"], valid_ids)
    except Exception as e:
        logger.error(f"Erro ao interpretar importação: {e}", exc_info=True)
        response.status_code = 200
        return ImportUploadResponse(
            status="erro",
            reason=f"Não foi possível interpretar o documento: {type(e).__name__}",
        )

    if not parsed["transacoes"]:
        response.status_code = 200
        return ImportUploadResponse(
            status="erro",
            reason="Nenhuma transação foi identificada no documento",
        )

    # 4. Dedup (RN-042) + persistir staging (RN-038)
    transacoes = import_service.mark_duplicates(db, current_user.id, parsed["transacoes"])

    batch = ImportBatch(
        user_id=current_user.id,
        filename=filename[:255],
        banco_detectado=parsed["banco"],
        tipo_documento=parsed["tipo_documento"],
        status="pendente_revisao",
        tokens_input=api_result.get("tokens_input"),
        tokens_output=api_result.get("tokens_output"),
        modelo=api_result["modelo"],
        tempo_processamento_ms=api_result.get("tempo_processamento_ms"),
    )
    for tx in transacoes:
        batch.transacoes.append(ImportTransaction(user_id=current_user.id, **tx))
    crud.create_import_batch(db, batch)

    return ImportUploadResponse(
        status="disponivel",
        batch=ImportBatchResponse.model_validate(batch),
    )


@router.get("/pending", response_model=list[ImportBatchSummary])
def get_pending_imports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lotes pendentes de revisao do usuario (retomada da revisao)."""
    return crud.get_pending_import_batches(db, current_user.id)


@router.get("/{batch_id}", response_model=ImportBatchResponse)
def get_import_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detalhes de um lote de importacao com suas transacoes."""
    batch = crud.get_import_batch_by_id(db, batch_id, current_user.id)
    if not batch:
        raise HTTPException(status_code=404, detail="Lote de importação não encontrado")
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
    atualizados = 0
    descartadas = 0
    expenses_ja_atualizados: set[str] = set()

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
            expenses_ja_atualizados.add(expense.id)

            expense.status = ExpenseStatus.PAGO.value  # RN-040
            expense.valor = decision.valor if decision.valor is not None else float(tx.valor)
            tx.expense_id_atualizado = expense.id
            tx.status = "confirmada"
            atualizados += 1

    batch.status = "confirmado"
    db.commit()

    return ImportConfirmResponse(
        gastos_diarios_criados=criados,
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

    batch.status = "descartado"
    for tx in batch.transacoes:
        if tx.status == "pendente":
            tx.status = "descartada"
    db.commit()
