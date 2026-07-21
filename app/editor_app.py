"""
Editor em janela REAL (F5.5 completa + sistema de design)
=========================================================
Abre o editor dentro do shell do app com a **grade inteira** do Belo Brasil
(15 células, fixture real): a célula-mestre aparece em **âmbar** — editá-la
propaga para todas; editar uma célula específica vira **override** local.

Rodar::

    python -m app.editor_app
    (ou: python -m app.main --editor)
"""

from __future__ import annotations

import re
import sys
from decimal import Decimal
from pathlib import Path

ARTE = "Frente Template.png"
FIXTURE = Path("app/tests/fixtures/ofertas_belo_brasil.txt")


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:60] or "item"


def _preco(txt: str | None):
    if not txt:
        return None
    return Decimal(txt.replace("R$", "").replace(" ", "").replace(",", "."))


_GRADE_CACHE: dict | None = None


def _grade_real():
    """A grade do Belo Brasil detectada UMA vez por boot (RG-01).

    A detecção (numpy sobre a arte 1080×1300) rodava 3× por abertura;
    agora roda uma e cada consumidor recebe a PRÓPRIA cópia via
    to_dict/from_dict — objetos independentes (editar um nunca vaza no
    outro; o mapa da Mesa continua por uid dentro do documento dela).
    """
    global _GRADE_CACHE
    import json

    from app.rendering.grade import layout_grade_de_arte
    from app.rendering.model import LayoutDef

    if _GRADE_CACHE is None:
        layout, _caixas = layout_grade_de_arte(ARTE)
        # JSON como fronteira: cópia PROFUNDA garantida (from_dict copia
        # `estilos` raso — mutação in place futura contaminaria o cache)
        _GRADE_CACHE = json.dumps(layout.to_dict(), ensure_ascii=False)
    return LayoutDef.from_dict(json.loads(_GRADE_CACHE))


def montar_editor():
    """Editor com a grade real: 15 células, nomes da fixture, fotos do cache."""
    from app.core.paths import SystemRoot
    from app.core.sanitize import formatar_nome
    from app.qt.editor import Editor
    from app.rendering.compositor import DadosProduto
    from app.scripts.importar_tabela import parse_tabela

    layout = _grade_real()
    n = len(layout.paginas[0].slots)
    cache = SystemRoot().biblioteca_imagens / "_auto"

    produtos = []
    for desc, preco in parse_tabela(FIXTURE)[:n]:
        nome = formatar_nome(desc)          # determinístico (offline)
        img = cache / f"{_slug(nome)}.png"  # foto tratada, se o cache tiver
        produtos.append(DadosProduto(
            nome, preco_por=_preco(preco),
            imagem_path=str(img) if img.exists() else None,
        ))

    editor = Editor()
    editor.carregar(layout, produtos, fundo_path=ARTE)
    return editor, layout


def _semear_layouts_padrao() -> None:
    """Garante os dois layouts de partida no banco — SÓ cria os ausentes.

    RG-08: o upsert de boot re-gravava os padrões a cada abertura e
    SOBRESCREVIA edição do dono neles (o "salvei e não persistiu" da
    auditoria tinha esta raiz possível). Layout existente nunca é tocado.
    """
    from app.core.database import Database
    from app.rendering.cartaz import layout_cartaz_exemplo
    from app.rendering.persistencia import listar_layouts, salvar_layout

    db = Database().init()
    with db.Session() as s:
        existentes = {r.nome for r in listar_layouts(s)}
        if "Tabloide Belo Brasil" not in existentes:
            try:
                salvar_layout(s, "Tabloide Belo Brasil", _grade_real(),
                              tipo_midia="TABLOIDE")
            except Exception:
                pass                   # sem a arte → segue sem o tabloide padrão
        if "Cartaz 10×15 — exemplo" not in existentes:
            salvar_layout(s, "Cartaz 10×15 — exemplo", layout_cartaz_exemplo(),
                          tipo_midia="CARTAZ")
        s.commit()


