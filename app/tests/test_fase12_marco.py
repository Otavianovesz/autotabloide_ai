"""
FASE 12 — Confiabilidade, MARCO FINAL e entrega (testes por conteúdo)
=====================================================================
Bloco A: recuperação de corrompido (R-137), somente-leitura (R-131),
.atproj (R-136), verificar atualização (R-127), integridade na abertura
(R-138). Tudo mutation-proof: cada teste confere por VALOR/byte — reverter
o conserto correspondente derruba o teste.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from app.tests import seeds_portabilidade as seeds


@pytest.fixture()
def raiz_env(tmp_path, monkeypatch):
    root = seeds.raiz(tmp_path, "raiz")
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(root.raiz))
    return root


def _app():
    return QApplication.instance() or QApplication([])


def _layout_simples():
    from app.rendering.model import (
        LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao)
    return LayoutDef(100, 100, dpi=96, paginas=[Pagina([
        Slot("s", [Regiao(TipoRegiao.NOME, Retangulo(5, 5, 40, 10))])])])


def _salvar(nome: str, preco: str = "1,00") -> int:
    from app.core import projetos
    from app.qt.telas.servico import ItemMesa
    it = ItemMesa("X", preco, "VERDE", nome)
    return projetos.salvar_projeto(nome, None, "TABLOIDE", _layout_simples(),
                                   [it.to_dict()])


# ============================================================================
# Bloco A — robustez final
# ============================================================================

def test_a_recuperacao_restaura_do_snapshot_bom(raiz_env):
    """R-137 (passos 1-3, 11, 14): projeto CORROMPIDO de propósito →
    diagnóstico em PT-BR (sem stack trace), snapshot bom listado com prévia,
    restauração POR CONTEÚDO (o item volta) e o lixo guardado num .bak."""
    from app.core import projetos, recuperacao
    from app.core.database import Database
    from app.core.models import ProjetoSalvo
    from app.core.projetos import _pasta
    pid = _salvar("Oferta boa", "9,90")
    # salvar por cima cria a VERSÃO do estado anterior (F2)
    from app.qt.telas.servico import ItemMesa
    it2 = ItemMesa("X", "8,88", "VERDE", "Oferta boa v2")
    projetos.salvar_projeto("Oferta boa", None, "TABLOIDE",
                            _layout_simples(), [it2.to_dict()],
                            projeto_id=pid)
    assert projetos.listar_versoes(pid)          # há snapshot bom

    db = Database().init()                       # corrompe DE PROPÓSITO
    try:
        with db.Session() as s:
            row = s.get(ProjetoSalvo, pid)
            uuid = row.uuid
            row.estado_slots = '{"layout": QUEBRADO'
            s.commit()
    finally:
        db.engine.dispose()

    with pytest.raises(Exception):
        projetos.abrir_projeto(pid)              # o quebrado NÃO abre

    problemas = recuperacao.diagnosticar_projeto(pid)
    assert any("ilegíve" in p for p in problemas)     # PT-BR, não traceback
    assert not any("Traceback" in p for p in problemas)

    sns = recuperacao.snapshots_de_recuperacao(pid)
    assert sns and sns[0]["origem"] == "versão"
    assert sns[0]["itens"] == 1                  # a prévia diz o conteúdo

    assert recuperacao.restaurar_de_snapshot(pid, sns[0])
    p = projetos.abrir_projeto(pid)              # agora ABRE
    assert p is not None
    assert p.itens[0]["nome"] == "Oferta boa"    # o conteúdo do snapshot BOM
    baks = list(_pasta(uuid).glob("corrompido_*.bak.json"))
    assert baks                                  # reversível: o lixo guardado
    assert "QUEBRADO" in baks[0].read_text(encoding="utf-8")
    log = Path(raiz_env.logs) / "recuperacoes.log"
    assert log.exists() and "restaurado" in log.read_text(encoding="utf-8")


def test_a_dialogo_de_recuperacao_constroi_e_escolhe(raiz_env):
    """A galeria da F12 pegou um KeyError de ícone aqui (o diálogo nunca era
    construído em teste — lacuna). Agora é, nos DOIS caminhos: com snapshots
    (escolha devolvida por conteúdo) e sem (EstadoVazio + Restaurar cego
    desabilitado)."""
    from app.qt.telas.recuperacao_dialog import RecuperacaoDialog
    _app()
    sn = [{"origem": "versao", "quando": "21/07/2026 09:12", "itens": 3,
           "estado": {"x": 1}},
          {"origem": "rascunho", "quando": "21/07/2026 09:15", "itens": 4,
           "estado": {"x": 2}}]
    dlg = RecuperacaoDialog(["JSON inválido na linha 1"], sn)
    dlg.lista.setCurrentRow(1)
    dlg._confirmar()
    assert dlg.snapshot_escolhido == sn[1]       # o ESCOLHIDO, não o 1º
    dlg.close()

    vazio = RecuperacaoDialog(["JSON inválido"], [])
    assert not vazio._btn_ok.isEnabled()
    assert not vazio.lista.isVisible() or vazio.lista.count() == 0
    vazio._confirmar()                           # sem item: não aceita nada
    assert vazio.snapshot_escolhido is None
    vazio.close()


def test_a_recuperacao_usa_o_rascunho_do_projeto_certo(raiz_env):
    """R-137: o rascunho automático só entra como candidato se é DESTE
    projeto (por id, I1) — o rascunho de outro projeto nunca vaza."""
    from app.core import rascunho, recuperacao
    pid = _salvar("Meu projeto")
    outro = _salvar("Outro projeto")
    estado = {"projeto_id": outro, "layout": _layout_simples().to_dict(),
              "itens": [], "mapa": {}, "overrides": {}}
    rascunho.salvar_rascunho(estado)
    origens = [s["origem"] for s in
               recuperacao.snapshots_de_recuperacao(pid)]
    assert "rascunho" not in origens             # o rascunho é do OUTRO
    origens2 = [s["origem"] for s in
                recuperacao.snapshots_de_recuperacao(outro)]
    assert "rascunho" in origens2                # no dono certo, entra


def test_a_atproj_roundtrip_identico(raiz_env, tmp_path):
    """R-136 (passos 6-7, 15): exportar → importar recria o projeto com os
    DADOS byte a byte e as fotos por caminho RELATIVO (arquivo copiado
    idêntico)."""
    from app.core import atproj, projetos
    from app.core.database import Database
    from app.core.models import ProjetoSalvo
    from app.core.projetos import _pasta
    from app.qt.telas.servico import ItemMesa
    foto = tmp_path / "foto.png"
    foto.write_bytes(seeds.png("#AA3311"))
    it = ItemMesa("X", "7,77", "VERDE", "Produto com foto",
                  imagem=str(foto))
    pid = projetos.salvar_projeto("Viajante", "Quintou", "TABLOIDE",
                                  _layout_simples(), [it.to_dict()])

    pacote = atproj.exportar_atproj(pid, tmp_path / "viagem")
    assert pacote.suffix == ".atproj"
    m = atproj.ler_manifesto(pacote)
    assert m["nome"] == "Viajante" and m["itens"] == 1    # a prévia fala

    novo = atproj.importar_atproj(pacote)
    assert novo != pid                           # cópia, nunca colisão (I1)
    db = Database().init()
    try:
        with db.Session() as s:
            original = s.get(ProjetoSalvo, pid)
            copia = s.get(ProjetoSalvo, novo)
            assert copia.estado_slots == original.estado_slots   # BYTE a byte
            assert copia.uuid != original.uuid
            rel = json.loads(copia.estado_slots)["itens"][0]["imagem"]
            assert not Path(rel).is_absolute()               # relativo (I3)
            f_orig = _pasta(original.uuid) / rel
            f_novo = _pasta(copia.uuid) / rel
            assert f_novo.exists()
            assert f_novo.read_bytes() == f_orig.read_bytes()  # foto idêntica
    finally:
        db.engine.dispose()
    p = projetos.abrir_projeto(novo)             # e ABRE de verdade
    assert p is not None and p.itens[0]["nome"] == "Produto com foto"


def test_a_somente_leitura_barra_e_reverte(raiz_env):
    """R-131 (passos 4-5, 16): ligado, as portas de ESCRITA levantam a
    mensagem PT-BR e o banco fica intacto; aprovar segue livre; desligar
    devolve a edição."""
    from app.core import modo, projetos
    from app.qt.telas import servico
    pid_prod = seeds.add_produto(raiz_env, "Arroz 5kg", "Camil", "24.90")
    pid_proj = _salvar("Aprovável")
    modo.definir_somente_leitura(True)
    try:
        assert modo.somente_leitura()
        with pytest.raises(modo.SomenteLeitura) as exc:
            servico.editar_produto(pid_prod, nome_sanitizado="Hackeado")
        assert "somente-leitura" in str(exc.value).lower()
        d = seeds.produto_por_chave(raiz_env, "Arroz 5kg", "Camil")
        assert d is not None                     # o banco NÃO mudou
        with pytest.raises(modo.SomenteLeitura):
            _salvar("Não pode")
        with pytest.raises(modo.SomenteLeitura):
            servico.excluir_produtos([pid_prod])
        # aprovar e exportar são o PROPÓSITO do modo — seguem livres
        projetos.aprovar(pid_proj)
        assert projetos.esta_aprovado(pid_proj)
    finally:
        modo.definir_somente_leitura(False)
    novo = servico.editar_produto(pid_prod, nome_sanitizado="Arroz Novo 5kg")
    assert novo["nome"] == "Arroz Novo 5kg"      # a edição voltou


def test_a_verificar_atualizacao_honesto(raiz_env, monkeypatch):
    """R-127 (passos 8-9, 17): sem URL → mensagem honesta; rede caída →
    degrada SEM travar nem mentir; com versão nova → novidades em PT-BR."""
    from app.core import atualizacao
    r = atualizacao.verificar_atualizacao()      # sem URL configurada
    assert r["disponivel"] is False
    assert "offline" in r["mensagem"]

    import requests

    def _cai(*a, **k):
        raise requests.ConnectionError("sem rede")
    monkeypatch.setattr(requests, "get", _cai)
    r2 = atualizacao.verificar_atualizacao("http://exemplo.local/v.json")
    assert r2["disponivel"] is False
    assert "app segue normal" in r2["mensagem"]  # honesto, não trava

    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"versao": "1.1",
                    "novidades": ["Etiquetas em lote", "Modo Pai"]}
    monkeypatch.setattr(requests, "get", lambda *a, **k: _Resp())
    r3 = atualizacao.verificar_atualizacao("http://exemplo.local/v.json")
    assert r3["disponivel"] is True and r3["versao"] == "1.1"
    assert "Modo Pai" in r3["mensagem"]


def test_a_verificar_ao_abrir_acusa_foto_sumida(raiz_env):
    """R-138 (passo 10): a checagem da abertura passa no PRAGMA e ACUSA o
    cadastro que aponta para foto sumida — aviso, nunca crash."""
    from app.core.database import Database
    from app.core.models import Produto
    from app.core.recuperacao import verificar_ao_abrir
    pid = seeds.add_produto(raiz_env, "Sem foto real", None, "1.00")
    db = Database(raiz_env).init()
    try:
        with db.Session() as s:
            s.get(Produto, pid).caminho_imagem = f"{pid}/sumida.png"
            s.commit()
    finally:
        db.engine.dispose()
    r = verificar_ao_abrir(raiz_env)
    assert r["banco_ok"] is True                 # o PRAGMA responde ok
    assert r["sem_arquivo"] == 1                 # e a foto sumida é ACUSADA
    assert any("sumiu" in a for a in r["avisos"])


# ============================================================================
# Bloco B — sonhos finais (R-144, R-148, R-149, R-147)
# ============================================================================

def test_b_etiquetas_em_lote_medem_certo(raiz_env, tmp_path):
    """R-144 (passos 19-20, 32): 10 etiquetas de 100×70 mm em folhas A4 —
    2×4 por folha (a grade nasce do tamanho REAL), 2 folhas, página medida
    em mm com pypdf; etiqueta grande demais é RECUSADA nominalmente."""
    from PIL import Image
    from pypdf import PdfReader

    from app.qt.telas import servico
    from app.qt.telas.servico import ItemMesa
    from app.rendering.imposicao import impor_etiquetas
    from app.rendering.units import mm_para_px
    itens = [ItemMesa("x", f"{i + 1},99", "VERDE", f"Produto {i}",
                      preco_de=f"{i + 3},99") for i in range(10)]
    destino = tmp_path / "etiquetas.pdf"
    caminho, avisos = servico.gerar_etiquetas_lote(itens, destino)
    r = PdfReader(str(caminho))
    assert len(r.pages) == 2                     # 8 por folha → 10 = 2 folhas
    w_pt = float(r.pages[0].mediabox.width)
    h_pt = float(r.pages[0].mediabox.height)
    assert w_pt * 25.4 / 72 == pytest.approx(210, abs=1)   # A4 em mm
    assert h_pt * 25.4 / 72 == pytest.approx(297, abs=1)

    # a grade por CONTEÚDO: uma etiqueta vermelha cai na 2ª coluna
    dpi = 96
    ew, eh = round(mm_para_px(100, dpi)), round(mm_para_px(70, dpi))
    vermelha = Image.new("RGB", (ew, eh), (200, 20, 20))
    branca = Image.new("RGB", (ew, eh), (250, 250, 250))
    folhas = impor_etiquetas([branca, vermelha], dpi)
    w = round(mm_para_px(210, dpi))
    ox0 = (w - 2 * ew) // 2
    oy0 = (round(mm_para_px(297, dpi)) - 4 * eh) // 2
    px = folhas[0].getpixel((ox0 + ew + ew // 2, oy0 + eh // 2))
    assert px[0] > 150 and px[1] < 80            # a vermelha na 2ª coluna

    # marcas de corte SÓ na área USADA (a galeria pegou marca no vazio da
    # folha parcial): com 2 etiquetas (1 linha de 4), a borda da linha usada
    # tem marca cinza; a altura da 4ª linha fica branca
    assert folhas[0].getpixel((ox0 - 2, oy0 + eh))[0] < 200
    assert folhas[0].getpixel((ox0 - 2, oy0 + 3 * eh))[0] > 240

    gigante = Image.new("RGB", (round(mm_para_px(300, dpi)), 100), "red")
    with pytest.raises(ValueError):
        impor_etiquetas([gigante], dpi)          # recusa nominal (I2)


def test_b_template_compartilhavel_nao_leva_dado_nenhum(raiz_env, tmp_path):
    """R-149 (passos 24-25, 32): o .attpl leva a ESTRUTURA; a varredura por
    AUSÊNCIA prova que nome de produto, preço, texto fixo e caminho de arte
    NÃO viajam — e o import devolve as mesmas células."""
    from app.core.template_compartilhavel import (
        exportar_template, importar_template, vazamentos_no_template)
    from app.rendering.model import (
        LayoutDef, Pagina, Regiao, Retangulo, Slot, TipoRegiao)
    arte = tmp_path / "arte_secreta_do_camil.png"
    arte.write_bytes(seeds.png("#AA0000"))
    reg_texto = Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(5, 80, 90, 10),
                       nome="Aviso")
    reg_texto.texto_fixo = "Oferta Camil só hoje por 24,90"
    lay = LayoutDef(100, 100, dpi=96, arquivo_fundo=str(arte), paginas=[
        Pagina([Slot("celula_a", [
            Regiao(TipoRegiao.IMAGEM, Retangulo(5, 5, 40, 30), nome="Foto"),
            Regiao(TipoRegiao.PRECO, Retangulo(5, 40, 40, 12), nome="Preço"),
            reg_texto])])])
    saida = exportar_template(lay, tmp_path / "presente")
    vazou = vazamentos_no_template(saida, [
        "Camil", "24,90", "arte_secreta", str(arte)])
    assert vazou == []                           # NADA do dono viaja
    lay2 = importar_template(saida)
    assert lay2.arquivo_fundo in (None, "")
    slots = lay2.paginas[0].slots
    assert len(slots) == 1 and len(slots[0].regioes) == 3   # a estrutura veio
    assert all(not getattr(r, "texto_fixo", None)
               for r in slots[0].regioes)        # sem os textos do dono


def test_b_calendario_datas_certas_e_evento(raiz_env):
    """R-148 (passos 21-23, 33): as datas móveis CALCULAM certo (Páscoa por
    Gauss, Black Friday, Dia das Mães/Pais), o lembrete olha a janela, e a
    data vira um EVENTO real no banco."""
    from datetime import date

    from app.core import calendario
    datas = {d["nome"]: d["data"] for d in calendario.datas_do_ano(2026)}
    assert datas["Páscoa"] == date(2026, 4, 5)
    assert datas["Black Friday"] == date(2026, 11, 27)
    assert datas["Dia das Mães"] == date(2026, 5, 10)
    assert datas["Dia dos Pais"] == date(2026, 8, 9)
    prox = calendario.proximas_datas(hoje=date(2026, 7, 21), dias=30)
    assert prox and prox[0]["nome"] == "Dia dos Pais"
    assert prox[0]["faltam"] == 19
    calendario.criar_evento_comemorativo(prox[0])
    from app.qt.telas.eventos import listar_eventos
    assert any(e["nome"] == "Dia dos Pais" for e in listar_eventos())


def test_b_gerador_de_fundo_degrada_sem_gpu(monkeypatch):
    """R-147 (passos 26-27, 33): sem GPU → (None, aviso honesto que cita a
    GPU) — nunca trava; com motor injetado, a imagem volta (ponto de
    partida editável)."""
    from PIL import Image

    import app.images.estudio as E
    from app.images import fundo_ia
    monkeypatch.setattr(E, "gerador_disponivel", lambda: None)
    assert fundo_ia.gerador_fundo_disponivel() is False
    img, aviso = fundo_ia.gerar_fundo("São João", 400, 300)
    assert img is None and "GPU" in aviso        # aviso honesto, sem crash
    fake = lambda tema, w, h: Image.new("RGB", (w, h), (240, 200, 40))  # noqa: E731
    img2, aviso2 = fundo_ia.gerar_fundo("São João", 400, 300, motor=fake)
    assert aviso2 is None and img2.size == (400, 300)
    assert img2.getpixel((10, 10)) == (240, 200, 40)


# ============================================================================
# Bloco C — Modo Pai (R-150)
# ============================================================================

def _projeto_completo(raiz_env, tmp_path, nome="Oferta da semana") -> int:
    """Um projeto APROVÁVEL: item com foto + preço entendido + validade."""
    from app.core import projetos
    from app.qt.telas.servico import ItemMesa
    foto = tmp_path / "p.png"
    foto.write_bytes(seeds.png("#BB2200"))
    it = ItemMesa("x", "9,90", "VERDE", "Arroz Tio João 5kg",
                  imagem=str(foto))
    return projetos.salvar_projeto(
        nome, "Quintou", "TABLOIDE", _layout_simples(), [it.to_dict()],
        validade_oferta="OFERTA VÁLIDA SOMENTE 21/07",
        mapa={"s": it.uid})


def test_c_modo_pai_so_tem_acoes_seguras(raiz_env):
    """R-150 (passos 40, 44): NENHUMA ação destrutiva alcançável — a
    varredura dos botões prova por conteúdo; as 4 ações seguras existem."""
    from PySide6.QtWidgets import QPushButton

    from app.qt.telas.modo_pai import ModoPaiTela
    _app()
    tela = ModoPaiTela()
    textos = [b.text().lower() for b in tela.findChildren(QPushButton)]
    proibidas = ("excluir", "apagar", "deletar", "editar", "remover",
                 "configura", "limpar")
    assert not any(p in txt for txt in textos for p in proibidas)
    assert any("aprovar" in txt for txt in textos)
    assert any("imprimir" in txt for txt in textos)
    assert any("enviar" in txt for txt in textos)
    assert any("sair do modo simples" in txt for txt in textos)
    tela.close()


def test_c_fluxo_3_passos_do_pronto_ao_envio(raiz_env, tmp_path, monkeypatch):
    """R-150 (passos 37, 39, 45): abrir pronto → conferir → aprovar (o
    checklist F8 decide) → enviar (copiar imagem) — sem passar por tela
    perigosa; a imagem enviada EXISTE e o aprovado sai SEM rascunho."""
    from app.core import projetos
    from app.qt.telas import compartilhar
    from app.qt.telas.modo_pai import ModoPaiTela
    _app()
    pid = _projeto_completo(raiz_env, tmp_path)
    tela = ModoPaiTela()
    tela.recarregar()                            # passo 1: a lista de prontos
    assert tela.lista.count() == 1
    assert tela.btn_aprovar.isEnabled()          # passo 2: conferindo
    assert "não aprovada" in tela._situacao.text().lower()

    tela._aprovar()                              # passo 3a: aprovar (F8)
    assert projetos.esta_aprovado(pid)           # o checklist PASSOU
    assert "Aprovada" in tela._situacao.text()

    enviados: list[str] = []
    monkeypatch.setattr(compartilhar, "copiar_imagem",
                        lambda c: enviados.append(str(c)) or True)
    tela._enviar()                               # passo 3b: enviar
    assert enviados and Path(enviados[0]).exists()
    from PIL import Image
    im = Image.open(enviados[0])
    assert im.width > 50 and im.height > 50      # a peça de verdade
    tela.close()


def test_c_modo_pai_lembrado_por_perfil(raiz_env):
    """R-150 (passo 38): entrar LEMBRA (o boot abre no modo); sair
    desliga — por conteúdo da Config."""
    from app.qt.telas.modo_pai import (
        ModoPaiTela, lembrar_modo_pai, modo_pai_lembrado)
    _app()
    assert modo_pai_lembrado() is False
    lembrar_modo_pai(True)
    assert modo_pai_lembrado() is True           # o próximo boot cai nele
    saiu: list[bool] = []
    tela = ModoPaiTela(ao_sair=lambda: saiu.append(True))
    tela._sair()
    assert saiu == [True]
    assert modo_pai_lembrado() is False          # sair é consciente e desliga
    tela.close()


# ============================================================================
# Bloco D — o MARCO refeito (RG-48/RG-58)
# ============================================================================

ARTE_QUINTOU = Path("arte/quintou")


def _fontes_reais(root):
    import shutil
    reais = Path("AutoTabloide_System_Root/fontes")
    if reais.exists():
        for f in reais.glob("*.ttf"):
            shutil.copy(f, root.fontes / f.name)


def test_d_campanhas_descobertas_e_faltantes_nomeadas(tmp_path):
    """Passo 50: o padrão-ouro descobre as campanhas REAIS por pasta; as que
    faltam são NOMEADAS (nunca um skip mudo, I2) — e uma campanha nova é
    absorvida SOZINHA quando a arte cair na pasta."""
    from app.core.marco import campanhas_do_marco, itens_reais_da_campanha
    disp, falt = campanhas_do_marco()
    nomes = [c["nome"] for c in disp]
    assert "quintou" in nomes                    # a campanha real do repo
    q = next(c for c in disp if c["nome"] == "quintou")
    assert q["verso"] is not None                # frente E verso reais
    assert q["validade"] == "ATÉ 26/05"          # RG-58: o "até" transcrito
    itens = itens_reais_da_campanha(q)
    assert len(itens) >= 30                      # as ofertas do dono
    assert ("Cerveja Itaipava 269ML", "1,98") in itens
    assert set(falt) == {"sexta_verde", "fim_de_semana"}   # nomeadas
    # a mecânica: uma campanha NOVA entra sozinha pela pasta
    nova = tmp_path / "arte2" / "sexta_verde"
    nova.mkdir(parents=True)
    (nova / "frente_template.png").write_bytes(seeds.png("#00AA00"))
    disp2, falt2 = campanhas_do_marco(tmp_path / "arte2")
    assert [c["nome"] for c in disp2] == ["sexta_verde"]
    assert "sexta_verde" not in falt2


@pytest.mark.skipif(not (ARTE_QUINTOU / "frente_template.png").exists(),
                    reason="arte real do Quintou não está no repositório")
def test_d_marco_dados_reais_validade_desenhada_e_pdf_em_mm(
        tmp_path, monkeypatch):
    """RG-48 + RG-58 (passos 47-49, 53-54, 61): o marco com os DADOS REAIS
    transcritos da peça (30 ofertas do Quintou) sobre o layout REAL detectado
    da arte (frente+verso); a VALIDADE da peça é DESENHADA (por pixel, nunca
    vazia); o PDF sai medido em mm; e o adversarial ATIVO troca 2 uids e
    prova que os pixels trocam exatamente."""
    from PIL import Image
    from pypdf import PdfReader

    from app.core.marco import campanhas_do_marco, itens_reais_da_campanha
    from app.core.paths import SystemRoot
    from app.qt.telas import servico
    from app.qt.telas.servico import ItemMesa
    from app.rendering.compositor import DadosProduto, compor_pagina
    from app.rendering.export import exportar_pdf_multipagina
    from app.rendering.grade import (
        adicionar_pagina_de_arte, layout_grade_de_arte, ocupaveis,
        ordenar_slots_visualmente)
    from app.rendering.model import (
        PapelTexto, Regiao, Retangulo, Slot, TipoRegiao)
    from app.rendering.units import mm_para_px
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    _app()
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    _fontes_reais(root)

    q = next(c for c in campanhas_do_marco()[0] if c["nome"] == "quintou")
    reais = itens_reais_da_campanha(q)
    assert q["validade"]                         # RG-58 no dado: nunca None

    layout, _ = layout_grade_de_arte(str(q["frente"]))
    adicionar_pagina_de_arte(layout, str(q["verso"]))
    # RG-58 na PEÇA: a validade vira um TEXTO_LEGAL papel VALIDADE na frente
    reg_val = Regiao(TipoRegiao.TEXTO_LEGAL, Retangulo(4, 2, 90, 6),
                     nome="Validade")
    reg_val.papel_texto = PapelTexto.VALIDADE
    reg_val.texto_fixo = "OFERTA VÁLIDA " + q["validade"]
    layout.paginas[0].slots.append(Slot("validade_marco", [reg_val]))

    itens = []
    for i, (nome, preco) in enumerate(reais):
        foto = tmp_path / ("r%d.png" % i)
        Image.new("RGB", (160, 160),
                  ((i * 53) % 256, (i * 97) % 256, (i * 31) % 256)).save(foto)
        itens.append(ItemMesa(nome.upper(), preco, "VERDE", nome,
                              imagem=str(foto)))
    slots = []
    for pag in layout.paginas:
        slots.extend(ocupaveis(ordenar_slots_visualmente(pag.slots)))
    mapa = {s.id: it.uid for s, it in zip(slots, itens)}
    assert len(mapa) >= 28                       # os ~30 reais couberam
    por_uid = {it.uid: it for it in itens}
    dados = {sid: DadosProduto(por_uid[u].nome,
                               preco_por=servico.preco_decimal(
                                   por_uid[u].preco),
                               imagem_path=por_uid[u].imagem)
             for sid, u in mapa.items()}
    avisos = servico.validar_composicao(layout, dados)
    assert avisos == []                          # pré-voo LIMPO (passo 59)

    imgs = [compor_pagina(layout, pag, dados) for pag in layout.paginas]
    # a VALIDADE desenhada: com vs sem texto → pixels diferem NA região
    reg_val.texto_fixo = ""
    sem_val = compor_pagina(layout, layout.paginas[0], dados)
    reg_val.texto_fixo = "OFERTA VÁLIDA " + q["validade"]
    x0 = round(mm_para_px(reg_val.rect.x_mm, layout.dpi))
    y0 = round(mm_para_px(reg_val.rect.y_mm, layout.dpi))
    x1 = round(mm_para_px(reg_val.rect.x_mm + reg_val.rect.larg_mm,
                          layout.dpi))
    y1 = round(mm_para_px(reg_val.rect.y_mm + reg_val.rect.alt_mm,
                          layout.dpi))
    faixa_com = imgs[0].crop((x0, y0, x1, y1))
    faixa_sem = sem_val.crop((x0, y0, x1, y1))
    assert faixa_com.tobytes() != faixa_sem.tobytes()   # há TINTA de validade

    pdf = exportar_pdf_multipagina(imgs, tmp_path / "marco_f12.pdf",
                                   layout.dpi)
    leitor = PdfReader(str(pdf))
    assert len(leitor.pages) == 2                # frente + verso reais
    w_mm = float(leitor.pages[0].mediabox.width) * 25.4 / 72
    h_mm = float(leitor.pages[0].mediabox.height) * 25.4 / 72
    assert w_mm == pytest.approx(layout.largura_mm, abs=0.5)   # medido em mm
    assert h_mm == pytest.approx(layout.altura_mm, abs=0.5)
    assert Path(pdf).stat().st_size > 50_000     # peça real, não vazia

    # ADVERSARIAL ATIVO (passos 56/63): trocar 2 uids TROCA os 2 pixels
    sids = [s.id for s in ocupaveis(
        ordenar_slots_visualmente(layout.paginas[0].slots))][:2]
    antes = {}
    for sid in sids:
        slot = next(s for s in layout.paginas[0].slots if s.id == sid)
        reg = next(r for r in slot.regioes if r.tipo == TipoRegiao.IMAGEM)
        cx = round(mm_para_px(reg.rect.x_mm + reg.rect.larg_mm / 2,
                              layout.dpi))
        cy = round(mm_para_px(reg.rect.y_mm + reg.rect.alt_mm / 2,
                              layout.dpi))
        antes[sid] = (cx, cy, imgs[0].getpixel((cx, cy))[:3])
    dados[sids[0]], dados[sids[1]] = dados[sids[1]], dados[sids[0]]
    trocada = compor_pagina(layout, layout.paginas[0], dados)
    a, b = antes[sids[0]], antes[sids[1]]
    assert trocada.getpixel((a[0], a[1]))[:3] == b[2]   # trocou exatamente
    assert trocada.getpixel((b[0], b[1]))[:3] == a[2]


def test_d_performance_5k_medida(tmp_path, monkeypatch):
    """Passos 52/62: 5.000 produtos no acervo — abrir o catálogo e conciliar
    DENTRO dos tetos, MEDIDO com relógio (não estimado)."""
    import time

    from app.core.database import Database
    from app.core.models import Produto
    from app.core.paths import SystemRoot
    from app.qt.telas import servico
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    SystemRoot(tmp_path / "raiz").criar_estrutura()
    db = Database().init()
    try:
        with db.Session() as s:
            s.add_all([Produto(
                nome_bruto="PRODUTO PERF %d" % i,
                nome_sanitizado="Produto Perf %d" % i,
                marca="Marca%d" % (i % 40)) for i in range(5000)])
            s.commit()
    finally:
        db.engine.dispose()

    t0 = time.monotonic()
    pagina = servico.listar_catalogo(offset=0, limite=50)
    t_abrir = time.monotonic() - t0
    assert len(pagina) == 50
    assert t_abrir < 2.0, "abrir catálogo levou %.2fs (teto 2s)" % t_abrir

    t0 = time.monotonic()
    res = servico.conciliar_linhas(
        [("PRODUTO PERF 4999", "1,00", None),
         ("Produto Perf 123", "2,00", None),
         ("COISA QUE NAO EXISTE 999", "3,00", None)], lambda _m: None)
    t_conc = time.monotonic() - t0
    assert res.itens[0].semaforo == "VERDE"      # exato no acervo de 5k
    assert t_conc < 45.0, "conciliar 3 em 5k levou %.1fs (teto 45s)" % t_conc
    print("\n[MEDIDO] abrir=%.3fs - conciliar 3 itens contra 5k=%.1fs"
          % (t_abrir, t_conc))


# ============================================================================
# Bloco E — empacotamento e entrega (migração do protótipo antigo)
# ============================================================================

def test_e_migracao_do_prototipo_por_chave_natural(raiz_env, tmp_path):
    """Passos 70-71, 79: um banco ANTIGO sintético (o schema real do
    protótipo) entra por CHAVE NATURAL — o repetido NÃO duplica (e é
    contado), marca/preço/categoria/aliases chegam íntegros, e o banco
    antigo não é tocado (só leitura)."""
    import sqlite3

    from app.core.migracao_antiga import (
        analisar_banco_antigo, migrar_banco_antigo)
    velho = tmp_path / "autotabloide_antigo.db"
    con = sqlite3.connect(velho)
    con.executescript(
        "CREATE TABLE produtos (id INTEGER PRIMARY KEY, sku_origem TEXT, "
        "nome_sanitizado TEXT, marca_normalizada TEXT, detalhe_peso TEXT, "
        "categoria TEXT, preco_venda_atual REAL);"
        "CREATE TABLE produto_aliases (id INTEGER PRIMARY KEY, "
        "produto_id INTEGER, alias_raw TEXT);")
    con.executemany(
        "INSERT INTO produtos (id, nome_sanitizado, marca_normalizada, "
        "detalhe_peso, categoria, preco_venda_atual) VALUES (?,?,?,?,?,?)",
        [(1, "Arroz 5kg", "Camil", "5kg", "Mercearia", 24.90),
         (2, "Café Torrado 500g", "Pilão", "500g", "Mercearia", 18.50),
         (3, "Detergente 500ml", "Ypê", "500ml", "Limpeza", 2.49)])
    con.executemany(
        "INSERT INTO produto_aliases (produto_id, alias_raw) VALUES (?,?)",
        [(1, "ARROZ TP1 CAMIL 5KG"), (2, "CAFE PILAO TRAD")])
    con.commit()
    con.close()
    bytes_antes = velho.read_bytes()

    # o "Arroz Camil" JÁ existe no acervo novo → a chave natural o pula
    seeds.add_produto(raiz_env, "Arroz 5kg", "Camil", "22.00")

    previa = analisar_banco_antigo(velho)        # o rito: PRÉVIA primeiro
    assert previa["total_antigo"] == 3
    assert previa["novos"] == 2
    assert previa["existentes"] == 1             # o repetido é CONTADO (I2)

    r = migrar_banco_antigo(velho)
    assert r == {"importados": 2, "pulados": 1, "aliases": 1}
    cafe = seeds.produto_por_chave(raiz_env, "Café Torrado 500g", "Pilão")
    assert cafe is not None and cafe["preco"] == "18.50"    # íntegro
    arroz = seeds.produto_por_chave(raiz_env, "Arroz 5kg", "Camil")
    assert arroz["preco"] == "22.00"             # o MEU acervo venceu (não
    # foi sobrescrito pelo antigo — chave natural pula, nunca atropela)
    from app.qt.telas import servico as _srv
    aliases = _srv.correcoes_aprendidas()
    assert any(a["alias"] == "CAFE PILAO TRAD" for a in aliases)
    assert velho.read_bytes() == bytes_antes     # o antigo intocado (byte)
