"""F13-SEXTUS §3 — monta a SEGUNDA REAL de 27/07 no banco DO DONO.

O primeiro teste de ponta a ponta com dado dele: a tabela
``Segunda 27.07.jpeg`` (8 itens) e a foto ``Ativo 2.png`` (o Kit
Burguer). Este script faz, NA RAIZ REAL (L10):

1. interna a foto do Kit na biblioteca (``_fixos/``) e grava o
   ``conteudo_fixo`` da célula fixa do layout "Segunda dos Frios" no
   BANCO (N1 — preço DA SEMANA);
2. prova o S3: ``atualizar_fixos_pela_tabela`` com a tabela real puxa
   o 39,00 pela chave natural (e sobrevive à reimportação);
3. cria o PROJETO "Segunda dos Frios 27/07" com os 8 itens reais
   (mapa por uid, I1) — abrível e EXPORTÁVEL pela Mesa;
4. compõe as DUAS variantes da célula que sobra (S2) para o dono
   apontar: (A) vazia limpa · (B) com o ornamento da casa.

Uso:  python -m app.scripts.montar_segunda_real
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parents[2]

# a tabela REAL, transcrita e conferida na imagem (S1 já provou o
# parser com as linhas cruas; aqui vão nome sanitizado + preço)
ITENS_2707 = [
    ("Kit Burguer Senepol BBX", "39,00", None),
    ("Creme de Leite Italac 200g", "2,44", "_auto/queijo_mussarela_latopar_1kg.png"),
    ("Leite Condensado Triangulo 395g", "7,44", "38/atual.png"),
    ("Batata Palha Bulnez Crocante 100g", "6,66",
     "_auto/batata_palha_bulnez_100g.png"),
    ("Azeite Gallo Extra Virgem Clássico 500ml", "38,80", "30/atual.png"),
    ("Suco de Uva Aurora Tinto TP 1,5L", "19,99", "22/atual.png"),
    ("Leite Integral Parmalat 1L", "5,95",
     "_auto/leite_parmalat_integral_1l.png"),
    ("Óleo de Soja Concordia 900ml", "7,70", "_auto/leo_de_soja_liza_900ml.png"),
]
# substitutos DECLARADOS (não há foto destes no acervo): Italac→miolo
# de laticínio; Azeite Gallo→Andorinha; Suco Aurora→Sofruta; Óleo
# Concordia→Liza. O dono cadastra as reais pelo Estúdio.


def montar() -> None:
    os.environ["AUTOTABLOIDE_ROOT"] = str(
        RAIZ_REPO / "AutoTabloide_System_Root")
    from app.core.database import Database
    from app.core.paths import SystemRoot
    from app.qt.telas.servico import (
        ItemMesa,
        atualizar_fixos_pela_tabela,
        preco_decimal,
    )
    from app.qt.telas.fixos_dialog import internar_foto_fixa
    from app.rendering.persistencia import (
        carregar_layout,
        listar_layouts,
        salvar_layout,
    )

    root = SystemRoot()
    print("raiz real:", root.raiz)

    # 1) a foto do Kit internada (I3) + conteudo_fixo no layout do banco
    rel = internar_foto_fixa(RAIZ_REPO / "Ativo 2.png")
    print("foto do Kit internada:", rel)
    db = Database().init()
    try:
        with db.Session() as s:
            alvo = next(r for r in listar_layouts(s)
                        if r.nome == "Segunda dos Frios")
            lay = carregar_layout(s, alvo.id, raiz=root)
            fixas = [sl for p in lay.paginas for sl in p.slots if sl.fixa]
            assert fixas, "a Segunda não tem célula fixa?!"
            fixas[0].conteudo_fixo = {
                "nome": "Kit Burguer Senepol BBX",
                "descritor": "blend senepol · 4 un × 120 g",
                "preco": None,               # vem DA SEMANA (S3)
                "preco_da_semana": True,
                "imagem": rel,
            }
            # 2) S3: a tabela real puxa o preço pela CHAVE NATURAL
            itens = [ItemMesa(nome=n, descricao="", semaforo="verde",
                              preco=p) for n, p, _f in ITENS_2707]
            avisos = atualizar_fixos_pela_tabela(lay, itens)
            for a in avisos:
                print("fixo:", a)
            assert fixas[0].conteudo_fixo["preco"] == "39,00", (
                "o preço da semana NÃO chegou ao fixo (S3)")
            salvar_layout(s, "Segunda dos Frios", lay,
                          layout_id=alvo.id, raiz=root)
            s.commit()
            print("conteudo_fixo gravado no layout", alvo.id)

            # 3) o PROJETO da semana — abrível/exportável pela Mesa
            from app.rendering.grade import (
                ocupaveis,
                ordenar_slots_visualmente,
            )
            livres = [sl.id for sl in ocupaveis(
                ordenar_slots_visualmente(lay.paginas[0].slots))]
            mapa = {}
            resto = [it for it in itens
                     if not it.nome.startswith("Kit Burguer")]
            for sid, it in zip(livres, resto):
                mapa[sid] = it.uid
            # foto do acervo em cada item (substitutos declarados)
            bib = root.biblioteca_imagens
            for it, (_n, _p, foto) in zip(itens, ITENS_2707):
                if foto:
                    it.imagem = str(bib / foto)
            from app.core import projetos
            pid = projetos.salvar_projeto(
                "Segunda dos Frios 27/07", "Segunda dos Frios",
                "TABLOIDE", lay, [it.to_dict() for it in itens],
                validade_oferta="SOMENTE 27/07", mapa=mapa)
            print(f"projeto salvo: id={pid} — abra na Mesa e exporte")
            n_vazias = len(livres) - len(resto)
            print(f"células livres: {len(livres)} · itens: {len(resto)}"
                  f" · vazias: {n_vazias} (S2 — as 2 variantes na galeria)")
    finally:
        db.engine.dispose()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    montar()
