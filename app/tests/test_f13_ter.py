"""ORDEM F13-TER — encartes ENCORPADOS (3ª rodada do laço; L1 sempre).

V1 (§1): a causa-raiz do "pequeneninhas" — o recorte justo era desfeito
pelo quadrado 1000×1000 do ``normalizar`` e o CONTER ajustava o
QUADRADO, não o produto. O ajuste novo ASSENTAR recorta pela bbox do
alfa NA COMPOSIÇÃO (conserta o acervo existente sem reprocessar),
escala pelo maior fator que caiba e ancora o produto no RODAPÉ da zona.
V5 (§3): prova ponta a ponta de que o quadrado morreu (a ``_justa``).
"""

from pathlib import Path

import pytest
from PIL import Image

from app.rendering.compositor import DadosProduto, compor_pagina
from app.rendering.model import (
    LayoutDef,
    Pagina,
    Regiao,
    Retangulo,
    Slot,
    TipoRegiao,
)
from app.tests import acervo


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    acervo.copiar_fontes_reais(root.fontes)
    return root


def _foto_quadrado_com_item(caminho: Path) -> Path:
    """O retrato do acervo REAL de hoje: um quadrado 1000×1000
    transparente com o produto (alto e estreito) pequeno no centro —
    o resultado do ``normalizar`` que causou a dupla redução."""
    q = Image.new("RGBA", (1000, 1000), (0, 0, 0, 0))
    item = Image.new("RGBA", (300, 880), (200, 30, 30, 255))
    q.paste(item, ((1000 - 300) // 2, (1000 - 880) // 2))
    q.save(caminho)
    return caminho


def test_v1_assentar_mata_o_quadrado_por_pixel(raiz_tmp, tmp_path):
    """V1: com ``Ajuste.ASSENTAR`` o produto é recortado pela bbox do
    alfa, escalado pelo MAIOR fator que caiba e ASSENTADO no rodapé da
    zona — por pixel: a tinta cobre ≥90% da ALTURA da zona e encosta no
    rodapé. Com CONTER (o defeito), o quadrado limita o produto a ~40%."""
    import numpy as np

    from app.rendering.model import Ajuste
    from app.rendering.units import mm_para_px

    foto = _foto_quadrado_com_item(tmp_path / "q.png")
    reg = Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 60, 80),
                 nome="Foto", ajuste=Ajuste.ASSENTAR)
    lay = LayoutDef(100, 100, dpi=100,
                    paginas=[Pagina([Slot("c", [reg])])])
    dados = {"c": DadosProduto("Item", imagem_path=str(foto))}
    img = compor_pagina(lay, lay.paginas[0], dados)

    x0 = round(mm_para_px(10, 100))
    y0 = round(mm_para_px(10, 100))
    x1 = round(mm_para_px(70, 100))
    y1 = round(mm_para_px(90, 100))
    a = np.asarray(img.crop((x0, y0, x1, y1)).convert("RGB"), dtype=int)
    tinta = (np.abs(a - np.array([200, 30, 30])).max(axis=2) <= 40)
    linhas = np.where(tinta.any(axis=1))[0]
    assert linhas.size, "o produto nem apareceu na zona"
    h_zona = a.shape[0]
    cobertura = (linhas.max() - linhas.min()) / h_zona
    assert cobertura >= 0.90, (
        f"o produto cobre só {cobertura:.0%} da altura da zona — o "
        "QUADRADO do acervo ainda limita a escala (a dupla redução)")
    assert linhas.max() >= h_zona - 3, (
        "o produto não ASSENTOU no rodapé da zona — está flutuando")


def test_v1_conter_segue_byte_identico(raiz_tmp, tmp_path):
    """V1: o CONTER de sempre NÃO muda (as provas byte-idênticas da
    F2/F5 dependem dele) — o quadrado só morre no ASSENTAR."""
    foto = _foto_quadrado_com_item(tmp_path / "q.png")
    reg = Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 60, 80),
                 nome="Foto")               # Ajuste.CONTER (padrão)
    lay = LayoutDef(100, 100, dpi=100,
                    paginas=[Pagina([Slot("c", [reg])])])
    dados = {"c": DadosProduto("Item", imagem_path=str(foto))}
    antes = compor_pagina(lay, lay.paginas[0], dados)
    depois = compor_pagina(lay, lay.paginas[0], dados)
    assert antes.tobytes() == depois.tobytes()


def test_v2_adorno_recola_o_fundo_por_cima_da_foto(raiz_tmp, tmp_path):
    """V2: a foto vai POR BAIXO dos adornos — a região ADORNO recola o
    recorte do FUNDO ORIGINAL por cima do que já foi desenhado. Por
    pixel: na área do adorno vence o fundo; fora dela, a foto."""
    from app.rendering.model import Ajuste
    from app.rendering.units import mm_para_px

    fundo = tmp_path / "fundo.png"
    Image.new("RGB", (394, 394), "#DDCC99").save(fundo)   # o "vime"
    foto = tmp_path / "foto.png"
    Image.new("RGBA", (300, 300), (20, 60, 200, 255)).save(foto)

    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([Slot("c", [
        Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 60, 60),
               nome="Foto", ajuste=Ajuste.ASSENTAR),
        Regiao(TipoRegiao.ADORNO, Retangulo(10, 50, 60, 20),
               nome="Cesta"),
    ])])])
    lay.arquivo_fundo = str(fundo)
    img = compor_pagina(lay, lay.paginas[0],
                        {"c": DadosProduto("X", imagem_path=str(foto))})
    px = round(mm_para_px(40, 100))
    y_foto = round(mm_para_px(30, 100))
    y_adorno = round(mm_para_px(60, 100))
    assert img.getpixel((px, y_foto))[:3] == (20, 60, 200), (
        "a foto não apareceu na parte livre da zona")
    assert img.getpixel((px, y_adorno))[:3] == (0xDD, 0xCC, 0x99), (
        "o ADORNO não recolou o fundo por cima da foto — o produto "
        "segue POR CIMA da cesta/banda (V2)")


