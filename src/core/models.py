"""
AutoTabloide AI - Modelos de Dados (SQLAlchemy ORM)
====================================================
Schema completo conforme Documentação Técnica Volumes I, III, IV e V.

Tabelas:
- Produto: Inventário mestre de produtos
- ProdutoAlias: Aprendizado de correlação de nomes
- LayoutMeta: Metadados de templates SVG
- ProjetoSalvo: Workspaces persistentes (snapshot imutável)
- AuditLog: Rastreabilidade forense
- KnowledgeVector: RAG local para embeddings
"""

import json
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from enum import Enum

from sqlalchemy import (
    Integer, String, Numeric, DateTime, Text, ForeignKey, 
    func, Index, Enum as SQLEnum, LargeBinary
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class para todos os modelos SQLAlchemy."""
    pass


# ==============================================================================
# ENUMERAÇÕES (Tipos de Dados Restritos)
# ==============================================================================

class TipoMidia(str, Enum):
    """Classificação de layouts conforme Vol. I, Cap. 4.2"""
    TABLOIDE = "TABLOIDE"
    CARTAZ_A4 = "CARTAZ_A4"
    CARTAZ_GIGANTE = "CARTAZ_GIGANTE"
    ETIQUETA = "ETIQUETA"


class StatusQualidade(int, Enum):
    """Estados de qualidade do cadastro conforme Vol. I, Tab. 4.1"""
    INCOMPLETO = 0      # Dados básicos faltando
    SEM_FOTO = 1        # Sem imagem associada
    FOTO_BAIXA_RES = 2  # Imagem < 800px
    PRONTO = 3          # Validado e aprovado


class TipoAcao(str, Enum):
    """Tipos de ação para auditoria conforme Vol. V, Cap. 5.1"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    IMPORT = "IMPORT"
    PRINT = "PRINT"
    ROLLBACK = "ROLLBACK"


class TipoEntidade(str, Enum):
    """Categorias de entidade para auditoria"""
    PRODUTO = "PRODUTO"
    PROJETO = "PROJETO"
    LAYOUT = "LAYOUT"
    SISTEMA = "SISTEMA"


# ==============================================================================
# TABELA: PRODUTOS (Inventário Mestre)
# Vol. I, Cap. 4.1 - A "Fonte da Verdade" para renderização
# ==============================================================================

class Produto(Base):
    """
    Tabela principal de inventário.
    Nenhum preço ou nome vai para cartaz sem existir como registro validado aqui.
    """
    __tablename__ = "produtos"

    # Identificação
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku_origem: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    # Dados Sanitizados pela IA (Vol. I, Tab. 4.1)
    nome_sanitizado: Mapped[str] = mapped_column(String(255), nullable=False)
    marca_normalizada: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    detalhe_peso: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Nova coluna: Categoria para lógica de ícone +18 (Vol. I, Cap. 5.3)
    categoria: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Precificação (CRÍTICO: DECIMAL para evitar erros de ponto flutuante)
    preco_venda_atual: Mapped[Decimal] = mapped_column(
        Numeric(10, 2, asdecimal=True), nullable=False
    )
    preco_referencia: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2, asdecimal=True), nullable=True
    )
    
    # Gestão de Ativos - Lista JSON de hashes MD5 (suporte multi-imagem)
    img_hash_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="[]")
    
    # Metadados de Qualidade (Vol. I, Tab. 4.1)
    status_qualidade: Mapped[int] = mapped_column(
        Integer, default=StatusQualidade.INCOMPLETO.value
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now()
    )
    last_modified: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now(), onupdate=func.now()
    )
    
    # Filtro "Já Impresso" - Rastreia último preço impresso para detectar alterações
    ultimo_preco_impresso: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2, asdecimal=True), nullable=True
    )
    data_ultima_impressao: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Relacionamentos
    aliases: Mapped[List["ProdutoAlias"]] = relationship(
        "ProdutoAlias", back_populates="produto", cascade="all, delete-orphan"
    )

    # === Helpers para Manipulação de Ativos ===
    
    def set_images(self, hashes: List[str]):
        """Define lista de hashes de imagem."""
        self.img_hash_ref = json.dumps(hashes)

    def get_images(self) -> List[str]:
        """Retorna lista de hashes de imagem."""
        if not self.img_hash_ref:
            return []
        try:
            return json.loads(self.img_hash_ref)
        except json.JSONDecodeError:
            return []
    
    def add_image(self, hash_md5: str):
        """Adiciona um hash à lista (sem duplicatas)."""
        images = self.get_images()
        if hash_md5 not in images:
            images.append(hash_md5)
            self.set_images(images)
    
    def is_alcoholic(self) -> bool:
        """Verifica se produto requer ícone +18."""
        restricted_categories = ["bebida alcoólica", "cigarro", "tabaco", "vinho", "cerveja", "vodka", "whisky"]
        if self.categoria:
            return self.categoria.lower() in restricted_categories
        return False
    
    def price_changed_since_print(self) -> bool:
        """
        Verifica se o preço mudou desde a última impressão.
        Retorna True se nunca foi impresso ou se preço mudou.
        """
        if self.ultimo_preco_impresso is None:
            return True  # Nunca impresso = preço "mudou"
        return self.preco_venda_atual != self.ultimo_preco_impresso
    
    def mark_as_printed(self):
        """
        Marca produto como impresso com preço atual.
        Deve ser chamado após exportação de PDF contendo este produto.
        """
        self.ultimo_preco_impresso = self.preco_venda_atual
        self.data_ultima_impressao = datetime.now()

    def __repr__(self):
        return f"<Produto(id={self.id}, sku='{self.sku_origem}', nome='{self.nome_sanitizado}')>"


