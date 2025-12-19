"""
AutoTabloide AI - Script de Inicialização do Banco de Dados
============================================================
Cria todas as tabelas e executa validação inicial.
Execute: python init_db.py
"""

import asyncio
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    print("=" * 60)
    print("AutoTabloide AI - Inicialização do Banco de Dados")
    print("=" * 60)
    
    # 1. Inicializa Schema
    print("\n[1/3] Criando schema do banco de dados...")
    from src.core.database import init_db, check_db_health, get_table_counts
    await init_db()
    print("     [OK] Tabelas criadas com sucesso!")
    
    # 2. Verifica saude
    print("\n[2/3] Verificando saude do banco...")
    health = await check_db_health()
    print(f"     Status: {health['status']}")
    print(f"     Journal Mode: {health.get('journal_mode', 'N/A')}")
    print(f"     Integridade: {health.get('integrity', 'N/A')}")
    print(f"     Tamanho DB: {health.get('db_size_bytes', 0):,} bytes")
    print(f"     Path: {health.get('db_path', 'N/A')}")
    
    # 3. Conta registros
    print("\n[3/3] Contando registros existentes...")
    counts = await get_table_counts()
    for table, count in counts.items():
        print(f"     {table}: {count} registros")
    
    print("\n" + "=" * 60)
    print("[OK] Inicializacao concluida com sucesso!")
    print("=" * 60)
    
    # Lista tabelas criadas
    print("\nTabelas do Schema:")
    from src.core.models import Base
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")

if __name__ == "__main__":
    asyncio.run(main())
