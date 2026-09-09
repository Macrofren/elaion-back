"""Testes de integração para o CRUD e sincronização de Bicos de Operação do Terminal."""

from decimal import Decimal
import random
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import create_access_token
from app.domain.models import (
    CategoriaProduto,
    ConviteCadastro,
    ModuloAssinatura,
    Plataforma,
    Produto,
    Tanque,
    Terminal,
    TerminalModuloContratado,
    TipoPlataforma,
    Usuario,
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
async def tenant_bicos():
    """Cria tenant com terminal, plataforma, produtos e tanques para os testes de bicos."""
    codigo = f"ELAION-BICOS-{random.randint(10**6, 10**7 - 1)}"
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

        # 1. Plataforma de teste
        plat = Plataforma(
            terminal_id=terminal.id,
            identificador="PL-01",
            nome="Plataforma Sul Mista",
            tipo=TipoPlataforma.MISTA,
            ativo=True,
        )
        plat_carr = Plataforma(
            terminal_id=terminal.id,
            identificador="PL-02",
            nome="Plataforma Norte Carregamento",
            tipo=TipoPlataforma.CARREGAMENTO,
            ativo=True,
        )
        s.add(plat)
        s.add(plat_carr)

        # 2. Dois produtos no catálogo
        uid = random.randint(10**5, 10**6 - 1)
        prod_diesel = Produto(
            codigo_anp=f"ANP-DSL-{uid}",
            nome=f"Diesel S10 A Teste {uid}",
            categoria=CategoriaProduto.DIESEL,
            unidade_medida="L",
        )
        prod_gasolina = Produto(
            codigo_anp=f"ANP-GAS-{uid}",
            nome=f"Gasolina Comum Teste {uid}",
            categoria=CategoriaProduto.GASOLINA,
            unidade_medida="L",
        )
        s.add(prod_diesel)
        s.add(prod_gasolina)
        await s.flush()

        # 3. Dois tanques: um de diesel e um de gasolina
        tq_diesel = Tanque(
            terminal_id=terminal.id,
            produto_id=prod_diesel.id,
            identificador_tanque="TQ-DSL-01",
            capacidade_nominal_litros=Decimal("50000.00"),
            capacidade_operacional_litros=Decimal("45000.00"),
            volume_atual_litros=Decimal("10000.00"),
            ativo=True,
        )
        tq_gasolina = Tanque(
            terminal_id=terminal.id,
            produto_id=prod_gasolina.id,
            identificador_tanque="TQ-GAS-01",
            capacidade_nominal_litros=Decimal("60000.00"),
            capacidade_operacional_litros=Decimal("55000.00"),
            volume_atual_litros=Decimal("15000.00"),
            ativo=True,
        )
        s.add(tq_diesel)
        s.add(tq_gasolina)

        await s.commit()

        master_id = (
            await s.execute(select(UsuarioTerminal.usuario_id).where(UsuarioTerminal.terminal_id == terminal.id))
        ).scalar_one()

        data = {
            "terminal_id": terminal.id,
            "master_id": master_id,
            "plataforma_id": plat.id,
            "plataforma_carr_id": plat_carr.id,
            "prod_diesel_id": prod_diesel.id,
            "prod_diesel_nome": prod_diesel.nome,
            "prod_gasolina_id": prod_gasolina.id,
            "prod_gasolina_nome": prod_gasolina.nome,
            "tq_diesel_id": tq_diesel.id,
            "tq_diesel_ident": tq_diesel.identificador_tanque,
            "tq_gasolina_id": tq_gasolina.id,
            "tq_gasolina_ident": tq_gasolina.identificador_tanque,
        }
    return data


@pytest.mark.asyncio
async def test_listar_bicos_sem_terminal(client: AsyncClient):
    """Sem header X-Terminal-ID ou token, deve retornar erro."""
    res = await client.get("/api/v1/bicos")
    assert res.status_code in [400, 401, 403]


@pytest.mark.asyncio
async def test_cadastrar_bico_sem_auth(client: AsyncClient):
    """Tentativa de cadastro sem autenticação deve retornar 401 ou 403."""
    res = await client.post("/api/v1/bicos", json={"identificador_bico": "BC-01"})
    assert res.status_code in [401, 403]


@pytest.mark.asyncio
async def test_sincronizar_terminal_bicos_sem_auth(client: AsyncClient):
    """Tentativa de sincronização em lote sem credenciais deve ser negada."""
    res = await client.put("/api/v1/terminal/bicos", json={"bicos": []})
    assert res.status_code in [401, 403]


@pytest.mark.asyncio
async def test_fluxo_bicos_completo_e2e(client: AsyncClient, tenant_bicos):
    """
    Testa o fluxo ponta-a-ponta de Bicos de Conexão:
    1. GET /terminal: bicos inicialmente vazio
    2. Validação: ao menos 1 tanque é obrigatório (tanque_ids = [] -> erro 400 ou 422)
    3. Validação: incompatibilidade de combustível (bico diesel com tanque de gasolina -> erro 400)
    4. POST /bicos: cadastro válido de bico com tanque de combustível compatível
    5. Validação: duplicidade de identificador (409 Conflict)
    6. GET /terminal: bicos agora contém o novo bico e dados completos (plataforma, produto, tanques)
    7. GET /terminal/bicos: sub-recurso
    8. GET /bicos/{id}
    9. PUT /bicos/{id}: edição granular
    10. PUT /terminal/bicos: sincronização em lote do Drawer (atualiza existente + cria novo)
    11. PUT /terminal/bicos: omissão no lote gera soft delete (ativo = False)
    12. PATCH /bicos/{id}/toggle-status: reativação
    13. Filtros na listagem granular
    """
    tid = tenant_bicos["terminal_id"]
    plat_id = tenant_bicos["plataforma_id"]
    plat_carr_id = tenant_bicos["plataforma_carr_id"]
    diesel_id = tenant_bicos["prod_diesel_id"]
    gasolina_id = tenant_bicos["prod_gasolina_id"]
    tq_diesel_id = tenant_bicos["tq_diesel_id"]
    tq_gasolina_id = tenant_bicos["tq_gasolina_id"]

    token = create_access_token({"sub": str(tenant_bicos["master_id"]), "is_master": True})
    headers = {"Authorization": f"Bearer {token}", "X-Terminal-ID": str(tid)}

    # 1. GET /terminal inicial: bicos deve ser uma lista vazia
    res_term_init = await client.get("/api/v1/terminal", headers=headers)
    assert res_term_init.status_code == 200
    assert "bicos" in res_term_init.json()
    assert res_term_init.json()["bicos"] == []

    # 2. Validação: tanque_ids vazio deve ser rejeitado (ao menos 1 tanque obrigatório)
    res_vazio = await client.post(
        "/api/v1/bicos",
        headers=headers,
        json={
            "identificador_bico": "BC-01",
            "plataforma_id": plat_id,
            "tipo_operacao": "CARREGAMENTO",
            "tanque_ids": [],
            "ativo": True,
        },
    )
    assert res_vazio.status_code in [400, 422]

    # 3. Validação: incompatibilidade plataforma x operação (Bico DESCARGA em plataforma de CARREGAMENTO)
    res_incompativel = await client.post(
        "/api/v1/bicos",
        headers=headers,
        json={
            "identificador_bico": "BC-01",
            "plataforma_id": plat_carr_id,
            "tipo_operacao": "DESCARGA",
            "tanque_ids": [tq_gasolina_id],
            "ativo": True,
        },
    )
    assert res_incompativel.status_code == 400
    assert "exclusivamente CARREGAMENTO" in res_incompativel.json()["detail"]

    # 4. Cadastro válido de bico com múltiplos tanques de produtos distintos (POST /bicos)
    res_create = await client.post(
        "/api/v1/bicos",
        headers=headers,
        json={
            "identificador_bico": "bc-01",  # Sanitização para maiúsculas
            "plataforma_id": plat_id,
            "tipo_operacao": "CARREGAMENTO",
            "tanque_ids": [tq_diesel_id, tq_gasolina_id],
            "ativo": True,
        },
    )
    assert res_create.status_code == 201, res_create.text
    bico_1 = res_create.json()
    assert bico_1["id"] > 0
    assert bico_1["identificador_bico"] == "BC-01"
    assert bico_1["plataforma_identificador"] == "PL-01"
    assert bico_1["tipo_operacao"] == "CARREGAMENTO"
    assert set(bico_1["tanque_ids"]) == {tq_diesel_id, tq_gasolina_id}
    assert bico_1["ativo"] is True
    bico_1_id = bico_1["id"]

    # 5. Validação de conflito de identificador duplicado no terminal
    res_dup = await client.post(
        "/api/v1/bicos",
        headers=headers,
        json={
            "identificador_bico": "BC-01",
            "plataforma_id": plat_id,
            "tipo_operacao": "CARREGAMENTO",
            "tanque_ids": [tq_diesel_id],
            "ativo": True,
        },
    )
    assert res_dup.status_code == 409

    # 6. GET /terminal deve refletir o bico criado
    res_term = await client.get("/api/v1/terminal", headers=headers)
    assert res_term.status_code == 200
    bicos_terminal = res_term.json()["bicos"]
    assert len(bicos_terminal) == 1
    assert bicos_terminal[0]["id"] == bico_1_id
    assert bicos_terminal[0]["identificador_bico"] == "BC-01"
    assert bicos_terminal[0]["plataforma_identificador"] == "PL-01"
    assert bicos_terminal[0]["tipo_operacao"] == "CARREGAMENTO"
    assert len(bicos_terminal[0]["tanques_identificadores"]) == 2

    # 7. GET /terminal/bicos (sub-recurso)
    res_sub = await client.get("/api/v1/terminal/bicos", headers=headers)
    assert res_sub.status_code == 200
    assert len(res_sub.json()) == 1
    assert res_sub.json()[0]["id"] == bico_1_id

    # 8. GET /bicos/{id}
    res_get = await client.get(f"/api/v1/bicos/{bico_1_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["id"] == bico_1_id

    # 9. PUT /bicos/{id} (edição granular)
    res_put = await client.put(
        f"/api/v1/bicos/{bico_1_id}",
        headers=headers,
        json={"identificador_bico": "BC-01-EXP", "tipo_operacao": "DESCARGA"},
    )
    assert res_put.status_code == 200
    assert res_put.json()["identificador_bico"] == "BC-01-EXP"
    assert res_put.json()["tipo_operacao"] == "DESCARGA"

    # 10. PUT /terminal/bicos (Sincronização em Lote pelo Drawer)
    # Atualiza o primeiro bico e adiciona o segundo bico
    payload_batch = {
        "bicos": [
            {
                "id": bico_1_id,
                "identificador_bico": "BC-01",
                "plataforma_id": plat_id,
                "tipo_operacao": "CARREGAMENTO",
                "tanque_ids": [tq_diesel_id],
                "ativo": True,
            },
            {
                "identificador_bico": "BC-02",
                "plataforma_id": plat_id,
                "tipo_operacao": "DESCARGA",
                "tanque_ids": [tq_gasolina_id],
                "ativo": True,
            },
        ]
    }
    res_batch = await client.put("/api/v1/terminal/bicos", headers=headers, json=payload_batch)
    assert res_batch.status_code == 200, res_batch.text
    bicos_batch = res_batch.json()
    assert len(bicos_batch) == 2
    idents = {b["identificador_bico"] for b in bicos_batch}
    assert "BC-01" in idents
    assert "BC-02" in idents

    bico_2 = next(b for b in bicos_batch if b["identificador_bico"] == "BC-02")
    bico_2_id = bico_2["id"]
    assert bico_2["tanques_identificadores"] == [tenant_bicos["tq_gasolina_ident"]]
    assert bico_2["tipo_operacao"] == "DESCARGA"

    # 11. Sincronização em Lote com Omissão (Soft Delete)
    # Enviamos apenas BC-02: BC-01 foi omitido e deve ser marcado como ativo=False
    payload_omit = {
        "bicos": [
            {
                "id": bico_2_id,
                "identificador_bico": "BC-02",
                "plataforma_id": plat_id,
                "tipo_operacao": "DESCARGA",
                "tanque_ids": [tq_gasolina_id],
                "ativo": True,
            }
        ]
    }
    res_omit = await client.put("/api/v1/terminal/bicos", headers=headers, json=payload_omit)
    assert res_omit.status_code == 200
    bicos_apos_omit = res_omit.json()
    bico_1_inativo = next(b for b in bicos_apos_omit if b["id"] == bico_1_id)
    assert bico_1_inativo["ativo"] is False

    # 12. Reativação via PATCH /bicos/{id}/toggle-status
    res_toggle = await client.patch(f"/api/v1/bicos/{bico_1_id}/toggle-status", headers=headers)
    assert res_toggle.status_code == 200
    assert res_toggle.json()["ativo"] is True

    # 13. Filtros granulares por tipo_operacao e status ativo
    res_filtro = await client.get(
        "/api/v1/bicos?tipo_operacao=DESCARGA&apenas_ativos=true",
        headers=headers,
    )
    assert res_filtro.status_code == 200
    filtrados = res_filtro.json()
    assert len(filtrados) == 1
    assert filtrados[0]["identificador_bico"] == "BC-02"
    assert filtrados[0]["tipo_operacao"] == "DESCARGA"


@pytest.mark.asyncio
async def test_rbac_bicos_permissoes(client: AsyncClient, tenant_bicos):
    """Testa bloqueio de acesso 403 para usuário sem permissão RBAC."""
    tid = tenant_bicos["terminal_id"]

    async with AsyncSessionLocal() as s:
        user_sem_perm = Usuario(
            nome="Colaborador",
            sobrenome="SemPerm",
            cpf=_digitos("8", 11),
            email=f"semperm_{random.randint(10**6, 10**7)}@teste.com",
            senha_hash="hash_teste",
            is_master=False,
            ativo=True,
            status_conta="ATIVO",
        )
        s.add(user_sem_perm)
        await s.flush()
        ut = UsuarioTerminal(usuario_id=user_sem_perm.id, terminal_id=tid, ativo=True)
        s.add(ut)
        await s.commit()
        user_id = user_sem_perm.id

    token = create_access_token({"sub": str(user_id), "is_master": False})
    headers = {"Authorization": f"Bearer {token}", "X-Terminal-ID": str(tid)}

    res_get = await client.get("/api/v1/bicos", headers=headers)
    assert res_get.status_code == 403

    res_post = await client.post(
        "/api/v1/bicos",
        headers=headers,
        json={
            "identificador_bico": "BC-TEST",
            "plataforma_id": tenant_bicos["plataforma_id"],
            "tipo_operacao": "CARREGAMENTO",
            "tanque_ids": [tenant_bicos["tq_diesel_id"]],
            "ativo": True,
        },
    )
    assert res_post.status_code == 403
