"""O MARCO da FASE 12 — executável (RG-48/RG-58, passos 51-54, 65, 89).

Roda o fluxo REAL de ponta a ponta e ARQUIVA as provas em `saida_marco/`:
acervo de 5.000 produtos → as ofertas TRANSCRITAS das campanhas reais em
`arte/<campanha>/` → conciliação (com a IA local se ligada) → composição
sobre o layout REAL detectado da arte (frente+verso) → PDF medido em
mm/bytes → medições de tempo → `DOSSIE_MARCO.md` (o material da sessão de
aceitação do dono). Campanha esperada sem arte no disco é NOMEADA no dossiê
(I2) — nunca um pulo mudo.

Rodar::

    python -m app.scripts.selfcheck_marco_f12
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

SAIDA = Path("saida_marco")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])

    import shutil

    from PIL import Image

    from app.core.database import Database
    from app.core.marco import campanhas_do_marco, itens_reais_da_campanha
    from app.core.models import Produto
    from app.core.paths import SystemRoot

    tmp = Path(tempfile.mkdtemp(prefix="marco_f12_"))
    os.environ["AUTOTABLOIDE_ROOT"] = str(tmp / "raiz")
    root = SystemRoot(tmp / "raiz").criar_estrutura()
    reais = Path("AutoTabloide_System_Root/fontes")
    if reais.exists():
        for f in reais.glob("*.ttf"):
            shutil.copy(f, root.fontes / f.name)
    SAIDA.mkdir(exist_ok=True)

    medicoes: dict = {"quando": datetime.now().strftime("%d/%m/%Y %H:%M"),
                      "acervo": 5000, "campanhas": {}}

    # --- o acervo de 5.000 (passo 52) ---------------------------------------
    print("Semeando o acervo de 5.000 produtos…")
    t0 = time.monotonic()
    db = Database().init()
    with db.Session() as s:
        s.add_all([Produto(nome_bruto=f"PRODUTO ACERVO {i}",
                           nome_sanitizado=f"Produto Acervo {i}",
                           marca=f"Marca{i % 60}") for i in range(5000)])
        s.commit()
    db.engine.dispose()
    medicoes["semear_5k_s"] = round(time.monotonic() - t0, 2)

    from app.qt.telas import servico
    t0 = time.monotonic()
    servico.listar_catalogo(offset=0, limite=50)
    medicoes["abrir_catalogo_s"] = round(time.monotonic() - t0, 3)

    disponiveis, faltantes = campanhas_do_marco()
    medicoes["campanhas_faltantes"] = faltantes

    from app.qt.telas.servico import ItemMesa
    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.export import exportar_pdf_multipagina, exportar_png
    from app.rendering.grade import (
        adicionar_pagina_de_arte, layout_grade_de_arte, ocupaveis,
        ordenar_slots_visualmente)
    from app.rendering.model import (
        PapelTexto, Regiao, Retangulo, Slot)
    from app.rendering.model import TipoRegiao as TR
    from pypdf import PdfReader

    for camp in disponiveis:
        nome = camp["nome"]
        print(f"\n=== Campanha {nome} ===")
        m: dict = {}
        reais_itens = itens_reais_da_campanha(camp)
        m["itens_reais"] = len(reais_itens)
        m["validade"] = camp["validade"]

        # conciliar as ofertas REAIS contra o acervo de 5k (medido)
        t0 = time.monotonic()
        res = servico.conciliar_linhas(
            [(n, p, None) for n, p in reais_itens], lambda _msg: None)
        m["conciliar_s"] = round(time.monotonic() - t0, 1)
        m["semaforo"] = {
            "verdes": sum(1 for i in res.itens if i.semaforo == "VERDE"),
            "amarelos": sum(1 for i in res.itens if i.semaforo == "AMARELO"),
            "vermelhos": sum(1 for i in res.itens
                             if i.semaforo == "VERMELHO")}
        print(f"  conciliar {len(reais_itens)} em 5k: {m['conciliar_s']}s "
              f"→ {m['semaforo']}")

        # o layout REAL da arte (frente+verso) — RG-48
        t0 = time.monotonic()
        layout, _det = layout_grade_de_arte(str(camp["frente"]))
        if camp["verso"]:
            adicionar_pagina_de_arte(layout, str(camp["verso"]))
        m["detectar_s"] = round(time.monotonic() - t0, 2)
        # RG-58: a validade da PEÇA — nunca vazia
        if camp["validade"]:
            reg_val = Regiao(TR.TEXTO_LEGAL, Retangulo(4, 2, 90, 6),
                             nome="Validade")
            reg_val.papel_texto = PapelTexto.VALIDADE
            reg_val.texto_fixo = "OFERTA VÁLIDA " + camp["validade"]
            layout.paginas[0].slots.append(Slot(f"validade_{nome}",
                                                [reg_val]))
        else:
            print("  [AVISO RG-58] a campanha não tem validade transcrita!")

        itens = []
        for i, (n, p) in enumerate(reais_itens):
            foto = tmp / f"{nome}_{i}.png"
            Image.new("RGB", (200, 200),
                      ((i * 53) % 256, (i * 97) % 256, (i * 31) % 256)
                      ).save(foto)
            itens.append(ItemMesa(n.upper(), p, "VERDE", n,
                                  imagem=str(foto)))
        slots = []
        for pag in layout.paginas:
            slots.extend(ocupaveis(ordenar_slots_visualmente(pag.slots)))
        mapa = {s.id: it.uid for s, it in zip(slots, itens)}
        por_uid = {it.uid: it for it in itens}
        dados = {sid: DadosProduto(
            por_uid[u].nome, preco_por=servico.preco_decimal(por_uid[u].preco),
            imagem_path=por_uid[u].imagem) for sid, u in mapa.items()}
        m["celulas_ocupadas"] = len(mapa)
        m["avisos_pre_voo"] = servico.validar_composicao(layout, dados)

        t0 = time.monotonic()
        imgs = [compor_pagina(layout, pag, dados) for pag in layout.paginas]
        m["compor_s"] = round(time.monotonic() - t0, 2)
        for np_, img in enumerate(imgs, 1):
            exportar_png(img, SAIDA / f"{nome}_p{np_}.png", layout.dpi)
        t0 = time.monotonic()
        pdf = exportar_pdf_multipagina(imgs, SAIDA / f"{nome}.pdf",
                                       layout.dpi)
        m["exportar_pdf_s"] = round(time.monotonic() - t0, 2)
        leitor = PdfReader(str(pdf))
        m["pdf"] = {
            "paginas": len(leitor.pages),
            "largura_mm": round(float(leitor.pages[0].mediabox.width)
                                * 25.4 / 72, 1),
            "altura_mm": round(float(leitor.pages[0].mediabox.height)
                               * 25.4 / 72, 1),
            "bytes": Path(pdf).stat().st_size}
        print(f"  compor {m['compor_s']}s · PDF {m['pdf']['paginas']} pág "
              f"{m['pdf']['largura_mm']}×{m['pdf']['altura_mm']} mm · "
              f"{m['pdf']['bytes']:,} bytes")
        medicoes["campanhas"][nome] = m

    # --- o dossiê (passo 65) ------------------------------------------------
    (SAIDA / "medicoes.json").write_text(
        json.dumps(medicoes, ensure_ascii=False, indent=2), encoding="utf-8")
    linhas = [
        "# DOSSIÊ DO MARCO — Fase 12 (material da sessão de aceitação)",
        f"\nGerado em {medicoes['quando']} · acervo de "
        f"{medicoes['acervo']} produtos",
        f"\nAbrir o catálogo: {medicoes['abrir_catalogo_s']}s",
    ]
    for nome, m in medicoes["campanhas"].items():
        linhas += [
            f"\n## Campanha {nome}",
            f"- {m['itens_reais']} ofertas REAIS transcritas da peça; "
            f"validade **{m['validade']}** (RG-58: nunca vazia)",
            f"- Conciliar contra 5k: **{m['conciliar_s']}s** → "
            f"{m['semaforo']}",
            f"- Layout REAL detectado da arte em {m['detectar_s']}s; "
            f"{m['celulas_ocupadas']} células ocupadas",
            f"- Compor: {m['compor_s']}s · PDF: {m['pdf']['paginas']} "
            f"páginas, {m['pdf']['largura_mm']}×{m['pdf']['altura_mm']} mm, "
            f"{m['pdf']['bytes']:,} bytes",
            f"- Pré-voo: {m['avisos_pre_voo'] or 'LIMPO'}",
        ]
    if medicoes["campanhas_faltantes"]:
        linhas += [
            "\n## Campanhas que FALTAM no disco (sessão de aceitação)",
            "As artes destas campanhas não estão em `arte/` — o marco as "
            "absorve SOZINHO quando as pastas receberem "
            "`frente_template.png` + `ofertas_*.txt`:",
        ] + [f"- **{f}**" for f in medicoes["campanhas_faltantes"]]
    (SAIDA / "DOSSIE_MARCO.md").write_text("\n".join(linhas),
                                           encoding="utf-8")
    print(f"\nDossiê e artefatos em {SAIDA}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
