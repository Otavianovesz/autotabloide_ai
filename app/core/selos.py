"""
Gestor de selos — o serviço sobre a entidade ``Selo`` (FASE 3, Bloco G)
=======================================================================
RG-33 completo: os selos deixam de viver na chave Config
``selos.personalizados`` e viram linhas da tabela ``selos`` — automáticos
(+18, Qualidade BB, com regra por flag do produto) e manuais (arte do dono,
escolhidos por item na Mesa).

Leis:
- o **+18 automático em bebida alcoólica é decisão TRAVADA** — a linha não
  desativa (``excluir_selo``/``definir_ativo`` recusam) e a composição o
  desenha SEMPRE que a flag vier;
- selo é DECORATIVO (lei da casa): nada aqui cria slot/região — o teste
  do passo 77 prova.
"""

from __future__ import annotations

from app.core.models import Selo

# nomes dos automáticos semeados (a composição os referencia por regra)
NOME_MAIS18 = "+18"
NOME_QUALIDADE = "Qualidade Belo Brasil"
REGRA_MAIS18 = "bebida_alcoolica"
REGRA_QUALIDADE = "marca_propria"

CANTOS = ("SUPERIOR_ESQUERDO", "SUPERIOR_DIREITO",
          "INFERIOR_ESQUERDO", "INFERIOR_DIREITO")


def migrar_selos(s) -> int:
    """Passo 64: semeia os 2 automáticos e importa os manuais da Config
    legada (``selos.personalizados``). Idempotente — roda quantas vezes
    for; devolve quantas linhas criou."""
    existentes = {x.nome.strip().lower() for x in s.query(Selo).all()}
    regras_presentes = {x.regra for x in s.query(Selo).all() if x.regra}
    criados = 0
    if REGRA_MAIS18 not in regras_presentes:
        s.add(Selo(nome=NOME_MAIS18, tipo="automatico", regra=REGRA_MAIS18,
                   canto="SUPERIOR_ESQUERDO"))
        criados += 1
    if REGRA_QUALIDADE not in regras_presentes:
        s.add(Selo(nome=NOME_QUALIDADE, tipo="automatico",
                   regra=REGRA_QUALIDADE, canto="SUPERIOR_DIREITO"))
        criados += 1
    # manuais da Config legada (a chave fica lá, intocada — só importamos)
    from app.core.repositories import ConfigRepositorio
    for v in (ConfigRepositorio(s).get("selos.personalizados") or []):
        if not (isinstance(v, dict) and v.get("nome")):
            continue
        if str(v["nome"]).strip().lower() in existentes:
            continue
        s.add(Selo(nome=str(v["nome"]).strip(), tipo="manual",
                   arquivo=v.get("arquivo"),
                   canto=v.get("canto") or "SUPERIOR_DIREITO"))
        existentes.add(str(v["nome"]).strip().lower())
        criados += 1
    s.flush()
    return criados


def listar_selos(s, apenas_ativos: bool = False) -> list[Selo]:
    # ordem de INSERÇÃO dentro do tipo (como o gestor antigo listava)
    q = s.query(Selo).order_by(Selo.tipo, Selo.id)
    if apenas_ativos:
        q = q.filter(Selo.ativo.is_(True))
    return list(q.all())


def criar_manual(s, nome: str, arquivo_rel: str,
                 canto: str = "SUPERIOR_DIREITO") -> Selo:
    selo = Selo(nome=nome.strip(), tipo="manual", arquivo=arquivo_rel,
                canto=canto if canto in CANTOS else "SUPERIOR_DIREITO")
    s.add(selo)
    s.flush()
    return selo


def editar_selo(s, selo_id: int, *, nome=None, canto=None,
                arquivo=None, regra=None) -> None:
    selo = s.get(Selo, selo_id)
    if selo is None:
        return
    if nome is not None and nome.strip():
        selo.nome = nome.strip()
    if canto is not None and canto in CANTOS:
        selo.canto = canto
    if arquivo is not None:
        selo.arquivo = arquivo or None
    if regra is not None and selo.tipo == "automatico":
        if selo.regra == REGRA_MAIS18:
            return                  # a regra do +18 é travada
        selo.regra = regra or None


def definir_ativo(s, selo_id: int, ativo: bool) -> bool:
    """Liga/desliga. Devolve False (recusa) para o +18 — decisão travada."""
    selo = s.get(Selo, selo_id)
    if selo is None:
        return False
    if selo.regra == REGRA_MAIS18 and not ativo:
        return False
    selo.ativo = bool(ativo)
    return True


def excluir_selo(s, selo_id: int) -> bool:
    """Manual: apaga a linha (a ARTE fica em selos/ — projeto congelado
    não quebra). Automático: só DESATIVA (o conceito não some — passo 66).
    +18: recusa (travado)."""
    selo = s.get(Selo, selo_id)
    if selo is None:
        return False
    if selo.tipo == "automatico":
        return definir_ativo(s, selo_id, False)
    s.delete(selo)
    return True


def config_automaticos(raiz=None) -> dict:
    """O que a COMPOSIÇÃO precisa saber dos automáticos, com defaults sãos
    (C3): {"MAIS18": {ativo, canto, arquivo_abs}, "QUALIDADE": {...}}.
    O +18 volta SEMPRE ativo (travado), aconteça o que acontecer no banco."""
    saida = {"MAIS18": {"ativo": True, "canto": "SUPERIOR_ESQUERDO",
                        "arquivo": None},
             "QUALIDADE": {"ativo": True, "canto": "SUPERIOR_DIREITO",
                           "arquivo": None}}
    try:
        from app.core.database import Database
        from app.core.paths import SystemRoot
        db = Database(raiz) if raiz is not None else Database()
        db.init()
        try:
            with db.Session() as s:
                for selo in s.query(Selo).filter(Selo.regra.isnot(None)):
                    chave = ("MAIS18" if selo.regra == REGRA_MAIS18 else
                             "QUALIDADE" if selo.regra == REGRA_QUALIDADE
                             else None)
                    if chave is None:
                        continue
                    arq = None
                    if selo.arquivo:
                        cand = SystemRoot().selos / selo.arquivo
                        arq = str(cand) if cand.exists() else None
                    saida[chave] = {
                        "ativo": True if chave == "MAIS18" else bool(selo.ativo),
                        "canto": selo.canto or saida[chave]["canto"],
                        "arquivo": arq,
                    }
        finally:
            db.engine.dispose()
    except Exception:
        pass                        # sem banco (teste puro) = clássico
    return saida
