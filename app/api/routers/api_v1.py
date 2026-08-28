from fastapi import APIRouter

from app.api.routers.crud_router_factory import create_crud_router
from app.domain.models import (
    Amostra,
    AnaliseAmostra,
    ColetaAmostra,
    ComprovanteAmostra,
    ComprovanteAmostraItem,
    Congenere,
    HistoricoEdicaoAmostra,
    HistoricoEdicaoAnalise,
    HistoricoEdicaoComprovante,
    HistoricoEdicaoVeiculo,
    Laboratorio,
    Produto,
    Tanque,
    Terminal,
    Transportadora,
    Usuario,
    Veiculo,
    VeiculoProduto,
)
from app.domain.schemas import (
    AmostraCreate,
    AmostraResponse,
    AmostraUpdate,
    AnaliseAmostraCreate,
    AnaliseAmostraResponse,
    AnaliseAmostraUpdate,
    ColetaAmostraCreate,
    ColetaAmostraResponse,
    ColetaAmostraUpdate,
    ComprovanteAmostraCreate,
    ComprovanteAmostraItemCreate,
    ComprovanteAmostraItemResponse,
    ComprovanteAmostraResponse,
    ComprovanteAmostraUpdate,
    CongenereCreate,
    CongenereResponse,
    CongenereUpdate,
    HistoricoEdicaoAmostraCreate,
    HistoricoEdicaoAmostraResponse,
    HistoricoEdicaoAnaliseCreate,
    HistoricoEdicaoAnaliseResponse,
    HistoricoEdicaoComprovanteCreate,
    HistoricoEdicaoComprovanteResponse,
    HistoricoEdicaoVeiculoCreate,
    HistoricoEdicaoVeiculoResponse,
    LaboratorioCreate,
    LaboratorioResponse,
    LaboratorioUpdate,
    ProdutoCreate,
    ProdutoResponse,
    ProdutoUpdate,
    TanqueCreate,
    TanqueResponse,
    TanqueUpdate,
    TerminalCreate,
    TerminalResponse,
    TerminalUpdate,
    TransportadoraCreate,
    TransportadoraResponse,
    TransportadoraUpdate,
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
    VeiculoCreate,
    VeiculoProdutoCreate,
    VeiculoProdutoResponse,
    VeiculoResponse,
    VeiculoUpdate,
)

api_router = APIRouter()

# 1. Usuários
api_router.include_router(
    create_crud_router(
        model=Usuario,
        create_schema=UsuarioCreate,
        update_schema=UsuarioUpdate,
        response_schema=UsuarioResponse,
        prefix="/usuarios",
        tags=["Usuários"],
    )
)

# 2. Terminais
api_router.include_router(
    create_crud_router(
        model=Terminal,
        create_schema=TerminalCreate,
        update_schema=TerminalUpdate,
        response_schema=TerminalResponse,
        prefix="/terminais",
        tags=["Terminais"],
    )
)

# 3. Laboratórios
api_router.include_router(
    create_crud_router(
        model=Laboratorio,
        create_schema=LaboratorioCreate,
        update_schema=LaboratorioUpdate,
        response_schema=LaboratorioResponse,
        prefix="/laboratorios",
        tags=["Laboratórios"],
    )
)

# 4. Tanques
api_router.include_router(
    create_crud_router(
        model=Tanque,
        create_schema=TanqueCreate,
        update_schema=TanqueUpdate,
        response_schema=TanqueResponse,
        prefix="/tanques",
        tags=["Tanques"],
    )
)

# 5. Congêneres
api_router.include_router(
    create_crud_router(
        model=Congenere,
        create_schema=CongenereCreate,
        update_schema=CongenereUpdate,
        response_schema=CongenereResponse,
        prefix="/congeneres",
        tags=["Congêneres"],
    )
)

# 6. Transportadoras
api_router.include_router(
    create_crud_router(
        model=Transportadora,
        create_schema=TransportadoraCreate,
        update_schema=TransportadoraUpdate,
        response_schema=TransportadoraResponse,
        prefix="/transportadoras",
        tags=["Transportadoras"],
    )
)

# 7. Produtos
api_router.include_router(
    create_crud_router(
        model=Produto,
        create_schema=ProdutoCreate,
        update_schema=ProdutoUpdate,
        response_schema=ProdutoResponse,
        prefix="/produtos",
        tags=["Produtos"],
    )
)

