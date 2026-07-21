"""
Self-check do builder — Etapa D do Bloco D (roteiro da sessão ao vivo)
======================================================================
Roda os TRÊS itens do gate na máquina real, com os dados REAIS do acervo,
sem tocar no System Root vivo (ele é só LIDO, via export):

  1. Cartaz ponta a ponta na Fábrica (placeholder 10×15 + preços reais do
     banco) → PDF multipágina MEDIDO com pypdf;
  2. Roundtrip casa↔mercado com raízes descartáveis + conflito proposital
     (preço e foto) resolvido no relatório — verificação byte a byte;
  3. Limiar do semáforo pela Config mudando a conciliação do MESMO item.

Rodar:  python -m app.scripts.selfcheck_bloco_d
Artefatos em ``saida_selfcheck_d/`` (PDF medido + pacotes .atpkg usados).
"""

from __future__ import annotations

import shutil
import sys
from decimal import Decimal
from pathlib import Path

SAIDA = Path("saida_selfcheck_d")


def _ok(msg: str) -> None:
    print(f"  OK  {msg}")


def _falha(msg: str) -> None:
    print(f"  FALHOU  {msg}")
    sys.exit(1)


def item1_cartaz_real() -> None:
    print("\n[1] Cartaz ponta a ponta (placeholder 10x15 + precos reais)")
    from pypdf import PdfReader
    from sqlalchemy import select

    from app.core.database import Database
    from app.core.models import Produto
    from app.core.paths import SystemRoot
    from app.qt.telas.servico import validar_composicao
    from app.rendering.cartaz import layout_cartaz_exemplo
    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.export import exportar_pdf_multipagina

    root = SystemRoot()
    db = Database(root).init()
    try:
        with db.Session() as s:
            reais = [p for p in s.execute(select(Produto)).scalars()
                     if p.caminho_imagem and p.preco_atual is not None][:3]
            if len(reais) < 3:
                _falha("menos de 3 produtos reais com foto+preço no banco")
            dados = []
            for p in reais:
                foto = root.biblioteca_imagens / p.caminho_imagem
                dados.append(DadosProduto(
                    p.nome_sanitizado,
                    preco_por=p.preco_atual,
                    preco_de=p.preco_atual + Decimal("1.00"),
                    imagem_path=str(foto) if foto.exists() else None,
                    mais18=bool(p.selo_mais18),
                ))
    finally:
        db.engine.dispose()

    lay = layout_cartaz_exemplo()
    slot_id = lay.paginas[0].slots[0].id
    pendencias = []
    for d in dados:
        pendencias += validar_composicao(lay, {slot_id: d}, cartaz=True)
    print(f"      pré-voo (cartaz=True): {len(pendencias)} pendência(s) "
          f"{'— ' + '; '.join(pendencias[:3]) if pendencias else '(nenhuma)'}")

    paginas = [compor_pagina(lay, lay.paginas[0], d) for d in dados]
    pdf = exportar_pdf_multipagina(paginas, SAIDA / "cartazes_selfcheck.pdf",
                                   lay.dpi)
    leitor = PdfReader(str(pdf))
    if len(leitor.pages) != 3:
        _falha(f"esperava 3 páginas (1 item = 1 página), veio {len(leitor.pages)}")
    for i, pg in enumerate(leitor.pages, 1):
        w_mm = float(pg.mediabox.width) / 72 * 25.4
        h_mm = float(pg.mediabox.height) / 72 * 25.4
        if abs(w_mm - 100) > 0.6 or abs(h_mm - 150) > 0.6:
            _falha(f"página {i} mediu {w_mm:.2f}×{h_mm:.2f} mm (≠ 100×150)")
        print(f"      página {i}: {w_mm:.2f} × {h_mm:.2f} mm — "
              f"“{dados[i-1].nome[:40]}”")
    _ok(f"PDF no tamanho exato da etiqueta: {pdf}")


