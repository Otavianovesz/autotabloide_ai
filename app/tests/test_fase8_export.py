"""FASE 8 — Exportação e publicação.

Cobre: perfis de exportação medidos em bytes (R-065), compartilhar (R-064),
marca d'água RASCUNHO + aprovação em 2 etapas (R-067/R-068), formatos sociais
reusando o compositor (R-140/141/145), vídeo com degradação sem ffmpeg
(R-139/142), e o reuso do compositor nos 4 formatos (uma cadeia só).
"""

import shutil
from decimal import Decimal
from pathlib import Path

import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication

from app.rendering import perfis, social, video
from app.rendering.compositor import DadosProduto
from app.rendering.marca_dagua import carimbar_rascunho


def _app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    reais = Path("AutoTabloide_System_Root/fontes")
    if reais.exists():
        for f in reais.glob("*.ttf"):
            shutil.copy(f, root.fontes / f.name)
    Database(root).init().engine.dispose()
    return root


def _dados(nome="Arroz Tio João 5kg", foto=None):
    return DadosProduto(nome, preco_por=Decimal("24.90"), preco_de=Decimal("29.90"),
                        imagem_path=foto)


def _peca(w=1181, h=1772, cor="white"):
    return Image.new("RGB", (w, h), cor)


# ===========================================================================
# R-065 — perfis de exportação + régua de bytes
# ===========================================================================

def test_perfil_whatsapp_escala_proporcional_lado_1080():
    """R-065/passo 4: WhatsApp escala o MAIOR lado para 1080, SEM deformar."""
    out, dpi = perfis.aplicar_perfil(_peca(1181, 1772),
                                     perfis.Perfil("W", "JPG", lado_maior_px=1080))
    assert max(out.size) == 1080                     # maior lado exato
    # proporção preservada (1181/1772 ≈ out.w/out.h)
    assert abs(out.width / out.height - 1181 / 1772) < 0.01


def test_perfil_stories_encaixa_exato_sem_esticar():
    """R-065: Stories 1080×1920 encaixa (contain + fundo), nunca estica. Verifica
    POR CONTEÚDO: uma peça 1181×1772 (proporção ~0.67) encaixada em 9:16 deixa
    BANDAS de fundo em cima/embaixo. Prova de mutação: um resize esticado (sem
    letterbox) preencheria as bandas com conteúdo e o teste cairia.
    (Reforço apontado pela minha frota adversarial: a versão anterior só checava
    o size — passaria mesmo esticando.)"""
    story = next(p for p in perfis.PERFIS_PADRAO if p.largura_px == 1080)
    peca = _peca(1181, 1772, (30, 60, 200))          # peça NÃO-branca
    out, dpi = perfis.aplicar_perfil(peca, story)
    assert out.size == (1080, 1920)
    branco = (255, 255, 255)
    # topo e base são a cor do fundo (letterbox), o centro é a peça (conteúdo)
    assert out.getpixel((540, 2)) == branco
    assert out.getpixel((540, 1917)) == branco
    assert out.getpixel((540, 960)) != branco


def test_perfil_impressao_mantem_e_grava_300dpi(tmp_path):
    """R-065/passo 3: Impressão mantém o tamanho e sai a 300 dpi — régua de bytes
    do PDF (mediabox em pontos = mm/25.4*72). Prova de mutação: dpi errado moveria
    a mediabox."""
    from pypdf import PdfReader
    from app.rendering.units import px_para_mm
    img = _peca(1181, 1772)                           # ~10×15cm @ 300dpi
    p = perfis.Perfil("Impr", "PDF", dpi=300)
    destino = perfis.exportar_com_perfil(img, tmp_path / "impr", p)
    assert destino.suffix == ".pdf"
    caixa = PdfReader(str(destino)).pages[0].mediabox
    larg_mm = px_para_mm(1181, 300)
    assert abs(float(caixa.width) - larg_mm / 25.4 * 72) < 0.5   # tamanho físico certo


def test_exportar_com_perfil_png_grava_dpi(tmp_path):
    """Régua de bytes do PNG: o dpi vai gravado no arquivo (info['dpi'])."""
    img = _peca(600, 800)
    p = perfis.Perfil("Story", "PNG", largura_px=1080, altura_px=1920, dpi=96)
    destino = perfis.exportar_com_perfil(img, tmp_path / "s", p)
    aberto = Image.open(destino)
    assert aberto.size == (1080, 1920)
    assert round(aberto.info["dpi"][0]) == 96