def _layout_padrao_do_banco():
    """O 'Tabloide Belo Brasil' COMO ESTÁ NO BANCO (edições do dono valem;
    uids estáveis entre boots). Fallback: a grade detectada da arte."""
    from app.core.database import Database
    from app.rendering.persistencia import carregar_layout, listar_layouts

    try:
        db = Database().init()
        try:
            with db.Session() as s:
                row = next((r for r in listar_layouts(s)
                            if r.nome == "Tabloide Belo Brasil"), None)
                ldef = carregar_layout(s, row.id) if row else None
        finally:
            db.engine.dispose()
        if ldef is not None:
            return ldef, (ldef.arquivo_fundo or ARTE)
    except Exception:
        pass
    return _grade_real(), ARTE


def _montar_shell(holder: dict):
    """RG-01: o MÍNIMO para a janela nascer — Shell + Dashboard (tela de
    chegada). O resto monta depois do show(), em ``_completar_janela``."""
    from app.qt.design.shell import Shell
    from app.qt.telas.dashboard import DashboardTela

    shell = Shell()

    def _abrir_projeto_dash(projeto_id: int) -> None:
        """Dashboard → reabre o congelado na tela certa."""
        from app.core import projetos
        if "mesa" not in holder:       # clique mais rápido que a montagem
            from app.qt.design.toast import mostrar_toast
            mostrar_toast(shell, "Um instante — as telas ainda estão sendo "
                                 "preparadas…")
            return
        p = projetos.abrir_projeto(projeto_id)
        if p is None:
            return
        if p.tipo == "CARTAZ":
            holder["fabrica"].abrir_projeto_congelado(p)
            shell.ir_para("fabrica")
        else:
            holder["mesa"].abrir_projeto_congelado(p)
            shell.ir_para("mesa")

    inicio = DashboardTela(ao_abrir_projeto=_abrir_projeto_dash,
                           ao_novo=shell.ir_para)
    holder["inicio"] = inicio            # FASE 2: a busca liga na fase 2
    shell.adicionar_tela("inicio", inicio)
    # Auditoria do dono (20/07): os grupos de ofertas moram na ABA PRÓPRIA
    # "Eventos" (entre Início e Ateliê) — o Início ficou só o dashboard
    from app.qt.telas.dashboard import EventosTela
    shell.adicionar_tela("eventos", EventosTela(inicio))
    # R-150 (FASE 12): o MODO PAI — a visão à prova de erro; lembrado por
    # perfil (o PC da loja pode NASCER nele)
    from app.qt.telas.modo_pai import ModoPaiTela, modo_pai_lembrado
    modo_pai = ModoPaiTela(ao_sair=lambda: shell.ir_para("inicio"))
    holder["modo_pai"] = modo_pai
    shell.adicionar_tela("modo_pai", modo_pai)
    shell.ir_para("modo_pai" if modo_pai_lembrado() else "inicio")
    shell.set_dica("Preparando as demais telas…")
    return shell


