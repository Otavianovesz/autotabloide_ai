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

import re
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
    # F13/COND-5 (selo do B, §5.6): a marca própria FLUI — o selo
    # "Qualidade" tinha o mesmo furo que o +18 tinha (campo que não
    # viajava do banco até a receita do cartaz/tabloide)
    marca_propria: bool = False
    via: str = ""                  # exato | alias | fuzzy | juiz | novo | banco
    score: float = 0.0
    candidato_nome: str = ""       # melhor palpite do banco (para o 🟡)
    # ADENDO 30/07: os TOP candidatos do banco viajam à UI (o motor
    # sempre calculou 5 e jogava fora 4 — se o certo era o nº2, o dono
    # criava duplicata). Lista de dicts {produto_id, nome, score}.
    candidatos: list = field(default_factory=list)
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
    # F13-TERTIUSDECIMUS/Q2: desconto DECLARADO na tabela ("com 20% de
    # desconto", sem preço) — a célula mostra o percentual (papel
    # DESCONTO) e o pré-voo não acusa "sem preço"
    desconto_pct: int | None = None
    # R-071 (Fase 7): observação por item ("limite 2 por cliente") — texto
    # OPCIONAL que vira uma região condicional (papel OBSERVACAO): só desenha
    # se preenchida; vazia não é problema no pré-voo (não-ocupável, lei da casa).
    observacao: str | None = None
    # Rodada JM (B3): os CÓDIGOS de pendência do sanitize ("multiplos",
    # "letra_isolada"…) viajam com o item VERMELHO — a curadoria usa
    # (a pergunta "são 2 produtos?" nasce daqui). Aditivo: from_dict
    # filtra chaves, projeto antigo abre normal.
    pendencias: list = field(default_factory=list)
    # QUINTUSDECIMUS/J18: o "de" veio DA TABELA ("de 18,81 por 6,90") —
    # quando True, o de/por e o % calculado desenham no tabloide (o
    # preco_de do BANCO continua só painel/cartaz, como sempre foi)
    preco_de_da_tabela: bool = False
    # QUINTUSDECIMUS: o MOTIVO do semáforo (a frase do veredito) viaja
    # até a tela — o amarelo diz POR QUÊ (tooltip da Situação)
    motivo: str = ""
    # Rodada JM (B4): a FAMÍLIA de sabores do produto casado —
    # {"id", "nome", "membros": [{"produto_id","nome","imagem"}]}.
    # Acende o "Sabores da família…" na estante; None = produto sem
    # família (o caminho comum não muda). Congela com o projeto.
    familia: dict | None = None
    # SEXTUSDECIMUS/M3: os SABORES da linha da oferta ("Branco", "Oreo").
    # O nome da célula fica o base da família; os sabores vão ao
    # DESCRITOR ("Branco ou Oreo · 45 g") — o cliente descobre o que há.
    sabores: list = field(default_factory=list)
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
    # Bancada dos Exemplos (P0.3c): porcentagem NUNCA é preço — "50% de
    # desconto" virava R$ 50,00 (valor errado é pior que ausente, I2); o
    # número colado num % sai da mesa e o que sobrar decide
    txt = re.sub(r"[\d.,]+\s*%", " ", str(txt))
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


def garantir_modelo_recorte(pai) -> bool:
    """F13/E1 (CA-01): a PERGUNTA do 1º recorte — o download de ~973 MB
    era disparado pelo BOOT, sem pedir, com o progresso indo para o
    stderr morto do exe. Três saídas: baixar o completo, usar o LEVE
    (~5 MB — grava na MESMA chave do combo das Configurações) ou agora
    não. True = pode seguir (o download em si acontece no worker do
    tratamento, narrado pela faixa de rodapé do D1)."""
    from app.images.fundo import modelo_baixado, modelo_configurado
    modelo = modelo_configurado()
    if modelo_baixado(modelo):
        return True
    from PySide6.QtWidgets import QMessageBox
    caixa = QMessageBox(pai)
    caixa.setWindowTitle("Modelo de recorte")
    caixa.setIcon(QMessageBox.Icon.Question)
    caixa.setText(
        "Para recortar o fundo das fotos, o app precisa baixar um modelo "
        "(uma vez só — precisa de internet).\n\n"
        "• Completo: qualidade máxima (~973 MB, demora)\n"
        "• Leve: ~5 MB, qualidade menor — dá para trocar depois nas "
        "Configurações › Imagens.")
    b_full = caixa.addButton("Baixar o completo (973 MB)",
                             QMessageBox.ButtonRole.AcceptRole)
    caixa.addButton("Usar o leve (~5 MB)",
                    QMessageBox.ButtonRole.ActionRole)
    b_nao = caixa.addButton("Agora não", QMessageBox.ButtonRole.RejectRole)
    caixa.setDefaultButton(b_nao)      # a lei do B3: Enter não baixa 1 GB
    caixa.setEscapeButton(b_nao)
    caixa.exec()
    clicado = caixa.clickedButton()
    if clicado is b_nao:
        return False
    if clicado is not b_full:          # o leve: grava a escolha na Config
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                ConfigRepositorio(s).set("imagem.modelo_rembg", "u2netp")
                s.commit()
        finally:
            db.engine.dispose()
    return True


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
        marca_propria=d.get("marca_propria", False),        # F13/COND-5
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
                       validade: str | None = None,
                       edicao: str | None = None,
                       marcas: set[str] | frozenset[str] | None = None):
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
    # F13-BIS/T2: o DESCRITOR da 2ª linha dos encartes ("marca própria ·
    # 100 g") — composto do que o item carrega hoje; a observação NÃO
    # entra (tem região própria, R-071)
    # SEXTUSDECIMUS/M3: os SABORES da linha abrem o descritor ("Tomate,
    # Óleo ou Limão · 125 g") — o nome fica o base da família e o
    # cliente descobre o que existe
    descritor = " · ".join(p for p in (
        juntar_com_ou(getattr(it, "sabores", None) or []) or None,
        "marca própria" if it.marca_propria else None,
        it.unidade) if p) or None
    # RODADA-125 v2 — a REGRA CANÔNICA da célula: as marcas conhecidas
    # do nome viajam no dado; a cadeia do nome_fit as desce ao
    # descritor (e dedupa o peso repetido) SÓ onde há SUBTITULO — em
    # célula sem descritor a marca fica no nome (nada some, I2)
    marcas_nome: tuple[str, ...] = ()
    if marcas:
        from app.core.marcas import marcas_no_nome
        marcas_nome = tuple(marcas_no_nome(nome, marcas))
    return DadosProduto(
        nome,
        selos_extra=extras,
        preco_por=preco_decimal(it.preco),
        # QUINTUSDECIMUS/J18: o "de" que veio DA TABELA desenha no
        # tabloide (riscado + % calculado onde o layout tiver as
        # regiões) — o preco_de do BANCO segue só painel/cartaz, para
        # não mudar páginas existentes por baixo do dono
        preco_de=(preco_decimal(it.preco_de)
                  if getattr(it, "preco_de_da_tabela", False) else None),
        multi_preco=it.multi_preco,          # R-070: "3 por R$10"
        observacao=it.observacao,            # R-071: "limite 2 por cliente"
        imagem_path=it.imagem,
        imagens=[ImagemSlot(c) for c in (it.imagens or [])],
        modo_arranjo=arranjo,
        mais18=it.mais18,
        marca_propria=it.marca_propria,                     # F13/COND-5
        unidade=it.unidade,
        descritor=descritor,                 # F13-BIS/T2
        desconto_pct=getattr(it, "desconto_pct", None),   # Q2
        marcas_nome=marcas_nome,             # v2: a hierarquia canônica
        sabores=tuple(getattr(it, "sabores", None) or ()),   # v3
        categoria=it.categoria,          # F8.2: as seções derivam daqui
        # RG-34: o de/até já vem como frase completa ("OFERTA VÁLIDA DE …");
        # o legado ("ATÉ 24/07" do OCR/RG-24) ganha o prefixo
        texto_legal=(validade
                     if (validade or "").upper().startswith("OFERTA")
                     else f"Ofertas válidas {validade}"
                     if validade else None),
        edicao=edicao,                       # F13-TER/D1: a edição viva
    )


def aplicar_secoes_do_agrupar(paginas, agrupar: bool) -> None:
    """RODADA-125 (achado 1 das seções): o agrupar SÓ liga o DESENHO de
    seções onde a página define estilo PRÓPRIO — os encartes da
    biblioteca (o Jornal) nascem com ``secoes_ligadas=False`` de
    propósito e o toggle antigo os ligava no CONTORNO global: chips por
    cima de títulos, molduras cortando colunas (as fotos do dono,
    03/08). Sem estilo próprio, agrupar vale como ORDENAÇÃO da fila.
    Desagrupar desliga em todas (o toggle por página, B3, segue
    mandando depois)."""
    for pag in paginas:
        if agrupar:
            if getattr(pag, "estilo_secoes", None):
                pag.secoes_ligadas = True
        else:
            pag.secoes_ligadas = False


def marcas_para_exibicao() -> set[str]:
    """RODADA-125 v2 — o vocabulário de marcas da REGRA CANÔNICA da
    célula: o seed do mercado + as marcas do acervo + as próprias da
    Config, normalizado. Carregar 1× POR LOTE/página (a lição de
    desempenho da Rodada JM) e passar a ``dados_para_desenho``."""
    from app.core.marcas import marcas_conhecidas
    return marcas_conhecidas(tuple(marcas_do_acervo()))


def dados_de_pagina(validade: str | None):
    """QUINTUSDECIMUS/J24: um DadosProduto "de página" que carrega SÓ o
    texto_legal (a validade formatada) — vai no dict sob a chave
    "__pagina__", que nunca casa slot algum: nada desenha por ele, mas
    os textos de página (manchete viva, rodapé) o enxergam via
    `_campo_vivo_da_pagina` mesmo com a página ainda vazia."""
    from app.rendering.compositor import DadosProduto
    return DadosProduto(
        "", texto_legal=(validade
                         if (validade or "").upper().startswith("OFERTA")
                         else (f"Ofertas válidas {validade}"
                               if validade else None)))


def dados_cartaz_de_item(it: "ItemMesa", *,
                         validade_texto: str | None = None):
    """F13/B6 (F-01): a receita ÚNICA ItemMesa→DadosProduto de cartaz e
    etiqueta. Havia TRÊS receitas quase-iguais (a da Fábrica, a das
    etiquetas em lote e o dict do projeto reaberto) e a divergência era a
    causa da etiqueta de bebida sair SEM o selo +18 (decisão travada
    ferida em silêncio) e do projeto CARTAZ reaberto perder mais18 e
    categoria. Toda porta de cartaz passa por AQUI."""
    return dados_cartaz_de_produto({
        "nome": it.nome, "preco": it.preco, "preco_de": it.preco_de,
        "imagem": it.imagem, "validade": it.validade,
        "mais18": it.mais18, "categoria": it.categoria,
        "marca_propria": it.marca_propria,                  # F13/COND-5
    }, validade_texto=validade_texto)


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
            # F13/B6: a receita ÚNICA — o dict incompleto daqui perdia
            # mais18/categoria no projeto CARTAZ reaberto (Modo Pai incluso)
            dados[sid] = dados_cartaz_de_item(
                it, validade_texto=aberto.validade_oferta)
    else:
        abrev = abreviacoes_tabloide()
        registro = selos_disponiveis()
        mset = marcas_para_exibicao()        # v2: 1× por projeto aberto
        for sid, uid in (aberto.mapa or {}).items():
            it = por_uid.get(uid)
            if it is None:
                faltas.append(f"célula {sid}: o item do projeto sumiu")
                continue
            d = dados_para_desenho(it, abrev or None, registro,
                                   aberto.validade_oferta,
                                   edicao=getattr(aberto, "edicao", None),
                                   marcas=mset)
            ov = (aberto.overrides or {}).get(sid)
            dados[sid] = aplicar_override(d, ov) if ov else d
    for sid, d in dados.items():
        cam = getattr(d, "imagem_path", None)
        if cam and not Path(cam).exists():
            faltas.append(f"a foto de “{d.nome}” sumiu do disco")
    return dados, faltas


