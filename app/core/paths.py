"""
Estrutura de pastas do sistema (System Root)
============================================
Conforme a Documentação-Mestre, seção 2.3.

Toda a "vida" do programa (banco, imagens, layouts, projetos, backups) mora
numa única pasta raiz. Por padrão ela fica dentro do projeto, em
``AutoTabloide_System_Root/``. Dá para apontar outra pasta pela variável de
ambiente ``AUTOTABLOIDE_ROOT`` (útil para testes e para levar os dados a outro PC).

Uso típico::

    from app.core.paths import SystemRoot

    root = SystemRoot().criar_estrutura()
    print(root.caminho_banco)   # .../AutoTabloide_System_Root/banco/core.db
"""

from __future__ import annotations

import os
from pathlib import Path

# Nome da pasta raiz de dados (quando não vem de AUTOTABLOIDE_ROOT).
NOME_RAIZ = "AutoTabloide_System_Root"

# Subpastas do System Root (nomes em português, como na doc).
# chave lógica -> nome da pasta em disco
SUBPASTAS: dict[str, str] = {
    "banco": "banco",                       # arquivo SQLite + índice de embeddings
    "biblioteca_imagens": "biblioteca_imagens",  # imagens dos produtos (+ versões antigas)
    "layouts": "layouts",                   # arte de fundo + descrição de grade/slots
    "projetos": "projetos",                 # projetos salvos (dados congelados)
    "fontes": "fontes",                     # fontes embutidas
    "config": "config",                     # preferências do usuário
    "backups": "backups",                   # cópias do banco e snapshots
    "modelos": "modelos",                   # referência aos modelos de IA
    "modelos_celula": "modelos_celula",     # R-048: modelos de célula (trios prontos)
    "logs": "logs",                         # diagnóstico (ex.: travamentos.log)
    "selos": "selos",                       # RG-33: artes de selo do usuário
}

# Nome do arquivo do banco principal (dados "vivos").
NOME_BANCO = "core.db"


def _raiz_projeto() -> Path:
    """Raiz do repositório (dois níveis acima deste arquivo: app/core/paths.py)."""
    return Path(__file__).resolve().parents[2]


class SystemRoot:
    """Localiza e cria a estrutura de pastas do sistema."""

    def __init__(self, raiz: Path | str | None = None):
        if raiz is None:
            env = os.environ.get("AUTOTABLOIDE_ROOT")
            raiz = Path(env) if env else _raiz_projeto() / NOME_RAIZ
        self.raiz = Path(raiz)

    def criar_estrutura(self) -> "SystemRoot":
        """Cria a pasta raiz e todas as subpastas (idempotente)."""
        self.raiz.mkdir(parents=True, exist_ok=True)
        for nome in SUBPASTAS.values():
            (self.raiz / nome).mkdir(parents=True, exist_ok=True)
        return self

    def subpasta(self, chave: str) -> Path:
        """Retorna o caminho de uma subpasta pela chave lógica (ex.: 'banco')."""
        try:
            return self.raiz / SUBPASTAS[chave]
        except KeyError as exc:
            raise KeyError(
                f"Subpasta desconhecida: {chave!r}. Opções: {sorted(SUBPASTAS)}"
            ) from exc

    # Atalhos legíveis para as pastas mais usadas -----------------------------
    @property
    def banco(self) -> Path:
        return self.raiz / SUBPASTAS["banco"]

    @property
    def biblioteca_imagens(self) -> Path:
        return self.raiz / SUBPASTAS["biblioteca_imagens"]

    @property
    def layouts(self) -> Path:
        return self.raiz / SUBPASTAS["layouts"]

    @property
    def projetos(self) -> Path:
        return self.raiz / SUBPASTAS["projetos"]

    @property
    def fontes(self) -> Path:
        return self.raiz / SUBPASTAS["fontes"]

    @property
    def config(self) -> Path:
        return self.raiz / SUBPASTAS["config"]

    @property
    def backups(self) -> Path:
        return self.raiz / SUBPASTAS["backups"]

    @property
    def modelos(self) -> Path:
        return self.raiz / SUBPASTAS["modelos"]

    @property
    def logs(self) -> Path:
        return self.raiz / SUBPASTAS["logs"]

    @property
    def selos(self) -> Path:
        return self.raiz / SUBPASTAS["selos"]

    @property
    def caminho_banco(self) -> Path:
        """Caminho completo do arquivo SQLite principal."""
        return self.banco / NOME_BANCO

    def __repr__(self) -> str:
        return f"<SystemRoot raiz={self.raiz}>"
