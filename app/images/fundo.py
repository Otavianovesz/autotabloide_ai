"""
Remoção de fundo + recorte + normalização (F4.2) — headless
============================================================
Entrada: uma imagem candidata (da busca, F4.1). Saída: PNG com fundo
transparente, recortado no conteúdo e normalizado (centralizado num quadrado
com padding padrão) — pronto para compor no layout.

Modelo: rembg com **birefnet-general** (ótimo em bordas finas, rótulo, plástico).
O primeiro uso baixa o modelo (~1 GB, precisa de internet uma vez; depois offline).

Orientação e múltiplas imagens no slot ficam para a F4.5; aqui é imagem única.
A lógica de recorte/normalização é testável sem o rembg (com imagem sintética).
"""

from __future__ import annotations

import threading
from pathlib import Path

from PIL import Image

MODELO_PADRAO = "birefnet-general"     # decisão travada: qualidade máxima
# Escolhas didáticas p/ a Config 'imagem.modelo_rembg' (RG-02):
# a 1ª chamada de um modelo novo BAIXA o arquivo (precisa de internet 1×).
MODELOS = {
    "birefnet-general": "Qualidade máxima (lento — o padrão)",
    "birefnet-general-lite": "Equilibrado (~220 MB)",
    "u2netp": "Rápido (~4,5 MB — qualidade menor)",
}

_sessoes: dict[str, object] = {}
_trava_sessao = threading.Lock()


def _sessao(modelo: str):
    """Cacheia a sessão do rembg (carregar o modelo custa ~7 s, medido).

    Com trava: dois Trabalhadores simultâneos não podem disparar duas
    cargas de ~1 GB do mesmo modelo (RG-02).
    """
    with _trava_sessao:
        if modelo not in _sessoes:
            from rembg import new_session

            _sessoes[modelo] = new_session(modelo)
        return _sessoes[modelo]


def aquecer(modelo: str = MODELO_PADRAO) -> None:
    """Pré-carrega o modelo em segundo plano (RG-02): a 1ª foto da sessão
    deixa de pagar os ~7 s de carga. Falha em silêncio ABENÇOADO aqui —
    é só aquecimento; o uso real reporta o erro de verdade."""
    try:
        _sessao(modelo)
    except Exception:
        pass


def modelo_configurado() -> str:
    """O modelo escolhido na Config ('imagem.modelo_rembg'); default são."""
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio

        db = Database().init()
        try:
            with db.Session() as s:
                valor = str(ConfigRepositorio(s).get(
                    "imagem.modelo_rembg") or MODELO_PADRAO)
        finally:
            db.engine.dispose()
        return valor if valor in MODELOS else MODELO_PADRAO
    except Exception:
        return MODELO_PADRAO


def remover_fundo_img(img: Image.Image, modelo: str = "birefnet-general") -> Image.Image:
    """Remove o fundo de uma imagem já em memória (RGBA)."""
    from rembg import remove

    return remove(img.convert("RGBA"), session=_sessao(modelo)).convert("RGBA")


def remover_fundo(imagem: str | Path, modelo: str = "birefnet-general") -> Image.Image:
    """Remove o fundo e devolve a imagem RGBA (conteúdo recortado por transparência)."""
    return remover_fundo_img(Image.open(imagem), modelo)


def _pular_rembg_fundo_branco(imagem: str | Path) -> bool:
    """R-095: True se a Config `imagem.detector_fundo_branco` está ligada E a foto
    já tem fundo branco uniforme (os 4 cantos). Nunca levanta."""
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                ligado = ConfigRepositorio(s).get(
                    "imagem.detector_fundo_branco", False)
        finally:
            db.engine.dispose()
        if not ligado:
            return False
        from app.images.curadoria import tem_fundo_branco
        return tem_fundo_branco(Image.open(imagem))
    except Exception:
        return False


def recortar_conteudo(img: Image.Image) -> Image.Image:
    """Recorta na caixa do conteúdo (bbox do canal alfa). Transparente puro -> igual."""
    bbox = img.getchannel("A").getbbox()
    return img if bbox is None else img.crop(bbox)


def normalizar(img: Image.Image, lado: int = 1000, padding_frac: float = 0.06) -> Image.Image:
    """Centraliza o conteúdo num quadrado ``lado``×``lado`` com padding padrão."""
    disponivel = lado * (1 - 2 * padding_frac)
    escala = min(disponivel / img.width, disponivel / img.height)
    novo = img.resize((max(1, round(img.width * escala)), max(1, round(img.height * escala))))
    canvas = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    canvas.paste(novo, ((lado - novo.width) // 2, (lado - novo.height) // 2), novo)
    return canvas


def processar_imagem(
    imagem: str | Path,
    destino: str | Path,
    *,
    modelo: str = "birefnet-general",
    lado: int = 1000,
    padding_frac: float = 0.06,
) -> Path:
    """Pipeline completo: remove fundo -> recorta -> normaliza -> salva PNG.

    R-095: se o detector de fundo-branco estiver LIGADO (Config) e a foto já
    tiver fundo branco uniforme, PULA o rembg (economiza tempo e não estraga foto
    boa) — só normaliza."""
    if _pular_rembg_fundo_branco(imagem):
        sem_fundo = Image.open(imagem).convert("RGBA")
    else:
        sem_fundo = remover_fundo(imagem, modelo)
    normalizado = normalizar(recortar_conteudo(sem_fundo), lado, padding_frac)
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    normalizado.save(destino, "PNG")
    return destino
