"""
Serviço da Mesa (headless)
==========================
A lógica da tela Mesa sem Qt: importar (tabela/foto), conciliar com o banco
(semáforo), criar item novo (enriquecer + candidatos de imagem), finalizar a
criação (banco + biblioteca). Tudo devolve **dados planos** (ItemMesa) — os
workers da UI chamam estas funções e os diálogos só exibem.

Degradação combinada: sem LM Studio → foto/OCR indisponível (tabela funciona;
nome sai só sanitizado); sem rede → item sem candidatos de imagem.
"""

from __future__ import annotations

import tempfile
import uuid as _uuid_mod
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable

from app.core.database import Database
from app.core.paths import SystemRoot

StatusCb = Callable[[str], None]

_EXT_IMAGEM = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


@dataclass
class ItemMesa:
    """Uma linha da oferta na Mesa (dados planos, prontos para a UI)."""

    descricao: str                 # como veio da tabela/foto
    preco: str | None              # "17,71" (texto, como veio) — o "por" da oferta
    semaforo: str                  # VERDE | AMARELO | VERMELHO
    nome: str                      # nome que vai para o tabloide
    produto_id: int | None = None
    imagem: str | None = None      # caminho ABSOLUTO da imagem atual (ou None)
    mais18: bool = False
    via: str = ""                  # exato | alias | fuzzy | juiz | novo | banco
    score: float = 0.0
    candidato_nome: str = ""       # melhor palpite do banco (para o 🟡)
    preco_de: str | None = None    # preço vigente no banco (o "de" do cartaz)
    validade: str | None = None    # validade do ITEM (cartaz, perto de vencer)
    unidade: str | None = None     # peso/medida ("500g") p/ a região UNIDADE
    categoria: str | None = None   # F8: p/ agrupar ("Outros" quando vazia)
    # F7.1 (Etapa C do Bloco E): vários sabores/fragrâncias num slot.
    # `imagens` NÃO-vazia é a lista COMPLETA e ordenada que o slot desenha
    # (substitui `imagem` no compositor — F4.5); vazia = foto única de sempre.
    imagens: list = field(default_factory=list)
    arranjo: str | None = None     # ModoArranjo.value; None = LEQUE (padrão)
    # F7.2 (Etapa D): item COMPOSTO ("Camil e Rei") — os DOIS itens de origem
    # guardados INTEIROS (to_dict), para o "separar" devolver exatamente o
    # que existia. Vazio = item normal. O composto tem uid PRÓPRIO: o mapa
    # continua 1 slot → 1 uid, sempre.
    origem_composto: list = field(default_factory=list)
    # RG-41: código de barras (da tabela importada ou do banco) — chave da
    # cascata de imagem (Open Food Facts antes do ddgs).
    ean: str | None = None
    # RG-33: selos personalizados escolhidos PARA ESTE item (nomes do
    # gestor) — os automáticos (+18/Qualidade) seguem por flag, como sempre.
    selos: list = field(default_factory=list)
    # R-070 (Fase 7): multi-preço "3 por R$10" — texto do FORMATO de promoção
    # por quantidade; quando presente, a região de preço desenha ele (não o
    # Decimal) e o pré-voo o trata como preço (não "sem preço").
    multi_preco: str | None = None
    # R-071 (Fase 7): observação por item ("limite 2 por cliente") — texto
    # OPCIONAL que vira uma região condicional (papel OBSERVACAO): só desenha
    # se preenchida; vazia não é problema no pré-voo (não-ocupável, lei da casa).
    observacao: str | None = None
    # Identidade estável do item (invariante I1) — o mapa slot→item usa o uid.
    uid: str = field(default_factory=lambda: _uuid_mod.uuid4().hex)

    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ItemMesa":
        from dataclasses import fields
        chaves = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in chaves})


@dataclass
class ResultadoMesa:
    itens: list[ItemMesa] = field(default_factory=list)
    validade_oferta: str | None = None
    # RG-04 (revisão): o cache-hit do OCR vira TOAST na tela — o status do
    # overlay era sobrescrito em ms e o reaproveitamento ficava invisível
    aviso: str | None = None
    # R-052 (Fase 7): o print/tabela ORIGINAL — a conciliação em tela cheia
    # mostra a foto ao lado (quando a fonte é imagem). None p/ tabela de texto.
    caminho_fonte: str | None = None


def preco_decimal(txt: str | None) -> Decimal | None:
    """Parser de preço à prova de milhar, lixo e AMBIGUIDADE (P0.3 + P0.3b).

    Aceita "R$ 1.299,00", "1.299", "17,7", "<> R$ 17,71", "1,299.00", "5.90",
    "R$ 5,90 UN". Texto com MAIS de um número ("2x 5,00", "3 por 10,00") é
    ambíguo → None: valor ERRADO é pior que ausente (I2) — fundir os dígitos
    produziria 25,00/310,00; devolvendo None, o pré-voo acusa e o usuário decide.
    No número único: o ÚLTIMO separador com 1–2 dígitos depois é o decimal; os
    demais são milhar.
    """
    if txt is None:
        return None
    import re
    # P0.3b: tokens numéricos do texto ORIGINAL (nunca fundir grupos de dígitos)
    tokens = [t for t in re.findall(r"[\d.,]+", str(txt)) if re.search(r"\d", t)]
    if len(tokens) != 1:
        return None            # nenhum número, ou mais de um (ambíguo)
    s = tokens[0].strip(".,")   # pontuação de borda: "10,00." no fim da frase
    if not s or not re.search(r"\d", s):
        return None
    ultimo = max(s.rfind(","), s.rfind("."))
    if ultimo == -1:
        inteiro, decimal = s, ""
    else:
        depois = s[ultimo + 1:]
        if 1 <= len(depois) <= 2 and depois.isdigit():
            inteiro, decimal = s[:ultimo], depois      # separador decimal
        else:
            inteiro, decimal = s, ""                   # era milhar (ex.: "1.299")
    inteiro = re.sub(r"[.,]", "", inteiro)             # remove milhares
    if not inteiro.isdigit() or (decimal and not decimal.isdigit()):
        return None
    try:
        return Decimal(f"{inteiro}.{decimal}" if decimal else inteiro)
    except InvalidOperation:
        return None


def _preco_texto(valor) -> str | None:
    """Decimal do banco → '12,34' (o formato de exibição do app)."""
    return f"{valor:.2f}".replace(".", ",") if valor is not None else None


def _qtd_texto(valor) -> str:
    """Decimal de peso → texto limpo, pt-BR (S2 da sessão ao vivo).

    Decimal('200.000') NÃO normaliza com ':g' (saía "200.000g" no tabloide!).
    Normaliza de verdade: 200.000→"200", 1.500→"1,5", 0.35→"0,35"."""
    from decimal import Decimal
    d = Decimal(valor).normalize()
    texto = f"{d:f}"
    return texto.replace(".", ",")


def _imagem_absoluta(caminho_rel: str | None) -> str | None:
    if not caminho_rel:
        return None
    abs_ = SystemRoot().biblioteca_imagens / caminho_rel
    return str(abs_) if abs_.exists() else None


def _motor_se_disponivel():
    from app.ai.client import ClienteOpenAICompat

    motor = ClienteOpenAICompat()
    return motor if motor.disponivel() else None


# --- catálogo (Almoxarifado) -----------------------------------------------------

def _produto_plano(p) -> dict:
    """Produto ORM → linha plana para a UI (com semáforo de qualidade)."""
    d = {
        "id": p.id,
        "nome": p.nome_sanitizado,
        "nome_bruto": p.nome_bruto,
        "marca": p.marca or "",
        "sabor": p.sabor or "",
        "peso_valor": _qtd_texto(p.peso_valor) if p.peso_valor is not None else "",
        "peso_unidade": p.peso_unidade or "",
        "preco": _preco_texto(p.preco_atual),
        "categoria": p.categoria.nome if p.categoria else "",
        "validade": p.validade_item.strftime("%d/%m/%Y") if p.validade_item else "",
        "alcool": bool(p.bebida_alcoolica),
        "mais18": bool(p.selo_mais18),
        "marca_propria": bool(p.marca_propria),
        "ean": p.ean or "",                    # RG-41
        "imagem": _imagem_absoluta(p.caminho_imagem),
        "imagens": imagens_do_produto(p),      # RG-28: sabores do acervo
    }
    d["qualidade"] = qualidade_produto(d)
    return d


def qualidade_produto(d: dict) -> str:
    """Semáforo do Image Doctor: 🔴 sem imagem · 🟡 dados incompletos · 🟢 ok."""
    if not d.get("imagem"):
        return "VERMELHO"
    if not d.get("preco") or not d.get("categoria"):
        return "AMARELO"
    return "VERDE"


def listar_catalogo(offset: int = 0, limite: int = 50, texto: str = "") -> list[dict]:
    """Página do catálogo (para o modelo virtualizado do Almoxarifado)."""
    from app.core.repositories import ProdutoRepositorio

    db = Database().init()
    try:
        with db.Session() as s:
            repo = ProdutoRepositorio(s)
            rows = (repo.buscar(texto, limit=limite, offset=offset) if texto
                    else repo.listar(limit=limite, offset=offset))
            return [_produto_plano(p) for p in rows]
    finally:
        db.engine.dispose()


def editar_produto(produto_id: int, **campos) -> dict:
    """Edita e devolve a linha plana atualizada (a tela mostra na hora).

    F8.1: categoria editada AQUI é gesto de HUMANO — fica marcada e nenhum
    passe de IA a sobrescreve depois.
    """
    from app.core.modo import exigir_escrita
    exigir_escrita()                 # R-131: PC da loja não edita
    from app.core.repositories import ProdutoRepositorio

    if "categoria" in campos:
        campos["categoria_origem"] = "humano" if campos["categoria"] else None
    db = Database().init()
    try:
        with db.Session() as s:
            repo = ProdutoRepositorio(s)
            repo.editar(produto_id, **campos)
            s.commit()
            return _produto_plano(repo.get(produto_id))
    finally:
        db.engine.dispose()


def excluir_produtos(ids: list[int]) -> None:
    """FASE 2 (passo 82): excluir da UI é SOFT — lixeira de 30 dias no
    Cofre (as fotos da biblioteca ficam no lugar até a purga)."""
    from app.core.modo import exigir_escrita
    exigir_escrita()                 # R-131: PC da loja não edita
    from app.core.lixeira import excluir_suave
    for pid in ids:
        excluir_suave("produto", pid)


def buscar_candidatos(nome: str, status_cb: StatusCb, n: int = 6) -> list[str]:
    """Candidatos de imagem para TROCAR a foto (sem enriquecer o nome)."""
    termo = remover_marcas_do_termo(nome)   # RG-30
    status_cb("Buscando imagem…")
    from app.images.busca import BaixadorWeb, buscar_imagens

    staging = Path(tempfile.mkdtemp(prefix="atb_troca_"))
    try:
        r = buscar_imagens(termo, BaixadorWeb(min_lado_hint=300), staging,
                           n=n, min_lado=300)
        return [str(c.caminho) for c in r.candidatos]
    except Exception:
        return []


# --- RG-33: selos personalizados do usuário ("Muito Barato", "Destaque"…) ----------


def selos_disponiveis() -> list[dict]:
    """Os selos MANUAIS ativos do gestor: [{nome, arquivo, canto}] —
    arquivo RELATIVO à pasta selos/ (I3); registro cuja arte sumiu do
    disco fica na lista (a composição desenha o badge genérico e o dono
    percebe — nunca some).

    FASE 3 (Bloco G): a fonte virou a TABELA ``selos`` (a Config legada
    é importada pela migração idempotente, que roda aqui de carona)."""
    from app.core.selos import listar_selos, migrar_selos
    try:
        db = Database().init()
        try:
            with db.Session() as s:
                migrar_selos(s)                     # passo 64: idempotente
                s.commit()
                return [{"nome": x.nome, "arquivo": x.arquivo or "",
                         "canto": x.canto}
                        for x in listar_selos(s, apenas_ativos=True)
                        if x.tipo == "manual"]
        finally:
            db.engine.dispose()
    except Exception:
        return []