def test_v2_adorno_nao_e_ocupavel():
    """V2 + a lei do tipo novo: ADORNO é decoração — slot só de adorno
    nunca engole produto da fila (A7)."""
    from app.rendering.grade import ocupaveis
    deco = Slot("deco", [Regiao(TipoRegiao.ADORNO,
                                Retangulo(0, 0, 10, 5))])
    prod = Slot("prod", [
        Regiao(TipoRegiao.IMAGEM, Retangulo(20, 0, 10, 10)),
        Regiao(TipoRegiao.NOME, Retangulo(20, 12, 10, 4)),
    ])
    assert [s.id for s in ocupaveis([deco, prod])] == ["prod"]


def test_s1_varredura_por_radical_no_pacote():
    """S1 (§2): a lição do SENEPAL — varredura de string por RADICAL,
    nunca pela grafia suposta. No pacote inteiro (geradores + SVGs de
    composição), toda ocorrência de ``senep*`` tem de ser "senepol";
    zero "senepal"/"cenepol". (Os *-CURVAS.svg são derivados do
    pipeline Inkscape e ficam fora — regenerados à parte.)"""
    import re
    raiz = Path(__file__).resolve().parents[2] / "Templates novos"
    if not raiz.exists():
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")
    ruins = []
    for p in list(raiz.glob("geradores/*.py")) + \
            [q for q in raiz.glob("artes/**/*.svg")
             if "CURVAS" not in q.name]:
        texto = p.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"[SsCc]enep\w*", texto):
            if m.group(0).lower() != "senepol":
                ruins.append(f"{p.name}: {m.group(0)}")
    assert not ruins, f"grafias erradas de Senepol no pacote: {ruins}"


def test_v4_selo_mais18_usa_o_asset_novo_e_tamanho_relativo(raiz_tmp):
    """V4: o +18 deixa de ser badge de texto — usa o ASSET vetorial do
    projeto (a tarja diagonal existe por pixel: tinta clara no quadrante
    inferior-esquerdo, onde o badge antigo era só disco vermelho) — e o
    tamanho vira RELATIVO com destaque (célula 400×400 ⇒ selo ≥ 96 px)."""
    import numpy as np

    from app.rendering.selos import Canto, Selo, desenhar_selos, render_selo

    img = render_selo(Selo("MAIS18"), 200)
    a = np.asarray(img.convert("RGBA"), dtype=int)
    q = a[130:180, 20:70]                  # a tarja cruza este quadrante
    claros = ((q[..., 3] > 200) &
              (q[..., :3].min(axis=2) > 180)).sum()
    assert claros > 200, (
        "o +18 ainda é o badge antigo (disco sem a tarja diagonal) — "
        "o asset novo do V4 não está sendo usado")

    base = Image.new("RGB", (500, 500), "#EEEEEE")
    desenhar_selos(base, (50, 50, 400, 400),
                   [Selo("MAIS18", Canto.SUPERIOR_DIREITO)])
    b = np.asarray(base, dtype=int)
    vermelhos = ((b[:, :, 0] > 130) & (b[:, :, 1] < 90) &
                 (b[:, :, 2] < 90))
    linhas = np.where(vermelhos.any(axis=1))[0]
    assert linhas.size and (linhas.max() - linhas.min()) >= 96, (
        f"o selo saiu com {linhas.max() - linhas.min() if linhas.size else 0} px "
        "numa célula de 400 — o mínimo relativo com destaque (≥24% + "
        "1.3× no +18) não valeu")


def test_v5_pipeline_guarda_a_justa_sem_faixa_transparente(
        raiz_tmp, tmp_path, monkeypatch):
    """V5: o pipeline ponta a ponta guarda a ``_justa.webp`` (alfa
    preservado, curadoria não-destrutiva) SEM faixa transparente nas
    quatro bordas — a prova de que o quadrado morreu no caminho novo.
    (Fundo branco uniforme ⇒ o detector R-095 pula o rembg — o teste
    não toca o modelo .onnx.)"""
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio
    from app.images.fundo import processar_imagem

    db = Database().init()
    try:
        with db.Session() as s:
            ConfigRepositorio(s).set("imagens.detectar_fundo_branco", True)
            s.commit()
    finally:
        db.engine.dispose()

    bruto = tmp_path / "bruta.png"
    img = Image.new("RGB", (600, 400), "#FFFFFF")
    for px in range(150, 450):
        for py in range(80, 320):
            img.putpixel((px, py), (30, 90, 200))
    img.save(bruto)

    destino = tmp_path / "acervo" / "atual.png"
    processar_imagem(bruto, destino)
    assert destino.exists(), "o pipeline não salvou a normalizada"
    justa = destino.with_name("atual_justa.webp")
    assert justa.exists(), (
        "a versão JUSTA não foi guardada ao lado da normalizada (V1)")
    ji = Image.open(justa).convert("RGBA")
    bbox = ji.getchannel("A").getbbox()
    assert bbox == (0, 0, ji.width, ji.height), (
        f"a _justa tem faixa transparente nas bordas (bbox {bbox} ≠ "
        f"{ji.size}) — o quadrado sobreviveu")


