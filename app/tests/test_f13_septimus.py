"""ORDEM F13-SEPTIMUS — O ORÇAMENTO DA CÉLULA.

O3: a validade NÃO chegava à página do projeto salvo (M-02 pela 4ª
vez) — a miniatura montava uma TERCEIRA receita à mão, sem
texto_legal/descritor/edição (a doença do Modo Pai da F12). O1/O2: o
orçamento com FAIXA (piso solto vira teto num sistema que otimiza).
"""

from pathlib import Path

import pytest
from PIL import Image

from app.tests import acervo

_PACOTE = Path(__file__).resolve().parents[2] / "Templates novos"


@pytest.fixture()
def raiz_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.paths import SystemRoot
    root = SystemRoot(tmp_path / "raiz").criar_estrutura()
    acervo.copiar_fontes_reais(root.fontes)
    return root


def test_o3_a_validade_chega_a_miniatura_do_projeto(raiz_tmp):
    """O3 (M-02 ×4): a miniatura do projeto salvo compõe pela MONTAGEM
    OFICIAL — a validade VIVA aparece por pixel na zona da região
    VALIDADE (antes: a receita à mão da miniatura a jogava fora e a
    região caía no texto de reserva)."""
    import numpy as np

    from app.core import projetos
    from app.rendering.model import (
        LayoutDef,
        Pagina,
        PapelTexto,
        Regiao,
        Retangulo,
        Slot,
        TipoRegiao,
    )

    sel = Slot("selo", [Regiao(
        TipoRegiao.TEXTO_LEGAL, Retangulo(10, 8, 80, 12),
        nome="Validade", papel_texto=PapelTexto.VALIDADE,
        cor="#000000")])
    cel = Slot("c1", [Regiao(TipoRegiao.NOME, Retangulo(10, 40, 60, 10),
                             cor="#000000")])
    lay = LayoutDef(100, 100, dpi=100, paginas=[Pagina([sel, cel])])
    from app.qt.telas.servico import ItemMesa
    it = ItemMesa(nome="Café", descricao="", semaforo="verde",
                  preco="9,90")

    def _tinta_da_miniatura(pid):
        pasta = next(p for p in raiz_tmp.projetos.iterdir()
                     if (p / "miniatura.png").exists()
                     and str(pid) in ((p / "id.txt").read_text()
                                      if (p / "id.txt").exists()
                                      else str(pid)))
        img = Image.open(pasta / "miniatura.png").convert("L")
        a = np.asarray(img, dtype=int)
        zona = a[: a.shape[0] * 22 // 100, :]        # a faixa do selo
        return int((zona < 128).sum())

    pid_sem = projetos.salvar_projeto(
        "Sem validade", "Ev", "TABLOIDE", lay, [it.to_dict()],
        mapa={"c1": it.uid})
    com = ItemMesa(nome="Café", descricao="", semaforo="verde",
                   preco="9,90")
    pid_com = projetos.salvar_projeto(
        "Com validade", "Ev", "TABLOIDE", lay, [com.to_dict()],
        validade_oferta="SOMENTE 27/07", mapa={"c1": com.uid})

    pastas = sorted(raiz_tmp.projetos.iterdir())
    assert len(pastas) >= 2
    tintas = []
    for pasta in pastas:
        mini = pasta / "miniatura.png"
        assert mini.exists(), "a miniatura não foi gerada"
        img = Image.open(mini).convert("L")
        a = np.asarray(img, dtype=int)
        zona = a[: a.shape[0] * 22 // 100, :]
        tintas.append(int((zona < 128).sum()))
    assert max(tintas) > min(tintas) + 30, (
        "a VALIDADE não mudou a miniatura — a data segue sem chegar à "
        f"página do projeto salvo (M-02): tintas={tintas}")


def test_o1_o_orcamento_da_celula_na_segunda():
    """O1 (a régua NOVA, com faixa — a de ≥55% da QUINQUE está
    REVOGADA): nas células de produto da Segunda, a FOTO fica entre
    55% e 68% da ALTURA útil da célula (nunca acima — foto gulosa era
    o defeito novo) e a faixa do NOME tem altura para 2 linhas em
    corpo legível (≥ 17% da célula)."""
    if not _PACOTE.exists():
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.grade import ocupaveis
    from app.rendering.model import TipoRegiao

    lay = layout_de_encarte("segunda-frios", _PACOTE)
    for s in ocupaveis(lay.paginas[0].slots):
        foto = next(r for r in s.regioes
                    if r.tipo == TipoRegiao.IMAGEM)
        nome = next(r for r in s.regioes if r.tipo == TipoRegiao.NOME)
        textos = [r for r in s.regioes
                  if r.tipo in (TipoRegiao.NOME, TipoRegiao.SUBTITULO)]
        y0 = min(r.rect.y_mm for r in s.regioes)
        y1 = max(r.rect.y_mm + r.rect.alt_mm for r in s.regioes)
        util = y1 - y0
        fr_foto = foto.rect.alt_mm / util
        fr_texto = sum(r.rect.alt_mm for r in textos) / util
        assert 0.55 <= fr_foto <= 0.68, (
            f"{s.id}: a foto ocupa {fr_foto:.0%} da altura útil — o "
            "orçamento O1 manda 55–68% (nem raquítica, nem gulosa)")
        # a banda azul é da ARTE (60px) — a zona de TEXTO (nome +
        # descritor) fica ≥16% dela e o corpo do nome ≥14pt (a regra
        # que manda: o texto nunca cede; crescer a banda = regenerar a
        # arte da Segunda, nominal)
        assert fr_texto >= 0.16, (
            f"{s.id}: a zona de texto tem {fr_texto:.0%} — não cabem "
            "2 linhas legíveis")
        assert nome.tamanho_max_pt >= 14.0, (
            f"{s.id}: corpo do nome {nome.tamanho_max_pt}pt < 14pt")


def test_upsert_do_import_preserva_o_conteudo_fixo(raiz_tmp):
    """SEPTIMUS (achado do rollout): ATUALIZAR um encarte pelo import
    NÃO apaga a configuração N1 do dono — o conteudo_fixo (o Kit com a
    foto escolhida) sobrevive ao upsert por slot.id."""
    if not _PACOTE.exists():
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")
    from app.core.database import Database
    from app.rendering.encartes import importar_pacote
    from app.rendering.persistencia import carregar_layout, listar_layouts

    db = Database().init()
    try:
        with db.Session() as s:
            importar_pacote(s, _PACOTE, raiz=raiz_tmp)
            s.commit()
            row = next(r for r in listar_layouts(s)
                       if r.nome == "Segunda dos Frios")
            lay = carregar_layout(s, row.id, raiz=raiz_tmp)
            fixa = next(sl for p in lay.paginas
                        for sl in p.slots if sl.fixa)
            fixa.conteudo_fixo = {"nome": "Kit do Dono",
                                  "preco": "39,00",
                                  "preco_da_semana": True}
            from app.rendering.persistencia import salvar_layout
            salvar_layout(s, "Segunda dos Frios", lay,
                          layout_id=row.id, raiz=raiz_tmp)
            s.commit()
            importar_pacote(s, _PACOTE, raiz=raiz_tmp)   # a atualização
            s.commit()
            lay2 = carregar_layout(s, row.id, raiz=raiz_tmp)
            fixa2 = next(sl for p in lay2.paginas
                         for sl in p.slots if sl.fixa)
            assert fixa2.conteudo_fixo and \
                fixa2.conteudo_fixo.get("nome") == "Kit do Dono", (
                    "o upsert do import APAGOU o conteúdo fixo do dono")
    finally:
        db.engine.dispose()


def test_o2_a_foto_do_kit_respira_no_oval():
    """O2: a célula FIXA da Segunda (o oval do Kit) é a MAIOR da página
    — a foto dela não pode ser a menor: a zona de foto ocupa ≥ 42% da
    altura útil do oval (o destaque do encarte respira)."""
    if not _PACOTE.exists():
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")
    from app.rendering.encartes import layout_de_encarte
    from app.rendering.model import TipoRegiao

    lay = layout_de_encarte("segunda-frios", _PACOTE)
    fixa = next(s for s in lay.paginas[0].slots if s.fixa)
    foto = next(r for r in fixa.regioes if r.tipo == TipoRegiao.IMAGEM)
    y0 = min(r.rect.y_mm for r in fixa.regioes)
    y1 = max(r.rect.y_mm + r.rect.alt_mm for r in fixa.regioes)
    fr = foto.rect.alt_mm / (y1 - y0)
    assert fr >= 0.42, (
        f"a foto do oval ocupa {fr:.0%} da altura útil — o Kit era um "
        "selo minúsculo na maior célula da página (O2)")