def adicionar_selo_personalizado(nome: str, arquivo_origem: str,
                                 canto: str = "SUPERIOR_DIREITO") -> None:
    """Copia a arte (PNG) para <raiz>/selos/ e registra na Config."""
    import re
    import shutil

    from app.core.models import Selo as SeloModelo
    from app.core.selos import criar_manual, migrar_selos

    pasta = SystemRoot().selos
    pasta.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "_", nome.lower()).strip("_") or "selo"
    destino = pasta / f"{slug}.png"
    from PIL import Image
    Image.open(arquivo_origem).convert("RGBA").save(destino)   # normaliza PNG
    db = Database().init()
    try:
        with db.Session() as s:
            migrar_selos(s)
            velho = s.query(SeloModelo).filter_by(nome=nome).one_or_none()
            if velho is not None:
                velho.arquivo, velho.canto = destino.name, canto
            else:
                criar_manual(s, nome, destino.name, canto)
            s.commit()
    finally:
        db.engine.dispose()


def remover_selo_personalizado(nome: str) -> None:
    """Tira do registro (a arte fica em selos/ — projetos antigos a usam)."""
    from app.core.models import Selo as SeloModelo
    from app.core.selos import excluir_selo
    db = Database().init()
    try:
        with db.Session() as s:
            selo = s.query(SeloModelo).filter_by(nome=nome).one_or_none()
            if selo is not None:
                excluir_selo(s, selo.id)
            s.commit()
    finally:
        db.engine.dispose()


def selos_do_item(nomes: list[str], registro: list[dict] | None = None):
    """Nomes escolhidos no item → objetos ``Selo`` (o passe final por
    âncora desenha — selo NUNCA vira slot/região: lei da casa por
    construção, com teste provando ocupável/pré-voo imunes)."""
    from app.rendering.selos import Canto, Selo

    registro = registro if registro is not None else selos_disponiveis()
    por_nome = {r["nome"]: r for r in registro}
    saida = []
    for nome in nomes or []:
        r = por_nome.get(nome)
        if r is None:
            continue                    # selo removido do gestor: some do item
        try:
            canto = Canto(r.get("canto") or "SUPERIOR_DIREITO")
        except ValueError:
            canto = Canto.SUPERIOR_DIREITO
        saida.append(Selo(tipo=nome, canto=canto,
                          imagem_path=str(SystemRoot().selos / r["arquivo"])))
    return saida


from functools import lru_cache


@lru_cache(maxsize=1)
def _upscaler_real(modelo_path: str):
    """O Real-ESRGAN carrega UMA vez por sessão (o .pth pesa ~64 MB)."""
    from app.images.upscale import UpscalerRealESRGAN
    return UpscalerRealESRGAN(modelo_path)


def aquecer_upscaler() -> bool:
    """OS F11.5 #80: pré-aquece o Real-ESRGAN pós-boot (como o rembg, RG-02) —
    o 1º cartaz da sessão não paga a carga do .pth. Sem o modelo no disco,
    não faz nada (False)."""
    modelo = SystemRoot().modelos / "RealESRGAN_x4plus.pth"
    if not modelo.exists():
        return False
    _upscaler_real(str(modelo))
    return True


def upscale_para_cartaz(caminho: str, lado_alvo_px: int,
                        status_cb: StatusCb) -> str:
    """RG-32: foto pequena esticada no cartaz grande saía "baixíssima
    qualidade" — amplia no FLUXO DO EXPORT (Real-ESRGAN da F4.3; sem o
    modelo, Lanczos COM aviso — nunca em silêncio), com cache por conteúdo
    (o mesmo produto não paga o modelo duas vezes). A original nunca muda.
    """
    import hashlib

    from PIL import Image
    try:
        with Image.open(caminho) as img:
            lado = max(img.size)        # R-101: mira o MAIOR lado (o da célula)
    except Exception:
        return caminho                  # ilegível: o pré-voo já acusa
    if lado >= lado_alvo_px * 0.9:
        return caminho                  # já enche a célula — NÃO amplia à toa
        # (achado da frota: mirar o menor lado inflava a paisagem em até 3× o alvo)
    # FASE 3 (passo 49): o upscale automático é DESLIGÁVEL na aba Imagens
    try:
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                auto = ConfigRepositorio(s).get("imagem.upscale_auto", True)
        finally:
            db.engine.dispose()
        if auto is False:
            status_cb("Foto pequena mantida — o upscale automático está "
                      "desligado nas Configurações › Imagens")
            return caminho
    except Exception:
        pass
    h = hashlib.sha256(Path(caminho).read_bytes()).hexdigest()[:16]
    pasta_cache = SystemRoot().biblioteca_imagens / "_upscale_cartaz"
    pasta_cache.mkdir(parents=True, exist_ok=True)
    destino = pasta_cache / f"{h}.png"
    if destino.exists():
        return str(destino)
    from app.images.upscale import UpscalerLanczos, ampliar_sob_demanda
    modelo = SystemRoot().modelos / "RealESRGAN_x4plus.pth"
    if modelo.exists():
        status_cb("Melhorando a foto para o cartaz (Real-ESRGAN)…")
        up = _upscaler_real(str(modelo))
    else:
        status_cb("Sem o modelo de upscale — ampliação simples (coloque o "
                  "RealESRGAN_x4plus.pth em modelos/ p/ qualidade máxima)")
        up = UpscalerLanczos()
    # R-101: amplia até o alvo no MAIOR lado (nem mais — a célula é CONTER)
    ampliada = ampliar_sob_demanda(caminho, up, lado_alvo_px)
    ampliada.save(destino, "PNG")
    return str(destino)


def salvar_imagens_produto(produto_id: int,
                           caminhos_absolutos: list[str]) -> int:
    """RG-28: persiste a LISTA ORDENADA de fotos do produto NO ACERVO — os
    sabores deixam de viver só no item/projeto e voltam em qualquer tabloide.

    Só caminhos DENTRO da pasta do produto viram relativos e persistem
    (imunes ao remap de id da portabilidade — I3); foto em pasta temporária
    (item sem produto na época) fica só no item, como sempre. Lista com
    menos de 2 fotos limpa o campo (multi de 1 é foto única).
    """
    import json as _json

    from app.core.repositories import ProdutoRepositorio

    pasta = (SystemRoot().biblioteca_imagens / str(produto_id)).resolve()
    rels: list[str] = []
    for cam in caminhos_absolutos:
        try:
            rels.append(Path(cam).resolve().relative_to(pasta).as_posix())
        except (ValueError, OSError):
            continue                     # fora da biblioteca: não persiste
    valor = _json.dumps(rels, ensure_ascii=False) if len(rels) >= 2 else None
    db = Database().init()
    try:
        with db.Session() as s:
            ProdutoRepositorio(s).editar(produto_id, imagens_json=valor)
            s.commit()
    finally:
        db.engine.dispose()
    return len(rels)


def imagens_do_produto(p) -> list[str]:
    """RG-28: os caminhos ABSOLUTOS das fotos persistidas, NA ORDEM.

    Foto sumida do disco fica na lista — o pré-voo acusa "imagem 2/3
    sumida" (I2), nunca some em silêncio."""
    import json as _json

    if not getattr(p, "imagens_json", None):
        return []
    try:
        rels = _json.loads(p.imagens_json)
    except (ValueError, TypeError):
        return []
    pasta = SystemRoot().biblioteca_imagens / str(p.id)
    return [str(pasta / r) for r in rels if isinstance(r, str) and r]


def preparar_extra(produto_id: int | None, fonte: str,
                   status_cb: StatusCb) -> str:
    """F7.1: trata uma foto EXTRA do item (sabor/fragrância) e a guarda.

    Com ``produto_id``, a foto mora em ``biblioteca/<id>/extras/`` (estável
    entre sessões); sem, fica em pasta temporária — nos dois casos o
    congelamento do projeto copia a foto para a pasta dele (a durabilidade
    oficial é o projeto salvo).
    """
    import shutil

    tratada = tratar_imagem(fonte, status_cb)
    if produto_id:
        from datetime import datetime

        destino_dir = SystemRoot().biblioteca_imagens / str(produto_id) / "extras"
        destino_dir.mkdir(parents=True, exist_ok=True)
        destino = destino_dir / \
            f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
        shutil.move(tratada, destino)
        return str(destino)
    return tratada


def webp_ligado() -> bool:
    """OS F11.5 #51/#52: a chave `imagem.webp` da Config — foto NOVA sai em
    WebP lossless (alfa preservado). Falha de leitura = PNG de sempre."""
    try:
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                return bool(ConfigRepositorio(s).get("imagem.webp", False))
        finally:
            db.engine.dispose()
    except Exception:
        return False


def biblioteca_da_config():
    """A BibliotecaImagens com o formato da Config (#51/#52) — o ponto único
    dos fluxos de ingestão."""
    from app.images.biblioteca import BibliotecaImagens
    return BibliotecaImagens(SystemRoot().biblioteca_imagens,
                             webp=webp_ligado())


def migrar_acervo_webp(para_webp: bool, status_cb: StatusCb = lambda _m: None,
                       *, previa: bool = False) -> dict:
    """OS F11.5 #51/#52: converte as fotos 'atual' do acervo PNG↔WebP
    (LOSSLESS — o alfa do packshot é sagrado), atualizando o caminho no
    banco. `previa=True` só MEDE o ganho, byte a byte, sem tocar em nada.
    REVERSÍVEL: rodar com `para_webp=False` volta tudo a PNG. Foto ilegível
    é pulada e RELATADA (I2). Devolve {"fotos", "bytes_antes",
    "bytes_depois", "puladas"}."""
    import io

    from PIL import Image as _Img

    from sqlalchemy import select

    from app.core.models import Produto
    raiz = SystemRoot().biblioteca_imagens
    alvo_ext = ".webp" if para_webp else ".png"
    fotos = antes = depois = 0
    puladas: list[str] = []
    db = Database().init()
    try:
        with db.Session() as s:
            rows = s.execute(select(Produto).where(
                Produto.caminho_imagem.is_not(None))).scalars().all()
            total = len(rows)
            for i, p in enumerate(rows, 1):
                rel = (p.caminho_imagem or "").replace("\\", "/")
                origem = raiz / rel
                if not origem.is_file() or origem.suffix.lower() == alvo_ext:
                    continue
                status_cb(f"{'Medindo' if previa else 'Convertendo'} "
                          f"{i}/{total}…")
                try:
                    img = _Img.open(origem).convert("RGBA")
                    buf = io.BytesIO()
                    if para_webp:
                        img.save(buf, "WEBP", lossless=True)
                    else:
                        img.save(buf, "PNG")
                except Exception:
                    puladas.append(rel)
                    continue
                fotos += 1
                antes += origem.stat().st_size
                depois += buf.tell()
                if previa:
                    continue
                destino = origem.with_suffix(alvo_ext)
                destino.write_bytes(buf.getvalue())
                origem.unlink()
                p.caminho_imagem = str(
                    Path(rel).with_suffix(alvo_ext).as_posix())
            if not previa:
                s.commit()
    finally:
        db.engine.dispose()
    return {"fotos": fotos, "bytes_antes": antes, "bytes_depois": depois,
            "puladas": puladas}


def definir_imagem(produto_id: int, imagem_tratada: str,
                   status_cb: StatusCb) -> dict:
    """Nova imagem do produto via biblioteca (a anterior vira versão)."""
    status_cb("Guardando na biblioteca…")
    bib = biblioteca_da_config()
    bib.ingerir(produto_id, imagem_tratada)
    return editar_produto(produto_id,
                          caminho_imagem=bib.caminho_relativo(produto_id))


def item_do_catalogo(d: dict) -> ItemMesa:
    """Linha do catálogo → ItemMesa verde (o 'importar do banco' da Mesa)."""
    unidade = (f'{d["peso_valor"]}{d["peso_unidade"]}'
               if d.get("peso_valor") and d.get("peso_unidade") else None)
    return ItemMesa(
        descricao=d.get("nome_bruto") or d["nome"], preco=d.get("preco"),
        semaforo="VERDE", nome=d["nome"], produto_id=d["id"],
        imagem=d.get("imagem"), mais18=d.get("mais18", False),
        via="banco", preco_de=d.get("preco"), unidade=unidade,
        categoria=d.get("categoria") or None,               # F8
        imagens=list(d.get("imagens") or []),               # RG-28
        ean=d.get("ean") or None,                           # RG-41
    )


# --- override por slot (F7.3): override do slot > item da estante > banco --------

