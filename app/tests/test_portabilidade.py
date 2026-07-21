"""Portabilidade (D-B1) — unidades: chave natural, pacote inválido, defesas."""

import json
import zipfile

import pytest

from app.core import portabilidade as porta
from app.core.portabilidade import chave_natural
from app.tests import seeds_portabilidade as seeds


def test_chave_natural_normaliza_acento_caixa_espaco():
    assert chave_natural("Açúcar Cristal  1kg", "União") == \
        chave_natural("acucar cristal 1kg", "UNIAO")
    assert chave_natural("Café", None) != chave_natural("Café", "Pilão")
    assert chave_natural(None, None) == ("", "")


def test_exportar_sem_banco_erro(tmp_path):
    from app.core.paths import SystemRoot

    root = SystemRoot(tmp_path / "vazia").criar_estrutura()   # sem core.db
    with pytest.raises(FileNotFoundError):
        porta.exportar_pacote(tmp_path / "x.atpkg", root)


def test_pacote_sem_manifesto_recusado(tmp_path):
    falso = tmp_path / "falso.atpkg"
    with zipfile.ZipFile(falso, "w") as z:
        z.writestr("qualquer.txt", "nada")
    b = seeds.raiz(tmp_path, "b")
    with pytest.raises(ValueError, match="atpkg"):
        porta.analisar_pacote(falso, b)


def test_pacote_de_versao_futura_recusado(tmp_path):
    a = seeds.raiz(tmp_path, "a")
    seeds.add_produto(a, "Coisa", "Marca", "1.00")
    pkg = porta.exportar_pacote(tmp_path / "a.atpkg", a)
    # reescreve o manifesto com um schema do futuro
    adulterado = tmp_path / "futuro.atpkg"
    with zipfile.ZipFile(pkg) as origem, \
            zipfile.ZipFile(adulterado, "w") as destino:
        for nome in origem.namelist():
            dados = origem.read(nome)
            if nome == "manifesto.json":
                m = json.loads(dados)
                m["versao_schema"] = 99
                dados = json.dumps(m).encode()
            destino.writestr(nome, dados)
    b = seeds.raiz(tmp_path, "b")
    with pytest.raises(ValueError, match="MAIS NOVA"):
        porta.analisar_pacote(adulterado, b)


def test_zip_slip_recusado(tmp_path):
    malicioso = tmp_path / "mal.atpkg"
    with zipfile.ZipFile(malicioso, "w") as z:
        z.writestr("manifesto.json", "{}")
        z.writestr("../fora_da_pasta.txt", "escapei")
    b = seeds.raiz(tmp_path, "b")
    with pytest.raises(ValueError, match="suspeito"):
        porta.analisar_pacote(malicioso, b)


def test_conflito_usar_pacote_arquiva_a_foto_antiga(tmp_path):
    """A foto local substituída não some: vira versão (histórico do produto)."""
    a = seeds.raiz(tmp_path, "a")
    seeds.add_produto(a, "Suco Uva 1L", "Aurora", "9.90", seeds.png("#333333"))
    b = seeds.raiz(tmp_path, "b")
    id_b = seeds.add_produto(b, "Suco Uva 1L", "Aurora", "9.90",
                             seeds.png("#444444"))

    pkg = porta.exportar_pacote(tmp_path / "a.atpkg", a)
    with porta.analisar_pacote(pkg, b) as analise:
        assert analise.conflitos and "foto" in analise.conflitos[0].campos
        porta.aplicar_importacao(
            analise, {analise.conflitos[0].id_decisao: porta.Decisao.USAR_PACOTE}, b)

    assert seeds.foto_de(b, "Suco Uva 1L", "Aurora") == seeds.png("#333333")
    versoes = list((b.biblioteca_imagens / str(id_b) / "versoes").glob("*.png"))
    assert len(versoes) == 1                       # a antiga foi arquivada
    assert versoes[0].read_bytes() == seeds.png("#444444")


