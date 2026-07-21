"""
Exportação CMYK opcional (F7.5, Etapa E do Bloco E)
===================================================
Impressão profissional pede CMYK; o fluxo digital (95% do uso) segue RGB.
As regras travadas da ordem:

- A conversão acontece SÓ NA EXPORTAÇÃO, como pós-processo do PDF já
  gravado — **o caminho RGB continua byte-idêntico ao de sempre** (com o
  CMYK desligado, nenhum byte do export muda; é regra testada).
- Ghostscript ausente **degrada COM aviso** (I2): o PDF fica em RGB e o
  usuário fica sabendo — exportar nunca trava por causa de impressão.
- Perfil ICC opcional pela Config (``export.perfil_icc``); liga/desliga
  pela chave ``export.cmyk_pdf`` (padrão: desligado).
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

_SEM_STATUS: Callable[[str], None] = lambda _m: None


def ghostscript_disponivel() -> str | None:
    """Caminho do executável do Ghostscript, ou None (Windows e afins)."""
    for nome in ("gswin64c", "gswin32c", "gs"):
        caminho = shutil.which(nome)
        if caminho:
            return caminho
    return None


def converter_pdf_cmyk(origem: str | Path, destino: str | Path | None = None,
                       perfil_icc: str | None = None) -> Path:
    """Converte um PDF para /DeviceCMYK via Ghostscript (mesmo arquivo por
    padrão). Levanta ``RuntimeError`` nominal se o gs falhar/faltar."""
    gs = ghostscript_disponivel()
    if gs is None:
        raise RuntimeError("Ghostscript não encontrado — instale-o (ou "
                           "desligue o CMYK nas Configurações)")
    origem = Path(origem)
    destino = Path(destino) if destino else origem
    saida = Path(tempfile.mkdtemp(prefix="atb_cmyk_")) / "cmyk.pdf"
    comando = [gs, "-dSAFER", "-dBATCH", "-dNOPAUSE",
               "-sDEVICE=pdfwrite",
               "-sColorConversionStrategy=CMYK",
               "-dProcessColorModel=/DeviceCMYK"]
    if perfil_icc and Path(perfil_icc).is_file():
        comando.append(f"-sOutputICCProfile={perfil_icc}")
    comando += ["-o", str(saida), str(origem)]
    resultado = subprocess.run(comando, capture_output=True, timeout=300)
    if resultado.returncode != 0 or not saida.is_file():
        erro = (resultado.stderr or b"").decode(errors="replace")[-400:]
        raise RuntimeError(f"a conversão CMYK falhou (Ghostscript): {erro}")
    shutil.move(str(saida), destino)
    return destino


def pos_processar_export(caminho: str | Path,
                         status_cb: Callable[[str], None] = _SEM_STATUS,
                         raiz=None) -> tuple[Path, str | None]:
    """Pós-processo do export: aplica CMYK se LIGADO na Config.

    Devolve ``(caminho, aviso)``. Com o CMYK desligado (o padrão) é um
    no-op ABSOLUTO — o arquivo não é tocado (RGB byte-idêntico, E1).
    Ghostscript ausente/falhando → o PDF fica em RGB e o ``aviso`` conta
    (I2: degradação nunca é silenciosa); exportar jamais trava por isso.
    """
    caminho = Path(caminho)
    if caminho.suffix.lower() != ".pdf":
        return caminho, None                    # PNG/afins: nada a fazer
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio

    db = Database(raiz) if raiz is not None else Database()
    db.init()
    try:
        with db.Session() as s:
            cfg = ConfigRepositorio(s)
            ligado = bool(cfg.get("export.cmyk_pdf", False))
            perfil = str(cfg.get("export.perfil_icc") or "").strip() or None
    finally:
        db.engine.dispose()
    if not ligado:
        return caminho, None                    # RGB de sempre, intocado

    aviso_perfil = ""
    if perfil and not Path(perfil).is_file():
        aviso_perfil = (f" (o perfil ICC “{perfil}” não foi encontrado — "
                        "convertido com o padrão)")
        perfil = None
    if ghostscript_disponivel() is None:
        return caminho, ("CMYK está ligado, mas o Ghostscript não foi "
                         "encontrado — o PDF ficou em RGB")
    status_cb("Convertendo o PDF para CMYK…")
    try:
        converter_pdf_cmyk(caminho, caminho, perfil)
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        return caminho, (f"a conversão CMYK falhou — o PDF ficou em RGB "
                         f"({exc})")
    return caminho, ("PDF convertido para CMYK (impressão)" + aviso_perfil)
