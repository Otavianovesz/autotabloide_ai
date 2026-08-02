"""O parser da validade da oferta (Rodada JM, B2A).

A validade viaja pelo app como TEXTO no vocabulário da casa ("SOMENTE
17/08", "OFERTA VÁLIDA DE 03/08 ATÉ 27/08", "enquanto durarem os
estoques") — e chega da tabela do dono em formas cruas ("OFERTAS
VALIDAS 03/08/2026 ATÉ 27/08/2026"). Este módulo é a régua ÚNICA que
transforma qualquer uma dessas strings no par de datas (início, fim):
os avisos de sanidade, o selo só-data e os textos de período vivo dos
encartes derivam TODOS daqui — nunca mais um regex pegando "a primeira
data" e errando o sentido.

Vive no core (sem Qt) porque o compositor (rendering) também consome.
"""

from __future__ import annotations

import re
from datetime import date

_RE_DATA = re.compile(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b")
# o período fixo gravado nas artes do Jornal ("do dia 1º ao 27")
_RE_PERIODO_FIXO = re.compile(r"\bdo dia (\d{1,2})º? ao (\d{1,2})\b",
                              re.IGNORECASE)


def _data_de(m: re.Match[str], hoje: date) -> date | None:
    """Uma captura de _RE_DATA vira date — ano escrito respeitado; sem
    ano, o corrente com a virada dez→jan (a regra da casa)."""
    dia, mes = int(m.group(1)), int(m.group(2))
    ano_txt = m.group(3)
    if ano_txt:
        ano = int(ano_txt)
        if ano < 100:
            ano += 2000
    else:
        ano = hoje.year
        if mes == 1 and hoje.month == 12:
            ano += 1
    try:
        return date(ano, mes, dia)
    except ValueError:
        return None                     # 32/13 não existe — as guardas avisam


def datas_da_validade(texto: str | None,
                      hoje: date | None = None
                      ) -> tuple[date | None, date | None]:
    """O par (início, fim) da validade escrita — (None, None) quando o
    texto não tem data válida nenhuma.

    Duas ou mais datas → (primeira, última). Uma data só → o PREFIXO
    decide: "ATÉ dd/mm" é só fim (None, d); qualquer outra ("SOMENTE",
    data solta) vale o dia inteiro (d, d)."""
    texto = (texto or "").strip()
    if not texto:
        return None, None
    hoje = hoje or date.today()
    datas = [d for m in _RE_DATA.finditer(texto)
             if (d := _data_de(m, hoje)) is not None]
    if not datas:
        return None, None
    if len(datas) >= 2:
        return datas[0], datas[-1]
    unica = datas[0]
    antes = texto[:_RE_DATA.search(texto).start()].lower()
    if re.search(r"\bat[eé]\s*$", antes):
        return None, unica
    return unica, unica


def texto_com_periodo_vivo(fixo: str | None,
                           validade: str | None) -> str | None:
    """Decisão do dono (03/08): os textos fixos do Jornal com o período
    gravado ("do dia 1º ao 27") passam a escrever o período REAL da
    oferta. Sem par (de, até) parseável — ou validade de um dia só — o
    fixo volta INTACTO: layout antigo e os outros encartes nunca mudam."""
    if not fixo or not validade:
        return fixo
    m = _RE_PERIODO_FIXO.search(fixo)
    if not m:
        return fixo
    de, ate = datas_da_validade(validade)
    if not (de and ate) or de == ate:
        return fixo
    dia_de = "1º" if de.day == 1 else str(de.day)
    novo = f"do dia {dia_de} ao {ate.day}"
    # o "º" é letra MINÚSCULA em Unicode — sai da conta da caixa
    if m.group(0).replace("º", "").isupper():
        novo = novo.upper()
    return fixo[:m.start()] + novo + fixo[m.end():]
