"""ORDEM F13-NONUS — a precedência tem de ser CÓDIGO, não procedimento.

N1: a precedência do nome (os 6 passos da OCTAVUS) vira função de
runtime chamada pelo compositor para TODO nome — e o "…" morre em nome
de produto. A prova-mestra: a página composta com o dado CRU (como o
caminho do dono produz) sai BYTE-IDÊNTICA à página composta com o dado
alfaiatado à mão — a confecção alcançou a alfaiataria.
"""

from pathlib import Path

import pytest

_PACOTE = Path(__file__).resolve().parents[2] / "Templates novos"


def _requer_pacote():
    if not _PACOTE.exists():
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")


def _fontes_reais(tmp_path):
    from app.tests import acervo
    fontes = tmp_path / "fontes"
    fontes.mkdir(exist_ok=True)
    acervo.copiar_fontes_reais(fontes)
    return fontes


# ---------------------------------------------------------------------------
# a função em si (unidade — sem compositor)
# ---------------------------------------------------------------------------


def test_n1_separar_peso_do_nome():
    """O peso sai do FIM do nome, formatado para leitura ("395 g"),
    inclusive não-canônico ("395 GR", "1,5 LT") — e peso no MEIO do
    nome não é tocado (a ordem dos tokens nunca muda)."""
    from app.core.sanitize import separar_peso

    assert separar_peso("Leite Condensado Triangulo 395g") == \
        ("Leite Condensado Triangulo", "395 g")
    assert separar_peso("Suco de Uva Aurora Tinto TP 1,5L") == \
        ("Suco de Uva Aurora Tinto TP", "1,5 L")
    assert separar_peso("Leite condensado triangulo 395 GR") == \
        ("Leite condensado triangulo", "395 g")
    assert separar_peso("Refrigerante 2 LTS") == ("Refrigerante", "2 L")
    # multiplicador vai junto (nunca sobra um "4x" órfão no nome)
    assert separar_peso("Kit 4x120g") == ("Kit", "4x120 g")
    # peso no meio: intacto (não se reordena nome)
    assert separar_peso("Oferta 200g no Pacote") == \
        ("Oferta 200g no Pacote", None)
    assert separar_peso("Kit Burguer Senepol BBX") == \
        ("Kit Burguer Senepol BBX", None)


