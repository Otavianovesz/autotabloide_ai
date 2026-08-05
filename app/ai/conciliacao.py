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
# Rodada JM (B1.1): a tabela real do dono escreve "5 Kgs", "1 LT",
# "5 LTS" — os PLURAIS/grafias cruas casam também (longas antes das
# curtas: "kgs" antes de "kg", senão o \b final barra o plural).
_PESO_RE = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*"
    r"(?:kgs?|kilos?|quilos?|mgs?|mls?|grs?|lts?|litros?|g|l)\b",
    re.IGNORECASE)

# fator para a base canônica (g / ml) — o desempate de irmãos compara
# grandezas na mesma régua ("1 kg" == "1000 g")
_FATOR_PESO = {
    "kg": 1000.0, "kgs": 1000.0, "kilo": 1000.0, "kilos": 1000.0,
    "quilo": 1000.0, "quilos": 1000.0,
    "g": 1.0, "gr": 1.0, "grs": 1.0,
    "mg": 0.001, "mgs": 0.001,
    "l": 1000.0, "lt": 1000.0, "lts": 1000.0,
    "litro": 1000.0, "litros": 1000.0,
    "ml": 1.0, "mls": 1.0,
}
# unidades que são VOLUME (base canônica "ml"); o resto é massa ("g")
_UNIDADES_VOLUME = frozenset(
    {"l", "lt", "lts", "litro", "litros", "ml", "mls"})

# QUINTUSDECIMUS/J11: candidato abaixo deste piso NÃO se exibe ao dono
# (ração de gato como sugestão para molho de tomate é pior que lista
# vazia — parece defeito e é armadilha de clique). O motor segue
# calculando os top-5 por dentro; a régua vale para a VITRINE.
PISO_CANDIDATO_EXIBIDO = 70.0


def _peso_canonico(texto: str) -> tuple[float, str] | None:
    """O peso do TEXTO na base canônica: (valor, 'g'|'ml') — None sem
    peso. "1,5L" → (1500, 'ml'); "500 g" → (500, 'g')."""
    m = _PESO_RE.search(texto or "")
    if not m:
        return None
    bruto = m.group(0).lower().replace(",", ".")
    m2 = re.match(r"([\d.]+)\s*([a-z]+)", bruto)
    if not m2:
        return None
    try:
        valor = float(m2.group(1))
    except ValueError:
        return None
    uni = m2.group(2)
    if uni not in _FATOR_PESO:
        return None
    base = "ml" if uni in _UNIDADES_VOLUME else "g"
    return valor * _FATOR_PESO[uni], base


def _peso_do_produto(produto: "Produto") -> tuple[float, str] | None:
    """O peso do CADASTRO na mesma base — do campo estruturado ou, na
    falta dele, do nome sanitizado."""
    valor = getattr(produto, "peso_valor", None)
    uni = (getattr(produto, "peso_unidade", None) or "").lower()
    if valor and uni in _FATOR_PESO:
        base = "ml" if uni in ("l", "ml") else "g"
        return float(valor) * _FATOR_PESO[uni], base
    return _peso_canonico(produto.nome_sanitizado or "")

# Palavras que não distinguem marca/produto (conectivos, embalagens, medidas).
_GENERICOS = frozenset({
    "de", "da", "do", "das", "dos", "e", "com", "para", "por", "tipo",
    "und", "un", "cx", "kit", "pct", "pet", "lt", "vd", "tp", "kg", "ml",
    "kgs", "lts", "grs", "mls", "mgs", "litro", "litros",   # Rodada JM
})


def _tokens_significativos(chave: str) -> set[str]:
    """Tokens que carregam identidade (marca, tipo) numa chave de comparação."""
    return {t for t in chave.split()
            if len(t) >= 3 and t not in _GENERICOS and not t.isdigit()}


