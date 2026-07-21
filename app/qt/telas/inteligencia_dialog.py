"""
Inteligência do negócio — o painel (R-115/117/120/121/126, Fase 11)
===================================================================
Um diálogo SÓ LEITURA que o dono abre sob demanda (não pesa o boot). Mostra a
saúde do acervo, o ranking dos mais ofertados, o histórico de preço de um
produto (com o menor do ano marcado) e o relatório da edição aberta.

Nada aqui muda o acervo; sem dado, diz "sem histórico ainda" (I2). Toda a
lógica vem de ``inteligencia`` (funções puras) — o diálogo só desenha.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QLabel,
    QListWidget,
    QProgressBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.qt.design import tokens as t
from app.qt.design.componentes import EstadoVazio
from app.qt.telas import inteligencia as I


def _caixa(w: QWidget) -> QVBoxLayout:
    """Layout padrão de uma aba: margens/spacing do design system."""
    v = QVBoxLayout(w)
    v.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
    v.setSpacing(t.ESP_2)
    return v


class _Sparkline(QWidget):
    """Mini-gráfico do preço ao longo das edições (R-115). O menor preço fica
    marcado (bolinha) — o dono lê de relance."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pontos: list = []
        self._menor = None
        self.setMinimumHeight(140)

    def definir(self, pontos, menor) -> None:
        self._pontos = pontos
        self._menor = menor
        self.update()

    @staticmethod
    def _reais(v: float) -> str:
        return f"R$ {v:.2f}".replace(".", ",")

    @staticmethod
    def _data(quando) -> str:
        try:
            return quando.strftime("%d/%m/%y")
        except Exception:
            return ""

    def paintEvent(self, _ev) -> None:  # noqa: N802 (Qt)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if len(self._pontos) < 1:
            p.setPen(QColor(t.TEXTO_3))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "sem histórico ainda")
            return
        precos = [float(pt.preco) for pt in self._pontos]
        lo, hi = min(precos), max(precos)
        faixa = (hi - lo) or 1.0
        n = len(precos)
        # eixos ROTULADOS (polimento): R$ à esquerda, datas embaixo — margens
        # assimétricas dão o espaço; os valores vêm dos próprios pontos.
        fm = p.fontMetrics()
        m_esq = max(fm.horizontalAdvance(self._reais(hi)),
                    fm.horizontalAdvance(self._reais(lo))) + 12
        m_dir, m_topo = 14, 10
        m_baixo = fm.height() + 10

        def _xy(i, val):
            x = m_esq + (w - m_esq - m_dir) * (i / max(1, n - 1))
            y = m_topo + (h - m_topo - m_baixo) * (1 - (val - lo) / faixa)
            return x, y

        # grade horizontal leve + rótulos do eixo y (máximo e mínimo)
        p.setPen(QPen(QColor(t.BORDA), 1))
        for val in (hi, lo):
            _, y = _xy(0, val)
            p.drawLine(m_esq, int(y), w - m_dir, int(y))
        p.setPen(QColor(t.TEXTO_3))
        for val in (hi, lo):
            _, y = _xy(0, val)
            p.drawText(4, int(y + fm.ascent() / 2) - 1, self._reais(val))
        # rótulos do eixo x: a data da primeira e da última edição
        d0 = self._data(self._pontos[0].quando)
        d1 = self._data(self._pontos[-1].quando)
        if d0:
            p.drawText(m_esq, h - 4, d0)
        if d1 and n > 1:
            p.drawText(w - m_dir - fm.horizontalAdvance(d1), h - 4, d1)
        # linha
        p.setPen(QPen(QColor(t.ACENTO), 2))
        pontos_xy = [_xy(i, v) for i, v in enumerate(precos)]
        for a, b in zip(pontos_xy, pontos_xy[1:]):
            p.drawLine(int(a[0]), int(a[1]), int(b[0]), int(b[1]))
        # marca o menor preço (o "menor do ano")
        for i, v in enumerate(precos):
            x, y = _xy(i, v)
            eh_menor = self._menor is not None and self._pontos[i].preco == self._menor
            p.setBrush(QColor(t.SUCESSO if eh_menor else t.ACENTO))
            p.setPen(Qt.PenStyle.NoPen)
            r = 6 if eh_menor else 3
            p.drawEllipse(int(x - r), int(y - r), 2 * r, 2 * r)


