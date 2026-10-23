"""
CR-044: Rate limiting compartilhado (slowapi).

Instancia unica do Limiter usada tanto no registro em app.main quanto nos
decorators dos endpoints (app.routers.auth). Storage em memoria (padrao do
slowapi): producao roda 1 worker uvicorn, entao o contador e consistente dentro
do processo; reseta a cada deploy/restart — aceitavel para anti-brute-force.

Chave por IP de origem (get_remote_address). Sem default_limits: os limites sao
aplicados por rota via @limiter.limit(...), nao globalmente.
"""
import hashlib

from fastapi import HTTPException, Request
from fastapi.security.utils import get_authorization_scheme_param
from limits import parse
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


# ========== API de integracao (CR-058, RN-054) ==========
# Um limite so para todas as rotas /api/integration/v1, checado ANTES da autenticacao (dependency
# do router): por token (60/min) e por IP (120/min — segura tokens inventados, que nunca chegam a
# contar por token). Mesmo storage em memoria do slowapi: 1 worker, zera a cada deploy.

INTEGRATION_PER_TOKEN = parse("60/minute")
INTEGRATION_PER_IP = parse("120/minute")
_integration_storage = MemoryStorage()
_integration_limiter = MovingWindowRateLimiter(_integration_storage)


def reset_integration_limits() -> None:
    """Zera os contadores da API de integracao (testes)."""
    _integration_storage.reset()


def integration_rate_limit(request: Request) -> None:
    """Chave por token = hash do token (nunca o token), sem depender da grafia do esquema Bearer."""
    _, credential = get_authorization_scheme_param(request.headers.get("Authorization"))
    token_key = hashlib.sha256(credential.encode()).hexdigest()
    allowed = _integration_limiter.hit(
        INTEGRATION_PER_IP, "integration-ip", get_remote_address(request)
    ) and _integration_limiter.hit(INTEGRATION_PER_TOKEN, "integration-token", token_key)
    if not allowed:
        raise HTTPException(status_code=429, detail="Muitas requisições: tente de novo em instantes")