def test_n1_a_cadeia_encurta_pelo_descritor_e_nunca_elipsa(tmp_path):
    """Os 4 itens-mostra da NONUS §2, na CÉLULA REAL da Segunda (flanco,
    186px, corpo 19/17): nenhum nome sai com "…", o nome final é um
    PREFIXO do original (nunca corta palavra, nunca reordena) e o
    descritor recebeu EXATAMENTE o que foi tirado (nada se perde — I2;
    única exceção declarada: a sigla de embalagem TP, que a tabela da
    ordem descarta)."""
    _requer_pacote()
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.model import TipoRegiao
    from app.rendering.nome_fit import precedencia_do_nome

    fontes = _fontes_reais(tmp_path)
    lay = layout_de_encarte("segunda-frios", _PACOTE)
    flanco = next(s for s in lay.paginas[0].slots if s.id == "celula-2")

    casos = [
        "Leite Condensado Triangulo 395g",
        "Azeite Gallo Extra Virgem Clássico 500ml",
        "Batata Palha Bulnez Crocante 100g",
        "Suco de Uva Aurora Tinto TP 1,5L",
    ]
    for nome in casos:
        aj = precedencia_do_nome(nome, None, None, flanco.regioes,
                                 lay.dpi, fontes)
        assert aj is not None
        assert "…" not in aj.nome, f"{nome!r}: elipsou ({aj.nome!r})"
        assert not aj.elipsa, f"{nome!r}: a cadeia declarou elipse"
        assert nome.startswith(aj.nome), \
            f"{nome!r}: o nome final {aj.nome!r} não é prefixo (reordenou?)"
        # nada se perde: nome final + descritor = o nome INTEIRO (só a
        # formatação do peso muda). CONTRATO CORRIGIDO PELO DONO
        # (27/07, pós-DECIMUS): a tabela da NONUS §2 descartava o TP e
        # ele mandou de volta — "não se pode omitir o tipo de
        # embalagem"; a sigla DESCE ao descritor (a anotação original
        # da SEPTIMUS §3: "tinto TP · 1,5 L"), nunca some.
        def _tokens(s):
            return [t.lower().replace(",", ".") for t in (s or "").replace(
                " · ", " ").split() if t]
        sobra = _tokens(nome)
        junto = _tokens(aj.nome) + [t for t in _tokens(aj.descritor)]
        # o peso "395g" vira "395 g" — normaliza colando número+unidade
        def _cola_peso(ts):
            out, i = [], 0
            while i < len(ts):
                if i + 1 < len(ts) and ts[i][:1].isdigit() and \
                        ts[i + 1] in ("g", "kg", "ml", "l", "mg"):
                    out.append(ts[i] + ts[i + 1]); i += 2
                else:
                    out.append(ts[i]); i += 1
            return out
        assert _cola_peso(junto) == _cola_peso(sobra), \
            f"{nome!r}: perdeu/alterou conteúdo — {junto} != {sobra}"

    # o caso da página do dono, cravado: o flanco NÃO comporta
    # "Leite Condensado Triangulo" em 2 linhas ≥17pt → passo 5
    aj = precedencia_do_nome("Leite Condensado Triangulo 395g", None, None,
                             flanco.regioes, lay.dpi, fontes)
    assert aj.nome == "Leite Condensado"
    assert aj.descritor == "Triangulo · 395 g"

    # e o caso do dono (27/07): o TP É a embalagem — cravado no descritor
    aj = precedencia_do_nome("Suco de Uva Aurora Tinto TP 1,5L", None, None,
                             flanco.regioes, lay.dpi, fontes)
    assert "TP" in (aj.descritor or "") or "TP" in aj.nome, (
        f"o TP sumiu — nome {aj.nome!r}, descritor {aj.descritor!r}")
    assert aj.descritor and aj.descritor.endswith("1,5 L")


def test_n1_adversarial_nome_gigante_degrada_sem_elipsar(tmp_path):
    """Um nome absurdo (60+ caracteres) atravessa a cadeia até o passo 5
    e AINDA sai sem "…" — o excedente inteiro desce ao descritor."""
    _requer_pacote()
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.nome_fit import precedencia_do_nome

    fontes = _fontes_reais(tmp_path)
    lay = layout_de_encarte("segunda-frios", _PACOTE)
    etiqueta = next(s for s in lay.paginas[0].slots if s.id == "celula-4")

    nome = ("Requeijão Cremoso Tradicional da Fazenda Boa Esperança "
            "com Sal Marinho Premium 220g")
    assert len(nome) > 60
    aj = precedencia_do_nome(nome, None, None, etiqueta.regioes,
                             lay.dpi, fontes)
    assert "…" not in aj.nome and not aj.elipsa
    assert nome.startswith(aj.nome) and len(aj.nome) < len(nome)
    assert aj.descritor and "220 g" in aj.descritor


def test_n1_sem_subtitulo_nao_ha_encurtamento(tmp_path):
    """Célula SEM região de descritor (o Quintou): os passos 4/5 não
    existem — mover excedente para lugar nenhum seria perda silenciosa
    (I2). O nome fica INTEIRO (e o peso não migra)."""
    _requer_pacote()
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.nome_fit import precedencia_do_nome

    fontes = _fontes_reais(tmp_path)
    lay = layout_de_encarte("quintou", _PACOTE)
    cel = next(s for s in lay.paginas[0].slots if s.id == "pos-01")

    aj = precedencia_do_nome("Nescau Achocolatado 400g", None, None,
                             cel.regioes, lay.dpi, fontes)
    assert aj is None or aj.nome == "Nescau Achocolatado 400g"


