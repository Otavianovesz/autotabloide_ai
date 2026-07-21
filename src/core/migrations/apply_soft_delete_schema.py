
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.core.database import AsyncSessionLocal
from src.core.soft_delete import add_soft_delete_columns

async def apply_migrations():
    print("--- Applying Soft Delete Schema Migrations ---")
    
    async with AsyncSessionLocal() as session:
        # Migrate 'produtos'
        print("Migrating 'produtos'...")
        try:
            added = await add_soft_delete_columns(session, "produtos")
            if added:
                print("   -> Added columns to 'produtos'")
            else:
                print("   -> 'produtos' already has columns")
        except Exception as e:
            print(f"   -> Error on 'produtos': {e}")

        # Migrate 'projetos_salvos'
        print("Migrating 'projetos_salvos'...")
        try:
            added = await add_soft_delete_columns(session, "projetos_salvos")
            if added:
                print("   -> Added columns to 'projetos_salvos'")
            else:
                print("   -> 'projetos_salvos' already has columns")
        except Exception as e:
            print(f"   -> Error on 'projetos_salvos': {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(apply_migrations())