def test_perfis_configurados_padrao(raiz_tmp):
    """Sem Config, os 3 perfis padrão; salvar/ler faz round-trip."""
    padrao = perfis.perfis_configurados()
    assert [p.nome for p in padrao][:3] == [
        "WhatsApp (1080)", "Impressão (300 dpi)", "Stories (1080×1920)"]
    perfis.salvar_perfis([perfis.Perfil("Meu", "PNG", lado_maior_px=800)])
    assert [p.nome for p in perfis.perfis_configurados()] == ["Meu"]


# ===========================================================================
# R-067/R-068 — marca d'água RASCUNHO + aprovação
# ===========================================================================

def test_marca_dagua_muda_a_peca_sem_tocar_o_original(raiz_tmp):
    """R-067: a marca d'água RASCUNHO aparece (pixel) e NÃO altera o original.
    Prova de mutação: sem o alpha_composite, a peça sairia idêntica."""
    _app()
    original = _peca(400, 600, "white")
    antes = list(original.getdata())
    com = carimbar_rascunho(original)
    assert list(com.getdata()) != antes             # a marca apareceu
    assert list(original.getdata()) == antes        # o original intacto


def test_aprovar_exige_o_checklist(raiz_tmp):
    """R-068/passo 21: aprovar EXIGE a conferência — item sem foto/preço reprova
    com as faltas; tudo ok aprova. Não é clique cego."""
    from app.qt.telas import servico
    incompleto = [servico.ItemMesa("A", None, "VERDE", "A")]   # sem foto/preço
    ok, faltas = servico.aprovar_projeto(None, incompleto, None)
    assert ok is False and faltas                    # reprovou, com motivos
    bom = servico.ItemMesa("B", "5,00", "VERDE", "B")
    bom.imagem = "x.png"
    ok2, faltas2 = servico.aprovar_projeto(None, [bom], "ATÉ 20/07")
    assert ok2 is True and faltas2 == []


def test_pode_exportar_limpo_so_apos_aprovar(raiz_tmp):
    """R-068/passo 27 (guarda): projeto novo (id None) nunca exporta limpo;
    depois de aprovar um id, libera."""
    from app.core import projetos
    from app.qt.telas import servico
    assert servico.pode_exportar_limpo(None) is False
    projetos.aprovar(123)
    assert servico.pode_exportar_limpo(123) is True
    projetos.desaprovar(123)
    assert servico.pode_exportar_limpo(123) is False


def test_editar_aprovado_volta_a_rascunho(raiz_tmp):
    """R-068/passo 23: editar (salvar com conteúdo NOVO) um projeto aprovado TIRA
    a aprovação — a marca d'água volta. Prova de mutação: sem o hook no
    salvar_projeto, a aprovação sobreviveria à edição."""
    from app.core import projetos
    from app.rendering.cartaz import layout_cartaz_exemplo
    from app.qt.telas.servico import ItemMesa
    lay = layout_cartaz_exemplo()
    it = ItemMesa("Arroz", "5,00", "VERDE", "Arroz")
    pid = projetos.salvar_projeto("P1", "Sexta", "TABLOIDE", lay,
                                  [it.to_dict()], "ATÉ 20/07",
                                  mapa={"cartaz": it.uid})
    projetos.aprovar(pid)
    assert projetos.esta_aprovado(pid) is True
    # salva de novo com conteúdo MUDADO (preço diferente)
    it.preco = "9,00"
    projetos.salvar_projeto("P1", "Sexta", "TABLOIDE", lay, [it.to_dict()],
                            "ATÉ 20/07", mapa={"cartaz": it.uid}, projeto_id=pid)
    assert projetos.esta_aprovado(pid) is False       # editar rebaixou


# ===========================================================================
# R-140/141/145 — formatos sociais reusando o compositor
# ===========================================================================

