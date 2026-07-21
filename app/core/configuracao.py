"""
Configurações aplicadas ao acervo (C2 do Bloco D / F6.7)
========================================================
Mudar regra de sanitização NÃO reescreve o acervo em silêncio (I2): a tela
mostra a PRÉVIA (quantos nomes mudariam, com amostra) e só o gesto explícito
"Aplicar ao acervo" grava — este módulo é a parte headless dos dois passos.

A reformatação usa ``formatar_nome`` (o acabamento determinístico: caixa,
unidades, siglas, glossário) — nunca a IA; o sentido dos nomes não é tocado.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.models import Produto
from app.core.sanitize import RegrasSanitizacao, formatar_nome


def previa_reformatacao(session: Session,
                        regras: RegrasSanitizacao) -> list[tuple[str, str]]:
    """(nome atual, nome novo) de cada produto cujo nome mudaria — nada grava."""
    mudancas: list[tuple[str, str]] = []
    for p in session.execute(select(Produto)).scalars():
        novo = formatar_nome(p.nome_sanitizado, regras)
        if novo != p.nome_sanitizado:
            mudancas.append((p.nome_sanitizado, novo))
    return mudancas


def aplicar_reformatacao(session: Session, regras: RegrasSanitizacao) -> int:
    """Grava a reformatação no acervo. Devolve quantos nomes mudaram.

    Só deve ser chamada DEPOIS da prévia confirmada pelo humano (C2).
    """
    n = 0
    for p in session.execute(select(Produto)).scalars():
        novo = formatar_nome(p.nome_sanitizado, regras)
        if novo != p.nome_sanitizado:
            p.nome_sanitizado = novo
            n += 1
    session.flush()
    return n
