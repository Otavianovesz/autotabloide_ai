"""ORDEM F13-DECIMUS — a validade se resolve SOZINHA.

O P-01/P-02 do dossiê: a automação da validade existia e nunca
disparava para o dono, porque dependia de um Evento cadastrado que ele
não tem motivo para conhecer. A resposta estava no nome do arquivo:
"Segunda dos Frios" É segunda-feira. D1: a cascata ganha o NOME DO
LAYOUT. D2: o chip permanente. D3: a mensagem diz onde. D4: guardas.
"""

from datetime import date
from pathlib import Path

import pytest

_PACOTE = Path(__file__).resolve().parents[2] / "Templates novos"


def _requer_pacote():
    if not _PACOTE.exists():
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")


def _app():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.tests import acervo
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    acervo.copiar_fontes_reais(root.fontes)
    Database(root).init().engine.dispose()
    return root


# ---------------------------------------------------------------------------
# D1 — o encarte sabe que dia ele é
# ---------------------------------------------------------------------------


def test_d1_dia_pelo_nome_casa_por_palavra_inteira():
    """D1: o dia da semana escrito no NOME do layout — radical, sem
    acento e sem caixa, POR PALAVRA INTEIRA (a disciplina do
    extrair_marca: ambíguo fica None; "Promoção Relâmpago" nunca vira
    segunda-feira por conter 'ão')."""
    from app.qt.telas.servico import PERIODO_MES, dia_pelo_nome

    assert dia_pelo_nome("Segunda dos Frios") == 0
    assert dia_pelo_nome("Terça do Pão") == 1
    assert dia_pelo_nome("terca do pao") == 1          # sem acento/caixa
    assert dia_pelo_nome("Quarta das Ofertas") == 2
    assert dia_pelo_nome("Quinta do Peixe") == 3
    assert dia_pelo_nome("Quintou do Real") == 3       # o radical quintou
    assert dia_pelo_nome("Sexta Verde") == 4
    assert dia_pelo_nome("Sábado da Carne") == 5
    assert dia_pelo_nome("Jornal do Mês") == PERIODO_MES
    # a guarda do falso positivo: palavra INTEIRA, nunca pedaço
    assert dia_pelo_nome("Promoção Relâmpago") is None
    assert dia_pelo_nome("Tabloide Belo Brasil") is None
    assert dia_pelo_nome("Terceirizados") is None      # "ter" só inteiro
    assert dia_pelo_nome("") is None


def test_d1_a_cascata_no_sugerir_validade(raiz_tmp):
    """D1: SEM evento cadastrado e SEM config, o nome do layout basta —
    e a data é a PRÓXIMA ocorrência contando hoje (nunca no passado).
    Nota L6: a regra do §2 manda ("se hoje é segunda, a validade é
    hoje") — a tabela ilustrativa do §1 foi computada de amanhã."""
    from app.qt.telas.servico import sugerir_validade

    seg = date(2026, 7, 27)                       # segunda-feira
    assert sugerir_validade("Segunda dos Frios", seg) == "SOMENTE 27/07"
    assert sugerir_validade("Terça do Pão", seg) == "SOMENTE 28/07"
    assert sugerir_validade("Sábado da Carne", seg) == "SOMENTE 01/08"
    # de um sábado, a segunda é depois de amanhã
    sab = date(2026, 7, 25)
    assert sugerir_validade("Segunda dos Frios", sab) == "SOMENTE 27/07"
    # o período do Jornal: o mês corrente enquanto o dia 27 não passou
    assert sugerir_validade("Jornal do Mês", date(2026, 7, 20)) == \
        "DE 01/07 A 27/07"
    assert sugerir_validade("Jornal do Mês", date(2026, 7, 28)) == \
        "DE 01/08 A 27/08"
    # dezembro vira para janeiro sem quebrar
    assert sugerir_validade("Jornal do Mês", date(2026, 12, 30)) == \
        "DE 01/01 A 27/01"
    # sem palavra de dia: sem palpite (o contrato antigo fica)
    assert sugerir_validade("Avulsos", seg) is None


def test_d1_o_evento_cadastrado_continua_mandando(raiz_tmp):
    """D1: a cascata NÃO destrona o que existe — evento com dia_semana
    vence o nome do layout (um 'Sexta Verde' cadastrado como quinta
    manda a quinta)."""
    from app.core.database import Database
    from app.qt.telas import eventos
    from app.qt.telas.servico import sugerir_validade

    db = Database().init()
    with db.Session() as s:
        ev = eventos.criar_evento(s, "Sexta Verde", dia_semana=3)
        s.commit()
        assert ev.dia_semana == 3
    db.engine.dispose()
    sab = date(2026, 7, 18)
    assert sugerir_validade("Sexta Verde", sab) == "SOMENTE 23/07", \
        "o evento cadastrado deixou de mandar (a cascata inverteu)"


