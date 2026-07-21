# AutoTabloide AI — Contexto do Projeto

> Fale sempre em **português (PT-BR)** com o Otaviano. Ele é o autor do projeto, estudante de medicina, **não é programador** — usa IA para programar. Seja didático, valide cada etapa com um caso real dele, e prefira código simples e legível.

## O que é

App **desktop offline** (Windows) que automatiza a produção de material gráfico de ofertas de um supermercado. Dois produtos num único app, com back-end compartilhado:

1. **Tabloide** — encarte de ofertas com vários produtos (WhatsApp/Instagram, às vezes impresso). Saída PNG/PDF, 1+ páginas.
2. **Cartaz de gôndola** — etiqueta de prateleira com preço "de"/"por". Saída PDF, 1 item por página, tamanho exato.

O fluxo que ele faz hoje na mão (Illustrator) e que o app automatiza: recebe foto/tabela de ofertas → OCR/importa → concilia com o banco → sanitiza nomes → busca/trata imagens → auto-preenche o layout → confere → exporta.

## Stack (decidido)

- **Python 3.12 + PySide6/Qt 6** (interface e canvas via QGraphicsScene).
- **SQLite + SQLAlchemy** (banco, modo WAL) + **sqlite-vec** (embeddings p/ conciliação).
- **IA local via LM Studio**, acessada pela **API padrão compatível com OpenAI** (não acoplar ao LM Studio — permitir trocar por Ollama). Modelos: **Qwen2.5-VL** (visão/OCR) + Qwen texto (sanitizar/julgar).
- **Imagens**: `rembg` (modelo **birefnet-general**) p/ fundo, `icrawler` (GoogleImageCrawler) p/ busca, **Real-ESRGAN** p/ upscale, Pillow/OpenCV.
- **Exportação**: Ghostscript (CMYK opcional) + pypdf.

## Decisões travadas (não violar)