def _completar_janela(shell, holder: dict):
    """As telas pesadas — com a janela JÁ visível (RG-01)."""
    from app.qt.telas.atelie import AtelieTela
    from app.qt.telas.fabrica import FabricaTela
    from app.qt.telas.mesa import MesaTela

    _semear_layouts_padrao()
    layout, fundo = _layout_padrao_do_banco()

    mesa = MesaTela()
    # padrão até escolher no Ateliê — DO BANCO (RG-08: fonte única; a grade
    # re-detectada tinha uids novos por boot e dessincronizava da biblioteca)
    mesa.carregar_layout(layout, fundo, nome_layout="Tabloide Belo Brasil")
    fabrica = FabricaTela()
    holder["mesa"] = mesa
    holder["fabrica"] = fabrica

    def _abrir_layout(ldef, tipo: str, nome: str) -> None:
        """Duplo-clique no Ateliê → a tela certa recebe o layout escolhido."""
        if tipo == "TABLOIDE":
            mesa.carregar_layout(ldef, ldef.arquivo_fundo, nome_layout=nome)
            shell.ir_para("mesa")
        else:
            fabrica.carregar_layout(ldef, nome_layout=nome)
            shell.ir_para("fabrica")
        shell.set_dica(f"Layout aberto: {nome} ({tipo.title()})")

    # o indicador salvo/não salvo do rodapé é POR TELA (RG-08): cada uma
    # informa o próprio estado e o rodapé mostra o da tela ativa
    mesa.ao_salvo = lambda s: shell.set_salvo_de("mesa", s)
    fabrica.ao_salvo = lambda s: shell.set_salvo_de("fabrica", s)
    # FASE 1 (passo 77): o título da janela mostra o projeto da tela ativa
    mesa.ao_documento = lambda n: shell.set_documento_de("mesa", n)
    fabrica.ao_documento = lambda n: shell.set_documento_de("fabrica", n)

    from app.qt.telas.almoxarifado import AlmoxarifadoTela
    from app.qt.telas.cofre import CofreTela
    from app.qt.telas.configuracoes import ConfiguracoesTela
    atelie = AtelieTela(ao_abrir=_abrir_layout)
    almox = AlmoxarifadoTela()
    holder["almoxarifado"] = almox
    holder["atelie"] = atelie
    shell.adicionar_tela("mesa", mesa)
    shell.adicionar_tela("fabrica", fabrica)
    shell.adicionar_tela("atelie", atelie)
    shell.adicionar_tela("almoxarifado", almox)
    shell.adicionar_tela("cofre", CofreTela())
    # FASE 3 (passo 93): as Configurações em 9 abas só constroem na 1ª
    # visita (~180 ms fora do boot; medido na máquina real)
    shell.adicionar_tela_preguicosa("configuracoes",
                                    lambda: ConfiguracoesTela())
    shell.set_dica("Início: seus projetos por evento  ·  Mesa/Fábrica: montar  "
                   "·  Ateliê: seus layouts")
    shell.set_dimensoes(f"{layout.largura_mm:.0f} × {layout.altura_mm:.0f} mm")

    # RG-05: o zoom do rodapé segue a TELA ATIVA (o editor "solto" que
    # alimentava o número morreu — ele nem aparecia na janela e mentia 2%)
    shell.registrar_zoom("mesa", mesa.area.canvas)

    def _editor_nasceu(ed) -> None:
        shell.registrar_zoom("atelie", ed.area.canvas)
        ed.sujo_mudou.connect(
            lambda sujo: shell.set_salvo_de("atelie", not sujo))

    atelie.ao_criar_editor = _editor_nasceu

    # FASE 2 (passos 73-74): a busca global navega — do Início e do Ctrl+K
    def _abrir_resultado(tipo: str, dado: dict) -> None:
        if tipo == "projetos":
            _abrir_projeto_dash_por_id(dado["id"])
        elif tipo == "produtos":
            almox.busca.setText(dado["nome"])   # filtra o catálogo nele
            shell.ir_para("almoxarifado")
        elif tipo == "layouts":
            shell.ir_para("atelie")
            atelie.selecionar_layout(dado["nome"])

    def _abrir_projeto_dash_por_id(pid: int) -> None:
        from app.core import projetos as proj_srv
        p = proj_srv.abrir_projeto(pid)
        if p is None:
            return
        if p.tipo == "CARTAZ":
            fabrica.abrir_projeto_congelado(p)
            shell.ir_para("fabrica")
        else:
            mesa.abrir_projeto_congelado(p)
            shell.ir_para("mesa")

    inicio = holder.get("inicio")
    if inicio is not None:
        inicio.ao_resultado_busca = _abrir_resultado

        def _resolver_indicador(chave: str) -> None:
            """FASE 2 (passo 91): cada indicador leva pra onde resolve."""
            if chave == "sem_foto":
                almox.filtro.setCurrentIndex(1)      # ● Sem imagem
                shell.ir_para("almoxarifado")
            elif chave == "sem_categoria":
                almox.filtro.setCurrentIndex(2)      # ● Incompletos
                shell.ir_para("almoxarifado")
            elif chave == "backup":
                shell.ir_para("cofre")
            elif chave == "ia":
                shell.ir_para("configuracoes")
            # cartões da Visão geral (polimento): cada um leva pro seu lugar
            elif chave in ("produtos", "com_foto"):
                shell.ir_para("almoxarifado")
            elif chave in ("edicoes", "evento"):
                shell.ir_para("eventos")

        inicio.ao_indicador = _resolver_indicador
    from app.qt.design.paleta_comandos import PaletaBusca
    shell._paleta_busca = PaletaBusca(shell, _abrir_resultado)
    from PySide6.QtCore import Qt as _Qt
    from app.qt.design.atalhos import criar_atalho
    criar_atalho("geral.busca", shell, shell._paleta_busca.abrir,
                 contexto=_Qt.ShortcutContext.WindowShortcut)
    return mesa