# 8. Veículo-Produto (Pivô)
api_router.include_router(
    create_crud_router(
        model=VeiculoProduto,
        create_schema=VeiculoProdutoCreate,
        update_schema=VeiculoProdutoCreate,
        response_schema=VeiculoProdutoResponse,
        prefix="/veiculo-produtos",
        tags=["Veículo-Produtos"],
    )
)

# 9. Veículos
api_router.include_router(
    create_crud_router(
        model=Veiculo,
        create_schema=VeiculoCreate,
        update_schema=VeiculoUpdate,
        response_schema=VeiculoResponse,
        prefix="/veiculos",
        tags=["Veículos"],
    )
)

# 10. Coletas de Amostra
api_router.include_router(
    create_crud_router(
        model=ColetaAmostra,
        create_schema=ColetaAmostraCreate,
        update_schema=ColetaAmostraUpdate,
        response_schema=ColetaAmostraResponse,
        prefix="/coletas",
        tags=["Coletas de Amostra"],
    )
)

# 11. Amostras
api_router.include_router(
    create_crud_router(
        model=Amostra,
        create_schema=AmostraCreate,
        update_schema=AmostraUpdate,
        response_schema=AmostraResponse,
        prefix="/amostras",
        tags=["Amostras"],
    )
)

# 12. Análises de Amostra
api_router.include_router(
    create_crud_router(
        model=AnaliseAmostra,
        create_schema=AnaliseAmostraCreate,
        update_schema=AnaliseAmostraUpdate,
        response_schema=AnaliseAmostraResponse,
        prefix="/analises",
        tags=["Análises de Amostra"],
    )
)

# 13. Comprovantes de Amostra
api_router.include_router(
    create_crud_router(
        model=ComprovanteAmostra,
        create_schema=ComprovanteAmostraCreate,
        update_schema=ComprovanteAmostraUpdate,
        response_schema=ComprovanteAmostraResponse,
        prefix="/comprovantes",
        tags=["Comprovantes de Amostra"],
    )
)

# 14. Comprovante Amostra Item (Pivô)
api_router.include_router(
    create_crud_router(
        model=ComprovanteAmostraItem,
        create_schema=ComprovanteAmostraItemCreate,
        update_schema=ComprovanteAmostraItemCreate,
        response_schema=ComprovanteAmostraItemResponse,
        prefix="/comprovante-itens",
        tags=["Itens de Comprovante"],
    )
)

# 15. Histórico de Edição de Comprovante
api_router.include_router(
    create_crud_router(
        model=HistoricoEdicaoComprovante,
        create_schema=HistoricoEdicaoComprovanteCreate,
        update_schema=HistoricoEdicaoComprovanteCreate,
        response_schema=HistoricoEdicaoComprovanteResponse,
        prefix="/historicos-comprovante",
        tags=["Histórico de Comprovante"],
    )
)

# 16. Histórico de Edição de Veículo
api_router.include_router(
    create_crud_router(
        model=HistoricoEdicaoVeiculo,
        create_schema=HistoricoEdicaoVeiculoCreate,
        update_schema=HistoricoEdicaoVeiculoCreate,
        response_schema=HistoricoEdicaoVeiculoResponse,
        prefix="/historicos-veiculo",
        tags=["Histórico de Veículo"],
    )
)

# 17. Histórico de Edição de Amostra
api_router.include_router(
    create_crud_router(
        model=HistoricoEdicaoAmostra,
        create_schema=HistoricoEdicaoAmostraCreate,
        update_schema=HistoricoEdicaoAmostraCreate,
        response_schema=HistoricoEdicaoAmostraResponse,
        prefix="/historicos-amostra",
        tags=["Histórico de Amostra"],
    )
)

# 18. Histórico de Edição de Análise
api_router.include_router(
    create_crud_router(
        model=HistoricoEdicaoAnalise,
        create_schema=HistoricoEdicaoAnaliseCreate,
        update_schema=HistoricoEdicaoAnaliseCreate,
        response_schema=HistoricoEdicaoAnaliseResponse,
        prefix="/historicos-analise",
        tags=["Histórico de Análise"],
    )
)
