"""
Configurações (F6.7, Etapa C do Bloco D)
========================================
Tela simples sobre a tabela ``Config``. Tudo tem default são (C3): campo
vazio ou valor incoerente cai no padrão, e um banco antigo (sem as chaves)
abre sem erro. Chaves:

- ``sanitizacao.siglas``    — siglas que ficam MAIÚSCULAS (lista);
- ``sanitizacao.glossario`` — expansão de siglas ("VD" → "vidro");
- ``ia.base_url`` / ``ia.modelo_*`` — servidor compatível-OpenAI (trocar
  LM Studio ↔ Ollama sem código);
- ``conciliacao.verde`` / ``conciliacao.amarelo`` — limiares do semáforo;
- ``backups.rotacao``       — quantos snapshots automáticos ficam.

C2: mudar regra de sanitização NÃO reescreve o acervo em silêncio — o botão
"Salvar e ver prévia do acervo" salva, mostra QUANTOS nomes mudariam (com
amostra) e só aplica com confirmação explícita.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.ai.client import ConfigIA
from app.ai.conciliacao import LimiaresConciliacao
from app.core.cofre import ROTACAO_PADRAO
from app.core.database import Database
from app.core.repositories import ConfigRepositorio, regras_de_config
from app.core.sanitize import REGRAS_PADRAO
from app.qt.design import tokens as t
from app.qt.design.componentes import Painel
from app.qt.design.icones import icone
from app.qt.design.toast import mostrar_toast


class TabelaPares(QWidget):
    """FASE 3 (passo 51): glossário em TABELA limpa — 2 colunas editáveis
    com "adicionar/remover linha", no lugar dos campos de texto "A = B".
    Linha incompleta (só um lado) conta como ignorada, nunca some em
    silêncio (I2)."""

    mudou = Signal()

    def __init__(self, col1: str, col2: str, dica: str = "", parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QTableWidget
        self.tabela = QTableWidget(0, 2)
        self.tabela.setHorizontalHeaderLabels([col1, col2])
        self.tabela.horizontalHeader().setStretchLastSection(True)
        self.tabela.horizontalHeader().setSectionResizeMode(
            0, self.tabela.horizontalHeader().ResizeMode.Stretch)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setMinimumHeight(150)
        self.tabela.setMaximumHeight(240)
        if dica:
            self.tabela.setToolTip(dica)
        self.tabela.cellChanged.connect(lambda *_a: self.mudou.emit())
        btn_add = QPushButton(" Adicionar linha")
        btn_add.setIcon(icone("duplicar", tamanho=14))
        btn_add.clicked.connect(self._adicionar_linha)
        btn_del = QPushButton(" Remover linha")
        btn_del.setIcon(icone("lixeira", tamanho=14))
        btn_del.clicked.connect(self._remover_linha)
        linha = QHBoxLayout()
        linha.setSpacing(t.ESP_2)
        linha.addWidget(btn_add)
        linha.addWidget(btn_del)
        linha.addStretch(1)
        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(t.ESP_1)
        vl.addWidget(self.tabela)
        vl.addLayout(linha)

    def _adicionar_linha(self) -> None:
        self.tabela.insertRow(self.tabela.rowCount())
        self.tabela.setCurrentCell(self.tabela.rowCount() - 1, 0)

    def _remover_linha(self) -> None:
        linha = self.tabela.currentRow()
        if linha >= 0:
            self.tabela.removeRow(linha)
            self.mudou.emit()

    def definir(self, pares: dict) -> None:
        from PySide6.QtWidgets import QTableWidgetItem
        self.tabela.blockSignals(True)
        self.tabela.setRowCount(0)
        for k, v in pares.items():
            r = self.tabela.rowCount()
            self.tabela.insertRow(r)
            self.tabela.setItem(r, 0, QTableWidgetItem(str(k)))
            self.tabela.setItem(r, 1, QTableWidgetItem(str(v)))
        self.tabela.blockSignals(False)

    def pares(self) -> tuple[dict, int]:
        """(dict das linhas completas, quantas ficaram pela metade)."""
        d: dict[str, str] = {}
        ignoradas = 0
        for r in range(self.tabela.rowCount()):
            i0, i1 = self.tabela.item(r, 0), self.tabela.item(r, 1)
            k = (i0.text() if i0 else "").strip()
            v = (i1.text() if i1 else "").strip()
            if k and v:
                d[k] = v
            elif k or v:
                ignoradas += 1
        return d, ignoradas


class ConfiguracoesTela(QWidget):
    def __init__(self, raiz=None, parent=None):
        super().__init__(parent)
        self._raiz = raiz              # None = System Root padrão

        # --- barra ------------------------------------------------------------------
        barra = QWidget()
        barra.setObjectName("barraFerramentas")
        hb = QHBoxLayout(barra)
        hb.setContentsMargins(t.ESP_3, t.ESP_1 + 2, t.ESP_3, t.ESP_1 + 2)
        hb.setSpacing(t.ESP_2)
        # FASE 3 (passo 17): SEM botão "Salvar" global — tudo salva na
        # hora; o "aplicar ao acervo" (C2) mora na aba Sanitização
        titulo_tela = QLabel("Configurações")
        titulo_tela.setProperty("papel", "titulo")
        dica = QLabel("Tudo salva sozinho · campo vazio volta ao padrão · "
                      "o acervo só muda com prévia e confirmação")
        dica.setProperty("papel", "legenda")
        hb.addWidget(titulo_tela)
        hb.addStretch(1)
        hb.addWidget(dica)

        # --- sanitização --------------------------------------------------------------
        self.campo_siglas = QLineEdit()
        self.campo_siglas.setPlaceholderText(
            "separadas por vírgula — ex.: TP, BB, XL")
        self.campo_siglas.setToolTip(
            "Siglas que ficam MAIÚSCULAS no nome (padrão: "
            + ", ".join(sorted(REGRAS_PADRAO.siglas)) + ")")
        # FASE 3 (passo 51): os glossários viram TABELAS limpas
        self.campo_glossario = TabelaPares(
            "Sigla", "Expansão",
            "Expansão de siglas da tabela de ofertas — ex.: VD → vidro, "
            "TP → tetra pak")
        # RG-22: abreviações SÓ do tabloide (o banco nunca muda) — evita
        # quebras feias na célula; a prévia é o próprio canvas (WYSIWYG)
        self.campo_abreviacoes = TabelaPares(
            "Nome longo", "Abreviação",
            "Aplicadas SÓ ao nome desenhado no tabloide — o cadastro no "
            "banco e a estante continuam com o nome completo")
        # passo 51: a ORDEM do nome (Tipo+Marca+Sabor+Peso) reordenável
        from app.ai.enriquecimento import ORDEM_NOME_PADRAO
        self.lista_ordem_nome = QListWidget()
        self.lista_ordem_nome.setDragDropMode(
            QListWidget.DragDropMode.InternalMove)
        self.lista_ordem_nome.setFixedHeight(118)
        self.lista_ordem_nome.setToolTip(
            "Arraste para mudar a ordem dos blocos do nome — a IA monta o "
            "nome nessa ordem ao enriquecer (o Peso costuma ficar no fim)")
        for bloco in ORDEM_NOME_PADRAO:
            self.lista_ordem_nome.addItem(bloco)
        self.campo_palavras_min = QLineEdit()
        self.campo_palavras_min.setPlaceholderText(
            "separadas por vírgula — ex.: de, da, com, para")
        self.campo_palavras_min.setToolTip(
            "Palavras que ficam minúsculas no MEIO do nome (preposições). "
            "Vazio = a lista padrão do app. As unidades são lei travada: "
            "g, kg, ml minúsculas; só o L é maiúsculo.")
        form_san = QFormLayout()
        form_san.setVerticalSpacing(t.ESP_2)
        form_san.addRow("Ordem do nome", self.lista_ordem_nome)
        form_san.addRow("Siglas maiúsculas", self.campo_siglas)
        form_san.addRow("Palavras minúsculas", self.campo_palavras_min)
        form_san.addRow("Glossário de siglas", self.campo_glossario)
        form_san.addRow("Abreviações do tabloide", self.campo_abreviacoes)
        caixa_san = QWidget()
        caixa_san.setLayout(form_san)

        # --- IA local -----------------------------------------------------------------
        self.campo_url = QLineEdit()
        self.campo_url.setPlaceholderText(ConfigIA.base_url)
        self.campo_url.setToolTip("API compatível com OpenAI — LM Studio, "
                                  "Ollama (http://127.0.0.1:11434/v1)…")
        self.campo_mod_texto = QLineEdit()
        self.campo_mod_texto.setPlaceholderText(ConfigIA.modelo_texto)
        self.campo_mod_visao = QLineEdit()
        self.campo_mod_visao.setPlaceholderText(ConfigIA.modelo_visao)
        self.campo_mod_emb = QLineEdit()
        self.campo_mod_emb.setPlaceholderText(ConfigIA.modelo_embeddings)
        form_ia = QFormLayout()
        form_ia.setVerticalSpacing(t.ESP_2)
        form_ia.addRow("URL do servidor", self.campo_url)
        form_ia.addRow("Modelo de texto", self.campo_mod_texto)
        form_ia.addRow("Modelo de visão (OCR)", self.campo_mod_visao)
        form_ia.addRow("Modelo de conciliação (embeddings)",
                       self.campo_mod_emb)
        caixa_ia = QWidget()
        caixa_ia.setLayout(form_ia)

        # --- conciliação + backups ------------------------------------------------------
        self.campo_verde = QDoubleSpinBox()
        self.campo_verde.setRange(1.0, 100.0)
        self.campo_verde.setToolTip("Score a partir do qual o item entra "
                                    "VERDE (sem conferência)")
        self.campo_amarelo = QDoubleSpinBox()
        self.campo_amarelo.setRange(0.5, 99.5)
        self.campo_amarelo.setToolTip("Abaixo do verde e a partir daqui: "
                                      "AMARELO (conferir); abaixo: VERMELHO (novo)")
        self.campo_rotacao = QSpinBox()
        self.campo_rotacao.setRange(1, 100)
        self.campo_rotacao.setToolTip("Quantos backups automáticos ficam "
                                      "guardados (os manuais não contam)")
        # F7.5: CMYK opcional na exportação (RGB continua o padrão)
        from PySide6.QtWidgets import QCheckBox
        self.campo_cmyk = QCheckBox("Converter PDF exportado para CMYK "
                                    "(impressão profissional)")
        self.campo_cmyk.setToolTip(
            "Usa o Ghostscript ao exportar PDF. Desligado (padrão), o PDF "
            "sai em RGB, idêntico ao de sempre — para WhatsApp/Instagram "
            "não mexa aqui.")
        self.campo_icc = QLineEdit()
        self.campo_icc.setPlaceholderText(
            "caminho do perfil .icc (opcional — vazio usa o padrão)")
        # FASE 3 (passo 16): o form-monólito vira UM form POR ABA
        form_ia_extra = QFormLayout()          # limiares moram na aba IA
        form_ia_extra.setVerticalSpacing(t.ESP_2)
        form_ia_extra.addRow("Semáforo — limiar do verde", self.campo_verde)
        form_ia_extra.addRow("Semáforo — limiar do amarelo",
                             self.campo_amarelo)
        # OS F11.5 #47/#81 (R-086): o dicionário regional EDITÁVEL — cada
        # linha é um grupo de sinônimos; a conciliação passa a casá-los
        from PySide6.QtWidgets import QPlainTextEdit as _QPTE
        self.campo_sinonimos = _QPTE()
        self.campo_sinonimos.setPlaceholderText(
            "um grupo por linha, termos separados por vírgula\n"
            "ex.: mandioca, macaxeira, aipim")
        self.campo_sinonimos.setMinimumHeight(56)
        self.campo_sinonimos.setToolTip(
            "Sinônimos da SUA região — a conciliação trata como o mesmo "
            "produto (ex.: a tabela diz “jerimum” e o cadastro diz "
            "“abóbora”). Os grupos padrão do app continuam valendo.")
        self.campo_sinonimos.textChanged.connect(
            lambda: self._salvar_debounce.start()
            if hasattr(self, "_salvar_debounce") else None)
        form_ia_extra.addRow("Sinônimos regionais", self.campo_sinonimos)
        # OS F11.5 #43/#53/#91: as correções APRENDIDAS (aliases) — ver e
        # reverter, direto do banco
        self.btn_correcoes = QPushButton(" Correções aprendidas…")
        self.btn_correcoes.setIcon(icone("texto", tamanho=14))
        self.btn_correcoes.setToolTip(
            "Tudo o que o banco aprendeu dos seus “Aceitar” — cada linha "
            "diz “quando a tabela escrever X, é o produto Y”. Dá para "
            "reverter qualquer uma.")
        self.btn_correcoes.clicked.connect(self._abrir_correcoes)
        form_ia_extra.addRow(self.btn_correcoes)
        form_backups = QFormLayout()
        form_backups.setVerticalSpacing(t.ESP_2)
        form_backups.addRow("Backups automáticos guardados",
                            self.campo_rotacao)
        # R-131 (FASE 12): o PC da loja aprova e imprime — não edita à toa
        self.chk_somente_leitura = QCheckBox(
            "Modo somente-leitura (o PC da loja: aprova e imprime, "
            "não edita)")
        self.chk_somente_leitura.setToolTip(
            "Com esta chave, editar produto, criar, fundir e salvar projeto "
            "ficam bloqueados (à prova de dedo) — aprovar, exportar e "
            "imprimir seguem livres. Desligar pede confirmação.")
        self.chk_somente_leitura.toggled.connect(self._somente_leitura_mudou)
        form_backups.addRow(self.chk_somente_leitura)
        # FASE 12 (passos 70-71): trazer o acervo do AutoTabloide ANTIGO
        self.btn_migrar_antigo = QPushButton(
            " Migrar do AutoTabloide antigo…")
        self.btn_migrar_antigo.setIcon(icone("abrir", tamanho=14))
        self.btn_migrar_antigo.setToolTip(
            "Lê o banco do programa antigo (só leitura) e traz os produtos "
            "que você ainda não tem — com prévia antes; nada duplica, nada "
            "sobrescreve o seu acervo.")
        self.btn_migrar_antigo.clicked.connect(self._migrar_antigo)
        form_backups.addRow(self.btn_migrar_antigo)
        form_imagens = QFormLayout()
        form_imagens.setVerticalSpacing(t.ESP_2)
        # FASE 3 (passos 49-50): upscale desligável, pasta da biblioteca
        # visível, e as DUAS chaves-semente da Fase 10 (WebP e detector de
        # fundo branco) — rotuladas como preparação, sem fingir função
        self.chk_upscale = QCheckBox(
            "Melhorar fotos pequenas sozinho ao exportar cartaz (upscale)")
        self.chk_upscale.setChecked(True)
        self.chk_upscale.setToolTip(
            "Foto pequena esticada no cartaz sai serrilhada — ligado, o "
            "app amplia com o Real-ESRGAN na hora do export (a original "
            "nunca muda). Desligado, a foto vai como está.")
        self.chk_webp = QCheckBox("Salvar as fotos em WebP (metade do disco, "
                                  "sem perda visível)")
        self.chk_webp.setToolTip(
            "R-100: o WebP preserva a transparência do packshot recortado. A "
            "compressão está disponível ao salvar; a migração do acervo inteiro "
            "é opcional/sob demanda (nada é convertido em silêncio).")
        self.chk_fundo_branco = QCheckBox(
            "Pular o recorte quando o fundo já é branco")
        self.chk_fundo_branco.setToolTip(
            "R-095: quando a foto já tem fundo branco uniforme, o app não roda o "
            "recorte (economiza tempo e não estraga foto boa).")
        # OS F11.5 #20 (F10): o degrau 2 do Estúdio é OPÇÃO, nunca requisito
        self.chk_estudio_gerador = QCheckBox(
            "Estúdio IA (gerador) — refinar o packshot com img2img local")
        self.chk_estudio_gerador.setToolTip(
            "Liga o DEGRAU 2 do Estúdio (SDXL local): o packshot passa por um "
            "refino de imagem. Precisa de GPU — sem ela, o app avisa e "
            "entrega o degrau 1 (que já resolve). A guarda anti-alucinação "
            "rejeita refino que mude demais o produto.")
        self.rot_pasta_bib = QLineEdit()
        self.rot_pasta_bib.setReadOnly(True)
        self.rot_pasta_bib.setToolTip(
            "Onde as fotos dos produtos vivem no disco (o banco guarda só "
            "os caminhos — decisão travada)")
        btn_abrir_bib = QPushButton(" Abrir pasta")
        btn_abrir_bib.setIcon(icone("abrir", tamanho=14))
        btn_abrir_bib.clicked.connect(self._abrir_pasta_biblioteca)
        linha_bib = QHBoxLayout()
        linha_bib.setSpacing(t.ESP_2)
        linha_bib.addWidget(self.rot_pasta_bib, 1)
        linha_bib.addWidget(btn_abrir_bib)
        form_imagens.addRow(self.chk_upscale)
        form_imagens.addRow(self.chk_webp)
        # OS F11.5 #51/#52: a migração do acervo é SOB DEMANDA (prévia →
        # confirma) e reversível — nada convertido em silêncio
        self.btn_migrar_webp = QPushButton(" Migrar o acervo (prévia)…")
        self.btn_migrar_webp.setIcon(icone("imagem", tamanho=14))
        self.btn_migrar_webp.setToolTip(
            "Converte as fotos do acervo para WebP (metade do disco, alfa "
            "preservado) — mostra a PRÉVIA do ganho e só converte se você "
            "confirmar. Reversível: com a chave desligada, volta a PNG.")
        self.btn_migrar_webp.clicked.connect(self._migrar_webp)
        form_imagens.addRow(self.btn_migrar_webp)
        form_imagens.addRow(self.chk_fundo_branco)
        form_imagens.addRow(self.chk_estudio_gerador)
        caixa_bib = QWidget()
        caixa_bib.setLayout(linha_bib)
        form_imagens.addRow("Pasta da biblioteca", caixa_bib)
        form_imagens.addRow(self.campo_cmyk)
        form_imagens.addRow("Perfil ICC de impressão", self.campo_icc)
        # OS F11.5 #5 (R-065): os perfis de exportação ganham tela de edição
        self.btn_perfis = QPushButton(" Perfis de exportação…")
        self.btn_perfis.setIcon(icone("salvar", tamanho=14))
        self.btn_perfis.setToolTip(
            "Criar/editar os presets de exportação (WhatsApp, Impressão, "
            "Stories…) — tamanho, formato e qualidade de cada um")
        self.btn_perfis.clicked.connect(self._abrir_perfis)
        form_imagens.addRow(self.btn_perfis)
        form_campanhas = QFormLayout()
        form_campanhas.setVerticalSpacing(t.ESP_2)
        # F8/A2: a ordem das seções do tabloide agrupado
        self.campo_categorias = QLineEdit()
        self.campo_categorias.setPlaceholderText(
            "ex.: Mercearia, Bebidas, Limpeza — vazio = alfabética; "
            "“Outros” é sempre o último")
        self.campo_categorias.setToolTip(
            "A ordem em que as categorias entram no tabloide agrupado "
            "(o “Agrupar por categoria” da Mesa)")
        # RG-44: preset com a ordem clássica dos setores da loja (semente)
        btn_preset = QPushButton("Preset da loja")
        btn_preset.setToolTip(
            "Preenche com a ordem clássica dos setores do mercado "
            "(hortifrúti → padaria → frios → … → bazar) — edite à vontade")
        btn_preset.clicked.connect(self._preset_setores)
        caixa_cat = QWidget()
        hcat = QHBoxLayout(caixa_cat)
        hcat.setContentsMargins(0, 0, 0, 0)
        hcat.setSpacing(6)
        hcat.addWidget(self.campo_categorias, 1)
        hcat.addWidget(btn_preset)
        form_campanhas.addRow("Ordem das categorias", caixa_cat)
        # RG-30: siglas de marca própria (marca_propria automático + a sigla
        # sai do termo de busca de imagem)
        self.campo_marcas = QLineEdit()
        self.campo_marcas.setPlaceholderText("ex.: BBX, BB")
        self.campo_marcas.setToolTip(
            "Siglas da marca própria do mercado: produto com a sigla ganha "
            "“marca própria” sozinho, e a sigla não vai à busca de imagem")
        # FASE 3 (passo 51): marcas próprias moram na SANITIZAÇÃO (RG-30
        # é regra de nome/busca, não de campanha)
        form_san.addRow("Marcas próprias", self.campo_marcas)
        # FASE 3 (passo 61): o campo-texto "Dias das campanhas" (RG-24)
        # SAIU — era porta dupla para o mesmo dado do gestor visual acima
        # (duplo clique na campanha edita o dia). A chave `eventos.dias`
        # segue lida SÓ na migração de bancos antigos (eventos.py).
        # RG-33: gestor de selos personalizados (upload da arte do dono)
        self.lista_selos = QListWidget()
        self.lista_selos.setMinimumHeight(84)         # passo 50: mínimo
        self.lista_selos.setToolTip(
            "Selos que você pode pôr POR ITEM na Mesa (botão direito no "
            "item → “Selos deste item…”). Os automáticos +18/Qualidade "
            "continuam por conta própria.")
        # FASE 3 (passos 65-67): a aba mostra TODOS os selos da tabela
        # (manuais E automáticos) com miniatura; duplo clique edita
        from PySide6.QtCore import QSize as _QSize
        self.lista_selos.setIconSize(_QSize(40, 40))
        self.lista_selos.itemDoubleClicked.connect(self._editar_selo)
        btn_selo_add = QPushButton(" Adicionar selo (PNG)…")
        btn_selo_add.setIcon(icone("imagem", tamanho=15))
        btn_selo_add.clicked.connect(self._adicionar_selo)
        btn_selo_edit = QPushButton(" Editar…")
        btn_selo_edit.setIcon(icone("propriedades", tamanho=15))
        btn_selo_edit.clicked.connect(
            lambda: self._editar_selo(self.lista_selos.currentItem()))
        btn_selo_del = QPushButton(" Excluir / desligar")
        btn_selo_del.setIcon(icone("lixeira", tamanho=15))
        btn_selo_del.setToolTip(
            "Selo manual: sai do gestor (a arte fica em selos/). "
            "Automático: só DESLIGA a regra — e o +18 em bebida é lei, "
            "não desliga.")
        btn_selo_del.clicked.connect(self._remover_selo)
        linha_selos = QHBoxLayout()
        linha_selos.setSpacing(6)
        linha_selos.addWidget(btn_selo_add)
        linha_selos.addWidget(btn_selo_edit)
        linha_selos.addWidget(btn_selo_del)
        linha_selos.addStretch(1)
        caixa_selos = QWidget()
        vs = QVBoxLayout(caixa_selos)
        vs.setContentsMargins(0, 0, 0, 0)
        vs.setSpacing(4)
        vs.addWidget(self.lista_selos)
        vs.addLayout(linha_selos)
        self._caixa_selos_legado = caixa_selos   # aba Selos (Bloco G)
        # F8.2: o visual das seções (contorno de categoria)
        # RG-31: o ESTILO da seção ("a borda atual: feia") + cor por categoria
        self.campo_secao_estilo = QComboBox()
        for valor, rotulo in [("CONTORNO", "Contorno (borda arredondada)"),
                              ("SO_TITULO", "Só o título (sem borda)"),
                              ("PILL", "Fundo suave (pill)"),
                              ("SEM_DESENHO", "Agrupar sem desenhar")]:
            self.campo_secao_estilo.addItem(rotulo, valor)
        self.campo_secao_estilo.setToolTip(
            "Como as seções de categoria aparecem no tabloide agrupado")
        self.campo_secao_por_cat = QCheckBox(
            "Cor por categoria (paleta automática)")
        self.campo_secao_por_cat.setToolTip(
            "Cada categoria ganha uma cor estável da paleta; desligado, "
            "vale a cor única abaixo")
        self.campo_secao_cor = QLineEdit()
        self.campo_secao_cor.setPlaceholderText("#1D4ED8 (o azul padrão)")
        self.campo_secao_cor.setToolTip(
            "Cor do contorno das seções — código de cor tipo #1D4ED8")
        self.campo_secao_esp = QDoubleSpinBox()
        self.campo_secao_esp.setRange(0.1, 5.0)
        self.campo_secao_esp.setSingleStep(0.1)
        self.campo_secao_esp.setToolTip("Espessura do contorno, em mm")
        form_campanhas.addRow("Seções — estilo",
                              self.campo_secao_estilo)  # RG-31
        form_campanhas.addRow(self.campo_secao_por_cat)
        form_campanhas.addRow("Seções — cor do contorno",
                              self.campo_secao_cor)
        form_campanhas.addRow("Seções — espessura (mm)",
                              self.campo_secao_esp)
        # RG-02: o modelo do remover-fundo (qualidade × velocidade)
        from app.images.fundo import MODELOS
        self.campo_rembg = QComboBox()
        self._modelos_rembg = list(MODELOS)
        for chave in self._modelos_rembg:
            self.campo_rembg.addItem(MODELOS[chave])
        self.campo_rembg.setToolTip(
            "Recorte de fundo das fotos. O padrão é a qualidade máxima "
            "(decisão de projeto); os modos mais rápidos baixam um modelo "
            "novo na 1ª vez (precisa de internet uma vez).")
        form_imagens.addRow("Recorte de fundo (rembg)", self.campo_rembg)
        # RG-04: a saída para a foto mal lida que ficou presa no cache
        btn_ocr = QPushButton("Esquecer leituras de foto (forçar reler no OCR)")
        btn_ocr.setToolTip("A leitura da IA não é determinística — se uma "
                           "foto foi mal lida, limpe aqui e reimporte.")
        btn_ocr.clicked.connect(self._limpar_cache_ocr)
        form_imagens.addRow(btn_ocr)

        # FASE 1 (passo 23): Aparência — tema em cards com prévia, na hora
        from app.qt.design.aparencia import SeletorTema
        self.seletor_tema = SeletorTema()
        caixa_ap = QWidget()
        va = QVBoxLayout(caixa_ap)
        va.setContentsMargins(0, 0, 0, 0)
        va.addWidget(self.seletor_tema)
        # FASE 1 (passo 64 — R-015): escala da interface, aplicada NA HORA
        self.combo_escala = QComboBox()
        for pct in (100, 125, 150):
            self.combo_escala.addItem(f"{pct}%", pct)
        self.combo_escala.setCurrentIndex(
            {100: 0, 125: 1, 150: 2}.get(t.ESCALA_ATUAL, 0))
        self.combo_escala.setToolTip(
            "Aumenta a letra e os controles da INTERFACE (a arte do "
            "tabloide não muda). Bom para telas grandes/vista cansada.")
        self.combo_escala.activated.connect(self._trocar_escala)
        linha_esc = QHBoxLayout()
        rot_esc = QLabel("Escala da interface")
        linha_esc.addWidget(rot_esc)
        linha_esc.addWidget(self.combo_escala)
        linha_esc.addStretch(1)
        va.addLayout(linha_esc)
        # FASE 3 (passo 26): animações ligadas/reduzidas com explicação
        self.chk_animacoes = QCheckBox("Animações ligadas")
        self.chk_animacoes.setToolTip(
            "Desligue no PC fraco do mercado: as transições ficam "
            "instantâneas (nada muda de função, só o movimento)")
        self.chk_animacoes.toggled.connect(self._trocar_animacoes)
        va.addWidget(self.chk_animacoes)
        # FASE 3 (passo 29): reduzir transparências (véus viram sólidos)
        self.chk_transparencias = QCheckBox("Reduzir transparências")
        self.chk_transparencias.setToolTip(
            "Para máquinas fracas: os véus translúcidos (diálogos, hover) "
            "não são desenhados")
        self.chk_transparencias.toggled.connect(self._trocar_transparencias)
        va.addWidget(self.chk_transparencias)
        # FASE 1 (passo 74) + FASE 3 (passo 28): som + botão de teste
        self.chk_som = QCheckBox("Som ao concluir exportação")
        self.chk_som.setToolTip("Um aviso curto e discreto quando o "
                                "PNG/PDF ficar pronto (padrão: desligado)")
        self.chk_som.toggled.connect(self._trocar_som)
        btn_som = QPushButton("Testar som")
        btn_som.clicked.connect(self._testar_som)
        linha_som = QHBoxLayout()
        linha_som.addWidget(self.chk_som)
        linha_som.addWidget(btn_som)
        linha_som.addStretch(1)
        va.addLayout(linha_som)
        # FASE 3 (passo 30): idioma — honestidade, sem promessa vazia
        combo_idioma = QComboBox()
        combo_idioma.addItem("Português (Brasil)")
        combo_idioma.setEnabled(False)
        combo_idioma.setToolTip("Outros idiomas: em breve — o app nasceu "
                                "PT-BR para o Belo Brasil")
        linha_idi = QHBoxLayout()
        rot_idi = QLabel("Idioma")
        linha_idi.addWidget(rot_idi)
        linha_idi.addWidget(combo_idioma)
        linha_idi.addStretch(1)
        va.addLayout(linha_idi)

        # =====================================================================
        # FASE 3 (Bloco B): a CARCAÇA DE ABAS — fim do formulário-monólito.
        # Abas verticais à esquerda; cada página é um QScrollArea (nunca
        # corta); conteúdo mínimo 560 px; salvar NA HORA com toast discreto.
        # =====================================================================
        montar = self._montar_pagina
        self._abas = [
            ("aparencia", "Aparência", "olho",
             "Tema, escala, animações e som — o jeitão do app.",
             [caixa_ap]),
            ("campanhas", "Campanhas", "cofre",
             "Eventos, dias fixos, ordem das categorias e as seções do "
             "tabloide agrupado.",
             [self._caixa_eventos(), self._widget_de(form_campanhas)]),
            ("ia", "IA local", "propriedades",
             "O servidor compatível com OpenAI (LM Studio/Ollama), os "
             "modelos e o semáforo da conciliação.",
             [self._caixa_ia_status(), caixa_ia, self._caixa_dica(),
              self._caixa_limiares(form_ia_extra)]),
            ("imagens", "Imagens", "imagem",
             "Upscale, recorte de fundo, a pasta da biblioteca, CMYK e o "
             "cache do OCR.",
             [self._widget_de(form_imagens)]),
            ("selos", "Selos", "check_circulo",
             "Seus selos próprios e os automáticos (+18, Qualidade).",
             [self._caixa_selos_legado]),
            ("sanitizacao", "Sanitização", "texto",
             "As regras do NOME: siglas, glossários e abreviações — o "
             "acervo só muda com prévia e confirmação.",
             [caixa_san, self._caixa_aplicar_acervo()]),
            ("backups", "Backups", "restaurar",
             "Backups do banco e os botões de manutenção — verificar, "
             "compactar, quarentena e o perfil de máquina fraca.",
             [self._widget_de(form_backups), self._caixa_backups_extra(),
              self._caixa_manutencao()]),
            ("atalhos", "Atalhos", "grade",
             "As teclas do app — clique na tecla, aperte a nova e pronto. "
             "Conflito é barrado; a folha de cola sai em PDF.",
             [self._caixa_atalhos()]),
            ("sobre", "Sobre", "info_circulo",
             "Versão, o que há de novo, o ícone do app e o diagnóstico "
             "para suporte.",
             [self._caixa_sobre()]),
        ]
        from PySide6.QtWidgets import QListWidgetItem, QStackedWidget
        self.lista_abas = QListWidget()
        self.lista_abas.setObjectName("listaAbasConfig")
        self.lista_abas.setFixedWidth(190)
        self._paginas = QStackedWidget()
        for chave, titulo, ic, descricao, blocos in self._abas:
            item = QListWidgetItem(icone(ic, tamanho=16), f" {titulo}")
            item.setData(Qt.ItemDataRole.UserRole, chave)
            self.lista_abas.addItem(item)
            self._paginas.addWidget(montar(titulo, descricao, blocos))
        self.lista_abas.currentRowChanged.connect(self._trocar_aba)

        # busca dentro das Configurações (passo 19)
        self.campo_busca_cfg = QLineEdit()
        self.campo_busca_cfg.setPlaceholderText(
            "Buscar uma opção… (ex.: “limiar”, “selo”, “backup”)")
        self.campo_busca_cfg.setClearButtonEnabled(True)
        self.campo_busca_cfg.setMinimumWidth(300)
        self.campo_busca_cfg.setMaximumWidth(460)
        self.campo_busca_cfg.textChanged.connect(self._filtrar_opcoes)
        hb.insertWidget(1, self.campo_busca_cfg)

        corpo = QHBoxLayout()
        corpo.setContentsMargins(0, 0, 0, 0)
        corpo.setSpacing(0)
        corpo.addWidget(self.lista_abas)
        corpo.addWidget(self._paginas, 1)

        raiz_lay = QVBoxLayout(self)
        raiz_lay.setContentsMargins(0, 0, 0, 0)
        raiz_lay.setSpacing(0)
        raiz_lay.addWidget(barra)
        raiz_lay.addLayout(corpo, 1)
        self.recarregar()
        self._ligar_salvar_na_hora()     # passo 17
        self._ir_para_ultima_aba()       # passo 21
        # passo 20: Ctrl+Tab circula as abas (R-018: do catálogo central)
        from app.qt.design.atalhos import criar_atalho
        criar_atalho("geral.abas_config", self,
                     lambda: self.lista_abas.setCurrentRow(
                         (self.lista_abas.currentRow() + 1)
                         % self.lista_abas.count()))
        from app.qt.design.polimento import ordenar_tab
        ordenar_tab(self)               # FASE 1 (passo 66): Tab visual

    # --- FASE 3: a carcaça ------------------------------------------------------

    def _widget_de(self, layout) -> QWidget:
        w = QWidget()
        w.setLayout(layout)
        return w

    def _montar_pagina(self, titulo: str, descricao: str,
                       blocos: list[QWidget]) -> QWidget:
        """Passos 12-14: página = cabeçalho (título grande + descrição) +
        blocos num QScrollArea próprio; conteúdo mínimo 560 px."""
        from PySide6.QtWidgets import QScrollArea
        conteudo = QWidget()
        conteudo.setMinimumWidth(560)
        vl = QVBoxLayout(conteudo)
        vl.setContentsMargins(t.ESPACO_3, t.ESPACO_3, t.ESPACO_3, t.ESPACO_3)
        vl.setSpacing(t.ESPACO_3)
        cab = QLabel(titulo)
        cab.setProperty("papel", "titulo")
        desc = QLabel(descricao)
        desc.setProperty("papel", "legenda")
        desc.setWordWrap(True)
        vl.addWidget(cab)
        vl.addWidget(desc)
        for bloco in blocos:
            vl.addWidget(bloco)
        vl.addStretch(1)
        rolagem = QScrollArea()
        rolagem.setWidget(conteudo)
        rolagem.setWidgetResizable(True)
        rolagem.setFrameShape(QScrollArea.Shape.NoFrame)
        return rolagem

    def _aba_em_construcao(self, texto: str) -> QWidget:
        from app.qt.design.componentes import EstadoVazio
        return EstadoVazio("propriedades", "Em construção nesta fase", texto)

    def _caixa_eventos(self) -> QWidget:
        """FASE 3 (passos 33-34/36): a lista dos Eventos (mesma fonte de
        verdade da Fase 2) — duplo-clique edita, ARRASTAR reordena (a
        ordem reflete no Início), combo de validade padrão por evento."""
        caixa = QWidget()
        vl = QVBoxLayout(caixa)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(t.ESP_2)
        rot = QLabel("SEUS EVENTOS")
        rot.setProperty("papel", "secao")
        vl.addWidget(rot)
        self.lista_eventos_cfg = QListWidget()
        self.lista_eventos_cfg.setToolTip(
            "Duplo-clique edita (nome, cor, dia, capa) · arraste para "
            "reordenar — a ordem vale no Início")
        self.lista_eventos_cfg.setDragDropMode(
            QListWidget.DragDropMode.InternalMove)
        self.lista_eventos_cfg.setMinimumHeight(120)
        self.lista_eventos_cfg.itemDoubleClicked.connect(
            self._editar_evento_cfg)
        self.lista_eventos_cfg.model().rowsMoved.connect(
            lambda *_: self._persistir_ordem_eventos())
        vl.addWidget(self.lista_eventos_cfg)
        # passo 36: validade padrão do evento SELECIONADO
        linha_val = QHBoxLayout()
        rot_val = QLabel("Validade padrão do evento selecionado")
        self.combo_validade_ev = QComboBox()
        self.combo_validade_ev.addItem(
            "até o próximo dia da campanha (padrão)", "dia")
        for n in (3, 5, 7):
            self.combo_validade_ev.addItem(f"válido por {n} dias", n)
        self.combo_validade_ev.setToolTip(
            "Como o app sugere o “ATÉ dd/mm” ao salvar um projeto deste "
            "evento sem validade")
        self.combo_validade_ev.activated.connect(self._trocar_validade_ev)
        self.lista_eventos_cfg.currentRowChanged.connect(
            lambda _r: self._refletir_validade_ev())
        linha_val.addWidget(rot_val)
        linha_val.addWidget(self.combo_validade_ev)
        linha_val.addStretch(1)
        vl.addLayout(linha_val)
        # passo 37 (semente do R-058): frases prontas com variáveis
        self.campo_frases = QPlainTextEdit()
        self.campo_frases.setPlaceholderText(
            "uma por linha — variáveis {data} e {evento}\n"
            "ex.: OFERTA VÁLIDA ATÉ {data} OU ENQUANTO DURAREM OS ESTOQUES")
        self.campo_frases.setMinimumHeight(64)
        self.campo_frases.setToolTip(
            "Frases prontas de aviso legal/validade — o texto legal do "
            "editor passa a oferecê-las na Fase 7 (por ora ficam guardadas)")
        self.campo_frases.textChanged.connect(
            lambda: self._salvar_debounce.start()
            if hasattr(self, "_salvar_debounce") else None)
        form_fr = QFormLayout()
        form_fr.addRow("Frases prontas (aviso legal)", self.campo_frases)
        vl.addLayout(form_fr)
        self._recarregar_eventos_cfg()
        return caixa

    def _recarregar_eventos_cfg(self) -> None:
        from PySide6.QtGui import QColor, QIcon, QPixmap
        from PySide6.QtWidgets import QListWidgetItem

        from app.qt.telas.eventos import listar_eventos
        self.lista_eventos_cfg.clear()
        nomes_dias = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
        try:
            eventos = listar_eventos()
        except Exception:
            eventos = []
        for ev in eventos:
            pm = QPixmap(14, 14)
            pm.fill(QColor(ev["cor"]))
            dia = (f' · toda {nomes_dias[ev["dia_semana"]]}'
                   if ev.get("dia_semana") is not None else "")
            item = QListWidgetItem(QIcon(pm), f'{ev["nome"]}{dia}')
            item.setData(Qt.ItemDataRole.UserRole, ev)
            self.lista_eventos_cfg.addItem(item)

    def _editar_evento_cfg(self, item) -> None:
        ev = item.data(Qt.ItemDataRole.UserRole)
        from app.core.database import Database
        from app.qt.telas import eventos as ev_srv
        from app.qt.telas.evento_dialog import EventoDialog
        dlg = EventoDialog(self, nome=ev["nome"], cor=ev["cor"],
                           dia_semana=ev["dia_semana"],
                           titulo="Salvar evento")
        if dlg.exec() != EventoDialog.DialogCode.Accepted:
            return
        novo_nome, cor, dia, capa = dlg.valores()
        db = Database().init()
        try:
            with db.Session() as s:
                if novo_nome != ev["nome"]:
                    ev_srv.renomear_evento(s, ev["id"], novo_nome)
                ev_srv.mudar_cor(s, ev["id"], cor)
                ev_srv.definir_dia(s, ev["id"], dia)
                if capa:
                    ev_srv.definir_capa(s, ev["id"], capa)
                s.commit()
        finally:
            db.engine.dispose()
        self._recarregar_eventos_cfg()

    def _persistir_ordem_eventos(self) -> None:
        """Passo 34: a ordem do drag vira `ordem` das entidades."""
        from app.core.database import Database
        from app.qt.telas.eventos import reordenar
        ids = []
        for i in range(self.lista_eventos_cfg.count()):
            ev = self.lista_eventos_cfg.item(i).data(Qt.ItemDataRole.UserRole)
            ids.append(ev["id"])
        db = Database().init()
        try:
            with db.Session() as s:
                reordenar(s, ids)
                s.commit()
        finally:
            db.engine.dispose()
        mostrar_toast(self, "Ordem dos eventos salva — vale no Início.")

    def _refletir_validade_ev(self) -> None:
        item = self.lista_eventos_cfg.currentItem()
        if item is None:
            return
        ev = item.data(Qt.ItemDataRole.UserRole)
        try:
            db = self._db()
            try:
                with db.Session() as s:
                    mapa = ConfigRepositorio(s).get(
                        "eventos.validade_regra") or {}
            finally:
                db.engine.dispose()
        except Exception:
            mapa = {}
        regra = mapa.get(ev["nome"], "dia")
        ix = self.combo_validade_ev.findData(regra)
        self.combo_validade_ev.setCurrentIndex(max(0, ix))

    def _trocar_validade_ev(self) -> None:
        item = self.lista_eventos_cfg.currentItem()
        if item is None:
            mostrar_toast(self, "Escolha um evento na lista primeiro.",
                          tipo="erro")
            return
        ev = item.data(Qt.ItemDataRole.UserRole)
        try:
            db = self._db()
            try:
                with db.Session() as s:
                    repo = ConfigRepositorio(s)
                    mapa = repo.get("eventos.validade_regra") or {}
                    mapa[ev["nome"]] = self.combo_validade_ev.currentData()
                    repo.set("eventos.validade_regra", mapa)
                    s.commit()
            finally:
                db.engine.dispose()
        except Exception:
            pass
        mostrar_toast(self, "Validade padrão salva.")

    # --- FASE 3, Bloco H: aba Backups + manutenção ------------------------------

    def _caixa_backups_extra(self) -> QWidget:
        """Passo 79: pasta visível, criar snapshot agora, abrir pasta."""
        from app.core.paths import SystemRoot
        self.rot_pasta_backups = QLineEdit()
        self.rot_pasta_backups.setReadOnly(True)
        try:
            self.rot_pasta_backups.setText(str(SystemRoot().backups))
        except Exception:
            pass
        btn_snap = QPushButton(" Criar backup agora")
        btn_snap.setIcon(icone("cofre", tamanho=14))
        btn_snap.setToolTip("Uma cópia manual do banco, fora da rotação "
                            "automática")
        btn_snap.clicked.connect(self._criar_snapshot_agora)
        btn_abrir = QPushButton(" Abrir pasta de backups")
        btn_abrir.setIcon(icone("abrir", tamanho=14))
        btn_abrir.clicked.connect(self._abrir_pasta_backups)
        linha = QHBoxLayout()
        linha.setSpacing(t.ESP_2)
        linha.addWidget(btn_snap)
        linha.addWidget(btn_abrir)
        linha.addStretch(1)
        vl = QVBoxLayout()
        vl.setSpacing(t.ESP_2)
        rot = QLabel("Onde os backups moram")
        rot.setProperty("papel", "secao")
        vl.addWidget(rot)
        vl.addWidget(self.rot_pasta_backups)
        vl.addLayout(linha)
        return self._widget_de(vl)

    def _criar_snapshot_agora(self) -> None:
        from pathlib import Path

        from app.core.cofre import criar_snapshot
        try:
            caminho = criar_snapshot(self._raiz, rotulo="manual")
        except Exception as exc:
            mostrar_toast(self, f"O snapshot falhou: {exc}", tipo="erro")
            return
        mostrar_toast(self, f"Backup criado: {Path(caminho).name}")

    def _abrir_pasta_backups(self) -> None:
        import os

        from app.core.paths import SystemRoot
        try:
            pasta = SystemRoot().backups
            pasta.mkdir(parents=True, exist_ok=True)
            os.startfile(str(pasta))
        except Exception as exc:
            mostrar_toast(self, f"Não abriu a pasta: {exc}", tipo="erro")

    def _caixa_manutencao(self) -> QWidget:
        """Passos 80-85: os botões de "consertar sozinho"."""
        rot = QLabel("Manutenção")
        rot.setProperty("papel", "secao")
        btn_verificar = QPushButton(" Verificar instalação")
        btn_verificar.setIcon(icone("check_circulo", tamanho=14))
        btn_verificar.setToolTip("Teste de fumaça: banco, pastas, fontes e "
                                 "a IA — relatório verde/vermelho (R-134)")
        btn_verificar.clicked.connect(self._verificar_instalacao)
        btn_compactar = QPushButton(" Compactar banco")
        btn_compactar.setIcon(icone("caixa", tamanho=14))
        btn_compactar.setToolTip("Faz uma faxina no arquivo do banco e libera o espaço de "
                                 "registros excluídos (R-135)")
        btn_compactar.clicked.connect(self._compactar_banco)
        btn_acervo = QPushButton(" Verificar integridade do acervo")
        btn_acervo.setIcon(icone("busca", tamanho=14))
        btn_acervo.setToolTip("Fotos órfãs vão para a QUARENTENA (nunca "
                              "apaga); produtos sem foto entram na lista "
                              "(R-129)")
        btn_acervo.clicked.connect(self._verificar_acervo)
        linha1 = QHBoxLayout()
        linha1.setSpacing(t.ESP_2)
        for b in (btn_verificar, btn_compactar, btn_acervo):
            linha1.addWidget(b)
        linha1.addStretch(1)
        self.rot_manutencao = QLabel("")
        self.rot_manutencao.setWordWrap(True)
        self.rot_manutencao.setTextFormat(Qt.TextFormat.RichText)
        # R-132: o perfil de máquina fraca (liga 4 chaves de uma vez)
        self.chk_maquina_fraca = QCheckBox(
            "Perfil de máquina fraca — para o PC do mercado")
        self.chk_maquina_fraca.setToolTip(
            "Liga DE UMA VEZ: animações reduzidas, transparências "
            "reduzidas, IA desligada e upscale desligado. Desmarcar "
            "devolve os padrões.")
        self.chk_maquina_fraca.toggled.connect(self._trocar_maquina_fraca)
        vl = QVBoxLayout()
        vl.setSpacing(t.ESP_2)
        vl.addWidget(rot)
        vl.addLayout(linha1)
        vl.addWidget(self.rot_manutencao)
        vl.addWidget(self.chk_maquina_fraca)
        return self._widget_de(vl)

    def _verificar_instalacao(self) -> None:
        """Passo 80 (R-134): relatório por item, sem travar (worker)."""
        from app.core.manutencao import verificar_instalacao
        from app.qt.workers import Trabalhador
        self.rot_manutencao.setText("Verificando…")

        def pronto(itens):
            linhas = []
            for it in itens:
                cor = t.SUCESSO if it["ok"] else (
                    t.ALERTA if not it["essencial"] else t.PERIGO)
                marca = "✓" if it["ok"] else "✗"
                linhas.append(f'<span style="color:{cor}">{marca} '
                              f'{it["nome"]}: {it["detalhe"]}</span>')
            self.rot_manutencao.setText("<br>".join(linhas))

        trab = Trabalhador(lambda _cb: verificar_instalacao())
        trab.ok.connect(pronto)
        trab.erro.connect(lambda m: self.rot_manutencao.setText(
            f'<span style="color:{t.PERIGO}">A verificação falhou: '
            f'{m}</span>'))
        self._trabalhos.rodar(trab)

    def _compactar_banco(self) -> None:
        from app.core.manutencao import compactar_banco
        try:
            antes, depois = compactar_banco(self._raiz)
        except Exception as exc:
            mostrar_toast(self, f"A compactação falhou: {exc}", tipo="erro")
            return
        kb = max(0, antes - depois) / 1024
        mostrar_toast(self, f"Banco compactado — {kb:.0f} KB liberados "
                            f"({antes/1024:.0f} → {depois/1024:.0f} KB).")

    def _verificar_acervo(self) -> None:
        """Passo 82 (R-129): lista + quarentena com CONFIRMAÇÃO."""
        from app.core.manutencao import quarentenar_orfas, verificar_acervo
        try:
            r = verificar_acervo(self._raiz)
        except Exception as exc:
            mostrar_toast(self, f"A verificação falhou: {exc}", tipo="erro")
            return
        orfas, sem_arq = r["orfas"], r["sem_arquivo"]
        if not orfas and not sem_arq:
            self.rot_manutencao.setText(
                f'<span style="color:{t.SUCESSO}">✓ Acervo íntegro — '
                'nenhuma foto órfã, nenhum produto sem arquivo.</span>')
            return
        partes = []
        if sem_arq:
            partes.append(f'<span style="color:{t.PERIGO}">✗ '
                          f'{len(sem_arq)} produto(s) com foto sumida: '
                          + "; ".join(n for _i, n, _c in sem_arq[:5])
                          + ("…" if len(sem_arq) > 5 else "") + "</span>")
        if orfas:
            partes.append(f'<span style="color:{t.ALERTA}">'
                          f'{len(orfas)} foto(s) órfã(s) no disco.</span>')
        self.rot_manutencao.setText("<br>".join(partes))
        if orfas:
            caixa = QMessageBox(self)
            caixa.setWindowTitle("Fotos órfãs")
            caixa.setIcon(QMessageBox.Icon.Question)
            caixa.setText(f"{len(orfas)} foto(s) sem produto apontando.")
            caixa.setInformativeText(
                "Mover para a pasta de quarentena "
                "(biblioteca_imagens/_quarentena/)? NADA é apagado — dá "
                "para voltar à mão quando quiser.")
            mover = caixa.addButton("Mover para a quarentena",
                                    QMessageBox.ButtonRole.AcceptRole)
            caixa.addButton("Deixar como está",
                            QMessageBox.ButtonRole.RejectRole)
            caixa.exec()
            if caixa.clickedButton() is mover:
                n = quarentenar_orfas(orfas, self._raiz)
                mostrar_toast(self, f"{n} foto(s) na quarentena — nada "
                                    "foi apagado.")

    def _trocar_maquina_fraca(self, ligar: bool) -> None:
        """Passo 85 (R-132): as 4 chaves de uma vez + reflexo nos toggles."""
        from app.core.manutencao import ativar_perfil_maquina_fraca
        try:
            ativar_perfil_maquina_fraca(ligar, self._raiz)
        except Exception as exc:
            mostrar_toast(self, f"Não apliquei o perfil: {exc}", tipo="erro")
            return
        self.recarregar()                 # os toggles espelham as chaves
        if ligar:
            mostrar_toast(self, "Perfil de máquina fraca LIGADO: animações "
                                "e transparências reduzidas, IA e upscale "
                                "desligados.")
        else:
            mostrar_toast(self, "Perfil desligado — tudo de volta ao "
                                "padrão.")

    # --- FASE 3, Bloco F: abas Imagens / Atalhos / Sobre ------------------------

    def _migrar_webp(self) -> None:
        """OS F11.5 #51/#52: prévia do ganho → confirma → migra em worker.
        O SENTIDO segue a chave WebP: ligada converte p/ WebP; desligada,
        de volta p/ PNG (reversível)."""
        from app.qt.telas import servico
        from app.qt.workers import Trabalhador
        para_webp = self.chk_webp.isChecked()
        rotulo = "WebP" if para_webp else "PNG"

        def _previa(st):
            return servico.migrar_acervo_webp(para_webp, st, previa=True)

        trab = Trabalhador(_previa)
        trab.status.connect(self._overlay.mostrar
                            if hasattr(self, "_overlay") else (lambda _m: None))

        def _mostrar(r):
            if hasattr(self, "_overlay"):
                self._overlay.esconder()
            if not r["fotos"]:
                mostrar_toast(self, f"Nada a converter — o acervo já está "
                                    f"em {rotulo}.")
                return
            mb_a = r["bytes_antes"] / 1_048_576
            mb_d = r["bytes_depois"] / 1_048_576
            from PySide6.QtWidgets import QMessageBox
            resp = QMessageBox.question(
                self, f"Migrar o acervo para {rotulo}?",
                f"{r['fotos']} foto(s): {mb_a:.1f} MB → {mb_d:.1f} MB "
                f"({mb_d - mb_a:+.1f} MB). Converter agora? (Reversível — "
                "rode de novo com a chave no outro estado para voltar.)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if resp != QMessageBox.StandardButton.Yes:
                return
            trab2 = Trabalhador(lambda st: servico.migrar_acervo_webp(
                para_webp, st, previa=False))
            trab2.ok.connect(lambda r2: mostrar_toast(
                self, f"{r2['fotos']} foto(s) convertidas para {rotulo}."
                + (f" {len(r2['puladas'])} pulada(s) — ilegíveis."
                   if r2["puladas"] else ""), tipo="sucesso"))
            trab2.erro.connect(lambda m: mostrar_toast(self, m, tipo="erro"))
            self._trabalhos.rodar(trab2)

        trab.ok.connect(_mostrar)
        trab.erro.connect(lambda m: mostrar_toast(self, m, tipo="erro"))
        self._trabalhos.rodar(trab)

    def _somente_leitura_mudou(self, ligado: bool) -> None:
        """R-131: LIGAR é direto (proteger é seguro); DESLIGAR é gesto
        consciente — pede confirmação (passo 5)."""
        if getattr(self, "_refletindo_somente_leitura", False):
            return
        from app.core import modo
        if not ligado and modo.somente_leitura():
            from PySide6.QtWidgets import QMessageBox
            resp = QMessageBox.question(
                self, "Sair do somente-leitura?",
                "Este PC volta a poder EDITAR o acervo e os projetos. "
                "Continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if resp != QMessageBox.StandardButton.Yes:
                self._refletindo_somente_leitura = True
                self.chk_somente_leitura.setChecked(True)
                self._refletindo_somente_leitura = False
                return
        modo.definir_somente_leitura(ligado)
        mostrar_toast(self, "Modo somente-leitura LIGADO — este PC só "
                            "aprova e imprime." if ligado
                      else "Modo somente-leitura desligado — edição "
                           "liberada.")

    def _migrar_antigo(self) -> None:
        """FASE 12: prévia → confirmação → migra em worker (chave natural)."""
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        from app.core.migracao_antiga import (
            analisar_banco_antigo, migrar_banco_antigo)
        arquivo, _ = QFileDialog.getOpenFileName(
            self, "O banco do AutoTabloide antigo", "",
            "Banco SQLite (*.db *.sqlite *.sqlite3);;Todos (*.*)")
        if not arquivo:
            return
        try:
            previa = analisar_banco_antigo(arquivo)
        except ValueError as exc:
            mostrar_toast(self, str(exc), tipo="erro")
            return
        resp = QMessageBox.question(
            self, "Trazer o acervo antigo?",
            f"O banco antigo tem {previa['total_antigo']} produto(s): "
            f"{previa['novos']} novo(s) para trazer e "
            f"{previa['existentes']} que você JÁ tem (serão pulados — "
            "nada duplica nem sobrescreve). Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp != QMessageBox.StandardButton.Yes:
            return
        from app.qt.workers import Trabalhador
        trab = Trabalhador(lambda st: migrar_banco_antigo(arquivo, st))
        trab.ok.connect(lambda r: mostrar_toast(
            self, f"Migração pronta: {r['importados']} trazidos, "
                  f"{r['pulados']} pulados (já existiam), "
                  f"{r['aliases']} apelidos aprendidos.", tipo="sucesso"))
        trab.erro.connect(lambda m: mostrar_toast(self, m, tipo="erro"))
        self._trabalhos.rodar(trab)

    def _verificar_atualizacao(self) -> None:
        """R-127 (FASE 12): checa em worker (a UI não congela); o resultado
        é sempre uma mensagem honesta — nunca obriga, nunca mente."""
        from app.core.atualizacao import verificar_atualizacao
        from app.qt.workers import Trabalhador
        trab = Trabalhador(lambda _st: verificar_atualizacao())

        def _pronto(r):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Verificar atualização",
                                    r["mensagem"])

        trab.ok.connect(_pronto)
        trab.erro.connect(lambda m: mostrar_toast(self, m, tipo="erro"))
        self._trabalhos.rodar(trab)

    def _abrir_correcoes(self) -> None:
        """OS F11.5 #43/#53/#91: ver/reverter os aliases aprendidos."""
        from app.qt.telas.correcoes_dialog import CorrecoesDialog
        CorrecoesDialog(self).exec()

    def _abrir_perfis(self) -> None:
        """OS F11.5 #5: a tela de perfis de exportação (salva na Config)."""
        from app.qt.telas.perfis_dialog import PerfisDialog
        dlg = PerfisDialog(self)
        if dlg.exec() == PerfisDialog.DialogCode.Accepted:
            mostrar_toast(self, "Perfis de exportação salvos.",
                          tipo="sucesso")

    def _abrir_pasta_biblioteca(self) -> None:
        """Passo 49: abre a pasta das fotos no Explorer."""
        import os

        from app.core.paths import SystemRoot
        pasta = SystemRoot().biblioteca_imagens
        try:
            os.startfile(str(pasta))          # Windows
        except Exception as exc:
            mostrar_toast(self, f"Não abriu a pasta: {exc}", tipo="erro")

    def _caixa_atalhos(self) -> QWidget:
        """Passos 53-55 (R-018): a tabela de atalhos EDITÁVEL — capturar
        tecla, conflito barrado, restaurar padrão, folha de cola em PDF."""
        from PySide6.QtWidgets import (
            QKeySequenceEdit, QTableWidget, QTableWidgetItem,
        )

        from app.qt.design.atalhos import CATALOGO, sequencia
        self.tabela_atalhos = QTableWidget(len(CATALOGO), 3)
        self.tabela_atalhos.setHorizontalHeaderLabels(
            ["Onde", "O que faz", "Tecla"])
        self.tabela_atalhos.horizontalHeader().setSectionResizeMode(
            1, self.tabela_atalhos.horizontalHeader().ResizeMode.Stretch)
        self.tabela_atalhos.verticalHeader().setVisible(False)
        self.tabela_atalhos.setMinimumHeight(360)
        self._ids_atalhos = list(CATALOGO)
        for r, id_ in enumerate(self._ids_atalhos):
            grupo, descr, _padrao = CATALOGO[id_]
            it_g = QTableWidgetItem(grupo)
            it_g.setFlags(it_g.flags() & ~Qt.ItemFlag.ItemIsEditable)
            it_d = QTableWidgetItem(descr)
            it_d.setFlags(it_d.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabela_atalhos.setItem(r, 0, it_g)
            self.tabela_atalhos.setItem(r, 1, it_d)
            captura = QKeySequenceEdit()
            captura.setKeySequence(sequencia(id_))
            captura.setMaximumSequenceLength(1)
            captura.editingFinished.connect(
                lambda id2=id_, w=captura: self._remapear_atalho(id2, w))
            self.tabela_atalhos.setCellWidget(r, 2, captura)
        btn_padrao = QPushButton(" Restaurar padrões")
        btn_padrao.setIcon(icone("restaurar", tamanho=14))
        btn_padrao.clicked.connect(self._restaurar_atalhos)
        btn_pdf = QPushButton(" Exportar folha de cola (PDF)")
        btn_pdf.setIcon(icone("impressora", tamanho=14))
        btn_pdf.setToolTip("Uma página com todos os atalhos, para deixar "
                           "do lado do teclado")
        btn_pdf.clicked.connect(self._exportar_folha_cola)
        linha = QHBoxLayout()
        linha.setSpacing(t.ESP_2)
        linha.addWidget(btn_padrao)
        linha.addWidget(btn_pdf)
        linha.addStretch(1)
        vl = QVBoxLayout()
        vl.setSpacing(t.ESP_2)
        vl.addWidget(self.tabela_atalhos)
        vl.addLayout(linha)
        return self._widget_de(vl)

    def _remapear_atalho(self, id_: str, captura) -> None:
        """Passo 53: valida o conflito ANTES de aplicar; tecla em uso é
        BARRADA (dois donos no Qt = nenhum dispara — lição do Ctrl+K)."""
        from app.qt.design.atalhos import aplicar, conflito, sequencia
        seq = captura.keySequence().toString()
        if not seq:                          # apagou = volta ao padrão
            from app.qt.design.atalhos import CATALOGO
            aplicar(id_, CATALOGO[id_][2])
            captura.setKeySequence(sequencia(id_))
            return
        dono = conflito(id_, seq)
        if dono:
            mostrar_toast(self, f"“{seq}” já é de: {dono} — escolha outra "
                                "tecla.", tipo="erro")
            captura.setKeySequence(sequencia(id_))     # reverte na tela
            return
        aplicar(id_, seq)                    # persiste E troca nos vivos
        mostrar_toast(self, f"Atalho aplicado: {seq}")

    def _restaurar_atalhos(self) -> None:
        from PySide6.QtWidgets import QKeySequenceEdit

        from app.qt.design.atalhos import restaurar_padrao, sequencia
        restaurar_padrao()
        for r, id_ in enumerate(self._ids_atalhos):
            w = self.tabela_atalhos.cellWidget(r, 2)
            if isinstance(w, QKeySequenceEdit):
                w.setKeySequence(sequencia(id_))
        mostrar_toast(self, "Todos os atalhos voltaram ao padrão.")

    def _exportar_folha_cola(self) -> None:
        """Passo 54: a folha de cola em PDF (uma página, por grupo)."""
        from PySide6.QtWidgets import QFileDialog

        from app.qt.design.atalhos import CATALOGO, sequencia
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Folha de cola dos atalhos", "atalhos_autotabloide.pdf",
            "PDF (*.pdf)")
        if not caminho:
            return
        grupos: dict[str, list[tuple[str, str]]] = {}
        for id_, (grupo, descr, _p) in CATALOGO.items():
            grupos.setdefault(grupo, []).append((descr, sequencia(id_)))
        html = ["<h1>AutoTabloide AI — atalhos do teclado</h1>"]
        for grupo, itens in grupos.items():
            html.append(f"<h2>{grupo}</h2>"
                        "<table border='0' cellspacing='0' cellpadding='4'>")
            for descr, seq in itens:
                html.append(f"<tr><td width='60%'>{descr}</td>"
                            f"<td><b>{seq}</b></td></tr>")
            html.append("</table>")
        try:
            from PySide6.QtGui import QPageSize, QTextDocument
            from PySide6.QtPrintSupport import QPrinter
            doc = QTextDocument()
            doc.setHtml("".join(html))
            impressora = QPrinter(QPrinter.PrinterMode.HighResolution)
            impressora.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            impressora.setOutputFileName(caminho)
            impressora.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            doc.print_(impressora)
        except Exception as exc:
            mostrar_toast(self, f"O PDF não saiu: {exc}", tipo="erro")
            return
        mostrar_toast(self, f"Folha de cola salva em {caminho}")

    def _caixa_sobre(self) -> QWidget:
        """Passo 56: versão, novidades em PT-BR, o campo da decisão A×B do
        ícone e o diagnóstico para suporte (R-128)."""
        from app import __version__
        rot_v = QLabel(f"AutoTabloide AI — versão {__version__}")
        rot_v.setProperty("papel", "titulo")
        rot_creditos = QLabel(
            "Feito para o Belo Brasil, do fluxo real do Otaviano: "
            "importar a oferta → conferir → montar → exportar.")
        rot_creditos.setProperty("papel", "legenda")
        rot_creditos.setWordWrap(True)
        novidades = QPlainTextEdit()
        novidades.setReadOnly(True)
        novidades.setMinimumHeight(150)
        novidades.setPlainText(
            "O que há de novo\n"
            "— Início repaginado: campanhas com capa, agenda da semana e "
            "“Produzir hoje”.\n"
            "— Configurações novas em 9 abas, com busca e salvar na hora.\n"
            "— Atalhos do teclado agora são editáveis (com folha de cola).\n"
            "— IA local com teste de conexão e interruptor mestre.\n"
            "— Editor: rotação, hifenização, célula como grupo, presets.\n"
            "— Exportação: cartaz com upscale automático e CMYK opcional.")
        self.combo_icone_app = QComboBox()
        self.combo_icone_app.addItem("“A” azul do AutoTabloide", "A")
        self.combo_icone_app.addItem("“B” laranja do Belo Brasil", "B")
        self.combo_icone_app.setToolTip(
            "O ícone da janela e da barra do Windows — aplica na hora.")
        self.combo_icone_app.activated.connect(self._trocar_icone_app)
        linha_ic = QHBoxLayout()
        rot_ic = QLabel("Ícone do aplicativo")
        linha_ic.addWidget(rot_ic)
        linha_ic.addWidget(self.combo_icone_app)
        linha_ic.addStretch(1)
        # passo 84 (R-133): o top de erros mora aqui no Sobre
        self.rot_top_erros = QLabel("")
        self.rot_top_erros.setProperty("papel", "legenda")
        self.rot_top_erros.setWordWrap(True)
        btn_diag = QPushButton(" Gerar diagnóstico para suporte")
        btn_diag.setIcon(icone("cofre", tamanho=14))
        btn_diag.setToolTip(
            "Um .zip pequeno com versões, contagens e o log de travamentos "
            "— SEM fotos, sem banco, sem seus textos (R-128).")
        btn_diag.clicked.connect(self._gerar_diagnostico)
        # R-127 (FASE 12): verificar atualização — honesto e nunca intrusivo
        btn_atualizar = QPushButton(" Verificar atualização")
        btn_atualizar.setIcon(icone("restaurar", tamanho=14))
        btn_atualizar.setToolTip(
            "Confere se há versão nova (precisa de internet). O app é "
            "offline — sem rede, nada muda e nada trava.")
        btn_atualizar.clicked.connect(self._verificar_atualizacao)
        linha_d = QHBoxLayout()
        linha_d.addWidget(btn_diag)
        linha_d.addWidget(btn_atualizar)
        linha_d.addStretch(1)
        vl = QVBoxLayout()
        vl.setSpacing(t.ESP_2)
        vl.addWidget(rot_v)
        vl.addWidget(rot_creditos)
        vl.addWidget(novidades)
        vl.addLayout(linha_ic)
        vl.addWidget(self.rot_top_erros)
        vl.addLayout(linha_d)
        return self._widget_de(vl)

    def _trocar_icone_app(self) -> None:
        """A decisão A×B do dono — persiste e aplica NA HORA."""
        escolha = self.combo_icone_app.currentData()
        try:
            db = self._db()
            try:
                with db.Session() as s:
                    ConfigRepositorio(s).set("app.icone", escolha)
                    s.commit()
            finally:
                db.engine.dispose()
        except Exception:
            pass
        from PySide6.QtWidgets import QApplication

        from app.qt.design.splash import icone_aplicativo
        app = QApplication.instance()
        if app is not None:
            app.setWindowIcon(icone_aplicativo())
        mostrar_toast(self, "Ícone trocado — vale para a janela agora e "
                            "para a barra no próximo boot.")

    def _gerar_diagnostico(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        from app.core.diagnostico import gerar_diagnostico
        # passo 83: sugere a ÁREA DE TRABALHO (fácil de achar p/ enviar)
        from pathlib import Path as _P
        sugestao = str(_P.home() / "Desktop" / "diagnostico_autotabloide.zip")
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Diagnóstico para suporte", sugestao, "Zip (*.zip)")
        if not caminho:
            return
        try:
            gerar_diagnostico(caminho)
        except Exception as exc:
            mostrar_toast(self, f"O diagnóstico falhou: {exc}", tipo="erro")
            return
        mostrar_toast(self, f"Diagnóstico salvo em {caminho} — pode enviar "
                            "para o suporte (não tem dados sensíveis).")

    # --- FASE 3, Bloco E: aba IA ------------------------------------------------

    def _caixa_ia_status(self) -> QWidget:
        """Passos 42-43+46: interruptor mestre, "Testar conexão" sem travar
        e o status em linguagem simples (R-090)."""
        from app.qt.workers import GerenciadorTrabalhos
        self._trabalhos = GerenciadorTrabalhos()   # threads só nos cliques

        self.chk_usar_ia = QCheckBox("Usar a inteligência artificial")
        self.chk_usar_ia.setToolTip(
            "O interruptor MESTRE. Desligado, o app continua funcionando: "
            "a conciliação usa só as regras (sem juiz), e leitura de foto, "
            "enriquecer nomes e Fica a Dica ficam indisponíveis — sempre "
            "com aviso, nunca em silêncio.")
        self.chk_usar_ia.toggled.connect(self._trocar_usar_ia)
        self.rot_ia_off = QLabel(
            "A IA está desligada: a conciliação usa só as regras; leitura "
            "de foto (OCR), enriquecer nomes e o Fica a Dica não funcionam "
            "até religar aqui.")
        self.rot_ia_off.setWordWrap(True)
        self.rot_ia_off.setStyleSheet(f"color: {t.ALERTA};")
        self.rot_ia_off.setVisible(False)

        self.btn_testar_ia = QPushButton(" Testar conexão")
        self.btn_testar_ia.setIcon(icone("propriedades", tamanho=16))
        self.btn_testar_ia.setToolTip(
            "Pinga o servidor de IA (LM Studio/Ollama) com a URL do campo "
            "abaixo — sem travar a tela.")
        self.btn_testar_ia.clicked.connect(self._testar_conexao_ia)
        self.rot_status_ia = QLabel("")
        self.rot_status_ia.setWordWrap(True)
        linha = QHBoxLayout()
        linha.setSpacing(t.ESP_2)
        linha.addWidget(self.btn_testar_ia)
        linha.addWidget(self.rot_status_ia, 1)
        # R-090: o detalhe em linguagem simples (um modelo por linha)
        self.rot_detalhe_ia = QLabel("")
        self.rot_detalhe_ia.setWordWrap(True)
        self.rot_detalhe_ia.setVisible(False)

        vl = QVBoxLayout()
        vl.setSpacing(t.ESP_2)
        vl.addWidget(self.chk_usar_ia)
        vl.addWidget(self.rot_ia_off)
        vl.addLayout(linha)
        vl.addWidget(self.rot_detalhe_ia)
        return self._widget_de(vl)

    def _trocar_usar_ia(self, ligada: bool) -> None:
        """Passo 46: persiste ``ia.usar`` na hora; desligar mostra o aviso
        de degradação (I2 — nada some em silêncio)."""
        try:
            db = self._db()
            try:
                with db.Session() as s:
                    ConfigRepositorio(s).set("ia.usar", bool(ligada))
                    s.commit()
            finally:
                db.engine.dispose()
        except Exception:
            pass
        self.rot_ia_off.setVisible(not ligada)
        if not ligada:
            mostrar_toast(self, "IA desligada — o app segue no modo "
                                "determinístico, com avisos.", tipo="erro")

    def _testar_conexao_ia(self) -> None:
        """Passo 42: pinga o endpoint NUM WORKER (a tela nunca congela) e
        pinta ligado/desligado em verde/vermelho."""
        from app.ai.client import ClienteOpenAICompat, ConfigIA
        from app.qt.workers import Trabalhador
        if not self.chk_usar_ia.isChecked():
            self.rot_status_ia.setStyleSheet(f"color: {t.PERIGO};")
            self.rot_status_ia.setText(
                "● Desligada pelo interruptor acima — religue para testar.")
            self.rot_detalhe_ia.setVisible(False)
            return
        padrao = ConfigIA()
        cfg = ConfigIA(
            base_url=self.campo_url.text().strip() or padrao.base_url,
            modelo_texto=(self.campo_mod_texto.text().strip()
                          or padrao.modelo_texto),
            modelo_visao=(self.campo_mod_visao.text().strip()
                          or padrao.modelo_visao),
            modelo_embeddings=(self.campo_mod_emb.text().strip()
                               or padrao.modelo_embeddings))
        self.btn_testar_ia.setEnabled(False)
        self.rot_status_ia.setStyleSheet("")
        self.rot_status_ia.setText("Testando…")
        self.rot_detalhe_ia.setVisible(False)

        def fn(_status):
            cli = ClienteOpenAICompat(cfg)
            ok = cli.disponivel()
            return {"ok": ok, "modelos": cli.listar_modelos() if ok else [],
                    "url": cfg.base_url,
                    "papeis": [("de texto (nomes, conciliação)",
                                cfg.modelo_texto),
                               ("de visão (ler foto de oferta)",
                                cfg.modelo_visao),
                               ("de embeddings (conciliação rápida)",
                                cfg.modelo_embeddings)]}

        trab = Trabalhador(fn)
        trab.ok.connect(self._resultado_teste_ia)
        trab.erro.connect(lambda m: self._resultado_teste_ia(
            {"ok": False, "modelos": [], "url": cfg.base_url, "papeis": []}))
        self._trabalhos.rodar(trab)

    def _resultado_teste_ia(self, d: dict) -> None:
        self.btn_testar_ia.setEnabled(True)
        if not d.get("ok"):
            self.rot_status_ia.setStyleSheet(f"color: {t.PERIGO};")
            self.rot_status_ia.setText(
                f"● Desligado — o servidor não respondeu em {d.get('url')}. "
                "Abra o LM Studio (ou Ollama) e teste de novo.")
            self.rot_detalhe_ia.setVisible(False)
            return
        modelos = d.get("modelos") or []
        self.rot_status_ia.setStyleSheet(f"color: {t.SUCESSO};")
        self.rot_status_ia.setText(
            f"● Ligado — {len(modelos)} modelo(s) prontos no servidor.")
        # R-090: linguagem simples, um papel por linha, sem jargão
        linhas = []
        for papel, nome in d.get("papeis", []):
            if any(nome.lower() in m.lower() or m.lower() in nome.lower()
                   for m in modelos):
                linhas.append(f"✓ O modelo {papel} está no servidor.")
            else:
                linhas.append(f"✗ O modelo {papel} — “{nome}” — não "
                              "apareceu na lista do servidor; confira o "
                              "nome no campo acima.")
        self.rot_detalhe_ia.setText("\n".join(linhas))
        self.rot_detalhe_ia.setVisible(True)

    def _caixa_dica(self) -> QWidget:
        """Passo 45 (R-088): o prompt do Fica a Dica editável, com prévia."""
        from app.ai.enriquecimento import PROMPT_DICA_PADRAO
        rot = QLabel("Como a IA escreve o “Fica a Dica”")
        rot.setProperty("papel", "secao")
        self.campo_prompt_dica = QPlainTextEdit()
        self.campo_prompt_dica.setPlaceholderText(PROMPT_DICA_PADRAO)
        self.campo_prompt_dica.setMinimumHeight(90)
        self.campo_prompt_dica.setToolTip(
            "A instrução que a IA recebe para escrever o quadro. Use "
            "{limite} onde o teto de caracteres da região deve entrar. "
            "Vazio = o texto padrão do app.")
        self.btn_previa_dica = QPushButton(" Ver prévia da dica")
        self.btn_previa_dica.setIcon(icone("olho", tamanho=16))
        self.btn_previa_dica.setToolTip(
            "Gera UMA dica de exemplo (com itens fictícios) usando o "
            "prompt acima — precisa da IA ligada.")
        self.btn_previa_dica.clicked.connect(self._previa_dica)
        self.rot_previa_dica = QLabel("")
        self.rot_previa_dica.setWordWrap(True)
        self.rot_previa_dica.setVisible(False)
        linha = QHBoxLayout()
        linha.addWidget(self.btn_previa_dica)
        linha.addStretch(1)
        vl = QVBoxLayout()
        vl.setSpacing(t.ESP_2)
        vl.addWidget(rot)
        vl.addWidget(self.campo_prompt_dica)
        vl.addLayout(linha)
        vl.addWidget(self.rot_previa_dica)
        return self._widget_de(vl)

    def _previa_dica(self) -> None:
        """A prévia REAL do passo 45: chama gerar_dica num worker com itens
        de exemplo; sem IA → aviso honesto (nunca uma prévia de mentira)."""
        from app.ai.client import ClienteOpenAICompat
        from app.ai.enriquecimento import gerar_dica
        from app.qt.workers import Trabalhador
        self._salvar(silencioso=True)      # a prévia usa o prompt SALVO
        self.btn_previa_dica.setEnabled(False)
        self.rot_previa_dica.setStyleSheet("")
        self.rot_previa_dica.setText("Gerando a prévia…")
        self.rot_previa_dica.setVisible(True)

        def fn(_status):
            return gerar_dica(
                ["Arroz Camil 5kg", "Feijão Rei 1kg", "Óleo Soya 900ml"],
                180, ClienteOpenAICompat())

        def pronto(dica):
            self.btn_previa_dica.setEnabled(True)
            if dica:
                self.rot_previa_dica.setText(f"“{dica}”")
            else:
                self.rot_previa_dica.setStyleSheet(f"color: {t.ALERTA};")
                self.rot_previa_dica.setText(
                    "A prévia não veio — a IA está desligada ou o servidor "
                    "não respondeu (teste a conexão acima).")

        trab = Trabalhador(fn)
        trab.ok.connect(pronto)
        trab.erro.connect(lambda _m: pronto(None))
        self._trabalhos.rodar(trab)

    def _caixa_limiares(self, form_ia_extra) -> QWidget:
        """Passo 44: os limiares com a explicação do que cada um faz."""
        rot = QLabel("Semáforo da conciliação")
        rot.setProperty("papel", "secao")
        exp = QLabel(
            "Quando você importa uma oferta, cada item ganha uma NOTA de 0 "
            "a 100 de parecença com o acervo. Nota igual ou acima do limiar "
            "do verde: casa sozinho. Entre o amarelo e o verde: pede a sua "
            "conferência. Abaixo do amarelo: tratado como produto novo.")
        exp.setProperty("papel", "legenda")
        exp.setWordWrap(True)
        vl = QVBoxLayout()
        vl.setSpacing(t.ESP_2)
        vl.addWidget(rot)
        vl.addWidget(exp)
        vl.addLayout(form_ia_extra)
        return self._widget_de(vl)

    def _caixa_aplicar_acervo(self) -> QWidget:
        """Passo 52 (semente): o C2 mora na aba Sanitização com botão claro."""
        caixa = QWidget()
        hl = QHBoxLayout(caixa)
        hl.setContentsMargins(0, 0, 0, 0)
        btn = QPushButton(" Aplicar regras ao acervo (com prévia)…")
        btn.setIcon(icone("olho", tamanho=16))
        btn.setToolTip("Mostra QUANTOS nomes mudariam — nada é reescrito "
                       "sem a sua confirmação (C2)")
        btn.clicked.connect(self._previa_acervo)
        hl.addWidget(btn)
        hl.addStretch(1)
        return caixa

    def _filtrar_opcoes(self, texto: str) -> None:
        """Passo 19: a busca esconde as LINHAS de formulário que não casam
        e apaga as abas sem nenhum resultado (a atual sempre navegável)."""
        alvo = texto.strip().lower()
        for i, (chave, _tit, _ic, _desc, _blocos) in enumerate(self._abas):
            pagina = self._paginas.widget(i)
            achou_na_aba = not alvo
            for form in pagina.findChildren(QFormLayout):
                for linha in range(form.rowCount()):
                    rotulo_item = form.itemAt(
                        linha, QFormLayout.ItemRole.LabelRole)
                    campo_item = form.itemAt(
                        linha, QFormLayout.ItemRole.FieldRole)
                    textos = []
                    for it in (rotulo_item, campo_item):
                        w = it.widget() if it else None
                        if w is not None:
                            textos.append(w.property("text") or "")
                            textos.append(w.toolTip() or "")
                    casa = (not alvo) or any(
                        alvo in str(x).lower() for x in textos)
                    form.setRowVisible(linha, casa)
                    achou_na_aba = achou_na_aba or casa
            item = self.lista_abas.item(i)
            item.setForeground(
                Qt.GlobalColor.gray if (alvo and not achou_na_aba)
                else self.lista_abas.palette().text())

    def _trocar_aba(self, linha: int) -> None:
        self._paginas.setCurrentIndex(linha)
        try:                             # passo 21: lembrar a última aba
            db = self._db()
            try:
                with db.Session() as s:
                    ConfigRepositorio(s).set(
                        "configuracoes.ultima_aba",
                        self._abas[linha][0] if 0 <= linha
                        < len(self._abas) else "aparencia")
                    s.commit()
            finally:
                db.engine.dispose()
        except Exception:
            pass

    def _ir_para_ultima_aba(self) -> None:
        try:
            db = self._db()
            try:
                with db.Session() as s:
                    chave = ConfigRepositorio(s).get(
                        "configuracoes.ultima_aba") or "aparencia"
            finally:
                db.engine.dispose()
        except Exception:
            chave = "aparencia"
        for i, (c, *_r) in enumerate(self._abas):
            if c == chave:
                self.lista_abas.setCurrentRow(i)
                return
        self.lista_abas.setCurrentRow(0)

    def _ligar_salvar_na_hora(self) -> None:
        """Passo 17: toda mudança salva sozinha (debounce de 700 ms) com
        toast discreto — nada de botão 'aplicar' esquecível. A validação
        do limiar (passo 18) continua barrando o salvar inválido."""
        from PySide6.QtCore import QTimer
        self._salvar_debounce = QTimer(self)
        self._salvar_debounce.setSingleShot(True)
        self._salvar_debounce.setInterval(700)
        self._salvar_debounce.timeout.connect(self._salvar_na_hora)
        for campo in (self.campo_siglas, self.campo_url,
                      self.campo_mod_texto, self.campo_mod_visao,
                      self.campo_mod_emb, self.campo_icc,
                      self.campo_categorias, self.campo_marcas,
                      self.campo_secao_cor):
            campo.textEdited.connect(lambda _t: self._salvar_debounce.start())
        self.campo_prompt_dica.textChanged.connect(
            lambda: self._salvar_debounce.start())
        for tabela in (self.campo_glossario, self.campo_abreviacoes):
            tabela.mudou.connect(lambda: self._salvar_debounce.start())
        self.campo_palavras_min.textEdited.connect(
            lambda _t: self._salvar_debounce.start())
        self.lista_ordem_nome.model().rowsMoved.connect(
            lambda *_a: self._salvar_debounce.start())
        for chk in (self.chk_upscale, self.chk_webp, self.chk_fundo_branco,
                    self.chk_estudio_gerador):
            chk.toggled.connect(lambda _v: self._salvar_debounce.start())
        for campo in (self.campo_verde, self.campo_amarelo,
                      self.campo_rotacao, self.campo_secao_esp):
            campo.valueChanged.connect(
                lambda _v: self._salvar_debounce.start())
        for campo in (self.campo_cmyk, self.campo_secao_por_cat):
            campo.toggled.connect(lambda _v: self._salvar_debounce.start())
        self.campo_secao_estilo.activated.connect(
            lambda _i: self._salvar_debounce.start())
        self.campo_rembg.activated.connect(
            lambda _i: self._salvar_debounce.start())

    def _salvar_na_hora(self) -> None:
        ok = self._salvar(silencioso=True)
        # passo 18: inválido trava com borda vermelha + dica
        for campo in (self.campo_verde, self.campo_amarelo):
            campo.setProperty("invalido", not ok)
            campo.style().unpolish(campo)
            campo.style().polish(campo)
        if ok:
            mostrar_toast(self, "Salvo.")
        else:
            self.campo_verde.setToolTip(
                "O limiar do verde precisa ser MAIOR que o do amarelo — "
                "nada foi salvo até corrigir.")

    # --- banco ------------------------------------------------------------------------

    def _db(self) -> Database:
        return Database(self._raiz).init()

    def _trocar_escala(self) -> None:
        """Passo 64: aplica e persiste a escala escolhida na hora."""
        from app.qt.design.tema import trocar_escala
        trocar_escala(int(self.combo_escala.currentData()))

    def _trocar_animacoes(self, ligadas: bool) -> None:
        """FASE 3 (passo 26): persiste e o motor recarrega NA HORA."""
        try:
            db = self._db()
            try:
                with db.Session() as s:
                    ConfigRepositorio(s).set(
                        "aparencia.animacoes",
                        "ligadas" if ligadas else "reduzidas")
                    s.commit()
            finally:
                db.engine.dispose()
        except Exception:
            pass
        from app.qt.design.animacoes import recarregar_config
        recarregar_config()

    def _trocar_transparencias(self, reduzir: bool) -> None:
        """FASE 3 (passo 29): os véus translúcidos deixam de ser pintados."""
        try:
            db = self._db()
            try:
                with db.Session() as s:
                    ConfigRepositorio(s).set(
                        "aparencia.transparencias",
                        "reduzidas" if reduzir else "normais")
                    s.commit()
            finally:
                db.engine.dispose()
        except Exception:
            pass
        from app.qt.design.animacoes import recarregar_config
        recarregar_config()

    def _testar_som(self) -> None:
        """FASE 3 (passo 28): toca o som SEM depender da chave ligada."""
        from pathlib import Path

        from app.qt.design.som import _WAV
        try:
            import winsound
            winsound.PlaySound(str(_WAV),
                               winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as exc:
            mostrar_toast(self, f"O som não tocou: {exc}", tipo="erro")

    def _trocar_som(self, ligado: bool) -> None:
        """Passo 74: persiste na hora (e dá a prova tocando 1x ao ligar)."""
        try:
            db = self._db()
            try:
                with db.Session() as s:
                    ConfigRepositorio(s).set(
                        "aparencia.som", "ligado" if ligado else "desligado")
                    s.commit()
            finally:
                db.engine.dispose()
        except Exception:
            pass
        if ligado:
            from app.qt.design.som import tocar_exportou
            tocar_exportou()

    def recarregar(self) -> None:
        """Campos ← Config (chave ausente = padrão são, C3)."""
        db = self._db()
        try:
            with db.Session() as s:
                cfg = ConfigRepositorio(s)
                siglas = cfg.get("sanitizacao.siglas") or []
                self.campo_siglas.setText(", ".join(siglas))
                glossario = cfg.get("sanitizacao.glossario") or {}
                self.campo_glossario.definir(glossario)
                abreviacoes = cfg.get("tabloide.abreviacoes") or {}
                self.campo_abreviacoes.definir(abreviacoes)
                # FASE 3 (passo 51): ordem do nome + palavras minúsculas
                from app.ai.enriquecimento import ORDEM_NOME_PADRAO
                ordem = cfg.get("sanitizacao.ordem")
                if (not isinstance(ordem, list)
                        or sorted(ordem) != sorted(ORDEM_NOME_PADRAO)):
                    ordem = list(ORDEM_NOME_PADRAO)
                self.lista_ordem_nome.blockSignals(True)
                self.lista_ordem_nome.clear()
                for bloco in ordem:
                    self.lista_ordem_nome.addItem(bloco)
                self.lista_ordem_nome.blockSignals(False)
                minusculas = cfg.get("sanitizacao.palavras_minusculas") or []
                self.campo_palavras_min.setText(", ".join(minusculas))
                # FASE 3 (passos 49-50): aba Imagens
                self.chk_upscale.setChecked(
                    cfg.get("imagem.upscale_auto", True) is not False)
                self.chk_webp.setChecked(
                    bool(cfg.get("imagem.webp", False)))
                self.chk_fundo_branco.setChecked(
                    bool(cfg.get("imagem.detector_fundo_branco", False)))
                self.chk_estudio_gerador.setChecked(
                    bool(cfg.get("estudio.gerador", False)))
                from app.core.paths import SystemRoot
                self.rot_pasta_bib.setText(
                    str(SystemRoot().biblioteca_imagens))
                # passo 56: o ícone A×B do dono
                ix_ic = self.combo_icone_app.findData(
                    str(cfg.get("app.icone") or "A").upper())
                self.combo_icone_app.setCurrentIndex(max(0, ix_ic))
                # passo 85 (R-132): o perfil de máquina fraca
                self.chk_maquina_fraca.blockSignals(True)
                self.chk_maquina_fraca.setChecked(
                    bool(cfg.get("aparencia.maquina_fraca", False)))
                self.chk_maquina_fraca.blockSignals(False)
                # passo 84 (R-133): top 3 funções com erro, no Sobre
                from app.core.manutencao import top_erros
                top = top_erros(3, self._raiz)
                if top:
                    self.rot_top_erros.setText(
                        "Funções com mais erros registrados (ajuda a "
                        "priorizar o próximo conserto): "
                        + " · ".join(f"{k} ({v}×)" for k, v in top))
                else:
                    self.rot_top_erros.setText(
                        "Nenhum erro registrado até agora — bom sinal.")
                self.campo_url.setText(str(cfg.get("ia.base_url") or ""))
                self.campo_mod_texto.setText(
                    str(cfg.get("ia.modelo_texto") or ""))
                self.campo_mod_visao.setText(
                    str(cfg.get("ia.modelo_visao") or ""))
                self.campo_mod_emb.setText(
                    str(cfg.get("ia.modelo_embeddings") or ""))
                padrao = LimiaresConciliacao()
                self.campo_verde.setValue(
                    float(cfg.get("conciliacao.verde", padrao.verde)))
                self.campo_amarelo.setValue(
                    float(cfg.get("conciliacao.amarelo", padrao.amarelo)))
                self.campo_rotacao.setValue(
                    int(cfg.get("backups.rotacao", ROTACAO_PADRAO)))
                self.campo_cmyk.setChecked(
                    bool(cfg.get("export.cmyk_pdf", False)))
                self.campo_icc.setText(str(cfg.get("export.perfil_icc") or ""))
                categorias = cfg.get("categorias.ordem") or []
                self.campo_categorias.setText(", ".join(categorias))
                from app.qt.telas.servico import MARCAS_PROPRIAS_PADRAO
                marcas = cfg.get("marcas.proprias") or MARCAS_PROPRIAS_PADRAO
                self.campo_marcas.setText(", ".join(marcas))
                modelo = str(cfg.get("imagem.modelo_rembg")
                             or self._modelos_rembg[0])
                if modelo in self._modelos_rembg:
                    self.campo_rembg.setCurrentIndex(
                        self._modelos_rembg.index(modelo))
                from app.rendering.secoes import (
                    COR_PADRAO, ESPESSURA_PADRAO_MM, ESTILO_PADRAO,
                )
                self.campo_secao_cor.setText(
                    str(cfg.get("secoes.cor") or COR_PADRAO))
                self.campo_secao_esp.setValue(float(
                    cfg.get("secoes.espessura_mm", ESPESSURA_PADRAO_MM)))
                estilo = str(cfg.get("secoes.estilo") or ESTILO_PADRAO)
                ix = self.campo_secao_estilo.findData(estilo)
                self.campo_secao_estilo.setCurrentIndex(max(0, ix))
                self.campo_secao_por_cat.setChecked(
                    bool(cfg.get("secoes.cores_por_categoria", False)))
                # FASE 1 (passo 74): refletir sem disparar o toggle
                self.chk_som.blockSignals(True)
                self.chk_som.setChecked(
                    str(cfg.get("aparencia.som") or "") == "ligado")
                self.chk_som.blockSignals(False)
                # FASE 3 (passos 26/29): idem para animações/transparências
                self.chk_animacoes.blockSignals(True)
                self.chk_animacoes.setChecked(
                    str(cfg.get("aparencia.animacoes") or "ligadas")
                    != "reduzidas")
                self.chk_animacoes.blockSignals(False)
                self.chk_transparencias.blockSignals(True)
                self.chk_transparencias.setChecked(
                    str(cfg.get("aparencia.transparencias") or "")
                    == "reduzidas")
                self.chk_transparencias.blockSignals(False)
                # FASE 3 (Bloco E): interruptor mestre + prompt da dica
                self.chk_usar_ia.blockSignals(True)
                ia_usar = cfg.get("ia.usar", True) is not False
                self.chk_usar_ia.setChecked(ia_usar)
                self.chk_usar_ia.blockSignals(False)
                self.rot_ia_off.setVisible(not ia_usar)
                self.campo_prompt_dica.blockSignals(True)
                self.campo_prompt_dica.setPlainText(
                    str(cfg.get("ia.prompt_dica") or ""))
                self.campo_prompt_dica.blockSignals(False)
                # OS F11.5: refletir as frases prontas salvas (bug latente —
                # sem o load, QUALQUER salvamento da tela zerava a lista, já
                # que o save grava tudo) e os sinônimos do dono (#47/#81)
                if hasattr(self, "campo_frases"):
                    self.campo_frases.blockSignals(True)
                    self.campo_frases.setPlainText("\n".join(
                        cfg.get("frases.validade", []) or []))
                    self.campo_frases.blockSignals(False)
                if hasattr(self, "campo_sinonimos"):
                    self.campo_sinonimos.blockSignals(True)
                    self.campo_sinonimos.setPlainText("\n".join(
                        ", ".join(g) for g in
                        (cfg.get("sinonimos.regionais", []) or [])))
                    self.campo_sinonimos.blockSignals(False)
                # R-131 (FASE 12): refletir a chave sem disparar o handler
                if hasattr(self, "chk_somente_leitura"):
                    self._refletindo_somente_leitura = True
                    self.chk_somente_leitura.setChecked(
                        bool(cfg.get("app.somente_leitura", False)))
                    self._refletindo_somente_leitura = False
        finally:
            db.engine.dispose()
        self._recarregar_selos()   # RG-33 (conexão própria, fora do with)
        # FASE 3 (pego na FOTO do passo 47): refletir a Config nos campos
        # dispara textChanged e agendava um salvamento fantasma — o toast
        # "Salvo." aparecia sem o usuário tocar em nada. Refletir NÃO é
        # editar: mata o debounce agendado pelos sets síncronos acima.
        if hasattr(self, "_salvar_debounce"):
            self._salvar_debounce.stop()

    def showEvent(self, ev) -> None:  # noqa: N802 (Qt)
        super().showEvent(ev)
        self.recarregar()

    def _preset_setores(self) -> None:
        """RG-44: semente da ordem — o campo fica editável como sempre."""
        from app.qt.telas.servico import ORDEM_SETORES_LOJA
        self.campo_categorias.setText(", ".join(ORDEM_SETORES_LOJA))

    # --- selos personalizados (RG-33) ---------------------------------------------

    def _icone_do_selo(self, selo):
        """Miniatura: a arte do disco, ou o badge interno desenhado."""
        from PySide6.QtGui import QIcon, QImage, QPixmap

        from app.core.paths import SystemRoot
        from app.rendering.selos import Canto
        from app.rendering.selos import Selo as SeloRender
        from app.rendering.selos import render_selo
        try:
            caminho = (SystemRoot().selos / selo.arquivo
                       if selo.arquivo else None)
            if caminho is not None and caminho.exists():
                return QIcon(str(caminho))
            tipo = ("MAIS18" if selo.regra == "bebida_alcoolica" else
                    "QUALIDADE" if selo.regra == "marca_propria"
                    else selo.nome)
            img = render_selo(SeloRender(tipo, Canto.SUPERIOR_DIREITO), 40)
            qimg = QImage(img.tobytes("raw", "RGBA"), img.width,
                          img.height, QImage.Format.Format_RGBA8888)
            return QIcon(QPixmap.fromImage(qimg))
        except Exception:
            return icone("selo", tamanho=24)

    def _recarregar_selos(self) -> None:
        """FASE 3 (passo 65): a grade — todos os selos da tabela."""
        from PySide6.QtWidgets import QListWidgetItem

        from app.core.selos import listar_selos, migrar_selos
        self.lista_selos.clear()
        try:
            db = self._db()
            try:
                with db.Session() as s:
                    migrar_selos(s)
                    s.commit()
                    selos = [(x.id, x.nome, x.tipo, x.regra, x.ativo, x)
                             for x in listar_selos(s)]
                    # o ícone precisa dos campos ANTES da sessão fechar
                    itens = []
                    for sid, nome, tipo, regra, ativo, obj in selos:
                        rot_tipo = ("automático — bebida alcoólica"
                                    if regra == "bebida_alcoolica" else
                                    "automático — marca própria"
                                    if regra == "marca_propria" else "manual")
                        texto = f"{nome}   ({rot_tipo})"
                        if not ativo:
                            texto += "  ·  DESLIGADO"
                        itens.append((sid, texto, self._icone_do_selo(obj)))
            finally:
                db.engine.dispose()
        except Exception:
            return
        for sid, texto, ic in itens:
            item = QListWidgetItem(ic, texto)
            item.setData(Qt.ItemDataRole.UserRole, sid)
            self.lista_selos.addItem(item)

    def _adicionar_selo(self) -> None:
        from PySide6.QtWidgets import QFileDialog, QInputDialog

        from app.qt.telas.servico import adicionar_selo_personalizado
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Arte do selo", "", "Imagens (*.png *.jpg *.jpeg *.webp)")
        if not caminho:
            return
        nome, ok = QInputDialog.getText(
            self, "Novo selo", "Nome do selo (ex.: Muito Barato):")
        if not ok or not nome.strip():
            return
        try:
            adicionar_selo_personalizado(nome.strip(), caminho)
        except Exception as exc:
            mostrar_toast(self, f"Arte inválida: {exc}", tipo="erro")
            return
        self._recarregar_selos()
        mostrar_toast(self, f"Selo “{nome.strip()}” pronto — use pelo botão "
                            "direito no item da Mesa.")

    def _remover_selo(self) -> None:
        """Passo 66: manual sai; automático DESLIGA; +18 é lei (recusa)."""
        from app.core.models import Selo as SeloModelo
        from app.core.selos import REGRA_MAIS18, excluir_selo
        item = self.lista_selos.currentItem()
        if item is None:
            return
        sid = item.data(Qt.ItemDataRole.UserRole)
        db = self._db()
        try:
            with db.Session() as s:
                selo = s.get(SeloModelo, sid)
                if selo is None:
                    return
                nome, tipo, regra = selo.nome, selo.tipo, selo.regra
                ok = excluir_selo(s, sid)
                s.commit()
        finally:
            db.engine.dispose()
        self._recarregar_selos()
        if not ok and regra == REGRA_MAIS18:
            mostrar_toast(self, "O +18 em bebida alcoólica é LEI DA CASA — "
                                "não desliga (pode trocar a arte no "
                                "Editar).", tipo="erro")
        elif tipo == "automatico":
            mostrar_toast(self, f"Regra do selo “{nome}” DESLIGADA — o "
                                "conceito fica no gestor; religue quando "
                                "quiser (Editar).")
        else:
            mostrar_toast(self, f"Selo “{nome}” removido do gestor (a arte "
                                "fica em selos/ — projetos congelados não "
                                "quebram).")

    def _editar_selo(self, item) -> None:
        """Passos 66-67: nome, canto, arte e (nos automáticos) ligar/
        desligar a regra — o +18 aparece travado com a explicação."""
        if item is None:
            return
        from PySide6.QtWidgets import (
            QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
        )

        from app.core.models import Selo as SeloModelo
        from app.core.selos import CANTOS, REGRA_MAIS18, definir_ativo
        sid = item.data(Qt.ItemDataRole.UserRole)
        db = self._db()
        try:
            with db.Session() as s:
                selo = s.get(SeloModelo, sid)
                if selo is None:
                    return
                dados = {"nome": selo.nome, "canto": selo.canto,
                         "tipo": selo.tipo, "regra": selo.regra,
                         "ativo": selo.ativo, "arquivo": selo.arquivo}
        finally:
            db.engine.dispose()

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Selo — {dados['nome']}")
        form = QFormLayout(dlg)
        campo_nome = QLineEdit(dados["nome"])
        combo_canto = QComboBox()
        rotulos = {"SUPERIOR_ESQUERDO": "canto superior esquerdo",
                   "SUPERIOR_DIREITO": "canto superior direito",
                   "INFERIOR_ESQUERDO": "canto inferior esquerdo",
                   "INFERIOR_DIREITO": "canto inferior direito"}
        for c in CANTOS:
            combo_canto.addItem(rotulos[c], c)
        combo_canto.setCurrentIndex(max(0, list(CANTOS).index(
            dados["canto"]) if dados["canto"] in CANTOS else 1))
        chk_ativo = QCheckBox("Regra ligada (o selo sai sozinho)")
        chk_ativo.setChecked(bool(dados["ativo"]))
        nova_arte: list[str] = []
        btn_arte = QPushButton("Trocar arte (PNG)…")

        def _escolher_arte():
            caminho, _ = QFileDialog.getOpenFileName(
                dlg, "Arte do selo", "",
                "Imagens (*.png *.jpg *.jpeg *.webp)")
            if caminho:
                nova_arte.clear()
                nova_arte.append(caminho)
                btn_arte.setText("Arte escolhida ✓")
        btn_arte.clicked.connect(_escolher_arte)
        form.addRow("Nome", campo_nome)
        form.addRow("Canto", combo_canto)
        form.addRow(btn_arte)
        if dados["tipo"] == "automatico":
            if dados["regra"] == REGRA_MAIS18:
                chk_ativo.setChecked(True)
                chk_ativo.setEnabled(False)
                chk_ativo.setText("Regra ligada — o +18 em bebida "
                                  "alcoólica é lei da casa")
            form.addRow(chk_ativo)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                  | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(dlg.accept)
        botoes.rejected.connect(dlg.reject)
        form.addRow(botoes)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        arquivo_rel = None
        if nova_arte:
            import re as _re

            from PIL import Image as _Img

            from app.core.paths import SystemRoot
            pasta = SystemRoot().selos
            pasta.mkdir(parents=True, exist_ok=True)
            slug = _re.sub(r"[^a-z0-9]+", "_",
                           campo_nome.text().lower()).strip("_") or "selo"
            destino = pasta / f"{slug}.png"
            try:
                _Img.open(nova_arte[0]).convert("RGBA").save(destino)
                arquivo_rel = destino.name
            except Exception as exc:
                mostrar_toast(self, f"Arte inválida: {exc}", tipo="erro")
                return
        from app.core.selos import editar_selo
        db = self._db()
        try:
            with db.Session() as s:
                editar_selo(s, sid, nome=campo_nome.text(),
                            canto=combo_canto.currentData(),
                            arquivo=arquivo_rel)
                if dados["tipo"] == "automatico":
                    definir_ativo(s, sid, chk_ativo.isChecked())
                s.commit()
        finally:
            db.engine.dispose()
        self._recarregar_selos()
        mostrar_toast(self, "Selo atualizado.")

    # --- salvar -------------------------------------------------------------------------

    def _glossario_da_tela(self) -> tuple[dict[str, str], int]:
        """FASE 3 (passo 51): agora direto da TABELA (linha incompleta =
        ignorada, contada — I2). Sigla vira MAIÚSCULA, como sempre."""
        pares, ignoradas = self.campo_glossario.pares()
        return {k.upper(): v for k, v in pares.items()}, ignoradas

    def _abreviacoes_da_tela(self) -> tuple[dict[str, str], int]:
        """RG-22 — FASE 3 (passo 51): direto da TABELA."""
        return self.campo_abreviacoes.pares()

    def _salvar(self, silencioso: bool = False) -> bool:
        verde = self.campo_verde.value()
        amarelo = self.campo_amarelo.value()
        if verde <= amarelo:
            if not silencioso:
                mostrar_toast(self, "O limiar do verde precisa ser MAIOR que "
                                    "o do amarelo — nada foi salvo.",
                              tipo="erro")
            return False
        glossario, ignoradas = self._glossario_da_tela()
        abreviacoes, abrev_ignoradas = self._abreviacoes_da_tela()
        ignoradas += abrev_ignoradas
        siglas = [s.strip().upper()
                  for s in self.campo_siglas.text().split(",") if s.strip()]
        db = self._db()
        try:
            with db.Session() as s:
                cfg = ConfigRepositorio(s)
                cfg.set("sanitizacao.siglas", siglas)
                cfg.set("sanitizacao.glossario", glossario)
                cfg.set("tabloide.abreviacoes", abreviacoes)   # RG-22
                cfg.set("ia.base_url", self.campo_url.text().strip())
                cfg.set("ia.modelo_texto", self.campo_mod_texto.text().strip())
                cfg.set("ia.modelo_visao", self.campo_mod_visao.text().strip())
                cfg.set("ia.modelo_embeddings", self.campo_mod_emb.text().strip())
                cfg.set("ia.prompt_dica",              # passo 45 (R-088)
                        self.campo_prompt_dica.toPlainText().strip())
                cfg.set("conciliacao.verde", verde)
                cfg.set("conciliacao.amarelo", amarelo)
                cfg.set("backups.rotacao", self.campo_rotacao.value())
                cfg.set("export.cmyk_pdf", self.campo_cmyk.isChecked())
                cfg.set("export.perfil_icc", self.campo_icc.text().strip())
                cfg.set("categorias.ordem",
                        [c.strip() for c in
                         self.campo_categorias.text().split(",") if c.strip()])
                cfg.set("marcas.proprias",
                        [m.strip() for m in
                         self.campo_marcas.text().split(",") if m.strip()])
                # passo 61: `eventos.dias` NÃO é mais gravada aqui — o dia
                # da campanha vive na entidade Evento (gestor visual); a
                # chave antiga fica intocada para a migração de bancos velhos
                # FASE 3 (passo 37): frases prontas (semente do R-058)
                if hasattr(self, "campo_frases"):
                    cfg.set("frases.validade",
                            [ln.strip() for ln in
                             self.campo_frases.toPlainText().splitlines()
                             if ln.strip()])
                # OS F11.5 #47/#81: os grupos de sinônimos do dono (R-086)
                if hasattr(self, "campo_sinonimos"):
                    grupos = []
                    for ln in (self.campo_sinonimos.toPlainText()
                               .splitlines()):
                        termos = [t.strip() for t in ln.split(",")
                                  if t.strip()]
                        if len(termos) >= 2:
                            grupos.append(termos)
                    cfg.set("sinonimos.regionais", grupos)
                cfg.set("secoes.cor", self.campo_secao_cor.text().strip())
                cfg.set("secoes.espessura_mm", self.campo_secao_esp.value())
                cfg.set("secoes.estilo",
                        self.campo_secao_estilo.currentData())   # RG-31
                cfg.set("secoes.cores_por_categoria",
                        self.campo_secao_por_cat.isChecked())
                cfg.set("imagem.modelo_rembg",
                        self._modelos_rembg[self.campo_rembg.currentIndex()])
                # FASE 3 (Bloco F): sanitização fina + aba Imagens
                cfg.set("sanitizacao.ordem",
                        [self.lista_ordem_nome.item(i).text()
                         for i in range(self.lista_ordem_nome.count())])
                cfg.set("sanitizacao.palavras_minusculas",
                        [p.strip().lower() for p in
                         self.campo_palavras_min.text().split(",")
                         if p.strip()])
                cfg.set("imagem.upscale_auto", self.chk_upscale.isChecked())
                cfg.set("imagem.webp", self.chk_webp.isChecked())
                cfg.set("imagem.detector_fundo_branco",
                        self.chk_fundo_branco.isChecked())
                cfg.set("estudio.gerador",
                        self.chk_estudio_gerador.isChecked())
                s.commit()
        finally:
            db.engine.dispose()
        aviso = (f" ({ignoradas} linha(s) do glossário ignoradas — use "
                 "SIGLA = expansão)") if ignoradas else ""
        if not silencioso or ignoradas:      # linha ruim SEMPRE avisa (I2)
            mostrar_toast(self, f"Configurações salvas.{aviso}",
                          tipo="erro" if ignoradas else "info")
        return True

    def _limpar_cache_ocr(self) -> None:
        from app.ai.ocr import cache_limpar
        n = cache_limpar()
        mostrar_toast(self, f"{n} leitura(s) de foto esquecidas — a próxima "
                            "importação relê com a IA.")

    # --- C2: prévia no acervo (nunca reescrever em silêncio) ---------------------------

    def _previa_acervo(self) -> None:
        from app.core.configuracao import aplicar_reformatacao, previa_reformatacao

        if not self._salvar():
            return
        db = self._db()
        try:
            with db.Session() as s:
                regras = regras_de_config(s)
                mudancas = previa_reformatacao(s, regras)
                if not mudancas:
                    mostrar_toast(self, "Nada mudaria no acervo com as regras "
                                        "atuais.")
                    return
                amostra = "\n".join(f"• {antes}  →  {depois}"
                                    for antes, depois in mudancas[:12])
                if len(mudancas) > 12:
                    amostra += "\n…"
                caixa = QMessageBox(self)
                caixa.setWindowTitle("Prévia — aplicar ao acervo")
                caixa.setIcon(QMessageBox.Icon.Question)
                caixa.setText(f"{len(mudancas)} nome(s) mudariam no acervo:")
                caixa.setInformativeText(amostra)
                aplicar = caixa.addButton("Aplicar ao acervo",
                                          QMessageBox.ButtonRole.AcceptRole)
                caixa.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
                caixa.exec()
                if caixa.clickedButton() is not aplicar:
                    mostrar_toast(self, "Nada foi alterado.")
                    return
                n = aplicar_reformatacao(s, regras)
                s.commit()
                mostrar_toast(self, f"{n} nome(s) reformatados no acervo.")
        finally:
            db.engine.dispose()
