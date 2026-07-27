"""A página de inspeção do laço F13-BIS (COND-11).

Compõe cada encarte com DADOS REAIS do acervo do dono — foto da
biblioteca real, nome sanitizado sem .upper(), preços reais, células
FIXAS com o conteúdo fixo, validade da semana do pacote — e gera o par
lado a lado (app | PREVIEW) em ``saida_f13/galeria_f13_bis/``.

É o artefato que responde "o dono publicaria isto?" — dados reais,
caminho real, sem fixture no meio (a lição do §5 da ordem).

Uso:
    python -m app.scripts.inspecao_encartes "Templates novos" [chave...]
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parents[2]
ACERVO = RAIZ_REPO / "AutoTabloide_System_Root" / "biblioteca_imagens"
GALERIA = RAIZ_REPO / "saida_f13" / "galeria_f13_bis"


def _foto(rel: str) -> str | None:
    p = ACERVO / rel
    return str(p) if p.exists() else None


# célula → (nome, descritor, preço "por", foto do acervo, extra)
# Produtos REAIS do banco/biblioteca do dono, escalados para o dia.
DADOS: dict[str, dict] = {
    "segunda-frios": {
        "validade": "27/07",
        "itens": {
            # a FIXA com o conteúdo fixo do modelo; não há foto de
            # hambúrguer no acervo — vai a mussarela (declarado: o dono
            # cadastra a foto real do kit)
            "celula-1": ("Senepal BBX", "blend senepol · 4 un × 120 g",
                         "24,90",
                         _foto("_auto/queijo_mussarela_latopar_1kg.png")),
            "celula-2": ("Queijo Mussarela Latopar", "Lactopar · quilo",
                         "55,05",
                         _foto("_auto/queijo_mussarela_latopar_1kg.png")),
            "celula-3": ("Leite Parmalat", "integral · 1 L",
                         "5,95", _foto("_auto/leite_parmalat_integral_1l.png")),
            "celula-4": ("Leite em Pó Ninho", "integral · lata 380 g",
                         "28,81",
                         _foto("_auto/leite_p_ninho_integral_instant_neo_380g.png")),
            "celula-5": ("Creme de Leite Italac", "caixinha 200 g",
                         "2,44", _foto("40/atual.png")),
            "celula-6": ("Leite Condensado Moça", "TP 395 g",
                         "8,88", _foto("38/atual.png")),
            "celula-7": ("Café Brasileiro", "extra forte · 500 g",
                         "23,99", _foto("12/atual.png")),
            "celula-8": ("Coco Ralado Menina", "100 g",
                         "4,44", _foto("5/atual.png")),
        },
    },
    "quarta-das-ofertas": {
        "validade": "29/07",
        "itens": {
            # as 3 FIXAS com o conteúdo FIXO do modelo (§3.3.4); a 3ª
            # tem de/por REAIS para o -% ser CALCULADO (nunca digitado)
            "celula-fixa-1": ("Mini Salgadinho BBX", "100 g", "4,99",
                              _foto("_auto/p_o_caseiro_bb_s_100g.png")),
            "celula-fixa-2": ("Pão de Queijo", "tradicional · 100 g",
                              "4,99",
                              _foto("_auto/p_o_caseiro_bb_x_s_100g.png")),
            "celula-fixa-3": ("Lanche na Chapa", "no capricho", "8,00",
                              _foto("35/atual.png"), "10,00"),
            "celula-var-1": ("Creme Dental Kolynos", "tubo 90 g", "6,90",
                             _foto("_auto/creme_dental_kolinos_90g.png")),
            "celula-var-2": ("Desodorante One", "aerossol · 150 mL",
                             "9,90",
                             _foto("_auto/desodorante_above_one_men_150ml.png")),
            "celula-var-3": ("Refri Kitubaína", "garrafa 1,5 L", "5,50",
                             _foto("_auto/refrigerante_kitubaina_1_5l.png")),
            "celula-var-4": ("Amaciante Ypê", "fragrâncias · 5 L",
                             "26,66", _foto("_auto/amaciante_yp_5l.png")),
            "celula-var-5": ("Chocolate M&M's", "amendoim · 40 g",
                             "4,94", _foto("23/atual.png")),
        },
    },
    "sabado-da-carne": {
        "validade": "01/08",
        "mais18": ["celula-9", "celula-10"],   # a lei: +18 SEMPRE em álcool
        "itens": {
            # o açougue REAL do banco do dono (BBX = a marca da casa)
            "celula-1": ("Bife à Milanesa BBX", "bovino · 100 g",
                         "4,90", _foto("13/atual.png")),
            "celula-2": ("Linguiça Perdigão", "pro churrasco · 100 g",
                         "2,50", _foto("34/atual.png")),
            "celula-3": ("Fígado Bovino BBX", "resfriado · 100 g",
                         "0,99", _foto("4/atual.png")),
            "celula-4": ("Coração e Língua Bovina", "BBX · 100 g",
                         "0,77", _foto("7/atual.png")),
            "celula-5": ("Coxa Sobrecoxa", "frango · 100 g",
                         "0,77", _foto("21/atual.png")),
            "celula-6": ("Frango Marombi", "congelado · 100 g",
                         "0,99", _foto("35/atual.png")),
            "celula-7": ("Tortilha Queijo Nacho", "Bebela · 84 g",
                         "5,90", _foto("9/atual.png")),
            "celula-8": ("Snack La Violetera", "aperitivo · 40 g",
                         "4,91", _foto("20/atual.png")),
            "celula-9": ("Cerveja Amstel", "lata 269 mL", "2,99",
                         _foto("_auto/cerveja_amstel_269ml.png")),
            "celula-10": ("Cerveja Amstel Palito", "269 mL", "2,90",
                          _foto("_auto/cerveja_amstel_palito_269ml.png")),
        },
    },
    "jornal-do-mes": {
        "validade": "OFERTAS VÁLIDAS DE 01/08 A 27/08/2026 OU ENQUANTO "
                    "DURAREM OS ESTOQUES · IMAGENS MERAMENTE "
                    "ILUSTRATIVAS · (66) 9969-4009 / (66) 3419-1405",
        "validade_p2": "válidas de 01/08 a 27/08/2026 ou enquanto "
                       "durarem os estoques",
        "dica": "Fica a dica: o pacotão de arroz de 5 kg rende mais de "
                "50 pratos — sai por menos de R$ 0,60 o prato.",
        "dica_p2": "Fica a dica: compare o preço por quilo — a página "
                   "2 concentra as embalagens econômicas do mês.",
        "mais18": ["jp2-l8"],
        "itens": {
            # o HERO do modelo EXISTE no acervo: o pacotão de arroz
            "jp1-hero": ("Arroz Somar & Caibi",
                         "o pacotão de 5 kg do mês", None,
                         _foto("_auto/arroz_somar_e_caibi_5kg.png")),
            "jp1-ch1": ("Leite em Pó Ninho", "integral · lata 380 g",
                        "28,81",
                        _foto("_auto/leite_p_ninho_integral_instant_neo_380g.png")),
            "jp1-ch2": ("Molho de Tomate", "Fugini/Cajamar · 300 g",
                        "1,50",
                        _foto("_auto/molho_tomate_fujini_e_cajamar_300g_original.png")),
            "jp1-ch3": ("Açúcar Cristal", "Doce Dia · 2 kg", "5,95",
                        _foto("_auto/a_car_cristal_doce_dia_2kg.png")),
            "jp1-ch4": ("Sabão em Pó Maciez", "Primavera · 1,6 kg",
                        "23,90",
                        _foto("_auto/sab_o_em_p_maciez_primavera.png")),
            "jp1-l1": ("Salgadinho Ruppers", "galinha · 50 g", "1,90",
                       _foto("2/atual.png")),
            "jp1-l2": ("Tortilha Queijo Nacho", "Bebela · 84 g", "5,90",
                       _foto("9/atual.png")),
            "jp1-l3": ("Amido de Milho Quero", "200 g", "4,90",
                       _foto("10/atual.png")),
            "jp1-l4": ("Goma Dori Minhocas", "frutas ácidas · 100 g",
                       "4,90", _foto("14/atual.png")),
            "jp1-l5": ("Biscoito Bauducco", "duplo chocolate · 140 g",
                       "1,90", _foto("15/atual.png")),
            "jp1-l6": ("Sal Amoníaco Mika", "gourmet · 100 g", "1,90",
                       _foto("16/atual.png")),
            "jp1-l7": ("Geleia Ritter", "alho caramelizado · 290 g",
                       "18,81", _foto("17/atual.png")),
            "jp1-l8": ("Macarrão Nissin", "canja de galinha · 70 g",
                       "2,66", _foto("19/atual.png")),
            "jp1-l9": ("Snack La Violetera", "aperitivo · 40 g", "4,91",
                       _foto("20/atual.png")),
            "jp1-l10": ("Coxa Sobrecoxa", "frango · 100 g", "0,77",
                        _foto("21/atual.png")),
            "jp1-l11": ("Extrato de Tomate", "pote 300 g", "4,44",
                        _foto("22/atual.png")),
            "jp1-l12": ("Granola Happy Life", "banana e canela · 250 g",
                        "6,66", _foto("24/atual.png")),
            "jp1-l13": ("Pé de Moleque Pinduca", "150 g", "8,88",
                        _foto("26/atual.png")),
            "jp1-l14": ("Ração Kit e Kat", "carne ao molho · 70 g",
                        "2,92", _foto("8/atual.png")),
            "jp1-l15": ("Creme Dental Oral-B", "detox · 102 g", "19,90",
                        _foto("25/atual.png")),
            "jp2-l1": ("Batata Palha Bulnez", "crocante · 100 g",
                       "6,66", _foto("_auto/batata_palha_bulnez_100g.png")),
            "jp2-l2": ("Creme Dental Kolynos", "tubo 90 g", "6,90",
                       _foto("_auto/creme_dental_kolinos_90g.png")),
            "jp2-l3": ("Desodorante One", "aerossol · 150 mL", "9,90",
                       _foto("_auto/desodorante_above_one_men_150ml.png")),
            "jp2-l4": ("Refri Kitubaína", "garrafa 1,5 L", "5,50",
                       _foto("_auto/refrigerante_kitubaina_1_5l.png")),
            # o Óleo Liza do modelo é SUPER OFERTA sem preço — aqui sai
            # sem carimbo (o splash por célula da grade fica p/ o G)
            "jp2-l5": ("Óleo de Soja Liza", "pet 900 mL", None,
                       _foto("_auto/leo_de_soja_liza_900ml.png")),
            "jp2-l6": ("Queijo Mussarela", "Lactopar · quilo", "55,05",
                       _foto("_auto/queijo_mussarela_latopar_1kg.png")),
            "jp2-l7": ("Leite Parmalat", "integral · 1 L", "5,95",
                       _foto("_auto/leite_parmalat_integral_1l.png")),
            "jp2-l8": ("Cerveja Amstel", "lata 269 mL", "2,99",
                       _foto("_auto/cerveja_amstel_269ml.png")),
            "jp2-l9": ("Doce de Leite Frimesa", "original · 400 g",
                       "13,90", _foto("1/atual.png")),
            "jp2-l10": ("Rosquinha Itamaraty", "banana e canela · 250 g",
                        "4,90", _foto("3/atual.png")),
            "jp2-l11": ("Coco Ralado Menina", "100 g", "4,44",
                        _foto("5/atual.png")),
            "jp2-l12": ("Doce de Banana Val", "250 g", "6,66",
                        _foto("6/atual.png")),
            "jp2-l13": ("Rosquinha Mabel", "chocolate · 300 g", "6,61",
                        _foto("11/atual.png")),
            "jp2-l14": ("Café Brasileiro", "extra forte · 500 g",
                        "23,99", _foto("12/atual.png")),
            "jp2-l15": ("Bife à Milanesa BBX", "bovino · 100 g", "4,90",
                        _foto("13/atual.png")),
            "jp2-l16": ("Açúcar Mascavo União", "1 kg", "19,99",
                        _foto("18/atual.png")),
            "jp2-l17": ("Chocolate M&M's", "amendoim · 40 g", "4,94",
                        _foto("23/atual.png")),
            "jp2-l18": ("Aromatizante Giorno", "sachê lavanda · 15 g",
                        "9,99", _foto("29/atual.png")),
            "jp2-l19": ("Azeite Andorinha", "lata 200 mL", "29,99",
                        _foto("30/atual.png")),
            "jp2-l20": ("Kit Shampoo Natu Hair", "300 mL", "19,90",
                        _foto("31/atual.png")),
            "jp2-l21": ("Sabonete Dove", "antibacteriano · 250 mL",
                        "11,91", _foto("33/atual.png")),
            "jp2-l22": ("Leite Condensado Moça", "TP 395 g", "8,88",
                        _foto("38/atual.png")),
        },
    },
    "quinta-do-peixe": {
        # não há PESCADO no acervo do dono — a página de inspeção sai
        # com as proteínas/congelados REAIS do banco (declarado); os
        # rótulos de destaque são texto_fixo do layout (o dono edita)
        "validade": "30/07",
        "itens": {
            "celula-1": ("Frango Marombi", "congelado · 100 g",
                         "0,99", _foto("35/atual.png")),
            "celula-2": ("Coxa Sobrecoxa", "frango · 100 g",
                         "0,77", _foto("21/atual.png")),
            "celula-3": ("Fígado Bovino BBX", "resfriado · 100 g",
                         "0,99", _foto("4/atual.png")),
            "celula-4": ("Bife à Milanesa BBX", "bovino · 100 g",
                         "4,90", _foto("13/atual.png")),
            "celula-5": ("Coração e Língua", "bovina BBX · 100 g",
                         "0,77", _foto("7/atual.png")),
            "celula-6": ("Linguiça Perdigão", "pro churrasco · 100 g",
                         "2,50", _foto("34/atual.png")),
            "celula-7": ("Macarrão Nissin", "canja de galinha · 70 g",
                         "2,66", _foto("19/atual.png")),
        },
    },
    "sexta-verde": {
        # o acervo ainda não tem hortifrúti FRESCO (é mercearia/limpeza)
        # — a página sai com a mercearia-verde REAL do banco; quando o
        # dono cadastrar o hortifrúti da semana, as células recebem os
        # frescos (declarado na frase da página)
        "validade": "31/07",
        "itens": {
            "celula-banca-1": ("Granola Happy Life",
                               "banana e canela · 250 g", "6,66",
                               _foto("24/atual.png")),
            "celula-banca-2": ("Azeite Andorinha", "lata 200 mL",
                               "29,99", _foto("30/atual.png")),
            "celula-3": ("Extrato de Tomate Só Fruta", "pote 300 g",
                         "4,44", _foto("22/atual.png")),
            "celula-4": ("Geleia Ritter", "alho caramelizado · 290 g",
                         "18,81", _foto("17/atual.png")),
            "celula-5": ("Coco Ralado Menina", "100 g", "4,44",
                         _foto("5/atual.png")),
            "celula-6": ("Amido de Milho Quero", "200 g", "4,90",
                         _foto("10/atual.png")),
            "celula-7": ("Doce de Banana Val", "250 g", "6,66",
                         _foto("6/atual.png")),
            "celula-8": ("Açúcar Mascavo União", "1 kg", "19,99",
                         _foto("18/atual.png")),
            "celula-9": ("Pesto Mastroiani", "alla genovese · 135 g",
                         "19,91", _foto("27/atual.png")),
            "celula-10": ("Snack La Violetera", "aperitivo · 40 g",
                          "4,91", _foto("20/atual.png")),
            "celula-11": ("Paçoca Rolha Pinduca", "135 g", "6,66",
                          _foto("39/atual.png")),
        },
    },
    "terca-do-pao": {
        "validade": "28/07",
        "itens": {
            # as FIXAS com o conteúdo fixo (COND-11)
            "celula-1": ("Pão Francês", "no quilo · saído do forno",
                         None, _foto("_auto/p_o_caseiro_bb_x_s_100g.png")),
            "celula-2": ("Sonho + Croissant", "a dupla do café · na unidade",
                         None, _foto("3/atual.png")),
            "celula-3": ("Pão Caseiro BBX", "unidade · 100 g",
                         "2,50", _foto("_auto/p_o_caseiro_bb_s_100g.png")),
            "celula-4": ("Rosquinha Itamaraty", "banana e canela · 250 g",
                         "4,90", _foto("3/atual.png")),
            "celula-5": ("Rosquinha Mabel", "chocolate · 300 g",
                         "6,61", _foto("11/atual.png")),
            "celula-6": ("Doce de Leite Frimesa", "original · 400 g",
                         "13,90", _foto("1/atual.png")),
        },
    },
}


def _compor(chave: str, pasta_pacote: Path) -> list[Path]:
    from PIL import Image

    from app.core.paths import SystemRoot
    from app.qt.telas.servico import preco_decimal
    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.encartes import (
        FONTES_DO_PACOTE, layout_de_encarte)
    from app.rendering.grade import ocupaveis
    from app.rendering.model import PapelTexto, TipoRegiao

    spec = DADOS[chave]
    lay = layout_de_encarte(chave, pasta_pacote)

    # raiz de trabalho DESCARTÁVEL com as fontes do pacote (o root real
    # do dono não é tocado)
    tmp = Path(tempfile.mkdtemp(prefix="inspecao_"))
    os.environ["AUTOTABLOIDE_ROOT"] = str(tmp / "raiz")
    root = SystemRoot(tmp / "raiz").criar_estrutura()
    for nome in FONTES_DO_PACOTE:
        origem = pasta_pacote / "fontes" / nome
        if origem.exists():
            shutil.copy(origem, root.fontes / nome)
    from app.tests import acervo as acervo_bancada
    acervo_bancada.copiar_fontes_reais(root.fontes)   # Roboto (fallback)

    saidas = []
    for n_pag, pag in enumerate(lay.paginas, start=1):
        dados = {}
        for sid, item in spec["itens"].items():
            if not any(s.id == sid for s in pag.slots):
                continue
            nome, descr, preco, foto = item[:4]
            preco_de = item[4] if len(item) > 4 else None
            dados[sid] = DadosProduto(
                nome, descritor=descr,
                preco_por=preco_decimal(preco) if preco else None,
                preco_de=preco_decimal(preco_de) if preco_de else None,
                imagem_path=foto,
                mais18=sid in spec.get("mais18", ()))
        validade = spec["validade"]
        if n_pag == 2 and spec.get("validade_p2"):
            validade = spec["validade_p2"]
        dica = spec.get("dica_p2") if (n_pag == 2 and
                                       spec.get("dica_p2")) \
            else spec.get("dica")
        for s in pag.slots:                 # validade da SEMANA + dica
            for r in s.regioes:
                if r.tipo != TipoRegiao.TEXTO_LEGAL:
                    continue
                if r.papel_texto == PapelTexto.VALIDADE:
                    r.texto_fixo = validade
                elif r.papel_texto == PapelTexto.DICA and dica:
                    r.texto_fixo = dica

        app_full = compor_pagina(lay, pag, dados)
        app_1x = app_full.resize((1080, 1440), Image.LANCZOS)
        nome_prev = Path(pag.arquivo_fundo).name \
            .replace("-BASE-2160x2880.png", "-PREVIEW.png") \
            .replace("-BASE.png", "-PREVIEW.png")
        preview = Image.open(Path(pag.arquivo_fundo).parent / nome_prev)
        lado = Image.new("RGB", (1080 * 2 + 8, 1440), "#666666")
        lado.paste(app_1x.convert("RGB"), (0, 0))
        lado.paste(preview.convert("RGB"), (1088, 0))
        GALERIA.mkdir(parents=True, exist_ok=True)
        sufixo = f"-p{n_pag}" if len(lay.paginas) > 1 else ""
        destino = GALERIA / f"{chave}{sufixo}.png"
        lado.save(destino)
        saidas.append(destino)
        ocup = len(ocupaveis(pag.slots))
        print(f"[{chave}{sufixo}] {len(dados)} itens em {ocup} células "
              f"livres (+fixas) → {destino.name}")
    return saidas


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    pacote = Path(sys.argv[1])
    chaves = sys.argv[2:] or list(DADOS)
    for c in chaves:
        _compor(c, pacote)
