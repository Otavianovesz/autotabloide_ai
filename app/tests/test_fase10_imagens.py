"""FASE 10 — Imagens II + Estúdio IA.

O sonho "foto de celular → packshot": Estúdio degrau 1 (sem IA generativa, prova
por PIXEL), degrau 2 degradável sem GPU, WebP com ALFA, fundo-branco, girar/cortar/
refino não-destrutivo, genéricas marcadas, foto repetida por HASH, upscale-alvo.

DECISÃO TRAVADA testada: o degrau 1 (sem IA) é o padrão garantido (roda sem GPU);
o degrau 2 (generativo) degrada com aviso e NUNCA é requisito.
"""

import shutil
from pathlib import Path

import pytest
from PIL import Image

from app.images import estudio


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


def _fake_rembg(_img):
    """rembg FAKE: um retângulo central opaco (produto), resto transparente —
    para testar o Estúdio sem carregar o modelo de ~1GB."""
    rgba = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    rgba.paste(Image.new("RGBA", (100, 120), (200, 40, 40, 255)), (50, 40))
    return rgba


# ===========================================================================
# R-091 — Estúdio degrau 1 (sem IA generativa) — PROVA POR PIXEL
# ===========================================================================

def test_packshot_degrau1_fundo_limpo_e_sombra():
    """R-091/passo 14: o packshot sai com FUNDO transparente + SOMBRA — conferido
    POR PIXEL. Prova de mutação: sem a sombra sintética, não haveria pixel
    escuro semitransparente abaixo do produto."""
    pack = estudio.packshot_degrau1(Image.new("RGB", (200, 200), "white"),
                                    remover_fundo=_fake_rembg, lado=400)
    assert pack.size == (400, 400) and pack.mode == "RGBA"
    assert pack.getpixel((5, 5))[3] == 0                 # canto transparente
    cx = pack.width // 2
    assert pack.getpixel((cx, pack.height // 2))[3] > 200   # produto opaco no centro
    sombra = any(0 < pack.getpixel((cx, y))[3] < 255 and pack.getpixel((cx, y))[0] < 120
                 for y in range(pack.height // 2, pack.height))
    assert sombra                                        # a sombra existe


def test_packshot_degrau1_roda_sem_gpu():
    """R-091/passo 15 (decisão travada): o caminho garantido NÃO depende de GPU —
    roda mesmo com o gerador (degrau 2) indisponível."""
    assert estudio.gerador_disponivel() is None or isinstance(
        estudio.gerador_disponivel(), str)
    pack = estudio.packshot_degrau1(Image.new("RGB", (150, 150), "white"),
                                    remover_fundo=_fake_rembg)
    assert pack.mode == "RGBA"                            # entregou sem GPU


# ===========================================================================
# R-091 — Estúdio degrau 2 (generativo) — degradável, nunca requisito
# ===========================================================================

def test_degrau2_sem_gpu_degrada_com_aviso():
    """R-091/passo 21+27 (RG-46 não bloqueia): sem GPU e sem motor, o degrau 2
    devolve (None, aviso honesto) — o degrau 1 já entregou. NUNCA trava."""
    if estudio.gerador_disponivel() is not None:
        pytest.skip("esta máquina TEM GPU — o caminho de degradação não se aplica")
    img, aviso = estudio.refinar_com_gerador(Image.new("RGBA", (100, 100)))
    assert img is None and aviso and "GPU" in aviso


def test_degrau2_anti_alucinacao_rejeita_mudanca_demais():
    """R-091/passo 24: se o img2img muda DEMAIS o produto (inventou outro), a
    guarda rejeita e avisa. Prova de mutação: sem `diferenca_demais`, a imagem
    inventada passaria."""
    class MotorInventa:
        def img2img(self, p, denoise):
            return Image.new("RGB", p.size, "blue")      # muda tudo
    pack = Image.new("RGBA", (80, 80), (200, 40, 40, 255))
    img, aviso = estudio.refinar_com_gerador(pack, motor=MotorInventa())
    assert img is None and aviso and "demais" in aviso


def test_degrau2_com_motor_preserva_o_produto():
    """R-091/passo 19: denoise baixo preserva o produto — uma saída quase igual é
    ACEITA (o encanamento do degrau 2, provado sem GPU via motor fake)."""
    class MotorFiel:
        def img2img(self, p, denoise):
            return p.convert("RGB")                      # devolve ~igual
    pack = Image.new("RGBA", (80, 80), (200, 40, 40, 255))
    img, aviso = estudio.refinar_com_gerador(pack, motor=MotorFiel())
    assert img is not None and aviso is None


# ===========================================================================
# R-100 — WebP com ALFA ; R-095 fundo-branco ; R-094/R-103 edição
# ===========================================================================

def test_webp_preserva_alfa_e_reduz(tmp_path):
    """R-100/passo 53+68: WebP preserva a TRANSPARÊNCIA (packshot recortado) e
    reduz o tamanho. Prova de mutação: salvar sem alfa (RGB) perderia a
    transparência do canto."""
    from app.images.curadoria import salvar_webp, webp_disponivel
    assert webp_disponivel()
    img = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    img.paste(Image.new("RGBA", (150, 150), (200, 40, 40, 255)), (75, 75))
    wp = salvar_webp(img, tmp_path / "p.webp", lossless=True)
    reaberto = Image.open(wp)
    assert reaberto.mode in ("RGBA", "LA") or "A" in reaberto.getbands()
    assert reaberto.convert("RGBA").getpixel((5, 5))[3] == 0    # alfa preservado
    png = tmp_path / "p.png"
    img.save(png, "PNG")
    assert wp.stat().st_size <= png.stat().st_size             # não maior que PNG


def test_detector_fundo_branco():
    """R-095/passo 42: fundo branco uniforme → pula o rembg; fundo colorido → não.
    Prova de mutação: medir o centro em vez dos cantos daria falso."""
    from app.images.curadoria import tem_fundo_branco
    branco = Image.new("RGB", (300, 300), (255, 255, 255))
    branco.paste(Image.new("RGB", (120, 120), (30, 30, 30)), (90, 90))  # produto escuro no meio
    assert tem_fundo_branco(branco) is True
    colorido = Image.new("RGB", (300, 300), (40, 120, 200))
    assert tem_fundo_branco(colorido) is False


def test_detector_fundo_branco_pula_rembg_quando_ligado(raiz_tmp, tmp_path):
    """R-095 (wiring): com a Config LIGADA e fundo branco, o pipeline PULA o rembg
    (o toggle da F3 passou a fazer algo — não é mais promessa morta). Prova de
    mutação: sem o gate da Config, pularia mesmo desligado."""
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio
    from app.images.fundo import _pular_rembg_fundo_branco
    branca = tmp_path / "branca.png"
    b = Image.new("RGB", (200, 200), (255, 255, 255))
    b.paste(Image.new("RGB", (80, 80), (20, 20, 20)), (60, 60))
    b.save(branca)
    assert _pular_rembg_fundo_branco(branca) is False    # flag desligada (padrão)
    db = Database().init()
    with db.Session() as s:
        ConfigRepositorio(s).set("imagem.detector_fundo_branco", True)
        s.commit()
    db.engine.dispose()
    assert _pular_rembg_fundo_branco(branca) is True      # ligada + branco → pula
    cor = tmp_path / "cor.png"
    Image.new("RGB", (200, 200), (40, 120, 200)).save(cor)
    assert _pular_rembg_fundo_branco(cor) is False        # colorido não pula


def test_girar_cortar_espelhar_e_refino_nao_destrutivo():
    """R-094/R-103/passo 48: edições preservam o original (versão nova, I1); o
    refino restaura/apaga o alfa por pincel (POR PIXEL)."""
    from app.images.curadoria import cortar, espelhar, girar, refinar_alfa
    # imagem com um CANTO marcado, para provar direção/espelho POR CONTEÚDO
    img = Image.new("RGBA", (100, 60), (200, 40, 40, 255))
    img.putpixel((0, 0), (0, 0, 255, 255))               # marca o canto superior-esq
    g = girar(img, 90)                                   # horário
    assert g.size == (60, 100)                           # 90° troca as dimensões
    assert g.getpixel((g.width - 1, 0)) == (0, 0, 255, 255)   # sup-esq → sup-dir (horário)
    esp = espelhar(img)                                  # horizontal
    assert esp.size == (100, 60)
    assert esp.getpixel((esp.width - 1, 0)) == (0, 0, 255, 255)  # o canto virou p/ a direita
    assert cortar(img, (10, 10, 40, 40)).size == (30, 30)
    assert cortar(img, (50, 50, 10, 10)) is not img      # caixa degenerada → cópia, não o mesmo
    # refino: apaga um círculo no alfa; o original fica intacto (não-destrutivo)
    apagada = refinar_alfa(img, [(50, 30)], raio=10, apagar=True)
    assert apagada.getpixel((50, 30))[3] == 0            # apagou o alfa ali
    assert img.getpixel((50, 30))[3] == 255              # o ORIGINAL intacto (I1)


# ===========================================================================
# R-099 genéricas ; R-104 foto repetida por hash ; R-101 upscale-alvo
# ===========================================================================

def test_generica_marcada_e_avisada_no_prevoo(raiz_tmp):
    """R-099/passo 69: a genérica é MARCADA (nunca vira foto real) e o pré-voo
    avisa. Prova de mutação: sem a checagem `eh_generica`, o pré-voo não acusaria."""
    from decimal import Decimal

    from app.core.genericas import caminho_generica, eh_generica
    from app.qt.telas import servico
    from app.rendering.compositor import DadosProduto
    from app.rendering.cartaz import layout_cartaz_exemplo
    cam = caminho_generica("Mercearia", forma="caixa")
    assert cam and eh_generica(cam) and not eh_generica("/fotos/arroz.png")
    lay = layout_cartaz_exemplo()
    dados = {"cartaz": DadosProduto("Arroz", preco_por=Decimal("5.00"),
                                    imagem_path=cam)}
    avisos = servico.validar_composicao(lay, dados)
    assert any("GENÉRICA" in a for a in avisos)           # o pré-voo avisou


def test_foto_repetida_por_hash_de_conteudo(raiz_tmp, tmp_path):
    """R-104/passo 68: a MESMA foto em 2 itens é detectada por HASH de CONTEÚDO,
    não por nome (nomes diferentes, mesmo conteúdo → pega). Prova de mutação:
    comparar por nome de arquivo não acharia."""
    from app.qt.telas import servico
    a = tmp_path / "a.png"
    b = tmp_path / "b_nome_diferente.png"       # NOME diferente…
    Image.new("RGB", (30, 30), (10, 120, 30)).save(a)
    shutil.copy(a, b)                            # …mas CONTEÚDO idêntico
    c = tmp_path / "c.png"
    Image.new("RGB", (30, 30), (200, 20, 20)).save(c)   # foto diferente
    it1 = servico.ItemMesa("A", "1,00", "VERDE", "A"); it1.imagem = str(a)
    it2 = servico.ItemMesa("B", "2,00", "VERDE", "B"); it2.imagem = str(b)
    it3 = servico.ItemMesa("C", "3,00", "VERDE", "C"); it3.imagem = str(c)
    grupos = servico.fotos_repetidas([it1, it2, it3])
    assert len(grupos) == 1                      # só a/b repetem
    assert {x.nome for x in grupos[0][1]} == {"A", "B"}


def test_upscale_mira_a_resolucao_alvo_da_celula():
    """R-101/passo 66: o lado-alvo é a resolução da célula de imagem (maior lado
    em px pelo DPI) — o upscale mira exatamente isto. Prova de mutação: usar mm
    em vez de px daria outro número."""
    from app.qt.telas import servico
    from app.rendering.model import TipoRegiao
    from app.rendering.units import mm_para_px
    from app.rendering.cartaz import layout_cartaz_exemplo
    lay = layout_cartaz_exemplo()
    # o alvo é o MAIOR lado da região IMAGEM em px — derivado da produção,
    # nunca um número mágico (I5). Prova de mutação: usar mm daria outro número.
    reg = next(r for s in lay.paginas[0].slots for r in s.regioes
               if r.tipo == TipoRegiao.IMAGEM)
    maior_mm = max(reg.rect.larg_mm, reg.rect.alt_mm)
    alvo = servico.lado_alvo_da_celula(lay)
    assert alvo == round(mm_para_px(maior_mm, 300))


def test_upscale_nao_amplia_alem_do_alvo(raiz_tmp, tmp_path):
    """[BUG achado pela frota] o upscale NÃO estoura o alvo da célula para foto
    não-quadrada: um panorama pequeno é ampliado com o MAIOR lado ≈ o alvo, nunca
    3× o alvo (o "nem mais" do R-101). E a foto que já enche a célula não é
    reprocessada à toa. Prova de mutação: mirar o menor lado inflaria o maior."""
    from app.qt.telas import servico
    pano = tmp_path / "pano.png"
    Image.new("RGB", (300, 100), (200, 40, 40)).save(pano)   # panorama pequeno
    saida = servico.upscale_para_cartaz(str(pano), 992, lambda *a: None)
    w, h = Image.open(saida).size
    assert max(w, h) <= 992 + 8                  # o MAIOR lado não passa do alvo
    assert max(w, h) >= 992 * 0.8                # e chega perto (nem menos)
    grande = tmp_path / "grande.png"
    Image.new("RGB", (1000, 700), (30, 120, 200)).save(grande)  # já enche a célula
    mesma = servico.upscale_para_cartaz(str(grande), 992, lambda *a: None)
    assert mesma == str(grande)                  # devolveu a original (não ampliou à toa)


def test_tratar_estudio_orquestra_e_salva_png(raiz_tmp, tmp_path, monkeypatch):
    """Casca R-091: `tratar_estudio` (worker-callable) roda o packshot e salva o
    PNG. Testado SEM o modelo de 1GB (monkeypatch do degrau 1). O degrau 2
    opcional degrada com aviso sem travar."""
    from app.images import estudio
    from app.qt.telas import servico
    fonte = tmp_path / "foto_celular.png"
    Image.new("RGB", (200, 200), "white").save(fonte)
    monkeypatch.setattr(estudio, "packshot_degrau1",
                        lambda img, **k: Image.new("RGBA", (400, 400), (0, 0, 0, 0)))
    avisos = []
    saida = servico.tratar_estudio(str(fonte), lambda m: avisos.append(m),
                                   com_gerador=True)
    assert Path(saida).exists() and Path(saida).suffix == ".png"
    assert Image.open(saida).mode == "RGBA"         # packshot com alfa
    # o degrau 2 sem GPU degradou COM aviso (não travou)
    assert any("degrau 1" in m or "GPU" in m for m in avisos)
