"""F13-TER/N1 — "Itens fixos deste encarte".

O pedido repetido em três encartes ("as três ali são fixas… eu quero
escolher as imagens ali e deixar elas na melhor forma possível"): o
conteúdo da célula FIXA — produto + foto ESCOLHIDA + preço fixo OU da
semana — vive no TEMPLATE (``Slot.conteudo_fixo``) e sobrevive à
reimportação da tabela. Este diálogo edita esse registro com prévia na
CÉLULA REAL (a página composta, recortada no slot).

Decisões:
- foto de arquivo é COPIADA para ``biblioteca_imagens/_fixos/`` e o
  caminho guardado RELATIVO (I3 — o template viaja entre PCs);
- "usar o preço da semana" liga o casamento por chave natural (D12) na
  importação — nunca OCR forçado; desligado, o preço é cravado do dono.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
)

from app.core.paths import SystemRoot


def slots_fixos(layout) -> list:
    """Os slots FIXOS de todas as páginas (a lista do diálogo)."""
    achados = []
    for pagina in getattr(layout, "paginas", []) or []:
        for slot in pagina.slots:
            if getattr(slot, "fixa", False):
                achados.append((pagina, slot))
    return achados


def internar_foto_fixa(origem: str | Path) -> str:
    """Copia a foto escolhida para ``biblioteca_imagens/_fixos/`` (se já
    não morar na biblioteca) e devolve o caminho RELATIVO à biblioteca
    (I3). Foto do próprio acervo só relativiza — nunca duplica."""
    origem = Path(origem)
    bib = SystemRoot().biblioteca_imagens
    try:
        return origem.resolve().relative_to(bib.resolve()).as_posix()
    except ValueError:
        pass                              # de fora: interna com cópia
    destino = bib / "_fixos" / origem.name
    destino.parent.mkdir(parents=True, exist_ok=True)
    if origem.resolve() != destino.resolve():
        shutil.copy2(origem, destino)
    return destino.relative_to(bib).as_posix()


class ItensFixosDialog(QDialog):
    """Edita ``Slot.conteudo_fixo`` dos slots fixos do layout ABERTO —
    quem salva o projeto/template depois congela junto (o layout
    serializa o campo)."""

    def __init__(self, layout, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Itens fixos deste encarte")
        self._layout_def = layout
        self._pares = slots_fixos(layout)
        self._atual = None

        raiz = QHBoxLayout(self)
        self.lista = QListWidget()
        for _pag, slot in self._pares:
            cf = slot.conteudo_fixo or {}
            self.lista.addItem(cf.get("nome") or f"(vazia) {slot.id}")
        self.lista.currentRowChanged.connect(self._trocar)
        raiz.addWidget(self.lista, 1)

        lado = QVBoxLayout()
        form = QFormLayout()
        self.ed_nome = QLineEdit()
        self.ed_descritor = QLineEdit()
        self.ed_preco = QLineEdit()
        self.ed_preco.setPlaceholderText("ex.: 17,90 — vazio: sem preço")
        self.chk_semana = QCheckBox(
            "Usar o preço da SEMANA (atualiza quando o produto aparecer "
            "na tabela)")
        form.addRow("Nome:", self.ed_nome)
        form.addRow("Descritor:", self.ed_descritor)
        form.addRow("Preço:", self.ed_preco)
        form.addRow("", self.chk_semana)
        lado.addLayout(form)

        linha_foto = QHBoxLayout()
        self._foto_lbl = QLabel("(sem foto)")
        self._foto_lbl.setProperty("papel", "legenda")
        btn_foto = QPushButton("Escolher foto…")
        btn_foto.clicked.connect(self._escolher_foto)
        linha_foto.addWidget(self._foto_lbl, 1)
        linha_foto.addWidget(btn_foto)
        lado.addLayout(linha_foto)

        self._previa = QLabel("")
        self._previa.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._previa.setMinimumSize(260, 200)
        lado.addWidget(self._previa, 1)
        btn_previa = QPushButton("Atualizar a prévia (célula real)")
        btn_previa.clicked.connect(self._atualizar_previa)
        lado.addWidget(btn_previa)

        caixa = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                 | QDialogButtonBox.StandardButton.Cancel)
        caixa.accepted.connect(self._confirmar)
        caixa.rejected.connect(self.reject)
        caixa.button(QDialogButtonBox.StandardButton.Ok).setText("Aplicar")
        caixa.button(
            QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        lado.addWidget(caixa)
        raiz.addLayout(lado, 2)

        self._imagem_rel: str | None = None
        if self._pares:
            self.lista.setCurrentRow(0)

    # --- estado por slot ------------------------------------------------------

    def _trocar(self, idx: int) -> None:
        self._gravar_form()               # guarda o slot que saiu
        if not (0 <= idx < len(self._pares)):
            self._atual = None
            return
        self._atual = idx
        cf = self._pares[idx][1].conteudo_fixo or {}
        self.ed_nome.setText(cf.get("nome") or "")
        self.ed_descritor.setText(cf.get("descritor") or "")
        self.ed_preco.setText(cf.get("preco") or "")
        self.chk_semana.setChecked(bool(cf.get("preco_da_semana")))
        self._imagem_rel = cf.get("imagem")
        self._foto_lbl.setText(self._imagem_rel or "(sem foto)")
        self._atualizar_previa()

    def _gravar_form(self) -> None:
        """O formulário vira ``conteudo_fixo`` do slot em edição."""
        if self._atual is None:
            return
        slot = self._pares[self._atual][1]
        nome = self.ed_nome.text().strip()
        if not (nome or self._imagem_rel or self.ed_preco.text().strip()):
            slot.conteudo_fixo = None     # tudo vazio = célula só-arte
            return
        slot.conteudo_fixo = {
            "nome": nome,
            "descritor": self.ed_descritor.text().strip() or None,
            "preco": self.ed_preco.text().strip() or None,
            "preco_da_semana": self.chk_semana.isChecked(),
            "imagem": self._imagem_rel,
        }
        item = self.lista.item(self._atual)
        if item is not None:
            item.setText(nome or f"(vazia) {slot.id}")

    def _confirmar(self) -> None:
        self._gravar_form()
        self.accept()

    # --- foto + prévia --------------------------------------------------------

    def _escolher_foto(self) -> None:
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Foto do item fixo",
            str(SystemRoot().biblioteca_imagens),
            "Imagens (*.png *.webp *.jpg *.jpeg)")
        if not caminho:
            return
        self._imagem_rel = internar_foto_fixa(caminho)
        self._foto_lbl.setText(self._imagem_rel)
        self._atualizar_previa()

    def _atualizar_previa(self) -> None:
        """A prévia é a CÉLULA REAL: compõe a página com o formulário
        atual e recorta o bbox do slot — o dono vê o que o export vê."""
        if self._atual is None:
            return
        self._gravar_form()
        pagina, slot = self._pares[self._atual]
        try:
            from app.rendering.compositor import compor_pagina
            from app.rendering.units import mm_para_px
            img = compor_pagina(self._layout_def, pagina, {}, dpi=96)
            xs, ys, x2, y2 = [], [], [], []
            for r in slot.regioes:
                xs.append(r.rect.x); ys.append(r.rect.y)
                x2.append(r.rect.x + r.rect.largura)
                y2.append(r.rect.y + r.rect.altura)
            if not xs:
                return
            m = 3.0                        # respiro de 3 mm no recorte
            caixa = tuple(round(mm_para_px(v, 96)) for v in (
                max(0.0, min(xs) - m), max(0.0, min(ys) - m),
                max(x2) + m, max(y2) + m))
            rec = img.crop(caixa)
            # via arquivo (nunca ImageQt: o QImage emprestado do buffer
            # PIL morre com o objeto e derruba o processo — crash real
            # desta bancada)
            import tempfile
            with tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False) as tf:
                caminho_tmp = tf.name
            rec.convert("RGB").save(caminho_tmp)
            pix = QPixmap(caminho_tmp)
            Path(caminho_tmp).unlink(missing_ok=True)
            self._previa.setPixmap(pix.scaled(
                self._previa.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        except Exception as exc:          # prévia nunca derruba o diálogo
            self._previa.setText(f"(prévia indisponível: {exc})")
