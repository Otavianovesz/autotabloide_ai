"""
Tema do AutoTabloide AI
=======================
Aplica o sistema de design no app inteiro: estilo Fusion + paleta clara
EXPLÍCITA (nunca herda o dark mode do Windows) + QSS gerado dos tokens.

Uso (uma linha, logo após criar o QApplication)::

    from app.qt.design.tema import aplicar_tema
    aplicar_tema(app)
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication

from app.qt.design import tokens as t

_ASSETS = Path(__file__).parent / "assets"


def _fonte_ui() -> str:
    """Escolhe a melhor fonte de UI disponível (Win11 → Segoe Variable)."""
    familias = set(QFontDatabase.families())
    for nome in t.FONTE_UI:
        if nome in familias:
            return nome
    return "Segoe UI"


def _paleta() -> QPalette:
    p = QPalette()
    grupos = (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive)
    papeis = {
        QPalette.ColorRole.Window: t.FUNDO_APP,
        QPalette.ColorRole.WindowText: t.TEXTO,
        QPalette.ColorRole.Base: t.SUPERFICIE,
        QPalette.ColorRole.AlternateBase: t.SUPERFICIE_2,
        QPalette.ColorRole.Text: t.TEXTO,
        QPalette.ColorRole.Button: t.SUPERFICIE,
        QPalette.ColorRole.ButtonText: t.TEXTO,
        QPalette.ColorRole.Highlight: t.PRIMARIA,
        QPalette.ColorRole.HighlightedText: t.TEXTO_INVERSO,
        QPalette.ColorRole.ToolTipBase: t.ESCURO,
        QPalette.ColorRole.ToolTipText: t.TEXTO_INVERSO,
        QPalette.ColorRole.PlaceholderText: t.TEXTO_3,
    }
    for grupo in grupos:
        for papel, cor in papeis.items():
            p.setColor(grupo, papel, QColor(cor))
    return p


def construir_qss() -> str:
    """QSS global, gerado dos tokens (fonte única de verdade)."""
    return f"""
/* ===== base ===== */
QWidget {{
    color: {t.TEXTO};
    font-size: {t.TAM_CORPO}pt;
}}
QMainWindow, QDialog {{ background: {t.FUNDO_APP}; }}
QLabel {{ background: transparent; }}
QLabel[papel="secao"] {{
    color: {t.TEXTO_2}; font-size: {t.TAM_SECAO}pt; font-weight: 700;
    letter-spacing: 1px;
}}
/* FASE 3 (passo 18): campo INVÁLIDO trava com borda vermelha */
QDoubleSpinBox[invalido="true"], QSpinBox[invalido="true"],
QLineEdit[invalido="true"] {{
    border: 2px solid {t.PERIGO};
}}
/* FASE 3 (passo 11): a lista de abas das Configurações */
#listaAbasConfig {{
    background: {t.FUNDO_APP}; border: none;
    border-right: 1px solid {t.BORDA}; border-radius: 0;
    padding: {t.ESP_2}px;
}}
#listaAbasConfig::item {{
    padding: 9px 10px; border-radius: {t.RAIO_CONTROLE}px;
    margin: 1px 0;
}}
#listaAbasConfig::item:selected {{
    background: {t.PRIMARIA_SUAVE}; color: {t.PRIMARIA_ESCURA};
    font-weight: 600;
}}

/* FASE 2 (passo 9): o swatch de cor escolhido ganha anel visível */
QToolButton#swatchCor {{ border: 2px solid transparent;
    border-radius: {t.RAIO_CONTROLE}px; padding: 1px; }}
QToolButton#swatchCor:checked {{ border: 2px solid {t.TEXTO}; }}

/* FASE 1 (passo 45): cabeçalho clicável das seções recolhíveis */
QToolButton[papel="secaoCabecalho"] {{
    background: transparent; border: none; padding: 4px 2px;
    color: {t.TEXTO_2}; font-size: {t.TAM_SECAO}pt; font-weight: 700;
}}
QLabel[papel="legenda"] {{ color: {t.TEXTO_3}; font-size: {t.TAM_LEGENDA}pt; }}
QLabel[papel="titulo"] {{ font-size: {t.TAM_TITULO}pt; font-weight: 600; }}

