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


_CONECTORES = ("e", "ou", "com")


def _juntar_descritor(partes: list[str], existente: str | None) -> str | None:
    """Monta o descritor final: excedente do nome (na ordem do nome) +
    o descritor que o item já tinha — sem duplicar conteúdo.

    RODADA-125 v2 (achado da frota): o ``existente`` entra FATIADO em
    " · " — comparado inteiro, "Diversos · 500ml" nunca continha o
    "500 ml" já emitido e a página saía "500 ml · Diversos · 500ml".

    v3: (a) o dedupe é por TOKENS, nunca por substring da concatenação
    — a unidade curta "g" era substring de "fugini" e sumia em
    silêncio (furava a QUARTUSDECIMUS §2 por dentro); (b) partes com
    CONECTOR na borda se FUNDEM ("Fujini e" + "Cajamar" → "Fujini e
    Cajamar" — o " · " nunca cai no meio da frase)."""
    pedacos: list[str] = []
    for p in partes:
        pedacos.extend((p or "").split(" · "))
    if existente:
        pedacos.extend(existente.split(" · "))
    saida: list[str] = []
    tokens_vistos: set[str] = set()
    for p in pedacos:
        p = (p or "").strip(" ·")
        if not p:
            continue
        toks = [_norm(t) for t in p.split()]
        # a parte inteira sem espaços também conta como "token": o
        # "500ml" colado casa com o "500 ml" já emitido (e vice-versa)
        if all(t in tokens_vistos for t in toks) \
                or _norm(p) in tokens_vistos:
            continue                     # tudo já dito — parte redundante
        if saida and saida[-1].split()[-1].lower() in _CONECTORES:
            saida[-1] = f"{saida[-1]} {p}"       # "Fujini e" + "Cajamar"
        elif saida and p.split()[0].lower() in _CONECTORES:
            saida[-1] = f"{saida[-1]} {p}"       # "Fujini" + "e Cajamar"
        else:
            saida.append(p)
        tokens_vistos.update(toks)
        tokens_vistos.add(_norm(p))
    # conector órfão na cauda ("… e") cai — nunca imprime frase manca
    while saida and saida[-1].split()[-1].lower() in _CONECTORES:
        resto = saida[-1].rsplit(None, 1)[0] if " " in saida[-1] else ""
        if resto:
            saida[-1] = resto
        else:
            saida.pop()
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


# v4 (a LEI do dono, 4ª prova): informação de venda sai POR EXTENSO —
# a forma compacta "N sabores" foi VETADA ("não fica bom e pode dar
# processo"); antes de QUALQUER tesoura o CORPO CEDE até o piso duro
# (o espelho do K3 do nome: legível-pequeno > cortado)
_PISO_DURO_DESCRITOR = 6.0


def descritor_que_cabe_ex(descritor: str | None, unidade: str | None,
                          reg: Regiao, dpi: int,
                          fontes_dir: str | Path,
                          ) -> tuple[str | None, str | None]:
    """v4 — devolve ``(texto_que_sai, o_que_foi_cortado)``. A escada:
    (1) o completo no corpo da região; (2) o completo com o CORPO
    CEDENDO até o piso duro (a lei do dono: NENHUMA informação é
    comida — o layout dá o espaço, a letra diminui); (3) só num caso
    patológico (nem no piso coube) a tesoura corta do FIM — e o que
    caiu volta NOMEADO no 2º campo (I2: o pré-voo/revisora anunciam)."""
    texto = descritor or unidade
    if not texto:
        return None, None
    fontes_dir = Path(fontes_dir)
    if _cabe(texto, reg, reg.rect, dpi, fontes_dir):
        return texto, None
    if reg.tamanho_min_pt > _PISO_DURO_DESCRITOR:
        reg_piso = replace(reg, tamanho_min_pt=_PISO_DURO_DESCRITOR)
        if _cabe(texto, reg_piso, reg.rect, dpi, fontes_dir):
            return texto, None           # coube inteiro, corpo reduzido
    qual, unidade_txt = dividir_descritor(texto, unidade)
    partes_q = qual.split(" · ") if qual else []
    cortadas: list[str] = []
    while partes_q:
        cortadas.insert(0, partes_q.pop())
        cand = " · ".join(partes_q + ([unidade_txt] if unidade_txt else []))
        if cand and _cabe(cand, reg, reg.rect, dpi, fontes_dir):
            return cand, " · ".join(cortadas)
    return (unidade_txt or texto), (" · ".join(cortadas) or None)


