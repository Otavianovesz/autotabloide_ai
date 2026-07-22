"""
OCR de tabela de ofertas (foto do WhatsApp -> tabela)
=====================================================
Passo 4 da Fase 3. Usa o modelo multimodal (Qwen3.5) para ler uma FOTO de uma
tabela de ofertas e devolver as linhas {descrição, preço}.

⚠️  A QUALIDADE do OCR só se prova com uma imagem real. O esqueleto e os testes
rodam com uma resposta de exemplo (MotorIAFake) — validam o encanamento.

Nota de resolução: modelos Qwen-VL rendem melhor com imagem grande (~1024 image
tokens). Se o print vier pequeno, ampliamos antes de enviar.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from app.ai.client import IAIndisponivel, MotorIA

PROMPT_OCR = (
    "Você lê uma FOTO de uma tabela de ofertas de supermercado. "
    "Devolva SOMENTE um objeto JSON com duas chaves: "
    '"validade_oferta" (o período de validade da oferta, ex: '
    '"01/07/2026 até 27/07/2026", geralmente no rodapé; null se não houver) e '
    '"linhas" (um array, um objeto por oferta: '
    '{"descricao": "<texto do produto como está na tabela>", '
    '"preco": "<preço no formato brasileiro, ex: 5,90>"}). '
    "Não invente itens nem pule itens. Ignore a coluna de quantidade/numeração. "
    "Se um preço não estiver legível, use null. "
    # bancada dos Exemplos (semana real do dono): promoção escrita em frase
    # ("leve 3 e ganhe 25% de desconto", "pão francês com 50% de desconto",
    # "lanche na chapa com 20% de desconto") era PULADA pelo modelo — e
    # pular linha em silêncio é bug (I2)
    "ATENÇÃO: promoção SEM preço numérico (desconto em %, leve-X-pague-Y, "
    "brinde) TAMBÉM é uma linha de oferta — nunca a pule: ponha o produto em "
    '"descricao" e o texto da promoção em "preco" (ex: "20% de desconto", '
    '"leve 3 pague 2"). Isso vale até quando a promoção está no meio do '
    "TEXTO CORRIDO do cabeçalho (ex: 'leve 3 sonhos e ganhe 25% de "
    "desconto' vira uma linha) — mas SÓ promoção com mecânica concreta "
    "(%, leve-X, brinde); slogan e frase de efeito não são oferta. "
    "Leia a imagem:"
)


@dataclass
class LinhaOferta:
    descricao: str
    preco: str | None = None


@dataclass
class TabelaOCR:
    """O que o OCR extrai: as linhas + a validade da OFERTA (contexto da importação)."""

    linhas: list[LinhaOferta] = field(default_factory=list)
    validade_oferta: str | None = None


def _preparar_imagem(caminho: Path, min_lado: int = 1024) -> Path:
    """Amplia a imagem se o maior lado for menor que min_lado (para o Qwen-VL)."""
    from PIL import Image

    img = Image.open(caminho)
    if max(img.size) >= min_lado:
        return caminho
    escala = min_lado / max(img.size)
    novo = img.resize((round(img.width * escala), round(img.height * escala)))
    destino = Path(tempfile.gettempdir()) / f"ocr_up_{caminho.stem}.png"
    novo.convert("RGB").save(destino)
    return destino


def _extrair_json_obj(texto: str) -> dict:
    t = texto.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:]
    ini, fim = t.find("{"), t.rfind("}")
    if ini == -1 or fim == -1:
        return {}
    try:
        dados = json.loads(t[ini : fim + 1])
    except json.JSONDecodeError:
        return {}
    return dados if isinstance(dados, dict) else {}


def ler_tabela(imagem: str | Path, motor: MotorIA, *, min_lado: int = 1024,
               status_cb=None) -> TabelaOCR:
    """Lê a foto e devolve linhas + validade da oferta. Sem IA, devolve vazio (degrada).

    ``status_cb`` (opcional) recebe as FASES honestas da leitura. Como a
    chamada de visão é ÚNICA (a resposta chega inteira no fim), progresso
    por linha durante a geração não existe de verdade — o texto diz isso em
    vez de fingir porcentagem (RG-04).
    """
    def _st(msg: str) -> None:
        if callable(status_cb):
            status_cb(msg)

    if not motor.disponivel():
        return TabelaOCR()
    _st("Preparando a imagem…")
    caminho = _preparar_imagem(Path(imagem), min_lado)
    _st("Lendo a foto com a IA — a tabela inteira é lida de uma vez; "
        "pode levar alguns minutos…")
    try:
        resposta = motor.visao(caminho, PROMPT_OCR, max_tokens=4096)
    except IAIndisponivel:
        return TabelaOCR()

    dados = _extrair_json_obj(resposta)
    linhas = []
    for d in dados.get("linhas", []):
        desc = (d.get("descricao") or "").strip()
        if desc:
            preco = d.get("preco")
            linhas.append(LinhaOferta(desc, str(preco).strip() if preco else None))

    validade = dados.get("validade_oferta")
    validade = validade.strip() if isinstance(validade, str) and validade.strip() else None
    _st(f"Foto lida: {len(linhas)} produtos encontrados")
    return TabelaOCR(linhas=linhas, validade_oferta=validade)


# --- cache de leitura (RG-04): reimportar a MESMA foto não re-roda o OCR ----------

_CACHE_VERSAO = 1
_CACHE_MAX = 30


def _cache_path() -> Path:
    from app.core.paths import SystemRoot
    return SystemRoot().config / "ocr_cache.json"


def _hash_arquivo(caminho: str | Path) -> str:
    import hashlib
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def _cache_carregar() -> dict:
    try:
        dados = json.loads(_cache_path().read_text(encoding="utf-8"))
        if dados.get("versao") == _CACHE_VERSAO:
            return dados.get("entradas", {})
    except (OSError, ValueError, AttributeError):
        pass
    return {}


def _versao_prompt() -> str:
    """Assinatura curta do PROMPT_OCR — quando o prompt evolui (bancada dos
    Exemplos: ele aprendeu promoções em %), o cache velho INVALIDA sozinho;
    sem isto, a foto relida devolvia a leitura do prompt antigo."""
    import hashlib
    return hashlib.sha1(PROMPT_OCR.encode("utf-8")).hexdigest()[:10]


def cache_consultar(caminho: str | Path, modelo_visao: str) -> TabelaOCR | None:
    """Leitura anterior da MESMA foto (mesmo conteúdo, mesmo modelo e mesmo
    PROMPT) — ou None."""
    entrada = _cache_carregar().get(_hash_arquivo(caminho))
    if not entrada or entrada.get("modelo") != modelo_visao:
        return None
    if entrada.get("prompt") != _versao_prompt():
        return None                      # prompt evoluiu: reler de verdade
    linhas = [LinhaOferta(d, p) for d, p in entrada.get("linhas", []) if d]
    if not linhas:
        return None
    return TabelaOCR(linhas=linhas,
                     validade_oferta=entrada.get("validade_oferta"))


def cache_limpar() -> int:
    """Apaga o cache de leituras (o botão das Configurações — força reler).

    É a saída para a leitura PARCIAL cacheada: o OCR não é determinístico e
    uma foto mal lida ficaria presa no cache sem isto (revisão da Onda 1).
    Devolve quantas leituras havia.
    """
    entradas = _cache_carregar()
    try:
        _cache_path().unlink(missing_ok=True)
    except OSError:
        pass
    return len(entradas)


def cache_guardar(caminho: str | Path, modelo_visao: str,
                  tabela: TabelaOCR) -> None:
    """Grava a leitura (só com linhas — falha não envenena o cache; I3: só o
    NOME do arquivo, nunca caminho de máquina). Escrita atômica; teto de
    entradas descarta a mais antiga."""
    if not tabela.linhas:
        return
    from datetime import datetime
    entradas = _cache_carregar()
    entradas[_hash_arquivo(caminho)] = {
        "linhas": [[ln.descricao, ln.preco] for ln in tabela.linhas],
        "validade_oferta": tabela.validade_oferta,
        "modelo": modelo_visao,
        "prompt": _versao_prompt(),
        "arquivo": Path(caminho).name,
        "quando": datetime.now().isoformat(timespec="seconds"),
    }
    while len(entradas) > _CACHE_MAX:
        mais_velha = min(entradas, key=lambda h: entradas[h].get("quando", ""))
        del entradas[mais_velha]
    try:
        destino = _cache_path()
        destino.parent.mkdir(parents=True, exist_ok=True)
        tmp = destino.with_suffix(".json.tmp")
        tmp.write_text(json.dumps({"versao": _CACHE_VERSAO,
                                   "entradas": entradas},
                                  ensure_ascii=False), encoding="utf-8")
        tmp.replace(destino)
    except OSError:
        pass                          # cache é conforto, nunca requisito
