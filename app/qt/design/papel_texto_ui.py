"""Campos de texto com PAPEL nomeado (RG-57/R-153, Fase 5 — Bloco A).

Ao criar uma região de texto legal, o dono escolhe — em português, com prévia —
para que ela serve. A escolha grava ``papel_texto`` na região; o editor exibe
um badge permanente (cor + ícone + nome). Aqui moram:

  * os RÓTULOS nomeados (o que o diálogo mostra) e os EXEMPLOS de prévia;
  * os PRESETS de aviso legal (bebida/sorteio/genérico);
  * ``badge_de_papel`` — a aparência do badge (dado puro, testável);
  * o ``DialogoPapelTexto`` e o atalho ``escolher_papel_texto``.

As partes de dado (rótulos, exemplos, presets, badge) são puras — testáveis
sem Qt. O +18 automático de bebida NÃO vem daqui: continua pelo SELO (passo 9).
"""

from __future__ import annotations

from app.rendering.model import PapelTexto

# Rótulos NOMEADOS, exatamente como o diálogo oferece (passo 2).
ROTULO_PAPEL: dict[PapelTexto, str] = {
    PapelTexto.LEGAL: "Aviso legal",
    PapelTexto.VALIDADE: "Validade da oferta (de/até)",
    PapelTexto.DICA: "Fica a Dica (a IA escreve)",
    PapelTexto.OBSERVACAO: "Observação do item (limite por cliente…)",
    PapelTexto.LIVRE: "Texto livre",
}

# Ordem em que aparecem no diálogo (aviso legal primeiro; livre por último).
ORDEM_PAPEIS: list[PapelTexto] = [
    PapelTexto.LEGAL, PapelTexto.VALIDADE, PapelTexto.DICA,
    PapelTexto.OBSERVACAO, PapelTexto.LIVRE,
]

# Exemplo real mostrado na prévia de cada papel (passo 3).
EXEMPLO_PAPEL: dict[PapelTexto, str] = {
    PapelTexto.LEGAL: "Bebida alcoólica — venda proibida para menores de 18 anos",
    PapelTexto.VALIDADE: "Oferta válida de 17/07 a 20/07",
    PapelTexto.DICA: "Combina com pão quentinho e um café passado na hora",
    PapelTexto.OBSERVACAO: "Limite de 2 unidades por cliente",
    PapelTexto.LIVRE: "(o que você digitar aparece aqui)",
}

# Presets de aviso legal (passo 9). Chave = rótulo no combo; valor = texto.
PRESETS_LEGAIS: dict[str, str] = {
    "Bebida alcoólica": "Bebida alcoólica. Venda proibida para menores de 18 anos.",
    "Sorteio / promoção": ("Promoção válida enquanto durarem os estoques. "
                           "Consulte o regulamento na loja."),
    "Aviso genérico": ("Imagens meramente ilustrativas. Ofertas válidas para "
                       "as unidades participantes, enquanto durarem os estoques."),
}

# Rótulo curto do badge, por papel (o nome longo fica no diálogo/tooltip).
_ROTULO_CURTO: dict[PapelTexto, str] = {
    PapelTexto.LEGAL: "Legal",
    PapelTexto.VALIDADE: "Validade",
    PapelTexto.DICA: "Dica",
    PapelTexto.OBSERVACAO: "Observação",
    PapelTexto.LIVRE: "Livre",
    PapelTexto.DESCONTO: "Desconto",    # F11: papel técnico do cartaz (−%)
}

# Ícone do badge, por papel (nomes de app.qt.design.icones).
_ICONE_PAPEL: dict[PapelTexto, str] = {
    PapelTexto.LEGAL: "alerta_circulo",
    PapelTexto.VALIDADE: "calendario",
    PapelTexto.DICA: "lampada",
    PapelTexto.OBSERVACAO: "paragrafo",
    PapelTexto.LIVRE: "paragrafo",
    PapelTexto.DESCONTO: "preco",
}


