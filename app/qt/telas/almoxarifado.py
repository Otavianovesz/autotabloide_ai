"""
Almoxarifado — gestão do catálogo (F6.3)
========================================
A lista **virtualizada** dos produtos do banco (carrega por páginas —
milhares de itens não pesam a RAM), com busca, filtro pelo **semáforo de
qualidade** (🔴 sem imagem · 🟡 incompleto · 🟢 ok), painel de edição
completo, **trocar imagem** (curadoria + versionamento da biblioteca),
**histórico de versões** e **"Corrigir nomes (IA)"** em lote
(`enriquecer_banco`). Botão direito com seleção múltipla.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QAbstractListModel, QModelIndex, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.qt.design import tokens as t
from app.qt.design.carregando import OverlayOcupado
from app.qt.design.componentes import EstadoVazio, Painel
from app.qt.design.icones import icone
from app.qt.design.toast import mostrar_toast
from app.qt.telas import servico
from app.qt.telas.curadoria_dialog import CuradoriaDialog
from app.qt.workers import GerenciadorTrabalhos, Trabalhador

_PAGINA = 50
_COR = {"VERDE": t.SUCESSO, "AMARELO": t.ALERTA, "VERMELHO": t.PERIGO}


def _bolinha(cor: str) -> QIcon:
    pm = QPixmap(20, 20)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(cor))
    p.drawEllipse(6, 6, 8, 8)
    p.end()
    return QIcon(pm)


class CatalogoModel(QAbstractListModel):
    """Modelo virtualizado: busca páginas de 50 sob demanda (fetchMore)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._linhas: list[dict] = []
        self._texto = ""
        self._filtro = ""          # "" | VERMELHO | AMARELO
        self._esgotado = False
        self._icones = {cor: _bolinha(hexa) for cor, hexa in _COR.items()}

    # --- API Qt -----------------------------------------------------------------

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._linhas)

    def canFetchMore(self, parent=QModelIndex()) -> bool:
        return not self._esgotado

    def fetchMore(self, parent=QModelIndex()) -> None:
        pagina = servico.listar_catalogo(offset=len(self._linhas),
                                         limite=_PAGINA, texto=self._texto)
        if self._filtro:
            pagina = [d for d in pagina if d["qualidade"] == self._filtro]
        if len(pagina) < _PAGINA:
            self._esgotado = True
        if pagina:
            ini = len(self._linhas)
            self.beginInsertRows(QModelIndex(), ini, ini + len(pagina) - 1)
            self._linhas.extend(pagina)
            self.endInsertRows()

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        d = self._linhas[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            preco = f"  ·  R$ {d['preco']}" if d["preco"] else ""
            return f"{d['nome']}{preco}"
        if role == Qt.ItemDataRole.DecorationRole:
            return self._icones[d["qualidade"]]
        if role == Qt.ItemDataRole.ToolTipRole:
            faltas = []
            if not d["imagem"]:
                faltas.append("sem imagem")
            if not d["preco"]:
                faltas.append("sem preço")
            if not d["categoria"]:
                faltas.append("sem categoria")
            return ", ".join(faltas) or "completo"
        if role == Qt.ItemDataRole.UserRole:
            return d
        return None

    # --- controle ----------------------------------------------------------------

    def redefinir(self, texto: str = "", filtro: str = "") -> None:
        self.beginResetModel()
        self._linhas = []
        self._texto = texto
        self._filtro = filtro
        self._esgotado = False
        self.endResetModel()

    def atualizar_linha(self, linha: int, d: dict) -> bool:
        """False se a linha não existe mais (a lista mudou sob um worker —
        rebusca/exclusão no meio do voo). RG-05: nunca estourar num slot."""
        if not 0 <= linha < len(self._linhas):
            return False
        self._linhas[linha] = d
        ix = self.index(linha)
        self.dataChanged.emit(ix, ix)
        return True


class HistoricoImagensDialog(QDialog):
    """Versões anteriores da imagem do produto; dá para restaurar uma."""

    def __init__(self, produto_id: int, parent=None):
        super().__init__(parent)
        from app.core.paths import SystemRoot
        from app.images.biblioteca import BibliotecaImagens

        self.setWindowTitle("Histórico de imagens")
        self.restaurada: str | None = None
        self._bib = BibliotecaImagens(SystemRoot().biblioteca_imagens)
        self._produto_id = produto_id

        titulo = QLabel("Histórico de imagens")
        titulo.setProperty("papel", "titulo")
        self.lista = QListWidget()
        self.lista.setViewMode(QListWidget.ViewMode.IconMode)
        self.lista.setMovement(QListWidget.Movement.Static)   # RG-10: sem drag
        self.lista.setIconSize(QSize(120, 120))
        self.lista.setResizeMode(QListWidget.ResizeMode.Adjust)
        versoes = self._bib.listar_versoes(produto_id)
        for v in reversed(versoes):                    # mais novas primeiro
            item = QListWidgetItem(QIcon(QPixmap(str(v))), v.stem)
            item.setData(Qt.ItemDataRole.UserRole, str(v))
            self.lista.addItem(item)
        vazio = EstadoVazio("imagem", "Sem versões anteriores",
                            "Troque a imagem e a anterior aparece aqui.")
        vazio.setVisible(not versoes)
        self.lista.setVisible(bool(versoes))

        # Comparador LADO A LADO (polimento F10): a atual × a versão escolhida,
        # em grande — o dono compara ANTES de restaurar, não às cegas.
        def _painel_foto(rotulo: str):
            w = QWidget()
            v = QVBoxLayout(w)
            v.setContentsMargins(0, 0, 0, 0)
            v.setSpacing(t.ESP_1)
            r = QLabel(rotulo)
            r.setProperty("papel", "legenda")
            r.setAlignment(Qt.AlignmentFlag.AlignCenter)
            foto = QLabel("—")
            foto.setAlignment(Qt.AlignmentFlag.AlignCenter)
            foto.setMinimumSize(180, 150)
            v.addWidget(r)
            v.addWidget(foto, 1)
            return w, foto

        caixa_atual, self._foto_atual = _painel_foto("ATUAL (fica se cancelar)")
        caixa_sel, self._foto_sel = _painel_foto("VERSÃO ESCOLHIDA")
        compara = QWidget()
        hc = QHBoxLayout(compara)
        hc.setContentsMargins(0, 0, 0, 0)
        hc.setSpacing(t.ESP_3)
        hc.addWidget(caixa_atual, 1)
        hc.addWidget(caixa_sel, 1)
        compara.setVisible(bool(versoes))
        atual = self._bib.caminho_atual(produto_id)
        if atual and Path(atual).exists():
            self._por_no_rotulo(self._foto_atual, str(atual))
        self.lista.itemSelectionChanged.connect(self._espelhar_selecao)

        restaurar = QPushButton(" Restaurar esta")
        restaurar.setIcon(icone("restaurar", cor=t.ACENTO_TEXTO, tamanho=15))
        restaurar.setProperty("tipo", "primario")
        restaurar.setToolTip("A escolhida vira a atual; a atual vira versão "
                             "(nada se perde)")
        restaurar.clicked.connect(self._restaurar)
        fechar = QPushButton("Fechar")
        fechar.clicked.connect(self.reject)
        botoes = QHBoxLayout()
        botoes.addStretch(1)
        botoes.addWidget(fechar)
        botoes.addWidget(restaurar)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.ESP_4, t.ESP_4, t.ESP_4, t.ESP_4)
        lay.addWidget(titulo)
        lay.addWidget(self.lista, 1)
        lay.addWidget(compara, 2)
        lay.addWidget(vazio, 1)
        lay.addLayout(botoes)
        self.resize(640, 560)

    @staticmethod
    def _por_no_rotulo(rotulo: QLabel, caminho: str) -> None:
        pm = QPixmap(caminho)
        if not pm.isNull():
            rotulo.setPixmap(pm.scaled(
                240, 200, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))

    def _espelhar_selecao(self) -> None:
        sel = self.lista.selectedItems()
        if sel:
            self._por_no_rotulo(self._foto_sel,
                                sel[0].data(Qt.ItemDataRole.UserRole))

    def _restaurar(self) -> None:
        sel = self.lista.selectedItems()
        if not sel:
            return
        caminho = sel[0].data(Qt.ItemDataRole.UserRole)
        self._bib.ingerir(self._produto_id, caminho)   # a atual vira versão
        self.restaurada = caminho
        self.accept()


