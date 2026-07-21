"""
Enriquecer os nomes do banco (passe de manutenção)
==================================================
Produtos importados por tabela (F1) ficam com o nome só **sanitizado**
("Ole o de Soja Liza"). Este passe roda o **enriquecimento da IA** em cada
produto e PERSISTE o resultado (nome limpo + selo +18 + categoria) — o nome
fica bonito em todo lugar (tabloide, cartaz, listas), não só na importação.

Requer o LM Studio ligado (degrada avisando). Idempotente: pular os que já
estão iguais. Este mesmo serviço alimenta o "corrigir nomes" do Almoxarifado.

Uso::

    python -m app.scripts.enriquecer_banco
"""

from __future__ import annotations

from app.ai.client import ClienteOpenAICompat
from app.ai.enriquecimento import enriquecer
from app.core.database import Database
from app.core.repositories import ProdutoRepositorio


def enriquecer_banco(motor=None, *, log=print) -> dict:
    """Enriquece e persiste os nomes de todos os produtos. Devolve um resumo."""
    from app.core.modo import exigir_escrita
    exigir_escrita()                     # R-131: reescreve o acervo inteiro
    motor = motor or ClienteOpenAICompat()
    if not motor.disponivel():
        log("LM Studio não acessível — nada a fazer (os nomes ficam como estão).")
        return {"atualizados": 0, "iguais": 0, "erros": 0}

    db = Database().init()
    atualizados = iguais = erros = revisar = 0
    try:
        with db.Session() as session:
            repo = ProdutoRepositorio(session)
            produtos = repo.listar(limit=10_000)
            for i, p in enumerate(produtos, 1):
                try:
                    enr = enriquecer(p.nome_bruto, motor)
                except Exception as exc:
                    erros += 1
                    log(f"[{i:>3}/{len(produtos)}] ERRO {type(exc).__name__}: {p.nome_bruto[:40]}")
                    continue
                # RG-20 (regra dura): a IA descartou palavra do bruto — o
                # lote NÃO aplica o nome novo (o humano revisa; contado)
                if enr.tokens_perdidos:
                    revisar += 1
                    log(f"[{i:>3}/{len(produtos)}] REVISAR (perdeu "
                        f"{', '.join(enr.tokens_perdidos)}): {p.nome_bruto[:40]}")
                    continue
                antes = p.nome_sanitizado   # antes do editar (que muta o ORM)
                if enr.nome_sanitizado != antes or enr.mais18 != bool(p.selo_mais18):
                    campos = {"nome_sanitizado": enr.nome_sanitizado,
                              "selo_mais18": enr.mais18}
                    # F8.1: categoria de HUMANO nunca é sobrescrita pela IA
                    if p.categoria_origem != "humano" and enr.categoria:
                        campos["categoria"] = enr.categoria
                        campos["categoria_origem"] = "ia"
                    repo.editar(p.id, **campos)
                    atualizados += 1
                    log(f"[{i:>3}/{len(produtos)}] {antes[:34]:<34} → {enr.nome_sanitizado[:40]}")
                else:
                    iguais += 1
            session.commit()
    finally:
        db.engine.dispose()
    resumo = {"atualizados": atualizados, "iguais": iguais, "erros": erros,
              "revisar": revisar}
    log(f"\nPronto: {resumo}")
    return resumo


def categorizar_acervo(motor=None, *, log=print) -> dict:
    """F8.1: categoriza EM LOTE só o que FALTA (categoria vazia).

    Nunca toca categoria existente — nem de humano (lei), nem de IA (o
    re-passe completo é o ``enriquecer_banco``, que respeita o humano).
    Item que a IA não souber fica SEM categoria — na Mesa ele agrupa em
    "Outros" (nunca some, I2).
    """
    from app.core.modo import exigir_escrita
    exigir_escrita()                     # R-131: escreve categoria em lote
    motor = motor or ClienteOpenAICompat()
    if not motor.disponivel():
        log("LM Studio não acessível — nada a fazer (categorias como estão).")
        return {"categorizados": 0, "sem_palpite": 0, "erros": 0}

    db = Database().init()
    categorizados = sem_palpite = erros = 0
    try:
        with db.Session() as session:
            repo = ProdutoRepositorio(session)
            alvo = [p for p in repo.listar(limit=10_000)
                    if p.categoria_id is None]
            for i, p in enumerate(alvo, 1):
                try:
                    enr = enriquecer(p.nome_bruto, motor)
                except Exception as exc:
                    erros += 1
                    log(f"[{i:>3}/{len(alvo)}] ERRO {type(exc).__name__}: "
                        f"{p.nome_bruto[:40]}")
                    continue
                if enr.categoria:
                    repo.editar(p.id, categoria=enr.categoria,
                                categoria_origem="ia")
                    categorizados += 1
                    log(f"[{i:>3}/{len(alvo)}] {p.nome_sanitizado[:34]:<34} "
                        f"→ {enr.categoria}")
                else:
                    sem_palpite += 1     # fica sem categoria → "Outros" na Mesa
            session.commit()
    finally:
        db.engine.dispose()
    resumo = {"categorizados": categorizados, "sem_palpite": sem_palpite,
              "erros": erros}
    log(f"\nPronto: {resumo}")
    return resumo


if __name__ == "__main__":
    import sys
    if "--categorizar" in sys.argv:
        categorizar_acervo()
    else:
        enriquecer_banco()
