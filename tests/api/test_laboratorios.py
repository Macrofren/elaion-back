"""Testes de integração para o CRUD e sincronização de Laboratórios do Terminal."""

import random
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import create_access_token
from app.domain.models import (
    ConviteCadastro,
    Laboratorio,
    ModuloAssinatura,
    Terminal,
    TerminalModuloContratado,
    UsuarioTerminal,
)
from app.domain.schemas import RegistrationPayload
from app.infra.database import AsyncSessionLocal
from app.services import cadastro_service


def _digitos(prefixo: str, n: int) -> str:
    r = random.randint(10**8, 10**9 - 1)
    base = f"{prefixo}{r}"
    return base[:n].ljust(n, "0")


def _registration_payload(codigo: str, master_cnpj: str) -> RegistrationPayload:
    uid = random.randint(10**8, 10**9 - 1)
    return RegistrationPayload.model_validate(
        {
            "codigo_ativacao": codigo,
            "organizacao": {
                "cnpj": _digitos("1", 14),
                "razao_social": "Org Teste SA",
                "nome_fantasia": "Org Teste",
                "inscricao_estadual": "240987654",
                "cep": "57000000",
                "uf": "AL",
                "cidade": "Maceió",
                "bairro": "Centro",
                "logradouro": "Av. Teste",
                "numero": "1",
                "complemento": None,
                "telefone": "82999990000",
                "email": f"org_{uid}@teste.com",
            },
            "terminal": {
                "razao_social": "Terminal Teste",
                "nome_fantasia": "Base Teste",
                "cnpj": _digitos("3", 14),
                "inscricao_estadual": "240987654",
                "cep": "57000000",
                "uf": "AL",
                "cidade": "Maceió",
                "bairro": "Centro",
                "logradouro": "Av. Teste",
                "numero": "1",
                "complemento": None,
                "telefone": "82999990000",
                "email": f"term_{uid}@teste.com",
                "telefone_financeiro": None,
                "email_financeiro": None,
            },
            "usuario_master": {"cnpj": master_cnpj, "senha": "SenhaForte@2026"},
        }
    )


@pytest_asyncio.fixture
async def tenant_lab():
    """Cria tenant isolado no banco para os testes de laboratório."""
    codigo = f"ELAION-LAB-{random.randint(10**6, 10**7 - 1)}"
    master_cnpj = _digitos("2", 14)
    async with AsyncSessionLocal() as s:
        s.add(ConviteCadastro(codigo=codigo, utilizado=False))
        await s.commit()
        organizacao = await cadastro_service.registrar(s, _registration_payload(codigo, master_cnpj))
        terminal = (
            await s.execute(select(Terminal).where(Terminal.organizacao_id == organizacao.id))
        ).scalar_one()
        sirac = (
            await s.execute(select(ModuloAssinatura).where(ModuloAssinatura.codigo == "SIRAC"))
        ).scalar_one()
        s.add(TerminalModuloContratado(terminal_id=terminal.id, modulo_id=sirac.id, ativo=True))
        await s.commit()

        master_id = (
            await s.execute(select(UsuarioTerminal.usuario_id).where(UsuarioTerminal.terminal_id == terminal.id))
        ).scalar_one()
        terminal_id = terminal.id
    return {"codigo": codigo, "master_cnpj": master_cnpj, "terminal_id": terminal_id, "master_id": master_id}


@pytest.mark.asyncio
async def test_listar_laboratorios_sem_terminal(client: AsyncClient):
    """Sem o header X-Terminal-ID ou token, deve retornar erro de autorização ou bad request."""
    res = await client.get("/api/v1/laboratorios")
    assert res.status_code in [400, 401, 403]


@pytest.mark.asyncio
async def test_cadastrar_laboratorio_sem_auth(client: AsyncClient):
    """Tentativa de cadastro sem autenticação deve retornar 401."""
    payload = {
        "nome": "Laboratório Central de Testes",
        "codigo": "LAB-01",
        "is_proprio": True,
        "ativo": True,
    }
    res = await client.post("/api/v1/laboratorios", json=payload)
    assert res.status_code in [401, 403]


@pytest.mark.asyncio
async def test_sincronizar_terminal_laboratorios_sem_auth(client: AsyncClient):
    """Tentativa de sincronização em lote sem credenciais deve ser negada."""
    payload = {
        "laboratorios": [
            {
                "nome": "Lab 1",
                "codigo": "L1",
                "is_proprio": True,
                "ativo": True,
            }
        ]
    }
    res = await client.put("/api/v1/terminal/laboratorios", json=payload)
    assert res.status_code in [401, 403]