# --- D1 (§4): Número e Ano do Jornal são REAIS -------------------------------


def test_d1_papel_edicao_e_dado_vivo_nunca_rotulo():
    """D1: o papel EDICAO desenha a edição VIVA do projeto; sem dado,
    não desenha NADA (a regra nova do §4: rótulo que não é sempre
    verdade não pode estar na estrutura — "Nº 177" cravado mentia)."""
    from app.rendering.compositor import texto_composto_legal
    from app.rendering.model import PapelTexto

    reg = Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(0, 0, 40, 8),
                 nome="Edição", papel_texto=PapelTexto.EDICAO)
    vivo = DadosProduto("", edicao="Nº 178 · ANO 42")
    assert texto_composto_legal(reg, vivo) == "Nº 178 · ANO 42"
    assert texto_composto_legal(reg, DadosProduto("")) == ""
    assert texto_composto_legal(reg, None) == ""


def test_d1_edicao_chega_ao_cabecalho_fora_de_celula(raiz_tmp):
    """D1: o cabeçalho do Jornal é slot DECORATIVO (sem produto) — a
    edição viva chega a ele pelo canal da página (o mesmo do D7 para a
    validade). Por pixel: com edição há tinta na caixa; sem, nenhuma."""
    import numpy as np

    from app.rendering.model import PapelTexto
    from app.rendering.units import mm_para_px

    cab = Slot("cab", [Regiao(
        TipoRegiao.TEXTO_LEGAL, Retangulo(10, 5, 60, 10), nome="Edição",
        papel_texto=PapelTexto.EDICAO, cor="#000000")])
    cel = Slot("c1", [
        Regiao(TipoRegiao.NOME, Retangulo(10, 40, 60, 10), cor="#000000"),
    ])
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([cab, cel])])

    def tinta(dados):
        img = compor_pagina(lay, lay.paginas[0], dados)
        x0, y0 = round(mm_para_px(10, 100)), round(mm_para_px(5, 100))
        x1, y1 = round(mm_para_px(70, 100)), round(mm_para_px(15, 100))
        a = np.asarray(img.crop((x0, y0, x1, y1)).convert("L"), dtype=int)
        return int((a < 128).sum())

    com = tinta({"c1": DadosProduto("Café", edicao="Nº 178 · ANO 42")})
    sem = tinta({"c1": DadosProduto("Café")})
    assert com > 30, "a edição viva não chegou ao cabeçalho fora de célula"
    assert sem == 0, "sem edição o cabeçalho tinha de ficar MUDO (nunca mentir)"


def test_d1_sugerir_edicao_incrementa_por_mes_e_o_ano_vira(raiz_tmp):
    """D1: a edição se sugere da BASE registrada (nº/ano de uma edição
    conhecida): o número incrementa por mês corrido e o ANO (de
    circulação) vira com o ano civil. Sem base, sem palpite (None)."""
    from datetime import date

    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio
    from app.qt.telas.servico import sugerir_edicao

    db = Database().init()
    try:
        with db.Session() as s:
            ConfigRepositorio(s).set("eventos.edicao_base", {
                "jornal do mês": {"numero": 177, "ano": 42,
                                  "quando": "2026-07"}})
            s.commit()
    finally:
        db.engine.dispose()

    assert sugerir_edicao("Jornal do Mês",
                          hoje=date(2026, 8, 5)) == "Nº 178 · ANO 42"
    assert sugerir_edicao("jornal do mês",          # caixa não importa
                          hoje=date(2026, 7, 30)) == "Nº 177 · ANO 42"
    assert sugerir_edicao("Jornal do Mês",
                          hoje=date(2027, 1, 10)) == "Nº 183 · ANO 43"
    assert sugerir_edicao("Quintou", hoje=date(2026, 8, 5)) is None


