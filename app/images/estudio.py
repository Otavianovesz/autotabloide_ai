"""Estúdio IA — foto de celular → packshot bonito (R-091/RG-46, Fase 10).

DECISÃO TRAVADA (o coração da fase):
- **DEGRAU 1 (SEM IA generativa)** é o PADRÃO GARANTIDO: rembg (birefnet-general)
  + normalização de luz + sombra sintética + enquadramento. Roda em CPU, em
  QUALQUER PC, sem GPU. Resolve ~80% e é o mínimo garantido (I2).
- **DEGRAU 2 (img2img local, SDXL)** é OPÇÃO condicionada à GPU, NUNCA requisito.
  Sem GPU/modelo, degrada COM aviso honesto — o degrau 1 já entregou o packshot.
  Denoise baixo preserva o PRODUTO (não inventa outro); guarda anti-alucinação.

Não-destrutivo: o packshot entra como VERSÃO NOVA da foto (a original preservada,
via `BibliotecaImagens`) — I1.
"""

from __future__ import annotations

from PIL import Image, ImageFilter, ImageOps


def _normalizar_luz(rgba: Image.Image) -> Image.Image:
    """Corrige exposição/branco do PRODUTO (autocontrast no RGB, alfa intacto) —
    "de vitrine" sem IA generativa."""
    r, g, b, a = rgba.split()
    rgb = ImageOps.autocontrast(Image.merge("RGB", (r, g, b)), cutoff=1)
    r2, g2, b2 = rgb.split()
    return Image.merge("RGBA", (r2, g2, b2, a))


def cor_sombra_do_tema(tema: str | None) -> tuple[int, int, int]:
    """OS F11.5 #57 (R-102): a cor da sombra sintética acompanha o TEMA da
    arte — no claro, sombra preta clássica; no escuro, um halo CLARO (sombra
    preta some em fundo escuro; o volume vem do contraste)."""
    return (185, 195, 210) if tema == "escuro" else (0, 0, 0)


def _enquadrar_com_sombra(produto: Image.Image, lado: int, margem_frac: float,
                          intensidade: float,
                          cor_sombra: tuple[int, int, int] = (0, 0, 0)
                          ) -> Image.Image:
    """Centraliza o produto num quadrado com margem de packshot e projeta uma
    SOMBRA sintética suave sob ele (a partir do alfa; dá volume). A cor vem
    do tema (#57) — preto no claro, halo claro no escuro."""
    disp = max(1, int(lado * (1 - 2 * margem_frac)))
    esc = min(disp / produto.width, disp / produto.height)
    pw, ph = max(1, round(produto.width * esc)), max(1, round(produto.height * esc))
    prod = produto.resize((pw, ph))
    px, py = (lado - pw) // 2, (lado - ph) // 2

    canvas = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    # sombra: o alfa do produto, deslocado p/ baixo, borrado e escurecido
    desl = int(ph * 0.05) + 4
    mascara = Image.new("L", (lado, lado), 0)
    mascara.paste(prod.getchannel("A"), (px + int(pw * 0.02), py + desl))
    raio = max(3, ph // 22)
    mascara = mascara.filter(ImageFilter.GaussianBlur(raio))
    inten = max(0.0, min(1.0, intensidade))
    mascara = mascara.point(lambda v: int(v * inten))
    r, g, b = cor_sombra
    sombra = Image.new("RGBA", (lado, lado), (r, g, b, 0))
    sombra.putalpha(mascara)                       # translúcido (a=máscara)
    canvas = Image.alpha_composite(canvas, sombra)   # sombra primeiro (embaixo)
    canvas.paste(prod, (px, py), prod)               # produto por cima
    return canvas


def packshot_degrau1(img: Image.Image, *, remover_fundo=None,
                     intensidade_sombra: float = 0.35, margem_frac: float = 0.08,
                     lado: int = 1000,
                     tema: str | None = None) -> Image.Image:
    """DEGRAU 1: foto crua → packshot (RGBA, fundo transparente + sombra). CPU,
    qualquer PC. `remover_fundo` é INJETÁVEL (o teste não carrega o modelo de
    ~1GB). Nunca deforma o produto (escala pela proporção). `tema` (#57)
    escolhe a cor da sombra (claro=preta · escuro=halo claro)."""
    if remover_fundo is None:
        from app.images.fundo import remover_fundo_img
        remover_fundo = remover_fundo_img
    from app.images.fundo import recortar_conteudo
    rgba = recortar_conteudo(remover_fundo(img).convert("RGBA"))
    produto = _normalizar_luz(rgba)
    return _enquadrar_com_sombra(produto, lado, margem_frac, intensidade_sombra,
                                 cor_sombra=cor_sombra_do_tema(tema))


# ---- Degrau 2: img2img local (opção condicionada à GPU) --------------------

def gerador_disponivel() -> str | None:
    """O DEGRAU 2 (img2img SDXL) exige GPU (pesquisa §6: SDXL ~12GB). Devolve o
    device ("cuda") ou None — sem GPU o degrau 1 é o padrão garantido. NUNCA
    levanta."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return None


def diferenca_demais(antes: Image.Image, depois: Image.Image,
                     limite: float = 0.35) -> bool:
    """Guarda anti-alucinação (R-091 passo 24): mede quanto o img2img mudou o
    produto (diferença média de pixel, 0..1). Acima do limite = mudou demais
    (provável 'inventou outro produto') → o chamador avisa e sugere baixar o
    denoise."""
    a = antes.convert("RGB").resize((64, 64))
    b = depois.convert("RGB").resize((64, 64))
    da = list(a.getdata())
    db = list(b.getdata())
    total = sum(abs(pa[i] - pb[i]) for pa, pb in zip(da, db) for i in range(3))
    return (total / (len(da) * 3 * 255)) > limite


def refinar_com_gerador(packshot: Image.Image, *, motor=None,
                        denoise: float = 0.5
                        ) -> tuple[Image.Image | None, str | None]:
    """DEGRAU 2: img2img local sobre o packshot do degrau 1 (denoise baixo
    preserva o produto). Devolve (imagem, aviso). SEM GPU/motor → (None, aviso) —
    degrada, o degrau 1 já entregou. NUNCA é requisito, NUNCA levanta.

    `motor` (injetável, API compatível-OpenAI de img2img) permite provar o
    encanamento sem GPU; None + sem GPU = desabilitado com explicação honesta."""
    if gerador_disponivel() is None and motor is None:
        return None, ("O Estúdio gerador (degrau 2) requer uma placa de vídeo "
                      "dedicada (GPU), que não foi encontrada. O packshot do "
                      "degrau 1 já está pronto — o app não depende do gerador.")
    if motor is None:
        return None, ("O gerador está ligado, mas nenhum modelo respondeu — "
                      "ficamos com o packshot do degrau 1.")
    try:
        saida = motor.img2img(packshot, denoise=denoise)
    except Exception:
        return None, ("O gerador falhou — ficamos com o packshot do degrau 1 "
                      "(o app não depende dele).")
    if saida is None:
        return None, "O gerador não devolveu imagem — mantido o degrau 1."
    if diferenca_demais(packshot, saida):        # anti-alucinação (passo 24)
        return None, ("O gerador mudou demais o produto (pode ter inventado outro) "
                      "— baixe o denoise ou fique com o degrau 1.")
    return saida, None
