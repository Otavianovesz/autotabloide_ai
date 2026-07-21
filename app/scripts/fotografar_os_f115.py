"""Galeria NATIVA da ORDEM DE SERVIÇO F11.5 (prova visual para a reauditoria).

Fotografa cada tela/diálogo NOVO da ordem, em tema claro e escuro: o diff da
edição, as correções aprendidas, o pincel de refino, a prévia antes/depois do
Estúdio, a fila de importação multi-arquivo, a conciliação com "Aceitar
verdes" + o painel da fila de IA, o Publicar com a seleção/ordem do carrossel
e a limitação honesta, o medidor de densidade na Mesa, as Configurações
(sinônimos/correções na aba de IA; WebP/gerador/perfis na de imagens) — e,
bônus pós-ordem, o MODO DE ISOLAMENTO no editor (véu + chip).

SEM offscreen de propósito (o offscreen renderiza glifos como caixas); janelas
com WA_DontShowOnScreen — nada pisca. Rodar::

    python -m app.scripts.fotografar_os_f115 saida_os_f115/claro
    python -m app.scripts.fotografar_os_f115 saida_os_f115/escuro --tema=escuro
"""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timedelta
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


def _foto_produto(caminho: Path, cor, lado: int = 240) -> str:
    """Um 'produto' RGBA com fundo transparente (packshot de mentira)."""
    from PIL import Image
    im = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    for x in range(30, lado - 30):
        for y in range(20, lado - 20):
            im.putpixel((x, y), (*cor, 255))
    im.save(caminho)
    return str(caminho)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pasta = Path(args[0] if args else "saida_os_f115/claro")
    tema = next((a.split("=", 1)[1] for a in sys.argv[1:]
                 if a.startswith("--tema=")), None)

    # raiz TEMPORÁRIA semeada (nunca o acervo vivo)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
    import seeds_portabilidade as seeds
    tmp = Path(tempfile.mkdtemp(prefix="os_f115_"))
    root = seeds.raiz(tmp, "raiz")
    os.environ["AUTOTABLOIDE_ROOT"] = str(root.raiz)
    # as FONTES reais da bancada (sem elas o Pillow rasteriza acento como
    # caixa — a galeria é prova de BELEZA, precisa das fontes de verdade)
    import shutil
    reais = Path("AutoTabloide_System_Root/fontes")
    if reais.exists():
        for f in reais.glob("*.ttf"):
            shutil.copy(f, root.fontes / f.name)
    pid_arroz = seeds.add_produto(root, "Arroz Tio João 5kg", "Tio João",
                                  "24.90", foto=seeds.png("#C0392B"),
                                  categoria="Mercearia")
    seeds.add_produto(root, "Café Pilão 500g", "Pilão", "9.90",
                      foto=seeds.png("#2C3E50"), categoria="Mercearia")
    seeds.add_produto(root, "Detergente Ypê 500ml", "Ypê", "1.99",
                      foto=seeds.png("#27AE60"), categoria="Limpeza")

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from app.qt.design.tema import aplicar_tema
    app = QApplication.instance() or QApplication([])
    aplicar_tema(app, tema) if tema else aplicar_tema(app)
    from app.qt.design.polimento import instalar_polimento
    instalar_polimento(app)
    DONT = Qt.WidgetAttribute.WA_DontShowOnScreen

    from app.qt.telas import servico
    from app.qt.telas.servico import ItemMesa

    # --- 1) diff da edição (R-062) -------------------------------------------
    ant = [ItemMesa("x", "10,00", "VERDE", "Arroz Tio João 5kg", ean="111"),
           ItemMesa("x", "5,00", "VERDE", "Feijão Kicaldo 1kg", ean="222"),
           ItemMesa("x", "7,50", "VERDE", "Óleo Soya 900ml", ean="444")]
    atu = [ItemMesa("x", "12,00", "VERDE", "Arroz Tio João 5kg", ean="111"),
           ItemMesa("x", "6,80", "VERDE", "Óleo Soya 900ml", ean="444"),
           ItemMesa("x", "18,00", "VERDE", "Café Pilão 500g", ean="333")]
    from app.qt.telas.diff_dialog import DiffEdicaoDialog
    dlg = DiffEdicaoDialog(servico.diff_edicoes(atu, ant))
    dlg.setAttribute(DONT, True)
    dlg.show()
    _grab(dlg, pasta, "diff_da_edicao.png")
    dlg.close()

    # --- 2) correções aprendidas (aliases reais do banco) --------------------
    from app.core.database import Database
    from app.core.repositories import ProdutoRepositorio
    db = Database(root).init()
    try:
        with db.Session() as s:
            rep = ProdutoRepositorio(s)
            rep._garantir_alias(pid_arroz, "ARROZ TP1 TIO JOAO 5KG")
            rep._garantir_alias(pid_arroz, "ARROZ T JOAO 5 KG PCT")
            s.commit()
    finally:
        db.engine.dispose()
    from app.qt.telas.correcoes_dialog import CorrecoesDialog
    dlg = CorrecoesDialog()
    dlg.setAttribute(DONT, True)
    dlg.show()
    _grab(dlg, pasta, "correcoes_aprendidas.png")
    dlg.close()

    # --- 3) pincel de refino (com um traço de apagar aplicado) ---------------
    recorte = _foto_produto(tmp / "recorte.png", (192, 57, 43))
    from app.qt.telas.refino_dialog import RefinoDialog
    dlg = RefinoDialog(recorte)
    dlg.setAttribute(DONT, True)
    dlg.raio.setValue(22)
    dlg.rb_apagar.setChecked(True)
    dlg.pintar([(60, 60), (80, 62), (100, 66)])     # a sobra "apagada"
    dlg.show()
    _grab(dlg, pasta, "refino_pincel.png")
    dlg.close()

    # --- 4) prévia antes/depois do Estúdio (sombra do TEMA) ------------------
    from PIL import Image

    from app.images.estudio import packshot_degrau1
    crua = tmp / "crua.png"
    im = Image.new("RGB", (300, 300), (210, 200, 185))   # "foto de celular"
    for x in range(60, 240):
        for y in range(40, 260):
            im.putpixel((x, y), (192, 57, 43))
    im.save(crua)
    pack = packshot_degrau1(Image.open(_foto_produto(tmp / "p.png",
                                                     (192, 57, 43))),
                            remover_fundo=lambda i: i,
                            tema=tema or "claro")
    depois = tmp / "packshot.png"
    pack.save(depois)
    from app.qt.telas.previa_estudio_dialog import PreviaEstudioDialog
    dlg = PreviaEstudioDialog(str(crua), str(depois))
    dlg.setAttribute(DONT, True)
    dlg.show()
    _grab(dlg, pasta, "estudio_antes_depois.png")
    dlg.close()

    # --- 5) fila de importação multi-arquivo (estados vivos) -----------------
    from app.qt.telas.fila_importacao import FilaImportacaoDialog
    dlg = FilaImportacaoDialog(["ofertas_terca.png", "jornal_do_mes.jpg",
                                "hortifruti.txt", "acougue.txt"])
    dlg.setAttribute(DONT, True)
    dlg.atualizar("ofertas_terca.png", "pronto")
    dlg.atualizar("jornal_do_mes.jpg", "erro")
    dlg.atualizar("hortifruti.txt", "lendo")
    dlg.show()
    _grab(dlg, pasta, "fila_importacao.png")
    dlg.close()

    # --- 6) conciliação: Aceitar verdes + painel da fila de IA ---------------
    from app.qt.telas.conciliacao_dialog import ConciliacaoDialog
    from app.qt.telas.servico import ResultadoMesa
    itens = [ItemMesa("ARROZ TP1 TIO JOAO 5KG", "19,90", "VERDE",
                      "Arroz Tio João 5kg", produto_id=pid_arroz),
             ItemMesa("CAFE PILAO TRAD 500G", "8,49", "VERDE",
                      "Café Pilão 500g", produto_id=2),
             ItemMesa("DETERG YPE CLEAR 500", "1,99", "AMARELO",
                      "Detergente Ypê 500ml",
                      candidato_nome="Detergente Ypê 500ml")]
    dlg = ConciliacaoDialog(ResultadoMesa(
        itens=itens, validade_oferta="OFERTA VÁLIDA SOMENTE 21/07"))
    dlg.setAttribute(DONT, True)
    dlg._fila_mudou("u1", "enriquecendo “DETERG YPE CLEAR 500”")
    dlg.show()
    dlg.resize(980, 480)
    _grab(dlg, pasta, "conciliacao_verdes_e_fila_ia.png")
    dlg.done(0)

    # --- 7) Publicar: carrossel selecionável + limitação honesta -------------
    from app.qt.telas.mesa import MesaTela
    m = MesaTela()
    m.setAttribute(DONT, True)
    m.show()
    m._itens = [
        ItemMesa("x", "19,90", "VERDE", "Arroz Tio João 5kg",
                 categoria="Mercearia"),
        ItemMesa("x", "8,49", "VERDE", "Café Pilão 500g",
                 categoria="Mercearia"),
        ItemMesa("x", "1,99", "VERDE", "Detergente Ypê 500ml",
                 categoria="Limpeza"),
    ]
    m._recarregar_lista()
    from app.qt.telas.publicar_dialog import PublicarDialog
    dlg = PublicarDialog(m)
    dlg.setAttribute(DONT, True)
    dlg.rb_carrossel.setChecked(True)
    dlg.show()
    _grab(dlg, pasta, "publicar_carrossel_limitacao.png")
    dlg.close()

    # --- 8) medidor de densidade na barra da Mesa ----------------------------
    from app.rendering.compositor import DadosProduto
    from app.rendering.model import (
        Ajuste, LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao)
    slots = [Slot(f"c{i}", [
        Regiao(TipoRegiao.IMAGEM, Retangulo(8 + i * 64, 10, 52, 50),
               ajuste=Ajuste.PREENCHER),
        Regiao(TipoRegiao.NOME, Retangulo(8 + i * 64, 62, 52, 8)),
        Regiao(TipoRegiao.PRECO, Retangulo(8 + i * 64, 71, 52, 10)),
    ], origem_mm=(8 + i * 64, 10)) for i in range(3)]
    lay = LayoutDef(210, 95, dpi=96, paginas=[Pagina(slots)])
    m._layout = lay
    dados = {f"c{i}": DadosProduto(it.nome, imagem_path=None)
             for i, it in enumerate(m._itens)}
    m.area.canvas.carregar(lay, dados)
    m.area.canvas.mapa.update({"c0": m._itens[0].uid, "c1": m._itens[1].uid})
    m._atualizar_densidade()
    m.resize(1500, 800)
    _processar()
    _grab(m._barra_mesa, pasta, "mesa_medidor_densidade.png")
    m.close()

    # --- 9) Configurações: IA (sinônimos/correções) e Imagens (WebP/gerador) -
    from app.qt.telas.configuracoes import ConfiguracoesTela
    cfg = ConfiguracoesTela()
    cfg.setAttribute(DONT, True)
    cfg.show()
    cfg.resize(1280, 780)
    cfg.campo_sinonimos.setPlainText("mandioca, macaxeira, aipim\n"
                                     "tangerina, mexerica, bergamota")

    def _ir_para_aba(trecho: str) -> None:
        for i in range(cfg.lista_abas.count()):
            if trecho.lower() in cfg.lista_abas.item(i).text().lower():
                cfg.lista_abas.setCurrentRow(i)
                return

    _ir_para_aba("ia")
    _grab(cfg, pasta, "config_ia_sinonimos_correcoes.png")
    _ir_para_aba("imagens")
    _grab(cfg, pasta, "config_imagens_webp_gerador_perfis.png")
    cfg.close()

    # --- 10) perfis de exportação (a tela nova) ------------------------------
    from app.qt.telas.perfis_dialog import PerfisDialog
    dlg = PerfisDialog()
    dlg.setAttribute(DONT, True)
    dlg.show()
    _grab(dlg, pasta, "perfis_exportacao.png")
    dlg.close()

    # --- 11) BÔNUS pós-ordem: modo de isolamento (véu + chip) ----------------
    from app.qt.canvas import CanvasView
    from app.rendering.grade import propagar_mestre
    regs = [Regiao(TipoRegiao.IMAGEM, Retangulo(10, 8, 42, 40),
                   ajuste=Ajuste.PREENCHER, nome="Foto"),
            Regiao(TipoRegiao.NOME, Retangulo(10, 50, 42, 8), nome="Nome"),
            Regiao(TipoRegiao.PRECO, Retangulo(10, 59, 42, 12), nome="Preço")]
    for r in regs:
        r.de_mestre = True
    lay_iso = LayoutDef(180, 90, dpi=96, paginas=[Pagina([
        Slot("celula_m", regs, mestre=True, origem_mm=(10, 8)),
        Slot("celula_c", ref_grupo="celula_m", origem_mm=(70, 8)),
        Slot("solta", [Regiao(TipoRegiao.NOME, Retangulo(132, 8, 38, 8),
                              nome="Título")]),
    ])])
    propagar_mestre(lay_iso.paginas[0])
    cv = CanvasView()
    cv.setAttribute(DONT, True)
    foto = _foto_produto(tmp / "iso.png", (41, 128, 185))
    cv.carregar(lay_iso, {"celula_m": DadosProduto("Arroz Tio João 5kg",
                                                   imagem_path=foto),
                          "celula_c": DadosProduto("Café Pilão 500g",
                                                   imagem_path=foto)})
    cv.resize(1100, 640)
    cv.show()
    cv.ajustar()
    cv.isolar_por_duplo_clique(regs[0])          # o grupo…
    cv.isolar_por_duplo_clique(regs[0])          # …e a célula (véu + chip)
    _processar()
    _grab(cv, pasta, "isolamento_celula_veu_chip.png")
    cv.sair_isolamento(tudo=True)
    cv.close()

    print(f"galeria em {pasta}")
    # teardown nativo do Qt no Windows derruba o processo DEPOIS dos arquivos
    from app.qt.workers import encerrar_todos
    encerrar_todos(espera_ms=1000)
    app.closeAllWindows()
    _processar()
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
