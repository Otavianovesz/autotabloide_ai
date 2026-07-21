"""
Busca de imagem de produto (F4.1) — headless
=============================================
A partir do ``nome_sanitizado`` de um produto, busca candidatos de imagem no
**DuckDuckGo** (via ``ddgs``), baixa para uma pasta de trabalho, e devolve os
candidatos já com dimensões, sem duplicatas e acima de uma resolução mínima.

Por que DuckDuckGo (``ddgs``) e não o ``icrawler`` (Bing/Google): o icrawler é um
scraper antigo cujos parsers quebram quando os buscadores mudam o HTML — na
prática ele passou a devolver **lixo** (imagens sem relação com o produto). O
``ddgs`` é mantido, grátis, sem chave, e traz resultados relevantes.

Duas coisas fazem a imagem certa aparecer:
1. **Nome enriquecido** (a IA conserta "De Sodorante" → "Desodorante").
2. **Sem peso/unidade** na busca ("Óleo de Soja Liza", não "...900ml") — o peso
   polui a busca de imagem. Ver :func:`remover_peso`.

O "baixador" é injetável: em produção usa o DuckDuckGo; nos testes, um fake local
(sem rede). Assim o pós-processamento (dedup, filtro, dimensões) é testável.

Bloqueio/rede: se o baixador não trouxer nada, sinalizamos ``bloqueado=True`` e
seguimos sem quebrar.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from PIL import Image

_log = logging.getLogger(__name__)

# User-Agent de navegador: alguns servidores de imagem recusam o padrão do requests.
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


@dataclass
class CandidatoImagem:
    caminho: Path
    largura: int
    altura: int
    hash_md5: str


@dataclass
class ResultadoBusca:
    query: str
    candidatos: list[CandidatoImagem] = field(default_factory=list)
    bloqueado: bool = False


class Baixador(Protocol):
    def baixar(self, query: str, n: int, destino: Path) -> list[Path]: ...


class BaixadorWeb:
    """Baixa imagens via DuckDuckGo (``ddgs``).

    Pede as URLs ao DuckDuckGo (região Brasil por padrão), descarta as pequenas
    demais pelas dimensões que o próprio buscador informa (``min_lado_hint`` —
    evita baixar miniatura), e baixa cada uma com timeout. Degrada sem quebrar:
    sem rede / sem resultado → lista vazia.

    Rate-limit do DuckDuckGo (lição da rodada dos 15): muitas buscas seguidas
    penduram/estouram. Defesas: **timeout na própria chamada do DDGS**, **pausa
    mínima entre buscas** e **retry com backoff**; se tudo falhar, devolve vazio
    (o item fica sem foto — degrada, não trava o lote).
    """

    def __init__(
        self,
        *,
        regiao: str = "br-br",
        min_lado_hint: int = 0,
        timeout: float = 10.0,
        pausa_entre_buscas: float = 1.5,
        tentativas: int = 3,
    ):
        self.regiao = regiao
        self.min_lado_hint = min_lado_hint
        self.timeout = timeout
        self.pausa_entre_buscas = pausa_entre_buscas
        self.tentativas = tentativas
        self._ultima_busca = 0.0  # monotonic; respeita a pausa entre produtos

    def baixar(self, query: str, n: int, destino: Path) -> list[Path]:
        destino.mkdir(parents=True, exist_ok=True)
        # Pede folga: parte das URLs falha ao baixar (404, timeout, hotlink bloqueado).
        resultados = self._buscar(query, max(n * 2, n + 4))

        arquivos: list[Path] = []
        for i, r in enumerate(resultados):
            if len(arquivos) >= n:
                break
            url = r.get("image")
            if not url:
                continue
            # Pré-filtro barato: descarta miniatura pelas dimensões que o ddgs informa.
            if self.min_lado_hint:
                lado = min(int(r.get("width") or 0), int(r.get("height") or 0))
                if 0 < lado < self.min_lado_hint:
                    continue
            alvo = self._baixar_url(url, destino / f"{i:02d}")
            if alvo:
                arquivos.append(alvo)
        return arquivos

    def _buscar(self, query: str, n: int) -> list[dict]:
        try:
            from ddgs import DDGS
        except ImportError:  # dependência ausente — degrada sem quebrar
            _log.warning("ddgs não instalado; busca de imagem indisponível.")
            return []
        atraso = max(self.pausa_entre_buscas, 1.0)
        for tentativa in range(1, self.tentativas + 1):
            self._respeitar_pausa()
            try:
                with DDGS(timeout=self.timeout) as ddgs:
                    return list(
                        ddgs.images(
                            query,
                            region=self.regiao,
                            safesearch="moderate",
                            max_results=n,
                        )
                    )
            except Exception as exc:  # rate limit / rede / mudança de API
                _log.warning(
                    "busca ddgs falhou (tentativa %d/%d, %s): %s",
                    tentativa, self.tentativas, type(exc).__name__, exc,
                )
                if tentativa < self.tentativas:
                    time.sleep(atraso)
                    atraso *= 2  # backoff exponencial
        return []  # esgotou — pula o item, não trava o lote

    def _respeitar_pausa(self) -> None:
        """Garante a pausa mínima entre buscas (educação com o DuckDuckGo)."""
        espera = self.pausa_entre_buscas - (time.monotonic() - self._ultima_busca)
        if espera > 0:
            time.sleep(espera)
        self._ultima_busca = time.monotonic()

    def _baixar_url(self, url: str, base: Path) -> Path | None:
        import requests

        try:
            resp = requests.get(url, headers={"User-Agent": _UA}, timeout=self.timeout)
            resp.raise_for_status()
            ext = _extensao(resp.headers.get("Content-Type", ""), url)
            alvo = base.with_suffix(ext)
            alvo.write_bytes(resp.content)
            return alvo
        except Exception as exc:  # 404, timeout, hotlink bloqueado — pula
            _log.debug("download falhou %s: %s", url, exc)
            return None


def _extensao(content_type: str, url: str) -> str:
    ct = content_type.lower()
    for chave, ext in (("jpeg", ".jpg"), ("jpg", ".jpg"), ("png", ".png"),
                       ("webp", ".webp"), ("gif", ".gif")):
        if chave in ct:
            return ext
    m = re.search(r"\.(jpg|jpeg|png|webp|gif)\b", url.lower())
    return "." + (m.group(1).replace("jpeg", "jpg") if m else "jpg")


# Peso/unidade/embalagem: tudo que polui a busca de IMAGEM (o preço/gramatura
# importa no layout, não na busca). Ordem: alternativas longas antes das curtas.
_PESO_RE = re.compile(
    r"""\b(
        \d+\s?x\s?\d+(?:[.,]\d+)?\s?(?:ml|litros?|lt|l|kg|g|un)   # multipack 12x350ml
      | c/\s?\d+                                                   # c/12
      | \d+(?:[.,]\d+)?\s?(?:ml|litros?|lt|l|kg|gr|g|mg
            |unid(?:ade)?s?|und|un|cx|kit|pct|pcte|pacote
            |fardo|dz|d[uú]zia|rolos?|folhas?)
    )\b""",
    re.IGNORECASE | re.VERBOSE,
)


def remover_peso(nome: str) -> str:
    """Remove peso/unidade/embalagem do nome, para a busca de imagem.

    "Óleo de Soja Liza 900ml" → "Óleo de Soja Liza". Se sobrar vazio (nome só de
    peso, improvável), devolve o original.
    """
    limpo = re.sub(r"\s{2,}", " ", _PESO_RE.sub(" ", nome)).strip()
    return limpo or nome


def montar_query(nome_sanitizado: str, termos_reforco: tuple[str, ...]) -> str:
    """Monta a busca a partir do nome + termos de reforço (opcionais)."""
    return " ".join([nome_sanitizado, *termos_reforco]).strip()


def buscar_imagens(
    nome_sanitizado: str,
    baixador: Baixador,
    destino: str | Path,
    *,
    n: int = 8,
    min_lado: int = 400,
    termos_reforco: tuple[str, ...] = (),
    sem_peso: bool = True,
) -> ResultadoBusca:
    """Busca, baixa e filtra candidatos de imagem para um produto.

    ``sem_peso=True`` (padrão) remove peso/unidade do nome antes de buscar — é o
    que faz achar o produto certo. ``termos_reforco`` fica vazio por padrão.
    """
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    nome_busca = remover_peso(nome_sanitizado) if sem_peso else nome_sanitizado
    query = montar_query(nome_busca, termos_reforco)

    arquivos = baixador.baixar(query, n, destino)

    candidatos: list[CandidatoImagem] = []
    vistos: set[str] = set()
    for arq in arquivos:
        try:
            with Image.open(arq) as im:
                largura, altura = im.size
        except Exception:
            continue  # arquivo corrompido / não é imagem
        if min(largura, altura) < min_lado:
            continue  # resolução baixa demais
        md5 = hashlib.md5(arq.read_bytes()).hexdigest()
        if md5 in vistos:
            continue  # duplicata
        vistos.add(md5)
        candidatos.append(CandidatoImagem(arq, largura, altura, md5))

    return ResultadoBusca(query=query, candidatos=candidatos, bloqueado=not arquivos)