def test_b_fix1_falha_apos_substituicao_restaura_a_foto_local(tmp_path, monkeypatch):
    """B-fix1 (reauditoria da Etapa B): falha DEPOIS de uma substituição.

    Dois conflitos de foto, os dois "usar do pacote". A foto de X é
    substituída; na verificação, a de Y "falha" (corrupção simulada). O banco
    reverte — e a foto ORIGINAL de X tem que voltar byte a byte ao disco
    (sem isso: banco dizendo uma coisa, pasta mostrando outra).
    """
    from pathlib import Path

    a = seeds.raiz(tmp_path, "a")
    seeds.add_produto(a, "Suco X 1L", "Marca", "5.00", seeds.png("#111111"))
    seeds.add_produto(a, "Suco Y 1L", "Marca", "5.00", seeds.png("#222222"))
    b = seeds.raiz(tmp_path, "b")
    seeds.add_produto(b, "Suco X 1L", "Marca", "5.00", seeds.png("#333333"))
    id_y_b = seeds.add_produto(b, "Suco Y 1L", "Marca", "5.00",
                               seeds.png("#444444"))

    pkg = porta.exportar_pacote(tmp_path / "a.atpkg", a)
    with porta.analisar_pacote(pkg, b) as analise:
        assert len(analise.conflitos) == 2
        # corrupção simulada: a leitura de verificação da foto de Y mente
        alvo = (b.biblioteca_imagens / str(id_y_b) / "atual.png").resolve()
        real = porta._bytes_ou_none

        def leitura_corrompida(caminho):
            if Path(caminho).resolve() == alvo:
                return b"corrompido"
            return real(caminho)

        monkeypatch.setattr(porta, "_bytes_ou_none", leitura_corrompida)
        with pytest.raises(RuntimeError, match="nada foi gravado"):
            porta.aplicar_importacao(
                analise,
                {c.id_decisao: porta.Decisao.USAR_PACOTE
                 for c in analise.conflitos}, b)
        monkeypatch.setattr(porta, "_bytes_ou_none", real)

    # as fotos locais originais VOLTARAM, byte a byte (X foi substituída
    # antes da falha — é exatamente ela que o rollback tem que devolver)
    assert seeds.foto_de(b, "Suco X 1L", "Marca") == seeds.png("#333333")
    assert seeds.foto_de(b, "Suco Y 1L", "Marca") == seeds.png("#444444")
    # o backup em versoes/ voltou para o lugar — não sobrou órfão
    for pid in b.biblioteca_imagens.iterdir():
        versoes = pid / "versoes"
        assert not versoes.exists() or not list(versoes.glob("*_pre_import.png"))
    # e o banco não mudou nada (preço/caminho continuam os locais)
    assert seeds.produto_por_chave(b, "Suco X 1L", "Marca")["preco"] == "5.00"


def test_config_nova_entra_existente_fica_local(tmp_path):
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio

    a = seeds.raiz(tmp_path, "a")
    seeds.add_produto(a, "Coisa", "Marca", "1.00")
    db = Database(a).init()
    with db.Session() as s:
        ConfigRepositorio(s).set("sanitizacao.siglas", ["VD", "PET"])
        s.commit()
    db.engine.dispose()

    # B vazio: a config VIAJA (glossário curado não se perde no PC novo)
    b = seeds.raiz(tmp_path, "b")
    pkg = porta.exportar_pacote(tmp_path / "a.atpkg", a)
    with porta.analisar_pacote(pkg, b) as analise:
        assert "sanitizacao.siglas" in analise.config_novas
        porta.aplicar_importacao(analise, {}, b)
    db = Database(b).init()
    with db.Session() as s:
        assert ConfigRepositorio(s).get("sanitizacao.siglas") == ["VD", "PET"]
    db.engine.dispose()

    # agora B muda a config: no próximo import a LOCAL vence, com aviso visível
    db = Database(b).init()
    with db.Session() as s:
        ConfigRepositorio(s).set("sanitizacao.siglas", ["VD"])
        s.commit()
    db.engine.dispose()
    with porta.analisar_pacote(pkg, b) as analise2:
        assert "sanitizacao.siglas" in analise2.config_diferentes
        rel = porta.aplicar_importacao(analise2, {}, b)
    assert any("sanitizacao.siglas" in a for a in rel.avisos)
    db = Database(b).init()
    with db.Session() as s:
        assert ConfigRepositorio(s).get("sanitizacao.siglas") == ["VD"]
    db.engine.dispose()


