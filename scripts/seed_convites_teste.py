"""
Script de Seed (opcional): códigos de ativação de teste em convite_cadastro.

Lê a variável de ambiente SEED_CONVITES (lista separada por vírgula) e insere
cada código como um convite NÃO utilizado e SEM expiração, de forma idempotente
(ignora os que já existem). Se a variável não estiver definida ou vazia, o script
não faz nada — seguro para rodar em produção a cada boot.

Os códigos são normalizados (strip + upper) exatamente como o cadastro_service
faz na validação, garantindo que batam com o que o usuário digitar no site.

Ex.: SEED_CONVITES="ELAION-TEST-0001,ELAION-TEST-0002"
"""

import asyncio
import os
from typing import List

from sqlalchemy import select

from app.infra.database import AsyncSessionLocal
from app.domain.models import ConviteCadastro


def _parse_codigos(raw: str) -> List[str]:
    codigos: List[str] = []
    for parte in (raw or "").split(","):
        codigo = parte.strip().upper()
        if codigo and codigo not in codigos:
            codigos.append(codigo)
    return codigos


async def seed_convites() -> None:
    codigos = _parse_codigos(os.getenv("SEED_CONVITES", ""))

    if not codigos:
        print("-> SEED_CONVITES não definido; nenhum convite de teste inserido.")
        return

    async with AsyncSessionLocal() as session:
        inseridos = 0
        for codigo in codigos:
            stmt = select(ConviteCadastro).where(ConviteCadastro.codigo == codigo)
            existente = (await session.execute(stmt)).scalar_one_or_none()
            if existente is None:
                session.add(ConviteCadastro(codigo=codigo, utilizado=False, expira_em=None))
                inseridos += 1
                print(f"   + Convite de teste criado: {codigo}")
            else:
                print(f"   = Convite já existe (ignorado): {codigo}")

        await session.commit()
        print(f"-> Seed de convites concluído! Novos: {inseridos}/{len(codigos)}")


if __name__ == "__main__":
    asyncio.run(seed_convites())
