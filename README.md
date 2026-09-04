# Elaion - Backend API (FastAPI, SQLAlchemy 2.0 & Clean Architecture)

Este repositório contém a API RESTful do sistema de gestão de terminais de combustíveis **Elaion**, construída com **Python 3.11+**, **FastAPI**, **SQLAlchemy 2.0 (Async/asyncpg)**, **PostgreSQL** e **Clean Architecture**.

---

## 🏛️ Arquitetura e Estrutura do Projeto

O backend adota o princípio de dependência estrita de fora para dentro:
`Routers (HTTP)` $\rightarrow$ `Services (Casos de Uso)` $\rightarrow$ `Repositories (Acesso ao DB)` $\rightarrow$ `Models/Schemas (Entidades/DTOs)`.

```text
backend/
├── alembic/                         # Configurações e versões de migrações do banco
│   ├── versions/                    # Scripts de migração autogerados
│   └── env.py                       # Runner assíncrono do Alembic (asyncpg)
├── app/
│   ├── api/
│   │   ├── deps.py                  # Dependências FastAPI (sessão DB, autenticação, permissões)
│   │   ├── exceptions.py            # Handlers globais de exceções de domínio
│   │   └── routers/
│   │       ├── api_v1.py            # Roteador principal agregador (v1)
│   │       └── ...                  # Rotas por contexto/módulo
│   ├── core/
│   │   ├── config.py                # Configurações globais via Pydantic Settings (.env)
│   │   └── security.py              # Middleware CORS, hash de senhas e JWT
│   ├── domain/
│   │   ├── models.py                # Modelos ORM SQLAlchemy 2.0 (24 tabelas com tipos nativos PG)
│   │   └── schemas.py               # Contratos e DTOs Pydantic v2 (Input/Output fail-fast)
│   ├── infra/
│   │   ├── database.py              # AsyncEngine e async_sessionmaker com asyncpg
│   │   └── repositories/            # Camada de acesso a dados (SQLAlchemy assíncrono)
│   ├── services/                    # Regras de negócio puras (sem dependência de HTTP/FastAPI)
│   └── main.py                      # Factory e entrypoint limpo do FastAPI
├── tests/
│   ├── conftest.py                  # Fixtures Pytest (AsyncClient e sessão DB de teste)
│   └── api/
│       └── test_health.py           # Testes de integração de endpoints
├── .env.example                     # Template de variáveis de ambiente
├── .gitignore                       # Arquivos ignorados pelo Git (venv, .env, caches)
├── alembic.ini                      # Configuração CLI do Alembic
└── pyproject.toml                   # Dependências e ferramentas de desenvolvimento
```

---

## 📋 Contrato de API (OpenAPI 3.1 & Swagger UI)

A aplicação adota o princípio de **Documentação Viva (*Living Documentation*)**: os contratos são definidos estritamente em Schemas Pydantic v2 e roteadores modulares, gerando a especificação interativa no Swagger e ReDoc:

* **Swagger UI Interativo:** `http://localhost:8000/api/v1/docs`
* **ReDoc:** `http://localhost:8000/api/v1/redoc`
* **Especificação OpenAPI JSON:** `http://localhost:8000/api/v1/openapi.json`

### Endpoints de Autenticação, Onboarding e Credenciais:

