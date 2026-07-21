"""FASE 5 — Editor II: ferramentas de profissional.

Cresce ao longo da fase (um bloco por vez). Bloco A: campos de texto com
papel nomeado (RG-57/R-153) — modelo idempotente, conteúdo composto POR
PAPEL (por conteúdo, não por "não deu exceção"), e a LEI DA CASA reconfirmada:
região TEXTO_LEGAL — seja qual for o papel — segue NÃO-ocupável e o pré-voo
a ignora (nunca em silêncio, I2).
"""

from app.rendering.compositor import DadosProduto, compor_pagina, texto_composto_legal
from app.rendering.model import (
    Ajuste, LayoutDef, Mascara, Pagina, PapelPreco, PapelTexto, Regiao,
    Retangulo, Slot, TipoRegiao,
)


def _legal(papel, texto_fixo=None, rect=(0, 0, 50, 10)):
    return Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(*rect),
                  papel_texto=papel, texto_fixo=texto_fixo)


# --- Passo 4: modelo idempotente (semente da migração do Bloco E) -----------

def test_papel_texto_serializa_idempotente():
    """to_dict/from_dict preservam o papel; layout ANTIGO (sem a chave) cai em
    LIVRE (padrão seguro) sem quebrar — base da migração idempotente (passo 63/64)."""
    reg = _legal(PapelTexto.VALIDADE)
    d = reg.to_dict()
    assert d["papel_texto"] == "VALIDADE"
    assert Regiao.from_dict(d).papel_texto is PapelTexto.VALIDADE

    d_antigo = reg.to_dict()
    del d_antigo["papel_texto"]                      # simula layout pré-F5
    assert Regiao.from_dict(d_antigo).papel_texto is PapelTexto.LIVRE


# --- Passo 15: o texto composto corresponde ao papel (POR CONTEÚDO) ---------

def test_texto_composto_por_papel():
    """Cada papel puxa o texto da sua fonte correta. Prova de mutação embutida:
    o papel VALIDADE devolve a validade VIVA do evento, ignorando um texto_fixo
    velho — se o helper ignorasse o papel, devolveria "TEXTO ANTIGO" e falharia."""
    dados = DadosProduto("Cerveja", texto_legal="OFERTA VÁLIDA DE 17/07 ATÉ 20/07")

    val = _legal(PapelTexto.VALIDADE, texto_fixo="TEXTO ANTIGO")
    assert texto_composto_legal(val, dados) == "OFERTA VÁLIDA DE 17/07 ATÉ 20/07"
    assert "ATÉ" in texto_composto_legal(val, dados)   # RG-58: o "até" nunca some

    dica = _legal(PapelTexto.DICA, texto_fixo="Combina com pão quentinho")
    assert texto_composto_legal(dica, dados) == "Combina com pão quentinho"

    legal = _legal(PapelTexto.LEGAL,
                   texto_fixo="Bebida alcoólica — venda proibida para menores de 18 anos")
    assert "menores de 18" in texto_composto_legal(legal, dados)

    livre = _legal(PapelTexto.LIVRE, texto_fixo="Promoção relâmpago")
    assert texto_composto_legal(livre, dados) == "Promoção relâmpago"


def test_texto_composto_legado_byte_identico():
    """O ramo não-VALIDADE é byte-idêntico à heurística legada
    (texto_fixo or texto_legal or "") — layout antigo (todo LIVRE) não muda."""
    dados = DadosProduto("X", texto_legal="Válido até 20/07")
    # texto_fixo presente vence a validade (como o legado `fixo or validade`)
    assert texto_composto_legal(_legal(PapelTexto.LIVRE, "Fica a Dica"), dados) == "Fica a Dica"
    # texto_fixo ausente cai na validade (como o legado `None or validade`)
    assert texto_composto_legal(_legal(PapelTexto.LIVRE, None), dados) == "Válido até 20/07"


# --- Passo 12 + 16: LEI DA CASA (6ª aplicação do tipo/porta nova) -----------

def test_lei_da_casa_papel_texto_nao_ocupavel():
    """TEXTO_LEGAL com QUALQUER papel novo (validade/dica) segue NÃO-ocupável:
    nenhum item é engolido por ele. Prova de mutação: se TEXTO_LEGAL entrasse
    em TIPOS_CONTEUDO, os slots de papel virariam ocupáveis e o assert cairia."""
    from app.qt.telas import servico
    from app.rendering.grade import ocupaveis, ordenar_slots_visualmente

    conteudo = [Slot(f"celula_{i}",
                     [Regiao(TipoRegiao.NOME, Retangulo(10, 10 + i, 20, 5))],
                     origem_mm=(10, 10 + i * 6)) for i in range(3)]
    slot_validade = Slot("livre_validade", [_legal(PapelTexto.VALIDADE, rect=(60, 40, 30, 8))],
                         origem_mm=(60, 40))
    slot_dica = Slot("livre_dica", [_legal(PapelTexto.DICA, "Combina com pão", (60, 60, 30, 8))],
                     origem_mm=(60, 60))
    lay = LayoutDef(100, 120, dpi=100,
                    paginas=[Pagina(conteudo + [slot_validade, slot_dica])])

    uteis = ocupaveis(ordenar_slots_visualmente(lay.paginas[0].slots))
    ids = {s.id for s in uteis}
    assert ids == {"celula_0", "celula_1", "celula_2"}   # os 2 de papel ficam de fora

    # 4 itens p/ 3 slots ocupáveis: o 4º fica FORA — nunca cai num slot de papel
    itens = [servico.ItemMesa(f"P{i}", "1,00", "VERDE", f"P{i}") for i in range(4)]
    mapa = {s.id: it.uid for s, it in zip(uteis, itens)}
    assert len(mapa) == 3
    assert "livre_validade" not in mapa and "livre_dica" not in mapa
    assert itens[3].uid not in mapa.values()


