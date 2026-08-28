from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.models import (
    EtapaAnalise,
    PapelUsuario,
    StatusComprovante,
    StatusPortaria,
    StatusResultadoAmostra,
)

# =============================================================================
# SCHEMAS: USUÁRIO
# =============================================================================

class UsuarioBase(BaseModel):
    nome_completo: str = Field(..., min_length=2, max_length=150)
    cpf: str = Field(..., min_length=11, max_length=14)
    login: str = Field(..., min_length=3, max_length=50)
    papel: PapelUsuario
    turno: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    ativo: bool = True


class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=6, max_length=100)


class UsuarioUpdate(BaseModel):
    nome_completo: Optional[str] = None
    papel: Optional[PapelUsuario] = None
    turno: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    ativo: Optional[bool] = None
    senha: Optional[str] = None


class UsuarioResponse(UsuarioBase):
    id: int
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHEMAS: TERMINAL
# =============================================================================

class TerminalBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    codigo: str = Field(..., min_length=2, max_length=50)
    ativo: bool = True


class TerminalCreate(TerminalBase):
    pass


class TerminalUpdate(BaseModel):
    nome: Optional[str] = None
    codigo: Optional[str] = None
    ativo: Optional[bool] = None


class TerminalResponse(TerminalBase):
    id: int
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHEMAS: LABORATÓRIO
# =============================================================================

class LaboratorioBase(BaseModel):
    terminal_id: int
    nome: str = Field(..., min_length=2, max_length=100)
    codigo: Optional[str] = None
    ativo: bool = True


class LaboratorioCreate(LaboratorioBase):
    pass


class LaboratorioUpdate(BaseModel):
    terminal_id: Optional[int] = None
    nome: Optional[str] = None
    codigo: Optional[str] = None
    ativo: Optional[bool] = None


class LaboratorioResponse(LaboratorioBase):
    id: int
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHEMAS: TANQUE
# =============================================================================

class TanqueBase(BaseModel):
    terminal_id: int
    produto_id: int
    identificador_tanque: str = Field(..., min_length=1, max_length=50)
    capacidade_litros: Decimal
    ativo: bool = True


class TanqueCreate(TanqueBase):
    pass


class TanqueUpdate(BaseModel):
    terminal_id: Optional[int] = None
    produto_id: Optional[int] = None
    identificador_tanque: Optional[str] = None
    capacidade_litros: Optional[Decimal] = None
    ativo: Optional[bool] = None


class TanqueResponse(TanqueBase):
    id: int
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHEMAS: CONGÊNERE
# =============================================================================

class CongenereBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    codigo_sicof: Optional[str] = None


class CongenereCreate(CongenereBase):
    pass


class CongenereUpdate(BaseModel):
    nome: Optional[str] = None
    codigo_sicof: Optional[str] = None


class CongenereResponse(CongenereBase):
    id: int
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHEMAS: TRANSPORTADORA
# =============================================================================

class TransportadoraBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150)
    is_propria: bool = False


class TransportadoraCreate(TransportadoraBase):
    pass


class TransportadoraUpdate(BaseModel):
    nome: Optional[str] = None
    is_propria: Optional[bool] = None


class TransportadoraResponse(TransportadoraBase):
    id: int
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHEMAS: PRODUTO
# =============================================================================

class ProdutoBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    categoria: str = Field(..., min_length=2, max_length=50)
    unidade_medida: str = "L"


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    categoria: Optional[str] = None
    unidade_medida: Optional[str] = None


class ProdutoResponse(ProdutoBase):
    id: int
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHEMAS: VEÍCULO PRODUTO (PIVÔ N:N)
# =============================================================================

class VeiculoProdutoBase(BaseModel):
    veiculo_id: int
    produto_id: int


class VeiculoProdutoCreate(VeiculoProdutoBase):
    pass


