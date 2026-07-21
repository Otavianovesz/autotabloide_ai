"""
O MARCO (FASE 12, Bloco D — RG-48/RG-58)
========================================
O padrão-ouro de regressão: as campanhas REAIS do dono em `arte/<campanha>/`
(cada uma com `frente_template.png` [+ `verso_template.png`] e as ofertas
transcritas em `ofertas_*.txt`). A descoberta é por PASTA — quando o dono
puser as artes do Sexta Verde e do Fim de Semana, o marco as pega SOZINHO;
até lá, as faltantes aparecem NOMEADAS no dossiê (I2 — nunca um skip mudo).
"""

from __future__ import annotations

import re
from pathlib import Path

# as três campanhas do padrão-ouro (passo 50) — nomes de pasta
CAMPANHAS_ESPERADAS = ("quintou", "sexta_verde", "fim_de_semana")


def campanhas_do_marco(raiz: str | Path = "arte"):
    """(disponíveis, faltantes): disponível = pasta com frente_template.png.
    Cada disponível: {"nome", "pasta", "frente", "verso"|None, "ofertas":
    [txt...], "validade"|None}."""
    raiz = Path(raiz)
    disponiveis: list[dict] = []
    nomes_achados: set[str] = set()
    if raiz.exists():
        for pasta in sorted(p for p in raiz.iterdir() if p.is_dir()):
            frente = pasta / "frente_template.png"
            if not frente.exists():
                continue
            verso = pasta / "verso_template.png"
            ofertas = sorted(pasta.glob("ofertas_*.txt"))
            disponiveis.append({
                "nome": pasta.name, "pasta": pasta, "frente": frente,
                "verso": verso if verso.exists() else None,
                "ofertas": ofertas,
                "validade": validade_das_ofertas(ofertas),
            })
            nomes_achados.add(pasta.name)
    faltantes = [n for n in CAMPANHAS_ESPERADAS if n not in nomes_achados]
    return disponiveis, faltantes


def validade_das_ofertas(arquivos_txt) -> str | None:
    """RG-58: a validade transcrita no cabeçalho dos txt ("validade da
    oferta: até 26/05") — o 'até' NUNCA fica vazio no marco; sem achar,
    devolve None e o chamador ACUSA (nunca inventa data)."""
    for txt in arquivos_txt or []:
        try:
            cabeca = Path(txt).read_text(encoding="utf-8")[:400]
        except OSError:
            continue
        m = re.search(r"validade[^:]*:\s*(at[eé]\s*\d{1,2}/\d{1,2})",
                      cabeca, re.IGNORECASE)
        if m:
            return m.group(1).strip().upper().replace("ATE", "ATÉ")
    return None


def itens_reais_da_campanha(campanha: dict) -> list[tuple[str, str | None]]:
    """As ofertas TRANSCRITAS da peça real, (nome, preço) — os dados do
    marco são os do dono, não sintéticos."""
    from app.scripts.importar_tabela import parse_tabela
    pares: list[tuple[str, str | None]] = []
    for txt in campanha.get("ofertas", []):
        pares.extend(parse_tabela(Path(txt)))
    return pares