@pytest.mark.parametrize("formato,larg,alt", [
    ("oferta_do_dia", 1080, 1080),
    ("oferta_do_dia_alto", 1080, 1350),
    ("carrossel", 1080, 1080),
    ("story", 1080, 1920),
    ("faixa", 1920, 1080),
])
def test_social_sai_no_tamanho_certo(raiz_tmp, formato, larg, alt):
    """R-141/140/145/passo 42+71 (régua): cada formato social sai no px exato
    (PIL medindo). Prova de mutação: proporção errada mudaria o size."""
    _app()
    img = social.compor_social(formato, _dados())
    assert img.size == (larg, alt)


def test_carrossel_gera_n_cards_na_ordem(raiz_tmp):
    """R-140/passo 33-36: 1 card por produto, NA ORDEM; N cards do mesmo tamanho."""
    _app()
    dados = [_dados("Arroz"), _dados("Feijão"), _dados("Óleo")]
    cards = social.compor_carrossel(dados)
    assert len(cards) == 3
    assert all(c.size == (1080, 1080) for c in cards)


def test_social_desenha_conteudo_nao_fica_branco(raiz_tmp, tmp_path):
    """R-141: o card social REALMENTE desenha o item (não fica em branco). Prova
    por conteúdo (pixel diferente do fundo)."""
    _app()
    foto = tmp_path / "p.png"
    Image.new("RGB", (300, 300), (200, 40, 40)).save(foto)
    img = social.compor_social("oferta_do_dia", _dados(foto=str(foto)))
    branco = Image.new("RGB", img.size, "white")
    assert list(img.getdata()) != list(branco.getdata())


# ===========================================================================
# R-139/142 — vídeo (com ffmpeg real + degradação sem ele)
# ===========================================================================

def test_video_degrada_sem_ffmpeg(monkeypatch, tmp_path):
    """R-142/passo 54+59 (I2): SEM ffmpeg, o vídeo devolve (None, aviso) e NÃO
    trava. Prova de mutação: sem o ramo de degradação, levantaria/travaria."""
    monkeypatch.setattr(video.shutil, "which", lambda nome: None)
    mp4, aviso = video.gerar_video_paginas([_peca(200, 300)], tmp_path / "v.mp4")
    assert mp4 is None and aviso and "ffmpeg" in aviso.lower()


@pytest.mark.skipif(video.ffmpeg_disponivel() is None,
                    reason="ffmpeg não instalado neste ambiente")
