"""E-A3 do Bloco E — arte de layout RELATIVA na raiz (cura do I3 no banco vivo).

Salvar interna (copia p/ layouts/ e grava relativo), carregar resolve,
layouts antigos migram na abertura com aviso — e o pacote continua
relativizando na fronteira (defesa em profundidade).
"""

import json
from pathlib import Path

from app.core import portabilidade as porta
from app.core.database import Database
from app.core.models import Layout
from app.rendering.model import layout_de_arte
from app.rendering.persistencia import (
    carregar_layout,
    migrar_artes_absolutas,
    resolver_arte,
    salvar_layout,
)
from app.tests import seeds_portabilidade as seeds


def _ldef_com_arte(arte: Path):
    ldef = layout_de_arte(str(arte))
    ldef.paginas[0].arquivo_fundo = str(arte)    # fundo por página também
    return ldef


def test_salvar_interna_e_carregar_resolve(tmp_path):
    root = seeds.raiz(tmp_path, "raiz")
    arte = tmp_path / "minha_arte.png"           # fora da raiz (ex.: Desktop)
    arte.write_bytes(seeds.png("#ABCDEF"))
    ldef = _ldef_com_arte(arte)

    db = Database(root).init()
    try:
        with db.Session() as s:
            row = salvar_layout(s, "Layout X", ldef, raiz=root)
            s.commit()
            # o banco guarda RELATIVO e a arte foi copiada p/ a pasta gerenciada
            assert not Path(row.arquivo_fundo).is_absolute()
            assert (root.layouts / row.arquivo_fundo).exists()
            estrutura = row.get_estrutura()
            assert not Path(estrutura["arquivo_fundo"]).is_absolute()
            assert not Path(
                estrutura["paginas"][0]["arquivo_fundo"]).is_absolute()
            # o LayoutDef do chamador NÃO foi mexido (a tela segue usável)
            assert ldef.arquivo_fundo == str(arte)

            # carregar resolve de volta para caminho usável (existe no disco)
            aberto = carregar_layout(s, row.id, raiz=root)
            assert Path(aberto.arquivo_fundo).is_absolute()
            assert Path(aberto.arquivo_fundo).exists()
            assert Path(aberto.paginas[0].arquivo_fundo).exists()
    finally:
        db.engine.dispose()


def test_salvar_de_novo_nao_duplica_arquivo(tmp_path):
    root = seeds.raiz(tmp_path, "raiz")
    arte = tmp_path / "arte.png"
    arte.write_bytes(seeds.png("#111111"))
    db = Database(root).init()
    try:
        with db.Session() as s:
            row = salvar_layout(s, "X", _ldef_com_arte(arte), raiz=root)
            s.commit()
            aberto = carregar_layout(s, row.id, raiz=root)
            salvar_layout(s, "X", aberto, raiz=root)     # re-salva o resolvido
            s.commit()
            row2 = s.get(Layout, row.id)
            assert not Path(row2.arquivo_fundo).is_absolute()
    finally:
        db.engine.dispose()
    assert len(list(root.layouts.glob("*.png"))) == 1    # nada duplicou


def test_colisao_de_nome_ganha_sufixo(tmp_path):
    root = seeds.raiz(tmp_path, "raiz")
    a1 = tmp_path / "d1" / "arte.png"
    a2 = tmp_path / "d2" / "arte.png"                    # mesmo nome, outra arte
    a1.parent.mkdir()
    a2.parent.mkdir()
    a1.write_bytes(seeds.png("#222222"))
    a2.write_bytes(seeds.png("#333333"))
    db = Database(root).init()
    try:
        with db.Session() as s:
            r1 = salvar_layout(s, "L1", _ldef_com_arte(a1), raiz=root)
            r2 = salvar_layout(s, "L2", _ldef_com_arte(a2), raiz=root)
            s.commit()
            assert r1.arquivo_fundo == "arte.png"
            assert r2.arquivo_fundo == "arte_2.png"      # sufixo anti-colisão
            assert (root.layouts / "arte_2.png").read_bytes() == \
                seeds.png("#333333")
    finally:
        db.engine.dispose()


def test_migracao_de_layouts_antigos_com_aviso(tmp_path):
    root = seeds.raiz(tmp_path, "raiz")
    arte = tmp_path / "arte_antiga.png"
    arte.write_bytes(seeds.png("#444444"))
    db = Database(root).init()
    try:
        with db.Session() as s:
            ldef = _ldef_com_arte(arte)
            # gravação ESTILO ANTIGO: caminho absoluto direto no banco
            s.add(Layout(nome="Antigo OK", arquivo_fundo=str(arte),
                         estrutura_json=json.dumps(ldef.to_dict())))
            s.add(Layout(nome="Antigo Sumido",
                         arquivo_fundo=str(tmp_path / "nao_existe.png"),
                         estrutura_json="{}"))
            s.commit()

            avisos = migrar_artes_absolutas(s, root)
            s.commit()
            assert any("Antigo OK" in a and "movida" in a for a in avisos)
            assert any("Antigo Sumido" in a and "não está no disco" in a
                       for a in avisos)

            ok = s.execute(
                __import__("sqlalchemy").select(Layout).where(
                    Layout.nome == "Antigo OK")).scalar_one()
            assert not Path(ok.arquivo_fundo).is_absolute()
            assert (root.layouts / ok.arquivo_fundo).read_bytes() == \
                seeds.png("#444444")
            e = ok.get_estrutura()
            assert not Path(e["arquivo_fundo"]).is_absolute()

            # idempotente: só a arte sumida continua avisando
            avisos2 = migrar_artes_absolutas(s, root)
            assert all("Antigo Sumido" in a for a in avisos2)
    finally:
        db.engine.dispose()


def test_pacote_viaja_com_a_convencao_nova(tmp_path):
    """Layout salvo relativo (E-A3) → pacote sem caminho de máquina → destino
    também relativo, com a arte instalada e resolvível."""
    import sqlite3
    import zipfile

    a = seeds.raiz(tmp_path, "a")
    arte = tmp_path / "arte_nova.png"
    arte.write_bytes(seeds.png("#555555"))
    db = Database(a).init()
    with db.Session() as s:
        salvar_layout(s, "Layout Novo", _ldef_com_arte(arte), raiz=a)
        s.commit()
    db.engine.dispose()

    pkg = porta.exportar_pacote(tmp_path / "a.atpkg", a)
    with zipfile.ZipFile(pkg) as z:
        z.extract("banco/core.db", tmp_path / "espiar")
        assert any(n.startswith("layouts_arte/") for n in z.namelist())
    conn = sqlite3.connect(tmp_path / "espiar" / "banco" / "core.db")
    fundos = [r[0] for r in
              conn.execute("SELECT arquivo_fundo FROM layouts").fetchall()]
    conn.close()
    assert all(f is None or f.startswith("layouts_arte/") for f in fundos)

    b = seeds.raiz(tmp_path, "b")
    with porta.analisar_pacote(pkg, b) as an:
        assert "Layout Novo" in an.layouts_novos
        porta.aplicar_importacao(an, {}, b)
    db = Database(b).init()
    with db.Session() as s:
        from sqlalchemy import select
        row = s.execute(select(Layout).where(
            Layout.nome == "Layout Novo")).scalar_one()
        assert not Path(row.arquivo_fundo).is_absolute()
        resolvido = resolver_arte(row.arquivo_fundo, b)
        assert Path(resolvido).exists()
        assert Path(resolvido).read_bytes() == seeds.png("#555555")
    db.engine.dispose()
