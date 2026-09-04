"""
Script de Seed: Catálogo de Módulos e Permissões do SIRAC.
Insere no banco de dados o módulo SIRAC e as 22 funcionalidades operacionais
compatíveis com o Drawer 'Novo Colaborador' do Frontend.
"""

import asyncio
from sqlalchemy import select
from app.infra.database import AsyncSessionLocal
from app.domain.models import ModuloAssinatura, ModuloFuncionalidade, TipoAcaoFuncionalidade

PERMISSOES_SIRAC_SEED = [
    # 1. Painéis
    {
        "chave": "sirac:paineis:visualizar",
        "nome": "Visualizar Painéis",
        "tipo_acao": TipoAcaoFuncionalidade.VISUALIZAR,
    },
    # 2. Controle de Acesso
    {
        "chave": "sirac:ca:visualizar_listagem",
        "nome": "Visualizar listagens (Controle de Acesso)",
        "tipo_acao": TipoAcaoFuncionalidade.VISUALIZAR,
    },
    {
        "chave": "sirac:ca:visualizar_detalhes",
        "nome": "Visualizar detalhes dos veículos",
        "tipo_acao": TipoAcaoFuncionalidade.VISUALIZAR,
    },
    {
        "chave": "sirac:ca:registrar_veiculo",
        "nome": "Registrar novo veículo na portaria",
        "tipo_acao": TipoAcaoFuncionalidade.CRIAR,
    },
    {
        "chave": "sirac:ca:editar_veiculo",
        "nome": "Editar dados do veículo",
        "tipo_acao": TipoAcaoFuncionalidade.EDITAR,
    },
    {
        "chave": "sirac:ca:alterar_status",
        "nome": "Alterar status operacional de veículo",
        "tipo_acao": TipoAcaoFuncionalidade.EDITAR,
    },
    # 3. Triagem
    {
        "chave": "sirac:triagem:visualizar_listagem",
        "nome": "Visualizar listagem da triagem",
        "tipo_acao": TipoAcaoFuncionalidade.VISUALIZAR,
    },
    {
        "chave": "sirac:triagem:registrar_amostras",
        "nome": "Registrar amostras de combustível",
        "tipo_acao": TipoAcaoFuncionalidade.CRIAR,
    },
    {
        "chave": "sirac:triagem:ver_detalhes_veiculo",
        "nome": "Ver detalhes de veículo na triagem",
        "tipo_acao": TipoAcaoFuncionalidade.VISUALIZAR,
    },
    {
        "chave": "sirac:triagem:gerar_comprovante",
        "nome": "Gerar comprovante de triagem",
        "tipo_acao": TipoAcaoFuncionalidade.CRIAR,
    },
    {
        "chave": "sirac:triagem:gerar_laudo",
        "nome": "Gerar laudo laboratorial da amostra",
        "tipo_acao": TipoAcaoFuncionalidade.CRIAR,
    },
    {
        "chave": "sirac:triagem:analisar_amostra",
        "nome": "Aprovar / Analisar laudo de amostra",
        "tipo_acao": TipoAcaoFuncionalidade.APROVAR,
    },
    # 4. Comprovantes
    {
        "chave": "sirac:comprovantes:visualizar_listagem",
        "nome": "Visualizar listagem de comprovantes",
        "tipo_acao": TipoAcaoFuncionalidade.VISUALIZAR,
    },
    {
        "chave": "sirac:comprovantes:visualizar_detalhes",
        "nome": "Visualizar detalhes do comprovante",
        "tipo_acao": TipoAcaoFuncionalidade.VISUALIZAR,
    },
    {
        "chave": "sirac:comprovantes:editar_comprovante",
        "nome": "Editar comprovante operacional",
        "tipo_acao": TipoAcaoFuncionalidade.EDITAR,
    },
    # 5. Configurações - Usuários
    {
        "chave": "sirac:config:usuarios:visualizar",
        "nome": "Visualizar colaboradores do terminal",
        "tipo_acao": TipoAcaoFuncionalidade.VISUALIZAR,
    },
    {
        "chave": "sirac:config:usuarios:registrar",
        "nome": "Registrar novo colaborador no terminal",
        "tipo_acao": TipoAcaoFuncionalidade.CRIAR,
    },
    {
        "chave": "sirac:config:usuarios:detalhes",
        "nome": "Visualizar detalhes do colaborador",
        "tipo_acao": TipoAcaoFuncionalidade.VISUALIZAR,
    },
    # 6. Configurações - Congênere
    {
        "chave": "sirac:config:congenere:visualizar",
        "nome": "Visualizar congêneres cadastradas",
        "tipo_acao": TipoAcaoFuncionalidade.VISUALIZAR,
    },
    {
        "chave": "sirac:config:congenere:detalhes",
        "nome": "Visualizar detalhes da congênere",
        "tipo_acao": TipoAcaoFuncionalidade.VISUALIZAR,
    },
    {
        "chave": "sirac:config:congenere:editar",
        "nome": "Editar dados da congênere",
        "tipo_acao": TipoAcaoFuncionalidade.EDITAR,
    },
    {
        "chave": "sirac:config:congenere:registrar",
        "nome": "Registrar nova empresa congênere",
        "tipo_acao": TipoAcaoFuncionalidade.CRIAR,
    },
    # 7. Configurações - Terminal
    {
        "chave": "sirac:config:terminal:dados_cadastrais",
        "nome": "Visualizar dados cadastrais do terminal",
        "tipo_acao": TipoAcaoFuncionalidade.VISUALIZAR,
    },
    {
        "chave": "sirac:config:terminal:tanques_ver",
        "nome": "Visualizar tanques, bicos e plataformas",
        "tipo_acao": TipoAcaoFuncionalidade.VISUALIZAR,
    },
    {
        "chave": "sirac:config:terminal:tanques_editar",
        "nome": "Registrar e editar tanques, bicos e plataformas",
        "tipo_acao": TipoAcaoFuncionalidade.EDITAR,
    },
    {
        "chave": "sirac:config:terminal:dados_editar",
        "nome": "Editar dados cadastrais do terminal",
        "tipo_acao": TipoAcaoFuncionalidade.EDITAR,
    },
    # 8. Relatórios
    {
        "chave": "sirac:relatorios:visualizar",
        "nome": "Visualizar relatórios gerenciais",
        "tipo_acao": TipoAcaoFuncionalidade.VISUALIZAR,
    },
]