def item2_roundtrip_real() -> None:
    print("\n[2] Roundtrip casa<->mercado (acervo REAL, raizes descartaveis)")
    from sqlalchemy import select

    from app.core import portabilidade as porta
    from app.core.database import Database
    from app.core.models import Produto
    from app.core.paths import SystemRoot
    from app.tests.seeds_portabilidade import (
        add_produto,
        contagens,
        foto_de,
        png,
        produto_por_chave,
        raiz,
    )

    real = SystemRoot()

    # fotos reais por chave natural (o gabarito byte a byte do roundtrip)
    gabarito: dict[tuple[str, str], bytes] = {}
    db = Database(real).init()
    try:
        with db.Session() as s:
            for p in s.execute(select(Produto)).scalars():
                if p.caminho_imagem:
                    f = real.biblioteca_imagens / p.caminho_imagem
                    if f.exists():
                        gabarito[porta.chave_natural(
                            p.nome_sanitizado, p.marca)] = f.read_bytes()
            esperados = contagens(real)
    finally:
        db.engine.dispose()

    # casa → mercado (o System Root real é apenas LIDO aqui)
    pkg1 = porta.exportar_pacote(SAIDA / "casa.atpkg", real)
    mercado = raiz(SAIDA, "raiz_mercado")
    with porta.analisar_pacote(pkg1, mercado) as an:
        if an.conflitos:
            _falha(f"import em raiz vazia não podia ter conflito: "
                   f"{[c.rotulo for c in an.conflitos]}")
        rel = porta.aplicar_importacao(an, {}, mercado)
    c_mercado = contagens(mercado)
    if c_mercado["produtos"] != esperados["produtos"] or \
            c_mercado["projetos"] != esperados["projetos"]:
        _falha(f"contagens divergem: mercado={c_mercado} real={esperados}")
    for chave, bytes_ in gabarito.items():
        f = None
        p = produto_por_chave(mercado, chave[0], chave[1])
        if p and p["caminho_imagem"]:
            f = mercado.biblioteca_imagens / p["caminho_imagem"]
        if f is None or not f.exists() or f.read_bytes() != bytes_:
            _falha(f"foto de {chave[0]!r} não é byte-idêntica após o remap")
    _ok(f"{esperados['produtos']} produtos, {rel.fotos_verificadas} fotos "
        f"verificadas byte a byte, {c_mercado['projetos']} projetos no mercado")

    # conflito proposital no mercado: preço + foto num produto real
    alvo = next(iter(gabarito))
    p_alvo = produto_por_chave(mercado, alvo[0], alvo[1])
    db = Database(mercado).init()
    try:
        with db.Session() as s:
            row = s.get(Produto, p_alvo["id"])
            preco_novo = (row.preco_atual or Decimal("5.00")) + Decimal("2.00")
            row.preco_atual = preco_novo
            s.commit()
    finally:
        db.engine.dispose()
    (mercado.biblioteca_imagens / p_alvo["caminho_imagem"]).write_bytes(
        png("#00FFAA"))
    add_produto(mercado, "Produto Novo do Mercado", "SelfCheck", "3.33",
                png("#AA00FF"))
    print(f"      conflito plantado em “{alvo[0]}”: preço → {preco_novo}, "
          "foto trocada; +1 produto novo")

    # mercado → casa (numa CÓPIA da casa — o vivo não é tocado)
    pkg2 = porta.exportar_pacote(SAIDA / "mercado.atpkg", mercado)
    casa2 = raiz(SAIDA, "raiz_casa_copia")
    with porta.analisar_pacote(pkg1, casa2) as an:
        porta.aplicar_importacao(an, {}, casa2)      # casa2 = estado da casa
    with porta.analisar_pacote(pkg2, casa2) as an2:
        rotulos = {c.id_decisao: c for c in an2.conflitos if c.tipo == "produto"}
        id_alvo = f"produto:{alvo[0]}|{alvo[1]}"
        if id_alvo not in rotulos:
            _falha("o conflito proposital não apareceu no relatório")
        campos = rotulos[id_alvo].campos
        if "preço" not in campos or "foto" not in campos:
            _falha(f"conflito sem os campos esperados: {campos}")
        print(f"      relatório acusou: {rotulos[id_alvo].rotulo} "
              f"(difere: {', '.join(campos)}) — decisão: preço do pacote, "
              "foto local")
        decisoes = {c.id_decisao: porta.Decisao.MANTER_LOCAL
                    for c in an2.conflitos}
        decisoes[id_alvo] = porta.Decisao.USAR_PACOTE     # preço do mercado
        rel2 = porta.aplicar_importacao(an2, decisoes, casa2)

    # USAR_PACOTE levou preço E foto do pacote — o gabarito do alvo é a nova
    p_final = produto_por_chave(casa2, alvo[0], alvo[1])
    if Decimal(p_final["preco"]) != preco_novo:
        _falha(f"preço do alvo não atualizou: {p_final['preco']} ≠ {preco_novo}")
    esperado_alvo = png("#00FFAA")
    for chave, bytes_ in gabarito.items():
        certo = esperado_alvo if chave == alvo else bytes_
        if foto_de(casa2, chave[0], chave[1]) != certo:
            _falha(f"foto de {chave[0]!r} trocou de produto no roundtrip!")
    if produto_por_chave(casa2, "Produto Novo do Mercado", "SelfCheck") is None:
        _falha("o produto novo do mercado não chegou")
    _ok("decisões aplicadas; NENHUMA foto trocada de produto (byte a byte)")

    # idempotência: o MESMO pacote de novo
    antes = contagens(casa2)
    with porta.analisar_pacote(pkg2, casa2) as an3:
        decisoes3 = {c.id_decisao: porta.Decisao.MANTER_LOCAL
                     for c in an3.conflitos}
        porta.aplicar_importacao(an3, decisoes3, casa2)
    if contagens(casa2) != antes:
        _falha(f"reimport duplicou algo: {contagens(casa2)} ≠ {antes}")
    _ok("mesmo pacote 2×: idempotente, zero duplicatas")


