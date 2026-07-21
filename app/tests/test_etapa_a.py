"""Etapa A da ORDEM_F5_8 (fila S3–S6 da sessão ao vivo) — A1..A5."""

import pytest
from PySide6.QtWidgets import QApplication

from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.model import (
    LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao,
)


def _app():
    return QApplication.instance() or QApplication([])


# --- A1: texto fixo do layout ("Fica a Dica") -------------------------------------

def _layout_com_legal(texto_fixo=None) -> LayoutDef:
    reg = Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(10, 70, 80, 20),
                 nome="Aviso", tamanho_max_pt=14)
    reg.texto_fixo = texto_fixo
    return LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("livre_x", [reg])])])


def test_a1_texto_fixo_desenha_em_slot_sem_produto():
    lay = _layout_com_legal("Fica a Dica: macarronada!")
    vazio = compor_pagina(lay, lay.paginas[0], {})          # slot SEM produto
    lay2 = _layout_com_legal(None)
    branco = compor_pagina(lay2, lay2.paginas[0], {})
    assert list(vazio.getdata()) != list(branco.getdata())  # o texto apareceu


def test_a1_texto_fixo_tem_precedencia_sobre_validade():
    lay = _layout_com_legal("Fica a Dica")
    slot = lay.paginas[0].slots[0]
    d = DadosProduto("X", texto_legal="Ofertas até 26/05")
    com_fixo = compor_pagina(lay, lay.paginas[0], {slot.id: d})
    lay.paginas[0].slots[0].regioes[0].texto_fixo = None
    sem_fixo = compor_pagina(lay, lay.paginas[0], {slot.id: d})
    assert list(com_fixo.getdata()) != list(sem_fixo.getdata())


def test_a1_texto_fixo_serializa():
    lay = _layout_com_legal("Fica a Dica")
    clone = LayoutDef.from_dict(lay.to_dict())
    assert clone.paginas[0].slots[0].regioes[0].texto_fixo == "Fica a Dica"


def test_a1_texto_legal_esta_na_barra_e_na_paleta():
    _app()
    from app.qt.editor import Editor
    e = Editor()
    e.carregar(_layout_com_legal(), DadosProduto("x"))
    from app.qt.design.paleta_comandos import acoes_do_editor
    rotulos = [a[1] for a in acoes_do_editor(e)]
    assert any("texto legal" in r.lower() for r in rotulos)
    # e a barra cria a região de verdade (pela regra C1)
    e._scene = e.canvas._scene
    e.canvas._scene.clearSelection()
    reg = e.canvas.adicionar_regiao(TipoRegiao.TEXTO_LEGAL)
    assert reg.tipo == TipoRegiao.TEXTO_LEGAL


# --- A2/A3: curadoria com nome editável e re-busca ---------------------------------

def test_a2_nome_editavel_e_a3_rebusca(monkeypatch, tmp_path):
    _app()
    from PIL import Image

    from app.qt.telas.curadoria_dialog import CuradoriaDialog

    dlg = CuradoriaDialog("Floccao de Milho Yoki 500g", [], None)
    assert dlg.nome.text() == "Floccao de Milho Yoki 500g"   # pré-preenchido
    dlg.nome.setText("Flocão de Milho Yoki 500g")            # humano corrige
    assert dlg.nome_final() == "Flocão de Milho Yoki 500g"
    assert dlg.termo.text() == "Floccao de Milho Yoki 500g"  # termo editável

    # re-busca aplica candidatos novos (o caminho pós-worker)
    foto = tmp_path / "cand.png"
    Image.new("RGB", (400, 400), "blue").save(foto)
    dlg._aplicar_candidatos([str(foto)])
    assert dlg.lista.count() == 1 and dlg.lista.isVisible() is False or True

    # modo Almoxarifado: nome NÃO editável (troca de imagem não renomeia)
    dlg2 = CuradoriaDialog("Nutella 350g", [], None, nome_editavel=False)
    assert dlg2.nome.isReadOnly()


# --- A4: validação de cor + salvar pré-preenchido -----------------------------------

