"""Galeria NATIVA da FASE 12 (passos 13, 31, 43, 82 e 91 — prova visual).

Fotografa as novidades do marco, em tema claro e escuro: a recuperação de
projeto (snapshots com prévia), o Levar/Trazer .atproj, o modo
somente-leitura + migração do programa antigo (Configurações → Backups),
o Verificar atualização (Sobre), o Calendário do ano, o Modo Pai (R-150)
e a folha de etiquetas em lote imposta em A4.

SEM offscreen de propósito (o offscreen renderiza glifos como caixas);
janelas com WA_DontShowOnScreen — nada pisca. Rodar::

    python -m app.scripts.fotografar_fase12 saida_fase12/claro
    python -m app.scripts.fotografar_fase12 saida_fase12/escuro --tema=escuro
"""

from __future__ import annotations

import os
import sys
import tempfile
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


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pasta = Path(args[0] if args else "saida_fase12/claro")
    tema = next((a.split("=", 1)[1] for a in sys.argv[1:]
                 if a.startswith("--tema=")), None)

    # raiz TEMPORÁRIA semeada (nunca o acervo vivo)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
    import seeds_portabilidade as seeds
    tmp = Path(tempfile.mkdtemp(prefix="fase12_"))
    root = seeds.raiz(tmp, "raiz")
    os.environ["AUTOTABLOIDE_ROOT"] = str(root.raiz)
    import shutil
    reais = Path("AutoTabloide_System_Root/fontes")
    if reais.exists():
        for f in reais.glob("*.ttf"):
            shutil.copy(f, root.fontes / f.name)
    seeds.add_produto(root, "Arroz Tio João 5kg", "Tio João", "24.90",
                      foto=seeds.png("#C0392B"), categoria="Mercearia")
    seeds.add_produto(root, "Café Pilão 500g", "Pilão", "9.90",
                      foto=seeds.png("#2C3E50"), categoria="Mercearia")

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from app.qt.design.tema import aplicar_tema
    app = QApplication.instance() or QApplication([])
    aplicar_tema(app, tema) if tema else aplicar_tema(app)
    from app.qt.design.polimento import instalar_polimento
    instalar_polimento(app)
    DONT = Qt.WidgetAttribute.WA_DontShowOnScreen

    # dois projetos reais no banco (um vira a prévia do Modo Pai)
    from app.core import projetos
    from app.qt.telas.servico import ItemMesa
    from app.rendering.model import (
        Ajuste, LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao)
    foto = tmp / "p.png"
    foto.write_bytes(seeds.png("#BB2200"))
    it = ItemMesa("x", "9,90", "VERDE", "Arroz Tio João 5kg",
                  imagem=str(foto))
    lay = LayoutDef(180, 120, dpi=96, paginas=[Pagina([Slot("s", [
        Regiao(TipoRegiao.IMAGEM, Retangulo(20, 12, 60, 58),
               ajuste=Ajuste.PREENCHER),
        Regiao(TipoRegiao.NOME, Retangulo(20, 74, 60, 10)),
        Regiao(TipoRegiao.PRECO, Retangulo(20, 86, 60, 16)),
    ])])])
    pid1 = projetos.salvar_projeto(
        "Quintou da semana", "Quintou", "TABLOIDE", lay, [it.to_dict()],
        validade_oferta="OFERTA VÁLIDA SOMENTE 23/07", mapa={"s": it.uid})
    projetos.salvar_projeto(
        "Fim de semana", None, "TABLOIDE", lay, [it.to_dict()],
        validade_oferta="OFERTA VÁLIDA 25 A 27/07", mapa={"s": it.uid})

    # --- 1) recuperação de projeto (Bloco A, R-137) --------------------------
    from app.qt.telas.recuperacao_dialog import RecuperacaoDialog
    dlg = RecuperacaoDialog(
        ["O arquivo de estado está danificado (JSON inválido na linha 1).",
         "A última gravação foi interrompida (queda de energia?)."],
        [{"origem": "versao", "quando": "21/07/2026 09:12", "itens": 24,
          "estado": {}},
         {"origem": "versao", "quando": "20/07/2026 18:40", "itens": 22,
          "estado": {}},
         {"origem": "rascunho", "quando": "21/07/2026 09:15", "itens": 24,
          "estado": {}}])
    dlg.setAttribute(DONT, True)
    dlg.show()
    dlg.lista.setCurrentRow(0)
    _grab(dlg, pasta, "recuperacao_snapshots.png")
    dlg.close()

    # --- 2) Levar/Trazer .atproj (Abrir projeto) -----------------------------
    from app.qt.telas.projetos_dialog import AbrirProjetoDialog
    dlg = AbrirProjetoDialog()
    dlg.setAttribute(DONT, True)
    dlg.show()
    if dlg.lista.count():
        dlg.lista.setCurrentRow(0)
    _grab(dlg, pasta, "abrir_projeto_atproj.png")
    dlg.close()

    # --- 3) Configurações: Backups (somente-leitura + migração) e Sobre ------
    from app.qt.telas.configuracoes import ConfiguracoesTela
    cfg = ConfiguracoesTela()
    cfg.setAttribute(DONT, True)
    cfg.show()
    cfg.resize(1280, 780)

    def _ir_para_aba(trecho: str) -> None:
        for i in range(cfg.lista_abas.count()):
            if trecho.lower() in cfg.lista_abas.item(i).text().lower():
                cfg.lista_abas.setCurrentRow(i)
                return

    _ir_para_aba("backup")
    _grab(cfg, pasta, "config_backups_somente_leitura_migrar.png")
    _ir_para_aba("sobre")
    _grab(cfg, pasta, "config_sobre_verificar_atualizacao.png")
    cfg.close()

    # --- 4) Calendário do ano (Bloco B, R-149) -------------------------------
    from app.qt.telas.calendario_dialog import CalendarioDialog
    dlg = CalendarioDialog()
    dlg.setAttribute(DONT, True)
    dlg.show()
    _grab(dlg, pasta, "calendario_do_ano.png")
    dlg.close()

    # --- 5) Modo Pai (Bloco C, R-150) ----------------------------------------
    from app.qt.telas.modo_pai import ModoPaiTela
    tela = ModoPaiTela()
    tela.setAttribute(DONT, True)
    tela.resize(1400, 820)
    tela.show()
    tela.recarregar()
    if tela.lista.count():
        tela.lista.setCurrentRow(0)
    _grab(tela, pasta, "modo_pai.png")
    tela.close()

    # --- 6) etiquetas em lote impostas em A4 (Bloco B, R-144) ----------------
    from PIL import Image

    from app.rendering.imposicao import impor_etiquetas
    base = Image.new("RGB", (472, 236), (255, 255, 255))   # 100×50mm@120dpi
    cores = [(187, 34, 0), (44, 62, 80), (39, 174, 96),
             (142, 68, 173), (230, 126, 34), (41, 128, 185)]
    etiquetas = []
    for cor in cores:
        im = base.copy()
        for x in range(12, 460):
            for y in range(12, 80):
                im.putpixel((x, y), cor)
        etiquetas.append(im)
    folhas = impor_etiquetas(etiquetas, 120)
    folhas[0].save(pasta / "etiquetas_impostas_a4.png")
    print("  etiquetas_impostas_a4.png")

    print(f"galeria em {pasta}")
    from app.qt.workers import encerrar_todos
    encerrar_todos(espera_ms=1000)
    app.closeAllWindows()
    _processar()
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