# ==============================================================================
# TABELA: PRODUTO_ALIASES (Aprendizado de Correlação)
# Vol. IV, Cap. 2.1 - Permite que o sistema aprenda variações de nome
# ==============================================================================

class ProdutoAlias(Base):
    """
    Tabela de aprendizado para o 'Juiz'.
    Permite correlacionar 'Cerveja X 350ml' com 'Cerv. X LATA'.
    
    PROTOCOLO MEMÓRIA VIVA: override_data armazena correções humanas
    que sobrescrevem a lógica da IA no futuro.
    """
    __tablename__ = "produto_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alias_raw: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    produto_id: Mapped[int] = mapped_column(Integer, ForeignKey("produtos.id"), nullable=False)
    
    # Confiança da correlação (0.0 a 1.0)
    confidence: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(3, 2, asdecimal=True), default=1.0
    )
    
    # NOVO: Override data para correções aprendidas (Protocolo Memória Viva)
    # Formato: {"nome_sanitizado": "Cerveja Skol LATA", "marca": "Skol", ...}
    override_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="{}")
    
    # Quantas vezes este alias foi usado com sucesso
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Última vez que foi confirmado pelo usuário
    last_confirmed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now()
    )

    produto: Mapped["Produto"] = relationship("Produto", back_populates="aliases")

    def get_overrides(self) -> dict:
        """Retorna overrides aprendidos."""
        if not self.override_data:
            return {}
        try:
            return json.loads(self.override_data)
        except json.JSONDecodeError:
            return {}
    
    def set_overrides(self, overrides: dict):
        """Define overrides aprendidos."""
        self.override_data = json.dumps(overrides, ensure_ascii=False)
    
    def add_override(self, field: str, value: str):
        """Adiciona um override específico."""
        overrides = self.get_overrides()
        overrides[field] = value
        self.set_overrides(overrides)

    def __repr__(self):
        return f"<Alias(raw='{self.alias_raw}', produto_id={self.produto_id})>"


# ==============================================================================
# TABELA: LAYOUTS_META (Metadados de Templates SVG)
# Vol. I, Cap. 4.2 - Cache de metadados para listagem rápida
# ==============================================================================

