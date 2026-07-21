"""
Modelos de dados (SQLAlchemy ORM, síncrono) — core.db
=====================================================
Schema enxuto da Fase 1. Uma única base (uma core.db).
Sem RAG, sem auditoria, sem a camada industrial.

Tabelas:
  * Produto        — inventário mestre (identidade, nome, marca, sabor, peso, preço…)
  * ProdutoAlias   — cada jeito de escrever já correlacionado a um produto (aprendizado)
  * Categoria      — Mercearia, Limpeza, Bebidas… (para o tabloide categorizado)
  * Layout         — arte de fundo + descrição de grade/camadas/slots
  * ProjetoSalvo   — snapshot congelado + overrides por slot
  * Config         — preferências do usuário (chave-valor)
"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base única do banco principal (core.db)."""


class TipoMidia(str, Enum):
    TABLOIDE = "TABLOIDE"
    CARTAZ = "CARTAZ"
    ETIQUETA = "ETIQUETA"


# ==============================================================================
# CATEGORIA
# ==============================================================================


class Categoria(Base):
    """Categoria do produto (Mercearia, Limpeza, Bebidas…)."""

    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now()
    )

    produtos: Mapped[list["Produto"]] = relationship(back_populates="categoria")

    def __repr__(self) -> str:
        return f"<Categoria {self.nome!r}>"


# ==============================================================================
# PRODUTO
# ==============================================================================


class Produto(Base):
    """
    Inventário mestre. É o ponto de partida "vivo": guarda a identidade do
    produto, o nome sanitizado, e o último preço conhecido (preco_atual).
    O preço final de cada tabloide fica congelado no projeto, não aqui.
    """

    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Identidade de origem: a própria descrição crua (SKU de origem = descrição).
    nome_bruto: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Dados tratados (a ORDEM final Tipo+Marca+Sabor+Peso é refinada pela IA na Fase 3).
    nome_sanitizado: Mapped[str] = mapped_column(String(255), nullable=False)
    marca: Mapped[str | None] = mapped_column(String(100), index=True)
    sabor: Mapped[str | None] = mapped_column(String(100))
    peso_valor: Mapped[Decimal | None] = mapped_column(Numeric(10, 3, asdecimal=True))
    peso_unidade: Mapped[str | None] = mapped_column(String(10))

    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categorias.id"))
    # F8.1: quem deu a categoria — "humano" (Almoxarifado) ou "ia" (passe em
    # lote). Correção humana NUNCA é sobrescrita por novo passe de IA.
    categoria_origem: Mapped[str | None] = mapped_column(String(10))

    # RG-41: código de barras (EAN/GTIN, 8–14 dígitos) — chave da cascata de
    # imagem (Open Food Facts primeiro); vem da tabela importada ou é
    # digitado no Almoxarifado.
    ean: Mapped[str | None] = mapped_column(String(14))

    # RG-28: as N fotos do produto (sabores/fragrâncias) — lista JSON de
    # caminhos RELATIVOS À PASTA do produto na biblioteca ("atual.png",
    # "extras/x.png"): imune ao remap de id da portabilidade (I3/I1).
    # Vazio/None = foto única de sempre (caminho_imagem).
    imagens_json: Mapped[str | None] = mapped_column(Text)

    # Último preço conhecido (ponto de partida). Pode estar vazio.
    preco_atual: Mapped[Decimal | None] = mapped_column(Numeric(10, 2, asdecimal=True))
    # FASE 2 (passo 81): lixeira de 30 dias — soft-delete
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime)

    # Validade do item — usada SÓ no cartaz (item perto de vencer).
    validade_item: Mapped[date | None] = mapped_column(Date)

    # Selo +18: a IA detecta a bebida alcoólica; o selo pode ser ligado à mão.
    bebida_alcoolica: Mapped[bool] = mapped_column(Boolean, default=False)
    selo_mais18: Mapped[bool] = mapped_column(Boolean, default=False)

    # Selo "Qualidade Belo Brasil" — marca própria do mercado (ligável à mão).
    marca_propria: Mapped[bool] = mapped_column(Boolean, default=False)

    # Imagem tratada em disco (o banco guarda só o caminho).
    caminho_imagem: Mapped[str | None] = mapped_column(String(500))

    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now()
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now(), onupdate=func.now()
    )

    categoria: Mapped["Categoria | None"] = relationship(back_populates="produtos")
    aliases: Mapped[list["ProdutoAlias"]] = relationship(
        back_populates="produto", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_produtos_nome_marca", "nome_sanitizado", "marca"),
    )

    def __repr__(self) -> str:
        return f"<Produto id={self.id} {self.nome_sanitizado!r}>"


# ==============================================================================
# PRODUTO ALIAS (aprendizado por alias)
# ==============================================================================


class ProdutoAlias(Base):
    """Cada jeito de escrever já correlacionado a um produto (o banco fica esperto)."""

    __tablename__ = "produto_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    alias_raw: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False)

    confianca: Mapped[Decimal] = mapped_column(
        Numeric(3, 2, asdecimal=True), default=Decimal("1.00")
    )
    # Correções aprendidas que têm precedência (JSON: {"marca": "Skol", ...}).
    overrides_json: Mapped[str] = mapped_column(Text, default="{}")
    usos: Mapped[int] = mapped_column(default=0)
    confirmado_em: Mapped[datetime | None] = mapped_column(DateTime)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now()
    )

    produto: Mapped["Produto"] = relationship(back_populates="aliases")

    def get_overrides(self) -> dict:
        try:
            return json.loads(self.overrides_json or "{}")
        except json.JSONDecodeError:
            return {}

    def set_overrides(self, dados: dict) -> None:
        self.overrides_json = json.dumps(dados, ensure_ascii=False)

    def __repr__(self) -> str:
        return f"<Alias {self.alias_raw!r} -> produto={self.produto_id}>"