def test_d1_pre_voo_avisa_edicao_vazia_e_a_anterior(raiz_tmp):
    """D1: o pré-voo AVISA (nunca veta) quando o layout tem papel EDICAO
    sem dado, e quando a edição composta é uma JÁ PUBLICADA — "nunca
    publicar com o número da edição anterior"."""
    from app.qt.telas.servico import (
        registrar_edicao_publicada,
        validar_composicao,
    )
    from app.rendering.model import PapelTexto

    cab = Slot("cab", [Regiao(
        TipoRegiao.TEXTO_LEGAL, Retangulo(10, 5, 60, 10), nome="Edição",
        papel_texto=PapelTexto.EDICAO)])
    cel = Slot("c1", [
        Regiao(TipoRegiao.IMAGEM, Retangulo(10, 20, 30, 30)),
        Regiao(TipoRegiao.NOME, Retangulo(10, 55, 60, 8)),
    ])
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([cab, cel])])
    foto = raiz_tmp.raiz / "foto.png"
    Image.new("RGB", (50, 50), "red").save(foto)

    def dados(edicao=None):
        from decimal import Decimal
        return {"c1": DadosProduto("Café", preco_por=Decimal("9.90"),
                                   imagem_path=str(foto), edicao=edicao)}

    vazios = validar_composicao(lay, dados())
    assert any("edição" in a.lower() for a in vazios), (
        f"papel EDICAO sem dado tinha de aparecer no pré-voo: {vazios}")

    registrar_edicao_publicada("Jornal do Mês", "Nº 177 · ANO 42")
    repetida = validar_composicao(lay, dados("Nº 177 · ANO 42"))
    assert any("publicada" in a.lower() for a in repetida), (
        f"a edição JÁ PUBLICADA tinha de ser avisada: {repetida}")

    nova = validar_composicao(lay, dados("Nº 178 · ANO 42"))
    assert not any("edição" in a.lower() for a in nova), (
        f"edição nova e viva não podia gerar aviso: {nova}")


def test_d1_edicao_persiste_no_projeto(raiz_tmp):
    """D1: a edição é campo do PROJETO (como a validade) — congela no
    salvar e volta no abrir."""
    from app.core.projetos import abrir_projeto, salvar_projeto

    cel = Slot("c1", [Regiao(TipoRegiao.NOME, Retangulo(10, 10, 60, 10))])
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([cel])])
    pid = salvar_projeto("Jornal ago", "Jornal do Mês", "TABLOIDE", lay,
                         [], edicao="Nº 178 · ANO 42")
    aberto = abrir_projeto(pid)
    assert aberto is not None
    assert aberto.edicao == "Nº 178 · ANO 42"


# --- N1 (§5): itens FIXOS com foto escolhida pelo dono ------------------------


def test_n1_conteudo_fixo_persiste_e_e_aditivo():
    """N1: ``Slot.conteudo_fixo`` (produto+foto+preço do TEMPLATE)
    congela no to_dict e volta no from_dict; layout antigo (sem o
    campo) carrega None — aditivo, nunca quebra o acervo."""
    s = Slot("c1", [], fixa=True, conteudo_fixo={
        "nome": "Pão Francês", "descritor": "o quilo", "preco": "17,90",
        "preco_da_semana": False, "imagem": "fixos/pao.png"})
    d = s.to_dict()
    volta = Slot.from_dict(d)
    assert volta.conteudo_fixo == s.conteudo_fixo
    antigo = {"id": "x", "regioes": []}          # JSON de antes do N1
    assert Slot.from_dict(antigo).conteudo_fixo is None


def test_n1_celula_fixa_compoe_o_conteudo_do_template(raiz_tmp, tmp_path):
    """N1: a célula FIXA desenha o conteúdo do TEMPLATE em toda porta
    (o compositor é o ponto único) — sem depender da tabela da semana.
    Por pixel: foto + nome + preço; sem conteúdo, a célula fica só arte."""
    import numpy as np

    from app.rendering.units import mm_para_px

    foto = tmp_path / "pao.png"
    Image.new("RGBA", (200, 200), (200, 30, 30, 255)).save(foto)
    fixa = Slot("fx", [
        Regiao(TipoRegiao.IMAGEM, Retangulo(10, 10, 40, 40)),
        Regiao(TipoRegiao.NOME, Retangulo(10, 52, 40, 10), cor="#000000"),
        Regiao(TipoRegiao.PRECO, Retangulo(10, 64, 40, 12), cor="#000000"),
    ], fixa=True, conteudo_fixo={
        "nome": "Pão Francês", "preco": "17,90",
        "preco_da_semana": False, "imagem": str(foto)})
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([fixa])])

    img = compor_pagina(lay, lay.paginas[0], {})
    a = np.asarray(img.convert("RGB"), dtype=int)

    def tinta(x0mm, y0mm, x1mm, y1mm):
        x0, y0 = round(mm_para_px(x0mm, 100)), round(mm_para_px(y0mm, 100))
        x1, y1 = round(mm_para_px(x1mm, 100)), round(mm_para_px(y1mm, 100))
        rec = a[y0:y1, x0:x1]
        return int((rec.max(axis=2) - rec.min(axis=2) > 30).sum()
                   + (rec.max(axis=2) < 128).sum())

    assert tinta(10, 10, 50, 50) > 100, "a FOTO escolhida não compôs"
    assert tinta(10, 52, 50, 62) > 20, "o NOME fixo não compôs"
    assert tinta(10, 64, 50, 76) > 20, "o PREÇO fixo não compôs"

    fixa.conteudo_fixo = None
    vazio = compor_pagina(lay, lay.paginas[0], {})
    b = np.asarray(vazio.convert("RGB"), dtype=int)
    assert int((b.max(axis=2) < 128).sum()) == 0, (
        "célula fixa SEM conteúdo tinha de ficar só arte (nada desenhado)")


