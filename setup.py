import os
import sys
import shutil
import platform
from pathlib import Path

# --- Configuration ---
REQUIRED_DIRS = [
    "bin",
    "config",
    "database",
    "snapshots",
    "assets/store",
    "assets/profiles",
    "staging",
    "temp_render",
    "library/svg_source",
    "library/thumbnails",
    "workspace/projects",
    "logs",
]

CRITICAL_BINARIES_WINDOWS = {
    "sqlite_vec": "vec0.dll",
    "ghostscript": "gswin64c.exe"
}

CRITICAL_BINARIES_UNIX = {
    "sqlite_vec": "vec0.so",
    "ghostscript": "gs"
}

def check_binaries(root_path: Path):
    """
    Verifies that critical binaries exist in the /bin directory.
    This enforces the 'Portable App' and 'Offline-First' requirement.
    """
    bin_dir = root_path / "bin"
    system = platform.system()
    
    required_binaries = {}
    if system == "Windows":
        required_binaries = CRITICAL_BINARIES_WINDOWS
    else:
        # Assuming Linux/Mac for robustness, though primary target is likely Windows
        required_binaries = CRITICAL_BINARIES_UNIX

    missing = []
    
    # 1. Check sqlite-vec
    vec_binary = bin_dir / required_binaries["sqlite_vec"]
    if not vec_binary.exists():
        missing.append(f"sqlite-vec extension ({required_binaries['sqlite_vec']})")

    # 2. Check Ghostscript
    gs_binary = bin_dir / required_binaries["ghostscript"]
    if not gs_binary.exists():
        missing.append(f"Ghostscript executable ({required_binaries['ghostscript']})")

    if missing:
        print("\n[CRITICAL ERROR] Missing Critical Binaries in /bin/")
        print("The following files are required for Autotabloide AI to function:")
        for item in missing:
            print(f"  - {item}")
        print("\nPlease populate the 'bin' directory manually from the distribution package.")
        print("We do not download these at runtime to strictly adhere to 'Offline-First' protocols.")
        sys.exit(1)
    else:
        print("[OK] Critical binaries verified.")

def main():
    print("INITIALIZING AUTOTABLOIDE AI INDUSTRIAL PROTOCOLS...")

    # 1. Define Root
    # In a portable app context, CWD is often the root.
    root = Path.cwd()
    system_root = root / "AutoTabloide_System_Root"
    
    # If the script is run FROM the root, or if we want to create the root subfolder:
    # The requirement said root is /AutoTabloide_System_Root/
    # We will ensure this directory exists.
    
    if not system_root.exists():
        try:
            system_root.mkdir()
            print(f"[CREATED] System Root: {system_root}")
        except PermissionError:
             print(f"[FATAL] Cannot create directory {system_root}. Run as Administrator.")
             sys.exit(1)

    # 2. Topology Enforcement
    for relative_path in REQUIRED_DIRS:
        target = system_root / relative_path
        if not target.exists():
            print(f"[CREATING] {target}")
            target.mkdir(parents=True, exist_ok=True)
    
    # Check for profiles
    manual_check = system_root / "assets/profiles/CoatedFOGRA39.icc"
    if not manual_check.exists():
        print("[WARNING] CoatedFOGRA39.icc profile missing in assets/profiles/.")
        print("Color management will be compromised until this file is added.")

    # 3. Critical Binary Verification (The "Empty Bin" Fix)
    # Note: We check inside the system_root/bin
    try:
        check_binaries(system_root)
    except SystemExit:
        # If check_binaries exits, we stop here.
        raise

    # 4. Validate Write Permissions
    test_file = system_root / "temp_render" / ".write_test"
    try:
        test_file.touch()
        test_file.unlink()
        print("[SUCCESS] Write permissions confirmed.")
    except PermissionError:
        print("[FATAL] Write permission denied in /temp_render. Run as Administrator.")
        sys.exit(1)
        
    # 5. Sanitization (Clean Boot)
    # Prevent disk bloating from previous crashed sessions.
    temp_render = system_root / "temp_render"
    if temp_render.exists():
         print("[CLEANUP] Sanitizing temp_render...")
         for item in temp_render.iterdir():
             if item.is_file():
                 item.unlink()
             elif item.is_dir():
                 shutil.rmtree(item)

    print("\nSYSTEM TOPOLOGY ESTABLISHED. READY FOR DEPLOYMENT.")

if __name__ == "__main__":
    main()
