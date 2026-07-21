"""
Self-check do MARCO (RG-36, Onda 5) — as TRÊS campanhas + performance 5k
========================================================================
O teste de regressão final da REVISAO_GERAL, reproduzível, com artefatos
para a medição independente do arquiteto:

  1. clone do acervo real (o vivo é só LIDO) via .atpkg;
  2. **Quintou frente+verso** (~40 itens, agrupado, seções CONTORNO) —
     PNG×N 1:1 + PDF;
  3. **Sexta Verde** (grade detectada da arte real da auditoria, capa com
     HERÓIS, seções PILL com cor por categoria, validade DE/ATÉ, selo
     personalizado "Muito Barato") — PNG + PDF;
  4. congela e reabre os projetos;
  5. **performance com acervo ≥5.000**: abrir (init+snapshot+listagem),
     conciliar os 40 (fuzzy/embeddings sobre o acervo cheio; a IA real
     entra quando o LM está ligado — registrado no relatório), exportar.
     Orçamentos: abrir <5 s · conciliar <180 s · exportar <30 s.

Rodar:  python -m app.scripts.selfcheck_marco
Artefatos + RELATORIO.txt em ``saida_marco/``.
"""

from __future__ import annotations

import os
import shutil
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SAIDA = Path("saida_marco")
FIXTURE = Path("app/tests/fixtures/ofertas_quintou_40.txt")
ARTE = Path("arte/quintou")
ARTE_SEXTA = Path("revisão/Sexta Verde Template.png")
CATEGORIAS_DEMO = ["Mercearia", "Bebidas", "Limpeza", "Higiene", "Frios"]
ACERVO_SINTETICO = 5000

_REL: list[str] = []


def _log(msg: str) -> None:
    print(msg)
    _REL.append(msg)


def _ok(msg: str) -> None:
    _log(f"  OK  {msg}")


