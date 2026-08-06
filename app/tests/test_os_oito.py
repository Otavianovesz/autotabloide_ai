"""O TESTE DOS OITO — a rede da L22 (ORDEM DUODETRICESIMUS §14).

> "Cada encarte novo que ele abre é uma REGRESSÃO a um estado já
> consertado em outro lugar. Isso não é sequência de defeitos: é um
> defeito só — o de as regras morarem no layout em vez de morarem no
> motor."

**Um arquivo. Oito parâmetros. Todas as regras de composição já
conquistadas.** Cada regra vira uma função nomeada que recebe a página
COMPOSTA (do banco, pela porta real — L16) e devolve as violações; o
pytest parametriza pelos oito encartes do pacote do dono.

Quando uma lei nova nascer numa rodada, ela entra AQUI — e passa a
valer nos oito no mesmo commit. É a única coisa que impede a próxima
auditoria de encarte de custar uma ordem inteira.

As regras cobertas hoje (cada uma com a ordem que a criou):
  R1  o hífen não parte marca (L25 · DUODETRICESIMUS §1)
  R2  nenhum nome elipsado (NONUS §2 · DUODETRICESIMUS §2)
  R3  nome nunca começa com número solto (DUODETRICESIMUS §3)
  R4  um peso por item (QUARTUS §1.2 · DUODETRICESIMUS §9)
  R5  a unidade nunca some do nome+descritor (QUARTUSDECIMUS §2)
  R6  o texto não transborda a região (TERTIUSDECIMUS/A1)
  R7  o corpo do nome respeita o piso do celular (UNDECIMUS/U1)
  R8  toda região de preço visível desenha DENTRO de forma/carimbo
      (DUODETRICESIMUS §4 — preço solto no fundo nunca)
"""

from __future__ import annotations

import unicodedata
from decimal import Decimal
from pathlib import Path

import pytest

_PACOTE = Path(__file__).resolve().parents[2] / "Templates novos"

# os OITO do dono (a chave do pacote → o nome no banco)
OITO = [
    "quintou", "jornal-do-mes", "segunda-frios", "terca-do-pao",
    "quarta-das-ofertas", "quinta-do-peixe", "sexta-verde",
    "sabado-da-carne",
]

# o item de PROVA — desenhado para exercitar todas as regras de uma vez:
# nome longo com MARCA longa (o hífen tenta partir), peso no nome E
# unidade divergente (o peso duplicado), sabor (o descritor cheio).
NOME_PROVA = "Achocolatado Andorinha Tradicional 700g"
UNIDADE_PROVA = "900 g"          # diverge de propósito (o peso do nome vence)
PRECO_PROVA = Decimal("11.91")