def badge_de_papel(papel: PapelTexto) -> tuple[str, str, str]:
    """(rótulo curto, cor, nome-do-ícone) do badge — cor lida do TEMA ATUAL
    (âmbar=legal · azul=validade · violeta=dica · neutro=livre, passo 6).

    GATE 1 da ordem F11.5: o dict de cor só mapeava 4 papéis — escolher
    "Observação do item" (que SEMPRE esteve no diálogo) estourava KeyError
    NO PAINT e travava a repintura da cena; a região DESCONTO do cartaz
    (F11) estouraria igual ao abrir o layout no Ateliê. Agora TODO papel do
    enum tem cor, e um papel futuro cai num neutro são em vez de derrubar o
    editor ("verde com crash não é verde")."""
    from app.qt.design import tokens as t
    cor = {
        PapelTexto.LEGAL: t.ACENTO,        # âmbar
        PapelTexto.VALIDADE: t.SELECAO,    # azul
        PapelTexto.DICA: t.GUIA_SNAP,      # violeta
        PapelTexto.OBSERVACAO: t.INFO,     # azul-informativo (nota do item)
        PapelTexto.LIVRE: t.TEXTO_3,       # neutro
        PapelTexto.DESCONTO: t.PERIGO,     # o vermelho do −% (cartaz)
    }.get(papel, t.TEXTO_3)
    return (_ROTULO_CURTO.get(papel, str(papel.value).capitalize()),
            cor,
            _ICONE_PAPEL.get(papel, "paragrafo"))


def pill_padrao_do_tema() -> tuple[str, int]:
    """OS F11.5 #24: a SUGESTÃO inicial da pill segue o tema da UI — no claro
    a faixa clássica escura (#000000/128); no escuro, o azul-carvão da casa
    com um véu mais denso (combina com as artes que o dono edita no escuro).
    Só o DEFAULT muda: quem já ajustou cor/opacidade nunca é tocado."""
    from app.qt.design import tokens as t
    if t.TEMA_ATUAL == "escuro":
        return ("#16202E", 150)
    return ("#000000", 128)


def texto_inicial_do_papel(papel: PapelTexto, *, preset_legal: str | None = None,
                           texto_livre: str | None = None) -> str | None:
    """O ``texto_fixo`` que a região nasce guardando, por papel:

    - LEGAL → o texto do preset escolhido;
    - LIVRE → o que o dono digitou (ou None se vazio);
    - VALIDADE → None (puxa a validade viva do evento no compositor);
    - DICA → None (a IA preenche depois, pelo botão do painel).
    """
    if papel is PapelTexto.LEGAL:
        return PRESETS_LEGAIS.get(preset_legal or "", "") or None
    if papel is PapelTexto.LIVRE:
        return (texto_livre or "").strip() or None
    return None


# ----------------------------------------------------------------------------
# Diálogo nomeado (passo 1) — construível sem exec() para os testes.
# ----------------------------------------------------------------------------

