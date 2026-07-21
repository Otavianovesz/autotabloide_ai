"""
Atalhos do teclado — o catálogo central (R-018, FASE 3 passos 53-55)
====================================================================
Antes, cada tela declarava suas teclas em listas soltas ("Ctrl+S" em três
lugares). Agora TODO atalho editável nasce daqui:

- ``CATALOGO``  — id → (grupo, o que faz, tecla padrão);
- ``sequencia(id)`` — a tecla EFETIVA (a customizada da Config, senão a padrão);
- ``criar_atalho(id, dono, slot)`` — o QShortcut já com a tecla efetiva,
  registrado num vivário: remapear na tela de Configurações APLICA NA HORA
  nos atalhos vivos (setKey), sem reiniciar;
- ``aplicar(id, seq)`` / ``restaurar_padrao()`` — usados pela aba Atalhos.

Persistência: Config ``atalhos.custom`` = {id: "Ctrl+X"} (só os diferentes
do padrão). Conflito (mesma tecla no MESMO grupo, ou cruzando com "Geral")
é BARRADO na tela — dois donos da mesma tecla no Qt = nenhum dispara
(lição do Ctrl+K da Fase 2).
"""

from __future__ import annotations

import weakref

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut

# id: (grupo, descrição, tecla padrão)
CATALOGO: dict[str, tuple[str, str, str]] = {
    "geral.busca":       ("Geral", "Busca global (projeto, produto, layout)",
                          "Ctrl+K"),
    "geral.abas_config": ("Geral", "Circular as abas das Configurações",
                          "Ctrl+Tab"),
    "mesa.desfazer":     ("Mesa", "Desfazer", "Ctrl+Z"),
    "mesa.refazer":      ("Mesa", "Refazer", "Ctrl+Y"),
    "mesa.exportar":     ("Mesa", "Exportar (PNG/PDF)", "Ctrl+E"),
    "mesa.salvar":       ("Mesa", "Salvar projeto", "Ctrl+S"),
    "mesa.abrir":        ("Mesa", "Abrir projeto", "Ctrl+O"),
    "editor.desfazer":   ("Ateliê", "Desfazer", "Ctrl+Z"),
    "editor.refazer":    ("Ateliê", "Refazer", "Ctrl+Shift+Z"),
    "editor.zoom_menos": ("Ateliê", "Diminuir zoom", "Ctrl+-"),
    "editor.zoom_mais":  ("Ateliê", "Aumentar zoom", "Ctrl+="),
    "editor.ajustar":    ("Ateliê", "Ajustar à tela", "Ctrl+0"),
    "editor.duplicar":   ("Ateliê", "Duplicar região", "Ctrl+D"),
    "editor.excluir":    ("Ateliê", "Excluir região", "Del"),
    "editor.copiar":     ("Ateliê", "Copiar região", "Ctrl+C"),
    "editor.colar":      ("Ateliê", "Colar região", "Ctrl+V"),
    "editor.paleta":     ("Ateliê", "Paleta de comandos", "Ctrl+Shift+P"),
    "editor.salvar":     ("Ateliê", "Salvar layout", "Ctrl+S"),
    "editor.abrir":      ("Ateliê", "Abrir layout do banco", "Ctrl+O"),
}

# customizações vivas em memória (espelho da Config; None = ainda não lidas)
_CUSTOM: dict[str, str] | None = None

# vivário: id → QShortcuts vivos (weakref — widget morto sai sozinho)
_VIVOS: dict[str, list] = {}


def _customizados() -> dict[str, str]:
    """Lê ``atalhos.custom`` UMA vez por processo (cache; ver recarregar)."""
    global _CUSTOM
    if _CUSTOM is None:
        _CUSTOM = {}
        try:
            from app.core.database import Database
            from app.core.repositories import ConfigRepositorio
            db = Database().init()
            try:
                with db.Session() as s:
                    bruto = ConfigRepositorio(s).get("atalhos.custom") or {}
            finally:
                db.engine.dispose()
            _CUSTOM = {k: str(v) for k, v in bruto.items()
                       if k in CATALOGO and str(v).strip()}
        except Exception:
            _CUSTOM = {}                 # config quebrada = padrões (C3)
    return _CUSTOM


def recarregar_atalhos() -> None:
    """Esquece o cache (a aba Atalhos chama após persistir)."""
    global _CUSTOM
    _CUSTOM = None


def sequencia(id_: str) -> str:
    """A tecla EFETIVA do atalho (customizada > padrão)."""
    padrao = CATALOGO.get(id_, ("", "", ""))[2]
    return _customizados().get(id_, padrao)


def criar_atalho(id_: str, dono, slot,
                 contexto=Qt.ShortcutContext.WidgetWithChildrenShortcut,
                 ) -> QShortcut:
    """QShortcut com a tecla efetiva, registrado no vivário: um remap na
    aba Atalhos troca a tecla DESTE atalho na hora (passo 55/59)."""
    sc = QShortcut(QKeySequence(sequencia(id_)), dono)
    sc.setContext(contexto)
    sc.activated.connect(slot)
    _VIVOS.setdefault(id_, []).append(weakref.ref(sc))
    return sc


def _repor_vivos(id_: str, seq: str) -> None:
    import shiboken6
    vivos = []
    for ref in _VIVOS.get(id_, []):
        sc = ref()
        if sc is not None and shiboken6.isValid(sc):
            sc.setKey(QKeySequence(seq))
            vivos.append(ref)
    _VIVOS[id_] = vivos


def conflito(id_: str, seq: str) -> str | None:
    """Outro atalho que JÁ usa a tecla ``seq`` no mesmo escopo (mesmo
    grupo, ou cruzando com "Geral" — que vale em toda parte). Devolve a
    descrição do dono do conflito, ou None se a tecla está livre."""
    if not seq:
        return None
    norm = QKeySequence(seq).toString()
    grupo = CATALOGO.get(id_, ("", "", ""))[0]
    for outro, (g, descr, _p) in CATALOGO.items():
        if outro == id_:
            continue
        if g != grupo and "Geral" not in (g, grupo):
            continue                      # telas diferentes não brigam
        if QKeySequence(sequencia(outro)).toString() == norm:
            return f"{descr} ({g})"
    return None


def aplicar(id_: str, seq: str) -> None:
    """Persiste o remap (ou volta ao padrão se ``seq`` == padrão) e troca
    a tecla nos atalhos VIVOS — sem reiniciar o app."""
    padrao = CATALOGO[id_][2]
    custom = dict(_customizados())
    norm = QKeySequence(seq).toString() or padrao
    if QKeySequence(norm).toString() == QKeySequence(padrao).toString():
        custom.pop(id_, None)
    else:
        custom[id_] = norm
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                ConfigRepositorio(s).set("atalhos.custom", custom)
                s.commit()
        finally:
            db.engine.dispose()
    except Exception:
        pass
    global _CUSTOM
    _CUSTOM = custom
    _repor_vivos(id_, norm)


def restaurar_padrao() -> None:
    """Zera TODAS as customizações e devolve as teclas padrão aos vivos."""
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                ConfigRepositorio(s).set("atalhos.custom", {})
                s.commit()
        finally:
            db.engine.dispose()
    except Exception:
        pass
    global _CUSTOM
    _CUSTOM = {}
    for id_, (_g, _d, padrao) in CATALOGO.items():
        _repor_vivos(id_, padrao)
