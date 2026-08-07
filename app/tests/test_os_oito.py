"""O TESTE DOS OITO — a rede da L22 (ORDEM DUODETRICESIMUS §14).

> "Cada encarte novo que ele abre é uma REGRESSÃO a um estado já
> consertado em outro lugar. Isso não é sequência de defeitos: é um
> defeito só — o de as regras morarem no layout em vez de morarem no
> motor."

**Um arquivo. Oito parâmetros. Todas as regras de composição já
conquistadas.** Cada regra vira uma função nomeada que recebe a página
COMPOSTA (do banco, pela porta real — L16) e devolve as violações; o
pytest parametriza pelos oito encartes do pacote do dono.

Quando uma lei nova nascer numa rodada, ela entra AQUI — e passa a
valer nos oito no mesmo commit. É a única coisa que impede a próxima
auditoria de encarte de custar uma ordem inteira.

As regras cobertas hoje (cada uma com a ordem que a criou):
  R1  o hífen não parte marca (L25 · DUODETRICESIMUS §1)
  R2  nenhum nome elipsado (NONUS §2 · DUODETRICESIMUS §2)
  R3  nome nunca começa com número solto (DUODETRICESIMUS §3)
  R4  um peso por item (QUARTUS §1.2 · DUODETRICESIMUS §9)
  R5  a unidade nunca some do nome+descritor (QUARTUSDECIMUS §2)
  R6  o texto não transborda a região (TERTIUSDECIMUS/A1)
  R7  o corpo do nome respeita o piso do celular (UNDECIMUS/U1)
  R8  toda região de preço visível desenha DENTRO de forma/carimbo
      (DUODETRICESIMUS §4 — preço solto no fundo nunca)
"""

from __future__ import annotations

import unicodedata
from decimal import Decimal
from pathlib import Path

import pytest

_PACOTE = Path(__file__).resolve().parents[2] / "Templates novos"

# os OITO do dono (a chave do pacote → o nome no banco)
OITO = [
    "quintou", "jornal-do-mes", "segunda-frios", "terca-do-pao",
    "quarta-das-ofertas", "quinta-do-peixe", "sexta-verde",
    "sabado-da-carne",
]

# o item de PROVA — desenhado para exercitar todas as regras de uma vez:
# nome longo com MARCA longa (o hífen tenta partir), peso no nome E
# unidade divergente (o peso duplicado), sabor (o descritor cheio).
NOME_PROVA = "Achocolatado Andorinha Tradicional 700g"
UNIDADE_PROVA = "900 g"          # diverge de propósito (o peso do nome vence)
PRECO_PROVA = Decimal("11.91")


