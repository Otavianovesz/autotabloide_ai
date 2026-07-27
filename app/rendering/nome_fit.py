"""
A precedência do nome — ORDEM F13-NONUS §2 (código, não procedimento)
=====================================================================
O "…" está PROIBIDO em nome de produto. Antes de qualquer elipse, a
cadeia da OCTAVUS roda em RUNTIME, para todo nome, nesta ordem:

1. o nome cabe no corpo mínimo (1 linha)?    → usa
2. cabe em 2+ linhas no corpo mínimo?        → usa (mesma medida)
3. a banda pode crescer (orçamento O1)?      → cresce, a FOTO cede
4. tem descritor? o descritor SAI            → o nome usa a banda inteira
5. o nome ENCURTA pelo descritor             → o excedente desce inteiro
6. só então elipsa — e a revisora/pré-voo acusa (``elipsa=True``)

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

from dataclasses import dataclass, field
from pathlib import Path

from app.core.sanitize import REGRAS_PADRAO, separar_peso
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
                   fontes_dir: Path) -> tuple[Retangulo, Retangulo] | None:
    """Passo 3: quanto a banda do nome PODE crescer para 2 linhas no
    corpo mínimo, com a foto cedendo — sem furar o piso de 55% do O1.
    Só quando a foto está ACIMA da banda (o desenho das células do
    pacote); devolve (rect_nome, rect_foto) ou None se não há folga."""
    rn, ri = reg_nome.rect, reg_img.rect
    if ri.y_mm + ri.alt_mm > rn.y_mm + 0.5:      # foto não está acima
        return None
    try:
        from PIL import ImageFont
        from app.rendering.units import pt_para_px
        px = max(1, round(pt_para_px(reg_nome.tamanho_min_pt, dpi)))
        f = ImageFont.truetype(str(fontes_dir / reg_nome.fonte), px)
        asc, desc = f.getmetrics()
    except OSError:
        return None
    precisa_px = 2 * round((asc + desc) * 1.12)
    delta_mm = px_para_mm(precisa_px, dpi) - rn.alt_mm
    if delta_mm <= 0:
        return None                              # altura não é o problema
    y0 = min(r.rect.y_mm for r in regioes if r.visivel)
    y1 = max(r.rect.y_mm + r.rect.alt_mm for r in regioes if r.visivel)
    folga_mm = ri.alt_mm - _FRACAO_MIN_FOTO * (y1 - y0)
    delta_mm = min(delta_mm, folga_mm)
    if delta_mm <= 0.1:
        return None
    return (
        Retangulo(rn.x_mm, rn.y_mm - delta_mm, rn.larg_mm,
                  rn.alt_mm + delta_mm),
        Retangulo(ri.x_mm, ri.y_mm, ri.larg_mm, ri.alt_mm - delta_mm),
    )


def precedencia_do_nome(
    nome: str,
    descritor: str | None,
    unidade: str | None,
    regioes: list[Regiao],
    dpi: int,
    fontes_dir: str | Path,
) -> NomeAjustado | None:
    """A cadeia dos 6 passos para UMA célula. Devolve None quando não há
    o que decidir (sem região NOME visível, ou nome vazio) — o
    compositor segue byte-idêntico ao de sempre."""
    if not nome:
        return None
    fontes_dir = Path(fontes_dir)
    reg_nome = next((r for r in regioes
                     if r.tipo == TipoRegiao.NOME and r.visivel), None)
    if reg_nome is None:
        return None
    reg_sub = next((r for r in regioes
                    if r.tipo == TipoRegiao.SUBTITULO and r.visivel), None)
    reg_img = next((r for r in regioes
                    if r.tipo == TipoRegiao.IMAGEM and r.visivel), None)

    descritor0 = descritor or unidade
    if reg_sub is None:
        # sem descritor na célula não há para onde mover (I2): a cadeia
        # é só o aviso de elipse (o Quintou/Jornal-fluxo caem aqui)
        if _cabe(nome, reg_nome, reg_nome.rect, dpi, fontes_dir):
            return None
        return NomeAjustado(nome, descritor, elipsa=True)

    # C2 no motor: com linha de descritor, o peso do fim do nome DESCE
    # (e some a duplicação "Italac 200g" + "200g" do caminho real) — e
    # a sigla de embalagem que o acompanha desce JUNTO, na ordem do
    # nome ("Tinto TP 1,5L" → "TP · 1,5 L"): o dono mandou (27/07),
    # embalagem nunca se omite
    partes_desc: list[str] = []
    nome_atual, peso = separar_peso(nome)
    tokens = nome_atual.split()
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
                                  fontes_dir)
        if crescido is not None:
            rect_nome, rect_foto = crescido
            rects = {reg_nome.uid: rect_nome, reg_img.uid: rect_foto}
            if _cabe(nome_atual, reg_nome, rect_nome, dpi, fontes_dir):
                return NomeAjustado(nome_atual, desc_atual, rects)

    # passo 4 — o descritor sai e o nome usa a banda inteira
    if desc_atual:
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
    tokens = nome_atual.split()
    excedente: list[str] = []
    while len(tokens) > 1:
        tk = tokens.pop()
        excedente.insert(0, tk)            # a sigla desce COM o resto
        candidato = " ".join(tokens)
        if _cabe(candidato, reg_nome, rect_nome, dpi, fontes_dir):
            return NomeAjustado(
                candidato,
                _juntar_descritor([" ".join(excedente)] + partes_desc,
                                  descritor0),
                rects)

    # passo 6 — nem a cadeia salvou: elipsa (o desenho trunca no piso) e
    # a revisora/pré-voo acusam pela flag
    return NomeAjustado(
        " ".join(tokens),
        _juntar_descritor([" ".join(excedente)] + partes_desc, descritor0)
        if excedente or partes_desc else desc_atual,
        rects, elipsa=True)
