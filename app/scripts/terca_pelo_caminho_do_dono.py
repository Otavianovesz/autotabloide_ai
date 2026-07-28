"""F13-DUODECIMUS §4 — a TERÇA DO PÃO pelo caminho do dono, na raiz REAL.

O teste difícil de verdade: a tabela é 2/3 prosa (T1), são 5 itens para
4 células livres (T2), os percentuais são da arte (T3) e as 3 fotos
fixas passam pelo PIPELINE — nunca pela mão (T6). Este script dirige a
Mesa de verdade e RELATA cada guarda que disparou.

Gestos de curadoria do dono, declarados: as fotos das fixas são
internadas no template via o MESMO caminho do diálogo dos fixos
(internar_foto_fixa), com o packshot do Estúdio (degrau 1) quando a
foto vem crua; item VERMELHO da conciliação é cadastrado sem foto pelo
caminho do botão "Criar todos sem foto".

Uso:  python -m app.scripts.terca_pelo_caminho_do_dono
"""

from __future__ import annotations

import os
import shutil
import sys
import time
from datetime import date
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parents[2]

# a tabela REAL da Terça (a transcrição da ordem, como o OCR lê)
TABELA_TERCA = '''"HOJE É O DIA DO SONHO E DO CROASONHO, NO BELO BRASIL".
É a terça-feira especial do pão francês do sonho e do croasonho com pedaços de
moranguinho!! Uma enorme diversidade de sabores  LEVE 3 SONHOS OU 3 CROASONHOS
E GANHE 25 % de DESCONTO, ...
VENHA... SABOREAR, e com os preços mais baixos da cidade.  E TEM TAMBEM.......

  <> O PÃO FRANCÊS COM 50 % de DESCONTO <>

• SALSICHA HOT DOG REZENDE KG__só__          9,90
• FIGADO BOVINO ____100 g ___SÓ________      0,99
• OSSINHO _________À_____100g ____só_______  1,81
• COXA SOB COXA_À______100g ____POR____      0,77
• LINGUA e CORAÇÃO ____100g _____Só_______   0,66'''

NOME_PROJETO = "Terça 28/07 — caminho do dono"


def _packshot(origem: Path, destino: Path, *,
              forcar: bool = False) -> list[str]:
    """T6: a foto CRUA vira packshot pelo DEGRAU 1 REAL (rembg +
    normalização + sombra) e devolve o relatório das guardas. A foto já
    recortada (alfa útil) NÃO é reprocessada — vai como está.
    ``forcar`` é o clique "processar" do Estúdio (gesto do dono,
    declarado): o croissant veio com alfa MAS com a tábua dentro do
    recorte — a reclamação clássica dele — e ele mandaria reprocessar."""
    from PIL import Image
    from app.images.avaliador import _blobs_relevantes, avaliar_foto
    from app.images.fundo import tem_alfa_util

    rel: list[str] = []
    img = Image.open(origem)
    if tem_alfa_util(img) and not forcar:
        rel.append(f"{origem.name}: alfa útil — rembg PULADO (T6)")
        shutil.copy2(origem, destino)
        return rel
    if forcar:
        rel.append(f"{origem.name}: REPROCESSO FORÇADO (o gesto do "
                   "Estúdio — a tábua veio dentro do recorte)")
    t0 = time.time()
    from app.images.estudio import packshot_degrau1
    pack = packshot_degrau1(img)
    pack.save(destino)
    rel.append(f"{origem.name}: degrau 1 em {time.time() - t0:.1f}s")
    blobs = _blobs_relevantes(pack)
    if blobs >= 2:
        rel.append(f"{origem.name}: GUARDA J18 ACESA — {blobs} objetos "
                   "separados no recorte (o pré-voo avisa)")
    else:
        rel.append(f"{origem.name}: recorte com {blobs} objeto — a "
                   "guarda J18 não precisou")
    av = avaliar_foto(destino)
    rel.append(f"{origem.name}: nota do avaliador {getattr(av, 'nota', '?')}"
               f" ({getattr(av, 'motivo', '')})")
    return rel


def _prova_do_esrgan(origem: Path) -> list[str]:
    """T6: a régua da F10 mira o MAIOR lado da CÉLULA — a zona do
    croissant tem 584 px no export (não dispara para 621 px de foto).
    A ordem manda provar que o Real-ESRGAN RODA: uma ampliação sob
    demanda de teste, medida, sem gravar nada."""
    rel: list[str] = []
    try:
        from app.core.paths import SystemRoot
        from app.images.upscale import UpscalerRealESRGAN, ampliar_sob_demanda
        modelo = SystemRoot().modelos / "RealESRGAN_x4plus.pth"
        if not modelo.exists():
            rel.append("Real-ESRGAN: o modelo RealESRGAN_x4plus.pth NÃO "
                       "está no disco — a produção degrada a Lanczos COM "
                       "aviso (a regra da F4.3); prova de vida impossível "
                       "nesta máquina — reportado, não contornado (T6)")
            return rel
        t0 = time.time()
        up = UpscalerRealESRGAN(str(modelo))
        grande = ampliar_sob_demanda(origem, up, 1200)
        rel.append(f"Real-ESRGAN RODOU: {origem.name} "
                   f"{Image_size(origem)} → {grande.size} em "
                   f"{time.time() - t0:.1f}s (prova; a régua da célula "
                   "584px NÃO pedia — nada gravado)")
    except Exception as e:
        rel.append(f"Real-ESRGAN NÃO RODOU: {type(e).__name__}: {e} — "
                   "reportado, não contornado (T6)")
    return rel