async def seed_sirac():
    async with AsyncSessionLocal() as session:
        # 1. Garantir existência do Módulo SIRAC
        stmt_mod = select(ModuloAssinatura).where(ModuloAssinatura.codigo == "SIRAC")
        res_mod = await session.execute(stmt_mod)
        modulo_sirac = res_mod.scalar_one_or_none()

        if not modulo_sirac:
            modulo_sirac = ModuloAssinatura(
                codigo="SIRAC",
                nome="SIRAC - Recepção e Amostragem de Combustíveis",
                descricao="Módulo operacional de portaria, pátio, coleta de amostras e laudos laboratoriais.",
                ativo=True,
            )
            session.add(modulo_sirac)
            await session.flush()
            print(f"-> Módulo SIRAC criado com ID: {modulo_sirac.id}")
        else:
            print(f"-> Módulo SIRAC já existe com ID: {modulo_sirac.id}")

        # 2. Inserir ou atualizar funcionalidades
        inseridas = 0
        for item in PERMISSOES_SIRAC_SEED:
            stmt_func = select(ModuloFuncionalidade).where(ModuloFuncionalidade.chave == item["chave"])
            res_func = await session.execute(stmt_func)
            func_existente = res_func.scalar_one_or_none()

            if not func_existente:
                nova_func = ModuloFuncionalidade(
                    modulo_id=modulo_sirac.id,
                    chave=item["chave"],
                    nome=item["nome"],
                    tipo_acao=item["tipo_acao"],
                )
                session.add(nova_func)
                inseridas += 1

        await session.commit()
        print(f"-> Seed concluído! Novas funcionalidades cadastradas: {inseridas}/{len(PERMISSOES_SIRAC_SEED)}")


if __name__ == "__main__":
    asyncio.run(seed_sirac())