| Método | Rota | Descrição |
| :--- | :--- | :--- |
| `POST` | `/api/v1/cadastro/validar-codigo` | Validação do código de assinatura comercial `ELAION-XXXX-XXXX` (Step 1 do Onboarding) |
| `POST` | `/api/v1/cadastro/registrar` | Conclusão do cadastro de Organização, Terminal e Usuário Master (Step 4) |
| `POST` | `/api/v1/auth/login` | Login por CPF/E-mail (emite Access Token + Cookie HttpOnly) |
| `POST` | `/api/v1/auth/refresh` | Rotação automática do par de tokens via Cookie seguro |
| `POST` | `/api/v1/auth/logout` | Encerramento de sessão e invalidação do Cookie HttpOnly |
| `GET` | `/api/v1/auth/me` | Dados do usuário autenticado e permissões nos terminais |
| `POST` | `/api/v1/auth/primeiro-acesso/validar` | Validação de CPF + código `ATIV-XXXX` emitido pelo gestor |
| `POST` | `/api/v1/auth/primeiro-acesso/concluir` | Definição da senha definitiva e PIN de 4 a 6 dígitos |
| `POST` | `/api/v1/auth/recuperar-senha/master/solicitar` | Disparo de e-mail com token temporário para o Master |
| `POST` | `/api/v1/auth/recuperar-senha/master/confirmar` | Validação do token recebido por e-mail e nova senha Master |
| `POST` | `/api/v1/auth/redefinir-senha/colaborador/confirmar` | Handshake Zero-Trust: CPF + `LIB-XXXX` + PIN + Nova Senha |
| `POST` | `/api/v1/terminais/{id}/usuarios` | Cadastro de colaborador no terminal (gera código `ATIV-XXXX`) |
| `GET` | `/api/v1/terminais/{id}/usuarios` | Listagem dos colaboradores associados ao terminal |
| `POST` | `/api/v1/terminais/{id}/usuarios/{uid}/autorizar-redefinicao` | Emissão presencial do código `LIB-XXXX` (válido por 15 min) |

---

## 🚀 Guia Passo a Passo: Configuração de Ambiente e Execução

### 1. Pré-requisitos
* **Python 3.11+** instalado (recomendado Python 3.12).
* **PostgreSQL** em execução localmente ou via container Docker (porta padrão: `5432` ou `5433`).
* Gerenciador de pacotes **pip** ou **uv**.

---

### 2. Criação e Ativação do Ambiente Virtual (venv)

Navegue até a pasta `backend/`:

#### No Windows (PowerShell):
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### No Linux / macOS (Bash/Zsh):
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Instalação das Dependências

Com o ambiente virtual ativado:
```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

> **Nota:** As dependências incluem `fastapi`, `uvicorn`, `sqlalchemy>=2.0`, `asyncpg`, `alembic`, `pydantic>=2.0`, `pydantic-settings`, `httpx`, `pytest` e `pytest-asyncio`.

---

### 4. Configuração das Variáveis de Ambiente (`.env`)

Crie o arquivo `.env` a partir do template `.env.example`:

#### Windows:
```powershell
Copy-Item .env.example .env
```

#### Linux / macOS:
```bash
cp .env.example .env
```

Abra o arquivo `.env` e confirme os dados de conexão do seu PostgreSQL local:
```ini
PROJECT_NAME="Elaion API"
API_V1_STR="/api/v1"

POSTGRES_SERVER=localhost
POSTGRES_PORT=5433
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=elaion_db

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/elaion_db
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

> **Atenção:** Certifique-se de ajustar `POSTGRES_PORT` (ex.: `5433`), usuário e senha para corresponder à sua instalação local do PostgreSQL.

---

### 5. Criação do Banco de Dados e Aplicação de Migrações (Alembic)

1. Certifique-se de que o banco `elaion_db` existe no seu servidor PostgreSQL. Se necessário, crie via SQL/psql/DBeaver/pgAdmin:
   ```sql
   CREATE DATABASE elaion_db;
   ```

2. Execute as migrações para criar as 24 tabelas do Elaion:
   ```bash
   alembic upgrade head
   ```

---

### 6. Inicialização do Servidor de Desenvolvimento

Inicie o servidor com *live reload*:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível nos seguintes endereços:
* **API Base / Health:** `http://localhost:8000/api/v1/health`
* **Swagger UI (Documentação Interativa):** `http://localhost:8000/api/v1/docs`
* **ReDoc (Documentação Alternativa):** `http://localhost:8000/api/v1/redoc`

---

### 7. Execução dos Testes Automatizados

Para rodar a suíte de testes assíncronos:
```bash
pytest
```

Para rodar com exibição detalhada:
```bash
pytest -v -s
```