def Image_size(p: Path):
    from PIL import Image
    with Image.open(p) as im:
        return im.size


def rodar() -> None:
    os.environ["AUTOTABLOIDE_ROOT"] = str(
        RAIZ_REPO / "AutoTabloide_System_Root")
    from app.core.paths import SystemRoot
    root = SystemRoot()
    print("raiz real:", root.raiz)

    banco = root.caminho_banco
    backup = root.raiz / "backups" / \
        f"core_pre_duodecimus_{date.today():%Y%m%d}.db"
    backup.parent.mkdir(exist_ok=True)
    if not backup.exists():
        shutil.copy2(banco, backup)
        print("backup:", backup.name)

    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import QAbstractButton, QApplication, QLineEdit
    app = QApplication.instance() or QApplication([])

    from app.core.database import Database
    from app.qt.telas import servico
    from app.qt.telas.colagem import linhas_para_tuplas, parse_colagem
    from app.qt.telas.fixos_dialog import internar_foto_fixa
    from app.qt.telas.mesa import MesaTela
    from app.rendering.persistencia import (
        carregar_layout, listar_layouts, salvar_layout,
    )

    def _drenar(ms=50):
        from PySide6.QtCore import QDeadlineTimer, QEventLoop
        fim = QDeadlineTimer(ms)
        while not fim.hasExpired():
            app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 10)

    # 1) T6 — as três fotos pelo PIPELINE (nunca pela mão)
    tmp = root.biblioteca_imagens / "_fixos"
    tmp.mkdir(parents=True, exist_ok=True)
    relatorio: list[str] = []
    relatorio += _packshot(RAIZ_REPO / "pão frances.png",
                           tmp / "pao-frances.png")
    relatorio += _packshot(RAIZ_REPO / "Sonho.jpg", tmp / "sonho.png")
    relatorio += _packshot(RAIZ_REPO / "croissant.png",
                           tmp / "croissant.png", forcar=True)
    relatorio += _prova_do_esrgan(tmp / "croissant.png")
    for r in relatorio:
        print("T6:", r)

    # 2) as fixas no TEMPLATE (o caminho do diálogo dos fixos: internar
    # + conteudo_fixo; os percentuais 50%/25% são DA ARTE — sem preço)
    db = Database().init()
    try:
        with db.Session() as s:
            alvo = next(r for r in listar_layouts(s)
                        if r.nome == "Terça do Pão")
            lay = carregar_layout(s, alvo.id, raiz=root)
            fixas = [sl for p in lay.paginas for sl in p.slots if sl.fixa]
            assert len(fixas) == 2, [f.id for f in fixas]
            f1 = next(f for f in fixas if f.id == "celula-1")
            f2 = next(f for f in fixas if f.id == "celula-2")
            f1.conteudo_fixo = {
                "nome": "Pão Francês", "descritor": "quentinho da hora",
                "preco": None, "preco_da_semana": False,
                "imagem": internar_foto_fixa(tmp / "pao-frances.png")}
            f2.conteudo_fixo = {
                "nome": "Sonho + Croissant",
                "descritor": "a dupla da terça",
                "preco": None, "preco_da_semana": False,
                "imagens": [internar_foto_fixa(tmp / "sonho.png"),
                            internar_foto_fixa(tmp / "croissant.png")]}
            salvar_layout(s, "Terça do Pão", lay,
                          layout_id=alvo.id, raiz=root)
            s.commit()
            print("fixas no template: Pão Francês + o PAR "
                  "Sonho/Croissant (T5)")
    finally:
        db.engine.dispose()

    # 3) o caminho do dono: Mesa real ← layout do banco
    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    m.carregar_layout(lay, lay.arquivo_fundo, nome_layout="Terça do Pão")
    m.show()
    _drenar()
    assert m._validade, "a validade não nasceu da cascata (DECIMUS)"
    print(f"validade NASCIDA SOZINHA: {m._validade} · chip: "
          f"{m._validade_lbl.text()}")

    # 4) a tabela CRUA — T1: a prosa vai ao balde, os 5 viram itens
    balde: list[str] = []
    linhas = parse_colagem(TABELA_TERCA, balde=balde)
    print(f"parser: {len(linhas)} itens · {len(balde)} linhas de prosa "
          "no balde (mostradas ao dono):")
    for b in balde:
        print("   balde:", b[:70])
    tuplas = linhas_para_tuplas(linhas)
    resultado = servico.conciliar_linhas(tuplas, lambda *a, **k: None)
    vermelhos = [it for it in resultado.itens if it.semaforo != "VERDE"]
    # a CORREÇÃO CONFIRMADA PELO DONO (27/07, por escrito): "o que for
    # gramaticalmente correto" — a caixa de edição da conciliação; e o
    # banco APRENDE o alias (a trava da F9: só o que o dono confirmou)
    CORRECOES_DO_DONO = {"COXA SOB COXA": "Coxa Sobrecoxa"}
    for it in vermelhos:
        prop = servico.enriquecer_descricao(
            it.descricao, servico._motor_se_disponivel())
        nome_final = prop.nome
        alias_de = None
        for cru, certo in CORRECOES_DO_DONO.items():
            if cru in it.descricao.upper():
                nome_final, alias_de = certo, it.descricao
        servico.finalizar_criacao(it, nome_final, prop.mais18, None,
                                  prop.categoria)
        if alias_de and it.produto_id:
            from app.core.database import Database as _DB
            _db = _DB().init()
            try:
                with _db.Session() as s:
                    from app.core.repositories import ProdutoRepositorio
                    ProdutoRepositorio(s).aprender_alias(
                        it.produto_id, alias_de)
                    s.commit()
                print(f"alias APRENDIDO: “{alias_de}” → “{nome_final}”")
            finally:
                _db.engine.dispose()
        print(f"cadastrado SEM FOTO (Criar todos): {it.nome}")
    if vermelhos:
        resultado = servico.conciliar_linhas(tuplas, lambda *a, **k: None)
    for it in resultado.itens:
        print(f"  {it.semaforo:8s} {it.nome}  "
              f"[foto {'sim' if it.imagem else 'NÃO'}]")

    fechado = {"ok": False}

    def _tic():
        cx = app.activeModalWidget()
        if cx is None:
            return
        b = next((x for x in cx.findChildren(QAbstractButton)
                  if x.text().strip() == "Concluir"), None)
        if b is not None and b.isEnabled():
            fechado["ok"] = True
            b.click()

    t = QTimer(); t.setInterval(40); t.timeout.connect(_tic); t.start()
    m._conciliar(resultado)
    t.stop()
    assert fechado["ok"] and len(m._itens) == 5, len(m._itens)
    print(f"estante: {len(m._itens)} itens")

    # 5) T2 — auto-preencher: 4 entram, o 5º fica VISÍVEL fora da grade
    m.btn_preencher.click()
    _drenar()
    assert len(m._mapa) == 4, m._mapa
    fora = [it for it in m._itens if it.uid not in m._mapa.values()]
    assert len(fora) == 1
    print(f"auto-preencher: 4/4 células livres · FORA DA GRADE (visível "
          f"na estante): {fora[0].nome}")

    # 6) salvar (reusa por nome se der) + compor
    from app.core import projetos as _projetos
    existente = next((p["id"] for p in _projetos.listar_projetos()
                      if p["nome"] == NOME_PROJETO), None)
    if existente:
        m._projeto_id = existente

    def _tic_salvar():
        dlg = app.activeModalWidget()
        if dlg is None:
            return
        campo = getattr(dlg, "nome", None)
        if isinstance(campo, QLineEdit):
            campo.setText(NOME_PROJETO)
            b = next((x for x in dlg.findChildren(QAbstractButton)
                      if "Salvar" in x.text() and "assim" not in x.text()),
                     None)
            if b is not None and b.isEnabled():
                b.click()
            return
        b = next((x for x in dlg.findChildren(QAbstractButton)
                  if x.text().strip() == "Salvar mesmo assim"), None)
        if b is not None:
            b.click()

    t2 = QTimer(); t2.setInterval(40)
    t2.timeout.connect(_tic_salvar); t2.start()
    m._salvar_projeto()
    t2.stop()
    _drenar()
    assert m._projeto_id, "o projeto não congelou"
    print(f"projeto salvo: id={m._projeto_id} “{NOME_PROJETO}”")

    from PIL import Image
    img = m.paginas_compostas()[0]
    pag = (m.area.canvas._layout or m._layout).paginas[0]
    dens = servico.densidade_da_pagina(pag, m._dados_por_slot())
    print(f"densidade da página: {dens:.2f}")
    alt = round(1080 * img.height / img.width)
    destino = RAIZ_REPO / "saida_f13" / "galeria_f13_bis" / \
        "terca-2807-caminho-do-dono.png"
    img.resize((1080, alt), Image.LANCZOS).save(destino)
    print("página composta:", destino)
    m.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    rodar()
