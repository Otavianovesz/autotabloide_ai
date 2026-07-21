"""
Serviço de fontes (seletor livre) — F5.7 essencial adiantado
============================================================
O compositor Pillow carrega fonte por ARQUIVO (.ttf/.otf), enquanto o sistema
lista por NOME. Para não quebrar: o seletor trabalha com ARQUIVOS, e ao escolher
uma fonte do sistema, **copiamos o arquivo para `/fontes`** e guardamos o nome do
arquivo em `reg.fonte`. Assim sempre carrega e viaja junto no empacotamento (F7.4).
"""

from __future__ import annotations

import shutil
from functools import lru_cache
from pathlib import Path

from app.core.paths import SystemRoot

_DIRS_SISTEMA = [
    Path("C:/Windows/Fonts"),
    Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
]


def dir_fontes() -> Path:
    d = SystemRoot().fontes
    d.mkdir(parents=True, exist_ok=True)
    return d


def fontes_bundled() -> list[str]:
    """Arquivos de fonte já em /fontes (viajam com o projeto)."""
    return sorted({p.name for p in dir_fontes().glob("*.ttf")} | {p.name for p in dir_fontes().glob("*.otf")})


def _arquivos_sistema() -> list[Path]:
    arqs: list[Path] = []
    for d in _DIRS_SISTEMA:
        if d.exists():
            arqs += list(d.glob("*.ttf")) + list(d.glob("*.otf"))
    return sorted(arqs)


def _assinatura(arquivos: list[Path]) -> str:
    """Invalida o cache quando as pastas de fonte mudam.

    Hash de (nome, mtime) de CADA arquivo — trocar uma fonte por outra de
    mesmo total (zip com mtime antigo) invalida também; contagem+mtime-máx
    deixava esse falso-válido passar (achado da revisão da Onda 1).
    """
    import hashlib
    h = hashlib.sha256()
    for a in arquivos:
        try:
            h.update(f"{a.name}:{a.stat().st_mtime_ns}\n".encode())
        except OSError:
            h.update(f"{a.name}:?\n".encode())
    return h.hexdigest()


def _cache_path() -> Path:
    return SystemRoot().config / "fontes_cache.json"


@lru_cache(maxsize=1)
def _mapa_sistema() -> dict[str, Path]:
    """rótulo ('Família — arquivo') -> caminho, lido do name table (fontTools).

    RG-01: abrir ~3.300 fontes com fontTools custava ~1s NO BOOT. Agora:
    (a) o resultado é cacheado em disco (invalidado por contagem+mtime das
    pastas) — as aberturas seguintes leem um JSON em poucos ms; (b) quem
    chama decide QUANDO pagar a varredura (o painel adia para a primeira
    abertura do combo — fora do caminho crítico do boot).
    """
    import json

    arquivos = _arquivos_sistema()
    assinatura = _assinatura(arquivos)
    cache = _cache_path()
    try:                              # cache válido = zero abertura de fonte
        dados = json.loads(cache.read_text(encoding="utf-8"))
        if dados.get("assinatura") == assinatura:
            _detalhes_cache.clear()
            _detalhes_cache.update(dados.get("detalhes") or {})
            return {r: Path(c) for r, c in dados["mapa"].items()}
    except (OSError, ValueError, KeyError, TypeError):
        pass                          # sem cache/corrompido: varre e regrava

    try:
        from fontTools.ttLib import TTFont
    except Exception:
        return {}   # sem fontTools: só as fontes bundled

    mapa: dict[str, Path] = {}
    detalhes: dict[str, dict] = {}    # RG-14: família/estilo por rótulo
    for arq in arquivos:
        try:
            f = TTFont(str(arq), fontNumber=0, lazy=True)
            nm = f["name"]
            familia = nm.getDebugName(16) or nm.getDebugName(1) or arq.stem
            estilo = nm.getDebugName(17) or nm.getDebugName(2) or "Regular"
        except Exception:
            continue
        rotulo = f"{familia} — {arq.stem}"
        mapa[rotulo] = arq
        detalhes[rotulo] = {"familia": familia, "estilo": estilo}
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(
            {"assinatura": assinatura,
             "mapa": {r: str(c) for r, c in mapa.items()},
             "detalhes": detalhes},
            ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass                          # cache é conforto, nunca requisito
    _detalhes_cache.clear()
    _detalhes_cache.update(detalhes)
    return mapa


def rotulos_sistema() -> list[str]:
    return sorted(_mapa_sistema().keys())


def garantir_em_fontes(rotulo_sistema: str) -> str | None:
    """Copia a fonte de sistema para /fontes e devolve o nome do arquivo (ou None).

    Fonte desinstalada com o app aberto (mapa da sessão desatualizado) não
    pode estourar — devolve None em vez de FileNotFoundError engolido.
    """
    arq = _mapa_sistema().get(rotulo_sistema)
    if arq is None or not arq.exists():
        return None
    destino = dir_fontes() / arq.name
    if not destino.exists():
        shutil.copy2(arq, destino)
    return arq.name


# --- RG-14: pesos/variantes da família ("quero Black") ----------------------------

# rótulo do sistema → {"familia": ..., "estilo": ...} (populado com o mapa)
_detalhes_cache: dict[str, dict] = {}


@lru_cache(maxsize=512)
def _familia_estilo_de(caminho: str) -> tuple[str, str]:
    """(família, estilo) da name table de UM arquivo — ex.: ('Archivo', 'Black')."""
    from pathlib import Path as _P
    try:
        from fontTools.ttLib import TTFont
        f = TTFont(caminho, fontNumber=0, lazy=True)
        nm = f["name"]
        familia = nm.getDebugName(16) or nm.getDebugName(1) or _P(caminho).stem
        estilo = nm.getDebugName(17) or nm.getDebugName(2) or "Regular"
        return familia, estilo
    except Exception:
        return _P(caminho).stem, "Regular"


def familia_estilo(nome_arquivo: str) -> tuple[str, str]:
    """(família, estilo) de um arquivo que mora em /fontes."""
    return _familia_estilo_de(str(dir_fontes() / nome_arquivo))


def variantes_bundled(nome_arquivo: str) -> list[tuple[str, str]]:
    """[(estilo, arquivo)] das fontes de /fontes com a MESMA família.
    Barato (name table dos poucos arquivos locais, com cache)."""
    familia = familia_estilo(nome_arquivo)[0]
    pares = []
    for arq in fontes_bundled():
        f2, e2 = familia_estilo(arq)
        if f2 == familia:
            pares.append((e2, arq))
    return sorted(pares)


def variantes_sistema(nome_arquivo: str) -> list[tuple[str, str]]:
    """[(estilo, rótulo_sistema)] das variantes da família instaladas no
    sistema. PAGA a varredura das fontes na 1ª vez — chame fora do boot
    (ex.: na abertura do combo, como o seletor de fontes faz)."""
    familia = familia_estilo(nome_arquivo)[0]
    _mapa_sistema()                    # garante _detalhes_cache populado
    ja = {arq for _, arq in variantes_bundled(nome_arquivo)}
    pares = []
    for rotulo, det in _detalhes_cache.items():
        if det.get("familia") == familia:
            arq = _mapa_sistema().get(rotulo)
            if arq is not None and arq.name not in ja:
                pares.append((det.get("estilo", "Regular"), rotulo))
    return sorted(pares)
