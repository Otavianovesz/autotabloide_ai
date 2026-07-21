"""Caça-duplicatas do acervo (R-075, Fase 9 — Bloco B).

Acha produtos duplicados e propõe FUNDIR — ASSISTIDA (o dono confirma) e por
CHAVE NATURAL (I1): nunca funde dois produtos diferentes por engano. Reusa a
`chave_natural` da portabilidade (o precedente selado de "casar o mesmo produto
por identidade, nunca por posição"). A fusão é reversível (soft-delete do
perdedor) e logada (aliases migram para o vencedor), sem perda silenciosa.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.portabilidade import chave_natural


@dataclass
class ParDuplicata:
    """Um par candidato a fundir — com a chave que os casou (evidência, não fé)."""
    a: object                 # o produto mais antigo (id menor) = candidato a vencedor
    b: object
    chave: tuple              # ("ean", "789…") ou ("nat", (nome, marca))


def _chave_forte(p) -> tuple:
    """EAN quando presente (chave forte); senão a chave natural nome+marca (I1)."""
    ean = getattr(p, "ean", None)
    if ean:
        return ("ean", str(ean))
    return ("nat", chave_natural(getattr(p, "nome_sanitizado", "") or "",
                                 getattr(p, "marca", "") or ""))


def achar_duplicatas(produtos) -> list[ParDuplicata]:
    """Agrupa o acervo por chave forte (EAN) ou natural (nome+marca) e devolve os
    pares candidatos. Marca DIFERENTE cai em chave diferente → NUNCA vira par
    (I1). Produtos já excluídos (lixeira) são ignorados."""
    grupos: dict[tuple, list] = {}
    for p in produtos:
        if getattr(p, "excluido_em", None) is not None:
            continue
        grupos.setdefault(_chave_forte(p), []).append(p)
    pares: list[ParDuplicata] = []
    for chave, membros in grupos.items():
        if len(membros) < 2:
            continue
        # ordena por id (o mais antigo é o candidato a vencedor — herda a história)
        membros = sorted(membros, key=lambda x: getattr(x, "id", 0) or 0)
        vencedor = membros[0]
        for outro in membros[1:]:
            pares.append(ParDuplicata(vencedor, outro, chave))
    return pares


def fundir_no_banco(session, vencedor_id: int, perdedor_id: int) -> dict:
    """Funde o perdedor no vencedor DENTRO da sessão dada (o chamador commita):
    os aliases do perdedor migram para o vencedor (sem duplicar), o nome bruto do
    perdedor vira alias do vencedor, e o perdedor é SOFT-DELETE (lixeira,
    reversível — nunca DELETE). Devolve um log do que aconteceu (I2). As fotos do
    perdedor ficam preservadas na pasta dele até a lixeira expirar (nada some)."""
    from datetime import datetime

    from app.core.models import Produto, ProdutoAlias
    from app.core.repositories import ProdutoRepositorio

    venc = session.get(Produto, vencedor_id)
    perd = session.get(Produto, perdedor_id)
    if venc is None or perd is None or venc.id == perd.id:
        raise ValueError("fusão inválida: vencedor/perdedor ausente ou igual")

    repo = ProdutoRepositorio(session)
    migrados: list[str] = []
    # os aliases do perdedor viram aliases do vencedor (idempotente, não duplica)
    for al in list(perd.aliases):
        repo._garantir_alias(vencedor_id, al.alias_raw)
        migrados.append(al.alias_raw)
    # o nome bruto do perdedor também vira alias (a loja escreve assim também)
    if getattr(perd, "nome_bruto", None):
        repo._garantir_alias(vencedor_id, perd.nome_bruto)
        migrados.append(perd.nome_bruto)
    # remove os aliases do perdedor (já migraram) e SOFT-DELETE o perdedor
    for al in list(perd.aliases):
        session.delete(al)
    perd.excluido_em = datetime.now()
    session.flush()
    return {"vencedor": vencedor_id, "perdedor": perdedor_id,
            "aliases_migrados": migrados}
