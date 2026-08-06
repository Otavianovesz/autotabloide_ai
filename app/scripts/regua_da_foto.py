"""F13-QUARTUSDECIMUS — o fecho na raiz REAL: a régua da foto + as páginas.

1. backup do banco; 2. reimporta o pacote (a fixa-3 VERDE + zona_flex
chegam ao banco do dono; o upsert preserva o conteúdo fixo por slot.id);
3. recompõe os projetos do caminho do dono com o LAYOUT NOVO do banco +
os DADOS congelados do projeto (a montagem oficial — sem OCR de novo);
4. MEDE célula a célula a ocupação foto/zona (a régua do §1), antes e
depois do plano; 5. a densidade da Terça (Q8); 6. os DOIS formatos do
desconto recortados para o dono escolher (Q4).

Uso:  python -m app.scripts.regua_da_foto
"""

from __future__ import annotations

import os
import shutil
import sys
from datetime import date
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parents[2]
SAIDA = RAIZ_REPO / "saida_f13" / "galeria_f13_bis"

PROJETOS_ALVO = {
    "Quarta 29/07 — caminho do dono": ("Quarta das Ofertas",
                                       "quarta-2907-caminho-do-dono.png"),
    "28/07": ("Terça do Pão", "terca-2807-caminho-do-dono.png"),
    "Segunda 27/07 — caminho do dono": ("Segunda dos Frios",
                                        "segunda-2707-caminho-do-dono.png"),
}


def _dim_util(caminho: str) -> tuple[int, int] | None:
    from PIL import Image
    try:
        img = Image.open(caminho).convert("RGBA")
    except OSError:
        return None
    bb = img.getchannel("A").getbbox()
    return (bb[2] - bb[0], bb[3] - bb[1]) if bb else (img.width, img.height)


def _medir_slot(slot, d) -> list[str]:
    """A régua para UMA célula: ocupação antes → depois (se houve plano)."""
    from app.rendering.foto_fit import medir_ocupacao, plano_da_celula
    from app.rendering.model import TipoRegiao

    linhas = []
    zonas = [r for r in slot.regioes
             if r.tipo == TipoRegiao.IMAGEM and r.visivel]
    if not zonas or d is None:
        return linhas
    imagens = list(getattr(d, "imagens", None) or [])
    for k, rz in enumerate(zonas):
        if len(zonas) > 1 and imagens:
            cam = imagens[min(k, len(imagens) - 1)].caminho
        else:
            cam = getattr(d, "imagem_path", None)
        if not cam:
            continue
        dim = _dim_util(cam)
        if not dim:
            continue
        m = medir_ocupacao(rz.rect.larg_mm, rz.rect.alt_mm, *dim)
        plano = plano_da_celula(slot.regioes, *dim) if len(zonas) == 1 \
            else None
        if plano is not None:
            novo = plano.rects[rz.uid]
            dep = medir_ocupacao(novo.larg_mm, novo.alt_mm, *dim)
            linhas.append(
                f"  {slot.id:16s} foto {dim[0]}x{dim[1]}: "
                f"{m.area_frac:5.0%} -> {dep.area_frac:5.0%} "
                f"({plano.arranjo}; area da foto "
                f"{plano.area_antes_mm2:.0f}->{plano.area_depois_mm2:.0f})")
        else:
            nota = ""
            if m.area_frac < 0.85:
                nota = (" [em pé — enche a altura, vazio lateral simétrico]"
                        if m.h_frac >= 0.85 else
                        " [sem plano: célula sem marca/vestida]")
            linhas.append(
                f"  {slot.id:16s} foto {dim[0]}x{dim[1]}: "
                f"{m.area_frac:5.0%} (h {m.h_frac:.0%}){nota}")
    return linhas


