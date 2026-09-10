"""
Schemas Pydantic (v2) - DTOs para validação de entrada e saída.
Estruturados para Clean Architecture e fail-fast com Pydantic v2.
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, EmailStr, Field, AliasChoices

from app.domain.models import (
    AcaoAuditoria,
    CategoriaProduto,
    EstadoVeiculo,
    PapelUsuario,
    ParecerLaudo,
    StatusAmostra,
    StatusComprovante,
    StatusOperacao,
    TipoAcaoFuncionalidade,
    TipoColeta,
    TipoCombustivel,
    TipoOperacao,
    TipoPlataforma,
    TipoUsuario,
)

# Exemplo de schema base com from_attributes habilitado
class SchemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 1. SCHEMAS: ONBOARDING / CADASTRO DO TERMINAL (ASSINATURA COMERCIAL)
# =============================================================================

class ValidarCodigoAssinaturaRequest(BaseModel):
    codigo: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Código de assinatura recebido do SaaS, ex: ELAION-A3X9-K2M1"
    )

class ValidarCodigoAssinaturaResponse(BaseModel):
    valid: bool = True
    message: str = "Código de ativação válido."


class OrganizacaoDataDTO(BaseModel):
    cnpj: str = Field(
        ...,
        pattern=r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$|^\d{14}$",
        description="CNPJ da organização com máscara (00.000.000/0000-00) ou apenas 14 dígitos numéricos"
    )
    inscricao_estadual: str = Field(
        ...,
        pattern=r"^[0-9./\-]{2,30}$",
        description="Inscrição Estadual contendo caracteres numéricos e separadores comuns"
    )
    cep: str = Field(
        ...,
        pattern=r"^\d{5}-\d{3}$|^\d{8}$",
        description="CEP com máscara (00000-000) ou 8 dígitos numéricos"
    )
    razao_social: str = Field(..., min_length=2, max_length=150)
    nome_fantasia: Optional[str] = Field(..., min_length=0, max_length=150)
    uf: str = Field(..., min_length=2, max_length=2)
    cidade: str = Field(..., max_length=256)
    bairro: str = Field(..., max_length=256)
    logradouro: str = Field(..., max_length=256)
    numero: str = Field(..., max_length=20)
    complemento: Optional[str] = Field(None, max_length=1024)
    telefone: str = Field(..., max_length=20)
    email: EmailStr


class TerminalDataDTO(OrganizacaoDataDTO):
    telefone_financeiro: Optional[str] = Field(None, max_length=20)
    email_financeiro: Optional[EmailStr] = None


class MasterUserDataDTO(BaseModel):
    cnpj: str = Field(..., min_length=14, max_length=18, description="CNPJ vinculado à conta")
    senha: str = Field(..., min_length=8, description="Senha forte de acesso mestre")


class RegistrationPayload(BaseModel):
    codigo_ativacao: str = Field(..., min_length=4, max_length=50, description="Código de assinatura comercial validado no Step 1")
    organizacao: OrganizacaoDataDTO
    terminal: TerminalDataDTO
    usuario_master: MasterUserDataDTO


class RegistrationResponse(BaseModel):
    id: int = Field(..., description="ID da organização criada")
    message: str = "Cadastro realizado com sucesso."



# =============================================================================
# 2. SCHEMAS: AUTENTICAÇÃO E SESSÃO (JWT & COOKIES)
# =============================================================================

class LoginRequest(BaseModel):
    identificador: str = Field(
        ...,
        pattern=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$|^\d{11}$|^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$|^\d{14}$|^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$|^[a-zA-Z0-9._-]{3,}$",
        description="Identificador de login: CPF, CNPJ (com ou sem máscara), e-mail ou username"
    )
    senha: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="Senha do usuário (mínimo 6 caracteres)"
    )


class TerminalVinculoDTO(BaseModel):
    id: int
    codigo: str
    nome: str
    model_config = ConfigDict(from_attributes=True)


class PermissaoFuncionalDTO(BaseModel):
    id: int
    chave: str
    nome: Optional[str] = None
    funcionalidade: Optional[str] = None
    modulo: Optional[str] = None
    tipo_acao: Union[TipoAcaoFuncionalidade, str]
    permitido: bool = True
    model_config = ConfigDict(from_attributes=True)



class UsuarioAutenticadoDTO(BaseModel):
    id: int
    nome: Optional[str] = None
    sobrenome: Optional[str] = None
    email: Optional[str] = None
    cpf: Optional[str] = None
    cnpj: Optional[str] = None
    telefone: Optional[str] = None
    is_master: bool
    tipo_usuario: TipoUsuario
    papel: Optional[PapelUsuario] = None
    status_conta: str
    foto_perfil_url: Optional[str] = None
    precisa_redefinir_senha: bool = False
    terminais: List[TerminalVinculoDTO] = []
    permissoes: List[PermissaoFuncionalDTO] = []
    model_config = ConfigDict(from_attributes=True)



class LoginResponse(BaseModel):
    access_token: str = Field(..., description="JWT Bearer Token de curta duração (15 minutos)")
    token_type: str = "bearer"
    expires_in: int = Field(default=900, description="Tempo de expiração do access token em segundos")
    usuario: UsuarioAutenticadoDTO


class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900


class LogoutResponse(BaseModel):
    mensagem: str = "Sessão encerrada com sucesso."


class TerminalPermissaoDetalheDTO(BaseModel):
    terminal_id: int
    codigo_terminal: str
    nome_fantasia: str
    permissoes: List[str] = []


class UserProfileResponse(BaseModel):
    id: int
    nome: Optional[str] = None
    sobrenome: Optional[str] = None
    cpf: Optional[str] = None
    cnpj: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    foto_perfil_url: Optional[str] = None
    is_master: bool
    tipo_usuario: TipoUsuario
    status_conta: str
    terminais: List[TerminalPermissaoDetalheDTO] = []
    model_config = ConfigDict(from_attributes=True)


class AtualizarPerfilRequest(BaseModel):
    nome: Optional[str] = None
    sobrenome: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    cpf: Optional[str] = None
    foto_perfil_url: Optional[str] = None
    senha_atual: Optional[str] = None
    nova_senha: Optional[str] = None
    confirmacao_senha: Optional[str] = None
    novo_pin: Optional[str] = None
    confirmacao_pin: Optional[str] = None


# =============================================================================
# 3. SCHEMAS: PRIMEIRO ACESSO DO COLABORADOR OPERACIONAL
# =============================================================================

class PrimeiroAcessoValidarRequest(BaseModel):
    cpf: str = Field(..., min_length=11, max_length=11, description="CPF numérico cadastrado pelo Master")
    codigo_ativacao: str = Field(..., min_length=4, max_length=20, description="Código recebido do Master, ex: ATIV-8921")


class PrimeiroAcessoValidarResponse(BaseModel):
    valido: bool = True
    nome_colaborador: str
    mensagem: str = "Código validado. Prossiga para a criação de sua senha pessoal e PIN."


class PrimeiroAcessoConcluirRequest(BaseModel):
    cpf: str = Field(..., min_length=11, max_length=11)
    codigo_ativacao: str = Field(..., min_length=4, max_length=20)
    nova_senha: str = Field(..., min_length=8, description="Senha forte pessoal")
    confirmacao_senha: str = Field(..., min_length=8)
    pin_seguranca: str = Field(..., min_length=4, max_length=6, pattern=r"^\d+$", description="PIN secreto de 4 a 6 dígitos")


class MensagemSucessoResponse(BaseModel):
    sucesso: bool = True
    mensagem: str


# =============================================================================
# 4. SCHEMAS: REDEFINIÇÃO DE SENHA - COLABORADOR (HANDSHAKE 2 FASES)
# =============================================================================

class AutorizarRedefinicaoResponse(BaseModel):
    usuario_id: int
    nome_colaborador: str
    codigo_liberacao: str = Field(..., description="Código de Liberação temporário, ex: LIB-4921")
    expira_em_minutos: int = 15
    orientacao: str = "Informe este código ao colaborador. Ele deverá utilizá-lo junto ao seu PIN pessoal na tela de Redefinição."


class RedefinirSenhaColaboradorRequest(BaseModel):
    cpf: str = Field(..., min_length=11, max_length=11)
    codigo_liberacao: str = Field(..., min_length=4, max_length=20, description="Código LIB-XXXX fornecido pelo gestor")
    pin_seguranca: str = Field(..., min_length=4, max_length=6, pattern=r"^\d+$", description="PIN pessoal secreto cadastrado no 1º acesso")
    nova_senha: str = Field(..., min_length=8)
    confirmacao_senha: str = Field(..., min_length=8)


# =============================================================================
# 5. SCHEMAS: REDEFINIÇÃO DE SENHA - USUÁRIO MASTER (SELF-SERVICE E-MAIL)
# =============================================================================

class RecuperarSenhaMasterRequest(BaseModel):
    identificador: str = Field(..., min_length=3, description="E-mail corporativo ou CPF da conta master")


class ConfirmarSenhaMasterRequest(BaseModel):
    token: str = Field(..., min_length=10, description="Token criptográfico enviado ao e-mail cadastrado")
    nova_senha: str = Field(..., min_length=8)
    confirmacao_senha: str = Field(..., min_length=8)

# =============================================================================
# 6. SCHEMAS: GESTÃO DE COLABORADORES DO TERMINAL (PELO MASTER)
# =============================================================================



class CatalogoPermissoesModuloDTO(BaseModel):
    modulo_id: int
    codigo_modulo: str
    nome_modulo: str
    funcionalidades: List[PermissaoFuncionalDTO]


class CriarUsuarioTerminalRequest(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    sobrenome: str = Field(..., min_length=2, max_length=100)
    cpf: str = Field(
        ...,
        pattern=r"^\d{11}$",
        description="CPF com apenas 11 dígitos numéricos"
    )
    papel: Optional[PapelUsuario] = Field(None, description="Papel/função do colaborador no terminal: Porteiro, Químico, Operador, Adm ou Congênere")
    laboratorio: Optional[Union[int, str]] = Field(None, description="ID ou nome do laboratório vinculado (obrigatório se papel for Químico)")
    congenere: Optional[Union[int, str]] = Field(None, description="ID ou nome da congênere vinculada (obrigatório se papel for Congênere)")
    email: Optional[EmailStr] = Field(None, description="E-mail opcional do colaborador")
    telefone: Optional[str] = None
    foto_perfil_url: Optional[str] = None
    permissoes: List[Union[int, str]] = Field(
        default=[], 
        description="Lista de IDs numéricos ou chaves de permissão do SIRAC (ex: [1, 2, 'sirac:triagem:analisar_amostra'])."
    )


class CriarUsuarioTerminalResponse(BaseModel):
    usuario_id: int
    nome_completo: str
    cpf: str
    papel: Optional[PapelUsuario] = None
    status_conta: str
    codigo_ativacao: str
    orientacao: str = "Entregue o código de ativação ao colaborador para que ele conclua seu Primeiro Acesso."


class UsuarioTerminalResumoDTO(BaseModel):
    id: int
    nome_completo: str
    cpf: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    foto_perfil_url: Optional[str] = None
    papel: Optional[PapelUsuario] = None
    status_conta: str
    ativo: bool
    is_master: bool
    permissoes: List[PermissaoFuncionalDTO] = []
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 7. SCHEMAS: CONGÊNERES (DISTRIBUIDORAS PARCEIRAS DO TERMINAL)
# =============================================================================

class CongenereProdutoDTO(BaseModel):
    combustivel: TipoCombustivel
    aditivado: bool = False
    cor: Optional[str] = Field(None, max_length=50)

    model_config = ConfigDict(from_attributes=True)


class CongenereCreateDTO(BaseModel):
    razao_social: str = Field(..., min_length=2, max_length=150, description="Razão Social da congênere")
    cnpj: str = Field(
        ...,
        pattern=r"^\d{14}$",
        description="CNPJ obrigatório sanitizado, contendo exatamente 14 dígitos numéricos"
    )
    telefone: str = Field(
        ...,
        min_length=8,
        max_length=20,
        description="Telefone de contato principal (apenas números)"
    )
    email: EmailStr = Field(..., description="E-mail principal para contato e envio de laudos/comprovantes")
    
    # Opcionais
    inscricao_estadual: Optional[str] = Field(None, max_length=30)
    telefone_financeiro: Optional[str] = Field(None, max_length=20)
    email_financeiro: Optional[EmailStr] = None
    cep: Optional[str] = Field(None, pattern=r"^\d{8}$", description="CEP com 8 dígitos numéricos")
    logradouro: Optional[str] = Field(None, max_length=150)
    numero: Optional[str] = Field(None, max_length=20)
    complemento: Optional[str] = Field(None, max_length=100)
    bairro: Optional[str] = Field(None, max_length=100)
    cidade: Optional[str] = Field(None, max_length=100)
    uf: Optional[str] = Field(None, min_length=2, max_length=2)
    logo_url: Optional[str] = Field(None, max_length=500)
    ativo: bool = Field(default=True)
    produtos: Optional[List[CongenereProdutoDTO]] = Field(default_factory=list)


class CongenereUpdateDTO(BaseModel):
    razao_social: Optional[str] = Field(None, min_length=2, max_length=150)
    cnpj: Optional[str] = Field(None, pattern=r"^\d{14}$")
    telefone: Optional[str] = Field(None, min_length=8, max_length=20)
    email: Optional[EmailStr] = None
    inscricao_estadual: Optional[str] = Field(None, max_length=30)
    telefone_financeiro: Optional[str] = Field(None, max_length=20)
    email_financeiro: Optional[EmailStr] = None
    cep: Optional[str] = Field(None, pattern=r"^\d{8}$")
    logradouro: Optional[str] = Field(None, max_length=150)
    numero: Optional[str] = Field(None, max_length=20)
    complemento: Optional[str] = Field(None, max_length=100)
    bairro: Optional[str] = Field(None, max_length=100)
    cidade: Optional[str] = Field(None, max_length=100)
    uf: Optional[str] = Field(None, min_length=2, max_length=2)
    logo_url: Optional[str] = Field(None, max_length=500)
    ativo: Optional[bool] = None
    produtos: Optional[List[CongenereProdutoDTO]] = None


class CongenereResponseDTO(BaseModel):
    id: int
    terminal_id: int
    razao_social: str
    cnpj: str
    inscricao_estadual: Optional[str] = None
    telefone: str
    email: str
    telefone_financeiro: Optional[str] = None
    email_financeiro: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    logo_url: Optional[str] = None
    ativo: bool
    produtos: List[CongenereProdutoDTO] = Field(
        default_factory=list,
        validation_alias=AliasChoices("produtos", "produtos_operados"),
    )
    criado_em: datetime
    atualizado_em: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedCongeneresResponseDTO(BaseModel):
    items: List[CongenereResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# 8. SCHEMAS: TERMINAL (DADOS GERAIS E CONFIGURAÇÃO)
# =============================================================================

class TerminalDetalheDTO(BaseModel):
    id: int
    organizacao_id: int
    codigo_terminal: str
    razao_social: str
    nome_fantasia: str
    cnpj: str
    inscricao_estadual: str
    telefone: Optional[str] = None
    telefone_financeiro: Optional[str] = None
    email: Optional[str] = None
    email_financeiro: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    ativo: bool = True
    criado_em: Optional[datetime] = None
    plataformas: List["PlataformaResponseDTO"] = Field(default_factory=list)
    tanques: List["TanqueResponseDTO"] = Field(default_factory=list)
    bicos: List["BicoResponseDTO"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TerminalGeralUpdateDTO(BaseModel):
    codigo_terminal: Optional[str] = Field(None, max_length=50)
    razao_social: Optional[str] = Field(None, min_length=2, max_length=150)
    nome_fantasia: Optional[str] = Field(None, min_length=2, max_length=150)
    cnpj: Optional[str] = Field(None, max_length=20)
    inscricao_estadual: Optional[str] = Field(None, max_length=30)
    telefone: Optional[str] = Field(None, max_length=20)
    telefone_financeiro: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    email_financeiro: Optional[str] = Field(None, max_length=100)
    cep: Optional[str] = Field(None, max_length=20)
    logradouro: Optional[str] = Field(None, max_length=150)
    numero: Optional[str] = Field(None, max_length=20)
    complemento: Optional[str] = Field(None, max_length=100)
    bairro: Optional[str] = Field(None, max_length=100)
    cidade: Optional[str] = Field(None, max_length=100)
    uf: Optional[str] = Field(None, max_length=2)
    ativo: Optional[bool] = None


# =============================================================================
# 9. SCHEMAS: LABORATÓRIOS DO TERMINAL
# =============================================================================

class LaboratorioCreateDTO(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100, description="Nome do laboratório")
    codigo: Optional[str] = Field(None, max_length=50, description="Código identificador (ex: LAB-01)")
    is_proprio: bool = Field(True, description="Indica se é laboratório próprio do terminal ou terceirizado")
    ativo: bool = Field(True, description="Status do laboratório")


class LaboratorioUpdateDTO(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=100, description="Nome do laboratório")
    codigo: Optional[str] = Field(None, max_length=50, description="Código identificador (ex: LAB-01)")
    is_proprio: Optional[bool] = Field(None, description="Indica se é laboratório próprio ou terceirizado")
    ativo: Optional[bool] = Field(None, description="Status do laboratório")


class LaboratorioResponseDTO(BaseModel):
    id: int
    terminal_id: int
    nome: str
    codigo: Optional[str] = None
    is_proprio: bool = True
    ativo: bool = True
    criado_em: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AtualizarTerminalLaboratoriosItemDTO(BaseModel):
    id: Optional[int] = Field(None, description="ID do laboratório (omitir para cadastrar novo)")
    nome: str = Field(..., min_length=1, max_length=100)
    codigo: Optional[str] = Field(None, max_length=50)
    is_proprio: bool = Field(True)
    ativo: bool = Field(True)


class AtualizarTerminalLaboratoriosRequestDTO(BaseModel):
    laboratorios: List[AtualizarTerminalLaboratoriosItemDTO]


# =============================================================================
# 10. SCHEMAS: PLATAFORMAS DE OPERAÇÃO DO TERMINAL
# =============================================================================

class PlataformaCreateDTO(BaseModel):
    identificador: str = Field(..., min_length=1, max_length=50, description="Identificador da plataforma (ex: PL-01)")
    nome: Optional[str] = Field(None, max_length=100, description="Nome descritivo da plataforma/baia")
    tipo: TipoPlataforma = Field(TipoPlataforma.CARREGAMENTO, description="Tipo operacional da plataforma")
    ativo: bool = Field(True, description="Status da plataforma")


class PlataformaUpdateDTO(BaseModel):
    identificador: Optional[str] = Field(None, min_length=1, max_length=50, description="Identificador da plataforma")
    nome: Optional[str] = Field(None, max_length=100, description="Nome descritivo da plataforma/baia")
    tipo: Optional[TipoPlataforma] = Field(None, description="Tipo operacional da plataforma")
    ativo: Optional[bool] = Field(None, description="Status da plataforma")


class PlataformaResponseDTO(BaseModel):
    id: int
    terminal_id: int
    identificador: str
    nome: Optional[str] = None
    tipo: TipoPlataforma
    ativo: bool = True

    model_config = ConfigDict(from_attributes=True)


class AtualizarTerminalPlataformasItemDTO(BaseModel):
    id: Optional[int] = Field(None, description="ID da plataforma (omitir para cadastrar nova)")
    identificador: str = Field(..., min_length=1, max_length=50)
    nome: Optional[str] = Field(None, max_length=100)
    tipo: TipoPlataforma = Field(TipoPlataforma.CARREGAMENTO)
    ativo: bool = Field(True)


class AtualizarTerminalPlataformasRequestDTO(BaseModel):
    plataformas: List[AtualizarTerminalPlataformasItemDTO]


# =============================================================================
# 11. SCHEMAS: TANQUES DE ARMAZENAMENTO DO TERMINAL
# =============================================================================

class TanqueCreateDTO(BaseModel):
    produto: TipoCombustivel = Field(..., description="Enum do combustível (ex: DIESEL_S10_A)")
    produto_id: Optional[int] = Field(None, description="ID do produto (legado/opcional)")
    identificador_tanque: str = Field(..., min_length=1, max_length=50, description="Identificador único no terminal (ex: TQ-101)")
    capacidade_operacional_litros: Decimal = Field(..., gt=0, description="Capacidade máxima operacional em litros")
    capacidade_nominal_litros: Optional[Decimal] = Field(None, gt=0, description="Capacidade física nominal (se omitido, assume o valor operacional)")
    volume_atual_litros: Optional[Decimal] = Field(Decimal("0.00"), ge=0, description="Volume inicial em litros (opcional, gerenciado por medição/telemetria)")
    ativo: bool = Field(True, description="Status do tanque no terminal")


class TanqueUpdateDTO(BaseModel):
    produto: Optional[TipoCombustivel] = Field(None, description="Enum do combustível (ex: DIESEL_S10_A)")
    produto_id: Optional[int] = Field(None, description="ID do produto (legado/opcional)")
    identificador_tanque: Optional[str] = Field(None, min_length=1, max_length=50, description="Identificador do tanque")
    capacidade_operacional_litros: Optional[Decimal] = Field(None, gt=0, description="Capacidade máxima operacional em litros")
    capacidade_nominal_litros: Optional[Decimal] = Field(None, gt=0, description="Capacidade física nominal em litros")
    volume_atual_litros: Optional[Decimal] = Field(None, ge=0, description="Ajuste manual de volume atual (se permitido)")
    ativo: Optional[bool] = Field(None, description="Status do tanque")


class TanqueResponseDTO(BaseModel):
    id: int
    terminal_id: int
    produto: TipoCombustivel = Field(..., description="Enum do combustível associado")
    produto_id: Optional[int] = Field(None, description="ID legado do produto")
    produto_nome: str = Field(..., description="Nome do produto cadastrado (ex: Diesel S10 A)")
    produto_codigo_anp: Optional[str] = Field(None, description="Código ANP do combustível")
    identificador_tanque: str
    capacidade_nominal_litros: Decimal
    capacidade_operacional_litros: Decimal
    volume_atual_litros: Decimal = Decimal("0.00")
    ativo: bool = True

    model_config = ConfigDict(from_attributes=True)


class AtualizarTerminalTanquesItemDTO(BaseModel):
    id: Optional[int] = Field(None, description="ID do tanque existente (omitir para novo cadastro)")
    produto: TipoCombustivel = Field(..., description="Enum do combustível (ex: DIESEL_S10_A)")
    produto_id: Optional[int] = Field(None, description="ID legado do produto")
    identificador_tanque: str = Field(..., min_length=1, max_length=50, description="Identificador do tanque (ex: TQ-101)")
    capacidade_operacional_litros: Decimal = Field(..., gt=0, description="Capacidade operacional em litros")
    capacidade_nominal_litros: Optional[Decimal] = Field(None, description="Capacidade nominal em litros")
    volume_atual_litros: Optional[Decimal] = Field(Decimal("0.00"), description="Volume atual (opcional, mantido por compatibilidade)")
    ativo: bool = Field(True, description="Status de ativação do tanque")


class AtualizarTerminalTanquesRequestDTO(BaseModel):
    tanques: List[AtualizarTerminalTanquesItemDTO] = Field(
        ..., description="Lista completa de tanques a serem sincronizados com o terminal"
    )


# =============================================================================
# 12. SCHEMAS: BICOS E BRAÇOS DE CONEXÃO DO TERMINAL
# =============================================================================

class BicoCreateDTO(BaseModel):
    plataforma_id: int = Field(..., gt=0, description="ID da plataforma/baia onde o bico está instalado")
    tipo_operacao: TipoOperacao = Field(TipoOperacao.CARREGAMENTO, description="Tipo de operação do bico (CARREGAMENTO ou DESCARGA)")
    produto: Optional[TipoCombustivel] = Field(None, description="Enum do combustível (legado/opcional)")
    produto_id: Optional[int] = Field(None, description="ID legado do produto")
    identificador_bico: str = Field(..., min_length=1, max_length=50, description="Identificador único no terminal (ex: BC-01)")
    tanque_ids: List[int] = Field(..., min_length=1, description="Lista de IDs dos tanques conectados (obrigatório ao menos 1)")
    ativo: bool = Field(True, description="Status do bico")


class BicoUpdateDTO(BaseModel):
    plataforma_id: Optional[int] = Field(None, gt=0, description="ID da plataforma/baia")
    tipo_operacao: Optional[TipoOperacao] = Field(None, description="Tipo de operação do bico")
    produto: Optional[TipoCombustivel] = Field(None, description="Enum do combustível operado")
    produto_id: Optional[int] = Field(None, description="ID legado do produto")
    identificador_bico: Optional[str] = Field(None, min_length=1, max_length=50, description="Identificador do bico")
    tanque_ids: Optional[List[int]] = Field(None, min_length=1, description="Lista de IDs dos tanques conectados")
    ativo: Optional[bool] = Field(None, description="Status do bico")


class BicoResponseDTO(BaseModel):
    id: int
    terminal_id: int
    plataforma_id: int
    plataforma_identificador: str
    tipo_operacao: TipoOperacao = Field(TipoOperacao.CARREGAMENTO, description="Tipo de operação do bico")
    produtos_operados: List[str] = Field(default_factory=list, description="Lista dos combustíveis presentes nos tanques vinculados")
    produto: Optional[TipoCombustivel] = Field(None, description="Enum do combustível (opcional/legado)")
    produto_id: Optional[int] = Field(None, description="ID legado do produto")
    produto_nome: Optional[str] = Field(None, description="Combustíveis vinculados (formatado)")
    tanque_ids: List[int] = Field(default_factory=list)
    tanques_identificadores: List[str] = Field(default_factory=list)
    identificador_bico: str
    ativo: bool = True

    model_config = ConfigDict(from_attributes=True)


class AtualizarTerminalBicosItemDTO(BaseModel):
    id: Optional[int] = Field(None, description="ID do bico existente (omitir para novo cadastro)")
    plataforma_id: int = Field(..., gt=0, description="ID da plataforma/baia")
    tipo_operacao: TipoOperacao = Field(TipoOperacao.CARREGAMENTO, description="Tipo de operação do bico")
    produto: Optional[TipoCombustivel] = Field(None, description="Enum do combustível")
    produto_id: Optional[int] = Field(None, description="ID legado do produto")
    identificador_bico: str = Field(..., min_length=1, max_length=50, description="Identificador do bico (ex: BC-01)")
    tanque_ids: List[int] = Field(..., min_length=1, description="Lista de IDs dos tanques vinculados (obrigatório ao menos 1)")
    ativo: bool = Field(True, description="Status de ativação do bico")


class AtualizarTerminalBicosRequestDTO(BaseModel):
    bicos: List[AtualizarTerminalBicosItemDTO] = Field(
        ..., description="Lista completa de bicos a serem sincronizados com o terminal"
    )


# =============================================================================
# 11. SCHEMAS: CONTROLE DE ACESSO AO TERMINAL
# =============================================================================

class ControleAcessoFiltrosDTO(BaseModel):
    """Parâmetros de filtro e busca para a listagem do controle de acesso."""
    data: date = Field(
        default_factory=date.today,
        description="Data de referência para as operações (default: data atual)",
    )
    busca: Optional[str] = Field(
        None,
        description="Busca textual por motorista, placa, transportadora ou distribuidora congênere",
    )
    estados: Optional[List[EstadoVeiculo]] = Field(
        None,
        description="Filtro por macro-estados do veículo na portaria (ex: AGUARDANDO, ENTRADA, COLETA, SAIDA, CANCELADO)",
    )
    operacoes: Optional[List[TipoOperacao]] = Field(
        None,
        description="Filtro por tipo de operação (CARREGAMENTO, DESCARGA)",
    )
    produtos: Optional[List[TipoCombustivel]] = Field(
        None,
        description="Filtro por combustíveis presentes nos compartimentos",
    )
    page: int = Field(1, ge=1, description="Número da página (1-based)")
    page_size: int = Field(10, ge=1, le=100, description="Quantidade de registros por página")


# Alias mantido para compatibilidade
ControleAcessoListagemRequestDTO = ControleAcessoFiltrosDTO


class ControleAcessoItemDTO(BaseModel):
    """Representação de um registro de veículo/operação na portaria do terminal."""
    id: int = Field(..., description="ID da operação do veículo")
    terminal_id: int = Field(..., description="ID do terminal ativo")
    estado: EstadoVeiculo = Field(
        EstadoVeiculo.AGUARDANDO,
        description="Macro-estado do veículo na portaria (AGUARDANDO, ENTRADA, COLETA, SAIDA, CANCELADO)",
    )
    status_operacao: StatusOperacao = Field(
        StatusOperacao.AGUARDANDO_PORTARIA,
        description="Status operacional detalhado do pátio/laboratório",
    )
    tipo_operacao: TipoOperacao = Field(
        TipoOperacao.CARREGAMENTO,
        description="Tipo de operação: CARREGAMENTO ou DESCARGA",
    )
    data_hora: datetime = Field(
        ...,
        description="Data e hora do registro ou entrada do veículo",
    )
    motorista: str = Field(..., description="Nome completo do motorista")
    placa: str = Field(
        ...,
        validation_alias=AliasChoices("placa", "placa_veiculo"),
        description="Placa do cavalo mecânico / veículo",
    )
    numero_nf: str = Field(
        ...,
        validation_alias=AliasChoices("numero_nf", "numero_nota_fiscal"),
        description="Número da nota fiscal de transporte",
    )
    congenere: str = Field(..., description="Nome da distribuidora congênere")
    congenere_id: Optional[int] = Field(None, description="ID da congênere")
    transportadora: str = Field(
        ...,
        validation_alias=AliasChoices("transportadora", "nome_transportadora"),
        description="Nome da transportadora",
    )
    is_propria: bool = Field(
        False,
        validation_alias=AliasChoices("is_propria", "is_transportadora_propria"),
        description="Indica se o frete é por frota própria",
    )
    produtos: List[TipoCombustivel] = Field(
        default_factory=list,
        description="Lista de combustíveis transportados nos compartimentos",
    )
    volume_nf: Decimal = Field(
        ...,
        description="Volume total faturado na nota fiscal (em litros)",
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "terminal_id": 1,
                "estado": "AGUARDANDO",
                "status_operacao": "AGUARDANDO_PORTARIA",
                "tipo_operacao": "CARREGAMENTO",
                "data_hora": "2026-09-10T08:30:00Z",
                "motorista": "Juliana Ferreira",
                "placa": "PQR2345",
                "numero_nf": "000128",
                "congenere": "Larco",
                "congenere_id": 2,
                "transportadora": "Transportadora Rodobrás",
                "is_propria": False,
                "produtos": ["DIESEL_S10_A", "ETANOL_HIDRATADO"],
                "volume_nf": "9800.00",
            }
        },
    )


# Alias mantido para compatibilidade com o rascunho anterior
ControleAcessoResponseDTO = ControleAcessoItemDTO


class PaginatedControleAcessoResponseDTO(BaseModel):
    """Envelope paginado de registros do controle de acesso."""
    items: List[ControleAcessoItemDTO] = Field(
        default_factory=list, description="Lista paginada de registros"
    )
    total: int = Field(..., description="Total geral de registros que atendem aos filtros")
    page: int = Field(..., ge=1, description="Página atual")
    page_size: int = Field(..., ge=1, description="Tamanho da página")
    total_pages: int = Field(..., ge=0, description="Total de páginas disponíveis")


class ControleAcessoContagensResponseDTO(BaseModel):
    """Contadores para os seletores de abas e resumo operacional do dia."""
    AGUARDANDO: int = Field(0, description="Veículos agendados aguardando portaria")
    ENTRADA: int = Field(0, description="Veículos que deram entrada no pátio")
    COLETA: int = Field(0, description="Veículos em etapa de coleta/amostragem")
    SAIDA: int = Field(0, description="Veículos que concluíram a operação e saíram")
    CANCELADO: int = Field(0, description="Operações canceladas/rejeitadas")
    total: int = Field(0, description="Total geral de veículos registrados no dia")


class TransicaoEstadoControleAcessoRequestDTO(BaseModel):
    """Payload para transição de estado do veículo pela portaria."""
    estado: EstadoVeiculo = Field(
        ..., description="Novo estado para o qual o veículo deve transitar (ex: ENTRADA, SAIDA)"
    )
    observacao: Optional[str] = Field(None, description="Observação opcional da portaria")


TerminalDetalheDTO.model_rebuild()