/* ===== botões ===== */
QPushButton {{
    background: {t.SUPERFICIE}; border: 1px solid {t.BORDA_FORTE};
    border-radius: {t.RAIO_CONTROLE}px; padding: 5px 12px;
    min-height: {t.ALTURA_CONTROLE - 12}px;   /* passo 50: 32px totais */
}}
/* FASE 1 (passo 41): o FUNDO do hover vem do véu animado de 120 ms
   (animacoes.instalar_vida) — o QSS só responde a borda, sem salto seco */
QPushButton:hover {{ border-color: {t.PRIMARIA}; }}
QPushButton:pressed {{ background: {t.PRIMARIA_SUAVE}; }}
QPushButton:disabled {{ color: {t.TEXTO_3}; background: {t.SUPERFICIE_2};
                        border-color: {t.BORDA}; }}
QPushButton:focus {{ border: 2px solid {t.PRIMARIA}; padding: 4px 11px; }}
QPushButton[tipo="primario"] {{
    background: {t.PRIMARIA}; color: {t.ACENTO_TEXTO}; border: 1px solid {t.PRIMARIA};
    font-weight: 600;
}}
QPushButton[tipo="primario"]:disabled {{
    background: {t.PRIMARIA_200}; border-color: {t.PRIMARIA_200};
    color: {t.ACENTO_TEXTO};
}}
QPushButton[tipo="fantasma"] {{ background: transparent; border: none; }}

/* ===== top-bar / navegação entre telas ===== */
#topBar {{ background: {t.SUPERFICIE}; border-bottom: 1px solid {t.BORDA}; }}
#topBar QToolButton[nav="true"] {{
    background: transparent; border: none; border-radius: {t.RAIO_CONTROLE}px;
    padding: 5px 12px; color: {t.TEXTO_2}; font-weight: 500;
}}
#topBar QToolButton[nav="true"]:hover {{ color: {t.TEXTO}; }}
#topBar QToolButton[nav="true"]:checked {{ background: {t.PRIMARIA_SUAVE};
    color: {t.PRIMARIA_ESCURA}; font-weight: 600; }}
#topBar QToolButton[nav="true"]:disabled {{ color: {t.TEXTO_3}; }}

/* ===== barra de ferramentas ===== */
#barraFerramentas {{
    background: {t.SUPERFICIE}; border-bottom: 1px solid {t.BORDA};
}}
#barraFerramentas QToolButton {{
    background: transparent; border: none; border-radius: {t.RAIO_CONTROLE}px;
    padding: 5px;
}}
#barraFerramentas QToolButton:pressed,
#barraFerramentas QToolButton:checked {{ background: {t.PRIMARIA_SUAVE}; }}
#barraFerramentas QFrame[papel="separador"] {{
    background: {t.BORDA}; max-width: 1px; margin: 6px 4px;
}}

/* ===== cartões/painéis ===== */
QWidget[papel="cartao"] {{
    background: {t.SUPERFICIE}; border: 1px solid {t.BORDA};
    border-radius: {t.RAIO_CARTAO}px;
}}
QWidget[papel="cartaoCabecalho"] {{
    background: {t.SUPERFICIE_2};
    border-top-left-radius: {t.RAIO_CARTAO}px;
    border-top-right-radius: {t.RAIO_CARTAO}px;
    border-bottom: 1px solid {t.BORDA};
}}
#lateral {{ background: {t.FUNDO_APP}; }}
QWidget[papel="reguaCanto"] {{
    background: {t.SUPERFICIE};
    border-right: 1px solid {t.BORDA}; border-bottom: 1px solid {t.BORDA};
}}

/* ===== campos ===== */
/* FASE 1 (passo 50): min-height do QSS conta só o CONTEÚDO — os valores
   somam ALTURA_CONTROLE com borda(2) + padding(8 campos / 10 botões) */
QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {{
    background: {t.SUPERFICIE}; border: 1px solid {t.BORDA_FORTE};
    border-radius: {t.RAIO_CONTROLE}px; padding: 4px 8px;
    min-height: {t.ALTURA_CONTROLE - 10}px;
    min-width: {t.LARGURA_MIN_CAMPO - 18}px;
    selection-background-color: {t.PRIMARIA}; selection-color: {t.TEXTO_INVERSO};
}}
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
    border: 2px solid {t.PRIMARIA}; padding: 3px 7px;
}}
QLineEdit:disabled, QComboBox:disabled {{ background: {t.SUPERFICIE_2};
    color: {t.TEXTO_3}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background: {t.SUPERFICIE}; border: 1px solid {t.BORDA};
    border-radius: {t.RAIO_CONTROLE}px;
    selection-background-color: {t.PRIMARIA_SUAVE}; selection-color: {t.TEXTO};
    outline: 0;
}}
/* FASE 1 (passo 67): anel de foco de 2 px no acento em TODO controle
   (campos e QPushButton já tinham; aqui os que faltavam) */