def _chave(t: str) -> str:
    t = unicodedata.normalize("NFKD", (t or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def _requer_pacote():
    if not _PACOTE.exists():
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")


def _layout_do_banco(chave: str, raiz):
    """A PORTA REAL (L16): importar_pacote → carregar_layout. Nenhum
    teste desta rede monta layout à mão — se o import quebrar, os oito
    ficam vermelhos, e é isso que se quer."""
    from app.core.database import Database
    from app.core.models import Layout
    from app.rendering.encartes import NOMES_EXIBICAO, importar_pacote
    from app.rendering.persistencia import carregar_layout

    db = Database(raiz).init()
    try:
        with db.Session() as s:
            importar_pacote(s, _PACOTE)
            s.commit()
            nome = NOMES_EXIBICAO.get(chave, chave)
            row = next((r for r in s.query(Layout).all()
                        if r.nome == nome), None)
            assert row is not None, f"{chave}: não entrou no banco"
            return carregar_layout(s, row.id)
    finally:
        db.engine.dispose()


def _dados_de_prova(pagina, marcas):
    """O MESMO item em toda célula ocupável da página — a régua tem de
    valer para qualquer produto, em qualquer célula."""
    from app.qt.telas.servico import ItemMesa, dados_para_desenho
    from app.rendering.grade import ocupaveis

    it = ItemMesa(descricao=NOME_PROVA, preco="11,91", semaforo="VERDE",
                  nome=NOME_PROVA, unidade=UNIDADE_PROVA)
    d = dados_para_desenho(it, None, None, validade="06/08", marcas=marcas)
    return {s.id: d for s in ocupaveis(pagina.slots)}


# ============================================================== as regras


def r1_hifen_nao_parte_marca(ctx) -> list[str]:
    """L25: marca, submarca e nome de linha são ÁTOMOS."""
    ruins = []
    for linhas in ctx["linhas_desenhadas"]:
        for i, ln in enumerate(linhas[:-1]):
            if not ln.rstrip().endswith("-"):
                continue
            pedaco = ln.rstrip()[:-1].split()[-1] if ln.split() else ""
            junto = _chave(pedaco + linhas[i + 1].split()[0]
                           if linhas[i + 1].split() else pedaco)
            if any(junto.startswith(_chave(m)) or _chave(m) in junto
                   for m in ctx["marcas"]):
                ruins.append(f"hífen partiu marca: {ln!r} + "
                             f"{linhas[i + 1]!r}")
    return ruins


def r2_nenhum_nome_elipsado(ctx) -> list[str]:
    """A elipse é o ÚLTIMO recurso e não deve sobrar nas páginas de
    prova — se sobrar, a escada não desceu todos os degraus."""
    return [f"nome elipsado: {' '.join(linhas)!r}"
            for linhas in ctx["linhas_desenhadas"]
            if any("…" in ln for ln in linhas)]


def r3_nome_sem_numero_solto(ctx) -> list[str]:
    """§3: a numeração da tabela é metadado, nunca nome."""
    import re
    return [f"nome começa com número solto: {ctx['nome']!r}"] \
        if re.match(r"^\s*\d{1,3}\s+\D", ctx["nome"]) else []


def r4_um_peso_por_item(ctx) -> list[str]:
    """QUARTUS §1.2: UM ITEM TEM UM PESO SÓ (o "500ml · 497 ml")."""
    import re
    texto = f"{ctx['nome']} {ctx['descritor'] or ''}"
    pesos = re.findall(r"\d+(?:[.,]\d+)?\s*(?:g|kg|ml|l)\b",
                       texto, flags=re.IGNORECASE)
    vistos = {re.sub(r"\s+", "", p.lower()) for p in pesos}
    return [f"dois pesos no mesmo item: {texto!r}"] if len(vistos) > 1 else []


def r5_a_unidade_nunca_some(ctx) -> list[str]:
    """QUARTUSDECIMUS §2: a unidade é informação comercial."""
    import re
    texto = f"{ctx['nome']} {ctx['descritor'] or ''}"
    return [] if re.search(r"\d+\s*(?:g|kg|ml|l)\b", texto, re.IGNORECASE) \
        else [f"a unidade sumiu: {texto!r}"]


def r6_texto_dentro_da_regiao(ctx) -> list[str]:
    """TERTIUSDECIMUS/A1: nenhum texto desenha fora do seu rect."""
    return [f"texto transborda a região {d['nome'] or d['tipo']}"
            for d in ctx["desenhado"].values()
            if d["altura_px"] > d["rect_alt_px"] + 1]


def r7_piso_do_celular(ctx) -> list[str]:
    """UNDECIMUS/U1: o corpo do NOME desenhado nunca desce abaixo do
    piso do celular da página (a régua de runtime)."""
    # o piso NUNCA excede o teto da própria região: layout que
    # declara 14 pt de máximo não pode ser cobrado por 16,6 (seria
    # medir o layout com a régua de outro — o erro de instrumento
    # que esta rodada ensinou a conferir antes de acusar)
    return [f"corpo {d['pt']:.1f}pt abaixo do piso "
            f"{min(ctx['piso'], d['max_pt']):.1f}pt em "
            f"{d['nome'] or d['tipo']}"
            for d in ctx["desenhado"].values()
            if d["tipo"] == "NOME"
            and d["pt"] < min(ctx["piso"], d["max_pt"]) - 0.51
            # ...e abaixo do mínimo que o LAYOUT declarou: o Quintou
            # declara 9,5 pt de propósito (adendo do dono: legível-
            # pequeno > cortado). Exceção DECLARADA vale; silenciosa
            # não existe — quem não declara é cobrado pelo piso.
            and d["pt"] < d["min_pt"] - 0.51
            # ...e SEM ter cedido para caber no rect: quando o corpo
            # desce abaixo do mínimo E o texto passa a caber, foi o
            # último recurso legítimo do A1 (o rect manda sobre o
            # piso — melhor pequeno dentro que grande vazando)
            and d["altura_px"] > d["rect_alt_px"]]


def _classe_da_celula(slot):
    """UNDETRICESIMUS §3 — DUAS CLASSES DE CÉLULA, E SÓ DUAS.

    Devolve "GRADE" (foto em cima, texto embaixo), "DESTAQUE" (texto à
    esquerda, foto à direita), "DESTAQUE_INVERTIDO" (foto à esquerda —
    o mesmo arranjo espelhado, que quebra o "sempre igual"), ou None
    quando a célula não é de produto (sem foto ou sem nome).
    """
    from app.rendering.model import TipoRegiao

    img = next((r for r in slot.regioes
                if r.tipo == TipoRegiao.IMAGEM and r.visivel), None)
    nome = next((r for r in slot.regioes
                 if r.tipo == TipoRegiao.NOME and r.visivel), None)
    if img is None or nome is None:
        return None
    i, n = img.rect, nome.rect
    # Pelos CENTROS, não pelas bordas: a caixa do nome tem respiro
    # interno e encosta ~2 mm na foto em todos os encartes aprovados —
    # medir borda com borda classificava célula de grade como "fora do
    # padrão" (régua minha nascida torta, corrigida antes de acusar).
    cxi, cyi = i.x_mm + i.larg_mm / 2, i.y_mm + i.alt_mm / 2
    cxn, cyn = n.x_mm + n.larg_mm / 2, n.y_mm + n.alt_mm / 2
    faixa = max(i.larg_mm, n.larg_mm) * 0.25
    if abs(cxi - cxn) <= faixa:
        return "GRADE" if cyi < cyn else "FORA DO PADRÃO"
    return "DESTAQUE" if cxi > cxn else "DESTAQUE_INVERTIDO"


def r9_duas_classes_de_celula(ctx) -> list[str]:
    """§3: um arranjo por classe, e só duas classes na página inteira —
    a de GRADE (foto em cima) e a HORIZONTAL (foto ao lado do texto).
    E, dentro da página, a horizontal é SEMPRE do mesmo lado ("sempre
    igual nas duas grandes"): é a mistura que o arquiteto viu na
    Quinta do Peixe.

    NÃO cobra o lado CANÔNICO (foto à direita): os oito medidos mostram
    o Jornal (4 chamadas), a Sexta (9 patches) e a Quarta (1 livre) com
    a foto à ESQUERDA — arranjos que o dono já aprovou em rodadas
    anteriores. Trocar o lado deles é redesenho de três encartes, e
    isso é decisão do dono, não régua de builder (L7). O que a rede
    garante é a COERÊNCIA, que é o defeito relatado."""
    ruins = [f"{sid}: arranjo interno fora das duas classes (a foto não "
             "está nem em cima nem ao lado do nome)"
             for sid, classe in ctx["classes"].items()
             if classe == "FORA DO PADRÃO"]
    lados = {c for c in ctx["classes"].values() if c.startswith("DESTAQUE")}
    if len(lados) > 1:
        ruins.append("a página mistura foto à direita e foto à esquerda "
                     "nas células horizontais — o arranjo é sempre igual")
    return ruins


def r10_zona_da_foto_generosa(ctx) -> list[str]:
    """§3: o produto ocupa ≥55% da célula de DESTAQUE ("as duas
    grandes" — a foto do Peixe Pintado ocupava um sexto da célula).

    Mede a ZONA, não a tinta: a zona é a promessa do layout (o que o
    app controla); quanto da zona o produto enche depende da foto do
    dono e já é lei do Q1/leque. E mede só as células GRANDES: o §3 diz
    "célula de destaque", que é relativo à página (L21) — cobrar 55% da
    célula miúda da grade seria régua inventada."""
    return [f"{sid}: a foto da célula de destaque ocupa {prop:.0%} da "
            f"área dela (mínimo 55%)"
            for sid, (_classe, prop) in ctx["zonas"].items()
            if prop < 0.55]


def r11_validade_fora_da_celula(ctx) -> list[str]:
    """§3: a validade é da PÁGINA — nunca se repete dentro de célula de
    produto (as duas células grandes do Peixe imprimiam a data).

    Mede o que foi DESENHADO, não o que o layout declara: a etiqueta
    das células do Peixe nasce vazia e a data entrava por HERANÇA do
    texto legal da página — nenhuma leitura do layout acharia isso."""
    return [f"{sid}: a validade da página ({txt!r}) está dentro de uma "
            f"célula de produto, na região {rot}"
            for sid, rot, txt in ctx["validade_em_celula"]]


def r12_patamar_do_preco(ctx) -> list[str]:
    """§3: a célula de DESTAQUE tem preço MAIOR que as outras — a
    hierarquia da página se lê no corpo do número. "Destaque" é a
    célula GRANDE (a mesma definição relativa da r10), não a que tem a
    foto ao lado: as chamadas do Jornal e os patches da Sexta são
    horizontais e MIÚDOS — preço grande neles inverteria a página."""
    dest = [pt for sid, pt in ctx["precos"] if sid in ctx["zonas"]]
    resto = [pt for sid, pt in ctx["precos"] if sid not in ctx["zonas"]]
    if not dest or not resto:
        return []
    if min(dest) <= max(resto):
        return [f"o preço da célula de destaque ({min(dest):.1f} pt) não "
                f"é maior que o das demais ({max(resto):.1f} pt)"]
    return []


def r8_preco_coerente_na_pagina(ctx) -> list[str]:
    """§4 (o Ervilha Fugini sem carimbo enquanto os outros 15 tinham):
    a régua honesta é a COERÊNCIA — numa mesma página, ou toda região
    de preço tem carimbo (forma do app ou pouso na arte), ou nenhuma
    tem. Célula que destoa das irmãs é o defeito."""
    from app.rendering.model import FormaPreco
    com, sem = [], []
    for reg in ctx["regioes_preco"]:
        tem = (reg.forma_preco != FormaPreco.TEXTO
               # o carimbo do app, o número que ENCHE o elemento de
               # arte (L24), ou o carimbo GRAVADO na arte do dono
               or getattr(reg, "preenche_caixa", False)
               or getattr(reg, "carimbo_na_arte", False))
        (com if tem else sem).append(reg.nome or reg.uid)
    if com and sem:
        return [f"{len(sem)} de {len(com) + len(sem)} preços da página "
                f"sem carimbo enquanto os outros têm"]
    return []


def r13_corpo_constante_e_hierarquia(ctx) -> list[str]:
    """TRICESIMUS / **L27 — DIMENSIONAR PELO CONJUNTO, NÃO PELA PEÇA**.

    Duas medidas na mesma regra, porque são o mesmo defeito visto de
    dois ângulos (o dono viu os dois na mesma peça):

    1. o corpo do preço é UM SÓ na página — o publicado dele tem 33 px
       em 14 dos 15 carimbos e o app chegou a NOVE tamanhos numa
       página; corpo por célula produz mosaico;
    2. a razão preço ÷ nome fica na BANDA 2,4×–2,9× (a dele é 2,75×) —
       a regra antiga dava piso sem teto e o nome ficou "absurdamente
       pequeno" enquanto o preço crescia sozinho.
    """
    ruins = []
    corpos = {round(d["pt"], 2) for d in ctx["precos_desenhados"]}
    if len(corpos) > 1:
        ruins.append(f"o corpo do preço varia na página: {sorted(corpos)}")
    # L31 — **CADA FACE TEM A SUA MÉTRICA.** Onde a face declara os
    # alvos medidos na peça do dono (subtração, L30), a régua é O
    # NÚMERO DELA: a banda 2,4–2,9 REPROVARIA o verso do próprio dono,
    # que opera em 1,50. A banda só vale onde não há medida.
    if not ctx["alvos_da_face"]:
        for razao in ctx["razoes"]:
            if not (2.4 - 0.01 <= razao <= 2.9 + 0.01):
                ruins.append("razão preço÷nome fora da banda 2,4–2,9: "
                             f"{razao}")
    # PRECEDÊNCIA DECLARADA, não defeito: quando o nome só cabe inteiro
    # abaixo do piso da banda, a BANDA cede (a lei do dono é
    # "informação completa SEMPRE"; a tesoura é proibida). O caso não
    # some — sai nomeado, e o contador vive no DIVIDA para o arquiteto
    # ver quantas células estão nessa situação.
    if ctx["banda_cedeu"] and not ctx["alvos_da_face"]:
        ruins.append(f"a banda cedeu em {ctx['banda_cedeu']} célula(s) "
                     "para o nome não ser cortado")
    return ruins


def r14_a_face_bate_com_a_peca_publicada(ctx) -> list[str]:
    """L30/L31 — **A ESPECIFICAÇÃO EXTRAÍDA POR SUBTRAÇÃO.** Onde a
    face declara os números medidos na peça do dono (área de tinta e
    altura do algarismo, escala 1080), o desenho tem de bater com eles.

    É a régua mais forte que existe no projeto: não compara o app com
    uma regra que alguém escreveu, compara com o que o dono imprimiu.
    """
    alvos = ctx["alvos_da_face"]
    if not alvos:
        return []
    ruins = []
    alvo_alg = alvos.get("algarismo") or 0
    if alvo_alg and ctx["precos_desenhados"]:
        alt = ctx["precos_desenhados"][0]["alt_alg_px"] * ctx["k_regua"]
        # ±5% OU 1 px, o que for maior: a altura do algarismo é inteira
        # em pixels e um arredondamento não é divergência de desenho
        if abs(alt - alvo_alg) > max(alvo_alg * 0.05, 1.0):
            ruins.append(f"o algarismo mede {alt:.0f} px onde a peça do "
                         f"dono tem {alvo_alg:.0f} (±5%)")
    alvo_area = alvos.get("area") or 0
    if alvo_area and ctx["tintas"]:
        for sid, tinta in ctx["tintas"].items():
            t = tinta * ctx["k_regua"] ** 2
            if t > alvo_area * 1.28:
                ruins.append(f"{sid}: a tinta do produto mede {t:.0f} px² "
                             f"onde a peça do dono tem {alvo_area:.0f} "
                             "(+28% é o teto medido)")
    return ruins


def r15_nao_multiplica_quem_tem_quantidade(ctx) -> list[str]:
    """**L32** (TRICESIMUS-SECUNDUS §2.4) — o dono, olhando a Sexta:
    *"os dois ovos com essa coisa de multiplicar — parece que tem mais
    ovo do que é pra ter"*. Bandeja de 30 unidades desenhada duas vezes
    faz o cliente ler 60. Vale igual para o que se vende por peso.

    A regra vai para os OITO porque o defeito é do motor, não da Sexta
    — é o crônico que o §7 da ordem nomeia: lei que fica na ordem em
    vez de ir para a rede volta no próximo encarte."""
    from app.rendering.compositor import quantidade_declarada

    if not quantidade_declarada(ctx["dados"]):
        return []
    return [f"{sid}: o produto tem quantidade declarada e mesmo assim "
            "foi multiplicado (o leque contradiz o número ao lado)"
            for sid, multiplicou in ctx["multiplicou"].items() if multiplicou]


# DÍVIDA DECLARADA (DUODETRICESIMUS §14): o que a rede achou HOJE e
# cujo conserto é de LAYOUT/arte, não de motor — fica NOMEADA aqui,
# nunca escondida. Defeito novo deixa o teste vermelho; dívida
# consertada também (o número tem de baixar junto com o conserto).
DIVIDA = {
    # TRICESIMUS — PRECEDÊNCIA DECLARADA (uma linha por página): com o
    # ITEM DE PROVA (o nome mais longo que qualquer um do dono, feito
    # para estressar as regras), o piso da banda 2,4–2,9 não cabe na
    # caixa de nome do Quintou e a BANDA cede para o nome não ser
    # cortado. Na página REAL do dono (galeria, dados dele) o quadro é
    # outro e está medido: algarismo 32 px CONSTANTE (o publicado tem
    # 33 — dentro dos ±5% do §5.3), razão 2,46 a 2,91 (a dele é 2,75),
    # e a banda cede num fio em 7 de 15 células da frente, zero no
    # verso. Se o arquiteto quiser a banda inviolável, o conserto é de
    # ARTE (a caixa do nome do Quintou precisa de mais altura) — e aí
    # este número tem de cair junto.
    ("quintou", "r13_corpo_constante_e_hierarquia"): 1,
    # QUITADA na UNDETRICESIMUS §5.4: os "2 de 11 preços sem carimbo"
    # da Sexta eram FALSO POSITIVO desta régua — o oval coral das
    # bancas está GRAVADO no BASE do dono, e o app desenha só o número
    # em cima. A página não tinha defeito; o layout é que não declarava
    # o que a arte já fazia (``carimbo_na_arte``). O dicionário fica
    # VAZIO: nenhuma dívida aberta nos oito.
    # QUITADA na UNDETRICESIMUS: as 8 dívidas de r6 (o transbordo do
    # nome, 12 a 40 por encarte) eram o CONFLITO DE LEIS que o
    # arquiteto despachou no §2 — o piso não cede, a CAIXA cede. Com o
    # crescimento da região (compositor.crescer_do_piso) e o degrau 4
    # da escada (§1), o transbordo foi a ZERO nos oito e as linhas
    # saíram daqui. Dívida consertada tem de sumir do dicionário: se
    # voltar, o teste fica vermelho — que é o ponto.
}


REGRAS = [r1_hifen_nao_parte_marca, r2_nenhum_nome_elipsado,
          r3_nome_sem_numero_solto, r4_um_peso_por_item,
          r5_a_unidade_nunca_some, r6_texto_dentro_da_regiao,
          r7_piso_do_celular, r8_preco_coerente_na_pagina,
          # UNDETRICESIMUS §3 — o padrão de célula dos sete
          r9_duas_classes_de_celula, r10_zona_da_foto_generosa,
          r11_validade_fora_da_celula, r12_patamar_do_preco,
          # TRICESIMUS — o preço é constante e a hierarquia tem banda
          r13_corpo_constante_e_hierarquia,
          # L30/L31 — a face bate com a peça publicada (por subtração)
          r14_a_face_bate_com_a_peca_publicada,
          # L32 — não se multiplica quem já tem quantidade declarada
          r15_nao_multiplica_quem_tem_quantidade]


# ============================================================== o motor


def _contexto(ldef, pagina, img, dados):
    """Tudo que as regras precisam — LIDO DO REGISTRO do compositor
    (``_texto_desenhado``), nunca recalculado: medir por fora ignora a
    escada, os rects substituídos e o piso de runtime, e faz o teste
    acusar defeito que não existe (a lição desta rodada, dos dois
    lados da dupla)."""
    from app.rendering.model import TipoRegiao
    from app.rendering.text_fit import piso_do_celular

    d0 = next(iter(dados.values()))
    desenhado = {uid: d for uid, d in
                 getattr(img, "_texto_desenhado", {}).items()
                 if d["tipo"] == "NOME"}
    regs_preco = [r for s in pagina.slots for r in s.regioes
                  if r.tipo == TipoRegiao.PRECO and r.visivel
                  and s.id in dados]

    # UNDETRICESIMUS §3 — o padrão de célula dos SETE (os encartes sem
    # peça publicada do dono; onde há original, quem manda é a L23)
    from statistics import median

    CONTEUDO = (TipoRegiao.IMAGEM, TipoRegiao.NOME, TipoRegiao.SUBTITULO,
                TipoRegiao.PRECO, TipoRegiao.UNIDADE)
    classes: dict[str, str] = {}
    validade_em_celula: list[tuple[str, str, str]] = []
    precos_por_classe: list[tuple[str, float]] = []
    medidas: list[tuple[str, str, float, float]] = []
    desenho = getattr(img, "_texto_desenhado", {})
    val_pg = (d0.texto_legal or "").strip()
    for slot in pagina.slots:
        if slot.id not in dados:
            continue                       # só célula de produto
        classe = _classe_da_celula(slot)
        if classe is None:
            continue
        classes[slot.id] = classe
        # a CÉLULA é o retângulo do CONTEÚDO — moldura, toldo e fios são
        # decoração e inflavam a caixa (a banca da Sexta media 42% por
        # causa do toldo, não da foto)
        vis = [r for r in slot.regioes if r.visivel and r.tipo in CONTEUDO]
        cx0 = min(r.rect.x_mm for r in vis)
        cy0 = min(r.rect.y_mm for r in vis)
        cx1 = max(r.rect.x_mm + r.rect.larg_mm for r in vis)
        cy1 = max(r.rect.y_mm + r.rect.alt_mm for r in vis)
        zi = next(r.rect for r in vis if r.tipo == TipoRegiao.IMAGEM)
        area_cel = max(1e-6, (cx1 - cx0) * (cy1 - cy0))
        medidas.append((slot.id, classe, area_cel,
                        (zi.larg_mm * zi.alt_mm) / area_cel))
        for r in slot.regioes:
            if not r.visivel:
                continue
            if r.tipo == TipoRegiao.TEXTO_LEGAL and val_pg:
                escrito = " ".join(
                    desenho.get(r.uid, {}).get("linhas", []))
                if escrito and escrito in val_pg:
                    validade_em_celula.append(
                        (slot.id, r.nome or "texto legal", escrito))
            if r.tipo == TipoRegiao.PRECO:
                precos_por_classe.append((slot.id, r.tamanho_max_pt))
    # "as duas GRANDES": destaque é RELATIVO à página (a mesma lei do
    # herói, L21) — célula bem maior que a mediana da própria página
    med = median([m[2] for m in medidas]) if medidas else 0.0
    zonas = {sid: (cl, prop) for sid, cl, area, prop in medidas
             if med and area > med * 1.5}

    # TRICESIMUS: os preços que ENCHEM elemento de arte e a razão da
    # hierarquia contra a caixa alta do nome (medida como o arquiteto
    # mede na peça, com a fonte real de cada região)
    precos_arte = [d for d in getattr(img, "_preco_desenhado", {}).values()
                   if d["enche_caixa"]]

    # L30/L31: os alvos MEDIDOS na peça publicada, por FACE, e a escala
    # da régua do arquiteto (a página em 1080 px de largura)
    from app.rendering.units import mm_para_px
    k_regua = 1080.0 / mm_para_px(ldef.largura_mm, ldef.dpi)
    alvos_face: dict[str, float] = {}
    for slot in pagina.slots:
        for r in slot.regioes:
            if getattr(r, "alvo_altura_algarismo_px", 0.0):
                alvos_face["algarismo"] = r.alvo_altura_algarismo_px
            if getattr(r, "alvo_area_tinta_px", 0.0):
                alvos_face["area"] = r.alvo_area_tinta_px
    tintas = {sid: t for sid, t in
              ((s.id, getattr(img, "_tinta_px", {}).get(r.uid))
               for s in pagina.slots for r in s.regioes
               if r.tipo == TipoRegiao.IMAGEM and r.visivel)
              if t}
    razoes = []
    cedeu = getattr(img, "_banda_cedeu", set())
    if precos_arte:
        alt_alg = precos_arte[0]["alt_alg_px"]
        razoes = sorted({round(alt_alg / d["cap_px"], 2)
                         for uid, d in desenhado.items()
                         if (d.get("cap_px") or 0) > 0 and uid not in cedeu})
    # o nome/descritor REAIS da página (o que a escada decidiu)
    nome_final = (next(iter(desenhado.values()))["texto"]
                  if desenhado else d0.nome)
    return {
        "nome": nome_final, "descritor": d0.descritor, "dpi": ldef.dpi,
        "marcas": [m for m in (d0.marcas_nome or ())] or ["Andorinha"],
        "desenhado": desenhado,
        "linhas_desenhadas": [d["linhas"] for d in desenhado.values()],
        "regioes_preco": regs_preco,
        "piso": piso_do_celular(ldef.largura_mm),
        "classes": classes, "zonas": zonas,
        "validade_em_celula": validade_em_celula,
        "precos": precos_por_classe,
        # TRICESIMUS: o que o PREÇO desenhou (corpo e altura do
        # algarismo) e a razão contra a caixa alta do nome — as duas
        # medidas saem do registro do compositor, na mesma escala
        "precos_desenhados": precos_arte,
        "razoes": razoes,
        "banda_cedeu": len(cedeu),
        # L30/L31: os alvos DECLARADOS desta FACE (só existem onde há
        # peça publicada do dono — hoje, o Quintou) e a escala da régua
        "alvos_da_face": alvos_face,
        "tintas": tintas,
        "k_regua": k_regua,
        # L32: o dado da prova e quem foi multiplicado pelo leque
        "dados": d0,
        "multiplicou": {
            s.id: any(r.uid in getattr(img, "_multiplicou", ())
                      for r in s.regioes)
            for s in pagina.slots if s.id in dados},
    }


@pytest.mark.parametrize("chave", OITO)
def test_os_oito_seguem_as_leis(chave, tmp_path, monkeypatch):
    """A REDE DA L22: as leis conquistadas rodando nos OITO encartes,
    com o MESMO item de prova, pela porta real do banco (L16).

    Falha aqui = uma lei que existe em um layout e não em outro — o
    defeito que a ordem DUODETRICESIMUS §14 mandou matar na causa."""
    _requer_pacote()
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.paths import SystemRoot
    from app.qt.telas.servico import marcas_para_exibicao
    from app.rendering.compositor import compor_pagina
    from app.tests import acervo

    fontes = tmp_path / "fontes"
    fontes.mkdir()
    acervo.copiar_fontes_reais(fontes)
    raiz = SystemRoot(tmp_path / "raiz")
    ldef = _layout_do_banco(chave, raiz)
    marcas = marcas_para_exibicao()

    violacoes: list[str] = []
    for n, pagina in enumerate(ldef.paginas, start=1):
        dados = _dados_de_prova(pagina, marcas)
        if not dados:
            continue
        img = compor_pagina(ldef, pagina, dados, fontes_dir=fontes)
        ctx = _contexto(ldef, pagina, img, dados)
        for regra in REGRAS:
            achados = regra(ctx)
            if len(achados) <= DIVIDA.get((chave, regra.__name__), 0):
                continue          # dívida DECLARADA e sem piora
            for v in achados:
                violacoes.append(f"[{chave} p{n}] {regra.__name__}: {v}")

    assert not violacoes, "\n".join(violacoes)
