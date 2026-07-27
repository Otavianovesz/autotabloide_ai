"""
Modelo de layout (resolução-independente) — semente do editor da Fase 5
=======================================================================
Hierarquia: LayoutDef -> Pagina -> Slot -> Regiao.

  * As medidas ficam em **milímetros** (origem no canto superior esquerdo).
  * Cada Regiao tem um tipo ([IMAGEM], [NOME], [UNIDADE], [PREÇO], [SELO]).
  * Nesta fase (cartaz) usamos [IMAGEM], [NOME] e [PREÇO] (papéis "de"/"por"),
    mas o modelo já contempla os outros para o editor não precisar mudar depois.

Tudo serializa para JSON (para guardar em Layout.estrutura_json no banco).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum


def _uid() -> str:
    return uuid.uuid4().hex


class TipoRegiao(str, Enum):
    IMAGEM = "IMAGEM"
    NOME = "NOME"
    UNIDADE = "UNIDADE"
    PRECO = "PRECO"
    SELO = "SELO"
    TEXTO_LEGAL = "TEXTO_LEGAL"   # data/validade da oferta, "beba com moderação", etc.
    # F13-BIS/T2: a linha de DESCRITOR do item ("senepol · m. própria ·
    # 100 g") — todo encarte do pacote tem duas linhas por produto e o
    # app tinha uma. NÃO é conteúdo ocupável (lei do tipo novo: um slot
    # só com subtítulo não engole produto — grade.TIPOS_CONTEUDO).
    SUBTITULO = "SUBTITULO"
    # F13-TER/V2: recola o recorte do FUNDO ORIGINAL por cima do que já
    # foi desenhado — é o que põe a foto POR BAIXO da cesta/toldo/banda
    # da arte ("deixar ela preencher todo o vazio"). Decoração pura:
    # fora do ocupável e do pré-voo (lei do tipo novo).
    ADORNO = "ADORNO"
    # F13-TER/N2: o FIO tipográfico — retângulo chapado na ``cor`` da
    # região (o cabeçalho de seção do Jornal é fio + versalete, e o
    # fluxo põe o fio onde a linha CAIU, não onde a arte cravou).
    # Decoração pura: fora do ocupável e do pré-voo (lei do tipo novo).
    FILETE = "FILETE"


class FormaPreco(str, Enum):
    """F13-BIS/T1: a FORMA do preço é conceito de 1ª classe.

    O diagnóstico-raiz da reprovação do dono: sete encartes com sete
    formas de preço no desenho (medalhão, etiqueta pendurada, tag,
    oval, bandeira girada, carimbo) e o app desenhava UMA — texto preto
    corrido. A forma leva fundo/borda (``forma_cor``/``forma_cor_borda``),
    o texto usa ``cor``/fontes/subtipo da região, e o giro é o
    ``rotacao_graus`` de sempre. Os VALORES saem dos geradores do
    pacote, nunca de defaults."""

    TEXTO = "TEXTO"                        # o comportamento antigo (padrão)
    TAG_ARREDONDADA = "TAG_ARREDONDADA"    # Quarta (pricepod), Sexta (patches)
    PILULA = "PILULA"                      # cápsula cheia (nenhum gerador usa)
    OVAL = "OVAL"                          # elipse (bancas da Sexta)
    MEDALHAO_ESTRELA = "MEDALHAO_ESTRELA"  # Segunda (selo de cera, 18 pétalas)
    ETIQUETA_GIRADA = "ETIQUETA_GIRADA"    # Sábado (bandeirola c/ ponta à dir.)
    ETIQUETA_PENDURADA = "ETIQUETA_PENDURADA"  # Terça (disco escalopado + cordão)
    # (extensão declarada ao T1: o scout provou que o Jornal usa uma 8ª
    # forma — o carimbo de borda perfurada — que a lista da ordem não tinha)
    CARIMBO = "CARIMBO"                    # Jornal (borda tracejada, sem fundo)
    # F13-TER: a 9ª forma — o QUINTOU entrou no pacote (o publicado
    # real usa etiqueta vermelha com LISTRAS diagonais; ref. nas artes
    # de preço 4500×5418 do próprio dono)
    ETIQUETA_LISTRADA = "ETIQUETA_LISTRADA"


class SubtipoPreco(str, Enum):
    SEPARADO = "SEPARADO"   # inteiro grande + centavos pequenos
    COMPLETO = "COMPLETO"   # "R$ 19,90" corrido


class PapelPreco(str, Enum):
    UNICO = "UNICO"
    DE = "DE"               # preço antigo
    POR = "POR"             # preço da oferta


class PapelTexto(str, Enum):
    """RG-57/R-153: o que uma região de texto legal DECLARA que é.

    Torna explícito o que antes era um ``texto_fixo`` mudo — a região escolhe
    seu papel na criação e o exibe como badge para sempre. O compositor usa o
    papel para decidir o que desenhar. Padrão ``LIVRE`` (seguro): layout antigo
    sem papel definido cai aqui, sem perder o texto que já tinha (Bloco E).
    """

    LIVRE = "LIVRE"        # texto livre digitado pelo dono (padrão seguro)
    LEGAL = "LEGAL"        # aviso legal (bebida, sorteio, genérico) — preset
    VALIDADE = "VALIDADE"  # "de X até Y": puxa as datas do evento (RG-24/34/58)
    DICA = "DICA"          # "Fica a Dica" escrita pela IA (R-088)
    OBSERVACAO = "OBSERVACAO"  # R-071: observação do item ("limite 2 por cliente")
                               # — puxa `dados.observacao`; condicional (vazia não desenha)
    DESCONTO = "DESCONTO"  # R-109 (Fase 11): "-XX%" CALCULADO de (de−por)/de;
                           # condicional — some se não houver "de" (nunca digitado)
    EDICAO = "EDICAO"      # F13-TER/D1: "Nº X · ANO Y" do Jornal — puxa a
                           # edição VIVA do projeto; condicional (sem dado não
                           # desenha — rótulo que não é sempre verdade não
                           # pode estar na estrutura)


class Alinhamento(str, Enum):
    ESQUERDA = "ESQUERDA"
    CENTRO = "CENTRO"
    DIREITA = "DIREITA"
    JUSTIFICADO = "JUSTIFICADO"


class AlinhamentoV(str, Enum):
    """F13/C4 (R-01): alinhamento VERTICAL do bloco de texto na caixa.

    Não era bug de UI — o campo NÃO EXISTIA no modelo (o compositor
    centralizava incondicional). CENTRO é o padrão: layout antigo compõe
    byte-idêntico."""

    TOPO = "TOPO"
    CENTRO = "CENTRO"
    BASE = "BASE"


class Ajuste(str, Enum):
    CONTER = "CONTER"       # aspect-fit (cabe inteira dentro do retângulo)
    PREENCHER = "PREENCHER"  # cobre o retângulo (pode cortar)
    # F13-TER/V1: a causa-raiz do "pequeneninhas" — o acervo guarda um
    # QUADRADO 1000×1000 com o item pequeno dentro, e o CONTER ajusta o
    # quadrado. ASSENTAR recorta pela bbox do ALFA na composição (o
    # quadrado morre sem reprocessar o acervo), escala pelo maior fator
    # que caiba e ancora o produto no RODAPÉ da zona (assenta, não
    # flutua). É o ajuste dos encartes.
    ASSENTAR = "ASSENTAR"


class Mascara(str, Enum):
    """R-036 (Fase 5): forma de recorte da imagem, aplicada NO COMPOSITOR
    (Qt/Pillow por alpha), nunca por SVG. A máscara NÃO muda o retângulo do
    slot (I1) — é só a forma por onde a foto aparece."""

    RETANGULO = "RETANGULO"      # padrão: sem recorte de forma
    ARREDONDADO = "ARREDONDADO"  # cantos arredondados (raio ajustável)
    CIRCULO = "CIRCULO"          # círculo/elipse inscrito no retângulo


@dataclass
class Retangulo:
    """Retângulo em milímetros (origem no canto superior esquerdo da página)."""

    x_mm: float
    y_mm: float
    larg_mm: float
    alt_mm: float

    def to_dict(self) -> dict:
        return {"x_mm": self.x_mm, "y_mm": self.y_mm,
                "larg_mm": self.larg_mm, "alt_mm": self.alt_mm}

    @classmethod
    def from_dict(cls, d: dict) -> "Retangulo":
        return cls(d["x_mm"], d["y_mm"], d["larg_mm"], d["alt_mm"])

    @classmethod
    def de_px(cls, x: float, y: float, w: float, h: float, dpi: int) -> "Retangulo":
        """Cria um retângulo a partir de coordenadas em PIXELS (arte digital)."""
        from app.rendering.units import px_para_mm

        return cls(px_para_mm(x, dpi), px_para_mm(y, dpi), px_para_mm(w, dpi), px_para_mm(h, dpi))


@dataclass
class Regiao:
    tipo: TipoRegiao
    rect: Retangulo

    # --- identidade / estado de camada (F5.2) ---
    nome: str = ""            # rótulo no painel de camadas (vazio -> usa o tipo)
    visivel: bool = True
    travado: bool = False

    # --- identidade (F5.5b, invariante I1: identidade, nunca posição) ---
    # uid: identidade estável da região. ref_mestre: uid da região da MESTRA que
    # esta derivada espelha — o pareamento da propagação é por ele (I4), imune a
    # reordenação de z-order.
    uid: str = field(default_factory=_uid)
    ref_mestre: str | None = None

    # --- célula-mestre (F5.5) ---
    # de_mestre: esta região foi replicada da célula-mestre (recebe propagação).
    # overrides: atributos editados NESTA célula — têm precedência sobre a mestra
    # (mesmo princípio do projeto congelado: override local vence o padrão).
    de_mestre: bool = False
    overrides: set = field(default_factory=set)

    # --- estilo nomeado (F5.7): "Estilo Nome", "Estilo Preço"… ---
    # estilo: nome do EstiloTexto do layout que esta região segue (None = solto).
    # overrides_estilo: atributos ajustados NESTA instância — têm precedência
    # sobre o estilo (mesmo princípio da célula-mestre: local vence o padrão).
    estilo: str | None = None
    overrides_estilo: set = field(default_factory=set)

    # --- texto (NOME, UNIDADE, PREÇO) ---
    fonte: str = "Roboto-Regular.ttf"
    tamanho_max_pt: float = 48.0
    tamanho_min_pt: float = 6.0
    cor: str = "#000000"
    alinhamento: Alinhamento = Alinhamento.ESQUERDA
    incluir_unidade: bool = True

    # --- preço ---
    subtipo_preco: SubtipoPreco = SubtipoPreco.COMPLETO
    papel_preco: PapelPreco = PapelPreco.UNICO
    tamanho_centavos_pt: float | None = None   # separado: tamanho dos centavos
    fonte_centavos: str | None = None
    mostrar_moeda: bool = True   # se a arte já tem "R$", desligue: desenha só o número
    riscado: bool = False        # preço "de" riscado (cartaz de gôndola)
    # F13-BIS/T1: a FORMA desenhada atrás do preço (medalhão/tag/oval…).
    # TEXTO = o comportamento antigo (layout velho carrega TEXTO). O giro
    # da forma é o rotacao_graus; o texto usa cor/fontes/subtipo daqui.
    forma_preco: FormaPreco = FormaPreco.TEXTO
    forma_cor: str = "#C0392B"           # fundo da forma
    forma_cor_borda: str | None = None   # contorno (None = sem contorno)
    # F13-BIS/T1: no pacote, SÓ a Quarta sobrescreve os centavos (dy<0);
    # os selos/discos/bandeiras usam UMA baseline com centavos menores.
    # False = sobrescrito (o comportamento de sempre do SEPARADO).
    centavos_na_base: bool = False

    # --- imagem ---
    ajuste: Ajuste = Ajuste.CONTER
    # R-036: forma de recorte (a foto aparece por dentro dela). O raio só vale
    # p/ ARREDONDADO. Recorte é no compositor por alpha — não muda o rect (I1).
    mascara: Mascara = Mascara.RETANGULO
    mascara_raio_mm: float = 4.0

    # --- legibilidade sobre foto (R-035 pill, R-034 sombra/contorno) ---
    # pill: faixa/pílula semitransparente atrás do texto (nome). sombra/contorno:
    # efeito por INSTÂNCIA (override vale) p/ o texto se ler sobre foto clara.
    pill: bool = False
    pill_cor: str = "#000000"
    pill_opacidade: int = 128            # alpha 0..255 da pílula
    sombra: bool = False
    contorno: bool = False
    cor_efeito: str = "#000000"          # cor da sombra/contorno

    # --- texto legal (A1 da ORDEM_F5_8) ---
    # texto_fixo: conteúdo do LAYOUT (ex.: "Fica a Dica"), não do produto.
    # Tem precedência sobre dados.texto_legal e desenha mesmo em slot vazio.
    texto_fixo: str | None = None

    # --- papel do texto (RG-57/R-153, Fase 5) ---
    # papel_texto: para regiões TEXTO_LEGAL, DIZ o que a região é (aviso legal,
    # validade de/até, dica da IA, ou texto livre). O compositor decide o que
    # desenhar por ele; o editor exibe um badge. Regiões que não são de texto
    # legal simplesmente ignoram o campo (fica no padrão LIVRE).
    papel_texto: PapelTexto = PapelTexto.LIVRE

    # --- rotação (RG-12, Onda 3) ---
    # Graus no sentido horário, girando o CONTEÚDO em torno do centro do
    # rect (o rect em si não muda — âncora e vínculo ficam estáveis, I1).
    # A "data deitada" do template real do dono é rotacao_graus=90.
    rotacao_graus: float = 0.0

    # F13/C4 (R-01): vertical do texto — CENTRO = o comportamento de sempre
    alinhamento_v: AlinhamentoV = AlinhamentoV.CENTRO

    # F13-BIS/T5: hifenizar é o ÚLTIMO recurso — nas células estreitas
    # dos encartes o hífen destruía os nomes; com sem_hifen o corpo cede.
    sem_hifen: bool = False

    def to_dict(self) -> dict:
        return {
            "tipo": self.tipo.value,
            "rect": self.rect.to_dict(),
            "nome": self.nome,
            "visivel": self.visivel,
            "travado": self.travado,
            "uid": self.uid,
            "ref_mestre": self.ref_mestre,
            "de_mestre": self.de_mestre,
            "overrides": sorted(self.overrides),
            "estilo": self.estilo,
            "overrides_estilo": sorted(self.overrides_estilo),
            "fonte": self.fonte,
            "tamanho_max_pt": self.tamanho_max_pt,
            "tamanho_min_pt": self.tamanho_min_pt,
            "cor": self.cor,
            "alinhamento": self.alinhamento.value,
            "incluir_unidade": self.incluir_unidade,
            "subtipo_preco": self.subtipo_preco.value,
            "papel_preco": self.papel_preco.value,
            "tamanho_centavos_pt": self.tamanho_centavos_pt,
            "fonte_centavos": self.fonte_centavos,
            "mostrar_moeda": self.mostrar_moeda,
            "riscado": self.riscado,
            "ajuste": self.ajuste.value,
            "mascara": self.mascara.value,
            "mascara_raio_mm": self.mascara_raio_mm,
            "pill": self.pill,
            "pill_cor": self.pill_cor,
            "pill_opacidade": self.pill_opacidade,
            "sombra": self.sombra,
            "contorno": self.contorno,
            "cor_efeito": self.cor_efeito,
            "texto_fixo": self.texto_fixo,
            "papel_texto": self.papel_texto.value,
            "rotacao_graus": self.rotacao_graus,
            "alinhamento_v": self.alinhamento_v.value,   # F13/C4
            "forma_preco": self.forma_preco.value,       # F13-BIS/T1
            "forma_cor": self.forma_cor,
            "forma_cor_borda": self.forma_cor_borda,
            "centavos_na_base": self.centavos_na_base,
            "sem_hifen": self.sem_hifen,                 # F13-BIS/T5
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Regiao":
        return cls(
            tipo=TipoRegiao(d["tipo"]),
            rect=Retangulo.from_dict(d["rect"]),
            nome=d.get("nome", ""),
            visivel=d.get("visivel", True),
            travado=d.get("travado", False),
            uid=d.get("uid") or _uid(),     # migração: layouts antigos ganham uid
            ref_mestre=d.get("ref_mestre"),
            de_mestre=d.get("de_mestre", False),
            overrides=set(d.get("overrides", [])),
            estilo=d.get("estilo"),
            overrides_estilo=set(d.get("overrides_estilo", [])),
            fonte=d.get("fonte", "Roboto-Regular.ttf"),
            tamanho_max_pt=d.get("tamanho_max_pt", 48.0),
            tamanho_min_pt=d.get("tamanho_min_pt", 6.0),
            cor=d.get("cor", "#000000"),
            alinhamento=Alinhamento(d.get("alinhamento", "ESQUERDA")),
            incluir_unidade=d.get("incluir_unidade", True),
            subtipo_preco=SubtipoPreco(d.get("subtipo_preco", "COMPLETO")),
            papel_preco=PapelPreco(d.get("papel_preco", "UNICO")),
            tamanho_centavos_pt=d.get("tamanho_centavos_pt"),
            fonte_centavos=d.get("fonte_centavos"),
            mostrar_moeda=d.get("mostrar_moeda", True),
            riscado=d.get("riscado", False),
            ajuste=Ajuste(d.get("ajuste", "CONTER")),
            mascara=Mascara(d.get("mascara", "RETANGULO")),   # antigo: sem forma
            mascara_raio_mm=d.get("mascara_raio_mm", 4.0),
            pill=d.get("pill", False),
            pill_cor=d.get("pill_cor", "#000000"),
            pill_opacidade=d.get("pill_opacidade", 128),
            sombra=d.get("sombra", False),
            contorno=d.get("contorno", False),
            cor_efeito=d.get("cor_efeito", "#000000"),
            texto_fixo=d.get("texto_fixo"),
            papel_texto=PapelTexto(d.get("papel_texto", "LIVRE")),  # antigo: LIVRE
            rotacao_graus=d.get("rotacao_graus", 0.0),   # layout antigo: 0
            # F13/C4: layout antigo sem a chave = CENTRO (byte-idêntico)
            alinhamento_v=AlinhamentoV(d.get("alinhamento_v", "CENTRO")),
            # F13-BIS/T1+T5: região antiga = TEXTO/hifeniza (como sempre)
            forma_preco=FormaPreco(d.get("forma_preco", "TEXTO")),
            forma_cor=d.get("forma_cor", "#C0392B"),
            forma_cor_borda=d.get("forma_cor_borda"),
            centavos_na_base=d.get("centavos_na_base", False),
            sem_hifen=d.get("sem_hifen", False),
        )


@dataclass
class Slot:
    id: str
    regioes: list[Regiao] = field(default_factory=list)

    # --- célula-mestre (F5.5) e grupos livres (F5.6) ---
    # mestre: este slot é o MESTRE do seu grupo (editá-lo propaga).
    # origem_mm: âncora do slot na página; a geometria propaga RELATIVA a ela.
    # ref_grupo (D2 da ORDEM_F5_6): id do slot-mestre de que esta cópia deriva
    # (None = mestre, avulso ou legado — a migração preenche na carga). Vários
    # grupos (grade + grupos livres) coexistem na mesma página.
    mestre: bool = False
    origem_mm: tuple | None = None
    ref_grupo: str | None = None
    # F13/F1: célula FIXA carrega produto da PRÓPRIA ARTE (Terça 2,
    # Segunda 1, Quarta 3) — fica fora do auto-preencher e não conta
    # como vaga (grade.ocupaveis é o ponto único da regra).
    fixa: bool = False
    # F13-TER/N1: o CONTEÚDO do item fixo, guardado COM o template —
    # produto + foto ESCOLHIDA pelo dono + preço fixo OU da semana:
    # {"nome", "descritor", "preco", "preco_da_semana", "imagem",
    #  "marca"}; imagem relativa resolve contra biblioteca_imagens
    # (I3). O compositor desenha em TODA porta; a tabela da semana só
    # atualiza o preço quando preco_da_semana=True (chave natural,
    # D12) — nunca depende de OCR.
    conteudo_fixo: dict | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "regioes": [r.to_dict() for r in self.regioes],
            "mestre": self.mestre,
            "origem_mm": list(self.origem_mm) if self.origem_mm else None,
            "ref_grupo": self.ref_grupo,
            "fixa": self.fixa,
            "conteudo_fixo": (dict(self.conteudo_fixo)
                              if self.conteudo_fixo else None),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Slot":
        origem = d.get("origem_mm")
        return cls(
            id=d["id"],
            regioes=[Regiao.from_dict(r) for r in d["regioes"]],
            mestre=d.get("mestre", False),
            origem_mm=tuple(origem) if origem else None,
            ref_grupo=d.get("ref_grupo"),
            fixa=d.get("fixa", False),      # layout antigo: nunca fixa
            conteudo_fixo=d.get("conteudo_fixo") or None,   # N1 aditivo
        )


@dataclass
class Pagina:
    slots: list[Slot] = field(default_factory=list)
    # D8.2 (ORDEM_F5_8): frente e verso têm ARTES diferentes — fundo POR
    # página; None = herda o arquivo_fundo do layout (compat total).
    arquivo_fundo: str | None = None
    # F13-QUATER/L9: a CAMADA do dono — arte de overlay (RGBA) colada
    # sobre o fundo, escalada à página, com alfa (a camada de etiquetas
    # de preço do Quintou: o asset É a fonte da verdade e é CONSUMIDO,
    # nunca imitado em código). None = página sem camada (compat total).
    arquivo_camada: str | None = None
    # F8.2: seções visuais (contorno + título por categoria). São camada
    # DERIVADA — a página só guarda o liga/desliga e os títulos editados;
    # os retângulos são recalculados do mapa a cada composição. A seção
    # NUNCA vira slot nem região: fica fora do "ocupável" e do pré-voo
    # por construção (a 3ª aplicação da lei do tipo novo).
    secoes_ligadas: bool = False
    titulos_secoes: dict = field(default_factory=dict)   # categoria → título
    # F13-QUATER/A4: o ESTILO de seção POR PÁGINA (None = o global da
    # Config) — o Jornal em fluxo liga "JORNAL" aqui; aditivo
    estilo_secoes: str | None = None
    # FASE 4 (Bloco E, R-027/028): guias arrastáveis e grade magnética.
    # `guias`: lista de (orientacao 'x'|'y', coord_mm) — coordenadas em mm
    # RELATIVAS à página (I3: portável, nunca px absoluto). `grade_*`: o
    # snapping à grade e o passo dela; persistem POR LAYOUT (passo 64).
    guias: list = field(default_factory=list)
    grade_magnetica: bool = False
    grade_passo_mm: float = 5.0

    def to_dict(self) -> dict:
        return {"slots": [s.to_dict() for s in self.slots],
                "arquivo_fundo": self.arquivo_fundo,
                "arquivo_camada": self.arquivo_camada,     # QUATER/L9
                "secoes_ligadas": self.secoes_ligadas,
                "titulos_secoes": dict(self.titulos_secoes),
                "estilo_secoes": self.estilo_secoes,       # A4 aditivo
                "guias": [list(g) for g in self.guias],
                "grade_magnetica": self.grade_magnetica,
                "grade_passo_mm": self.grade_passo_mm}

    @classmethod
    def from_dict(cls, d: dict) -> "Pagina":
        return cls(slots=[Slot.from_dict(s) for s in d["slots"]],
                   arquivo_fundo=d.get("arquivo_fundo"),
                   arquivo_camada=d.get("arquivo_camada"),  # L9 aditivo
                   secoes_ligadas=d.get("secoes_ligadas", False),
                   titulos_secoes=dict(d.get("titulos_secoes") or {}),
                   estilo_secoes=d.get("estilo_secoes"),   # A4 aditivo
                   guias=[tuple(g) for g in (d.get("guias") or [])],
                   grade_magnetica=d.get("grade_magnetica", False),
                   grade_passo_mm=float(d.get("grade_passo_mm", 5.0)))


@dataclass
class LayoutDef:
    """Layout completo: tamanho físico canônico + DPI da arte + páginas.

    ``estilos`` (F5.7): os estilos de texto nomeados do layout — viajam com
    ele, congelam no projeto e são portáveis (I3), como tudo que serializa.
    """

    largura_mm: float
    altura_mm: float
    dpi: int = 300
    arquivo_fundo: str | None = None
    paginas: list[Pagina] = field(default_factory=list)
    estilos: dict = field(default_factory=dict)   # nome → EstiloTexto.to_dict()

    def to_dict(self) -> dict:
        return {
            "largura_mm": self.largura_mm,
            "altura_mm": self.altura_mm,
            "dpi": self.dpi,
            "arquivo_fundo": self.arquivo_fundo,
            "paginas": [p.to_dict() for p in self.paginas],
            "estilos": dict(self.estilos),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LayoutDef":
        layout = cls(
            largura_mm=d["largura_mm"],
            altura_mm=d["altura_mm"],
            dpi=d.get("dpi", 300),
            arquivo_fundo=d.get("arquivo_fundo"),
            paginas=[Pagina.from_dict(p) for p in d.get("paginas", [])],
            estilos=dict(d.get("estilos", {})),
        )
        layout.validar_ids_unicos()   # D8.1: recusa duplicata, NUNCA silêncio
        return layout

    def validar_ids_unicos(self) -> None:
        """D8.1 (ORDEM_F5_8): ids de slot são únicos no LAYOUT INTEIRO.

        Duas páginas do mesmo template com `celula_0..N` duplicados quebrariam
        o mapa `{slot_id → uid}` em silêncio (I1). Duplicata = erro claro.
        """
        vistos: dict[str, int] = {}
        duplicados: list[str] = []
        for n, pagina in enumerate(self.paginas, start=1):
            for slot in pagina.slots:
                if slot.id in vistos:
                    duplicados.append(
                        f"“{slot.id}” (páginas {vistos[slot.id]} e {n})")
                else:
                    vistos[slot.id] = n
        if duplicados:
            raise ValueError(
                "Layout inválido — ids de slot duplicados entre páginas: "
                + "; ".join(duplicados))


def layout_de_arte(caminho_arte: str, dpi: int | None = None, paginas: list["Pagina"] | None = None) -> "LayoutDef":
    """Cria um LayoutDef cuja base tem EXATAMENTE o tamanho em px da arte digital.

    Arte de tabloide/cartaz vem em pixels (ex.: 1080×1300). Largura/altura_mm
    derivam do px pelo dpi, então a composição sai 1:1 com a arte (sem
    reamostragem). Sem ``dpi`` explícito, vale o que a ARTE traz gravado —
    o Illustrator exporta o ppi no PNG, então o cartaz 10×15 cm a 300 ppi
    entra como ~100×150 mm e o PDF imprime no tamanho certo (A3 do Bloco D);
    arte sem metadado assume 96 (arte digital, de tela).
    """
    from PIL import Image

    from app.rendering.units import px_para_mm

    with Image.open(caminho_arte) as img:
        w, h = img.size
        if dpi is None:
            gravado = round((img.info.get("dpi") or (0,))[0])
            dpi = gravado if gravado > 1 else 96   # (1,1) = metadado JFIF vazio
    return LayoutDef(
        largura_mm=px_para_mm(w, dpi),
        altura_mm=px_para_mm(h, dpi),
        dpi=dpi,
        arquivo_fundo=str(caminho_arte),
        paginas=paginas or [Pagina([Slot("pagina", [])])],
    )
