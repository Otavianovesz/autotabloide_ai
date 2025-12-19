import os
import sys
import platform
import shutil
import aiosqlite
from pathlib import Path

# Constants matching setup.py
SYSTEM_ROOT_NAME = "AutoTabloide_System_Root"

def get_system_root() -> Path:
    """Resolves the absolute path to the system root."""
    # Assuming runtime execution from project root or similar. 
    # Adjust logic if needed based on entry point.
    return Path.cwd() / SYSTEM_ROOT_NAME

class MissingBinaryError(Exception):
    """Raised when a critical binary is missing from /bin."""
    pass

class FatalFileSystemError(Exception):
    """Raised when the system cannot write to its own directories."""
    pass

class IntegrityChecker:
    """
    Runtime verification logic. 
    Runs at application boot to ensure environment sanity.
    """
    
    REQUIRED_DIRS = [
        "bin", "database", "temp_render", "assets/profiles"
    ]

    def __init__(self):
        self.root = get_system_root()

    def check_topology(self):
        if not self.root.exists():
             raise FatalFileSystemError(f"System Root not found at {self.root}. Run setup.py first.")
        
        for d in self.REQUIRED_DIRS:
            path = self.root / d
            if not path.exists():
                 # We could auto-create, but at runtime, missing 'bin' or 'assets' is suspicious.
                 # 'temp_render' is volatile so we can create it.
                 if d == "temp_render":
                     path.mkdir(parents=True, exist_ok=True)
                 else:
                     raise FatalFileSystemError(f"Critical directory missing: {path}")

    def check_binaries(self):
        bin_dir = self.root / "bin"
        system = platform.system()
        
        vec_lib = "vec0.dll" if system == "Windows" else "vec0.so"
        print(f"[DEBUG] Checking for sqlite-vec at: {bin_dir / vec_lib}")
        if not (bin_dir / vec_lib).exists():
             raise MissingBinaryError(f"sqlite-vec extension ({vec_lib}) missing in {bin_dir}")

        gs_exe = "gswin64c.exe" if system == "Windows" else "gs"
        if not (bin_dir / gs_exe).exists():
             raise MissingBinaryError(f"Ghostscript executable ({gs_exe}) missing in {bin_dir}")

    def clean_temp(self):
        temp_dir = self.root / "temp_render"
        if temp_dir.exists():
            for item in temp_dir.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except Exception as e:
                    print(f"Warning: Failed to clean temp item {item}: {e}")

    def run(self):
        self.check_topology()
        self.check_binaries()
        self.clean_temp()
        print("[INTEGRITY] Runtime verification passed.")

# --- Database Factory with Robust Extension Loading ---

async def get_db(db_path: str = None) -> aiosqlite.Connection:
    """
    Creates an aiosqlite connection with sqlite-vec loaded safely.
    Uses non-blocking syntax for extension loading.
    """
    root = get_system_root()
    if db_path is None:
        db_path = root / "database" / "core.db"
    
    # Determine extension path
    bin_dir = root / "bin"
    ext_name = "vec0.dll" if platform.system() == "Windows" else "vec0.so"
    lib_path = os.path.abspath(bin_dir / ext_name)
    
    conn = await aiosqlite.connect(db_path)
    
    # Enable extension loading
    # Note: enable_load_extension is not async in aiosqlite < 0.20 (checking context usually safe to run in executor)
    # But for strict asyncio compliance/robustness as requested:
    
    def _enable_and_load(db_conn, extension_path):
        """Helper to run in thread pool to avoid blocking the event loop."""
        db_conn.enable_load_extension(True)
        db_conn.load_extension(extension_path)

    try:
        # aiosqlite 0.19+ supports await conn.load_extension logic directly usually, 
        # but the request specifically asked for robust thread usage.
        await conn.run_async(_enable_and_load, lib_path)
    except Exception as e:
        await conn.close()
        raise RuntimeError(f"Failed to load sqlite-vec extension from {lib_path}. Error: {e}")

    return conn
