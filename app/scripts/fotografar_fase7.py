"""Galeria NATIVA da FASE 7 (Mesa II — produção em massa).

Fotografa os artefatos que o arquiteto sela no olho: a prévia da colagem "isto é
o que entendi" (com promoção e preço a rever), o campo qtd+valor da promoção, a
conciliação em TELA CHEIA com a foto ao lado, a planilha da estante (com a coluna
Observação), o seletor de frases prontas, e a Mesa com as badges de promoção/
observação + a estatística no rodapé.

SEM offscreen de propósito — o plugin nativo resolve as fontes da UI (o offscreen
desta bancada renderiza glifos como caixas); as janelas usam WA_DontShowOnScreen,
nada pisca na tela. Rodar::

    python -m app.scripts.fotografar_fase7 saida_fase7/claro
    python -m app.scripts.fotografar_fase7 saida_fase7/escuro --tema=escuro
"""

from __future__ import annotations

import sys
from pathlib import Path


def _processar(n: int = 3) -> None:
    from PySide6.QtWidgets import QApplication
    for _ in range(n):
        QApplication.processEvents()


def _grab(widget, pasta: Path, nome: str) -> None:
    _processar()
    pasta.mkdir(parents=True, exist_ok=True)
    widget.grab().save(str(pasta / nome))
    print(f"  {nome}")


