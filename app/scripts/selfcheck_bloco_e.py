"""
Self-check do Bloco E — artefatos de demonstração por etapa (gate)
==================================================================
Reproduzível: ``python -m app.scripts.selfcheck_bloco_e``. Gera exports em
``saida_selfcheck_e/`` e confere POR CONTEÚDO no console — o arquiteto
verifica por conta própria, sem depender do relato do builder.

  [B] override por slot rendendo só na célula dele (PNG);
  [C] multi-imagem em leque e lado a lado (PNGs, ordem por pixel);
  [D] composto "Camil e Rei" (PNG) + separar devolvendo os originais;
  [E] PDF RGB intocado (hash) + PDF CMYK convertido e medido.

Usa grade sintética com fotos de cor única (a mesma do adversarial — o
conteúdo entrega qualquer troca) e o Ghostscript real do ambiente.
"""

from __future__ import annotations

import hashlib
import shutil
import sys
from decimal import Decimal
from pathlib import Path

SAIDA = Path("saida_selfcheck_e")


def _ok(msg: str) -> None:
    print(f"  OK  {msg}")


def _falha(msg: str) -> None:
    print(f"  FALHOU  {msg}")
    sys.exit(1)


def _pix(img, layout, slot, fx, fy):
    from app.rendering.model import TipoRegiao
    from app.rendering.units import mm_para_px
    reg = next(r for r in slot.regioes if r.tipo == TipoRegiao.IMAGEM)
    cx = mm_para_px(reg.rect.x_mm + reg.rect.larg_mm * fx, layout.dpi)
    cy = mm_para_px(reg.rect.y_mm + reg.rect.alt_mm * fy, layout.dpi)
    return img.getpixel((round(cx), round(cy)))[:3]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    SAIDA.mkdir(parents=True)

    from PIL import Image
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])

    # grade sintética + itens coloridos (reusa o arsenal do adversarial)
    from app.qt.telas import servico
    from app.rendering.arranjo import ModoArranjo
    from app.rendering.compositor import DadosProduto, ImagemSlot, compor_pagina
    from app.rendering.export import exportar_pdf_multipagina, exportar_png
    from app.tests.test_adversarial_vinculo import _grade_4, _itens

    print("Self-check do Bloco E — artefatos por etapa em", SAIDA)
    layout = _grade_4()
    itens = _itens(SAIDA)[:4]
    slots = layout.paginas[0].slots
    mapa = {s.id: it.uid for s, it in zip(slots, itens)}
    por_uid = {it.uid: it for it in itens}

    def _dados(overrides=None):
        d = {}
        for sid, u in mapa.items():
            it = por_uid[u]
            base = DadosProduto(it.nome, preco_por=Decimal("1"),
                                imagem_path=it.imagem)
            ov = (overrides or {}).get(sid)
            d[sid] = servico.aplicar_override(base, ov) if ov else base
        return d

    # [B] override numa célula — a foto forçada rende SÓ nela
    print("\n[B] Override por slot")
    foto_ov = SAIDA / "override.png"
    Image.new("RGB", (200, 200), "#654321").save(foto_ov)
    ov = {slots[1].id: {"nome": "Oferta da Célula", "preco": "9,99",
                        "imagem": str(foto_ov)}}
    img = compor_pagina(layout, layout.paginas[0], _dados(ov))
    exportar_png(img, SAIDA / "etapaB_override.png", layout.dpi)
    if _pix(img, layout, slots[1], .5, .5) != (0x65, 0x43, 0x21):
        _falha("o override não rendeu na célula dele")
    if _pix(img, layout, slots[0], .5, .5) != (255, 0, 0):
        _falha("o override vazou para a célula vizinha!")
    _ok("etapaB_override.png — override só na célula dele, vizinha intacta")

    # [C] multi-imagem: leque e lado a lado, ordem por pixel
    print("\n[C] Multi-imagem (sabores)")
    fotos = []
    for i, cor in enumerate(["#FF0000", "#00FF00", "#0000FF"]):
        f = SAIDA / f"sabor_{i}.png"
        Image.new("RGB", (200, 200), cor).save(f)
        fotos.append(str(f))
    d = _dados()
    d[slots[0].id] = DadosProduto("Multi Sabores", preco_por=Decimal("1"),
                                  imagens=[ImagemSlot(c) for c in fotos],
                                  modo_arranjo=ModoArranjo.LADO_A_LADO)
    img = compor_pagina(layout, layout.paginas[0], d)
    exportar_png(img, SAIDA / "etapaC_lado_a_lado.png", layout.dpi)
    esperadas = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    for i in range(3):
        if _pix(img, layout, slots[0], (i + .5) / 3, .5) != esperadas[i]:
            _falha(f"lado a lado: o terço {i} não é a foto {i} da lista")
    d[slots[0].id] = DadosProduto("Multi Sabores", preco_por=Decimal("1"),
                                  imagens=[ImagemSlot(c) for c in fotos],
                                  modo_arranjo=ModoArranjo.LEQUE)
    exportar_png(compor_pagina(layout, layout.paginas[0], d),
                 SAIDA / "etapaC_leque.png", layout.dpi)
    _ok("etapaC_lado_a_lado.png (ordem por pixel) + etapaC_leque.png")

    # [D] composto "Camil e Rei": compor por pixel + separar devolvendo tudo
    print("\n[D] Item composto (Camil e Rei)")
    a, b = itens[0], itens[1]
    a.nome, b.nome = "Arroz Camil 5kg", "Arroz Rei 5kg"
    comp = servico.compor_itens(a, b, preco="39,90")
    print(f"      nome montado: “{comp.nome}” · preço único {comp.preco}")
    d = _dados()
    d[slots[0].id] = DadosProduto(
        comp.nome, preco_por=servico.preco_decimal(comp.preco),
        imagens=[ImagemSlot(c) for c in comp.imagens],
        modo_arranjo=ModoArranjo.LADO_A_LADO)
    img = compor_pagina(layout, layout.paginas[0], d)
    exportar_png(img, SAIDA / "etapaD_composto.png", layout.dpi)
    if _pix(img, layout, slots[0], .25, .5) != (255, 0, 0) or \
            _pix(img, layout, slots[0], .75, .5) != (0, 255, 0):
        _falha("composto: Camil não está à esquerda / Rei à direita")
    v_a, v_b = servico.separar_item(comp)
    if (v_a.uid, v_b.uid) != (a.uid, b.uid) or v_a.to_dict() != a.to_dict():
        _falha("separar não devolveu exatamente os originais")
    _ok(f"etapaD_composto.png — “{comp.nome}”, separar devolve os originais")

    # [E] CMYK opcional: RGB intocado por hash; convertido medido
    print("\n[E] CMYK opcional (Ghostscript real)")
    from app.rendering import cmyk
    from app.rendering.cartaz import layout_cartaz_exemplo
    from pypdf import PdfReader
    lay = layout_cartaz_exemplo()
    dados_c = DadosProduto("Cartaz CMYK", preco_de=Decimal("4.99"),
                           preco_por=Decimal("3.99"))
    pags = [compor_pagina(lay, lay.paginas[0], dados_c)]
    rgb = exportar_pdf_multipagina(pags, SAIDA / "etapaE_rgb.pdf", lay.dpi)
    hash_rgb = hashlib.sha256(rgb.read_bytes()).hexdigest()
    convertido = SAIDA / "etapaE_cmyk.pdf"
    shutil.copy(rgb, convertido)
    if cmyk.ghostscript_disponivel() is None:
        _falha("Ghostscript não encontrado no ambiente")
    cmyk.converter_pdf_cmyk(convertido)
    if hashlib.sha256(rgb.read_bytes()).hexdigest() != hash_rgb:
        _falha("o PDF RGB foi tocado!")
    if b"/DeviceCMYK" not in convertido.read_bytes():
        _falha("o convertido não tem /DeviceCMYK")
    pg = PdfReader(str(convertido)).pages[0]
    w_mm = float(pg.mediabox.width) / 72 * 25.4
    h_mm = float(pg.mediabox.height) / 72 * 25.4
    if abs(w_mm - 100) > 0.6 or abs(h_mm - 150) > 0.6:
        _falha(f"tamanho mudou na conversão: {w_mm:.2f}×{h_mm:.2f}")
    _ok(f"etapaE_rgb.pdf intocado (sha256 {hash_rgb[:12]}…) · "
        f"etapaE_cmyk.pdf /DeviceCMYK, {w_mm:.2f}×{h_mm:.2f} mm")

    print("\nSELF-CHECK DO BLOCO E COMPLETO: artefatos prontos para o arquiteto.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
