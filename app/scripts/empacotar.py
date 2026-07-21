"""Empacota o AutoTabloide (FASE 12, Bloco G, passos 67-68 e 80).

Roda o PyInstaller com o ``autotabloide.spec`` e MEDE o que importa:
tempo do build, tamanho da pasta ``dist/AutoTabloide`` e tamanho do .zip
portátil. Os números vão para ``saida_marco/medicoes.json`` (a mesma
ficha do marco) — medição registrada, não achismo (lei do passo 80).

Rodar::  python -m app.scripts.empacotar
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DIST = RAIZ / "dist" / "AutoTabloide"
MEDICOES = RAIZ / "saida_marco" / "medicoes.json"


def _tamanho_mb(pasta: Path) -> float:
    total = sum(f.stat().st_size for f in pasta.rglob("*") if f.is_file())
    return round(total / (1024 * 1024), 1)


def _zip_portatil(pasta: Path, destino: Path) -> float:
    """Compacta a pasta onedir num .zip 'leve no pendrive' e devolve o
    tamanho em MB."""
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=6) as z:
        for f in sorted(pasta.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(pasta.parent))
    return round(destino.stat().st_size / (1024 * 1024), 1)


def empacotar(com_zip: bool = True) -> dict:
    inicio = time.monotonic()
    proc = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "autotabloide.spec",
         "--noconfirm", "--clean"],
        cwd=RAIZ, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    duracao = round(time.monotonic() - inicio, 1)
    if proc.returncode != 0:
        cauda = "\n".join((proc.stderr or "").splitlines()[-25:])
        raise RuntimeError(
            f"PyInstaller falhou (código {proc.returncode}):\n{cauda}")
    exe = DIST / "AutoTabloide.exe"
    if not exe.exists():
        raise RuntimeError(f"build terminou mas {exe} não existe")

    medidas = {
        "build_segundos": duracao,
        "pasta_dist_mb": _tamanho_mb(DIST),
        "exe_mb": round(exe.stat().st_size / (1024 * 1024), 1),
        "arquivos": sum(1 for f in DIST.rglob("*") if f.is_file()),
    }
    if com_zip:
        zip_destino = RAIZ / "dist" / "AutoTabloide_1.0_portatil.zip"
        medidas["zip_portatil_mb"] = _zip_portatil(DIST, zip_destino)
        medidas["zip_portatil"] = zip_destino.name

    # registra na ficha do marco (preserva o que já foi medido)
    ficha = {}
    if MEDICOES.exists():
        ficha = json.loads(MEDICOES.read_text(encoding="utf-8"))
    ficha["instalador"] = medidas
    MEDICOES.parent.mkdir(parents=True, exist_ok=True)
    MEDICOES.write_text(json.dumps(ficha, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    return medidas


def main() -> int:
    if shutil.which("pyinstaller") is None:
        try:
            import PyInstaller  # noqa: F401
        except ImportError:
            print("PyInstaller não instalado: pip install pyinstaller")
            return 1
    medidas = empacotar()
    print(f"build em {medidas['build_segundos']}s — "
          f"pasta {medidas['pasta_dist_mb']} MB "
          f"({medidas['arquivos']} arquivos)"
          + (f", zip {medidas['zip_portatil_mb']} MB"
             if "zip_portatil_mb" in medidas else ""))
    print(f"medições em {MEDICOES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
