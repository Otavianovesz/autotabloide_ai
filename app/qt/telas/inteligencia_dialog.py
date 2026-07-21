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
        # OS F11.5 #45 (R-121): a memória sazonal ganha a aba dela
        abas.addTab(self._aba_sazonal(), "Ano passado")
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
            # OS F11.5 #51/#52: a saúde com METAS + integridade + nota de foto
            s = I.saude_com_metas()
        except Exception:
            s = {"total": 0}
        if not s.get("total"):
            v.addWidget(EstadoVazio(
                "caixa", "Sem produtos no acervo ainda",
                "A saúde aparece quando os primeiros produtos entrarem."), 1)
            return w
        v.addWidget(QLabel(f"<b>{s['total']}</b> produtos no acervo"))
        metas = s.get("metas", {})
        for rot, chave, n in (
            ("Com foto", "pct_foto", s["com_foto"]),
            ("Com código de barras (EAN)", "pct_ean", s["com_ean"]),
            ("Com preço", "pct_preco", s["com_preco"]),
            ("Com categoria", "pct_categoria", s["com_categoria"]),
        ):
            pct = s[chave]
            m = metas.get(chave, {})
            extra = ""
            if m:
                extra = ("  ·  meta ✓" if m.get("ok")
                         else f"  ·  abaixo da meta ({m.get('alvo')}%)")
            v.addWidget(QLabel(f"{rot} — {n}/{s['total']}{extra}"))
            barra = QProgressBar()
            barra.setValue(int(pct))
            barra.setFormat(f"{pct}%")
            v.addWidget(barra)
        # R-129 + avaliador F9 numa visão só (#52)
        pes = []
        if "orfas" in s:
            pes.append(f"{s['orfas']} foto(s) órfã(s)")
        if "sem_arquivo" in s:
            pes.append(f"{s['sem_arquivo']} cadastro(s) apontando p/ foto "
                       "que sumiu")
        if "fotos_avaliadas" in s:
            pes.append(f"{s['fotos_ruins']} foto(s) ruins de "
                       f"{s['fotos_avaliadas']} avaliadas")
        if pes:
            rodape = QLabel("Integridade: " + " · ".join(pes))
            rodape.setProperty("papel", "legenda")
            rodape.setWordWrap(True)
            v.addWidget(rodape)
        v.addStretch(1)
        return w

    # --- memória sazonal (R-121, OS F11.5 #45) -----------------------------------

    def _aba_sazonal(self) -> QWidget:
        w = QWidget()
        v = _caixa(w)
        try:
            sugestoes = I.memoria_sazonal(self._edicoes)
        except Exception:
            sugestoes = []
        if not sugestoes:
            v.addWidget(EstadoVazio(
                "calendario", "Nada nesta época do ano passado",
                "Quando houver edições salvas de ~1 ano atrás (±10 dias), "
                "os produtos delas aparecem aqui como lembrete."), 1)
            return w
        v.addWidget(QLabel("Ano passado, nesta época, você ofertou:"))
        self.lista_sazonal = QListWidget()
        for s in sugestoes:
            self.lista_sazonal.addItem(s["nome"])
        self.lista_sazonal.setToolTip("Sugestão, não imposição — lembrete "
                                      "por data + chave natural (I1)")
        v.addWidget(self.lista_sazonal, 1)
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
        # OS F11.5 #39 (R-117): o relatório sai em PDF (reusa o molde do
        # checklist F7 — checklist + os números da edição num papel só)
        from PySide6.QtWidgets import QHBoxLayout, QPushButton
        btn_pdf = QPushButton("Exportar em PDF…")
        btn_pdf.setToolTip("O relatório + o checklist da edição num PDF "
                           "imprimível (conferência a quatro olhos)")
        btn_pdf.clicked.connect(self._exportar_relatorio_pdf)
        linha = QHBoxLayout()
        linha.addStretch(1)
        linha.addWidget(btn_pdf)
        v.addLayout(linha)
        return w

    def linhas_relatorio(self) -> list[str]:
        """#39: as linhas do relatório (as MESMAS da tela) — o miolo do PDF,
        testável por conteúdo."""
        rel = I.relatorio_edicao(self._itens)
        linhas = [f"{rel['total']} itens na edição · "
                  f"{rel['sem_foto']} sem foto"]
        if rel["preco_min"] is not None:
            linhas.append(
                f"Faixa de preços: R$ {rel['preco_min']:.2f} a "
                f"R$ {rel['preco_max']:.2f} (média R$ {rel['preco_medio']:.2f})"
                .replace(".", ","))
        for cat, n in rel["por_categoria"].items():
            linhas.append(f"{cat}: {n}")
        return linhas

    def _exportar_relatorio_pdf(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        from app.qt.telas import servico
        destino, _ = QFileDialog.getSaveFileName(
            self, "Salvar o relatório", "relatorio_edicao.pdf",
            "PDF (*.pdf)")
        if not destino:
            return
        servico.exportar_checklist_pdf(
            self._itens, None, destino, titulo="Relatório da edição",
            extras=self.linhas_relatorio())
        from app.qt.design.toast import mostrar_toast
        mostrar_toast(self, "Relatório salvo em PDF.", tipo="sucesso")
