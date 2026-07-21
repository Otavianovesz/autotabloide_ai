
import asyncio
import sys
import os
from pathlib import Path
from sqlalchemy import select, update

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.core.database import AsyncSessionLocal
from src.core.models import LayoutMeta
from src.core.services.file_service import FileSystemService

async def migrate_paths():
    print("--- Migrating Absolute Paths to Relative (CAS) ---")
    
    fs = FileSystemService()
    migrated_count = 0
    errors = 0
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(LayoutMeta))
        layouts = result.scalars().all()
        
        print(f"Scanning {len(layouts)} layouts...")
        
        for layout in layouts:
            changed = False
            
            # 1. Migrate Source File
            if os.path.isabs(layout.arquivo_fonte):
                print(f"Migrating source: {layout.arquivo_fonte}")
                try:
                    # Import to CAS
                    _, rel_path, _ = fs.import_asset(layout.arquivo_fonte)
                    
                    # Update DB (Direct update to bypass repository check during migration?? 
                    # Actually repo check is for NEW inserts/updates via repo methods. 
                    # Here we update object attached to session.)
                    layout.arquivo_fonte = rel_path
                    changed = True
                    print(f"   -> migrated to: {rel_path}")
                except FileNotFoundError:
                    print(f"   [ERROR] File not found: {layout.arquivo_fonte}")
                    errors += 1
                except Exception as e:
                    print(f"   [ERROR] Failed to migrate: {e}")
                    errors += 1
            
            # 2. Migrate Thumbnail
            if layout.thumbnail_path and os.path.isabs(layout.thumbnail_path):
                print(f"Migrating thumb: {layout.thumbnail_path}")
                try:
                    _, rel_path, _ = fs.import_asset(layout.thumbnail_path)
                    layout.thumbnail_path = rel_path
                    changed = True
                    print(f"   -> migrated to: {rel_path}")
                except FileNotFoundError:
                    print(f"   [ERROR] File not found: {layout.thumbnail_path}")
                    errors += 1
                except Exception as e:
                    print(f"   [ERROR] Failed to migrate: {e}")
                    errors += 1
            
            if changed:
                migrated_count += 1
        
        if migrated_count > 0:
            await session.commit()
            print(f"\nMigration complete. {migrated_count} layouts updated.")
        else:
            print("\nNo layouts required migration.")
            
        if errors > 0:
            print(f"WARNING: {errors} files could not be migrated (not found or error).")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(migrate_paths())
    except Exception as e:
        print(f"Fatal Error: {e}")
