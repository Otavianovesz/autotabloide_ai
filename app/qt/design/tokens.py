"""
Tokens do sistema de design
===========================
A fonte única da identidade visual: cores, tipografia, espaçamento, raios,
elevação e movimento. Tudo que a interface usa sai daqui — mudar um token
muda o app inteiro.

Modo claro EXPLÍCITO (decisão travada: nunca herdar o dark mode do SO).
"""

from __future__ import annotations

# =============================================================================
# COR
# =============================================================================

# --- Primária (azul) — escala completa ---------------------------------------
PRIMARIA_50 = "#EFF6FF"
PRIMARIA_100 = "#DBEAFE"
PRIMARIA_200 = "#BFDBFE"
PRIMARIA_300 = "#93C5FD"
PRIMARIA_400 = "#60A5FA"
PRIMARIA_500 = "#3B82F6"
PRIMARIA_600 = "#2563EB"
PRIMARIA_700 = "#1D4ED8"
PRIMARIA_800 = "#1E40AF"
PRIMARIA_900 = "#1E3A8A"

# Papéis da primária (use estes, não os números, no código de UI)
PRIMARIA = PRIMARIA_600          # ação principal, seleção, links
PRIMARIA_ESCURA = PRIMARIA_700   # hover/pressed da primária
PRIMARIA_SUAVE = PRIMARIA_100    # fundo de item selecionado
PRIMARIA_FUNDO = PRIMARIA_50     # fundo de hover suave

ACENTO = "#F59E0B"               # âmbar — destaque de oferta/atenção (pontual)

# --- Semânticas ---------------------------------------------------------------
SUCESSO = "#16A34A"
SUCESSO_FUNDO = "#EAF7EF"
ALERTA = "#D97706"
ALERTA_FUNDO = "#FDF3E3"
PERIGO = "#DC2626"
PERIGO_FUNDO = "#FCEDED"
INFO = PRIMARIA_600
INFO_FUNDO = PRIMARIA_50

# tons CLAROS das semânticas (vivem no chrome escuro: toasts, tooltips)
SUCESSO_CLARO = "#4ADE80"
PERIGO_CLARO = "#F87171"
INFO_CLARO = "#93C5FD"

# --- Neutros (modo claro explícito) -------------------------------------------
TEXTO = "#16202E"                # texto principal
TEXTO_2 = "#4B5565"              # texto secundário (rótulos, cabeçalhos)
TEXTO_3 = "#8A94A3"              # texto apagado (legendas, placeholders)
TEXTO_INVERSO = "#FFFFFF"        # texto sobre primária/tooltip

FUNDO_APP = "#F3F5F8"            # fundo geral da janela / sidebar
SUPERFICIE = "#FFFFFF"           # cartões, campos, listas, toolbar
SUPERFICIE_2 = "#F8FAFC"         # cabeçalho de cartão, linhas alternadas
SUPERFICIE_3 = "#EEF1F5"         # pressed de item neutro
BORDA = "#DDE3EB"                # borda padrão
BORDA_FORTE = "#C6CEDA"          # borda de campo / separadores
ESCURO = "#252B36"               # tooltip, toast, command palette (chrome escuro)

# --- Canvas (mesa de trabalho ≠ chrome da UI) ----------------------------------
CANVAS_FUNDO = "#E2E6EC"         # área ao redor da página
CANVAS_VINHETA = "#D3D9E1"       # tom da vinheta nas bordas da mesa
PAGINA_SOMBRA = "#16202E"        # cor-base da sombra sob a página (com alpha)
PAGINA_HALO = "#FFFFFF"          # halo da página no escuro (sombra clara)

# --- Aliases semânticos canônicos (FASE 1, passo 9) ----------------------------
# O vocabulário oficial do design system 2.0. Os nomes antigos continuam
# válidos (são os MESMOS objetos) — os temas trocam TODOS juntos.
FUNDO = FUNDO_APP                # fundo geral da janela
TEXTO_1 = TEXTO                  # texto principal
ACENTO_TEXTO = TEXTO_INVERSO     # texto sobre acento/primária
SOMBRA = PAGINA_SOMBRA           # cor-base de sombras (com alpha no uso)
VEU_OCUPADO = "rgba(255, 255, 255, 150)"   # véu do overlay (tematizado)
VEU_DIALOGO = "rgba(22, 32, 46, 70)"       # fundo escurecido sob diálogos
# véus de hover (passo 41): translúcidos que REPRODUZEM as cores de hover
# antigas por cima do fundo — o fade de 120ms vive num overlay, não no QSS
HOVER_VEU = "rgba(59, 130, 246, 21)"       # botões neutros/fantasma/nav
HOVER_VEU_FORTE = "rgba(0, 0, 0, 55)"      # botão primário (escurece)

