"""
CR-044: Rate limiting compartilhado (slowapi).

Instancia unica do Limiter usada tanto no registro em app.main quanto nos
decorators dos endpoints (app.routers.auth). Storage em memoria (padrao do
slowapi): producao roda 1 worker uvicorn, entao o contador e consistente dentro
do processo; reseta a cada deploy/restart — aceitavel para anti-brute-force.

Chave por IP de origem (get_remote_address). Sem default_limits: os limites sao
aplicados por rota via @limiter.limit(...), nao globalmente.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