# --- agrupar por categoria (F8.2/A2): ordenação prévia, nunca vínculo ------------

OUTROS = "Outros"


def checklist_final(itens: list[ItemMesa], validade: str | None,
                    *, cartaz: bool = False):
    """R-063: checklist antes de exportar, gerado do ESTADO REAL do projeto —
    marca sozinho o que já está ok. Devolve [(pergunta, ok, detalhe)].

    F13/D8: no modo ``cartaz`` a pergunta da validade DA OFERTA sai — o
    cartaz não tem validade de oferta (a de item é o RG-58); era por isso
    que a aprovação seria inalcançável na Fábrica (P-07)."""
    n = len(itens)
    sem_foto = [it for it in itens if not (it.imagem or it.imagens)]
    sem_preco = [it for it in itens
                 if preco_decimal(it.preco) is None and not it.multi_preco]
    bebidas = [it for it in itens if it.mais18]
    perguntas = [
        ("Todos os itens têm foto?", not sem_foto,
         "ok" if not sem_foto else f"{len(sem_foto)} sem foto"),
        ("Todos os itens têm preço entendido?", not sem_preco,
         "ok" if not sem_preco else f"{len(sem_preco)} sem preço"),
    ]
    if not cartaz:
        perguntas.append(
            ("A validade da oferta está definida?", bool(validade),
             validade or "defina a validade de/até"))
    perguntas += [
        ("As bebidas alcoólicas estão com +18?", True,
         f"{len(bebidas)} bebida(s) — o selo +18 é automático"
         if bebidas else "nenhuma bebida alcoólica"),
        ("Há itens na oferta?", n > 0, f"{n} item(ns)"),
    ]
    return perguntas


def aprovar_projeto(projeto_id, itens: list[ItemMesa], validade: str | None,
                    *, cartaz: bool = False):
    """R-068 (aprovação em 2 etapas): aprovar EXIGE a conferência — roda o
    checklist da F7 e só aprova se TUDO estiver ok. Não é clique cego. Devolve
    (aprovado, faltas) — `faltas` é a lista de perguntas ainda não resolvidas."""
    faltas = [p for p, ok, _d in
              checklist_final(itens, validade, cartaz=cartaz) if not ok]
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


# --- F13/D12 (VC-081): atualizar preços da oferta ABERTA por chave natural --

@dataclass
class PlanoPrecos:
    """A prévia do 'Atualizar preços' — nada muda até aplicar (o padrão
    prévia→confirma da ponte Excel R-118)."""

    atualizaveis: list = field(default_factory=list)   # (da_estante, novo)
    sem_par: list = field(default_factory=list)        # novos sem par
    nao_citados: list = field(default_factory=list)    # da estante, fora
    identicos: int = 0


def plano_atualizar_precos(estante: list["ItemMesa"],
                           novos: list["ItemMesa"]) -> PlanoPrecos:
    """A semana RECORRENTE: casa estante×tabela nova por CHAVE NATURAL
    (nunca posição, I1) e lista o que mudaria. Não grava nada."""
    por_chave: dict = {}
    for it in estante:
        por_chave.setdefault(chave_natural(it), it)
    plano = PlanoPrecos()
    casados: set = set()
    for n in novos:
        alvo = por_chave.get(chave_natural(n))
        if alvo is None:
            plano.sem_par.append(n)
            continue
        casados.add(alvo.uid)
        if ((n.preco or "") != (alvo.preco or "")
                or n.preco_de != alvo.preco_de
                or n.multi_preco != alvo.multi_preco):
            plano.atualizaveis.append((alvo, n))
        else:
            plano.identicos += 1
    plano.nao_citados = [it for it in estante if it.uid not in casados]
    return plano


def aplicar_atualizacao_precos(plano: PlanoPrecos) -> int:
    """Muta SÓ os campos de preço dos itens da ESTANTE — o uid, o mapa,
    os overrides e a montagem ficam exatamente onde estão (I1)."""
    for alvo, novo in plano.atualizaveis:
        alvo.preco = novo.preco
        alvo.preco_de = novo.preco_de
        alvo.multi_preco = novo.multi_preco
    return len(plano.atualizaveis)


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

# F13-DECIMUS/D1: o período do mês (o Jornal) — sentinela devolvida no
# lugar do dia da semana quando o nome fala de mês, não de dia
PERIODO_MES = "mes"

# os radicais do dia no NOME do layout — casados por PALAVRA INTEIRA,
# sem acento e sem caixa (a disciplina do extrair_marca: ambíguo = None)
_RADICAIS_DIA = (
    (0, ("segunda", "seg")),
    (1, ("terca", "ter")),
    (2, ("quarta", "qua")),
    (3, ("quinta", "quintou", "qui")),
    (4, ("sexta", "sex")),
    (5, ("sabado", "sab")),
    (6, ("domingo", "dom")),
)
_RADICAIS_PERIODO = ("jornal", "mes", "mensal")


def _sem_acento(texto: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in t if not unicodedata.combining(c))


def dia_pelo_nome(nome: str | None):
    """F13-DECIMUS/D1: o dia da semana escrito no NOME do layout.

    "Segunda dos Frios" É segunda-feira — a resposta estava no nome do
    arquivo o tempo todo (P-01). Casa por PALAVRA INTEIRA, nunca por
    pedaço ("Promoção Relâmpago" nunca vira segunda por conter "ão").
    Devolve 0..6, ``PERIODO_MES`` (jornal/mensal) ou None."""
    if not nome:
        return None
    tokens = set(_sem_acento(nome).lower().split())
    if tokens & set(_RADICAIS_PERIODO):
        return PERIODO_MES
    for dia, radicais in _RADICAIS_DIA:
        if tokens & set(radicais):
            return dia
    return None


def dia_do_evento(evento: str | None):
    """O dia da semana (0=seg…6=dom) do evento, ``PERIODO_MES`` ou None.

    F13-DECIMUS/D1 — a CASCATA de fontes, nesta ordem:
    1. a entidade Evento (``dia_semana``) — continua mandando;
    2. a Config antiga ``eventos.dias`` (fallback legado);
    3. o NOME em si (``dia_pelo_nome``) — o dono abre "Segunda dos
       Frios" e o app SABE que é segunda, zero configuração;
    4. nada casou → None, e aí sim o app pergunta."""
    if not evento:
        return None
    try:
        from app.qt.telas.eventos import dia_do_evento_v2
        db = Database().init()
        try:
            with db.Session() as s:
                dia = dia_do_evento_v2(s, evento)
        finally:
            db.engine.dispose()
    except Exception:
        dia = None
    if dia is not None:
        return dia
    return dia_pelo_nome(evento)


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
    if dia == PERIODO_MES:
        # F13-DECIMUS/D1: o Jornal vale do dia 1º ao 27 — o período
        # corrente enquanto o 27 não passou; depois, o do mês seguinte
        # (a mesma semântica do "hoje conta" da próxima ocorrência)
        h = hoje or date.today()
        if h.day > 27:
            h = (h.replace(day=1) + timedelta(days=32)).replace(day=1)
        return f"DE 01/{h.month:02d} A 27/{h.month:02d}"
    data = proxima_ocorrencia(dia, hoje)
    return f"SOMENTE {data.strftime('%d/%m')}"


def avisos_da_validade(validade: str | None, nome_layout: str | None = None,
                       evento: str | None = None, hoje=None) -> list[str]:
    """F13-DECIMUS/D4: as guardas de sanidade da data — AVISAM, nunca
    vetam (a trava #3 caiu e continua caída), e toda frase diz ONDE
    clicar. Com a data preenchendo sozinha, o risco novo é data errada
    passar despercebida (o M-02: o marco publicado com validade de maio
    em julho).

    Rodada JM (B2A): as guardas leem o PAR (início, fim) da régua única
    `datas_da_validade` — o "já passou" compara com a data-FIM (o falso
    positivo que gritaria o mês inteiro do Jornal morreu), o ano escrito
    é respeitado e o "fora do mês" olha o INTERVALO, não a 1ª data.

    Validade sem data nenhuma ("enquanto durarem os estoques") passa em
    silêncio — as guardas são DE DATA."""
    import re as _re
    from datetime import date as _date

    from app.core.validade import datas_da_validade
    if not (validade or "").strip():
        return []
    if not _re.search(r"\d{1,2}/\d{1,2}", validade):
        return []                       # escolha legítima sem data
    hoje = hoje or _date.today()
    de, ate = datas_da_validade(validade, hoje)
    if de is None and ate is None:
        return [f"a validade “{validade}” tem uma data que não existe — "
                "clique no 📅 na barra da Mesa"]
    inicio = de or ate
    fim = ate or de
    avisos: list[str] = []
    if fim < hoje:
        avisos.append(f"a validade “{validade}” já passou — clique no 📅 "
                      "na barra da Mesa para corrigir")
    elif not ((inicio.year, inicio.month) <= (hoje.year, hoje.month)
              <= (fim.year, fim.month)):
        avisos.append(f"a validade “{validade}” está fora do mês corrente "
                      "— confira no 📅 da barra da Mesa (pode ser "
                      "legítimo no Jornal)")
    # o dia da semana só faz sentido para oferta de UM dia
    if inicio == fim:
        dia = dia_do_evento(evento) if evento else None
        if dia is None:
            dia = dia_pelo_nome(nome_layout)
        if isinstance(dia, int) and inicio.weekday() != dia:
            avisos.append(f"a validade “{validade}” não bate com o dia do "
                          "encarte — confira no 📅 da barra da Mesa")
    return avisos


# --- F13-TER/D1: a EDIÇÃO do Jornal é REAL ("Nº 177 · ANO 42" mudava todo
# mês e estava cravada na arte) --------------------------------------------------


def sugerir_edicao(evento: str | None, hoje=None) -> str | None:
    """A edição sugerida a partir da BASE registrada (o nº/ano de uma
    edição conhecida do evento): o NÚMERO incrementa por mês corrido
    desde a base e o ANO (de circulação do jornal) vira junto com o ano
    civil. Sem base registrada, sem palpite (None) — a região EDICAO
    fica muda e o pré-voo avisa; um número inventado seria rótulo
    mentindo (§4 da ordem TER)."""
    from datetime import date
    if not evento:
        return None
    try:
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                mapa = ConfigRepositorio(s).get("eventos.edicao_base") or {}
        finally:
            db.engine.dispose()
    except Exception:
        return None
    base = next((v for k, v in mapa.items()
                 if k.strip().lower() == evento.strip().lower()), None)
    if not isinstance(base, dict):
        return None
    try:
        numero, ano = int(base["numero"]), int(base["ano"])
        ano_civil, mes = (int(x) for x in str(base["quando"]).split("-")[:2])
    except (KeyError, TypeError, ValueError):
        return None
    d = hoje or date.today()
    meses = (d.year - ano_civil) * 12 + (d.month - mes)
    if meses < 0:
        return None                       # base do futuro: sem palpite
    return f"Nº {numero + meses} · ANO {ano + (d.year - ano_civil)}"


