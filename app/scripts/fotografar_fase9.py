"""Galeria NATIVA da FASE 9 (Conteúdo & IA II — a IA colega).

Fotografa o que o arquiteto sela no olho: o LAUDO DA REVISORA pegando um preço
trocado (o flagship), o chat da oferta com o resumo, as manchetes sugeridas + a
dica em 3 estilos, e as "correções aprendidas". Tudo com a IA fake (determinística)
— a inspeção é do encanamento e da apresentação; a qualidade real é do modelo.

SEM offscreen (o plugin nativo resolve as fontes da UI). Encerra com os._exit(0).
Rodar::

    python -m app.scripts.fotografar_fase9 saida_fase9/claro
    python -m app.scripts.fotografar_fase9 saida_fase9/escuro --tema=escuro
"""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path


def _processar(n: int = 3) -> None:
    from PySide6.QtWidgets import QApplication
    for _ in range(n):
        QApplication.processEvents()


def _grab(widget, pasta: Path, nome: str) -> None:
    _processar()
    pasta.mkdir(parents=True, exist_ok=True)
    widget.grab().save(str(pasta / nome))
    print(f"  {nome}")


def _painel(titulo: str, linhas: list[str], larg: int = 560):
    """Um cartão simples (título + linhas) no estilo do app, para os artefatos de
    texto (manchetes, dica, correções) virarem imagem legível."""
    from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout
    card = QFrame()
    card.setProperty("elevacao", "1")
    card.setFixedWidth(larg)
    lay = QVBoxLayout(card)
    t = QLabel(titulo)
    t.setProperty("papel", "titulo")
    lay.addWidget(t)
    for ln in linhas:
        rot = QLabel(ln)
        rot.setWordWrap(True)
        if ln.startswith("•") or ln.startswith("⚠"):
            rot.setProperty("papel", "legenda")
        lay.addWidget(rot)
    lay.addStretch(1)
    return card


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pasta = Path(args[0] if args else "saida_fase9/claro")
    tema = next((a.split("=", 1)[1] for a in sys.argv[1:]
                 if a.startswith("--tema=")), None)

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from app.qt.design.tema import aplicar_tema
    app = QApplication.instance() or QApplication([])
    aplicar_tema(app, tema) if tema else aplicar_tema(app)
    from app.qt.design.polimento import instalar_polimento
    instalar_polimento(app)
    DONT = Qt.WidgetAttribute.WA_DontShowOnScreen

    from app.ai.enriquecimento import ESTILOS_DICA
    from app.rendering.compositor import DadosProduto

    # --- 1) LAUDO DA REVISORA (o flagship) — visão pega o preço trocado -------
    from app.ai.fake import MotorIAFake
    from app.ai.revisora import revisar_export
    dados = {
        "s0": DadosProduto("Sabonete Dove 90g", preco_por=Decimal("3.49"),
                           categoria="Higiene"),
        "s1": DadosProduto("Café Pilão 500g", preco_por=Decimal("12.90"),
                           preco_de=Decimal("10.90"), categoria="Mercearia"),
    }
    fake = MotorIAFake(respostas_visao={
        "revisor de encarte": json.dumps({"precos": ["3,49", "79,90"]})})
    avisos, deg = revisar_export("peca.png", dados, motor=fake)
    linhas = [f"• {a}" for a in avisos] or ["• Nada a apontar."]
    if deg:
        linhas.append(f"⚠ {deg}")
    laudo = _painel("Laudo da revisora — avisos (você decide, não trava)", linhas)
    laudo.setAttribute(DONT, True)
    laudo.show()
    _grab(laudo, pasta, "laudo_revisora.png")

    # --- 2) chat da oferta (resumo) ------------------------------------------
    from app.qt.telas import servico
    # resultado fake sem banco: monta ItemMesa direto p/ o resumo
    itens = [servico.ItemMesa("Óleo de Soja Liza 900ml", "7,71", "VERDE",
                              "Óleo de Soja Liza 900ml"),
             servico.ItemMesa("Arroz Tio João 5kg", "24,90", "AMARELO",
                              "Arroz Tio João 5kg"),
             servico.ItemMesa("Doce de Banana 250g", "6,66", "VERMELHO",
                              "Doce de Banana 250g")]
    res = servico.ResultadoMesa(itens=itens)
    chat = _painel("Chat da oferta — “monte o Quintou com estas linhas”", [
        "Você colou 3 linhas. Entendi assim:",
        f"• {servico.resumo_do_resultado(res)}",
        "• É um rascunho para ajustar — nada é publicado direto."])
    chat.setAttribute(DONT, True)
    chat.show()
    _grab(chat, pasta, "chat_oferta.png")

    # --- 3) manchetes + dica em 3 estilos ------------------------------------
    from app.ai.enriquecimento import sugerir_manchetes
    manch = sugerir_manchetes("Quintou do Real", motor=None, limite_chars=40)
    dicas = {
        "receita": "Arroz soltinho: refogue o alho no óleo antes de juntar a água.",
        "economia": "Compre o arroz de 5kg: rende mais e sai mais barato por quilo.",
        "curiosidade": "O café coado é a forma mais popular de tomar café no Brasil.",
    }
    painel_txt = _painel("Manchetes sugeridas + Fica a Dica (3 estilos)",
                         ["Manchetes (você escolhe/edita):",
                          *[f"• {mm}" for mm in manch[:4]], "",
                          "Fica a Dica:"] +
                         [f"• [{k}] {v}" for k, v in dicas.items()])
    painel_txt.setAttribute(DONT, True)
    painel_txt.show()
    _grab(painel_txt, pasta, "manchetes_e_dica.png")

    # --- 4) correções aprendidas (typos/siglas) ------------------------------
    aprend = _painel("Correções aprendidas (o dono confirmou — local, editável)", [
        "Typos do fornecedor:", "• “Huppers” → “Ruppers”",
        "• “Camill” → “Camil”", "",
        "Siglas: • “VD” → “vidro”   • “PT” → “pote”",
        "Sinônimos regionais: • macaxeira = mandioca = aipim"])
    aprend.setAttribute(DONT, True)
    aprend.show()
    _grab(aprend, pasta, "correcoes_aprendidas.png")

    _processar()
    print(f"Galeria da Fase 9 em {pasta.resolve()}")
    sys.stdout.flush()
    import os
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