class LayoutMeta(Base):
    """
    Metadados cacheados de templates SVG.
    Evita parsing do XML a cada listagem na galeria.
    """
    __tablename__ = "layouts_meta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Identificação
    nome_amigavel: Mapped[str] = mapped_column(String(150), nullable=False)
    arquivo_fonte: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    
    # Classificação (Vol. I, Tab. 4.2)
    tipo_midia: Mapped[str] = mapped_column(
        String(20), default=TipoMidia.TABLOIDE.value
    )
    
    # Capacidade e Estrutura
    capacidade_slots: Mapped[int] = mapped_column(Integer, default=1)
    
    # Estrutura JSON: Mapa de camadas, coordenadas, IDs detectados
    estrutura_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Lista JSON de fontes requeridas pelo template
    fontes_requeridas: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="[]")
    
    # Hash de integridade para detectar alterações
    integrity_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Caminho do thumbnail gerado
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now()
    )
    last_validated: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relacionamento com projetos
    projetos: Mapped[List["ProjetoSalvo"]] = relationship(
        "ProjetoSalvo", back_populates="layout"
    )

    # === Helpers ===
    
    def get_fonts(self) -> List[str]:
        """Retorna lista de fontes requeridas."""
        if not self.fontes_requeridas:
            return []
        try:
            return json.loads(self.fontes_requeridas)
        except json.JSONDecodeError:
            return []
    
    def set_fonts(self, fonts: List[str]):
        """Define lista de fontes requeridas."""
        self.fontes_requeridas = json.dumps(fonts)
    
    def get_structure(self) -> dict:
        """Retorna estrutura parseada do layout."""
        if not self.estrutura_json:
            return {}
        try:
            return json.loads(self.estrutura_json)
        except json.JSONDecodeError:
            return {}

    def __repr__(self):
        return f"<Layout(nome='{self.nome_amigavel}', tipo='{self.tipo_midia}', slots={self.capacidade_slots})>"


# ==============================================================================
# TABELA: PROJETOS_SALVOS (Workspaces Persistentes)
# Vol. V, Cap. 3 - Snapshot imutável para fidelidade histórica
# ==============================================================================

class ProjetoSalvo(Base):
    """
    Persistência do trabalho em andamento.
    O estado_slots armazena um SNAPSHOT IMUTÁVEL dos dados no momento do save.
    """
    __tablename__ = "projetos_salvos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Identificação
    nome_projeto: Mapped[str] = mapped_column(String(200), nullable=False)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    
    # Referência ao layout base
    layout_id: Mapped[int] = mapped_column(Integer, ForeignKey("layouts_meta.id"), nullable=False)
    
    # Hash de integridade do template no momento do save (Vol. V, Cap. 3.1)
    layout_integrity_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # === Dados de Estado (CRÍTICO: Snapshot Imutável) ===
    # estado_slots: JSON com dados COMPLETOS de cada slot no momento do save
    # Formato: {"SLOT_01": {"produto_id": 50, "preco": 19.90, "nome": "...", "img_hash": "..."}, ...}
    estado_slots: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="{}")
    
    # overrides_json: Edições manuais que têm precedência sobre o snapshot
    overrides_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="{}")
    
    # Controle de Estado
    is_locked: Mapped[bool] = mapped_column(Integer, default=False)  # SQLite não tem BOOLEAN nativo
    is_dirty: Mapped[bool] = mapped_column(Integer, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now()
    )
    last_modified: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now(), onupdate=func.now()
    )
    
    # Metadados do autor
    author_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Relacionamento
    layout: Mapped["LayoutMeta"] = relationship("LayoutMeta", back_populates="projetos")

    # === Helpers ===
    
    def get_slots(self) -> dict:
        """Retorna estado dos slots."""
        if not self.estado_slots:
            return {}
        try:
            return json.loads(self.estado_slots)
        except json.JSONDecodeError:
            return {}
    
    def set_slots(self, slots: dict):
        """Define estado dos slots."""
        self.estado_slots = json.dumps(slots, ensure_ascii=False)
    
    def get_overrides(self) -> dict:
        """Retorna overrides manuais."""
        if not self.overrides_json:
            return {}
        try:
            return json.loads(self.overrides_json)
        except json.JSONDecodeError:
            return {}
    
    def set_overrides(self, overrides: dict):
        """Define overrides manuais."""
        self.overrides_json = json.dumps(overrides, ensure_ascii=False)
    
    def get_slot_data(self, slot_id: str) -> dict:
        """Retorna dados de um slot específico, aplicando overrides."""
        slots = self.get_slots()
        overrides = self.get_overrides()
        
        base_data = slots.get(slot_id, {})
        slot_overrides = overrides.get(slot_id, {})
        
        # Overrides têm precedência
        return {**base_data, **slot_overrides}

    def __repr__(self):
        return f"<Projeto(nome='{self.nome_projeto}', layout_id={self.layout_id})>"


# ==============================================================================
# TABELA: AUDIT_LOG (Rastreabilidade Forense)
# Vol. V, Cap. 5.1 - Histórico completo para rollback
# ==============================================================================