@pytest.mark.asyncio
async def test_fluxo_laboratorio_completo_e2e(client: AsyncClient, tenant_lab):
    """
    Testa o fluxo ponta-a-ponta de Laboratórios:
    1. Listagem inicial (vazia)
    2. Cadastro de laboratório (POST /laboratorios)
    3. Listagem confirmando inserção (GET /laboratorios)
    4. Consulta por ID (GET /laboratorios/{id})
    5. Edição granular (PUT /laboratorios/{id})
    6. Sincronização em lote pelo Drawer (PUT /terminal/laboratorios)
    7. Desativação lógica (DELETE /laboratorios/{id})
    8. Filtro apenas ativos (GET /laboratorios?apenas_ativos=true)
    """
    tid = tenant_lab["terminal_id"]
    token = create_access_token({"sub": str(tenant_lab["master_id"]), "is_master": True})
    headers = {"Authorization": f"Bearer {token}", "X-Terminal-ID": str(tid)}

    # 1. Listagem inicial vazia
    res_list_init = await client.get("/api/v1/laboratorios", headers=headers)
    assert res_list_init.status_code == 200
    assert res_list_init.json() == []

    # 2. Cadastro de Laboratório
    payload_create = {
        "nome": "Laboratório de Controle de Qualidade",
        "codigo": "LAB-CQ-01",
        "is_proprio": True,
        "ativo": True,
    }
    res_create = await client.post("/api/v1/laboratorios", headers=headers, json=payload_create)
    assert res_create.status_code == 201, res_create.text
    lab_criado = res_create.json()
    assert lab_criado["id"] > 0
    assert lab_criado["nome"] == "Laboratório de Controle de Qualidade"
    assert lab_criado["codigo"] == "LAB-CQ-01"
    assert lab_criado["is_proprio"] is True
    assert lab_criado["ativo"] is True
    lab_id = lab_criado["id"]

    # 3. Listagem confirmando inserção
    res_list = await client.get("/api/v1/laboratorios", headers=headers)
    assert res_list.status_code == 200
    labs = res_list.json()
    assert len(labs) == 1
    assert labs[0]["id"] == lab_id

    # 4. Obter por ID
    res_get = await client.get(f"/api/v1/laboratorios/{lab_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["id"] == lab_id

    # 5. Edição granular
    payload_update = {
        "nome": "Laboratório CQ Modificado",
        "codigo": "LAB-CQ-02",
        "is_proprio": False,
        "ativo": True,
    }
    res_update = await client.put(f"/api/v1/laboratorios/{lab_id}", headers=headers, json=payload_update)
    assert res_update.status_code == 200
    lab_atualizado = res_update.json()
    assert lab_atualizado["nome"] == "Laboratório CQ Modificado"
    assert lab_atualizado["codigo"] == "LAB-CQ-02"
    assert lab_atualizado["is_proprio"] is False

    # 6. Sincronização em Lote (PUT /terminal/laboratorios)
    # Atualiza o existente e cadastra um novo na mesma requisição
    payload_batch = {
        "laboratorios": [
            {
                "id": lab_id,
                "nome": "Laboratório CQ Final",
                "codigo": "LAB-CQ-FINAL",
                "is_proprio": True,
                "ativo": True,
            },
            {
                "nome": "Laboratório Terceirizado SGS",
                "codigo": "LAB-SGS",
                "is_proprio": False,
                "ativo": True,
            },
        ]
    }
    res_batch = await client.put("/api/v1/terminal/laboratorios", headers=headers, json=payload_batch)
    assert res_batch.status_code == 200, res_batch.text
    labs_batch = res_batch.json()
    assert len(labs_batch) == 2
    nomes = [l["nome"] for l in labs_batch]
    assert "Laboratório CQ Final" in nomes
    assert "Laboratório Terceirizado SGS" in nomes

    # 7. Desativação Lógica
    res_delete = await client.delete(f"/api/v1/laboratorios/{lab_id}", headers=headers)
    assert res_delete.status_code == 200
    assert res_delete.json()["ativo"] is False

    # 8. Listar apenas ativos
    res_ativos = await client.get("/api/v1/laboratorios?apenas_ativos=true", headers=headers)
    assert res_ativos.status_code == 200
    labs_ativos = res_ativos.json()
    assert len(labs_ativos) == 1
    assert labs_ativos[0]["nome"] == "Laboratório Terceirizado SGS"

    # 9. Verificação de persistência REAL no banco de dados através de uma sessão independente
    async with AsyncSessionLocal() as s_independente:
        res_db = await s_independente.execute(
            select(Laboratorio).where(Laboratorio.terminal_id == tid)
        )
        labs_db = res_db.scalars().all()
        assert len(labs_db) == 2, "Os laboratórios devem estar fisicamente persistidos no PostgreSQL."
        nomes_db = {l.nome for l in labs_db}
        assert "Laboratório CQ Final" in nomes_db
        assert "Laboratório Terceirizado SGS" in nomes_db

