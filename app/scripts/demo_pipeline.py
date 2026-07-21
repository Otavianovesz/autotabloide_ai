"""
Demonstra o fluxo completo da Fase 3: foto -> OCR -> conciliação -> enriquecimento.

Por padrão roda com FAKE (encanamento): imagem stub + respostas de exemplo.
Com --real <caminho_da_imagem>, usa o Qwen3.5 no print de verdade.

Uso::

    python -m app.scripts.demo_pipeline
    python -m app.scripts.demo_pipeline --real caminho/para/print.jpg
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from app.ai.conciliacao import Conciliador, Semaforo
from app.ai.fake import MotorIAFake
from app.ai.pipeline import processar_tabela
from app.core.database import Database
from app.core.paths import SystemRoot
from app.core.repositories import ProdutoRepositorio
from app.scripts.importar_tabela import parse_tabela

_AI = Path(__file__).resolve().parents[1] / "ai" / "fixtures"
OCR_FIX = _AI / "ocr_exemplo.json"
ENR_FIX = _AI / "enriquecimento_exemplo.json"
TABELA_42 = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "ofertas_belo_brasil.txt"

_ICONE = {Semaforo.VERDE: "🟢", Semaforo.AMARELO: "🟡", Semaforo.VERMELHO: "🔴"}


def montar_fake_completo() -> MotorIAFake:
    """Fake com respostas de OCR (visão) e de enriquecimento (chat)."""
    ocr = json.loads(OCR_FIX.read_text(encoding="utf-8"))
    ocr_obj = {"validade_oferta": ocr.get("validade_oferta"), "linhas": ocr["linhas"]}
    enr = json.loads(ENR_FIX.read_text(encoding="utf-8"))["respostas"]
    return MotorIAFake(
        respostas_visao={"tabela de ofertas": json.dumps(ocr_obj, ensure_ascii=False)},
        respostas_chat={n: json.dumps(o, ensure_ascii=False) for n, o in enr.items()},
    )


def gerar_imagem_stub(caminho: Path) -> Path:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (800, 1000), "white")
    ImageDraw.Draw(img).text((40, 40), "JORNAL DE OFERTAS (stub)", fill="black")
    img.save(caminho)
    return caminho


def main(real: bool = False, imagem: str | None = None) -> None:
    with tempfile.TemporaryDirectory() as d:
        os.environ["AUTOTABLOIDE_ROOT"] = str(Path(d) / "raiz")
        db = Database(SystemRoot(Path(d) / "raiz")).init()
        try:
            with db.Session() as session:
                repo = ProdutoRepositorio(session)

                if real:
                    from app.ai.client import ClienteOpenAICompat

                    motor = ClienteOpenAICompat()
                    if not motor.disponivel():
                        print("LM Studio não acessível.")
                        return
                    if not imagem:
                        print("Modo --real exige o caminho de uma imagem (o print).")
                        return
                    img = imagem
                    conc = Conciliador(session, motor=motor, embedder=motor)
                    # banco = catálogo real (a fixture de 42)
                    for n, p in parse_tabela(TABELA_42):
                        repo.importar(n, preco=p)
                    print("✅ FLUXO REAL (Qwen3.5): OCR + conciliação + enriquecimento\n")
                else:
                    motor = montar_fake_completo()
                    img = gerar_imagem_stub(Path(d) / "stub.png")
                    conc = Conciliador(session)  # sem juiz (semáforo fuzzy real)
                    # banco parcial: Azeite NÃO está -> vira vermelho -> enriquece
                    for nome in ["BOMBRIL 45 g", "REFRIGERANTE KITUBAINA 1,5 LT"]:
                        repo.importar(nome)
                    print("⚙️  FLUXO COM FAKE (encanamento): imagem stub + respostas de exemplo\n")

                session.commit()
                imp = processar_tabela(img, motor, conc, motor_enriquecimento=motor)

                if imp.validade_oferta:
                    print(f"📅 Validade da oferta: {imp.validade_oferta}\n")

                for r in imp.linhas:
                    ic = _ICONE[r.veredito.semaforo]
                    preco = f"R$ {r.linha.preco}" if r.linha.preco else "-"
                    print(f"{ic} {r.veredito.semaforo.value:<8} {r.linha.descricao}  ({preco})")
                    if r.veredito.produto:
                        print(f"     -> banco: {r.veredito.produto.nome_sanitizado}")
                    if r.enriquecido:
                        e = r.enriquecido
                        print(f"     -> NOVO enriquecido: {e.nome_sanitizado}  [cat={e.categoria}]")
                        for c in e.componentes:
                            print(f"          componente: {c.nome_sanitizado} [{c.marca}]")
        finally:
            db.engine.dispose()


if __name__ == "__main__":
    import sys

    args = sys.argv[1:]
    real = "--real" in args
    caminho = None
    if real:
        rest = [a for a in args if a != "--real"]
        caminho = rest[0] if rest else None
    main(real=real, imagem=caminho)