def registrar_edicao_publicada(evento: str | None, edicao: str | None,
                               hoje=None) -> None:
    """Grava a edição EXPORTADA do evento — o pré-voo compara contra ela
    para avisar "esta edição já foi publicada" (nunca repetir o número
    da edição anterior). Se a edição parsear ("Nº 178 · ANO 42"), também
    REALIMENTA a base da sugestão: o dono digita uma vez e os meses
    seguintes se sugerem sozinhos. Nunca levanta (registro é rede)."""
    import re
    from datetime import date
    if not evento or not (edicao or "").strip():
        return
    try:
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                repo = ConfigRepositorio(s)
                mapa = repo.get("eventos.edicao_publicada") or {}
                mapa[evento.strip().lower()] = edicao.strip()
                repo.set("eventos.edicao_publicada", mapa)
                m = re.search(r"N[º°o]?\s*(\d+).*?ANO\s*(\d+)",
                              edicao, re.IGNORECASE)
                if m:
                    d = hoje or date.today()
                    base = repo.get("eventos.edicao_base") or {}
                    base[evento.strip().lower()] = {
                        "numero": int(m.group(1)), "ano": int(m.group(2)),
                        "quando": f"{d.year:04d}-{d.month:02d}"}
                    repo.set("eventos.edicao_base", base)
                s.commit()
        finally:
            db.engine.dispose()
    except Exception:
        pass


def atualizar_fixos_pela_tabela(layout, itens) -> list[str]:
    """F13-TER/N1: item FIXO com "preço da semana" atualiza quando o
    produto APARECE na tabela importada — casamento por CHAVE NATURAL
    (D12, nunca OCR forçado). Preço fixo nunca é tocado; ausente mantém
    o que está. Devolve avisos NOMEADOS (I2) das atualizações feitas."""
    from app.core.portabilidade import chave_natural
    avisos: list[str] = []
    por_chave = {chave_natural(it.nome, getattr(it, "marca", None)): it
                 for it in itens}
    for pagina in getattr(layout, "paginas", []) or []:
        for slot in pagina.slots:
            cf = getattr(slot, "conteudo_fixo", None)
            if not (getattr(slot, "fixa", False) and cf
                    and cf.get("preco_da_semana")):
                continue
            it = por_chave.get(
                chave_natural(cf.get("nome"), cf.get("marca")))
            if it is None:
                continue                      # ausente: mantém o que está
            # Q2 (TERTIUSDECIMUS): a oferta do fixo pode ser um DESCONTO
            # declarado ("Lanche na Chapa com 20%") — atualiza como o
            # preço da semana atualiza
            dp = getattr(it, "desconto_pct", None)
            if dp and cf.get("desconto_pct") != dp:
                cf["desconto_pct"] = dp
                avisos.append(f"item fixo “{cf.get('nome')}”: desconto "
                              f"da semana atualizado para {dp}%")
            if not (it.preco or "").strip():
                continue
            if (cf.get("preco") or "").strip() != it.preco.strip():
                cf["preco"] = it.preco.strip()
                avisos.append(f"item fixo “{cf.get('nome')}”: preço da "
                              f"semana atualizado para {cf['preco']}")
    return avisos


def _edicoes_publicadas() -> set[str]:
    """As edições já exportadas (todas as campanhas) — para o aviso do
    pré-voo. Nunca levanta (sem banco = sem aviso, não sem export)."""
    try:
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                mapa = ConfigRepositorio(s).get(
                    "eventos.edicao_publicada") or {}
        finally:
            db.engine.dispose()
        return {str(v).strip() for v in mapa.values() if str(v).strip()}
    except Exception:
        return set()


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


def normalizar_validade_tabela(texto: str | None) -> str | None:
    """Rodada JM (B2A): o rodapé CRU da tabela ("OFERTAS VALIDAS
    03/08/2026 ATÉ 27/08/2026") vira o vocabulário canônico da casa
    ("OFERTA VÁLIDA DE 03/08 ATÉ 27/08") antes de entrar no chip e no
    desenho. Sem data parseável → None (o chamador decide o que fazer
    com o cru)."""
    from app.core.validade import datas_da_validade
    de, ate = datas_da_validade(texto)
    if de is None and ate is None:
        return None
    return montar_validade_oferta(
        de.strftime("%d/%m") if de else None,
        ate.strftime("%d/%m") if ate else None)


def validade_vence(atual: str | None, origem: str | None,
                   da_tabela: str | None) -> bool:
    """Rodada JM (B2A): a validade ESCRITA NA TABELA vence o vazio e o
    palpite da CASCATA do calendário (documento > palpite) — mas NUNCA
    sobrescreve em silêncio a escolha do dono (origem manual/projeto);
    nesse caso o chamador avisa (I2) e o 📅 troca."""
    if not (da_tabela or "").strip():
        return False
    if not (atual or "").strip():
        return True
    return origem == "cascata"


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

# Rodada JM (B3.4) → v2: a lista de EMBALAGENS subiu ao core (o
# rendering desce "tubo"/"caixeta" ao descritor pela MESMA régua)
from app.core.sanitize import EMBALAGENS as _EMBALAGENS  # noqa: E402


def _embalagem_do_nome(tokens: list[str]) -> str | None:
    """O token de embalagem conhecido do nome (minúsculo) — ou None."""
    for tk in tokens:
        if tk.lower() in _EMBALAGENS:
            return tk.lower()
    return None


def _juntar_com_e(nome_a: str, nome_b: str,
                  rotulo_a: str | None = None,
                  rotulo_b: str | None = None) -> str:
    """O miolo histórico do composto: prefixo/sufixo comuns preservados,
    miolos distintos com "e" — agora com rótulo opcional por miolo (a
    embalagem entre parênteses, B3.4)."""
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
    if rotulo_a:
        miolo_a = f"{miolo_a} ({rotulo_a})"
    if rotulo_b:
        miolo_b = f"{miolo_b} ({rotulo_b})"
    partes = ta[:pre] + [f"{miolo_a} e {miolo_b}"] + (ta[len(ta) - suf:]
                                                      if suf else [])
    return " ".join(partes)


def nome_composto(nome_a: str, nome_b: str) -> str:
    """Monta o nome do composto — decisão do dono (03/08): com peso
    COMUM aos dois, o peso sai do nome e vira descritor com "·"
    ("Arroz Somar e Tio Bonini · 5 kg"); embalagens DIFERENTES por
    componente entram entre parênteses ("Milho Verde Fugini (pouch) e
    Bonare (lata) · 170 g"). Sem peso comum, o formato de sempre.
    Sempre editável pelo humano no diálogo."""
    from app.core.sanitize import separar_peso
    na, pa = separar_peso(nome_a)
    nb, pb = separar_peso(nome_b)
    if not (pa and pb and pa == pb):
        return _juntar_com_e(nome_a, nome_b)
    ta, tb = na.split(), nb.split()
    ea, eb = _embalagem_do_nome(ta), _embalagem_do_nome(tb)
    rot_a = rot_b = None
    if ea and eb and ea != eb:
        # a embalagem sai do miolo e vira o rótulo entre parênteses
        ta = [tk for tk in ta if tk.lower() != ea]
        tb = [tk for tk in tb if tk.lower() != eb]
        rot_a, rot_b = ea, eb
    base = _juntar_com_e(" ".join(ta), " ".join(tb), rot_a, rot_b)
    return f"{base} · {pa}"


def eh_composto(it: ItemMesa) -> bool:
    return bool(it.origem_composto)


# --- FAMÍLIAS de sabores (Rodada JM, B4) ---------------------------------------


def nome_de_familia(nomes: list[str]) -> str:
    """A sugestão de nome da família: o PREFIXO comum de tokens dos
    membros ("Sardinha Coqueiro 125g Tomate" + "… Óleo" → "Sardinha
    Coqueiro 125g"). Sem prefixo comum, o primeiro nome serve."""
    listas = [n.split() for n in nomes if (n or "").strip()]
    if not listas:
        return ""
    comum: list[str] = []
    for tokens in zip(*listas):
        if all(t.lower() == tokens[0].lower() for t in tokens):
            comum.append(tokens[0])
        else:
            break
    comum_txt = " ".join(comum).strip(" ·-")
    return comum_txt or " ".join(listas[0])


def criar_familia_de(produto_ids: list[int], nome: str) -> int:
    """Cria (ou reusa) a família e liga os produtos — a porta única de
    nascimento de família (Mesa e Almoxarifado chamam aqui)."""
    from app.core.modo import exigir_escrita
    exigir_escrita()
    from app.core.repositories import FamiliaRepositorio, ProdutoRepositorio
    db = Database().init()
    try:
        with db.Session() as s:
            fid = FamiliaRepositorio(s).obter_ou_criar(nome)
            ProdutoRepositorio(s).definir_familia(list(produto_ids), fid)
            s.commit()
            return fid
    finally:
        db.engine.dispose()


def familia_do_item(produto_id: int | None) -> dict | None:
    """A família do produto, pronta para a UI: {"id","nome","membros"}
    com caminhos de imagem ABSOLUTOS — None sem família/produto."""
    if not produto_id:
        return None
    from app.core.models import Produto
    from app.core.repositories import FamiliaRepositorio
    db = Database().init()
    try:
        with db.Session() as s:
            p = s.get(Produto, produto_id)
            if p is None or not p.familia_id:
                return None
            fam = FamiliaRepositorio(s)
            membros = [{"produto_id": m.id,
                        "nome": m.nome_sanitizado,
                        "imagem": _imagem_absoluta(m.caminho_imagem)}
                       for m in fam.membros(p.familia_id)]
            return {"id": p.familia_id,
                    "nome": fam.nome_de(p.familia_id) or "",
                    "membros": membros}
    finally:
        db.engine.dispose()


def sabor_do_membro(nome_membro: str, nome_familia: str) -> str:
    """SEXTUSDECIMUS/M3: o SABOR de um membro é o nome dele sem o prefixo
    da família ("Sardinha Coqueiro 125g Tomate" → "Tomate"); se a grafia
    não bate, o nome inteiro fica (nunca devolve vazio)."""
    m, f = (nome_membro or "").strip(), (nome_familia or "").strip()
    if f and m.lower().startswith(f.lower()):
        resto = m[len(f):].strip(" ·—-")
        if resto:
            return resto
    return m


def juntar_com_ou(nomes: list[str]) -> str:
    """"Tomate", "Tomate ou Óleo", "Tomate, Óleo ou Limão" — a prosa da
    célula (§2.2 da SEXTUSDECIMUS)."""
    limpos = [n for n in (nomes or []) if n]
    if not limpos:
        return ""
    if len(limpos) == 1:
        return limpos[0]
    return ", ".join(limpos[:-1]) + " ou " + limpos[-1]


def juntar_com_e_texto(nomes: list[str]) -> str:
    """v4: o irmão do juntar_com_ou para MARCAS que somam ("Bulnez e
    Adoralle", "A, B e C") — o conjunto oferece as duas, não uma OU
    outra."""
    limpos = [n for n in (nomes or []) if n]
    if not limpos:
        return ""
    if len(limpos) == 1:
        return limpos[0]
    return ", ".join(limpos[:-1]) + " e " + limpos[-1]


