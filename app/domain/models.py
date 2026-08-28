"""
Modelos ORM do Banco de Dados Relacional - Elaion Sirac
Mapeamento feito via SQLAlchemy 2.0 (Declarative Base)
baseado no Dicionário de Entidades e Atributos (MER_ELAION_SIRAC.md)
"""

from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Classe base declarativa para os modelos SQLAlchemy."""
    pass


# =============================================================================
# ENUMS DE DOMÍNIO
# =============================================================================

class PapelUsuario(str, PyEnum):
    PORTEIRO = "Porteiro"
    QUIMICO = "Químico"
    OPERADOR = "Operador"
    ADM = "Adm"


class StatusPortaria(str, PyEnum):
    AGUARDANDO = "Aguardando"
    ENTRARAM = "Entraram"
    SAIRAM = "Saíram"
    CANCELADOS = "Cancelados"


class EtapaAnalise(str, PyEnum):
    COLETA = "Coleta"
    EM_ANALISE = "Em análise"
    CONCLUIDA = "Concluída"


class StatusResultadoAmostra(str, PyEnum):
    NORMAL = "Normal"
    RECOLETA = "Recoleta"
    REPROVADA = "Reprovada"


class StatusComprovante(str, PyEnum):
    PENDENTE = "Pendente"
    DISPONIVEL = "Disponível"
    EDITADO = "Editado"


# =============================================================================
# ENTIDADES PRINCIPAIS E INFRAESTRUTURA
# =============================================================================

class Usuario(Base):
    """
    Entidade: usuario
    Módulo Origem: Equipes (61:4875)
    Descrição: Armazena colaboradores e operadores com suas credenciais e perfis.
    """
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    cpf: Mapped[str] = mapped_column(String(14), unique=True, nullable=False)
    login: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    papel: Mapped[PapelUsuario] = mapped_column(
        Enum(PapelUsuario, native_enum=False), nullable=False
    )
    turno: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    telefone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relacionamentos
    veiculos_registrados: Mapped[List["Veiculo"]] = relationship(
        foreign_keys="[Veiculo.usuario_registro_id]", back_populates="usuario_registro"
    )
    amostras_coletadas: Mapped[List["Amostra"]] = relationship(
        foreign_keys="[Amostra.operador_id]", back_populates="operador"
    )
    analises_executadas: Mapped[List["AnaliseAmostra"]] = relationship(
        foreign_keys="[AnaliseAmostra.analista_id]", back_populates="analista"
    )
    comprovantes_emitidos: Mapped[List["ComprovanteAmostra"]] = relationship(
        foreign_keys="[ComprovanteAmostra.criado_por_usuario_id]", back_populates="criado_por_usuario"
    )
    historico_edicoes_comprovantes: Mapped[List["HistoricoEdicaoComprovante"]] = relationship(
        back_populates="usuario"
    )

    def __repr__(self) -> str:
        return f"<Usuario(id={self.id}, login='{self.login}', papel='{self.papel}')>"


class Terminal(Base):
    """
    Entidade: terminal
    Módulo Origem: Infraestrutura / Operação
    Descrição: Cadastro dos terminais de recebimento e armazenagem de combustíveis.
    """
    __tablename__ = "terminal"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relacionamentos
    laboratorios: Mapped[List["Laboratorio"]] = relationship(back_populates="terminal", cascade="all, delete-orphan")
    tanques: Mapped[List["Tanque"]] = relationship(back_populates="terminal", cascade="all, delete-orphan")
    veiculos: Mapped[List["Veiculo"]] = relationship(back_populates="terminal")

    def __repr__(self) -> str:
        return f"<Terminal(id={self.id}, nome='{self.nome}', codigo='{self.codigo}')>"


class Laboratorio(Base):
    """
    Entidade: laboratorio
    Módulo Origem: Qualidade / Laboratório
    Descrição: Laboratórios vinculados a um terminal para ensaios físico-químicos.
    """
    __tablename__ = "laboratorio"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    terminal_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("terminal.id", ondelete="CASCADE"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    codigo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relacionamentos
    terminal: Mapped["Terminal"] = relationship(back_populates="laboratorios")
    analises: Mapped[List["AnaliseAmostra"]] = relationship(back_populates="laboratorio")

    def __repr__(self) -> str:
        return f"<Laboratorio(id={self.id}, nome='{self.nome}', terminal_id={self.terminal_id})>"


class Tanque(Base):
    """
    Entidade: tanque
    Módulo Origem: Infraestrutura / Operação
    Descrição: Tanques de armazenamento situados no terminal.
    """
    __tablename__ = "tanque"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    terminal_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("terminal.id", ondelete="CASCADE"), nullable=False
    )
    produto_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("produto.id"), nullable=False)
    identificador_tanque: Mapped[str] = mapped_column(String(50), nullable=False)
    capacidade_litros: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relacionamentos
    terminal: Mapped["Terminal"] = relationship(back_populates="tanques")
    produto: Mapped["Produto"] = relationship()
    comprovantes_descarga: Mapped[List["ComprovanteAmostra"]] = relationship(back_populates="tanque_descarga")

    def __repr__(self) -> str:
        return f"<Tanque(id={self.id}, identificador='{self.identificador_tanque}', terminal_id={self.terminal_id})>"


class Congenere(Base):
    """
    Entidade: congenere
    Módulo Origem: Portaria (0:1), Amostras (15:9289), Comprovantes (41:2)
    Descrição: Cadastro de distribuidoras e empresas congêneres.
    """
    __tablename__ = "congenere"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    codigo_sicof: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relacionamentos
    veiculos: Mapped[List["Veiculo"]] = relationship(back_populates="congenere")
    comprovantes: Mapped[List["ComprovanteAmostra"]] = relationship(back_populates="congenere")

    def __repr__(self) -> str:
        return f"<Congenere(id={self.id}, nome='{self.nome}')>"


class Transportadora(Base):
    """
    Entidade: transportadora
    Módulo Origem: Portaria (0:1), Amostras (15:9289), Comprovantes (41:2)
    Descrição: Cadastro de empresas de transporte rodoviário de combustíveis.
    """
    __tablename__ = "transportadora"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    is_propria: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relacionamentos
    veiculos: Mapped[List["Veiculo"]] = relationship(back_populates="transportadora")

    def __repr__(self) -> str:
        return f"<Transportadora(id={self.id}, nome='{self.nome}', is_propria={self.is_propria})>"


class Produto(Base):
    """
    Entidade: produto
    Módulo Origem: Portaria (0:1), Amostras (15:9289), Comprovantes (41:2)
    Descrição: Catálogo de combustíveis e derivados de petróleo.
    """
    __tablename__ = "produto"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
    unidade_medida: Mapped[str] = mapped_column(String(20), default="L", nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relacionamentos
    veiculos: Mapped[List["Veiculo"]] = relationship(
        secondary="veiculo_produto", back_populates="produtos"
    )
    amostras: Mapped[List["Amostra"]] = relationship(back_populates="produto")

    def __repr__(self) -> str:
        return f"<Produto(id={self.id}, nome='{self.nome}', categoria='{self.categoria}')>"


# =============================================================================
# OPERAÇÃO DE PORTARIA E AMOSTRAGEM
# =============================================================================

class VeiculoProduto(Base):
    """
    Entidade: veiculo_produto (Tabela Pivô N:N)
    Módulo Origem: Portaria (0:1)
    Descrição: Associação entre veículos e produtos transportados (MultiSelect).
    """
    __tablename__ = "veiculo_produto"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    veiculo_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("veiculo.id", ondelete="CASCADE"), nullable=False
    )
    produto_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("produto.id", ondelete="CASCADE"), nullable=False
    )


class Veiculo(Base):
    """
    Entidade: veiculo
    Módulo Origem: Portaria (0:1), Amostras (15:9289), Comprovantes (41:2)
    Descrição: Registro de entrada e acompanhamento de caminhões-tanque.
    """
    __tablename__ = "veiculo"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    terminal_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("terminal.id"), nullable=False)
    placa: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    nome_motorista: Mapped[str] = mapped_column(String(150), nullable=False)
    numero_nota_fiscal: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    origem: Mapped[str] = mapped_column(String(150), nullable=False)
    congenere_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("congenere.id"), nullable=False)
    transportadora_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("transportadora.id"), nullable=False
    )
    is_transportadora_propria: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    numero_compartimentos: Mapped[int] = mapped_column(Integer, nullable=False)
    capacidade_total_litros: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    volume_nota_fiscal_litros: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status_portaria: Mapped[StatusPortaria] = mapped_column(
        Enum(StatusPortaria, native_enum=False), default=StatusPortaria.AGUARDANDO, nullable=False
    )
    data_hora_entrada: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    data_hora_saida: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    motivo_cancelamento: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    observacao_cancelamento: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    observacao_geral: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_registro_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("usuario.id"), nullable=False)
    usuario_aprovacao_saida_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("usuario.id"), nullable=True)

    # Relacionamentos
    terminal: Mapped["Terminal"] = relationship(back_populates="veiculos")
    congenere: Mapped["Congenere"] = relationship(back_populates="veiculos")
    transportadora: Mapped["Transportadora"] = relationship(back_populates="veiculos")
    usuario_registro: Mapped["Usuario"] = relationship(
        foreign_keys=[usuario_registro_id], back_populates="veiculos_registrados"
    )
    usuario_aprovacao_saida: Mapped[Optional["Usuario"]] = relationship(
        foreign_keys=[usuario_aprovacao_saida_id]
    )
    produtos: Mapped[List["Produto"]] = relationship(
        secondary="veiculo_produto", back_populates="veiculos"
    )
    coletas: Mapped[List["ColetaAmostra"]] = relationship(
        back_populates="veiculo", cascade="all, delete-orphan"
    )
    amostras: Mapped[List["Amostra"]] = relationship(
        back_populates="veiculo", cascade="all, delete-orphan"
    )
    comprovante: Mapped[Optional["ComprovanteAmostra"]] = relationship(
        back_populates="veiculo", uselist=False
    )
    historico_edicoes: Mapped[List["HistoricoEdicaoVeiculo"]] = relationship(
        back_populates="veiculo", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Veiculo(id={self.id}, placa='{self.placa}', status='{self.status_portaria}')>"


class ColetaAmostra(Base):
    """
    Entidade: coleta_amostra
    Módulo Origem: Amostras (15:9289)
    Descrição: Registra a sessão/lote de amostragem efetuada em um veículo.
    """
    __tablename__ = "coleta_amostra"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    veiculo_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("veiculo.id", ondelete="CASCADE"), nullable=False
    )
    numero_coleta: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    data_hora_coleta: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="Em andamento", nullable=False)
    amostrador_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("usuario.id"), nullable=True)
    usuario_recebimento_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("usuario.id"), nullable=True)

    # Relacionamentos
    veiculo: Mapped["Veiculo"] = relationship(back_populates="coletas")
    amostrador: Mapped[Optional["Usuario"]] = relationship(foreign_keys=[amostrador_id])
    usuario_recebimento: Mapped[Optional["Usuario"]] = relationship(foreign_keys=[usuario_recebimento_id])
    amostras: Mapped[List["Amostra"]] = relationship(
        back_populates="coleta", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ColetaAmostra(id={self.id}, veiculo_id={self.veiculo_id}, numero_coleta={self.numero_coleta})>"


class Amostra(Base):
    """
    Entidade: amostra
    Módulo Origem: Amostras (15:9289), Comprovantes (41:2)
    Descrição: Representa cada amostra colhida individualmente por compartimento.
    """
    __tablename__ = "amostra"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    codigo_amostra: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    coleta_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("coleta_amostra.id", ondelete="CASCADE"), nullable=False
    )
    veiculo_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("veiculo.id", ondelete="CASCADE"), nullable=False
    )
    produto_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("produto.id"), nullable=False)
    identificador_compartimento: Mapped[str] = mapped_column(String(10), nullable=False)
    capacidade_compartimento_litros: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    temperatura_coleta_celsius: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    data_hora_coleta: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    data_hora_fim_analise: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    etapa_analise: Mapped[EtapaAnalise] = mapped_column(
        Enum(EtapaAnalise, native_enum=False), default=EtapaAnalise.COLETA, nullable=False
    )
    status_resultado: Mapped[StatusResultadoAmostra] = mapped_column(
        Enum(StatusResultadoAmostra, native_enum=False),
        default=StatusResultadoAmostra.NORMAL,
        nullable=False,
    )
    is_recoleta: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    origem_procedimento: Mapped[str] = mapped_column(String(30), default="Descarga", nullable=False)
    operador_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("usuario.id"), nullable=True)
    usuario_reprovacao_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("usuario.id"), nullable=True)
    data_hora_reprovacao: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    motivo_reprovacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_recoleta_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("usuario.id"), nullable=True)
    data_hora_recoleta: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    motivo_recoleta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relacionamentos
    coleta: Mapped["ColetaAmostra"] = relationship(back_populates="amostras")
    veiculo: Mapped["Veiculo"] = relationship(back_populates="amostras")
    produto: Mapped["Produto"] = relationship(back_populates="amostras")
    operador: Mapped[Optional["Usuario"]] = relationship(
        foreign_keys=[operador_id], back_populates="amostras_coletadas"
    )
    usuario_reprovacao: Mapped[Optional["Usuario"]] = relationship(foreign_keys=[usuario_reprovacao_id])
    usuario_recoleta: Mapped[Optional["Usuario"]] = relationship(foreign_keys=[usuario_recoleta_id])
    analise: Mapped[Optional["AnaliseAmostra"]] = relationship(
        back_populates="amostra", uselist=False, cascade="all, delete-orphan"
    )
    comprovantes: Mapped[List["ComprovanteAmostra"]] = relationship(
        secondary="comprovante_amostra_item", back_populates="amostras"
    )
    historico_edicoes: Mapped[List["HistoricoEdicaoAmostra"]] = relationship(
        back_populates="amostra", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Amostra(id={self.id}, codigo='{self.codigo_amostra}', compartimento='{self.identificador_compartimento}')>"


class AnaliseAmostra(Base):
    """
    Entidade: analise_amostra
    Módulo Origem: Amostras (15:9289), Comprovantes (41:2)
    Descrição: Laudo contendo os resultados dos ensaios físico-químicos da amostra.
    """
    __tablename__ = "analise_amostra"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    amostra_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("amostra.id", ondelete="CASCADE"), nullable=False
    )
    analista_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("usuario.id"), nullable=False)
    laboratorio_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("laboratorio.id"), nullable=True)
    tipo_especifico_produto: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cor: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    aspecto: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    material_particulado: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    agua_livre: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    numero_amostra_lab: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    visto_analista: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    densidade_kg_l: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    temperatura_ensaio_celsius: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    fator_correcao: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    massa_especifica_20c_kg_l: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    grau_inpm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    teor_agua_ppm: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_hora_analise: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relacionamentos
    amostra: Mapped["Amostra"] = relationship(back_populates="analise")
    analista: Mapped["Usuario"] = relationship(
        foreign_keys=[analista_id], back_populates="analises_executadas"
    )
    laboratorio: Mapped[Optional["Laboratorio"]] = relationship(back_populates="analises")
    historico_edicoes: Mapped[List["HistoricoEdicaoAnalise"]] = relationship(
        back_populates="analise", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AnaliseAmostra(id={self.id}, amostra_id={self.amostra_id}, densidade={self.densidade_kg_l})>"


# =============================================================================
# CERTIFICAÇÃO E AUDITORIA
# =============================================================================

class ComprovanteAmostra(Base):
    """
    Entidade: comprovante_amostra
    Módulo Origem: Comprovantes (41:2)
    Descrição: Certificado de análise e documento de conferência volumétrica.
    """
    __tablename__ = "comprovante_amostra"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    veiculo_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("veiculo.id"), nullable=False)
    congenere_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("congenere.id"), nullable=False)
    numero_sicof: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    lancamento_sicof: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    nota_fiscal_numero: Mapped[str] = mapped_column(String(50), nullable=False)
    volume_ambiente_nf_litros: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    volume_20c_nf_litros: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    data_geracao: Mapped[date] = mapped_column(Date, nullable=False)
    hora_geracao: Mapped[time] = mapped_column(Time, nullable=False)
    densidade_20c_apurada: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    grau_inpm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    fator_correcao: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    volume_ambiente_apurado_litros: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    volume_20c_apurado_litros: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    resultado_variacao_litros: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tanque_descarga_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("tanque.id"), nullable=True)
    volume_retirada_litros: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    complemento_observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[StatusComprovante] = mapped_column(
        Enum(StatusComprovante, native_enum=False),
        default=StatusComprovante.DISPONIVEL,
        nullable=False,
    )
    criado_por_usuario_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("usuario.id"), nullable=False)

    # Relacionamentos
    veiculo: Mapped["Veiculo"] = relationship(back_populates="comprovante")
    congenere: Mapped["Congenere"] = relationship(back_populates="comprovantes")
    tanque_descarga: Mapped[Optional["Tanque"]] = relationship(back_populates="comprovantes_descarga")
    criado_por_usuario: Mapped["Usuario"] = relationship(
        foreign_keys=[criado_por_usuario_id], back_populates="comprovantes_emitidos"
    )
    amostras: Mapped[List["Amostra"]] = relationship(
        secondary="comprovante_amostra_item", back_populates="comprovantes"
    )
    historico_edicoes: Mapped[List["HistoricoEdicaoComprovante"]] = relationship(
        back_populates="comprovante", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ComprovanteAmostra(id={self.id}, sicof='{self.numero_sicof}', variacao_L={self.resultado_variacao_litros})>"


class ComprovanteAmostraItem(Base):
    """
    Entidade: comprovante_amostra_item (Tabela Pivô N:N)
    Módulo Origem: Comprovantes (41:2)
    Descrição: Relaciona as amostras selecionadas para compor o comprovante emitido.
    """
    __tablename__ = "comprovante_amostra_item"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    comprovante_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("comprovante_amostra.id", ondelete="CASCADE"), nullable=False
    )
    amostra_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("amostra.id", ondelete="CASCADE"), nullable=False
    )


# =============================================================================
# HISTÓRICOS DE AUDITORIA E EDICÕES
# =============================================================================

class HistoricoEdicaoComprovante(Base):
    """
    Entidade: historico_edicao_comprovante
    Módulo Origem: Comprovantes (41:2)
    Descrição: Registro de auditoria contendo modificações em comprovantes.
    """
    __tablename__ = "historico_edicao_comprovante"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    comprovante_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("comprovante_amostra.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("usuario.id"), nullable=False)
    data_hora: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    descricao_acao: Mapped[str] = mapped_column(Text, nullable=False)

    # Relacionamentos
    comprovante: Mapped["ComprovanteAmostra"] = relationship(back_populates="historico_edicoes")
    usuario: Mapped["Usuario"] = relationship(back_populates="historico_edicoes_comprovantes")

    def __repr__(self) -> str:
        return f"<HistoricoEdicaoComprovante(id={self.id}, comprovante_id={self.comprovante_id}, usuario_id={self.usuario_id})>"


class HistoricoEdicaoVeiculo(Base):
    """
    Entidade: historico_edicao_veiculo
    Módulo Origem: Portaria / Auditoria
    Descrição: Registro de auditoria contendo alterações nos dados do veículo.
    """
    __tablename__ = "historico_edicao_veiculo"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    veiculo_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("veiculo.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("usuario.id"), nullable=False)
    data_hora: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    campo_alterado: Mapped[str] = mapped_column(String(100), nullable=False)
    valor_anterior: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    valor_novo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    motivo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relacionamentos
    veiculo: Mapped["Veiculo"] = relationship(back_populates="historico_edicoes")
    usuario: Mapped["Usuario"] = relationship()

    def __repr__(self) -> str:
        return f"<HistoricoEdicaoVeiculo(id={self.id}, veiculo_id={self.veiculo_id}, campo='{self.campo_alterado}')>"


class HistoricoEdicaoAmostra(Base):
    """
    Entidade: historico_edicao_amostra
    Módulo Origem: Amostras / Auditoria
    Descrição: Registro de auditoria contendo alterações nos dados da amostra.
    """
    __tablename__ = "historico_edicao_amostra"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    amostra_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("amostra.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("usuario.id"), nullable=False)
    data_hora: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    campo_alterado: Mapped[str] = mapped_column(String(100), nullable=False)
    valor_anterior: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    valor_novo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    motivo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relacionamentos
    amostra: Mapped["Amostra"] = relationship(back_populates="historico_edicoes")
    usuario: Mapped["Usuario"] = relationship()

    def __repr__(self) -> str:
        return f"<HistoricoEdicaoAmostra(id={self.id}, amostra_id={self.amostra_id}, campo='{self.campo_alterado}')>"


class HistoricoEdicaoAnalise(Base):
    """
    Entidade: historico_edicao_analise
    Módulo Origem: Amostras / Auditoria
    Descrição: Registro de auditoria contendo alterações nos ensaios/laudos da análise da amostra.
    """
    __tablename__ = "historico_edicao_analise"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    analise_amostra_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("analise_amostra.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("usuario.id"), nullable=False)
    data_hora: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    campo_alterado: Mapped[str] = mapped_column(String(100), nullable=False)
    valor_anterior: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    valor_novo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    motivo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relacionamentos
    analise: Mapped["AnaliseAmostra"] = relationship(back_populates="historico_edicoes")
    usuario: Mapped["Usuario"] = relationship()

    def __repr__(self) -> str:
        return f"<HistoricoEdicaoAnalise(id={self.id}, analise_amostra_id={self.analise_amostra_id}, campo='{self.campo_alterado}')>"
