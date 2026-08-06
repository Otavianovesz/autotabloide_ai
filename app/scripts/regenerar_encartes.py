"""Regera as artes do pacote de encartes (F13-BIS/T6).

As BASE.png em disco carregavam as strings VELHAS que o F8 corrigiu nos
geradores ("CRIADA E PRODUZIDA", "SENEPOL MARCA PRÓPRIA", "O MÊS
INTEIRO") — sem regenerar, o dono publica a arte errada. O pipeline é o
do README do pacote (Playwright + Chromium, viewport 1080×1440,
deviceScaleFactor=2 ⇒ BASE.png 2160×2880), com UMA diferença declarada:
as fontes NÃO são instaladas no sistema — viajam embutidas num
``@font-face`` base64 no HTML que embrulha o SVG (mesmo resultado,
máquina do dono intocada).

Uso:
    python -m app.scripts.regenerar_encartes "Templates novos" [chave...]

Sem chaves, regenera os 7. Cada encarte: roda o gerador (refaz
MASTER.svg/BASE.svg já com o F8) e renderiza BASE.png (2160×2880) e
PREVIEW.png (1080×1440, do MASTER).
"""

from __future__ import annotations

import base64
import subprocess
import sys
from pathlib import Path

# gerador → (subpasta em artes/, [(svg, png, escala)])
ALVOS: dict[str, tuple[str, list[tuple[str, str, int]]]] = {
    "gen_segunda3.py": ("segunda-frios", [
        ("segunda-frios-BASE.svg", "segunda-frios-BASE.png", 2),
        ("segunda-frios-MASTER.svg", "segunda-frios-PREVIEW.png", 1)]),
    "gen_terca_final.py": ("terca-do-pao", [
        ("terca-do-pao-BASE.svg", "terca-do-pao-BASE.png", 2),
        ("terca-do-pao-MASTER.svg", "terca-do-pao-PREVIEW.png", 1)]),
    "gen_final.py": ("quarta-das-ofertas", [
        ("quarta-das-ofertas-BASE.svg",
         "quarta-das-ofertas-BASE-2160x2880.png", 2),
        ("quarta-das-ofertas-MASTER.svg",
         "quarta-das-ofertas-PREVIEW.png", 1)]),
    "gen_peixe5.py": ("quinta-do-peixe", [
        ("quinta-do-peixe-BASE.svg", "quinta-do-peixe-BASE.png", 2),
        ("quinta-do-peixe-MASTER.svg", "quinta-do-peixe-PREVIEW.png", 1)]),
    "gen_verde5.py": ("sexta-verde", [
        ("sexta-verde-BASE.svg", "sexta-verde-BASE-2160x2880.png", 2),
        ("sexta-verde-MASTER.svg", "sexta-verde-PREVIEW.png", 1)]),
    "gen_carne_final.py": ("sabado-da-carne", [
        ("sabado-da-carne-BASE.svg", "sabado-da-carne-BASE.png", 2),
        ("sabado-da-carne-MASTER.svg", "sabado-da-carne-PREVIEW.png", 1)]),
    "gen_jornal_final.py": ("jornal-do-mes", [
        ("jornal-p1-BASE.svg", "jornal-p1-BASE.png", 2),
        ("jornal-p1-MASTER.svg", "jornal-p1-PREVIEW.png", 1),
        ("jornal-p2-BASE.svg", "jornal-p2-BASE.png", 2),
        ("jornal-p2-MASTER.svg", "jornal-p2-PREVIEW.png", 1)]),
}

# arquivo .ttf do pacote → (família CSS, peso, itálico?). Os pesos que
# os geradores pedem sem face exata caem no matching do Chromium
# (500→400, 800→900 etc.), o mesmo que ocorreria com fontes instaladas.
FACES = (
    ("Anton-Regular.ttf", "Anton", 400, False),
    ("Archivo-Bold.ttf", "Archivo", 700, False),
    ("Archivo-Medium.ttf", "Archivo", 500, False),
    ("Baloo2-Bold.ttf", "Baloo 2", 700, False),
    ("Baloo2-ExtraBold.ttf", "Baloo 2", 800, False),
    ("Caveat-Bold.ttf", "Caveat", 700, False),
    ("Fraunces-Italic.ttf", "Fraunces", 400, True),
    ("Fraunces-Regular.ttf", "Fraunces", 400, False),
    ("Fraunces-SemiBold.ttf", "Fraunces", 600, False),
    ("Nunito-Black.ttf", "Nunito", 900, False),
    ("Nunito-Bold.ttf", "Nunito", 700, False),
    ("UnifrakturMaguntia.ttf", "UnifrakturMaguntia", 400, False),
)


def _css_fontes(pasta_fontes: Path) -> str:
    regras = []
    for arq, familia, peso, italico in FACES:
        p = pasta_fontes / arq
        if not p.exists():
            print(f"  AVISO: fonte ausente no pacote: {arq}")
            continue
        b64 = base64.b64encode(p.read_bytes()).decode()
        estilo = "italic" if italico else "normal"
        regras.append(
            f"@font-face{{font-family:'{familia}';font-weight:{peso};"
            f"font-style:{estilo};"
            f"src:url(data:font/ttf;base64,{b64}) format('truetype');}}")
    return "\n".join(regras)


def regenerar(pasta_pacote: Path, so: list[str] | None = None) -> int:
    from playwright.sync_api import sync_playwright

    geradores = pasta_pacote / "geradores"
    artes = pasta_pacote / "artes"
    css = _css_fontes(pasta_pacote / "fontes")
    falhas = 0
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        try:
            for gen, (sub, saidas) in ALVOS.items():
                if so and sub not in so:
                    continue
                print(f"[{sub}] gerador {gen}…")
                r = subprocess.run([sys.executable, gen], cwd=geradores,
                                   capture_output=True, text=True)
                if r.returncode != 0:
                    print(f"  FALHOU: {r.stderr.strip()[:400]}")
                    falhas += 1
                    continue
                for svg_nome, png_nome, escala in saidas:
                    svg = artes / sub / svg_nome
                    if not svg.exists():
                        print(f"  FALTA {svg_nome} (o gerador não gerou?)")
                        falhas += 1
                        continue
                    corpo = svg.read_text(encoding="utf-8")
                    html = ("<!doctype html><html><head>"
                            "<meta charset='utf-8'><style>" + css +
                            "html,body{margin:0;padding:0}</style>"
                            "</head><body>" + corpo + "</body></html>")
                    pg = nav.new_page(
                        viewport={"width": 1080, "height": 1440},
                        device_scale_factor=escala)
                    pg.set_content(html)
                    pg.wait_for_timeout(1000)   # fontes (o README manda)
                    pg.screenshot(path=str(artes / sub / png_nome))
                    pg.close()
                    print(f"  ✓ {png_nome} ({1080 * escala}×{1440 * escala})")
        finally:
            nav.close()
    return falhas


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    pacote = Path(sys.argv[1])
    chaves = sys.argv[2:] or None
    raise SystemExit(1 if regenerar(pacote, chaves) else 0)
