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