def descritor_que_cabe(descritor: str | None, unidade: str | None,
                       reg: Regiao, dpi: int,
                       fontes_dir: str | Path) -> str | None:
    """O texto que o SUBTITULO desenha (o wrapper histórico — quem
    precisa saber O QUE caiu usa ``descritor_que_cabe_ex``)."""
    texto, _cortado = descritor_que_cabe_ex(descritor, unidade, reg,
                                            dpi, fontes_dir)
    return texto


def _altura_real_mm(texto: str, reg: Regiao, dpi: int,
                    fontes_dir: Path) -> float | None:
    """Quantos mm o texto REALMENTE usa na largura da região (linhas
    de verdade × entrelinha) — a medida da célula elástica."""
    if not texto:
        return 0.0
    aj = ajustar_texto(
        texto, fontes_dir / reg.fonte,
        mm_para_px(reg.rect.larg_mm, dpi),
        mm_para_px(reg.rect.alt_mm, dpi),
        reg.tamanho_max_pt, dpi, reg.tamanho_min_pt,
        sem_hifen=reg.sem_hifen)
    if any("…" in ln for ln in aj.linhas):
        return None                      # nem coube — não mexe na célula
    return px_para_mm(len(aj.linhas) * aj.altura_linha_px + 2, dpi)


def compactar_coluna(regioes: list[Regiao], nome: str,
                     descritor: str | None, unidade: str | None,
                     dpi: int, fontes_dir: str | Path,
                     rects_atuais: dict, piso_pt: float | None = None,
                     ) -> dict[str, Retangulo]:
    """RODADA-125 v4.1 (a 5ª prova do dono: "quase descolado, as
    imagens diminuíram ainda mais"): a CÉLULA DE COLUNA é ELÁSTICA.

    A caixa de 3 linhas do descritor é RESERVA para o caso cheio (o
    Biscoito com 2 marcas × 4 sabores); a célula comum, de 1 linha,
    não pode pagar por ela com foto pequena e vãos mortos. A régua:
    o texto MEDE o que realmente usa, ANCORA no preço (a base fixa da
    coluna), e a FOTO cresce até encostar nele — zero vão, foto
    dominante, o layout que um diagramador faria à mão.

    Só age na topologia de COLUNA (foto acima do nome, nome acima do
    descritor, descritor acima do preço, todos visíveis); devolve os
    rects substitutos por uid — o modelo nunca muda (I1)."""
    fontes_dir = Path(fontes_dir)

    def _r_de(reg: Regiao) -> Retangulo:
        return rects_atuais.get(reg.uid, reg.rect)

    por_tipo: dict = {}
    for r in regioes:
        if r.visivel and r.tipo in (TipoRegiao.NOME, TipoRegiao.SUBTITULO,
                                    TipoRegiao.IMAGEM, TipoRegiao.PRECO):
            if r.tipo in por_tipo:
                return {}                # 2 do mesmo tipo: célula rara, fora
            por_tipo[r.tipo] = r
    if len(por_tipo) < 4:
        return {}
    reg_img = por_tipo[TipoRegiao.IMAGEM]
    # o MESMO contrato do plano Q1: só a célula marcada REPLANEJÁVEL
    # (``zona_flex``) aceita re-layout por dentro — nas demais a arte
    # do autor manda (o invariante A1 da máscara por região fica de pé)
    if not getattr(reg_img, "zona_flex", False):
        return {}
    reg_nome = por_tipo[TipoRegiao.NOME]
    reg_sub = por_tipo[TipoRegiao.SUBTITULO]
    reg_preco = por_tipo[TipoRegiao.PRECO]
    ri, rn = _r_de(reg_img), _r_de(reg_nome)
    rs, rp = _r_de(reg_sub), _r_de(reg_preco)
    # a topologia da coluna (com 1 mm de tolerância de arte)
    if not (ri.y_mm + ri.alt_mm <= rn.y_mm + 1.0
            and rn.y_mm + rn.alt_mm <= rs.y_mm + 1.0
            and rs.y_mm + rs.alt_mm <= rp.y_mm + 1.0):
        return {}
    reg_nome_m = reg_nome
    if piso_pt:
        min_ef = min(reg_nome.tamanho_max_pt,
                     max(reg_nome.tamanho_min_pt, piso_pt))
        reg_nome_m = replace(reg_nome, tamanho_min_pt=min_ef)
    alt_nome = _altura_real_mm(nome, reg_nome_m, dpi, fontes_dir)
    reg_sub_m = (reg_sub if reg_sub.tamanho_min_pt <= _PISO_DURO_DESCRITOR
                 else replace(reg_sub,
                              tamanho_min_pt=_PISO_DURO_DESCRITOR))
    texto_sub = descritor_que_cabe(descritor, unidade, reg_sub_m, dpi,
                                   fontes_dir)
    alt_sub = _altura_real_mm(texto_sub or "", reg_sub_m, dpi, fontes_dir)
    if alt_nome is None or alt_sub is None:
        return {}
    folga = 0.5                          # o respiro fino entre blocos
    y_sub = rp.y_mm - folga - alt_sub
    y_nome = y_sub - folga - alt_nome
    alt_foto = y_nome - folga - ri.y_mm
    if alt_foto <= ri.alt_mm:
        return {}                        # a foto só CRESCE — nunca perde
    return {
        reg_img.uid: Retangulo(ri.x_mm, ri.y_mm, ri.larg_mm, alt_foto),
        reg_nome.uid: Retangulo(rn.x_mm, y_nome, rn.larg_mm, alt_nome),
        reg_sub.uid: Retangulo(rs.x_mm, y_sub, rs.larg_mm, alt_sub),
    }


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
_PARES_DO_MERCADO = {("extra", "virgem"), ("mon", "bijou"),
                     # v2: "Açúcar Cristal DOCE / DIA · 2kg" na página
                     ("doce", "dia")}