def test_n1_passo3_a_banda_cresce_e_a_foto_cede(tmp_path):
    """O passo 3 em runtime: numa célula cuja banda só tem 1 linha, um
    nome de 2 linhas FAZ a banda crescer e a FOTO ceder — dentro do
    orçamento O1 (a foto nunca desce de 55% da altura útil)."""
    from app.rendering.model import (
        Alinhamento,
        Regiao,
        Retangulo,
        TipoRegiao,
    )
    from app.rendering.nome_fit import precedencia_do_nome
    from app.rendering.units import px_para_mm

    fontes = _fontes_reais(tmp_path)
    dpi = 96

    def _r(x, y, w, h):
        return Retangulo(px_para_mm(x, dpi), px_para_mm(y, dpi),
                         px_para_mm(w, dpi), px_para_mm(h, dpi))

    foto = Regiao(TipoRegiao.IMAGEM, _r(0, 0, 200, 240))
    nome = Regiao(TipoRegiao.NOME, _r(0, 244, 200, 28),
                  fonte="Roboto-Bold.ttf", tamanho_max_pt=19.0,
                  tamanho_min_pt=17.0, alinhamento=Alinhamento.CENTRO,
                  sem_hifen=True)
    sub = Regiao(TipoRegiao.SUBTITULO, _r(0, 276, 200, 16),
                 fonte="Roboto-Regular.ttf", tamanho_max_pt=10.0)
    regs = [foto, nome, sub]

    aj = precedencia_do_nome("Creme de Leite Italac", None, None,
                             regs, dpi, fontes)
    assert aj is not None and not aj.elipsa and "…" not in aj.nome
    # a banda cresceu (o rect do NOME mudou) e a foto cedeu
    assert nome.uid in aj.rects and foto.uid in aj.rects
    r_nome, r_foto = aj.rects[nome.uid], aj.rects[foto.uid]
    assert r_nome.alt_mm > nome.rect.alt_mm
    assert r_foto.alt_mm < foto.rect.alt_mm
    # o orçamento O1 respeitado: foto ≥55% da altura útil
    util = (sub.rect.y_mm + sub.rect.alt_mm) - foto.rect.y_mm
    assert r_foto.alt_mm >= 0.55 * util - 1e-6


def test_n1_o_peso_migra_ao_descritor_quando_ha_subtitulo(tmp_path):
    """C2 completada NO MOTOR: com região de descritor na célula, o peso
    sai do nome e desce — sem duplicar quando o descritor já o tem."""
    _requer_pacote()
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.nome_fit import precedencia_do_nome

    fontes = _fontes_reais(tmp_path)
    lay = layout_de_encarte("segunda-frios", _PACOTE)
    etiqueta = next(s for s in lay.paginas[0].slots if s.id == "celula-4")

    aj = precedencia_do_nome("Creme de Leite Italac 200g", None, None,
                             etiqueta.regioes, lay.dpi, fontes)
    assert aj.nome == "Creme de Leite Italac"
    assert aj.descritor == "200 g"

    # dedupe: o descritor JÁ diz o peso — não vira "200 g · 200 g"
    aj2 = precedencia_do_nome("Creme de Leite Italac 200g", "200 g", None,
                              etiqueta.regioes, lay.dpi, fontes)
    assert aj2.descritor.count("200") == 1


# ---------------------------------------------------------------------------
# a prova-mestra: o compositor CHAMA a cadeia (confecção == alfaiataria)
# ---------------------------------------------------------------------------