QToolButton:focus {{ border: 2px solid {t.PRIMARIA};
    border-radius: {t.RAIO_CONTROLE}px; }}
QCheckBox::indicator:focus {{ border: 2px solid {t.PRIMARIA}; }}
QListWidget:focus, QListView:focus, QTreeView:focus, QTableView:focus,
QPlainTextEdit:focus, QTextEdit:focus {{
    border: 2px solid {t.PRIMARIA};
}}

QCheckBox {{ spacing: 6px; }}
QCheckBox::indicator {{
    width: 15px; height: 15px; border: 1px solid {t.BORDA_FORTE};
    border-radius: 4px; background: {t.SUPERFICIE};
}}
QCheckBox::indicator:hover {{ border-color: {t.PRIMARIA}; }}
QCheckBox::indicator:checked {{ background: {t.PRIMARIA}; border-color: {t.PRIMARIA};
    image: url("{(_ASSETS / 'check.svg').as_posix()}"); }}

/* ===== listas ===== */
QListWidget, QListView, QTreeView, QTableView {{
    background: {t.SUPERFICIE}; border: 1px solid {t.BORDA};
    border-radius: {t.RAIO_CONTROLE}px; outline: 0;
}}
QListWidget::item {{ border-radius: 4px; padding: 2px; }}
QListWidget::item:hover {{ background: {t.PRIMARIA_FUNDO}; }}
QListWidget::item:selected {{ background: {t.PRIMARIA_SUAVE}; color: {t.TEXTO}; }}

/* ===== grupos ===== */
QGroupBox {{
    border: 1px solid {t.BORDA}; border-radius: {t.RAIO_CONTROLE}px;
    margin-top: 10px; font-weight: 600; color: {t.TEXTO_2};
    background: transparent;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 8px; padding: 0 4px; }}

/* ===== menus / tooltip / status ===== */
QMenu {{
    background: {t.SUPERFICIE}; border: 1px solid {t.BORDA};
    border-radius: {t.RAIO_CARTAO}px; padding: 4px;
}}
QMenu::item {{ padding: 5px 24px 5px 12px; border-radius: 4px; }}
QMenu::item:selected {{ background: {t.PRIMARIA_FUNDO}; }}
QMenu::separator {{ height: 1px; background: {t.BORDA}; margin: 4px 8px; }}
QToolTip {{
    background: {t.ESCURO}; color: {t.TEXTO_INVERSO}; border: none;
    padding: 5px 8px; border-radius: 4px; font-size: {t.TAM_ROTULO}pt;
}}
QStatusBar {{
    background: {t.SUPERFICIE}; border-top: 1px solid {t.BORDA};
    color: {t.TEXTO_2};
}}
QStatusBar::item {{ border: none; }}

/* ===== toast / overlay / command palette ===== */
#toast {{ background: {t.ESCURO}; border-radius: {t.RAIO_CARTAO}px; }}
#toast QLabel {{ color: {t.TEXTO_INVERSO}; }}
/* FASE 1 (passo 71): o botão "Desfazer" do toast, discreto no chrome */
#toast #toastAcao {{
    background: transparent; border: 1px solid {t.TEXTO_3};
    border-radius: {t.RAIO_CONTROLE}px; color: {t.INFO_CLARO};
    padding: 2px 10px; min-height: 0; font-weight: 600;
}}
#toast #toastAcao:hover {{ border-color: {t.INFO_CLARO}; }}
#overlayOcupado {{ background: {t.VEU_OCUPADO}; }}
#overlayOcupado #overlayCaixa {{
    background: {t.SUPERFICIE}; border: 1px solid {t.BORDA};
    border-radius: {t.RAIO_CARTAO}px;
}}
#paletaCmd {{
    background: {t.SUPERFICIE}; border: 1px solid {t.BORDA_FORTE};
    border-radius: 10px;
}}
#paletaCmd QLineEdit {{
    border: none; border-bottom: 1px solid {t.BORDA}; border-radius: 0;
    padding: 10px 14px; font-size: 10.5pt; background: transparent;
}}
#paletaCmd QLineEdit:focus {{ border: none; border-bottom: 2px solid {t.PRIMARIA};
    padding: 10px 14px 9px 14px; }}
