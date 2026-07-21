"""
Fluxo completo da Fase 3: foto -> tabela -> conciliação -> enriquecimento
=========================================================================
Junta as peças: OCR lê a foto; cada linha é conciliada com o banco (semáforo);
os itens NOVOS (vermelho) passam pelo enriquecimento para virar produto.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.ai.client import MotorIA
from app.ai.conciliacao import Conciliador, Semaforo, Veredito
from app.ai.enriquecimento import ProdutoEnriquecido, enriquecer
from app.ai.ocr import LinhaOferta, ler_tabela


@dataclass
class ResultadoLinha:
    linha: LinhaOferta
    veredito: Veredito
    enriquecido: ProdutoEnriquecido | None = None


@dataclass
class ResultadoImportacao:
    """Resultado de importar uma tabela: as linhas processadas + a validade da oferta.

    A ``validade_oferta`` fica no contexto da IMPORTAÇÃO/projeto (alimenta o texto
    legal no layout), NÃO na tabela Produto.
    """

    linhas: list[ResultadoLinha] = field(default_factory=list)
    validade_oferta: str | None = None


def processar_tabela(
    imagem: str | Path,
    motor_ocr: MotorIA,
    conciliador: Conciliador,
    *,
    motor_enriquecimento: MotorIA | None = None,
) -> ResultadoImportacao:
    """Lê a foto e processa cada linha (conciliar; enriquecer os novos)."""
    motor_enriquecimento = motor_enriquecimento or motor_ocr
    tabela = ler_tabela(imagem, motor_ocr)
    resultados: list[ResultadoLinha] = []
    for linha in tabela.linhas:
        veredito = conciliador.conciliar(linha.descricao)
        enriquecido = None
        if veredito.semaforo == Semaforo.VERMELHO:
            enriquecido = enriquecer(linha.descricao, motor_enriquecimento)
        resultados.append(ResultadoLinha(linha, veredito, enriquecido))
    return ResultadoImportacao(linhas=resultados, validade_oferta=tabela.validade_oferta)