def aplicar_override(dados, ov: dict):
    """Aplica o override de UM slot sobre os dados do item (Bloco E, B1).

    A cadeia de precedência da visão §3.1: o que o humano fixou NESTA célula
    vence o item da estante, que vence o banco. Campo ausente/vazio herda;
    "imagem" troca a foto da célula (vira foto única — as múltiplas do item
    não se misturam com a foto forçada); "arranjo" muda a disposição F4.5.
    """
    from dataclasses import replace

    from app.rendering.arranjo import ModoArranjo

    novo = dados
    if ov.get("nome"):
        novo = replace(novo, nome=str(ov["nome"]))
    if ov.get("preco"):
        novo = replace(novo, preco_por=preco_decimal(str(ov["preco"])))
    if ov.get("imagem"):
        novo = replace(novo, imagem_path=str(ov["imagem"]), imagens=[])
    if ov.get("arranjo"):
        try:
            novo = replace(novo, modo_arranjo=ModoArranjo(str(ov["arranjo"])))
        except ValueError:      # valor estranho num projeto velho: herda o do
            pass                # item (o arranjo é cosmético, nunca some conteúdo)
    enq = ov.get("enquadramento")
    if enq:
        # R-037 (Fase 5): pan/zoom da foto DENTRO do slot, POR célula (I3:
        # valores relativos). Aplica a mesma moldura às imagens do slot.
        from app.rendering.compositor import ImagemSlot
        z = float(enq.get("zoom", 1.0))
        fx = float(enq.get("foco_x", 0.5))
        fy = float(enq.get("foco_y", 0.5))
        base_imgs = novo.imagens or (
            [ImagemSlot(novo.imagem_path)] if novo.imagem_path else [])
        if base_imgs:
            novo = replace(novo, imagens=[
                replace(im, zoom=z, foco_x=fx, foco_y=fy) for im in base_imgs])
    return novo


def dados_para_desenho(it: "ItemMesa", abreviacoes: dict | None = None,
                       registro_selos: list | None = None,
                       validade: str | None = None):
    """A montagem OFICIAL item→DadosProduto — a MESMA para Mesa, export e
    Modo Pai (frota F12: o Modo Pai montava a peça 'à mão' e imprimia
    DIFERENTE do export — sem multi-preço, sem selo +18, sem validade)."""
    from app.rendering.arranjo import ModoArranjo
    from app.rendering.compositor import DadosProduto, ImagemSlot
    try:
        arranjo = ModoArranjo(it.arranjo) if it.arranjo else ModoArranjo.LEQUE
    except ValueError:
        arranjo = ModoArranjo.LEQUE           # valor estranho: leque padrão
    # RG-22: a abreviação vale SÓ para o desenho — banco/estante intactos
    nome = (abreviar_para_tabloide(it.nome, abreviacoes)
            if abreviacoes else it.nome)
    # RG-33: os selos escolhidos do item viram selos_extra do passe final
    extras = selos_do_item(it.selos, registro_selos) if it.selos else []
    # RG-34: item com validade cadastrada ganha "De olho na validade"
    # AUTOMÁTICO (decisão travada do padrão +18: automático é automático)
    if it.validade:
        from app.rendering.selos import Canto, Selo
        extras = extras + [Selo("VALIDADE", Canto.INFERIOR_ESQUERDO)]
    return DadosProduto(
        nome,
        selos_extra=extras,
        preco_por=preco_decimal(it.preco),
        multi_preco=it.multi_preco,          # R-070: "3 por R$10"
        observacao=it.observacao,            # R-071: "limite 2 por cliente"
        imagem_path=it.imagem,
        imagens=[ImagemSlot(c) for c in (it.imagens or [])],
        modo_arranjo=arranjo,
        mais18=it.mais18,
        unidade=it.unidade,
        categoria=it.categoria,          # F8.2: as seções derivam daqui
        # RG-34: o de/até já vem como frase completa ("OFERTA VÁLIDA DE …");
        # o legado ("ATÉ 24/07" do OCR/RG-24) ganha o prefixo
        texto_legal=(validade
                     if (validade or "").upper().startswith("OFERTA")
                     else f"Ofertas válidas {validade}"
                     if validade else None),
    )


def dados_de_projeto_aberto(aberto):
    """slot→DadosProduto de um ``ProjetoAberto``, com a precedência oficial
    (override > item > banco) e as FALTAS visíveis (I2 — foto sumida nunca
    é pulada em silêncio). Devolve ``(dados, faltas)``. Projeto CARTAZ usa
    a montagem do cartaz (de/por + %-calculado)."""
    itens = [ItemMesa.from_dict(d) for d in aberto.itens]
    por_uid = {it.uid: it for it in itens}
    faltas: list[str] = []
    dados: dict = {}
    if (aberto.tipo or "").upper() == "CARTAZ":
        for sid, uid in (aberto.mapa or {}).items():
            it = por_uid.get(uid)
            if it is None:
                faltas.append(f"célula {sid}: o item do projeto sumiu")
                continue
            dados[sid] = dados_cartaz_de_produto(
                {"nome": it.nome, "preco": it.preco,
                 "preco_de": it.preco_de, "imagem": it.imagem,
                 "validade": it.validade},
                validade_texto=aberto.validade_oferta)
    else:
        abrev = abreviacoes_tabloide()
        registro = selos_disponiveis()
        for sid, uid in (aberto.mapa or {}).items():
            it = por_uid.get(uid)
            if it is None:
                faltas.append(f"célula {sid}: o item do projeto sumiu")
                continue
            d = dados_para_desenho(it, abrev or None, registro,
                                   aberto.validade_oferta)
            ov = (aberto.overrides or {}).get(sid)
            dados[sid] = aplicar_override(d, ov) if ov else d
    for sid, d in dados.items():
        cam = getattr(d, "imagem_path", None)
        if cam and not Path(cam).exists():
            faltas.append(f"a foto de “{d.nome}” sumiu do disco")
    return dados, faltas


# --- agrupar por categoria (F8.2/A2): ordenação prévia, nunca vínculo ------------

OUTROS = "Outros"


def checklist_final(itens: list[ItemMesa], validade: str | None):
    """R-063: checklist antes de exportar, gerado do ESTADO REAL do projeto —
    marca sozinho o que já está ok. Devolve [(pergunta, ok, detalhe)]."""
    n = len(itens)
    sem_foto = [it for it in itens if not (it.imagem or it.imagens)]
    sem_preco = [it for it in itens
                 if preco_decimal(it.preco) is None and not it.multi_preco]
    bebidas = [it for it in itens if it.mais18]
    return [
        ("Todos os itens têm foto?", not sem_foto,
         "ok" if not sem_foto else f"{len(sem_foto)} sem foto"),
        ("Todos os itens têm preço entendido?", not sem_preco,
         "ok" if not sem_preco else f"{len(sem_preco)} sem preço"),
        ("A validade da oferta está definida?", bool(validade),
         validade or "defina a validade de/até"),
        ("As bebidas alcoólicas estão com +18?", True,
         f"{len(bebidas)} bebida(s) — o selo +18 é automático"
         if bebidas else "nenhuma bebida alcoólica"),
        ("Há itens na oferta?", n > 0, f"{n} item(ns)"),
    ]


def aprovar_projeto(projeto_id, itens: list[ItemMesa], validade: str | None):
    """R-068 (aprovação em 2 etapas): aprovar EXIGE a conferência — roda o
    checklist da F7 e só aprova se TUDO estiver ok. Não é clique cego. Devolve
    (aprovado, faltas) — `faltas` é a lista de perguntas ainda não resolvidas."""
    faltas = [p for p, ok, _d in checklist_final(itens, validade) if not ok]
    if faltas:
        return False, faltas
    if projeto_id is not None:
        from app.core import projetos
        projetos.aprovar(projeto_id)
    return True, []


def pode_exportar_limpo(projeto_id) -> bool:
    """R-068 (guarda testada): exportar SEM a marca d'água RASCUNHO só depois de
    aprovado. Projeto novo/não salvo (id None) nunca está aprovado."""
    from app.core import projetos
    return projetos.esta_aprovado(projeto_id)


def chave_natural(item: ItemMesa):
    """R-062/I1: a chave que casa o MESMO produto entre edições — produto_id
    (forte) > ean > nome sanitizado. NUNCA a posição na lista."""
    if item.produto_id:
        return ("pid", item.produto_id)
    if item.ean:
        return ("ean", str(item.ean))
    return ("nome", (item.nome or "").strip().lower())


def diff_edicoes(atual: list[ItemMesa], anterior: list[ItemMesa]):
    """R-062: o que mudou de preço, o que ENTROU e o que SAIU entre a edição
    atual e a anterior — casando por chave natural (I1), nunca por posição.
    Devolve {novos, removidos, precos: [(item, preco_antigo, preco_novo)]}."""
    por_ant = {chave_natural(it): it for it in anterior}
    por_atu = {chave_natural(it): it for it in atual}
    novos = [it for k, it in por_atu.items() if k not in por_ant]
    removidos = [it for k, it in por_ant.items() if k not in por_atu]
    precos: list[tuple] = []
    for k, it in por_atu.items():
        ant = por_ant.get(k)
        if ant is not None and (it.preco or "") != (ant.preco or ""):
            precos.append((it, ant.preco, it.preco))
    return {"novos": novos, "removidos": removidos, "precos": precos}


# --- R-058: frases prontas com variáveis {data}/{evento} --------------------

BANCO_FRASES: list[str] = [
    "Oferta válida {data}",
    "Ofertas do {evento}",
    "Confira as ofertas do {evento} — válidas {data}",
    "Promoção válida enquanto durarem os estoques",
    "Imagens meramente ilustrativas",
]


def frases_do_combo() -> list[str]:
    """OS F11.5 #39: as frases do combo = padrão (BANCO_FRASES) + as que o
    DONO adicionou (config `frases.validade`), sem repetir. Falha de leitura
    do banco degrada para o padrão (I2: o combo nunca fica vazio)."""
    proprias: list[str] = []
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                proprias = list(ConfigRepositorio(s).get(
                    "frases.validade", []) or [])
        finally:
            db.engine.dispose()
    except Exception:
        proprias = []
    vistas = set()
    saida: list[str] = []
    for f in list(BANCO_FRASES) + proprias:
        f = (f or "").strip()
        if f and f not in vistas:
            vistas.add(f)
            saida.append(f)
    return saida


def adicionar_frase_do_combo(frase: str) -> bool:
    """OS F11.5 #39: grava uma frase nova do dono na config `frases.validade`
    (a mesma lista que a tela de Configurações edita). Devolve False se a
    frase é vazia/repetida ou o banco falhou — a UI avisa (I2)."""
    frase = (frase or "").strip()
    if not frase or frase in frases_do_combo():
        return False
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                rep = ConfigRepositorio(s)
                atuais = list(rep.get("frases.validade", []) or [])
                atuais.append(frase)
                rep.set("frases.validade", atuais)
                s.commit()
        finally:
            db.engine.dispose()
        return True
    except Exception:
        return False


def resolver_frase(template: str, contexto: dict) -> tuple[str, list[str]]:
    """R-058: resolve {data}, {evento} e qualquer {chave} do contexto numa frase
    pronta. Devolve (texto, faltantes): a variável SEM valor fica VISÍVEL como
    «{chave}» (I2 — nunca some calada) e entra em `faltantes` para a UI avisar.
    O texto resolvido alimenta os papéis de texto da F5 (LEGAL/VALIDADE/LIVRE) —
    uma fonte só, sem duplicar a lógica de desenho."""
    import re as _re
    faltantes: list[str] = []

    def _sub(m):
        chave = m.group(1).strip()
        val = contexto.get(chave)
        if val is None or str(val).strip() == "":
            faltantes.append(chave)
            return "{" + chave + "}"          # visível, não engolido (I2)
        return str(val)

    texto = _re.sub(r"\{([^{}]+)\}", _sub, template or "")
    return texto, faltantes


# --- R-059: alerta de repetição (produto há N edições seguidas) -------------

def semanas_seguidas(chave, historico) -> int:
    """Quantas edições MAIS RECENTES seguidas contêm este produto. `historico`
    é a lista de edições (cada uma um iterável de chaves naturais), da mais
    ANTIGA para a mais recente. Conta a sequência que termina na última."""
    n = 0
    for edicao in reversed(list(historico)):
        if chave in set(edicao):
            n += 1
        else:
            break
    return n


def alerta_repeticao(chave, historico, limite: int = 3) -> str | None:
    """R-059: avisa (sem bloquear, I2) quando um produto está no encarte há
    `limite`+ edições seguidas. Informativo — o dono decide manter ou variar."""
    n = semanas_seguidas(chave, historico)
    if n >= limite:
        return f"Está no encarte há {n} edições seguidas — que tal variar?"
    return None