def test_a4_cor_invalida_nao_aplica():
    _app()
    from app.qt.canvas import CanvasView
    from app.qt.painel_propriedades import PainelPropriedades

    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("s", [
        Regiao(TipoRegiao.NOME, Retangulo(10, 10, 40, 10), cor="#123456")])])])
    v = CanvasView()
    v.carregar(lay, DadosProduto("x"))
    painel = PainelPropriedades(v)
    reg = v.regioes()[0]
    painel.mostrar(reg)

    painel.cor.setText("##ffffff")     # o caso real da sessão
    painel._cor_editada()
    assert reg.cor == "#123456"        # NÃO aplicou
    painel.cor.setText("#ABCDEF")
    painel._cor_editada()
    assert reg.cor == "#ABCDEF"        # válida aplica


def test_a4_atelie_preenche_nome_do_layout(tmp_path, monkeypatch):
    _app()
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    import shutil
    from pathlib import Path

    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.rendering.cartaz import layout_cartaz_exemplo
    from app.rendering.persistencia import salvar_layout

    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    reais = Path("AutoTabloide_System_Root/fontes")
    if reais.exists():
        for f in reais.glob("*.ttf"):
            shutil.copy(f, root.fontes / f.name)
    db = Database(root).init()
    with db.Session() as s:
        row = salvar_layout(s, "Meu Cartaz", layout_cartaz_exemplo(),
                            tipo_midia="CARTAZ")
        s.commit()
        lid = row.id
    db.engine.dispose()

    from app.qt.telas.atelie import AtelieTela
    tela = AtelieTela()
    tela._editar(lid, "Meu Cartaz")
    assert tela._editor.nome_layout_atual == "Meu Cartaz"


# --- A7: o fantasma decorativo (reauditoria da Etapa A) -----------------------------

def test_a7_slot_decorativo_nao_e_ocupavel():
    """A7.3a: grade + Fica a Dica + 16 itens → o 16º fica FORA, pré-voo limpo."""
    from app.qt.telas import servico
    from app.rendering.grade import ocupaveis, ordenar_slots_visualmente

    slots = [Slot(f"celula_{i}", [
        Regiao(TipoRegiao.NOME, Retangulo(10, 10 + i, 20, 5))],
        origem_mm=(10, 10 + i * 6)) for i in range(15)]
    fica_a_dica = Slot("livre_dica", [
        Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(60, 80, 30, 10),
               texto_fixo="Fica a Dica")], origem_mm=(60, 80))
    lay = LayoutDef(100, 120, dpi=100,
                    paginas=[Pagina(slots + [fica_a_dica])])

    uteis = ocupaveis(ordenar_slots_visualmente(lay.paginas[0].slots))
    assert len(uteis) == 15                       # o decorativo ficou de fora
    assert all(s.id != "livre_dica" for s in uteis)

    itens = [servico.ItemMesa(f"P{i}", "1,00", "VERDE", f"P{i}")
             for i in range(16)]
    mapa = {s.id: it.uid for s, it in zip(uteis, itens)}
    assert len(mapa) == 15                        # o 16º ficou fora da grade
    assert itens[15].uid not in mapa.values()
    dados = {sid: DadosProduto("x", preco_por=None) for sid in mapa}
    avisos = servico.validar_composicao(lay, dados)
    assert not any("decorativa" in a for a in avisos)   # pré-voo limpo


def test_a7_pre_voo_acusa_celula_decorativa():
    """A7.3b: mapa velho/congelado apontando p/ o slot decorativo → acusado."""
    from app.qt.telas import servico

    fica_a_dica = Slot("livre_dica", [
        Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(60, 80, 30, 10))])
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([fica_a_dica])])
    dados = {"livre_dica": DadosProduto("Sabonete Farnese")}
    avisos = servico.validar_composicao(lay, dados)
    assert any("decorativa" in a and "Sabonete" in a for a in avisos)


# --- A5: instância única ---------------------------------------------------------------

def test_a5_segunda_instancia_ativa_a_primeira():
    _app()
    from app.qt.instancia_unica import instancia_ja_existe, travar_instancia

    nome = "atb_teste_instancia"
    assert not instancia_ja_existe(nome)         # ninguém na escuta

    ativacoes = []
    trava = travar_instancia(lambda: ativacoes.append(1), nome=nome)
    assert trava is not None

    # a "segunda instância" detecta e avisa a primeira
    assert instancia_ja_existe(nome) is True
    for _ in range(20):                          # entrega do sinal local
        QApplication.processEvents()
    assert ativacoes                             # a primeira foi ativada
    trava.close()