def _divergencia(entrada_chave: str, candidato_chave: str) -> set[str]:
    """S1 da sessão ao vivo: tokens significativos do CADASTRO ausentes da
    OFERTA. Se o cadastro diz "aurora" e a oferta diz "campo largo", pode ser
    OUTRA MARCA — e divergência de marca **nunca é verde** (§14 da ordem):
    no máximo amarelo, para o humano decidir (a confirmação vira alias).

    ADENDO 30/07 (o dia a dia do dono): presença TOLERANTE — (a) o token
    do cadastro que aparece na oferta sem espaços não é ausência ("bbx"
    está em "bb x", que a chave separou); (b) o quase-igual por difflib
    ≥0,8 é erro de LEITURA do OCR ("tortuguita"×"toturguita"), não marca
    diferente. Era o rebaixamento que obrigava o dono a conferir (ou
    duplicar) item que o fuzzy já tinha reconhecido com 94+."""
    div = (_tokens_significativos(candidato_chave)
           - _tokens_significativos(entrada_chave))
    if not div:
        return div
    import difflib
    colada = entrada_chave.replace(" ", "")
    q_tokens = entrada_chave.split()
    sobra: set[str] = set()
    for t in div:
        if t in colada:
            continue
        if difflib.get_close_matches(t, q_tokens, n=1, cutoff=0.8):
            continue
        sobra.add(t)
    return sobra


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
    # F13/B7 (CI-03): piso de CONFIANÇA do juiz IA — abaixo dele o juiz
    # nunca pinta VERDE (a trava da F9: "ambíguo vira amarelo")
    juiz_confianca: float = 0.6


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
        juiz = float(cfg.get("conciliacao.juiz_confianca",
                             padrao.juiz_confianca))
    except (TypeError, ValueError):
        juiz = padrao.juiz_confianca
    if not (0 < juiz <= 1):
        juiz = padrao.juiz_confianca          # C3: inválido cai no padrão
    try:
        verde = float(cfg.get("conciliacao.verde", padrao.verde))
        amarelo = float(cfg.get("conciliacao.amarelo", padrao.amarelo))
    except (TypeError, ValueError):
        return LimiaresConciliacao(juiz_confianca=juiz)
    if not (0 < amarelo < verde <= 100):
        return LimiaresConciliacao(juiz_confianca=juiz)
    return LimiaresConciliacao(verde=verde, amarelo=amarelo,
                               juiz_confianca=juiz)


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
        status_cb=None,
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
        # Rodada JM (B1.6): a VIDA do motor é checada 1× por lote — era
        # 1 GET (timeout 3 s) por item ambíguo; em 42 itens do Jornal,
        # minutos só perguntando se o LM Studio está de pé
        self._motor_vivo: bool | None = None
        self._status = status_cb or (lambda _m: None)
        # o índice em memória: (ids, matriz numpy L2-normalizada) ou None
        self._indice_cache: tuple[list[int], object] | None = None
        self._indice_pronto = False
        self.avisos: list[str] = []   # I2: degradação NUNCA é muda
        self._embedder_morto = False  # 1ª falha desliga o lote inteiro
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

    # --- a guarda da marca (VICESIMUS-QUARTUS §2.2) ------------------------------

    def _vocab_marcas(self) -> set[str]:
        """O vocabulário de marcas do LOTE (1 consulta): o seed do
        mercado + as marcas confirmadas do acervo + as próprias da
        Config. Degrada para o seed (nunca inventa)."""
        if getattr(self, "_marcas_cache", None) is None:
            from app.core.marcas import marcas_conhecidas
            extras: list[str] = []
            try:
                from sqlalchemy import select

                from app.core.models import Produto
                from app.core.repositories import ConfigRepositorio
                for (m,) in self.session.execute(
                        select(Produto.marca).distinct()):
                    if m and str(m).strip():
                        extras.append(str(m).strip())
                extras += list(ConfigRepositorio(self.session).get(
                    "marcas.proprias", []) or [])
            except Exception:
                pass
            self._marcas_cache = marcas_conhecidas(tuple(extras))
        return self._marcas_cache

    def _marcas_de(self, texto: str) -> set[str]:
        """As marcas CONHECIDAS presentes no texto, normalizadas."""
        from app.core.marcas import _chave as chave_marca
        from app.core.marcas import marcas_no_nome
        return {chave_marca(m)
                for m in marcas_no_nome(texto or "", self._vocab_marcas())}

    def _marcas_do_produto(self, produto) -> set[str]:
        """As do CANDIDATO: as reconhecidas no nome + o campo ``marca``
        do cadastro (dado confirmado pelo dono — conta sempre)."""
        from app.core.marcas import _chave as chave_marca
        marcas = self._marcas_de(produto.nome_sanitizado or "")
        campo = chave_marca(getattr(produto, "marca", None) or "")
        if campo:
            marcas.add(campo)
        return marcas

    def _vermelho_se_marca_troca(self, veredito: Veredito,
                                 nome_bruto: str) -> Veredito:
        """§2.2: MARCA CONHECIDA DIFERENTE NUNCA CASA — o açúcar
        Itamaraty da tabela saiu impresso como Doce Dia, verde e calado.
        A irmã da J10, um degrau mais dura: quando a linha e o candidato
        têm marcas conhecidas e NENHUMA coincide, o veredito cai a
        VERMELHO (produto NOVO — o candidato fica à vista, mas nada se
        pré-aceita). Só age quando os DOIS lados têm marca reconhecida
        (sem prova não se acusa; a régua nunca inventa)."""
        if veredito.semaforo != Semaforo.VERDE or veredito.produto is None:
            return veredito
        da_linha = self._marcas_de(nome_bruto)
        do_produto = self._marcas_do_produto(veredito.produto)
        if da_linha and do_produto and not (da_linha & do_produto):
            nome_p = veredito.produto.nome_sanitizado
            veredito.semaforo = Semaforo.VERMELHO
            veredito.produto = None
            veredito.motivo = ("a marca não bate (a linha diz "
                               f"“{' / '.join(sorted(da_linha))}”; o "
                               f"cadastro “{nome_p}” é outra marca) — "
                               "parece produto NOVO")
        return veredito

    # --- corpus para o fuzzy (nomes sanitizados + aliases sanitizados) ---------

    def _corpus(self) -> dict[str, list[int]]:
        """chave de comparação -> [produto_ids] (nomes sanitizados + aliases).

        CACHEADO por instância (FASE 12, achado do marco 5k): o Conciliador
        vive por LOTE e só LÊ o acervo — reconstruir o corpus a cada item
        custava ~0,3 s × N itens no acervo grande.

        ADENDO 30/07: a chave (sem peso, de propósito) COLIDE produtos
        irmãos que só diferem pela gramatura — era ``setdefault`` e o 2º
        produto ficava INVISÍVEL ("não sabe puxar dois itens diferentes",
        a queixa do dono). Agora todos os pids da chave são candidatos e
        o peso da OFERTA desempata em ``_candidatos``."""
        if self._corpus_cache is None:
            corpus: dict[str, list[int]] = {}
            # F13/E5 (CI-01): a conciliação não enxergava a LIXEIRA —
            # produto excluído (soft-delete) voltava VERDE, calado
            for pid, nome in self.session.execute(
                select(Produto.id, Produto.nome_sanitizado)
                .where(Produto.excluido_em.is_(None))
            ).all():
                grupo = corpus.setdefault(self._chave(nome), [])
                if pid not in grupo:
                    grupo.append(pid)
            for pid, alias in self.session.execute(
                select(ProdutoAlias.produto_id, ProdutoAlias.alias_raw)
            ).all():
                chave = self._chave(
                    sanitizar(alias, self.regras).nome_sanitizado)
                grupo = corpus.setdefault(chave, [])
                if pid not in grupo:
                    grupo.append(pid)
            self._corpus_cache = corpus
        return self._corpus_cache

    @staticmethod
    def _pontuar(q: str, chave: str) -> float:
        """Média de dois scorers: token_set (bom p/ subconjunto/palavras extras) e
        token_sort (penaliza diferença de tamanho — abreviação vira 'conferir', não
        'certo'). A média dá um spread útil sem os falsos positivos do WRatio."""
        return 0.5 * fuzz.token_set_ratio(q, chave) + 0.5 * fuzz.token_sort_ratio(q, chave)

    # tamanho do lote de textos por POST ao construir o índice (1ª vez ou
    # produtos novos/renomeados) — nunca o acervo inteiro num request só
    LOTE_EMBED = 128

    def _modelo_embed(self) -> str:
        cfg = getattr(self.embedder, "config", None)
        return getattr(cfg, "modelo_embeddings", "") or type(
            self.embedder).__name__

    def _embedder_falhou(self, exc: Exception) -> None:
        """1ª falha DESLIGA a camada pro lote inteiro (nada de re-tentar o
        POST condenado a cada item) e AVISA (I2) — antes, o except engolia
        e o dono acreditava que o significado estava trabalhando."""
        self._embedder_morto = True
        aviso = ("A camada de significado ficou DESLIGADA neste lote "
                 "(o modelo de embeddings não respondeu: "
                 f"{type(exc).__name__}). A conferência seguiu por "
                 "semelhança de texto — confira os amarelos com atenção.")
        if aviso not in self.avisos:
            self.avisos.append(aviso)

    def _indice(self) -> tuple[list[int], object] | None:
        """O índice de significado do acervo: (ids, matriz numpy float32
        L2-normalizada, uma linha por produto), vindo da tabela
        ``produto_embeddings``. Embeda SÓ o que falta/mudou (por CHAVE), em
        lotes, UMA vez — depois é leitura + matemática local. Falha do
        embedder → None + aviso (I2), e o fuzzy segura o lote sozinho."""
        if self._indice_pronto:
            return self._indice_cache
        self._indice_pronto = True
        self._indice_cache = None
        if self.embedder is None or self._embedder_morto:
            return None
        import struct

        from app.core.models import EmbeddingProduto
        modelo = self._modelo_embed()
        chaves: dict[int, str] = {}
        for pid, nome in self.session.execute(
                select(Produto.id, Produto.nome_sanitizado)).all():
            chaves[pid] = self._chave(nome or "")
        if not chaves:
            return None
        prontos: dict[int, list[float]] = {}
        for row in self.session.execute(select(EmbeddingProduto)).scalars():
            if (row.modelo == modelo and chaves.get(row.produto_id)
                    == row.chave and row.dim):
                prontos[row.produto_id] = list(struct.unpack(
                    f"<{row.dim}f", row.vetor))
        faltam = [pid for pid in chaves if pid not in prontos]
        try:
            for i in range(0, len(faltam), self.LOTE_EMBED):
                lote = faltam[i:i + self.LOTE_EMBED]
                if len(faltam) > self.LOTE_EMBED:    # a 1ª vez tem VOZ
                    self._status(
                        "Preparando o índice de significado (uma vez só): "
                        f"{i + len(lote)}/{len(faltam)} produtos…")
                vecs = self.embedder.embeddings([chaves[p] for p in lote])
                for pid, vec in zip(lote, vecs):
                    prontos[pid] = vec
                    row = self.session.get(EmbeddingProduto, pid)
                    if row is None:
                        row = EmbeddingProduto(produto_id=pid, vetor=b"")
                        self.session.add(row)
                    row.modelo = modelo
                    row.chave = chaves[pid]
                    row.dim = len(vec)
                    row.vetor = struct.pack(f"<{len(vec)}f", *vec)
            if faltam:
                self.session.commit()
        except Exception as exc:
            self._embedder_falhou(exc)
            return None
        try:
            import numpy as np
            ids = list(prontos)
            m = np.asarray([prontos[p] for p in ids], dtype=np.float32)
            normas = np.linalg.norm(m, axis=1, keepdims=True)
            normas[normas == 0] = 1.0
            self._indice_cache = (ids, m / normas)
        except ImportError:
            self._indice_cache = (list(prontos), prontos)  # fallback puro
        return self._indice_cache

    def _candidatos(self, nome_bruto: str) -> list[Candidato]:
        q = self._chave(sanitizar(nome_bruto, self.regras).nome_sanitizado)
        corpus = self._corpus()
        if not corpus:
            return []

        # Camada FUZZY (sempre real, local): melhor score por produto
        # (nomes E aliases entram no corpus; irmãos da mesma chave
        # entram TODOS — adendo 30/07)
        fuzzy_pid: dict[int, float] = {}
        for chave, pids in corpus.items():
            s = self._pontuar(q, chave)
            for pid in pids:
                if s > fuzzy_pid.get(pid, -1.0):
                    fuzzy_pid[pid] = s

        # Camada de SIGNIFICADO sobre o ACERVO INTEIRO, via índice
        # persistido (frota F12): cosseno local contra os vetores prontos —
        # 1 POST pequeno por item (só a consulta), nunca o corpus de novo.
        # O corte top-K anterior deixava o par certo de fora ("mamão
        # papaya"×"papaia formosa") e misturava DUAS escalas no ranking.
        sem_pid: dict[int, float] = {}
        indice = self._indice()
        if indice is not None and not self._embedder_morto:
            try:
                qv = self.embedder.embeddings([q])[0]
                ids, matriz = indice
                if isinstance(matriz, dict):        # fallback sem numpy
                    for pid in ids:
                        sem_pid[pid] = _cosseno(qv, matriz[pid]) * 100.0
                else:
                    import numpy as np
                    v = np.asarray(qv, dtype=np.float32)
                    n = float(np.linalg.norm(v)) or 1.0
                    cos = matriz @ (v / n)
                    for pid, c in zip(ids, cos):
                        sem_pid[pid] = float(c) * 100.0
            except Exception as exc:
                self._embedder_falhou(exc)
                sem_pid = {}

        # Combina numa escala SÓ: com significado ligado, TODO produto leva
        # a média ponderada (produto sem vetor conta sem=0 — se quase nada
        # tem vetor, o índice inteiro é descartado com aviso lá em cima);
        # sem significado, fuzzy puro para todos.
        final: dict[int, float] = {}
        for pid, fz in fuzzy_pid.items():
            if sem_pid:
                final[pid] = (1 - self.peso_sem) * fz \
                    + self.peso_sem * sem_pid.get(pid, 0.0)
            else:
                final[pid] = fz

        # ADENDO 30/07: o PESO da oferta desempata os irmãos de chave —
        # "PAO DE QUEIJO 1KG" prefere o cadastro de 1 kg ao de 500 g
        # (bônus/pena pequenos, só no topo do ranking: reordenam gêmeos
        # sem atropelar diferenças reais de texto)
        topo = sorted(final.items(),
                      key=lambda kv: -kv[1])[: self.limiares.top_k * 2]
        peso_q = _peso_canonico(nome_bruto)
        ajustado: list[tuple[int, float]] = []
        for pid, score in topo:
            produto = self.session.get(Produto, pid)
            if produto is None:
                continue
            if peso_q is not None:
                pp = _peso_do_produto(produto)
                if pp is not None:
                    score += 2.5 if pp == peso_q else -2.5
            ajustado.append((pid, score))
        ordenado = sorted(ajustado,
                          key=lambda kv: -kv[1])[: self.limiares.top_k]
        cands: list[Candidato] = []
        for pid, score in ordenado:
            produto = self.session.get(Produto, pid)
            if produto is not None:
                cands.append(Candidato(produto, float(min(100.0, score))))
        return cands

    def categoria_do_vizinho(self, nome_bruto: str,
                             piso: float | None = None):
        """F13/D4 (VC-051): a categoria do VIZINHO mais parecido — a linha
        que a conciliação sempre calculou e jogava fora. DOIS degraus
        honestos: embeddings quando o LM responde, fuzzy puro sem ele (o
        D4 não herda o ponto cego C-03 que veio consertar). Devolve
        (nome_da_categoria | None, score); abaixo do piso (padrão: o
        limiar do amarelo) não há palpite. UMA fonte para o lote, a
        conciliação e a criação (a lição do B6: nunca três receitas).
        Rodada JM (B1.6): o miolo virou `categoria_dos_candidatos` —
        quem JÁ tem a lista do veredito não refaz fuzzy+embedding."""
        piso = self.limiares.amarelo if piso is None else piso
        return categoria_dos_candidatos(self._candidatos(nome_bruto), piso)

    def _motor_ok(self) -> bool:
        """Rodada JM (B1.6): o GET de vida do motor vale para o LOTE
        inteiro (a vida do cache é a vida do Conciliador — um por
        importação). Se o LM cair NO MEIO do lote, o juiz falha e o
        item degrada a amarelo pelo caminho de sempre (I2)."""
        if self.motor is None:
            return False
        if self._motor_vivo is None:
            self._motor_vivo = bool(self.motor.disponivel())
        return self._motor_vivo

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
        piso = self.limiares.juiz_confianca
        if indice is None:
            if conf < piso:
                # F13/B7: "é novo" com confiança baixa é AMBÍGUO — vira
                # amarelo com o melhor palpite (a trava da F9), nunca um
                # vermelho que cria produto novo por chute
                return Veredito(nome_bruto, Semaforo.AMARELO,
                                candidatos[0].produto, candidatos, conf,
                                f"juiz IA inseguro (confiança {conf:.2f}) — "
                                "confira se é novo mesmo", "juiz")
            return Veredito(nome_bruto, Semaforo.VERMELHO, None, candidatos, conf,
                            "juiz IA: item novo", "juiz")
        if isinstance(indice, int) and 0 <= indice < len(candidatos):
            escolhido = candidatos[indice]
            if conf < piso:
                # F13/B7 (CI-03): a confiança era LIDA e nunca comparada —
                # o juiz pintava VERDE com 0,05. Abaixo do piso, o humano
                # confirma (amarelo com o candidato escolhido à vista).
                return Veredito(nome_bruto, Semaforo.AMARELO,
                                escolhido.produto, candidatos, conf,
                                f"juiz IA inseguro (confiança {conf:.2f}) — "
                                "confirme o candidato", "juiz")
            return Veredito(nome_bruto, Semaforo.VERDE, escolhido.produto, candidatos,
                            conf, "juiz IA: confirmou candidato", "juiz")
        return None

    # --- API -------------------------------------------------------------------

    def conciliar(self, nome_bruto: str) -> Veredito:
        exato = self.repo.buscar_por_nome_bruto(nome_bruto) or self.repo.buscar_por_alias(
            nome_bruto
        )
        if exato is not None:
            v = Veredito(nome_bruto, Semaforo.VERDE, exato,
                         [Candidato(exato, 100.0)], 1.0,
                         "match exato (nome cru ou alias)", "exato")
            # VICESIMUS-QUARTUS §2.2: nem o ALIAS passa verde com marca
            # trocada — foi exatamente por um alias (confirmação errada
            # de ontem) que o Itamaraty virou Doce Dia calado. A escolha
            # do dono segue valendo (o vínculo fica), mas NUNCA calada:
            # desce a AMARELO com o conflito dito, todo import.
            da_linha = self._marcas_de(nome_bruto)
            do_produto = self._marcas_do_produto(exato)
            if da_linha and do_produto and not (da_linha & do_produto):
                v.semaforo = Semaforo.AMARELO
                v.motivo = ("o atalho aprendido liga marcas DIFERENTES "
                            f"(a linha diz “{' / '.join(sorted(da_linha))}”; "
                            f"o cadastro é “{exato.nome_sanitizado}”) — "
                            "confirme, ou desfaça o vínculo")
            return v

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

        def _guardas_do_verde(veredito: Veredito) -> Veredito:
            """§2.2 (marca conhecida diferente → VERMELHO) + S1
            (divergência de termos) + J10 (peso/volume) — as guardas que
            impedem um verde calado errado. A da marca roda PRIMEIRO:
            marca trocada não é "conferir", é outro produto."""
            veredito = self._vermelho_se_marca_troca(veredito, nome_bruto)
            return _rebaixar_se_qualificador_perdido(
                _rebaixar_se_peso_diverge(
                    _rebaixar_se_divergente(veredito), nome_bruto),
                nome_bruto)

        melhor = cands[0]
        if melhor.score >= self.limiares.verde:
            return _guardas_do_verde(
                Veredito(nome_bruto, Semaforo.VERDE, melhor.produto, cands,
                         melhor.score / 100, "similaridade alta", "fuzzy"))

        if melhor.score >= self.limiares.amarelo:
            if self._motor_ok():
                veredito = self._juiz(nome_bruto, cands)
                if veredito is not None:
                    return _guardas_do_verde(veredito)
            return Veredito(nome_bruto, Semaforo.AMARELO, melhor.produto, cands,
                            melhor.score / 100, "provável — conferência humana", "fuzzy")

        return Veredito(nome_bruto, Semaforo.VERMELHO, None, cands,
                        melhor.score / 100, "abaixo do limiar — provável novo", "novo")


