"""
QR opcional no cartaz (R-114 da Fase 11)
========================================
Um QR **opcional** (link do encarte, catálogo) gerado LOCALMENTE — coerente
com o app offline. Fica **desligado por padrão**: só entra quando o dono
liga e informa o texto/URL.

A geração degrada com honestidade (I2): sem a lib ``qrcode`` o cartaz sai
igual, sem o QR, e o chamador recebe um aviso — nunca trava (mesmo contrato
do ffmpeg no vídeo e do Ghostscript no CMYK).
"""

from __future__ import annotations

from PIL import Image, ImageColor


def qr_disponivel() -> bool:
    """True se a lib local de QR está instalada (offline, sem serviço)."""
    try:
        import qrcode  # noqa: F401
        return True
    except Exception:
        return False


def gerar_qr(texto: str, lado_px: int, *, cor: str = "#000000",
             fundo: str = "#FFFFFF") -> tuple[Image.Image | None, str | None]:
    """Gera o QR como uma imagem quadrada ``lado_px``×``lado_px`` (RGBA).

    Devolve ``(imagem, aviso)``: sem a lib, ``(None, aviso)``; texto vazio,
    ``(None, aviso)``. O fundo pode ser transparente passando ``fundo=None``.
    """
    texto = (texto or "").strip()
    if not texto:
        return None, "QR sem texto/URL — nada a codificar"
    if not qr_disponivel():
        return None, ("a biblioteca de QR não está instalada — o cartaz sai "
                      "sem o QR")
    import qrcode

    lado_px = max(1, int(lado_px))
    qr = qrcode.QRCode(border=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(texto)
    qr.make(fit=True)
    rgb_cor = ImageColor.getrgb(cor)
    fundo_rgba = (0, 0, 0, 0) if fundo is None else (*ImageColor.getrgb(fundo), 255)
    img = qr.make_image(fill_color=rgb_cor,
                        back_color="white").convert("RGBA")
    if fundo is None or fundo_rgba != (*ImageColor.getrgb("#FFFFFF"), 255):
        # repinta o fundo (o make_image só aceita nomes simples)
        base = Image.new("RGBA", img.size, fundo_rgba)
        px = img.load()
        bp = base.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, _ = px[x, y]
                if (r, g, b) == (0, 0, 0):          # módulo escuro → cor pedida
                    bp[x, y] = (*rgb_cor, 255)
        img = base
    # QR é quadrado; NEAREST preserva os módulos nítidos ao redimensionar
    return img.resize((lado_px, lado_px), Image.NEAREST), None


def aplicar_qr(base: Image.Image, texto: str, *, lado_px: int,
               canto: str = "inferior_direito", margem_px: int = 12,
               cor: str = "#000000",
               fundo: str = "#FFFFFF") -> tuple[Image.Image, str | None]:
    """Cola o QR num canto de uma cópia da imagem composta (não-destrutivo).

    Sem QR possível, devolve a base intocada + o aviso (I2). O QR opcional
    nunca cobre o preço: fica ancorado num canto, com margem.
    """
    qr, aviso = gerar_qr(texto, lado_px, cor=cor, fundo=fundo)
    if qr is None:
        return base, aviso
    out = base.convert("RGBA")
    lp = qr.width
    if "direito" in canto:
        x = out.width - lp - margem_px
    else:
        x = margem_px
    if "inferior" in canto:
        y = out.height - lp - margem_px
    else:
        y = margem_px
    out.paste(qr, (max(0, x), max(0, y)), qr)
    return out.convert(base.mode), None