- **Um app só**, telas diferentes p/ tabloide e cartaz, back-end compartilhado.
- **Renderização NÃO é SVG rasterizado** (CairoSVG estraga sombra/gradiente). É um **editor de camadas próprio**: o Illustrator faz só a arte de fundo (imagem); o app compõe as camadas dinâmicas (imagem do produto, nome, preço) desenhando texto e imagem diretamente (Qt/Pillow).
- **Flexibilidade/DIY**: os padrões (pilha de camadas, grade) são ponto de partida; quase tudo é personalizável.
- **Grade E agrupamento livre** com auxílio de alinhamento (snapping, distribuir) — nem todo tabloide é grade regular. Marcar célula-mestre 1 vez e replicar.
- **Projeto salvo congela os dados** (preço/nome/imagem/gramatura da época). Banco é ponto de partida; overrides por slot têm precedência.
- **Conciliação em 3 camadas**: embeddings → fuzzy → IA só nos ambíguos (nunca lê o banco inteiro). Semáforo verde/amarelo/vermelho.
- **Importação = tabela inteira sempre** (sem diff com o dia anterior); só cria os itens novos (vermelhos).
- **Sanitização**: ordem Tipo+Marca+Sabor+Peso; 1ª maiúscula, resto minúsculo; unidades minúsculas (g, kg, ml) exceto L; configurável.
- **Sem** criptografia pesada, **sem** módulo mobile/foto, **sem** camada "industrial" (watchdog, resiliência de missão crítica, RAG), **sem** kit campanha social.
- **Portabilidade**: banco simples + exportar/importar banco e pasta de imagens entre PCs.
- **Imagens ficam em disco** (não no banco); banco guarda o caminho + versões.
- **Impressão**: RGB padrão (CMYK opcional); **sem** imposição NUP (1 item = 1 página no tamanho exato).
- **Publicação social (F8, travada):** formato social (Oferta do Dia, carrossel, story, faixa) é **OUTRO `LayoutDef`** com outra proporção + a **MESMA cadeia produto→slot** — reusa `compor_pagina`, **nenhum motor novo**. **MP4 é OPCIONAL** (ffmpeg via `shutil.which`+subprocess; sem ele degrada COM aviso, nunca trava — o mínimo garantido é PNG/PDF + copiar imagem). A **marca d'água RASCUNHO** é automática até a **aprovação** (exige o checklist da F7) e vale em **TODA porta de exportação** — Mesa E Fábrica (lição da frota: a Fábrica foi a 2ª porta esquecida).
- **Estúdio de imagem (F10, travada):** o Estúdio tem **DOIS DEGRAUS**. O **degrau 1** (rembg + normalização de luz + sombra sintética + enquadramento, `app/images/estudio.py`) é o **PADRÃO GARANTIDO** — roda em CPU, em qualquer PC, sem GPU (o mínimo do "foto de celular → packshot"). O **degrau 2** (img2img local SDXL) é **OPÇÃO condicionada à GPU, NUNCA requisito** — sem GPU degrada com aviso e o degrau 1 entrega (guarda anti-alucinação `diferenca_demais`: se mudar demais o produto, rejeita). Curadoria **não-destrutiva** (original sempre preservada, versão nova, I1); **WebP preserva o alfa**; **upscale sob demanda mira o MAIOR lado da célula** (nem mais — bug da frota corrigido); foto repetida por **hash de conteúdo** (não nome); genéricas **marcadas** por convenção de caminho (`_genericas`, o pré-voo avisa); aba de scanner de código de barras **VETADA** (só Web e Acervo).
- **Cartaz, Fábrica e inteligência (F11, travada):** o **cartaz é 1 item/página no tamanho FÍSICO exato (mm), RGB** — biblioteca de layouts (`app/rendering/cartaz.py` `PRESETS_CARTAZ`: A4 retrato/paisagem, A5, etiqueta). O **% de desconto é CALCULADO (de−por)/de, NUNCA digitado** (`compositor.percentual_desconto` + `PapelTexto.DESCONTO`; some sem "de"/sem desconto real). A **validade no rodapé nunca fica vazia** (papel VALIDADE + pré-voo, RG-58). O **2-em-1 (R-106) é imposição CONTROLADA — SÓ no cartaz, SÓ se o dono ligar, NUNCA no tabloide** (guarda testada: a Mesa não conhece `impor_2em1`); sai em A4 paisagem com marcas de corte. A **cartaz-relâmpago (R-110, do Almoxarifado ao PDF num clique) é sempre RASCUNHO** — não há projeto aprovado por trás (a 3ª porta de exportação; um preço de balcão errado não vai limpo ao PDV). A **impressão direta (R-112, QPrinter) respeita mm E orientação** via `QPageLayout` (o Qt normaliza o `QPageSize` para retrato — orientação à parte). O **Excel (R-118) casa por CHAVE NATURAL** (reusa `portabilidade.chave_natural`), prévia→confirma, conflito nominal (I2), **sem foto/caminho absoluto (I3)**, roundtrip idempotente. A **inteligência (R-115..126) é SÓ LEITURA e LOCAL** (histórico/ranking/sazonal/relatório/divergência-por-uid/meta/saúde), carrega sob demanda (boot intacto). **VETADOS, ausentes por varredura de IDENTIFICADOR de código: R-116/119/124/125 (custo/margem de lucro, diário de alterações, backup em nuvem, ERP).**
- **IA colega (F9, travadas):** (1) a IA **NUNCA bloqueia o export** — a revisora/sentinela/avaliador são avisos clicáveis, nunca veto (teste: com erro plantado, o export acontece). (2) A IA **NUNCA inventa** marca/sigla/protocolo — só aprende o que o dono confirmou (alias/glossário); ambíguo vira amarelo (`extrair_marca` só devolve marca CONHECIDA, fronteira de palavra). (3) **Sem IA, tudo degrada** para fuzzy/manual COM aviso — ponto único `servico._motor_se_disponivel() → None`; a revisora do export (visão local) cai para heurística (nome cortado por medida, de≤por, preço fora de faixa) e nunca trava. Caça-duplicatas (R-075) funde por **chave natural** (I1, reusa `portabilidade.chave_natural`), soft-delete reversível — marca diferente nunca é par.

## Reaproveitar do código atual

- **Salvar**: `src/core/models.py` (schema), pipeline de imagem (recorte/rembg), ideia dos "smart items" gráficos.
- **Reescrever**: `src/engine/judge.py` (o `_match_fuzzy` é ingênuo — usar a conciliação em 3 camadas).
- **Descartar**: rasterizador CairoSVG (`src/qt/rendering/svg_engine.py`), camada industrial (century_industrial, sentinel_watchdog, resiliência, RAG, criptografia).

