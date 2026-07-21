"""
Painel de propriedades + ferramentas de região (F5.3)
=====================================================
Mostra e edita as propriedades da região selecionada (fonte, tamanho, cor,
alinhamento, subtipo/papel do preço, mostrar_moeda, ajuste da imagem). Toda
mudança muta o modelo e recompõe pelo compositor (WYSIWYG).

Também tem os botões "＋" para adicionar uma região de cada tipo à célula.
"""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.qt.design import tokens as t
from app.qt.design.componentes import EstadoVazio
from app.qt.fontes import fontes_bundled, garantir_em_fontes, rotulos_sistema
from app.rendering.model import (
    Ajuste, Alinhamento, PapelPreco, PapelTexto, SubtipoPreco, TipoRegiao,
)


class PainelPropriedades(QWidget):
    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(300)        # FASE 1 (passo 51)
        self.canvas = canvas
        self.reg = None
        self._carregando = False

        # (adicionar região agora fica só na barra de ferramentas, sem duplicar aqui)
        # --- estilo nomeado (F5.7) ---
        self.estilo = QComboBox()
        self.estilo.activated.connect(self._estilo_escolhido)
        self.btn_novo_estilo = QPushButton("Novo…")
        self.btn_novo_estilo.setToolTip(
            "Salvar a tipografia desta região como um estilo nomeado")
        self.btn_novo_estilo.clicked.connect(self._novo_estilo)
        self.btn_atualizar_estilo = QPushButton("Atualizar")
        self.btn_atualizar_estilo.setToolTip(
            "Empurrar a tipografia desta região para o estilo — muda em TODOS "
            "que o usam (ajustes próprios de cada instância são respeitados)")
        self.btn_atualizar_estilo.clicked.connect(self._atualizar_estilo)
        self.btn_restaurar_estilo = QPushButton("Restaurar")
        self.btn_restaurar_estilo.setProperty("tipo", "fantasma")
        self.btn_restaurar_estilo.setToolTip(
            "Descartar os ajustes desta instância; voltar a seguir o estilo")
        self.btn_restaurar_estilo.clicked.connect(self._restaurar_estilo)
        # RG-16: combo em linha própria + botões embaixo — os 4 espremidos
        # na mesma linha saíam cortados ("(ne", "Novo..", "tualiza")
        self.estilo.setToolTip(
            "Estilo de texto nomeado: salve a tipografia (fonte/tamanho/cor) "
            "uma vez e aplique em várias regiões — mudar o estilo muda todas")
        caixa_estilo = QWidget()
        ve_est = QVBoxLayout(caixa_estilo)
        ve_est.setContentsMargins(0, 0, 0, 0)
        ve_est.setSpacing(4)
        ve_est.addWidget(self.estilo)
        linha_botoes = QHBoxLayout()
        linha_botoes.setSpacing(4)
        linha_botoes.addWidget(self.btn_novo_estilo)
        linha_botoes.addWidget(self.btn_atualizar_estilo)
        linha_botoes.addWidget(self.btn_restaurar_estilo)
        linha_botoes.addStretch(1)
        ve_est.addLayout(linha_botoes)

        # --- campos ---
        self.nome = QLineEdit()
        self.nome.textEdited.connect(lambda v: self._set("nome", v))
        self.fonte = QComboBox()
        self._popular_fontes()
        self.fonte.currentIndexChanged.connect(self._fonte_mudou)
        self.tam = QDoubleSpinBox()
        self.tam.setRange(4, 400)
        self.tam.valueChanged.connect(lambda v: self._set("tamanho_max_pt", float(v)))
        # cor: campo hex + amostra clicável que abre o seletor
        self.cor = QLineEdit()
        self.cor.setPlaceholderText("#000000")
        self.cor.editingFinished.connect(self._cor_editada)
        self.amostra_cor = QPushButton()
        self.amostra_cor.setFixedSize(26, 26)
        self.amostra_cor.setToolTip("Escolher cor")
        self.amostra_cor.clicked.connect(self._abrir_seletor_cor)
        caixa_cor = QWidget()
        hc = QHBoxLayout(caixa_cor)
        hc.setContentsMargins(0, 0, 0, 0)
        hc.setSpacing(6)
        hc.addWidget(self.amostra_cor)
        hc.addWidget(self.cor, 1)
        self.alinha = QComboBox()
        self.alinha.addItems([a.value for a in Alinhamento])
        self.alinha.currentTextChanged.connect(lambda v: self._set_enum("alinhamento", Alinhamento, v))

        self.subtipo = QComboBox()
        self.subtipo.addItems([s.value for s in SubtipoPreco])
        self.subtipo.currentTextChanged.connect(lambda v: self._set_enum("subtipo_preco", SubtipoPreco, v))
        self.papel = QComboBox()
        self.papel.addItems([p.value for p in PapelPreco])
        self.papel.currentTextChanged.connect(lambda v: self._set_enum("papel_preco", PapelPreco, v))
        self.moeda = QCheckBox("Mostrar R$ (desligue se a arte já tem)")
        self.moeda.toggled.connect(lambda v: self._set("mostrar_moeda", v))
        self.riscado = QCheckBox("Riscado (preço “de” do cartaz)")
        self.riscado.toggled.connect(lambda v: self._set("riscado", v))

        self.ajuste = QComboBox()
        self.ajuste.addItems([a.value for a in Ajuste])
        self.ajuste.currentTextChanged.connect(lambda v: self._set_enum("ajuste", Ajuste, v))

        # R-036 (Fase 5): máscara de forma (retângulo/arredondado/círculo)
        from app.rendering.model import Mascara
        self.mascara = QComboBox()
        _rot_masc = {"RETANGULO": "Retângulo", "ARREDONDADO": "Cantos arredondados",
                     "CIRCULO": "Círculo"}
        for _m in Mascara:
            self.mascara.addItem(_rot_masc[_m.value], _m)
        self.mascara.setToolTip("Forma por onde a foto aparece — recorte no "
                                "compositor, não muda o retângulo do slot")
        self.mascara.activated.connect(self._mascara_escolhida)
        self.mascara_raio = QDoubleSpinBox()
        self.mascara_raio.setRange(0.0, 60.0)
        self.mascara_raio.setSuffix(" mm")
        self.mascara_raio.setToolTip("Raio dos cantos arredondados")
        self.mascara_raio.valueChanged.connect(
            lambda v: self._set("mascara_raio_mm", float(v)))
        # R-032: centralizar a foto na caixa prevista pela arte de fundo
        self.btn_centralizar = QPushButton("Centralizar na arte")
        self.btn_centralizar.setToolTip(
            "Move a região para o centro da caixa da arte de fundo")
        self.btn_centralizar.clicked.connect(self._centralizar_na_arte)

        # R-035 (pill) + R-034 (sombra/contorno): legibilidade do texto na foto
        self.pill = QCheckBox("Pílula atrás do texto")
        self.pill.setToolTip("Faixa semitransparente atrás do texto, para ler "
                             "sobre a foto")
        self.pill.toggled.connect(lambda v: self._set("pill", v))
        self.pill_opac = QDoubleSpinBox()
        self.pill_opac.setRange(0, 255)
        self.pill_opac.setDecimals(0)
        self.pill_opac.setToolTip("Opacidade da pílula (0 = transparente, "
                                  "255 = sólida)")
        self.pill_opac.valueChanged.connect(
            lambda v: self._set("pill_opacidade", int(v)))
        self.pill_cor_btn = self._botao_cor("pill_cor")
        self.sombra = QCheckBox("Sombra no texto")
        self.sombra.toggled.connect(lambda v: self._set("sombra", v))
        self.contorno = QCheckBox("Contorno no texto")
        self.contorno.toggled.connect(lambda v: self._set("contorno", v))
        self.efeito_cor_btn = self._botao_cor("cor_efeito")

        # RG-57 (Fase 5): PAPEL do texto legal — recategorizar sem recriar
        # (mesma escolha do diálogo de criação; espelha e muda o estado).
        from app.qt.design.papel_texto_ui import ORDEM_PAPEIS, ROTULO_PAPEL
        self.papel_texto = QComboBox()
        for _p in ORDEM_PAPEIS:
            self.papel_texto.addItem(ROTULO_PAPEL[_p], _p)
        self.papel_texto.setToolTip(
            "O que este campo é: aviso legal, validade de/até, dica da IA ou "
            "texto livre — decide o que o compositor desenha")
        self.papel_texto.activated.connect(self._papel_texto_escolhido)

        # A1 (ORDEM_F5_8): texto FIXO do layout p/ TEXTO_LEGAL ("Fica a Dica")
        self.texto_fixo = QLineEdit()
        self.texto_fixo.setPlaceholderText("vazio = usa a validade do projeto")
        self.texto_fixo.editingFinished.connect(
            lambda: self._set("texto_fixo", self.texto_fixo.text().strip() or None))
        # RG-25: a IA escreve o "Fica a Dica" com os itens da oferta, no
        # tamanho que CABE na região (limite derivado de área ÷ fonte)
        self.btn_dica = QPushButton(" Gerar dica (IA)")
        self.btn_dica.setToolTip(
            "A IA escreve uma dica/receita curta com os itens da oferta — "
            "o texto respeita o que cabe NESTA região; edite depois à vontade")
        self.btn_dica.clicked.connect(self._gerar_dica)
        # R-083 (polimento): o ESTILO da dica que a F9 deixou pronto no motor
        # (receita/economia/curiosidade) — a UI nunca o oferecia
        from app.ai.enriquecimento import ESTILOS_DICA
        self.estilo_dica = QComboBox()
        self.estilo_dica.setToolTip(
            "O tom da dica: receita rápida, dica de economia ou curiosidade")
        for chave in ESTILOS_DICA:
            self.estilo_dica.addItem(chave.capitalize(), chave)
        caixa_fixo = QWidget()
        vf = QVBoxLayout(caixa_fixo)
        vf.setContentsMargins(0, 0, 0, 0)
        vf.setSpacing(4)
        vf.addWidget(QLabel("Papel:"))
        vf.addWidget(self.papel_texto)
        vf.addWidget(self.texto_fixo)
        linha_dica = QWidget()
        hd = QHBoxLayout(linha_dica)
        hd.setContentsMargins(0, 0, 0, 0)
        hd.setSpacing(4)
        hd.addWidget(self.estilo_dica)
        hd.addWidget(self.btn_dica, 1)
        vf.addWidget(linha_dica)

        # RG-12: rotação do conteúdo em torno do centro (a data deitada = 90°)
        self.rotacao = QDoubleSpinBox()
        self.rotacao.setRange(-180.0, 180.0)
        self.rotacao.setSingleStep(15.0)
        self.rotacao.setSuffix("°")
        self.rotacao.setToolTip("Gira o conteúdo em torno do centro da região "
                                "(sentido horário; 90° = texto deitado)")
        self.rotacao.valueChanged.connect(
            lambda v: self._set("rotacao_graus", float(v)))

        # RG-18: o campo mostra o TETO; o desenho usa o ajustado (só-reduz) —
        # este rótulo conta o efetivo quando difere ("confundiu" na auditoria)
        self.tam_efetivo = QLabel("")
        self.tam_efetivo.setProperty("papel", "legenda")
        caixa_tam = QWidget()
        vt = QVBoxLayout(caixa_tam)
        vt.setContentsMargins(0, 0, 0, 0)
        vt.setSpacing(1)
        vt.addWidget(self.tam)
        vt.addWidget(self.tam_efetivo)

        # RG-16/17: rótulos que explicam + tooltip em todo controle
        self.nome.setToolTip("Rótulo desta camada no painel Camadas "
                             "(não aparece no tabloide)")
        self.fonte.setToolTip("Fonte do texto — as do sistema entram na "
                              "primeira abertura da lista")
        self.tam.setToolTip("Tamanho MÁXIMO da fonte (pt) — o desenho reduz "
                            "sozinho até o texto caber na região")
        self.alinha.setToolTip("Alinhamento do texto dentro da região "
                               "(JUSTIFICADO estica as linhas até a borda)")
        self.subtipo.setToolTip("SEPARADO = inteiro grande + centavos "
                                "pequenos · COMPLETO = “R$ 19,90” corrido")
        self.papel.setToolTip("DE = preço antigo (riscável) · POR = preço da "
                              "oferta · UNICO = preço só")
        self.ajuste.setToolTip("CONTER = a foto cabe inteira · PREENCHER = "
                               "cobre a região (pode cortar borda)")
        self.texto_fixo.setToolTip("Texto do LAYOUT (ex.: “Fica a Dica”) — "
                                   "desenha até em célula vazia")

        form = QFormLayout()
        form.setVerticalSpacing(t.ESP_2)
        # FASE 1 (passo 51): rótulo sobe para a linha de cima quando aperta
        # (nunca rótulo truncado ao lado do campo)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.addRow("Rótulo da camada", self.nome)   # era "Nome: Nome" (RG-16)
        form.addRow("Estilo", caixa_estilo)
        form.addRow("Fonte", self.fonte)
        form.addRow("Tamanho", caixa_tam)
        form.addRow("Cor", caixa_cor)
        form.addRow("Alinhar", self.alinha)
        # RG-14: peso/variante da família ("quero Black") — lista as irmãs
        # da fonte atual; as do sistema entram na 1ª abertura (padrão RG-01)
        self.peso = QComboBox()
        self.peso.setToolTip("Peso/variante da família da fonte "
                             "(Black, Bold, Light…)")
        self.peso.activated.connect(self._peso_escolhido)
        self._pesos_sistema_ok = False
        self.peso.showPopup = self._abrir_combo_pesos

        form.addRow("Texto fixo", caixa_fixo)        # linha 6: só TEXTO_LEGAL
        form.addRow("Rotação", self.rotacao)         # linha 7: qualquer região
        form.addRow("Peso", self.peso)               # linha 8: regiões de texto
        self._form = form   # linhas 1..5 = estilo/fonte/tamanho/cor/alinhar (texto)
        caixa_form = QWidget()
        caixa_form.setLayout(form)
        self._caixa_form = caixa_form

        # FASE 1 (passo 45): seções recolhíveis com animação de altura
        from app.qt.design.componentes import SecaoRecolhivel
        corpo_preco = QWidget()
        fp = QFormLayout(corpo_preco)
        fp.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        fp.addRow("Subtipo", self.subtipo)
        fp.addRow("Papel", self.papel)
        fp.addRow(self.moeda)
        fp.addRow(self.riscado)
        self.grp_preco = SecaoRecolhivel("Preço", corpo_preco)

        corpo_img = QWidget()
        fi = QFormLayout(corpo_img)
        fi.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        fi.addRow("Ajuste", self.ajuste)
        fi.addRow("Máscara", self.mascara)
        fi.addRow("Raio", self.mascara_raio)
        fi.addRow(self.btn_centralizar)
        self.grp_img = SecaoRecolhivel("Imagem", corpo_img)

        # R-034/R-035: legibilidade do texto sobre a foto (pill + sombra/contorno)
        corpo_leg = QWidget()
        fl = QFormLayout(corpo_leg)
        fl.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        fl.addRow(self.pill)
        fl.addRow("Opacidade", self.pill_opac)
        fl.addRow("Cor da pílula", self.pill_cor_btn)
        fl.addRow(self.sombra)
        fl.addRow(self.contorno)
        fl.addRow("Cor do efeito", self.efeito_cor_btn)
        self.grp_leg = SecaoRecolhivel("Legibilidade", corpo_leg)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.vazio = EstadoVazio(
            "propriedades", "Nada selecionado",
            "Clique numa região do layout para\neditar as propriedades dela.")
        self.tipo_lbl = QLabel("(nada selecionado)")
        self.tipo_lbl.setProperty("papel", "legenda")
        lay.addWidget(self.vazio)
        lay.addWidget(self.tipo_lbl)
        lay.addWidget(caixa_form)
        lay.addWidget(self.grp_preco)
        lay.addWidget(self.grp_img)
        lay.addWidget(self.grp_leg)
        # RG-17: a legenda dos pontinhos do canvas (o dono via cores e não
        # sabia o que significavam)
        legenda = QLabel(
            f'<span style="color:{t.ACENTO}">●</span> célula com ajuste '
            f'próprio &nbsp;·&nbsp; <span style="color:{t.GUIA_SNAP}">●</span> '
            f'conteúdo trocado só nela<br>'
            f'<span style="color:{t.ACENTO}">▭</span> contorno âmbar = '
            f'célula-mestre (editar propaga)')
        legenda.setProperty("papel", "legenda")
        legenda.setWordWrap(True)
        lay.addWidget(legenda)
        lay.addStretch(1)

        canvas.selecao_mudou.connect(self.mostrar)
        self.mostrar(None)
        from app.qt.design.polimento import ordenar_tab
        ordenar_tab(self)               # FASE 1 (passo 66): Tab visual

    # --- máscara / legibilidade / centralizar (Fase 5, Bloco B) -----------

    def _botao_cor(self, attr: str) -> "QPushButton":
        """Botão que abre o seletor de cor e grava o hex no atributo `attr`."""
        b = QPushButton("Cor…")

        def _abrir():
            if self.reg is None:
                return
            atual = QColor(getattr(self.reg, attr, "#000000"))
            cor = QColorDialog.getColor(atual, self, "Escolher cor")
            if cor.isValid():
                self._set(attr, cor.name())
                b.setStyleSheet(f"background:{cor.name()};")
        b.clicked.connect(_abrir)
        return b

    def _mascara_escolhida(self) -> None:
        if self.reg is None:
            return
        self._set("mascara", self.mascara.currentData())   # enum vem no itemData

    def _centralizar_na_arte(self) -> None:
        """R-032: centraliza a região na caixa da arte (a página, no cartaz)."""
        if self.reg is not None and hasattr(self.canvas, "centralizar_na_arte"):
            self.canvas.centralizar_na_arte(self.reg)

    # --- cor ---------------------------------------------------------------

    def _pintar_amostra(self, cor_hex: str) -> None:
        cor = QColor(cor_hex)
        if not cor.isValid():
            cor = QColor("#000000")
        self.amostra_cor.setStyleSheet(
            f"background: {cor.name()}; border: 1px solid {t.BORDA_FORTE};"
            f"border-radius: 5px;")

    def _cor_editada(self) -> None:
        import re

        from app.qt.design import tokens as tk
        texto = self.cor.text().strip()
        # A4 (ORDEM_F5_8): valida #RRGGBB — inválido ("##ffffff") não aplica
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", texto):
            self.cor.setStyleSheet(f"border: 2px solid {tk.PERIGO};")
            self.cor.setToolTip("Cor no formato #RRGGBB (ex.: #FFFFFF)")
            return
        self.cor.setStyleSheet("")
        self.cor.setToolTip("")
        self._pintar_amostra(texto)
        self._set("cor", texto)

    def _abrir_seletor_cor(self) -> None:
        if self.reg is None:
            return
        cor = QColorDialog.getColor(QColor(self.reg.cor), self, "Cor do texto")
        if cor.isValid():
            self.cor.setText(cor.name())
            self._pintar_amostra(cor.name())
            self._set("cor", cor.name())

    def _popular_fontes(self) -> None:
        """No BOOT, só as fontes bundled (/fontes) — a varredura das ~3.300
        fontes do sistema custava ~1s e atrasava a janela (RG-01). As fontes
        do sistema entram na PRIMEIRA abertura do combo (com cache em disco,
        as aberturas seguintes são instantâneas)."""
        self._carregando = True
        self.fonte.clear()
        for nome in fontes_bundled():
            self.fonte.addItem(nome, nome)                     # valor = nome do arquivo
        self._carregando = False
        self._fontes_sistema_ok = False
        self.fonte.showPopup = self._abrir_combo_fontes        # adia a varredura

    def _abrir_combo_fontes(self) -> None:
        """1ª abertura do combo: carrega as fontes do sistema (fora do boot)."""
        if not self._fontes_sistema_ok:
            self._fontes_sistema_ok = True
            atual = self.fonte.currentIndex()
            self._carregando = True
            for rotulo in rotulos_sistema():                   # cache em disco
                self.fonte.addItem(f"⤓ {rotulo}", ("sys", rotulo))
            self.fonte.setCurrentIndex(atual)
            self._carregando = False
        type(self.fonte).showPopup(self.fonte)                 # o popup de verdade

    def _selecionar_fonte(self, nome_arquivo: str) -> None:
        for i in range(self.fonte.count()):
            if self.fonte.itemData(i) == nome_arquivo:
                self.fonte.setCurrentIndex(i)
                return
        self.fonte.insertItem(0, nome_arquivo, nome_arquivo)   # recém-copiada
        self.fonte.setCurrentIndex(0)

    def _fonte_mudou(self, index: int) -> None:
        if self._carregando or self.reg is None:
            return
        data = self.fonte.itemData(index)
        if isinstance(data, tuple) and data and data[0] == "sys":
            nome = garantir_em_fontes(data[1])   # copia p/ /fontes -> sempre carrega no Pillow
            if nome is None:
                return
            self._carregando = True
            self.fonte.setItemText(index, nome)
            self.fonte.setItemData(index, nome)
            self._carregando = False
            self.reg.fonte = nome
        else:
            self.reg.fonte = data
        if self.reg.estilo:                     # F5.7: override da instância
            self.reg.overrides_estilo.add("fonte")
            self.btn_restaurar_estilo.setVisible(True)
        self.canvas.notificar_edicao(self.reg, "fonte")
        self._popular_pesos()                   # RG-14: a família pode ter mudado

    def mostrar(self, reg) -> None:
        self.reg = reg
        self._carregando = True
        self.vazio.setVisible(reg is None)          # estado vazio com craft
        self.tipo_lbl.setVisible(reg is not None)
        self._caixa_form.setVisible(reg is not None)
        if reg is None:
            self.tipo_lbl.setText("")
        else:
            self.tipo_lbl.setText(f"Tipo: {reg.tipo.value}")
            self.nome.setText(reg.nome)
            self._selecionar_fonte(reg.fonte)
            self.tam.setValue(reg.tamanho_max_pt)
            self.cor.setText(reg.cor)
            self._pintar_amostra(reg.cor)
            self.alinha.setCurrentText(reg.alinhamento.value)
            self.subtipo.setCurrentText(reg.subtipo_preco.value)
            self.papel.setCurrentText(reg.papel_preco.value)
            self.moeda.setChecked(reg.mostrar_moeda)
            self.riscado.setChecked(reg.riscado)
            self.ajuste.setCurrentText(reg.ajuste.value)
            self.rotacao.setValue(reg.rotacao_graus)   # RG-12
            # Bloco B: máscara/raio (imagem) + pill/sombra/contorno (texto)
            im = self.mascara.findData(reg.mascara)
            if im >= 0:
                self.mascara.setCurrentIndex(im)
            self.mascara_raio.setValue(reg.mascara_raio_mm)
            self.pill.setChecked(reg.pill)
            self.pill_opac.setValue(reg.pill_opacidade)
            self.sombra.setChecked(reg.sombra)
            self.contorno.setChecked(reg.contorno)
        self.grp_preco.setVisible(reg is not None and reg.tipo == TipoRegiao.PRECO)
        self.grp_img.setVisible(reg is not None and reg.tipo == TipoRegiao.IMAGEM)
        # campos de texto (estilo/fonte/tamanho/cor/alinhar) só p/ regiões de texto
        texto = reg is not None and reg.tipo in (
            TipoRegiao.NOME, TipoRegiao.UNIDADE, TipoRegiao.PRECO, TipoRegiao.TEXTO_LEGAL
        )
        # legibilidade (pill/sombra/contorno) só p/ regiões de texto
        self.grp_leg.setVisible(texto)
        for linha in (1, 2, 3, 4, 5):
            self._form.setRowVisible(linha, texto)
        # linha 6 (texto fixo): exclusiva do TEXTO_LEGAL (A1)
        eh_legal = reg is not None and reg.tipo == TipoRegiao.TEXTO_LEGAL
        self._form.setRowVisible(6, eh_legal)
        if eh_legal:
            self.texto_fixo.setText(reg.texto_fixo or "")
            idx = self.papel_texto.findData(reg.papel_texto)
            if idx >= 0:
                self.papel_texto.setCurrentIndex(idx)
        self._form.setRowVisible(8, texto)           # RG-14: peso da família
        if texto:
            self._popular_estilos()
            self._popular_pesos()
        self._atualizar_tamanho_efetivo()            # RG-18
        self._carregando = False

    def _papel_texto_escolhido(self) -> None:
        """RG-57 (passo 11): recategoriza o papel do texto legal — pelo canvas,
        que recompõe (prévia ao vivo) e repinta o badge. `activated` só dispara
        na ação do usuário, então não precisa do guard de `_carregando`."""
        if self.reg is None:
            return
        self.canvas.definir_papel_texto(self.reg, self.papel_texto.currentData())

    def _gerar_dica(self) -> None:
        """RG-25: worker de IA → texto_fixo (a UI nunca congela)."""
        reg = self.reg
        if reg is None:
            return
        from app.ai.enriquecimento import gerar_dica, limite_caracteres
        from app.qt.design.toast import mostrar_toast
        from app.qt.telas import servico
        from app.qt.workers import GerenciadorTrabalhos, Trabalhador

        motor = servico._motor_se_disponivel()
        if motor is None:
            mostrar_toast(self, "LM Studio não acessível — escreva a dica à "
                                "mão ou ligue a IA.", tipo="erro")
            return
        nomes = self.canvas.nomes_dos_itens()
        if not nomes:
            mostrar_toast(self, "Sem itens compostos ainda — preencha a grade "
                                "antes de gerar a dica.", tipo="erro")
            return
        limite = limite_caracteres(reg.rect.larg_mm, reg.rect.alt_mm,
                                   reg.tamanho_max_pt)
        if not hasattr(self, "_trabalhos"):
            self._trabalhos = GerenciadorTrabalhos()   # RG-05b cobre o shutdown
        self.btn_dica.setEnabled(False)
        self.btn_dica.setText(" Gerando…")
        # R-083 (polimento): o estilo escolhido no combo muda o TOM da dica;
        # o texto atual entra em `evitar` (memória — não repete a mesma dica)
        estilo = self.estilo_dica.currentData()
        evitar = [x for x in (self.texto_fixo.text().strip(),) if x]
        trab = Trabalhador(lambda st: gerar_dica(nomes, limite, motor,
                                                 estilo=estilo, evitar=evitar))

        def _pronto(dica):
            self.btn_dica.setEnabled(True)
            self.btn_dica.setText(" Gerar dica (IA)")
            if not dica:
                mostrar_toast(self, "A IA não devolveu dica — tente de novo "
                                    "ou escreva à mão.", tipo="erro")
                return
            if self.reg is reg:            # a seleção pode ter mudado no voo
                self.texto_fixo.setText(dica)
            reg.texto_fixo = dica
            self.canvas.notificar_edicao(reg, "texto_fixo")
            mostrar_toast(self, f"Dica gerada ({len(dica)} caracteres — "
                                "cabe na região). Edite à vontade.")

        trab.ok.connect(_pronto)
        trab.erro.connect(lambda _m: (_pronto(None)))
        self._trabalhos.rodar(trab)

    def _atualizar_tamanho_efetivo(self) -> None:
        """RG-18: mostra o tamanho que o desenho USA quando o ajuste reduziu."""
        reg = self.reg
        efetivo = (self.canvas.tamanho_efetivo_pt(reg)
                   if reg is not None else None)
        if efetivo is not None and efetivo < reg.tamanho_max_pt - 0.25:
            self.tam_efetivo.setText(
                f"desenhado a {efetivo:.0f} pt (reduziu para caber)")
        else:
            self.tam_efetivo.setText("")

    # --- peso/variante da família (RG-14) -------------------------------------

    def _popular_pesos(self) -> None:
        from app.qt.fontes import familia_estilo, variantes_bundled

        self.peso.blockSignals(True)
        self.peso.clear()
        if self.reg is not None:
            for estilo, arq in variantes_bundled(self.reg.fonte):
                self.peso.addItem(estilo, arq)
            ix = self.peso.findData(self.reg.fonte)
            if ix < 0:                 # a atual sempre aparece selecionada
                self.peso.insertItem(0, familia_estilo(self.reg.fonte)[1],
                                     self.reg.fonte)
                ix = 0
            self.peso.setCurrentIndex(ix)
        self.peso.blockSignals(False)
        self._pesos_sistema_ok = False

    def _abrir_combo_pesos(self) -> None:
        """1ª abertura: junta as variantes instaladas no sistema (a varredura
        é paga aqui, nunca no boot — mesma técnica do combo de fontes)."""
        if not self._pesos_sistema_ok and self.reg is not None:
            self._pesos_sistema_ok = True
            from app.qt.fontes import variantes_sistema
            atual = self.peso.currentIndex()
            for estilo, rotulo in variantes_sistema(self.reg.fonte):
                self.peso.addItem(f"⤓ {estilo}", ("sys", rotulo))
            self.peso.setCurrentIndex(atual)
        type(self.peso).showPopup(self.peso)

    def _peso_escolhido(self, index: int) -> None:
        if self._carregando or self.reg is None:
            return
        data = self.peso.itemData(index)
        if isinstance(data, tuple) and data and data[0] == "sys":
            from app.qt.fontes import garantir_em_fontes
            nome = garantir_em_fontes(data[1])   # copia p/ /fontes
            if nome is None:
                return
        else:
            nome = data
        self._carregando = True                  # o combo de fonte acompanha
        self._selecionar_fonte(nome)             # sem disparar edição dupla
        self._carregando = False
        self._set("fonte", nome)

    # --- estilos nomeados (F5.7) --------------------------------------------------

    def _popular_estilos(self) -> None:
        reg = self.reg
        self.estilo.blockSignals(True)
        self.estilo.clear()
        self.estilo.addItem("(nenhum)", None)
        for nome in sorted(self.canvas._layout.estilos if self.canvas._layout else []):
            self.estilo.addItem(nome, nome)
        atual = reg.estilo if reg is not None else None
        ix = self.estilo.findData(atual)
        self.estilo.setCurrentIndex(ix if ix >= 0 else 0)
        self.estilo.blockSignals(False)
        tem = reg is not None and bool(reg.estilo)
        self.btn_atualizar_estilo.setEnabled(tem)
        self.btn_restaurar_estilo.setVisible(
            tem and bool(reg.overrides_estilo))

    def _estilo_escolhido(self, _ix: int) -> None:
        if self._carregando or self.reg is None:
            return
        from app.rendering.estilos import aplicar_estilo, desvincular, estilos_do_layout
        nome = self.estilo.currentData()
        if nome is None:
            desvincular(self.reg)
        else:
            est = estilos_do_layout(self.canvas._layout).get(nome)
            if est is None:
                return
            aplicar_estilo(self.reg, est, respeitar_overrides=False)
        self.canvas.notificar_edicao(self.reg, "estilo")
        self.mostrar(self.reg)          # reflete fonte/tamanho/cor novos

    def _novo_estilo(self) -> None:
        if self.reg is None:
            return
        from PySide6.QtWidgets import QInputDialog

        from app.rendering.estilos import estilo_da_regiao
        nome, ok = QInputDialog.getText(self, "Novo estilo",
                                        "Nome do estilo (ex.: Estilo Preço):")
        if not ok or not nome.strip():
            return
        est = estilo_da_regiao(self.reg, nome.strip())
        self.reg.estilo = est.nome
        self.reg.overrides_estilo = set()
        self.canvas.definir_estilo_layout(est)
        self.mostrar(self.reg)

    def _atualizar_estilo(self) -> None:
        if self.reg is None or not self.reg.estilo:
            return
        from app.rendering.estilos import estilo_da_regiao
        self.reg.overrides_estilo = set()   # esta região vira a referência
        est = estilo_da_regiao(self.reg, self.reg.estilo)
        self.canvas.definir_estilo_layout(est)
        self.mostrar(self.reg)

    def _restaurar_estilo(self) -> None:
        if self.reg is None:
            return
        if self.canvas.restaurar_estilo(self.reg):
            self.mostrar(self.reg)

    def _set(self, attr: str, valor) -> None:
        if self._carregando or self.reg is None:
            return
        setattr(self.reg, attr, valor)
        # F5.7: ajuste local numa região COM estilo vira override da instância
        if self.reg.estilo and attr in ("fonte", "tamanho_max_pt", "cor"):
            self.reg.overrides_estilo.add(attr)
            self.btn_restaurar_estilo.setVisible(True)
        self.canvas.notificar_edicao(self.reg, attr)
        self._atualizar_tamanho_efetivo()   # RG-18: reflete a edição na hora

    def _set_enum(self, attr: str, enum, valor: str) -> None:
        if self._carregando or self.reg is None:
            return
        setattr(self.reg, attr, enum(valor))
        self.canvas.notificar_edicao(self.reg, attr)
