import asyncio
from decimal import Decimal
from src.core.database import init_db, get_db
from src.core.models import Produto, ProdutoAlias
from src.core.repositories import ProductRepository
from src.engine.judge import TheJudge, STATUS_VERDE, STATUS_AMARELO, STATUS_VERMELHO

async def test_judge():
    print("[-] Iniciando Teste do Juiz...")
    
    # 1. Setup DB
    await init_db()
    
    async for session in get_db():
        repo = ProductRepository(session)
        juiz = TheJudge(repo)
        
        # Limpar base para teste confiável
        await session.execute(from_sqlalchemy_text("DELETE FROM produto_aliases"))
        await session.execute(from_sqlalchemy_text("DELETE FROM produtos"))
        await session.commit()
        
        # -----------------------------------------------------
        # CENÁRIO 1: Match Exato
        # -----------------------------------------------------
        prod = await repo.create_or_update(
            sku="123", 
            nome="Coca-Cola 2L", 
            preco=Decimal("10.00"),
            marca="Coca-Cola",
            peso="2L"
        )
        
        veredito = await juiz.julgar({'sku_origem': '123', 'descricao': 'Qualquer coisa', 'preco': Decimal('10.00')})
        assert veredito.status == STATUS_VERDE, f"Falha Exato SKU: {veredito.status}"
        print("[OK] Match Exato (SKU)")
        
        # -----------------------------------------------------
        # CENÁRIO 2: Match Alias
        # -----------------------------------------------------
        await repo.add_alias(prod.id, "COCA COLA 2 LITROS")
        veredito = await juiz.julgar({'sku_origem': '999', 'descricao': 'COCA COLA 2 LITROS', 'preco': Decimal('10.00')})
        assert veredito.status == STATUS_VERDE, f"Falha Exato Alias: {veredito.status}"
        print("[OK] Match Exato (Alias)")

        # -----------------------------------------------------
        # CENÁRIO 3: Match Fuzzy (>90%)
        # -----------------------------------------------------
        # "Coca-Cola 2L" (BD) vs "Coca-Cola 2L Promocao" (Input) - deve dar match alto ou similar
        # Vamos testar algo bem próximo: "Coca-Cola 2L."
        veredito = await juiz.julgar({'sku_origem': '888', 'descricao': 'Coca-Cola 2L', 'preco': Decimal('10.00')}) 
        # Nota: Como o nome exato já existe no BD em 'prod.nome_sanitizado', rapidfuzz deve achar
        # Rapidfuzz match com 'Coca-Cola 2L' (100%) mas sem ser SKU/Alias explícito
        assert veredito.status == STATUS_AMARELO, f"Falha Fuzzy: {veredito.status}"
        print(f"[OK] Match Fuzzy (Score: {veredito.confianca})")

        # -----------------------------------------------------
        # CENÁRIO 4: Novo Produto (Sanitização)
        # -----------------------------------------------------
        input_sujo = "ARROZ TIO JOAO 500 GR"
        veredito = await juiz.julgar({'sku_origem': '777', 'descricao': input_sujo, 'preco': Decimal('5.00')})
        assert veredito.status == STATUS_VERMELHO, f"Falha Novo: {veredito.status}"
        
        sanitizado = veredito.dados_sanitizados['nome_sanitizado']
        esperado = "Arroz Tio Joao 500g" # Title case e Unidade
        # Nota: Title() do python em "JOAO" vira "Joao". 
        # O regex converte "500 GR" -> "500g" antes ou depois?
        # Código: upper -> regex -> title -> fix units
        # ARROZ TIO JOAO 500 GR -> ARROZ TIO JOAO 500g -> Arroz Tio Joao 500g
        
        assert sanitizado == esperado, f"Falha Sanitização: '{sanitizado}' != '{esperado}'"
        print(f"[OK] Sanitização: '{input_sujo}' -> '{sanitizado}'")

from sqlalchemy import text as from_sqlalchemy_text

if __name__ == "__main__":
    asyncio.run(test_judge())
