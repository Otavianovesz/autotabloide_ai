"""BLOCO E da ORDEM_F13 — confiabilidade e primeira execução (L1: cada
conserto com a rodada VERMELHA registrada antes; gesto/conteúdo sobre a
bancada do A)."""

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.tests import acervo
from app.tests.gestos import vigia_dialogo


def _app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    acervo.copiar_fontes_reais(root.fontes)
    Database(root).init().engine.dispose()
    return root


RAIZ_APP = Path(__file__).resolve().parents[1]


def _fontes_de_producao():
    """Todos os .py de produção (app/ sem tests/tests_janela/scripts de
    bancada) — a varredura por CONTEÚDO da lei dos vetos (B10/B2c)."""
    for p in RAIZ_APP.rglob("*.py"):
        rel = p.relative_to(RAIZ_APP).as_posix()
        if rel.startswith(("tests/", "tests_janela/")):
            continue
        yield p


# ---------------------------------------------------------------------------
# E10 · COND-8 (§7.4) — nenhuma tela ensina a lei morta do RASCUNHO
# ---------------------------------------------------------------------------


def test_e10_cond8_nenhuma_tela_ensina_a_lei_morta():
    """COND-8 (selo do D, §7.4): o motor da trava #1 caiu no D8, mas duas
    legendas continuavam ensinando a regra REVOGADA ("sai com RASCUNHO
    até você aprovar") — no exportar_dialog a contradição morava DENTRO
    do mesmo diálogo (o rótulo dizia carimbado; o checkbox logo abaixo
    dizia opcional). É a família M-06: o programa contando ao dono algo
    que não é verdade. Varredura por conteúdo: nenhuma string de UI
    afirma carimbo automático ou aprovação obrigatória."""
    culpados = []
    for p in _fontes_de_producao():
        texto = p.read_text(encoding="utf-8", errors="replace")
        for padrao in ("até você aprovar", "ate voce aprovar",
                       "até aprovar o projeto"):
            if padrao in texto:
                culpados.append(f"{p.name}: contém {padrao!r}")
    assert culpados == [], (
        "telas ainda ensinam a LEI MORTA do RASCUNHO (a trava #1 caiu no "
        f"D8; a legenda tem que contar a regra viva — COND-8): {culpados}")


# ---------------------------------------------------------------------------
# E2 · CA-02 — a rede de erro do exe (console=False engolia tudo)
# ---------------------------------------------------------------------------


def test_e2_rede_de_erros_grava_traceback_em_logs(raiz_tmp):
    """E2 (CA-02): com console=False, sys.excepthook default e todo
    traceback.print_exc() viram NO-OP no exe — erro fatal morria mudo.
    A rede grava o traceback INTEIRO em logs/erros.log (molde do vigia:
    append tolerante, nunca levanta)."""
    import sys
    from app.core import erros
    erros.instalar_rede_de_erros()
    try:
        try:
            raise ZeroDivisionError("bum de bancada")
        except ZeroDivisionError:
            sys.excepthook(*sys.exc_info())
    finally:
        sys.excepthook = sys.__excepthook__
    log = raiz_tmp.raiz / "logs" / "erros.log"
    assert log.exists(), "a rede não gravou NADA (CA-02)"
    texto = log.read_text(encoding="utf-8", errors="replace")
    assert "ZeroDivisionError" in texto and "bum de bancada" in texto


def test_e2_diagnostico_de_suporte_leva_os_erros(raiz_tmp, tmp_path):
    """E2: o zip 'diagnóstico para suporte' tinha 3 arquivos e NENHUM
    traceback (só travamentos.log). Agora leva erros.log e cofre.log."""
    import zipfile
    (raiz_tmp.raiz / "logs").mkdir(exist_ok=True)
    (raiz_tmp.raiz / "logs" / "erros.log").write_text(
        "RASTRO-XYZ", encoding="utf-8")
    (raiz_tmp.raiz / "logs" / "cofre.log").write_text(
        "COFRE-ABC", encoding="utf-8")
    from app.core.diagnostico import gerar_diagnostico
    z = gerar_diagnostico(tmp_path / "diag.zip")
    with zipfile.ZipFile(z) as f:
        nomes = set(f.namelist())
        assert "erros.log" in nomes, (
            "o diagnóstico de suporte sai SEM os erros — o suporte recebe "
            "um zip cego (CA-02)")
        assert "cofre.log" in nomes
        assert b"RASTRO-XYZ" in f.read("erros.log")


