#!/bin/sh
set -e

# ==============================================================================
# Elaion Backend - Docker Entrypoint Inteligente
# Aguarda o PostgreSQL, executa migrações Alembic e seeds, e inicia a aplicação.
# ==============================================================================

echo "---------------------------------------------------------------"
echo ">> Iniciando Elaion Backend (FastAPI)"
echo "---------------------------------------------------------------"

# Parâmetros de controle via ambiente
RUN_MIGRATIONS=${RUN_MIGRATIONS:-"true"}
RUN_SEEDS=${RUN_SEEDS:-"true"}
DB_WAIT_TIMEOUT=${DB_WAIT_TIMEOUT:-60}

# 1. Rotina de espera pelo Banco de Dados (TCP probe via Python padrão)
echo ">> [1/4] Verificando conectividade com o banco de dados..."

python << END
import os
import sys
import socket
import time
from urllib.parse import urlparse

timeout = int(os.getenv("DB_WAIT_TIMEOUT", "60"))
db_url = os.getenv("DATABASE_URL")

if db_url:
    clean_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    parsed = urlparse(clean_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
else:
    host = os.getenv("POSTGRES_SERVER", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5432"))

print(f"   Aguardando PostgreSQL em {host}:{port} (timeout máximo: {timeout}s)...")
start_time = time.time()

while True:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect((host, port))
        sock.close()
        print(f"   ✓ Conexão TCP estabelecida com sucesso com {host}:{port}!")
        sys.exit(0)
    except Exception:
        elapsed = time.time() - start_time
        if elapsed >= timeout:
            print(f"   ✗ ERRO: Timeout de {timeout}s aguardando PostgreSQL em {host}:{port}.")
            sys.exit(1)
        time.sleep(2)
END

# 2. Execução de migrações automáticas (Alembic)
if [ "$RUN_MIGRATIONS" = "true" ] || [ "$RUN_MIGRATIONS" = "1" ]; then
    echo ">> [2/4] Aplicando migrações do Alembic (alembic upgrade head)..."
    alembic upgrade head
    echo "   ✓ Migrações aplicadas com sucesso."
else
    echo ">> [2/4] Migrações do Alembic desabilitadas (RUN_MIGRATIONS=$RUN_MIGRATIONS)."
fi

# 3. Execução de seeds de catálogo/permissões do SIRAC
if [ "$RUN_SEEDS" = "true" ] || [ "$RUN_SEEDS" = "1" ]; then
    echo ">> [3/4] Executando seeds de permissões do SIRAC..."
    python scripts/seed_permissoes_sirac.py
    echo "   ✓ Seeds executados com sucesso."
else
    echo ">> [3/4] Execução de seeds desabilitada (RUN_SEEDS=$RUN_SEEDS)."
fi

# 3.1 Seed opcional de códigos de ativação de teste (idempotente, gated por env)
if [ -n "$SEED_CONVITES" ]; then
    echo ">> [3.1] Inserindo códigos de ativação de teste (SEED_CONVITES)..."
    python scripts/seed_convites_teste.py
    echo "   ✓ Seed de convites de teste concluído."
fi

# 4. Handover para o comando final (Uvicorn)
echo ">> [4/4] Subindo servidor Uvicorn..."
echo "---------------------------------------------------------------"

# Se o primeiro argumento começar com '-', repassa como opções para o uvicorn
if [ "${1#-}" != "$1" ]; then
    set -- uvicorn app.main:app "$@"
fi

# Se nenhum comando foi passado, executa o comando padrão com concorrência configurável
if [ "$#" -eq 0 ]; then
    WORKERS=${WEB_CONCURRENCY:-1}
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "$WORKERS"
fi

exec "$@"
