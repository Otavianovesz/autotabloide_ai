"""
MotorIAFake — dublê de IA para os testes rodarem SEM modelo
===========================================================
⚠️  ATENÇÃO: este fake valida o **ENCANAMENTO**, não a **QUALIDADE** da IA.
Ele devolve respostas pré-combinadas (de exemplo, escritas à mão). Não prova que
o Qwen vai acertar — só que o texto entra, é parseado e volta como estrutura.
A qualidade real do enriquecimento e do OCR só se confirma com o modelo real.
"""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path


class MotorIAFake:
    def __init__(
        self,
        respostas_chat: dict[str, str] | None = None,
        respostas_visao: dict[str, str] | None = None,
        disponivel: bool = True,
        dim_embeddings: int = 64,
    ):
        # mapeia "trecho que aparece no prompt" -> resposta a devolver
        self._chat = respostas_chat or {}
        self._visao = respostas_visao or {}
        self._disp = disponivel
        self._dim = dim_embeddings
        self.chamadas: list[str] = []  # log para asserção nos testes

    def disponivel(self) -> bool:
        return self._disp

    def _casar(self, texto: str, tabela: dict[str, str]) -> str:
        for chave, resposta in tabela.items():
            if chave and chave in texto:
                return resposta
        return "{}"

    def chat(self, mensagens, *, temperatura=0.2, max_tokens=1024, formato_json=False) -> str:
        texto = " ".join(
            m.get("content", "") for m in mensagens if isinstance(m.get("content"), str)
        )
        self.chamadas.append(texto)
        return self._casar(texto, self._chat)

    def visao(self, imagem, prompt, *, max_tokens=2048) -> str:
        self.chamadas.append(prompt)
        return self._casar(prompt, self._visao)

    def embeddings(self, textos: list[str]) -> list[list[float]]:
        # vetor pseudo-determinístico a partir do hash (só para o encanamento;
        # NÃO tem significado semântico — a camada real usa o modelo de embeddings).
        saida = []
        for t in textos:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            vec = [
                struct.unpack("<H", h[i : i + 2])[0] / 65535.0
                for i in range(0, self._dim * 2, 2)
            ]
            saida.append(vec)
        return saida
