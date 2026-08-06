"""BLOCO B da ORDEM_F13 — as hemorragias, cada uma com o vermelho antes (L1).

Cada teste deste arquivo nasceu VERMELHO no código de antes do conserto
correspondente (a rodada vermelha está registrada na resposta do builder,
no fim da ordem). Tudo por gesto (L2) ou conteúdo (L3), sobre os helpers
de app/tests/gestos.py.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.rendering.model import (
    LayoutDef,
    Pagina,
    Regiao,
    Retangulo,
    Slot,
    TipoRegiao,
)
from app.tests import acervo
from app.tests.gestos import clicar, drenar, vigia_dialogo


def _app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    acervo.copiar_fontes_reais(root.fontes)
    Database(root).init().engine.dispose()
    return root


# ---------------------------------------------------------------------------
# B1 · CD-01 — editar preço/nome NÃO apaga a pilha de desfazer
# ---------------------------------------------------------------------------


def test_b1_editar_nome_e_preco_preserva_o_desfazer(raiz_tmp):
    """B1 (CD-01 — os 9 Ctrl+Z da gravação): mover uma região, depois
    editar o nome/preço do item na estante (os DOIS diálogos reais,
    respondidos pelo vigia), depois DESFAZER pelo botão real da Mesa.
    A região tem de voltar ao lugar — hoje a edição recria o Historico
    (canvas.py:210 via _aplicar_mapa) e o desfazer morre calado."""
    from app.qt.telas import servico
    from app.qt.telas.mesa import MesaTela
    _app()
    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    m.show()
    try:
        it = servico.ItemMesa("Arroz", "1,00", "VERDE", "Arroz")
        m._itens = [it]
        lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("c", [
            Regiao(TipoRegiao.NOME, Retangulo(10, 10, 40, 10), nome="Nome"),
            Regiao(TipoRegiao.PRECO, Retangulo(10, 30, 40, 10), nome="Preço"),
        ])])])
        m._layout = lay
        m.area.carregar(lay, {})
        m._mapa = {"c": it.uid}
        m._recarregar_lista()

        canvas = m.area.canvas
        reg = canvas._layout.paginas[0].slots[0].regioes[0]
        x0 = reg.rect.x_mm
        item = next(i for i in canvas._itens if i.regiao is reg)
        item.setSelected(True)               # o commit grava as SELECIONADAS
        item.setPos(*canvas.mm_para_cena(30.0, 10.0))
        canvas._commit_regiao(item)          # 1 estado de desfazer na pilha
        assert canvas._layout.paginas[0].slots[0].regioes[0].rect.x_mm == \
            pytest.approx(30.0)
        assert canvas._historico.pode_desfazer()

        # o gesto da gravação: editar nome e preço na estante (2 diálogos)
        with vigia_dialogo("OK", vezes=2) as v:
            m._editar_item(m.lista.item(0))
        assert v.disparos == 2, "os diálogos de edição nem abriram"

        assert canvas._historico.pode_desfazer(), (
            "editar nome/preço APAGOU a pilha de desfazer (CD-01)")
        clicar(m.btn_desfazer)               # o desfazer REAL da Mesa
        assert canvas._layout.paginas[0].slots[0].regioes[0].rect.x_mm == \
            pytest.approx(x0), "o desfazer não devolveu a região ao lugar"
    finally:
        m.close()


# ---------------------------------------------------------------------------
# B2d · L-05 — X/Esc no "Recuperar rascunho?" NÃO destroem o rascunho
# ---------------------------------------------------------------------------


def _semear_rascunho():
    from app.core import rascunho
    it = {"descricao": "ARROZ TIO JOAO 5KG", "preco": "24,90",
          "semaforo": "VERDE", "nome": "Arroz Tio João 5kg"}
    rascunho.salvar_rascunho({"itens": [it]})


def _mesa_mostrada():
    from app.qt.telas.mesa import MesaTela
    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    return m


def test_b2d_esc_no_recuperar_rascunho_deixa_para_depois(raiz_tmp):
    """B2d (L-05): Esc (e o X, que cai no MESMO reject) no diálogo de
    recuperação é "decido depois" — o rascunho FICA. Hoje tudo que não é
    Yes cai em descartar_rascunhos() e o trabalho morre calado."""
    from app.core import rascunho
    _app()
    _semear_rascunho()
    assert rascunho.ha_rascunho()
    m = _mesa_mostrada()
    try:
        with vigia_dialogo(tecla=Qt.Key.Key_Escape) as v:
            m.show()             # showEvent → _oferecer_recuperacao → diálogo
        assert v.disparou, "o diálogo de recuperação nem abriu"
        assert rascunho.ha_rascunho(), (
            "Esc DESTRUIU o rascunho — não existe 'depois eu vejo' (L-05)")
    finally:
        m.close()


def test_b2d_descartar_explicito_ainda_descarta(raiz_tmp):
    """B2d: a destruição continua POSSÍVEL — mas só pelo botão que DIZ
    isso ('Descartar de vez'), nunca pelo X."""
    from app.core import rascunho
    _app()
    _semear_rascunho()
    m = _mesa_mostrada()
    try:
        with vigia_dialogo("Descartar de vez") as v:
            m.show()
        assert v.disparou
        assert v.faltou_botao is None, (
            f"o diálogo não tem 'Descartar de vez' — tem {v.textos_botoes}")
        assert not rascunho.ha_rascunho()
    finally:
        m.close()


def test_b2d_recuperar_recupera_e_fala_portugues(raiz_tmp):
    """B2d + B2c: o botão afirmativo recupera de verdade, e NENHUM botão
    do diálogo fala inglês (era Yes/No — L-03)."""
    from app.core import rascunho
    _app()
    _semear_rascunho()
    m = _mesa_mostrada()
    try:
        with vigia_dialogo("Recuperar") as v:
            m.show()
        assert v.disparou
        assert v.faltou_botao is None, (
            f"o diálogo não tem 'Recuperar' — tem {v.textos_botoes}")
        assert not any(b.strip() in ("Yes", "No", "&Yes", "&No")
                       for b in v.textos_botoes), (
            f"o diálogo fala inglês: {v.textos_botoes} (L-03)")
        assert [it.nome for it in m._itens] == ["Arroz Tio João 5kg"]
        # o rascunho SÓ some no salvar de verdade (mesa._salvar_projeto) ou
        # no descarte explícito — recuperar não abre janela de perda
        assert rascunho.ha_rascunho()
    finally:
        m.close()


# ---------------------------------------------------------------------------
# B2e · L-09 — sair do editor com edição não salva PERGUNTA
# ---------------------------------------------------------------------------


def _atelie_editando(raiz_tmp, nome="Terça do Pão"):
    from app.core.database import Database
    from app.qt.telas.atelie import AtelieTela
    from app.rendering.persistencia import salvar_layout
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("s", [
        Regiao(TipoRegiao.NOME, Retangulo(10, 10, 40, 10), nome="Nome")])])])
    db = Database().init()
    try:
        with db.Session() as s:
            row = salvar_layout(s, nome, lay)
            s.commit()
            lid = row.id
    finally:
        db.engine.dispose()
    tela = AtelieTela()
    tela._editar(lid, nome)
    assert tela._paginas.currentIndex() == 1     # está no editor
    return tela, lid


def _sujar_editor(tela) -> None:
    from app.tests.gestos import botao_por_tooltip
    clicar(botao_por_tooltip(tela._editor.barra, "Adicionar imagem"))
    assert tela._editor._sujo, "o clique na barra não sujou o editor"


def test_b2e_voltar_com_edicao_suja_pergunta_e_ficar_fica(raiz_tmp):
    """B2e (L-09): título com •, clique REAL em ' Biblioteca' — tem de
    PERGUNTAR. 'Ficar no editor' fica, com a edição intacta. Hoje volta em
    silêncio e a próxima abertura come 20 min de trabalho."""
    from app.tests.gestos import botao_por_texto
    _app()
    tela, _lid = _atelie_editando(raiz_tmp)
    _sujar_editor(tela)
    with vigia_dialogo("Ficar no editor") as v:
        clicar(botao_por_texto(tela, "Biblioteca"))
    assert v.disparou, "saiu do editor sujo SEM perguntar (L-09, I2)"
    assert v.faltou_botao is None, f"botões errados: {v.textos_botoes}"
    assert tela._paginas.currentIndex() == 1     # ficou no editor
    assert tela._editor._sujo                    # edição intacta
    tela.close()


def test_b2e_sair_sem_salvar_sai_e_reabrir_pergunta_no_ponto_da_perda(
        raiz_tmp):
    """B2e: 'Sair sem salvar' sai (a edição segue viva no widget); abrir
    OUTRO layout — o ponto onde a perda é REAL — pergunta de novo, e
    'Voltar' não recarrega nada por cima."""
    from app.tests.gestos import botao_por_texto
    _app()
    tela, _lid = _atelie_editando(raiz_tmp)
    _sujar_editor(tela)
    with vigia_dialogo("Sair sem salvar") as v:
        clicar(botao_por_texto(tela, "Biblioteca"))
    assert v.disparou and v.faltou_botao is None
    assert tela._paginas.currentIndex() == 0     # saiu para a biblioteca

    from app.core.database import Database
    from app.rendering.persistencia import salvar_layout
    lay2 = LayoutDef(80, 80, dpi=100, paginas=[Pagina([Slot("s2", [
        Regiao(TipoRegiao.PRECO, Retangulo(5, 5, 30, 10), nome="Preço")])])])
    db = Database().init()
    try:
        with db.Session() as s:
            lid2 = salvar_layout(s, "Outro Layout", lay2).id
            s.commit()
    finally:
        db.engine.dispose()

    with vigia_dialogo("Voltar") as v2:
        tela._editar(lid2, "Outro Layout")
    assert v2.disparou, "abrir outro layout por cima da edição suja não perguntou"
    assert tela._editor.nome_layout_atual == "Terça do Pão", (
        "o carregar passou por cima da edição não salva")
    tela.close()


# ---------------------------------------------------------------------------
# B2/B2b · COND-2 — a sequência REAL do §19: modal DURANTE o crossfade
# ---------------------------------------------------------------------------


def test_b2_cond2_modal_no_meio_do_crossfade_janela_volta_ao_brilho(
        vida, raiz_tmp):
    """COND-2 (§4.3 do selo): Início → paleta Ctrl+K aberta → trocar de
    tela com um QMessageBox modal abrindo DURANTE o crossfade (o showEvent
    da tela destino, como a Mesa faz com o rascunho). Depois de tudo:
    nenhuma foto de crossfade no ar, nenhum véu de diálogo órfão, a paleta
    NÃO atravessou a troca, e a tela destino está na frente — a janela
    volta ao brilho normal. Filtro INSTALADO (nada de belt-out aqui)."""
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QLabel, QMessageBox, QWidget

    from app.qt.design import animacoes as anim
    from app.qt.design.paleta_comandos import PaletaBusca
    from app.qt.design.shell import Shell
    _app()

    class TelaComModal(QLabel):
        vezes = 0

        def showEvent(self, ev):  # noqa: N802 (Qt)
            super().showEvent(ev)
            if TelaComModal.vezes == 0:
                TelaComModal.vezes = 1
                caixa = QMessageBox(self)
                caixa.setWindowTitle("Recuperar rascunho?")
                caixa.setText("…")
                caixa.addButton("Deixar para depois",
                                QMessageBox.ButtonRole.RejectRole)
                # o "dono" fecha o modal com o crossfade AINDA no ar
                QTimer.singleShot(100, caixa.reject)
                caixa.exec()

    TelaComModal.vezes = 0
    shell = Shell()
    shell.resize(900, 600)
    shell.adicionar_tela("inicio", QLabel("Início"))
    shell.adicionar_tela("mesa", TelaComModal("Mesa"))
    shell._paleta_busca = PaletaBusca(shell, lambda *_a: None)
    shell.show()
    drenar()
    shell.ir_para("inicio")
    drenar()
    shell._paleta_busca.abrir()
    assert shell._paleta_busca.isVisible()

    shell.ir_para("mesa")           # crossfade ANIMADO + modal no meio
    drenar(900)                     # atravessa a animação e os failsafes

    assert TelaComModal.vezes == 1, "o modal do destino nem abriu"
    assert not anim._veus_troca, "a foto do crossfade ficou registrada (L-02)"
    fotos = [w for w in shell.findChildren(QWidget, "veuTrocaTela")
             if w.isVisible()]
    assert not fotos, "a foto da tela antiga continua desenhada (L-02)"
    veus = [w for w in shell.findChildren(QWidget, "veuDialogo")
            if w.isVisible()]
    assert not veus, "véu de diálogo órfão sobre a janela (L-01)"
    assert not shell._paleta_busca.isVisible(), (
        "a paleta do Ctrl+K atravessou a troca de tela (L-10)")
    assert shell._pilha.currentWidget() is shell.tela("mesa")
    shell.close()


# ---------------------------------------------------------------------------
# B2c · L-03 — as perguntas da casa falam PT-BR (e o padrão é o seguro)
# ---------------------------------------------------------------------------


def test_b2c_varredura_nenhum_question_estatico_na_producao():
    """B2c (L-03): varredura por IDENTIFICADOR (a lei dos vetos da F11) —
    zero `QMessageBox.question(` e zero `StandardButton.Yes` na produção.
    As perguntas da casa passam pelo helper PT-BR com padrão declarado."""
    maus: list[str] = []
    raiz_app = acervo.RAIZ_REPO / "app"
    for py in raiz_app.rglob("*.py"):
        rel = py.relative_to(raiz_app).as_posix()
        if rel.startswith(("tests/", "tests_janela/")):
            continue
        texto = py.read_text(encoding="utf-8", errors="replace")
        for padrao in ("QMessageBox.question(", "StandardButton.Yes",
                       "QMessageBox.Yes"):
            if padrao in texto:
                maus.append(f"{rel}: {padrao}")
    assert not maus, (
        "diálogo estático em inglês sobrando na produção: " + "; ".join(maus))


def test_b2c_perguntar_fala_portugues_pelo_clique_real():
    """O contrato do helper novo: Sim/Não em PT-BR (ou o verbo que o
    chamador mandar), clique real decide, Enter cai no seguro."""
    from app.qt.design.componentes import perguntar
    _app()
    with vigia_dialogo("Migrar agora") as v:
        resposta = perguntar(None, "Migrar o acervo?", "Leva uns minutos.",
                             sim="Migrar agora", nao="Deixar como está")
    assert v.disparou and resposta is True
    assert "Deixar como está" in v.textos_botoes
    with vigia_dialogo("Deixar como está") as v2:
        resposta2 = perguntar(None, "Migrar o acervo?", "…",
                              sim="Migrar agora", nao="Deixar como está")
    assert resposta2 is False
    with vigia_dialogo(tecla=Qt.Key.Key_Return) as v3:
        resposta3 = perguntar(None, "Migrar o acervo?", "…",
                              sim="Migrar agora", nao="Deixar como está")
    assert v3.disparou
    assert resposta3 is False, "Enter caiu no afirmativo — o padrão é o seguro"


# ---------------------------------------------------------------------------
# B4 · CI-05 — a foto ORIGINAL nunca morre na poda
# ---------------------------------------------------------------------------


def test_b4_a_original_sobrevive_a_11a_troca_por_conteudo(tmp_path):
    """B4 (CI-05, trava da F10: curadoria NÃO-destrutiva): trocar a foto
    mais vezes que o limite de versões NÃO pode apagar a original. Prova
    por CONTEÚDO: cada troca é uma cor única; depois de estourar o
    limite, a COR da primeira foto ainda existe no histórico."""
    from PIL import Image

    from app.images.biblioteca import BibliotecaImagens
    bib = BibliotecaImagens(tmp_path / "lib", max_versoes=3)
    cores = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF",
             "#00FFFF", "#123456"]
    for i, cor in enumerate(cores):
        f = tmp_path / f"c{i}.png"
        Image.new("RGB", (8, 8), cor).save(f)
        bib.ingerir(7, str(f))

    presentes = set()
    for v in bib.listar_versoes(7):
        with Image.open(v) as im:
            presentes.add(im.convert("RGB").getpixel((4, 4)))
    assert (255, 0, 0) in presentes, (
        "a foto ORIGINAL (vermelha) morreu na poda — CI-05, a 11ª troca")
    assert len(bib.listar_versoes(7)) == 3      # o limite segue valendo


# ---------------------------------------------------------------------------
# B5 · CB-01 — o snapshot do boot não copia banco corrompido
# ---------------------------------------------------------------------------


def test_b5_snapshot_do_boot_pula_banco_corrompido_e_preserva_os_bons(
        raiz_tmp):
    """B5 (CB-01): com o banco vivo CORROMPIDO, o snapshot automático NÃO
    cria cópia nova (o lixo não entra na estante de backups) e NÃO
    rotaciona os bons para fora — e deixa o rastro no log (I2)."""
    from app.core import cofre
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio

    db = Database().init()
    try:
        with db.Session() as s:
            ConfigRepositorio(s).set("backups.rotacao", 2)
            s.commit()
    finally:
        db.engine.dispose()

    bons = [cofre.snapshot_automatico(raiz_tmp),
            cofre.snapshot_automatico(raiz_tmp)]
    assert all(b is not None and b.exists() for b in bons)

    raiz_tmp.caminho_banco.write_bytes(b"LIXO QUE NAO E SQLITE" * 100)

    resultado = cofre.snapshot_automatico(raiz_tmp)
    assert resultado is None, "banco corrompido virou snapshot (CB-01)"
    assert all(b.exists() for b in bons), (
        "a rotação empurrou um backup BOM para fora por causa do corrompido")
    autos = [x for x in cofre.listar_snapshots(raiz_tmp)
             if x["rotulo"] == "auto"]
    assert len(autos) == 2                      # nenhum snapshot novo
    log = raiz_tmp.raiz / "logs" / "cofre.log"
    assert log.exists() and "PULADO" in log.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# B9 · D-06 — a purga pula o item travado e purga o resto
# ---------------------------------------------------------------------------


def test_b9_purga_com_projeto_vivo_apontando_nao_aborta(raiz_tmp):
    """B9 (D-06): layout na lixeira com um ProjetoSalvo VIVO apontando
    (FK sem ondelete) — a purga PULA o layout COM relato nominal, purga o
    produto vencido normalmente, não levanta, e NÃO toca nos arquivos do
    item que ficou."""
    import uuid as _uuid
    from datetime import datetime, timedelta

    from app.core import lixeira
    from app.core.database import Database
    from app.core.models import Layout, Produto, ProjetoSalvo

    velho = datetime.now() - timedelta(days=40)
    db = Database().init()
    try:
        with db.Session() as s:
            lay = Layout(nome="Preso", estrutura_json="{}",
                         excluido_em=velho)
            s.add(lay)
            s.flush()
            s.add(ProjetoSalvo(nome="Vivo", uuid=_uuid.uuid4().hex,
                               layout_id=lay.id))
            prod = Produto(nome_bruto="VENCIDO", nome_sanitizado="Vencido",
                           excluido_em=velho)
            s.add(prod)
            s.commit()
            lay_id, prod_id = lay.id, prod.id
    finally:
        db.engine.dispose()

    pasta_fotos = raiz_tmp.biblioteca_imagens / str(prod_id)
    pasta_fotos.mkdir(parents=True, exist_ok=True)
    (pasta_fotos / "atual.png").write_bytes(b"png")

    log = lixeira.purgar()                     # hoje: IntegrityError aborta

    assert any("Vencido" in linha for linha in log), "o produto não purgou"
    assert not pasta_fotos.exists()            # arquivos DEPOIS do commit
    presos = [linha for linha in log if "FICOU na lixeira" in linha]
    assert presos and "Preso" in presos[0], (
        "o layout travado não foi RELATADO (I2)")
    db = Database().init()
    try:
        with db.Session() as s:
            assert s.get(Layout, lay_id) is not None   # ficou, sem meio-morto
            assert s.get(Produto, prod_id) is None
    finally:
        db.engine.dispose()


# ---------------------------------------------------------------------------
# B10 · D-07 — as minas latentes foram removidas (varredura de identificador)
# ---------------------------------------------------------------------------


def test_b10_hard_deletes_sem_chamador_foram_removidos():
    """B10 (D-07, a lei dos vetos da F11 — ausência por IDENTIFICADOR):
    os dois hard-deletes públicos sem chamador não existem mais; a
    exclusão oficial é a lixeira (suave + purga de 30 dias)."""
    import app.rendering.persistencia as persistencia
    from app.core.repositories import ProdutoRepositorio
    assert not hasattr(persistencia, "excluir_layout"), (
        "excluir_layout ainda existe (mina latente D-07)")
    assert not hasattr(ProdutoRepositorio, "excluir"), (
        "ProdutoRepositorio.excluir ainda existe (mina latente D-07)")


# ---------------------------------------------------------------------------
# B6 · F-01 — a receita ÚNICA do cartaz (o +18 volta às etiquetas)
# ---------------------------------------------------------------------------


def test_b6_etiqueta_em_lote_diferencia_mais18_por_conteudo(raiz_tmp,
                                                            tmp_path):
    """B6 (F-01, decisão travada da casa): bebida alcoólica leva o selo
    +18 SEMPRE — inclusive na etiqueta em lote. Prova por CONTEÚDO na
    porta pública inteira: com/sem mais18, os bytes da imagem embutida no
    PDF têm de DIFERIR. Hoje o dict local das etiquetas perde o campo e
    as duas saem idênticas (a 4ª porta, de novo)."""
    from pypdf import PdfReader

    from app.qt.telas import servico
    from app.qt.telas.servico import ItemMesa

    def _folha(nome_arq: str, mais18: bool) -> bytes:
        item = ItemMesa("Cerveja Itaipava 269ml", "1,98", "VERDE",
                        "Cerveja Itaipava 269ml", mais18=mais18)
        caminho, _avisos = servico.gerar_etiquetas_lote(
            [item], tmp_path / nome_arq)
        imagens = list(PdfReader(caminho).pages[0].images)
        assert imagens
        return imagens[0].data

    com_selo = _folha("com18.pdf", True)
    sem_selo = _folha("sem18.pdf", False)
    assert com_selo != sem_selo, (
        "mais18 NÃO muda a etiqueta em lote — o selo +18 da bebida "
        "continua sumindo (F-01)")


def test_b6_projeto_cartaz_reaberto_mantem_mais18_e_categoria(raiz_tmp):
    """B6: o ramo CARTAZ de dados_de_projeto_aberto montava um dict
    INCOMPLETO — projeto reaberto (Modo Pai incluso) perdia mais18 e
    categoria."""
    from types import SimpleNamespace

    from app.qt.telas import servico
    d_item = {"descricao": "CERVEJA ITAIPAVA 269ML", "preco": "1,98",
              "semaforo": "VERDE", "nome": "Cerveja Itaipava 269ml",
              "mais18": True, "categoria": "Bebidas", "uid": "u1"}
    aberto = SimpleNamespace(tipo="CARTAZ", itens=[d_item],
                             mapa={"s": "u1"}, validade_oferta=None,
                             overrides={})
    dados, _faltas = servico.dados_de_projeto_aberto(aberto)
    assert dados["s"].mais18 is True, "o projeto CARTAZ reaberto perdeu o +18"
    assert dados["s"].categoria == "Bebidas"


def test_b6_fabrica_compoe_do_mesmo_dado_da_receita_unica(raiz_tmp):
    """B6: a Fábrica delega para a receita única — a categoria do item
    (que a receita local jogava fora) chega ao DadosProduto."""
    from app.qt.telas import servico
    from app.qt.telas.fabrica import FabricaTela
    from app.qt.telas.servico import ItemMesa
    _app()
    f = FabricaTela()
    it = ItemMesa("Cerveja Itaipava 269ml", "1,98", "VERDE",
                  "Cerveja Itaipava 269ml", mais18=True, categoria="Bebidas",
                  preco_de="2,49")
    d = f._dados(it)
    assert d.mais18 is True
    assert d.categoria == "Bebidas", (
        "a receita local da Fábrica segue divergente da receita única")
    esperado = servico.dados_cartaz_de_item(it)
    assert (d.nome, d.preco_por, d.preco_de, d.mais18, d.categoria) == \
        (esperado.nome, esperado.preco_por, esperado.preco_de,
         esperado.mais18, esperado.categoria)
    f.close()


# ---------------------------------------------------------------------------
# B7 · CI-03 — o juiz respeita a própria confiança
# ---------------------------------------------------------------------------


@pytest.fixture()
def sessao_conciliacao(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.models import Produto
    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    db = Database(root).init()
    with db.Session() as s:
        s.add(Produto(nome_bruto="BOMBRIL 45G",
                      nome_sanitizado="Bombril 45g"))
        s.commit()
        yield s
    db.engine.dispose()


def test_b7_juiz_com_confianca_baixa_vira_amarelo(sessao_conciliacao):
    """B7 (CI-03, trava da F9): o juiz LIA a confiança e nunca a
    comparava — 0,05 pintava VERDE. Abaixo do piso, o veredito é AMARELO
    com o candidato à vista (o humano confirma)."""
    from app.ai.conciliacao import (
        Conciliador, LimiaresConciliacao, Semaforo,
    )
    from app.ai.fake import MotorIAFake
    fake = MotorIAFake(respostas_chat={
        "BOMBRIL": '{"indice": 0, "confianca": 0.05}'})
    limiares = LimiaresConciliacao(verde=99.0, amarelo=10.0)
    v = Conciliador(sessao_conciliacao, motor=fake,
                    limiares=limiares).conciliar("BOMBRIL 45 G DA BOA")
    assert v.via == "juiz", f"o juiz nem rodou (via={v.via})"
    assert v.semaforo == Semaforo.AMARELO, (
        f"confiança 0,05 pintou {v.semaforo} — o juiz ignora a confiança "
        "(CI-03)")
    assert v.produto is not None            # o palpite fica à vista
    assert "confiança" in v.motivo


def test_b7_juiz_confiante_segue_verde(sessao_conciliacao):
    """Regressão do B7: confiança ALTA continua verde (nada de amarelar
    o mundo)."""
    from app.ai.conciliacao import (
        Conciliador, LimiaresConciliacao, Semaforo,
    )
    from app.ai.fake import MotorIAFake
    fake = MotorIAFake(respostas_chat={
        "BOMBRIL": '{"indice": 0, "confianca": 0.93}'})
    limiares = LimiaresConciliacao(verde=99.0, amarelo=10.0)
    v = Conciliador(sessao_conciliacao, motor=fake,
                    limiares=limiares).conciliar("BOMBRIL 45 G DA BOA")
    assert v.via == "juiz"
    assert v.semaforo == Semaforo.VERDE


# ---------------------------------------------------------------------------
# B8 · CI-02 — a revisora usa os NOMES que ela mesma pede
# ---------------------------------------------------------------------------


def test_b8_revisora_pega_preco_trocado_entre_dois_itens():
    """B8 (CI-02): o caso que ela EXISTE para pegar — Arroz com o preço do
    Feijão e vice-versa. Os dois preços existem no projeto, o conjunto de
    preços fecha, e hoje passa limpo porque os nomes lidos são jogados
    fora."""
    import json
    from decimal import Decimal

    from app.ai.fake import MotorIAFake
    from app.ai.revisora import revisar_export
    from app.rendering.compositor import DadosProduto
    dados = {
        "s0": DadosProduto("Arroz Tio João 5kg", preco_por=Decimal("24.90")),
        "s1": DadosProduto("Feijão Carioca 1kg", preco_por=Decimal("8.90")),
    }
    fake = MotorIAFake(respostas_visao={"revisor de encarte": json.dumps({
        "itens": [{"nome": "Arroz Tio João 5kg", "preco": "8,90"},
                  {"nome": "Feijão Carioca 1kg", "preco": "24,90"}],
        "precos": ["8,90", "24,90"],
        "nomes": ["Arroz Tio João 5kg", "Feijão Carioca 1kg"]})})
    avisos, deg = revisar_export("peca.png", dados, motor=fake)
    assert deg is None
    troca = [a for a in avisos if "TROCADO" in a.upper()]
    assert troca, (
        f"preço trocado entre duas células passou LIMPO (CI-02) — avisos: "
        f"{avisos}")
    assert any("Arroz" in a and "8,90" in a for a in troca)


def test_b8_revisora_par_correto_nao_gera_alarme_falso():
    """Regressão do B8: pares certos não viram aviso (alarme falso mata a
    confiança na colega)."""
    import json
    from decimal import Decimal

    from app.ai.fake import MotorIAFake
    from app.ai.revisora import revisar_export
    from app.rendering.compositor import DadosProduto
    dados = {
        "s0": DadosProduto("Arroz Tio João 5kg", preco_por=Decimal("24.90")),
    }
    fake = MotorIAFake(respostas_visao={"revisor de encarte": json.dumps({
        "itens": [{"nome": "Arroz Tio Joao 5kg", "preco": "24,90"}],
        "precos": ["24,90"], "nomes": ["Arroz Tio Joao 5kg"]})})
    avisos, _deg = revisar_export("peca.png", dados, motor=fake)
    assert not [a for a in avisos if "TROCADO" in a.upper()]


# ---------------------------------------------------------------------------
# B3 · CF-01 — Enter na caixa "não tem volta" NUNCA apaga
# ---------------------------------------------------------------------------


def test_b3_enter_no_dialogo_destrutivo_cai_no_seguro():
    """B3 (CF-01): o Enter — o gesto de "tá bom, some daqui" — tem de cair
    no caminho SEGURO (Cancelar), nunca no verbo destrutivo. Na gravação ao
    vivo (L-06) o botão afirmativo estava com o anel de foco."""
    from app.qt.design.componentes import confirmar_destrutivo
    _app()
    with vigia_dialogo(tecla=Qt.Key.Key_Return) as v:
        resultado = confirmar_destrutivo(
            None, "Excluir produtos",
            "Isto não tem volta. Excluir mesmo?", "Excluir 2 produtos")
    assert v.disparou, "o QMessageBox real nunca abriu"
    assert resultado is False, (
        "Enter CONFIRMOU a exclusão — o botão destrutivo é o padrão (CF-01)")


def test_b3_esc_no_dialogo_destrutivo_cancela():
    """B3: Esc = Cancelar, declarado por setEscapeButton (não por sorte da
    heurística do Qt)."""
    from app.qt.design.componentes import confirmar_destrutivo
    _app()
    with vigia_dialogo(tecla=Qt.Key.Key_Escape) as v:
        resultado = confirmar_destrutivo(
            None, "Excluir produtos", "Isto não tem volta.", "Excluir 1 produto")
    assert v.disparou
    assert resultado is False


def test_b3_enter_no_pre_voo_nao_exporta_com_pendencias():
    """B3 no portão do I2: com pendências na tela, Enter NÃO pode significar
    "exportar mesmo assim" — o padrão é parar e ler."""
    from app.qt.telas.prevoo import confirmar_pre_voo
    _app()
    with vigia_dialogo(tecla=Qt.Key.Key_Return) as v:
        resultado = confirmar_pre_voo(
            None, ["“Arroz”: sem imagem"], "Exportar")
    assert v.disparou
    assert resultado is False, (
        "Enter EXPORTOU com pendências — 'mesmo assim' virou o padrão (CF-01)")


def test_b3_o_padrao_declarado_e_o_cancelar_nos_dois_dialogos():
    """B3: o botão PADRÃO (o que o Enter aciona) é declarado e é o Cancelar —
    conferido no diálogo vivo, não por leitura de código."""
    from app.qt.design.componentes import confirmar_destrutivo
    from app.qt.telas.prevoo import confirmar_pre_voo
    _app()
    with vigia_dialogo("Cancelar") as v1:
        confirmar_destrutivo(None, "Excluir", "…", "Excluir tudo")
    assert v1.botao_padrao == "Cancelar"
    with vigia_dialogo("Cancelar") as v2:
        confirmar_pre_voo(None, ["“X”: sem foto"], "Salvar")
    assert v2.botao_padrao == "Cancelar"
