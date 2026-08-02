"""
A precedência do nome — ORDEM F13-NONUS §2 (código, não procedimento)
=====================================================================
O "…" está PROIBIDO em nome de produto. Antes de qualquer elipse, a
cadeia da OCTAVUS roda em RUNTIME, para todo nome, nesta ordem:

1. o nome cabe no corpo mínimo (1 linha)?    → usa
2. cabe em 2+ linhas no corpo mínimo?        → usa (mesma medida)
3. a banda pode crescer (orçamento O1)?      → cresce, a FOTO cede
4. descritor SEM unidade sai (banda inteira); COM unidade fica —
   a UNIDADE nunca é sacrificável (QUARTUSDECIMUS §2)
5. o nome ENCURTA pelo descritor             → o excedente desce inteiro
6. só então elipsa — e a revisora/pré-voo acusa (``elipsa=True``)

QUARTUSDECIMUS §2: o descritor tem DUAS metades — o QUALIFICADOR
("BB-X", "tinto", "extra virgem") pode sair; a UNIDADE ("100 g", "kg",
"1,5 L") é informação comercial: "Salsicha — R$ 9,90" sem o kg, ao
lado de vizinhos "100 g", lê DEZ vezes mais caro. Caso-limite escrito
junto com a regra (a lição do §6): item vendido a quilo cercado de
itens por 100 g; e o SUBTITULO estreito que elipsava o número
("BB-X · 10…") — o desenho corta o qualificador, nunca a unidade.

O encurtamento do passo 5 é MECÂNICO, nunca heurístico: como a ordem
travada do nome é Tipo+Marca+Sabor+Peso, o fim do nome é o que pode
descer — o peso primeiro (``separar_peso`` do sanitize, L9), depois os
tokens do fim, um a um, SEMPRE inteiros e SEMPRE preservados no
descritor (nada se perde — I2). A sigla de embalagem (TP, BB…) DESCE
junto — a tabela da NONUS §2 a descartava e o DONO corrigiu (27/07):
"não se pode omitir o tipo de embalagem"; vale a anotação original da
SEPTIMUS §3 ("tinto TP · 1,5 L"). Sem região SUBTITULO na célula não
há passos 4/5 — mover excedente para lugar nenhum seria perda
silenciosa.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from pathlib import Path

from app.core.sanitize import REGRAS_PADRAO, _canonizar_unidade, separar_peso
from app.rendering.model import Regiao, Retangulo, TipoRegiao
from app.rendering.text_fit import ajustar_texto
from app.rendering.units import mm_para_px, px_para_mm

# o passo 3 respeita o orçamento O1 (SEPTIMUS §O1, teto OCTAVUS §3):
# a foto nunca desce de 55% da altura útil da célula
_FRACAO_MIN_FOTO = 0.55


@dataclass
class NomeAjustado:
    """O veredito da cadeia para UMA célula."""

    nome: str
    descritor: str | None
    # uid da região → rect substituto (o passo 3 cresceu a banda e/ou o
    # passo 4 deu a banda inteira ao nome) — só para ESTA composição; o
    # modelo nunca muda (I1)
    rects: dict[str, Retangulo] = field(default_factory=dict)
    descritor_saiu: bool = False        # passo 4 venceu: o SUBTITULO cala
    elipsa: bool = False                # passo 6: nem a cadeia salvou
    # QUINTOU (adendo do dono): sem SUBTITULO o piso do celular CEDE
    # antes da tesoura — legível-pequeno > cortado; a revisora avisa
    piso_cedeu: bool = False


def _norm(s: str) -> str:
    return (s or "").lower().replace(" ", "").replace(",", ".")


def _juntar_descritor(partes: list[str], existente: str | None) -> str | None:
    """Monta o descritor final: excedente do nome (na ordem do nome) +
    o descritor que o item já tinha — sem duplicar conteúdo."""
    saida: list[str] = []
    for p in partes + ([existente] if existente else []):
        p = (p or "").strip(" ·")
        if p and _norm(p) not in _norm(" ".join(saida)):
            saida.append(p)
    return " · ".join(saida) or None


# uma PARTE do descritor é unidade quando é peso/volume ("100 g",
# "1,5 L", "4x120 g", "395g") ou unidade solta de venda a peso ("kg").
# Rodada JM (B1.1/B1.2): a coluna Unidade da planilha é texto LIVRE —
# a forma CRUA da tabela ("2 Kgs", "1 LT") e a metragem/contagem
# ("30 m", "12 rolos") são unidade também: metade PROTEGIDA, nunca
# qualificador sacrificável (QUARTUSDECIMUS §2 vale em toda grafia).
_RE_PARTE_UNIDADE = re.compile(
    r"^(?:\d+\s*x\s*)?\d+(?:[.,]\d+)?\s*"
    r"(?:kgs?|kilos?|quilos?|grs?|g|mgs?|mls?|lts?|litros?|l|un"
    r"|rolos?|folhas?|mts?|metros?|m)\.?$"
    r"|^(?:kgs?|grs?|g|mls?|mgs?|lts?|un|l|m)\.?$", re.IGNORECASE)

# T4 (DUODECIMUS) + Rodada JM: unidade SOLTA no fim do nome ("…Rezende
# KG", vendido a peso sem número) desce ao descritor — nas grafias
# canônicas E cruas. Constante de módulo: a régua é uma só e testável.
UNIDADES_SOLTAS = frozenset(
    {"kg", "g", "ml", "mg", "un", "l",
     "kgs", "lts", "grs", "lt", "gr", "m"})


def dividir_descritor(descritor: str | None,
                      unidade: str | None = None,
                      ) -> tuple[str | None, str | None]:
    """QUARTUSDECIMUS §2 — as duas metades do descritor: devolve
    ``(qualificador, protegido)``. O qualificador é sacrificável; o
    protegido NUNCA sai por falta de espaço e inclui a UNIDADE (peso/
    volume — informação comercial) **e as SIGLAS DE EMBALAGEM
    conhecidas** (TP, L.V., BB…): a palavra do dono (adendo NONUS,
    27/07 — "não se pode omitir o tipo de embalagem") vale também no
    desenho, não só na precedência (achado da frota QUARTUSDECIMUS).
    A ``unidade`` do dado decide o empate quando uma parte não parece
    peso (ex.: "un" declarada pelo cadastro)."""
    if not descritor:
        return None, None
    quals: list[str] = []
    prot: list[str] = []
    for parte in descritor.split(" · "):
        p = parte.strip()
        if not p:
            continue
        if bool(_RE_PARTE_UNIDADE.match(p)) or (
                unidade is not None and _norm(p) == _norm(unidade)):
            prot.append(p)
            continue
        # o SUFIXO de siglas de embalagem da parte é protegido
        # ("tinto TP" → qualificador "tinto", protegido "TP")
        tks = p.split()
        sig: list[str] = []
        while tks and tks[-1].upper() in REGRAS_PADRAO.siglas:
            sig.insert(0, tks.pop())
        if tks:
            quals.append(" ".join(tks))
        if sig:
            prot.append(" ".join(sig))
    return (" · ".join(quals) or None), (" · ".join(prot) or None)


def descritor_que_cabe(descritor: str | None, unidade: str | None,
                       reg: Regiao, dpi: int,
                       fontes_dir: str | Path) -> str | None:
    """O texto que o SUBTITULO desenha: o descritor completo se couber
    sem elipse; senão o QUALIFICADOR sai e a unidade fica — reticências
    em cima do número ("BB-X · 10…") é preço errado na vitrine. Se nem
    a unidade sozinha cabe, ela vai mesmo assim (região pequena demais
    é caso de calibração; elipsar a unidade seria pior)."""
    texto = descritor or unidade
    if not texto:
        return None
    fontes_dir = Path(fontes_dir)
    if _cabe(texto, reg, reg.rect, dpi, fontes_dir):
        return texto
    _qual, unidade_txt = dividir_descritor(texto, unidade)
    return unidade_txt or texto


def _cabe(texto: str, reg: Regiao, rect: Retangulo, dpi: int,
          fontes_dir: Path) -> bool:
    """O texto cabe SEM elipse no corpo mínimo da região? (passos 1-2:
    1 ou N linhas é a mesma medida — quem manda é a altura da caixa)."""
    if not texto:
        return True
    aj = ajustar_texto(
        texto, fontes_dir / reg.fonte,
        mm_para_px(rect.larg_mm, dpi), mm_para_px(rect.alt_mm, dpi),
        reg.tamanho_max_pt, dpi, reg.tamanho_min_pt,
        sem_hifen=reg.sem_hifen,
    )
    return not any("…" in ln for ln in aj.linhas)


def _crescer_banda(reg_nome: Regiao, reg_img: Regiao,
                   regioes: list[Regiao], dpi: int,
                   fontes_dir: Path,
                   texto: str) -> tuple[Retangulo, Retangulo] | None:
    """Passo 3: quanto a banda do nome PRECISA crescer para o texto
    caber, com a foto cedendo — sem furar o piso de 55% do O1. Só
    quando a foto está ACIMA da banda (o desenho das células do
    pacote); devolve (rect_nome, rect_foto) ou None se não há folga.

    ADENDO QUARTUSDECIMUS (achado do OLHAR): a régua é o PRÓPRIO
    ``_cabe`` — a estimativa antiga por métrica de fonte SUBESTIMAVA a
    altura de 2 linhas (o ajustar_texto tem entrelinha própria) e a
    banda crescia de menos: "Mini Salgadinhos" caía na escada mesmo
    com folga sobrando. Bisseção até o MENOR delta que faz caber (a
    foto nunca cede mais do que o texto precisa)."""
    rn, ri = reg_nome.rect, reg_img.rect
    if ri.y_mm + ri.alt_mm > rn.y_mm + 0.5:      # foto não está acima
        return None
    # TERTIUSDECIMUS/A1: a banda só cresce COLADA na foto — crescer
    # através de um vão de ARTE (o painel das cestas da Terça) pinta
    # texto sobre o desenho; com vão, a precedência segue ao passo 4/5
    if rn.y_mm - (ri.y_mm + ri.alt_mm) > 2.5:    # ~9 px de folga na régua
        return None
    y0 = min(r.rect.y_mm for r in regioes if r.visivel)
    y1 = max(r.rect.y_mm + r.rect.alt_mm for r in regioes if r.visivel)
    folga_mm = ri.alt_mm - _FRACAO_MIN_FOTO * (y1 - y0)
    if folga_mm <= 0.1:
        return None

    def _rects(delta: float) -> tuple[Retangulo, Retangulo]:
        return (
            Retangulo(rn.x_mm, rn.y_mm - delta, rn.larg_mm,
                      rn.alt_mm + delta),
            Retangulo(ri.x_mm, ri.y_mm, ri.larg_mm, ri.alt_mm - delta),
        )

    if not _cabe(texto, reg_nome, _rects(folga_mm)[0], dpi, fontes_dir):
        return None                     # nem com a folga toda cabe
    lo, hi = 0.0, folga_mm
    for _ in range(5):
        mid = (lo + hi) / 2.0
        if _cabe(texto, reg_nome, _rects(mid)[0], dpi, fontes_dir):
            hi = mid
        else:
            lo = mid
    return _rects(hi)


# K3 (QUINTUSDECIMUS): pares do mercado que NUNCA se separam — o mesmo
# critério conservador do vocabulário da ortografia: só entra o
# inequívoco no domínio; na dúvida, fica de fora.
_PARES_DO_MERCADO = {("extra", "virgem"), ("mon", "bijou")}


def _corte_parte_marca(ultimo: str, descido: str) -> bool:
    """O corte deixaria uma marca partida ao meio? Órfão CURTO no fim do
    nome (<4 letras não-sigla — o "Mon" de Mon Bijou) ou par consagrado
    partido ("Extra | Virgem"): o par desce junto ao descritor."""
    if (ultimo.lower(), descido.lower()) in _PARES_DO_MERCADO:
        return True
    return (len(ultimo) < 4 and ultimo.isalpha()
            and ultimo.upper() not in REGRAS_PADRAO.siglas)


def precedencia_do_nome(
    nome: str,
    descritor: str | None,
    unidade: str | None,
    regioes: list[Regiao],
    dpi: int,
    fontes_dir: str | Path,
    piso_pt: float | None = None,
) -> NomeAjustado | None:
    """A cadeia dos 6 passos para UMA célula. Devolve None quando não há
    o que decidir (sem região NOME visível, ou nome vazio) — o
    compositor segue byte-idêntico ao de sempre.

    F13-UNDECIMUS/U1: ``piso_pt`` é a RÉGUA de runtime (o piso do
    celular calculado da página); o ``tamanho_min_pt`` da região só
    manda quando é MAIOR que ela (override para cima) — o 6.0 inerte
    do banco velho deixa de ser consultado."""
    if not nome:
        return None
    fontes_dir = Path(fontes_dir)
    reg_nome = next((r for r in regioes
                     if r.tipo == TipoRegiao.NOME and r.visivel), None)
    if reg_nome is None:
        return None
    reg_nome_cru = reg_nome
    if piso_pt:
        min_ef = min(reg_nome.tamanho_max_pt,
                     max(reg_nome.tamanho_min_pt, piso_pt))
        if min_ef != reg_nome.tamanho_min_pt:
            reg_nome = replace(reg_nome, tamanho_min_pt=min_ef)
    reg_sub = next((r for r in regioes
                    if r.tipo == TipoRegiao.SUBTITULO and r.visivel), None)
    reg_img = next((r for r in regioes
                    if r.tipo == TipoRegiao.IMAGEM and r.visivel), None)

    # QUARTUSDECIMUS (frota): a unidade do DADO entra SEMPRE no
    # descritor de trabalho (dedupe cuida da repetição) — descritor
    # qualificador-puro com unidade só no campo não engana mais o
    # passo 4 nem o desenho
    descritor0 = _juntar_descritor([descritor] if descritor else [],
                                   unidade)
    if reg_sub is None:
        # sem descritor na célula não há para onde mover (I2): a cadeia
        # é só o aviso de elipse (o Quintou/Jornal-fluxo caem aqui)
        if _cabe(nome, reg_nome, reg_nome.rect, dpi, fontes_dir):
            return None
        # ADENDO do dono (Quintou, 30/07): "não reduziu o tamanho dos
        # textos maiores" — sem SUBTITULO não há como encurtar; antes
        # da tesoura o PISO CEDE até o mínimo original da região (o
        # publicado reduz o corpo dos nomes longos, nunca corta)
        if reg_nome_cru.tamanho_min_pt < reg_nome.tamanho_min_pt \
                and _cabe(nome, reg_nome_cru, reg_nome_cru.rect, dpi,
                          fontes_dir):
            return NomeAjustado(nome, descritor, piso_cedeu=True)
        return NomeAjustado(nome, descritor, elipsa=True)

    # C2 no motor: com linha de descritor, o peso do fim do nome DESCE
    # (e some a duplicação "Italac 200g" + "200g" do caminho real) — e
    # a sigla de embalagem que o acompanha desce JUNTO, na ordem do
    # nome ("Tinto TP 1,5L" → "TP · 1,5 L"): o dono mandou (27/07),
    # embalagem nunca se omite
    partes_desc: list[str] = []
    nome_atual, peso = separar_peso(nome)
    tokens = nome_atual.split()
    # T4 (DUODECIMUS): unidade SOLTA no fim ("…Rezende KG", vendido a
    # peso sem número) desce ao descritor como o peso desce — canonizada
    # pela régua única do sanitize ("LTS" → "L", "KGS" → "kg")
    if peso is None and len(tokens) > 1 \
            and tokens[-1].lower() in UNIDADES_SOLTAS:
        solta = tokens.pop()
        peso = _canonizar_unidade(solta.lower(), REGRAS_PADRAO)
    siglas: list[str] = []
    if peso:
        while len(tokens) > 1 and tokens[-1].upper() in REGRAS_PADRAO.siglas:
            siglas.insert(0, tokens.pop())
    partes_desc.extend(siglas)
    if peso:
        partes_desc.append(peso)
    nome_atual = " ".join(tokens)
    desc_atual = _juntar_descritor(partes_desc, descritor0)

    rects: dict[str, Retangulo] = {}
    rect_nome = reg_nome.rect

    # passos 1-2
    if _cabe(nome_atual, reg_nome, rect_nome, dpi, fontes_dir):
        return NomeAjustado(nome_atual, desc_atual, rects)

    # passo 3 — a banda cresce, a foto cede (orçamento O1)
    if reg_img is not None:
        crescido = _crescer_banda(reg_nome, reg_img, regioes, dpi,
                                  fontes_dir, nome_atual)
        if crescido is not None:
            rect_nome, rect_foto = crescido
            rects = {reg_nome.uid: rect_nome, reg_img.uid: rect_foto}
            if _cabe(nome_atual, reg_nome, rect_nome, dpi, fontes_dir):
                return NomeAjustado(nome_atual, desc_atual, rects)

    # passo 4 — QUARTUSDECIMUS §2: a banda inteira (o SUBTITULO cala)
    # só existe para item SEM unidade nenhuma; com unidade no descritor
    # a cadeia segue ao passo 5 — o nome encurta, a unidade fica
    if desc_atual and dividir_descritor(desc_atual, unidade)[1] is None:
        alto = min(rect_nome.y_mm, reg_sub.rect.y_mm)
        baixo = max(rect_nome.y_mm + rect_nome.alt_mm,
                    reg_sub.rect.y_mm + reg_sub.rect.alt_mm)
        banda_inteira = Retangulo(rect_nome.x_mm, alto,
                                  rect_nome.larg_mm, baixo - alto)
        if _cabe(nome_atual, reg_nome, banda_inteira, dpi, fontes_dir):
            rects = dict(rects)
            rects[reg_nome.uid] = banda_inteira
            return NomeAjustado(nome_atual, None, rects,
                                descritor_saiu=True)

    # passo 5 — o nome encurta pelo descritor (o fim desce, inteiro,
    # na ordem do nome; Tipo+Marca ficam enquanto couber)
    # K3 (QUINTUSDECIMUS): o corte NUNCA parte marca ao meio — o pop que
    # deixaria um órfão curto no fim ("Amaciante Mon | Bijou…") desce o
    # par JUNTO; idem o par consagrado do mercado ("Extra | Virgem")
    tokens = nome_atual.split()
    excedente: list[str] = []
    while len(tokens) > 1:
        tk = tokens.pop()
        excedente.insert(0, tk)            # a sigla desce COM o resto
        while len(tokens) > 1 and _corte_parte_marca(tokens[-1],
                                                     excedente[0]):
            excedente.insert(0, tokens.pop())
        candidato = " ".join(tokens)
        if _cabe(candidato, reg_nome, rect_nome, dpi, fontes_dir):
            return NomeAjustado(
                candidato,
                _juntar_descritor([" ".join(excedente)] + partes_desc,
                                  descritor0),
                rects)

    # K3, a palavra do dono na reauditoria: "na dúvida entre cortar a
    # marca e diminuir o corpo, diminui o corpo" — antes da elipse o
    # PISO CEDE ao mínimo original da região e o nome sai INTEIRO
    # (o espelho do ramo sem SUBTITULO do adendo do Quintou)
    if reg_nome_cru.tamanho_min_pt < reg_nome.tamanho_min_pt \
            and _cabe(nome_atual, reg_nome_cru, rect_nome, dpi,
                      fontes_dir):
        return NomeAjustado(nome_atual, desc_atual, rects,
                            piso_cedeu=True)

    # passo 6 — nem a cadeia salvou: elipsa (o desenho trunca no piso) e
    # a revisora/pré-voo acusam pela flag
    return NomeAjustado(
        " ".join(tokens),
        _juntar_descritor([" ".join(excedente)] + partes_desc, descritor0)
        if excedente or partes_desc else desc_atual,
        rects, elipsa=True)
