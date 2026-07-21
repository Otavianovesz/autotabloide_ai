"""
Estilos de texto nomeados (F5.7) — reutilizáveis, com override por instância
============================================================================
Doc-mestre §6.5: o usuário define estilos ("Estilo Nome", "Estilo Preço…");
**trocar o estilo muda em todos os lugares que o usam**; MAS uma instância
pode ser sobrescrita sem afetar as outras.

Semântica idêntica à da célula-mestre (o padrão de precedência do app):
estilo → região é como mestra → cópia. ``Regiao.overrides_estilo`` guarda os
atributos ajustados na instância; a re-aplicação do estilo respeita-os.

Matriz grade-override × estilo-override (E-A4 do Bloco E — o contrato que
os testes ``test_estilos.py`` exercitam, agora normativo aqui):

- São DOIS conjuntos independentes na ``Regiao``: ``overrides`` (o ajuste
  local que vence a MESTRA da grade) e ``overrides_estilo`` (o ajuste local
  que vence o ESTILO nomeado). Limpar um NUNCA limpa o outro.
- Editar fonte/tamanho/cor numa região que é DERIVADA **e** tem estilo marca
  o atributo NOS DOIS conjuntos de uma vez (painel → ``overrides_estilo``;
  canvas ``_apos_edicao`` → ``overrides``): nem a propagação da mestra nem a
  re-aplicação do estilo sobrescrevem o ajuste do humano.
- ``propagar_mestre`` copia da mestra os ``ATRIBUTOS_ESTILO`` — o VÍNCULO
  ``estilo`` incluso — exceto os marcados em ``overrides``;
  ``overrides_estilo`` NÃO propaga (é da instância).
- ``definir_estilo`` (mudar o conjunto) re-aplica no layout inteiro
  respeitando ``overrides_estilo`` de cada região.
- "Restaurar da mestra" limpa só ``overrides`` (volta a seguir a grade);
  "Restaurar" do estilo limpa só ``overrides_estilo`` e re-aplica o conjunto.
- Precedência final de um atributo de texto numa derivada com estilo:
  ajuste local > estilo da região > o que a mestra propagou.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.rendering.model import LayoutDef, Regiao

# O que um estilo de TEXTO governa (alinhamento/quebra são do layout, não do estilo)
ATRIBUTOS_DE_ESTILO = ("fonte", "tamanho_max_pt", "cor")

# R-031 (Fase 5): o que o CONTA-GOTAS replica — tipografia + legibilidade.
# NUNCA geometria (rect, rotacao) nem conteúdo (tipo, papel, texto_fixo,
# subtipo, incluir_unidade…): copiar estilo não move nem troca o item.
ATRIBUTOS_CONTA_GOTAS = (
    "fonte", "tamanho_max_pt", "tamanho_min_pt", "cor", "alinhamento",
    "pill", "pill_cor", "pill_opacidade", "sombra", "contorno", "cor_efeito",
)


@dataclass
class EstiloTexto:
    nome: str
    fonte: str = "Roboto-Regular.ttf"
    tamanho_max_pt: float = 48.0
    cor: str = "#000000"

    def to_dict(self) -> dict:
        return {"nome": self.nome, "fonte": self.fonte,
                "tamanho_max_pt": self.tamanho_max_pt, "cor": self.cor}

    @classmethod
    def from_dict(cls, d: dict) -> "EstiloTexto":
        return cls(nome=d["nome"], fonte=d.get("fonte", "Roboto-Regular.ttf"),
                   tamanho_max_pt=d.get("tamanho_max_pt", 48.0),
                   cor=d.get("cor", "#000000"))


def estilos_do_layout(layout: LayoutDef) -> dict[str, EstiloTexto]:
    return {nome: EstiloTexto.from_dict(d) for nome, d in layout.estilos.items()}


def _regioes_do_layout(layout: LayoutDef):
    for pagina in layout.paginas:
        for slot in pagina.slots:
            yield from slot.regioes


def aplicar_estilo(regiao: Regiao, estilo: EstiloTexto,
                   *, respeitar_overrides: bool = True) -> None:
    """Aplica o estilo à região. Com ``respeitar_overrides``, os atributos
    ajustados na instância (``overrides_estilo``) NÃO são tocados; sem, a
    aplicação é limpa (vincular pela primeira vez zera os ajustes locais)."""
    regiao.estilo = estilo.nome
    if not respeitar_overrides:
        regiao.overrides_estilo = set()
    for attr in ATRIBUTOS_DE_ESTILO:
        if respeitar_overrides and attr in regiao.overrides_estilo:
            continue
        setattr(regiao, attr, getattr(estilo, attr))


def copiar_estilo_visual(origem: Regiao, destino: Regiao) -> int:
    """R-031 (conta-gotas): copia SÓ o estilo visual (tipografia+legibilidade)
    de ``origem`` para ``destino`` — nunca geometria nem conteúdo. Se o destino
    segue um estilo NOMEADO (F5.7), marca os atributos de tipografia como
    override da instância, para o cole não ser revertido na próxima
    ``reaplicar_estilos`` (mesma regra do painel). Devolve quantos mudaram."""
    n = 0
    for attr in ATRIBUTOS_CONTA_GOTAS:
        val = getattr(origem, attr)
        if getattr(destino, attr) != val:
            setattr(destino, attr, val)
            n += 1
        if destino.estilo and attr in ATRIBUTOS_DE_ESTILO:
            destino.overrides_estilo.add(attr)
    return n


def reaplicar_estilos(layout: LayoutDef) -> int:
    """Re-aplica TODOS os estilos nomeados às regiões vinculadas (respeitando
    os overrides por instância). Devolve quantas regiões foram tocadas."""
    estilos = estilos_do_layout(layout)
    n = 0
    for reg in _regioes_do_layout(layout):
        if reg.estilo and reg.estilo in estilos:
            aplicar_estilo(reg, estilos[reg.estilo])
            n += 1
    return n


def definir_estilo(layout: LayoutDef, estilo: EstiloTexto) -> int:
    """Cria/atualiza o estilo e **re-aplica em todo o layout** (a regra da
    doc: mudar o estilo muda o conjunto; overrides de instância prevalecem)."""
    layout.estilos[estilo.nome] = estilo.to_dict()
    return reaplicar_estilos(layout)


def estilo_da_regiao(regiao: Regiao, nome: str) -> EstiloTexto:
    """Captura a tipografia atual da região como um estilo nomeado."""
    return EstiloTexto(nome=nome, fonte=regiao.fonte,
                       tamanho_max_pt=regiao.tamanho_max_pt, cor=regiao.cor)


def excluir_estilo(layout: LayoutDef, nome: str) -> int:
    """Remove o estilo; as regiões MANTÊM os valores atuais e ficam soltas
    (``estilo=None``) — nada muda visualmente ao excluir. Devolve o nº delas."""
    layout.estilos.pop(nome, None)
    n = 0
    for reg in _regioes_do_layout(layout):
        if reg.estilo == nome:
            reg.estilo = None
            reg.overrides_estilo = set()
            n += 1
    return n


def desvincular(regiao: Regiao) -> None:
    """Solta a região do estilo mantendo a aparência atual."""
    regiao.estilo = None
    regiao.overrides_estilo = set()


def restaurar_do_estilo(layout: LayoutDef, regiao: Regiao) -> bool:
    """Descarta os ajustes da instância: volta a seguir o estilo por inteiro."""
    estilos = estilos_do_layout(layout)
    if not regiao.estilo or regiao.estilo not in estilos:
        return False
    aplicar_estilo(regiao, estilos[regiao.estilo], respeitar_overrides=False)
    return True
