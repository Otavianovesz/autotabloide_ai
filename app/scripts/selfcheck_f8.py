"""
Self-check do MARCO (F8.3) — o tabloide categorizado de ~40 itens, real
========================================================================
Roda o fluxo de aceitação ponta a ponta com o ACERVO REAL — clonado via
.atpkg para uma raiz descartável (o System Root vivo é apenas LIDO):

  clone do acervo → categorias (IA real se o LM estiver ligado; completa
  com categorias de demonstração no CLONE) → fixture de ~40 itens reais →
  conciliação (o placar do semáforo) → auto-preencher AGRUPADO nas artes
  reais frente+verso (+1 página extra) → seções desenhadas → pré-voo
  nominal → export PNG×N + PDF medido → congela e reabre o projeto.

Rodar:  python -m app.scripts.selfcheck_f8
Artefatos em ``saida_selfcheck_f8/`` para a inspeção independente do
arquiteto. Fixture canônica: ``app/tests/fixtures/ofertas_quintou_40.txt``
(gerada do acervo real na primeira execução; depois, reutilizada).
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SAIDA = Path("saida_selfcheck_f8")
FIXTURE = Path("app/tests/fixtures/ofertas_quintou_40.txt")
ARTE = Path("arte/quintou")
CATEGORIAS_DEMO = ["Mercearia", "Bebidas", "Limpeza", "Higiene", "Frios"]


def _ok(msg: str) -> None:
    print(f"  OK  {msg}")


def _falha(msg: str) -> None:
    print(f"  FALHOU  {msg}")
    sys.exit(1)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if not (ARTE / "frente_template.png").exists():
        _falha("arte real do Quintou não encontrada em arte/quintou/")
    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    SAIDA.mkdir(parents=True)

    # a raiz REAL é capturada ANTES do desvio de ambiente (e só é LIDA)
    from app.core.paths import SystemRoot
    raiz_real = SystemRoot()
    os.environ["AUTOTABLOIDE_ROOT"] = str((SAIDA / "raiz").resolve())
    clone = SystemRoot().criar_estrutura()

    print("Self-check do MARCO F8.3 — acervo real, raiz descartável em", clone.raiz)

    # --- clone do acervo (o vivo é só lido) --------------------------------------
    from app.core import portabilidade as porta
    pkg = porta.exportar_pacote(SAIDA / "acervo.atpkg", raiz_real)
    with porta.analisar_pacote(pkg, clone) as an:
        rel = porta.aplicar_importacao(an, {}, clone)
    _ok(f"acervo clonado: {len(rel.produtos_novos)} produtos, "
        f"{rel.fotos_verificadas} fotos byte a byte")

    # --- categorias no CLONE: IA real se houver; demo completa o resto ------------
    from sqlalchemy import select

    from app.core.database import Database
    from app.core.models import Produto
    from app.qt.telas.servico import _motor_se_disponivel
    motor = _motor_se_disponivel()
    if motor is not None:
        from app.scripts.enriquecer_banco import categorizar_acervo
        r = categorizar_acervo(motor, log=lambda _l: None)
        print(f"      IA real categorizou {r['categorizados']} "
              f"(sem palpite: {r['sem_palpite']})")
    db = Database(clone).init()
    with db.Session() as s:
        from app.core.repositories import ProdutoRepositorio
        repo = ProdutoRepositorio(s)
        sem = [p for p in s.execute(select(Produto)).scalars()
               if p.categoria_id is None]
        for i, p in enumerate(sem):        # demo determinística, SÓ no clone
            repo.editar(p.id, categoria=CATEGORIAS_DEMO[i % 5],
                        categoria_origem="ia")
        s.commit()
        produtos = list(s.execute(select(Produto)).scalars())
        com_foto = [p for p in produtos if p.caminho_imagem]
        n_cats = len({p.categoria_id for p in produtos if p.categoria_id})
    db.engine.dispose()
    _ok(f"categorias no clone: {n_cats} distintas "
        f"({len(sem)} completadas com demo)")

    # --- fixture de ~40 itens REAIS (gera uma vez; depois reutiliza) ---------------
    if not FIXTURE.exists():
        escolhidos = (com_foto + [p for p in produtos
                                  if not p.caminho_imagem])[:40]
        linhas = [f"{p.nome_bruto} | "
                  f"{(str(p.preco_atual).replace('.', ',') if p.preco_atual is not None else f'{i + 1},99')}"
                  for i, p in enumerate(escolhidos)]
        FIXTURE.write_text("\n".join(linhas), encoding="utf-8")
        print(f"      fixture GERADA do acervo real: {FIXTURE}")
    shutil.copy(FIXTURE, SAIDA / "ofertas_40.txt")
    n_fixture = len([ln for ln in FIXTURE.read_text(encoding='utf-8')
                    .splitlines() if ln.strip()])

    # --- o fluxo da Mesa, ponta a ponta -------------------------------------------
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from app.qt.telas import servico
    from app.qt.telas.mesa import MesaTela
    from app.rendering.grade import adicionar_pagina_de_arte, layout_grade_de_arte

    layout, caixas = layout_grade_de_arte(str(ARTE / "frente_template.png"))
    adicionar_pagina_de_arte(layout, str(ARTE / "verso_template.png"))
    adicionar_pagina_de_arte(layout, str(ARTE / "verso_template.png"))
    total_celulas = sum(len(p.slots) for p in layout.paginas)

    mesa = MesaTela()
    mesa.carregar_layout(layout, str(ARTE / "frente_template.png"),
                         nome_layout="Marco F8 (frente+verso+extra)")

    resultado = servico.importar_ofertas(FIXTURE, lambda _m: None)
    placar = {"VERDE": 0, "AMARELO": 0, "VERMELHO": 0}
    for it in resultado.itens:
        placar[it.semaforo] += 1
    _ok(f"conciliação dos {n_fixture}: 🟢{placar['VERDE']} "
        f"🟡{placar['AMARELO']} 🔴{placar['VERMELHO']}")
    if placar["VERDE"] < n_fixture:
        print("      (não-verdes ficam de fora — na tela seriam resolvidos "
              "na conciliação; o marco segue com os verdes)")

    mesa._itens = [it for it in resultado.itens if it.semaforo == "VERDE"]
    mesa.chk_agrupar.setChecked(True)
    mesa._auto_preencher()
    na_grade = len(mesa._mapa)
    _ok(f"auto-preencher AGRUPADO: {na_grade} itens em {total_celulas} "
        f"células, 3 páginas, seções ligadas")

    # a fila agrupada de verdade: categorias em blocos contíguos
    por_uid = {it.uid: it for it in mesa._itens}
    from app.rendering.grade import ocupaveis, ordenar_slots_visualmente
    slots_ordem = []
    for pag in layout.paginas:
        slots_ordem.extend(ocupaveis(ordenar_slots_visualmente(pag.slots)))
    cats_na_ordem = [(por_uid[mesa._mapa[s.id]].categoria or "Outros")
                     for s in slots_ordem if s.id in mesa._mapa]
    blocos = [c for i, c in enumerate(cats_na_ordem)
              if i == 0 or cats_na_ordem[i - 1] != c]
    if len(blocos) != len(set(blocos)):
        _falha(f"categoria repetida em blocos separados: {blocos}")
    _ok(f"agrupamento contíguo: {' → '.join(blocos)}")

    # pré-voo NOMINAL (acervo real: pendências são informação, não surpresa)
    avisos = (servico.validar_composicao(layout, mesa._dados_por_slot())
              + mesa._avisos_orfaos())
    print(f"      pré-voo: {len(avisos)} pendência(s)")
    for a in avisos[:8]:
        print(f"        • {a}")
    if len(avisos) > 8:
        print(f"        … (+{len(avisos) - 8})")

    # --- export: PNG×3 + PDF medido; seções visíveis ------------------------------
    from pypdf import PdfReader

    from app.rendering.compositor import compor_pagina
    from app.rendering.export import exportar_pdf_multipagina, exportar_png
    dados = mesa._dados_por_slot()
    imgs = []
    for n, pag in enumerate(layout.paginas, start=1):
        img = compor_pagina(layout, pag, dados,
                            fundo_path=str(ARTE / "frente_template.png")
                            if n == 1 else None)
        if img.size != (1080, 1300):
            _falha(f"página {n} não é 1:1 com a arte: {img.size}")
        exportar_png(img, SAIDA / f"marco_p{n}.png", layout.dpi)
        imgs.append(img)
    pdf = exportar_pdf_multipagina(imgs, SAIDA / "marco.pdf", layout.dpi)
    leitor = PdfReader(str(pdf))
    if len(leitor.pages) != 3:
        _falha(f"PDF deveria ter 3 páginas, tem {len(leitor.pages)}")
    for pag in layout.paginas:
        pag.secoes_ligadas = False
    sem_secoes = compor_pagina(layout, layout.paginas[0], dados,
                               fundo_path=str(ARTE / "frente_template.png"))
    for pag in layout.paginas:
        pag.secoes_ligadas = True
    if list(sem_secoes.getdata()) == list(imgs[0].getdata()):
        _falha("as seções não apareceram no desenho")
    _ok(f"export: marco_p1..p3.png (1080×1300) + marco.pdf "
        f"({len(leitor.pages)} páginas) — seções visíveis")

    # --- congela e reabre (no CLONE) ------------------------------------------------
    from app.core import projetos
    pid = projetos.salvar_projeto(
        "Marco F8 — Quintou 40", "Quintou", "TABLOIDE", layout,
        [it.to_dict() for it in mesa._itens], resultado.validade_oferta,
        nome_layout="Marco F8", mapa=mesa._mapa)
    p = projetos.abrir_projeto(pid)
    if p.mapa != mesa._mapa or len(p.itens) != len(mesa._itens):
        _falha("o congelado não reabriu idêntico")
    if not all(pag.secoes_ligadas for pag in p.layout.paginas):
        _falha("as seções não congelaram ligadas")
    _ok("projeto congelado e reaberto idêntico (mapa + seções + itens)")

    print("\nMARCO F8.3 EXECUTADO: artefatos em saida_selfcheck_f8/ para a "
          "inspeção independente do arquiteto.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
