# -*- mode: python ; coding: utf-8 -*-
"""Spec do PyInstaller — AutoTabloide AI 1.0 (FASE 12, Bloco G, passos 67-68).

REESCRITO na F12: o spec antigo era do protótipo (Flet/cairosvg/llama_cpp —
tudo descartado). O app real é PySide6 + Pillow + rembg/onnxruntime +
torch(CPU)/spandrel. ONEDIR de propósito (onefile com Qt+onnx+torch daria
um boot de minutos). O pesado, às claras:
- rembg/onnxruntime: recorte de fundo (o modelo .onnx baixa no 1º uso);
- torch CPU + spandrel: o Real-ESRGAN (o .pth mora na pasta do usuário);
- PySide6: a interface.
Tamanho e tempo do build são MEDIDOS por `app/scripts/empacotar.py`
(passo 80). Uso: pyinstaller autotabloide.spec
"""

import os

from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [
    # SEMENTES da raiz de dados (o launcher as copia no 1º boot): as fontes
    # reais do compositor (sem elas, acento vira caixa) + logo/sons
    ("AutoTabloide_System_Root/fontes", "semente/fontes"),
    ("AutoTabloide_System_Root/assets", "semente/assets"),
]
binaries = []
hiddenimports = []

for pacote in ("rembg", "onnxruntime", "spandrel"):
    try:
        d, b, h = collect_all(pacote)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass
hiddenimports += collect_submodules("PIL")
hiddenimports += ["sqlalchemy.dialects.sqlite", "pypdf", "openpyxl",
                  "httpx", "rapidfuzz", "pyphen"]

a = Analysis(
    ["lancar_autotabloide.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "IPython", "jupyter", "notebook",
              "pytest", "PyQt5", "PyQt6"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AutoTabloide",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon="AutoTabloide_System_Root/assets/logo.ico"
    if os.path.exists("AutoTabloide_System_Root/assets/logo.ico") else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="AutoTabloide",
)