def test_lei_da_casa_papel_texto_prevoo_acusa_nunca_silencia():
    """I2: se um mapa velho apontar um produto para um slot de papel
    (validade/dica), o pré-voo ACUSA "célula decorativa" — nunca desenha em
    silêncio. Também é prova de mutação de TIPOS_CONTEUDO."""
    from app.qt.telas import servico

    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([
        Slot("livre_validade", [_legal(PapelTexto.VALIDADE, rect=(60, 40, 30, 8))]),
    ])])
    dados = {"livre_validade": DadosProduto("Sabonete Farnese")}
    avisos = servico.validar_composicao(lay, dados)
    assert any("decorativa" in a and "Sabonete" in a for a in avisos)


# --- Passos 5-6: badge (dado puro) + passos 1-3/10: diálogo nomeado ---------

def _app():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def test_badge_de_papel_cor_e_icone():
    """Cada papel tem rótulo, ícone e COR distintos (reconhecível de relance)."""
    _app()
    from app.qt.design.papel_texto_ui import badge_de_papel
    esperado_ic = {PapelTexto.LEGAL: "alerta_circulo",
                   PapelTexto.VALIDADE: "calendario",
                   PapelTexto.DICA: "lampada",
                   PapelTexto.LIVRE: "paragrafo"}
    cores = {}
    for p, ic in esperado_ic.items():
        rotulo, cor, nome_ic = badge_de_papel(p)
        assert nome_ic == ic and rotulo and cor
        cores[p] = cor
    assert len(set(cores.values())) == 4          # as 4 cores são distintas


def test_texto_inicial_do_papel():
    """O texto_fixo com que a região nasce, por papel (passos 9/10)."""
    from app.qt.design.papel_texto_ui import PRESETS_LEGAIS, texto_inicial_do_papel
    assert texto_inicial_do_papel(
        PapelTexto.LEGAL, preset_legal="Bebida alcoólica"
    ) == PRESETS_LEGAIS["Bebida alcoólica"]
    assert texto_inicial_do_papel(PapelTexto.LIVRE, texto_livre="  Oi  ") == "Oi"
    assert texto_inicial_do_papel(PapelTexto.LIVRE, texto_livre="   ") is None
    assert texto_inicial_do_papel(PapelTexto.VALIDADE) is None   # puxa do evento
    assert texto_inicial_do_papel(PapelTexto.DICA) is None       # a IA preenche


def test_dialogo_papel_resultado_por_escolha():
    """O diálogo devolve (papel, texto_fixo) certo por escolha (sem exec)."""
    _app()
    from app.qt.design.papel_texto_ui import PRESETS_LEGAIS, _dialogo_cls
    Dlg = _dialogo_cls()

    dlg = Dlg(None)
    dlg.selecionar(PapelTexto.LEGAL)
    dlg.combo_legal.setCurrentText("Bebida alcoólica")
    assert dlg.resultado() == (PapelTexto.LEGAL, PRESETS_LEGAIS["Bebida alcoólica"])

    dlg.selecionar(PapelTexto.VALIDADE)
    assert dlg.resultado() == (PapelTexto.VALIDADE, None)

    dlg.selecionar(PapelTexto.DICA)
    assert dlg.resultado() == (PapelTexto.DICA, None)

    dlg.selecionar(PapelTexto.LIVRE)
    dlg.edit_livre.setText("Promoção da semana")
    assert dlg.resultado() == (PapelTexto.LIVRE, "Promoção da semana")


# --- Passo 11 + 13: criar já com papel; trocar sem apagar/recriar -----------

def _canvas_com_layout():
    from app.qt.canvas import CanvasView
    _app()
    v = CanvasView()
    slot = Slot("s", [Regiao(TipoRegiao.PRECO, Retangulo(10, 10, 40, 20))])
    v.carregar(LayoutDef(100, 100, dpi=100, paginas=[Pagina([slot])]),
               DadosProduto("x"))
    return v


def test_criar_texto_legal_grava_papel():
    """adicionar_regiao(TEXTO_LEGAL, papel=…) nasce já com o papel escolhido."""
    v = _canvas_com_layout()
    reg = v.adicionar_regiao(TipoRegiao.TEXTO_LEGAL,
                             papel_texto=PapelTexto.VALIDADE)
    assert reg.tipo is TipoRegiao.TEXTO_LEGAL
    assert reg.papel_texto is PapelTexto.VALIDADE


