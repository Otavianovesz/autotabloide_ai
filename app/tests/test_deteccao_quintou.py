"""G2 do gate 3 (ORDEM_F5_6 §11): detecção nas DUAS faces da arte real.

Frente = regressão; verso = caso novo (logo Belo Brasil no topo-direito, última
linha deslocada). Proibido consertar uma face quebrando a outra — as duas vivem
no MESMO teste. Riscos do §11 conferidos por assert, não no olho.
"""

from pathlib import Path

import pytest

from app.rendering.grade import detectar_caixas_preco, layout_grade_de_arte

ARTE = Path("arte/quintou")

pytestmark = pytest.mark.skipif(
    not (ARTE / "frente_template.png").exists(),
    reason="arte real do Quintou não está no repositório")


def _linhas(caixas, tol=30):
    caixas = sorted(caixas, key=lambda c: (c[1], c[0]))
    grupos: list[list] = []
    for c in caixas:
        if grupos and abs(c[1] - grupos[-1][0][1]) < tol:
            grupos[-1].append(c)
        else:
            grupos.append([c])
    return grupos


def test_frente_regressao_15_caixas():
    caixas = detectar_caixas_preco(str(ARTE / "frente_template.png"))
    grupos = _linhas(caixas)
    assert len(caixas) == 15
    assert [len(g) for g in grupos] == [4, 4, 4, 3]
    # última linha deslocada à DIREITA (canto inferior-esq. é da logomarca B)
    assert min(c[0] for c in grupos[3]) > 400
    # risco §11: tracinhos vermelhos finos não viram caixa (largura mínima real)
    assert all(c[2] > 50 for c in caixas)
    # risco §11: neon do cabeçalho fora (1ª linha abaixo do corte de 30%)
    assert grupos[0][0][1] > 1300 * 0.30


def test_verso_caso_novo_15_caixas():
    caixas = detectar_caixas_preco(str(ARTE / "verso_template.png"))
    grupos = _linhas(caixas)
    assert len(caixas) == 15
    assert [len(g) for g in grupos] == [4, 4, 4, 3]
    # última linha deslocada à ESQUERDA — o canto inferior-DIREITO fica livre
    # para o bloco "Fica a Dica" (a região livre do G3)
    assert max(c[0] for c in grupos[3]) < 900
    assert all(c[2] > 50 for c in caixas)
    # risco §11: última linha dentro da varredura (~95% da altura)
    assert grupos[3][0][1] < 1300 * 0.97


def test_verso_vira_grade_com_mestre():
    layout, caixas = layout_grade_de_arte(str(ARTE / "verso_template.png"))
    slots = layout.paginas[0].slots
    assert len(slots) == 15
    assert slots[0].mestre
    assert all(s.ref_grupo == "celula_0" for s in slots[1:])
    assert all(len(s.regioes) == 3 for s in slots)   # Imagem/Nome/Preço em todas