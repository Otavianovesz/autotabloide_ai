"""Acervo do dono na bancada (ORDEM_F13_RESGATE · Bloco A · A5).

A prova da arte real dependia do CWD (``Path("arte/quintou")`` relativo)
e ``arte/`` está no ``.gitignore`` — rodar o pytest de outra pasta, ou
num clone, calava os testes SEM AVISO (T-08; §1.5 da varredura: 10
vermelhos + 8 pulados + 205 testes degradando para a fonte embutida do
Pillow em silêncio, com métricas diferentes e o teste de pixel mudando
de significado).

A lei nova, decidida na F13:
* caminho de acervo SEMPRE ancorado na RAIZ DO REPOSITÓRIO (imune ao
  CWD do pytest);
* acervo ausente vira skip EXPLÍCITO com o prefixo ``REQUER ACERVO DO
  DONO`` — o conftest CONTA esses skips e estampa o aviso no fim do
  relatório. Skip silencioso não é verde.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

REQUER = "REQUER ACERVO DO DONO"

# app/tests/acervo.py → parents[2] = raiz do repositório
RAIZ_REPO = Path(__file__).resolve().parents[2]
ARTE_QUINTOU = RAIZ_REPO / "arte" / "quintou"
ARTE_BELO_BRASIL = RAIZ_REPO / "Frente Template.png"
FONTES_REAIS = RAIZ_REPO / "AutoTabloide_System_Root" / "fontes"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

requer_arte_quintou = pytest.mark.skipif(
    not (ARTE_QUINTOU / "frente_template.png").exists(),
    reason=f"{REQUER}: arte/quintou/frente_template.png "
           "(a arte real do Quintou não viaja no git)")

requer_arte_belo_brasil = pytest.mark.skipif(
    not ARTE_BELO_BRASIL.exists(),
    reason=f"{REQUER}: 'Frente Template.png' na raiz do repositório "
           "(a arte real do Belo Brasil não viaja no git)")


def foto_de_bancada(caminho, cor=(200, 40, 40), lado: int = 600):
    """F13/D10: a foto sintética de teste tem de ser NÍTIDA e ≥500px —
    cor chapada tem Laplaciano zero e o avaliador (agora no pré-voo,
    CORRETO) a marca 'borrada/pequena — RUIM'. Xadrez determinístico nas
    BORDAS (a nitidez); o MIOLO (terço central) fica de cor PURA — os
    testes de pixel amostram o centro da célula."""
    from PIL import Image
    img = Image.new("RGB", (lado, lado), cor)
    branco = Image.new("RGB", (16, 16), (255, 255, 255))
    m0, m1 = lado // 3, 2 * lado // 3
    for x in range(0, lado, 32):
        for y in range(0, lado, 32):
            if m0 <= x < m1 and m0 <= y < m1:
                continue                     # o miolo puro fica intacto
            img.paste(branco, (x, y))
    img.save(caminho)
    return str(caminho)


def copiar_fontes_reais(destino: Path | str) -> int:
    """Copia as fontes reais do acervo para a pasta de fontes da raiz de
    teste. SEM elas o teste NÃO segue: ``text_fit`` cairia na fonte
    embutida do Pillow (métricas completamente diferentes) e o teste de
    pixel mudaria de significado em silêncio (§1.5 da varredura).
    Devolve o nº de fontes copiadas."""
    fontes = sorted(FONTES_REAIS.glob("*.ttf")) if FONTES_REAIS.exists() else []
    if not fontes:
        pytest.skip(f"{REQUER}: fontes reais em AutoTabloide_System_Root/fontes")
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    for f in fontes:
        shutil.copy(f, destino / f.name)
    return len(fontes)