class AlmoxarifadoTela(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._trabalhos = GerenciadorTrabalhos()
        self._linha_atual = -1
        self._carregando = False

        # --- barra ---------------------------------------------------------------
        barra = QWidget()
        barra.setObjectName("barraFerramentas")
        hb = QHBoxLayout(barra)
        hb.setContentsMargins(t.ESP_3, t.ESP_1 + 2, t.ESP_3, t.ESP_1 + 2)
        hb.setSpacing(t.ESP_2)
        self.busca = QLineEdit()
        self.busca.setPlaceholderText("Buscar produto, marca…")
        # FASE 1 (passo 50): mínimo + teto em vez de fixo (não corta nem engole)
        self.busca.setMinimumWidth(240)
        self.busca.setMaximumWidth(420)
        self.busca.textChanged.connect(self._rebuscar)
        self.filtro = QComboBox()
        self.filtro.addItem("Todos", "")
        self.filtro.addItem("● Sem imagem", "VERMELHO")
        self.filtro.addItem("● Incompletos", "AMARELO")
        self.filtro.currentIndexChanged.connect(self._rebuscar)
        corrigir = QPushButton(" Corrigir nomes (IA)")
        corrigir.setIcon(icone("texto", tamanho=16))
        corrigir.setToolTip("Enriquecer todos os nomes do banco com a IA "
                            "(LM Studio) — persiste no cadastro")
        corrigir.clicked.connect(self._corrigir_nomes)
        categorizar = QPushButton(" Categorizar (IA)")
        categorizar.setIcon(icone("grade", tamanho=16))
        categorizar.setToolTip(
            "F8.1: a IA categoriza SÓ o que está sem categoria; a que você "
            "corrigiu à mão nunca é sobrescrita. Sem palpite fica vazio "
            "(agrupa em “Outros” na Mesa).")
        categorizar.clicked.connect(self._categorizar)
        # R-075 (polimento): a UI do caça-duplicatas que a F9 deixou pronta
        btn_dupl = QPushButton(" Duplicatas")
        btn_dupl.setIcon(icone("duplicar", tamanho=16))
        btn_dupl.setToolTip("Acha produtos repetidos (mesmo EAN ou mesmo "
                            "nome e marca) e funde lado a lado — reversível")
        btn_dupl.clicked.connect(self._cacar_duplicatas)
        # Fase 11: a ponte Excel (R-118) e o painel de inteligência (R-115…126)
        btn_exp_xls = QPushButton(" Exportar Excel")
        btn_exp_xls.setIcon(icone("cofre", tamanho=16))
        btn_exp_xls.setToolTip("Leva o acervo para uma planilha .xlsx (dados, "
                               "sem foto)")
        btn_exp_xls.clicked.connect(self._exportar_excel)
        btn_imp_xls = QPushButton(" Importar Excel…")
        btn_imp_xls.setIcon(icone("abrir", tamanho=16))
        btn_imp_xls.setToolTip("Traz uma planilha de volta — casa por chave "
                               "natural, conflito nunca em silêncio")
        btn_imp_xls.clicked.connect(self._importar_excel)
        btn_intel = QPushButton(" Inteligência")
        btn_intel.setIcon(icone("grade", tamanho=16))
        btn_intel.setToolTip("Histórico de preço, ranking, saúde do acervo "
                             "(só leitura)")
        btn_intel.clicked.connect(self._abrir_inteligencia)
        hb.addWidget(self.busca)
        hb.addWidget(self.filtro)
        hb.addWidget(corrigir)
        hb.addWidget(categorizar)
        hb.addWidget(btn_dupl)
        hb.addWidget(btn_exp_xls)
        hb.addWidget(btn_imp_xls)
        hb.addWidget(btn_intel)
        hb.addStretch(1)

        # --- lista virtualizada -----------------------------------------------------
        self.modelo = CatalogoModel(self)
        self.lista = QListView()
        self.lista.setModel(self.modelo)
        self.lista.setSelectionMode(QListView.SelectionMode.ExtendedSelection)
        self.lista.setUniformItemSizes(True)
        # FASE 1 (passo 43): skeleton ADIADO — só aparece se a primeira
        # página do catálogo demorar mais de 90 ms (nunca pisca à toa)
        from app.qt.design.componentes import Skeleton
        self._esqueleto = Skeleton(linhas=6, altura_linha=40,
                                   parent=self.lista.viewport())
        self._esqueleto.hide()
        self.modelo.rowsInserted.connect(lambda *_: self._esqueleto.hide())
        # FASE 1 (passo 73): catálogo VAZIO ganha ação; busca sem resultado
        # é outro estado (há produtos — o filtro é que não achou)
        from app.qt.design.componentes import EstadoVazio
        btn_vazio_cat = QPushButton(" Importar ofertas na Mesa")
        btn_vazio_cat.setIcon(icone("abrir", tamanho=16))
        btn_vazio_cat.clicked.connect(self._ir_para_mesa)
        self._vazio_catalogo = EstadoVazio(
            "caixa", "Nenhum produto no catálogo",
            "Importe uma oferta na Mesa — a conciliação\n"
            "cadastra os produtos novos aqui.", acao=btn_vazio_cat,
            parent=self.lista.viewport())
        self._vazio_catalogo.hide()
        self._vazio_busca = EstadoVazio(
            "busca", "Nada encontrado",
            "Mude o termo da busca ou o filtro.",
            parent=self.lista.viewport())
        self._vazio_busca.hide()
        self.modelo.rowsInserted.connect(
            lambda *_: (self._vazio_catalogo.hide(),
                        self._vazio_busca.hide()))
        # FASE 1 (passo 76): contador vivo — "+" enquanto há mais páginas
        self.modelo.rowsInserted.connect(lambda *_: self._contar_catalogo())
        self.modelo.modelReset.connect(lambda *_: self._contar_catalogo())
        self.lista.clicked.connect(self._selecionou)
        self.lista.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lista.customContextMenuRequested.connect(self._menu)

        # --- painel do produto ---------------------------------------------------------
        self.foto = QLabel("—")
        self.foto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.foto.setFixedHeight(170)
        # OS F11.5 #27/#28 (R-085): a NOTA da foto (boa/atenção/ruim) com os
        # motivos no tooltip — pequena demais liga o aviso do upscale
        self.nota_foto = QLabel("")
        self.nota_foto.setProperty("papel", "legenda")
        self.nota_foto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nota_foto.setWordWrap(True)
        self.nome = QLineEdit()
        self.marca = QLineEdit()
        self.sabor = QLineEdit()
        self.peso = QLineEdit()
        self.peso.setPlaceholderText("ex.: 500 g · 1,5 kg")
        self.preco = QLineEdit()
        self.preco.setPlaceholderText("ex.: 12,99")
        self.categoria = QLineEdit()
        # RG-41: código de barras — a chave da cascata de imagem (OFF)
        self.ean = QLineEdit()
        self.ean.setPlaceholderText("código de barras (8–14 dígitos)")
        self.ean.setToolTip("EAN/GTIN: com ele, a busca de imagem tenta o "
                            "packshot oficial do Open Food Facts primeiro")
        self.validade = QLineEdit()
        self.validade.setPlaceholderText("dd/mm/aaaa (só p/ cartaz)")
        self.alcool = QCheckBox("Bebida alcoólica")
        self.mais18 = QCheckBox("Selo +18")
        self.marca_propria = QCheckBox("Marca própria (Qualidade Belo Brasil)")
        for campo, attr in [(self.nome, "nome_sanitizado"), (self.marca, "marca"),
                            (self.sabor, "sabor"), (self.preco, "preco_atual"),
                            (self.categoria, "categoria"),
                            (self.ean, "ean")]:
            campo.editingFinished.connect(
                lambda c=campo, a=attr: self._salvar_campo(a, c.text().strip()))
        self.peso.editingFinished.connect(self._salvar_peso)
        self.validade.editingFinished.connect(self._salvar_validade)
        for check, attr in [(self.alcool, "bebida_alcoolica"),
                            (self.mais18, "selo_mais18"),
                            (self.marca_propria, "marca_propria")]:
            check.toggled.connect(
                lambda v, a=attr: self._salvar_campo(a, bool(v)))

        trocar = QPushButton(" Trocar imagem…")
        trocar.setIcon(icone("imagem", tamanho=15))
        trocar.setToolTip("Buscar uma foto nova (web, arquivo, colar, URL)")
        trocar.clicked.connect(self._trocar_imagem)
        historico = QPushButton(" Histórico…")
        historico.setIcon(icone("restaurar", tamanho=15))
        historico.setToolTip("Ver e restaurar versões anteriores da foto — "
                             "com comparador lado a lado")
        historico.clicked.connect(self._historico)
        # Polimento F10: o editor girar/cortar e o Estúdio (packshot) que o
        # modelo deixou prontos sem casca
        ajustar = QPushButton(" Ajustar…")
        ajustar.setIcon(icone("ajustar", tamanho=15))
        ajustar.setToolTip("Girar, espelhar ou cortar a foto atual — a "
                           "anterior fica no histórico")
        ajustar.clicked.connect(self._ajustar_imagem)
        estudio = QPushButton(" Estúdio")
        estudio.setIcon(icone("lampada", tamanho=15))
        estudio.setToolTip("Foto de celular → packshot: remove o fundo, "
                           "normaliza a luz e põe sombra — roda no seu PC")
        estudio.clicked.connect(self._estudio)
        linha_img = QHBoxLayout()
        linha_img.addWidget(trocar)
        linha_img.addWidget(ajustar)
        linha_img.addWidget(estudio)
        linha_img.addWidget(historico)

        form = QFormLayout()
        form.setVerticalSpacing(t.ESP_2)
        form.addRow("Nome", self.nome)
        form.addRow("Marca", self.marca)
        form.addRow("Sabor", self.sabor)
        form.addRow("Peso", self.peso)
        form.addRow("Preço", self.preco)
        form.addRow("Categoria", self.categoria)
        form.addRow("Cód. barras", self.ean)   # RG-41
        form.addRow("Validade", self.validade)
        form.addRow(self.alcool)
        form.addRow(self.mais18)
        form.addRow(self.marca_propria)

        painel = QWidget()
        vp = QVBoxLayout(painel)
        vp.setContentsMargins(0, 0, 0, 0)
        vp.setSpacing(t.ESP_2)
        vp.addWidget(self.foto)
        vp.addWidget(self.nota_foto)
        vp.addLayout(linha_img)
        vp.addLayout(form)
        vp.addStretch(1)
        self._vazio = EstadoVazio("caixa", "Nenhum produto selecionado",
                                  "Clique num item da lista para editar.")
        caixa_painel = QWidget()
        vc = QVBoxLayout(caixa_painel)
        vc.setContentsMargins(0, 0, 0, 0)
        vc.addWidget(self._vazio)
        vc.addWidget(painel)
        self._painel = painel
        painel.hide()

        esquerda = QWidget()
        ve = QVBoxLayout(esquerda)
        ve.setContentsMargins(t.ESP_3, t.ESP_3, t.ESP_3, t.ESP_3)
        self._painel_catalogo = Painel("Catálogo", "caixa", self.lista)
        ve.addWidget(self._painel_catalogo)

        direita = QWidget()
        direita.setObjectName("lateral")
        vd = QVBoxLayout(direita)
        vd.setContentsMargins(t.ESP_3, t.ESP_3, t.ESP_3, t.ESP_3)
        vd.addWidget(Painel("Produto", "propriedades", caixa_painel))

        # FASE 1 (passo 59): painel do produto em splitter com memória
        from app.qt.design.componentes import splitter_com_memoria
        corpo = splitter_com_memoria("almoxarifado", esquerda, direita,
                                     indice_lateral=1)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)
        raiz.addWidget(barra)
        raiz.addWidget(corpo, 1)
        self._overlay = OverlayOcupado(self)
        from app.qt.design.polimento import ordenar_tab
        ordenar_tab(self)               # FASE 1 (passo 66): Tab visual

    # --- lista -----------------------------------------------------------------------

    def showEvent(self, ev) -> None:  # noqa: N802 (Qt)
        """RG-08: o catálogo relê o banco ao aparecer — produto criado na
        Mesa/conciliação entra sem precisar reabrir o app."""
        super().showEvent(ev)
        self._rebuscar()

    def _rebuscar(self) -> None:
        # RG-05: o reset do modelo invalida a linha do painel — soltar a
        # referência ANTES (senão os campos editingFinished e os workers
        # em voo aplicariam edição/imagem no produto ERRADO da nova lista)
        self._linha_atual = -1
        self._painel.hide()
        self._vazio.show()
        self.modelo.redefinir(self.busca.text().strip(),
                              self.filtro.currentData())
        from PySide6.QtCore import QTimer
        QTimer.singleShot(90, self._skeleton_se_vazio)

    def _skeleton_se_vazio(self) -> None:
        """Passo 43: catálogo ainda sem a 1ª página após 90 ms → skeleton
        (banco vazio DE VERDADE não conta — esse é estado vazio, não espera)."""
        if (self.isVisible() and self.modelo.rowCount() == 0
                and self.modelo.canFetchMore()):
            self._esqueleto.setGeometry(self.lista.viewport().rect())
            self._esqueleto.show()
        else:
            self._esqueleto.hide()
        # FASE 1 (passo 73): vazio de verdade → estado vazio COM ação
        vazio_real = (self.modelo.rowCount() == 0
                      and not self.modelo.canFetchMore())
        com_filtro = bool(self.busca.text().strip()
                          or self.filtro.currentData())
        area = self.lista.viewport().rect()
        self._vazio_catalogo.setGeometry(area)
        self._vazio_busca.setGeometry(area)
        self._vazio_catalogo.setVisible(vazio_real and not com_filtro)
        self._vazio_busca.setVisible(vazio_real and com_filtro)

    def _contar_catalogo(self) -> None:
        """Passo 76: o modelo pagina — o número mostra o carregado e ganha
        um "+" honesto enquanto o banco ainda tem páginas."""
        if not hasattr(self, "_painel_catalogo"):
            return                       # ainda no meio do __init__
        n = self.modelo.rowCount()
        mais = "+" if self.modelo.canFetchMore() and n else ""
        self._painel_catalogo.set_titulo(f"Catálogo · {n}{mais}")

    def _ir_para_mesa(self) -> None:
        """Ação do estado vazio: leva à Mesa (onde a importação mora)."""
        shell = self.window()
        if hasattr(shell, "ir_para"):
            shell.ir_para("mesa")
        else:                            # fora do shell (bancada): avisa
            mostrar_toast(self, "Abra a tela Mesa para importar ofertas.")

    def _dado_atual(self) -> dict | None:
        return (self.modelo._linhas[self._linha_atual]
                if 0 <= self._linha_atual < len(self.modelo._linhas) else None)

    def _selecionou(self, index) -> None:
        self._linha_atual = index.row()
        d = self._dado_atual()
        if d is None:
            return
        self._carregando = True
        self._vazio.hide()
        self._painel.show()
        self.nome.setText(d["nome"])
        self.marca.setText(d["marca"])
        self.sabor.setText(d["sabor"])
        peso = f'{d["peso_valor"]} {d["peso_unidade"]}'.strip()
        self.peso.setText(peso)
        self.preco.setText(d["preco"] or "")
        self.categoria.setText(d["categoria"])
        self.ean.setText(d.get("ean", ""))     # RG-41
        self.validade.setText(d["validade"])
        self.alcool.setChecked(d["alcool"])
        self.mais18.setChecked(d["mais18"])
        self.marca_propria.setChecked(d["marca_propria"])
        if d["imagem"] and Path(d["imagem"]).exists():
            pm = QPixmap(d["imagem"]).scaled(
                220, 164, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            self.foto.setPixmap(pm)
            self._mostrar_nota_foto(d["imagem"])
        else:
            self.foto.setPixmap(QPixmap())
            self.foto.setText("sem imagem")
            self.nota_foto.setText("")
            self.nota_foto.setToolTip("")
        self._carregando = False

    def _mostrar_nota_foto(self, caminho: str) -> None:
        """OS F11.5 #27/#28 (R-085): a nota da foto, com cor por faixa e os
        motivos no tooltip; motivo de TAMANHO cita o upscale (F10)."""
        try:
            from app.images.avaliador import ROTULO_NOTA, avaliar_foto
            av = avaliar_foto(caminho)
        except Exception:
            self.nota_foto.setText("")
            return
        cor = {"boa": t.SUCESSO, "atencao": t.ALERTA,
               "ruim": t.PERIGO}[av.nota]
        texto = f"● {ROTULO_NOTA[av.nota]}"
        if av.sugere_upscale:
            texto += " · o upscale do export resolve"
        self.nota_foto.setText(texto)
        self.nota_foto.setStyleSheet(f"color: {cor};")
        self.nota_foto.setToolTip("\n".join(av.motivos) or "Sem ressalvas.")

    # --- edição ------------------------------------------------------------------------

    def _salvar_campo(self, attr: str, valor) -> None:
        d = self._dado_atual()
        if d is None or self._carregando:
            return
        if attr == "preco_atual" and valor == (d["preco"] or ""):
            return
        novo = servico.editar_produto(d["id"], **{attr: valor or None})
        self.modelo.atualizar_linha(self._linha_atual, novo)

    def _salvar_peso(self) -> None:
        """'500 g' / '1,5 kg' → peso_valor + peso_unidade."""
        import re
        d = self._dado_atual()
        if d is None or self._carregando:
            return
        m = re.match(r"\s*([\d.,]+)\s*([a-zA-Z]*)\s*$", self.peso.text())
        valor = m.group(1).replace(",", ".") if m else None
        unidade = (m.group(2) or None) if m else None
        novo = servico.editar_produto(d["id"], peso_valor=valor,
                                      peso_unidade=unidade)
        self.modelo.atualizar_linha(self._linha_atual, novo)

    def _salvar_validade(self) -> None:
        """dd/mm/aaaa → date (vazio limpa)."""
        from datetime import datetime
        d = self._dado_atual()
        if d is None or self._carregando:
            return
        texto = self.validade.text().strip()
        try:
            data = datetime.strptime(texto, "%d/%m/%Y").date() if texto else None
        except ValueError:
            mostrar_toast(self, "Validade no formato dd/mm/aaaa.", tipo="erro")
            return
        novo = servico.editar_produto(d["id"], validade_item=data)
        self.modelo.atualizar_linha(self._linha_atual, novo)

    # --- imagem -------------------------------------------------------------------------

    def _trocar_imagem(self) -> None:
        d = self._dado_atual()
        if d is None:
            return
        # RG-41: com EAN cadastrado, a cascata tenta o packshot oficial antes
        trab = Trabalhador(
            lambda st, n=d["nome"], e=d.get("ean") or None:
            servico.buscar_candidatos_para(n, st, ean=e))
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(lambda cands, dd=d: self._curadoria(dd, cands))
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _curadoria(self, d: dict, candidatos: list[str]) -> None:
        self._overlay.esconder()
        dlg = CuradoriaDialog(d["nome"], candidatos, self, nome_editavel=False)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        tipo, valor = dlg.escolha
        if tipo == "nenhuma":
            return

        def _fluxo(st, v=valor, pid=d["id"]):
            tratada = servico.tratar_imagem(v, st)
            return servico.definir_imagem(pid, tratada, st)

        trab = Trabalhador(_fluxo)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._imagem_trocada)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _imagem_trocada(self, novo: dict) -> None:
        self._overlay.esconder()
        if not self.modelo.atualizar_linha(self._linha_atual, novo):
            # a lista mudou durante o tratamento; o banco JÁ tem a imagem
            mostrar_toast(self, "Imagem salva no produto — a lista mudou "
                                "durante o tratamento, busque para ver.")
            return
        self._selecionou(self.modelo.index(self._linha_atual))
        mostrar_toast(self, "Imagem trocada (a anterior foi para o histórico).")

    def _historico(self) -> None:
        d = self._dado_atual()
        if d is None:
            return
        dlg = HistoricoImagensDialog(d["id"], self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.restaurada:
            novo = servico.editar_produto(d["id"])   # relê (imagem já trocada)
            self.modelo.atualizar_linha(self._linha_atual, novo)
            self._selecionou(self.modelo.index(self._linha_atual))
            mostrar_toast(self, "Versão restaurada.")

    def _ajustar_imagem(self) -> None:
        """Polimento F10: girar/espelhar/cortar a foto ATUAL — o resultado é
        ingerido como nova versão (a anterior fica no histórico, I1)."""
        from app.qt.telas.ajuste_imagem_dialog import AjusteImagemDialog
        d = self._dado_atual()
        if d is None:
            return
        if not (d.get("imagem") and Path(d["imagem"]).exists()):
            mostrar_toast(self, "Este produto ainda não tem foto — use "
                                "“Trocar imagem…” primeiro.", tipo="info")
            return
        dlg = AjusteImagemDialog(d["imagem"], self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        ajustada = dlg.caminho_final()

        def _fluxo(st, caminho=ajustada, pid=d["id"]):
            return servico.definir_imagem(pid, caminho, st)

        trab = Trabalhador(_fluxo)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._imagem_trocada)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _estudio(self) -> None:
        """Polimento F10: a foto atual passa pelo ESTÚDIO (degrau 1 — rembg +
        luz + sombra sintética; CPU, qualquer PC) e vira nova versão. O
        `tratar_estudio` existia sem nenhum chamador de UI."""
        d = self._dado_atual()
        if d is None:
            return
        if not (d.get("imagem") and Path(d["imagem"]).exists()):
            mostrar_toast(self, "Este produto ainda não tem foto — use "
                                "“Trocar imagem…” primeiro.", tipo="info")
            return

        def _fluxo(st, fonte=d["imagem"], pid=d["id"]):
            tratada = servico.tratar_estudio(fonte, st)
            return servico.definir_imagem(pid, tratada, st)

        trab = Trabalhador(_fluxo)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._imagem_trocada)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    # --- lote / menu -------------------------------------------------------------------

    def _corrigir_nomes(self) -> None:
        from app.scripts.enriquecer_banco import enriquecer_banco

        def _rodar(st):
            return enriquecer_banco(log=lambda linha: st(str(linha)[:70]))

        trab = Trabalhador(_rodar)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._nomes_corrigidos)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _nomes_corrigidos(self, resumo: dict) -> None:
        self._overlay.esconder()
        self._rebuscar()
        extra = (f", {resumo['revisar']} p/ revisar (a IA descartou palavra "
                 "— RG-20)" if resumo.get("revisar") else "")
        mostrar_toast(self, f"Nomes: {resumo['atualizados']} corrigidos, "
                            f"{resumo['iguais']} já certos, "
                            f"{resumo['erros']} erros{extra}.")

    def _categorizar(self) -> None:
        """F8.1: lote de categorias — só o que falta; humano nunca é vencido."""
        from app.scripts.enriquecer_banco import categorizar_acervo

        def _rodar(st):
            return categorizar_acervo(log=lambda linha: st(str(linha)[:70]))

        trab = Trabalhador(_rodar)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._categorizado)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _categorizado(self, resumo: dict) -> None:
        self._overlay.esconder()
        self._rebuscar()
        mostrar_toast(self, f"Categorias: {resumo['categorizados']} novas, "
                            f"{resumo['sem_palpite']} sem palpite (→ “Outros”), "
                            f"{resumo['erros']} erros.")

    def _menu(self, pos) -> None:
        index = self.lista.indexAt(pos)
        if not index.isValid():
            return
        selecao = [ix.row() for ix in self.lista.selectedIndexes()] or [index.row()]
        menu = QMenu(self)
        a_editar = menu.addAction(icone("propriedades", tamanho=16), "Editar")
        a_img = menu.addAction(icone("imagem", tamanho=16), "Trocar imagem…")
        a_hist = menu.addAction(icone("restaurar", tamanho=16), "Histórico…")
        menu.addSeparator()
        # R-110/R-113 (Fase 11): do balcão ao PDF num clique
        a_cartaz = menu.addAction(icone("impressora", tamanho=16),
                                  "Cartaz-relâmpago…")
        a_kit = menu.addAction(icone("impressora", tamanho=16),
                               "Kit ponta-de-gôndola…")
        menu.addSeparator()
        rotulo = (f"Excluir {len(selecao)} produtos" if len(selecao) > 1
                  else "Excluir")
        a_del = menu.addAction(icone("lixeira", tamanho=16), rotulo)
        escolha = menu.exec(self.lista.mapToGlobal(pos))
        if escolha == a_editar:
            # RG-09: "Editar" com função real — abre o painel E foca o nome
            self._selecionou(index)
            self.nome.setFocus()
            self.nome.selectAll()
        elif escolha == a_img:
            self._selecionou(index)
            self._trocar_imagem()
        elif escolha == a_hist:
            self._selecionou(index)
            self._historico()
        elif escolha == a_cartaz:
            self._selecionou(index)
            self._cartaz_relampago(kit=False)
        elif escolha == a_kit:
            self._selecionou(index)
            self._cartaz_relampago(kit=True)
        elif escolha == a_del:
            from app.qt.design.componentes import confirmar_destrutivo
            if confirmar_destrutivo(              # passo 78: verbo no botão
                    self, "Excluir produtos",
                    f"{len(selecao)} produto(s) sairão do banco. Não tem volta.",
                    f"Excluir {len(selecao)} produto(s)"):
                ids = [self.modelo._linhas[r]["id"] for r in selecao]
                self._excluir(ids)

    def _excluir(self, ids: list[int]) -> None:
        """RG-05: exclusão fora do thread da UI (com acervo grande, o commit
        no thread da tela era candidato a 'app travou' após exclusões)."""
        def _rodar(st, alvo=list(ids)):
            st(f"Excluindo {len(alvo)} produto(s)…")
            servico.excluir_produtos(alvo)
            return len(alvo)

        trab = Trabalhador(_rodar)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._excluiu)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _excluiu(self, n: int) -> None:
        self._overlay.esconder()
        self._rebuscar()               # também solta a linha do painel (RG-05)
        mostrar_toast(self, f"{n} produto(s) excluído(s).")

    # --- cartaz-relâmpago / kit (R-110/R-113, Fase 11) ---------------------------

    def _cartaz_relampago(self, *, kit: bool = False) -> None:
        """Do produto selecionado ao PDF do cartaz (ou kit) num clique.

        Polimento F11: um diálogo pequeno coleta as OPÇÕES que o serviço sempre
        aceitou (QR opcional R-114, nº de etiquetas do kit) — antes ninguém as
        oferecia (parâmetros órfãos de UI)."""
        from PySide6.QtWidgets import QFileDialog

        from app.qt.telas.relampago_dialog import RelampagoDialog
        d = self._dado_atual()
        if d is None:
            return
        opcoes = RelampagoDialog(d.get("nome") or "?", kit=kit,
                                 preco_por=d.get("preco"), parent=self)
        if opcoes.exec() != RelampagoDialog.DialogCode.Accepted:
            return
        qr_texto = opcoes.qr()
        n_etiquetas = opcoes.n_etiquetas()
        preco_por, preco_de = opcoes.precos()
        base = (d.get("nome") or "cartaz").strip()[:30] or "cartaz"
        seguro = "".join(c if c.isalnum() or c in " -_" else "_" for c in base)
        titulo = "Salvar kit ponta-de-gôndola" if kit else "Salvar cartaz-relâmpago"
        destino, _ = QFileDialog.getSaveFileName(
            self, titulo, f"{'kit' if kit else 'cartaz'}_{seguro}.pdf",
            "PDF (*.pdf)")
        if not destino:
            return
        prod = dict(d)
        # os preços do diálogo mandam (o acervo não guarda o "de" — auditoria)
        if preco_por:
            prod["preco"] = preco_por
        if preco_de:
            prod["preco_de"] = preco_de

        def _rodar(st, prod=prod, destino=destino, kit=kit,
                   qr=qr_texto, n_et=n_etiquetas):
            if kit:
                return servico.gerar_kit_gondola(
                    prod, destino, n_etiquetas=n_et, qr_texto=qr, status_cb=st)
            return servico.cartaz_relampago(
                prod, destino, qr_texto=qr, status_cb=st)

        trab = Trabalhador(_rodar)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._cartaz_pronto)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _cartaz_pronto(self, resultado) -> None:
        self._overlay.esconder()
        caminho, avisos = resultado
        nome = Path(caminho).name
        if avisos:                              # I2: pendências ficam visíveis
            mostrar_toast(
                self, f"Cartaz gerado ({nome}) com {len(avisos)} aviso(s): "
                + "; ".join(avisos[:2]), tipo="info")
        else:
            mostrar_toast(self, f"Cartaz gerado: {nome}")

    # --- caça-duplicatas (R-075, polimento) -------------------------------------

    def _cacar_duplicatas(self) -> None:
        trab = Trabalhador(lambda st: (st("Varrendo o acervo…"),
                                       servico.pares_duplicatas())[1])
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._duplicatas_achadas)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _duplicatas_achadas(self, pares: list) -> None:
        self._overlay.esconder()
        from app.qt.telas.duplicatas_dialog import DuplicatasDialog
        dlg = DuplicatasDialog(pares, self)
        if dlg.exec() != DuplicatasDialog.DialogCode.Accepted:
            return
        escolhidos = dlg.escolhidos()
        if not escolhidos:
            mostrar_toast(self, "Nenhum par marcado — nada foi fundido.",
                          tipo="info")
            return

        def _rodar(st, pares_ids=escolhidos):
            return servico.fundir_duplicatas(pares_ids, st)

        trab = Trabalhador(_rodar)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._duplicatas_fundidas)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _duplicatas_fundidas(self, resumo: dict) -> None:
        self._overlay.esconder()
        self._rebuscar()
        mostrar_toast(self, f"{resumo['fundidos']} par(es) fundido(s) — "
                            f"{resumo['aliases']} apelido(s) migrados; os "
                            "repetidos estão na lixeira.")

    # --- Excel (R-118) e inteligência (Fase 11) ---------------------------------

    def _exportar_excel(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        destino, _ = QFileDialog.getSaveFileName(
            self, "Exportar acervo (Excel)", "acervo.xlsx", "Excel (*.xlsx)")
        if not destino:
            return

        def _rodar(st, destino=destino):
            st("Gravando a planilha…")
            from app.core import excel_acervo
            return excel_acervo.exportar_acervo_xlsx(destino)

        trab = Trabalhador(_rodar)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._excel_exportado)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _excel_exportado(self, caminho) -> None:
        self._overlay.esconder()
        mostrar_toast(self, f"Acervo exportado: {Path(caminho).name}")

    def _importar_excel(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Importar acervo (Excel)", "", "Excel (*.xlsx);;Todos (*.*)")
        if not caminho:
            return

        def _rodar(st, caminho=caminho):
            st("Comparando com o acervo (por chave natural)…")
            from app.core import excel_acervo
            return excel_acervo.analisar_planilha(caminho)

        trab = Trabalhador(_rodar)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._excel_analisado)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _excel_analisado(self, analise) -> None:
        self._overlay.esconder()
        from app.qt.telas.importar_planilha_dialog import ImportarPlanilhaDialog
        if not (analise.novos or analise.conflitos):
            mostrar_toast(self, "Nada a importar — o acervo já bate com a "
                                "planilha.", tipo="info")
            return
        dlg = ImportarPlanilhaDialog(analise, self)
        if dlg.exec() != ImportarPlanilhaDialog.DialogCode.Accepted:
            return
        decisoes = dlg.decisoes()

        def _rodar(st, analise=analise, decisoes=decisoes):
            st("Gravando (casando por chave natural)…")
            from app.core import excel_acervo
            return excel_acervo.aplicar_importacao_planilha(analise, decisoes)

        trab = Trabalhador(_rodar)
        trab.status.connect(self._overlay.mostrar)
        trab.ok.connect(self._excel_importado)
        trab.erro.connect(self._falhou)
        self._trabalhos.rodar(trab)

    def _excel_importado(self, rel) -> None:
        self._overlay.esconder()
        self._rebuscar()
        mostrar_toast(self, rel.resumo())

    def _abrir_inteligencia(self) -> None:
        from app.qt.telas.inteligencia_dialog import InteligenciaDialog
        InteligenciaDialog(parent=self).exec()

    def _falhou(self, msg: str) -> None:
        self._overlay.esconder()
        mostrar_toast(self, msg, tipo="erro")
