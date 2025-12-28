"""
AutoTabloide AI - Database Seed Script
=======================================
Cria dados iniciais para demonstração e testes.
Passo 24 do Protocolo Industrial.
"""

import asyncio
from decimal import Decimal
from pathlib import Path

async def seed_database():
    """Seed do banco com produtos demo."""
    from src.core.database import AsyncSessionLocal
    from src.core.repositories import ProductRepository
    
    # Produtos de demonstração variados
    demo_products = [
        {
            "sku": "ARROZ001",
            "nome": "Arroz Branco Camil Tipo 1 5kg",
            "preco": Decimal("21.90"),
            "preco_ref": Decimal("25.90"),
            "marca": "Camil",
            "peso": "5kg",
            "categoria": "Mercearia"
        },
        {
            "sku": "FEIJAO001",
            "nome": "Feijão Carioca Camil 1kg",
            "preco": Decimal("8.49"),
            "preco_ref": Decimal("10.99"),
            "marca": "Camil",
            "peso": "1kg",
            "categoria": "Mercearia"
        },
        {
            "sku": "LEITE001",
            "nome": "Leite Integral Parmalat 1L",
            "preco": Decimal("5.99"),
            "preco_ref": Decimal("6.99"),
            "marca": "Parmalat",
            "peso": "1L",
            "categoria": "Laticínios"
        },
        {
            "sku": "CAFE001",
            "nome": "Café Pilão Torrado e Moído 500g",
            "preco": Decimal("15.90"),
            "preco_ref": Decimal("19.90"),
            "marca": "Pilão",
            "peso": "500g",
            "categoria": "Mercearia"
        },
        {
            "sku": "ACUCAR001",
            "nome": "Açúcar Refinado União 1kg",
            "preco": Decimal("4.99"),
            "preco_ref": Decimal("5.99"),
            "marca": "União",
            "peso": "1kg",
            "categoria": "Mercearia"
        },
        {
            "sku": "OLEO001",
            "nome": "Óleo de Soja Soya 900ml",
            "preco": Decimal("7.49"),
            "preco_ref": Decimal("8.99"),
            "marca": "Soya",
            "peso": "900ml",
            "categoria": "Mercearia"
        },
        {
            "sku": "MARG001",
            "nome": "Margarina Qualy com Sal 500g",
            "preco": Decimal("6.99"),
            "preco_ref": Decimal("8.49"),
            "marca": "Qualy",
            "peso": "500g",
            "categoria": "Laticínios"
        },
        {
            "sku": "CERV001",
            "nome": "Cerveja Skol Pilsen Lata 350ml",
            "preco": Decimal("3.49"),
            "preco_ref": Decimal("4.29"),
            "marca": "Skol",
            "peso": "350ml",
            "categoria": "Bebidas Alcoólicas"
        },
        {
            "sku": "REFRI001",
            "nome": "Refrigerante Coca-Cola 2L",
            "preco": Decimal("9.99"),
            "preco_ref": Decimal("11.99"),
            "marca": "Coca-Cola",
            "peso": "2L",
            "categoria": "Bebidas"
        },
        {
            "sku": "MACAR001",
            "nome": "Macarrão Espaguete Barilla 500g",
            "preco": Decimal("6.49"),
            "preco_ref": Decimal("7.99"),
            "marca": "Barilla",
            "peso": "500g",
            "categoria": "Mercearia"
        },
        {
            "sku": "BISCOITO001",
            "nome": "Biscoito Recheado Oreo 90g",
            "preco": Decimal("4.29"),
            "preco_ref": Decimal("5.49"),
            "marca": "Oreo",
            "peso": "90g",
            "categoria": "Biscoitos"
        },
        {
            "sku": "SABAO001",
            "nome": "Sabão em Pó Omo 1kg",
            "preco": Decimal("14.99"),
            "preco_ref": Decimal("18.99"),
            "marca": "Omo",
            "peso": "1kg",
            "categoria": "Limpeza"
        },
        {
            "sku": "DETERG001",
            "nome": "Detergente Líquido Ypê 500ml",
            "preco": Decimal("2.49"),
            "preco_ref": Decimal("2.99"),
            "marca": "Ypê",
            "peso": "500ml",
            "categoria": "Limpeza"
        },
        {
            "sku": "SHAMP001",
            "nome": "Shampoo Head & Shoulders 400ml",
            "preco": Decimal("19.90"),
            "preco_ref": Decimal("24.90"),
            "marca": "Head & Shoulders",
            "peso": "400ml",
            "categoria": "Higiene"
        },
        {
            "sku": "PAPEL001",
            "nome": "Papel Higiênico Neve 12 Rolos",
            "preco": Decimal("15.99"),
            "preco_ref": Decimal("19.99"),
            "marca": "Neve",
            "peso": "12un",
            "categoria": "Higiene"
        },
        {
            "sku": "WHISKY001",
            "nome": "Whisky Johnnie Walker Red Label 750ml",
            "preco": Decimal("89.90"),
            "preco_ref": Decimal("109.90"),
            "marca": "Johnnie Walker",
            "peso": "750ml",
            "categoria": "Bebidas Alcoólicas"
        },
        {
            "sku": "VINHO001",
            "nome": "Vinho Tinto Casillero del Diablo 750ml",
            "preco": Decimal("44.90"),
            "preco_ref": Decimal("54.90"),
            "marca": "Casillero del Diablo",
            "peso": "750ml",
            "categoria": "Bebidas Alcoólicas"
        },
        {
            "sku": "SUCO001",
            "nome": "Suco de Laranja Natural One 900ml",
            "preco": Decimal("12.99"),
            "preco_ref": Decimal("14.99"),
            "marca": "Natural One",
            "peso": "900ml",
            "categoria": "Bebidas"
        },
        {
            "sku": "IOGURTE001",
            "nome": "Iogurte Natural Danone 170g",
            "preco": Decimal("3.99"),
            "preco_ref": Decimal("4.99"),
            "marca": "Danone",
            "peso": "170g",
            "categoria": "Laticínios"
        },
        {
            "sku": "QUEIJO001",
            "nome": "Queijo Mussarela Fatiado Sadia 150g",
            "preco": Decimal("9.99"),
            "preco_ref": Decimal("12.99"),
            "marca": "Sadia",
            "peso": "150g",
            "categoria": "Frios"
        },
    ]
    
    async with AsyncSessionLocal() as session:
        repo = ProductRepository(session)
        
        # Verifica se já tem produtos
        count = await repo.count()
        if count > 0:
            print(f"[Seed] Banco já tem {count} produtos. Pulando seed.")
            return count
        
        created = 0
        for prod in demo_products:
            try:
                await repo.create_or_update(
                    sku=prod["sku"],
                    nome=prod["nome"],
                    preco=prod["preco"],
                    marca=prod.get("marca"),
                    peso=prod.get("peso"),
                    preco_ref=prod.get("preco_ref"),
                    categoria=prod.get("categoria")
                )
                created += 1
                print(f"[Seed] Criado: {prod['nome']}")
            except Exception as e:
                print(f"[Seed] Erro em {prod['sku']}: {e}")
        
        await session.commit()
        print(f"[Seed] Total criados: {created}")
        return created


def run_seed():
    """Executa seed de forma síncrona."""
    import asyncio
    return asyncio.run(seed_database())


if __name__ == "__main__":
    run_seed()