def test_d1_abrir_o_layout_preenche_a_validade(raiz_tmp):
    """§6 (o teste de aceitação): carregar o layout na Mesa já preenche
    a validade — SEM evento cadastrado, sem clique nenhum."""
    from app.qt.telas.mesa import MesaTela
    from app.qt.telas.servico import proxima_ocorrencia
    from app.rendering.model import LayoutDef, Pagina, Slot
    _app()
    m = MesaTela()
    try:
        lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("c", [])])])
        m.carregar_layout(lay, None, nome_layout="Segunda dos Frios")
        esperado = proxima_ocorrencia(0).strftime("%d/%m")
        assert m._validade == f"SOMENTE {esperado}", (
            f"a validade não nasceu sozinha: {m._validade!r}")
        # e uma validade JÁ definida nunca é sobrescrita em silêncio
        m._validade = "ATÉ 30/09"
        m.carregar_layout(lay, None, nome_layout="Terça do Pão")
        assert m._validade == "ATÉ 30/09"
    finally:
        m.close()


# ---------------------------------------------------------------------------
# D2 — o chip permanente
# ---------------------------------------------------------------------------


def test_d2_o_chip_e_permanente_e_nunca_nasce_vazio(raiz_tmp):
    """D2: o campo invisível era um segredo (P-02). O chip é SEMPRE
    visível: com data mostra a data; sem data convida ao clique — e
    fica em cor de alerta."""
    from app.qt.telas.mesa import MesaTela
    _app()
    m = MesaTela()
    try:
        assert m._validade_lbl.text().strip(), \
            "o chip nasceu vazio — o segredo do P-02 continua"
        assert "clique" in m._validade_lbl.text().lower()
        assert m._validade_lbl.property("alerta"), \
            "sem data o chip tem de estar em alerta"
        m._validade = "SOMENTE 27/07"
        m._atualizar_chip_validade()
        assert "27/07" in m._validade_lbl.text()
    finally:
        m.close()


def test_d2_o_popover_tem_as_respostas_prontas(raiz_tmp):
    """D2: um popover com as escolhas prontas — a sugerida JÁ marcada —
    no lugar dos dois QInputDialog em sequência."""
    from app.qt.telas.validade_dialog import ValidadeDialog
    _app()
    dlg = ValidadeDialog(sugerida="SOMENTE 03/08", hoje=date(2026, 7, 27))
    try:
        assert dlg.op_sugerida.isChecked(), "a sugerida não vem marcada"
        assert "03/08" in dlg.op_sugerida.text()
        assert "27/07" in dlg.op_hoje.text()
        dlg.op_hoje.setChecked(True)
        assert dlg.valor() == "SOMENTE 27/07"
        dlg.op_estoques.setChecked(True)
        assert "estoques" in dlg.valor().lower()
        dlg.op_sugerida.setChecked(True)
        assert dlg.valor() == "SOMENTE 03/08"
    finally:
        dlg.close()


# ---------------------------------------------------------------------------
# D3 — a mensagem diz ONDE, e o aviso abre o campo
# ---------------------------------------------------------------------------


def test_d3_a_mensagem_do_pre_voo_diz_onde_clicar(raiz_tmp, tmp_path):
    """D3: a frase que fez o dono dizer "não faço a mínima ideia" agora
    aponta a porta: o 📅 na barra da Mesa."""
    from app.qt.telas.servico import validar_composicao
    from app.rendering.compositor import DadosProduto
    from app.rendering.model import (
        LayoutDef, Pagina, PapelTexto, Regiao, Retangulo, Slot, TipoRegiao,
    )
    from app.tests import acervo
    fontes = tmp_path / "fontes"
    fontes.mkdir(exist_ok=True)
    acervo.copiar_fontes_reais(fontes)
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("c", [
        Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 30, 30), nome="Foto"),
        Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(10, 60, 60, 8),
               papel_texto=PapelTexto.VALIDADE, nome="Validade da oferta"),
    ])])])
    avisos = validar_composicao(
        lay, {"c": DadosProduto("X", texto_legal=None)}, fontes_dir=fontes)
    alvo = [a for a in avisos if "Validade" in a]
    assert alvo, f"o pré-voo não acusou a validade vazia: {avisos}"
    assert "📅" in alvo[0] and "barra" in alvo[0].lower(), (
        f"a mensagem segue sem dizer ONDE: {alvo[0]!r}")


def test_d3_o_aviso_clicavel_abre_o_campo(raiz_tmp, monkeypatch):
    """D3: o aviso da validade no laudo é CLICÁVEL e abre o popover
    direto (o padrão _ir_para_aviso do D10, estendido — L9)."""
    from app.qt.telas.mesa import MesaTela
    _app()
    m = MesaTela()
    try:
        abriu = []
        monkeypatch.setattr(m, "_editar_validade_oferta",
                            lambda: abriu.append(True))
        alvo = m._ir_para_aviso(
            "selo: papel “Validade da oferta” sem data — clique no 📅 "
            "na barra da Mesa, ao lado de Exportar")
        assert abriu, "clicar no aviso da validade não abriu o campo"
        assert alvo == "validade"
    finally:
        m.close()


