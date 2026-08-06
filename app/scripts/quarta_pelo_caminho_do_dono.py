"""F13-TERTIUSDECIMUS Parte 2 — a QUARTA DAS OFERTAS na raiz REAL.

O teste de OCR mais duro: a tabela é FOTO DE UM MONITOR (moldura,
reflexo, perspectiva). PROIBIDO tratar a imagem à mão — se o Qwen não
der conta, o script PARA e reporta (o achado vale mais que a página).
Os 3 fixos (Lanche 20% · Mini Salgadinhos 4,99 · Pão de Queijo 4,99)
provam os três modos do N1 numa página: desconto declarado + preço da
semana ×2. Gestos do dono declarados: fotos das fixas pelo pipeline;
as 3 linhas fixas saem da estante depois de alimentarem o template
(o gesto Ignorar — já são fixas).

Uso:  python -m app.scripts.quarta_pelo_caminho_do_dono
"""

from __future__ import annotations

import os
import shutil
import sys
import time
from datetime import date
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parents[2]
NOME_PROJETO = "Quarta 29/07 — caminho do dono"


def _packshot(origem: Path, destino: Path) -> list[str]:
    from PIL import Image
    from app.images.avaliador import _blobs_relevantes, avaliar_foto
    from app.images.fundo import tem_alfa_util

    rel: list[str] = []
    img = Image.open(origem)
    if tem_alfa_util(img):
        rel.append(f"{origem.name}: alfa útil — rembg PULADO")
        shutil.copy2(origem, destino)
        return rel
    t0 = time.time()
    from app.images.estudio import packshot_degrau1
    pack = packshot_degrau1(img)
    pack.save(destino)
    rel.append(f"{origem.name}: degrau 1 em {time.time() - t0:.1f}s")
    blobs = _blobs_relevantes(pack)
    rel.append(f"{origem.name}: {blobs} objeto(s) no recorte"
               + (" — GUARDA J18 ACESA" if blobs >= 2 else ""))
    av = avaliar_foto(destino)
    rel.append(f"{origem.name}: nota {getattr(av, 'nota', '?')} "
               f"({'; '.join(getattr(av, 'motivos', []) or [])})")
    return rel