def _tabela_png(destino: Path) -> str:
    """Um 'print' de tabela de ofertas para a foto da conciliação em tela cheia."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (420, 300), (250, 249, 246))
    d = ImageDraw.Draw(img)
    linhas = ["OFERTAS DA SEMANA — BELO BRASIL", "",
              "OLEO SOJA LIZA 900ML .... 7,71",
              "ARROZ TIO JOAO 5KG ...... 24,90",
              "SABAO OMO 1,6KG ... 3 por 10,00",
              "REFRIG KITUBAINA 1,5L .... 5,50",
              "DOCE BANANA VAL 250G ..... 6,66"]
    y = 16
    for ln in linhas:
        d.text((18, y), ln, fill=(40, 40, 40))
        y += 38
    destino.parent.mkdir(parents=True, exist_ok=True)
    img.save(destino)
    return str(destino)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pasta = Path(args[0] if args else "saida_fase7/claro")
    tema = next((a.split("=", 1)[1] for a in sys.argv[1:]
                 if a.startswith("--tema=")), None)

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from app.qt.design.tema import aplicar_tema
    app = QApplication.instance() or QApplication([])
    aplicar_tema(app, tema) if tema else aplicar_tema(app)
    from app.qt.design.polimento import instalar_polimento
    instalar_polimento(app)

    DONT = Qt.WidgetAttribute.WA_DontShowOnScreen

    from app.qt.telas import servico
    from app.qt.telas.servico import ItemMesa, ResultadoMesa

    # --- 1) prévia da colagem (com promoção e preço a rever) -----------------
    from app.qt.telas.colagem import parse_colagem
    from app.qt.telas.colagem_dialog import ColagemPreviaDialog
    texto = ("Produto;Preço\n"
             "Óleo de Soja Liza 900ml;7,71\n"
             "Arroz Tio João 5kg;24,90\n"
             "Sabão OMO 1,6kg;3 por R$ 10,00\n"      # promoção
             "Detergente Ypê;2x 5,00\n"              # preço a rever (I2)
             "Refrigerante Kitubaina 1,5L;5,50\n"
             "TOTAL;49,01\n")
    dlg = ColagemPreviaDialog(parse_colagem(texto))
    dlg.setAttribute(DONT, True)
    dlg.resize(620, 460)
    dlg.show()
    _grab(dlg, pasta, "dialogo_colagem_previa.png")
    dlg.reject()

    # --- 2) campo qtd+valor da promoção --------------------------------------
    from app.qt.telas.promocao_dialog import PromocaoDialog
    promo = PromocaoDialog("3 por R$ 10,00")
    promo.setAttribute(DONT, True)
    promo.resize(420, 260)
    promo.show()
    _grab(promo, pasta, "dialogo_promocao.png")
    promo.reject()

    # --- 3) conciliação em TELA CHEIA com a foto ao lado ---------------------
    foto = _tabela_png(pasta / "_fonte_ocr.png")
    itens = [
        ItemMesa("OLEO DE SOJA LIZA 900 ML", "7,71", "VERDE",
                 "Óleo de Soja Liza 900ml"),
        ItemMesa("ARROZ TIO JOAO 5KG", "24,90", "VERDE", "Arroz Tio João 5kg"),
        ItemMesa("REFRIG. KITUBAINA 1500ML", "5,50", "AMARELO",
                 "?", candidato_nome="Refrigerante Kitubaina 1,5L"),
        ItemMesa("DOCE DE BANANA VAL 250 G", "6,66", "VERMELHO",
                 "DOCE DE BANANA VAL 250 G"),
    ]
    res = ResultadoMesa(itens=itens, validade_oferta="ATÉ 20/07",
                        caminho_fonte=foto)
    from app.qt.telas.conciliacao_dialog import ConciliacaoDialog
    tela = ConciliacaoDialog(res)
    tela.setAttribute(DONT, True)
    tela.resize(1180, 640)
    tela.show()
    _grab(tela, pasta, "dialogo_conciliacao_tela_cheia.png")
    tela.done(0)

    # --- 4) a Mesa com badges (promoção/observação) + estatística ------------
    from app.qt.telas.mesa import MesaTela
    mesa = MesaTela()
    prom = ItemMesa("Sabão OMO 1,6kg", None, "VERDE", "Sabão OMO 1,6kg")
    prom.multi_preco = "3 por R$ 10,00"
    obs = ItemMesa("Arroz Tio João 5kg", "24,90", "VERDE", "Arroz Tio João 5kg")
    obs.observacao = "Limite de 2 por cliente"
    mesa._itens = [
        ItemMesa("Óleo de Soja Liza 900ml", "7,71", "VERDE",
                 "Óleo de Soja Liza 900ml"),
        prom, obs,
        ItemMesa("Refrigerante Kitubaina 1,5L", "5,50", "AMARELO",
                 "Refrigerante Kitubaina 1,5L"),
    ]
    mesa._validade = "ATÉ 20/07"
    mesa._recarregar_lista()
    mesa.setAttribute(DONT, True)
    mesa.resize(1280, 760)
    mesa.show()
    _processar()
    _grab(mesa, pasta, "tela_mesa_massa.png")

    # --- 5) planilha da estante (coluna Observação) --------------------------
    from app.qt.telas.planilha_dialog import DialogoPlanilha
    plan = DialogoPlanilha(mesa, mesa)
    plan.setAttribute(DONT, True)
    plan.resize(880, 420)
    plan.show()
    _grab(plan, pasta, "dialogo_planilha.png")
    plan.done(0)

    # --- 6) seletor de frases prontas (papel de texto) -----------------------
    from app.qt.design.papel_texto_ui import _dialogo_cls
    from app.rendering.model import PapelTexto
    Dlg = _dialogo_cls()
    fr = Dlg(None, papel=PapelTexto.LIVRE,
             contexto={"data": "ATÉ 20/07", "evento": "Sexta Verde"})
    fr.setAttribute(DONT, True)
    fr.resize(460, 520)
    fr.show()
    _grab(fr, pasta, "dialogo_frases_prontas.png")
    fr.reject()

    mesa.close()
    _processar()
    # teardown limpo (lei "verde com crash no exit NÃO é verde"): nenhum worker/
    # timer vivo no fim do processo nativo — senão o Windows derruba com 0xC…
    from app.qt.workers import encerrar_todos
    encerrar_todos(espera_ms=1000)
    app.closeAllWindows()
    _processar()
    print(f"Galeria da Fase 7 em {pasta.resolve()}")
    # As fotos já estão no disco (grab().save acima). O teardown NATIVO do Qt no
    # Windows (limpeza de GDI/fontes) às vezes derruba o processo com 0xC…; como
    # não há mais nada a gravar, encerramos de forma determinística — padrão de
    # scripts de captura, não mascara bug de produção (a suíte roda offscreen).
    sys.stdout.flush()
    import os
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