# ---------------------------------------------------------------------------
# D4 — as guardas de sanidade (avisar, nunca vetar)
# ---------------------------------------------------------------------------


def test_d4_guardas_da_data(raiz_tmp):
    """D4: data no passado, mês estranho e dia que não bate com o
    encarte AVISAM (com a porta na frase) — nunca vetam."""
    from app.qt.telas.servico import avisos_da_validade

    hoje = date(2026, 7, 27)                      # segunda-feira
    # no passado
    avs = avisos_da_validade("SOMENTE 20/07", "Segunda dos Frios", hoje=hoje)
    assert any("passou" in a for a in avs), avs
    # mês diferente (aviso, não veto — pode ser legítimo no Jornal)
    avs = avisos_da_validade("SOMENTE 03/09", "Segunda dos Frios", hoje=hoje)
    assert any("mês" in a for a in avs), avs
    # o dia não bate com o encarte (29/07 é quarta; o encarte é segunda)
    avs = avisos_da_validade("SOMENTE 29/07", "Segunda dos Frios", hoje=hoje)
    assert any("não bate" in a or "dia do encarte" in a for a in avs), avs
    # a certa: silêncio
    assert avisos_da_validade("SOMENTE 27/07", "Segunda dos Frios",
                              hoje=hoje) == []
    # sem data (enquanto durarem os estoques): as guardas de data calam
    assert avisos_da_validade("enquanto durarem os estoques",
                              "Segunda dos Frios", hoje=hoje) == []


# ---------------------------------------------------------------------------
# §6 — o teste de aceitação por GESTO + a data no selo por pixel
# ---------------------------------------------------------------------------


def test_s6_duplo_clique_no_atelie_e_a_data_ja_esta_la(raiz_tmp):
    """§6: o dono faz duplo-clique em "Segunda dos Frios" e a validade
    JÁ está certa — SEM NENHUM evento cadastrado no banco. E a data
    chega ao SELO da página composta, por pixel."""
    _requer_pacote()
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from app.core.database import Database
    from app.qt.telas.atelie import AtelieTela
    from app.qt.telas.mesa import MesaTela
    from app.qt.telas.servico import proxima_ocorrencia
    from app.rendering.encartes import importar_pacote
    from app.tests.gestos import drenar
    _app()

    db = Database().init()
    try:
        with db.Session() as s:
            importar_pacote(s, _PACOTE, raiz=raiz_tmp)
            s.commit()
    finally:
        db.engine.dispose()

    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    tela = AtelieTela(ao_abrir=lambda ldef, tipo, nome: m.carregar_layout(
        ldef, ldef.arquivo_fundo, nome_layout=nome))
    tela.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    tela.resize(1100, 720)
    tela.show()
    drenar()
    try:
        it = next(tela.lista.item(i) for i in range(tela.lista.count())
                  if "Segunda dos Frios" in tela.lista.item(i).text())
        tela.lista.scrollToItem(it)
        drenar()
        r = tela.lista.visualItemRect(it)
        QTest.mouseClick(tela.lista.viewport(), Qt.MouseButton.LeftButton,
                         Qt.KeyboardModifier.NoModifier, r.center())
        QTest.mouseDClick(tela.lista.viewport(), Qt.MouseButton.LeftButton,
                          Qt.KeyboardModifier.NoModifier, r.center())
        drenar()

        esperado = proxima_ocorrencia(0).strftime("%d/%m")
        assert m._validade == f"SOMENTE {esperado}", (
            f"o duplo-clique não trouxe a data: {m._validade!r} — o "
            "conserto não está pronto (§6)")
        assert esperado in m._validade_lbl.text(), "o chip não mostra a data"

        # a data chega ao SELO por pixel: o miolo do selo com a validade
        # difere do miolo sem ela (o molde do N1)
        from app.rendering.compositor import DadosProduto, compor_pagina
        from app.rendering.model import TipoRegiao
        from app.rendering.units import mm_para_px
        lay = m.area.canvas._layout
        pag = lay.paginas[0]
        selo = next(s for s in pag.slots if s.id == "selo-validade")
        reg = selo.regioes[0]
        com = compor_pagina(lay, pag, {"celula-2": DadosProduto(
            "Prova", texto_legal=f"Ofertas válidas {m._validade}")}, dpi=96)
        sem = compor_pagina(lay, pag, {"celula-2": DadosProduto(
            "Prova", texto_legal=None)}, dpi=96)
        x = round(mm_para_px(reg.rect.x_mm, 96))
        y = round(mm_para_px(reg.rect.y_mm, 96))
        w = round(mm_para_px(reg.rect.larg_mm, 96))
        h = round(mm_para_px(reg.rect.alt_mm, 96))
        borda = 30            # a rotação espalha; recorte generoso
        caixa = (max(0, x - borda), max(0, y - borda), x + w + borda,
                 y + h + borda)
        assert com.crop(caixa).tobytes() != sem.crop(caixa).tobytes(), (
            "a data sugerida não chegou ao selo da página composta")
    finally:
        m.close()
        tela.deleteLater()
        drenar()
