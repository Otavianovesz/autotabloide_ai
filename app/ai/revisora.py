"""IA revisora do export (R-081, Fase 9 — Bloco B) — o item mais ambicioso.

Antes de aprovar, a IA "lê" o PNG final e aponta preço trocado, nome cortado,
foto errada — comparando o que VÊ com os dados do projeto (preço/nome por slot).

TRÊS DECISÕES TRAVADAS respeitadas:
1. A revisora NUNCA bloqueia o export — só devolve AVISOS (o dono decide).
2. Sem o modelo de VISÃO (IA off/indisponível/erro), degrada para checagens
   HEURÍSTICAS (nome que não cabe por medida, preço fora de faixa, de ≤ por) COM
   aviso — e o export acontece igual.
3. A revisora NÃO altera o projeto — só lê e aponta (a peça sai idêntica com/sem).

Devolve ``(avisos: list[str], aviso_degradacao: str | None)``. Nunca levanta.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from app.core.sentinela import faixas_por_categoria, preco_suspeito

_PROMPT = (
    "Você é um revisor de encarte de supermercado. Olhe a imagem e liste, em "
    "JSON, os PARES produto+preço que você consegue LER claramente juntos "
    "(o preço que está NA CÉLULA daquele produto): "
    '{"itens": [{"nome": "Arroz 5kg", "preco": "5,90"}], '
    '"precos": ["5,90"], "nomes": ["Arroz 5kg"]}. '
    "Não invente — se não conseguir ler um par completo, não o liste."
)


def _fmt_preco(v: Decimal | None) -> str | None:
    if v is None:
        return None
    q = v.quantize(Decimal("0.01"))
    return f"{int(q)},{int((q - int(q)) * 100):02d}"


def _norm_preco(txt: str) -> str:
    """Normaliza um preço lido para 'X,XX' (tira R$, espaços; vírgula decimal)."""
    t = "".join(c for c in str(txt) if c.isdigit() or c in ",.")
    t = t.replace(".", ",")
    if "," in t:
        inteiro, _, cent = t.rpartition(",")
        cent = (cent + "00")[:2]
        return f"{inteiro or '0'},{cent}"
    return f"{t},00" if t else ""


def _regiao_nome(slot):
    from app.rendering.model import TipoRegiao
    return next((r for r in slot.regioes if r.tipo == TipoRegiao.NOME), None)


def _pares_de_calibracao(dados_por_slot):
    """OS F11.5 #25/#26 (R-078): os pares (categoria, preço) do projeto EM
    TELA + o HISTÓRICO das edições salvas (o acervo F11) — com poucos itens
    no projeto, o histórico calibra as faixas e a sentinela passa a disparar.
    Falha de leitura degrada para só-o-projeto (I2, nunca levanta)."""
    pares = [(d.categoria, d.preco_por) for d in dados_por_slot.values()]
    try:
        from app.core.projetos import itens_das_edicoes_recentes
        from app.qt.telas.servico import preco_decimal
        for edicao in itens_das_edicoes_recentes(8):
            for it in edicao:
                pares.append((it.get("categoria"),
                              preco_decimal(it.get("preco"))))
    except Exception:
        pass
    return pares


def heuristicas_do_pre_voo(layout, dados_por_slot,
                           fontes_dir=None) -> list[str]:
    """F13/D10 (VC-050): o piso determinístico EXPOSTO para o pré-voo —
    a mesma lista do revisar_export, sem precisar compor o PNG. O app
    sempre soube detectar (nome cortado, preço fora de faixa, de≤por);
    só contava no botão 'Revisar' — agora pergunta na hora certa."""
    return _heuristicas(layout, dados_por_slot, fontes_dir)


def _heuristicas(layout, dados_por_slot, fontes_dir) -> list[str]:
    """As checagens que rodam SEM visão (o piso, decisão travada): nome que não
    cabe na medida da região, preço de ≤ por (PROCON), preço fora da faixa da
    categoria. Baratas, determinísticas, nunca levantam."""
    avisos: list[str] = []
    # faixa de preço aprendida do projeto + do HISTÓRICO (R-078 calibrada)
    faixas = faixas_por_categoria(_pares_de_calibracao(dados_por_slot))
    slots = {s.id: s for p in getattr(layout, "paginas", []) for s in p.slots} \
        if layout is not None else {}
    for sid, d in dados_por_slot.items():
        rot = f"“{d.nome}”"
        # de ≤ por (risco PROCON) — o mesmo critério do pré-voo
        if d.preco_de is not None and d.preco_por is not None \
                and d.preco_de <= d.preco_por:
            avisos.append(f"{rot}: o preço “de” (R$ {_fmt_preco(d.preco_de)}) não "
                          f"é maior que o “por” (R$ {_fmt_preco(d.preco_por)}) — "
                          "risco PROCON.")
        # preço fora de faixa (R-078)
        susp = preco_suspeito(d.preco_por, d.categoria, faixas)
        if susp:
            avisos.append(f"{rot}: {susp}")
        # nome cortado por medida — a MESMA cadeia do compositor
        # (F13-NONUS/N1): a precedência encurta pelo descritor antes de
        # qualquer elipse; o aviso só sai quando NEM a cadeia salvou
        # (o que a composição de verdade vai truncar)
        slot = slots.get(sid)
        reg = _regiao_nome(slot) if slot is not None else None
        if reg is not None and (d.nome or "").strip() and fontes_dir is not None:
            try:
                from app.rendering.nome_fit import precedencia_do_nome
                from app.rendering.text_fit import piso_do_celular
                dpi = getattr(layout, "dpi", 300)
                # v3 (achado da frota): a simulação roda com as MESMAS
                # marcas do desenho — sem elas a revisora via OUTRA
                # página (a hierarquia canônica muda nome e descritor)
                # e nenhum corte real era anunciado
                aj = precedencia_do_nome(
                    d.nome, getattr(d, "descritor", None),
                    getattr(d, "unidade", None), slot.regioes, dpi,
                    Path(fontes_dir),
                    piso_pt=piso_do_celular(
                        getattr(layout, "largura_mm", 0)),
                    marcas=getattr(d, "marcas_nome", ()))
                if aj is not None and aj.elipsa:
                    avisos.append(f"{rot}: o nome não cabe inteiro na célula — "
                                  "aparece cortado (…).")
                if aj is not None and getattr(aj, "piso_cedeu", False):
                    avisos.append(f"{rot}: o nome só coube abaixo do piso "
                                  "de legibilidade do celular (corpo "
                                  "reduzido — confira no zoom).")
                # QUARTUSDECIMUS (frota, I2): o corte do QUALIFICADOR
                # no desenho do SUBTITULO nunca é silencioso — a MESMA
                # decisão do desenho (descritor_que_cabe), anunciada
                from app.rendering.model import TipoRegiao
                from app.rendering.nome_fit import descritor_que_cabe_ex
                reg_sub = next(
                    (r for r in slot.regioes
                     if r.tipo == TipoRegiao.SUBTITULO and r.visivel),
                    None)
                desc_f = (aj.descritor if aj is not None
                          else getattr(d, "descritor", None))
                uni_f = (None if aj is not None and aj.descritor_saiu
                         else getattr(d, "unidade", None))
                cheio = desc_f or uni_f
                if aj is not None and aj.descritor_saiu \
                        and (getattr(d, "descritor", None) or "").strip():
                    # v3: o passo 4 calou a 2ª linha INTEIRA — com a
                    # hierarquia canônica ela carrega marca/sabores;
                    # o desenho declarou, alguém tem que anunciar
                    avisos.append(
                        f"{rot}: a 2ª linha saiu para o nome caber — "
                        f"perdeu “{d.descritor}”.")
                if reg_sub is not None and cheio:
                    vai, cortado = descritor_que_cabe_ex(
                        desc_f, uni_f, reg_sub, dpi, Path(fontes_dir))
                    if cortado:
                        avisos.append(
                            f"{rot}: o descritor não coube — perdeu "
                            f"“{cortado}” (sai “{vai}”).")
            except Exception:
                pass
    return avisos


def _norm_nome(txt: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKD", str(txt))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(t.lower().split())


def _casa_nome(lido: str, esperado: str) -> bool:
    """O nome LIDO na peça é o produto ESPERADO? Tolerante ao OCR: um
    contém o outro, ou similaridade alta (difflib)."""
    a, b = _norm_nome(lido), _norm_nome(esperado)
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a, b).ratio() >= 0.75


def _revisao_por_visao(png_path, dados_por_slot, motor) -> list[str]:
    """Compara o que o modelo de visão LÊ na peça com o que o projeto
    espera. F13/B8 (CI-02): o prompt sempre pediu os NOMES e a revisora
    os jogava fora — preço TROCADO entre dois itens (os dois preços
    existem no projeto!) passava limpo, a coisa que ela existe para
    pegar. Agora os PARES nome+preço são conferidos item a item."""
    from app.ai.ocr import _extrair_json_obj
    esperados = {_fmt_preco(d.preco_por) for d in dados_por_slot.values()
                 if d.preco_por is not None}
    esperados.discard(None)
    resp = motor.visao(str(png_path), _PROMPT, max_tokens=1024)
    obj = _extrair_json_obj(resp)
    avisos: list[str] = []

    # 1) os PARES (a prova do preço trocado)
    itens_do_projeto = [(d.nome, _fmt_preco(d.preco_por))
                        for d in dados_por_slot.values()
                        if d.nome and d.preco_por is not None]
    for par in obj.get("itens", []) or []:
        nome_lido = str(par.get("nome", "")).strip()
        preco_lido = _norm_preco(par.get("preco", ""))
        if not nome_lido or not preco_lido:
            continue
        casados = [(n, p) for n, p in itens_do_projeto
                   if _casa_nome(nome_lido, n)]
        if not casados:
            continue                      # nome que não é do projeto: ruído
        if any(p == preco_lido for _n, p in casados):
            continue                      # o par confere
        certo = casados[0][1]
        dono_do_preco = next((n for n, p in itens_do_projeto
                              if p == preco_lido), None)
        if dono_do_preco is not None:
            avisos.append(
                f"A peça mostra “{nome_lido}” com R$ {preco_lido}, que é o "
                f"preço de “{dono_do_preco}” (o esperado era R$ {certo}) — "
                "parece PREÇO TROCADO entre as células.")
        else:
            avisos.append(
                f"A peça mostra “{nome_lido}” com R$ {preco_lido}, mas o "
                f"projeto diz R$ {certo} — confira essa célula.")

    # 2) a rede antiga (preço solto que não pertence a ninguém)
    lidos = [_norm_preco(p) for p in obj.get("precos", []) if str(p).strip()]
    for p in lidos:
        if p and esperados and p not in esperados:
            avisos.append(f"A peça mostra o preço R$ {p}, que não bate com "
                          "nenhum preço do projeto — confira se não trocou.")
    return avisos


def revisar_export(png_path, dados_por_slot, *, layout=None, motor=None,
                   fontes_dir=None) -> tuple[list[str], str | None]:
    """R-081: revisa a peça e devolve (avisos, aviso_degradacao). As heurísticas
    (o piso) rodam SEMPRE; a visão ACRESCENTA a comparação preço-lido × esperado
    quando disponível. NUNCA bloqueia, NUNCA altera o projeto, NUNCA levanta —
    TODO o corpo está sob try (achado da frota: `disponivel()`/heurística fora do
    try feriam o 'nunca levanta')."""
    avisos: list[str] = []
    aviso_deg: str | None = None
    try:
        avisos = _heuristicas(layout, dados_por_slot, fontes_dir)
        tem_visao = motor is not None and getattr(
            motor, "disponivel", lambda: False)()
    except Exception:
        return avisos, ("A revisão falhou nas medidas — o export não foi "
                        "bloqueado.")
    if tem_visao:
        try:
            avisos = avisos + _revisao_por_visao(png_path, dados_por_slot, motor)
        except Exception:
            aviso_deg = ("A revisão por visão falhou — revisei só pelas medidas "
                         "(heurística). O export não foi bloqueado.")
    else:
        aviso_deg = ("A IA de visão está desligada — revisei pelas medidas "
                     "(heurística). O export não foi bloqueado.")
    return avisos, aviso_deg
