"""
Cliente de IA — API compatível com OpenAI (desacoplado do LM Studio)
====================================================================
Uma interface ``MotorIA`` que a lógica usa, e um cliente real que fala HTTP com
o servidor local (LM Studio em http://localhost:1234/v1 por padrão; Ollama e
outros usam a mesma API).

Degradação elegante: se o servidor não responder, ``disponivel()`` devolve False
e as chamadas levantam ``IAIndisponivel`` — as camadas de cima caem no modo
determinístico, sem quebrar o app.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


class IAIndisponivel(RuntimeError):
    """O servidor de IA não está acessível (ou falhou na chamada)."""


@dataclass
class ConfigIA:
    """Endereço e modelos do servidor local (editável na tabela Config).

    Padrão calibrado para o setup do Otaviano (RTX 8 GB): Qwen 3.5 9B é
    multimodal, então faz OCR e texto no MESMO modelo (sem troca); o embedder
    0.6B cabe junto. O Gemma é reserva de OCR (não padrão; exige descarregar o 9B).
    """

    base_url: str = "http://127.0.0.1:1234/v1"
    api_key: str = "lm-studio"          # LM Studio ignora, mas a API exige algo
    # qwen3.5-9b com "thinking" DESLIGADO (feito no LM Studio) venceu o comparativo:
    # ~5s/item e melhor qualidade (separa marcas, categoriza). Multimodal: serve
    # texto E OCR. Gemma fica de reserva. Regra 8 GB: um chat model por vez na GPU.
    modelo_texto: str = "qwen/qwen3.5-9b"
    modelo_visao: str = "qwen/qwen3.5-9b"
    modelo_embeddings: str = "text-embedding-qwen3-embedding-0.6b"
    modelo_reserva: str = "google/gemma-4-e4b"
    timeout: float = 300.0
    # FASE 3 (passo 46): o interruptor MESTRE da aba IA — False desliga a
    # IA inteira (conciliação cai para o determinístico, OCR/enriquecer
    # indisponíveis) COM aviso nas telas, nunca em silêncio (I2).
    usar: bool = True

    @classmethod
    def da_config(cls, raiz=None) -> "ConfigIA":
        """Carrega da tabela Config (C1 do Bloco D): trocar LM Studio↔Ollama
        é editar a URL/modelos na tela, sem código. Chaves: 'ia.base_url',
        'ia.modelo_texto', 'ia.modelo_visao', 'ia.modelo_embeddings'.

        Default são (C3): banco ausente, chave ausente ou valor vazio caem
        no padrão acima — a IA nunca fica inacessível por config quebrada.
        """
        padrao = cls()
        try:
            from app.core.database import Database
            from app.core.repositories import ConfigRepositorio

            db = Database(raiz) if raiz is not None else Database()
            db.init()
            try:
                with db.Session() as s:
                    cfg = ConfigRepositorio(s)

                    def _txt(chave: str, atual: str) -> str:
                        v = cfg.get(chave)
                        return str(v).strip() if v and str(v).strip() else atual

                    return cls(
                        base_url=_txt("ia.base_url", padrao.base_url),
                        modelo_texto=_txt("ia.modelo_texto", padrao.modelo_texto),
                        modelo_visao=_txt("ia.modelo_visao", padrao.modelo_visao),
                        modelo_embeddings=_txt("ia.modelo_embeddings",
                                               padrao.modelo_embeddings),
                        usar=cfg.get("ia.usar", True) is not False,
                    )
            finally:
                db.engine.dispose()
        except Exception:
            return padrao                # config quebrada nunca derruba a IA


@runtime_checkable
class MotorIA(Protocol):
    """Contrato que a lógica de IA usa (real ou fake)."""

    def disponivel(self) -> bool: ...

    def chat(
        self,
        mensagens: list[dict],
        *,
        temperatura: float = 0.2,
        max_tokens: int = 1024,
        formato_json: bool = False,
    ) -> str: ...

    def visao(self, imagem: str | Path, prompt: str, *, max_tokens: int = 2048) -> str: ...

    def embeddings(self, textos: list[str]) -> list[list[float]]: ...


class ClienteOpenAICompat:
    """Cliente real (httpx). Import de httpx é preguiçoso para não travar os testes."""

    def __init__(self, config: ConfigIA | None = None):
        # sem config explícita, vale a da tabela Config (tela Configurações)
        self.config = config or ConfigIA.da_config()

    def _client(self):
        import httpx  # import preguiçoso

        return httpx.Client(
            base_url=self.config.base_url,
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=self.config.timeout,
        )

    def disponivel(self) -> bool:
        if not self.config.usar:      # passo 46: o interruptor mestre manda
            return False
        try:
            import httpx

            with httpx.Client(base_url=self.config.base_url, timeout=3.0) as c:
                r = c.get("/models")
                return r.status_code == 200
        except Exception:
            return False

    def listar_modelos(self) -> list[str]:
        """IDs dos modelos carregados no servidor (para conferir/ajustar o ConfigIA)."""
        try:
            import httpx

            with httpx.Client(base_url=self.config.base_url, timeout=5.0) as c:
                r = c.get("/models")
                r.raise_for_status()
                return [m["id"] for m in r.json().get("data", [])]
        except Exception:
            return []

    def _post(self, rota: str, payload: dict) -> dict:
        try:
            with self._client() as c:
                r = c.post(rota, json=payload)
                r.raise_for_status()
                return r.json()
        except Exception as exc:  # rede, timeout, HTTP...
            raise IAIndisponivel(str(exc)) from exc

    def chat(self, mensagens, *, temperatura=0.2, max_tokens=1024, formato_json=False) -> str:
        # Obs.: não enviamos response_format — servidores divergem (LM Studio exige
        # json_schema, não json_object). O JSON é garantido pelo prompt + parser robusto.
        payload: dict = {
            "model": self.config.modelo_texto,
            "messages": mensagens,
            "temperature": temperatura,
            "max_tokens": max_tokens,
        }
        dados = self._post("/chat/completions", payload)
        return dados["choices"][0]["message"]["content"]

    def visao(self, imagem, prompt, *, max_tokens=2048) -> str:
        dados_uri = _imagem_para_data_uri(Path(imagem))
        mensagens = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": dados_uri}},
                ],
            }
        ]
        payload = {
            "model": self.config.modelo_visao,
            "messages": mensagens,
            "temperature": 0.0,
            "max_tokens": max_tokens,
        }
        dados = self._post("/chat/completions", payload)
        return dados["choices"][0]["message"]["content"]

    def embeddings(self, textos: list[str]) -> list[list[float]]:
        payload = {"model": self.config.modelo_embeddings, "input": textos}
        dados = self._post("/embeddings", payload)
        return [item["embedding"] for item in dados["data"]]


def _imagem_para_data_uri(caminho: Path) -> str:
    dados = caminho.read_bytes()
    b64 = base64.b64encode(dados).decode("ascii")
    sufixo = caminho.suffix.lower().lstrip(".") or "png"
    mime = "jpeg" if sufixo in {"jpg", "jpeg"} else sufixo
    return f"data:image/{mime};base64,{b64}"
