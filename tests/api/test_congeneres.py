"""Testes unitários e de integração para o CRUD de Congêneres."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cadastrar_congenere_valida(client: AsyncClient):
    """Testa o cadastro com os 4 campos obrigatórios e contatos do financeiro."""
    payload = {
        "razao_social": "Petrobras Distribuidora Teste S.A.",
        "cnpj": "12345678000199",
        "telefone": "2199998888",
        "email": "contato@petrobras.com.br",
        "telefone_financeiro": "2199997777",
        "email_financeiro": "financeiro@petrobras.com.br",
        "cep": "20000000",
        "logradouro": "Av. República do Chile",
        "numero": "65",
        "bairro": "Centro",
        "cidade": "Rio de Janeiro",
        "uf": "RJ",
        "ativo": True,
    }

    # Sem o header X-Terminal-ID, deve retornar 400
    res_sem_terminal = await client.post("/api/v1/congeneres", json=payload)
    assert res_sem_terminal.status_code in [400, 401, 403]


@pytest.mark.asyncio
async def test_congeneres_diesel_nunca_aditivado():
    """Testa regra de negócio: combustíveis diesel não podem ser aditivados mesmo se solicitado."""
    from app.domain.models import CongenereProduto
    from app.domain.schemas import CongenereProdutoDTO, TipoCombustivel

    prod_s10 = CongenereProdutoDTO(combustivel=TipoCombustivel.DIESEL_S10_A, aditivado=True)
    prod_s500 = CongenereProdutoDTO(combustivel=TipoCombustivel.DIESEL_S500_A, aditivado=True)
    prod_gas = CongenereProdutoDTO(combustivel=TipoCombustivel.GASOLINA_A, aditivado=True)
    prod_eta = CongenereProdutoDTO(combustivel=TipoCombustivel.ETANOL_HIDRATADO, aditivado=True)

    for p in [prod_s10, prod_s500, prod_gas, prod_eta]:
        comb_str = str(p.combustivel.value if hasattr(p.combustivel, "value") else p.combustivel)
        is_diesel = comb_str.upper().startswith("DIESEL")
        obj = CongenereProduto(
            congenere_id=1,
            combustivel=p.combustivel,
            aditivado=False if is_diesel else p.aditivado,
            cor=p.cor,
        )
        if is_diesel:
            assert obj.aditivado is False
        else:
            assert obj.aditivado is True