def chaves_edicoes_anteriores(limite_edicoes: int = 4) -> list[set]:
    """R-059: as chaves naturais das últimas edições SALVAS (mais antiga →
    mais recente), para o alerta de repetição. Cada edição vira o conjunto das
    chaves dos seus itens (I1: casa por chave natural, nunca por posição)."""
    from app.core import projetos
    out: list[set] = []
    for itens_dicts in projetos.itens_das_edicoes_recentes(limite_edicoes):
        out.append({chave_natural(ItemMesa.from_dict(d)) for d in itens_dicts})
    return out


def alertas_de_repeticao(itens: list[ItemMesa], historico=None, *,
                         limite: int = 3):
    """R-059: para cada item da oferta ATUAL, avisa se ele está no encarte há
    `limite`+ edições SALVAS seguidas. `historico` (lista de conjuntos de
    chaves, mais antiga→recente) é INJETÁVEL — se None, lê as edições salvas.
    Informativo (I2): devolve [(item, aviso)], nunca bloqueia."""
    if historico is None:
        historico = chaves_edicoes_anteriores()
    fora = []
    for it in itens:
        aviso = alerta_repeticao(chave_natural(it), historico, limite)
        if aviso:
            fora.append((it, aviso))
    return fora


def html_do_checklist(itens: list[ItemMesa], validade: str | None,
                      *, titulo: str = "Checklist da edição",
                      extras: list[str] | None = None) -> str:
    """OS F11.5 #48/#50: o HTML EXATO que vira o PDF do checklist — função
    pura separada para o conteúdo ser conferível (o Qt offscreen imprime o
    texto como curvas; o conteúdo se prova aqui, a tinta se prova no PDF)."""
    linhas = ["<h2>%s</h2>" % titulo]
    for pergunta, ok, detalhe in checklist_final(itens, validade):
        marca = "✔" if ok else "✘"
        linhas.append(f"<p>{marca} <b>{pergunta}</b><br>&nbsp;&nbsp;"
                      f"{detalhe}</p>")
    for extra in (extras or []):
        linhas.append(f"<p>{extra}</p>")
    return "".join(linhas)