def aplicar_sabores(item: ItemMesa, membros: list[dict]) -> ItemMesa:
    """O CHECK vira o LEQUE: as fotos dos membros escolhidos entram no
    ITEM (congela com o projeto — o imagens_json por-produto do RG-28
    não entra aqui, I3) na ordem por produto_id (identidade, I1).
    M3: os NOMES dos sabores escolhidos viajam também — o descritor da
    célula os anuncia ("Tomate, Óleo ou Limão")."""
    escolhidos = sorted(membros, key=lambda m: m.get("produto_id") or 0)
    # RODADA-125: a régua do CABER — até MAX_FOTOS_CELULA todas entram;
    # acima, a seleção espaçada (o descritor segue falando por TODOS)
    item.imagens = selecionar_fotos_da_celula(
        [m["imagem"] for m in escolhidos if m.get("imagem")])
    base = (item.familia or {}).get("nome") or item.nome or ""
    item.sabores = [sabor_do_membro(m.get("nome") or "", base)
                    for m in escolhidos]
    if item.imagens:
        item.arranjo = "LEQUE"
    return item


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
        marca_propria=a.marca_propria or b.marca_propria,   # F13/COND-5
        via="composto",
        unidade=a.unidade if a.unidade == b.unidade else None,
        origem_composto=[a.to_dict(), b.to_dict()],
    )