# ---------------------------------------------------------------------------
# E3 · CA-03 — pasta sem escrita não mata o boot antes da janela
# ---------------------------------------------------------------------------


def test_e3_criar_estrutura_prova_a_escrita(tmp_path, monkeypatch):
    """E3 (CA-03): criar_estrutura só fazia mkdir — pasta que aceita
    diretório mas NEGA arquivo (ACL/OneDrive) passava aqui e morria
    DEPOIS, no meio do boot, sem janela. A prova de escrita acontece já
    na estrutura, com erro NOMINAL em PT-BR."""
    from pathlib import Path as _P
    from app.core.paths import SystemRoot
    original = _P.write_text

    def _nega(self, *a, **k):
        if self.name == ".escrita_ok":
            raise PermissionError("ACL de bancada")
        return original(self, *a, **k)

    monkeypatch.setattr(_P, "write_text", _nega)
    with pytest.raises(OSError) as exc:
        SystemRoot(tmp_path / "raiz_e3").criar_estrutura()
    assert "escrita" in str(exc.value).lower() or \
           "permiss" in str(exc.value).lower()


def test_e3_fase_nua_do_boot_morre_contando_nunca_muda(raiz_tmp, monkeypatch):
    """E3: a fase 1 do boot (_montar_shell) era NUA — sqlite3.
    OperationalError (pasta sem escrita) matava o processo ANTES do
    show(), sem caixa e sem log. O embrulho conta: caixa crítica legível
    + traceback em logs/erros.log."""
    import sqlite3
    from app import editor_app
    from app.tests.gestos import vigia_dialogo
    _app()

    def _boom(_holder):
        raise sqlite3.OperationalError("unable to open database file")

    monkeypatch.setattr(editor_app, "_montar_shell", _boom)
    with vigia_dialogo("OK") as v:
        shell = editor_app._montar_shell_seguro({})
    assert shell is None
    assert v.disparou, "a fase nua morreu MUDA — sem caixa (CA-03)"
    log = raiz_tmp.raiz / "logs" / "erros.log"
    assert log.exists() and "OperationalError" in log.read_text(
        encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# E7+E9 · D-11/D-10 — versão de schema, backup ANTES de migrar, índices
# ---------------------------------------------------------------------------


def test_e7_migracao_tem_versao_backup_antes_e_indices(tmp_path, monkeypatch):
    """E7 (D-11): não havia versão de schema nem backup pré-migração — e
    no entrypoint real o ALTER rodava ANTES do snapshot do boot (a ordem
    invertida que o scout achou). Com o backup DENTRO do init, a ordem
    fica certa por construção. E9 (D-10): o migrador aprende CREATE
    INDEX (create_all pula tabela existente — índice novo nunca chegava
    a banco antigo)."""
    import sqlite3
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    # um banco ANTIGO de verdade: produtos sem as colunas novas
    con = sqlite3.connect(root.caminho_banco)
    con.execute("CREATE TABLE produtos (id INTEGER PRIMARY KEY, "
                "nome_bruto TEXT)")
    con.execute("INSERT INTO produtos (nome_bruto) VALUES ('ARROZ')")
    con.commit()
    con.close()

    from app.core.database import Database
    Database(root).init().engine.dispose()

    con = sqlite3.connect(root.caminho_banco)
    uv = con.execute("PRAGMA user_version").fetchone()[0]
    cols = [r[1] for r in con.execute("PRAGMA table_info(produtos)")]
    idx_prod = [r[1] for r in con.execute("PRAGMA index_list('produtos')")]
    idx_lay = [r[1] for r in con.execute("PRAGMA index_list('layouts')")]
    idx_proj = [r[1] for r in
                con.execute("PRAGMA index_list('projetos_salvos')")]
    con.close()

    assert "categoria_origem" in cols          # a migração aconteceu
    assert uv >= 1, "não há VERSÃO de schema no banco (D-11)"
    pre = list((root.raiz / "backups").glob("pre_migracao_*.db"))
    assert pre, "migrou SEM backup antes (D-11/P7)"
    con = sqlite3.connect(pre[0])
    cols_backup = [r[1] for r in con.execute("PRAGMA table_info(produtos)")]
    con.close()
    assert "categoria_origem" not in cols_backup, (
        "o backup foi tirado DEPOIS do ALTER — não protege nada")
    # E9: os índices chegam TAMBÉM ao banco antigo
    assert any("excluido" in i for i in idx_prod), (
        "produtos.excluido_em sem índice (D-10)")
    assert any("excluido" in i for i in idx_lay)
    assert any("nome" in i for i in idx_lay), "Layout.nome sem índice"
    assert any("excluido" in i for i in idx_proj)


# ---------------------------------------------------------------------------
# E8 · D-12 — as conexões fora do hook ganham o PRAGMA
# ---------------------------------------------------------------------------


def test_e8_sessao_do_pacote_liga_foreign_keys(tmp_path):
    """E8 (D-12): o engine do pacote (.atpkg) nasce por create_engine
    direto, fora do hook do PRAGMA — sem foreign_keys=ON, a mesclagem
    roda sem a rede de FK que o banco vivo tem."""
    import sqlite3
    from sqlalchemy import text
    from app.core import portabilidade
    banco = tmp_path / "pacote.db"
    sqlite3.connect(banco).close()
    eng, fabrica_sessao = portabilidade._sessao_pacote(banco)
    try:
        with fabrica_sessao() as s:
            fk = s.execute(text("PRAGMA foreign_keys")).scalar()
    finally:
        eng.dispose()
    assert fk == 1, ("a sessão do pacote não liga foreign_keys — a "
                     "mesclagem corre sem a rede (D-12)")


# ---------------------------------------------------------------------------
# E4 · CB-02 — Cofre e .atpkg respeitam o somente-leitura
# ---------------------------------------------------------------------------


def test_e4_cofre_e_atpkg_respeitam_o_somente_leitura(raiz_tmp):
    """E4 (CB-02): no PC da loja (somente leitura) o Cofre criava/
    restaurava/apagava snapshots e o .atpkg APLICAVA mesclagem no banco
    vivo — nenhum dos dois passava por exigir_escrita(). E o snapshot do
    boot tem de PULAR sem drama (o boot da loja não pode morrer)."""
    from app.core import cofre, modo, portabilidade
    modo.definir_somente_leitura(True)
    try:
        with pytest.raises(modo.SomenteLeitura):
            cofre.criar_snapshot("manual")
        with pytest.raises(modo.SomenteLeitura):
            cofre.excluir_snapshot("qualquer.db")
        with pytest.raises(modo.SomenteLeitura):
            cofre.restaurar_snapshot("qualquer.db")
        with pytest.raises(modo.SomenteLeitura):
            portabilidade.aplicar_importacao(None, None)
        assert cofre.snapshot_automatico() is None      # pula SEM levantar
        assert not list((raiz_tmp.raiz / "backups").glob("*.db")), (
            "o snapshot do boot ESCREVEU no PC somente-leitura")
    finally:
        modo.definir_somente_leitura(False)


# ---------------------------------------------------------------------------
# E6 · D-02 — o gêmeo do migrador para Produto.caminho_imagem
# ---------------------------------------------------------------------------


def test_e6_fotos_com_caminho_absoluto_migram_com_aviso(raiz_tmp, tmp_path):
    """E6 (D-02): linha legada com caminho ABSOLUTO ficava assim para
    sempre — os leitores toleram e mascaram (quebra em outra máquina sem
    uma palavra). O gêmeo de migrar_artes_absolutas: dentro→relativo,
    fora-mas-viva→copia, sumida→aviso com rastro."""
    from PIL import Image
    from app.core.database import Database
    from app.core.repositories import ProdutoRepositorio
    from app.images.biblioteca import BibliotecaImagens

    solta = tmp_path / "fora" / "foto_solta.png"
    solta.parent.mkdir()
    Image.new("RGB", (60, 60), (10, 200, 10)).save(solta)

    db = Database().init()
    with db.Session() as s:
        repo = ProdutoRepositorio(s)
        p1 = repo.importar("ARROZ COM FOTO SOLTA").produto
        p1.caminho_imagem = str(solta)                      # ABSOLUTO, fora
        p2 = repo.importar("FEIJAO FOTO SUMIDA").produto
        p2.caminho_imagem = str(tmp_path / "nao_existe.png")
        s.commit()
        avisos = BibliotecaImagens.migrar_produtos_absolutos(s)
        s.commit()
        p1_id, p2_id = p1.id, p2.id
    db.engine.dispose()

    assert len(avisos) == 2 and any("copiada" in a for a in avisos) \
        and any("não está no disco" in a for a in avisos)
    db = Database().init()
    with db.Session() as s:
        prods = {p.id: p for p in ProdutoRepositorio(s).listar(limit=10)}
        assert prods[p1_id].caminho_imagem == f"{p1_id}/atual.png"
        assert (raiz_tmp.biblioteca_imagens / str(p1_id) /
                "atual.png").exists()
        assert prods[p2_id].caminho_imagem.endswith("nao_existe.png")
    db.engine.dispose()


# ---------------------------------------------------------------------------
# E1 · CA-01 — o boot não baixa 973 MB sem pedir
# ---------------------------------------------------------------------------


def test_e1_aquecer_nao_baixa_modelo_ausente(raiz_tmp, monkeypatch,
                                             tmp_path):
    """E1 (CA-01): o aquecedor do boot chamava new_session INCONDICIONAL
    — e o rembg BAIXA dentro do construtor (973 MB, sem pergunta, com o
    progresso indo para o stderr morto do exe). Aquecer vira no-op
    quando o .onnx não está no disco (o molde do ESRGAN)."""
    import sys
    import types
    chamadas = []
    fake = types.ModuleType("rembg")
    fake.new_session = lambda m: chamadas.append(m) or object()
    monkeypatch.setitem(sys.modules, "rembg", fake)
    monkeypatch.setenv("U2NET_HOME", str(tmp_path / "modelos"))
    from app.images import fundo
    monkeypatch.setattr(fundo, "_sessoes", {}, raising=False)

    fundo.aquecer("birefnet-general")
    assert chamadas == [], (
        "o boot CARREGOU/BAIXOU o modelo sem o arquivo no disco e sem "
        "perguntar (CA-01)")

    pasta = tmp_path / "modelos"
    pasta.mkdir(exist_ok=True)
    (pasta / "birefnet-general.onnx").write_bytes(b"x")
    fundo.aquecer("birefnet-general")
    assert chamadas == ["birefnet-general"], (
        "com o modelo NO DISCO o aquecer tinha que aquecer")


def test_e1_primeiro_recorte_pergunta_com_opcao_leve(raiz_tmp, monkeypatch,
                                                     tmp_path):
    """E1: a pergunta no 1º uso REAL — 3 saídas (baixar o completo /
    usar o leve / agora não), gravando a escolha leve na MESMA chave da
    Config que o combo das Configurações usa."""
    from app.qt.telas import servico
    _app()
    monkeypatch.setenv("U2NET_HOME", str(tmp_path / "m"))
    with vigia_dialogo("Agora não") as v:
        ok = servico.garantir_modelo_recorte(None)
    assert v.disparou, "ninguém perguntou nada (CA-01)"
    assert ok is False

    with vigia_dialogo("Usar o leve (~5 MB)") as v2:
        ok2 = servico.garantir_modelo_recorte(None)
    assert v2.disparou and ok2 is True
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio
    db = Database().init()
    with db.Session() as s:
        assert ConfigRepositorio(s).get("imagem.modelo_rembg") == "u2netp"
    db.engine.dispose()