# ==============================================================================
# LAYOUT
# ==============================================================================


class Layout(Base):
    """Metadados de um layout: arte de fundo (imagem) + grade/camadas/slots (JSON)."""

    __tablename__ = "layouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    arquivo_fundo: Mapped[str | None] = mapped_column(String(500))
    tipo_midia: Mapped[str] = mapped_column(String(20), default=TipoMidia.TABLOIDE.value)
    # FASE 2 (passo 81): lixeira de 30 dias — soft-delete
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime)
    estrutura_json: Mapped[str] = mapped_column(Text, default="{}")
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now()
    )

    projetos: Mapped[list["ProjetoSalvo"]] = relationship(back_populates="layout")

    def get_estrutura(self) -> dict:
        try:
            return json.loads(self.estrutura_json or "{}")
        except json.JSONDecodeError:
            return {}

    def __repr__(self) -> str:
        return f"<Layout {self.nome!r} ({self.tipo_midia})>"


# ==============================================================================
# PROJETO SALVO (congelado)
# ==============================================================================


class Evento(Base):
    """FASE 2 (passo 1): o evento como ENTIDADE — cor, capa, dia da semana,
    notas. O texto `ProjetoSalvo.evento` fica por compat; a verdade é o id."""

    __tablename__ = "eventos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True,
                                      nullable=False, index=True)
    cor: Mapped[str] = mapped_column(String(9), default="#2563EB")
    capa: Mapped[str | None] = mapped_column(String(300))   # relativa (I3)
    dia_semana: Mapped[int | None] = mapped_column()        # 0=seg … 6=dom
    ordem: Mapped[int] = mapped_column(default=0)
    notas: Mapped[str] = mapped_column(Text, default="")
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Evento {self.nome!r} cor={self.cor}>"


class Selo(Base):
    """FASE 3 (passo 63, RG-33): o selo como ENTIDADE do gestor.

    - ``arquivo``: PNG RELATIVO à pasta selos/ (I3); None = badge interno
      desenhado (os automáticos +18/Qualidade nascem assim).
    - ``tipo``: "manual" (o dono escolhe por item) | "automatico" (dispara
      pela ``regra``: "bebida_alcoolica" → +18, "marca_propria" → Qualidade).
    - ``ativo``: desligar um automático desliga a REGRA (o conceito fica);
      exceção TRAVADA: o +18 em bebida alcoólica é lei e não desliga.
    """

    __tablename__ = "selos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True,
                                      nullable=False, index=True)
    arquivo: Mapped[str | None] = mapped_column(String(300))   # relativo (I3)
    tipo: Mapped[str] = mapped_column(String(20), default="manual")
    regra: Mapped[str | None] = mapped_column(String(40))
    canto: Mapped[str] = mapped_column(String(30),
                                       default="SUPERIOR_DIREITO")
    ativo: Mapped[bool] = mapped_column(default=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Selo {self.nome!r} tipo={self.tipo}>"


class ProjetoSalvo(Base):
    """Projeto salvo: snapshot imutável dos slots + overrides por slot."""

    __tablename__ = "projetos_salvos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    layout_id: Mapped[int] = mapped_column(ForeignKey("layouts.id"), nullable=False)

    # Pasta temática do Dashboard (ex.: "Terça do Pão").
    evento: Mapped[str | None] = mapped_column(String(120), index=True)
    # FASE 2 (passo 2): a verdade é o id; o texto acima fica por compat
    evento_id: Mapped[int | None] = mapped_column(index=True)
    # FASE 2 (passo 35): rascunho → pronto → exportado → publicado
    status: Mapped[str | None] = mapped_column(String(12),
                                               default="rascunho")
    # FASE 2 (passo 50): favorito sobe no topo do evento (só exibição)
    favorito: Mapped[bool | None] = mapped_column(default=False)
    # FASE 2 (passo 81): lixeira de 30 dias — soft-delete
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime)

    estado_slots: Mapped[str] = mapped_column(Text, default="{}")   # snapshot congelado
    overrides_json: Mapped[str] = mapped_column(Text, default="{}")  # edições manuais

    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now()
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now(), onupdate=func.now()
    )

    layout: Mapped["Layout"] = relationship(back_populates="projetos")

    def get_slots(self) -> dict:
        try:
            return json.loads(self.estado_slots or "{}")
        except json.JSONDecodeError:
            return {}

    def set_slots(self, dados: dict) -> None:
        self.estado_slots = json.dumps(dados, ensure_ascii=False)

    def __repr__(self) -> str:
        return f"<Projeto {self.nome!r} layout={self.layout_id}>"


# ==============================================================================
# CONFIG (chave-valor)
# ==============================================================================


class Config(Base):
    """Preferências do usuário em chave-valor (valor guardado como JSON)."""

    __tablename__ = "config"

    id: Mapped[int] = mapped_column(primary_key=True)
    chave: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    valor_json: Mapped[str] = mapped_column(Text, default="null")
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now()
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now(), onupdate=func.now()
    )

    def get_valor(self):
        try:
            return json.loads(self.valor_json)
        except (json.JSONDecodeError, TypeError):
            return None

    def set_valor(self, valor) -> None:
        self.valor_json = json.dumps(valor, ensure_ascii=False)

    def __repr__(self) -> str:
        return f"<Config {self.chave!r}>"