def test_e_a1_layout_manter_ambos_deduplica_nome(tmp_path):
    """Reimportar com MANTER_AMBOS não colide: (importado), (importado 2)…"""
    arte = tmp_path / "arte.png"
    arte.write_bytes(seeds.png("#ABCDEF"))
    a = seeds.raiz(tmp_path, "a")
    seeds.add_produto(a, "Coisa", "Marca", "1.00")
    seeds.add_layout_com_arte(a, "Tabloide Padrão", arte)

    b = seeds.raiz(tmp_path, "b")
    arte2 = tmp_path / "arte2.png"
    arte2.write_bytes(seeds.png("#FEDCBA"))
    lid_b = seeds.add_layout_com_arte(b, "Tabloide Padrão", arte2)
    from app.core.database import Database
    from app.core.models import Layout
    db = Database(b).init()
    with db.Session() as s:
        row = s.get(Layout, lid_b)
        e = row.get_estrutura()
        e["largura_mm"] = 999.0
        row.estrutura_json = json.dumps(e, ensure_ascii=False)
        s.commit()
    db.engine.dispose()

    pkg = porta.exportar_pacote(tmp_path / "a.atpkg", a)
    nomes = []
    for _ in range(2):                     # duas importações, mesma decisão
        with porta.analisar_pacote(pkg, b) as analise:
            lay = next(c for c in analise.conflitos if c.tipo == "layout")
            rel = porta.aplicar_importacao(
                analise, {lay.id_decisao: porta.Decisao.MANTER_AMBOS}, b)
            nomes += rel.layouts_importados
    assert nomes == ["Tabloide Padrão (importado)",
                     "Tabloide Padrão (importado 2)"]


def test_e_a2_acervo_mudou_entre_analise_e_aplicacao(tmp_path):
    """Produto criado localmente entre as fases → erro nominal, sem duplicata."""
    a = seeds.raiz(tmp_path, "a")
    seeds.add_produto(a, "Coisa Nova", "Marca", "1.00", seeds.png("#101010"))
    b = seeds.raiz(tmp_path, "b")

    pkg = porta.exportar_pacote(tmp_path / "a.atpkg", a)
    with porta.analisar_pacote(pkg, b) as analise:
        assert len(analise.novos) == 1
        # entre a análise e a aplicação, o humano cadastra o MESMO produto
        seeds.add_produto(b, "coisa nova", "MARCA", "2.00")   # chave natural igual
        with pytest.raises(ValueError, match="re-analise"):
            porta.aplicar_importacao(analise, {}, b)
    assert seeds.contagens(b)["produtos"] == 1     # nada duplicou

    # re-análise enxerga o estado novo: vira conflito e o fluxo segue normal
    with porta.analisar_pacote(pkg, b) as analise2:
        assert not analise2.novos and len(analise2.conflitos) == 1
        porta.aplicar_importacao(
            analise2,
            {analise2.conflitos[0].id_decisao: porta.Decisao.MANTER_LOCAL}, b)
    assert seeds.contagens(b)["produtos"] == 1


def test_layout_divergente_e_conflito_visivel(tmp_path):
    """Mesmo nome de layout, estrutura diferente → conflito (nunca silêncio)."""
    arte = tmp_path / "arte.png"
    arte.write_bytes(seeds.png("#ABCDEF"))
    a = seeds.raiz(tmp_path, "a")
    seeds.add_produto(a, "Coisa", "Marca", "1.00")
    seeds.add_layout_com_arte(a, "Tabloide Padrão", arte)

    b = seeds.raiz(tmp_path, "b")
    arte2 = tmp_path / "arte2.png"
    arte2.write_bytes(seeds.png("#FEDCBA"))
    lid_b = seeds.add_layout_com_arte(b, "Tabloide Padrão", arte2)
    # muda a ESTRUTURA do layout de B (não só a arte)
    from app.core.database import Database
    from app.core.models import Layout
    db = Database(b).init()
    with db.Session() as s:
        row = s.get(Layout, lid_b)
        e = row.get_estrutura()
        e["largura_mm"] = 999.0
        row.estrutura_json = json.dumps(e, ensure_ascii=False)
        s.commit()
    db.engine.dispose()

    pkg = porta.exportar_pacote(tmp_path / "a.atpkg", a)
    with porta.analisar_pacote(pkg, b) as analise:
        lays = [c for c in analise.conflitos if c.tipo == "layout"]
        assert len(lays) == 1 and lays[0].rotulo == "Tabloide Padrão"
        rel = porta.aplicar_importacao(
            analise, {lays[0].id_decisao: porta.Decisao.MANTER_LOCAL}, b)
    assert ("Tabloide Padrão", "manter_local") in rel.conflitos_resolvidos
