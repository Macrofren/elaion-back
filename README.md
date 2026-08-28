# Elaion Sirac - Backend API (FastAPI & Clean Architecture)

Este repositório contém a API RESTful do sistema **Elaion Sirac**, construída com **Python 3.11+**, **FastAPI**, **SQLAlchemy 2.0 (Async)** e **Clean Architecture** rigorosa.

---

## 🏛️ Arquitetura e Estrutura de Pastas

A aplicação segue uma separação rigorosa de camadas e fluxo de dependências de fora para dentro: `Routers` $\rightarrow$ `Services` $\rightarrow$ `Repositories` $\rightarrow$ `Models/Schemas`.

```text
backend/
├── app/
│   ├── api/
│   │   ├── deps.py                  # Injeção de dependências de sessão assíncrona do DB
│   │   ├── exceptions.py            # Handlers globais para captura de exceções de domínio
│   │   └── routers/
│   │       ├── api_v1.py            # Agregador principal de rotas v1
│   │       └── crud_router_factory.py # Factory genérica de endpoints CRUD
│   ├── core/
│   │   ├── config.py                # Configurações globais lidas do .env (Pydantic Settings)
│   │   └── security.py              # Middleware de CORS e utilitários de segurança
│   ├── domain/
│   │   ├── models.py                # Modelos ORM SQLAlchemy 2.0 (Declarative Base do Elaion Sirac)
│   │   └── schemas.py               # Schemas DTO Pydantic v2 (Request, Response, Update)
│   ├── services/
│   │   └── crud_service.py          # Camada de Serviço genérica para CRUD sem regras de negócio
│   ├── infra/
│   │   ├── database.py              # Configuração de AsyncEngine e async_sessionmaker
│   │   └── repositories/
│   │       └── base.py              # Repositório genérico de acesso a dados
│   └── main.py                      # Entrypoint limpo do FastAPI
├── tests/
│   ├── conftest.py                  # Fixtures Pytest (SQLite in-memory async, AsyncClient)
│   └── api/
│       └── test_crud.py             # Testes de integração de endpoints
├── pyproject.toml                  # Gerenciador de dependências (PEP 621) e Pytest
├── makeMer.py                      # Script de geração automatizada do diagrama MER em SVG/PNG
├── MER_ELAION_SIRAC.md             # Dicionário de Dados e especificações do MER
├── MER_ELAION_SIRAC.svg            # Diagrama MER em vetor SVG
└── .env.example                    # Modelo de variáveis de ambiente
```

---

## 🛠️ Entidades & Endpoints Mapeados (API v1)

Todos os recursos possuem endpoints completos de **Criar (`POST`)**, **Listar (`GET`)**, **Buscar por ID (`GET /{id}`)**, **Atualizar (`PUT /{id}`)** e **Deletar (`DELETE /{id}`)**:

| Recurso | Prefixo da Rota | Descrição |
| :--- | :--- | :--- |
| **Usuários** | `/api/v1/usuarios` | Colaboradores, operadores e químicos |
| **Terminais** | `/api/v1/terminais` | Terminais de operação e armazenagem |
| **Laboratórios** | `/api/v1/laboratorios` | Laboratórios físico-químicos por terminal |
| **Tanques** | `/api/v1/tanques` | Tanques receptores de combustível |
| **Congêneres** | `/api/v1/congeneres` | Distribuidoras e clientes |
| **Transportadoras** | `/api/v1/transportadoras` | Empresas de logística e transporte |
| **Produtos** | `/api/v1/produtos` | Catálogo de combustíveis e derivados |
| **Veículo-Produto** | `/api/v1/veiculo-produtos` | Tabela pivô de associação N:N |
| **Veículos** | `/api/v1/veiculos` | Registro e controle de caminhões-tanque |
| **Coletas de Amostra** | `/api/v1/coletas` | Lotes/sessões de amostragem por veículo |
| **Amostras** | `/api/v1/amostras` | Amostras colhidas por compartimento |
| **Análises de Amostra** | `/api/v1/analises` | Laudos e ensaios físico-químicos |
| **Comprovantes** | `/api/v1/comprovantes` | Certificados de análise e conferência volumétrica |
| **Comprovante Item** | `/api/v1/comprovante-itens` | Associação N:N entre comprovante e amostras |
| **Histórico Comprovante** | `/api/v1/historicos-comprovante` | Registro de auditoria de edições em comprovantes |
| **Histórico Veículo** | `/api/v1/historicos-veiculo` | Registro de auditoria de edições em veículos |
| **Histórico Amostra** | `/api/v1/historicos-amostra` | Registro de auditoria de edições em amostras |
| **Histórico Análise** | `/api/v1/historicos-analise` | Registro de auditoria de edições em laudos |

---

## 🚀 Como Executar o Projeto

### 1. Pré-requisitos
- Python 3.11+
- PostgreSQL (ou SQLite para desenvolvimento local rápida)

### 2. Instalação de Dependências
```bash
# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows

# Instalar dependências
pip install -e .[dev]
```

### 3. Configuração de Variáveis de Ambiente
Copie o arquivo `.env.example` para `.env` e ajuste as credenciais do seu banco de dados:
```bash
cp .env.example .env
```

### 4. Executar o Servidor de Desenvolvimento
```bash
uvicorn app.main:app --reload --port 8000
```
Acesse a documentação interativa no navegador:
- **Swagger UI:** `http://localhost:8000/api/v1/docs`
- **ReDoc:** `http://localhost:8000/api/v1/redoc`

### 5. Executar os Testes Automatizados
```bash
pytest
```
