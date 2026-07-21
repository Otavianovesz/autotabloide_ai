"""Perfis de exportação (R-065, Fase 8 — Bloco A).

O dono não pensa em pixel nem dpi — escolhe "WhatsApp" ou "Impressão" e manda.
O perfil cuida do número: redimensiona a peça já composta (proporcional, SEM
deformar) e grava no formato/dpi certo. Reusa `export.py` (o mesmo pipeline
medido em bytes das fases anteriores); só decide o tamanho de saída.

Decisão: o perfil age SOBRE a Image final (depois do compositor), não muda o
compositor — uma cadeia só. Perfis editáveis vivem na Config (`export.perfis`);
os padrões moram aqui (como as marcas próprias).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image

from app.rendering.export import exportar_pdf, exportar_png


@dataclass
class Perfil:
    """Um preset de exportação. `lado_maior_px` escala proporcional (o maior
    lado vira N); `largura_px`+`altura_px` encaixam no tamanho exato (contain +
    fundo, sem esticar); nenhum dos dois = mantém o tamanho nativo (impressão)."""
    nome: str
    formato: str = "PNG"          # PNG | PDF | JPG
    lado_maior_px: int | None = None
    largura_px: int | None = None
    altura_px: int | None = None
    dpi: int = 300
    qualidade: int = 90           # JPG/compressão (compressão sã do WhatsApp)
    fundo: str = "#FFFFFF"        # cor do letterbox quando encaixa exato

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Perfil":
        from dataclasses import fields
        chaves = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in chaves})


# Os 3 presets prontos (passo 1-4). Impressão mantém o tamanho físico em 300 dpi;
# WhatsApp otimiza p/ enviar rápido; Stories já sai no 1080×1920 vertical.
PERFIS_PADRAO: list[Perfil] = [
    Perfil("WhatsApp (1080)", "JPG", lado_maior_px=1080, dpi=96, qualidade=85),
    Perfil("Impressão (300 dpi)", "PDF", dpi=300),
    Perfil("Stories (1080×1920)", "PNG", largura_px=1080, altura_px=1920, dpi=96),
]

_EXT = {"PNG": ".png", "PDF": ".pdf", "JPG": ".jpg"}


def perfis_configurados() -> list[Perfil]:
    """Os perfis do dono (Config `export.perfis`) ou os padrões. Degrada para o
    padrão se a Config estiver vazia/inválida (nunca fica sem perfil)."""
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                bruto = ConfigRepositorio(s).get("export.perfis")
        finally:
            db.engine.dispose()
        if bruto:
            perfis = [Perfil.from_dict(d) for d in bruto]
            if perfis:
                return perfis
    except Exception:
        pass
    return [Perfil(**asdict(p)) for p in PERFIS_PADRAO]


def salvar_perfis(perfis: list[Perfil]) -> None:
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio
    db = Database().init()
    try:
        with db.Session() as s:
            ConfigRepositorio(s).set("export.perfis", [p.to_dict() for p in perfis])
            s.commit()
    finally:
        db.engine.dispose()


def aplicar_perfil(img: Image.Image, perfil: Perfil) -> tuple[Image.Image, int]:
    """Redimensiona a peça conforme o perfil (SEM deformar) e devolve
    (img_saida, dpi). Encaixe exato usa contain + letterbox (fundo); escala
    proporcional respeita a proporção; nenhum = a img como veio."""
    if perfil.largura_px and perfil.altura_px:
        alvo = (int(perfil.largura_px), int(perfil.altura_px))
        esc = min(alvo[0] / img.width, alvo[1] / img.height)
        nw, nh = max(1, round(img.width * esc)), max(1, round(img.height * esc))
        redim = img.convert("RGB").resize((nw, nh), Image.LANCZOS)
        tela = Image.new("RGB", alvo, perfil.fundo)
        tela.paste(redim, ((alvo[0] - nw) // 2, (alvo[1] - nh) // 2))
        return tela, perfil.dpi
    if perfil.lado_maior_px:
        maior = max(img.width, img.height)
        esc = int(perfil.lado_maior_px) / maior
        nw, nh = max(1, round(img.width * esc)), max(1, round(img.height * esc))
        return img.convert("RGB").resize((nw, nh), Image.LANCZOS), perfil.dpi
    return img, perfil.dpi


def exportar_com_perfil(img: Image.Image, caminho_sem_ext: str | Path,
                        perfil: Perfil) -> Path:
    """Aplica o perfil e grava no formato certo. A extensão vem do perfil (o dono
    não precisa saber). Devolve o caminho final."""
    saida, dpi = aplicar_perfil(img, perfil)
    base = Path(caminho_sem_ext)
    destino = base.with_suffix(_EXT.get(perfil.formato, ".png"))
    if perfil.formato == "PDF":
        return exportar_pdf(saida, destino, dpi)
    if perfil.formato == "JPG":
        destino.parent.mkdir(parents=True, exist_ok=True)
        saida.convert("RGB").save(str(destino), "JPEG",
                                  quality=int(perfil.qualidade),
                                  dpi=(dpi, dpi), optimize=True)
        return destino
    return exportar_png(saida, destino, dpi)