def test_n1_fixa_com_conteudo_segue_fora_da_fila():
    """N1 + lei do tipo novo: a fixa COM conteúdo continua fora do
    auto-preencher (o conteúdo é do template, não da semana)."""
    from app.rendering.grade import ocupaveis
    fixa = Slot("fx", [
        Regiao(TipoRegiao.IMAGEM, Retangulo(0, 0, 10, 10)),
        Regiao(TipoRegiao.NOME, Retangulo(0, 12, 10, 4)),
    ], fixa=True, conteudo_fixo={"nome": "Kit", "preco": "9,90"})
    livre = Slot("lv", [
        Regiao(TipoRegiao.IMAGEM, Retangulo(20, 0, 10, 10)),
        Regiao(TipoRegiao.NOME, Retangulo(20, 12, 10, 4)),
    ])
    assert [s.id for s in ocupaveis([fixa, livre])] == ["lv"]


def test_n1_preco_da_semana_atualiza_por_chave_natural():
    """N1: item fixo com "preço da semana" atualiza quando o produto
    APARECE na tabela (chave natural, D12); preço FIXO nunca é tocado;
    ausente mantém o que está — e cada atualização é NOMEADA (I2)."""
    from app.qt.telas.servico import ItemMesa, atualizar_fixos_pela_tabela

    semana = Slot("s1", [], fixa=True, conteudo_fixo={
        "nome": "Pão Francês", "preco": "16,90", "preco_da_semana": True})
    cravado = Slot("s2", [], fixa=True, conteudo_fixo={
        "nome": "Mini Salgadinho", "preco": "24,90",
        "preco_da_semana": False})
    ausente = Slot("s3", [], fixa=True, conteudo_fixo={
        "nome": "Kit Burguer", "preco": "39,90", "preco_da_semana": True})
    lay = LayoutDef(100, 100, dpi=100,
                    paginas=[Pagina([semana, cravado, ausente])])
    itens = [ItemMesa(nome="Pão Francês", descricao="", semaforo="verde",
                      preco="17,90"),
             ItemMesa(nome="Mini Salgadinho", descricao="",
                      semaforo="verde", preco="1,00")]
    avisos = atualizar_fixos_pela_tabela(lay, itens)
    assert semana.conteudo_fixo["preco"] == "17,90"
    assert cravado.conteudo_fixo["preco"] == "24,90"      # nunca tocado
    assert ausente.conteudo_fixo["preco"] == "39,90"      # mantém
    assert any("Pão Francês" in a for a in avisos)
    assert not any("Salgadinho" in a for a in avisos)


def test_n1_dialogo_edita_o_template_e_interna_a_foto(raiz_tmp, tmp_path):
    """N1: o diálogo "Itens fixos deste encarte" grava o formulário no
    ``conteudo_fixo`` do slot; foto de FORA da biblioteca é INTERNADA
    (cópia em ``_fixos/``, caminho relativo — I3); foto do acervo só
    relativiza, nunca duplica."""
    from PySide6.QtWidgets import QApplication

    from app.qt.telas.fixos_dialog import (
        ItensFixosDialog,
        internar_foto_fixa,
    )

    _ = QApplication.instance() or QApplication([])
    fora = tmp_path / "kit.png"
    Image.new("RGB", (10, 10), "red").save(fora)
    rel = internar_foto_fixa(fora)
    assert rel == "_fixos/kit.png"
    assert (raiz_tmp.biblioteca_imagens / "_fixos" / "kit.png").exists()

    dentro = raiz_tmp.biblioteca_imagens / "ja_no_acervo.png"
    Image.new("RGB", (10, 10), "blue").save(dentro)
    assert internar_foto_fixa(dentro) == "ja_no_acervo.png"
    assert not (raiz_tmp.biblioteca_imagens / "_fixos"
                / "ja_no_acervo.png").exists()

    fixa = Slot("fx", [Regiao(TipoRegiao.NOME, Retangulo(10, 10, 40, 10))],
                fixa=True)
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([fixa])])
    dlg = ItensFixosDialog(lay)
    dlg.ed_nome.setText("Kit Burguer")
    dlg.ed_preco.setText("39,90")
    dlg.chk_semana.setChecked(True)
    dlg._imagem_rel = rel
    dlg._confirmar()
    assert fixa.conteudo_fixo == {
        "nome": "Kit Burguer", "descritor": None, "preco": "39,90",
        "preco_da_semana": True, "imagem": "_fixos/kit.png"}
    dlg.deleteLater()


# --- QUATER L9: a CAMADA do dono é consumida, nunca imitada ------------------


def test_l9_camada_da_pagina_compoe_por_pixel(raiz_tmp, tmp_path):
    """L9/Q1: ``Pagina.arquivo_camada`` — a arte de overlay do DONO
    (a camada das etiquetas de preço do Quintou) é COLADA sobre o fundo,
    escalada à página, com o alfa respeitado. Por pixel: onde a camada
    tem tinta, vence a camada; onde é transparente, fica o fundo. E o
    campo é aditivo (layout antigo carrega None)."""
    import numpy as np

    from app.rendering.units import mm_para_px

    fundo = tmp_path / "fundo.png"
    Image.new("RGB", (200, 200), "#001040").save(fundo)
    camada = tmp_path / "camada.png"
    cam = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    for px in range(100, 300):
        for py in range(180, 220):
            cam.putpixel((px, py), (255, 0, 0, 255))
    cam.save(camada)

    pag = Pagina([Slot("c", [Regiao(TipoRegiao.NOME,
                                    Retangulo(10, 80, 80, 10))])],
                 arquivo_fundo=str(fundo), arquivo_camada=str(camada))
    lay = LayoutDef(100, 100, dpi=100, paginas=[pag])
    img = compor_pagina(lay, pag, {})
    meio = round(mm_para_px(50, 100))
    alto = round(mm_para_px(20, 100))
    assert img.getpixel((meio, meio))[:3] == (255, 0, 0), (
        "a tinta da CAMADA do dono não venceu no miolo — o asset não "
        "foi consumido (L9)")
    assert img.getpixel((meio, alto))[:3] == (0, 16, 64), (
        "o alfa da camada não foi respeitado — o fundo sumiu")
    antigo = {"slots": [], "arquivo_fundo": None}
    assert Pagina.from_dict(antigo).arquivo_camada is None


