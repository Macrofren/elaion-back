"""
Testes de integração das rotas implementadas (contra o PostgreSQL real).

Cada teste cria seu próprio tenant isolado (convite + organização + terminal +
master) com dados únicos, exercitando o fluxo ponta-a-ponta sem depender de dados
pré-existentes nem de respostas mocadas.
"""

import random

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select

from app.core.cache import permissoes_cache
from app.core.security import create_access_token
from app.domain.models import (
    ConviteCadastro,
    ModuloAssinatura,
    Terminal,
    TerminalModuloContratado,
)
from app.domain.schemas import RegistrationPayload
from app.infra.database import AsyncSessionLocal
from app.services import cadastro_service

SENHA_MASTER = "SenhaForte@2026"


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
                "cnpj": _digitos("1", 14), "razao_social": "Org Teste SA", "nome_fantasia": "Org Teste",
                "inscricao_estadual": "240987654", "cep": "57000000", "uf": "AL", "cidade": "Maceió",
                "bairro": "Centro", "logradouro": "Av. Teste", "numero": "1", "complemento": None,
                "telefone": "82999990000", "email": f"org_{uid}@teste.com",
            },
            "terminal": {
                "razao_social": "Terminal Teste", "nome_fantasia": "Base Teste", "cnpj": _digitos("3", 14),
                "inscricao_estadual": "240987654", "cep": "57000000", "uf": "AL", "cidade": "Maceió",
                "bairro": "Centro", "logradouro": "Av. Teste", "numero": "1", "complemento": None,
                "telefone": "82999990000", "email": f"term_{uid}@teste.com", "telefone_financeiro": None,
                "email_financeiro": None,
            },
            "usuario_master": {"cnpj": master_cnpj, "senha": SENHA_MASTER},
        }
    )


@pytest_asyncio.fixture
async def tenant():
    """Cria convite + org + terminal + master (com módulo SIRAC contratado)."""
    codigo = f"ELAION-IT-{random.randint(10**6, 10**7 - 1)}"
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
        from app.domain.models import UsuarioTerminal

        master_id = (
            await s.execute(select(UsuarioTerminal.usuario_id).where(UsuarioTerminal.terminal_id == terminal.id))
        ).scalar_one()
        terminal_id = terminal.id
    return {"codigo": codigo, "master_cnpj": master_cnpj, "terminal_id": terminal_id, "master_id": master_id}


@pytest.mark.asyncio
async def test_validar_codigo(client: AsyncClient):
    codigo = f"ELAION-VC-{random.randint(10**6, 10**7 - 1)}"
    async with AsyncSessionLocal() as s:
        s.add(ConviteCadastro(codigo=codigo, utilizado=False))
        await s.commit()

    assert (await client.post("/api/v1/cadastro/validar-codigo", json={"codigo": codigo})).status_code == 200
    assert (await client.post("/api/v1/cadastro/validar-codigo", json={"codigo": "NAO-EXISTE-XYZ"})).status_code == 400


@pytest.mark.asyncio
async def test_registrar_consome_convite(client: AsyncClient):
    codigo = f"ELAION-RG-{random.randint(10**6, 10**7 - 1)}"
    async with AsyncSessionLocal() as s:
        s.add(ConviteCadastro(codigo=codigo, utilizado=False))
        await s.commit()

    payload = _registration_payload(codigo, _digitos("2", 14)).model_dump()
    res = await client.post("/api/v1/cadastro/registrar", json=payload)
    assert res.status_code == 201, res.text
    assert "id" in res.json()
    # Convite consumido -> nova validação falha
    assert (await client.post("/api/v1/cadastro/validar-codigo", json={"codigo": codigo})).status_code == 400