# §15.2: palavras que ABREM par com a seguinte e nunca encerram um nome
# de produto sozinhas — artigo/preposição/conjunção ("Alface | A Peça",
# "Sabão | em Pó") e o título de marca do varejo ("Tio Bonini",
# "Tia Rosa").
_ABRE_PAR = {"a", "o", "à", "ao", "de", "do", "da", "dos", "das",
             "em", "com", "e", "sem", "sob", "para", "p/",
             "tio", "tia"}


def _mesmo_peso_exibido(token: str, unidade: str | None) -> bool:
    """O token do nome é o MESMO peso da unidade do dado? ("104g" ×
    "104 g", "1,6kg" × "1.6 Kg") — a comparação da exibição, espaços/
    vírgula/caixa fora."""
    if not unidade or not _RE_PARTE_UNIDADE.match(token or ""):
        return False
    return _norm(token) == _norm(unidade)


def peso_do_cadastro(nome: str) -> str | None:
    """VICESIMUS-QUARTUS §1.2: o peso que o NOME do cadastro carrega, em
    QUALQUER posição ("Água Mineral Marajá 497ml S/ Gás" → "497ml") —
    ``separar_peso`` só olha as bordas; aqui a régua é o token. É a
    metade "achar" da lei UM ITEM TEM UM PESO SÓ: quando este peso
    diverge do da tabela, ELE vence (é a correção do dono) e a
    divergência vira aviso da conciliação (J10), nunca texto na arte."""
    for t in (nome or "").split():
        if _RE_PARTE_UNIDADE.match(t):
            return t
    _, p = separar_peso(nome or "")
    return p


def mesmo_peso_exibido(a: str | None, b: str | None) -> bool:
    """A comparação pública da exibição — espaços/vírgula/caixa fora
    ("497ml" × "497 ml" é o MESMO; "500ml" × "497 ml" NÃO é)."""
    if not a or not b:
        return False
    return _norm(a) == _norm(b)