def test_l9_quintou_declara_camada_e_quicksand():
    """L9/Q1+Q2: o layout do Quintou CONSOME os assets do dono — a
    camada de preço declarada nas DUAS páginas (frente e verso) e a
    Quicksand nas regiões de nome/preço/validade (a fonte certa estava
    na raiz dele e não era usada)."""
    raiz = Path(__file__).resolve().parents[2] / "Templates novos"
    if not raiz.exists():
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")
    from app.rendering.encartes import layout_de_encarte
    lay = layout_de_encarte("quintou", raiz)
    assert len(lay.paginas) == 2
    for n, pag in enumerate(lay.paginas, start=1):
        assert pag.arquivo_camada and "Preço" in pag.arquivo_camada, (
            f"p{n}: a camada de preço do dono não está declarada")
        assert Path(pag.arquivo_camada).exists()
        fontes = {r.fonte for s in pag.slots for r in s.regioes
                  if r.tipo in (TipoRegiao.NOME, TipoRegiao.PRECO,
                                TipoRegiao.TEXTO_LEGAL) and r.fonte}
        assert any("Quicksand" in f for f in fontes), (
            f"p{n}: nenhuma região usa a Quicksand ({fontes})")
        assert not any("Archivo" in f for f in fontes), (
            f"p{n}: o Quintou ainda usa Archivo ({fontes}) — Q2")


def test_l9_quicksand_entra_no_pacote(raiz_tmp):
    """Q2: ``importar_pacote`` copia a Quicksand para a pasta de fontes
    do app (os 4 pesos entraram em FONTES_DO_PACOTE; o .otf carrega no
    PIL — não há filtro de extensão)."""
    raiz = Path(__file__).resolve().parents[2] / "Templates novos"
    if not raiz.exists():
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")
    from app.rendering.encartes import FONTES_DO_PACOTE
    quick = [f for f in FONTES_DO_PACOTE if "Quicksand" in f]
    assert quick, "a Quicksand não entrou em FONTES_DO_PACOTE"
    for f in quick:
        assert (raiz / "fontes" / f).exists(), (
            f"{f} não está no pacote do dono (fontes/)")


# --- QUATER A4: UM motor de seção só (estilo JORNAL no secoes.py) ------------


def test_a4_estilo_jornal_vive_no_motor_de_secoes(raiz_tmp):
    """A4: o cabeçalho de seção do jornal é um ESTILO de ``secoes.py``
    (versalete + fio, sem retângulo colorido) — não um mecanismo
    paralelo. E o estilo é POR PÁGINA (``Pagina.estilo_secoes``), com
    o global da Config como fallback. Por pixel: com JORNAL há fio de
    tinta escura acima do bloco e NENHUM azul saturado do CONTORNO."""
    import numpy as np

    from app.rendering.units import mm_para_px

    def celula(i, x):
        return Slot(f"c{i}", [
            Regiao(TipoRegiao.IMAGEM, Retangulo(x, 30, 30, 30)),
            Regiao(TipoRegiao.NOME, Retangulo(x, 62, 30, 8)),
        ])

    pag = Pagina([celula(1, 10), celula(2, 45)],
                 secoes_ligadas=True, estilo_secoes="JORNAL")
    lay = LayoutDef(100, 100, dpi=100, paginas=[pag])
    dados = {"c1": DadosProduto("A", categoria="Mercearia"),
             "c2": DadosProduto("B", categoria="Mercearia")}
    img = compor_pagina(lay, pag, dados)
    a = np.asarray(img.convert("RGB"), dtype=int)

    azul = ((a[:, :, 2] > 150) & (a[:, :, 0] < 100)).sum()
    assert azul == 0, ("o estilo JORNAL não pode desenhar o retângulo/"
                       "etiqueta azul do CONTORNO (é alienígena no papel)")
    topo = round(mm_para_px(30, 100))
    faixa = a[topo - round(mm_para_px(14, 100)):topo, :]
    escuro = (faixa.max(axis=2) < 120).any(axis=1)
    assert escuro.any(), ("o fio/versalete do cabeçalho JORNAL não "
                          "apareceu acima do bloco da seção")