def rodar() -> None:
    os.environ["AUTOTABLOIDE_ROOT"] = str(
        RAIZ_REPO / "AutoTabloide_System_Root")
    from app.core.paths import SystemRoot
    root = SystemRoot()
    print("raiz real:", root.raiz)

    banco = root.caminho_banco
    backup = root.raiz / "backups" / \
        f"core_pre_tertius_{date.today():%Y%m%d}.db"
    backup.parent.mkdir(exist_ok=True)
    if not backup.exists():
        shutil.copy2(banco, backup)
        print("backup:", backup.name)

    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import QAbstractButton, QApplication, QLineEdit
    app = QApplication.instance() or QApplication([])

    from app.core.database import Database
    from app.core.portabilidade import chave_natural
    from app.qt.telas import servico
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

    # 1) as três fotos pelo PIPELINE
    tmp = root.biblioteca_imagens / "_fixos"
    tmp.mkdir(parents=True, exist_ok=True)
    for r in (_packshot(RAIZ_REPO / "Lanche na Chapa.jpg",
                        tmp / "lanche-chapa.png")
              + _packshot(RAIZ_REPO / "Salgados.jpg",
                          tmp / "mini-salgadinhos.png")
              + _packshot(RAIZ_REPO / "Pão de Queijo.jpg",
                          tmp / "pao-de-queijo.png")):
        print("FOTOS:", r)

    # 2) as três fixas no TEMPLATE (os TRÊS modos do N1: desconto
    # declarado + preço da semana ×2 — "a única coisa que muda
    # raramente é o preço do mini salgado e do pão de queijo")
    db = Database().init()
    try:
        with db.Session() as s:
            alvo = next(r for r in listar_layouts(s)
                        if r.nome == "Quarta das Ofertas")
            lay = carregar_layout(s, alvo.id, raiz=root)
            fixas = {sl.id: sl for p in lay.paginas for sl in p.slots
                     if sl.fixa}
            print("fixas do layout:", sorted(fixas))
            f1, f2, f3 = (fixas["celula-fixa-1"], fixas["celula-fixa-2"],
                          fixas["celula-fixa-3"])
            f1.conteudo_fixo = {
                "nome": "Lanche na Chapa", "descritor": "feito na hora",
                "preco": None, "preco_da_semana": True,
                "desconto_pct": 20,
                "imagem": internar_foto_fixa(tmp / "lanche-chapa.png")}
            f2.conteudo_fixo = {
                "nome": "Mini Salgadinhos BB-X", "descritor": "100 g",
                "preco": "4,99", "preco_da_semana": True,
                "imagem": internar_foto_fixa(tmp / "mini-salgadinhos.png")}
            f3.conteudo_fixo = {
                "nome": "Pão de Queijo Tradicional BB-X",
                "descritor": "100 g",
                "preco": "4,99", "preco_da_semana": True,
                "imagem": internar_foto_fixa(tmp / "pao-de-queijo.png")}
            salvar_layout(s, "Quarta das Ofertas", lay,
                          layout_id=alvo.id, raiz=root)
            s.commit()
            print("fixas no template: Lanche (20%) + Mini + Pão de Queijo")
    finally:
        db.engine.dispose()

    # 3) O OCR REAL da FOTO DE MONITOR — sem tratar a imagem à mão
    print("OCR da foto de tela (Qwen2.5-VL via LM Studio)…")
    t0 = time.time()
    resultado = servico.importar_ofertas(
        str(RAIZ_REPO / "Quarta de Ofertas Tabela.jpeg"),
        lambda *a, **k: None)
    print(f"OCR + conciliação em {time.time() - t0:.0f}s — "
          f"{len(resultado.itens)} itens lidos:")
    for it in resultado.itens:
        print(f"  {it.semaforo:8s} {it.nome!r} preco={it.preco!r} "
              f"desconto={getattr(it, 'desconto_pct', None)}")
    if len(resultado.itens) < 5:
        print("OCR DERRUBADO pela foto de tela — PARANDO e reportando "
              "(a ordem §4: não forçar a página com dado digitado).")
        return

    # 4) a tabela alimenta o TEMPLATE (preço da semana + desconto) e as
    # linhas fixas saem da estante (o gesto Ignorar — já são fixas)
    avisos_fx = servico.atualizar_fixos_pela_tabela(lay, resultado.itens)
    for a in avisos_fx:
        print("fixo:", a)
    db = Database().init()
    try:
        with db.Session() as s:
            salvar_layout(s, "Quarta das Ofertas", lay,
                          layout_id=alvo.id, raiz=root)
            s.commit()
    finally:
        db.engine.dispose()
    chaves_fixas = {chave_natural(f.conteudo_fixo["nome"], None)
                    for f in (f1, f2, f3)}
    resultado.itens = [it for it in resultado.itens
                       if chave_natural(it.nome, None) not in chaves_fixas
                       and not getattr(it, "desconto_pct", None)]
    print(f"estante candidata (fixos fora): {len(resultado.itens)}")

    # 5) o caminho do dono
    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    m.carregar_layout(lay, lay.arquivo_fundo,
                      nome_layout="Quarta das Ofertas")
    m.show()
    _drenar()
    print(f"validade NASCIDA SOZINHA: {m._validade}")

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
    print(f"estante: {len(m._itens)} itens (Concluir={fechado['ok']})")

    m.btn_preencher.click()
    _drenar()
    print(f"auto-preencher: {len(m._mapa)} células · "
          f"{len(m._itens) - len(m._mapa)} fora da grade")

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
    print(f"projeto salvo: id={m._projeto_id} “{NOME_PROJETO}”")

    from PIL import Image
    img = m.paginas_compostas()[0]
    alt = round(1080 * img.height / img.width)
    destino = RAIZ_REPO / "saida_f13" / "galeria_f13_bis" / \
        "quarta-2907-caminho-do-dono.png"
    img.resize((1080, alt), Image.LANCZOS).save(destino)
    print("página composta:", destino)
    m.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    rodar()