def rodar() -> None:
    os.environ["AUTOTABLOIDE_ROOT"] = str(
        RAIZ_REPO / "AutoTabloide_System_Root")
    from app.core.paths import SystemRoot
    root = SystemRoot()
    print("raiz real:", root.raiz)

    banco = root.caminho_banco
    backup = root.raiz / "backups" / \
        f"core_pre_quartusdecimus_{date.today():%Y%m%d}.db"
    backup.parent.mkdir(exist_ok=True)
    if not backup.exists():
        shutil.copy2(banco, backup)
        print("backup:", backup.name)

    from app.core.database import Database
    from app.core import projetos as _projetos
    from app.qt.telas import servico
    from app.rendering.compositor import compor_pagina
    from app.rendering.encartes import importar_pacote
    from app.rendering.persistencia import carregar_layout, listar_layouts

    # 2) o pacote novo no banco do dono (preserva o conteúdo fixo)
    db = Database().init()
    try:
        with db.Session() as s:
            rel = importar_pacote(s, RAIZ_REPO / "Templates novos", root)
            s.commit()
        print(f"pacote reimportado: {len(rel)} encartes")
    finally:
        db.engine.dispose()

    # 3+4) recompõe os projetos com o layout NOVO e mede a régua
    from PIL import Image
    todos = _projetos.listar_projetos()
    for nome_proj, (nome_layout, arquivo) in PROJETOS_ALVO.items():
        pid = next((p["id"] for p in todos if p["nome"] == nome_proj), None)
        if pid is None:
            print(f"[{nome_proj}] NÃO ACHADO — pulando (nomeado)")
            continue
        aberto = _projetos.abrir_projeto(pid)
        dados, faltas = servico.dados_de_projeto_aberto(aberto)
        for f in faltas:
            print(f"[{nome_proj}] FALTA: {f}")
        db = Database().init()
        try:
            with db.Session() as s:
                alvo = next(r for r in listar_layouts(s)
                            if r.nome == nome_layout)
                lay = carregar_layout(s, alvo.id, raiz=root)
        finally:
            db.engine.dispose()
        img = compor_pagina(lay, lay.paginas[0], dados,
                            fundo_path=lay.arquivo_fundo)
        alt = round(1080 * img.height / img.width)
        destino = SAIDA / arquivo
        menor = img.resize((1080, alt), Image.LANCZOS)
        try:
            menor.save(destino)
        except OSError:
            # o OSError 22 transitório do Windows (handle preso do
            # indexador) — a família do incidente da OCTAVUS; 1 retry
            import time
            time.sleep(1.5)
            menor.save(destino)
        print(f"[{nome_proj}] id={pid} recomposta -> {destino.name}")

        print(f"[{nome_proj}] A RÉGUA (ocupação foto/zona, antes -> depois):")
        from app.rendering.compositor import _dados_do_conteudo_fixo
        for slot in lay.paginas[0].slots:
            d = dados.get(slot.id)
            if d is None and getattr(slot, "fixa", False) \
                    and slot.conteudo_fixo:
                d = _dados_do_conteudo_fixo(slot.conteudo_fixo)
            for ln in _medir_slot(slot, d):
                print(ln)

        if nome_layout == "Terça do Pão":
            dens = servico.densidade_da_pagina(lay.paginas[0], dados)
            print(f"[Q8] densidade da Terça (células ocupáveis com item): "
                  f"{dens:.2f}")

    # 6) os DOIS formatos do desconto, recortados para o dono (Q4)
    import app.rendering.compositor as comp
    pid = next((p["id"] for p in todos
                if p["nome"] == "Quarta 29/07 — caminho do dono"), None)
    if pid is not None:
        aberto = _projetos.abrir_projeto(pid)
        dados, _ = servico.dados_de_projeto_aberto(aberto)
        db = Database().init()
        try:
            with db.Session() as s:
                alvo = next(r for r in listar_layouts(s)
                            if r.nome == "Quarta das Ofertas")
                lay = carregar_layout(s, alvo.id, raiz=root)
        finally:
            db.engine.dispose()
        fixa3 = next(sl for sl in lay.paginas[0].slots
                     if sl.id == "celula-fixa-3")
        from app.rendering.units import mm_para_px
        xs, ys, xe, ye = 1e9, 1e9, 0, 0
        for r in fixa3.regioes:
            xs = min(xs, r.rect.x_mm); ys = min(ys, r.rect.y_mm)
            xe = max(xe, r.rect.x_mm + r.rect.larg_mm)
            ye = max(ye, r.rect.y_mm + r.rect.alt_mm)
        for estilo, arq in (("off", "desconto-opcao-1-off.png"),
                            ("menos", "desconto-opcao-2-menos.png")):
            antigo = comp.FORMATO_DESCONTO_PADRAO
            comp.FORMATO_DESCONTO_PADRAO = estilo
            try:
                img = compor_pagina(lay, lay.paginas[0], dados,
                                    fundo_path=lay.arquivo_fundo)
            finally:
                comp.FORMATO_DESCONTO_PADRAO = antigo
            dpi = lay.dpi
            esc = img.width / mm_para_px(lay.largura_mm, dpi)
            rec = img.crop((
                int(mm_para_px(xs - 4, dpi) * esc),
                int(mm_para_px(ys - 4, dpi) * esc),
                int(mm_para_px(xe + 4, dpi) * esc),
                int(mm_para_px(ye + 4, dpi) * esc)))
            rec.save(SAIDA / arq)
            print(f"[Q4] opção “{estilo}” -> {arq}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    rodar()