## Documentação

**Leia primeiro `docs/VISAO_COMPLETA.md`** — é a **referência-mãe da visão** do Otaviano (consolida os áudios e tudo que ele imaginou/decidiu; serve para você **antecipar cada caso de uso e ir além**). Depois, `docs/PLANO_DE_CONSTRUCAO.md` (estado atual + ordem das fases). Os `.docx` em `docs/` têm a especificação detalhada. O "como fazer" você detalha em código à medida que constrói.

## Como trabalhar

Construir de baixo para cima, buscando um resultado visível cedo. Ordem: (1) fundação limpa + salvar núcleo → (2) fatia vertical mínima (renderizar 1 produto num layout e exportar) → (3) IA + conciliação → (4) imagens → (5) as 6 telas → (6) teste final categorizado. Validar cada fase com um caso real do Otaviano. **Não** reintroduzir a complexidade "industrial" do protótipo antigo.

## Protocolo do builder (chat novo? comece EXATAMENTE por aqui)

Você é o **builder** de uma dupla com papéis fixos: o **arquiteto (Cowork, o
"auditor" que o Otaviano menciona)** emite ordens normativas em `docs/ORDEM_*.md`,
reaudita seu código lendo a fonte, conduz sessões ao vivo na tela e decide os
gates. **Você constrói.** O Otaviano dá o selo humano final. Esse fluxo
(ordem → construção → reauditoria → selo) fechou F5.5b, F5.6, F5.7 e F5.8 —
não o mude.

**Ritual de retomada (nesta ordem, sem pular):**
1. Este arquivo inteiro; 2. a **ordem vigente** (apontada acima) — é a sua
   pauta, execute na letra e na ordem das etapas; 3. `docs/PLANO_DE_CONSTRUCAO.md`
   (estado real); 4. rode `pytest app/tests -q` ANTES de tocar em qualquer
   coisa (linha de base: se não estiver verde, PARE e reporte); 5. só então
   codifique.

**Regras de conduta que viraram lei (cada uma nasceu de um bug real):**
- **Modelo antes de UI**; cada etapa fecha com a suíte INTEIRA verde na
  máquina real, informando **passados e zero skips** (skip silencioso não é
  verde — os testes da arte real em `arte/quintou/` contam).
- **Honestidade de bancada:** bugs seus achados pelos próprios testes são
  DOCUMENTADOS na resposta do builder dentro da ordem, nunca escondidos.
- **Teste que precisa de filtro/regra própria para passar = mascaramento:**
  a lógica sobe para a produção e o teste a importa (lição da C5/A7).
- **Todo TIPO NOVO de slot/região/entidade reavalia "ocupável" e o pré-voo**
  (o fantasma renasceu 2× por portas novas — não deixe nascer a 3ª).
- **Teste adversarial verifica POR CONTEÚDO** (pixel/byte), nunca por
  "não deu exceção"; toda fase que toca slot/item/região/id o atualiza (I5).
- Nomes/UI **em PT-BR**, código simples e legível; degradação sempre COM
  aviso (I2); nunca resolver conflito ou pular item em silêncio.
- Ao fechar etapa: atualizar o PLANO, responder na ordem vigente com
  "**o que ficou de fora**", e **PARAR no ponto de reauditoria** — não
  comece a etapa seguinte sem o selo do arquiteto.
- Dúvida de intenção/visão? `docs/VISAO_COMPLETA.md` responde; se não
  responder, pergunte ao Otaviano em vez de supor.

## Invariantes de integridade (auditoria 2026-07-09 — NUNCA violar)

Detalhes, justificativas e o gate vigente em **`docs/AUDITORIA_INTEGRIDADE_VINCULO.md`** (normativo).

- **I1. Identidade, nunca posição:** vínculo produto↔slot e região↔região-mestra sempre por ID estável (uid/produto_id). Índice de lista não é vínculo.
- **I2. Sem degradação silenciosa:** conteúdo ausente/inválido (imagem sumida, preço não parseado, fonte faltando) em exportação/salvamento aparece em relatório visível ao usuário; "pular em silêncio" é bug.
- **I3. Persistência portável:** nenhum caminho absoluto em JSON persistido (banco/projetos) — sempre relativo à raiz da pasta correspondente.
- **I4. Casamento mestra↔célula por `ref_mestre` (uid)**, imune a reordenação de z-order.
- **I5. Teste adversarial:** fase que toca slots/itens/regiões só fecha com o teste adversarial (§4 da auditoria) atualizado e verde — o teste tenta ativamente trocar conteúdo de lugar e confere o trio imagem/nome/preço por conteúdo, não por ausência de exceção.

