"""F13-QUATER/A6 — o MEDIDOR DE FIDELIDADE do Quintou.

Três rodadas reprovadas por "está feio" não escalam — a régua vira
NÚMERO. O Quintou é o único encarte com um PUBLICADO real: este script
compõe a página do app com exatamente os produtos e preços do
publicado de 16/07 (a spec da inspeção), alinha em 1080×1300 e reporta
o % de pixels diferentes GLOBAL e POR CÉLULA, com mapa de calor.

O número nunca vai a zero (as fotos do acervo não são as do publicado)
— mas cada rodada ele CAI, e o mapa diz ONDE trabalhar. Meta da ordem:
< 12% global, nenhuma célula acima de 25%.

Uso:
    python -m app.scripts.medidor_quintou "Templates novos"

Saída: ``saida_f13/medidor_quintou.md`` (os números) +
``medidor_quintou_mapa_p1.png``/``_p2.png`` (real | app | mapa de calor).
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parents[2]

LIMIAR = 40                     # |Δ| máximo por canal para "igual"

# as zonas nomeadas (px 1×): 15/16 células + painel + validade
_CELULAS_P1 = {
    f"pos-{p:02d}": (((p - 1) % 4) * 270, 270 + ((p - 1) // 4) * 258,
                     270, 258)
    for p in range(1, 17) if p != 13
}
_CELULAS_P2 = {
    f"vpos-{p:02d}": (((p - 1) % 4) * 270, 270 + ((p - 1) // 4) * 258,
                      270, 258)
    for p in range(1, 17)
}
_ZONAS_P1 = dict(_CELULAS_P1, painel=(588, 18, 468, 226),
                 validade=(213, 1044, 57, 256))
_ZONAS_P2 = dict(_CELULAS_P2)


def _compor_paginas(pacote: Path):
    """Compõe frente e verso com os dados EXATOS do publicado (a spec
    da inspeção é a fonte única — Q4 já a alinhou ao publicado)."""
    from app.qt.telas.servico import preco_decimal
    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.model import PapelTexto, TipoRegiao
    from app.scripts.inspecao_encartes import DADOS, layout_do_banco

    spec = DADOS["quintou"]
    # QUINQUE/A1 (L10): o medidor também mede o que vem do BANCO pela
    # porta do botão — a fidelidade medida é a do PRODUTO
    lay, _lid = layout_do_banco("quintou", pacote)
    dados = {}
    for sid, item in spec["itens"].items():
        nome, descr, preco, foto = item[:4]
        dados[sid] = DadosProduto(
            nome, descritor=descr, unidade=descr,
            preco_por=preco_decimal(preco) if preco else None,
            imagem_path=foto)
    paginas = []
    for n_pag, pag in enumerate(lay.paginas, start=1):
        validade = spec["validade"]
        if n_pag == 2 and spec.get("validade_p2"):
            validade = spec["validade_p2"]
        for s in pag.slots:
            for r in s.regioes:
                if (r.tipo == TipoRegiao.TEXTO_LEGAL
                        and r.papel_texto == PapelTexto.VALIDADE):
                    r.texto_fixo = validade
        paginas.append(compor_pagina(lay, pag, dados))
    return paginas


def medir(pacote: str | Path) -> dict:
    import numpy as np
    from PIL import Image

    pacote = Path(pacote)
    reais = [Image.open(pacote / "Quintou" / "Quintou Frente Real.png"),
             Image.open(pacote / "Quintou" / "Quintou Verso Real.png")]
    paginas = _compor_paginas(pacote)
    saida = RAIZ_REPO / "saida_f13"
    saida.mkdir(exist_ok=True)

    relatorio: dict = {"paginas": []}
    for n, (app_img, real_img, zonas) in enumerate(
            zip(paginas, reais, (_ZONAS_P1, _ZONAS_P2)), start=1):
        app_1x = np.asarray(
            app_img.resize((1080, 1300), Image.LANCZOS).convert("RGB"),
            dtype=int)
        real = np.asarray(
            real_img.resize((1080, 1300), Image.LANCZOS).convert("RGB"),
            dtype=int)
        dif = np.abs(app_1x - real).max(axis=2)
        difere = dif > LIMIAR
        global_pct = float(difere.mean()) * 100

        # a métrica do que o APP CONTROLA: fora dos miolos de FOTO
        # (as fotos do acervo nunca são as do publicado — é o piso
        # declarado da ordem; o resto tem de convergir)
        mask_foto = np.zeros(difere.shape, dtype=bool)
        for nome, (zx, zy, _zw, _zh) in zonas.items():
            if nome.startswith(("pos-", "vpos-")):
                mask_foto[zy + 2:zy + 192, zx + 8:zx + 262] = True
        sem_fotos = float(difere[~mask_foto].mean()) * 100

        por_zona = {}
        for nome, (zx, zy, zw, zh) in zonas.items():
            rec = difere[zy:zy + zh, zx:zx + zw]
            por_zona[nome] = float(rec.mean()) * 100

        # mapa de calor: real | app | diff (vermelho = diferente)
        calor = np.zeros((1300, 1080, 3), dtype=np.uint8)
        calor[..., 0] = np.clip(dif * 2, 0, 255)
        painel = Image.new("RGB", (1080 * 3 + 16, 1300), "#444444")
        painel.paste(Image.fromarray(real.astype(np.uint8)), (0, 0))
        painel.paste(Image.fromarray(app_1x.astype(np.uint8)), (1088, 0))
        painel.paste(Image.fromarray(calor), (2176, 0))
        painel.save(saida / f"medidor_quintou_mapa_p{n}.png")
        relatorio["paginas"].append(
            {"pagina": n, "global": global_pct,
             "sem_fotos": sem_fotos, "zonas": por_zona})

    linhas = ["# Medidor de fidelidade do Quintou (QUATER/A6)", "",
              f"Limiar por canal: |Δ| > {LIMIAR}. Meta: < 12% global, "
              "nenhuma célula > 25%.", ""]
    for pag in relatorio["paginas"]:
        n = pag["pagina"]
        linhas.append(f"## Página {n} ({'frente' if n == 1 else 'verso'})"
                      f" — GLOBAL: {pag['global']:.1f}% · fora das "
                      f"fotos: {pag['sem_fotos']:.1f}%")
        linhas.append("")
        linhas.append("| zona | % diferente |")
        linhas.append("|---|---|")
        for nome, pct in sorted(pag["zonas"].items(),
                                key=lambda kv: -kv[1]):
            marca = " ⚠" if pct > 25 else ""
            linhas.append(f"| {nome} | {pct:.1f}%{marca} |")
        linhas.append("")
    (saida / "medidor_quintou.md").write_text(
        "\n".join(linhas), encoding="utf-8")
    return relatorio


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    sys.stdout.reconfigure(encoding="utf-8")
    r = medir(sys.argv[1])
    for pag in r["paginas"]:
        pior = max(pag["zonas"].items(), key=lambda kv: kv[1])
        print(f"p{pag['pagina']}: global {pag['global']:.1f}% · fora "
              f"das fotos {pag['sem_fotos']:.1f}% · pior zona "
              f"{pior[0]} = {pior[1]:.1f}%")
