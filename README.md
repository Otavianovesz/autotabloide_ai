# Autotabloide AI

## Overview

Offline-first AI-powered tabloid generation system.

## Setup Instructions

1. **Initialize Requirements**:
   Run the setup script to create the directory structure:

   ```bash
   python setup.py
   ```

2. **Critical Binaries (Manual Step)**:
   Per strict offline protocols, you must manually populate the `AutoTabloide_System_Root/bin/` directory with:

   - `vec0.dll` (Windows) or `vec0.so` (Linux) - [sqlite-vec extension]
   - `gswin64c.exe` (Windows) or `gs` (Linux) - [Ghostscript]

3. **Install Dependencies**:
   ```bash
   poetry install
   ```

## Architecture

- **Root**: `AutoTabloide_System_Root/`
- **Database**: SQLite + `sqlite-vec` (Vector Search)
- **GUI**: Flet
- **AI**: Local GGUF models via `llama-cpp-python`
