"""
Passe de POLIMENTO pré-F12 — testes
===================================
A dívida de UI das F4–F11 fechada com prova: cada casca nova construída sobre
o modelo selado é exercitada aqui (fluxo real, por conteúdo — nunca só "não
deu exceção"). A lógica selada NÃO muda: estes testes chamam os mesmos
serviços que a suíte das fases já cobre.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.tests import seeds_portabilidade as seeds


@pytest.fixture()
def raiz_env(tmp_path, monkeypatch):
    root = seeds.raiz(tmp_path, "raiz")
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(root.raiz))
    return root


def _app():
    return QApplication.instance() or QApplication([])


# --- R-075: fusão de duplicatas (a UI que faltava da F9) ---------------------------

def test_duplicatas_fluxo_completo(raiz_env):
    """Par achado por chave forte → diálogo lado a lado → fundir → o repetido
    some (lixeira) e o alias migra. Marca diferente nunca vira par."""
    _app()
    from app.qt.telas import servico
    from app.qt.telas.duplicatas_dialog import DuplicatasDialog
    seeds.add_produto(raiz_env, "Arroz 5kg", "Camil", "24.90",
                      foto=seeds.png("#f00"))
    seeds.add_produto(raiz_env, "Arroz 5kg", "Camil", "19.90")
    seeds.add_produto(raiz_env, "Arroz 5kg", "Tio João", "22.90")  # OUTRA marca

    pares = servico.pares_duplicatas()
    assert len(pares) == 1                       # a marca diferente NÃO é par
    assert pares[0]["motivo"] == "mesmo nome e marca"

    dlg = DuplicatasDialog(pares)
    escolhidos = dlg.escolhidos()
    assert escolhidos and escolhidos[0][0] < escolhidos[0][1]   # fica o antigo
    resumo = servico.fundir_duplicatas(escolhidos)
    assert resumo["fundidos"] == 1 and resumo["aliases"] >= 1
    assert servico.pares_duplicatas() == []       # acervo limpo
    dlg.close()


def test_duplicatas_dialog_vazio_tem_estado():
    """Sem pares, o diálogo mostra o estado vazio (craft) e o Ok desabilita."""
    _app()
    from PySide6.QtWidgets import QDialogButtonBox

    from app.qt.design.componentes import EstadoVazio
    from app.qt.telas.duplicatas_dialog import DuplicatasDialog
    dlg = DuplicatasDialog([])
    assert dlg.findChild(EstadoVazio) is not None
    ok = dlg.findChild(QDialogButtonBox).button(
        QDialogButtonBox.StandardButton.Ok)
    assert not ok.isEnabled()
    dlg.close()


# --- R-083/R-084: estilo da dica + manchetes (F9) ----------------------------------

def test_painel_tem_seletor_de_estilo_da_dica():
    """O combo de estilo existe e carrega os 3 tons do motor (a F9 os deixou
    prontos; a UI nunca os oferecia)."""
    _app()
    from app.ai.enriquecimento import ESTILOS_DICA
    from app.qt.canvas import CanvasView
    from app.qt.painel_propriedades import PainelPropriedades
    p = PainelPropriedades(CanvasView())
    dados = {p.estilo_dica.itemData(i)
             for i in range(p.estilo_dica.count())}
    assert dados == set(ESTILOS_DICA)


def test_manchetes_degradam_sem_ia():
    """R-084: sem IA, `sugerir_manchetes` devolve a lista padrão com o evento —
    o botão do diálogo de papel sempre entrega algo útil (I2)."""
    from app.ai.enriquecimento import sugerir_manchetes
    lista = sugerir_manchetes("Quintou", None)
    assert len(lista) >= 3
    assert any("Quintou" in m for m in lista)


def test_dialogo_papel_tem_manchetes():
    _app()
    from app.qt.design.papel_texto_ui import _dialogo_cls
    from app.rendering.model import PapelTexto
    dlg = _dialogo_cls()(None, papel=PapelTexto.LIVRE,
                         contexto={"evento": "Quintou"})
    assert dlg.btn_manchetes.isVisibleTo(dlg)     # papel LIVRE mostra o botão
    dlg.selecionar(PapelTexto.VALIDADE)
    assert not dlg.btn_manchetes.isVisibleTo(dlg)  # os outros papéis não
    dlg.close()


# --- Polimento F11: meta na barra, relâmpago com opções ----------------------------

def test_meta_do_evento_aparece_na_barra(raiz_env):
    """R-122 vivo: com meta definida, a barra mostra o pulso "N/meta"."""
    _app()
    from app.qt.telas import inteligencia
    from app.qt.telas.mesa import MesaTela
    from app.qt.telas.servico import ItemMesa
    inteligencia.definir_meta_evento("Quintou", 3)
    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    m.show()
    m._evento = "Quintou"
    m._itens = [ItemMesa("A", "1,00", "VERDE", "A"),
                ItemMesa("B", "2,00", "VERDE", "B")]
    m._atualizar_estatistica()
    assert m._estatistica_lbl.text() == "2/3"
    m.close()


def test_relampago_dialog_qr_e_etiquetas():
    """O diálogo de opções entrega o que o serviço sempre aceitou: QR
    (desligado por padrão) e nº de etiquetas do kit."""
    _app()
    from app.qt.telas.relampago_dialog import RelampagoDialog
    dlg = RelampagoDialog("Café", kit=True)
    assert dlg.qr() is None                      # QR desligado por padrão
    dlg.com_qr.setChecked(True)
    dlg.qr_texto.setText("https://loja.com/encarte")
    dlg.etiquetas.setValue(4)
    assert dlg.qr() == "https://loja.com/encarte"
    assert dlg.n_etiquetas() == 4
    dlg.close()
    # auditoria: o acervo não guarda o "de" — o diálogo coleta de/por (o
    # "por" vem preenchido do produto; o "de" é do dono)
    dlg3 = RelampagoDialog("Café", preco_por="9,99")
    assert dlg3.precos() == ("9,99", None)
    dlg3.preco_de.setText("12,99")
    assert dlg3.precos() == ("9,99", "12,99")
    dlg3.close()
    # fora do kit, etiquetas não contam
    dlg2 = RelampagoDialog("Café", kit=False)
    assert dlg2.n_etiquetas() == 1
    dlg2.close()


# --- Polimento F6: colar preços + categoria em massa no modo planilha --------------

def _mesa_com_itens(itens):
    from app.qt.telas.mesa import MesaTela
    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    m.show()
    m._itens = itens
    return m


def test_planilha_colar_atualiza_precos_pelo_nome(raiz_env):
    """Ctrl+V com nome×preço ATUALIZA o item CERTO (casado por nome, nunca por
    posição); sem par avisa; ambíguo ("2x 5,00") não grava (P0.3/I2)."""
    _app()
    from app.qt.telas.planilha_dialog import DialogoPlanilha
    from app.qt.telas.servico import ItemMesa
    m = _mesa_com_itens([
        ItemMesa("Arroz 5kg", "24,90", "VERDE", "Arroz 5kg"),
        ItemMesa("Café 500g", "9,90", "VERDE", "Café 500g"),
    ])
    dlg = DialogoPlanilha(m, m)
    QApplication.clipboard().setText(
        "Café 500g\t8,49\nProduto Fantasma\t1,00\nArroz 5kg\t2x 5,00")
    dlg._colar_tabela()
    assert m._itens[1].preco == "8,49"           # o Café atualizou
    assert m._itens[0].preco == "24,90"          # o ambíguo NÃO gravou (P0.3)
    # a grade refletiu por conteúdo
    col_preco = 2
    from app.qt.telas import planilha as L
    col_preco = L.COLUNAS.index("Preço")
    assert dlg.tab.item(1, col_preco).text() == "8,49"
    dlg.close()
    m.close()


def test_planilha_categoria_em_massa(raiz_env):
    """A aplicação em massa reusa aplicar_edicao linha a linha (mesma decisão
    da célula única) e reflete na grade."""
    _app()
    from app.qt.telas import planilha as L
    from app.qt.telas.planilha_dialog import DialogoPlanilha
    from app.qt.telas.servico import ItemMesa
    m = _mesa_com_itens([
        ItemMesa("Arroz", "1,00", "VERDE", "Arroz"),
        ItemMesa("Feijão", "2,00", "VERDE", "Feijão"),
        ItemMesa("Sabão", "3,00", "VERDE", "Sabão"),
    ])
    dlg = DialogoPlanilha(m, m)
    col_cat = L.COLUNAS.index("Categoria")
    # aplica direto pela mesma rotina que o menu usa (sem abrir o QMenu)
    for lin in (0, 1):
        L.aplicar_edicao(m._itens[lin], "Categoria", "Mercearia")
        dlg._repor(lin, col_cat, dlg._texto_celula(m._itens[lin], "Categoria"))
    m.refletir_planilha()
    assert m._itens[0].categoria == "Mercearia"
    assert m._itens[1].categoria == "Mercearia"
    assert m._itens[2].categoria is None         # a não selecionada intacta
    assert dlg.tab.item(0, col_cat).text() == "Mercearia"
    dlg.close()
    m.close()


# --- Consistência: tokens no lugar de cor fixa -------------------------------------

def test_sem_perigo_suave_fantasma(raiz_env):
    """Reescrito no GATE 2.4 da ordem F11.5 (só checava ausência de string):
    a célula-problema resolve POR CONTEÚDO para o PERIGO_FUNDO do TEMA — no
    escuro, o vinho #331414 (não um rosa claro fixo). Prova de mutação:
    hardcodear qualquer hex claro na célula faz o name() divergir e falhar."""
    from PySide6.QtWidgets import QApplication

    from app.qt.design import tokens as t
    from app.qt.design.tema import aplicar_tema
    from app.qt.telas.planilha_dialog import DialogoPlanilha
    from app.qt.telas import planilha as L
    from app.qt.telas.servico import ItemMesa
    app = _app()
    aplicar_tema(app, "escuro")
    try:
        assert t.PERIGO_FUNDO.upper() == "#331414"      # o token do escuro
        m = _mesa_com_itens([ItemMesa("Sem preço", None, "VERDE", "Sem preço")])
        dlg = DialogoPlanilha(m, m)
        cel = dlg.tab.item(0, L.COLUNAS.index("Preço"))
        cor = cel.background().color().name().upper()
        assert cor == "#331414", cor                     # o PERIGO_FUNDO real
        dlg.close()
        m.close()
    finally:
        aplicar_tema(app, "claro")
    # bônus: a string fantasma segue banida do código
    from pathlib import Path as _P
    telas = _P(__file__).resolve().parents[1] / "qt" / "telas"
    for nome in ("planilha_dialog.py", "colagem_dialog.py"):
        texto = (telas / nome).read_text(encoding="utf-8")
        assert "#FDE8E8" not in texto, nome
        assert "PERIGO_SUAVE" not in texto, nome


# --- Polimento F10: ajuste de imagem, acervo, comparador ---------------------------

def test_ajuste_imagem_por_conteudo(tmp_path):
    """Girar muda a orientação DE VERDADE (por conteúdo: o canto marcado
    muda de lugar); reiniciar volta ao original; o corte por seleção mapeia
    widget→imagem. Original em disco intocada (não-destrutivo)."""
    from PIL import Image
    from PySide6.QtCore import QRect

    from app.images import curadoria
    from app.qt.telas.ajuste_imagem_dialog import AjusteImagemDialog
    _app()
    foto = tmp_path / "f.png"
    base = Image.new("RGB", (200, 100), "white")
    base.paste(Image.new("RGB", (50, 50), (220, 30, 30)), (0, 0))
    base.save(foto)
    antes = foto.read_bytes()

    dlg = AjusteImagemDialog(str(foto))
    assert dlg.imagem_final().size == (200, 100)
    dlg._aplicar(curadoria.girar, 90)
    girada = dlg.imagem_final()
    assert girada.size == (100, 200)
    # horário: o canto vermelho (topo-esq) vai para o topo-DIREITO
    assert girada.convert("RGB").getpixel((95, 5))[0] > 150
    dlg._reiniciar()
    assert dlg.imagem_final().size == (200, 100)
    # corte por seleção: seleciona a metade esquerda da prévia
    dlg._repintar()
    pm = dlg.previa.pixmap()
    off_x = (dlg.previa.width() - pm.width()) // 2
    off_y = (dlg.previa.height() - pm.height()) // 2
    dlg.previa.selecao = QRect(off_x, off_y, pm.width() // 2, pm.height())
    dlg._cortar()
    assert dlg.imagem_final().width == pytest.approx(100, abs=3)
    assert foto.read_bytes() == antes           # o disco não foi tocado
    dlg.close()


def test_acervo_picker_lista_e_filtra(raiz_env):
    _app()
    from app.qt.telas.acervo_picker_dialog import AcervoPickerDialog
    seeds.add_produto(raiz_env, "Arroz 5kg", "Camil", "9.90",
                      foto=seeds.png("#f00"))
    seeds.add_produto(raiz_env, "Café 500g", "Pilão", "8.90",
                      foto=seeds.png("#00f"))
    seeds.add_produto(raiz_env, "Sem Foto", "X", "1.00")   # não aparece
    dlg = AcervoPickerDialog()
    assert dlg.lista.count() == 2
    dlg.busca.setText("café")
    assert dlg.lista.count() == 1
    dlg.lista.setCurrentRow(0)
    dlg._usar()
    assert dlg.caminho and Path(dlg.caminho).exists()
    dlg.close()


def test_historico_dialog_tem_comparador(raiz_env):
    """O histórico agora compara lado a lado (atual × escolhida)."""
    _app()
    from app.qt.telas.almoxarifado import HistoricoImagensDialog
    pid = seeds.add_produto(raiz_env, "Arroz", "Camil", "9.90",
                            foto=seeds.png("#f00"))
    from app.images.biblioteca import BibliotecaImagens
    from app.core.paths import SystemRoot
    import tempfile as _tf
    bib = BibliotecaImagens(SystemRoot().biblioteca_imagens)
    nova = Path(_tf.mkdtemp()) / "n.png"
    nova.write_bytes(seeds.png("#0f0"))
    bib.ingerir(pid, str(nova))                  # a antiga vira versão
    dlg = HistoricoImagensDialog(pid)
    assert dlg.lista.count() == 1                # 1 versão no histórico
    assert dlg._foto_atual.pixmap() is not None  # a atual já aparece
    dlg.lista.setCurrentRow(0)
    assert dlg._foto_sel.pixmap() is not None    # a escolhida espelha
    dlg.close()


def test_importar_planilha_dialog_pt_br(raiz_env, tmp_path):
    """O botão do diálogo de import não sai mais "Cancel" em inglês."""
    _app()
    from PySide6.QtWidgets import QDialogButtonBox

    from app.core import excel_acervo as X
    from app.qt.telas.importar_planilha_dialog import ImportarPlanilhaDialog
    seeds.add_produto(raiz_env, "Arroz", "Camil", "9.90")
    xlsx = X.exportar_acervo_xlsx(tmp_path / "a.xlsx", raiz=raiz_env)
    dlg = ImportarPlanilhaDialog(X.analisar_planilha(xlsx, raiz=raiz_env))
    caixa = dlg.findChild(QDialogButtonBox)
    textos = {b.text() for b in caixa.buttons()}
    assert "Cancelar" in textos and "Importar" in textos
    assert "Cancel" not in textos
    dlg.close()
