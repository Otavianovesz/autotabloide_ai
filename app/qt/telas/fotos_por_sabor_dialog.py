"""
Uma foto por sabor — a tela da decisão 2 da ORDEM SEXTUSDECIMUS (02/08)
=======================================================================
"Uma tela com um espaço por sabor — cada sabor com sua busca já semeada
e seu quadradinho. Ele preenche os que quiser e segue."

É a porta que fecha o N dos sabores E do composto (L14: meia função não
é função): a lista que sai daqui é PARALELA aos rótulos e alimenta
``criar_familia_de_sabores``/``criar_como_composto`` — cada produto
nasce com a SUA foto. Espaço vazio avisa (I2), nunca some calado.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.qt.design import tokens as t
from app.qt.design.carregando import OverlayOcupado
from app.qt.design.icones import icone
from app.qt.design.toast import mostrar_toast
from app.qt.workers import GerenciadorTrabalhos, Trabalhador

_MINIATURA = 96


class FotosPorSaborDialog(QDialog):
    """Devolve ``fotos()`` — lista paralela aos rótulos, ``None`` no
    espaço que o dono deixou vazio. ``buscador``/``tratador`` são
    injetáveis (a bancada roda sem web e sem rembg)."""

    def __init__(self, base: str, rotulos: list[str], parent=None, *,
                 pre: list[str | None] | None = None,
                 titulo: str | None = None,
                 buscador=None, tratador=None):
        super().__init__(parent)
        # ``base`` semeia a busca ("{base} {rótulo}"); no COMPOSTO os
        # rótulos JÁ são nomes completos — base vazia, busca pelo rótulo
        self._base = base
        self._rotulos = list(rotulos)
        self._fotos: list[str | None] = list(pre or []) + \
            [None] * len(self._rotulos)
        self._fotos = self._fotos[:len(self._rotulos)]
        self._buscador = buscador
        self._tratador = tratador
        self.setWindowTitle(f"Uma foto para cada — {titulo or base}")
        self.setMinimumSize(520, 360)

        dica = QLabel(
            "Cada espaço busca já com o nome certo. Preencha os que "
            "quiser e conclua — espaço sem foto fica avisado no pré-voo.")
        dica.setWordWrap(True)
        dica.setProperty("papel", "legenda")

        grade_w = QWidget()
        grade = QGridLayout(grade_w)
        grade.setSpacing(t.ESP_2)
        self._minis: list[QLabel] = []
        for i, rotulo in enumerate(self._rotulos):
            cartao = QFrame()
            cartao.setProperty("papel", "cartao")
            cl = QVBoxLayout(cartao)
            cl.setSpacing(t.ESP_1)
            titulo = QLabel(rotulo)
            titulo.setStyleSheet("font-weight: 600;")
            titulo.setWordWrap(True)
            mini = QLabel("sem foto")
            mini.setAlignment(Qt.AlignmentFlag.AlignCenter)
            mini.setFixedSize(_MINIATURA + 24, _MINIATURA + 24)
            mini.setProperty("papel", "legenda")
            mini.setFrameShape(QFrame.Shape.StyledPanel)
            mini.setToolTip("Duplo clique amplia (confira a gramatura)")
            mini.setCursor(Qt.CursorShape.PointingHandCursor)
            mini.mouseDoubleClickEvent = (
                lambda _ev, k=i: self._ampliar(k))
            self._minis.append(mini)
            buscar = QPushButton(" Buscar…")
            buscar.setIcon(icone("busca", tamanho=15))
            buscar.setToolTip(f'Busca "{base} {rotulo}" e abre a '
                              "curadoria — você escolhe")
            buscar.clicked.connect(lambda _c=False, k=i: self._buscar(k))
            arquivo = QPushButton(" Arquivo…")
            arquivo.setIcon(icone("abrir", tamanho=15))
            arquivo.clicked.connect(lambda _c=False, k=i: self._arquivo(k))
            limpar = QPushButton("Limpar")
            limpar.setProperty("tipo", "fantasma")
            limpar.clicked.connect(lambda _c=False, k=i: self._limpar(k))
            cl.addWidget(titulo)
            cl.addWidget(mini, 0, Qt.AlignmentFlag.AlignHCenter)
            cl.addWidget(buscar)
            cl.addWidget(arquivo)
            cl.addWidget(limpar)
            grade.addWidget(cartao, i // 3, i % 3)
            if self._fotos[i]:
                self._mostrar(i, self._fotos[i])

        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setWidget(grade_w)

        self._resumo = QLabel("")
        self._resumo.setProperty("papel", "legenda")
        self._atualizar_resumo()

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                  | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Ok).setText("Concluir")
        botoes.button(
            QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)

        raiz = QVBoxLayout(self)
        raiz.setSpacing(t.ESP_2)
        raiz.addWidget(dica)
        raiz.addWidget(rolagem, 1)
        raiz.addWidget(self._resumo)
        raiz.addWidget(botoes)

        self._overlay = OverlayOcupado(self)
        self._trabalhos = GerenciadorTrabalhos()
        from app.qt.design.polimento import ordenar_tab
        ordenar_tab(self)

    def showEvent(self, ev) -> None:  # noqa: N802 (Qt)
        super().showEvent(ev)
        from app.qt.design.polimento import clampar_a_tela
        clampar_a_tela(self)            # L3: cabe em qualquer notebook

    def done(self, resultado: int) -> None:  # noqa: N802 (Qt)
        # junta as pontas dos workers ANTES de morrer (a lição do crash
        # nativo de QThread órfã do FotosItemDialog)
        self._trabalhos.encerrar()
        super().done(resultado)

    # --- API -----------------------------------------------------------------

    def fotos(self) -> list[str | None]:
        return list(self._fotos)

    # --- gestos ----------------------------------------------------------------

    def _buscar(self, i: int) -> None:
        termo = f"{self._base} {self._rotulos[i]}".strip()
        buscador = self._buscador

        def _trabalho(st, q=termo):
            if buscador is not None:
                return buscador(q)
            from app.qt.telas import servico
            return servico.buscar_candidatos(q, st)

        trab = Trabalhador(_trabalho)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(lambda cands, tm=termo, k=i: self._curar(k, tm,
                                                                 cands))
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _curar(self, i: int, termo: str, candidatos: list[str]) -> None:
        from app.qt.telas.curadoria_dialog import CuradoriaDialog

        self._overlay.esconder()
        dlg = CuradoriaDialog(termo, candidatos, self, nome_editavel=False)
        if dlg.exec() != CuradoriaDialog.DialogCode.Accepted:
            return
        tipo, valor = dlg.escolha
        if tipo == "nenhuma" or not valor:
            return
        self._tratar(i, valor)

    def _arquivo(self, i: int) -> None:
        cam, _ = QFileDialog.getOpenFileName(
            self, f"Foto — {self._rotulos[i]}", "",
            "Imagens (*.png *.jpg *.jpeg *.webp *.bmp)")
        if cam:
            self._tratar(i, cam)

    def _tratar(self, i: int, fonte: str) -> None:
        tratador = self._tratador
        if tratador is None:
            from app.qt.telas import servico as _svc
            if not _svc.garantir_modelo_recorte(self):      # CA-01
                return

        avisos_rec: list[str] = []

        def _trabalho(st, f=fonte):
            if tratador is not None:
                return tratador(f)
            from app.qt.telas import servico
            return servico.tratar_imagem(f, st,
                                         aviso_cb=avisos_rec.append)

        trab = Trabalhador(_trabalho)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(lambda cam, k=i, av=avisos_rec:
                        (self._pronta(k, cam),
                         av and mostrar_toast(self, av[0], tipo="erro")))
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _pronta(self, i: int, caminho: str) -> None:
        self._overlay.esconder()
        self._fotos[i] = caminho
        self._mostrar(i, caminho)
        self._atualizar_resumo()

    def _ampliar(self, i: int) -> None:
        """LUPA: a foto do espaço em tamanho real (gramatura legível)."""
        from app.qt.design.lupa import ampliar_imagem
        ampliar_imagem(self, self._fotos[i],
                       titulo=self._rotulos[i])

    def _limpar(self, i: int) -> None:
        self._fotos[i] = None
        self._minis[i].setPixmap(QPixmap())
        self._minis[i].setText("sem foto")
        self._atualizar_resumo()

    def _mostrar(self, i: int, caminho: str) -> None:
        pm = QPixmap(caminho)
        if pm.isNull():
            return
        self._minis[i].setText("")
        self._minis[i].setPixmap(pm.scaled(
            _MINIATURA, _MINIATURA, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
        self._minis[i].setToolTip(Path(caminho).name)

    def _atualizar_resumo(self) -> None:
        n = sum(1 for f in self._fotos if f)
        total = len(self._rotulos)
        if n == total:
            self._resumo.setText(f"✓ {n} de {total} com foto")
        else:
            self._resumo.setText(
                f"{n} de {total} com foto — o que ficar vazio "
                "aparece no pré-voo")

    def _falhou(self, msg: str) -> None:
        self._overlay.esconder()
        mostrar_toast(self, msg, tipo="erro")
