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

        # F13-DUODECIMUS/T5: uma foto POR ZONA da célula ("Sonho +
        # Croissant" tem duas) — as linhas nascem em _trocar, conforme
        # o slot; célula de zona única fica com a linha de sempre
        self._caixa_fotos = QVBoxLayout()
        lado.addLayout(self._caixa_fotos)
        self._foto_lbls: list[QLabel] = []

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

        self._imagens_rel: list[str | None] = []
        if self._pares:
            self.lista.setCurrentRow(0)

    def _zonas_de_foto(self, slot) -> int:
        from app.rendering.model import TipoRegiao
        return max(1, sum(1 for r in slot.regioes
                          if r.tipo == TipoRegiao.IMAGEM and r.visivel))

    def _montar_linhas_de_foto(self, slot) -> None:
        """T5: (re)monta uma linha de foto por ZONA do slot em edição."""
        while self._caixa_fotos.count():
            item = self._caixa_fotos.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
            lay = item.layout()
            if lay is not None:
                while lay.count():
                    sub = lay.takeAt(0)
                    if sub.widget() is not None:
                        sub.widget().deleteLater()
        self._foto_lbls = []
        n = self._zonas_de_foto(slot)
        for k in range(n):
            linha = QHBoxLayout()
            lbl = QLabel("(sem foto)")
            lbl.setProperty("papel", "legenda")
            rotulo = ("Escolher foto…" if n == 1
                      else f"Foto da zona {k + 1}…")
            btn = QPushButton(rotulo)
            btn.clicked.connect(lambda _c=False, i=k:
                                self._escolher_foto(i))
            linha.addWidget(lbl, 1)
            linha.addWidget(btn)
            self._caixa_fotos.addLayout(linha)
            self._foto_lbls.append(lbl)

    # --- estado por slot ------------------------------------------------------

    def _trocar(self, idx: int) -> None:
        self._gravar_form()               # guarda o slot que saiu
        if not (0 <= idx < len(self._pares)):
            self._atual = None
            return
        self._atual = idx
        slot = self._pares[idx][1]
        cf = slot.conteudo_fixo or {}
        self.ed_nome.setText(cf.get("nome") or "")
        self.ed_descritor.setText(cf.get("descritor") or "")
        self.ed_preco.setText(cf.get("preco") or "")
        self.chk_semana.setChecked(bool(cf.get("preco_da_semana")))
        self._montar_linhas_de_foto(slot)
        n = self._zonas_de_foto(slot)
        gravadas = list(cf.get("imagens") or [])
        if not gravadas and cf.get("imagem"):
            gravadas = [cf.get("imagem")]
        self._imagens_rel = [(gravadas[k] if k < len(gravadas) else None)
                             for k in range(n)]
        for k, lbl in enumerate(self._foto_lbls):
            lbl.setText(self._imagens_rel[k] or "(sem foto)")
        self._atualizar_previa()

    def _gravar_form(self) -> None:
        """O formulário vira ``conteudo_fixo`` do slot em edição."""
        if self._atual is None:
            return
        slot = self._pares[self._atual][1]
        nome = self.ed_nome.text().strip()
        fotos = [r for r in self._imagens_rel if r]
        if not (nome or fotos or self.ed_preco.text().strip()):
            slot.conteudo_fixo = None     # tudo vazio = célula só-arte
            return
        slot.conteudo_fixo = {
            "nome": nome,
            "descritor": self.ed_descritor.text().strip() or None,
            "preco": self.ed_preco.text().strip() or None,
            "preco_da_semana": self.chk_semana.isChecked(),
            # T5: a lista por zona é a verdade; o singular segue para
            # compat (a 1ª foto)
            "imagem": fotos[0] if fotos else None,
            "imagens": [r for r in self._imagens_rel] if len(
                self._imagens_rel) > 1 else None,
        }
        item = self.lista.item(self._atual)
        if item is not None:
            item.setText(nome or f"(vazia) {slot.id}")

    def _confirmar(self) -> None:
        self._gravar_form()
        self.accept()

    # --- foto + prévia --------------------------------------------------------

    def _escolher_foto(self, zona: int = 0) -> None:
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Foto do item fixo",
            str(SystemRoot().biblioteca_imagens),
            "Imagens (*.png *.webp *.jpg *.jpeg)")
        if not caminho:
            return
        rel = internar_foto_fixa(caminho)
        while len(self._imagens_rel) <= zona:
            self._imagens_rel.append(None)
        self._imagens_rel[zona] = rel
        if zona < len(self._foto_lbls):
            self._foto_lbls[zona].setText(rel)
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