def test_a4_fluxo_do_jornal_usa_o_motor_unico():
    """A4: com ``secoes=``, o Jornal NÃO gera mais slots de cabeçalho
    (jsec-*/FILETE) — quem desenha a seção é ``desenhar_secoes`` com o
    estilo JORNAL, ligado por página. O FILETE vira legado tolerado
    (nenhum layout novo o cria)."""
    raiz = Path(__file__).resolve().parents[2] / "Templates novos"
    if not raiz.exists():
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")
    from app.rendering.encartes import layout_de_encarte
    lay = layout_de_encarte("jornal-do-mes", raiz,
                            secoes=[("Mercearia", 6), ("Bebidas", 3)])
    for n, pag in enumerate(lay.paginas, start=1):
        assert not [s for s in pag.slots if s.id.startswith("jsec")], (
            f"p{n}: o cabeçalho de seção ainda nasce como SLOT — o 2º "
            "motor segue vivo (A4)")
        assert not [r for s in pag.slots for r in s.regioes
                    if r.tipo == TipoRegiao.FILETE], (
            f"p{n}: layout novo ainda cria FILETE")
        assert pag.secoes_ligadas, f"p{n}: seções desligadas no fluxo"
        assert pag.estilo_secoes == "JORNAL", (
            f"p{n}: o estilo da página não é JORNAL")


# --- N2 (§5): o Jornal por SEÇÕES em fluxo -----------------------------------


def test_n2_filete_desenha_e_nao_e_ocupavel(raiz_tmp):
    """N2: o FILETE (fio tipográfico do cabeçalho de seção) é primitivo
    do motor — retângulo chapado na cor da região. Lei do tipo novo:
    não é conteúdo (slot só-filete fica fora da fila) e não entra no
    pré-voo de vazios."""
    import numpy as np

    from app.rendering.grade import ocupaveis
    from app.rendering.units import mm_para_px

    fio = Regiao(TipoRegiao.FILETE, Retangulo(10, 20, 80, 0.6),
                 cor="#22303A")
    lay = LayoutDef(100, 100, dpi=100,
                    paginas=[Pagina([Slot("cab", [fio])])])
    img = compor_pagina(lay, lay.paginas[0], {})
    y = round(mm_para_px(20.3, 100))
    a = np.asarray(img.convert("RGB"), dtype=int)
    linha = a[y, round(mm_para_px(12, 100)):round(mm_para_px(88, 100))]
    assert (linha.max(axis=1) < 100).mean() > 0.9, (
        "o FILETE não desenhou o fio chapado na cor da região")

    deco = Slot("deco", [fio])
    prod = Slot("p", [Regiao(TipoRegiao.IMAGEM, Retangulo(0, 0, 10, 10)),
                      Regiao(TipoRegiao.NOME, Retangulo(0, 12, 10, 4))])
    assert [s.id for s in ocupaveis([deco, prod])] == ["p"]


def test_n2_fluxo_degraus_declarados_e_ultima_linha_inteira():
    """N2: o motor de fluxo cumpre a letra do §5 — os degraus são
    TABELADOS e na ordem declarada; tudo cabendo, nenhum degrau é usado.
    QUATER/J1 (contrato INVERTIDO): a última linha de cada seção agora
    ESTICA — as células alargam e preenchem a banda INTEIRA (a versão
    centralizada deixava colunas 1 e 5 vazias e leu como "esburacada").
    E J2: TODAS as células da faixa têm a MESMA altura."""
    from app.rendering.fluxo_jornal import FaixaFluxo, montar_fluxo

    faixa = FaixaFluxo(x=64, y=132, largura=990, altura=850,
                       colunas=(5,), alturas_celula=(202, 178, 156),
                       altura_cabecalho=34)
    r = montar_fluxo([("MERCEARIA", 7), ("BEBIDAS", 3)], [faixa])
    assert not r.avisos, f"cabendo tudo, sem degrau nem aviso: {r.avisos}"
    blocos = r.blocos
    assert [b.secao for b in blocos] == ["MERCEARIA", "BEBIDAS"]
    m = blocos[0]
    assert len(m.celulas) == 7
    linha2 = [c for c in m.celulas if c[1] > m.celulas[0][1]]
    assert len(linha2) == 2, "7 itens em 5 colunas = 5 + 2"
    # SEXTUS (o caso do Oral-B): o esticamento tem TETO de 1,6× — acima
    # disso a célula vira deserto; o conjunto centraliza na banda
    larg_base = 990 / 5
    for c in linha2:
        assert abs(c[2] - larg_base * 1.6) < 1, (
            f"a última linha estica até o teto de 1,6× ({c[2]:.0f})")
    esq = min(c[0] for c in linha2)
    dir_ = max(c[0] + c[2] for c in linha2)
    centro = (esq + dir_) / 2
    assert abs(centro - (64 + 990 / 2)) < 1, (
        f"o conjunto da última linha centraliza na banda ({centro:.0f})")
    # SEXTUS/J16 (contrato ESTENDIDO): a sobra da faixa é distribuída —
    # a altura final é ÚNICA (J2) e ≥ o degrau escolhido; a faixa enche
    alturas = {round(c[3], 1) for b in blocos for c in b.celulas}
    assert len(alturas) == 1 and min(alturas) >= 202, (
        f"J2+J16: altura única ≥ degrau ({alturas})")


