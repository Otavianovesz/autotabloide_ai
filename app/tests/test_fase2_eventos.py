"""FASE 2, Bloco A (passos 11-13) — o Evento como entidade, sem perder nada."""

from pathlib import Path

import pytest

from app.qt.telas.servico import ItemMesa
from app.rendering.model import LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.database import Database
    from app.core.paths import SystemRoot

    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    Database(root).init().engine.dispose()
    return root


def _layout() -> LayoutDef:
    return LayoutDef(100, 100, dpi=100, paginas=[Pagina([
        Slot("s", [Regiao(TipoRegiao.NOME, Retangulo(10, 10, 30, 10))])])])


def _salvar(nome: str, evento: str | None) -> int:
    from app.core import projetos
    item = ItemMesa(descricao="X", preco="1,00", semaforo="VERDE",
                    nome="Produto X")
    return projetos.salvar_projeto(nome, evento, "TABLOIDE", _layout(),
                                   [item.to_dict()])


def test_migracao_3_eventos_texto_viram_entidades(raiz_tmp):
    """Passo 11: eventos-texto distintos → Eventos com projetos LIGADOS."""
    from app.core.database import Database
    from app.core.models import Evento, ProjetoSalvo
    from app.qt.telas.eventos import migrar_eventos_texto

    _salvar("P1", "Quintou")
    _salvar("P2", "Quintou")
    _salvar("P3", "Sexta Verde")
    _salvar("P4", "Terça do Pão")
    db = Database().init()
    try:
        # simula banco LEGADO: zera os ids que o salvar novo já preencheu
        with db.Session() as s:
            for p in s.query(ProjetoSalvo).all():
                p.evento_id = None
            s.query(Evento).delete()
            s.commit()
        with db.Session() as s:
            criados = migrar_eventos_texto(s)
            s.commit()
        with db.Session() as s:
            eventos = {e.nome: e for e in s.query(Evento).all()}
            assert criados == 3 and len(eventos) == 3
            # TODO projeto ligado ao Evento certo (por conteúdo, não posição)
            for p in s.query(ProjetoSalvo).all():
                assert p.evento_id == eventos[p.evento].id
            # cor estável por hash: migrar de novo não muda nada
            cores = {e.nome: e.cor for e in eventos.values()}
            assert migrar_eventos_texto(s) == 0        # idempotente
            for e in s.query(Evento).all():
                assert e.cor == cores[e.nome]
    finally:
        db.engine.dispose()


def test_excluir_movendo_preserva_projetos(raiz_tmp):
    """Passo 12: excluir com destino move TODOS; nunca órfão silencioso."""
    from app.core.database import Database
    from app.core.models import Evento, ProjetoSalvo
    from app.qt.telas.eventos import excluir_evento, listar_eventos

    _salvar("P1", "Quintou")
    _salvar("P2", "Quintou")
    _salvar("P3", "Sexta Verde")
    db = Database().init()
    try:
        with db.Session() as s:
            evs = {e["nome"]: e for e in listar_eventos(s)}
            with pytest.raises(ValueError):
                excluir_evento(s, evs["Quintou"]["id"])   # cheio, sem destino
            excluir_evento(s, evs["Quintou"]["id"],
                           mover_para=evs["Sexta Verde"]["id"])
            s.commit()
        with db.Session() as s:
            assert s.query(Evento).filter_by(nome="Quintou").first() is None
            movidos = s.query(ProjetoSalvo).filter_by(
                evento_id=evs["Sexta Verde"]["id"]).all()
            assert {p.nome for p in movidos} == {"P1", "P2", "P3"}
            assert all(p.evento == "Sexta Verde" for p in movidos)
    finally:
        db.engine.dispose()


def test_capa_internada_relativa(raiz_tmp, tmp_path):
    """Passo 13: capa copiada para layouts/capas; banco SÓ relativo (I3)."""
    from app.core.database import Database
    from app.core.models import Evento
    from app.qt.telas.eventos import caminho_capa, criar_evento, definir_capa

    origem = tmp_path / "minha_capa.png"
    from PIL import Image
    Image.new("RGB", (40, 40), "#FF0000").save(origem)
    db = Database().init()
    try:
        with db.Session() as s:
            ev = criar_evento(s, "Quintou")
            definir_capa(s, ev.id, str(origem))
            s.commit()
            capa = s.get(Evento, ev.id).capa
            assert capa == f"capas/evento_{ev.id}.png"   # relativa, nunca C:\
            assert ":" not in capa and "\\" not in capa
            resolvida = caminho_capa(capa)
            assert resolvida is not None and resolvida.exists()
            assert resolvida.read_bytes() == origem.read_bytes()
            assert str(raiz_tmp.layouts) in str(resolvida)
    finally:
        db.engine.dispose()
