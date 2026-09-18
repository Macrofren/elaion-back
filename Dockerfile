# ==============================================================================
# Elaion Backend - Multi-stage Dockerfile
# Imagem Python 3.12-slim com execução não-root e concorrência configurável
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Builder (Compilação e resolução de dependências)
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Instalação de ferramentas mínimas para compilação de extensões C se necessário
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Criação de ambiente virtual isolado
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalação de dependências do projeto
COPY pyproject.toml README.md ./
COPY app/ ./app/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# ------------------------------------------------------------------------------
# Stage 2: Final (Imagem enxuta e segura para produção)
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS final

LABEL maintainer="Elaion Team"
LABEL description="API Backend RESTful do Elaion em FastAPI e Clean Architecture"

WORKDIR /app

# Utilitários de runtime: curl (healthcheck) e cliente postgres (diagnóstico)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar o ambiente virtual com dependências pré-instaladas
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Criar usuário de aplicação sem privilégios administrativos
RUN groupadd -r appgroup && useradd -r -g appgroup -u 1001 appuser

# Criar estrutura de storage para uploads com permissões ao appuser
RUN mkdir -p /app/storage/uploads/fotos_perfil \
             /app/storage/uploads/logos_congeneres && \
    chown -R appuser:appgroup /app/storage

# Copiar arquivos da aplicação
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY docker-entrypoint.sh /docker-entrypoint.sh

# Normalizar quebra de linha (LF) e permissão de execução no entrypoint
RUN sed -i 's/\r$//' /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh && \
    chown -R appuser:appgroup /app

# Execução com usuário não-root
USER appuser

# Porta padrão de exposição
EXPOSE 8000

# Healthcheck do serviço Backend
HEALTHCHECK --interval=10s --timeout=5s --retries=5 --start-period=15s \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