**Decisão travada da Fase 4 (RG-55, 19/07/2026): o PAINEL DE PROPRIEDADES NUNCA FICA ÓRFÃO.** Clicar numa região SEMPRE a mostra no painel — agrupada ou não, sob outra ou não, rotacionada ou não. O 1º clique numa célula acende o TRIO (RG-15, para mover a célula), mas a região efetivamente clicada (`_primaria` no canvas) é a que o painel exibe; `selecionada()` a devolve mesmo com o trio selecionado. Todo estado agrupável tem seu inverso a UM clique no menu de contexto (RG-56). Instrumentação de seleção em `app/qt/design/diag_selecao.py` (desligável).

**ATUALIZAÇÃO (20/07/2026): FASES 4, 5, 6, 7, 8, 9 e 10 SELADAS. `docs/FASE_11.md` (Cartaz & Fábrica completos + inteligência) EXECUTADA — os 100 passos, INLINE (4 scouts de leitura no início + frota adversarial de 4 revisores no fecho; nenhum subagente escreveu). Baseline 665 → 708 verdes ×2, zero skips, exit 0 limpo. Cartaz completo (biblioteca de layouts em mm, de/por + % calculado, validade RG-58), cartaz-relâmpago + kit do Almoxarifado, QR, 2-em-1 (só no cartaz), impressão direta (mm+orientação), Excel por chave natural, inteligência só-leitura, vetos ausentes. Achado próprio: a impressão saía retrato num layout paisagem (Qt normaliza o QPageSize) — corrigido com QPageLayout. Galeria `saida_fase11/` claro/escuro + GIF. PARADO no passo 100 aguardando a reauditoria. Detalhe em `docs/FASE_11.md` e memória `fase11-progresso`. Próxima após o selo: `docs/FASE_12.md` (a última — precisa do Otaviano: teste de aceitação, instalador em Windows limpo, máquina com GPU p/ a revisora F9 + o SDXL F10). Histórico abaixo. —— **Ordem original: `docs/PLANO_PERFEITO.md` + o caderno da fase corrente. FASES 1, 2 e 3 SELADAS pelo arquiteto (18/07, 450 verdes ×2, zero skips, adversariais 16/16; RG-59 resolvido). `docs/FASE_4.md` EXECUTADA e CONSERTADA e **SELADA pelo arquiteto (19/07/2026)** — a reauditoria confirmou os consertos no disco real; o "must-fix #5" (CLAUDE.md) era falso positivo do staging obsoleto do arquiteto. `docs/FASE_5.md` **EXECUTADA (19/07/2026) — os 100 passos, INLINE (subagentes só p/ scout: 4 de leitura, ~190k, barato); PARADO no passo 100 aguardando a reauditoria do arquiteto (frota lendo o disco real)**. Blocos A–G: papel_texto nomeado + badge (RG-57); máscara de forma/enquadrar/pill/sombra (compositor, byte-idêntico no padrão); conta-gotas de estilo, modelos de célula + vitrine, reflow harmônico; miniaturas/undo visual/prévia mm/contraste WCAG/distribuir por espaçamento; migração RICA de layout antigo (testada com arte REAL de arte/quintou/) + pré-voo dos papéis; adversariais I1–I5 (achado próprio: lacuna I4 dos campos do Bloco B na propagação da mestra, corrigido + prova de mutação); galeria NATIVA (badges legíveis), GIF, jargão PT-BR. **538 verdes ×2, zero skips; prova de mutação em cada teste-pixel/adversarial/migração; boot ~58ms**. Detalhe em `docs/FASE_5.md` (Registro + Resposta do builder) e na memória `fase5-progresso`. **Decisão travada nova: todo TEXTO_LEGAL DECLARA o papel na criação (diálogo nomeado) e o EXIBE como badge permanente (cor+ícone); segue não-ocupável.** **FASE 5 SELADA pelo arquiteto (reauditoria no disco real + inspeção visual).** `docs/FASE_6.md` (Mesa I) **EXECUTADA (19–20/07/2026), os 100 passos, INLINE (4 scouts leitura ~340k); PARADO no passo 100 aguardando a reauditoria**: RG-53 barra que cabe a 720p (`setMinimumWidth(1)`+medição genérica); R-051 modo planilha (parser P0.3 rejeita ambíguo, reflete por uid, respeita override); estante viva (trocar por uid/override fica no slot, reordenar, duplicar uid novo, filtros); R-061 rascunho automático ISOLADO das versões F2 (nunca por cima do salvo) + Ctrl+K. **554 verdes ×2, zero skips; prova de mutação em cada teste-chave; boot da Mesa 35,6ms.** Detalhe em `docs/FASE_6.md` e memória `fase6-progresso`. Próxima após o selo: `docs/FASE_7.md`. RG-55/56/49/54 + R-025..041; boot do editor F4 14ms. Mapa DETALHADO de TODAS as fases 4–12 já escrito em `docs/FASES_4_A_12.md` — escopo, decisões travadas e testes de cada uma; o caderno literal de 100 passos nasce no início de cada fase.** — reta final em 12 fases × ~100 passos finos com "Por quê" por bloco (decisão do dono 18/07: extremo detalhe; 141 recomendações aceitas de docs/RECOMENDACOES_150.md, 9 VETADAS listadas no plano — não construir). Leis novas: selo só com inspeção visual de TODOS os artefatos; ambiguidade do dono se pergunta, não se escolhe. Histórico da revisão: `docs/REVISAO_GERAL.md` — a AUDITORIA DO DONO (17/07/2026: 1h de áudio + 1.057 capturas do Gravador de Passos em `revisão/` + campanha Sexta Verde nova). 40 achados RG-01..RG-40 em 6 ONDAS: 1-Desempenho (reclamação nº1: boot lento, pipeline sequencial, rembg 26s) → 2-Estabilidade (travamentos, teclado, estante sem gestão, dessincronia) → 3-UX do editor (Alt+roda=zoom, rotação, hifenização, célula como grupo, tooltips) → 4-Conteúdo/IA (enriquecer nunca descarta palavra, abreviações, datas inteligentes, Fica-a-Dica por IA) → 5-Visual+o marco ~40 → 6-Pesquisa (ciência do tabloide). Uma onda por vez, reauditoria por onda. Absorve o resto da ORDEM_F8. Históricos: `docs/ORDEM_F8.md` (Etapas A/B seladas), `docs/ORDEM_BLOCO_E.md` (FECHADO). **Regra vigente: sem sessões ao vivo nem lição de casa do Otaviano até o quase-fim — o arquiteto valida por artefatos**; a validação humana concentra na revisão geral pré-lançamento (F8/G). Históricos: `docs/ORDEM_BLOCO_D.md` (Bloco D FECHADO — Fábrica, Cofre/Portabilidade com remap, Configurações), `docs/ORDEM_F5_8.md`, `docs/ORDEM_F5_6.md`. Decisão travada nova: **selo +18 automático SEMPRE em bebida alcoólica**. As ressalvas de fidelidade do Otaviano ficam para a revisão geral pré-lançamento (§16 da ORDEM_F5_6).

**Gate histórico:** F5.5b **FECHADA em 2026-07-09** (P0.1–P0.4 + P1.1–P1.7; ver `docs/AUDITORIA_PESSIMISTA.md`), **confirmada pela reauditoria do arquiteto** (§5b da `docs/AUDITORIA_INTEGRIDADE_VINCULO.md`). A ressalva **P0.3b já foi implementada pelo próprio arquiteto (Cowork) em 2026-07-09** — `preco_decimal` devolve None para texto com mais de um número ("2x 5,00" nunca vira 25,00), com casos novos no `test_preco_decimal_adversarial` — **F5.6 liberada sem ressalvas** — pendência operacional **CUMPRIDA em 2026-07-09**: o builder rodou `pytest app/tests -q` na máquina real após as edições do arquiteto → **174 verdes** (incluindo o adversarial com os casos novos do P0.3b). Os invariantes I1–I5 acima seguem **permanentes**: toda fase que tocar slot/item/região atualiza e mantém verde o `test_adversarial_vinculo.py`.