def test_n1_a_confeccao_alcanca_a_alfaiataria_byte_a_byte(tmp_path):
    """A página composta com o dado CRU (o nome inteiro da tabela, sem
    descritor — como o caminho do dono produz) sai BYTE-IDÊNTICA à
    composta com o dado alfaiatado à mão (nome curto + descritor do
    OCTAVUS). É a definição do conserto: o app faz sozinho o que o
    builder fazia item a item."""
    _requer_pacote()
    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.encartes import layout_de_encarte

    fontes = _fontes_reais(tmp_path)
    lay = layout_de_encarte("segunda-frios", _PACOTE)
    pag = lay.paginas[0]

    cru = {"celula-3": DadosProduto("Leite Condensado Triangulo 395g",
                                    preco_por=None)}
    alfaiatado = {"celula-3": DadosProduto("Leite Condensado",
                                           descritor="Triangulo · 395 g",
                                           preco_por=None)}
    img_cru = compor_pagina(lay, pag, cru, fontes_dir=fontes, dpi=96)
    img_mao = compor_pagina(lay, pag, alfaiatado, fontes_dir=fontes, dpi=96)
    assert img_cru.tobytes() == img_mao.tobytes(), \
        "a composição do dado cru difere da alfaiatada — a cadeia não rodou"

    # e o descritor MATERIALIZOU: a faixa do SUBTITULO da celula-3 tem
    # tinta no cru (antes do N1 ficava muda)
    from app.rendering.model import TipoRegiao
    from app.rendering.units import mm_para_px
    slot = next(s for s in pag.slots if s.id == "celula-3")
    sub = next(r for r in slot.regioes if r.tipo == TipoRegiao.SUBTITULO)
    x = round(mm_para_px(sub.rect.x_mm, 96))
    y = round(mm_para_px(sub.rect.y_mm, 96))
    w = round(mm_para_px(sub.rect.larg_mm, 96))
    h = round(mm_para_px(sub.rect.alt_mm, 96))
    vazio = compor_pagina(lay, pag, {"celula-3": DadosProduto(
        "Leite Condensado")}, fontes_dir=fontes, dpi=96)
    faixa_cru = img_cru.crop((x, y, x + w, y + h)).tobytes()
    faixa_vazia = vazio.crop((x, y, x + w, y + h)).tobytes()
    assert faixa_cru != faixa_vazia, \
        "o SUBTITULO da celula-3 ficou mudo — o peso não migrou"


# ---------------------------------------------------------------------------
# N2 — a varredura do piso inerte: NENHUM nome em min_pt=6.0 nas 8 páginas
# ---------------------------------------------------------------------------


_CHAVES_8 = ["segunda-frios", "terca-do-pao", "quarta-das-ofertas",
             "quinta-do-peixe", "sexta-verde", "sabado-da-carne",
             "jornal-do-mes", "quintou"]


def test_n2_nenhum_nome_no_piso_inerte_nas_8_paginas():
    """N2: a régua RELATIVA universal (a lição da SEPTIMUS: toda régua
    tem FAIXA) — em TODA região NOME/SUBTITULO das 8 páginas, fixas
    INCLUÍDAS (o furo que deixou o Kit escapar: o teste do C1 iterava
    ``ocupaveis``, que exclui fixa): o piso mata o default inerte
    (>6.0), nunca passa do teto (≤max — o text_fit desenharia ACIMA do
    teto) e o corpo cede no máximo UM degrau (min ≥ max−3) — depois a
    precedência do N1 encurta pelo descritor, nunca encolhe a ilegível."""
    _requer_pacote()
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.model import TipoRegiao

    problemas = []
    for chave in _CHAVES_8:
        variantes = [layout_de_encarte(chave, _PACOTE)]
        if chave == "jornal-do-mes":     # o fluxo por seções cria jf-NN
            variantes.append(layout_de_encarte(
                chave, _PACOTE, secoes=[("Mercearia", 5), ("Bebidas", 4)]))
        for lay in variantes:
            for pag in lay.paginas:
                for s in pag.slots:
                    tem_sub = any(r2.tipo == TipoRegiao.SUBTITULO
                                  and r2.visivel for r2 in s.regioes)
                    for r in s.regioes:
                        if r.tipo not in (TipoRegiao.NOME,
                                          TipoRegiao.SUBTITULO):
                            continue
                        rot = f"{chave}/{s.id}/{r.tipo.value}"
                        if r.tamanho_min_pt <= 6.0:
                            problemas.append(f"{rot}: piso inerte "
                                             f"({r.tamanho_min_pt})")
                        if r.tamanho_min_pt > r.tamanho_max_pt:
                            problemas.append(f"{rot}: piso {r.tamanho_min_pt}"
                                             f" > teto {r.tamanho_max_pt}")
                        # ADENDO do dono (30/07, rastro): em célula SEM
                        # SUBTITULO (o Quintou) o range grande É o
                        # mecanismo — sem linha de descritor não há
                        # escada; o corpo desce (14,5→9,5, como o
                        # publicado) e a revisora avisa. O degrau ≤3pt
                        # segue valendo onde a escada existe.
                        if tem_sub and \
                                r.tamanho_min_pt < r.tamanho_max_pt - 3.0 - 1e-6:
                            problemas.append(
                                f"{rot}: degrau {r.tamanho_max_pt}→"
                                f"{r.tamanho_min_pt} maior que 3pt")
    assert not problemas, "a calibração passou por cima de:\n" + \
        "\n".join(problemas)