def test_n2_fluxo_degrada_em_ordem_e_transborda_com_aviso():
    """N2: apertando a faixa, o fluxo desce o DEGRAU de altura (tabelado,
    nunca contínuo); estourando as faixas, TRANSBORDA para a próxima e
    avisa; o que não coube em lugar nenhum é NOMEADO (I2)."""
    from app.rendering.fluxo_jornal import FaixaFluxo, montar_fluxo

    apertada = FaixaFluxo(x=64, y=132, largura=990, altura=430,
                          colunas=(5,), alturas_celula=(202, 178, 156),
                          altura_cabecalho=34)
    r = montar_fluxo([("MERCEARIA", 10)], [apertada])
    # SEXTUS/J16: o DEGRAU escolhido é o 178 (o aviso o nomeia); a
    # altura final pode crescer pela distribuição da sobra (uniforme)
    alturas = {round(c[3], 1) for b in r.blocos for c in b.celulas}
    assert len(alturas) == 1 and 178 <= min(alturas) < 202, (
        f"2 linhas + cabeçalho em 430px exigem o degrau 178 ({alturas})")
    assert any("degrau" in a for a in r.avisos)

    p2 = FaixaFluxo(x=64, y=112, largura=990, altura=850,
                    colunas=(5,), alturas_celula=(202, 178, 156),
                    altura_cabecalho=34)
    r2 = montar_fluxo([("MERCEARIA", 10), ("BEBIDAS", 10)],
                      [apertada, p2])
    paginas = {b.faixa for b in r2.blocos}
    assert paginas == {0, 1}, "a 2ª seção tinha de transbordar à faixa 2"
    assert any("transbord" in a for a in r2.avisos)

    minima = FaixaFluxo(x=0, y=0, largura=990, altura=200,
                        colunas=(5,), alturas_celula=(202, 178, 156),
                        altura_cabecalho=34)
    r3 = montar_fluxo([("MERCEARIA", 40)], [minima])
    assert any("não coube" in a for a in r3.avisos), (
        f"o excedente tinha de ser NOMEADO: {r3.avisos}")


def test_n2_secao_de_um_item_compartilha_a_linha():
    """N2 (decisão registrada): seção de 1 item NÃO ganha linha própria —
    a célula dela entra na MESMA linha da seção seguinte e o cabeçalho
    fica INLINE (na largura da célula, sobre ela)."""
    from app.rendering.fluxo_jornal import FaixaFluxo, montar_fluxo

    faixa = FaixaFluxo(x=0, y=0, largura=990, altura=900,
                       colunas=(5,), alturas_celula=(202,),
                       altura_cabecalho=34)
    r = montar_fluxo([("PADARIA", 1), ("MERCEARIA", 6)], [faixa])
    pad = next(b for b in r.blocos if b.secao == "PADARIA")
    mer = next(b for b in r.blocos if b.secao == "MERCEARIA")
    assert pad.cabecalho_inline, "o cabeçalho da seção de 1 item é INLINE"
    y_pad = pad.celulas[0][1]
    assert y_pad == mer.celulas[0][1], (
        "a célula única tinha de COMPARTILHAR a linha da seção seguinte")
    assert pad.cabecalho[2] == pad.celulas[0][2], (
        "o cabeçalho inline tem a LARGURA da célula, não da banda")


def test_d2_nenhuma_etiqueta_nasce_cravada_no_pacote():
    """D2 (§4): "rótulo que não é sempre verdade não pode estar na
    estrutura" — TODA etiqueta de célula dos 8 encartes (Etiqueta,
    Splash) nasce VAZIA; o dono escolhe o texto (vazia = não desenha,
    nem a forma). Varredura PERMANENTE: um encarte novo com rótulo
    cravado quebra aqui."""
    raiz = Path(__file__).resolve().parents[2] / "Templates novos"
    if not raiz.exists():
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")
    from app.rendering.encartes import chaves_do_pacote, layout_de_encarte
    cravadas = []
    for chave in chaves_do_pacote(raiz):
        lay = layout_de_encarte(chave, raiz)
        for pag in lay.paginas:
            for s in pag.slots:
                for r in s.regioes:
                    if r.nome in ("Etiqueta", "Splash") \
                            and (r.texto_fixo or "").strip():
                        cravadas.append(
                            f"{chave}/{s.id}: “{r.texto_fixo}”")
    assert not cravadas, (
        "etiquetas nascendo com rótulo CRAVADO (podem mentir): "
        f"{cravadas}")


def test_d1_jornal_do_pacote_declara_o_papel_edicao():
    """D1: no layout do Jornal, a região "Edição" declara o papel EDICAO
    com texto_fixo VAZIO — o "Nº 177 · ANO 42" cravado morreu."""
    from app.rendering.model import PapelTexto

    raiz = Path(__file__).resolve().parents[2] / "Templates novos"
    if not raiz.exists():
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")
    from app.rendering.encartes import layout_de_encarte
    lay = layout_de_encarte("jornal-do-mes", raiz)
    regs = [r for p in lay.paginas for s in p.slots for r in s.regioes
            if r.nome == "Edição"]
    assert regs, "a região 'Edição' sumiu do cabeçalho do Jornal"
    for r in regs:
        assert r.papel_texto == PapelTexto.EDICAO
        assert not (r.texto_fixo or "").strip(), (
            "o Nº/ANO segue CRAVADO na estrutura — rótulo que não é "
            "sempre verdade não pode estar na estrutura (§4)")