def item3_limiar_vivo() -> None:
    print("\n[3] Limiar do semaforo pela Config (efeito real na conciliacao)")
    from sqlalchemy import select

    from app.ai.conciliacao import Conciliador
    from app.core.database import Database
    from app.core.models import Produto
    from app.core.paths import SystemRoot
    from app.core.repositories import ConfigRepositorio

    # na CÓPIA da casa (dados reais), nunca no vivo
    casa2 = SystemRoot(SAIDA / "raiz_casa_copia")
    db = Database(casa2).init()
    try:
        with db.Session() as s:
            # acha um item REAL que concilia VERDE via fuzzy no limiar padrão
            entrada, v1 = None, None
            for p in s.execute(select(Produto)).scalars():
                if len(p.nome_sanitizado.split()) < 3:
                    continue
                tentativa = p.nome_sanitizado.upper() + " OFERTA"
                v = Conciliador(s).conciliar(tentativa)
                if v.semaforo.value == "VERDE" and v.via == "fuzzy":
                    entrada, v1 = tentativa, v
                    break
            if v1 is None:
                _falha("nenhum item real conciliou VERDE via fuzzy p/ a demo")
            ConfigRepositorio(s).set("conciliacao.verde", 99.5)
            ConfigRepositorio(s).set("conciliacao.amarelo", 10.0)
            s.commit()
            v2 = Conciliador(s).conciliar(entrada)
            print(f"      item real: “{entrada[:50]}”")
            print(f"      limiar padrão (88/62): {v1.semaforo.value} "
                  f"(score {v1.confianca*100:.0f}, via {v1.via})")
            print(f"      limiar apertado (99,5/10): {v2.semaforo.value}")
            if v1.semaforo.value != "VERDE" or v2.semaforo.value == "VERDE":
                _falha("o limiar da Config não mudou o semáforo como esperado")
    finally:
        db.engine.dispose()
    _ok("trocar o limiar na Config muda a conciliação do MESMO item")


def main() -> int:
    # console do Windows pode ser cp1252 — acentos/setas não podem derrubar
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    SAIDA.mkdir(parents=True)
    print("Self-check da Etapa D — Bloco D (acervo real, raizes descartaveis)")
    item1_cartaz_real()
    item2_roundtrip_real()
    item3_limiar_vivo()
    print("\nSELF-CHECK COMPLETO: os 3 itens do roteiro da sessão passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