def criar_como_composto(item: ItemMesa, nomes_componentes: list[str],
                        mais18: bool,
                        imagens_tratadas: str | list | None,
                        categoria: str | None = None) -> ItemMesa:
    """RG-29: a linha com DUAS marcas ("Coração e Língua") já NASCE composta
    na conciliação — cada componente vira produto PRÓPRIO no banco (nunca um
    nome remendado), e o item da estante é o composto de sempre (F7.2:
    separável, rastreável, 1 slot → 1 uid).

    Rodada JM (B3.3): ``imagens_tratadas`` aceita a LISTA paralela aos
    componentes (foto por componente); a string única dos chamadores
    antigos segue valendo (vai ao 1º — o 2º fica para a curadoria do
    Almoxarifado, avisado no pré-voo como sempre).
    """
    from app.core.modo import exigir_escrita
    exigir_escrita()                 # R-131: PC da loja não edita
    if isinstance(imagens_tratadas, (str, type(None))):
        imagens: list[str | None] = [imagens_tratadas, None]
    else:
        imagens = list(imagens_tratadas) + [None, None]
    subs: list[ItemMesa] = []
    for i, nome in enumerate(nomes_componentes[:2]):
        sub = ItemMesa(descricao=nome, preco=item.preco,
                       semaforo="VERMELHO", nome=nome)
        subs.append(finalizar_criacao(sub, nome, mais18, imagens[i],
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

_NOTAS_FOTO: dict = {}


def _nota_da_foto(caminho):
    """D10 (VC-040): avaliar_foto com cache por (caminho, mtime) — o
    pré-voo roda SÍNCRONO no exportar/salvar; 30 fotos sem cache pagam o
    Laplaciano 30× por gesto. Nunca levanta (None quando nem dá)."""
    try:
        p = Path(caminho)
        chave = (str(p), p.stat().st_mtime_ns)
        av = _NOTAS_FOTO.get(chave)
        if av is None:
            from app.images.avaliador import avaliar_foto
            av = avaliar_foto(p)
            _NOTAS_FOTO[chave] = av
        return av
    except Exception:
        return None


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
                else:
                    # F13/D10 (VC-040): a NOTA da foto entra no pré-voo —
                    # o avaliador só falava no tooltip do Almoxarifado
                    av = _nota_da_foto(c)
                    if av is not None and av.nota == "ruim":
                        avisos.append(
                            f"{rotulo} ({nome}): foto com nota RUIM{idx} — "
                            + "; ".join(av.motivos))
        # RODADA-125 v3 (a Sardinha): a célula que ANUNCIA N sabores e
        # só tem M fotos fala no pré-voo — 3 telas prometiam esse
        # aviso e nenhuma cumpria (promessa falsa fere a I2)
        sabs = tuple(getattr(d, "sabores", ()) or ())
        if sabs and caminhos and len(caminhos) < len(sabs):
            avisos.append(
                f"{rotulo} ({nome}): anuncia {len(sabs)} sabores e só "
                f"{len(caminhos)} têm foto — complete as fotos da "
                "família (botão direito → Sabores da família)")
        if d.preco_por is None and not d.multi_preco \
                and not getattr(d, "desconto_pct", None):
            # R-070: multi-preço TEM preço; Q2: desconto declarado idem
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
                    # F13-DECIMUS/D3: a mensagem que pede ação DIZ ONDE
                    # (a frase antiga fez o dono dizer "não faço a
                    # mínima ideia de como fazer isso")
                    msg = (f"{rot}: papel “Validade da oferta” sem data — "
                           "clique no 📅 na barra da Mesa, ao lado de "
                           "Exportar")
                elif reg.papel_texto == PapelTexto.LIVRE and fixo:
                    # Rodada JM (B2A): o período gravado no molde ("do
                    # dia 1º ao 27") só vira o REAL quando a validade
                    # tem par de datas — sem par, o texto fixo mentiria
                    from app.core.validade import (_RE_PERIODO_FIXO,
                                                   datas_da_validade)
                    if _RE_PERIODO_FIXO.search(fixo):
                        de_, ate_ = datas_da_validade(
                            (d.texto_legal if d else None) or "")
                        if not (de_ and ate_ and de_ != ate_):
                            msg = (f"{rot}: o texto tem período gravado "
                                   "(“do dia … ao …”) e a validade não diz "
                                   "o período — clique no 📅 na barra da "
                                   "Mesa e escolha “De … até …”")
                elif reg.papel_texto == PapelTexto.DICA and not fixo:
                    msg = f"{rot}: papel “Fica a Dica” sem texto — gere a dica pela IA"
                elif reg.papel_texto == PapelTexto.LEGAL and not fixo:
                    msg = f"{rot}: papel “Aviso legal” sem texto — escolha um preset"
                elif reg.papel_texto == PapelTexto.EDICAO:
                    # F13-TER/D1: a edição é REAL — sem dado avisa; igual
                    # a uma JÁ EXPORTADA avisa ("nunca publicar com o
                    # número da edição anterior"). Aviso, nunca veto.
                    from app.rendering.compositor import (
                        _campo_vivo_da_pagina,
                    )
                    ed = (_campo_vivo_da_pagina(dados_por_slot, "edicao")
                          or "").strip()
                    if not ed:
                        msg = (f"{rot}: papel “Edição” sem número — defina "
                               "a edição do jornal (Nº/Ano)")
                    elif ed in _edicoes_publicadas():
                        msg = (f"{rot}: a edição “{ed}” já foi publicada — "
                               "incremente antes de exportar")
                if msg and msg not in vistos:
                    vistos.add(msg)
                    avisos.append(msg)

    # F13/D10 (VC-050): o piso determinístico da REVISORA entra no pré-voo
    # (nome cortado por medida, preço fora da faixa aprendida, de≤por).
    # No cartaz o "de ≤ por" de cima já cobre POR CÉLULA — pula o par.
    from app.ai.revisora import heuristicas_do_pre_voo
    for a in heuristicas_do_pre_voo(layout, dados_por_slot, fontes_dir):
        if cartaz and "risco PROCON" in a:
            continue
        if a not in avisos:
            avisos.append(a)
    return avisos


# --- importar + conciliar -----------------------------------------------------

# QUINTUSDECIMUS/J18: "de X por Y" é o padrão-mãe do varejo — preço de
# PRIMEIRA classe, nunca exceção rejeitada. Y é o preço; X é o riscado.
_RE_DE_POR = re.compile(
    r"\bde\s*(?:R\$\s*)?(\d[\d.,]*)\s*(?:por|->|→)\s*(?:R\$\s*)?"
    r"(\d[\d.,]*)", re.IGNORECASE)


def preco_de_por(texto: str | None) -> tuple[str, str] | None:
    """Reconhece "de X por Y" (com ou sem R$) → ``(de, por)`` — os dois
    validados pelo P0.3. Sem o padrão (ou com número inválido) → None;
    a guarda P0.3b do `preco_decimal` segue intocada."""
    m = _RE_DE_POR.search(texto or "")
    if not m:
        return None
    de, por = m.group(1), m.group(2)
    if preco_decimal(de) is None or preco_decimal(por) is None:
        return None
    return de, por


# §13.5/L4: o preço INLINE da tabela do dono — o número mora na
# DESCRIÇÃO atrás do "<>" e a coluna de valor diz "S. OFERTA"
_RE_PRECO_INLINE = re.compile(r"(?:<>\s*)?R\$\s*(\d+[.,]\d{2})")


def preco_inline_da_descricao(descricao: str | None
                              ) -> tuple[str, str | None]:
    """K2/L4: quando a coluna de valor é TEXTO ("S. OFERTA") e a
    descrição carrega UM número monetário ("… <> R$ 18,81"), esse
    número É o preço — devolve ``(descricao_limpa, preco)``. Dois
    números = ambíguo, não extrai (a lei do P0.3b); zero = nada muda."""
    texto = (descricao or "")
    achados = _RE_PRECO_INLINE.findall(texto)
    if len(achados) != 1:
        return texto, None
    limpo = _RE_PRECO_INLINE.sub(" ", texto)
    limpo = re.sub(r"\s{2,}", " ", limpo).strip(" -–·<>")
    # o código de coluna que apontava o preço ("… 5 Kgs T-1 <> R$ …")
    # sobra colado no FIM — só AQUI ele é sempre código (a limpa geral
    # exige frequência no lote); "VITAMINA B-12" segue intocada, por
    # regra escrita
    limpo = re.sub(r"(?<!VITAMINA )(?<!COMPLEXO )\b[A-Z]{1,2}-\d+$", "",
                   limpo, flags=re.IGNORECASE).strip(" -–·")
    return limpo, achados[0]


def classificar_preco_ocr(texto_preco: str | None
                          ) -> tuple[str | None, str | None, str | None]:
    """Rodada JM (B2B) + J18: a regra nomeada do filtro do import —
    devolve ``(preco, multi_preco, preco_de)`` a partir do campo
    "preco" do OCR. "de X por Y" vira preço Y com o "de" X a bordo;
    preço em TEXTO ("S. OFERTA") vira o canônico "SUPER OFERTA";
    promoção com mecânica (%, leve-X, brinde) segue multi_preco cru
    (R-070); o resto é o preço numérico de sempre."""
    from app.qt.telas.colagem import preco_texto_oferta

    texto = (texto_preco or "").strip()
    dp = preco_de_por(texto)
    if dp:
        return dp[1], None, dp[0]
    canonico = preco_texto_oferta(texto)
    if canonico:
        return None, canonico, None
    if texto and preco_decimal(texto) is None and (
            "%" in texto or any(t in texto.lower() for t in
                                ("leve", "pague", "ganhe",
                                 "desconto", "brinde"))):
        return None, texto, None
    return texto_preco, None, None


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
        # bancada dos Exemplos (semana real): "preço" que é PROMOÇÃO em
        # texto ("20% de desconto", "leve 3 pague 2") não é preço — vira
        # multi_preco (R-070) e a bolha desenha a promoção, como a arte do
        # dono faz ("R$ 20%"); o preço numérico segue o caminho de sempre
        linhas = []
        multi_precos: list[str | None] = []
        precos_de: list[str | None] = []
        for ln in tabela.linhas:
            preco, mp, pde = classificar_preco_ocr(ln.preco)
            desc = ln.descricao
            # L4: carimbo sem número + número inline na descrição →
            # o número é o preço e sai da descrição (junto, nunca no
            # lugar — K2)
            if mp and not preco:
                desc, inline = preco_inline_da_descricao(desc)
                if inline:
                    preco = inline
            linhas.append((desc, preco, None))
            multi_precos.append(mp)
            precos_de.append(pde)
        validade = tabela.validade_oferta
        return conciliar_linhas(linhas, status_cb, validade=validade,
                                aviso=aviso_cache,
                                caminho_fonte=str(caminho),
                                multi_precos=multi_precos,
                                precos_de=precos_de)

    status_cb("Lendo a tabela…")
    from app.scripts.importar_tabela import parse_tabela_ean
    linhas = parse_tabela_ean(caminho)   # RG-41: o EAN da tabela flui
    return conciliar_linhas(linhas, status_cb, validade=validade,
                            aviso=aviso_cache, caminho_fonte=None)


def conciliar_linhas(linhas, status_cb: StatusCb, *, validade=None,
                     aviso=None, caminho_fonte=None,
                     multi_precos=None, descontos=None,
                     precos_de=None) -> ResultadoMesa:
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
            # ADENDO 30/07: 1ª passada concilia TUDO; a exclusividade
            # de lote roda sobre os vereditos (duas linhas nunca casam
            # verdes com o mesmo produto em silêncio); a 2ª monta os
            # itens da Mesa
            from app.ai.conciliacao import (PISO_CANDIDATO_EXIBIDO,
                                            Semaforo,
                                            categoria_dos_candidatos,
                                            exclusividade_de_lote)
            from app.core.mais18 import eh_bebida_alcoolica
            from app.core.sanitize import sanitizar
            vereditos = []
            for i, (desc, preco, ean) in enumerate(linhas, 1):
                status_cb(f"Conciliando {i}/{len(linhas)}…")
                vereditos.append(conc.conciliar(desc))
            exclusividade_de_lote(vereditos)
            houve_categoria = False
            cache_familias: dict[int, dict] = {}     # B4: 1 consulta/família
            for i, ((desc, preco, ean), v) in enumerate(
                    zip(linhas, vereditos), 1):
                p = v.produto
                # F13/D5 (C-01): o acervo se conserta SOZINHO a cada
                # importação — produto casado SEM categoria ganha a do
                # vizinho (humano nunca é vencido: só escreve onde está
                # VAZIO). No PC da loja (somente leitura) pula sem drama.
                # Rodada JM (B1.6): a categoria sai dos candidatos que o
                # veredito JÁ carrega (nada de refazer fuzzy+embedding);
                # o match EXATO vem com um candidato só (ele mesmo) — só
                # nele a busca de vizinhos roda de verdade. Um commit
                # por LOTE, não por item.
                if p is not None and p.categoria is None:
                    cat, _sc = categoria_dos_candidatos(
                        v.candidatos, conc.limiares.amarelo)
                    if not cat and v.via == "exato":
                        cat, _sc = conc.categoria_do_vizinho(desc)
                    if cat:
                        try:
                            from app.core.repositories import (
                                ProdutoRepositorio,
                            )
                            ProdutoRepositorio(session).editar(
                                p.id, categoria=cat,
                                categoria_origem="vizinho")
                            houve_categoria = True
                        except Exception:
                            session.rollback()
                mp = (multi_precos[i - 1] if multi_precos
                      and i - 1 < len(multi_precos) else None)
                dp = (descontos[i - 1] if descontos
                      and i - 1 < len(descontos) else None)
                pde = (precos_de[i - 1] if precos_de
                       and i - 1 < len(precos_de) else None)
                # B1.5/B3: o VERMELHO nasce sanitizado e com as
                # pendências a bordo. QUINTUSDECIMUS/J9: o sanitize roda
                # para TODOS — linha que parece 2 produtos ("multiplos")
                # casada VERDE desce a AMARELO com o motivo dito (duas
                # marcas nunca viram uma em silêncio); o match
                # EXATO/alias fica: é aprendizado confirmado pelo dono.
                san = sanitizar(desc, conc.regras)
                # RODADA-125 Onda 3 (o print do dono): a linha MULTI
                # tenta primeiro o CONJUNTO do acervo — se todos os
                # membros declarados JÁ existem, o item nasce VERDE
                # montado (leque das fotos dele, sabores no descritor)
                # e ninguém refaz nada. Parcial não inventa: segue o
                # fluxo normal.
                if any(pd.codigo == "multiplos"
                       for pd in san.pendencias) or " e " in desc.lower():
                    conjunto = conjunto_do_acervo(desc)
                    if conjunto is not None:
                        itens.append(item_do_conjunto(
                            desc, preco, ean or None, conjunto,
                            mp=mp, dp=dp))
                        continue
                if (v.semaforo == Semaforo.VERDE and v.via != "exato"
                        and any(pd.codigo == "multiplos"
                                for pd in san.pendencias)):
                    v.semaforo = Semaforo.AMARELO
                    v.motivo = ("a linha parece ter 2 produtos no mesmo "
                                "preço — confira antes de aceitar "
                                "(o Criar abre a pergunta)")
                # J18: preço ILEGÍVEL nunca sai verde calado — a recusa
                # do P0.3b vira pendência dita (era um `—` silencioso
                # nos dois destaques da página do dono)
                pendencias = [pd.codigo for pd in san.pendencias]
                if ((preco or "").strip() and mp is None and dp is None
                        and preco_decimal(preco) is None):
                    pendencias.append("preco_ilegivel")
                    if v.semaforo == Semaforo.VERDE:
                        v.semaforo = Semaforo.AMARELO
                    v.motivo = (f"o preço «{preco}» não foi entendido — "
                                "corrija na coluna Preço"
                                + (f" · {v.motivo}" if v.motivo else ""))
                itens.append(ItemMesa(
                    descricao=desc,
                    preco=preco,
                    multi_preco=mp,                          # R-070 (colagem)
                    desconto_pct=dp,                         # Q2 (declarado)
                    ean=ean or (p.ean if p else None),
                    semaforo=v.semaforo.value,
                    # Rodada JM (B1.5): o item NOVO nasce com o nome
                    # SANITIZADO (acentos/unidades/caixa) — a descrição
                    # CRUA fica em `descricao` (alias/identidade, I1)
                    nome=p.nome_sanitizado if p else san.nome_sanitizado,
                    pendencias=pendencias,
                    motivo=v.motivo,
                    produto_id=p.id if p else None,
                    imagem=_imagem_absoluta(p.caminho_imagem) if p else None,
                    # L12 (A RÉGUA SOMA — §13.2/L1): o dado do banco
                    # SOMA com a heurística, nunca a substitui. O item
                    # novo (27 de 42 no Jornal) ganhava mais18=False
                    # cravado e a Amstel ia à página SEM selo; e o
                    # cadastro velho (selo_mais18=0 de antes da régua)
                    # também envelhecia. `or`, nunca if/else.
                    mais18=((bool(p.selo_mais18) if p else False)
                            or eh_bebida_alcoolica(
                                p.nome_sanitizado if p
                                else san.nome_sanitizado)),
                    marca_propria=bool(p.marca_propria) if p else False,
                    via=v.via,
                    score=v.confianca,
                    candidato_nome=(v.candidatos[0].produto.nome_sanitizado
                                    if v.candidatos else ""),
                    # J11: a VITRINE só mostra candidato plausível — o
                    # motor segue com os top-5 por dentro
                    candidatos=[{"produto_id": c.produto.id,
                                 "nome": c.produto.nome_sanitizado,
                                 "score": round(float(c.score), 1)}
                                for c in (v.candidatos or [])
                                if c.score >= PISO_CANDIDATO_EXIBIDO],
                    # J18: o "de" DA TABELA vence o preço vigente do
                    # banco (o documento manda; o banco é o fallback)
                    preco_de=(pde or (_preco_texto(p.preco_atual)
                                      if p else None)),
                    preco_de_da_tabela=bool(pde),
                    unidade=(f"{_qtd_texto(p.peso_valor)}{p.peso_unidade}"
                             if p and p.peso_valor is not None and p.peso_unidade
                             else None),
                    categoria=(p.categoria.nome
                               if p and p.categoria else None),   # F8
                    imagens=imagens_do_produto(p) if p else [],   # RG-28
                    # B4: a família viaja com o item casado (cache por
                    # lote — irmãos da mesma família = 1 consulta)
                    familia=(_familia_em_lote(
                        session, p.familia_id, cache_familias)
                        if p is not None
                        and getattr(p, "familia_id", None) else None),
                ))
                # RODADA-125 v2 (achado 11): a linha MULTI casada com
                # UM produto de FAMÍLIA nunca mais sai muda ("Amaciante
                # / 5 L" sem fragrância nenhuma) — o leque e os sabores
                # dos membros entram na hora; a escolha fina segue do
                # dono (a linha multi casada já desce a amarelo, J9)
                it_v2 = itens[-1]
                if (it_v2.familia
                        and "multiplos" in (it_v2.pendencias or [])
                        and not it_v2.sabores):
                    aplicar_sabores(it_v2, it_v2.familia["membros"])
                    # a célula fala pela FAMÍLIA — o nome vira o base
                    # (o sabor específico do produto casado sairia
                    # como se fosse o único da oferta)
                    it_v2.nome = (it_v2.familia.get("nome")
                                  or it_v2.nome)
            if houve_categoria:
                try:
                    session.commit()          # 1 commit por lote (B1.6)
                except Exception:
                    session.rollback()
        # I2 (frota F12): a degradação do conciliador (embeddings mortos)
        # sobe até a tela — antes ficava engolida e o dono acreditava que
        # a camada de significado tinha trabalhado
        for a in conc.avisos:
            aviso = f"{aviso} · {a}" if aviso else a
    finally:
        db.engine.dispose()
    return ResultadoMesa(itens=itens, validade_oferta=validade, aviso=aviso,
                         caminho_fonte=caminho_fonte)


def _familia_em_lote(session, familia_id: int, cache: dict) -> dict | None:
    """B4: o dict da família DENTRO da sessão do lote (o cache evita a
    consulta repetida quando vários irmãos aparecem na mesma tabela)."""
    if familia_id in cache:
        return cache[familia_id]
    from app.core.repositories import FamiliaRepositorio
    fam = FamiliaRepositorio(session)
    dado = {"id": familia_id,
            "nome": fam.nome_de(familia_id) or "",
            "membros": [{"produto_id": m.id,
                         "nome": m.nome_sanitizado,
                         "imagem": _imagem_absoluta(m.caminho_imagem)}
                        for m in fam.membros(familia_id)]}
    cache[familia_id] = dado
    return dado


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
        descontos_de, linhas_para_tuplas, multi_precos_de, parse_colagem,
        precos_de_de)
    linhas = parse_colagem(texto)
    return conciliar_linhas(linhas_para_tuplas(linhas), status_cb,
                            multi_precos=multi_precos_de(linhas),
                            descontos=descontos_de(linhas),
                            precos_de=precos_de_de(linhas))


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


def _compor_cartaz(layout, dados, *, rascunho: bool = False, qr_texto=None):
    """Compõe 1 página de cartaz a partir de um DadosProduto (QR opcional).

    F13/D8 (a trava #1, decisão do dono 24/07): sai LIMPO por padrão —
    a marca d'água RASCUNHO virou opção EXPLÍCITA (``rascunho=True``)."""
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
                     rascunho: bool = False,
                     status_cb: StatusCb = lambda _m: None):
    """R-110: do produto ao PDF do cartaz num passo — sem montar nada na Mesa.

    Usa o layout padrão de cartaz + os dados do produto (de/por, foto oficial).
    Roda o pré-voo cartaz=True (sem foto/preço/“de” avisa ANTES do PDF, I2).

    F13/D8 (a trava #1 derrubada pelo dono, 24/07 — manda sobre a decisão
    da F11): o relâmpago sai LIMPO por padrão; a marca RASCUNHO virou
    opção explícita. O pré-voo continua avisando ANTES do PDF (I2).
    Devolve (Path, avisos)."""
    from app.rendering.cartaz import layout_cartaz_exemplo
    from app.rendering.export import exportar_pdf_multipagina

    layout = layout or layout_cartaz_exemplo()
    dados = dados_cartaz_de_produto(produto, validade_texto=validade_texto)
    slot_id = layout.paginas[0].slots[0].id
    status_cb("Conferindo o cartaz…")
    avisos = validar_composicao(layout, {slot_id: dados}, cartaz=True)
    status_cb("Compondo o cartaz…")
    img, extra = _compor_cartaz(layout, dados, rascunho=rascunho,
                                qr_texto=qr_texto)
    avisos.extend(extra)
    status_cb("Gravando o PDF…")
    caminho = exportar_pdf_multipagina([img], destino, layout.dpi)
    return caminho, avisos