def test_video_slideshow_frames_e_duracao_exatos(tmp_path):
    """R-142/passo 56+60 (reescrito no GATE 2.3 da ordem F11.5 — só contava
    frames): além da contagem EXATA, a FIDELIDADE por pixel — o frame do
    vídeo tem a COR da página de origem (página 1 vermelha no frame 0;
    página 2 verde no frame do meio). Prova de mutação: embaralhar a ordem
    das páginas (ou recompor com outro conteúdo) muda a cor e falha."""
    pgs = [_peca(400, 600, c) for c in ("red", "green", "blue")]
    mp4, aviso = video.gerar_video_paginas(pgs, tmp_path / "t.mp4",
                                           seg_por_pagina=1.0, fps=24)
    assert mp4 is not None and mp4.exists() and aviso is None
    if video.ffprobe_disponivel():
        assert video.contar_frames(mp4) == 72
        assert abs(video.duracao_video(mp4) - 3.0) < 0.15

    def _cor_central(png):
        img = Image.open(png).convert("RGB")
        return img.getpixel((img.width // 2, img.height // 2))

    # frame 0 = página 1 (vermelha); frame 36 (meio) = página 2 (verde) —
    # tolerância p/ compressão do H.264
    f0 = video.frame_do_video(mp4, 0, tmp_path / "f0.png")
    f36 = video.frame_do_video(mp4, 36, tmp_path / "f36.png")
    assert f0 is not None and f36 is not None
    r, g, b = _cor_central(f0)
    assert r > 180 and g < 80 and b < 80, (r, g, b)      # vermelho de verdade
    r, g, b = _cor_central(f36)
    assert g > 100 and r < 80 and b < 80, (r, g, b)      # verde de verdade


@pytest.mark.skipif(video.ffmpeg_disponivel() is None,
                    reason="ffmpeg não instalado neste ambiente")
def test_video_story_gera_mp4(tmp_path):
    """R-139: o Story vertical vira um MP4 curto (respiro leve)."""
    mp4, aviso = video.gerar_video_story(_peca(1080, 1920, "navy"),
                                         tmp_path / "s.mp4", dur_s=1.0, fps=24)
    assert mp4 is not None and mp4.exists() and aviso is None


# ===========================================================================
# R-064 — compartilhar (limite do SO honesto)
# ===========================================================================

def test_copiar_imagem_para_area(raiz_tmp, tmp_path):
    """R-064/passo 9: "Copiar imagem" põe a peça na área de transferência."""
    _app()
    from app.qt.telas import compartilhar
    png = tmp_path / "peca.png"
    Image.new("RGB", (50, 50), (10, 120, 30)).save(png)
    assert compartilhar.copiar_imagem(png) is True
    from PySide6.QtWidgets import QApplication
    assert not QApplication.clipboard().image().isNull()   # tem imagem colável


def test_compartilhar_documenta_limite_do_so():
    """R-064/passo 8 (I2): a limitação do SO é dita honestamente (não promete o
    que o Windows não faz)."""
    from app.qt.telas import compartilhar
    txt = compartilhar.LIMITACAO_SO.lower()
    assert "whatsapp" in txt and "copiar" in txt


# ===========================================================================
# Bloco E — reuso do compositor: 1 cadeia, 4 formatos
# ===========================================================================

def test_reuso_compositor_mesmo_item_4_formatos(raiz_tmp, tmp_path):
    """Passo 72: o MESMO DadosProduto compõe tabloide, Oferta do Dia, carrossel e
    story — uma cadeia só (compor_pagina), sem motor novo. Cada um no seu tamanho."""
    _app()
    from app.rendering.cartaz import layout_cartaz_exemplo
    from app.rendering.compositor import compor_pagina
    foto = tmp_path / "p.png"
    Image.new("RGB", (300, 300), (30, 80, 200)).save(foto)
    d = _dados(foto=str(foto))
    # tabloide (cartaz) — 1 slot "cartaz"
    lay = layout_cartaz_exemplo()
    tab = compor_pagina(lay, lay.paginas[0], {"cartaz": d})
    assert tab.size[0] > 0
    # os 3 sociais reusam o MESMO d
    of = social.compor_social("oferta_do_dia", d)
    card = social.compor_social("carrossel", d)
    st = social.compor_social("story", d)
    assert of.size == (1080, 1080)
    assert card.size == (1080, 1080)
    assert st.size == (1080, 1920)


# ===========================================================================
# Casca — marca d'água no export real + encerramento do worker (lei exit-0)
# ===========================================================================

def test_tabloide_marca_dagua_liga_desliga_com_aprovacao(raiz_tmp, tmp_path,
                                                         monkeypatch):
    """R-067/068/passo 26 (integração): exportar NÃO aprovado sai com RASCUNHO;
    aprovado sai LIMPO — a mesma peça, só a marca muda. Prova de mutação: sem o
    ramo `if marca` no _trabalho, os dois arquivos seriam idênticos."""
    from PySide6.QtWidgets import QFileDialog
    from app.qt.telas import servico
    from app.qt.telas.mesa import MesaTela
    from app.rendering.cartaz import layout_cartaz_exemplo
    _app()
    m = MesaTela()
    lay = layout_cartaz_exemplo()
    m._layout = lay
    m._fundo = None
    m.area.carregar(lay, {})
    it = servico.ItemMesa("Arroz Tio João 5kg", "5,00", "VERDE",
                          "Arroz Tio João 5kg")
    m._itens = [it]
    m._mapa = {"cartaz": it.uid}
    monkeypatch.setattr("app.qt.telas.prevoo.confirmar_pre_voo",
                        lambda *a, **k: True)

    def _export(nome, aprovado):
        monkeypatch.setattr(servico, "pode_exportar_limpo", lambda pid: aprovado)
        m._salvo = aprovado                  # limpo exige salvo E aprovado
        saida = tmp_path / nome
        monkeypatch.setattr(QFileDialog, "getSaveFileName",
                            lambda *a, **k: (str(saida), "PNG (*.png)"))
        m._exportar()
        m._trabalhos.encerrar(5000)          # espera o worker gravar
        QApplication.processEvents()
        return saida

    rascunho = _export("rascunho.png", aprovado=False)
    limpo = _export("limpo.png", aprovado=True)
    assert rascunho.exists() and limpo.exists()
    r = list(Image.open(rascunho).convert("RGB").getdata())
    c = list(Image.open(limpo).convert("RGB").getdata())
    assert r != c                            # o rascunho tem marca; o limpo não
    m.close()


def test_editar_sem_salvar_derruba_a_aprovacao_limpa(raiz_tmp, monkeypatch):
    """Achado do revisor adversarial (R-068): aprovado+salvo exporta limpo; MAS
    editar em memória (sem salvar) derruba a aprovação limpa — a marca d'água
    volta. Prova de mutação: sem o `_salvo` em `esta_aprovado`, editar sem salvar
    exportaria limpo (o buraco)."""
    from app.qt.telas import servico
    from app.qt.telas.mesa import MesaTela
    _app()
    m = MesaTela()
    m._projeto_id = 7
    monkeypatch.setattr(servico, "pode_exportar_limpo", lambda pid: True)
    m._marcar_salvo(True)                    # salvo + aprovado
    assert m.esta_aprovado() is True
    m._marcar_salvo(False)                   # editou em memória (dirty)
    assert m.esta_aprovado() is False        # a aprovação LIMPA caiu (marca volta)
    m.close()


def test_publicar_dialog_done_encerra_worker(raiz_tmp):
    """Lei exit-0 (teste dedicado do worker novo): PublicarDialog.done() encerra
    os trabalhos — nada vivo no fechamento. Prova de mutação: sem o encerrar no
    done(), o worker (sleep) sobrevive sob o gerenciador."""
    import time as _t

    from app.qt.telas.mesa import MesaTela
    from app.qt.telas.publicar_dialog import PublicarDialog
    from app.qt.telas.servico import ItemMesa
    from app.qt.workers import Trabalhador
    _app()
    m = MesaTela()
    m._itens = [ItemMesa("A", "5,00", "VERDE", "A")]
    dlg = PublicarDialog(m, m)
    trab = Trabalhador(lambda st: _t.sleep(0.5))
    dlg._trabalhos.rodar(trab)
    assert trab in dlg._trabalhos._vivos
    dlg.done(0)                              # encerra JUNTA o worker (espera)
    # a prova do exit-0: nada NATIVO rodando no fechamento (o worker foi juntado).
    # Sem o encerrar no done(), o sleep de 0,5s ainda estaria rodando aqui.
    assert not trab.isRunning()
    m.close()


def test_fila_lote_um_perfil_com_erro_nao_para_os_outros(raiz_tmp, tmp_path):
    """R-066/passo 11-12 (I2): a fila de exportação roda em worker e um perfil
    com erro NÃO derruba os outros — fica marcado e a fila segue até o fim."""
    _app()
    from app.qt.workers import TrabalhadorFila
    from app.rendering.perfis import Perfil, exportar_com_perfil
    peca = _peca(200, 300)

    def _um(perfil):
        if perfil.nome == "RUIM":
            raise RuntimeError("falhou de propósito")
        return str(exportar_com_perfil(peca, tmp_path / perfil.nome, perfil))

    pares = [("A", Perfil("A", "PNG", lado_maior_px=100)),
             ("RUIM", Perfil("RUIM", "PNG")),
             ("C", Perfil("C", "PNG", lado_maior_px=120))]
    prontos, erros, terminou = [], [], []
    fila = TrabalhadorFila(pares, _um)
    fila.item_pronto.connect(lambda n, r: prontos.append(n))
    fila.item_falhou.connect(lambda n, m: erros.append(n))
    fila.fila_terminou.connect(lambda: terminou.append(True))
    fila.start()
    fila.wait(5000)
    QApplication.processEvents()
    assert set(prontos) == {"A", "C"}        # os bons saíram
    assert erros == ["RUIM"]                 # o ruim marcado, nominal (I2)
    assert terminou == [True]                # a fila terminou até o fim


def test_lote_multipagina_nao_perde_paginas(raiz_tmp, tmp_path, monkeypatch):
    """[achado da minha frota adversarial] O lote de perfis NÃO come páginas: um
    tabloide de 2 páginas gera 2 arquivos por perfil (_p1/_p2). Antes, o lote
    pegava só `paginas[0]` e perdia o resto EM SILÊNCIO (violava I2)."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QFileDialog
    from app.qt.telas.exportar_dialog import ExportarDialog
    from app.qt.telas.mesa import MesaTela
    from app.qt.telas.servico import ItemMesa
    _app()
    m = MesaTela()
    m._itens = [ItemMesa("A", "5,00", "VERDE", "A")]
    monkeypatch.setattr(m, "paginas_compostas",
                        lambda: [_peca(200, 300, "red"), _peca(200, 300, "blue")])
    monkeypatch.setattr(m, "esta_aprovado", lambda: True)   # foco nas páginas
    dlg = ExportarDialog(m, m)
    for i in range(dlg.lista.count()):        # marca só o 1º perfil
        dlg.lista.item(i).setCheckState(
            Qt.CheckState.Checked if i == 0 else Qt.CheckState.Unchecked)
    monkeypatch.setattr(QFileDialog, "getExistingDirectory",
                        lambda *a, **k: str(tmp_path))
    dlg._exportar()
    dlg._trabalhos.encerrar(6000)
    QApplication.processEvents()
    assert len(dlg._gerados) == 2             # 2 páginas → 2 arquivos (nada perdido)
    m.close()


def test_cartaz_da_fabrica_tambem_leva_a_marca_dagua(raiz_tmp, tmp_path,
                                                     monkeypatch):
    """[CRÍTICO achado da minha frota] A Fábrica de cartazes é a 2ª PORTA de
    exportação — também aplica a marca d'água RASCUNHO quando NÃO aprovado (um
    cartaz de preço errado não pode ir LIMPO ao PDV). Prova de mutação: sem o
    ramo `if marca` no fabrica._exportar, os dois PDFs seriam idênticos."""
    from PySide6.QtWidgets import QFileDialog
    from app.qt.telas import servico
    from app.qt.telas.fabrica import FabricaTela
    _app()
    f = FabricaTela()
    f._itens = [servico.ItemMesa("A", "2,99", "VERDE", "Produto A",
                                 preco_de="3,99")]
    f._recarregar_lista()
    monkeypatch.setattr("app.qt.telas.prevoo.confirmar_pre_voo",
                        lambda *a, **k: True)

    def _export(nome, aprovado):
        monkeypatch.setattr(servico, "pode_exportar_limpo", lambda pid: aprovado)
        saida = tmp_path / nome
        monkeypatch.setattr(QFileDialog, "getSaveFileName",
                            lambda *a, **k: (str(saida), "PDF (*.pdf)"))
        f._exportar()
        f._trabalhos.encerrar(6000)
        QApplication.processEvents()
        return saida

    rascunho = _export("cart_rascunho.pdf", aprovado=False)
    limpo = _export("cart_limpo.pdf", aprovado=True)
    assert rascunho.exists() and limpo.exists()
    # compara a IMAGEM EMBUTIDA no PDF (conteúdo) — os bytes do PDF diferem por
    # metadados/timestamp, então byte-diff seria um teste FALSO (a mutação
    # passaria). A imagem extraída é determinística: com a marca, difere.
    from pypdf import PdfReader

    def _img(caminho):
        ims = PdfReader(str(caminho)).pages[0].images
        return ims[0].data if ims else b""

    assert _img(rascunho) != _img(limpo)     # o rascunho tem a marca; o limpo não
    f.close()


def test_exportar_dialog_done_encerra_worker(raiz_tmp):
    """Lei exit-0: ExportarDialog.done() encerra a fila — nada vivo no fechamento."""
    import time as _t

    from app.qt.telas.exportar_dialog import ExportarDialog
    from app.qt.telas.mesa import MesaTela
    from app.qt.telas.servico import ItemMesa
    from app.qt.workers import Trabalhador
    _app()
    m = MesaTela()
    m._itens = [ItemMesa("A", "5,00", "VERDE", "A")]
    dlg = ExportarDialog(m, m)
    assert dlg.lista.count() == 3            # 3 perfis padrão carregados
    trab = Trabalhador(lambda st: _t.sleep(0.5))
    dlg._trabalhos.rodar(trab)
    dlg.done(0)
    assert not trab.isRunning()              # juntado no fechamento
    m.close()