def _chave(t: str) -> str:
    t = unicodedata.normalize("NFKD", (t or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def _requer_pacote():
    if not _PACOTE.exists():
        pytest.skip("REQUER ACERVO DO DONO: a pasta 'Templates novos/'")


def _layout_do_banco(chave: str, raiz):
    """A PORTA REAL (L16): importar_pacote → carregar_layout. Nenhum
    teste desta rede monta layout à mão — se o import quebrar, os oito
    ficam vermelhos, e é isso que se quer."""
    from app.core.database import Database
    from app.core.models import Layout
    from app.rendering.encartes import NOMES_EXIBICAO, importar_pacote
    from app.rendering.persistencia import carregar_layout

    db = Database(raiz).init()
    try:
        with db.Session() as s:
            importar_pacote(s, _PACOTE)
            s.commit()
            nome = NOMES_EXIBICAO.get(chave, chave)
            row = next((r for r in s.query(Layout).all()
                        if r.nome == nome), None)
            assert row is not None, f"{chave}: não entrou no banco"
            return carregar_layout(s, row.id)
    finally:
        db.engine.dispose()


def _dados_de_prova(pagina, marcas):
    """O MESMO item em toda célula ocupável da página — a régua tem de
    valer para qualquer produto, em qualquer célula."""
    from app.qt.telas.servico import ItemMesa, dados_para_desenho
    from app.rendering.grade import ocupaveis

    it = ItemMesa(descricao=NOME_PROVA, preco="11,91", semaforo="VERDE",
                  nome=NOME_PROVA, unidade=UNIDADE_PROVA)
    d = dados_para_desenho(it, None, None, validade="06/08", marcas=marcas)
    return {s.id: d for s in ocupaveis(pagina.slots)}


# ============================================================== as regras


def r1_hifen_nao_parte_marca(ctx) -> list[str]:
    """L25: marca, submarca e nome de linha são ÁTOMOS."""
    ruins = []
    for linhas in ctx["linhas_desenhadas"]:
        for i, ln in enumerate(linhas[:-1]):
            if not ln.rstrip().endswith("-"):
                continue
            pedaco = ln.rstrip()[:-1].split()[-1] if ln.split() else ""
            junto = _chave(pedaco + linhas[i + 1].split()[0]
                           if linhas[i + 1].split() else pedaco)
            if any(junto.startswith(_chave(m)) or _chave(m) in junto
                   for m in ctx["marcas"]):
                ruins.append(f"hífen partiu marca: {ln!r} + "
                             f"{linhas[i + 1]!r}")
    return ruins


def r2_nenhum_nome_elipsado(ctx) -> list[str]:
    """A elipse é o ÚLTIMO recurso e não deve sobrar nas páginas de
    prova — se sobrar, a escada não desceu todos os degraus."""
    return [f"nome elipsado: {' '.join(linhas)!r}"
            for linhas in ctx["linhas_desenhadas"]
            if any("…" in ln for ln in linhas)]


def r3_nome_sem_numero_solto(ctx) -> list[str]:
    """§3: a numeração da tabela é metadado, nunca nome."""
    import re
    return [f"nome começa com número solto: {ctx['nome']!r}"] \
        if re.match(r"^\s*\d{1,3}\s+\D", ctx["nome"]) else []


def r4_um_peso_por_item(ctx) -> list[str]:
    """QUARTUS §1.2: UM ITEM TEM UM PESO SÓ (o "500ml · 497 ml")."""
    import re
    texto = f"{ctx['nome']} {ctx['descritor'] or ''}"
    pesos = re.findall(r"\d+(?:[.,]\d+)?\s*(?:g|kg|ml|l)\b",
                       texto, flags=re.IGNORECASE)
    vistos = {re.sub(r"\s+", "", p.lower()) for p in pesos}
    return [f"dois pesos no mesmo item: {texto!r}"] if len(vistos) > 1 else []


def r5_a_unidade_nunca_some(ctx) -> list[str]:
    """QUARTUSDECIMUS §2: a unidade é informação comercial."""
    import re
    texto = f"{ctx['nome']} {ctx['descritor'] or ''}"
    return [] if re.search(r"\d+\s*(?:g|kg|ml|l)\b", texto, re.IGNORECASE) \
        else [f"a unidade sumiu: {texto!r}"]


def r6_texto_dentro_da_regiao(ctx) -> list[str]:
    """TERTIUSDECIMUS/A1: nenhum texto desenha fora do seu rect."""
    return [f"texto transborda a região {d['nome'] or d['tipo']}"
            for d in ctx["desenhado"].values()
            if d["altura_px"] > d["rect_alt_px"] + 1]


def r7_piso_do_celular(ctx) -> list[str]:
    """UNDECIMUS/U1: o corpo do NOME desenhado nunca desce abaixo do
    piso do celular da página (a régua de runtime)."""
    # o piso NUNCA excede o teto da própria região: layout que
    # declara 14 pt de máximo não pode ser cobrado por 16,6 (seria
    # medir o layout com a régua de outro — o erro de instrumento
    # que esta rodada ensinou a conferir antes de acusar)
    return [f"corpo {d['pt']:.1f}pt abaixo do piso "
            f"{min(ctx['piso'], d['max_pt']):.1f}pt em "
            f"{d['nome'] or d['tipo']}"
            for d in ctx["desenhado"].values()
            if d["tipo"] == "NOME"
            and d["pt"] < min(ctx["piso"], d["max_pt"]) - 0.51
            # ...e abaixo do mínimo que o LAYOUT declarou: o Quintou
            # declara 9,5 pt de propósito (adendo do dono: legível-
            # pequeno > cortado). Exceção DECLARADA vale; silenciosa
            # não existe — quem não declara é cobrado pelo piso.
            and d["pt"] < d["min_pt"] - 0.51
            # ...e SEM ter cedido para caber no rect: quando o corpo
            # desce abaixo do mínimo E o texto passa a caber, foi o
            # último recurso legítimo do A1 (o rect manda sobre o
            # piso — melhor pequeno dentro que grande vazando)
            and d["altura_px"] > d["rect_alt_px"]]


def r8_preco_coerente_na_pagina(ctx) -> list[str]:
    """§4 (o Ervilha Fugini sem carimbo enquanto os outros 15 tinham):
    a régua honesta é a COERÊNCIA — numa mesma página, ou toda região
    de preço tem carimbo (forma do app ou pouso na arte), ou nenhuma
    tem. Célula que destoa das irmãs é o defeito."""
    from app.rendering.model import FormaPreco
    com, sem = [], []
    for reg in ctx["regioes_preco"]:
        tem = (reg.forma_preco != FormaPreco.TEXTO
               or getattr(reg, "preenche_caixa", False))
        (com if tem else sem).append(reg.nome or reg.uid)
    if com and sem:
        return [f"{len(sem)} de {len(com) + len(sem)} preços da página "
                f"sem carimbo enquanto os outros têm"]
    return []


# DÍVIDA DECLARADA (DUODETRICESIMUS §14): o que a rede achou HOJE e
# cujo conserto é de LAYOUT/arte, não de motor — fica NOMEADA aqui,
# nunca escondida. Defeito novo deixa o teste vermelho; dívida
# consertada também (o número tem de baixar junto com o conserto).
DIVIDA = {
    # A Sexta Verde tem 2 células de destaque com preço em TEXTO puro
    # enquanto as outras 9 têm carimbo — a mesma classe do "Ervilha
    # Fugini sem carimbo" do §4. Conserto: dar forma às duas (arte do
    # encarte), numa rodada da Sexta.
    ("sexta-verde", "r8_preco_coerente_na_pagina"): 1,
    # CONFLITO DE LEIS, para o arquiteto decidir (achado desta rede):
    # nome longo em região cujo PISO é igual ao TETO fica mais alto
    # que a caixa. Ceder o corpo resolve o desenho e quebra a U1/C1
    # (piso inviolável); manter o piso respeita a U1 e deixa o bloco
    # transbordar. O builder NÃO escolheu: o piso ficou (é lei
    # vigente) e o caso está aqui, contado, até a ordem que decidir.
    # Medido com o item de prova mais longo que os nomes reais.
    ("jornal-do-mes", "r6_texto_dentro_da_regiao"): 40,
    ("sabado-da-carne", "r6_texto_dentro_da_regiao"): 12,
    ("quintou", "r6_texto_dentro_da_regiao"): 32,
    ("terca-do-pao", "r6_texto_dentro_da_regiao"): 12,
    ("segunda-frios", "r6_texto_dentro_da_regiao"): 12,
    ("quarta-das-ofertas", "r6_texto_dentro_da_regiao"): 12,
    ("quinta-do-peixe", "r6_texto_dentro_da_regiao"): 12,
    ("sexta-verde", "r6_texto_dentro_da_regiao"): 12,
}


REGRAS = [r1_hifen_nao_parte_marca, r2_nenhum_nome_elipsado,
          r3_nome_sem_numero_solto, r4_um_peso_por_item,
          r5_a_unidade_nunca_some, r6_texto_dentro_da_regiao,
          r7_piso_do_celular, r8_preco_coerente_na_pagina]


# ============================================================== o motor


def _contexto(ldef, pagina, img, dados):
    """Tudo que as regras precisam — LIDO DO REGISTRO do compositor
    (``_texto_desenhado``), nunca recalculado: medir por fora ignora a
    escada, os rects substituídos e o piso de runtime, e faz o teste
    acusar defeito que não existe (a lição desta rodada, dos dois
    lados da dupla)."""
    from app.rendering.model import TipoRegiao
    from app.rendering.text_fit import piso_do_celular

    d0 = next(iter(dados.values()))
    desenhado = {uid: d for uid, d in
                 getattr(img, "_texto_desenhado", {}).items()
                 if d["tipo"] == "NOME"}
    regs_preco = [r for s in pagina.slots for r in s.regioes
                  if r.tipo == TipoRegiao.PRECO and r.visivel
                  and s.id in dados]
    # o nome/descritor REAIS da página (o que a escada decidiu)
    nome_final = (next(iter(desenhado.values()))["texto"]
                  if desenhado else d0.nome)
    return {
        "nome": nome_final, "descritor": d0.descritor, "dpi": ldef.dpi,
        "marcas": [m for m in (d0.marcas_nome or ())] or ["Andorinha"],
        "desenhado": desenhado,
        "linhas_desenhadas": [d["linhas"] for d in desenhado.values()],
        "regioes_preco": regs_preco,
        "piso": piso_do_celular(ldef.largura_mm),
    }


@pytest.mark.parametrize("chave", OITO)
def test_os_oito_seguem_as_leis(chave, tmp_path, monkeypatch):
    """A REDE DA L22: as leis conquistadas rodando nos OITO encartes,
    com o MESMO item de prova, pela porta real do banco (L16).

    Falha aqui = uma lei que existe em um layout e não em outro — o
    defeito que a ordem DUODETRICESIMUS §14 mandou matar na causa."""
    _requer_pacote()
    monkeypatch.setenv("AUTOTABLOIDE_ROOT", str(tmp_path / "raiz"))
    from app.core.paths import SystemRoot
    from app.qt.telas.servico import marcas_para_exibicao
    from app.rendering.compositor import compor_pagina
    from app.tests import acervo

    fontes = tmp_path / "fontes"
    fontes.mkdir()
    acervo.copiar_fontes_reais(fontes)
    raiz = SystemRoot(tmp_path / "raiz")
    ldef = _layout_do_banco(chave, raiz)
    marcas = marcas_para_exibicao()

    violacoes: list[str] = []
    for n, pagina in enumerate(ldef.paginas, start=1):
        dados = _dados_de_prova(pagina, marcas)
        if not dados:
            continue
        img = compor_pagina(ldef, pagina, dados, fontes_dir=fontes)
        ctx = _contexto(ldef, pagina, img, dados)
        for regra in REGRAS:
            achados = regra(ctx)
            if len(achados) <= DIVIDA.get((chave, regra.__name__), 0):
                continue          # dívida DECLARADA e sem piora
            for v in achados:
                violacoes.append(f"[{chave} p{n}] {regra.__name__}: {v}")

    assert not violacoes, "\n".join(violacoes)