# VICESIMUS-QUARTUS §2.3 (o Toscana que sumiu): qualificadores QUE
# VENDEM — inequívocos no domínio (o mesmo critério conservador da
# ortografia; na dúvida, a palavra NÃO entra). A oferta que os declara
# não pode casar calada com um cadastro genérico.
_QUALIFICADORES_QUE_VENDEM = frozenset({
    "toscana", "calabresa", "defumada", "defumado",
})


def _rebaixar_se_qualificador_perdido(veredito: Veredito,
                                      nome_bruto: str) -> Veredito:
    """§2.3: a Linguiça Perdigão TOSCANA casou verde com o cadastro
    "Linguiça Perdigão" e o Toscana SUMIU da página — o S1 só olhava a
    direção cadastro→oferta. O espelho, vocabulário-guiado: token da
    OFERTA que é qualificador conhecido e não está no candidato
    rebaixa a AMARELO com o motivo dito (nunca uma régua genérica —
    a oferta real é cheia de ruído; só o inequívoco acusa)."""
    if veredito.semaforo != Semaforo.VERDE or veredito.produto is None:
        return veredito
    da_oferta = _tokens_significativos(_chave_comparacao(nome_bruto))
    do_cad = _tokens_significativos(
        _chave_comparacao(veredito.produto.nome_sanitizado or ""))
    perdidos = (da_oferta & _QUALIFICADORES_QUE_VENDEM) - do_cad
    if perdidos:
        veredito.semaforo = Semaforo.AMARELO
        veredito.motivo = ("a oferta diz "
                           f"“{', '.join(sorted(perdidos))}” e o cadastro "
                           "não — confira se é o mesmo produto")
    return veredito