def _tirar_peso_repetido(tokens: list[str], unidade: str | None,
                         ) -> tuple[list[str], list[str]]:
    """RODADA-125 v2 (as 5 células "…1,6kg / … · 1,6kg"): o peso que
    mora no MEIO do nome do banco e é IGUAL à unidade sai da linha
    grande — a unidade já o leva ao descritor. O token de EMBALAGEM
    colado ao peso ("104g Tubo") desce junto, como qualificador. Só a
    EXIBIÇÃO muda; o banco fica intacto (a lei da camada do sanitize
    segue de pé)."""
    from app.core.sanitize import EMBALAGENS
    saida: list[str] = []
    partes: list[str] = []
    i = 0
    while i < len(tokens):
        tk = tokens[i]
        if _mesmo_peso_exibido(tk, unidade):
            if i + 1 < len(tokens) and tokens[i + 1].lower() in EMBALAGENS:
                partes.append(tokens[i + 1])
                i += 2
                continue
            i += 1
            continue
        saida.append(tk)
        i += 1
    return saida, partes


def _descer_marca(tokens: list[str], marcas: tuple[str, ...],
                  ) -> tuple[list[str], list[str], list[str]]:
    """A REGRA CANÔNICA da célula (decisão do dono na 2ª prova): a
    linha grande diz O QUE É; a MARCA desce ao descritor — SEMPRE, não
    só quando falta espaço (era a causa do "sem padrão": Triângulo
    ficava grande numa célula e Parmalat descia na outra).

    Devolve ``(tokens_do_tipo, partes_do_descritor, pesos_do_resto)``.
    O span vai da 1ª marca reconhecida à última, engolindo conectores
    ("e"/"ou") e parênteses de embalagem — "Fugini (pouch) e Bonare
    (lata)" desce INTEIRO. O que vem DEPOIS da marca (sabor/
    qualificador) desce junto, na ordem; o PESO escondido no resto sai
    à parte (v3 — quem o põe no FIM é a junção). Marca no token 0 não
    divide (não existe tipo antes — o nome É a marca); sem marca
    reconhecida, nada muda (F9: a régua reconhece, nunca inventa)."""
    if not marcas or len(tokens) < 2:
        return tokens, [], []
    chaves = [t.lower().strip("().,;:·") for t in tokens]
    alvos = [tuple(m.lower().split()) for m in marcas if m]

    def _casa(i: int) -> int | None:
        for alvo in sorted(alvos, key=len, reverse=True):
            j = i + len(alvo)
            if j <= len(chaves) and tuple(chaves[i:j]) == alvo:
                return j
        return None

    ini = fim = None
    for i in range(1, len(tokens)):          # 0 nunca: tipo não pode sumir
        j = _casa(i)
        if j is not None:
            ini, fim = i, j
            break
    if ini is None:
        return tokens, [], []
    # v3 (a 3ª prova: "Molho Tomate Fujini e · Cajamar"): o tipo NUNCA
    # termina em conector — quando o padrão é [X, e/ou, MARCA], o "X e"
    # desce JUNTO (o X antes do conector é a marca-irmã que a régua não
    # reconheceu; "Tipo e Marca" não existe no vocabulário do mercado)
    while ini >= 2 and chaves[ini - 1] in ("e", "ou"):
        ini -= 2
    # …e a régua do passo 5 vale aqui também: preposição/artigo/par
    # consagrado nunca fica órfão no fim do tipo ("Farinha de | X e M")
    while ini > 1 and _corte_parte_marca(tokens[ini - 1], tokens[ini]):
        ini -= 1
    if ini < 1:
        return tokens, [], []
    # estende: (rótulo) → [e|ou (rótulo)? marca (rótulo)?]*
    while fim < len(tokens):
        if tokens[fim].startswith("(") and tokens[fim].endswith(")"):
            fim += 1
            continue
        if chaves[fim] in ("e", "ou") and _casa(fim + 1):
            fim = _casa(fim + 1)
            continue
        break
    marca_txt = " ".join(tokens[ini:fim])
    # v3: o peso escondido DENTRO do resto sai e canoniza ("600g Coco
    # e Leite" → resto "Coco e Leite", peso "600 g" — quem o põe no
    # FIM é a junção; antes a parte descia crua com o peso na frente)
    resto_toks = [t for t in tokens[fim:] if t != "·"]
    pesos_resto = []
    for t in resto_toks:
        if _RE_PARTE_UNIDADE.match(t):
            _x, pf = separar_peso(f"x {t}")
            pesos_resto.append(pf or t)      # canonizado ("600g"→"600 g")
    resto = " ".join(t for t in resto_toks
                     if not _RE_PARTE_UNIDADE.match(t)).strip(" ·")
    partes = [marca_txt] + ([resto] if resto else [])
    return tokens[:ini], partes, pesos_resto