def gerar_etiquetas_lote(itens: list[ItemMesa], destino,
                         status_cb: StatusCb = lambda _m: None,
                         *, dpi_folha: int | None = None,
                         rascunho: bool = False):
    """R-144 (FASE 12): dezenas de etiquetas por FOLHA — uma etiqueta por
    item selecionado (a mesma fonte de verdade do cartaz), impostas em A4
    com marcas de corte (imposição CONTROLADA, só no fluxo do cartaz).
    Devolve (caminho_pdf, avisos) — item sem preço entendido é AVISADO e a
    etiqueta sai mesmo assim (I2: aviso, nunca silêncio nem bloqueio).

    F13/D8 (a trava #1, decisão do dono 24/07 — manda sobre a lei da
    frota F12): sai LIMPA por padrão; ``rascunho=True`` é a opção
    EXPLÍCITA que carimba. As 9 portas seguem o MESMO padrão."""
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
        # F13/B6 (F-01): a receita ÚNICA — o dict local daqui não passava
        # mais18 e a etiqueta de bebida saía SEM o selo +18, calada
        d = dados_cartaz_de_item(it)
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
                      rascunho: bool = False,
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
    cartaz_img, extra = _compor_cartaz(lay_cartaz, dados, rascunho=rascunho,
                                       qr_texto=qr_texto)
    avisos.extend(extra)
    paginas = [cartaz_img]
    for k in range(max(1, n_etiquetas)):
        status_cb(f"Compondo etiqueta {k + 1}/{max(1, n_etiquetas)}…")
        etiq_img, _ = _compor_cartaz(lay_etiq, dados, rascunho=rascunho)
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

def aceitar_correspondencia(item: ItemMesa,
                            produto_id: int | None = None) -> ItemMesa:
    """Confirma o palpite do banco para o item 🟡 e APRENDE o alias.

    ADENDO 30/07: ``produto_id`` explícito é o VÍNCULO FORÇADO — o dono
    escolheu o produto (no menu de candidatos ou na busca do acervo) e
    a escolha humana é a confirmação por excelência (F9): vira alias e
    a próxima importação casa sozinha, VERDE exato."""
    from app.core.repositories import ProdutoRepositorio

    if produto_id is not None:
        item.produto_id = produto_id
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


def criar_produto_manual(nome: str, preco: str | None = None) -> tuple[int, str]:
    """ADENDO 30/07 (a queixa 1 do dono): cadastrar um item AVULSO no
    Almoxarifado, sem passar por importação. Reusa a porta única de
    nascimento (``ProdutoRepositorio.importar``: sanitiza, casa por
    nome/alias — não duplica se já existe — e aprende o alias).
    Devolve (produto_id, nome_sanitizado)."""
    from app.core.modo import exigir_escrita
    from app.core.repositories import ProdutoRepositorio

    exigir_escrita()
    db = Database().init()
    try:
        with db.Session() as session:
            r = ProdutoRepositorio(session).importar(nome.strip(),
                                                     preco=preco)
            session.commit()
            return r.produto.id, r.produto.nome_sanitizado
    finally:
        db.engine.dispose()


def buscar_produtos_para_vinculo(texto: str, limite: int = 30) -> list[dict]:
    """ADENDO 30/07: a busca do gesto "é ESTE aqui" — produtos do acervo
    para o dono escolher o vínculo na conciliação. Dados planos p/ a UI."""
    from app.core.repositories import ProdutoRepositorio

    db = Database().init()
    try:
        with db.Session() as session:
            repo = ProdutoRepositorio(session)
            achados = (repo.buscar(texto, limit=limite) if texto.strip()
                       else repo.listar(limit=limite))
            return [{"produto_id": p.id,
                     "nome": p.nome_sanitizado,
                     "imagem": _imagem_absoluta(p.caminho_imagem),
                     "preco": _preco_texto(p.preco_atual)}
                    for p in achados]
    finally:
        db.engine.dispose()


def reconciliar_item(item: ItemMesa) -> ItemMesa:
    """ADENDO 30/07: o dono corrigiu o texto do OCR na linha — a linha
    RE-CONCILIA na hora (muitos vermelhos viram verdes só com o nome
    certo; antes a correção não recalculava nada e nascia duplicata).
    Preserva a identidade (uid) e o que é da OFERTA, não do matching."""
    resultado = conciliar_linhas([(item.descricao, item.preco, item.ean)],
                                 lambda *_a, **_k: None)
    if not resultado.itens:
        return item
    novo = resultado.itens[0]
    novo.uid = item.uid                     # I1: a identidade fica
    novo.multi_preco = item.multi_preco
    novo.desconto_pct = item.desconto_pct
    novo.observacao = item.observacao
    novo.selos = item.selos
    return novo


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
    # Rodada JM (B3): a linha PARECE 2 produtos (a pendência "multiplos"
    # do sanitize dividiu limpo) — a curadoria PERGUNTA "são 2
    # produtos?" com a sugestão nos campos; quem decide é o humano.
    possivel_composto: bool = False
    sugestao_componentes: list[str] = field(default_factory=list)
    # True quando os componentes vieram do LM (a curadoria pré-marca o
    # check — e DESMARCAR cancela o composto: a IA nunca decide sozinha)
    componentes_da_ia: bool = False


def _cabeca_pre_medida(texto: str) -> str:
    """RODADA-125 v2 (o Biscoito do dono): a linha se corta na ÚLTIMA
    medida — o que vem antes é a CABEÇA (tipo+marcas+peso), o que vem
    depois é rabo de sabores. As réguas de composto olham SÓ a cabeça:
    a barra do rabo ("C. CRACKER/LEITE/AGUA E SAL") não pode vetar o
    " e " das marcas da frente."""
    from app.core.sanitize import REGRAS_PADRAO, _regex_unidades
    ultimo = None
    for m in _regex_unidades(REGRAS_PADRAO).finditer(texto):
        ultimo = m
    return texto[:ultimo.end()].strip() if ultimo else texto


def dividir_em_dois(descricao: str | None) -> list[str]:
    """Rodada JM (B3.1): a SUGESTÃO determinística para a linha com
    duas marcas num preço — corta no primeiro " e ", replica o peso
    comum do fim e o TIPO (1º token) no 2º componente, e sanitiza os
    dois. É sugestão: quem decide é o humano na curadoria.

    BARRA na CABEÇA = sabores/variantes (caso de FAMÍLIA), nunca
    composto de marcas → lista vazia. Sem " e " idem. v2 (o Biscoito):
    o veto e a busca do " e " valem na CABEÇA pré-medida — o rabo de
    sabores não cala mais as marcas da frente."""
    import re as _re

    from app.core.sanitize import sanitizar, separar_peso
    texto = _cabeca_pre_medida((descricao or "").strip())
    if not texto or "/" in texto:
        return []
    m = _re.search(r"\s+e\s+", texto, flags=_re.IGNORECASE)
    if not m:
        return []
    esq, dir_ = texto[:m.start()].strip(), texto[m.end():].strip()
    esq_nome, esq_peso = separar_peso(esq)
    dir_nome, dir_peso = separar_peso(dir_)
    peso = dir_peso or esq_peso        # o peso do fim da LINHA é comum
    if not esq_nome.strip() or not dir_nome.strip():
        return []
    tipo = esq_nome.split()[0]
    tokens_dir = {t.lower() for t in dir_nome.split()}
    if len(tipo) >= 3 and tipo.lower() not in tokens_dir:
        dir_nome = f"{tipo} {dir_nome}"
    sufixo = f" {peso}" if peso else ""
    comp_a = sanitizar(f"{esq_nome}{sufixo}").nome_sanitizado
    comp_b = sanitizar(f"{dir_nome}{sufixo}").nome_sanitizado
    if not comp_a or not comp_b:
        return []
    return [comp_a, comp_b]


# RODADA-125 v2 (o Biscoito): sabores CONSAGRADOS que carregam " e "
# dentro — o par nunca se parte no split ("AGUA E SAL" é UM sabor, não
# dois). O mesmo critério conservador do _PARES_DO_MERCADO/ortografia:
# só entra o inequívoco; comparação sem acento/caixa.
_SABORES_COMPOSTOS = frozenset({
    "agua e sal", "doce de leite", "milho e ervilha",
    "coco e leite", "leite e mel",
})


