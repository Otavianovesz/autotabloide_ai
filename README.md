# AutoTabloide AI

## Overview

Offline-first AI-powered tabloid generation system for retail graphic automation.

## Features

- **Industrial-grade rendering**: SVG vector manipulation with CMYK support
- **Local AI**: LLM for data sanitization, image search, background removal
- **Qt Desktop UI**: 5 screens (Ateliê, Almoxarifado, Fábrica, Cofre, Configurações)
- **Offline-First**: Complete autonomy without cloud dependencies

## Setup Instructions

1. **Initialize Requirements**:
   Run the setup script to create the directory structure:

   ```bash
   python setup.py
   ```

2. **Critical Binaries (Manual Step)**:
   Per strict offline protocols, you must manually populate the `AutoTabloide_System_Root/bin/` directory with:

   - `vec0.dll` (Windows) or `vec0.so` (Linux) - [sqlite-vec extension] (optional, for RAG)
   - `gswin64c.exe` (Windows) or `gs` (Linux) - [Ghostscript] (required for PDF/CMYK)

3. **Install Dependencies**:

   ```bash
   poetry install
   ```

4. **Verify Installation**:

   ```bash
   python verify_system.py
   ```

5. **Run Application**:
   ```bash
   python main.py
   ```

## Architecture

- **Root**: `AutoTabloide_System_Root/`
- **Database**: SQLite (WAL mode) + optional `sqlite-vec` for vector search
- **GUI**: PySide6 (Qt6)
- **AI**: Local GGUF models via `llama-cpp-python`
- **Rendering**: lxml + CairoSVG + Ghostscript

## Tech Stack

| Component      | Technology                    |
| -------------- | ----------------------------- |
| Language       | Python 3.12+                  |
| UI Framework   | PySide6 (Qt6)                 |
| Database       | SQLAlchemy Async + SQLite WAL |
| Vector Engine  | lxml + CairoSVG               |
| AI/ML          | llama-cpp-python, rembg, ONNX |
| PDF Processing | Ghostscript, pypdf            |