def _dialogo_cls():
    """Import tardio do Qt: o módulo carrega (dados) sem tela."""
    from PySide6.QtWidgets import (
        QButtonGroup, QComboBox, QDialog, QDialogButtonBox, QLabel, QLineEdit,
        QPushButton, QRadioButton, QVBoxLayout,
    )

    class DialogoPapelTexto(QDialog):
        """Pergunta, em PT-BR e com prévia, para que serve o campo de texto."""

        def __init__(self, parent=None, papel=None, texto=None, contexto=None):
            super().__init__(parent)
            self.setWindowTitle("Novo campo de texto — para que serve?")
            self._contexto = dict(contexto or {})   # R-058: {data}/{evento} vivos
            self._grupo = QButtonGroup(self)
            self._radios: dict = {}
            raiz = QVBoxLayout(self)
            for p in ORDEM_PAPEIS:
                rb = QRadioButton(ROTULO_PAPEL[p])
                rb.setStyleSheet("font-weight: 600;")
                self._grupo.addButton(rb)
                self._radios[p] = rb
                raiz.addWidget(rb)
                ex = QLabel("ex.: " + EXEMPLO_PAPEL[p])
                ex.setWordWrap(True)
                ex.setContentsMargins(24, 0, 0, 6)
                ex.setStyleSheet("color: palette(mid);")
                raiz.addWidget(ex)
                rb.toggled.connect(self._atualizar_visibilidade)

            self.combo_legal = QComboBox()
            self.combo_legal.addItems(list(PRESETS_LEGAIS))
            self.combo_legal.setToolTip("Preset do aviso legal")
            raiz.addWidget(self.combo_legal)

            # R-058: frases prontas com {data}/{evento} — escolher e inserir,
            # já resolvidas pelo contexto (o que não tiver valor fica visível).
            # OS F11.5 #39: o combo soma as frases do DONO (config) às padrão,
            # e o último item ("Nova frase…") adiciona e PERSISTE uma nova.
            from app.qt.telas.servico import frases_do_combo
            self.combo_frases = QComboBox()
            self.combo_frases.addItem("Frases prontas…")
            for f in frases_do_combo():
                self.combo_frases.addItem(f)
            self.combo_frases.addItem("＋ Nova frase…")
            self.combo_frases.setToolTip(
                "Insere uma frase pronta; {data}/{evento} se resolvem "
                "sozinhos. A última opção adiciona uma frase SUA (fica salva "
                "para as próximas vezes; edite tudo em Configurações).")
            self.combo_frases.activated.connect(self._inserir_frase)
            raiz.addWidget(self.combo_frases)

            # R-084 (polimento): as MANCHETES prontas da F9 — a função
            # `sugerir_manchetes` existia sem nenhuma UI. Sem IA, degrada
            # para a lista padrão com o nome do evento (sempre útil, I2).
            self.btn_manchetes = QPushButton("Sugerir manchetes (IA)")
            self.btn_manchetes.setToolTip(
                "5 manchetes curtas para a capa/chamada — com IA local se "
                "ligada; sem ela, as frases padrão do evento")
            self.btn_manchetes.clicked.connect(self._sugerir_manchetes)
            raiz.addWidget(self.btn_manchetes)
            self.combo_manchetes = QComboBox()
            self.combo_manchetes.addItem("Manchetes sugeridas…")
            self.combo_manchetes.setToolTip("Escolher uma manchete a inserir")
            self.combo_manchetes.activated.connect(self._inserir_manchete)
            self.combo_manchetes.hide()
            raiz.addWidget(self.combo_manchetes)

            self.edit_livre = QLineEdit()
            self.edit_livre.setPlaceholderText("Digite o texto livre…")
            raiz.addWidget(self.edit_livre)

            botoes = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok
                | QDialogButtonBox.StandardButton.Cancel)
            botoes.accepted.connect(self.accept)
            botoes.rejected.connect(self.reject)
            raiz.addWidget(botoes)

            self.selecionar(papel or PapelTexto.LEGAL)
            if texto is not None:
                self.edit_livre.setText(texto)

        # --- API testável (sem exec) ---
        def selecionar(self, papel: PapelTexto) -> None:
            self._radios[papel].setChecked(True)
            self._atualizar_visibilidade()

        def papel_escolhido(self) -> PapelTexto:
            for p, rb in self._radios.items():
                if rb.isChecked():
                    return p
            return PapelTexto.LIVRE

        def _atualizar_visibilidade(self) -> None:
            p = self.papel_escolhido()
            self.combo_legal.setVisible(p is PapelTexto.LEGAL)
            self.edit_livre.setVisible(p is PapelTexto.LIVRE)
            self.combo_frases.setVisible(p is PapelTexto.LIVRE)
            self.btn_manchetes.setVisible(p is PapelTexto.LIVRE)
            self.combo_manchetes.setVisible(
                p is PapelTexto.LIVRE and self.combo_manchetes.count() > 1)

        def _sugerir_manchetes(self) -> None:
            """R-084: worker de IA → combo (a UI nunca congela); sem IA a
            lista padrão volta na hora — sempre degrada com algo útil."""
            from app.ai.enriquecimento import sugerir_manchetes
            from app.qt.telas import servico
            from app.qt.workers import GerenciadorTrabalhos, Trabalhador
            evento = (self._contexto or {}).get("evento")
            motor = servico._motor_se_disponivel()
            if not hasattr(self, "_trabalhos"):
                self._trabalhos = GerenciadorTrabalhos()
            self.btn_manchetes.setEnabled(False)
            self.btn_manchetes.setText("Sugerindo…")
            trab = Trabalhador(lambda st: sugerir_manchetes(evento, motor))

            def _ok(lista):
                self.btn_manchetes.setEnabled(True)
                self.btn_manchetes.setText("Sugerir manchetes (IA)")
                self.combo_manchetes.clear()
                self.combo_manchetes.addItem("Manchetes sugeridas…")
                for m in (lista or []):
                    self.combo_manchetes.addItem(m)
                self._atualizar_visibilidade()

            def _erro(_m):
                self.btn_manchetes.setEnabled(True)
                self.btn_manchetes.setText("Sugerir manchetes (IA)")

            trab.ok.connect(_ok)
            trab.erro.connect(_erro)
            self._trabalhos.rodar(trab)

        def _inserir_manchete(self, idx: int) -> None:
            if idx <= 0:
                return
            self.edit_livre.setText(self.combo_manchetes.itemText(idx))
            self.combo_manchetes.setCurrentIndex(0)

        def done(self, resultado: int) -> None:  # noqa: N802 (Qt)
            # lei exit-0: nenhum worker de manchete vivo ao fechar
            if hasattr(self, "_trabalhos"):
                self._trabalhos.encerrar()
            super().done(resultado)

        def _inserir_frase(self, idx: int) -> None:
            """R-058: resolve {data}/{evento} do contexto e joga no texto livre;
            variável sem valor fica VISÍVEL (I2), o dono completa."""
            if idx <= 0:
                return
            # OS F11.5 #39: o último item cria uma frase NOVA e a persiste
            if idx == self.combo_frases.count() - 1:
                self._nova_frase()
                return
            from app.qt.telas.servico import resolver_frase
            texto, _faltantes = resolver_frase(
                self.combo_frases.itemText(idx), self._contexto)
            self.edit_livre.setText(texto)
            self.combo_frases.setCurrentIndex(0)

        def _nova_frase(self) -> None:
            """OS F11.5 #39: pergunta a frase, salva na config (a mesma lista
            de Configurações) e já a deixa escolhida no combo."""
            from PySide6.QtWidgets import QInputDialog, QMessageBox
            self.combo_frases.setCurrentIndex(0)
            frase, ok = QInputDialog.getText(
                self, "Nova frase pronta",
                "A frase (pode usar {data} e {evento}):")
            frase = (frase or "").strip()
            if not ok or not frase:
                return
            from app.qt.telas import servico
            if not servico.adicionar_frase_do_combo(frase):
                QMessageBox.information(
                    self, "Nova frase",
                    "Essa frase já existe (ou não deu para salvar agora) — "
                    "nada foi duplicado.")
                return
            pos = self.combo_frases.count() - 1     # antes do "＋ Nova frase…"
            self.combo_frases.insertItem(pos, frase)
            self._inserir_frase(pos)                # já aplica no texto livre

        def resultado(self) -> tuple[PapelTexto, str | None]:
            p = self.papel_escolhido()
            return p, texto_inicial_do_papel(
                p, preset_legal=self.combo_legal.currentText(),
                texto_livre=self.edit_livre.text())

    return DialogoPapelTexto


def escolher_papel_texto(parent, papel=None, texto=None, contexto=None):
    """Abre o diálogo; devolve (papel, texto_fixo) ou None se cancelado."""
    from PySide6.QtWidgets import QDialog
    dlg = _dialogo_cls()(parent, papel=papel, texto=texto, contexto=contexto)
    if dlg.exec() == QDialog.DialogCode.Accepted:
        return dlg.resultado()
    return None


def criar_texto_legal_com_papel(canvas, parent):
    """Gesto ÚNICO (barra + paleta de comandos): pergunta o papel e cria o
    TEXTO_LEGAL já com ele. Cancelar não cria nada. O contexto das frases
    (R-058) vem da janela, quando ela o expõe (`contexto_frases`)."""
    from app.rendering.model import TipoRegiao
    obtem = getattr(parent, "contexto_frases", None)
    contexto = obtem() if callable(obtem) else {}
    r = escolher_papel_texto(parent, contexto=contexto)
    if r is None:
        return None
    papel, texto = r
    return canvas.adicionar_regiao(TipoRegiao.TEXTO_LEGAL,
                                   papel_texto=papel, texto_fixo=texto)
