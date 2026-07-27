"""F13-NONUS §6.4 — a Segunda recomposta PELO CAMINHO DO DONO, na raiz REAL.

A prova desta rodada não é uma página montada à mão: é o caminho
Ateliê → Mesa → importar → auto-preencher rodando com a tabela CRUA
dele (a transcrição de "Segunda 27.07.jpeg") e a página saindo certa
SEM nenhum dado alfaiatado. Este script dirige a MESA DE VERDADE
(cliques e diálogos respondidos por timer — o mesmo harness do teste
F2), com dois gestos de CURADORIA que são do dono, declarados:

* a linha do KIT é IGNORADA na importação (o Kit já vive FIXO no
  template, com foto e preço — o botão "Ignorar" da conciliação);
* item VERMELHO é cadastrado SEM FOTO pelo caminho do botão "Criar
  todos sem foto" (RG-03: enriquecer degradado sem LM + finalizar) —
  as fotos vêm depois, do acervo, como o fluxo dele manda.

Uso:  python -m app.scripts.segunda_pelo_caminho_do_dono
"""

from __future__ import annotations

import os
import shutil
import sys
from datetime import date
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parents[2]

# as 8 linhas CRUAS (idênticas às do teste S1 — a tabela como o OCR lê)
LINHAS_REAIS = """KIT BURGUER SENEPOL BBX ______ POR ______ 39,00
CREME DE LEITE ITALAC 200G________ SÓ________ 2,44
LEITE CONDENSADO TRIANGULO 395G________ só ________ 7,44
BATATA PALHA BULNEZ CROCANTE 100G____ SÓ _____ 6,66
AZEITE GALLO EXTRA VIRGEM CLÁSSICO 500ML ____ SÓ ____ 38,80
SUCO DE UVA AURORA TINTO TP/1,5LT _____ POR ______ 19,99
LEITE INTEGRAL PARMALAT 1LT________ POR ________ 5,95
OLEO DE SOJA CONCORDIA 900ML____ só _____ 7,70"""

NOME_PROJETO = "Segunda 27/07 — caminho do dono"


def rodar() -> None:
    os.environ["AUTOTABLOIDE_ROOT"] = str(
        RAIZ_REPO / "AutoTabloide_System_Root")
    from app.core.paths import SystemRoot
    root = SystemRoot()
    print("raiz real:", root.raiz)

    # backup antes de qualquer escrita (a lei da QUINQUE)
    banco = root.caminho_banco
    backup = root.raiz / "backups" / \
        f"core_pre_nonus_{date.today():%Y%m%d}.db"
    backup.parent.mkdir(exist_ok=True)
    if not backup.exists():
        shutil.copy2(banco, backup)
        print("backup:", backup.name)

    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import (
        QAbstractButton, QApplication, QLineEdit,
    )
    app = QApplication.instance() or QApplication([])

    from app.core.database import Database
    from app.qt.telas import servico
    from app.qt.telas.colagem import linhas_para_tuplas, parse_colagem
    from app.qt.telas.mesa import MesaTela
    from app.rendering.persistencia import carregar_layout, listar_layouts

    def _drenar(ms=50):
        from PySide6.QtCore import QDeadlineTimer, QEventLoop
        fim = QDeadlineTimer(ms)
        while not fim.hasExpired():
            app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 10)

    # 1) o Ateliê abriria o layout do BANCO — a mesma porta (L10)
    db = Database().init()
    try:
        with db.Session() as s:
            alvo = next(r for r in listar_layouts(s)
                        if r.nome == "Segunda dos Frios")
            ldef = carregar_layout(s, alvo.id, raiz=root)
    finally:
        db.engine.dispose()
    fixa = next(sl for p in ldef.paginas for sl in p.slots if sl.fixa)
    assert fixa.conteudo_fixo, "o Kit não está no template — rode a OCTAVUS"
    print("layout do banco: Segunda dos Frios · Kit fixo:",
          fixa.conteudo_fixo.get("nome"), "· preço",
          fixa.conteudo_fixo.get("preco"))

    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    m.carregar_layout(ldef, ldef.arquivo_fundo,
                      nome_layout="Segunda dos Frios")
    m.show()
    _drenar()

    # 2) a colagem da tabela CRUA; o gesto "Ignorar" do dono na linha
    # do Kit (ele já está fixo no template)
    linhas = parse_colagem(LINHAS_REAIS)
    tuplas = [t for t in linhas_para_tuplas(linhas)
              if "KIT BURGUER" not in t[0].upper()]
    print(f"tabela: {len(linhas)} linhas · {len(tuplas)} para a estante "
          "(o Kit IGNORADO — já é fixo)")

    resultado = servico.conciliar_linhas(tuplas, lambda *a, **k: None)
    vermelhos = [it for it in resultado.itens if it.semaforo != "VERDE"]
    for it in vermelhos:
        prop = servico.enriquecer_descricao(
            it.descricao, servico._motor_se_disponivel())
        servico.finalizar_criacao(it, prop.nome, prop.mais18, None,
                                  prop.categoria)
        print(f"cadastrado SEM FOTO (Criar todos): {it.nome}")
    if vermelhos:      # reconciliar: agora tudo casa verde
        resultado = servico.conciliar_linhas(tuplas, lambda *a, **k: None)
    for it in resultado.itens:
        print(f"  {it.semaforo:8s} {it.nome}  "
              f"[foto {'sim' if it.imagem else 'NÃO'}]")

    # 3) o diálogo de conciliação REAL, o Concluir clicado por timer
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

    t = QTimer()
    t.setInterval(40)
    t.timeout.connect(_tic)
    t.start()
    m._conciliar(resultado)
    t.stop()
    assert fechado["ok"] and len(m._itens) == 7, (
        f"a conciliação não fechou verde ({len(m._itens)} na estante)")
    print(f"estante: {len(m._itens)} itens")

    # o gesto do rótulo (RG-34): a validade da oferta
    m._validade = "SOMENTE 27/07"
    m._validade_lbl.setText(f"Validade: {m._validade}")

    # 4) auto-preencher pelo BOTÃO
    m.btn_preencher.click()
    _drenar()
    assert fixa.id not in m._mapa and len(m._mapa) == 7, (
        f"o mapa não fechou 7/7 fora da fixa: {m._mapa}")
    print("auto-preencher: 7/7 células livres · fixa intocada")

    # 5) salvar o PROJETO (diálogo real respondido por timer) — nome
    # novo; o id=7 do dono fica intacto
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
        if b is not None:        # o pré-voo AVISA (fotos faltando) — segue
            b.click()

    t2 = QTimer()
    t2.setInterval(40)
    t2.timeout.connect(_tic_salvar)
    t2.start()
    m._salvar_projeto()
    t2.stop()
    _drenar()
    assert m._projeto_id, "o projeto não congelou"
    print(f"projeto salvo: id={m._projeto_id} “{NOME_PROJETO}” — "
          "abrível pela Mesa (L10)")

    # 6) a página COMPOSTA (a receita do Exportar) — 1080 p/ o celular
    from PIL import Image
    img = m.paginas_compostas()[0]
    alt = round(1080 * img.height / img.width)
    destino = RAIZ_REPO / "saida_f13" / "galeria_f13_bis" / \
        "segunda-2707-caminho-do-dono.png"
    img.resize((1080, alt), Image.LANCZOS).save(destino)
    print("página composta:", destino)
    m.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    rodar()
