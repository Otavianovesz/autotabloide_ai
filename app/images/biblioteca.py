"""
Biblioteca de imagens (F4.4) — ingestão, armazenamento e histórico
==================================================================
Camada headless que RECEBE uma imagem de qualquer fonte (bytes colados, caminho
de arquivo, URL), opcionalmente a processa (remoção de fundo → recorte → upscale)
e a armazena com versionamento. Os gestos de UI (colar/arrastar) ficam no Bloco D.

Layout em disco (referenciado pela portabilidade F7.4 e pelo empacotamento):

    biblioteca_imagens/<id_produto>/atual.png
    biblioteca_imagens/<id_produto>/versoes/<timestamp>.png

O banco (Produto.caminho_imagem) guarda o caminho RELATIVO da atual (portável);
o histórico vive só em disco, com limite configurável.
"""

from __future__ import annotations

import io
import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable

from PIL import Image


def _baixar_url_http(url: str) -> bytes:
    import httpx

    r = httpx.get(url, follow_redirects=True, timeout=60)
    r.raise_for_status()
    return r.content


# fonte pode ser: bytes (colado), caminho de arquivo, ou URL (str http...)
Fonte = bytes | str | Path


class BibliotecaImagens:
    def __init__(
        self,
        raiz: str | Path,
        *,
        processador: Callable[[Image.Image], Image.Image] | None = None,
        baixar_url: Callable[[str], bytes] | None = None,
        max_versoes: int = 10,
    ):
        self.raiz = Path(raiz)
        self.processador = processador          # pipeline F4.2/F4.3 (opcional)
        self.baixar_url = baixar_url or _baixar_url_http
        self.max_versoes = max_versoes

    # --- caminhos --------------------------------------------------------------

    def pasta(self, produto_id: int) -> Path:
        return self.raiz / str(produto_id)

    def caminho_atual(self, produto_id: int) -> Path:
        return self.pasta(produto_id) / "atual.png"

    def caminho_relativo(self, produto_id: int) -> str:
        """Caminho a guardar no banco (relativo à biblioteca — portável)."""
        return f"{produto_id}/atual.png"

    def _dir_versoes(self, produto_id: int) -> Path:
        return self.pasta(produto_id) / "versoes"

    def listar_versoes(self, produto_id: int) -> list[Path]:
        vdir = self._dir_versoes(produto_id)
        return sorted(vdir.glob("*.png")) if vdir.exists() else []

    # --- ingestão --------------------------------------------------------------

    def _carregar_fonte(self, fonte: Fonte) -> Image.Image:
        if isinstance(fonte, (bytes, bytearray)):
            return Image.open(io.BytesIO(bytes(fonte)))
        s = str(fonte)
        if s.startswith(("http://", "https://")):
            return Image.open(io.BytesIO(self.baixar_url(s)))
        return Image.open(fonte)

    def ingerir(self, produto_id: int, fonte: Fonte) -> Path:
        """Recebe a imagem, processa (se houver processador) e a torna a 'atual'.

        Se já existia uma 'atual', ela é arquivada em versoes/ antes.
        """
        img = self._carregar_fonte(fonte).convert("RGBA")
        if self.processador is not None:
            img = self.processador(img)

        self.pasta(produto_id).mkdir(parents=True, exist_ok=True)
        atual = self.caminho_atual(produto_id)
        if atual.exists():
            self._arquivar(produto_id, atual)
        img.save(atual, "PNG")
        return atual

    def _arquivar(self, produto_id: int, atual: Path) -> None:
        vdir = self._dir_versoes(produto_id)
        vdir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        destino = vdir / f"{ts}.png"
        contador = 1
        while destino.exists():
            destino = vdir / f"{ts}_{contador}.png"
            contador += 1
        shutil.move(str(atual), str(destino))
        self._podar(produto_id)

    def _podar(self, produto_id: int) -> None:
        versoes = self.listar_versoes(produto_id)
        for v in versoes[: max(0, len(versoes) - self.max_versoes)]:
            v.unlink()
