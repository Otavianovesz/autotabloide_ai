"""
Template compartilhável — .attpl (FASE 12, Bloco B — R-149)
===========================================================
Um presente para outro mercado: a ESTRUTURA do layout (células, regiões,
estilos), JAMAIS os dados do dono. A limpeza é ATIVA e testada por AUSÊNCIA:
arte de fundo fora, textos fixos fora, overrides fora, caminhos fora —
sobra a geometria e o estilo (I3 + privacidade, passo 25).
"""

from __future__ import annotations

import json
from pathlib import Path

FORMATO = "attpl"
VERSAO_FORMATO = 1

# campos de Regiao que NUNCA viajam (conteúdo/vínculo do dono)
_CAMPOS_PRIVADOS_REGIAO = {"texto_fixo", "uid", "ref_mestre", "overrides"}


def _limpar_regiao(d: dict) -> dict:
    limpo = {k: v for k, v in d.items() if k not in _CAMPOS_PRIVADOS_REGIAO}
    return limpo


def exportar_template(layout_def, destino: str | Path,
                      nome: str = "Layout compartilhado") -> Path:
    """Grava o .attpl: o LayoutDef SEM arte, sem textos, sem vínculos —
    só a estrutura (células/regiões/estilos)."""
    bruto = layout_def.to_dict()
    bruto.pop("arquivo_fundo", None)
    for pag in bruto.get("paginas", []):
        pag.pop("arquivo_fundo", None)
        for slot in pag.get("slots", []):
            slot["regioes"] = [_limpar_regiao(r)
                               for r in slot.get("regioes", [])]
    pacote = {"formato": FORMATO, "versao": VERSAO_FORMATO,
              "nome": nome, "layout": bruto}
    destino = Path(destino)
    if destino.suffix.lower() != ".attpl":
        destino = destino.with_suffix(".attpl")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(pacote, ensure_ascii=False, indent=2),
                       encoding="utf-8")
    return destino


def importar_template(arquivo: str | Path):
    """Lê o .attpl e devolve o LayoutDef pronto para o editor (uids
    NOVOS nascem no from_dict/uso — nada colide com o que o outro
    mercado tinha, I1). Levanta ValueError em arquivo inválido."""
    from app.rendering.model import LayoutDef
    dados = json.loads(Path(arquivo).read_text(encoding="utf-8"))
    if dados.get("formato") != FORMATO:
        raise ValueError("Este arquivo não é um template .attpl.")
    return LayoutDef.from_dict(dados["layout"])


def vazamentos_no_template(arquivo: str | Path,
                           termos_do_dono: list[str]) -> list[str]:
    """A varredura por AUSÊNCIA (passo 25/32): devolve os termos do dono
    (nomes de produto, preços, caminhos) encontrados no arquivo — a lista
    DEVE ser vazia. É a prova, não a fé."""
    texto = Path(arquivo).read_text(encoding="utf-8").lower()
    return [t for t in termos_do_dono if t and t.lower() in texto]
