"""
AutoTabloide AI - Testes de Modelos de Dados
=============================================
Valida schema, relacionamentos e métodos helper.
"""

import pytest
import asyncio
import json
from decimal import Decimal
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.models import (
    Base, Produto, ProdutoAlias, LayoutMeta, ProjetoSalvo,
    AuditLog, KnowledgeVector, HumanCorrection,
    TipoMidia, StatusQualidade, TipoAcao, TipoEntidade
)


class TestEnumerations:
    """Testa enumerações de tipos."""
    
    def test_tipo_midia_values(self):
        """Verifica valores de TipoMidia."""
        assert TipoMidia.TABLOIDE.value == "TABLOIDE"
        assert TipoMidia.CARTAZ_A4.value == "CARTAZ_A4"
        assert TipoMidia.CARTAZ_GIGANTE.value == "CARTAZ_GIGANTE"
        assert TipoMidia.ETIQUETA.value == "ETIQUETA"
    
    def test_status_qualidade_values(self):
        """Verifica valores de StatusQualidade."""
        assert StatusQualidade.INCOMPLETO.value == 0
        assert StatusQualidade.SEM_FOTO.value == 1
        assert StatusQualidade.FOTO_BAIXA_RES.value == 2
        assert StatusQualidade.PRONTO.value == 3
    
    def test_tipo_acao_values(self):
        """Verifica valores de TipoAcao."""
        assert TipoAcao.CREATE.value == "CREATE"
        assert TipoAcao.UPDATE.value == "UPDATE"
        assert TipoAcao.DELETE.value == "DELETE"
        assert TipoAcao.ROLLBACK.value == "ROLLBACK"


class TestProdutoModel:
    """Testa modelo Produto."""
    
    def test_produto_creation(self):
        """Testa criação de produto com campos obrigatórios."""
        produto = Produto(
            sku_origem="SKU123",
            nome_sanitizado="Cafe Pilao 500g",
            preco_venda_atual=Decimal("19.90"),
            status_qualidade=StatusQualidade.INCOMPLETO.value  # Explicit for test
        )
        
        assert produto.sku_origem == "SKU123"
        assert produto.nome_sanitizado == "Cafe Pilao 500g"
        assert produto.preco_venda_atual == Decimal("19.90")
        assert produto.status_qualidade == StatusQualidade.INCOMPLETO.value
    
    def test_produto_images_helpers(self):
        """Testa métodos set_images e get_images."""
        produto = Produto(
            sku_origem="SKU456",
            nome_sanitizado="Arroz",
            preco_venda_atual=Decimal("10.00")
        )
        
        # Inicialmente vazio
        assert produto.get_images() == []
        
        # Define lista de imagens
        hashes = ["abc123", "def456", "ghi789"]
        produto.set_images(hashes)
        
        # Recupera lista
        assert produto.get_images() == hashes
        
        # Adiciona imagem
        produto.add_image("jkl012")
        assert "jkl012" in produto.get_images()
        
        # Não adiciona duplicata
        produto.add_image("abc123")
        assert produto.get_images().count("abc123") == 1
    
    def test_produto_is_alcoholic(self):
        """Testa detecção de produto com restrição de idade."""
        # Produto normal
        produto1 = Produto(
            sku_origem="P1",
            nome_sanitizado="Leite",
            preco_venda_atual=Decimal("5.00"),
            categoria="Laticinio"
        )
        assert produto1.is_alcoholic() == False
        
        # Cerveja
        produto2 = Produto(
            sku_origem="P2",
            nome_sanitizado="Heineken",
            preco_venda_atual=Decimal("6.00"),
            categoria="Cerveja"
        )
        assert produto2.is_alcoholic() == True
        
        # Bebida alcoólica
        produto3 = Produto(
            sku_origem="P3",
            nome_sanitizado="Vodka",
            preco_venda_atual=Decimal("50.00"),
            categoria="Bebida Alcoólica"
        )
        assert produto3.is_alcoholic() == True
        
        # Sem categoria
        produto4 = Produto(
            sku_origem="P4",
            nome_sanitizado="Produto X",
            preco_venda_atual=Decimal("10.00")
        )
        assert produto4.is_alcoholic() == False
    
    def test_produto_repr(self):
        """Testa representação string."""
        produto = Produto(
            id=1,
            sku_origem="XYZ",
            nome_sanitizado="Teste",
            preco_venda_atual=Decimal("1.00")
        )
        repr_str = repr(produto)
        assert "Produto" in repr_str
        assert "XYZ" in repr_str


class TestLayoutMetaModel:
    """Testa modelo LayoutMeta."""
    
    def test_layout_creation(self):
        """Testa criação de layout."""
        layout = LayoutMeta(
            nome_amigavel="Oferta Semanal",
            arquivo_fonte="oferta_semanal.svg",
            tipo_midia=TipoMidia.TABLOIDE.value,
            capacidade_slots=12
        )
        
        assert layout.nome_amigavel == "Oferta Semanal"
        assert layout.capacidade_slots == 12
        assert layout.tipo_midia == "TABLOIDE"
    
    def test_layout_fonts_helpers(self):
        """Testa métodos get_fonts e set_fonts."""
        layout = LayoutMeta(
            nome_amigavel="Test",
            arquivo_fonte="test.svg"
        )
        
        # Inicialmente vazio
        assert layout.get_fonts() == []
        
        # Define fontes
        fonts = ["Roboto-Bold.ttf", "Arial.ttf"]
        layout.set_fonts(fonts)
        
        # Recupera
        assert layout.get_fonts() == fonts
    
    def test_layout_structure_helpers(self):
        """Testa métodos get_structure."""
        layout = LayoutMeta(
            nome_amigavel="Test",
            arquivo_fonte="test.svg"
        )
        
        # Inicialmente vazio
        assert layout.get_structure() == {}
        
        # Com estrutura
        structure = {"slots": ["SLOT_01", "SLOT_02"], "texts": ["TXT_NOME"]}
        layout.estrutura_json = json.dumps(structure)
        
        assert layout.get_structure() == structure


