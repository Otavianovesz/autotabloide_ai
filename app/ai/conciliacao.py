"""
Conciliação de itens importados com o banco (semáforo verde/amarelo/vermelho)
=============================================================================
Cascata (reaproveita a estrutura do "Juiz" antigo, com motor reescrito):

  1. Match EXATO  — nome cru igual, ou alias já aprendido        -> VERDE
  2. Candidatos   — (embeddings, quando ligado) + FUZZY (rapidfuzz) top-K
  3. Semáforo por similaridade:
       score alto   -> VERDE
       score médio  -> AMARELO (ambíguo: chama o "juiz" IA se houver modelo)
       score baixo  -> VERMELHO (novo)

O que se valida SEM modelo: exato/alias e fuzzy são reais → o semáforo já funciona.
O "juiz" dos ambíguos usa a IA (fake por ora, claramente rotulado).

Camada de embeddings (significado): ponto de extensão pronto — entra como
pré-filtro antes do fuzzy quando escolhermos o provedor (LM Studio ou local).
É um dos "pontos em aberto" do plano (modelo de embeddings).
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.client import IAIndisponivel, MotorIA
from app.core.models import Produto, ProdutoAlias
from app.core.repositories import ProdutoRepositorio
from app.core.sanitize import REGRAS_PADRAO, RegrasSanitizacao, sanitizar


class Semaforo(str, Enum):
    VERDE = "VERDE"        # já existe (match forte)
    AMARELO = "AMARELO"    # provável — conferir
    VERMELHO = "VERMELHO"  # novo


# Peso normalizado (ex.: "1,5L", "380g") — removido antes de comparar, pois a
# unidade compartilhada infla o score e casa produtos diferentes.
_PESO_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:kg|mg|g|ml|l)\b", re.IGNORECASE)

# Palavras que não distinguem marca/produto (conectivos, embalagens, medidas).
_GENERICOS = frozenset({
    "de", "da", "do", "das", "dos", "e", "com", "para", "por", "tipo",
    "und", "un", "cx", "kit", "pct", "pet", "lt", "vd", "tp", "kg", "ml",
})


def _tokens_significativos(chave: str) -> set[str]:
    """Tokens que carregam identidade (marca, tipo) numa chave de comparação."""
    return {t for t in chave.split()
            if len(t) >= 3 and t not in _GENERICOS and not t.isdigit()}


def _divergencia(entrada_chave: str, candidato_chave: str) -> set[str]:
    """S1 da sessão ao vivo: tokens significativos do CADASTRO ausentes da
    OFERTA. Se o cadastro diz "aurora" e a oferta diz "campo largo", pode ser
    OUTRA MARCA — e divergência de marca **nunca é verde** (§14 da ordem):
    no máximo amarelo, para o humano decidir (a confirmação vira alias)."""
    return (_tokens_significativos(candidato_chave)
            - _tokens_significativos(entrada_chave))


def _chave_comparacao(texto: str) -> str:
    """Normaliza para o fuzzy: remove peso, acentos e pontuação; minúsculo.

    Casar deve ser insensível a acento e à medida — o que importa é o
    tipo+marca. Ex.: 'CAFE PILAO 500G' e 'Café Pilão ... 500g' viram a mesma base.
    """
    t = _PESO_RE.sub(" ", texto)
    t = "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9 ]", " ", t.lower())
    return re.sub(r"\s+", " ", t).strip()


def _cosseno(a: list[float], b: list[float]) -> float:
    d = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return d / (na * nb) if na and nb else 0.0


@dataclass
class Candidato:
    produto: Produto
    score: float           # 0..100


@dataclass
class LimiaresConciliacao:
    verde: float = 88.0    # score >= verde  -> VERDE
    amarelo: float = 62.0  # amarelo <= score < verde -> AMARELO
    top_k: int = 5


def limiares_de_config(session: Session) -> LimiaresConciliacao:
    """Limiares do semáforo salvos na Config (C1 do Bloco D).

    Chaves 'conciliacao.verde' e 'conciliacao.amarelo'. Default são (C3):
    ausente, não-numérico ou incoerente (verde ≤ amarelo, fora de 0–100)
    cai no padrão 88/62 — limiar quebrado NUNCA derruba a conciliação.
    """
    from app.core.repositories import ConfigRepositorio

    cfg = ConfigRepositorio(session)
    padrao = LimiaresConciliacao()
    try:
        verde = float(cfg.get("conciliacao.verde", padrao.verde))
        amarelo = float(cfg.get("conciliacao.amarelo", padrao.amarelo))
    except (TypeError, ValueError):
        return padrao
    if not (0 < amarelo < verde <= 100):
        return padrao
    return LimiaresConciliacao(verde=verde, amarelo=amarelo)


@dataclass
class Veredito:
    entrada: str
    semaforo: Semaforo
    produto: Produto | None
    candidatos: list[Candidato] = field(default_factory=list)
    confianca: float = 0.0
    motivo: str = ""
    via: str = ""          # exato | alias | fuzzy | juiz | novo


class Conciliador:
    def __init__(
        self,
        session: Session,
        motor: MotorIA | None = None,
        *,
        embedder: MotorIA | None = None,
        peso_semantico: float = 0.5,
        limiares: LimiaresConciliacao | None = None,
        regras: RegrasSanitizacao = REGRAS_PADRAO,
    ):
        self.session = session
        self.repo = ProdutoRepositorio(session)
        self.motor = motor            # None => sem "juiz" IA (só exato/fuzzy)
        self.embedder = embedder      # None => sem camada de significado (só fuzzy)
        self.peso_sem = peso_semantico
        # sem limiares explícitos, valem os da Config (ajustáveis na tela —
        # C1 do Bloco D); sem chaves na Config, o padrão 88/62 de sempre
        self.limiares = limiares or limiares_de_config(session)
        self.regras = regras
        self._corpus_cache: dict[str, int] | None = None   # 1× por lote (F12)
        # OS F11.5 #47/#81 (R-086): os sinônimos regionais (padrão + os do
        # dono na Config) entram na chave de comparação — "macaxeira" casa
        # "mandioca" no fuzzy. Falha de leitura degrada para o padrão (I2).
        try:
            from app.core.aprendizado import grupos_com_extras
            from app.core.repositories import ConfigRepositorio
            extras = ConfigRepositorio(session).get("sinonimos.regionais", [])
            self._sinonimos = grupos_com_extras(extras)
        except Exception:
            from app.core.aprendizado import SINONIMOS_REGIONAIS_PADRAO
            self._sinonimos = SINONIMOS_REGIONAIS_PADRAO

    def _chave(self, texto: str) -> str:
        """A chave de comparação já CANONIZADA pelos sinônimos regionais."""
        from app.core.aprendizado import canonizar_sinonimos
        return _chave_comparacao(canonizar_sinonimos(texto, self._sinonimos))

    # --- corpus para o fuzzy (nomes sanitizados + aliases sanitizados) ---------

    def _corpus(self) -> dict[str, int]:
        """chave de comparação -> produto_id (nomes sanitizados + aliases).

        CACHEADO por instância (FASE 12, achado do marco 5k): o Conciliador
        vive por LOTE e só LÊ o acervo — reconstruir o corpus a cada item
        custava ~0,3 s × N itens no acervo grande."""
        if self._corpus_cache is None:
            corpus: dict[str, int] = {}
            for pid, nome in self.session.execute(
                select(Produto.id, Produto.nome_sanitizado)
            ).all():
                corpus.setdefault(self._chave(nome), pid)
            for pid, alias in self.session.execute(
                select(ProdutoAlias.produto_id, ProdutoAlias.alias_raw)
            ).all():
                chave = self._chave(
                    sanitizar(alias, self.regras).nome_sanitizado)
                corpus.setdefault(chave, pid)
            self._corpus_cache = corpus
        return self._corpus_cache

    @staticmethod
    def _pontuar(q: str, chave: str) -> float:
        """Média de dois scorers: token_set (bom p/ subconjunto/palavras extras) e
        token_sort (penaliza diferença de tamanho — abreviação vira 'conferir', não
        'certo'). A média dá um spread útil sem os falsos positivos do WRatio."""
        return 0.5 * fuzz.token_set_ratio(q, chave) + 0.5 * fuzz.token_sort_ratio(q, chave)

    # quantos candidatos do fuzzy sobem à camada de SIGNIFICADO — nunca o
    # banco inteiro (a decisão travada; achado do marco 5k: gerar embeddings
    # do acervo todo custava ~73 s POR LOTE no LM local)
    TOP_EMBEDDINGS = 40

    def _candidatos(self, nome_bruto: str) -> list[Candidato]:
        q = self._chave(sanitizar(nome_bruto, self.regras).nome_sanitizado)
        corpus = self._corpus()
        if not corpus:
            return []

        # Camada FUZZY (sempre real, local): melhor score e melhor CHAVE por
        # produto — a chave vai à camada de significado dos top-K.
        fuzzy_pid: dict[int, float] = {}
        chave_pid: dict[int, str] = {}
        for chave, pid in corpus.items():
            s = self._pontuar(q, chave)
            if s > fuzzy_pid.get(pid, -1.0):
                fuzzy_pid[pid] = s
                chave_pid[pid] = chave

        # Camada de SIGNIFICADO (embeddings, quando ligada) SÓ nos TOP-K do
        # fuzzy (FASE 12): o fuzzy pré-seleciona local e barato; o vetor
        # refina o desempate — um POST pequeno, nunca o acervo inteiro.
        sem_pid: dict[int, float] = {}
        if self.embedder is not None:
            top = sorted(fuzzy_pid.items(),
                         key=lambda kv: -kv[1])[: self.TOP_EMBEDDINGS]
            try:
                textos = [q] + [chave_pid[pid] for pid, _s in top]
                vetores = self.embedder.embeddings(textos)
                qv = vetores[0]
                for (pid, _s), vec in zip(top, vetores[1:]):
                    sem_pid[pid] = _cosseno(qv, vec) * 100.0
            except Exception:
                sem_pid = {}             # sem significado: o fuzzy segura

        # Combina: quem subiu à camada de significado leva a média ponderada;
        # o resto fica com o fuzzy puro (o top-5 final sai dos top-K mesmo).
        final: dict[int, float] = {}
        for pid, fz in fuzzy_pid.items():
            if pid in sem_pid:
                final[pid] = (1 - self.peso_sem) * fz \
                    + self.peso_sem * sem_pid[pid]
            else:
                final[pid] = fz

        ordenado = sorted(final.items(), key=lambda kv: -kv[1])[: self.limiares.top_k]
        cands: list[Candidato] = []
        for pid, score in ordenado:
            produto = self.session.get(Produto, pid)
            if produto is not None:
                cands.append(Candidato(produto, float(score)))
        return cands

    # --- "juiz" IA (só nos ambíguos; usa 3–5 candidatos, nunca o banco todo) ---

    def _juiz(self, nome_bruto: str, candidatos: list[Candidato]) -> Veredito | None:
        opcoes = [c.produto.nome_sanitizado for c in candidatos]
        sistema = (
            "Você concilia um item de oferta com o cadastro. Dada a descrição bruta "
            "e uma lista curta de candidatos, responda SÓ um JSON: "
            '{"indice": <int do candidato que é o MESMO produto, ou null se for novo>, '
            '"confianca": <0..1>}.'
        )
        usuario = json.dumps(
            {"descricao": nome_bruto, "candidatos": opcoes}, ensure_ascii=False
        )
        try:
            resposta = self.motor.chat(
                [{"role": "system", "content": sistema},
                 {"role": "user", "content": usuario}],
                formato_json=True,
            )
            dados = json.loads(resposta[resposta.find("{"): resposta.rfind("}") + 1])
        except (IAIndisponivel, ValueError, json.JSONDecodeError, KeyError):
            return None

        indice = dados.get("indice")
        conf = float(dados.get("confianca", 0.0))
        if indice is None:
            return Veredito(nome_bruto, Semaforo.VERMELHO, None, candidatos, conf,
                            "juiz IA: item novo", "juiz")
        if isinstance(indice, int) and 0 <= indice < len(candidatos):
            escolhido = candidatos[indice]
            return Veredito(nome_bruto, Semaforo.VERDE, escolhido.produto, candidatos,
                            conf, "juiz IA: confirmou candidato", "juiz")
        return None

    # --- API -------------------------------------------------------------------

    def conciliar(self, nome_bruto: str) -> Veredito:
        exato = self.repo.buscar_por_nome_bruto(nome_bruto) or self.repo.buscar_por_alias(
            nome_bruto
        )
        if exato is not None:
            return Veredito(nome_bruto, Semaforo.VERDE, exato,
                            [Candidato(exato, 100.0)], 1.0,
                            "match exato (nome cru ou alias)", "exato")

        cands = self._candidatos(nome_bruto)
        if not cands:
            return Veredito(nome_bruto, Semaforo.VERMELHO, None, [], 0.0,
                            "sem candidatos no banco", "novo")

        q_chave = self._chave(sanitizar(nome_bruto, self.regras).nome_sanitizado)

        def _rebaixar_se_divergente(veredito: Veredito) -> Veredito:
            """S1: verde não-exato com termos do cadastro ausentes da oferta
            desce para AMARELO — marca diferente jamais passa sem humano."""
            if veredito.semaforo != Semaforo.VERDE or veredito.produto is None:
                return veredito
            div = _divergencia(
                q_chave, self._chave(veredito.produto.nome_sanitizado))
            if div:
                veredito.semaforo = Semaforo.AMARELO
                veredito.motivo = ("cadastro tem termos ausentes na oferta "
                                   f"({', '.join(sorted(div))}) — confira a marca")
            return veredito

        melhor = cands[0]
        if melhor.score >= self.limiares.verde:
            return _rebaixar_se_divergente(
                Veredito(nome_bruto, Semaforo.VERDE, melhor.produto, cands,
                         melhor.score / 100, "similaridade alta", "fuzzy"))

        if melhor.score >= self.limiares.amarelo:
            if self.motor is not None and self.motor.disponivel():
                veredito = self._juiz(nome_bruto, cands)
                if veredito is not None:
                    return _rebaixar_se_divergente(veredito)
            return Veredito(nome_bruto, Semaforo.AMARELO, melhor.produto, cands,
                            melhor.score / 100, "provável — conferência humana", "fuzzy")

        return Veredito(nome_bruto, Semaforo.VERMELHO, None, cands,
                        melhor.score / 100, "abaixo do limiar — provável novo", "novo")