def test_n2_a_fixa_da_segunda_esta_calibrada():
    """N2: o caso nomeado da ordem — a celula-1 (o Kit) estava em 6.0
    enquanto as demais tinham 17; agora o piso dela segue a régua."""
    _requer_pacote()
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.model import TipoRegiao

    lay = layout_de_encarte("segunda-frios", _PACOTE)
    fixa = next(s for s in lay.paginas[0].slots if s.fixa)
    nome = next(r for r in fixa.regioes if r.tipo == TipoRegiao.NOME)
    assert nome.tamanho_min_pt >= 17.0, (
        f"o Kit segue no piso {nome.tamanho_min_pt} — a calibração do "
        "C1 não chegou à fixa")


# ---------------------------------------------------------------------------
# N3 + F1 — a Mesa mostra a PÁGINA, não a marcação; portas visíveis
# ---------------------------------------------------------------------------


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


def test_n3_a_mesa_nao_pinta_badges_de_papel(raiz_tmp):
    """N3: os badges do RG-57 ("¶ Livre", "📅 Validade") são ajuda de
    edição do LAYOUT — o Ateliê os pinta, a MESA não (o dono viu os
    badges e mandou a foto achando que era a página). Prova por TINTA:
    o mesmo item pinta com a flag ligada e cala com ela desligada."""
    from PySide6.QtGui import QImage, QPainter
    from app.qt.canvas import CanvasView
    from app.qt.telas.mesa import MesaTela
    from app.rendering.compositor import DadosProduto
    from app.rendering.model import (
        LayoutDef, Pagina, PapelTexto, Regiao, Retangulo, Slot, TipoRegiao,
    )
    _app()
    m = MesaTela()
    try:
        assert m.area.canvas.badges_de_papel is False, \
            "a Mesa está pintando badge de papel (N3)"
    finally:
        m.close()
    assert CanvasView().badges_de_papel is True   # o Ateliê continua

    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("c", [
        Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(10, 10, 40, 12),
               papel_texto=PapelTexto.LIVRE, texto_fixo="Nº 02"),
    ])])])
    c = CanvasView()
    c.resize(400, 300)
    c.show()
    c.carregar(lay, DadosProduto("x"))
    try:
        item = c._itens[0]

        def _pinta() -> bytes:
            img = QImage(120, 60, QImage.Format.Format_ARGB32)
            img.fill(0)
            p = QPainter(img)
            item._paint_badge_papel(p)
            p.end()
            return bytes(img.constBits())

        c.badges_de_papel = True
        com = _pinta()
        c.badges_de_papel = False
        sem = _pinta()
        assert com != sem, "a flag não muda nada — o badge pinta sempre"
        base = QImage(120, 60, QImage.Format.Format_ARGB32)
        base.fill(0)
        assert sem == bytes(base.constBits()), \
            "com a flag desligada o badge AINDA deixou tinta"
    finally:
        c.close()


