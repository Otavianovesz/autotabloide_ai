import asyncio
from src.core.database import init_db, engine
from sqlalchemy import text

async def verify_infrastructure():
    print("[-] Iniciando Verificação de Infraestrutura Auditada...")
    
    # 1. Criação de tabelas via função oficial
    try:
        await init_db()
        print("[+] Schema inicializado com sucesso.")
    except Exception as e:
        print(f"[CRITICAL] Falha ao inicializar o banco: {e}")
        return

    # 2. Verificação de PRAGMAs (WAL, Foreign Keys)
    async with engine.connect() as conn:
        print("[-] Verificando PRAGMAs críticos...")
        
        # Check WAL
        res_wal = await conn.execute(text("PRAGMA journal_mode"))
        wal_mode = res_wal.scalar()
        if wal_mode.upper() == "WAL":
            print("[OK] Journal Mode: WAL (Ativo)")
        else:
            print(f"[CRITICAL] Journal Mode Incorreto: {wal_mode} (Esperado: WAL)")

        # Check FK
        res_fk = await conn.execute(text("PRAGMA foreign_keys"))
        fk_mode = res_fk.scalar()
        if fk_mode == 1:
            print("[OK] Foreign Keys: ON (Ativo)")
        else:
            print(f"[CRITICAL] Foreign Keys Incorreto: {fk_mode} (Esperado: 1)")

if __name__ == "__main__":
    asyncio.run(verify_infrastructure())