def test_trocar_papel_preserva_texto():
    """Passo 11: recategorizar NÃO apaga o texto_fixo (só muda o papel)."""
    v = _canvas_com_layout()
    reg = v.adicionar_regiao(TipoRegiao.TEXTO_LEGAL,
                             papel_texto=PapelTexto.LIVRE,
                             texto_fixo="Combina com pão")
    v.definir_papel_texto(reg, PapelTexto.DICA)
    assert reg.papel_texto is PapelTexto.DICA
    assert reg.texto_fixo == "Combina com pão"       # nada se perdeu


def test_badge_pinta_sem_quebrar():
    """Passo 5: pintar a cena com um TEXTO_LEGAL de badge não lança e marca
    pixels (o caminho de `_paint_badge_papel` executa de verdade)."""
    from PySide6.QtGui import QImage, QPainter
    v = _canvas_com_layout()
    reg = v.adicionar_regiao(TipoRegiao.TEXTO_LEGAL, papel_texto=PapelTexto.DICA)
    it = next(i for i in v._itens if i.regiao is reg)
    it.setSelected(True)
    cena = v.scene()
    img = QImage(400, 400, QImage.Format.Format_ARGB32)
    img.fill(0)
    p = QPainter(img)
    cena.render(p)          # levanta se o paint do badge quebrar
    p.end()
    assert any(img.pixelColor(x, y).alpha() > 0
               for x in range(0, 400, 4) for y in range(0, 400, 4))


# ============================================================================
# BLOCO B — imagem na região: máscara, enquadrar, pill, sombra (passos 17-32)
# ============================================================================

def _foto(tmp_path, cor=(220, 20, 60), tam=(200, 200), nome="foto.png"):
    from PIL import Image as PImage
    p = tmp_path / nome
    PImage.new("RGB", tam, cor).save(p)
    return str(p)