#paletaCmd QListWidget {{ border: none; background: transparent; padding: 4px; }}
#paletaCmd QListWidget::item {{ padding: 6px 10px; border-radius: 6px; }}

/* ===== barras de rolagem (finas) ===== */
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{
    background: {t.BORDA_FORTE}; border-radius: 4px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {t.TEXTO_3}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{
    background: {t.BORDA_FORTE}; border-radius: 4px; min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{ background: {t.TEXTO_3}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
"""


def _escala_da_config() -> int:
    """FASE 1 (passo 64 — R-015): `aparencia.escala` (100 é o padrão)."""
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                valor = int(ConfigRepositorio(s).get("aparencia.escala")
                            or 100)
        finally:
            db.engine.dispose()
        return valor if valor in (100, 125, 150) else 100
    except Exception:
        return 100


def _tema_da_config() -> str:
    """`aparencia.tema` da Config — claro é o padrão travado (C3)."""
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                valor = str(ConfigRepositorio(s).get("aparencia.tema")
                            or "claro")
        finally:
            db.engine.dispose()
        return valor if valor in t.TEMAS else "claro"
    except Exception:
        return "claro"


def aplicar_tema(app: QApplication, nome: str | None = None) -> None:
    """Fusion + paleta do TEMA + QSS regenerado dos tokens + fonte de UI.

    FASE 1 (passos 13/17/18): sem `nome`, vale a Config (claro é o padrão
    travado — nunca herda o dark do SO). Com `nome`, ativa e aplica —
    a troca em runtime chama isto de novo e repolimenta o Shell (passo 19).
    """
    t.ativar_escala(_escala_da_config())   # passo 64: antes do QSS/fonte
    t.ativar_tema(nome if nome is not None else _tema_da_config())
    app.setStyle("Fusion")                 # neutraliza o estilo nativo/dark do SO
    app.setPalette(_paleta())
    fonte = QFont(_fonte_ui())
    fonte.setPointSizeF(t.TAM_CORPO)
    app.setFont(fonte)
    app.setStyleSheet(construir_qss())


def trocar_tema(nome: str) -> None:
    """FASE 1 (passos 19/24): troca NA HORA, persiste e repolimenta tudo.

    O QSS/paleta regenerados valem para todo widget vivo; o repolimento
    força a repintura. Ícones criados com cor explícita atualizam quando a
    tela recria (limite documentado no caderno); os do top-bar o Shell
    refaz via ``retematizar``."""
    from PySide6.QtWidgets import QApplication

    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                ConfigRepositorio(s).set("aparencia.tema", nome)
                s.commit()
        finally:
            db.engine.dispose()
    except Exception:
        pass                               # sem banco: o tema vale na sessão
    app = QApplication.instance()
    if app is None:
        return
    aplicar_tema(app, nome)
    _repolir_tudo(app)


def _repolir_tudo(app) -> None:
    """Repolimento global com defesa: wrapper Python cujo C++ já morreu
    (deleteLater em voo) derruba o processo se tocado — filtra com
    shiboken6.isValid antes de repolir."""
    import shiboken6
    for w in app.allWidgets():
        if not shiboken6.isValid(w):
            continue
        w.style().unpolish(w)
        w.style().polish(w)
        w.update()


def trocar_escala(pct: int) -> None:
    """FASE 1 (passo 64): muda a escala NA HORA, persiste e repolimenta —
    o mesmo caminho vivo do trocar_tema."""
    from PySide6.QtWidgets import QApplication

    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                ConfigRepositorio(s).set("aparencia.escala", int(pct))
                s.commit()
        finally:
            db.engine.dispose()
    except Exception:
        pass                               # sem banco: vale na sessão
    app = QApplication.instance()
    if app is None:
        return
    aplicar_tema(app)                      # relê Config (escala + tema)
    _repolir_tudo(app)
    for janela in app.topLevelWidgets():
        if hasattr(janela, "retematizar"):
            janela.retematizar()           # o Shell refaz os ícones do topo
