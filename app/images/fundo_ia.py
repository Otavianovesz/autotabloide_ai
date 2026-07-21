"""
Gerador de artes de fundo por IA (FASE 12, Bloco B — R-147)
===========================================================
EXPERIMENTAL e condicionado à GPU — a MESMA disciplina do Estúdio degrau 2
(RG-46): sem GPU, desabilitado COM aviso honesto; o app nunca depende dele.
O fundo gerado é um PONTO DE PARTIDA editável — a arte do Illustrator segue
sendo o caminho principal do dono (passos 26-28).
"""

from __future__ import annotations

AVISO_SEM_GPU = ("O gerador de fundos precisa de uma placa de vídeo (GPU) "
                 "com CUDA, que este PC não tem. O app não depende dele — "
                 "a arte do Illustrator continua sendo o caminho principal.")


def gerador_fundo_disponivel() -> bool:
    """A MESMA sonda de GPU do Estúdio degrau 2 (uma régua só no app)."""
    try:
        from app.images.estudio import gerador_disponivel
        return gerador_disponivel() is not None
    except Exception:
        return False


def gerar_fundo(tema: str, largura_px: int, altura_px: int,
                *, motor=None):
    """Gera um fundo para a data/tema pedido. Devolve (Image|None, aviso).

    Sem GPU (ou sem motor) → (None, AVISO_SEM_GPU) — degrada com aviso,
    nunca trava (I2). Com GPU, o `motor` injetável (o SDXL local do Estúdio)
    recebe o prompt em PT-BR e devolve a imagem; qualquer falha vira aviso."""
    if motor is None and not gerador_fundo_disponivel():
        return None, AVISO_SEM_GPU
    try:
        if motor is not None:
            img = motor(tema, largura_px, altura_px)
        else:                            # [MÁQUINA DO DONO]: o SDXL real
            from app.images.estudio import gerador_disponivel
            pipe = gerador_disponivel()
            img = pipe(tema, largura_px, altura_px)
        if img is None:
            return None, ("O gerador não devolveu imagem — use uma arte "
                          "pronta ou tente outro tema.")
        return img, None
    except Exception as exc:
        return None, (f"O gerador falhou ({type(exc).__name__}) — o app "
                      "segue normal; use uma arte pronta.")
