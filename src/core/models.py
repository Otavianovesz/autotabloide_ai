import json
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Integer, String, Numeric, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Produto(Base):
    __tablename__ = "produtos"

    # Identificação
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku_origem: Mapped[str] = mapped_column(String, unique=True, nullable=False) # A "Chave Suja" mas única
    
    # Dados Sanitizados
    nome_sanitizado: Mapped[str] = mapped_column(String, nullable=False)
    marca_normalizada: Mapped[str] = mapped_column(String, index=True, nullable=True)
    detalhe_peso: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Ex: "500g"
    
    # Precificação (CRÍTICO: DECIMAL, NÃO FLOAT)
    preco_venda_atual: Mapped[Decimal] = mapped_column(Numeric(10, 2, asdecimal=True), nullable=False)
    preco_referencia: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2, asdecimal=True), nullable=True)
    
    # Gestão de Ativos (Armazenado como JSON String, manipulado como lista)
    img_hash_ref: Mapped[Optional[str]] = mapped_column(String, nullable=True, default="[]")
    
    # Metadados de Qualidade e Controle
    status_qualidade: Mapped[int] = mapped_column(Integer, default=0) # 0=Novo, 1=Revisado, 2=Aprovado, 3=Publicado
    last_modified: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, server_default=func.now(), onupdate=func.now())

    # Relacionamentos
    aliases: Mapped[List["ProdutoAlias"]] = relationship("ProdutoAlias", back_populates="produto", cascade="all, delete-orphan")

    # Helpers para Manipulação de Ativos
    def set_images(self, hashes: List[str]):
        self.img_hash_ref = json.dumps(hashes)

    def get_images(self) -> List[str]:
        if not self.img_hash_ref:
            return []
        try:
            return json.loads(self.img_hash_ref)
        except json.JSONDecodeError:
            return []

    def __repr__(self):
        return f"<Produto(sku='{self.sku_origem}', nome='{self.nome_sanitizado}')>"

class ProdutoAlias(Base):
    """
    Tabela fundamental para o 'Juiz'. 
    Permite que o sistema aprenda que 'Cerveja X 350ml' é o mesmo que 'Cerv. X LATA'.
    """
    __tablename__ = "produto_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alias_raw: Mapped[str] = mapped_column(String, index=True, nullable=False)
    produto_id: Mapped[int] = mapped_column(Integer, ForeignKey("produtos.id"), nullable=False)

    produto: Mapped["Produto"] = relationship("Produto", back_populates="aliases")

    def __repr__(self):
        return f"<Alias(raw='{self.alias_raw}', produto_id={self.produto_id})>"