class VeiculoProdutoResponse(VeiculoProdutoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHEMAS: VEÍCULO
# =============================================================================

class VeiculoBase(BaseModel):
    terminal_id: int
    placa: str = Field(..., min_length=7, max_length=10)
    nome_motorista: str = Field(..., min_length=2, max_length=150)
    numero_nota_fiscal: str = Field(..., min_length=1, max_length=50)
    origem: str = Field(..., min_length=2, max_length=150)
    congenere_id: int
    transportadora_id: int
    is_transportadora_propria: bool = False
    numero_compartimentos: int = Field(..., ge=1)
    capacidade_total_litros: Decimal
    volume_nota_fiscal_litros: Decimal
    status_portaria: StatusPortaria = StatusPortaria.AGUARDANDO
    motivo_cancelamento: Optional[str] = None
    observacao_cancelamento: Optional[str] = None
    observacao_geral: Optional[str] = None
    usuario_registro_id: int
    usuario_aprovacao_saida_id: Optional[int] = None
    data_hora_saida: Optional[datetime] = None


class VeiculoCreate(VeiculoBase):
    produto_ids: Optional[List[int]] = None


class VeiculoUpdate(BaseModel):
    terminal_id: Optional[int] = None
    placa: Optional[str] = None
    nome_motorista: Optional[str] = None
    numero_nota_fiscal: Optional[str] = None
    origem: Optional[str] = None
    congenere_id: Optional[int] = None
    transportadora_id: Optional[int] = None
    is_transportadora_propria: Optional[bool] = None
    numero_compartimentos: Optional[int] = None
    capacidade_total_litros: Optional[Decimal] = None
    volume_nota_fiscal_litros: Optional[Decimal] = None
    status_portaria: Optional[StatusPortaria] = None
    data_hora_saida: Optional[datetime] = None
    motivo_cancelamento: Optional[str] = None
    observacao_cancelamento: Optional[str] = None
    observacao_geral: Optional[str] = None
    usuario_aprovacao_saida_id: Optional[int] = None


class VeiculoResponse(VeiculoBase):
    id: int
    data_hora_entrada: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHEMAS: COLETA AMOSTRA
# =============================================================================

class ColetaAmostraBase(BaseModel):
    veiculo_id: int
    numero_coleta: int = 1
    status: str = "Em andamento"
    amostrador_id: Optional[int] = None
    usuario_recebimento_id: Optional[int] = None


class ColetaAmostraCreate(ColetaAmostraBase):
    pass


class ColetaAmostraUpdate(BaseModel):
    numero_coleta: Optional[int] = None
    status: Optional[str] = None
    amostrador_id: Optional[int] = None
    usuario_recebimento_id: Optional[int] = None


class ColetaAmostraResponse(ColetaAmostraBase):
    id: int
    data_hora_coleta: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHEMAS: AMOSTRA
# =============================================================================

class AmostraBase(BaseModel):
    codigo_amostra: str = Field(..., min_length=1, max_length=30)
    coleta_id: int
    veiculo_id: int
    produto_id: int
    identificador_compartimento: str = Field(..., min_length=1, max_length=10)
    capacidade_compartimento_litros: Decimal
    temperatura_coleta_celsius: Decimal
    etapa_analise: EtapaAnalise = EtapaAnalise.COLETA
    status_resultado: StatusResultadoAmostra = StatusResultadoAmostra.NORMAL
    is_recoleta: bool = False
    origem_procedimento: str = "Descarga"
    operador_id: Optional[int] = None
    usuario_reprovacao_id: Optional[int] = None
    data_hora_reprovacao: Optional[datetime] = None
    motivo_reprovacao: Optional[str] = None
    usuario_recoleta_id: Optional[int] = None
    data_hora_recoleta: Optional[datetime] = None
    motivo_recoleta: Optional[str] = None


class AmostraCreate(AmostraBase):
    pass


class AmostraUpdate(BaseModel):
    codigo_amostra: Optional[str] = None
    produto_id: Optional[int] = None
    identificador_compartimento: Optional[str] = None
    capacidade_compartimento_litros: Optional[Decimal] = None
    temperatura_coleta_celsius: Optional[Decimal] = None
    etapa_analise: Optional[EtapaAnalise] = None
    status_resultado: Optional[StatusResultadoAmostra] = None
    is_recoleta: Optional[bool] = None
    origem_procedimento: Optional[str] = None
    operador_id: Optional[int] = None
    usuario_reprovacao_id: Optional[int] = None
    data_hora_reprovacao: Optional[datetime] = None
    motivo_reprovacao: Optional[str] = None
    usuario_recoleta_id: Optional[int] = None
    data_hora_recoleta: Optional[datetime] = None
    motivo_recoleta: Optional[str] = None


class AmostraResponse(AmostraBase):
    id: int
    data_hora_coleta: datetime
    data_hora_fim_analise: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHEMAS: ANÁLISE AMOSTRA
# =============================================================================

class AnaliseAmostraBase(BaseModel):
    amostra_id: int
    analista_id: int
    laboratorio_id: Optional[int] = None
    tipo_especifico_produto: Optional[str] = None
    cor: Optional[str] = None
    aspecto: Optional[str] = None
    material_particulado: Optional[bool] = None
    agua_livre: Optional[bool] = None
    numero_amostra_lab: Optional[str] = None
    visto_analista: Optional[str] = None
    densidade_kg_l: Optional[Decimal] = None
    temperatura_ensaio_celsius: Optional[Decimal] = None
    fator_correcao: Optional[Decimal] = None
    massa_especifica_20c_kg_l: Optional[Decimal] = None
    grau_inpm: Optional[Decimal] = None
    teor_agua_ppm: Optional[Decimal] = None
    observacoes: Optional[str] = None


class AnaliseAmostraCreate(AnaliseAmostraBase):
    pass


class AnaliseAmostraUpdate(BaseModel):
    analista_id: Optional[int] = None
    laboratorio_id: Optional[int] = None
    tipo_especifico_produto: Optional[str] = None
    cor: Optional[str] = None
    aspecto: Optional[str] = None
    material_particulado: Optional[bool] = None
    agua_livre: Optional[bool] = None
    numero_amostra_lab: Optional[str] = None
    visto_analista: Optional[str] = None
    densidade_kg_l: Optional[Decimal] = None
    temperatura_ensaio_celsius: Optional[Decimal] = None
    fator_correcao: Optional[Decimal] = None
    massa_especifica_20c_kg_l: Optional[Decimal] = None
    grau_inpm: Optional[Decimal] = None
    teor_agua_ppm: Optional[Decimal] = None
    observacoes: Optional[str] = None


class AnaliseAmostraResponse(AnaliseAmostraBase):
    id: int
    data_hora_analise: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHEMAS: COMPROVANTE AMOSTRA
# =============================================================================

class ComprovanteAmostraBase(BaseModel):
    veiculo_id: int
    congenere_id: int
    numero_sicof: str = Field(..., min_length=1, max_length=50)
    lancamento_sicof: Optional[str] = None
    nota_fiscal_numero: str = Field(..., min_length=1, max_length=50)
    volume_ambiente_nf_litros: Decimal
    volume_20c_nf_litros: Decimal
    data_geracao: date
    hora_geracao: time
    densidade_20c_apurada: Decimal
    grau_inpm: Optional[Decimal] = None
    fator_correcao: Decimal
    volume_ambiente_apurado_litros: Decimal
    volume_20c_apurado_litros: Decimal
    resultado_variacao_litros: Decimal
    tanque_descarga_id: Optional[int] = None
    volume_retirada_litros: Optional[Decimal] = None
    complemento_observacoes: Optional[str] = None
    status: StatusComprovante = StatusComprovante.DISPONIVEL
    criado_por_usuario_id: int


class ComprovanteAmostraCreate(ComprovanteAmostraBase):
    amostra_ids: Optional[List[int]] = None


class ComprovanteAmostraUpdate(BaseModel):
    numero_sicof: Optional[str] = None
    lancamento_sicof: Optional[str] = None
    nota_fiscal_numero: Optional[str] = None
    volume_ambiente_nf_litros: Optional[Decimal] = None
    volume_20c_nf_litros: Optional[Decimal] = None
    densidade_20c_apurada: Optional[Decimal] = None
    grau_inpm: Optional[Decimal] = None
    fator_correcao: Optional[Decimal] = None
    volume_ambiente_apurado_litros: Optional[Decimal] = None
    volume_20c_apurado_litros: Optional[Decimal] = None
    resultado_variacao_litros: Optional[Decimal] = None
    tanque_descarga_id: Optional[int] = None
    volume_retirada_litros: Optional[Decimal] = None
    complemento_observacoes: Optional[str] = None
    status: Optional[StatusComprovante] = None


class ComprovanteAmostraResponse(ComprovanteAmostraBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHEMAS: COMPROVANTE AMOSTRA ITEM (PIVÔ N:N)
# =============================================================================

class ComprovanteAmostraItemBase(BaseModel):
    comprovante_id: int
    amostra_id: int


class ComprovanteAmostraItemCreate(ComprovanteAmostraItemBase):
    pass


class ComprovanteAmostraItemResponse(ComprovanteAmostraItemBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHEMAS: HISTÓRICOS DE AUDITORIA
# =============================================================================

class HistoricoEdicaoComprovanteBase(BaseModel):
    comprovante_id: int
    usuario_id: int
    descricao_acao: str


class HistoricoEdicaoComprovanteCreate(HistoricoEdicaoComprovanteBase):
    pass


class HistoricoEdicaoComprovanteResponse(HistoricoEdicaoComprovanteBase):
    id: int
    data_hora: datetime

    model_config = ConfigDict(from_attributes=True)


class HistoricoEdicaoVeiculoBase(BaseModel):
    veiculo_id: int
    usuario_id: int
    campo_alterado: str
    valor_anterior: Optional[str] = None
    valor_novo: Optional[str] = None
    motivo: Optional[str] = None


class HistoricoEdicaoVeiculoCreate(HistoricoEdicaoVeiculoBase):
    pass


class HistoricoEdicaoVeiculoResponse(HistoricoEdicaoVeiculoBase):
    id: int
    data_hora: datetime

    model_config = ConfigDict(from_attributes=True)


class HistoricoEdicaoAmostraBase(BaseModel):
    amostra_id: int
    usuario_id: int
    campo_alterado: str
    valor_anterior: Optional[str] = None
    valor_novo: Optional[str] = None
    motivo: Optional[str] = None


class HistoricoEdicaoAmostraCreate(HistoricoEdicaoAmostraBase):
    pass


class HistoricoEdicaoAmostraResponse(HistoricoEdicaoAmostraBase):
    id: int
    data_hora: datetime

    model_config = ConfigDict(from_attributes=True)


class HistoricoEdicaoAnaliseBase(BaseModel):
    analise_amostra_id: int
    usuario_id: int
    campo_alterado: str
    valor_anterior: Optional[str] = None
    valor_novo: Optional[str] = None
    motivo: Optional[str] = None


class HistoricoEdicaoAnaliseCreate(HistoricoEdicaoAnaliseBase):
    pass


class HistoricoEdicaoAnaliseResponse(HistoricoEdicaoAnaliseBase):
    id: int
    data_hora: datetime

    model_config = ConfigDict(from_attributes=True)
