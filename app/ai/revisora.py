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
    "JSON, os PREÇOS e os NOMES de produto que você consegue LER claramente. "
    'Responda só o JSON: {"precos": ["5,90", "12,49"], "nomes": ["Arroz 5kg"]}. '
    "Não invente — se não conseguir ler, deixe a lista vazia."
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
        # nome cortado por medida (reusa o text_fit do compositor)
        slot = slots.get(sid)
        reg = _regiao_nome(slot) if slot is not None else None
        if reg is not None and (d.nome or "").strip() and fontes_dir is not None:
            try:
                from app.rendering.text_fit import ajustar_texto
                from app.rendering.units import mm_para_px
                dpi = getattr(layout, "dpi", 300)
                aj = ajustar_texto(
                    d.nome, str(Path(fontes_dir) / reg.fonte),
                    round(mm_para_px(reg.rect.larg_mm, dpi)),
                    round(mm_para_px(reg.rect.alt_mm, dpi)),
                    reg.tamanho_max_pt, dpi, reg.tamanho_min_pt)
                if any("…" in ln for ln in aj.linhas):
                    avisos.append(f"{rot}: o nome não cabe inteiro na célula — "
                                  "aparece cortado (…).")
            except Exception:
                pass
    return avisos


def _revisao_por_visao(png_path, dados_por_slot, motor) -> list[str]:
    """Compara o que o modelo de visão LÊ na peça com os preços esperados dos
    dados. Preço visível que não bate com nenhum esperado = provável troca."""
    from app.ai.ocr import _extrair_json_obj
    esperados = {_fmt_preco(d.preco_por) for d in dados_por_slot.values()
                 if d.preco_por is not None}
    esperados.discard(None)
    resp = motor.visao(str(png_path), _PROMPT, max_tokens=1024)
    obj = _extrair_json_obj(resp)
    lidos = [_norm_preco(p) for p in obj.get("precos", []) if str(p).strip()]
    avisos: list[str] = []
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