class AuditLog(Base):
    """
    Log de auditoria para rastreabilidade total.
    Permite "Time Machine" - rollback de qualquer alteração.
    """
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Timestamp preciso (UTC recomendado)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now(), index=True
    )
    
    # Identificação do operador
    user_ref: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Contexto da ação
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    action_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    
    # Payload de diferença (CRÍTICO para rollback)
    # Formato: {"field": "preco_venda", "old_value": 10.50, "new_value": 9.90, "source_context": "manual_ui"}
    diff_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Severidade: 1=Info, 2=Warning, 3=Critical
    severity: Mapped[int] = mapped_column(Integer, default=1)
    
    # Descrição legível para humanos
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Índice composto para queries comuns
    __table_args__ = (
        Index('ix_audit_entity', 'entity_type', 'entity_id'),
        Index('ix_audit_timeline', 'timestamp', 'action_type'),
    )

    # === Helpers ===
    
    def get_diff(self) -> dict:
        """Retorna payload de diferença."""
        if not self.diff_payload:
            return {}
        try:
            return json.loads(self.diff_payload)
        except json.JSONDecodeError:
            return {}
    
    def set_diff(self, diff: dict):
        """Define payload de diferença."""
        self.diff_payload = json.dumps(diff, ensure_ascii=False)
    
    def get_old_value(self):
        """Retorna valor anterior (para rollback)."""
        diff = self.get_diff()
        return diff.get('old_value')
    
    def get_new_value(self):
        """Retorna novo valor."""
        diff = self.get_diff()
        return diff.get('new_value')
    
    def can_rollback(self) -> bool:
        """Verifica se esta ação é reversível."""
        reversible_actions = [TipoAcao.UPDATE.value, TipoAcao.DELETE.value]
        return self.action_type in reversible_actions and self.get_old_value() is not None

    def __repr__(self):
        return f"<Audit({self.action_type} {self.entity_type}:{self.entity_id} @ {self.timestamp})>"


# ==============================================================================
# TABELA: KNOWLEDGE_VECTORS (RAG Local)
# Vol. IV, Cap. 2.2 - Embeddings para memória institucional
# ==============================================================================

class KnowledgeVector(Base):
    """
    Armazenamento de embeddings para busca semântica (RAG).
    Permite que a IA aprenda com correções do usuário.
    """
    __tablename__ = "knowledge_vectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Texto original que gerou o embedding
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Hash do texto para deduplicação rápida
    text_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    
    # Vetor de embedding (serializado como BLOB ou JSON)
    # Para SQLite, usamos BLOB para eficiência
    embedding: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    
    # Dimensionalidade do vetor (ex: 384 para all-MiniLM-L6-v2)
    dimensions: Mapped[int] = mapped_column(Integer, default=384)
    
    # Referência ao produto resultante (se for correção validada)
    produto_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("produtos.id"), nullable=True
    )
    
    # Resultado validado pelo humano
    validated_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Boost de prioridade (correções humanas têm boost alto)
    priority_boost: Mapped[Decimal] = mapped_column(
        Numeric(3, 2, asdecimal=True), default=1.0
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now()
    )

    def __repr__(self):
        return f"<KnowledgeVector(hash='{self.text_hash[:8]}...', produto_id={self.produto_id})>"


# ==============================================================================
# TABELA: HUMAN_CORRECTIONS (Feedback Loop)
# Vol. IV, Cap. 8 - Aprendizado via correções humanas
# ==============================================================================

class HumanCorrection(Base):
    """
    Registro de correções humanas para aprendizado contínuo.
    Permite que o sistema aprenda com os erros sem re-treinamento.
    """
    __tablename__ = "human_corrections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Hash da entrada original
    input_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    
    # Texto original que a IA recebeu
    original_input: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Predição da IA que foi rejeitada
    ai_prediction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Correção final do humano
    human_correction: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Delta de confiança (quão errada estava a IA)
    confidence_delta: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(3, 2, asdecimal=True), nullable=True
    )
    
    # Se já foi processado para atualizar RAG
    processed: Mapped[bool] = mapped_column(Integer, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now()
    )

    def __repr__(self):
        return f"<Correction(input='{self.original_input[:20]}...', processed={self.processed})>"
