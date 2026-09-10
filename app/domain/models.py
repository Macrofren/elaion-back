"""
Modelos ORM do Banco de Dados Relacional - Elaion (Versão 2 / Atualizada)
Mapeamento feito via SQLAlchemy 2.0 (Declarative Base)
Compatível com PostgreSQL (asyncpg / psycopg) e Clean Architecture.
"""

from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Classe base declarativa para os modelos SQLAlchemy v2."""
    pass


# =============================================================================
# ENUMS DE DOMÍNIO
# =============================================================================

class PapelUsuario(str, PyEnum):
    PORTEIRO = "Porteiro"
    QUIMICO = "Químico"
    OPERADOR = "Operador"
    ADM = "Adm"
    CONGENERE = "Congênere"


class TipoUsuario(str, PyEnum):
    ADMIN_SISTEMA = "ADMIN_SISTEMA"
    USUARIO_TERMINAL = "USUARIO_TERMINAL"
    CLIENTE_CONGENERE = "CLIENTE_CONGENERE"


class TipoAcaoFuncionalidade(str, PyEnum):
    VISUALIZAR = "VISUALIZAR"
    CRIAR = "CRIAR"
    EDITAR = "EDITAR"
    APROVAR = "APROVAR"
    EXCLUIR = "EXCLUIR"


class CategoriaProduto(str, PyEnum):
    GASOLINA = "GASOLINA"
    ETANOL = "ETANOL"
    DIESEL = "DIESEL"
    BIODIESEL = "BIODIESEL"


class TipoCombustivel(str, PyEnum):
    GASOLINA_A = "GASOLINA_A"
    DIESEL_S10_A = "DIESEL_S10_A"
    DIESEL_S500_A = "DIESEL_S500_A"
    ETANOL_ANIDRO = "ETANOL_ANIDRO"
    ETANOL_HIDRATADO = "ETANOL_HIDRATADO"


NOMES_COMBUSTIVEIS: dict[TipoCombustivel, str] = {
    TipoCombustivel.GASOLINA_A: "Gasolina A",
    TipoCombustivel.DIESEL_S10_A: "Diesel S10 A",
    TipoCombustivel.DIESEL_S500_A: "Diesel S500 A",
    TipoCombustivel.ETANOL_ANIDRO: "Etanol Anidro",
    TipoCombustivel.ETANOL_HIDRATADO: "Etanol Hidratado",
}

CODIGOS_ANP_COMBUSTIVEIS: dict[TipoCombustivel, str] = {
    TipoCombustivel.GASOLINA_A: "320101001",
    TipoCombustivel.DIESEL_S10_A: "420101004",
    TipoCombustivel.DIESEL_S500_A: "420102004",
    TipoCombustivel.ETANOL_ANIDRO: "610101001",
    TipoCombustivel.ETANOL_HIDRATADO: "610101002",
}


class TipoPlataforma(str, PyEnum):
    DESCARGA = "DESCARGA"
    CARREGAMENTO = "CARREGAMENTO"
    MISTA = "MISTA"


class TipoOperacao(str, PyEnum):
    DESCARGA = "DESCARGA"
    CARREGAMENTO = "CARREGAMENTO"


class StatusOperacao(str, PyEnum):
    AGUARDANDO_PORTARIA = "AGUARDANDO_PORTARIA"
    EM_AMOSTRAGEM = "EM_AMOSTRAGEM"
    EM_ANALISE_LAB = "EM_ANALISE_LAB"
    APROVADO_OPERACAO = "APROVADO_OPERACAO"
    EM_OPERACAO = "EM_OPERACAO"
    CONCLUIDO = "CONCLUIDO"
    REPROVADO = "REPROVADO"
    CANCELADO = "CANCELADO"


class EstadoVeiculo(str, PyEnum):
    AGUARDANDO = "AGUARDANDO"
    ENTRADA = "ENTRADA"
    COLETA = "COLETA"
    SAIDA = "SAIDA"
    CANCELADO = "CANCELADO"


class TipoColeta(str, PyEnum):
    CORRIDO = "CORRIDO"
    TOPO = "TOPO"
    MEIO = "MEIO"
    FUNDO = "FUNDO"


class StatusAmostra(str, PyEnum):
    AGUARDANDO_ANALISE = "AGUARDANDO_ANALISE"
    EM_ANALISE = "EM_ANALISE"
    APROVADA = "APROVADA"
    REPROVADA = "REPROVADA"
    RECOLETA_SOLICITADA = "RECOLETA_SOLICITADA"


class ParecerLaudo(str, PyEnum):
    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONFORME = "CONFORME"
    NAO_CONFORME = "NAO_CONFORME"
    RECOLETA = "RECOLETA"


class StatusComprovante(str, PyEnum):
    PENDENTE = "PENDENTE"
    DISPONIVEL = "DISPONIVEL"
    CANCELADO = "CANCELADO"


class AcaoAuditoria(str, PyEnum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

class OrigemMP(str, PyEnum):
    VEGETAL = "VEGETAL"
    ANIMAL = "ANIMAL"
    


# =============================================================================
# 1. MULTI-TENANCY, MÓDULOS E PERMISSÕES (RBAC)
# =============================================================================

class Organizacao(Base):
    """
    Entidade: organizacao
    Descrição: Empresa dona da conta SaaS / mantenedora dos terminais de combustíveis.
    """
    __tablename__ = "organizacao"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    razao_social: Mapped[str] = mapped_column(String(150), nullable=False)
    nome_fantasia: Mapped[str] = mapped_column(String(150), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, nullable=False, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Relacionamentos
    terminais: Mapped[List["Terminal"]] = relationship(back_populates="organizacao", cascade="all, delete-orphan")
    convite: Mapped[Optional["ConviteCadastro"]] = relationship(back_populates="organizacao", uselist=False)

    def __repr__(self) -> str:
        return f"<Organizacao(id={self.id}, nome='{self.nome_fantasia}', cnpj='{self.cnpj}')>"


class ConviteCadastro(Base):
    """
    Entidade: convite_cadastro
    Descrição: Código de assinatura comercial emitido pelo SaaS (ex: ELAION-A3X9-K2M1)
    necessário para autorizar o cadastro (onboarding) de uma nova organização/terminal.
    """
    __tablename__ = "convite_cadastro"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    utilizado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    utilizado_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    organizacao_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("organizacao.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    expira_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Relacionamentos
    organizacao: Mapped[Optional["Organizacao"]] = relationship(back_populates="convite")

    def __repr__(self) -> str:
        return f"<ConviteCadastro(id={self.id}, codigo='{self.codigo}', utilizado={self.utilizado})>"


class ModuloAssinatura(Base):
    """
    Entidade: modulo_assinatura
    Descrição: Catálogo global dos módulos comercializados no sistema (ex: Operação de Pátio, Laboratório, SICOF).
    """
    __tablename__ = "modulo_assinatura"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relacionamentos
    funcionalidades: Mapped[List["ModuloFuncionalidade"]] = relationship(
        back_populates="modulo", cascade="all, delete-orphan"
    )
    contratos: Mapped[List["TerminalModuloContratado"]] = relationship(
        back_populates="modulo", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ModuloAssinatura(id={self.id}, codigo='{self.codigo}', nome='{self.nome}')>"


class ModuloFuncionalidade(Base):
    """
    Entidade: modulo_funcionalidade
    Descrição: Funcionalidades e ações específicas pertencentes a cada módulo.
    """
    __tablename__ = "modulo_funcionalidade"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    modulo_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("modulo_assinatura.id", ondelete="CASCADE"), nullable=False
    )
    chave: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo_acao: Mapped[TipoAcaoFuncionalidade] = mapped_column(
        Enum(TipoAcaoFuncionalidade, native_enum=False), nullable=False
    )

    # Relacionamentos
    modulo: Mapped["ModuloAssinatura"] = relationship(back_populates="funcionalidades")
    permissoes_usuarios: Mapped[List["UsuarioPermissao"]] = relationship(
        back_populates="funcionalidade", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ModuloFuncionalidade(id={self.id}, chave='{self.chave}', acao='{self.tipo_acao}')>"


class Terminal(Base):
    """
    Entidade: terminal
    Descrição: Unidade operacional física do terminal de recebimento e armazenagem.
    """
    __tablename__ = "terminal"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organizacao_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organizacao.id", ondelete="CASCADE"), nullable=False
    )
    codigo_terminal: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    razao_social: Mapped[str] = mapped_column(String(150), nullable=False)
    nome_fantasia: Mapped[str] = mapped_column(String(150), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(14), nullable=False)
    inscricao_estadual: Mapped[str] = mapped_column(String(30), nullable=False)
    telefone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    telefone_financeiro: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email_financeiro: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cep: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    logradouro: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    numero: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    complemento: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bairro: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cidade: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    uf: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("organizacao_id", "codigo_terminal", name="uq_terminal_org_codigo"),
    )

    # Relacionamentos
    organizacao: Mapped["Organizacao"] = relationship(back_populates="terminais")
    modulos_contratados: Mapped[List["TerminalModuloContratado"]] = relationship(
        back_populates="terminal", cascade="all, delete-orphan"
    )
    usuarios_vinculados: Mapped[List["UsuarioTerminal"]] = relationship(
        back_populates="terminal", cascade="all, delete-orphan"
    )
    laboratorios: Mapped[List["Laboratorio"]] = relationship(
        back_populates="terminal", cascade="all, delete-orphan"
    )
    congeneres: Mapped[List["Congenere"]] = relationship(
        back_populates="terminal", cascade="all, delete-orphan"
    )
    plataformas: Mapped[List["Plataforma"]] = relationship(
        back_populates="terminal", cascade="all, delete-orphan"
    )
    tanques: Mapped[List["Tanque"]] = relationship(
        back_populates="terminal", cascade="all, delete-orphan"
    )
    bicos: Mapped[List["Bico"]] = relationship(
        back_populates="terminal", cascade="all, delete-orphan"
    )
    produtos_operados: Mapped[List["TerminalProduto"]] = relationship(
        back_populates="terminal", cascade="all, delete-orphan"
    )
    operacoes: Mapped[List["OperacaoVeiculo"]] = relationship(
        back_populates="terminal"
    )
    auditorias: Mapped[List["AuditoriaLog"]] = relationship(
        back_populates="terminal"
    )

    def __repr__(self) -> str:
        return f"<Terminal(id={self.id}, nome='{self.nome_fantasia}', codigo='{self.codigo_terminal}')>"


class TerminalModuloContratado(Base):
    """
    Entidade: terminal_modulo_contratado
    Descrição: Módulos contratados pelo terminal e seu período de vigência.
    """
    __tablename__ = "terminal_modulo_contratado"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    terminal_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("terminal.id", ondelete="CASCADE"), nullable=False
    )
    modulo_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("modulo_assinatura.id", ondelete="CASCADE"), nullable=False
    )
    data_inicio: Mapped[date] = mapped_column(Date, default=func.current_date(), nullable=False)
    data_fim: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("terminal_id", "modulo_id", name="uq_terminal_modulo"),
    )

    # Relacionamentos
    terminal: Mapped["Terminal"] = relationship(back_populates="modulos_contratados")
    modulo: Mapped["ModuloAssinatura"] = relationship(back_populates="contratos")


class Usuario(Base):
    """
    Entidade: usuario
    Descrição: Cadastro central de colaboradores, operadores, químicos e parceiros.
    """
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sobrenome: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(150), unique=True, nullable=True, index=True)
    cpf: Mapped[Optional[str]] = mapped_column(String(11), unique=True, nullable=True, index=True)
    cnpj: Mapped[Optional[str]] = mapped_column(String(14), unique=True, nullable=True, index=True)
    telefone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    foto_perfil_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    papel: Mapped[Optional[PapelUsuario]] = mapped_column(
        Enum(PapelUsuario, native_enum=False), nullable=True
    )
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    pin_seguranca_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    codigo_ativacao: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    codigo_liberacao_master: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    liberacao_expira_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status_conta: Mapped[str] = mapped_column(String(30), default="PENDENTE_ATIVACAO", nullable=False, index=True)
    tipo_usuario: Mapped[TipoUsuario] = mapped_column(
        Enum(TipoUsuario, native_enum=False), default=TipoUsuario.USUARIO_TERMINAL, nullable=False
    )
    is_master: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Relacionamentos
    terminais_acesso: Mapped[List["UsuarioTerminal"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Usuario(id={self.id}, cpf='{self.cpf}', status='{self.status_conta}')>"


class UsuarioTerminal(Base):
    """
    Entidade: usuario_terminal
    Descrição: Associação de acesso do usuário a um determinado terminal (sem cargo rígido).
    """
    __tablename__ = "usuario_terminal"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False
    )
    terminal_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("terminal.id", ondelete="CASCADE"), nullable=False
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("usuario_id", "terminal_id", name="uq_usuario_terminal"),
    )

    # Relacionamentos
    usuario: Mapped["Usuario"] = relationship(back_populates="terminais_acesso")
    terminal: Mapped["Terminal"] = relationship(back_populates="usuarios_vinculados")
    permissoes: Mapped[List["UsuarioPermissao"]] = relationship(
        back_populates="usuario_terminal", cascade="all, delete-orphan"
    )


class UsuarioPermissao(Base):
    """
    Entidade: usuario_permissao
    Descrição: Permissões funcionais diretas atribuídas ao usuário no terminal pelo usuário master.
    """
    __tablename__ = "usuario_permissao"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    usuario_terminal_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario_terminal.id", ondelete="CASCADE"), nullable=False
    )
    funcionalidade_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("modulo_funcionalidade.id", ondelete="CASCADE"), nullable=False
    )
    permitido: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("usuario_terminal_id", "funcionalidade_id", name="uq_usuario_funcionalidade"),
    )

    # Relacionamentos
    usuario_terminal: Mapped["UsuarioTerminal"] = relationship(back_populates="permissoes")
    funcionalidade: Mapped["ModuloFuncionalidade"] = relationship(back_populates="permissoes_usuarios")


# =============================================================================
# 2. ESTRUTURA FÍSICA E CADASTROS DE APOIO
# =============================================================================

class Laboratorio(Base):
    """
    Entidade: laboratorio
    Descrição: Laboratórios vinculados ao terminal para ensaios físico-químicos.
    """
    __tablename__ = "laboratorio"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    terminal_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("terminal.id", ondelete="CASCADE"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    codigo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_proprio: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    # Relacionamentos
    terminal: Mapped["Terminal"] = relationship(back_populates="laboratorios")
    analises: Mapped[List["AnaliseAmostra"]] = relationship(back_populates="laboratorio")


class Congenere(Base):
    """
    Entidade: congenere
    Descrição: Distribuidoras e clientes proprietárias das cargas e combustíveis.
    """
    __tablename__ = "congenere"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    terminal_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("terminal.id", ondelete="CASCADE"), nullable=False
    )
    razao_social: Mapped[str] = mapped_column(String(150), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(14), nullable=False, index=True)
    inscricao_estadual: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    
    # Contatos
    telefone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    telefone_financeiro: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email_financeiro: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Endereço
    cep: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    logradouro: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    numero: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    complemento: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bairro: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cidade: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    uf: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)

    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    atualizado_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    __table_args__ = (
        UniqueConstraint("terminal_id", "cnpj", name="uq_congenere_terminal_cnpj"),
    )

    # Relacionamentos
    terminal: Mapped["Terminal"] = relationship(back_populates="congeneres")
    operacoes: Mapped[List["OperacaoVeiculo"]] = relationship(back_populates="congenere")
    produtos_operados: Mapped[List["CongenereProduto"]] = relationship(
        back_populates="congenere", cascade="all, delete-orphan", lazy="selectin"
    )


class CongenereProduto(Base):
    """
    Entidade: congenere_produto
    Descrição: Combustíveis operados por cada congênere no terminal, com indicação de aditivação e cor.
    """
    __tablename__ = "congenere_produto"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    congenere_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("congenere.id", ondelete="CASCADE"), nullable=False
    )
    combustivel: Mapped[TipoCombustivel] = mapped_column(
        Enum(TipoCombustivel, native_enum=False), nullable=False
    )
    aditivado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cor: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    __table_args__ = (
        UniqueConstraint("congenere_id", "combustivel", name="uq_congenere_combustivel"),
    )

    # Relacionamentos
    congenere: Mapped["Congenere"] = relationship(back_populates="produtos_operados")

    def __repr__(self) -> str:
        return f"<CongenereProduto(id={self.id}, congenere_id={self.congenere_id}, combustivel='{self.combustivel}', aditivado={self.aditivado}, cor='{self.cor}')>"


class Produto(Base):
    """
    Entidade: produto
    Descrição: Catálogo mestre de combustíveis e derivados de petróleo.
    """
    __tablename__ = "produto"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    codigo_anp: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    categoria: Mapped[CategoriaProduto] = mapped_column(
        Enum(CategoriaProduto, native_enum=False), nullable=False
    )
    unidade_medida: Mapped[str] = mapped_column(String(10), default="L", nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relacionamentos
    tanques: Mapped[List["Tanque"]] = relationship(back_populates="produto_rel")
    bicos: Mapped[List["Bico"]] = relationship(back_populates="produto_rel")
    terminais_vinculados: Mapped[List["TerminalProduto"]] = relationship(back_populates="produto")

    def __repr__(self) -> str:
        return f"<Produto(id={self.id}, codigo_anp='{self.codigo_anp}', nome='{self.nome}')>"


class TerminalProduto(Base):
    """
    Entidade: terminal_produto
    Descrição: Associação entre produtos do catálogo e os terminais que os operam.
    """
    __tablename__ = "terminal_produto"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    terminal_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("terminal.id", ondelete="CASCADE"), nullable=False
    )
    produto_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("produto.id", ondelete="RESTRICT"), nullable=False
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("terminal_id", "produto_id", name="uq_terminal_produto"),
    )

    # Relacionamentos
    terminal: Mapped["Terminal"] = relationship(back_populates="produtos_operados")
    produto: Mapped["Produto"] = relationship(back_populates="terminais_vinculados")


class Plataforma(Base):
    """
    Entidade: plataforma
    Descrição: Baias e ilhas físicas de operação no pátio do terminal.
    """
    __tablename__ = "plataforma"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    terminal_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("terminal.id", ondelete="CASCADE"), nullable=False
    )
    identificador: Mapped[str] = mapped_column(String(50), nullable=False)
    nome: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tipo: Mapped[TipoPlataforma] = mapped_column(
        Enum(TipoPlataforma, native_enum=False), default=TipoPlataforma.MISTA, nullable=False
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relacionamentos
    terminal: Mapped["Terminal"] = relationship(back_populates="plataformas")
    bicos: Mapped[List["Bico"]] = relationship(back_populates="plataforma", cascade="all, delete-orphan")


class Tanque(Base):
    """
    Entidade: tanque
    Descrição: Tanques de armazenamento físico situados no terminal.
    """
    __tablename__ = "tanque"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    terminal_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("terminal.id", ondelete="CASCADE"), nullable=False
    )
    produto: Mapped[TipoCombustivel] = mapped_column(
        Enum(TipoCombustivel, native_enum=False), default=TipoCombustivel.DIESEL_S10_A, nullable=False
    )
    produto_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("produto.id", ondelete="SET NULL"), nullable=True
    )
    identificador_tanque: Mapped[str] = mapped_column(String(50), nullable=False)
    capacidade_nominal_litros: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    capacidade_operacional_litros: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    volume_atual_litros: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relacionamentos
    terminal: Mapped["Terminal"] = relationship(back_populates="tanques")
    produto_rel: Mapped[Optional["Produto"]] = relationship(back_populates="tanques")
    vinculos_bicos: Mapped[List["BicoTanqueVinculo"]] = relationship(
        back_populates="tanque", cascade="all, delete-orphan"
    )
    alocacoes_comprovante: Mapped[List["ComprovanteTanqueAlocacao"]] = relationship(
        back_populates="tanque"
    )

    @property
    def produto_nome(self) -> str:
        if self.produto in NOMES_COMBUSTIVEIS:
            return NOMES_COMBUSTIVEIS[self.produto]
        produto_rel = self.__dict__.get("produto_rel")
        if produto_rel:
            return produto_rel.nome
        return str(self.produto) if self.produto else "Combustível"

    @property
    def produto_codigo_anp(self) -> Optional[str]:
        if self.produto in CODIGOS_ANP_COMBUSTIVEIS:
            return CODIGOS_ANP_COMBUSTIVEIS[self.produto]
        produto_rel = self.__dict__.get("produto_rel")
        if produto_rel:
            return produto_rel.codigo_anp
        return None

    def __repr__(self) -> str:
        return f"<Tanque(id={self.id}, identificador='{self.identificador_tanque}', volume={self.volume_atual_litros})>"


class Bico(Base):
    """
    Entidade: bico
    Descrição: Braços de conexão e pontos de descarga/carregamento instalados nas plataformas.
    """
    __tablename__ = "bico"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    terminal_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("terminal.id", ondelete="CASCADE"), nullable=False
    )
    plataforma_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("plataforma.id", ondelete="CASCADE"), nullable=False
    )
    tipo_operacao: Mapped[TipoOperacao] = mapped_column(
        Enum(TipoOperacao, native_enum=False), default=TipoOperacao.CARREGAMENTO, nullable=False
    )
    produto: Mapped[Optional[TipoCombustivel]] = mapped_column(
        Enum(TipoCombustivel, native_enum=False), default=None, nullable=True
    )
    produto_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("produto.id", ondelete="SET NULL"), nullable=True
    )
    identificador_bico: Mapped[str] = mapped_column(String(50), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relacionamentos
    terminal: Mapped["Terminal"] = relationship(back_populates="bicos")
    plataforma: Mapped["Plataforma"] = relationship(back_populates="bicos")
    produto_rel: Mapped[Optional["Produto"]] = relationship(back_populates="bicos")
    vinculos_tanques: Mapped[List["BicoTanqueVinculo"]] = relationship(
        back_populates="bico", cascade="all, delete-orphan"
    )
    alocacoes_comprovante: Mapped[List["ComprovanteTanqueAlocacao"]] = relationship(
        back_populates="bico"
    )

    @property
    def plataforma_identificador(self) -> str:
        plataforma = self.__dict__.get("plataforma")
        if plataforma:
            return plataforma.identificador
        return ""

    @property
    def produtos_operados(self) -> List[str]:
        vinculos = self.__dict__.get("vinculos_tanques")
        if not vinculos:
            return []
        nomes: List[str] = []
        for v in vinculos:
            tanque = v.__dict__.get("tanque")
            if v.ativo and tanque and tanque.produto_nome:
                if tanque.produto_nome not in nomes:
                    nomes.append(tanque.produto_nome)
        return nomes

    @property
    def produto_nome(self) -> str:
        if self.produtos_operados:
            return ", ".join(self.produtos_operados)
        if self.produto in NOMES_COMBUSTIVEIS:
            return NOMES_COMBUSTIVEIS[self.produto]
        produto_rel = self.__dict__.get("produto_rel")
        if produto_rel:
            return produto_rel.nome
        return ""

    @property
    def tanque_ids(self) -> List[int]:
        vinculos = self.__dict__.get("vinculos_tanques")
        if not vinculos:
            return []
        return [v.tanque_id for v in vinculos if v.ativo]

    @property
    def tanques_identificadores(self) -> List[str]:
        vinculos = self.__dict__.get("vinculos_tanques")
        if not vinculos:
            return []
        nomes: List[str] = []
        for v in vinculos:
            tanque = v.__dict__.get("tanque")
            if v.ativo and tanque:
                nomes.append(tanque.identificador_tanque)
        return nomes

    def __repr__(self) -> str:
        return f"<Bico(id={self.id}, identificador='{self.identificador_bico}', terminal_id={self.terminal_id})>"


class BicoTanqueVinculo(Base):
    """
    Entidade: bico_tanque_vinculo
    Descrição: Mapeamento de tubulação/manifold entre bicos e tanques de destino.
    """
    __tablename__ = "bico_tanque_vinculo"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bico_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("bico.id", ondelete="CASCADE"), nullable=False
    )
    tanque_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tanque.id", ondelete="CASCADE"), nullable=False
    )
    is_padrao: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("bico_id", "tanque_id", name="uq_bico_tanque"),
    )

    # Relacionamentos
    bico: Mapped["Bico"] = relationship(back_populates="vinculos_tanques")
    tanque: Mapped["Tanque"] = relationship(back_populates="vinculos_bicos")


# =============================================================================
# 3. OPERAÇÃO DE PÁTIO (DESCARGA E CARREGAMENTO)
# =============================================================================

class OperacaoVeiculo(Base):
    """
    Entidade: operacao_veiculo
    Descrição: Registro da viagem/atendimento do caminhão-tanque no terminal (Descarga ou Carregamento).
    """
    __tablename__ = "operacao_veiculo"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    terminal_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("terminal.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    congenere_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("congenere.id", ondelete="RESTRICT"), nullable=False
    )
    nome_transportadora: Mapped[str] = mapped_column(String(150), nullable=False)
    is_transportadora_propria: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    placa_veiculo: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    nome_motorista: Mapped[str] = mapped_column(String(150), nullable=False)
    numero_nota_fiscal: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    origem_destino: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo_operacao: Mapped[TipoOperacao] = mapped_column(
        Enum(TipoOperacao, native_enum=False), default=TipoOperacao.DESCARGA, nullable=False
    )
    status_operacao: Mapped[StatusOperacao] = mapped_column(
        Enum(StatusOperacao, native_enum=False), default=StatusOperacao.AGUARDANDO_PORTARIA, nullable=False
    )
    data_hora_entrada: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    data_hora_saida: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    observacao_geral: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    motivo_cancelamento: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_registro_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    usuario_liberacao_saida_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )

    __table_args__ = (
        Index("idx_operacao_terminal_data", "terminal_id", "data_hora_entrada"),
    )

    # Relacionamentos
    terminal: Mapped["Terminal"] = relationship(back_populates="operacoes")
    congenere: Mapped["Congenere"] = relationship(back_populates="operacoes")
    usuario_registro: Mapped["Usuario"] = relationship(foreign_keys=[usuario_registro_id])
    usuario_liberacao_saida: Mapped[Optional["Usuario"]] = relationship(foreign_keys=[usuario_liberacao_saida_id])
    compartimentos: Mapped[List["OperacaoCompartimento"]] = relationship(
        back_populates="operacao", cascade="all, delete-orphan"
    )
    historico_status: Mapped[List["OperacaoStatusHistorico"]] = relationship(
        back_populates="operacao", cascade="all, delete-orphan"
    )
    amostras: Mapped[List["Amostra"]] = relationship(
        back_populates="operacao", cascade="all, delete-orphan"
    )
    comprovantes: Mapped[List["ComprovanteOperacao"]] = relationship(
        back_populates="operacao"
    )

    def __repr__(self) -> str:
        return f"<OperacaoVeiculo(id={self.id}, placa='{self.placa_trator}', tipo='{self.tipo_operacao}', status='{self.status_operacao}')>"


class OperacaoCompartimento(Base):
    """
    Entidade: operacao_compartimento
    Descrição: Compartimentos físicos do caminhão-tanque nesta viagem específica.
    """
    __tablename__ = "operacao_compartimento"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    operacao_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("operacao_veiculo.id", ondelete="CASCADE"), nullable=False
    )
    numero_compartimento: Mapped[int] = mapped_column(Integer, nullable=False)
    produto_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("produto.id", ondelete="RESTRICT"), nullable=False
    )
    volume_nf_litros: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    capacidade_compartimento_litros: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

    __table_args__ = (
        UniqueConstraint("operacao_id", "numero_compartimento", name="uq_operacao_num_compartimento"),
    )

    # Relacionamentos
    operacao: Mapped["OperacaoVeiculo"] = relationship(back_populates="compartimentos")
    produto: Mapped["Produto"] = relationship()
    amostras: Mapped[List["Amostra"]] = relationship(
        back_populates="compartimento", cascade="all, delete-orphan"
    )


class OperacaoStatusHistorico(Base):
    """
    Entidade: operacao_status_historico
    Descrição: Rastreabilidade das transições de status da operação no pátio.
    """
    __tablename__ = "operacao_status_historico"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    operacao_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("operacao_veiculo.id", ondelete="CASCADE"), nullable=False
    )
    status_anterior: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    status_novo: Mapped[str] = mapped_column(String(30), nullable=False)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    usuario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relacionamentos
    operacao: Mapped["OperacaoVeiculo"] = relationship(back_populates="historico_status")
    usuario: Mapped["Usuario"] = relationship()


# =============================================================================
# 4. AMOSTRAGEM E CONTROLE DE QUALIDADE (LABORATÓRIO)
# =============================================================================

class Amostra(Base):
    """
    Entidade: amostra
    Descrição: Amostra colhida diretamente por compartimento para ensaios laboratoriais.
    """
    __tablename__ = "amostra"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    operacao_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("operacao_veiculo.id", ondelete="CASCADE"), nullable=False, index=True
    )
    compartimento_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("operacao_compartimento.id", ondelete="CASCADE"), nullable=False
    )
    produto_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("produto.id", ondelete="RESTRICT"), nullable=False
    )
    codigo_amostra: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    temperatura_coleta_celsius: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    tipo_coleta: Mapped[TipoColeta] = mapped_column(
        Enum(TipoColeta, native_enum=False), default=TipoColeta.CORRIDO, nullable=False
    )
    is_recoleta: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_descarga: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    amostra_origem_recoleta_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("amostra.id", ondelete="SET NULL"), nullable=True
    )
    tanque_descarga_pretendido_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("tanque.id", ondelete="SET NULL"), nullable=True
    )
    status_amostra: Mapped[StatusAmostra] = mapped_column(
        Enum(StatusAmostra, native_enum=False), default=StatusAmostra.AGUARDANDO_ANALISE, nullable=False
    )
    data_hora_coleta: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    operador_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    motivo_reprovacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    motivo_recoleta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    origemMp: Mapped[OrigemMP] = mapped_column(
        Enum(OrigemMP, native_enum=False), default=OrigemMP.VEGETAL, nullable=False
    )

    # Relacionamentos
    operacao: Mapped["OperacaoVeiculo"] = relationship(back_populates="amostras")
    compartimento: Mapped["OperacaoCompartimento"] = relationship(back_populates="amostras")
    produto: Mapped["Produto"] = relationship()
    operador: Mapped["Usuario"] = relationship(foreign_keys=[operador_id])
    tanque_pretendido: Mapped[Optional["Tanque"]] = relationship(foreign_keys=[tanque_descarga_pretendido_id])
    amostra_origem: Mapped[Optional["Amostra"]] = relationship(
        remote_side=[id], backref="recoletas"
    )
    analise: Mapped[Optional["AnaliseAmostra"]] = relationship(
        back_populates="amostra", uselist=False, cascade="all, delete-orphan"
    )
    comprovantes_representados: Mapped[List["ComprovanteOperacao"]] = relationship(
        back_populates="amostra_representativa"
    )

    def __repr__(self) -> str:
        return f"<Amostra(id={self.id}, codigo='{self.codigo_amostra}', status='{self.status_amostra}')>"


class AnaliseAmostra(Base):
    """
    Entidade: analise_amostra
    Descrição: Laudo físico-químico unificado contendo os resultados dos ensaios da amostra.
    """
    __tablename__ = "analise_amostra"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    amostra_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("amostra.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    analista_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    laboratorio_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("laboratorio.id", ondelete="RESTRICT"), nullable=False
    )
    data_hora_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    data_hora_fim: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    parecer_final: Mapped[ParecerLaudo] = mapped_column(
        Enum(ParecerLaudo, native_enum=False), default=ParecerLaudo.EM_ANDAMENTO, nullable=False
    )
    visto_analista: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    data_hora_visto: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    visto_registro_snapshot: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    hash_integridade_visto: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Parâmetros Físico-Químicos Diretos
    densidade_kg_l: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    temperatura_ensaio_celsius: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    fator_correcao: Mapped[Optional[Decimal]] = mapped_column(Numeric(7, 5), nullable=True)
    massa_especifica_20c_kg_l: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    grau_inpm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    teor_etanol_gasolina_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    teor_agua_ppm: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    aspecto: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cor: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    material_particulado: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    agua_livre: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    ponto_fulgor_celsius: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    condutividade_eletrica: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    metanol: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    destilacao: Mapped[Optional[Boolean]] = mapped_column(Boolean, nullable=True)

    # Suporte a resultados extras e futuros parâmetros sem necessidade de migração DDL
    resultados_extras: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Relacionamentos
    amostra: Mapped["Amostra"] = relationship(back_populates="analise")
    analista: Mapped["Usuario"] = relationship(foreign_keys=[analista_id])
    laboratorio: Mapped["Laboratorio"] = relationship(back_populates="analises")

    def __repr__(self) -> str:
        return f"<AnaliseAmostra(id={self.id}, amostra_id={self.amostra_id}, parecer='{self.parecer_final}')>"


# =============================================================================
# 5. COMPROVANTES DE OPERAÇÃO E BALANÇO VOLUMÉTRICO
# =============================================================================

class ComprovanteOperacao(Base):
    """
    Entidade: comprovante_operacao
    Descrição: Certificado e comprovante volumétrico apurado a 20°C por tipo de produto.
    """
    __tablename__ = "comprovante_operacao"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    operacao_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("operacao_veiculo.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    produto_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("produto.id", ondelete="RESTRICT"), nullable=False
    )
    amostra_representativa_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("amostra.id", ondelete="RESTRICT"), nullable=False
    )
    congenere_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("congenere.id", ondelete="RESTRICT"), nullable=False
    )
    numero_sicof: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    lancamento_sicof: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    numero_nota_fiscal: Mapped[str] = mapped_column(String(50), nullable=False)
    data_geracao: Mapped[date] = mapped_column(Date, nullable=False)
    hora_geracao: Mapped[time] = mapped_column(Time, nullable=False)
    densidade_20c_apurada: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    fator_correcao_fcv: Mapped[Decimal] = mapped_column(Numeric(7, 5), nullable=False)
    grau_inpm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    volume_ambiente_nf_litros: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    volume_20c_nf_litros: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    volume_ambiente_apurado_litros: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    volume_20c_litros: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    resultado_variacao_litros: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    retirada_litros: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=True)
    complemento_litros: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[StatusComprovante] = mapped_column(
        Enum(StatusComprovante, native_enum=False), default=StatusComprovante.DISPONIVEL, nullable=False
    )
    criado_por_usuario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Relacionamentos
    operacao: Mapped["OperacaoVeiculo"] = relationship(back_populates="comprovantes")
    produto: Mapped["Produto"] = relationship()
    amostra_representativa: Mapped["Amostra"] = relationship(back_populates="comprovantes_representados")
    congenere: Mapped["Congenere"] = relationship()
    criado_por_usuario: Mapped["Usuario"] = relationship(foreign_keys=[criado_por_usuario_id])
    alocacoes_tanques: Mapped[List["ComprovanteTanqueAlocacao"]] = relationship(
        back_populates="comprovante", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ComprovanteOperacao(id={self.id}, sicof='{self.numero_sicof}', variacao_L={self.resultado_variacao_litros})>"


class ComprovanteTanqueAlocacao(Base):
    """
    Entidade: comprovante_tanque_alocacao
    Descrição: Alocação do volume descarregado/carregado em 1 ou mais tanques do terminal.
    """
    __tablename__ = "comprovante_tanque_alocacao"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    comprovante_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("comprovante_operacao.id", ondelete="CASCADE"), nullable=False
    )
    tanque_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tanque.id", ondelete="RESTRICT"), nullable=False
    )
    bico_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("bico.id", ondelete="RESTRICT"), nullable=False
    )
    volume_alocado_litros: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Relacionamentos
    comprovante: Mapped["ComprovanteOperacao"] = relationship(back_populates="alocacoes_tanques")
    tanque: Mapped["Tanque"] = relationship(back_populates="alocacoes_comprovante")
    bico: Mapped["Bico"] = relationship(back_populates="alocacoes_comprovante")


# =============================================================================
# 6. AUDITORIA CENTRALIZADA
# =============================================================================

class AuditoriaLog(Base):
    """
    Entidade: auditoria_log
    Descrição: Registro centralizado e imutável de auditoria com diffs JSONB.
    """
    __tablename__ = "auditoria_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    terminal_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("terminal.id", ondelete="SET NULL"), nullable=True, index=True
    )
    tabela_nome: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    registro_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    acao: Mapped[AcaoAuditoria] = mapped_column(
        Enum(AcaoAuditoria, native_enum=False), nullable=False
    )
    dados_anteriores: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    dados_novos: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    motivo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True
    )
    ip_origem: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("idx_auditoria_tabela_reg", "tabela_nome", "registro_id", "criado_em"),
    )

    # Relacionamentos
    terminal: Mapped[Optional["Terminal"]] = relationship(back_populates="auditorias")
    usuario: Mapped[Optional["Usuario"]] = relationship()

    def __repr__(self) -> str:
        return f"<AuditoriaLog(id={self.id}, tabela='{self.tabela_nome}', registro_id={self.registro_id}, acao='{self.acao}')>"