def test_mascara_circulo_recorta_por_pixel(tmp_path):
    """R-036/passo 28: o canto FORA do círculo fica transparente (volta o
    fundo); o centro é a foto. Prova de mutação: sem a máscara o canto é foto."""
    foto = _foto(tmp_path)

    def _compor(masc):
        reg = Regiao(TipoRegiao.IMAGEM, Retangulo(0, 0, 40, 40),
                     ajuste=Ajuste.PREENCHER, mascara=masc)
        lay = LayoutDef(40, 40, dpi=100, paginas=[Pagina([Slot("c", [reg])])])
        return compor_pagina(lay, lay.paginas[0],
                             {"c": DadosProduto("x", imagem_path=foto)})

    com = _compor(Mascara.CIRCULO)
    sem = _compor(Mascara.RETANGULO)
    w, h = com.size
    assert com.getpixel((2, 2))[:3] == (255, 255, 255)      # canto recortado
    assert sem.getpixel((2, 2))[:3] != (255, 255, 255)      # sem máscara = foto
    assert com.getpixel((w // 2, h // 2))[:3][0] > 150       # centro avermelhado


def test_mascara_arredondada_recorta_o_canto(tmp_path):
    """Cantos arredondados também recortam o extremo do canto (por pixel)."""
    foto = _foto(tmp_path, cor=(0, 128, 255))
    reg = Regiao(TipoRegiao.IMAGEM, Retangulo(0, 0, 40, 40),
                 ajuste=Ajuste.PREENCHER, mascara=Mascara.ARREDONDADO,
                 mascara_raio_mm=12)
    lay = LayoutDef(40, 40, dpi=100, paginas=[Pagina([Slot("c", [reg])])])
    img = compor_pagina(lay, lay.paginas[0],
                        {"c": DadosProduto("x", imagem_path=foto)})
    assert img.getpixel((0, 0))[:3] == (255, 255, 255)       # canto recortado
    w, h = img.size
    assert img.getpixel((w // 2, h // 2))[:3][2] > 150        # centro é a foto


def test_mascara_nao_altera_rect_nem_ocupavel():
    """Passo 68 / I1: a máscara é só recorte — não muda o rect do slot e o
    slot de imagem segue ocupável (o vínculo e o pré-voo veem o slot inteiro)."""
    from app.rendering.grade import ocupaveis
    reg = Regiao(TipoRegiao.IMAGEM, Retangulo(3, 4, 20, 15),
                 mascara=Mascara.CIRCULO)
    antes = reg.rect.to_dict()
    lay = LayoutDef(40, 40, dpi=100, paginas=[Pagina([Slot("c", [reg])])])
    assert reg.rect.to_dict() == antes
    assert [s.id for s in ocupaveis(lay.paginas[0].slots)] == ["c"]


def test_enquadrar_nao_deforma_mantem_proporcao(tmp_path):
    """R-037/passo 29: enquadrar mantém a PROPORÇÃO (não estica). Uma foto 1:2
    fica 1:2 na camada; se deformasse p/ preencher, a razão iria a ~1."""
    from PIL import Image as PImage
    from app.rendering.compositor import ImagemSlot, _imagem_enquadrada
    src = PImage.new("RGBA", (100, 200), (10, 200, 30, 255))    # 1:2
    cam = _imagem_enquadrada(src, 120, 120, ImagemSlot("x"), Ajuste.CONTER)
    bbox = cam.getchannel("A").getbbox()
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    assert abs((w / h) - 0.5) < 0.05


def test_enquadrar_zoom_muda_o_recorte(tmp_path):
    """R-037: zoom reenquadra (o conteúdo visível muda). Foto com marca no
    canto: ao aproximar no centro, a marca sai do quadro."""
    from PIL import Image as PImage
    from app.rendering.compositor import ImagemSlot
    p = tmp_path / "marca.png"
    im = PImage.new("RGB", (200, 200), (0, 0, 255))
    for xx in range(0, 40):
        for yy in range(0, 40):
            im.putpixel((xx, yy), (255, 0, 0))     # marca vermelha no canto
    im.save(p)
    reg = Regiao(TipoRegiao.IMAGEM, Retangulo(0, 0, 40, 40), ajuste=Ajuste.PREENCHER)
    lay = LayoutDef(40, 40, dpi=100, paginas=[Pagina([Slot("c", [reg])])])

    def _compor(zoom):
        d = DadosProduto("x", imagens=[ImagemSlot(str(p), zoom=zoom)])
        return compor_pagina(lay, lay.paginas[0], {"c": d})

    z1, z2 = _compor(1.0), _compor(2.5)
    assert list(z1.getdata()) != list(z2.getdata())      # o enquadramento mudou


def test_pill_desenha_atras_do_texto(tmp_path):
    """R-035/passo 23: a pílula muda os pixels atrás do nome (faixa aparece)."""
    def _compor(pill):
        reg = Regiao(TipoRegiao.NOME, Retangulo(2, 2, 36, 12), cor="#ffffff",
                     pill=pill, pill_cor="#000000", pill_opacidade=210,
                     tamanho_max_pt=18)
        lay = LayoutDef(40, 16, dpi=100, paginas=[Pagina([Slot("c", [reg])])])
        return compor_pagina(lay, lay.paginas[0], {"c": DadosProduto("Arroz")})

    assert list(_compor(True).getdata()) != list(_compor(False).getdata())


def test_sombra_e_contorno_mudam_pixels(tmp_path):
    """R-034/passo 26: sombra e contorno mudam a composição do texto."""
    def _compor(**kw):
        reg = Regiao(TipoRegiao.NOME, Retangulo(2, 2, 36, 12), cor="#ffffff",
                     cor_efeito="#000000", tamanho_max_pt=18, **kw)
        lay = LayoutDef(40, 16, dpi=100, paginas=[Pagina([Slot("c", [reg])])])
        return compor_pagina(lay, lay.paginas[0], {"c": DadosProduto("Arroz")})

    base = list(_compor().getdata())
    assert list(_compor(sombra=True).getdata()) != base
    assert list(_compor(contorno=True).getdata()) != base


def test_bloco_b_serializa_idempotente():
    """Campos novos (máscara/pill/sombra/contorno) round-trip; layout antigo
    sem as chaves → padrões seguros (retângulo, sem pill, sem efeito)."""
    reg = Regiao(TipoRegiao.IMAGEM, Retangulo(0, 0, 10, 10),
                 mascara=Mascara.CIRCULO, pill=True, sombra=True, contorno=True)
    r2 = Regiao.from_dict(reg.to_dict())
    assert r2.mascara is Mascara.CIRCULO and r2.pill and r2.sombra and r2.contorno

    d_old = reg.to_dict()
    for k in ("mascara", "mascara_raio_mm", "pill", "pill_cor", "pill_opacidade",
              "sombra", "contorno", "cor_efeito"):
        d_old.pop(k, None)
    r3 = Regiao.from_dict(d_old)
    assert r3.mascara is Mascara.RETANGULO and not r3.pill and not r3.sombra
    assert not r3.contorno


def _canvas_com_imagem():
    from app.qt.canvas import CanvasView
    _app()
    v = CanvasView()
    reg = Regiao(TipoRegiao.IMAGEM, Retangulo(0, 0, 40, 40))
    v.carregar(LayoutDef(40, 40, dpi=100, paginas=[Pagina([Slot("s", [reg])])]),
               DadosProduto("x"))
    return v


def test_soltar_imagem_resolve_o_item_por_uid(tmp_path):
    """R-038/passo 30 (I1): soltar sobre a célula resolve o ITEM pela ligação
    slot→uid (mapa), não pela posição; chama o callback com (slot_id, caminho)."""
    from PySide6.QtCore import QPointF
    v = _canvas_com_imagem()
    v.mapa = {"s": "uid-XYZ"}
    capturado = []
    v.ao_soltar_imagem = lambda sid, cam: capturado.append((sid, cam))
    reg = v.regioes()[0]
    cx = reg.rect.x_mm + reg.rect.larg_mm / 2
    cy = reg.rect.y_mm + reg.rect.alt_mm / 2
    px, py = v.mm_para_cena(cx, cy)
    caminho = str(tmp_path / "nova.png")
    uid = v.soltar_imagem(QPointF(px, py), caminho)
    assert uid == "uid-XYZ"                        # resolveu por uid (I1)
    assert capturado == [("s", caminho)]


def test_override_enquadramento_aplica_zoom_e_foco():
    """R-037/passo 20: o override 'enquadramento' vira zoom/foco na ImagemSlot
    (por célula, sem tocar a foto do banco)."""
    from app.qt.telas import servico
    d = DadosProduto("x", imagem_path="/tmp/f.png")
    novo = servico.aplicar_override(
        d, {"enquadramento": {"zoom": 2.0, "foco_x": 0.2, "foco_y": 0.8}})
    assert novo.imagens and abs(novo.imagens[0].zoom - 2.0) < 1e-9
    assert abs(novo.imagens[0].foco_x - 0.2) < 1e-9
    assert abs(novo.imagens[0].foco_y - 0.8) < 1e-9


def test_centralizar_na_arte_move_para_o_centro():
    """R-032: centralizar move o rect para o centro da página (I1: só move)."""
    v = _canvas_com_imagem()
    reg = v.regioes()[0]
    reg.rect.x_mm, reg.rect.y_mm = 0.0, 0.0
    reg.rect.larg_mm, reg.rect.alt_mm = 20.0, 10.0
    uid = reg.uid
    v.centralizar_na_arte(reg)
    assert abs(reg.rect.x_mm - (40 - 20) / 2) < 1e-6
    assert abs(reg.rect.y_mm - (40 - 10) / 2) < 1e-6
    assert reg.uid == uid                          # I1: a identidade não muda


def test_override_dialog_enquadramento_so_quando_muda():
    """O modal de override só devolve 'enquadramento' se saiu do padrão; e
    pré-preenche de volta (round-trip da UI)."""
    _app()
    from app.qt.telas import servico
    from app.qt.telas.override_dialog import OverrideDialog
    it = servico.ItemMesa("Produto", "1,00", "VERDE", "Produto")
    dlg = OverrideDialog(it)
    assert "enquadramento" not in dlg.valores()      # padrão não vira override
    dlg.campo_zoom.setValue(1.8)
    dlg.foco_x.setValue(0.3)
    ov = dlg.valores()
    assert ov["enquadramento"] == {"zoom": 1.8, "foco_x": 0.3, "foco_y": 0.5}
    dlg2 = OverrideDialog(it, ov)                    # reabre com o override
    assert dlg2.valores()["enquadramento"]["zoom"] == 1.8


def test_adversarial_mascara_pill_nao_deslocam_o_trio(tmp_path):
    """Passo 32 (adversarial nominal, POR pixel): com máscara na imagem e pill
    no nome, cada região desenha o SEU conteúdo no SEU lugar — a imagem em cima
    (verde), a pílula/nome embaixo (vermelho). Nada se desloca nem troca."""
    foto = _foto(tmp_path, cor=(0, 200, 0))          # verde
    img = Regiao(TipoRegiao.IMAGEM, Retangulo(0, 0, 40, 20),
                 ajuste=Ajuste.PREENCHER, mascara=Mascara.CIRCULO)
    nome = Regiao(TipoRegiao.NOME, Retangulo(0, 20, 40, 20), cor="#ffffff",
                  pill=True, pill_cor="#ff0000", pill_opacidade=255,
                  tamanho_max_pt=16)
    lay = LayoutDef(40, 40, dpi=100, paginas=[Pagina([Slot("c", [img, nome])])])
    out = compor_pagina(lay, lay.paginas[0],
                        {"c": DadosProduto("Arroz", imagem_path=foto)})
    w, h = out.size
    assert out.getpixel((w // 2, h // 4))[:3][1] > 150       # verde na imagem (cima)
    baixo = [out.getpixel((x, 3 * h // 4))[:3] for x in range(0, w, 3)]
    assert any(r > 150 and g < 100 and b < 100 for (r, g, b) in baixo)  # pill vermelha (baixo)


# ============================================================================
# BLOCO C — estilo e reuso: conta-gotas, modelos, vitrine, reflow (passos 33-48)
# ============================================================================

def test_conta_gotas_so_estilo_nunca_geometria_nem_conteudo():
    """R-031/passo 34: o conta-gotas copia SÓ estilo (fonte/cor/pill/sombra),
    nunca geometria (rect/rotação) nem conteúdo (papel/texto_fixo)."""
    from app.rendering.estilos import copiar_estilo_visual
    origem = Regiao(TipoRegiao.NOME, Retangulo(0, 0, 10, 10), fonte="A.ttf",
                    cor="#ff0000", pill=True, sombra=True, tamanho_max_pt=30)
    destino = Regiao(TipoRegiao.PRECO, Retangulo(50, 50, 40, 20),
                     fonte="B.ttf", cor="#000000", papel_preco=PapelPreco.DE,
                     texto_fixo="NÃO COPIAR", rotacao_graus=45.0)
    copiar_estilo_visual(origem, destino)
    assert destino.fonte == "A.ttf" and destino.cor == "#ff0000"
    assert destino.pill and destino.sombra and destino.tamanho_max_pt == 30
    # geometria e conteúdo INTOCADOS
    assert destino.rect.x_mm == 50 and destino.rect.larg_mm == 40
    assert destino.rotacao_graus == 45.0
    assert destino.papel_preco is PapelPreco.DE
    assert destino.texto_fixo == "NÃO COPIAR"


def test_conta_gotas_respeita_estilo_nomeado():
    """R-031/passo 45: colar estilo numa região COM estilo nomeado marca os
    atributos de tipografia como override da instância (não quebra a F5.7)."""
    from app.rendering.estilos import copiar_estilo_visual
    origem = Regiao(TipoRegiao.NOME, Retangulo(0, 0, 10, 10), fonte="X.ttf",
                    cor="#123456", tamanho_max_pt=40)
    destino = Regiao(TipoRegiao.NOME, Retangulo(0, 0, 10, 10),
                     estilo="Estilo Nome")
    copiar_estilo_visual(origem, destino)
    assert {"fonte", "tamanho_max_pt", "cor"} <= destino.overrides_estilo


def test_capturar_e_carimbar_modelo_uid_fresco_e_relativo():
    """R-048/passo 37 (I1/I3): captura por rects RELATIVOS; carimbar escala p/
    a caixa-alvo e cada região nasce com uid NOVO (nunca herda vínculo)."""
    from app.rendering.modelos import capturar_modelo, carimbar_modelo
    orig = [
        Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 40, 40), uid="U1"),
        Regiao(TipoRegiao.NOME, Retangulo(10, 52, 40, 8), uid="U2"),
    ]
    modelo = capturar_modelo("teste", orig)
    novas = carimbar_modelo(modelo, 100, 200, 80, 100)   # caixa-alvo
    assert len(novas) == 2
    assert {r.uid for r in novas}.isdisjoint({"U1", "U2"})   # I1: uid fresco
    # a imagem (topo-esquerda no modelo) cai no topo-esquerda da caixa-alvo
    img = next(r for r in novas if r.tipo is TipoRegiao.IMAGEM)
    assert abs(img.rect.x_mm - 100) < 1e-6 and abs(img.rect.y_mm - 200) < 1e-6


def test_modelo_persiste_portable(tmp_path, monkeypatch):
    """I3: modelo salva/carrega em JSON sem caminho absoluto; rects relativos."""
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path))
    from app.rendering import modelos
    m = modelos.modelo_vitrine()
    modelos.salvar_modelo(m)
    assert "Vitrine (herói)" in modelos.listar_modelos()
    de_volta = modelos.carregar_modelo("Vitrine (herói)")
    assert de_volta is not None and len(de_volta.regioes) == 3
    for rd in de_volta.regioes:
        assert "rect_frac" in rd                       # relativo, não mm absoluto
        assert all(0.0 <= f <= 1.5 for f in rd["rect_frac"])


def test_vitrine_tem_o_trio():
    """R-044: a vitrine de fábrica é um trio imagem+nome+preço de herói."""
    from app.rendering.modelos import carimbar_modelo, modelo_vitrine
    regs = carimbar_modelo(modelo_vitrine(), 0, 0, 100, 100)
    tipos = {r.tipo for r in regs}
    assert TipoRegiao.IMAGEM in tipos and TipoRegiao.NOME in tipos
    assert TipoRegiao.PRECO in tipos


def test_reflow_nome_cede_com_reticencias():
    """R-045/passo 43: nome longo demais CEDE com "…" e cabe na altura (nunca
    transborda); o preço, região à parte, não é afetado. Prova de mutação:
    sem as reticências, o nº de linhas estoura a altura."""
    from app.core.paths import SystemRoot
    from app.rendering.text_fit import ajustar_texto
    from app.rendering.units import mm_para_px
    fonte = str(SystemRoot().fontes / "Roboto-Regular.ttf")
    texto = ("Biscoito recheado sabor chocolate ao leite com cobertura "
             "especial edição limitada de verão pacote família")
    larg = mm_para_px(30, 100)
    alt = mm_para_px(10, 100)
    aj = ajustar_texto(texto, fonte, larg, alt, 40, 100, tamanho_min_pt=6)
    assert aj.linhas[-1].endswith("…")                  # o nome cedeu
    assert aj.altura_linha_px * len(aj.linhas) <= alt + 0.5   # coube na altura


def test_carimbar_no_canvas_acrescenta_regioes_com_uid():
    """R-048/passo 37: carimbar no canvas acrescenta o trio ao slot ativo, com
    uids frescos — o conteúdo virá do item do slot."""
    from app.rendering.modelos import modelo_vitrine
    v = _canvas_com_imagem()
    n0 = len(v.regioes())
    uids0 = {r.uid for r in v.regioes()}
    novas = v.carimbar_modelo(modelo_vitrine())
    assert len(v.regioes()) == n0 + 3
    assert {r.uid for r in novas}.isdisjoint(uids0)      # I1: identidade nova


# ============================================================================
# BLOCO D — páginas e visão: contraste, distribuir, prévia, undo visual (49-62)
# ============================================================================

def test_razao_contraste_conhecida():
    from app.rendering.contraste import razao_contraste
    assert abs(razao_contraste((0, 0, 0), (255, 255, 255)) - 21.0) < 0.1
    assert razao_contraste((255, 255, 255), (255, 255, 255)) == 1.0


def test_contraste_avisa_branco_sobre_claro(tmp_path):
    """R-047/passo 57-58: texto branco sobre foto CLARA acusa (e sugere pílula/
    contorno); sobre foto ESCURA não; com pílula, protegido → não avisa.
    Prova de mutação: sem o limiar, nunca avisaria."""
    from app.rendering.contraste import avisos_contraste
    claro = _foto(tmp_path, cor=(240, 240, 240), nome="claro.png")
    escuro = _foto(tmp_path, cor=(15, 15, 15), nome="escuro.png")

    def _avisos(foto, **kw):
        img = Regiao(TipoRegiao.IMAGEM, Retangulo(0, 0, 40, 40),
                     ajuste=Ajuste.PREENCHER)
        nome = Regiao(TipoRegiao.NOME, Retangulo(2, 15, 36, 10), cor="#ffffff",
                      nome="Nome", **kw)
        lay = LayoutDef(40, 40, dpi=100, paginas=[Pagina([Slot("c", [img, nome])])])
        return avisos_contraste(lay, lay.paginas[0],
                                {"c": DadosProduto("Arroz", imagem_path=foto)})

    assert _avisos(claro)                                   # branco/claro → avisa
    assert not _avisos(escuro)                              # branco/escuro → ok
    assert not _avisos(claro, pill=True, pill_cor="#000000")  # pílula protege


def test_distribuir_espacamento_fixo():
    """R-033/passo 59: espaçamento FIXO (borda a borda) igual entre os itens."""
    from app.qt.alinhamento import distribuir_espacamento
    rects = [(0, 0, 10, 5), (100, 0, 20, 5), (40, 0, 10, 5)]   # fora de ordem
    pos = distribuir_espacamento(rects, "h", espaco=5)
    # ordenados por x: (0,10) → começa em 0; próximo em 0+10+5=15; depois 15+10+5=30
    xs = sorted((pos[i][0], rects[i][2]) for i in range(3))
    assert xs[0][0] == 0
    assert xs[1][0] == 0 + 10 + 5
    assert xs[2][0] == 15 + xs[1][1] + 5


def test_previa_impressao_tamanho_fisico(tmp_path):
    """R-046/passo 56: a prévia mede página + 2×sangria em mm; em px bate com o
    dpi."""
    from app.rendering.previa_impressao import previa_impressao, tamanho_fisico_mm
    from app.rendering.units import mm_para_px
    lay = LayoutDef(100, 150, dpi=100,
                    paginas=[Pagina([Slot("c", [
                        Regiao(TipoRegiao.NOME, Retangulo(10, 10, 40, 10))])])])
    img = previa_impressao(lay, lay.paginas[0], {"c": DadosProduto("X")},
                          margem_mm=5, sangria_mm=3)
    lw_mm, lh_mm = tamanho_fisico_mm(lay, sangria_mm=3)
    assert (lw_mm, lh_mm) == (106, 156)
    assert abs(img.width - mm_para_px(106, 100)) <= 2
    assert abs(img.height - mm_para_px(156, 100)) <= 2


def test_duplicar_pagina_identidade_fresca():
    """R-030/passo 51: duplicar dá ids de slot únicos (D8.1) e uids frescos (I1)."""
    v = _canvas_com_imagem()
    p0 = v._layout.paginas[0]
    ids0 = {s.id for s in p0.slots}
    uids0 = {r.uid for s in p0.slots for r in s.regioes}
    v.duplicar_pagina_atual()
    assert v.total_paginas() == 2
    p1 = v._layout.paginas[1]
    assert {s.id for s in p1.slots}.isdisjoint(ids0)         # D8.1
    assert {r.uid for s in p1.slots for r in s.regioes}.isdisjoint(uids0)  # I1


def test_mover_pagina_reordena():
    """R-030/passo 50: reordenar páginas troca a ordem (reflete no PDF)."""
    v = _canvas_com_imagem()
    v.duplicar_pagina_atual()
    id_p0 = v._layout.paginas[0].slots[0].id
    id_p1 = v._layout.paginas[1].slots[0].id
    assert v.mover_pagina(0, 1)
    assert v._layout.paginas[0].slots[0].id == id_p1
    assert v._layout.paginas[1].slots[0].id == id_p0


def test_undo_visual_salta_para_estado():
    """R-042/passo 53-54: pular para um estado volta layout+mapa juntos."""
    v = _canvas_com_imagem()
    idx0 = v.historico_indice()
    n0 = len(v.regioes())
    v.adicionar_regiao(TipoRegiao.NOME)
    v.adicionar_regiao(TipoRegiao.PRECO)
    assert len(v.regioes()) == n0 + 2
    assert v.ir_para_estado(idx0)                           # salta ao início
    assert len(v.regioes()) == n0


# ============================================================================
# BLOCO E — migração do modelo + pré-voo dos papéis novos (passos 63-74)
# ============================================================================

def test_migracao_layout_antigo_real_do_acervo():
    """Passos 63-65: um layout REAL (detecção da arte de arte/quintou) com
    regiões TEXTO_LEGAL ANTIGAS (sem papel_texto) migra DE CARONA ao abrir —
    infere o papel do conteúdo, SEM perder texto, e é idempotente."""
    from pathlib import Path
    from app.rendering.grade import layout_grade_de_arte
    from app.rendering.migracao import migrar_papeis_texto_dict
    arte = Path("arte/quintou/frente_template.png")
    assert arte.exists(), "arte real do acervo ausente"     # zero skips
    lay, _caixas = layout_grade_de_arte(str(arte))
    slot = lay.paginas[0].slots[0]
    slot.regioes += [
        Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(5, 5, 40, 8),
               texto_fixo="Bebida alcoólica. Venda proibida para menores de 18 anos."),
        Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(5, 15, 40, 8), texto_fixo=None),
        Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(5, 25, 40, 8), texto_fixo="Fica a Dica"),
    ]
    d = lay.to_dict()
    for pag in d["paginas"]:                                # simula layout ANTIGO
        for s in pag["slots"]:
            for r in s["regioes"]:
                r.pop("papel_texto", None)

    n = migrar_papeis_texto_dict(d)
    assert n >= 3
    lay2 = LayoutDef.from_dict(d)
    legais = [r for s in lay2.paginas[0].slots for r in s.regioes
              if r.tipo is TipoRegiao.TEXTO_LEGAL]
    porfixo = {(r.texto_fixo or ""): r.papel_texto for r in legais}
    assert porfixo["Bebida alcoólica. Venda proibida para menores de 18 anos."] is PapelTexto.LEGAL
    assert porfixo[""] is PapelTexto.VALIDADE               # vazio = validade legada
    assert porfixo["Fica a Dica"] is PapelTexto.LIVRE       # texto livre (seguro)
    # conteúdo preservado: o texto_fixo não sumiu
    assert any(r.texto_fixo == "Fica a Dica" for r in legais)
    # idempotente: reabrir de novo não migra nada
    assert migrar_papeis_texto_dict(d) == 0


def test_migracao_nao_toca_papel_ja_declarado():
    """Idempotência: região que JÁ tem papel_texto não é reinferida."""
    from app.rendering.migracao import migrar_papeis_texto_dict
    d = {"paginas": [{"slots": [{"regioes": [
        {"tipo": "TEXTO_LEGAL", "texto_fixo": "Bebida", "papel_texto": "LIVRE"},
    ]}]}]}
    assert migrar_papeis_texto_dict(d) == 0                 # já tem papel
    assert d["paginas"][0]["slots"][0]["regioes"][0]["papel_texto"] == "LIVRE"


def test_prevoo_papeis_avisa_dado_faltando():
    """Passo 69 (I2): validade sem data, dica sem texto, legal sem preset →
    aviso visível no pré-voo, nunca em silêncio."""
    from app.qt.telas import servico
    slot = Slot("livre", [_legal(PapelTexto.VALIDADE), _legal(PapelTexto.DICA),
                          _legal(PapelTexto.LEGAL)])
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([slot])])
    avisos = " ".join(servico.validar_composicao(lay, {}))
    assert "Validade da oferta" in avisos
    assert "Fica a Dica" in avisos
    assert "Aviso legal" in avisos


