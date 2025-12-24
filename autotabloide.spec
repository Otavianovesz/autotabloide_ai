# -*- mode: python ; coding: utf-8 -*-
"""
AutoTabloide AI - PyInstaller Spec
====================================
Configuração para build de executável.
Passos 80-82 do Checklist 100.

Uso:
    pyinstaller autotabloide.spec

Assets incluídos:
- Fontes em assets/fonts/
- Templates em library/svg_source/
- Modelos em bin/models/
- Ícone da aplicação
"""

import os
import sys
from pathlib import Path

# Diretório raiz
ROOT_DIR = Path(SPECPATH)

# Nome do executável
APP_NAME = "AutoTabloide_AI"
ICON_PATH = ROOT_DIR / "assets" / "icon.ico"

# Imports ocultos necessários
hidden_imports = [
    # Flet e dependências
    'flet',
    'flet_core',
    'flet_runtime',
    
    # SQLAlchemy
    'sqlalchemy',
    'aiosqlite',
    'sqlalchemy.ext.asyncio',
    
    # AI
    'llama_cpp',
    
    # Imagem
    'PIL',
    'PIL.Image',
    'PIL.ImageFont',
    'cairosvg',
    'lxml',
    'lxml.etree',
    
    # Opcional
    'rembg',
    'cv2',
    'pyphen',
    'rapidfuzz',
    'pydantic',
]

# Dados a incluir
datas = [
    # Fontes
    (str(ROOT_DIR / 'AutoTabloide_System_Root' / 'assets' / 'fonts'), 'assets/fonts'),
    
    # Templates SVG
    (str(ROOT_DIR / 'AutoTabloide_System_Root' / 'library' / 'svg_source'), 'library/svg_source'),
    
    # Thumbnails
    (str(ROOT_DIR / 'AutoTabloide_System_Root' / 'library' / 'thumbnails'), 'library/thumbnails'),
    
    # Sons
    (str(ROOT_DIR / 'AutoTabloide_System_Root' / 'assets' / 'sounds'), 'assets/sounds'),
]

# Binários extras
binaries = []

# Se o modelo LLM existir, incluir
model_path = ROOT_DIR / 'AutoTabloide_System_Root' / 'bin' / 'models'
if model_path.exists():
    for gguf_file in model_path.glob('*.gguf'):
        # Nota: modelos GGUF são grandes, considere distribuir separadamente
        pass

# Ghostscript bundled (se existir)
gs_path = ROOT_DIR / 'AutoTabloide_System_Root' / 'bin' / 'gs'
if gs_path.exists():
    binaries.append((str(gs_path), 'bin/gs'))

# Análise do código
a = Analysis(
    ['main.py'],
    pathex=[str(ROOT_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'notebook',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Filtrar binários desnecessários
a.binaries = [b for b in a.binaries if not b[0].startswith('api-ms-')]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI sem console
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON_PATH) if ICON_PATH.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)