def exportar_checklist_pdf(itens: list[ItemMesa], validade: str | None,
                           destino, *, titulo: str = "Checklist da edição",
                           extras: list[str] | None = None):
    """OS F11.5 #48/#50 (R-063) e #39-F11 (R-117): o checklist/relatório vira
    um PDF imprimível — a conferência a quatro olhos em papel. QTextDocument →
    QPrinter PdfFormat (o molde da folha de cola da F3)."""
    from PySide6.QtGui import QTextDocument
    from PySide6.QtPrintSupport import QPrinter

    doc = QTextDocument()
    doc.setHtml(html_do_checklist(itens, validade, titulo=titulo,
                                  extras=extras))
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    from pathlib import Path as _P
    destino = _P(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    printer.setOutputFileName(str(destino))
    doc.print_(printer)
    return destino


def diff_contra_ultima_edicao(itens: list[ItemMesa]):
    """OS F11.5 #44 (R-062): o diff da oferta ATUAL contra a ÚLTIMA edição
    salva (por chave natural, I1) — None quando não há edição anterior."""
    from app.core import projetos
    anteriores = projetos.itens_das_edicoes_recentes(1)
    if not anteriores:
        return None
    anterior = [ItemMesa.from_dict(d) for d in anteriores[-1]]
    return diff_edicoes(itens, anterior)


# --- R-072: estatística da montagem (local, offline — sem telemetria) -------

def _mmss(seg: float) -> str:
    m, s = divmod(int(seg), 60)
    return f"{m}min {s:02d}s" if m else f"{s}s"


def resumo_montagem(segundos: float, n_itens: int) -> dict:
    """R-072: estatística LOCAL e discreta da montagem (decisão travada: offline,
    sem telemetria externa). Tempo total e itens por minuto — o dono vê o app
    economizando o tempo dele."""
    seg = max(0.0, float(segundos))
    ipm = (n_itens / seg * 60.0) if seg > 0 else 0.0
    return {
        "segundos": round(seg, 1),
        "itens": n_itens,
        "itens_por_minuto": round(ipm, 1),
        "resumo": f"{n_itens} itens em {_mmss(seg)} ({round(ipm, 1)}/min)",
    }


# --- R-071: banco de observações frequentes ---------------------------------

BANCO_OBSERVACOES: list[str] = [
    "Limite de 2 unidades por cliente",
    "Limite de 3 unidades por cliente",
    "Enquanto durarem os estoques",
    "Preço exclusivo para pagamento à vista",
    "Válido somente para a loja física",
]


def banco_observacoes() -> list[str]:
    """R-071: observações frequentes para o dono escolher rápido (não vão para o
    banco de produtos — são texto de layout, como as frases prontas)."""
    return list(BANCO_OBSERVACOES)


def separar_por_semaforo(itens: list[ItemMesa]):
    """R-053: separa (verdes, amarelos, vermelhos) — 'aceitar todos os verdes'
    resolve SÓ os que a conciliação casou com confiança (o MESMO predicado
    `semaforo == "VERDE"` já usado na Mesa), sem tocar amarelo/vermelho."""
    verdes = [it for it in itens if it.semaforo == "VERDE"]
    amarelos = [it for it in itens if it.semaforo == "AMARELO"]
    vermelhos = [it for it in itens if it.semaforo == "VERMELHO"]
    return verdes, amarelos, vermelhos


def plano_encher_pagina(itens: list[ItemMesa], slot_ids: list[str]):
    """R-056: plano de 'encher a página' — atribui itens aos slots NA ORDEM,
    por uid (I1), com PRÉ-VOO ANTES (avisa item sem foto/preço, I2). Devolve
    (mapa {slot_id: uid}, resto [itens que não couberam], avisos [str])."""
    mapa: dict[str, str] = {}
    avisos: list[str] = []
    n = min(len(slot_ids), len(itens))
    for sid, it in zip(slot_ids, itens[:n]):
        mapa[sid] = it.uid                       # vínculo por uid, não posição
        if not (it.imagem or it.imagens):
            avisos.append(f"“{it.nome}”: sem foto — entrou na página assim mesmo")
        if preco_decimal(it.preco) is None and not it.multi_preco:
            avisos.append(f"“{it.nome}”: sem preço entendido")
    return mapa, list(itens[n:]), avisos


def filtrar_itens(itens: list[ItemMesa], *, sem_foto: bool = False,
                  sem_preco: bool = False, categoria: str | None = None,
                  busca: str | None = None) -> list[ItemMesa]:
    """R-054 (Fase 6): filtra a estante. Filtros COMBINÁVEIS (sem foto +
    categoria + busca…). Devolve a sublista que passa em TODOS os ativos —
    não muda o vínculo, só a visão."""
    alvo = (busca or "").strip().lower()
    res: list[ItemMesa] = []
    for it in itens:
        if sem_foto and (it.imagem or it.imagens):
            continue                                  # tem foto → fora
        if sem_preco and it.preco and preco_decimal(it.preco) is not None:
            continue                                  # tem preço válido → fora
        if categoria and (it.categoria or OUTROS) != categoria:
            continue
        if alvo and alvo not in (it.nome or "").lower():
            continue
        res.append(it)
    return res


def ordenar_por_categoria(itens: list[ItemMesa],
                          ordem: list[str] | None = None) -> list[ItemMesa]:
    """A2 da ORDEM_F8: ordena a estante por categoria ANTES do preenchimento.

    É SÓ ordenação (estável — a ordem relativa dentro da categoria fica);
    o vínculo continua sendo o mapa slot→uid. Regras: a ``ordem`` da Config
    manda; categoria fora da lista vem depois, em ordem alfabética;
    item SEM categoria agrupa em "Outros", SEMPRE por último (nunca some).
    """
    ordem_norm = [c.strip().lower() for c in (ordem or []) if c.strip()]

    def chave(it: ItemMesa):
        cat = (it.categoria or "").strip() or OUTROS
        low = cat.lower()
        if low == OUTROS.lower():
            return (2, "", "")
        if low in ordem_norm:
            return (0, ordem_norm.index(low), "")
        return (1, 0, low)                     # fora da lista: alfabética

    return sorted(itens, key=chave)


# RG-44 (pesquisa §1): a ordem dos SETORES espelhando a loja física —
# blocking por setor estimula compra conjunta. É a SEMENTE do
# `categorias.ordem` (botão "Preset da loja" nas Configurações), editável.
ORDEM_SETORES_LOJA = [
    "Hortifrúti", "Padaria", "Frios", "Congelados", "Mercearia",
    "Bebidas", "Limpeza", "Higiene", "Pet", "Bazar",
]

# RG-30: siglas de marca própria do mercado (default = as do Belo Brasil;
# configurável em `marcas.proprias` nas Configurações)
MARCAS_PROPRIAS_PADRAO = ["BBX", "BB"]


def abreviacoes_tabloide() -> dict[str, str]:
    """RG-22: o glossário reverso da Config (`tabloide.abreviacoes`) —
    "Leite Condensado" → "Leite Cond.". Vazio por padrão (opt-in do dono)."""
    from app.core.repositories import ConfigRepositorio
    try:
        db = Database().init()
        try:
            with db.Session() as s:
                valor = ConfigRepositorio(s).get("tabloide.abreviacoes")
        finally:
            db.engine.dispose()
        if isinstance(valor, dict):
            return {str(k): str(v) for k, v in valor.items() if k and v}
    except Exception:
        pass
    return {}


# RG-24: datas inteligentes — campanha tem dia fixo por EVENTO ("Quintou" é
# quinta; "Sexta Verde" é sexta). FASE 2: o dia mora no Evento (entidade);
# a tabela de nomes→número vive em eventos._DIAS.


def dia_do_evento(evento: str | None) -> int | None:
    """O dia da semana (0=seg…6=dom) do evento, ou None.

    FASE 2 (passo 7): a verdade agora é o ENTIDADE Evento (dia_semana);
    a Config antiga `eventos.dias` continua como fallback (bancos legados
    e nomes ainda não migrados)."""
    if not evento:
        return None
    try:
        from app.qt.telas.eventos import dia_do_evento_v2
        db = Database().init()
        try:
            with db.Session() as s:
                return dia_do_evento_v2(s, evento)
        finally:
            db.engine.dispose()
    except Exception:
        return None


def proxima_ocorrencia(dia_semana: int, hoje=None):
    """A PRÓXIMA data com aquele dia da semana (hoje conta como próxima)."""
    from datetime import date, timedelta
    hoje = hoje or date.today()
    delta = (dia_semana - hoje.weekday()) % 7
    return hoje + timedelta(days=delta)


def sugerir_validade(evento: str | None, hoje=None) -> str | None:
    """RG-24 + auditoria do dono (20/07): a oferta da campanha vale SÓ NO DIA
    em que entra em vigor — a sugestão do dia fixo é "SOMENTE [o dia da
    campanha]", não um intervalo. As EXCEÇÕES continuam cobertas: a regra por
    evento "válido por N dias" (Config, F3 passo 36) segue "ATÉ hoje+N", e a
    validade ESCRITA NA TABELA (o jornal do mês) sempre manda — esta função
    só roda quando não há nenhuma. Sem regra nem dia → None."""
    from datetime import date, timedelta
    if evento:
        try:
            from app.core.repositories import ConfigRepositorio
            db = Database().init()
            try:
                with db.Session() as s:
                    mapa = ConfigRepositorio(s).get(
                        "eventos.validade_regra") or {}
            finally:
                db.engine.dispose()
            regra = next((v for k, v in mapa.items()
                          if k.strip().lower() == evento.strip().lower()),
                         None)
            if isinstance(regra, int) and regra > 0:
                data = (hoje or date.today()) + timedelta(days=regra)
                return f"ATÉ {data.strftime('%d/%m')}"
        except Exception:
            pass
    dia = dia_do_evento(evento)
    if dia is None:
        return None
    data = proxima_ocorrencia(dia, hoje)
    return f"SOMENTE {data.strftime('%d/%m')}"


# --- RG-43: assistente de preço (pesquisa §3 — charm pricing) ----------------------


def sugerir_terminacao(preco_txt: str | None) -> str | None:
    """Sugestão OPCIONAL de terminação psicológica (,99/,X9) — nunca aplica
    sozinha (o preço é do dono; o aviso PROCON acompanha na UI).

    10,00 → 9,99 (efeito do dígito esquerdo) · 5,30 → 5,29 · já-charm → None.
    """
    valor = preco_decimal(preco_txt)
    if valor is None:
        return None
    centavos = int((valor * 100) % 100)
    if centavos % 10 == 9 or centavos in (98, 90, 95):
        return None                     # já é terminação de varejo
    if centavos == 0:
        novo = valor - Decimal("0.01")  # 10,00 → 9,99 (quebra o dígito esq.)
    else:
        alvo = centavos - (centavos % 10) - 1   # 30→29 · 42→39 · 07→desce
        if alvo < 0:
            novo = (valor // 1) - 1 + Decimal("0.99")
        else:
            novo = (valor // 1) + Decimal(alvo) / 100
    if novo <= 0:
        return None
    reais = int(novo)
    return f"{reais},{int((novo - reais) * 100):02d}"


# --- RG-42: presets de composição (pesquisa §1-2) ----------------------------------


def ordenar_com_herois(fila: list, n_capa: int) -> list:
    """RG-42 "capa com heróis": os N slots da CAPA recebem os itens mais
    BARATOS (âncora de tráfego — a prática do Quintou com a abóbora a 0,19);
    o resto segue na ordem que veio (agrupada ou importada). Estável: itens
    sem preço nunca viram herói."""
    if n_capa <= 0:
        return list(fila)
    com_preco = [it for it in fila if preco_decimal(it.preco) is not None]
    herois = sorted(com_preco, key=lambda it: preco_decimal(it.preco))[:n_capa]
    ids = {it.uid for it in herois}
    resto = [it for it in fila if it.uid not in ids]
    return herois + resto


def densidade_da_pagina(pagina, dados: dict) -> float:
    """RG-42 "medidor de entulho": fração das células ocupáveis com item.
    (O respiro vende — regra 60-30-10 da pesquisa; o aviso é da UI.)"""
    from app.rendering.grade import ocupaveis

    uteis = ocupaveis(pagina.slots)
    if not uteis:
        return 0.0
    ocupadas = sum(1 for s in uteis if dados.get(s.id) is not None)
    return ocupadas / len(uteis)


def montar_validade_oferta(de: str | None, ate: str | None) -> str | None:
    """RG-34: a validade da OFERTA (de/até) é conceito PRÓPRIO — separado
    da validade do item (que é o "perto de vencer" do cartaz).

    "17/07" + "24/07" → "OFERTA VÁLIDA DE 17/07 ATÉ 24/07";
    o MESMO dia nos dois → "OFERTA VÁLIDA SOMENTE 17/07" (auditoria do dono:
    a oferta do dia vale só no dia); só o fim → "ATÉ 24/07"; nada → None."""
    de = (de or "").strip()
    ate = (ate or "").strip()
    if de and ate and de == ate:
        return f"OFERTA VÁLIDA SOMENTE {de}"
    if de and ate:
        return f"OFERTA VÁLIDA DE {de} ATÉ {ate}"
    if ate:
        return f"ATÉ {ate}"
    return None


def abreviar_para_tabloide(nome: str,
                           glossario: dict[str, str] | None = None) -> str:
    """RG-22: aplica as abreviações SÓ ao nome desenhado no tabloide — o
    banco e a estante seguem com o nome completo. Frases mais longas têm
    precedência ("Leite Condensado Moça" antes de "Leite Condensado");
    a comparação ignora caixa, a troca preserva o resto do nome."""
    import re
    g = glossario if glossario is not None else abreviacoes_tabloide()
    resultado = nome
    for longo in sorted(g, key=len, reverse=True):
        resultado = re.sub(re.escape(longo), g[longo], resultado,
                          count=1, flags=re.IGNORECASE)
    return resultado


def marcas_proprias() -> list[str]:
    """O glossário de marcas próprias da Config (default são — C3)."""
    from app.core.repositories import ConfigRepositorio
    try:
        db = Database().init()
        try:
            with db.Session() as s:
                valor = ConfigRepositorio(s).get("marcas.proprias")
        finally:
            db.engine.dispose()
        if isinstance(valor, list) and valor:
            return [str(v).strip() for v in valor if str(v).strip()]
    except Exception:
        pass
    return list(MARCAS_PROPRIAS_PADRAO)


def eh_marca_propria(nome: str, glossario: list[str] | None = None) -> bool:
    """RG-30: o nome contém uma sigla de marca própria (token exato)?"""
    tokens = {t.strip(".,;").upper() for t in nome.split()}
    return any(m.upper() in tokens for m in (glossario or marcas_proprias()))


def remover_marcas_do_termo(termo: str,
                            glossario: list[str] | None = None) -> str:
    """RG-30/26: tira a sigla da marca própria do TERMO DE BUSCA de imagem
    ("Fígado Bovino BBX" acha fígado, não a sigla) — o NOME não muda."""
    siglas = {m.upper() for m in (glossario or marcas_proprias())}
    limpo = [t for t in termo.split() if t.strip(".,;").upper() not in siglas]
    return " ".join(limpo) or termo


def categorias_ordenadas(session) -> list[str]:
    """A ordem das categorias salva na Config ('categorias.ordem')."""
    from app.core.repositories import ConfigRepositorio

    valor = ConfigRepositorio(session).get("categorias.ordem")
    return [str(c) for c in valor] if isinstance(valor, list) else []


# --- item composto (F7.2, Etapa D do Bloco E): dois produtos, UM uid -------------

def nome_composto(nome_a: str, nome_b: str) -> str:
    """Monta o nome do composto: "Arroz Camil 5kg" + "Arroz Rei 5kg" →
    "Arroz Camil e Rei 5kg" (prefixo e sufixo comuns preservados; os miolos
    distintos entram com "e"). Sempre editável pelo humano no diálogo."""
    ta, tb = nome_a.split(), nome_b.split()
    pre = 0
    while pre < min(len(ta), len(tb)) and ta[pre].lower() == tb[pre].lower():
        pre += 1
    suf = 0
    while (suf < min(len(ta), len(tb)) - pre
           and ta[-1 - suf].lower() == tb[-1 - suf].lower()):
        suf += 1
    miolo_a = " ".join(ta[pre:len(ta) - suf or None])
    miolo_b = " ".join(tb[pre:len(tb) - suf or None])
    if not miolo_a or not miolo_b:
        return f"{nome_a} e {nome_b}"
    partes = ta[:pre] + [f"{miolo_a} e {miolo_b}"] + (ta[len(ta) - suf:]
                                                      if suf else [])
    return " ".join(partes)


def eh_composto(it: ItemMesa) -> bool:
    return bool(it.origem_composto)


def compor_itens(a: ItemMesa, b: ItemMesa, nome: str | None = None,
                 preco: str | None = None) -> ItemMesa:
    """F7.2: dois produtos viram UM item composto — uid PRÓPRIO (o mapa é e
    continua 1 slot → 1 uid), nome montado, 2 imagens LADO_A_LADO, preço
    único. Os originais viajam INTEIROS em ``origem_composto`` — "separar"
    devolve exatamente o que existia (rastreável e desfazível).

    Composto NÃO compõe de novo (profundidade 1 — sem bonecas russas).
    """
    if eh_composto(a) or eh_composto(b):
        raise ValueError("item composto não compõe de novo — "
                         "separe primeiro (profundidade 1)")
    fotos = [c for c in (a.imagem, b.imagem) if c]
    return ItemMesa(
        descricao=f"{a.descricao} + {b.descricao}",
        preco=preco or a.preco,
        semaforo="VERDE",
        nome=nome or nome_composto(a.nome, b.nome),
        produto_id=None,               # o rastro fica nos origens (to_dict)
        imagem=fotos[0] if fotos else None,
        imagens=fotos if len(fotos) == 2 else [],
        arranjo="LADO_A_LADO",         # o padrão da ordem para 2 produtos
        mais18=a.mais18 or b.mais18,
        via="composto",
        unidade=a.unidade if a.unidade == b.unidade else None,
        origem_composto=[a.to_dict(), b.to_dict()],
    )


def criar_como_composto(item: ItemMesa, nomes_componentes: list[str],
                        mais18: bool, imagem_tratada: str | None,
                        categoria: str | None = None) -> ItemMesa:
    """RG-29: a linha com DUAS marcas ("Coração e Língua") já NASCE composta
    na conciliação — cada componente vira produto PRÓPRIO no banco (nunca um
    nome remendado), e o item da estante é o composto de sempre (F7.2:
    separável, rastreável, 1 slot → 1 uid).

    A foto da curadoria vai ao PRIMEIRO componente (o segundo fica para a
    curadoria contínua do Almoxarifado — avisado no pré-voo como sempre).
    """
    from app.core.modo import exigir_escrita
    exigir_escrita()                 # R-131: PC da loja não edita
    subs: list[ItemMesa] = []
    for i, nome in enumerate(nomes_componentes[:2]):
        sub = ItemMesa(descricao=nome, preco=item.preco,
                       semaforo="VERMELHO", nome=nome)
        subs.append(finalizar_criacao(sub, nome, mais18,
                                      imagem_tratada if i == 0 else None,
                                      categoria=categoria))
    comp = compor_itens(subs[0], subs[1], preco=item.preco)
    comp.descricao = item.descricao      # a linha ORIGINAL fica no rastro
    comp.ean = item.ean
    return comp


def separar_item(comp: ItemMesa) -> list[ItemMesa]:
    """Desfaz o composto: devolve os DOIS itens originais como eram
    (uids ORIGINAIS inclusos — nada se recria, nada se duplica)."""
    if not eh_composto(comp):
        raise ValueError("este item não é composto")
    return [ItemMesa.from_dict(d) for d in comp.origem_composto]


# --- pré-voo de exportação (P0.4, invariante I2: nada some em silêncio) ---------

def validar_composicao(layout, dados_por_slot: dict, *, cartaz: bool = False,
                       fontes_dir=None) -> list[str]:
    """Pendências por slot ocupado, ANTES de exportar/salvar.

    Checa: imagem sumida do disco, item sem foto, preço não parseado, nome
    vazio, fonte ausente (com fallback declarado), e no cartaz o par de/por
    ("de" ≤ "por" = risco PROCON).
    """
    fontes_dir = Path(fontes_dir) if fontes_dir else SystemRoot().fontes
    avisos: list[str] = []
    fontes_checadas: set[str] = set()
    varias = len(layout.paginas) > 1
    for n_pag, pagina in enumerate(layout.paginas, start=1):
      for slot in pagina.slots:
        d = dados_por_slot.get(slot.id)
        if d is None:
            continue                              # célula sem produto = arte pura (ok)
        rotulo = (f"célula {slot.id.replace('celula_', '')}"
                  if slot.id.startswith("celula_") else slot.id)
        if varias:                                # D8.5: pré-voo rotula a página
            rotulo = f"página {n_pag}, {rotulo}"
        if not slot.regioes:                      # C5.2: item em célula VAZIA
            avisos.append(f"{rotulo}: “{(d.nome or '?').strip()}” está numa "
                          "célula vazia (não será desenhado)")
            continue
        from app.rendering.grade import TIPOS_CONTEUDO
        if not any(r.tipo in TIPOS_CONTEUDO for r in slot.regioes):
            # A7.2: mapa velho/congelado apontando p/ célula decorativa
            avisos.append(f"{rotulo}: “{(d.nome or '?').strip()}” está numa "
                          "célula decorativa (só texto/selo) — não será desenhado")
            continue
        nome = (d.nome or "").strip()
        if not nome:
            avisos.append(f"{rotulo}: item sem nome")
            nome = "(sem nome)"
        # cobre também multi-imagem (F4.5): valida CADA foto do slot
        caminhos = ([e.caminho for e in d.imagens] if d.imagens
                    else [d.imagem_path] if d.imagem_path else [])
        if not caminhos:
            avisos.append(f"{rotulo} ({nome}): sem foto")
        else:
            from app.core.genericas import eh_generica
            for k, c in enumerate(caminhos, 1):
                idx = (f" (imagem {k}/{len(caminhos)})"
                       if len(caminhos) > 1 else "")
                if not c or not Path(c).exists():
                    avisos.append(
                        f"{rotulo} ({nome}): a imagem sumiu do disco{idx}")
                elif eh_generica(c):        # R-099: genérica nunca é foto real
                    avisos.append(
                        f"{rotulo} ({nome}): usando foto GENÉRICA (placeholder)"
                        f"{idx} — troque pela foto real quando puder")
        if d.preco_por is None and not d.multi_preco:   # R-070: multi-preço TEM preço
            avisos.append(f"{rotulo} ({nome}): sem preço (ou preço não entendido)")
        # FASE 3 (passo 73, I2): selo escolhido cuja ARTE sumiu do disco —
        # o desenho cairia no badge genérico sem ninguém saber por quê
        for selo_extra in (d.selos_extra or []):
            arte = getattr(selo_extra, "imagem_path", None)
            if arte and not Path(arte).exists():
                avisos.append(f"{rotulo} ({nome}): a arte do selo "
                              f"“{selo_extra.tipo}” sumiu do disco — sai o "
                              "selo genérico no lugar")
        if cartaz:
            if d.preco_de is None:
                avisos.append(f"{rotulo} ({nome}): sem preço “de”")
            elif d.preco_por is not None and d.preco_de <= d.preco_por:
                avisos.append(f"{rotulo} ({nome}): “de” ≤ “por” — risco PROCON")
        for reg in slot.regioes:
            if reg.fonte and reg.fonte not in fontes_checadas:
                fontes_checadas.add(reg.fonte)
                if not (fontes_dir / reg.fonte).exists():
                    avisos.append(f"fonte “{reg.fonte}” não encontrada — "
                                  "será usado o fallback (Roboto)")

    # RG-57 (Bloco E, passo 69): pré-voo dos PAPÉIS de texto — a fonte de dado
    # de cada papel faltando aparece (I2), nunca em silêncio. Varre TODAS as
    # regiões TEXTO_LEGAL (inclusive as de slot decorativo, sem produto).
    from app.rendering.compositor import texto_composto_legal
    from app.rendering.model import PapelTexto, TipoRegiao
    vistos: set[str] = set()
    for pagina in layout.paginas:
        for slot in pagina.slots:
            d = dados_por_slot.get(slot.id)
            for reg in slot.regioes:
                if reg.tipo != TipoRegiao.TEXTO_LEGAL or not reg.visivel:
                    continue
                rot = reg.nome or "campo de texto legal"
                fixo = (reg.texto_fixo or "").strip()
                msg = None
                if (reg.papel_texto == PapelTexto.VALIDADE
                        and not texto_composto_legal(reg, d).strip()):
                    msg = f"{rot}: papel “Validade da oferta” sem data — defina a validade"
                elif reg.papel_texto == PapelTexto.DICA and not fixo:
                    msg = f"{rot}: papel “Fica a Dica” sem texto — gere a dica pela IA"
                elif reg.papel_texto == PapelTexto.LEGAL and not fixo:
                    msg = f"{rot}: papel “Aviso legal” sem texto — escolha um preset"
                if msg and msg not in vistos:
                    vistos.add(msg)
                    avisos.append(msg)
    return avisos


# --- importar + conciliar -----------------------------------------------------

def importar_ofertas(caminho: str | Path, status_cb: StatusCb) -> ResultadoMesa:
    """Lê a fonte (foto → OCR; texto → parse) e concilia tudo com o banco."""
    caminho = Path(caminho)
    validade = None
    aviso_cache = None

    if caminho.suffix.lower() in _EXT_IMAGEM:
        from app.ai.client import ConfigIA
        from app.ai.ocr import cache_consultar, cache_guardar, ler_tabela

        # RG-04: a MESMA foto (mesmo conteúdo, mesmo modelo) não re-roda o
        # OCR — na auditoria a reimportação custou minutos à toa. O
        # reaproveitamento é AVISADO (I2), nunca silencioso.
        modelo_visao = ConfigIA.da_config().modelo_visao
        tabela = cache_consultar(caminho, modelo_visao)
        if tabela is not None:
            aviso_cache = (f"Foto já lida antes — OCR reaproveitado "
                           f"({len(tabela.linhas)} produtos). Para reler, "
                           "limpe o cache do OCR nas Configurações.")
            status_cb(aviso_cache)
        else:
            status_cb("Lendo a foto (OCR)…")
            motor = _motor_se_disponivel()
            if motor is None:
                raise RuntimeError(
                    "A foto precisa do OCR (LM Studio), que não está acessível. "
                    "Ligue o LM Studio ou importe a tabela como arquivo de texto.")
            tabela = ler_tabela(caminho, motor, status_cb=status_cb)
            cache_guardar(caminho, modelo_visao, tabela)
        linhas = [(ln.descricao, ln.preco, None) for ln in tabela.linhas]
        validade = tabela.validade_oferta
    else:
        status_cb("Lendo a tabela…")
        from app.scripts.importar_tabela import parse_tabela_ean
        linhas = parse_tabela_ean(caminho)   # RG-41: o EAN da tabela flui

    fonte = str(caminho) if caminho.suffix.lower() in _EXT_IMAGEM else None
    return conciliar_linhas(linhas, status_cb, validade=validade,
                            aviso=aviso_cache, caminho_fonte=fonte)


def conciliar_linhas(linhas, status_cb: StatusCb, *, validade=None,
                     aviso=None, caminho_fonte=None,
                     multi_precos=None) -> ResultadoMesa:
    """Concilia uma lista de tuplas ``(descricao, preco, ean)`` com o banco —
    o MESMO caminho que ``importar_ofertas`` usa. A COLAGEM (R-050, Fase 7)
    reusa isto: o parser de colagem produz as tuplas e cai aqui, sem duplicar
    a conciliação nem reimplementar o P0.3/RG-20.

    ``multi_precos`` (opcional, PARALELO a ``linhas``) leva o multi-preço
    reconhecido na colagem (R-070) para o ItemMesa — a tupla só carrega o valor,
    o formato de promoção viaja aqui."""
    status_cb("Conciliando com o banco…")
    from app.ai.conciliacao import Conciliador

    motor = _motor_se_disponivel()
    db = Database().init()          # conexão PRÓPRIA (estamos num worker)
    itens: list[ItemMesa] = []
    try:
        with db.Session() as session:
            conc = Conciliador(session, motor=motor, embedder=motor,
                               status_cb=status_cb)
            for i, (desc, preco, ean) in enumerate(linhas, 1):
                status_cb(f"Conciliando {i}/{len(linhas)}…")
                v = conc.conciliar(desc)
                p = v.produto
                mp = (multi_precos[i - 1] if multi_precos
                      and i - 1 < len(multi_precos) else None)
                itens.append(ItemMesa(
                    descricao=desc,
                    preco=preco,
                    multi_preco=mp,                          # R-070 (colagem)
                    ean=ean or (p.ean if p else None),
                    semaforo=v.semaforo.value,
                    nome=p.nome_sanitizado if p else desc,
                    produto_id=p.id if p else None,
                    imagem=_imagem_absoluta(p.caminho_imagem) if p else None,
                    mais18=bool(p.selo_mais18) if p else False,
                    via=v.via,
                    score=v.confianca,
                    candidato_nome=(v.candidatos[0].produto.nome_sanitizado
                                    if v.candidatos else ""),
                    preco_de=_preco_texto(p.preco_atual) if p else None,
                    unidade=(f"{_qtd_texto(p.peso_valor)}{p.peso_unidade}"
                             if p and p.peso_valor is not None and p.peso_unidade
                             else None),
                    categoria=(p.categoria.nome
                               if p and p.categoria else None),   # F8
                    imagens=imagens_do_produto(p) if p else [],   # RG-28
                ))
        # I2 (frota F12): a degradação do conciliador (embeddings mortos)
        # sobe até a tela — antes ficava engolida e o dono acreditava que
        # a camada de significado tinha trabalhado
        for a in conc.avisos:
            aviso = f"{aviso} · {a}" if aviso else a
    finally:
        db.engine.dispose()
    return ResultadoMesa(itens=itens, validade_oferta=validade, aviso=aviso,
                         caminho_fonte=caminho_fonte)


def importar_varios(caminhos, status_cb: StatusCb, progresso_cb=None):
    """R-049 (Fase 7): enfileira vários arquivos e processa em SÉRIE. Um
    arquivo com erro NÃO derruba a fila (I2): fica marcado e o resto segue.
    Devolve (ResultadoMesa combinado, [(arquivo, erro)]).
    `progresso_cb(nome, estado)` (OS F11.5 #2) narra o estado POR ARQUIVO —
    "lendo" → "pronto"/"erro" — para o widget da fila na Mesa."""
    prog = progresso_cb or (lambda _n, _e: None)
    itens: list[ItemMesa] = []
    validade = None
    erros: list[tuple[str, str]] = []
    total = len(caminhos)
    for i, cam in enumerate(caminhos, 1):
        nome = Path(cam).name
        status_cb(f"Arquivo {i}/{total}: {nome}…")
        prog(nome, "lendo")
        try:
            res = importar_ofertas(cam, status_cb)
            itens.extend(res.itens)
            validade = validade or res.validade_oferta
            prog(nome, "pronto")
        except Exception as e:               # I2: o erro fica visível, a fila segue
            erros.append((nome, str(e)))
            prog(nome, "erro")
    aviso = (None if not erros else
             f"{len(erros)} de {total} arquivo(s) com erro — o resto foi lido "
             f"({total - len(erros)} ok).")
    return ResultadoMesa(itens=itens, validade_oferta=validade, aviso=aviso), erros


def resumo_do_resultado(resultado) -> str:
    """R-073 (transparência): o que a conciliação fez, em linguagem simples —
    "casei 18; 2 p/ conferir; 1 novo; 3 sem foto"."""
    itens = resultado.itens
    v = sum(1 for i in itens if i.semaforo == "VERDE")
    a = sum(1 for i in itens if i.semaforo == "AMARELO")
    r = sum(1 for i in itens if i.semaforo == "VERMELHO")
    sf = sum(1 for i in itens if not (i.imagem or i.imagens))
    partes = []
    if v:
        partes.append(f"casei {v}")
    if a:
        partes.append(f"{a} p/ conferir")
    if r:
        partes.append(f"{r} novo(s)")
    if sf:
        partes.append(f"{sf} sem foto")
    return "; ".join(partes) or "nada reconhecido"


def montar_pelo_chat(texto: str, status_cb: StatusCb) -> ResultadoMesa:
    """R-073 (chat da oferta): o dono cola/descreve as ofertas e vira um RASCUNHO,
    REUSANDO a conciliação (parse de colagem + conciliar_linhas) — não um pipeline
    novo. É sempre rascunho para AJUSTAR (nunca publicado direto, I2)."""
    from app.qt.telas.colagem import (
        linhas_para_tuplas, multi_precos_de, parse_colagem)
    linhas = parse_colagem(texto)
    return conciliar_linhas(linhas_para_tuplas(linhas), status_cb,
                            multi_precos=multi_precos_de(linhas))


def ordenar_por_prioridade(pares, foco=None):
    """R-089 (fila de IA com prioridade): reordena os pares (chave, valor) de uma
    fila pondo a chave em FOCO na frente — o que o dono olha agora roda primeiro.
    Estável no resto (não embaralha a ordem original dos demais)."""
    if foco is None:
        return list(pares)
    return sorted(pares, key=lambda p: 0 if p[0] == foco else 1)


def _hash_foto(caminho) -> str | None:
    """sha256 dos bytes da foto — "mesma foto por CONTEÚDO, não por nome" (o
    mesmo idioma do cache de OCR/upscale)."""
    try:
        import hashlib
        from pathlib import Path as _P
        return hashlib.sha256(_P(caminho).read_bytes()).hexdigest()
    except Exception:
        return None


def fotos_repetidas(itens: list[ItemMesa]):
    """R-104: a MESMA foto usada em 2+ itens da edição ATUAL, por HASH de conteúdo
    (não por nome de arquivo — pega a repetição REAL). Devolve os grupos
    repetidos [(hash, [itens])]. Informativo (I2) — nunca bloqueia."""
    por_hash: dict[str, list] = {}
    for it in itens:
        cam = it.imagem or (it.imagens[0] if it.imagens else None)
        h = _hash_foto(cam) if cam else None
        if h:
            por_hash.setdefault(h, []).append(it)
    return [(h, its) for h, its in por_hash.items() if len(its) > 1]


def lado_alvo_da_celula(layout) -> int:
    """R-101: a resolução-ALVO em px da célula de imagem (o MAIOR lado da 1ª
    região IMAGEM, em px pelo DPI). O upscale mira exatamente isto — nem mais
    (desperdício), nem menos (borrado)."""
    from app.rendering.model import TipoRegiao
    from app.rendering.units import mm_para_px
    for pag in getattr(layout, "paginas", []):
        for s in pag.slots:
            reg = next((r for r in s.regioes if r.tipo == TipoRegiao.IMAGEM), None)
            if reg is not None:
                return round(mm_para_px(
                    max(reg.rect.larg_mm, reg.rect.alt_mm), layout.dpi))
    return 0


# --- cartaz-relâmpago e kit ponta-de-gôndola (R-110/R-113, Fase 11) -----------

def dados_cartaz_de_produto(produto: dict, *,
                            validade_texto: str | None = None):
    """Monta o DadosProduto de um cartaz a partir de um produto do Almoxarifado.

    UMA fonte de verdade: a cartaz-relâmpago E as etiquetas do kit usam ESTE
    mesmo dado — a coerência de preço/validade do kit (R-113) nasce daqui. O
    "por" é o preço atual; o "de" só entra se o produto trouxer um preço
    anterior (``preco_de``). A validade preferida é a passada (a da oferta);
    senão a validade do item ("Válido até …"). Sem nenhuma, fica None e o
    pré-voo acusa (RG-58 — a validade nunca some calada, I2)."""
    from app.rendering.compositor import DadosProduto

    texto_val = (validade_texto or "").strip() or None
    if texto_val is None and (produto.get("validade") or "").strip():
        texto_val = f"Válido até {produto['validade']}"
    return DadosProduto(
        (produto.get("nome") or "").strip(),
        preco_por=preco_decimal(produto.get("preco")),
        preco_de=preco_decimal(produto.get("preco_de")),
        imagem_path=produto.get("imagem"),
        mais18=bool(produto.get("mais18") or produto.get("alcool")),
        marca_propria=bool(produto.get("marca_propria")),
        categoria=produto.get("categoria"),
        texto_legal=texto_val,
    )


def _compor_cartaz(layout, dados, *, rascunho: bool = True, qr_texto=None):
    """Compõe 1 página de cartaz a partir de um DadosProduto (com marca d'água
    RASCUNHO e QR opcional). Devolve (imagem, avisos_extra)."""
    from app.rendering.compositor import compor_pagina

    avisos: list[str] = []
    img = compor_pagina(layout, layout.paginas[0], dados)
    if rascunho:
        from app.rendering.marca_dagua import carimbar_rascunho
        img = carimbar_rascunho(img)
    if qr_texto:
        from app.rendering.qr import aplicar_qr
        from app.rendering.units import mm_para_px
        lado = round(mm_para_px(
            min(layout.largura_mm, layout.altura_mm) * 0.18, layout.dpi))
        img, aviso_qr = aplicar_qr(img, qr_texto, lado_px=lado)
        if aviso_qr:
            avisos.append(aviso_qr)
    return img, avisos


def cartaz_relampago(produto: dict, destino, *, layout=None,
                     validade_texto: str | None = None, qr_texto=None,
                     status_cb: StatusCb = lambda _m: None):
    """R-110: do produto ao PDF do cartaz num passo — sem montar nada na Mesa.

    Usa o layout padrão de cartaz + os dados do produto (de/por, foto oficial).
    Roda o pré-voo cartaz=True (sem foto/preço/“de” avisa ANTES do PDF, I2) e
    carimba a marca d'água RASCUNHO — não há projeto aprovado por trás, e um
    preço de balcão errado não pode ir limpo ao PDV (decisão travada; a 3ª
    porta de exportação). Devolve (Path, avisos)."""
    from app.rendering.cartaz import layout_cartaz_exemplo
    from app.rendering.export import exportar_pdf_multipagina

    layout = layout or layout_cartaz_exemplo()
    dados = dados_cartaz_de_produto(produto, validade_texto=validade_texto)
    slot_id = layout.paginas[0].slots[0].id
    status_cb("Conferindo o cartaz…")
    avisos = validar_composicao(layout, {slot_id: dados}, cartaz=True)
    status_cb("Compondo o cartaz…")
    img, extra = _compor_cartaz(layout, dados, rascunho=True, qr_texto=qr_texto)
    avisos.extend(extra)
    status_cb("Gravando o PDF…")
    caminho = exportar_pdf_multipagina([img], destino, layout.dpi)
    return caminho, avisos


def gerar_etiquetas_lote(itens: list[ItemMesa], destino,
                         status_cb: StatusCb = lambda _m: None,
                         *, dpi_folha: int | None = None,
                         rascunho: bool = True):
    """R-144 (FASE 12): dezenas de etiquetas por FOLHA — uma etiqueta por
    item selecionado (a mesma fonte de verdade do cartaz), impostas em A4
    com marcas de corte (imposição CONTROLADA, só no fluxo do cartaz).
    Devolve (caminho_pdf, avisos) — item sem preço entendido é AVISADO e a
    etiqueta sai mesmo assim (I2: aviso, nunca silêncio nem bloqueio).

    ``rascunho=True`` é o PADRÃO (frota F12: esta era a 4ª PORTA esquecida
    — relâmpago foi a 3ª, a Fábrica a 2ª): etiqueta com preço só sai LIMPA
    quando o chamador prova aprovação (`not pode_exportar_limpo` → True)."""
    from app.rendering.cartaz import layout_etiqueta
    from app.rendering.compositor import compor_pagina
    from app.rendering.export import exportar_pdf_multipagina
    from app.rendering.imposicao import impor_etiquetas
    from app.rendering.marca_dagua import carimbar_rascunho
    if not itens:
        raise ValueError("nenhum item selecionado para as etiquetas")
    lay = layout_etiqueta()
    sid = lay.paginas[0].slots[0].id
    avisos: list[str] = []
    etiquetas = []
    for i, it in enumerate(itens, 1):
        status_cb(f"Etiqueta {i}/{len(itens)}…")
        d = dados_cartaz_de_produto({
            "nome": it.nome, "preco": it.preco,
            "preco_de": it.preco_de, "imagem": it.imagem,
            "validade": it.validade})
        avisos.extend(f"“{it.nome}”: {a}"
                      for a in validar_composicao(lay, {sid: d}, cartaz=True))
        img = compor_pagina(lay, lay.paginas[0], {sid: d})
        if rascunho:
            img = carimbar_rascunho(img)
        etiquetas.append(img)
    status_cb("Impondo as etiquetas na folha…")
    folhas = impor_etiquetas(etiquetas, lay.dpi)
    caminho = exportar_pdf_multipagina(folhas, destino,
                                       dpi_folha or lay.dpi)
    return caminho, avisos


def gerar_kit_gondola(produto: dict, destino, *, layout_cartaz_fn=None,
                      layout_etiqueta_fn=None, n_etiquetas: int = 1,
                      validade_texto: str | None = None, qr_texto=None,
                      status_cb: StatusCb = lambda _m: None):
    """R-113: o KIT ponta-de-gôndola — cartaz + etiquetas do MESMO item de uma
    vez, num PDF (página 1 = cartaz; as demais = etiquetas).

    A coerência (mesmo preço/validade entre o cartaz e as etiquetas, R-113) é
    estrutural: TODAS as páginas saem do MESMO DadosProduto (uma fonte de
    verdade, ``dados_cartaz_de_produto``). Cada layout tem seu tamanho físico
    (o cartaz e a etiqueta são de tamanhos diferentes) e o PDF respeita cada um
    (páginas de tamanhos distintos, mesmo DPI). Pré-voo cartaz=True em ambos."""
    from app.rendering.cartaz import layout_cartaz_a5, layout_etiqueta
    from app.rendering.export import exportar_pdf_multipagina

    lay_cartaz = (layout_cartaz_fn or layout_cartaz_a5)()
    lay_etiq = (layout_etiqueta_fn or layout_etiqueta)()
    dados = dados_cartaz_de_produto(produto, validade_texto=validade_texto)
    avisos: list[str] = []
    for lay, quando in ((lay_cartaz, "cartaz"), (lay_etiq, "etiqueta")):
        sid = lay.paginas[0].slots[0].id
        avisos.extend(f"{quando}: {a}"
                      for a in validar_composicao(lay, {sid: dados}, cartaz=True))
    status_cb("Compondo o cartaz…")
    cartaz_img, extra = _compor_cartaz(lay_cartaz, dados, rascunho=True,
                                       qr_texto=qr_texto)
    avisos.extend(extra)
    paginas = [cartaz_img]
    for k in range(max(1, n_etiquetas)):
        status_cb(f"Compondo etiqueta {k + 1}/{max(1, n_etiquetas)}…")
        etiq_img, _ = _compor_cartaz(lay_etiq, dados, rascunho=True)
        paginas.append(etiq_img)
    status_cb("Gravando o kit…")
    # o cartaz e a etiqueta têm o MESMO DPI; o PDF fica multipágina/multitamanho
    caminho = exportar_pdf_multipagina(paginas, destino, lay_cartaz.dpi)
    return caminho, avisos


# --- caça-duplicatas (R-075, polimento: a UI que faltava) -----------------------

def pares_duplicatas() -> list[dict]:
    """R-075: os pares de duplicatas do acervo (EAN forte > chave natural),
    PLANOS para a UI do diálogo de fusão. Só leitura — nada muda aqui."""
    from sqlalchemy import select

    from app.core.database import Database
    from app.core.deduplicacao import achar_duplicatas
    from app.core.models import Produto
    db = Database().init()
    try:
        with db.Session() as s:
            prods = list(s.execute(select(Produto)).scalars())
            out = []
            for par in achar_duplicatas(prods):
                out.append({
                    "vencedor": _produto_plano(par.a),
                    "perdedor": _produto_plano(par.b),
                    "motivo": ("mesmo código de barras (EAN)"
                               if par.chave[0] == "ean"
                               else "mesmo nome e marca"),
                })
            return out
    finally:
        db.engine.dispose()


def fundir_duplicatas(pares: list[tuple[int, int]],
                      status_cb: StatusCb = lambda _m: None) -> dict:
    """R-075: funde os pares escolhidos (vencedor_id, perdedor_id) — o repetido
    vai para a LIXEIRA (soft-delete, reversível) e os aliases migram. Devolve
    {"fundidos": n, "aliases": n}."""
    from app.core.modo import exigir_escrita
    exigir_escrita()                 # R-131: PC da loja não edita
    from app.core.database import Database
    from app.core.deduplicacao import fundir_no_banco
    from app.core.paths import SystemRoot
    db = Database().init()
    fundidos = aliases = fotos = 0
    raiz_bib = SystemRoot().biblioteca_imagens
    try:
        with db.Session() as s:
            for i, (venc, perd) in enumerate(pares, 1):
                status_cb(f"Fundindo par {i}/{len(pares)}…")
                # OS F11.5 #33/#39: as fotos do perdedor viram versões
                r = fundir_no_banco(s, venc, perd, biblioteca_raiz=raiz_bib)
                fundidos += 1
                aliases += len(r["aliases_migrados"])
                fotos += len(r.get("fotos_migradas", []))
            s.commit()
    finally:
        db.engine.dispose()
    return {"fundidos": fundidos, "aliases": aliases, "fotos": fotos}


def correcoes_aprendidas() -> list[dict]:
    """OS F11.5 #43/#53/#91: as correções que o banco APRENDEU (aliases) —
    cada uma diz "quando a tabela escrever X, é o produto Y". A lista real,
    do banco (não uma imagem estática)."""
    from sqlalchemy import select

    from app.core.models import Produto, ProdutoAlias
    saida: list[dict] = []
    db = Database().init()
    try:
        with db.Session() as s:
            rows = s.execute(
                select(ProdutoAlias.id, ProdutoAlias.alias_raw,
                       Produto.id, Produto.nome_sanitizado)
                .join(Produto, Produto.id == ProdutoAlias.produto_id)
                .order_by(Produto.nome_sanitizado)).all()
            for aid, alias, pid, nome in rows:
                saida.append({"id": aid, "alias": alias,
                              "produto_id": pid, "produto": nome})
    finally:
        db.engine.dispose()
    return saida


def esquecer_correcao(alias_id: int) -> bool:
    """#43/#53/#91: REVERTE uma correção aprendida (apaga o alias) — na
    próxima importação aquele texto volta a ser conferido pelo humano."""
    from app.core.models import ProdutoAlias
    db = Database().init()
    try:
        with db.Session() as s:
            row = s.get(ProdutoAlias, alias_id)
            if row is None:
                return False
            s.delete(row)
            s.commit()
            return True
    finally:
        db.engine.dispose()


# --- aceitar 🟡 (aprende alias) -------------------------------------------------

def aceitar_correspondencia(item: ItemMesa) -> ItemMesa:
    """Confirma o palpite do banco para o item 🟡 e APRENDE o alias."""
    from app.core.repositories import ProdutoRepositorio

    db = Database().init()
    try:
        with db.Session() as session:
            repo = ProdutoRepositorio(session)
            repo.aprender_alias(item.produto_id, item.descricao)
            session.commit()
            p = repo.get(item.produto_id)
            item.semaforo = "VERDE"
            item.via = "alias"
            item.nome = p.nome_sanitizado
            item.imagem = _imagem_absoluta(p.caminho_imagem)
            item.mais18 = bool(p.selo_mais18)
            item.preco_de = _preco_texto(p.preco_atual)
    finally:
        db.engine.dispose()
    return item


# --- criar 🔴: enriquecer + candidatos de imagem --------------------------------

@dataclass
class PropostaCriacao:
    """O que o worker apronta para o diálogo de curadoria."""

    nome: str
    mais18: bool
    categoria: str | None
    candidatos: list[str] = field(default_factory=list)   # caminhos baixados
    # RG-20: palavras do bruto que a IA descartou — a curadoria AVISA e o
    # humano decide (o nome nunca é aceito em silêncio com perda)
    tokens_perdidos: list[str] = field(default_factory=list)
    # RG-29: DUAS marcas na mesma linha → nomes dos componentes (a criação
    # nasce composta; lista vazia = produto único de sempre)
    componentes: list[str] = field(default_factory=list)


def marcas_do_acervo() -> list[str]:
    """OS F11.5 #49: as marcas CONFIRMADAS — as distintas do banco + as
    marcas próprias da Config. Degrada para lista vazia (nunca inventa)."""
    marcas: list[str] = []
    try:
        from sqlalchemy import select

        from app.core.models import Produto
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                for (m,) in s.execute(select(Produto.marca).distinct()):
                    if m and str(m).strip():
                        marcas.append(str(m).strip())
                proprias = ConfigRepositorio(s).get("marcas.proprias", []) or []
        finally:
            db.engine.dispose()
        for m in proprias:
            if m and str(m).strip() and str(m).strip() not in marcas:
                marcas.append(str(m).strip())
    except Exception:
        pass
    return marcas


def enriquecer_descricao(descricao: str, motor=None) -> PropostaCriacao:
    """SÓ a metade do nome (sem busca de imagem) — a fila em lote usa isto.

    RG-02a: os vermelhos são enriquecidos em fila logo após a conciliação.
    Guarda do ``motor`` None (LM desligado): degrada para o determinístico —
    conserta o bug latente em que ``enriquecer(desc, None)`` estourava
    AttributeError em vez de degradar.
    """
    if motor is None:
        from app.core.aprendizado import ordenar_tipo_marca
        from app.core.sanitize import sanitizar
        res = sanitizar(descricao)
        # OS F11.5 #49: a marca CONHECIDA vai para o lugar da casa
        # (Tipo+Marca+…) mesmo sem IA — determinístico, nunca inventa
        nome = res.nome_sanitizado
        try:
            nome = ordenar_tipo_marca(nome, marcas_do_acervo())
        except Exception:
            pass
        return PropostaCriacao(nome=nome, mais18=False,
                               categoria=None)
    from app.ai.enriquecimento import enriquecer
    enr = enriquecer(descricao, motor)
    return PropostaCriacao(nome=enr.nome_sanitizado, mais18=enr.mais18,
                           categoria=enr.categoria,
                           tokens_perdidos=list(enr.tokens_perdidos),
                           componentes=[c.nome_sanitizado
                                        for c in enr.componentes])


def candidatos_do_acervo(nome: str, limite: int = 2) -> list[str]:
    """OS F11.5 #49: fotos JÁ TRATADAS do acervo cujo produto casa o nome
    (fuzzy ≥ 82) — aparecem ANTES da web na curadoria: packshot pronto ganha
    de download cru. Degrada para lista vazia."""
    saida: list[tuple[float, str]] = []
    try:
        from rapidfuzz import fuzz
        from sqlalchemy import select

        from app.core.models import Produto
        raiz = SystemRoot().biblioteca_imagens
        db = Database().init()
        try:
            with db.Session() as s:
                rows = s.execute(select(
                    Produto.nome_sanitizado, Produto.caminho_imagem).where(
                    Produto.caminho_imagem.is_not(None))).all()
        finally:
            db.engine.dispose()
        for nome_p, rel in rows:
            score = fuzz.token_set_ratio((nome or "").lower(),
                                         (nome_p or "").lower())
            if score >= 82:
                cam = raiz / str(rel).replace("\\", "/")
                if cam.is_file():
                    saida.append((score, str(cam)))
    except Exception:
        return []
    saida.sort(key=lambda p: -p[0])
    return [c for _s, c in saida[:limite]]


def buscar_candidatos_para(nome: str, status_cb: StatusCb,
                           n_candidatos: int = 6,
                           ean: str | None = None) -> list[str]:
    """Candidatos de imagem para um nome JÁ enriquecido (degrada p/ vazio).

    RG-41 (a cascata da pesquisa): com EAN, o packshot do Open Food Facts
    vem PRIMEIRO (foto oficial pelo código de barras); o ACERVO vem antes da
    web (#49 — foto tratada da casa ganha de download); o ddgs completa. OFF
    sem resultado/sem rede AVISA e segue — nunca cala a busca (I2).
    """
    termo = remover_marcas_do_termo(nome)   # RG-30: a sigla não vai à busca
    staging = Path(tempfile.mkdtemp(prefix="atb_curadoria_"))
    encontrados: list[str] = []
    if ean:
        status_cb(f"Procurando pelo código de barras {ean}…")
        from app.images.off import buscar_imagem_off
        oficial = buscar_imagem_off(ean, staging)
        if oficial:
            encontrados.append(oficial)
        else:
            status_cb("Código não achado no Open Food Facts — "
                      "buscando na web…")
    # #49: o ACERVO vem antes da web (depois da foto oficial do EAN)
    do_acervo = candidatos_do_acervo(nome)
    if do_acervo:
        status_cb(f"{len(do_acervo)} foto(s) parecidas no seu acervo…")
        encontrados.extend(do_acervo)
    status_cb(f"Buscando imagem de “{termo[:40]}”…")
    from app.images.busca import BaixadorWeb, buscar_imagens
    try:
        r = buscar_imagens(termo, BaixadorWeb(min_lado_hint=300),
                           staging, n=n_candidatos, min_lado=300)
        encontrados += [str(c.caminho) for c in r.candidatos]
    except Exception:
        pass                        # sem rede → segue com o que o OFF deu
    return encontrados              # vazio = degradação avisada de sempre


def preparar_criacao(descricao: str, status_cb: StatusCb,
                     n_candidatos: int = 6,
                     ean: str | None = None) -> PropostaCriacao:
    """Enriquece o nome (IA ou degradado) e baixa candidatos de imagem."""
    status_cb("Enriquecendo nome…")
    proposta = enriquecer_descricao(descricao, _motor_se_disponivel())
    proposta.candidatos = buscar_candidatos_para(proposta.nome, status_cb,
                                                 n_candidatos, ean=ean)
    return proposta


def tratar_imagem(fonte: str, status_cb: StatusCb) -> str:
    """Baixa (se URL), remove o fundo + recorta/normaliza. Devolve o tratado.

    ``fonte``: caminho de arquivo OU URL (o "colar URL" da curadoria).
    """
    caminho = Path(fonte)
    if fonte.startswith(("http://", "https://")):
        status_cb("Baixando imagem…")
        import requests
        resp = requests.get(fonte, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        resp.raise_for_status()
        caminho = Path(tempfile.mkdtemp(prefix="atb_url_")) / "baixada"
        caminho.write_bytes(resp.content)

    from app.images.fundo import _sessoes, modelo_configurado, processar_imagem
    modelo = modelo_configurado()          # RG-02: escolha da Config
    if modelo not in _sessoes:             # o dono vê ONDE o tempo vai (RG-02)
        status_cb("Carregando o modelo de recorte (1ª vez — pode levar "
                  "alguns segundos)…")
    else:
        status_cb("Removendo fundo…")
    destino = Path(tempfile.mkdtemp(prefix="atb_tratada_")) / "tratada.png"
    processar_imagem(caminho, destino, modelo=modelo)
    return str(destino)


def estudio_gerador_ligado() -> bool:
    """OS F11.5 #20: a flag "Estúdio IA (gerador)" da Config — liga o degrau 2
    (img2img local). Padrão DESLIGADO (o degrau 2 é opção condicionada à GPU,
    nunca requisito). Falha de leitura = desligado."""
    try:
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                return bool(ConfigRepositorio(s).get("estudio.gerador", False))
        finally:
            db.engine.dispose()
    except Exception:
        return False


def tratar_estudio(fonte: str, status_cb: StatusCb, *,
                   com_gerador: bool = False) -> str:
    """R-091 (Estúdio degrau 1): foto crua → PACKSHOT (fundo limpo + luz + sombra
    + enquadramento). Baixa se URL; reusa o mesmo modelo de recorte. Roda em CPU,
    qualquer PC. `com_gerador` tenta o degrau 2 (img2img) — sem GPU degrada com
    aviso e fica no degrau 1 (RG-46 nunca bloqueia). Devolve o PNG do packshot."""
    import tempfile

    from PIL import Image

    from app.images.estudio import packshot_degrau1, refinar_com_gerador
    caminho = Path(fonte)
    if fonte.startswith(("http://", "https://")):
        status_cb("Baixando imagem…")
        import requests
        resp = requests.get(fonte, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        resp.raise_for_status()
        caminho = Path(tempfile.mkdtemp(prefix="atb_url_")) / "baixada"
        caminho.write_bytes(resp.content)
    status_cb("Estúdio: removendo o fundo e montando o packshot…")
    # OS F11.5 #57 (R-102): a sombra acompanha o TEMA da arte em uso
    from app.qt.design import tokens as _t
    pack = packshot_degrau1(Image.open(caminho),
                            tema=getattr(_t, "TEMA_ATUAL", "claro"))
    if com_gerador:
        status_cb("Estúdio gerador (degrau 2)…")
        melhor, aviso = refinar_com_gerador(pack)
        if melhor is not None:
            pack = melhor
        elif aviso:
            status_cb(aviso)                   # degrada COM aviso (I2)
    destino = Path(tempfile.mkdtemp(prefix="atb_packshot_")) / "packshot.png"
    pack.convert("RGBA").save(destino, "PNG")
    return str(destino)


def finalizar_criacao(item: ItemMesa, nome: str, mais18: bool,
                      imagem_tratada: str | None,
                      categoria: str | None = None) -> ItemMesa:
    """Cadastra o produto novo no banco (+ imagem na biblioteca) → item 🟢.

    RG-23: a categoria da IA (mesmo prompt do enriquecer) entra JÁ na
    criação — acabou o acervo "tudo Outros" por lote nunca rodado.
    """
    from app.core.modo import exigir_escrita
    exigir_escrita()                 # R-131: PC da loja não edita
    from app.core.repositories import ProdutoRepositorio
    from app.images.biblioteca import BibliotecaImagens

    db = Database().init()
    try:
        with db.Session() as session:
            repo = ProdutoRepositorio(session)
            res = repo.importar(item.descricao, preco=item.preco)
            produto = res.produto
            repo.editar(produto.id, nome_sanitizado=nome, selo_mais18=mais18)
            if categoria:                # IA sem palpite deixa vazio (→ "Outros")
                repo.editar(produto.id, categoria=categoria,
                            categoria_origem="ia")
            if eh_marca_propria(nome) or eh_marca_propria(item.descricao):
                repo.editar(produto.id, marca_propria=True)   # RG-30
            if imagem_tratada:
                bib = biblioteca_da_config()          # #51/#52: WebP opcional
                bib.ingerir(produto.id, imagem_tratada)
                repo.editar(produto.id,
                            caminho_imagem=bib.caminho_relativo(produto.id))
            session.commit()
            item.produto_id = produto.id
    finally:
        db.engine.dispose()
    item.semaforo = "VERDE"
    item.via = "novo"
    item.nome = nome
    item.mais18 = mais18
    item.imagem = imagem_tratada and _imagem_absoluta(
        f"{item.produto_id}/atual.png")
    return item
