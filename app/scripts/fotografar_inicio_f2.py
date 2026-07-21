"""
Fotos do Início novo (FASE 2, passo 30)
=======================================
6 capturas: {0 eventos (hero), 1 evento (com "Produzir hoje"), 4+ eventos
(acervo REAL, intocado)} × {claro, escuro} em ``saida_fase2/``.

Os estados 0 e 1 usam raiz TEMPORÁRIA (env AUTOTABLOIDE_ROOT); o 4+ usa a
raiz real SÓ EM LEITURA (nenhuma escrita além da migração idempotente).

Rodar::

    python -m app.scripts.fotografar_inicio_f2
"""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import date
from pathlib import Path


def _foto(dash, nome: str) -> None:
    from PySide6.QtWidgets import QApplication
    for _ in range(6):
        QApplication.processEvents()
    dash.grab().save(f"saida_fase2/{nome}")
    print(f"  {nome}")


def _dash(tamanho=(1440, 860)):
    from PySide6.QtCore import Qt

    from app.qt.telas.dashboard import DashboardTela
    d = DashboardTela()
    d.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    d.resize(*tamanho)
    d.show()
    return d


def _semear_estado_1() -> None:
    """1 evento COM o dia de hoje (o 'Produzir hoje' aparece) + 1 projeto."""
    from app.core import projetos
    from app.core.database import Database
    from app.qt.telas.eventos import criar_evento
    from app.qt.telas.servico import ItemMesa
    from app.rendering.model import (
        LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao)

    db = Database().init()
    try:
        with db.Session() as s:
            criar_evento(s, "Quintou", dia_semana=date.today().weekday())
            s.commit()
    finally:
        db.engine.dispose()
    layout = LayoutDef(100, 100, dpi=100, paginas=[Pagina([
        Slot("s", [Regiao(TipoRegiao.NOME, Retangulo(10, 10, 60, 12))])])])
    item = ItemMesa(descricao="X", preco="9,99", semaforo="VERDE",
                    nome="Produto Exemplo")
    projetos.salvar_projeto("Quintou 18/07", "Quintou", "TABLOIDE",
                            layout, [item.to_dict()])


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from PySide6.QtWidgets import QApplication

    from app.qt.design.tema import aplicar_tema

    Path("saida_fase2").mkdir(exist_ok=True)
    app = QApplication.instance() or QApplication([])
    raiz_real = os.environ.pop("AUTOTABLOIDE_ROOT", None)

    with tempfile.TemporaryDirectory() as tmp0, \
            tempfile.TemporaryDirectory() as tmp1:
        # --- estado 0: hero -------------------------------------------------
        os.environ["AUTOTABLOIDE_ROOT"] = str(Path(tmp0) / "raiz")
        from app.core.database import Database
        from app.core.paths import SystemRoot
        Database(SystemRoot(Path(tmp0) / "raiz").criar_estrutura()
                 ).init().engine.dispose()
        for tema in ("claro", "escuro"):
            aplicar_tema(app, tema)
            d = _dash()
            _foto(d, f"inicio_0_eventos_{tema}.png")
            d.close()

        # --- estado 1: Produzir hoje ---------------------------------------
        os.environ["AUTOTABLOIDE_ROOT"] = str(Path(tmp1) / "raiz")
        Database(SystemRoot(Path(tmp1) / "raiz").criar_estrutura()
                 ).init().engine.dispose()
        _semear_estado_1()
        for tema in ("claro", "escuro"):
            aplicar_tema(app, tema)
            d = _dash()
            _foto(d, f"inicio_1_evento_hoje_{tema}.png")
            d.close()

    # --- estado 4+: 4 eventos sintéticos (a letra do passo 30) -------------
    with tempfile.TemporaryDirectory() as tmp4:
        os.environ["AUTOTABLOIDE_ROOT"] = str(Path(tmp4) / "raiz")
        from app.core.database import Database as _Db
        from app.core.paths import SystemRoot as _SR
        _Db(_SR(Path(tmp4) / "raiz").criar_estrutura()
            ).init().engine.dispose()
        _semear_estado_4()
        for tema in ("claro", "escuro"):
            aplicar_tema(app, tema)
            d = _dash()
            _foto(d, f"inicio_4mais_eventos_{tema}.png")
            d.close()

    # --- bônus: o acervo REAL (leitura), como evidência viva ---------------
    if raiz_real is not None:
        os.environ["AUTOTABLOIDE_ROOT"] = raiz_real
    else:
        os.environ.pop("AUTOTABLOIDE_ROOT", None)
    for tema in ("claro", "escuro"):
        aplicar_tema(app, tema)
        d = _dash()
        _foto(d, f"inicio_acervo_real_{tema}.png")
        d.close()
    aplicar_tema(app, "claro")
    return 0


def _semear_estado_4() -> None:
    """4 eventos com dias/cores variados + 5 projetos (grade responsiva)."""
    from app.core import projetos
    from app.core.database import Database
    from app.qt.telas.eventos import criar_evento
    from app.qt.telas.servico import ItemMesa
    from app.rendering.model import (
        LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao)

    hoje = date.today().weekday()
    db = Database().init()
    try:
        with db.Session() as s:
            criar_evento(s, "Quintou", dia_semana=3)
            criar_evento(s, "Sexta Verde", dia_semana=4)
            criar_evento(s, "Terça do Pão", dia_semana=1)
            criar_evento(s, "Fim de Semana", dia_semana=(hoje + 1) % 7)
            s.commit()
    finally:
        db.engine.dispose()
    layout = LayoutDef(100, 100, dpi=100, paginas=[Pagina([
        Slot("s", [Regiao(TipoRegiao.NOME, Retangulo(10, 10, 60, 12))])])])
    item = ItemMesa(descricao="X", preco="9,99", semaforo="VERDE",
                    nome="Produto Exemplo")
    for nome, evento in [("Quintou 10/07", "Quintou"),
                         ("Quintou 17/07", "Quintou"),
                         ("Sexta Verde 11/07", "Sexta Verde"),
                         ("Terça 15/07", "Terça do Pão"),
                         ("Avulso 01", None)]:
        projetos.salvar_projeto(nome, evento, "TABLOIDE", layout,
                                [item.to_dict()])


if __name__ == "__main__":
    raise SystemExit(main())
