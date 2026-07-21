"""Modelos de célula (R-048/R-044, Fase 5 — Bloco C).

Um "modelo de célula" é um TRIO pronto (imagem + nome + preço, com estilos e
posições RELATIVAS) que se carimba em qualquer arte/slot: os campos entram
com o estilo salvo; o CONTEÚDO vem do item daquele slot.

Regras travadas:
- **Só estrutura + estilo**, nunca conteúdo de produto (as regiões não guardam
  texto do item — ele vem do ``DadosProduto`` na composição).
- **Posições relativas** ao retângulo do modelo (I3: portável, sem mm absoluto
  nem caminho de disco). Carimbar escala para a caixa-alvo.
- Cada região carimbada nasce com **uid novo** (I1: identidade fresca, nunca
  herda vínculo de grupo).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from app.rendering.model import (
    Ajuste, Alinhamento, PapelPreco, Regiao, Retangulo, TipoRegiao,
)

# atributos de vínculo/identidade que NÃO viajam no modelo (nascem frescos)
_NAO_VIAJAM = ("uid", "ref_mestre", "de_mestre", "overrides",
               "estilo", "overrides_estilo")


@dataclass
class ModeloCelula:
    nome: str
    larg_ref_mm: float = 1.0
    alt_ref_mm: float = 1.0
    regioes: list[dict] = field(default_factory=list)   # to_dict()+rect_frac

    def to_dict(self) -> dict:
        return {"nome": self.nome, "larg_ref_mm": self.larg_ref_mm,
                "alt_ref_mm": self.alt_ref_mm, "regioes": self.regioes}

    @classmethod
    def from_dict(cls, d: dict) -> "ModeloCelula":
        return cls(nome=d["nome"], larg_ref_mm=d.get("larg_ref_mm", 1.0),
                   alt_ref_mm=d.get("alt_ref_mm", 1.0),
                   regioes=list(d.get("regioes", [])))


def capturar_modelo(nome: str, regioes: list[Regiao]) -> ModeloCelula:
    """Captura as regiões dadas como um modelo — rects RELATIVOS ao retângulo
    que as contém, sem os campos de vínculo/identidade."""
    if not regioes:
        return ModeloCelula(nome)
    minx = min(r.rect.x_mm for r in regioes)
    miny = min(r.rect.y_mm for r in regioes)
    w = max(r.rect.x_mm + r.rect.larg_mm for r in regioes) - minx or 1.0
    h = max(r.rect.y_mm + r.rect.alt_mm for r in regioes) - miny or 1.0
    regs: list[dict] = []
    for r in regioes:
        d = r.to_dict()
        d["rect_frac"] = [(r.rect.x_mm - minx) / w, (r.rect.y_mm - miny) / h,
                          r.rect.larg_mm / w, r.rect.alt_mm / h]
        for k in _NAO_VIAJAM:
            d.pop(k, None)
        regs.append(d)
    return ModeloCelula(nome, w, h, regs)


def carimbar_modelo(modelo: ModeloCelula, x_mm: float, y_mm: float,
                    larg_mm: float, alt_mm: float) -> list[Regiao]:
    """Instancia o modelo na caixa-alvo (posição + tamanho em mm). Cada região
    nasce com uid novo (I1) e o rect escalado da fração salva."""
    regs: list[Regiao] = []
    for rd in modelo.regioes:
        fx, fy, fw, fh = rd.get("rect_frac", [0.0, 0.0, 1.0, 1.0])
        d = {k: v for k, v in rd.items() if k not in ("rect_frac",) + _NAO_VIAJAM}
        d["rect"] = {"x_mm": x_mm + fx * larg_mm, "y_mm": y_mm + fy * alt_mm,
                     "larg_mm": fw * larg_mm, "alt_mm": fh * alt_mm}
        regs.append(Regiao.from_dict(d))   # from_dict gera uid fresco (I1)
    return regs


# --- persistência JSON portável (I3) ---------------------------------------

def _dir():
    from app.core.paths import SystemRoot
    d = SystemRoot().subpasta("modelos_celula")
    d.mkdir(parents=True, exist_ok=True)
    return d


def salvar_modelo(modelo: ModeloCelula) -> None:
    (_dir() / f"{modelo.nome}.json").write_text(
        json.dumps(modelo.to_dict(), ensure_ascii=False, indent=1),
        encoding="utf-8")


def listar_modelos() -> list[str]:
    return sorted(p.stem for p in _dir().glob("*.json"))


def carregar_modelo(nome: str) -> ModeloCelula | None:
    p = _dir() / f"{nome}.json"
    if not p.exists():
        return None
    return ModeloCelula.from_dict(json.loads(p.read_text(encoding="utf-8")))


def excluir_modelo(nome: str) -> None:
    (_dir() / f"{nome}.json").unlink(missing_ok=True)


def renomear_modelo(velho: str, novo: str) -> None:
    m = carregar_modelo(velho)
    if m is None:
        return
    m.nome = novo
    salvar_modelo(m)
    excluir_modelo(velho)


# --- R-044: vitrine/herói de fábrica (é um modelo de célula especial) -------

def modelo_vitrine() -> ModeloCelula:
    """Célula de destaque pronta: foto grande, nome com pílula, preço gigante
    com contorno. Proporções de herói (reusa R-048)."""
    img = Regiao(TipoRegiao.IMAGEM, Retangulo(0, 0, 100, 60),
                 ajuste=Ajuste.PREENCHER, nome="Foto")
    nome = Regiao(TipoRegiao.NOME, Retangulo(2, 62, 96, 15), nome="Nome",
                  alinhamento=Alinhamento.CENTRO, tamanho_max_pt=30,
                  cor="#ffffff", pill=True, pill_cor="#111111",
                  pill_opacidade=205)
    preco = Regiao(TipoRegiao.PRECO, Retangulo(2, 79, 96, 21), nome="Preço",
                   alinhamento=Alinhamento.CENTRO, tamanho_max_pt=66,
                   papel_preco=PapelPreco.UNICO, cor="#ffffff",
                   contorno=True, cor_efeito="#000000")
    return capturar_modelo("Vitrine (herói)", [img, nome, preco])