def test_prevoo_papeis_nao_avisa_quando_ok():
    """O pré-voo NÃO reclama quando cada papel tem sua fonte de dado."""
    from app.qt.telas import servico
    val = _legal(PapelTexto.VALIDADE)
    dica = _legal(PapelTexto.DICA, texto_fixo="Combina com pão")
    legal = _legal(PapelTexto.LEGAL, texto_fixo="Beba com moderação")
    slot = Slot("livre", [val, dica, legal])
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([slot])])
    dados = {"livre": DadosProduto("x", texto_legal="OFERTA VÁLIDA ATÉ 20/07")}
    avisos = " ".join(servico.validar_composicao(lay, dados))
    assert "Validade da oferta" not in avisos and "Fica a Dica" not in avisos
    assert "Aviso legal" not in avisos


def test_i3_campos_bloco5_sem_caminho_absoluto():
    """I3: máscara/pill/sombra/enquadramento serializam como forma/flags/cor/
    números — nada de caminho absoluto no JSON."""
    import json
    from app.rendering.compositor import ImagemSlot
    reg = Regiao(TipoRegiao.IMAGEM, Retangulo(0, 0, 10, 10),
                 mascara=Mascara.CIRCULO, pill=True, sombra=True)
    s = json.dumps(reg.to_dict())
    assert ":\\" not in s and "/Users" not in s and "/home" not in s
    esp = ImagemSlot("foto.png", zoom=2.0, foco_x=0.3, foco_y=0.7)
    assert 0.0 <= esp.foco_x <= 1.0 and esp.zoom == 2.0     # relativo/número


# ============================================================================
# BLOCO G — fechamento (passos 87-100)
# ============================================================================

def test_rg58_validade_sempre_tem_ate():
    """Passo 96 (RG-58): a validade de/até nunca sai vazia no "até" — quando
    há validade, o "ATÉ" está lá; o papel VALIDADE a carrega."""
    from app.qt.telas.servico import montar_validade_oferta
    assert montar_validade_oferta("17/07", "24/07") == "OFERTA VÁLIDA DE 17/07 ATÉ 24/07"
    assert montar_validade_oferta(None, "24/07") == "ATÉ 24/07"
    assert montar_validade_oferta("17/07", None) is None   # sem "até" não inventa
    reg = _legal(PapelTexto.VALIDADE)
    d = DadosProduto("x", texto_legal=montar_validade_oferta("17/07", "24/07"))
    assert "ATÉ" in texto_composto_legal(reg, d)


def test_f5_7_estilos_nomeados_intactos():
    """Passo 95: o conjunto de atributos do estilo nomeado F5.7 não regrediu."""
    from app.rendering.estilos import ATRIBUTOS_DE_ESTILO
    assert ATRIBUTOS_DE_ESTILO == ("fonte", "tamanho_max_pt", "cor")