def montar_janela():
    """Shell completo de uma vez (compat p/ scripts; o app usa as duas fases)."""
    holder: dict = {}
    shell = _montar_shell(holder)
    _completar_janela(shell, holder)
    editor, _layout = montar_editor()   # p/ screenshots do editor (design)
    return shell, editor


def _migrar_artes() -> list[str]:
    """E-A3: arte de layout com caminho de máquina migra p/ a pasta da raiz."""
    from app.core.database import Database
    from app.rendering.persistencia import migrar_artes_absolutas

    db = Database().init()
    try:
        with db.Session() as s:
            avisos = migrar_artes_absolutas(s)
            s.commit()
    finally:
        db.engine.dispose()
    for a in avisos:
        print(f"migração de arte: {a}")
    return avisos


def main() -> int:
    from PySide6.QtWidgets import QApplication

    from app.qt.design.tema import aplicar_tema
    from app.qt.instancia_unica import instancia_ja_existe, travar_instancia

    # A5: nunca duas instâncias em silêncio — a segunda ativa a primeira e sai
    if instancia_ja_existe():
        print("AutoTabloide já está aberto — trouxe a janela para frente.")
        return 0

    # Polimento: identidade PRÓPRIA na barra de tarefas do Windows — sem o
    # AppUserModelID o processo agrupa como "python" e o ícone da barra sai
    # o do interpretador, não a logo (tem que rodar ANTES da janela nascer).
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "BeloBrasil.AutoTabloideAI")
        except Exception:
            pass

    app = QApplication.instance() or QApplication(sys.argv)
    aplicar_tema(app)
    # FASE 1 (passo 80): splash IMEDIATO (pixmap pintado, ~ms) — a marca
    # aparece antes de qualquer montagem; some em fade quando o shell abre
    from app.qt.design.splash import (
        fechar_splash, icone_aplicativo, mostrar_splash)
    app.setWindowIcon(icone_aplicativo())   # FASE 1 (passo 83)
    splash = mostrar_splash()
    app.processEvents()
    from app.qt.design.animacoes import instalar_vida
    from app.qt.design.polimento import instalar_polimento
    instalar_vida(app)          # FASE 1 (40-41): diálogos e hover com vida
    instalar_polimento(app)     # FASE 1 (52): combos sem texto cortado

    # RG-01: a JANELA nasce primeiro; snapshot, migração e as telas pesadas
    # montam logo depois do show() (a percepção de abertura é a janela)
    holder: dict = {}
    shell = _montar_shell(holder)

    def _ativar() -> None:
        shell.showNormal()
        shell.raise_()
        shell.activateWindow()

    trava = travar_instancia(_ativar)   # segurar a referência a vida toda
    shell._trava_instancia = trava

    shell.resize(1440, 900)
    # FASE 1 (passo 60, R-023): geometria lembrada; a última tela navega
    # quando as telas pesadas existirem (boot em 2 fases — RG-01)
    tela_lembrada = shell.restaurar_estado()
    shell.show()
    fechar_splash(splash, shell)    # passo 80: sai em fade sobre o shell

    # RG-05: vigia de travamento — se a UI congelar, o traceback de todas
    # as threads vai para <raiz>/logs/travamentos.log (1 dump por episódio)
    from PySide6.QtCore import QTimer as _QTimer

    from app.core.paths import SystemRoot
    from app.core.vigia import VigiaTravamento
    vigia = VigiaTravamento(SystemRoot().logs / "travamentos.log").iniciar()
    batimento = _QTimer(shell)
    batimento.timeout.connect(vigia.batimento)
    batimento.start(1000)
    shell._vigia = vigia

    def _completar() -> None:
        # D-B2: snapshot automático a cada abertura (antes de qualquer edição)
        from app.core.cofre import snapshot_automatico
        snapshot_automatico()
        avisos_migracao = _migrar_artes()   # E-A3: caminho antigo → layouts/
        # FASE 2 (passo 3): eventos-texto viram entidades na abertura
        from app.qt.telas.eventos import listar_eventos
        listar_eventos()                    # migra + commita (idempotente)
        # FASE 2 (passo 85): a purga da lixeira (>30 dias) roda no boot
        from app.core.lixeira import purgar
        purgados = purgar()
        if purgados:                        # I2: nunca em silêncio
            from app.qt.design.toast import mostrar_toast as _toast
            _toast(shell, f"Lixeira: {len(purgados)} item(ns) com mais de "
                          "30 dias foram apagados de vez (log no console).")
        shell._editor = _completar_janela(shell, holder)
        if tela_lembrada != "inicio":   # passo 60: reabre onde parou
            shell.ir_para(tela_lembrada)
        # FASE 1 (passo 81): saudação da PRIMEIRA execução (3 caminhos)
        from app.qt.design.boas_vindas import mostrar_se_primeira_execucao
        mostrar_se_primeira_execucao(shell)
        if avisos_migracao:             # I2: migração nunca é silenciosa
            from app.qt.design.toast import mostrar_toast
            mostrar_toast(shell, f"{len(avisos_migracao)} layout(s) com arte "
                                 "migrada/pendente — detalhes no console.")
        # RG-02: pré-aquece o modelo de recorte em segundo plano — a 1ª foto
        # da sessão deixa de pagar os ~7 s de carga (medido)
        from app.images.fundo import aquecer, modelo_configurado
        from app.qt.workers import GerenciadorTrabalhos, Trabalhador
        shell._trabalhos_globais = GerenciadorTrabalhos()
        aquecedor = Trabalhador(
            lambda _st, m=modelo_configurado(): aquecer(m))
        shell._trabalhos_globais.rodar(aquecedor)
        # OS F11.5 #80: o Real-ESRGAN também aquece (o 1º cartaz da sessão
        # deixava de responder enquanto o .pth carregava)
        def _aquecer_esrgan(_st):
            try:
                from app.qt.telas.servico import aquecer_upscaler
                return aquecer_upscaler()
            except Exception:
                return False
        shell._trabalhos_globais.rodar(Trabalhador(_aquecer_esrgan))
        # R-138 (FASE 12): a validação de integridade da abertura — PRAGMA +
        # referências de foto, em worker; problema vira AVISO discreto (I2),
        # nunca trava o boot
        def _verificar_integridade(_st):
            try:
                from app.core.recuperacao import verificar_ao_abrir
                return verificar_ao_abrir()
            except Exception:
                return {"avisos": []}

        def _avisar_integridade(r):
            avisos = (r or {}).get("avisos") or []
            if avisos:
                from app.qt.design.toast import mostrar_toast
                mostrar_toast(shell, avisos[0] + " (Configurações › "
                              "verificação da instalação)", tipo="erro")
        vig = Trabalhador(_verificar_integridade)
        vig.ok.connect(_avisar_integridade)
        shell._trabalhos_globais.rodar(vig)

    from PySide6.QtCore import QTimer
    QTimer.singleShot(0, _completar)    # roda com a janela já pintada
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