def _sem_acento(t: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKD", (t or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c)).strip()


def familia_da_linha(descricao: str | None) -> tuple[str, list[str]]:
    """QUINTUSDECIMUS/J13: o detector de SABORES da linha — o que vem
    DEPOIS da medida é sabor ("SARDINHA COQUEIRO 125 g TOMATE / OLEO e
    LIMÃO" → base "Sardinha Coqueiro 125g", sabores ["Tomate", "Óleo",
    "Limão"]); o que vem ANTES é marca (o "ARROZ SOMAR e TIO BONINI
    5 Kgs" devolve zero sabores — é caso de 2 PRODUTOS, não família).
    Determinístico; a decisão final é a 3ª pergunta na curadoria.

    v2 (o Biscoito): o split é em DOIS TEMPOS — primeiro só a barra;
    dentro de cada segmento o " e " só quebra se o segmento não for
    sabor consagrado ("C. CRACKER/LEITE/AGUA E SAL" dá 3 sabores, não
    4; "TOMATE/OLEO e LIMÃO" segue dando 3 porque "oleo e limão" não
    está no vocabulário)."""
    from app.core.sanitize import REGRAS_PADRAO, _regex_unidades, sanitizar
    texto = (descricao or "").strip()
    if not texto:
        return "", []
    ultimo = None
    for m in _regex_unidades(REGRAS_PADRAO).finditer(texto):
        ultimo = m
    if ultimo is None:
        return sanitizar(texto).nome_sanitizado, []
    base = sanitizar(texto[:ultimo.end()]).nome_sanitizado
    rabo = texto[ultimo.end():]
    segmentos: list[str] = []
    for seg in re.split(r"\s*/\s*", rabo):
        seg = seg.strip()
        if not seg:
            continue
        if _sem_acento(seg.strip(" .,-–")) in _SABORES_COMPOSTOS:
            segmentos.append(seg)
        else:
            segmentos.extend(re.split(r"\s+e\s+", seg,
                                      flags=re.IGNORECASE))
    sabores: list[str] = []
    for p in segmentos:
        p = p.strip(" .,-–")
        if p and any(c.isalpha() for c in p):
            nome = sanitizar(p).nome_sanitizado
            if nome:
                sabores.append(nome)
    return base, (sabores if len(sabores) >= 2 else [])


def marcas_e_sabores_da_linha(descricao: str | None,
                              ) -> tuple[str, list[str], list[str]]:
    """RODADA-125 v2 (o Biscoito completo): a linha "BISCOITO BULNEZ e
    ADORALLE 270 g C. CRACKER/LEITE/AGUA E SAL" declara um CARTESIANO —
    marcas na CABEÇA, sabores no rabo. Devolve ``(base_sem_marcas,
    marcas, sabores)``; as marcas saem do vocabulário conhecido (F9:
    nunca se inventa) e a base limpa alimenta os rótulos marca-major
    ("Biscoito Bulnez Cream Cracker 270g"). Sem 2 marcas conhecidas na
    cabeça, devolve a base de sempre e marcas=[]."""
    from app.core.marcas import marcas_no_nome
    from app.core.sanitize import sanitizar
    base, sabores = familia_da_linha(descricao)
    cabeca = _cabeca_pre_medida((descricao or "").strip())
    marcas = marcas_no_nome(cabeca, marcas_para_exibicao()) \
        if cabeca else []
    if len(marcas) < 2:
        return base, [], sabores
    limpa = cabeca
    for mc in marcas:
        limpa = re.sub(rf"\s*\be\b\s+{re.escape(mc)}\b", " ", limpa,
                       flags=re.IGNORECASE)
        limpa = re.sub(rf"\b{re.escape(mc)}\b", " ", limpa,
                       flags=re.IGNORECASE)
    limpa = re.sub(r"\s{2,}", " ", limpa).strip(" e·-,")
    base_limpa = sanitizar(limpa).nome_sanitizado or base
    return base_limpa, [sanitizar(m).nome_sanitizado or m
                        for m in marcas], sabores


def membro_do_acervo(nome: str) -> dict | None:
    """RODADA-125 Onda 2 (a pergunta do dono: "como ele não correlaciona
    o que já existe?"): procura o produto que este NOME JÁ É no acervo —
    nome bruto exato → alias aprendido → CHAVE NATURAL do sanitizado (a
    régua conservadora do caça-duplicatas: marca diferente nunca casa).
    Devolve {"id","nome","tem_foto"} ou None."""
    from app.core.models import Produto
    from app.core.portabilidade import chave_natural
    from app.core.repositories import ProdutoRepositorio
    from app.core.sanitize import sanitizar

    db = Database().init()
    try:
        with db.Session() as s:
            repo = ProdutoRepositorio(s)
            p = (repo.buscar_por_nome_bruto(nome)
                 or repo.buscar_por_alias(nome))
            if p is None:
                import re as _re
                alvo = chave_natural(
                    sanitizar(nome).nome_sanitizado, "")
                # a grafia da unidade não separa ("5kg" × "5 kg"):
                # a comparação de reserva ignora TODO espaço
                alvo_denso = _re.sub(r"\s+", "", alvo[0])
                # v2 (o cartesiano do Biscoito): a ORDEM dos tokens
                # também não separa — "Biscoito 270g Bulnez Cream
                # Cracker" e "Biscoito Bulnez Cream Cracker 270g" são
                # o MESMO produto (mesmo multiconjunto de palavras);
                # a 3ª reserva compara os tokens ordenados
                alvo_ord = "".join(sorted(alvo[0].split()))
                for cand in s.query(Produto).filter(
                        Produto.excluido_em.is_(None)):
                    ch = chave_natural(cand.nome_sanitizado or "", "")
                    if (ch == alvo
                            or _re.sub(r"\s+", "", ch[0]) == alvo_denso
                            or "".join(sorted(ch[0].split())) == alvo_ord):
                        p = cand
                        break
            if p is None or p.excluido_em is not None:
                return None
            return {"id": p.id, "nome": p.nome_sanitizado,
                    "tem_foto": bool(p.caminho_imagem),
                    "imagem": _imagem_absoluta(p.caminho_imagem)}
    finally:
        db.engine.dispose()


def rotulos_marcas_x_sabores(marcas: list[str],
                             sabores: list[str]) -> list[str]:
    """RODADA-125 Onda 2 (a decisão do dono, 03/08): a linha "Bulnez e
    Adoralle · Cream Cracker/Leite/Maisena" declara o CARTESIANO — um
    produto por (marca × sabor), marca-major ("Bulnez Cream Cracker",
    "Bulnez Leite", …, "Adoralle Maisena")."""
    if not marcas:
        return list(sabores)
    if not sabores:
        return list(marcas)
    return [f"{m} {s}".strip() for m in marcas for s in sabores]


# a régua do CABER (decisão do dono): até 4 fotos a célula mostra
# todas; acima disso a seleção espaçada pega as pontas (marcas
# diferentes, na geração marca-major) e o DESCRITOR fala por todos
MAX_FOTOS_CELULA = 4


def selecionar_fotos_da_celula(imagens: list, max_n: int = MAX_FOTOS_CELULA
                               ) -> list:
    """"Isso se couber; se não, dê um jeito de selecionar adequadamente"
    — espaçamento uniforme sobre a lista (pega a 1ª, a última e o meio:
    com cartesiano marca-major, marcas diferentes entram)."""
    if len(imagens) <= max_n:
        return list(imagens)
    idx = [round(i * (len(imagens) - 1) / (max_n - 1))
           for i in range(max_n)]
    vistos: list = []
    for k in idx:
        if imagens[k] not in vistos:
            vistos.append(imagens[k])
    return vistos


def conjunto_do_acervo(descricao: str) -> dict | None:
    """RODADA-125 Onda 3 (o print do dono, 03/08): a conciliação pensava
    por PRODUTO ÚNICO — "MON BIJOU PROTEÇÃO e CLASSICO" casava com UM
    sabor e o dono refazia tudo. O conceito que faltava: a linha MULTI
    casa com um CONJUNTO do acervo. Se TODOS os membros que a linha
    declara já existem (nome → alias → chave natural), devolve
    ``{"tipo": "familia"|"composto", "base", "rotulos", "membros"}`` —
    e o item nasce VERDE montado (leque das fotos existentes, sabores
    no descritor), sem curadoria nenhuma. PARCIAL NÃO INVENTA: com
    qualquer membro faltando devolve None e o fluxo normal decide
    (nada nasce verde calado). v2 (o Biscoito): marcas×sabores no
    mesmo conjunto agora casam — os rótulos marca-major do
    ``rotulos_marcas_x_sabores`` procuram os 6 no acervo."""
    from app.core.sanitize import separar_peso
    base, sabores = familia_da_linha(descricao)
    comps = dividir_em_dois(descricao)
    base_mx, marcas_mx, sabores_mx = marcas_e_sabores_da_linha(descricao)
    # SABORES vencem quando os dois detectores disparam: o pós-medida é
    # o sinal mais específico ("MON BIJOU 5L PROTEÇÃO e CLASSICO" também
    # divide em 2, mas a divisão perde a marca do 2º)
    if len(marcas_mx) >= 2 and len(sabores_mx) >= 2:
        bn, bp = separar_peso(base_mx)
        sufixo = f" {bp}" if bp else ""
        nomes = [f"{bn} {m} {s}{sufixo}".strip()
                 for m in marcas_mx for s in sabores_mx]
        # v4 (a lei do dono: o Biscoito DIZ as marcas): a base do item
        # carrega as marcas ("Biscoito Bulnez e Adoralle 270g") — a
        # hierarquia canônica as desce ao descritor; e os SABORES
        # exibidos são os FATORADOS (Cream Cracker, Leite ou Água e
        # Sal), nunca os N×M rótulos do cartesiano por extenso
        base = f"{bn} {juntar_com_e_texto(marcas_mx)}{sufixo}".strip()
        tipo = "familia"
        rotulos = list(sabores_mx)
    elif len(sabores) >= 2:
        nomes = [f"{base} {s}".strip() for s in sabores]
        tipo, rotulos = "familia", list(sabores)
    elif len(comps) >= 2:
        nomes = list(comps)
        tipo, rotulos = "composto", list(comps)
    else:
        return None
    membros = []
    for n in nomes:
        m = membro_do_acervo(n)
        if m is None:
            return None                # parcial não inventa
        membros.append(m)
    return {"tipo": tipo, "base": base or descricao,
            "rotulos": rotulos, "membros": membros}


def _motivo_fotos_do_conjunto(membros: list[dict]) -> str | None:
    """RODADA-125 v3 (a Sardinha da 3ª prova): o conjunto casou os 3
    sabores mas 2 não tinham foto — a célula mostrou UMA lata e o dono
    achou que os sabores foram ignorados. O item nasce dizendo o que
    falta (I2), com o caminho para completar."""
    sem = [m["nome"] for m in membros if not m.get("imagem")]
    if not sem:
        return None
    return (f"família casada, mas {len(sem)} de {len(membros)} sabores "
            f"SEM FOTO ({', '.join(sem[:3])}"
            + ("…" if len(sem) > 3 else "")
            + ") — complete pelo Almoxarifado ou botão direito → "
            "Sabores da família")


def item_do_conjunto(desc: str, preco, ean, conjunto: dict,
                     mp=None, dp=None) -> ItemMesa:
    """Monta o ItemMesa VERDE do conjunto reconhecido — a linha vira
    UMA célula (I6) com as fotos que o acervo JÁ tem."""
    membros = conjunto["membros"]
    fotos = selecionar_fotos_da_celula(
        [m["imagem"] for m in membros if m.get("imagem")])
    n = len(membros)
    if conjunto["tipo"] == "composto":
        a = ItemMesa(descricao=membros[0]["nome"], preco=preco,
                     semaforo="VERDE", nome=membros[0]["nome"],
                     produto_id=membros[0]["id"],
                     imagem=membros[0].get("imagem"))
        b = ItemMesa(descricao=membros[1]["nome"], preco=preco,
                     semaforo="VERDE", nome=membros[1]["nome"],
                     produto_id=membros[1]["id"],
                     imagem=membros[1].get("imagem"))
        comp = compor_itens(a, b, preco=preco)
        comp.descricao = desc
        comp.ean = ean
        comp.multi_preco = mp
        comp.desconto_pct = dp
        comp.via = "conjunto"
        comp.motivo = (f"linha casada com os {n} produtos que você já "
                       "criou — nada foi recriado")
        return comp
    item = ItemMesa(
        descricao=desc, preco=preco, semaforo="VERDE",
        nome=conjunto["base"], produto_id=membros[0]["id"],
        ean=ean, multi_preco=mp, desconto_pct=dp,
        imagem=next((m["imagem"] for m in membros
                     if m.get("imagem")), None),
        imagens=fotos, arranjo="LEQUE" if fotos else None,
        sabores=list(conjunto["rotulos"]), via="conjunto",
        # v3: sabor sem foto vira PENDÊNCIA dita (a Sardinha parecia
        # "ignorada" porque 2 de 3 latas nem existiam no acervo)
        pendencias=(["sabor_sem_foto"]
                    if _motivo_fotos_do_conjunto(membros) else []),
        motivo=(_motivo_fotos_do_conjunto(membros)
                or (f"linha casada com a família já criada "
                    f"({n} sabores) — nada foi recriado")))
    item.familia = familia_do_item(membros[0]["id"])
    item.mais18 = item.mais18 or eh_bebida_alcoolica_nome(
        conjunto["base"])
    return item


def eh_bebida_alcoolica_nome(nome: str) -> bool:
    from app.core.mais18 import eh_bebida_alcoolica
    return eh_bebida_alcoolica(nome)


def montar_conjunto_manual(item: ItemMesa, produto_ids: list[int],
                           tipo: str, nome_base: str) -> ItemMesa:
    """RODADA-125 Onda 3b (o pedido do dono: "preciso ter liberdade pra
    CAÇAR esses dois itens já existentes e colocar ali"): a CESTA — o
    dono escolhe N produtos do acervo à mão e a linha vira a célula
    montada, com as fotos DELES. ``tipo``: "sabores" (leque, nome-base
    + sabores no descritor) ou "diferentes" (2 → o composto separável
    de sempre; 3+ → vitrine com o nome que o dono deu). O item da
    estante nasce VERDE via "conjunto" — nada é recriado."""
    from app.core.models import Produto

    membros: list[dict] = []
    db = Database().init()
    try:
        with db.Session() as s:
            for pid in produto_ids:
                p = s.get(Produto, pid)
                if p is None or p.excluido_em is not None:
                    continue
                membros.append({
                    "id": p.id, "nome": p.nome_sanitizado,
                    "tem_foto": bool(p.caminho_imagem),
                    "imagem": _imagem_absoluta(p.caminho_imagem),
                    "mais18": bool(p.selo_mais18 or p.bebida_alcoolica),
                })
    finally:
        db.engine.dispose()
    if len(membros) < 2:
        raise ValueError("a cesta precisa de pelo menos 2 produtos")

    if tipo == "diferentes" and len(membros) == 2:
        a = ItemMesa(descricao=membros[0]["nome"], preco=item.preco,
                     semaforo="VERDE", nome=membros[0]["nome"],
                     produto_id=membros[0]["id"],
                     imagem=membros[0].get("imagem"),
                     mais18=membros[0]["mais18"])
        b = ItemMesa(descricao=membros[1]["nome"], preco=item.preco,
                     semaforo="VERDE", nome=membros[1]["nome"],
                     produto_id=membros[1]["id"],
                     imagem=membros[1].get("imagem"),
                     mais18=membros[1]["mais18"])
        comp = compor_itens(a, b, nome=nome_base or None,
                            preco=item.preco)
        comp.descricao = item.descricao
        comp.ean = item.ean
        comp.multi_preco = item.multi_preco
        comp.via = "conjunto"
        comp.motivo = "montado do acervo pela cesta — nada recriado"
        return comp

    fotos = selecionar_fotos_da_celula(
        [m["imagem"] for m in membros if m.get("imagem")])
    novo = ItemMesa(
        descricao=item.descricao, preco=item.preco, semaforo="VERDE",
        nome=nome_base or membros[0]["nome"],
        produto_id=membros[0]["id"], ean=item.ean,
        multi_preco=item.multi_preco,
        imagem=next((m["imagem"] for m in membros
                     if m.get("imagem")), None),
        imagens=fotos,
        arranjo=("LEQUE" if tipo == "sabores" else "LADO_A_LADO"),
        sabores=([sabor_do_membro(m["nome"], nome_base)
                  for m in membros] if tipo == "sabores" else []),
        via="conjunto",
        motivo=(f"montado do acervo pela cesta ({len(membros)} "
                "produtos) — nada recriado"),
        uid=item.uid)                    # I1: a identidade da linha fica
    novo.mais18 = (any(m["mais18"] for m in membros)
                   or eh_bebida_alcoolica_nome(nome_base or ""))
    novo.familia = familia_do_item(membros[0]["id"])
    return novo


def criar_familia_de_sabores(item: ItemMesa, nome_familia: str,
                             sabores: list[str], mais18: bool,
                             imagem_tratada: str | list | None,
                             categoria: str | None = None) -> ItemMesa:
    """J13 + SEXTUSDECIMUS/M1: a resposta "são SABORES do mesmo produto"
    — cria um produto COMPLETO por sabor ("Sardinha Coqueiro 125g
    Tomate"…), liga todos à FAMÍLIA (B4) e o item da estante vira o
    leque. ``imagem_tratada`` é a LISTA paralela aos sabores (a tela de
    um espaço por sabor) — CADA sabor grava a sua foto; ``str`` de
    compatibilidade vai ao 1º (o mesmo padrão do composto). Sabor sem
    foto avisa (I2), nunca some — L14: ou fecha o N, ou não oferece."""
    from app.core.modo import exigir_escrita
    exigir_escrita()
    if isinstance(imagem_tratada, (list, tuple)):
        fotos = list(imagem_tratada) + [None] * len(sabores)
    else:
        fotos = [imagem_tratada] + [None] * len(sabores)
    ids: list[int] = []
    for i, sabor in enumerate(sabores):
        nome = f"{nome_familia} {sabor}".strip()
        # Onda 2 (anti-duplicata): o sabor que JÁ EXISTE no acervo é
        # CASADO, nunca recriado — reimportar/sabores novos SOMAM à
        # família. Foto nova de membro existente é ingerida NO
        # existente (a curadoria não-destrutiva preserva a anterior
        # como versão) — a grafia diferente nunca mais vira duplicata.
        exist = membro_do_acervo(nome)
        if exist is not None:
            if fotos[i]:
                from app.core.repositories import ProdutoRepositorio
                from app.images.biblioteca import biblioteca_da_config
                bib = biblioteca_da_config()
                bib.ingerir(exist["id"], fotos[i])
                db_e = Database().init()
                try:
                    with db_e.Session() as s_e:
                        ProdutoRepositorio(s_e).editar(
                            exist["id"],
                            caminho_imagem=bib.caminho_relativo(
                                exist["id"]))
                        s_e.commit()
                finally:
                    db_e.engine.dispose()
            ids.append(exist["id"])
            continue
        sub = ItemMesa(descricao=nome, preco=item.preco,
                       semaforo="VERMELHO", nome=nome)
        finalizar_criacao(sub, nome, mais18, fotos[i],
                          categoria=categoria)
        ids.append(sub.produto_id)
    criar_familia_de(ids, nome_familia)
    fam = familia_do_item(ids[0])
    item.produto_id = ids[0]
    item.semaforo = "VERDE"
    item.via = "novo"
    item.mais18 = mais18
    item.nome = nome_familia
    item.familia = fam
    item.sabores = list(sabores)           # M3: o descritor os anuncia
    if fam:
        aplicar_sabores(item, fam["membros"])
    item.imagem = next((m["imagem"] for m in (fam or {}).get("membros", [])
                        if m.get("imagem")), None)
    return item


def deve_revisar_no_lote(proposta: "PropostaCriacao") -> str | None:
    """Rodada JM (B3): a política da fila em lote numa função só — o
    motivo pelo qual o item NÃO é criado calado (None = pode criar).
    Perda de palavra (C-09) e "parece 2 produtos" sem componentes
    confirmados seguram o item para a curadoria; composto por chute
    nunca nasce."""
    if proposta.tokens_perdidos:
        return "a IA descartou palavra do nome"
    if proposta.possivel_composto and len(proposta.componentes) < 2:
        return "parece 2 produtos no mesmo preço — confirme na curadoria"
    return None


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
    from app.core.mais18 import eh_bebida_alcoolica
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
        # Rodada JM (B3): a pendência "multiplos" do sanitize vira a
        # PERGUNTA da curadoria (sugestão determinística; o humano
        # decide) — e o +18 heurístico entra (era False cravado)
        sugestao = (dividir_em_dois(descricao)
                    if any(pd.codigo == "multiplos"
                           for pd in res.pendencias) else [])
        return PropostaCriacao(nome=nome,
                               mais18=eh_bebida_alcoolica(nome),
                               categoria=None,
                               possivel_composto=len(sugestao) == 2,
                               sugestao_componentes=sugestao)
    from app.ai.enriquecimento import enriquecer
    enr = enriquecer(descricao, motor)
    comps = [c.nome_sanitizado for c in enr.componentes]
    # QUINTUSDECIMUS/J1 — a lei: a IA SOMA, nunca substitui. O detector
    # determinístico ("multiplos" + dividir_em_dois) continua valendo
    # com o LM ligado — na máquina do dono a IA devolvia zero
    # componentes e o sinal pronto era descartado; a pergunta "são 2
    # produtos?" nunca aparecia (o mesmo `or` que o mais18 já tinha).
    det = dividir_em_dois(descricao)
    return PropostaCriacao(
        nome=enr.nome_sanitizado,
        # a heurística só LIGA o +18 — nunca desliga o que a IA ligou
        mais18=enr.mais18 or eh_bebida_alcoolica(enr.nome_sanitizado),
        categoria=enr.categoria,
        tokens_perdidos=list(enr.tokens_perdidos),
        # L12 (§13.3/L2): a CARGA também soma — a IA que devolve UM
        # componente (o nome inteiro) não vale como resposta; a
        # sugestão determinística preenche os 2 campos (o dono não
        # digita à mão o que a régua já sabia)
        componentes=(comps if len(comps) >= 2 else det),
        possivel_composto=len(comps) >= 2 or len(det) == 2,
        sugestao_componentes=det,
        # o check só nasce PRÉ-MARCADO quando a IA deu os componentes;
        # sugestão da régua = desmarcado (o humano decide)
        componentes_da_ia=len(comps) >= 2)


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


def tratar_imagem(fonte: str, status_cb: StatusCb,
                  aviso_cb=None) -> str:
    """Baixa (se URL), remove o fundo + recorta + LUZ DE VITRINE +
    normaliza. Devolve o tratado.

    ``fonte``: caminho de arquivo OU URL (o "colar URL" da curadoria).
    SEXTUSDECIMUS-ESTÚDIO (03/08): a correção de exposição do Estúdio
    roda AQUI também (a queixa do dono: colar foto ruim só passava o
    removedor); ``aviso_cb`` recebe o aviso da régua do recorte-que-
    comeu-o-produto (I2 — o corte nunca mais é calado)."""
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
    processar_imagem(caminho, destino, modelo=modelo,
                     luz_de_vitrine=True, aviso_cb=aviso_cb)
    return str(destino)


def aprimorar_no_estudio(fonte: str, status_cb: StatusCb
                         ) -> tuple[str, str | None]:
    """ESTÚDIO na curadoria (pedido do dono, 03/08): a foto vira a
    melhor versão de DESIGN — o packshot completo do degrau 1 (recorte
    + luz + sombra sintética + enquadramento) e, se o gerador (degrau
    2) estiver ligado na Config E houver GPU/modelo, o refino de IA por
    cima. Sem GPU/modelo degrada COM aviso (a trava da F10: o degrau 2
    nunca é requisito). Devolve ``(caminho, aviso|None)``."""
    from PIL import Image

    from app.images.estudio import packshot_degrau1, refinar_com_gerador

    status_cb("Estúdio: compondo o packshot…")
    pack = packshot_degrau1(Image.open(fonte))
    aviso = None
    if estudio_gerador_ligado():
        status_cb("Estúdio: refinando com o gerador (IA)…")
        refinado, aviso = refinar_com_gerador(pack)
        if refinado is not None:
            pack = refinado
    destino = Path(tempfile.mkdtemp(prefix="atb_estudio_")) / "packshot.png"
    pack.save(destino, "PNG")
    return str(destino), aviso


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
            # Rodada JM (B3.5): bebida_alcoolica TAMBÉM é gravada — a
            # regra do selo automático (selos.py) e o Excel leem ELA;
            # gravar só selo_mais18 deixava o round-trip reverter o +18
            repo.editar(produto.id, nome_sanitizado=nome,
                        selo_mais18=mais18, bebida_alcoolica=mais18)
            # RODADA-125 v2: a MARCA reconhecida no nome é GRAVADA na
            # criação (o banco real tinha 116 produtos e ZERO marcas —
            # a hierarquia canônica da célula precisa dela; medido).
            # Só o inequívoco entra (F9: reconhece, nunca inventa).
            from app.core.marcas import marcas_no_nome
            achadas = marcas_no_nome(nome, marcas_para_exibicao())
            if achadas:
                repo.editar(produto.id, marca=achadas[0])
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