def test_n3_ver_como_vai_sair_mostra_a_composicao_real(raiz_tmp, monkeypatch):
    """N3: o botão da Mesa abre a COMPOSIÇÃO (a receita do Exportar),
    nunca uma captura do canvas — provado por CONTEÚDO: o diálogo exibe
    exatamente a imagem que ``paginas_compostas`` devolveu."""
    from PIL import Image
    from PySide6.QtWidgets import QDialog, QLabel
    from app.qt.telas.mesa import MesaTela
    from app.rendering.model import (
        LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao,
    )
    _app()
    m = MesaTela()
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("c", [
        Regiao(TipoRegiao.NOME, Retangulo(10, 10, 40, 12), nome="Nome"),
    ])])])
    m._layout = lay
    m.area.carregar(lay, {})

    vermelha = Image.new("RGB", (400, 400), "#d01818")
    monkeypatch.setattr(m, "paginas_compostas", lambda: [vermelha])
    capturado = []
    monkeypatch.setattr(QDialog, "exec",
                        lambda self: capturado.append(self) or 0)
    try:
        m._ver_como_vai_sair()
        assert capturado, "o diálogo da prévia não abriu"
        dlg = capturado[0]
        pix = next((lb.pixmap() for lb in dlg.findChildren(QLabel)
                    if lb.pixmap() and not lb.pixmap().isNull()), None)
        assert pix is not None, "o diálogo não mostra imagem nenhuma"
        cor = pix.toImage().pixelColor(pix.width() // 2, pix.height() // 2)
        assert (cor.red(), cor.green(), cor.blue()) == (0xD0, 0x18, 0x18), \
            "a imagem do diálogo NÃO é a composição devolvida pela receita"
    finally:
        m.close()


def test_f2_o_caminho_inteiro_do_dono_por_gesto(raiz_tmp, monkeypatch):
    """F2 (a ordem curta do ROTEIRO): o CAMINHO inteiro que o dono faz —
    Ateliê → duplo-clique no encarte → a MESA REAL carrega → importar a
    tabela (linhas CRUAS, o diálogo de conciliação respondido por
    GESTO) → auto-preencher → salvar → REABRIR. Cada peça tinha teste;
    o caminho nunca teve. Prova por CONTEÚDO: o Kit fixo sobreviveu no
    template e o mapa por uid sobreviveu ao congelamento.

    Declarado: a conciliação roda pela via síncrona (o worker
    ``Trabalhador`` é o mesmo da fase 9, já testado); o Kit usa preço
    FIXO (o "da semana" pela tabela tem teste próprio na TER)."""
    _requer_pacote()
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from app.core import projetos
    from app.core.database import Database
    from app.core.repositories import ProdutoRepositorio
    from app.qt.telas import servico
    from app.qt.telas.atelie import AtelieTela
    from app.qt.telas.colagem import linhas_para_tuplas, parse_colagem
    from app.qt.telas.mesa import MesaTela
    from app.rendering.compositor import _dados_do_conteudo_fixo
    from app.rendering.encartes import importar_pacote
    from app.rendering.persistencia import (
        carregar_layout, listar_layouts, salvar_layout,
    )
    from app.tests.gestos import clicar, drenar
    from app.tests.test_bloco_d_f13 import _vigia_salvar_projeto
    _app()

    # o banco do dono: os encartes importados + o Kit configurado na fixa
    db = Database().init()
    try:
        with db.Session() as s:
            importar_pacote(s, _PACOTE, raiz=raiz_tmp)
            s.commit()
            alvo = next(r for r in listar_layouts(s)
                        if r.nome == "Segunda dos Frios")
            lay0 = carregar_layout(s, alvo.id, raiz=raiz_tmp)
            fixa0 = next(sl for p in lay0.paginas for sl in p.slots
                         if sl.fixa)
            fixa0.conteudo_fixo = {
                "nome": "Kit Burguer Senepol BBX",
                "descritor": "blend senepol · 4 un × 120 g",
                "preco": "39,00", "preco_da_semana": False,
                "imagem": None}
            salvar_layout(s, "Segunda dos Frios", lay0,
                          layout_id=alvo.id, raiz=raiz_tmp)
            # o acervo (ponto de partida): a tabela da semana casa VERDE
            repo = ProdutoRepositorio(s)
            for nome in ("Creme de Leite Italac 200 g",
                         "Leite Condensado Triangulo 395 gr",
                         "Batata Palha Bulnez Crocante 100 g",
                         "Azeite Gallo Extra Virgem Classico 500 ml",
                         "Suco de Uva Aurora Tinto TP/1,5LT",
                         "Leite Integral Parmalat 1 LT",
                         "Oleo de Soja Concordia 900 ml"):
                repo.importar(nome)
            s.commit()
    finally:
        db.engine.dispose()

    # 1) Ateliê → DUPLO-CLIQUE no encarte → a Mesa REAL recebe (o fio
    # do editor_app._abrir_layout, com a MesaTela de verdade)
    m = MesaTela()
    m.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    abertos = []

    def _abrir_layout(ldef, tipo, nome):
        abertos.append((tipo, nome))
        m.carregar_layout(ldef, ldef.arquivo_fundo, nome_layout=nome)

    tela = AtelieTela(ao_abrir=_abrir_layout)
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
        assert r.isValid() and r.width() > 0, "o item não tem retângulo"
        QTest.mouseClick(tela.lista.viewport(),
                         Qt.MouseButton.LeftButton,
                         Qt.KeyboardModifier.NoModifier, r.center())
        QTest.mouseDClick(tela.lista.viewport(),
                          Qt.MouseButton.LeftButton,
                          Qt.KeyboardModifier.NoModifier, r.center())
        drenar()
        assert abertos and abertos[0][1] == "Segunda dos Frios", (
            "o duplo-clique do Ateliê não chegou à Mesa")
        assert m.area.canvas._layout is not None

        # 2) importar a tabela CRUA (o parser + a conciliação + o
        # diálogo REAL respondido por gesto — "Concluir")
        texto = ("CREME DE LEITE ITALAC 200 G ______ por 2,44\n"
                 "LEITE CONDENSADO TRIANGULO 395 GR ______ SÓ 7,44\n"
                 "BATATA PALHA BULNEZ CROCANTE 100 G ______ por 6,66\n"
                 "AZEITE GALLO EXTRA VIRGEM CLASSICO 500 ML ______ 38,80\n"
                 "SUCO DE UVA AURORA TINTO TP/1,5LT ______ SÓ 19,99\n"
                 "LEITE INTEGRAL PARMALAT 1 LT ______ por 5,95\n"
                 "OLEO DE SOJA CONCORDIA 900 ML ______ por 7,70")
        tuplas = linhas_para_tuplas(parse_colagem(texto))
        assert len(tuplas) == 7, f"o parser perdeu linha: {tuplas}"
        resultado = servico.conciliar_linhas(tuplas, lambda *a, **k: None)
        # vigia local que RETENTA (o Concluir pode estar desabilitado
        # por um instante) + guarda de escape para o teste nunca pendurar
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QAbstractButton, QApplication
        estado = {"viu": [], "cliques": 0, "escapou": False}

        def _tic():
            cx = QApplication.activeModalWidget()
            if cx is None:
                return
            nome_cx = type(cx).__name__
            if nome_cx not in estado["viu"]:
                estado["viu"].append(nome_cx)
            b = next((x for x in cx.findChildren(QAbstractButton)
                      if x.text().strip() == "Concluir"), None)
            if b is not None and b.isEnabled() and b.isVisible():
                estado["cliques"] += 1
                clicar(b)

        t = QTimer()
        t.setInterval(30)
        t.timeout.connect(_tic)
        t.start()

        def _escape():
            cx = QApplication.activeModalWidget()
            if cx is not None:
                estado["escapou"] = True
                cx.reject()

        guarda = QTimer()
        guarda.setSingleShot(True)
        guarda.setInterval(20000)
        guarda.timeout.connect(_escape)
        guarda.start()
        try:
            m._conciliar(resultado)
        finally:
            t.stop()
            guarda.stop()
        assert not estado["escapou"], (
            f"a conciliação não fechou pelo clique — viu {estado['viu']}, "
            f"cliques {estado['cliques']}")
        assert estado["viu"], "o diálogo de conciliação nem abriu"
        assert len(m._itens) == 7, (
            f"a estante não ficou com os 7 ({len(m._itens)}) — "
            "a conciliação não saiu toda VERDE")

        # 3) auto-preencher pelo BOTÃO — a fixa fica fora, 7 em 7
        m.show()
        drenar()
        if m.btn_preencher.isVisible():
            clicar(m.btn_preencher)
        else:
            m._auto_preencher()
        drenar()
        fixa_id = fixa0.id
        assert fixa_id not in m._mapa, "o auto-preencher invadiu a fixa"
        assert len(m._mapa) == 7, (
            f"a tabela de 7 não fechou as 7 livres ({len(m._mapa)})")

        # 4) salvar (o diálogo REAL pelo teclado) e REABRIR noutra Mesa
        with _vigia_salvar_projeto(nome="Segunda F2") as vs:
            m._salvar_projeto()
        assert vs["disparou"] and m._projeto_id, "o salvar não congelou"
        m2 = MesaTela()
        m2.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        try:
            p = projetos.abrir_projeto(m._projeto_id)
            m2.abrir_projeto_congelado(p)
            drenar()
            assert m2._mapa == m._mapa and len(m2._mapa) == 7, (
                "o mapa por uid não sobreviveu ao congelamento")
            lay2 = m2.area.canvas._layout or m2._layout
            fixa2 = next(sl for pg in lay2.paginas for sl in pg.slots
                         if sl.fixa)
            assert fixa2.conteudo_fixo, "o Kit sumiu do template ao reabrir"
            d_kit = _dados_do_conteudo_fixo(fixa2.conteudo_fixo)
            assert d_kit.nome == "Kit Burguer Senepol BBX"
            assert str(d_kit.preco_por) == "39.00"
        finally:
            m2.close()
            drenar()
    finally:
        m.close()
        tela.deleteLater()
        drenar()


def test_f1_a_celula_fixa_abre_os_fixos_pelo_menu(raiz_tmp):
    """F1: botão direito NA CÉLULA FIXA oferece "Conteúdo fixo desta
    célula…" (o gesto natural) — só na fixa, e só onde a Mesa ligou o
    fio (no Ateliê a entrada não existe, como o override)."""
    from app.qt.canvas import CanvasView
    from app.rendering.compositor import DadosProduto
    from app.rendering.model import (
        LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao,
    )
    _app()
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([
        Slot("livre", [Regiao(TipoRegiao.NOME,
                              Retangulo(10, 10, 40, 12), nome="Nome")]),
        Slot("fixa", [Regiao(TipoRegiao.NOME,
                             Retangulo(10, 40, 40, 12), nome="Nome")],
             fixa=True),
    ])])
    c = CanvasView()
    c.resize(400, 300)
    c.show()
    c.carregar(lay, DadosProduto("x"))
    chamados = []
    c.ao_itens_fixos = chamados.append
    try:
        slots = lay.paginas[0].slots
        it_fixa = next(i for i in c._itens if i.regiao is slots[1].regioes[0])
        _menu, acoes = it_fixa.montar_menu_contexto()
        alvo = next((a for a in acoes
                     if "conteúdo fixo" in a.text().lower()), None)
        assert alvo is not None, "a célula FIXA não oferece os fixos (F1)"
        acoes[alvo]()
        assert chamados == ["fixa"], "a ação não chamou o fio da Mesa"

        it_livre = next(i for i in c._itens
                        if i.regiao is slots[0].regioes[0])
        _m2, acoes2 = it_livre.montar_menu_contexto()
        assert not any("conteúdo fixo" in a.text().lower() for a in acoes2), \
            "célula LIVRE ganhou a entrada dos fixos"

        c.ao_itens_fixos = None            # o Ateliê: fio desligado
        _m3, acoes3 = it_fixa.montar_menu_contexto()
        assert not any("conteúdo fixo" in a.text().lower() for a in acoes3), \
            "a entrada aparece sem o fio da Mesa (vazaria no Ateliê)"
    finally:
        c.close()
