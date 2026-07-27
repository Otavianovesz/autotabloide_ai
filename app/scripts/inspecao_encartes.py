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
    "quintou": {
        # o PADRÃO-OURO: os 15 produtos do "Quintou Frente Real.png"
        # PUBLICADO, com os preços da campanha real (16/07) e as fotos
        # do acervo — a régua é lado a lado com o próprio publicado
        "validade": "Até 16/07",
        "validade_p2": "*Imagens meramente ilustrativas · Ofertas "
                       "válidas até dia 16/07 ou enquanto durarem os "
                       "nossos estoques",
        "preview": ["Quintou/Quintou Frente Real.png",
                    "Quintou/Quintou Verso Real.png"],
        "dica": "Fica a dica: o Quintou muda toda quinta — chegou "
                "cedo, levou o melhor preço da semana.",
        # QUATER/Q4: os NOMES copiam o PUBLICADO — Title Case, peso
        # COLADO ("400g"), sem o separador "·" (descritor None: nada é
        # anexado ao nome pelo canal da unidade)
        "itens": {
            "pos-01": ("Doce de Leite Frimesa Original 400g", None,
                       "13,90", _foto("1/atual.png")),
            "pos-02": ("Goma Dori Minhocas Frutas Ácidas 100g", None,
                       "4,90", _foto("14/atual.png")),
            "pos-03": ("Fígado Bovino BBX 100g", None, "0,99",
                       _foto("4/atual.png")),
            "pos-04": ("Coração e Língua Bov. BBX 100g", None, "0,77",
                       _foto("7/atual.png")),
            "pos-05": ("Geléia Ritter Cebola Caram. 290g", None,
                       "19,90", _foto("17/atual.png")),
            "pos-06": ("Snacks La violetera Aperit. 40g", None, "4,91",
                       _foto("20/atual.png")),
            "pos-07": ("Bife a Milanesa BBX 100g", None, "4,90",
                       _foto("13/atual.png")),
            "pos-08": ("Extrato Tomate Só Fruta 300g", None, "4,44",
                       _foto("22/atual.png")),
            "pos-09": ("Ração Kit e Kat Carne ao Molho 70g", None,
                       "1,91", _foto("8/atual.png")),
            "pos-10": ("Tortilhas Queijo Nacho Bebela 84g", None,
                       "5,90", _foto("9/atual.png")),
            "pos-11": ("Choc. M&M's Amendoim 40g", None, "4,94",
                       _foto("23/atual.png")),
            "pos-12": ("Amido Milho Quero 200g", None, "1,91",
                       _foto("10/atual.png")),
            "pos-14": ("Marrom Glace Val 250g", None, "6,66",
                       _foto("6/atual.png")),
            "pos-15": ("Rosquinha Mabel Choc. 300g", None, "6,61",
                       _foto("11/atual.png")),
            "pos-16": ("Creme Dental Oral-B Detox 102g", None, "19,90",
                       _foto("25/atual.png")),
            # a logo no painel (célula FIXA com foto escolhida — N1).
            # QUATER/L9: a foto escolhida é a ARTE DO PAINEL do próprio
            # publicado (recorte de Quintou Frente Real.png) — é a que
            # o dono escolheria; a genérica deixava 20,6% de diferença
            "painel-logo": ("", None, None, str(
                RAIZ_REPO / "Templates novos" / "brand"
                / "painel_logo_quintou.png")),
            # ---- VERSO (§9.4: frente + verso) — os produtos do
            # "Quintou Verso Real.png"; 8 saem EXATOS do publicado e 8
            # são os REAIS MAIS PRÓXIMOS do acervo (buracos declarados:
            # sem foto de Pastilhas Dori, Frango Marombi, Sandella,
            # Paçoca Rolha, Pesto Mastroiani, Linguiça Perdigão,
            # Italac, Agnesi — nunca inventados)
            "vpos-01": ("Pé de Moleque Pinduca 150g", None, "8,88",
                        _foto("26/atual.png")),
            "vpos-02": ("Coxa Sobrecoxa 100g", None, "0,77",
                        _foto("21/atual.png")),
            "vpos-03": ("Granola Happy Life Banana e Canela 250g",
                        None, "9,90", _foto("24/atual.png")),
            "vpos-04": ("Goma Dori Minhocas Frutas Ácidas 100g", None,
                        "4,90", _foto("14/atual.png")),
            "vpos-05": ("Doce de Banana Val 250g", None, "6,66",
                        _foto("6/atual.png")),
            "vpos-06": ("Bife a Milanesa BBX 100g", None, "4,90",
                        _foto("13/atual.png")),
            "vpos-07": ("Macarrão Nissin Canja de Galinha 70g", None,
                        "2,66", _foto("19/atual.png")),
            "vpos-08": ("Kit NatuHair Shampoo & Cond. 300mL", None,
                        "19,90", _foto("31/atual.png")),
            "vpos-09": ("Salgadinho Ruppers Galinha 50g", None, "1,90",
                        _foto("2/atual.png")),
            "vpos-10": ("Geléia Ritter Alho Caram. 290g", None,
                        "18,81", _foto("17/atual.png")),
            "vpos-11": ("Queijo Mussarela Lactopar Quilo", None,
                        "55,05",
                        _foto("_auto/queijo_mussarela_latopar_1kg.png")),
            "vpos-12": ("Leite Parmalat Integral 1L", None, "5,95",
                        _foto("_auto/leite_parmalat_integral_1l.png")),
            "vpos-13": ("Sab. Líquido Dove Antib. 250mL", None,
                        "11,91", _foto("33/atual.png")),
            "vpos-14": ("Café Brasileiro Extra Forte 500g", None,
                        "23,99", _foto("12/atual.png")),
            "vpos-15": ("Batata Palha Bulnez Crocante 100g", None,
                        "6,66", _foto("_auto/batata_palha_bulnez_100g.png")),
            "vpos-16": ("Coco Ralado Adoçado Menina 100g", None, "2,92",
                        _foto("5/atual.png")),
        },
    },
    "segunda-frios": {
        "validade": "27/07",
        "itens": {
            # a FIXA com o conteúdo fixo do modelo; não há foto de
            # hambúrguer no acervo — vai a mussarela (declarado: o dono
            # cadastra a foto real do kit)
            "celula-1": ("Senepol BBX", "blend senepol · 4 un × 120 g",
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
        "etiquetas": {"celula-1": "CORTE DA SEMANA"},
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
        # D1: a edição REAL de agosto/2026 (a base do pacote era
        # Nº 177 · ANO 42 em julho — incrementa por mês)
        "edicao": "Nº 178 · ANO 42",
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
        # D2: o splash da capa é etiqueta OPCIONAL — aqui o dono
        # escolheria "SUPER OFERTA" para o hero do mês (verdade: é a
        # manchete do pacotão)
        "etiquetas": {"jp1-hero": "SUPER OFERTA"},
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
            # QUATER/J6: o "Sabão em Pó Maciez" saiu — a foto dele no
            # acervo é um CLIPART errado (balões de fala; o crawler
            # antigo baixou lixo — achado de curadoria, LEDGER). Entra
            # o Moça, com foto real conferida.
            "jp1-ch4": ("Leite Condensado Moça", "TP 395 g", "8,88",
                        _foto("38/atual.png")),
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
        # rótulos de destaque são etiquetas OPCIONAIS (D2) — aqui vão
        # as que são VERDADE para os produtos reais
        "validade": "30/07",
        "etiquetas": {"celula-1": "DESTAQUE DO DIA",
                      "celula-4": "CORTE NOBRE"},
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
        "etiquetas": {"celula-banca-1": "DESTAQUE DA SEMANA",
                      "celula-banca-2": "SELEÇÃO DA CASA"},
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


def _r_px(x, y, w, h):
    from app.rendering.encartes import DPI_VIEWBOX
    from app.rendering.model import Retangulo
    return Retangulo.de_px(x, y, w, h, DPI_VIEWBOX)


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
                nome, descritor=descr, unidade=descr,
                preco_por=preco_decimal(preco) if preco else None,
                preco_de=preco_decimal(preco_de) if preco_de else None,
                imagem_path=foto,
                mais18=sid in spec.get("mais18", ()),
                # D1: a edição VIVA (Nº/ANO) — canal de página; o layout
                # não tem mais o "Nº 177" cravado
                edicao=spec.get("edicao"))
        validade = spec["validade"]
        if n_pag == 2 and spec.get("validade_p2"):
            validade = spec["validade_p2"]
        dica = spec.get("dica_p2") if (n_pag == 2 and
                                       spec.get("dica_p2")) \
            else spec.get("dica")
        etiquetas = spec.get("etiquetas", {})
        for s in pag.slots:                 # validade da SEMANA + dica
            for r in s.regioes:
                if r.tipo != TipoRegiao.TEXTO_LEGAL:
                    continue
                if r.papel_texto == PapelTexto.VALIDADE:
                    r.texto_fixo = validade
                elif r.papel_texto == PapelTexto.DICA and dica:
                    r.texto_fixo = dica
                elif r.nome in ("Etiqueta", "Splash") and s.id in etiquetas:
                    # D2: a etiqueta é OPCIONAL e do dono — a inspeção
                    # põe a que é VERDADE para o produto da célula
                    r.texto_fixo = etiquetas[s.id]

        app_full = compor_pagina(lay, pag, dados)
        alt_1x = round(1080 * lay.altura_mm / lay.largura_mm)
        app_1x = app_full.resize((1080, alt_1x), Image.LANCZOS)
        if spec.get("preview"):
            prev = spec["preview"]
            if isinstance(prev, (list, tuple)):     # um por página (§9.4)
                prev = prev[n_pag - 1]
            preview = Image.open(pasta_pacote / prev)
        else:
            nome_prev = Path(pag.arquivo_fundo).name \
                .replace("-BASE-2160x2880.png", "-PREVIEW.png") \
                .replace("-BASE.png", "-PREVIEW.png")
            preview = Image.open(Path(pag.arquivo_fundo).parent
                                 / nome_prev)
        lado = Image.new("RGB", (1080 * 2 + 8, alt_1x), "#666666")
        lado.paste(app_1x.convert("RGB"), (0, 0))
        lado.paste(preview.convert("RGB").resize((1080, alt_1x)),
                   (1088, 0))
        GALERIA.mkdir(parents=True, exist_ok=True)
        sufixo = f"-p{n_pag}" if len(lay.paginas) > 1 else ""
        destino = GALERIA / f"{chave}{sufixo}.png"
        lado.save(destino)
        saidas.append(destino)
        # as DUAS opções do painel do Quintou (decisão do dono): a
        # variante A tira a logo e dá o painel INTEIRO ao Fica a Dica,
        # com corpo LEGÍVEL (Q5: meio a meio arruinava os dois — o
        # builder entrega a B fiel ao publicado; a A nasce aqui)
        if chave == "quintou" and n_pag == 1:
            from app.rendering.model import (
                Alinhamento,
                PapelTexto,
                Regiao,
                Slot as _Slot,
                TipoRegiao,
            )
            for s in pag.slots:
                if s.id == "painel-logo":
                    s.regioes[0].visivel = False
            pag.slots.append(_Slot("painel-dica-A", [
                Regiao(TipoRegiao.TEXTO_LEGAL, _r_px(612, 40, 432, 40),
                       nome="Título", fonte="Quicksand-Bold.ttf",
                       papel_texto=PapelTexto.LIVRE,
                       texto_fixo="FICA A DICA", tamanho_max_pt=17.0,
                       cor="#1B2A4A", alinhamento=Alinhamento.ESQUERDA),
                Regiao(TipoRegiao.TEXTO_LEGAL, _r_px(612, 88, 432, 140),
                       nome="Fica a Dica", fonte="Quicksand-Medium.ttf",
                       papel_texto=PapelTexto.DICA,
                       texto_fixo=spec.get("dica") or "",
                       tamanho_max_pt=12.5, cor="#33384A",
                       alinhamento=Alinhamento.ESQUERDA),
            ]))
            opcao_a = compor_pagina(lay, pag, dados) \
                .resize((1080, alt_1x), Image.LANCZOS)
            par = Image.new("RGB", (1080 * 2 + 8, alt_1x), "#666666")
            par.paste(app_1x.convert("RGB"), (0, 0))
            par.paste(opcao_a.convert("RGB"), (1088, 0))
            par.save(GALERIA / "quintou-opcoes-painel.png")
            print("[quintou] opções do painel: B (logo+dica, esq) × "
                  "A (só a dica, dir) → quintou-opcoes-painel.png")
        ocup = len(ocupaveis(pag.slots))
        print(f"[{chave}{sufixo}] {len(dados)} itens em {ocup} células "
              f"livres (+fixas) → {destino.name}")
    return saidas


# F13-TER/N2: o MESMO Jornal com o miolo em FLUXO por seções — os
# produtos REAIS da spec agrupados pela verdade de cada um. A ordem
# exercita as três leis do fluxo: o degrau de altura (não cabe tudo no
# 1º), a continuação de seção entre páginas e a seção de 1 item (Pet)
# com cabeçalho INLINE compartilhando a linha da seguinte.
SECOES_JORNAL = [
    ("Mercearia", ["jp1-l3", "jp1-l7", "jp1-l8", "jp1-l11", "jp2-l16",
                   "jp2-l19", "jp2-l14", "jp2-l5"]),
    ("Guloseimas & Biscoitos", ["jp1-l1", "jp1-l4", "jp1-l5", "jp1-l13",
                                "jp2-l1", "jp2-l10", "jp2-l17"]),
    ("Frios & Laticínios", ["jp2-l6", "jp2-l7", "jp2-l9", "jp2-l22"]),
    ("Pet", ["jp1-l14"]),
    ("Higiene & Perfumaria", ["jp2-l2", "jp2-l3", "jp2-l21", "jp1-l15"]),
    ("Bebidas", ["jp2-l4", "jp2-l8"]),
]


def _compor_jornal_secoes(pasta_pacote: Path) -> list[Path]:
    from PIL import Image

    from app.qt.telas.servico import preco_decimal
    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.model import PapelTexto, TipoRegiao

    spec = DADOS["jornal-do-mes"]
    lay = layout_de_encarte(
        "jornal-do-mes", pasta_pacote,
        secoes=[(t, len(ids)) for t, ids in SECOES_JORNAL])
    for a in lay.avisos_fluxo:
        print(f"[jornal-secoes] aviso do fluxo: {a}")

    dados = {}
    for sid in ("jp1-hero", "jp1-ch1", "jp1-ch2", "jp1-ch3", "jp1-ch4"):
        nome, descr, preco, foto = spec["itens"][sid][:4]
        dados[sid] = DadosProduto(
            nome, descritor=descr, unidade=descr,
            preco_por=preco_decimal(preco) if preco else None,
            imagem_path=foto, edicao=spec.get("edicao"))
    n = 0
    for titulo, ids in SECOES_JORNAL:
        for src in ids:
            n += 1
            nome, descr, preco, foto = spec["itens"][src][:4]
            dados[f"jf-{n:02d}"] = DadosProduto(
                nome, descritor=descr, unidade=descr,
                preco_por=preco_decimal(preco) if preco else None,
                imagem_path=foto, mais18=src in spec.get("mais18", ()),
                # A4: a CATEGORIA é a seção — o motor único de seções
                # (estilo JORNAL) agrupa e desenha o cabeçalho por ela
                categoria=titulo,
                edicao=spec.get("edicao"))

    saidas = []
    for n_pag, pag in enumerate(lay.paginas, start=1):
        validade = spec["validade"]
        if n_pag == 2 and spec.get("validade_p2"):
            validade = spec["validade_p2"]
        dica = spec.get("dica_p2") if (n_pag == 2 and
                                       spec.get("dica_p2")) \
            else spec.get("dica")
        etiquetas = spec.get("etiquetas", {})
        for s in pag.slots:
            for r in s.regioes:
                if r.tipo != TipoRegiao.TEXTO_LEGAL:
                    continue
                if r.papel_texto == PapelTexto.VALIDADE:
                    r.texto_fixo = validade
                elif r.papel_texto == PapelTexto.DICA and dica:
                    r.texto_fixo = dica
                elif r.nome in ("Etiqueta", "Splash") and s.id in etiquetas:
                    r.texto_fixo = etiquetas[s.id]
        img = compor_pagina(lay, pag, dados)
        alt_1x = round(1080 * lay.altura_mm / lay.largura_mm)
        destino = GALERIA / f"jornal-secoes-p{n_pag}.png"
        GALERIA.mkdir(parents=True, exist_ok=True)
        img.resize((1080, alt_1x), Image.LANCZOS).save(destino)
        saidas.append(destino)
        print(f"[jornal-secoes-p{n_pag}] → {destino.name}")
    return saidas


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    pacote = Path(sys.argv[1])
    chaves = sys.argv[2:] or list(DADOS)
    for c in chaves:
        if c == "jornal-secoes":
            _compor_jornal_secoes(pacote)
        else:
            _compor(c, pacote)