class TestProjetoSalvoModel:
    """Testa modelo ProjetoSalvo."""
    
    def test_projeto_creation(self):
        """Testa criação de projeto."""
        projeto = ProjetoSalvo(
            nome_projeto="Campanha Natal",
            uuid="abc-123-def",
            layout_id=1,
            is_locked=False,  # Explicit for test (defaults apply on DB commit)
            is_dirty=False
        )
        
        assert projeto.nome_projeto == "Campanha Natal"
        assert projeto.uuid == "abc-123-def"
        assert projeto.is_locked == False
        assert projeto.is_dirty == False
    
    def test_projeto_slots_helpers(self):
        """Testa métodos de manipulação de slots."""
        projeto = ProjetoSalvo(
            nome_projeto="Test",
            uuid="test-uuid",
            layout_id=1
        )
        
        # Inicialmente vazio
        assert projeto.get_slots() == {}
        
        # Define slots
        slots = {
            "SLOT_01": {"produto_id": 1, "preco": 19.90, "nome": "Cafe"},
            "SLOT_02": {"produto_id": 2, "preco": 24.50, "nome": "Arroz"}
        }
        projeto.set_slots(slots)
        
        # Recupera
        assert projeto.get_slots() == slots
    
    def test_projeto_overrides(self):
        """Testa overrides sobre slots."""
        projeto = ProjetoSalvo(
            nome_projeto="Test",
            uuid="test-uuid",
            layout_id=1
        )
        
        # Define slots base
        projeto.set_slots({
            "SLOT_01": {"produto_id": 1, "preco": 19.90, "nome": "Cafe"}
        })
        
        # Define override
        projeto.set_overrides({
            "SLOT_01": {"preco": 17.90}  # Preço promocional só neste projeto
        })
        
        # get_slot_data deve mesclar
        data = projeto.get_slot_data("SLOT_01")
        assert data["produto_id"] == 1
        assert data["nome"] == "Cafe"
        assert data["preco"] == 17.90  # Override aplicado


class TestAuditLogModel:
    """Testa modelo AuditLog."""
    
    def test_audit_creation(self):
        """Testa criação de log."""
        log = AuditLog(
            entity_type=TipoEntidade.PRODUTO.value,
            entity_id=1,
            action_type=TipoAcao.UPDATE.value,
            severity=1
        )
        
        assert log.entity_type == "PRODUTO"
        assert log.action_type == "UPDATE"
    
    def test_audit_diff_helpers(self):
        """Testa métodos de diff."""
        log = AuditLog(
            entity_type="PRODUTO",
            entity_id=1,
            action_type="UPDATE"
        )
        
        # Define diff
        diff = {
            "field": "preco_venda",
            "old_value": 19.90,
            "new_value": 17.90,
            "source_context": "manual_ui"
        }
        log.set_diff(diff)
        
        # Recupera
        assert log.get_diff() == diff
        assert log.get_old_value() == 19.90
        assert log.get_new_value() == 17.90
    
    def test_audit_can_rollback(self):
        """Testa verificação de rollback."""
        # UPDATE com old_value pode rollback
        log1 = AuditLog(
            entity_type="PRODUTO",
            entity_id=1,
            action_type="UPDATE"
        )
        log1.set_diff({"field": "preco", "old_value": 10, "new_value": 15})
        assert log1.can_rollback() == True
        
        # CREATE não pode rollback
        log2 = AuditLog(
            entity_type="PRODUTO",
            entity_id=1,
            action_type="CREATE"
        )
        assert log2.can_rollback() == False
        
        # UPDATE sem old_value não pode rollback
        log3 = AuditLog(
            entity_type="PRODUTO",
            entity_id=1,
            action_type="UPDATE"
        )
        log3.set_diff({"field": "preco", "new_value": 15})
        assert log3.can_rollback() == False


class TestKnowledgeVectorModel:
    """Testa modelo KnowledgeVector."""
    
    def test_knowledge_vector_creation(self):
        """Testa criação de vetor de conhecimento."""
        vector = KnowledgeVector(
            source_text="Cerveja Heineken 350ml Lata",
            text_hash="abc123hash",
            embedding=b"\x00\x01\x02",
            dimensions=384,
            priority_boost=Decimal("1.0")  # Explicit for test
        )
        
        assert vector.source_text == "Cerveja Heineken 350ml Lata"
        assert vector.dimensions == 384
        assert vector.priority_boost == Decimal("1.0")


class TestHumanCorrectionModel:
    """Testa modelo HumanCorrection."""
    
    def test_correction_creation(self):
        """Testa criação de correção humana."""
        correction = HumanCorrection(
            input_hash="inputhash123",
            original_input="CERV HEIN 350ML LT",
            ai_prediction="Cerveja Heineken 350ml",
            human_correction="Cerveja Heineken Lata 350ml",
            processed=False
        )
        
        assert correction.original_input == "CERV HEIN 350ML LT"
        assert correction.processed == False


# Pytest configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
