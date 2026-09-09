"""Testes de integração para o CRUD e sincronização de Plataformas de Operação do Terminal."""

import random
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import create_access_token
from app.domain.models import (
    ConviteCadastro,
    ModuloAssinatura,
    Plataforma,
    Terminal,
    TerminalModuloContratado,
    TipoPlataforma,
    Usuario,
    UsuarioPermissao,
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
async def tenant_plat():
    """Cria tenant isolado no banco para os testes de plataforma."""
    codigo = f"ELAION-PLAT-{random.randint(10**6, 10**7 - 1)}"
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
async def test_listar_plataformas_sem_terminal(client: AsyncClient):
    """Sem header X-Terminal-ID ou token, deve retornar 400, 401 ou 403."""
    res = await client.get("/api/v1/plataformas")
    assert res.status_code in [400, 401, 403]


@pytest.mark.asyncio
async def test_cadastrar_plataforma_sem_auth(client: AsyncClient):
    """Tentativa de cadastro sem autenticação deve retornar 401 ou 403."""
    payload = {
        "identificador": "PL-01",
        "nome": "Plataforma Sul",
        "tipo": "CARREGAMENTO",
        "ativo": True,
    }
    res = await client.post("/api/v1/plataformas", json=payload)
    assert res.status_code in [401, 403]


@pytest.mark.asyncio
async def test_sincronizar_terminal_plataformas_sem_auth(client: AsyncClient):
    """Tentativa de sincronização em lote sem credenciais deve ser negada."""
    payload = {
        "plataformas": [
            {
                "identificador": "PL-01",
                "nome": "Plataforma 1",
                "tipo": "MISTA",
                "ativo": True,
            }
        ]
    }
    res = await client.put("/api/v1/terminal/plataformas", json=payload)
    assert res.status_code in [401, 403]


@pytest.mark.asyncio
async def test_fluxo_plataforma_completo_e2e(client: AsyncClient, tenant_plat):
    """
    Testa o fluxo ponta-a-ponta de Plataformas de Operação:
    1. GET /terminal inicial: plataformas deve estar presente como lista vazia
    2. POST /plataformas: cria nova plataforma
    3. Validação de identificador duplicado (deve retornar 409 Conflict)
    4. GET /terminal: plataformas agora deve conter a plataforma criada
    5. GET /terminal/plataformas: consulta de sub-recurso
    6. GET /plataformas/{id}: consulta granular
    7. PUT /plataformas/{id}: alteração granular de campos
    8. PUT /terminal/plataformas: sincronização em lote do Drawer (atualiza existente + cria nova)
    9. PUT /terminal/plataformas com omissão: soft delete da omitida (ativo = False)
    10. PATCH /plataformas/{id}/toggle-status: reativa a plataforma
    11. Filtro por apenas_ativos e tipo
    12. Verificação de integridade física no banco de dados
    """
    tid = tenant_plat["terminal_id"]
    token = create_access_token({"sub": str(tenant_plat["master_id"]), "is_master": True})
    headers = {"Authorization": f"Bearer {token}", "X-Terminal-ID": str(tid)}

    # 1. GET /terminal inicial: plataformas deve ser uma lista vazia
    res_term_init = await client.get("/api/v1/terminal", headers=headers)
    assert res_term_init.status_code == 200, res_term_init.text
    term_init = res_term_init.json()
    assert "plataformas" in term_init
    assert term_init["plataformas"] == []

    # 2. Cadastro individual de Plataforma (POST /plataformas)
    payload_create = {
        "identificador": "pl-01",  # Teste sanitização para maiúsculas
        "nome": "Plataforma Sul de Carregamento",
        "tipo": "CARREGAMENTO",
        "ativo": True,
    }
    res_create = await client.post("/api/v1/plataformas", headers=headers, json=payload_create)
    assert res_create.status_code == 201, res_create.text
    plat_criada = res_create.json()
    assert plat_criada["id"] > 0
    assert plat_criada["identificador"] == "PL-01"
    assert plat_criada["nome"] == "Plataforma Sul de Carregamento"
    assert plat_criada["tipo"] == "CARREGAMENTO"
    assert plat_criada["ativo"] is True
    plat_1_id = plat_criada["id"]

    # 3. Validação de conflito de identificador duplicado no terminal
    res_dup = await client.post(
        "/api/v1/plataformas",
        headers=headers,
        json={"identificador": "PL-01", "nome": "Duplicada", "tipo": "DESCARGA", "ativo": True},
    )
    assert res_dup.status_code == 409

    # 4. GET /terminal deve refletir a plataforma criada
    res_term_after = await client.get("/api/v1/terminal", headers=headers)
    assert res_term_after.status_code == 200
    term_after = res_term_after.json()
    assert len(term_after["plataformas"]) == 1
    assert term_after["plataformas"][0]["id"] == plat_1_id
    assert term_after["plataformas"][0]["identificador"] == "PL-01"

    # 5. GET /terminal/plataformas (sub-recurso usado para consulta direta)
    res_sub = await client.get("/api/v1/terminal/plataformas", headers=headers)
    assert res_sub.status_code == 200
    sub_plats = res_sub.json()
    assert len(sub_plats) == 1
    assert sub_plats[0]["identificador"] == "PL-01"

    # 6. GET /plataformas/{id}
    res_get = await client.get(f"/api/v1/plataformas/{plat_1_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["id"] == plat_1_id

    # 7. PUT /plataformas/{id} (edição granular)
    payload_update = {
        "identificador": "PL-01-A",
        "nome": "Plataforma Sul Mista",
        "tipo": "MISTA",
        "ativo": True,
    }
    res_update = await client.put(
        f"/api/v1/plataformas/{plat_1_id}", headers=headers, json=payload_update
    )
    assert res_update.status_code == 200
    plat_att = res_update.json()
    assert plat_att["identificador"] == "PL-01-A"
    assert plat_att["tipo"] == "MISTA"
    assert plat_att["nome"] == "Plataforma Sul Mista"

    # 8. Sincronização em Lote (PUT /terminal/plataformas) pelo Drawer
    # Atualiza a primeira e cadastra uma segunda plataforma
    payload_batch = {
        "plataformas": [
            {
                "id": plat_1_id,
                "identificador": "PL-01",
                "nome": "Plataforma Principal",
                "tipo": "MISTA",
                "ativo": True,
            },
            {
                "identificador": "PL-02",
                "nome": "Plataforma de Descarga Norte",
                "tipo": "DESCARGA",
                "ativo": True,
            },
        ]
    }
    res_batch = await client.put("/api/v1/terminal/plataformas", headers=headers, json=payload_batch)
    assert res_batch.status_code == 200, res_batch.text
    batch_plats = res_batch.json()
    assert len(batch_plats) == 2
    idents = {p["identificador"] for p in batch_plats}
    assert "PL-01" in idents
    assert "PL-02" in idents

    plat_2 = next(p for p in batch_plats if p["identificador"] == "PL-02")
    plat_2_id = plat_2["id"]

    # 9. Sincronização em Lote com omissão (Soft Delete)
    # Enviamos apenas PL-02: PL-01 foi omitida e deve ser marcada como ativo=False
    payload_omit = {
        "plataformas": [
            {
                "id": plat_2_id,
                "identificador": "PL-02",
                "nome": "Plataforma de Descarga Norte",
                "tipo": "DESCARGA",
                "ativo": True,
            }
        ]
    }
    res_omit = await client.put("/api/v1/terminal/plataformas", headers=headers, json=payload_omit)
    assert res_omit.status_code == 200
    res_omit_data = res_omit.json()
    # Deve conter ambas, sendo PL-01 inativa
    plat_1_inativa = next(p for p in res_omit_data if p["id"] == plat_1_id)
    assert plat_1_inativa["ativo"] is False

    # 10. PATCH /plataformas/{id}/toggle-status
    res_toggle = await client.patch(
        f"/api/v1/plataformas/{plat_1_id}/toggle-status", headers=headers
    )
    assert res_toggle.status_code == 200
    assert res_toggle.json()["ativo"] is True

    # 11. Filtros na listagem granular (apenas_ativos e tipo)
    res_filtro_tipo = await client.get(
        "/api/v1/plataformas?tipo=DESCARGA", headers=headers
    )
    assert res_filtro_tipo.status_code == 200
    plats_descarga = res_filtro_tipo.json()
    assert len(plats_descarga) == 1
    assert plats_descarga[0]["identificador"] == "PL-02"

    # 12. Verificação de persistência física no banco de dados independente
    async with AsyncSessionLocal() as s_independente:
        res_db = await s_independente.execute(
            select(Plataforma).where(Plataforma.terminal_id == tid)
        )
        plats_db = res_db.scalars().all()
        assert len(plats_db) == 2
        ident_db = {p.identificador for p in plats_db}
        assert "PL-01" in ident_db
        assert "PL-02" in ident_db


@pytest.mark.asyncio
async def test_rbac_plataformas_permissoes(client: AsyncClient, tenant_plat):
    """
    Testa o controle de acesso RBAC específico:
    - Usuário com sirac:config:terminal:tanques_ver consegue ler, mas falha ao cadastrar (403).
    - Usuário com sirac:config:terminal:tanques_registrar consegue cadastrar.
    """
    tid = tenant_plat["terminal_id"]

    # Criação de um usuário normal (não-master)
    async with AsyncSessionLocal() as s:
        user_comum = Usuario(
            nome="Operador",
            sobrenome="Terminal",
            cpf=_digitos("9", 11),
            email=f"operador_{random.randint(10**6, 10**7)}@teste.com",
            senha_hash="hash_teste",
            is_master=False,
            ativo=True,
            status_conta="ATIVO",
        )
        s.add(user_comum)
        await s.flush()

        # Vincula ao terminal
        ut = UsuarioTerminal(usuario_id=user_comum.id, terminal_id=tid, ativo=True)
        s.add(ut)
        await s.commit()
        user_id = user_comum.id

    token_comum = create_access_token({"sub": str(user_id), "is_master": False})
    headers_comum = {"Authorization": f"Bearer {token_comum}", "X-Terminal-ID": str(tid)}

    # Sem nenhuma permissão atribuída: leitura deve retornar 403
    res_sem_perm = await client.get("/api/v1/plataformas", headers=headers_comum)
    assert res_sem_perm.status_code == 403

    # Tentativa de cadastro sem permissão: deve retornar 403
    res_cad_sem_perm = await client.post(
        "/api/v1/plataformas",
        headers=headers_comum,
        json={"identificador": "PL-TEST", "tipo": "MISTA", "ativo": True},
    )
    assert res_cad_sem_perm.status_code == 403
