"""
Instrumentação de seleção (FASE 4, Bloco A — RG-55)
===================================================
Log estruturado e **DESLIGÁVEL** do gesto de clique-grupo. O RG-55 (dono
clica no preço de uma célula agrupada e a região "some"/o painel esvazia)
não se teoriza — instrumenta-se e reproduz-se. Cada anotação é um dict com
o estado que o log precisa PROVAR: uid sob o cursor, z-order no ponto, se é
mestra/cópia, ângulo de rotação, estado do colapso-no-release, e o que o
painel efetivamente recebeu.

Ligado só em teste/depuração (passo 14: em produção fica desligado e o
``anotar`` retorna na 1ª linha — custo zero). NUNCA imprime sozinho.
"""

from __future__ import annotations

_LIGADO = False
_REGISTRO: list[dict] = []


def ligar() -> None:
    """Liga a captura (e zera o registro anterior)."""
    global _LIGADO
    _LIGADO = True
    _REGISTRO.clear()


def desligar() -> None:
    global _LIGADO
    _LIGADO = False


def ligado() -> bool:
    return _LIGADO


def limpar() -> None:
    _REGISTRO.clear()


def registro() -> list[dict]:
    """Cópia rasa da sequência capturada, na ordem dos eventos."""
    return list(_REGISTRO)


def anotar(evento: str, **campos) -> None:
    """Registra um evento SE a captura estiver ligada (custo zero desligado)."""
    if _LIGADO:
        _REGISTRO.append({"evento": evento, **campos})
