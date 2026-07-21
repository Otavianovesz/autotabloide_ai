"""
FASE 12 — Confiabilidade, MARCO FINAL e entrega (testes por conteúdo)
=====================================================================
Bloco A: recuperação de corrompido (R-137), somente-leitura (R-131),
.atproj (R-136), verificar atualização (R-127), integridade na abertura
(R-138). Tudo mutation-proof: cada teste confere por VALOR/byte — reverter
o conserto correspondente derruba o teste.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from app.tests import seeds_portabilidade as seeds


@pytest.fixture()
def raiz_env(tmp_path, monkeypatch):
    root = seeds.raiz(tmp_path, "raiz")
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(root.raiz))
    return root


def _app():
    return QApplication.instance() or QApplication([])


def _layout_simples():
    from app.rendering.model import (
        LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao)
    return LayoutDef(100, 100, dpi=96, paginas=[Pagina([
        Slot("s", [Regiao(TipoRegiao.NOME, Retangulo(5, 5, 40, 10))])])])


def _salvar(nome: str, preco: str = "1,00") -> int:
    from app.core import projetos
    from app.qt.telas.servico import ItemMesa
    it = ItemMesa("X", preco, "VERDE", nome)
    return projetos.salvar_projeto(nome, None, "TABLOIDE", _layout_simples(),
                                   [it.to_dict()])


# ============================================================================
# Bloco A — robustez final
# ============================================================================

def test_a_recuperacao_restaura_do_snapshot_bom(raiz_env):
    """R-137 (passos 1-3, 11, 14): projeto CORROMPIDO de propósito →
    diagnóstico em PT-BR (sem stack trace), snapshot bom listado com prévia,
    restauração POR CONTEÚDO (o item volta) e o lixo guardado num .bak."""
    from app.core import projetos, recuperacao
    from app.core.database import Database
    from app.core.models import ProjetoSalvo
    from app.core.projetos import _pasta
    pid = _salvar("Oferta boa", "9,90")
    # salvar por cima cria a VERSÃO do estado anterior (F2)
    from app.qt.telas.servico import ItemMesa
    it2 = ItemMesa("X", "8,88", "VERDE", "Oferta boa v2")
    projetos.salvar_projeto("Oferta boa", None, "TABLOIDE",
                            _layout_simples(), [it2.to_dict()],
                            projeto_id=pid)
    assert projetos.listar_versoes(pid)          # há snapshot bom

    db = Database().init()                       # corrompe DE PROPÓSITO
    try:
        with db.Session() as s:
            row = s.get(ProjetoSalvo, pid)
            uuid = row.uuid
            row.estado_slots = '{"layout": QUEBRADO'
            s.commit()
    finally:
        db.engine.dispose()

    with pytest.raises(Exception):
        projetos.abrir_projeto(pid)              # o quebrado NÃO abre

    problemas = recuperacao.diagnosticar_projeto(pid)
    assert any("ilegíve" in p for p in problemas)     # PT-BR, não traceback
    assert not any("Traceback" in p for p in problemas)

    sns = recuperacao.snapshots_de_recuperacao(pid)
    assert sns and sns[0]["origem"] == "versão"
    assert sns[0]["itens"] == 1                  # a prévia diz o conteúdo

    assert recuperacao.restaurar_de_snapshot(pid, sns[0])
    p = projetos.abrir_projeto(pid)              # agora ABRE
    assert p is not None
    assert p.itens[0]["nome"] == "Oferta boa"    # o conteúdo do snapshot BOM
    baks = list(_pasta(uuid).glob("corrompido_*.bak.json"))
    assert baks                                  # reversível: o lixo guardado
    assert "QUEBRADO" in baks[0].read_text(encoding="utf-8")
    log = Path(raiz_env.logs) / "recuperacoes.log"
    assert log.exists() and "restaurado" in log.read_text(encoding="utf-8")


def test_a_recuperacao_usa_o_rascunho_do_projeto_certo(raiz_env):
    """R-137: o rascunho automático só entra como candidato se é DESTE
    projeto (por id, I1) — o rascunho de outro projeto nunca vaza."""
    from app.core import rascunho, recuperacao
    pid = _salvar("Meu projeto")
    outro = _salvar("Outro projeto")
    estado = {"projeto_id": outro, "layout": _layout_simples().to_dict(),
              "itens": [], "mapa": {}, "overrides": {}}
    rascunho.salvar_rascunho(estado)
    origens = [s["origem"] for s in
               recuperacao.snapshots_de_recuperacao(pid)]
    assert "rascunho" not in origens             # o rascunho é do OUTRO
    origens2 = [s["origem"] for s in
                recuperacao.snapshots_de_recuperacao(outro)]
    assert "rascunho" in origens2                # no dono certo, entra


def test_a_atproj_roundtrip_identico(raiz_env, tmp_path):
    """R-136 (passos 6-7, 15): exportar → importar recria o projeto com os
    DADOS byte a byte e as fotos por caminho RELATIVO (arquivo copiado
    idêntico)."""
    from app.core import atproj, projetos
    from app.core.database import Database
    from app.core.models import ProjetoSalvo
    from app.core.projetos import _pasta
    from app.qt.telas.servico import ItemMesa
    foto = tmp_path / "foto.png"
    foto.write_bytes(seeds.png("#AA3311"))
    it = ItemMesa("X", "7,77", "VERDE", "Produto com foto",
                  imagem=str(foto))
    pid = projetos.salvar_projeto("Viajante", "Quintou", "TABLOIDE",
                                  _layout_simples(), [it.to_dict()])

    pacote = atproj.exportar_atproj(pid, tmp_path / "viagem")
    assert pacote.suffix == ".atproj"
    m = atproj.ler_manifesto(pacote)
    assert m["nome"] == "Viajante" and m["itens"] == 1    # a prévia fala

    novo = atproj.importar_atproj(pacote)
    assert novo != pid                           # cópia, nunca colisão (I1)
    db = Database().init()
    try:
        with db.Session() as s:
            original = s.get(ProjetoSalvo, pid)
            copia = s.get(ProjetoSalvo, novo)
            assert copia.estado_slots == original.estado_slots   # BYTE a byte
            assert copia.uuid != original.uuid
            rel = json.loads(copia.estado_slots)["itens"][0]["imagem"]
            assert not Path(rel).is_absolute()               # relativo (I3)
            f_orig = _pasta(original.uuid) / rel
            f_novo = _pasta(copia.uuid) / rel
            assert f_novo.exists()
            assert f_novo.read_bytes() == f_orig.read_bytes()  # foto idêntica
    finally:
        db.engine.dispose()
    p = projetos.abrir_projeto(novo)             # e ABRE de verdade
    assert p is not None and p.itens[0]["nome"] == "Produto com foto"


def test_a_somente_leitura_barra_e_reverte(raiz_env):
    """R-131 (passos 4-5, 16): ligado, as portas de ESCRITA levantam a
    mensagem PT-BR e o banco fica intacto; aprovar segue livre; desligar
    devolve a edição."""
    from app.core import modo, projetos
    from app.qt.telas import servico
    pid_prod = seeds.add_produto(raiz_env, "Arroz 5kg", "Camil", "24.90")
    pid_proj = _salvar("Aprovável")
    modo.definir_somente_leitura(True)
    try:
        assert modo.somente_leitura()
        with pytest.raises(modo.SomenteLeitura) as exc:
            servico.editar_produto(pid_prod, nome_sanitizado="Hackeado")
        assert "somente-leitura" in str(exc.value).lower()
        d = seeds.produto_por_chave(raiz_env, "Arroz 5kg", "Camil")
        assert d is not None                     # o banco NÃO mudou
        with pytest.raises(modo.SomenteLeitura):
            _salvar("Não pode")
        with pytest.raises(modo.SomenteLeitura):
            servico.excluir_produtos([pid_prod])
        # aprovar e exportar são o PROPÓSITO do modo — seguem livres
        projetos.aprovar(pid_proj)
        assert projetos.esta_aprovado(pid_proj)
    finally:
        modo.definir_somente_leitura(False)
    novo = servico.editar_produto(pid_prod, nome_sanitizado="Arroz Novo 5kg")
    assert novo["nome"] == "Arroz Novo 5kg"      # a edição voltou


def test_a_verificar_atualizacao_honesto(raiz_env, monkeypatch):
    """R-127 (passos 8-9, 17): sem URL → mensagem honesta; rede caída →
    degrada SEM travar nem mentir; com versão nova → novidades em PT-BR."""
    from app.core import atualizacao
    r = atualizacao.verificar_atualizacao()      # sem URL configurada
    assert r["disponivel"] is False
    assert "offline" in r["mensagem"]

    import requests

    def _cai(*a, **k):
        raise requests.ConnectionError("sem rede")
    monkeypatch.setattr(requests, "get", _cai)
    r2 = atualizacao.verificar_atualizacao("http://exemplo.local/v.json")
    assert r2["disponivel"] is False
    assert "app segue normal" in r2["mensagem"]  # honesto, não trava

    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"versao": "1.1",
                    "novidades": ["Etiquetas em lote", "Modo Pai"]}
    monkeypatch.setattr(requests, "get", lambda *a, **k: _Resp())
    r3 = atualizacao.verificar_atualizacao("http://exemplo.local/v.json")
    assert r3["disponivel"] is True and r3["versao"] == "1.1"
    assert "Modo Pai" in r3["mensagem"]


def test_a_verificar_ao_abrir_acusa_foto_sumida(raiz_env):
    """R-138 (passo 10): a checagem da abertura passa no PRAGMA e ACUSA o
    cadastro que aponta para foto sumida — aviso, nunca crash."""
    from app.core.database import Database
    from app.core.models import Produto
    from app.core.recuperacao import verificar_ao_abrir
    pid = seeds.add_produto(raiz_env, "Sem foto real", None, "1.00")
    db = Database(raiz_env).init()
    try:
        with db.Session() as s:
            s.get(Produto, pid).caminho_imagem = f"{pid}/sumida.png"
            s.commit()
    finally:
        db.engine.dispose()
    r = verificar_ao_abrir(raiz_env)
    assert r["banco_ok"] is True                 # o PRAGMA responde ok
    assert r["sem_arquivo"] == 1                 # e a foto sumida é ACUSADA
    assert any("sumiu" in a for a in r["avisos"])