# =============================================================================
# TEMAS (FASE 1, passos 11–12) — claro (padrão travado) e escuro
# =============================================================================
# Só o que TEMATIZA entra aqui; o resto do módulo é invariante. `ativar_tema`
# atualiza os atributos DESTE módulo — todo consumidor que lê `t.X` na hora
# do uso (QSS regenerado, painters, ícones) obedece na próxima pintura.

_CLARO = {
    "VEU_OCUPADO": "rgba(255, 255, 255, 150)",   # véu do overlay (passo 28)
    "VEU_DIALOGO": "rgba(22, 32, 46, 70)",       # sob diálogos (passo 40)
    "HOVER_VEU": "rgba(59, 130, 246, 21)",
    "HOVER_VEU_FORTE": "rgba(0, 0, 0, 55)",
    "FUNDO_APP": "#F3F5F8", "SUPERFICIE": "#FFFFFF",
    "SUPERFICIE_2": "#F8FAFC", "SUPERFICIE_3": "#EEF1F5",
    "TEXTO": "#16202E", "TEXTO_2": "#4B5565", "TEXTO_3": "#8A94A3",
    "TEXTO_INVERSO": "#FFFFFF",
    "BORDA": "#DDE3EB", "BORDA_FORTE": "#C6CEDA", "ESCURO": "#252B36",
    "CANVAS_FUNDO": "#E2E6EC", "CANVAS_VINHETA": "#D3D9E1",
    "PAGINA_SOMBRA": "#16202E",
    "ICONE": "#3D4654", "ICONE_APAGADO": "#A2ABB8",
    "PRIMARIA": PRIMARIA_600, "PRIMARIA_ESCURA": PRIMARIA_700,
    "PRIMARIA_SUAVE": PRIMARIA_100, "PRIMARIA_FUNDO": PRIMARIA_50,
    "SELECAO": PRIMARIA_600, "SELECAO_HOVER": PRIMARIA_400,
    "ALCA_BORDA": PRIMARIA_600,
    "SUCESSO_FUNDO": "#EAF7EF", "ALERTA_FUNDO": "#FDF3E3",
    "PERIGO_FUNDO": "#FCEDED", "INFO_FUNDO": PRIMARIA_50,
}

_ESCURO = {
    # a spec do caderno (passo 12), com as derivadas de bom senso
    "VEU_OCUPADO": "rgba(8, 10, 14, 170)",       # véu escuro (passo 28)
    "VEU_DIALOGO": "rgba(0, 0, 0, 120)",         # sob diálogos (passo 40)
    "HOVER_VEU": "rgba(60, 110, 240, 28)",
    "HOVER_VEU_FORTE": "rgba(255, 255, 255, 47)",  # primário CLAREIA no escuro
    "FUNDO_APP": "#101216", "SUPERFICIE": "#181B21",
    "SUPERFICIE_2": "#20242C", "SUPERFICIE_3": "#262B34",
    "TEXTO": "#E8EAED", "TEXTO_2": "#A8ADB5", "TEXTO_3": "#6C7280",
    "TEXTO_INVERSO": "#FFFFFF",
    "BORDA": "#2A2F38", "BORDA_FORTE": "#3A4150", "ESCURO": "#313844",
    "CANVAS_FUNDO": "#14171C", "CANVAS_VINHETA": "#0E1014",
    "PAGINA_SOMBRA": "#FFFFFF",          # halo claro sob a página (passo 20)
    "ICONE": "#C9CEDA", "ICONE_APAGADO": "#5A6270",
    "PRIMARIA": "#5B8DEF", "PRIMARIA_ESCURA": "#79A2F2",
    "PRIMARIA_SUAVE": "#1E2A44", "PRIMARIA_FUNDO": "#182238",
    "SELECAO": "#5B8DEF", "SELECAO_HOVER": "#79A2F2",
    "ALCA_BORDA": "#5B8DEF",
    "SUCESSO_FUNDO": "#13291D", "ALERTA_FUNDO": "#33260F",
    "PERIGO_FUNDO": "#331414", "INFO_FUNDO": "#14213A",
}

TEMAS = {"claro": _CLARO, "escuro": _ESCURO}
TEMA_ATUAL = "claro"

# aliases que derivam de tokens tematizados (recalculados na troca)
_ALIASES = {"FUNDO": "FUNDO_APP", "TEXTO_1": "TEXTO",
            "ACENTO_TEXTO": "TEXTO_INVERSO", "SOMBRA": "PAGINA_SOMBRA"}