@pytest.mark.asyncio
async def test_login_master_por_cnpj_e_me(client: AsyncClient, tenant):
    res = await client.post(
        "/api/v1/auth/login", json={"identificador": tenant["master_cnpj"], "senha": SENHA_MASTER}
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["token_type"] == "bearer"
    assert data["usuario"]["is_master"] is True
    assert "refresh_token" in res.cookies

    # senha incorreta -> 401
    res_bad = await client.post(
        "/api/v1/auth/login", json={"identificador": tenant["master_cnpj"], "senha": "errada123"}
    )
    assert res_bad.status_code == 401

    # /me com o token emitido
    token = data["access_token"]
    res_me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["is_master"] is True


@pytest.mark.asyncio
async def test_login_por_email_bloqueado(client: AsyncClient, tenant):
    res = await client.post(
        "/api/v1/auth/login", json={"identificador": "term@teste.com", "senha": SENHA_MASTER}
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_fluxo_colaborador_completo(client: AsyncClient, tenant):
    tid = tenant["terminal_id"]
    master_token = create_access_token({"sub": str(tenant["master_id"]), "is_master": True})
    headers = {"Authorization": f"Bearer {master_token}", "X-Terminal-ID": str(tid)}

    # Catálogo de permissões
    res_cat = await client.get(f"/api/v1/terminais/{tid}/usuarios/permissoes-disponiveis", headers=headers)
    assert res_cat.status_code == 200
    assert res_cat.json()[0]["codigo_modulo"] == "SIRAC"

    # Criar colaborador
    cpf = _digitos("9", 11)
    res_create = await client.post(
        f"/api/v1/terminais/{tid}/usuarios",
        headers=headers,
        json={
            "nome": "Sebastião", "sobrenome": "Ferreira", "cpf": cpf, "papel": "Operador",
            "permissoes": ["sirac:config:usuarios:visualizar"],
        },
    )
    assert res_create.status_code == 201, res_create.text
    ativ = res_create.json()["codigo_ativacao"]
    colab_id = res_create.json()["usuario_id"]
    assert ativ.startswith("ATIV-")

    # Listagem inclui master + colaborador
    res_list = await client.get(f"/api/v1/terminais/{tid}/usuarios", headers=headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 2

    # Primeiro acesso
    assert (
        await client.post(
            "/api/v1/auth/primeiro-acesso/validar", json={"cpf": cpf, "codigo_ativacao": ativ}
        )
    ).status_code == 200

    senha_colab = "NovaSenhaSegura@2026"
    res_conc = await client.post(
        "/api/v1/auth/primeiro-acesso/concluir",
        json={
            "cpf": cpf, "codigo_ativacao": ativ, "nova_senha": senha_colab,
            "confirmacao_senha": senha_colab, "pin_seguranca": "4912",
        },
    )
    assert res_conc.status_code == 200 and res_conc.json()["sucesso"] is True

    # Login do colaborador por CPF
    res_login = await client.post(
        "/api/v1/auth/login", json={"identificador": cpf, "senha": senha_colab}
    )
    assert res_login.status_code == 200
    assert res_login.json()["usuario"]["is_master"] is False

    # Autorizar redefinição (gera LIB)
    res_lib = await client.post(
        f"/api/v1/terminais/{tid}/usuarios/{colab_id}/autorizar-redefinicao", headers=headers
    )
    assert res_lib.status_code == 200
    assert res_lib.json()["codigo_liberacao"].startswith("LIB-")


@pytest.mark.asyncio
async def test_rbac_permissao_cache_e_bloqueio(client: AsyncClient, tenant):
    """Colaborador sem permissão é barrado (403); com permissão em cache acessa (200)."""
    tid = tenant["terminal_id"]

    # Cria um colaborador ativo diretamente para obter um id real vinculado ao terminal
    cpf = _digitos("8", 11)
    master_token = create_access_token({"sub": str(tenant["master_id"]), "is_master": True})
    headers_master = {"Authorization": f"Bearer {master_token}", "X-Terminal-ID": str(tid)}
    res_create = await client.post(
        f"/api/v1/terminais/{tid}/usuarios",
        headers=headers_master,
        json={"nome": "Sem", "sobrenome": "Permissao", "cpf": cpf, "papel": "Operador", "permissoes": []},
    )
    colab_id = res_create.json()["usuario_id"]

    # Ativa o colaborador para poder autenticar
    from app.domain.models import Usuario

    async with AsyncSessionLocal() as s:
        u = (await s.execute(select(Usuario).where(Usuario.id == colab_id))).scalar_one()
        u.status_conta = "ATIVO"
        await s.commit()

    colab_token = create_access_token({"sub": str(colab_id), "is_master": False})
    headers = {"Authorization": f"Bearer {colab_token}", "X-Terminal-ID": str(tid)}

    await permissoes_cache.clear()
    res_sem = await client.get(f"/api/v1/terminais/{tid}/usuarios", headers=headers)
    assert res_sem.status_code == 403
    assert "Acesso negado" in res_sem.json()["detail"]

    await permissoes_cache.set(f"permissoes:{colab_id}:{tid}", {"sirac:config:usuarios:visualizar"})
    res_com = await client.get(f"/api/v1/terminais/{tid}/usuarios", headers=headers)
    assert res_com.status_code == 200

    await permissoes_cache.delete(f"permissoes:{colab_id}:{tid}")
    res_pos = await client.get(f"/api/v1/terminais/{tid}/usuarios", headers=headers)
    assert res_pos.status_code == 403
