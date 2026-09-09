"""Serviço de Negócio para Gestão de Congêneres do Terminal."""

import re
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import ConflitoException, ItemNaoEncontradoException, RegraNegocioException
from app.domain.models import Congenere, CongenereProduto, TipoCombustivel
from app.domain.schemas import (
    CongenereCreateDTO,
    CongenereResponseDTO,
    CongenereUpdateDTO,
    PaginatedCongeneresResponseDTO,
)

TODOS_COMBUSTIVEIS = [
    TipoCombustivel.GASOLINA_A,
    TipoCombustivel.DIESEL_S10_A,
    TipoCombustivel.DIESEL_S500_A,
    TipoCombustivel.ETANOL_ANIDRO,
    TipoCombustivel.ETANOL_HIDRATADO,
]

from app.infra.repositories.congeneres_repository import congenere_repository
from app.infra.repositories.terminal_repository import terminal_repository


def _sanitizar_digitos(valor: Optional[str]) -> Optional[str]:
    if not valor:
        return None
    return re.sub(r"\D", "", valor)


class CongeneresService:
    """Regras de negócio de congêneres associadas ao terminal ativo."""

    async def cadastrar_congenere(
        self,
        session: AsyncSession,
        terminal_id: int,
        dto: CongenereCreateDTO,
    ) -> CongenereResponseDTO:
        # 1. Validar se o terminal existe
        terminal = await terminal_repository.get_by_id(session, terminal_id)
        if not terminal:
            raise ItemNaoEncontradoException(f"Terminal {terminal_id} não encontrado.")

        # 2. Sanitizar dígitos obrigatórios e opcionais
        clean_cnpj = _sanitizar_digitos(dto.cnpj)
        if not clean_cnpj or len(clean_cnpj) != 14:
            raise RegraNegocioException("CNPJ inválido. Deve conter exatamente 14 dígitos.")

        clean_telefone = _sanitizar_digitos(dto.telefone)
        if not clean_telefone or len(clean_telefone) < 10:
            raise RegraNegocioException("Telefone inválido. Deve conter DDD e número.")

        clean_tel_fin = _sanitizar_digitos(dto.telefone_financeiro)
        clean_cep = _sanitizar_digitos(dto.cep)

        # 3. Verificar duplicidade de CNPJ no mesmo terminal
        congenere_existente = await congenere_repository.get_by_cnpj_terminal(
            session, terminal_id, clean_cnpj
        )
        if congenere_existente:
            raise ConflitoException(
                f"Já existe uma congênere cadastrada com o CNPJ {dto.cnpj} neste terminal."
            )

        # 4. Montar dicionário para persistência
        dados = {
            "razao_social": dto.razao_social.strip(),
            "cnpj": clean_cnpj,
            "inscricao_estadual": dto.inscricao_estadual.strip() if dto.inscricao_estadual else None,
            "telefone": clean_telefone,
            "email": dto.email.strip().lower(),
            "telefone_financeiro": clean_tel_fin,
            "email_financeiro": dto.email_financeiro.strip().lower() if dto.email_financeiro else None,
            "cep": clean_cep,
            "logradouro": dto.logradouro.strip() if dto.logradouro else None,
            "numero": dto.numero.strip() if dto.numero else None,
            "complemento": dto.complemento.strip() if dto.complemento else None,
            "bairro": dto.bairro.strip() if dto.bairro else None,
            "cidade": dto.cidade.strip() if dto.cidade else None,
            "uf": dto.uf.strip().upper() if dto.uf else None,
            "logo_url": dto.logo_url,
            "ativo": dto.ativo,
        }

        congenere = await congenere_repository.criar(session, terminal_id, dados)

        # Mapeia produtos informados pelo frontend para extrair aditivação e cor
        aditivados_map = {}
        if dto.produtos:
            for p in dto.produtos:
                c_key = str(p.combustivel.value if hasattr(p.combustivel, "value") else p.combustivel)
                aditivados_map[c_key] = p

        for comb in TODOS_COMBUSTIVEIS:
            c_str = str(comb.value if hasattr(comb, "value") else comb)
            is_diesel = c_str.upper().startswith("DIESEL")
            p_info = aditivados_map.get(c_str)
            is_aditivado = bool(p_info.aditivado) if (p_info and not is_diesel) else False
            cor_val = p_info.cor.strip() if (p_info and p_info.cor and is_aditivado) else None

            session.add(
                CongenereProduto(
                    congenere_id=congenere.id,
                    combustivel=comb,
                    aditivado=is_aditivado,
                    cor=cor_val,
                )
            )

        await session.flush()
        await session.commit()
        await session.refresh(congenere)
        return CongenereResponseDTO.model_validate(congenere)


    async def listar_congeneres(
        self,
        session: AsyncSession,
        terminal_id: int,
        busca: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedCongeneresResponseDTO:
        items, total_count = await congenere_repository.listar_por_terminal(
            session, terminal_id, busca, page=page, page_size=page_size
        )
        total_pages = max(1, (total_count + page_size - 1) // page_size)

        return PaginatedCongeneresResponseDTO(
            items=[CongenereResponseDTO.model_validate(c) for c in items],
            total=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


    async def obter_congenere_por_id(
        self,
        session: AsyncSession,
        terminal_id: int,
        congenere_id: int,
    ) -> CongenereResponseDTO:
        congenere = await congenere_repository.get_by_id(session, congenere_id)
        if not congenere or congenere.terminal_id != terminal_id:
            raise ItemNaoEncontradoException(
                f"Congênere {congenere_id} não encontrada para o terminal ativo."
            )
        return CongenereResponseDTO.model_validate(congenere)

    async def atualizar_congenere(
        self,
        session: AsyncSession,
        terminal_id: int,
        congenere_id: int,
        dto: CongenereUpdateDTO,
    ) -> CongenereResponseDTO:
        congenere = await congenere_repository.get_by_id(session, congenere_id)
        if not congenere or congenere.terminal_id != terminal_id:
            raise ItemNaoEncontradoException(
                f"Congênere {congenere_id} não encontrada para o terminal ativo."
            )

        dados_atualizar = {}
        if dto.razao_social is not None:
            dados_atualizar["razao_social"] = dto.razao_social.strip()
        if dto.cnpj is not None:
            clean_cnpj = _sanitizar_digitos(dto.cnpj)
            if clean_cnpj != congenere.cnpj:
                existe = await congenere_repository.get_by_cnpj_terminal(session, terminal_id, clean_cnpj)
                if existe:
                    raise ConflitoException("Já existe outra congênere cadastrada com este CNPJ neste terminal.")
            dados_atualizar["cnpj"] = clean_cnpj
        if dto.telefone is not None:
            dados_atualizar["telefone"] = _sanitizar_digitos(dto.telefone)
        if dto.email is not None:
            dados_atualizar["email"] = dto.email.strip().lower()
        if dto.inscricao_estadual is not None:
            dados_atualizar["inscricao_estadual"] = dto.inscricao_estadual.strip() or None
        if dto.telefone_financeiro is not None:
            dados_atualizar["telefone_financeiro"] = _sanitizar_digitos(dto.telefone_financeiro)
        if dto.email_financeiro is not None:
            dados_atualizar["email_financeiro"] = dto.email_financeiro.strip().lower() if dto.email_financeiro else None
        if dto.cep is not None:
            dados_atualizar["cep"] = _sanitizar_digitos(dto.cep)
        if dto.logradouro is not None:
            dados_atualizar["logradouro"] = dto.logradouro.strip() or None
        if dto.numero is not None:
            dados_atualizar["numero"] = dto.numero.strip() or None
        if dto.complemento is not None:
            dados_atualizar["complemento"] = dto.complemento.strip() or None
        if dto.bairro is not None:
            dados_atualizar["bairro"] = dto.bairro.strip() or None
        if dto.cidade is not None:
            dados_atualizar["cidade"] = dto.cidade.strip() or None
        if dto.uf is not None:
            dados_atualizar["uf"] = dto.uf.strip().upper() or None
        if dto.logo_url is not None:
            dados_atualizar["logo_url"] = dto.logo_url
        if dto.ativo is not None:
            dados_atualizar["ativo"] = dto.ativo

        if dto.produtos is not None:
            aditivados_map = {}
            for p in dto.produtos:
                c_key = str(p.combustivel.value if hasattr(p.combustivel, "value") else p.combustivel)
                aditivados_map[c_key] = p

            existentes_map = {
                str(p.combustivel.value if hasattr(p.combustivel, "value") else p.combustivel): p
                for p in congenere.produtos_operados
            }

            for comb in TODOS_COMBUSTIVEIS:
                c_str = str(comb.value if hasattr(comb, "value") else comb)
                is_diesel = c_str.upper().startswith("DIESEL")
                p_info = aditivados_map.get(c_str)
                is_aditivado = bool(p_info.aditivado) if (p_info and not is_diesel) else False
                cor_val = p_info.cor.strip() if (p_info and p_info.cor and is_aditivado) else None

                if c_str in existentes_map:
                    item = existentes_map[c_str]
                    item.aditivado = is_aditivado
                    item.cor = cor_val
                else:
                    congenere.produtos_operados.append(
                        CongenereProduto(
                            congenere_id=congenere.id,
                            combustivel=comb,
                            aditivado=is_aditivado,
                            cor=cor_val,
                        )
                    )
            await session.flush()

        atualizada = await congenere_repository.atualizar(session, congenere, dados_atualizar)
        await session.commit()
        await session.refresh(atualizada)
        return CongenereResponseDTO.model_validate(atualizada)



congeneres_service = CongeneresService()