def _falha(msg: str) -> None:
    _log(f"  FALHOU  {msg}")
    (SAIDA / "RELATORIO.txt").write_text("\n".join(_REL), encoding="utf-8")
    sys.exit(1)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for exigido in (ARTE / "frente_template.png", ARTE / "verso_template.png",
                    ARTE_SEXTA, FIXTURE):
        if not exigido.exists():
            _falha(f"artefato exigido ausente: {exigido}")
    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    SAIDA.mkdir(parents=True)

    from app.core.paths import SystemRoot
    raiz_real = SystemRoot()
    os.environ["AUTOTABLOIDE_ROOT"] = str((SAIDA / "raiz").resolve())
    clone = SystemRoot().criar_estrutura()
    _log(f"MARCO RG-36 — raiz descartável: {clone.raiz}")

    # --- 1. clone do acervo real ------------------------------------------------
    from app.core import portabilidade as porta
    pkg = porta.exportar_pacote(SAIDA / "acervo.atpkg", raiz_real)
    with porta.analisar_pacote(pkg, clone) as an:
        rel = porta.aplicar_importacao(an, {}, clone)
    _ok(f"acervo real clonado: {len(rel.produtos_novos)} produtos, "
        f"{rel.fotos_verificadas} fotos byte a byte")

    # --- categorias no clone (IA real se houver; demo completa) -------------------
    from sqlalchemy import select

    from app.core.database import Database
    from app.core.models import Produto
    from app.core.repositories import ProdutoRepositorio
    from app.qt.telas.servico import _motor_se_disponivel
    motor = _motor_se_disponivel()
    _log(f"      IA local: {'LIGADA' if motor is not None else 'DESLIGADA'} "
         "(a conciliação degrada para fuzzy/embeddings — registrado)")
    if motor is not None:
        from app.scripts.enriquecer_banco import categorizar_acervo
        r = categorizar_acervo(motor, log=lambda _l: None)
        _log(f"      IA real categorizou {r['categorizados']}")
    db = Database(clone).init()
    with db.Session() as s:
        repo = ProdutoRepositorio(s)
        sem = [p for p in s.execute(select(Produto)).scalars()
               if p.categoria_id is None]
        for i, p in enumerate(sem):
            repo.editar(p.id, categoria=CATEGORIAS_DEMO[i % 5],
                        categoria_origem="ia")
        s.commit()
    db.engine.dispose()

    # --- 5a. acervo sintético ≥5k (ANTES de medir: o cenário do orçamento) --------
    t0 = time.perf_counter()
    db = Database(clone).init()
    with db.Session() as s:
        repo = ProdutoRepositorio(s)
        base = repo.contar()
        for i in range(ACERVO_SINTETICO):
            repo.importar(f"PRODUTO SINTETICO {i:04d} MARCA{i % 40} "
                          f"{100 + i % 900} G", preco=f"{1 + i % 50},{i % 100:02d}")
        s.commit()
        total = repo.contar()
    db.engine.dispose()
    _ok(f"acervo sintético: {base} reais + {ACERVO_SINTETICO} = {total} "
        f"produtos ({time.perf_counter() - t0:.1f}s de semeio)")

    # --- 5b. ABRIR com acervo 5k (init + snapshot + listagens de chegada) ---------
    t0 = time.perf_counter()
    from app.core.cofre import snapshot_automatico
    Database(clone).init().engine.dispose()
    snapshot_automatico()
    from app.core import projetos as proj_mod
    proj_mod.listar_projetos()
    from app.qt.telas import servico
    servico.listar_catalogo(limite=50)          # a 1ª página do Almoxarifado
    t_abrir = time.perf_counter() - t0
    _ok(f"ABRIR com {total} produtos: {t_abrir:.2f}s (orçamento 5s)")
    if t_abrir >= 5.0:
        _falha(f"orçamento de abertura estourado: {t_abrir:.2f}s")

    # --- 5c. CONCILIAR os 40 sobre o acervo cheio ---------------------------------
    t0 = time.perf_counter()
    resultado = servico.importar_ofertas(FIXTURE, lambda _m: None)
    t_conc = time.perf_counter() - t0
    placar = {"VERDE": 0, "AMARELO": 0, "VERMELHO": 0}
    for it in resultado.itens:
        placar[it.semaforo] += 1
    n40 = len(resultado.itens)
    _ok(f"CONCILIAR {n40} sobre {total}: {t_conc:.1f}s (orçamento 180s) — "
        f"🟢{placar['VERDE']} 🟡{placar['AMARELO']} 🔴{placar['VERMELHO']}")
    if t_conc >= 180:
        _falha(f"orçamento de conciliação estourado: {t_conc:.1f}s")

    # bancada sem o acervo do Quintou (ex.: máquina do builder): os 🔴 são
    # CRIADOS no clone — o fluxo real do RG-03 ("criar todos sem foto");
    # grade vazia com OK seria silêncio, e silêncio é bug (I2)
    if placar["VERMELHO"]:
        _log(f"      criando {placar['VERMELHO']} novos no CLONE "
             "(fluxo RG-03 — bancada sem o acervo do Quintou)")
        for it in resultado.itens:
            if it.semaforo == "VERMELHO":
                prop = servico.enriquecer_descricao(it.descricao, None)
                servico.finalizar_criacao(it, prop.nome, prop.mais18, None,
                                          categoria=prop.categoria)
        db = Database(clone).init()
        with db.Session() as s:
            repo = ProdutoRepositorio(s)
            sem = [p for p in s.execute(select(Produto)).scalars()
                   if p.categoria_id is None]
            for i, p in enumerate(sem):
                repo.editar(p.id, categoria=CATEGORIAS_DEMO[i % 5],
                            categoria_origem="ia")
            s.commit()
        db.engine.dispose()
        for it in resultado.itens:      # a categoria recém-posta entra no item
            if it.via == "novo" and not it.categoria:
                it.categoria = CATEGORIAS_DEMO[
                    resultado.itens.index(it) % 5]

    # --- 2. QUINTOU frente+verso (~40, agrupado, seções CONTORNO) ------------------
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from app.qt.telas.mesa import MesaTela
    from app.rendering.grade import adicionar_pagina_de_arte, layout_grade_de_arte

    layout, _ = layout_grade_de_arte(str(ARTE / "frente_template.png"))
    adicionar_pagina_de_arte(layout, str(ARTE / "verso_template.png"))
    adicionar_pagina_de_arte(layout, str(ARTE / "verso_template.png"))

    mesa = MesaTela()
    mesa.carregar_layout(layout, str(ARTE / "frente_template.png"),
                         nome_layout="Marco — Quintou")
    mesa._itens = [it for it in resultado.itens
                   if it.semaforo == "VERDE" or it.via == "novo"]
    mesa.chk_agrupar.setChecked(True)
    mesa._auto_preencher()
    if len(mesa._mapa) < 30:            # o marco é de ~40: menos = falha
        _falha(f"grade do Quintou com só {len(mesa._mapa)} células — o "
               "marco exige ≥30 itens preenchidos")
    _ok(f"Quintou agrupado: {len(mesa._mapa)} células preenchidas, "
        f"{len(layout.paginas)} páginas")

    avisos = (servico.validar_composicao(layout, mesa._dados_por_slot())
              + mesa._avisos_orfaos())
    _log(f"      pré-voo Quintou: {len(avisos)} pendência(s) nominais")

    from pypdf import PdfReader

    from app.rendering.compositor import compor_pagina
    from app.rendering.export import exportar_pdf_multipagina, exportar_png
    t0 = time.perf_counter()
    dados = mesa._dados_por_slot()
    imgs = []
    for n, pag in enumerate(layout.paginas, start=1):
        img = compor_pagina(layout, pag, dados,
                            fundo_path=str(ARTE / "frente_template.png")
                            if n == 1 else None)
        if img.size != (1080, 1300):
            _falha(f"página {n} não é 1:1 com a arte: {img.size}")
        exportar_png(img, SAIDA / f"quintou_p{n}.png", layout.dpi)
        imgs.append(img)
    pdf = exportar_pdf_multipagina(imgs, SAIDA / "quintou.pdf", layout.dpi)
    t_exp = time.perf_counter() - t0
    if len(PdfReader(str(pdf)).pages) != len(layout.paginas):
        _falha("PDF do Quintou com nº de páginas errado")
    _ok(f"EXPORTAR Quintou (PNG×{len(imgs)} + PDF): {t_exp:.1f}s "
        f"(orçamento 30s)")
    if t_exp >= 30:
        _falha(f"orçamento de export estourado: {t_exp:.1f}s")

    pid = proj_mod.salvar_projeto(
        "Marco — Quintou 40", "Quintou", "TABLOIDE", layout,
        [it.to_dict() for it in mesa._itens], resultado.validade_oferta,
        nome_layout="Marco — Quintou", mapa=mesa._mapa)
    p = proj_mod.abrir_projeto(pid)
    if p.mapa != mesa._mapa:
        _falha("o congelado do Quintou não reabriu idêntico")
    _ok("Quintou congelado e reaberto idêntico")

    # --- 3. SEXTA VERDE (heróis + PILL/cor por categoria + de/até + selo) ----------
    from app.core.repositories import ConfigRepositorio
    db = Database(clone).init()
    with db.Session() as s:
        cfg = ConfigRepositorio(s)
        cfg.set("secoes.estilo", "PILL")            # RG-31 em prova viva
        cfg.set("secoes.cores_por_categoria", True)
        s.commit()
    db.engine.dispose()
    arte_selo = SAIDA / "_selo_barato.png"
    from PIL import Image as _Img
    _Img.new("RGBA", (96, 96), "#D91E2E").save(arte_selo)
    servico.adicionar_selo_personalizado("Muito Barato", str(arte_selo))

    # a Sexta Verde REAL nasceu "do zero" na auditoria (o dono desenhou as
    # células à mão sobre a arte — capturas 19-165 da gravação de Config).
    # O layout DELE viaja no clone (.atpkg leva layouts): usamos O MESMO.
    # Fallback (bancada sem o layout): grade programática 2×3, registrada.
    from app.rendering.grade import ocupaveis as _ocupaveis
    from app.rendering.persistencia import carregar_layout, listar_layouts
    layout_sv = None
    db = Database(clone).init()
    with db.Session() as s:
        row = next((r for r in listar_layouts(s)
                    if r.nome.strip().lower() == "sexta verde"), None)
        if row is not None:
            layout_sv = carregar_layout(s, row.id)
    db.engine.dispose()
    if layout_sv is not None and _ocupaveis(layout_sv.paginas[0].slots):
        _log("      layout da Sexta Verde: O DO DONO (da auditoria)")
    else:
        if layout_sv is not None:
            _log("      ACHADO: o layout “Sexta Verde” do banco está VAZIO "
                 "— as células desenhadas na auditoria não foram salvas "
                 "(consistente com o RG-08, curado DEPOIS da sessão). "
                 "Grade programática 2×3 em uso — o dono redesenha no "
                 "editor quando quiser.")
        else:
            _log("      layout da Sexta Verde ausente — grade programática")
        from app.rendering.grade import propagar_mestre
        from app.rendering.model import (
            Alinhamento as _Al, PapelPreco as _PP, Regiao as _Reg,
            Retangulo as _Ret, Slot as _Slot, SubtipoPreco as _SP,
            TipoRegiao as _TR, layout_de_arte,
        )
        from app.rendering.units import px_para_mm as _px_mm
        layout_sv = layout_de_arte(str(ARTE_SEXTA))
        dpi_sv = layout_sv.dpi
        bw, bh = 430, 250
        caixas = [(60 + c * 500, 330 + li * 235, bw, bh)
                  for li in range(3) for c in range(2)]
        bx, by, *_ = caixas[0]
        regioes0 = [
            _Reg(_TR.IMAGEM, _Ret.de_px(bx + 10, by + 6, bw - 20,
                                        int(bh * 0.44), dpi_sv),
                 nome="Imagem"),
            _Reg(_TR.NOME, _Ret.de_px(bx + 10, by + int(bh * 0.52),
                                      bw - 20, int(bh * 0.2), dpi_sv),
                 nome="Nome", fonte="Quicksand-Bold.ttf",
                 tamanho_max_pt=13, cor="#1B4332",
                 alinhamento=_Al.ESQUERDA),
            _Reg(_TR.PRECO, _Ret.de_px(bx + 10, by + int(bh * 0.72),
                                       bw - 20, int(bh * 0.26), dpi_sv),
                 nome="Preço", fonte="Quicksand-Bold.ttf",
                 tamanho_max_pt=34, cor="#FFFFFF",
                 alinhamento=_Al.CENTRO, subtipo_preco=_SP.COMPLETO,
                 papel_preco=_PP.POR, mostrar_moeda=False),
        ]
        for r in regioes0:
            r.de_mestre = True
        slots_sv = [_Slot("celula_0", regioes0, mestre=True,
                          origem_mm=(_px_mm(bx, dpi_sv), _px_mm(by, dpi_sv)))]
        for i, cx in enumerate(caixas[1:], start=1):
            slots_sv.append(_Slot(
                f"celula_{i}",
                origem_mm=(_px_mm(cx[0], dpi_sv), _px_mm(cx[1], dpi_sv)),
                ref_grupo="celula_0"))
        layout_sv.paginas[0].slots = slots_sv
        propagar_mestre(layout_sv.paginas[0])
    n_cel = len(_ocupaveis(layout_sv.paginas[0].slots))
    if n_cel < 4:
        _falha(f"layout da Sexta Verde sem células ocupáveis ({n_cel})")
    mesa2 = MesaTela()
    mesa2.carregar_layout(layout_sv, str(ARTE_SEXTA),
                          nome_layout="Marco — Sexta Verde")
    mesa2._itens = [it for it in resultado.itens
                    if it.semaforo == "VERDE"][:n_cel]
    if mesa2._itens:
        mesa2._itens[0].selos = ["Muito Barato"]    # RG-33 em prova viva
    mesa2._validade = servico.montar_validade_oferta("18/07", "24/07")
    mesa2.chk_agrupar.setChecked(True)
    mesa2.chk_herois.setChecked(True)               # RG-42 em prova viva
    mesa2._auto_preencher()
    dados2 = mesa2._dados_por_slot()
    img_sv = compor_pagina(layout_sv, layout_sv.paginas[0], dados2,
                           fundo_path=str(ARTE_SEXTA))
    exportar_png(img_sv, SAIDA / "sexta_verde.png", layout_sv.dpi)
    pdf_sv = exportar_pdf_multipagina([img_sv], SAIDA / "sexta_verde.pdf",
                                      layout_sv.dpi)
    if len(PdfReader(str(pdf_sv)).pages) != 1:
        _falha("PDF da Sexta Verde com nº de páginas errado")
    pid2 = proj_mod.salvar_projeto(
        "Marco — Sexta Verde", "Sexta Verde", "TABLOIDE", layout_sv,
        [it.to_dict() for it in mesa2._itens], mesa2._validade,
        nome_layout="Marco — Sexta Verde", mapa=mesa2._mapa)
    if proj_mod.abrir_projeto(pid2).mapa != mesa2._mapa:
        _falha("o congelado da Sexta Verde não reabriu idêntico")
    _ok(f"Sexta Verde: grade {n_cel} células, heróis + PILL/cor por "
        f"categoria + “{mesa2._validade}” + selo do gestor — congelada")

    _log("\nRESUMO DOS ORÇAMENTOS (F8-D1):")
    _log(f"  abrir com {total} produtos : {t_abrir:6.2f}s  (teto 5s)")
    _log(f"  conciliar {n40} itens       : {t_conc:6.1f}s  (teto 180s)")
    _log(f"  exportar 3 páginas         : {t_exp:6.1f}s  (teto 30s)")
    _log("\nMARCO RG-36 EXECUTADO — artefatos em saida_marco/ para a "
         "medição independente do arquiteto. O selo final é do Otaviano.")
    (SAIDA / "RELATORIO.txt").write_text("\n".join(_REL), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