def _rebaixar_se_peso_diverge(veredito: Veredito,
                              nome_bruto: str) -> Veredito:
    """QUINTUSDECIMUS/J10: peso/volume divergente entre a oferta e o
    candidato REBAIXA o verde a amarelo — o Kitubaina de 1,6 L casou
    calado com o cadastro de 1,3 L. O desempate do ADENDO 30/07 escolhe
    ENTRE candidatos; esta guarda REJEITA quando até o melhor diverge.
    Só age quando os DOIS lados têm medida (sem medida não há prova).
    O match EXATO/alias não passa por aqui — a escolha do dono vale."""
    if veredito.semaforo != Semaforo.VERDE or veredito.produto is None:
        return veredito
    pq = _peso_canonico(nome_bruto)
    pp = _peso_do_produto(veredito.produto)
    if pq is None or pp is None or pq == pp:
        return veredito
    m = _PESO_RE.search(nome_bruto)
    lado_oferta = m.group(0).strip() if m else "?"
    p = veredito.produto
    if p.peso_valor is not None and p.peso_unidade:
        lado_banco = f"{p.peso_valor:g}{p.peso_unidade}"
    else:
        m2 = _PESO_RE.search(p.nome_sanitizado or "")
        lado_banco = m2.group(0).strip() if m2 else "?"
    veredito.semaforo = Semaforo.AMARELO
    veredito.motivo = (f"o peso/volume não bate ({lado_oferta} × "
                       f"{lado_banco}) — confira se é o mesmo produto")
    return veredito


