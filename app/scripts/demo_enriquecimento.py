"""
Demonstra o enriquecimento (passo 2 da Fase 3) rodando com o MotorIAFake.

⚠️  As respostas são de EXEMPLO (escritas à mão). Isto valida o ENCANAMENTO,
não a qualidade da IA — que só se prova com o Qwen no LM Studio.

Uso::

    python -m app.scripts.demo_enriquecimento
"""

from __future__ import annotations

import json
from pathlib import Path

from app.ai.enriquecimento import enriquecer
from app.ai.fake import MotorIAFake

FIXTURE = Path(__file__).resolve().parents[1] / "ai" / "fixtures" / "enriquecimento_exemplo.json"


def montar_fake() -> MotorIAFake:
    dados = json.loads(FIXTURE.read_text(encoding="utf-8"))
    # o fake casa por trecho do prompt: a chave (nome cru) aparece no prompt.
    respostas = {nome: json.dumps(obj, ensure_ascii=False) for nome, obj in dados["respostas"].items()}
    return MotorIAFake(respostas_chat=respostas)


def main(real: bool = False) -> None:
    dados = json.loads(FIXTURE.read_text(encoding="utf-8"))
    nomes = list(dados["respostas"].keys())

    if real:
        from app.ai.client import ClienteOpenAICompat

        motor = ClienteOpenAICompat()
        if not motor.disponivel():
            print("LM Studio não acessível. Suba o servidor local + um modelo de texto e tente de novo.")
            return
        print("=" * 90)
        print("✅ ENRIQUECIMENTO COM O MODELO REAL (LM Studio) — agora sim é a qualidade da IA.")
        print("=" * 90)
    else:
        motor = montar_fake()
        print("=" * 90)
        print("⚠️  ENRIQUECIMENTO COM RESPOSTAS FAKE — valida o ENCANAMENTO, não a qualidade da IA.")
        print("=" * 90)
    for nome in nomes:
        r = enriquecer(nome, motor)
        print(f"\n• {nome}")
        print(f"    -> {r.nome_sanitizado}")
        extras = []
        if r.categoria:
            extras.append(f"categoria={r.categoria}")
        if r.marca:
            extras.append(f"marca={r.marca}")
        if r.mais18:
            extras.append("+18")
        if extras:
            print(f"       {'  |  '.join(extras)}")
        if r.componentes:
            print("       COMPONENTES (2 produtos que vão juntos no slot):")
            for c in r.componentes:
                print(f"         - {c.nome_sanitizado}  [{c.marca}]")
        if r.variantes:
            print(f"       VARIANTES (mesmo produto): {', '.join(r.variantes)}")
        if r.observacoes:
            print(f"       obs: {r.observacoes}")


if __name__ == "__main__":
    import sys

    main(real="--real" in sys.argv)