class InteligenciaDialog(QDialog):
    """R-115/117/120/121/126: o painel de inteligência (só leitura)."""

    def __init__(self, itens=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inteligência do negócio")
        self.resize(560, 480)
        self._itens = itens or []

        from app.core import projetos
        try:
            self._edicoes = projetos.historico_edicoes()
        except Exception:
            self._edicoes = []

        abas = QTabWidget()
        abas.addTab(self._aba_saude(), "Saúde do acervo")
        abas.addTab(self._aba_ranking(), "Mais ofertados")
        abas.addTab(self._aba_historico(), "Histórico de preço")
        abas.addTab(self._aba_relatorio(), "Relatório da edição")
        abas.setToolTip("Tudo aqui é SÓ LEITURA — nada muda o acervo, "
                        "nada sai do seu computador")

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(t.ESP_3, t.ESP_3, t.ESP_3, t.ESP_3)
        raiz.setSpacing(t.ESP_2)
        raiz.addWidget(abas)

    # --- saúde (R-126) -----------------------------------------------------------

    def _aba_saude(self) -> QWidget:
        w = QWidget()
        v = _caixa(w)
        try:
            s = I.saude_acervo()
        except Exception:
            s = {"total": 0}
        if not s.get("total"):
            v.addWidget(EstadoVazio(
                "caixa", "Sem produtos no acervo ainda",
                "A saúde aparece quando os primeiros produtos entrarem."), 1)
            return w
        v.addWidget(QLabel(f"<b>{s['total']}</b> produtos no acervo"))
        for rot, pct, n in (
            ("Com foto", s["pct_foto"], s["com_foto"]),
            ("Com código de barras (EAN)", s["pct_ean"], s["com_ean"]),
            ("Com preço", s["pct_preco"], s["com_preco"]),
            ("Com categoria", s["pct_categoria"], s["com_categoria"]),
        ):
            v.addWidget(QLabel(f"{rot} — {n}/{s['total']}"))
            barra = QProgressBar()
            barra.setValue(int(pct))
            barra.setFormat(f"{pct}%")
            v.addWidget(barra)
        v.addStretch(1)
        return w

    # --- ranking (R-120) ---------------------------------------------------------

    def _aba_ranking(self) -> QWidget:
        w = QWidget()
        v = _caixa(w)
        lista = QListWidget()
        rank = I.ranking_ofertados(self._edicoes, top=20)
        if not rank:
            v.addWidget(EstadoVazio(
                "grade", "Sem edições salvas ainda",
                "O ranking dos carros-chefe aparece quando você salvar "
                "encartes."), 1)
        else:
            for i, r in enumerate(rank, 1):
                lista.addItem(f"{i}. {r['nome']}  ·  {r['edicoes']} edição(ões)")
            v.addWidget(QLabel("Seus carros-chefe (mais entram nos encartes):"))
            v.addWidget(lista)
        return w

    # --- histórico de preço (R-115) ---------------------------------------------

    def _aba_historico(self) -> QWidget:
        w = QWidget()
        v = _caixa(w)
        self._combo_hist = QComboBox()
        self._combo_hist.setToolTip(
            "O preço deste produto ao longo das edições salvas — o menor "
            "fica marcado em verde")
        self._chaves_hist = []
        for r in I.ranking_ofertados(self._edicoes):
            self._combo_hist.addItem(r["nome"])
            self._chaves_hist.append(r["chave"])
        self._spark = _Sparkline()
        self._lbl_menor = QLabel("")
        self._lbl_menor.setProperty("papel", "legenda")
        v.addWidget(QLabel("Produto:"))
        v.addWidget(self._combo_hist)
        v.addWidget(self._spark, 1)
        v.addWidget(self._lbl_menor)
        self._combo_hist.currentIndexChanged.connect(self._mostrar_historico)
        if self._chaves_hist:
            self._mostrar_historico(0)
        else:
            v.addWidget(EstadoVazio(
                "calendario", "Sem histórico ainda",
                "Salve edições para acompanhar o preço semana a semana."))
        return w

    def _mostrar_historico(self, idx: int) -> None:
        if not (0 <= idx < len(self._chaves_hist)):
            return
        s = I.serie_de_um(self._edicoes, self._chaves_hist[idx])
        self._spark.definir(s["pontos"], s["menor"])
        if s["menor"] is not None:
            self._lbl_menor.setText(
                f"Menor preço do histórico: R$ {s['menor']:.2f}".replace(".", ","))
        else:
            self._lbl_menor.setText("Sem histórico de preço ainda.")

    # --- relatório da edição (R-117) --------------------------------------------

    def _aba_relatorio(self) -> QWidget:
        w = QWidget()
        v = _caixa(w)
        if not self._itens:
            v.addWidget(EstadoVazio(
                "abrir", "Nenhuma edição aberta",
                "Abra uma edição na Mesa ou na Fábrica para ver o relatório."),
                1)
            return w
        rel = I.relatorio_edicao(self._itens)
        v.addWidget(QLabel(f"<b>{rel['total']}</b> itens na edição · "
                           f"{rel['sem_foto']} sem foto"))
        if rel["preco_min"] is not None:
            v.addWidget(QLabel(
                f"Faixa de preços: R$ {rel['preco_min']:.2f} a "
                f"R$ {rel['preco_max']:.2f} (média R$ {rel['preco_medio']:.2f})"
                .replace(".", ",")))
        v.addWidget(QLabel("<b>Itens por categoria:</b>"))
        lista = QListWidget()
        for cat, n in rel["por_categoria"].items():
            lista.addItem(f"{cat}: {n}")
        v.addWidget(lista, 1)
        return w