def _corte_parte_marca(ultimo: str, descido: str) -> bool:
    """O corte deixaria um PAR partido? A régua não conta letras
    (reauditoria §15.2 — o degrau de comprimento consertou "Mon Bijou"
    e quebrou "Multi Uso"): palavra curta que ENCERRA o nome é do nome
    ("…Multi Uso", "Leite Pó"); desce junto só quem forma par com a
    palavra seguinte — o consagrado ou o gramatical."""
    if (ultimo.lower(), descido.lower()) in _PARES_DO_MERCADO:
        return True
    return ultimo.lower() in _ABRE_PAR


def precedencia_do_nome(
    nome: str,
    descritor: str | None,
    unidade: str | None,
    regioes: list[Regiao],
    dpi: int,
    fontes_dir: str | Path,
    piso_pt: float | None = None,
    marcas: tuple[str, ...] = (),
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
    # o composto "Arroz Somar e Tio Bonini · 5 kg" deixa um "·" órfão
    # quando o peso sai — cai aqui, antes da tokenização
    tokens = [t for t in nome_atual.split() if t != "·"]
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
    # RODADA-125 v2: o peso do MEIO igual à unidade sai da exibição (a
    # unidade já desce ao descritor) e a embalagem colada a ele desce
    tokens, partes_meio = _tirar_peso_repetido(tokens, unidade)
    # a REGRA CANÔNICA: a marca reconhecida desce ao descritor SEMPRE
    tokens, partes_marca, pesos_resto = _descer_marca(tokens, marcas)
    partes_desc.extend(partes_marca)
    partes_desc.extend(partes_meio)
    partes_desc.extend(siglas)
    # v3: o PESO fecha o descritor SEMPRE — depois dos sabores do
    # descritor0, nunca no meio ("Mabel · Coco ou Leite · 600 g"); os
    # pesos do resto da marca e o do C2 entram na cauda, deduplicados
    # contra a unidade que o descritor0 já carrega
    # VICESIMUS-QUARTUS §1.2: UM ITEM TEM UM PESO SÓ — o peso do resto
    # da marca que é IGUAL à unidade nunca entra na cauda (o descritor0
    # já o carrega; era o "500ml · 497 ml" quando divergiam — a
    # divergência agora se resolve ANTES, no dado, e aqui não passa
    # repetição nenhuma)
    cauda_pesos = [pz for pz in pesos_resto
                   if not (unidade and _norm(pz) == _norm(unidade))]
    if peso and not _mesmo_peso_exibido(peso, unidade):
        cauda_pesos.append(peso)
    nome_atual = " ".join(tokens)

    def _montar_descritor(partes_frente: list[str]) -> str | None:
        return _juntar_descritor(
            partes_frente + ([descritor0] if descritor0 else [])
            + cauda_pesos, None)

    desc_atual = _montar_descritor(partes_desc)

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
    pesos_meio: list[str] = []
    while len(tokens) > 1:
        tk = tokens.pop()
        excedente.insert(0, tk)            # a sigla desce COM o resto
        while len(tokens) > 1 and _corte_parte_marca(tokens[-1],
                                                     excedente[0]):
            excedente.insert(0, tokens.pop())
        # v2 (achado da frota): o corte pode deixar o candidato
        # TERMINANDO em peso ("Detg. Limpol 500ml" após descer
        # "Diversos") — re-separa a cada passo; o peso vai ao
        # descritor, nunca fica na linha grande
        cand_nome, cand_peso = separar_peso(" ".join(tokens))
        if cand_peso:
            pesos_meio.append(cand_peso)
            tokens = cand_nome.split()
        candidato = " ".join(tokens)
        if _cabe(candidato, reg_nome, rect_nome, dpi, fontes_dir):
            return NomeAjustado(
                candidato,
                _montar_descritor([" ".join(excedente)] + pesos_meio
                                  + partes_desc),
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
        _montar_descritor([" ".join(excedente)] + pesos_meio + partes_desc)
        if excedente or pesos_meio or partes_desc else desc_atual,
        rects, elipsa=True)