def ativar_tema(nome: str) -> None:
    """Troca os tokens tematizados DESTE módulo (claro é o padrão travado).

    Nome desconhecido cai no claro (C3: default são, nunca estoura)."""
    global TEMA_ATUAL
    tema = TEMAS.get(nome) or _CLARO
    TEMA_ATUAL = nome if nome in TEMAS else "claro"
    g = globals()
    g.update(tema)
    for alias, origem in _ALIASES.items():
        g[alias] = tema[origem]

# --- Editor: seleção / guias ----------------------------------------------------
SELECAO = PRIMARIA_600           # contorno do item selecionado
SELECAO_HOVER = PRIMARIA_400     # realce ao passar o mouse (antes do clique)
ALCA_PREENCHIMENTO = "#FFFFFF"   # alça: miolo branco…
ALCA_BORDA = PRIMARIA_600        # …com borda primária (estilo Figma)
GUIA_SNAP = "#8B5CF6"            # guia magnética (violeta elegante, não vermelho)

ICONE = "#3D4654"                # traço padrão dos ícones
ICONE_APAGADO = "#A2ABB8"        # ícone desabilitado

# =============================================================================
# TIPOGRAFIA
# =============================================================================
FONTE_UI = ("Segoe UI Variable Text", "Segoe UI")
TAM_TITULO = 14      # pt — título de janela/tela (semibold)
TAM_SECAO = 8        # pt — cabeçalho de painel (bold, maiúsculas espaçadas)
TAM_CORPO = 9.5      # pt — texto padrão
TAM_ROTULO = 9       # pt — rótulos de campo
TAM_LEGENDA = 8      # pt — legendas/apoio

PESO_NORMAL = 400
PESO_MEDIO = 500
PESO_SEMI = 600
PESO_BOLD = 700

# =============================================================================
# ESPAÇAMENTO (escala de 4px) e RAIOS
# =============================================================================
ESP_1 = 4
ESP_2 = 8
ESP_3 = 12
ESP_4 = 16
ESP_5 = 24

# FASE 1 (passo 49): mínimos dos controles — a régua anti-corte do Bloco E
ALTURA_CONTROLE = 32     # px — botões/campos/combos nunca menores que isto
LARGURA_MIN_CAMPO = 96   # px — nenhum campo espremido a ponto de sumir
ESPACO_1 = 4             # respiros oficiais (múltiplos de 4)
ESPACO_2 = 8
ESPACO_3 = 16

# FASE 1 (passo 64 — R-015): escala da interface (100/125/150%).
# `ativar_escala` muta a TIPOGRAFIA DA UI e a régua de controles; o QSS
# regenerado espalha o resto. A tipografia do DOCUMENTO (página) não passa
# por aqui — escala de UI nunca muda a arte. (`_BASE_ESCALA` é montada no
# FIM do módulo, lendo os valores canônicos — nada duplicado.)
ESCALA_ATUAL = 100


def ativar_escala(pct: int) -> None:
    """Escala desconhecida cai em 100 (default são, nunca estoura)."""
    global ESCALA_ATUAL
    pct = pct if pct in (100, 125, 150) else 100
    ESCALA_ATUAL = pct
    g = globals()
    for nome, base in _BASE_ESCALA.items():
        valor = base * pct / 100
        g[nome] = int(round(valor)) if isinstance(base, int) else valor

RAIO_CONTROLE = 6    # botões, campos, combos
RAIO_CARTAO = 8      # painéis/cartões
RAIO_PILULA = 999    # chips/badges

# =============================================================================
# ELEVAÇÃO (specs para sombras desenhadas/effects; QSS não tem box-shadow)
# blur_px, deslocamento_y_px, alpha (0-255)
# =============================================================================
SOMBRA_1 = (8, 2, 26)     # cartões levemente elevados
SOMBRA_2 = (16, 4, 34)    # popovers, menus, toasts
SOMBRA_3 = (32, 8, 48)    # diálogos, command palette

# =============================================================================
# MOVIMENTO (ms) — rápido e discreto
# =============================================================================
DUR_HOVER = 120      # hover/realces
DUR_PAINEL = 200     # painéis, toasts, popovers

# base da escala de UI (passo 64) — lida DOS valores canônicos acima
_BASE_ESCALA = {n: globals()[n] for n in
                ("TAM_TITULO", "TAM_SECAO", "TAM_CORPO", "TAM_ROTULO",
                 "TAM_LEGENDA", "ALTURA_CONTROLE")}