def categoria_dos_candidatos(candidatos: list[Candidato],
                             piso: float) -> tuple[str | None, float]:
    """Rodada JM (B1.6): a categoria do vizinho a partir de uma lista de
    candidatos JÁ CALCULADA (ordenada por score) — o veredito da
    conciliação carrega os top-5; refazer fuzzy+embedding por item era
    metade da "demora" que o dono notou. Abaixo do ``piso`` não há
    palpite (mesma régua do `categoria_do_vizinho`, uma fonte só)."""
    for cand in candidatos or []:
        if cand.score < piso:
            break                     # ordenado: dali para baixo não serve
        cat = getattr(cand.produto, "categoria", None)
        if cat is not None:
            return cat.nome, float(cand.score)
    return None, 0.0


def exclusividade_de_lote(vereditos: list[Veredito]) -> None:
    """ADENDO 30/07 (o dia a dia do dono): duas linhas do MESMO lote não
    casam VERDES com o mesmo produto em silêncio — era assim que o OCR
    "puxava" dois itens diferentes para o mesmo registro. A linha de
    menor confiança desce a AMARELO com o motivo dito; o dono decide
    qual é qual (e o vínculo forçado resolve a outra)."""
    por_pid: dict[int, list[Veredito]] = {}
    for v in vereditos:
        if v.semaforo == Semaforo.VERDE and v.produto is not None:
            por_pid.setdefault(v.produto.id, []).append(v)
    for grupo in por_pid.values():
        if len(grupo) < 2:
            continue
        grupo.sort(key=lambda v: -float(v.confianca or 0.0))
        for v in grupo[1:]:
            v.semaforo = Semaforo.AMARELO
            v.motivo = ("outra linha desta importação já casou com este "
                        "produto — confira qual é qual")
