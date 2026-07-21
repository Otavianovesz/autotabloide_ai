"""
Demonstra a conciliação (passo 3 da Fase 3) — SEM modelo (só exato + fuzzy).
O semáforo é 100% real aqui: nada de fake (o "juiz" IA fica desligado nesta demo).

Uso::

    python -m app.scripts.demo_conciliacao
"""

from __future__ import annotations

from pathlib import Path

from app.ai.conciliacao import Conciliador, Semaforo
from app.core.database import Database
from app.core.paths import SystemRoot
from app.core.repositories import ProdutoRepositorio
from app.scripts.importar_tabela import parse_tabela

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "ofertas_belo_brasil.txt"

# Variações abreviadas/tortas de itens que EXISTEM (esperado: amarelo).
VARIACOES = [
    "REFRI KITUBAINA 1,5 L",
    "LEITE NINHO 380G",
    "CAFE PILAO 500G",
    "SABAO TIXAN PO",
]

# Erros de digitação em nome curto (o limite do fuzzy puro).
TYPOS = [
    "NUTELA 350G",       # Nutella
    "BONBRIL",           # Bombril
]

# Itens que NÃO existem no banco (esperado: vermelho).
NOVOS = [
    "ESPONJA DE AÇO ASSOLAN 8 UN",
    "FRALDA PAMPERS CONFORT SEC M",
    "PILHA DURACELL AA 4 UN",
]

_ICONE = {Semaforo.VERDE: "🟢", Semaforo.AMARELO: "🟡", Semaforo.VERMELHO: "🔴"}


def semear(session) -> int:
    repo = ProdutoRepositorio(session)
    for nome, preco in parse_tabela(FIXTURE):
        repo.importar(nome, preco=preco)
    session.commit()
    return repo.contar()


def _linha(v) -> str:
    icone = _ICONE[v.semaforo]
    sug = f" -> {v.produto.nome_sanitizado}" if v.produto else ""
    return f"  {icone} {v.semaforo.value:<8} score={v.confianca*100:5.1f}  [{v.via}] {v.entrada}{sug}"


def main(real: bool = False) -> None:
    import os
    import tempfile

    embedder = None
    if real:
        from app.ai.client import ClienteOpenAICompat

        embedder = ClienteOpenAICompat()
        if not embedder.disponivel():
            print("LM Studio não acessível — rode sem --real ou suba o servidor.")
            return
        print("✅ CONCILIAÇÃO COM EMBEDDINGS REAIS (3 camadas: significado + fuzzy).\n")
    else:
        print("⚙️  CONCILIAÇÃO SÓ COM FUZZY (sem embeddings) — semáforo real, sem modelo.\n")

    with tempfile.TemporaryDirectory() as d:
        os.environ["AUTOTABLOIDE_ROOT"] = str(Path(d) / "raiz")
        db = Database(SystemRoot(Path(d) / "raiz")).init()
        try:
            with db.Session() as session:
                total = semear(session)
                conc = Conciliador(session, embedder=embedder)  # juiz desligado

                print(f"Banco semeado com {total} produtos.\n")

                print("A) MESMA TABELA (esperado: 🟢 verde)")
                verdes = sum(
                    conc.conciliar(nome).semaforo == Semaforo.VERDE
                    for nome, _ in parse_tabela(FIXTURE)
                )
                print(f"   {verdes}/{total} vieram VERDE (match exato pelo nome cru/alias)\n")

                print("B) VARIAÇÕES ABREVIADAS (esperado: 🟡 amarelo)")
                for nome in VARIACOES:
                    print(_linha(conc.conciliar(nome)))

                print("\nD) ERROS DE DIGITAÇÃO (fuzzy puro erra; com embeddings deve virar 🟡)")
                for nome in TYPOS:
                    print(_linha(conc.conciliar(nome)))

                print("\nC) ITENS NOVOS (esperado: 🔴 vermelho)")
                for nome in NOVOS:
                    print(_linha(conc.conciliar(nome)))
        finally:
            db.engine.dispose()  # libera o SQLite antes de apagar o tempdir


if __name__ == "__main__":
    import sys

    main(real="--real" in sys.argv)
