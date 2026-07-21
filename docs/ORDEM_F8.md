# Ordem de Serviço — F8: Categorização, Seções e o Tabloide de ~40 (MARCO DE ACEITAÇÃO)

> Emitida em 2026-07-10 pelo arquiteto (Cowork). **Normativa** — sucede a
> `ORDEM_BLOCO_E.md` (Bloco E FECHADO). Invariantes I1–I5 e o critério
> "exit 0 limpo" valem. Etapas **A → B → C → D → E**, cada uma parada na
> reauditoria. Esta é a ordem do **teste de aceitação definido no primeiro
> dia**: o tabloide híbrido categorizado de ~40 itens. Ao fim dela, o
> Otaviano VOLTA ao circuito para a revisão geral (ressalvas, arte real do
> cartaz, selo humano final) — preparar essa volta é a Etapa E.

## Etapa A — F8.1: categorização corrigível

- **A1.** IA categoriza EM LOTE o que falta no acervo (reusa o motor do
  `enriquecer_banco`); categoria nunca é obrigatória — item sem categoria
  entra em **"Outros"** (nunca some, I2). Correção humana já existe no
  Almoxarifado (campo categoria) — conferir que a correção SOBREVIVE a novo
  passe de IA (humano venceu = não reprocessar; marcar origem
  humana/IA da categoria).
- **A2.** Mesa ganha o modo **"Agrupar por categoria"** no auto-preencher
  (toggle, padrão desligado): ordena a estante por categoria (ordem das
  categorias configurável; "Outros" por último) ANTES do preenchimento na
  ordem visual. O mapa continua slot→uid — o agrupamento é só ordenação
  prévia, nunca vínculo novo.

## Resposta do builder — Etapa A executada (2026-07-10)

Linha de base: **281 verdes, zero skips, exit 0**. Ao fechar: **287 verdes,
zero skips, exit 0 em DUAS rodadas** (6 testes em `test_categorizacao.py`).

- **A1 ✓** — `Produto.categoria_origem` ("humano"/"ia") com a **primeira
  migração real de schema do projeto**: `_migrar_schema` no `Database.init`
  (`ALTER TABLE ADD COLUMN`, idempotente, guiado por um mapa de colunas
  novas) — banco ANTIGO abre sem erro e ganha a coluna (testado com sqlite
  cru, sem a coluna, re-init inofensivo). Categoria editada no Almoxarifado
  → `servico.editar_produto` marca **"humano"**; a guarda no
  `enriquecer_banco` **nunca a sobrescreve** — e o teste é duro: o fake
  RENOMEIA o produto de propósito, provando que a edição ACONTECEU e mesmo
  assim a categoria humana ficou. Botão **"Categorizar (IA)"** no
  Almoxarifado (`categorizar_acervo`): lote SÓ no que falta; categoria
  existente (humana OU de IA) intocada; IA sem palpite deixa vazio — o
  item agrupa em "Outros" na Mesa e **nunca some** (I2).
- **A2 ✓** — Toggle **"Agrupar por categoria"** na barra da Mesa (padrão
  DESLIGADO): `ordenar_por_categoria` é ordenação **estável** da FILA do
  preenchimento (a estante não muda; **o mapa continua slot→uid** — o
  agrupamento é ordenação prévia, nunca vínculo novo, testado). Ordem das
  categorias pela Config (`categorias.ordem`, campo novo na tela de
  Configurações); categoria fora da lista entra alfabética depois das
  listadas; **"Outros" sempre por último**. `ItemMesa.categoria`
  preenchida na conciliação e no importar-do-banco (projetos velhos sem a
  chave abrem com None — sem migração).

**Achado de bancada (documentado):** o `MotorIAFake` com chave de resposta
VAZIA nunca casa (`_casar` pula chave falsy) — o primeiro rascunho de dois
testes passava por *sorte compatível* (a resposta "{}" degradava para o
mesmo resultado esperado), sem provar nada. Corrigido com chave real do
prompt ("supermercado") e o teste do humano endurecido para exigir a
edição real antes da guarda.

**O que ficou de fora (Etapa A):**

- "Outros" é rótulo de AGRUPAMENTO (não vira linha na tabela Categoria —
  item sem categoria continua sem categoria no banco).
- A origem "humano"/"ia" não aparece na UI do Almoxarifado (só governa a
  regra); um badge é polimento.
- A ordem das categorias é global (Config), não por projeto — congela no
  projeto via mapa, como tudo.

**PARADO no ponto de reauditoria.** Etapa B (F8.2 — seções visuais, a 3ª
aplicação da lei do tipo novo) só começa com o selo do arquiteto.

## SELO do arquiteto — Etapa A (2026-07-10): APROVADA

`_migrar_schema` é a migração mínima certa (PRAGMA-guiada, idempotente,
mapa de colunas novas pronto para as próximas); `ordenar_por_categoria` é
ordenação estável pura com "Outros" sempre por último — o vínculo nem é
tocado, como a ordem exigia. A guarda humano-vence-IA testada com o fake
RENOMEANDO o produto (provando que a edição aconteceu e a categoria humana
ficou) é teste duro de verdade. E o achado de bancada vai para a moldura ao
lado dos outros: **"teste que passa sem exercitar a regra é tão perigoso
quanto teste vermelho"** — a caça ao fake-que-nunca-casa é auditoria do
próprio instrumento. Exclusões declaradas aceitas ("Outros" como rótulo de
agrupamento, não linha no banco, é a decisão correta). **287 verdes ×2,
exit 0, zero skips aceitos. Etapa B AUTORIZADA** — seção é decorativa;
ocupável e pré-voo reavaliados ANTES do primeiro teste; o B4 (seções não
deslocam nem cobrem conteúdo, por pixel) é onde a lupa vai morar.

## Etapa B — F8.2: seções visuais (contorno + título)

**LEI DA CASA (3ª aplicação): tipo novo de região/entidade → reavaliar
"ocupável" e o pré-voo ANTES do primeiro teste.** A seção é DECORATIVA.

- **B1.** Seções são CALCULADAS do preenchimento agrupado: runs de células
  contíguas (na ordem visual, por página) com a mesma categoria. Desenho:
  contorno arredondado (cor/espessura configuráveis, padrão azul da visão)
  + **título da seção** ("Limpeza") no topo do bloco. Run que atravessa
  quebra de linha desenha por sub-retângulos (um por linha) com título só
  no primeiro — célula não-retangular não quebra o desenho.
- **B2.** As seções vivem como camada derivada (recalculada do mapa+
  categorias a cada recomposição) — NÃO entram no mapa, NÃO são ocupáveis,
  e o pré-voo as ignora por desenho (com teste provando que um layout com
  seções não consome item nem gera aviso falso).
- **B3.** DIY da visão: título editável por seção (override por página),
  seção pode ser desligada por página; multipágina desenha por página.
- **B4.** Adversarial: com seções LIGADAS, o trio imagem×nome×preço por
  célula continua exato (por pixel) sob shuffle + reabrir; seções não
  deslocam nem cobrem conteúdo (amostragem de pixels das células sob o
  contorno).

## Resposta do builder — Etapa B executada (2026-07-10)

Linha de base: **287 verdes, zero skips, exit 0**. Ao fechar: **294 verdes,
zero skips, exit 0 em DUAS rodadas** (6 em `test_secoes.py` + 1 adversarial).

- **A lei da casa, cumprida ANTES do primeiro teste — por construção:**
  a seção NUNCA entra no modelo. Não é slot, não é região, não entra no
  mapa: é camada DERIVADA (`app/rendering/secoes.py`), recalculada do
  preenchimento a cada composição. A página guarda SÓ o liga/desliga e os
  títulos editados (`Pagina.secoes_ligadas`/`titulos_secoes`, serializados
  → congelam no projeto de graça). O teste da B2 prova: grade completa +
  seções ligadas = ocupáveis IDÊNTICOS e pré-voo com ZERO aviso — o
  fantasma não tem porta para nascer.
- **B1 ✓** — `calcular_secoes`: runs de células CONTÍGUAS na ordem visual
  com a mesma categoria (célula vazia QUEBRA o run; sem categoria =
  "Outros"); run que atravessa quebra de linha vira **um sub-retângulo por
  linha** (linhas detectadas pelo topo das células), título só no 1º.
  Desenho: contorno arredondado na FOLGA entre células (bbox do run +
  margem) + **título em etiqueta na borda** (pílula da cor da seção com o
  texto em branco); cor/espessura pela Config (`secoes.cor`,
  `secoes.espessura_mm` — campos na tela de Configurações, defaults sãos:
  o azul da visão, 0,8 mm). As seções desenham DEPOIS do fundo e ANTES do
  conteúdo — cobertura do trio é IMPOSSÍVEL por ordem de pintura.
- **B2 ✓** — teste nominal da lei (acima) + gancho único no compositor
  (`pagina.secoes_ligadas` e dados com categoria — nada muda em quem não
  usa).
- **B3 ✓** — DIY: na Mesa, agrupar LIGA as seções em todas as páginas;
  checkbox **"Seções nesta página"** desliga por página (sincronizado na
  navegação); botão **"Títulos…"** edita o rótulo por seção/página
  ("Limpeza" → "Casa Limpa"; vazio volta ao padrão). Tudo congela no
  projeto e reabre idêntico.
- **B4 ✓ (a mira da lupa)** — `test_adversarial_secoes_nao_cobrem_conteudo`:
  com seções LIGADAS, o trio de CADA célula é **pixel-idêntico** ao
  desligado em 4 pontos por região (centro + 3 quartos), a imagem composta
  muda (as seções EXISTEM), shuffle da estante não mexe em nada, e o
  congelado reabre com liga/desliga + títulos persistidos e o trio exato
  por cor.

**O que ficou de fora (Etapa B):**

- O título mora sempre na borda superior do 1º sub-retângulo (posição
  fixa); posição configurável é polimento.
- Contorno pode ficar parcialmente ATRÁS de uma foto opaca na borda da
  célula — consequência deliberada do desenho-antes-do-conteúdo (a
  garantia de nunca cobrir o trio); visualmente correto nas artes com
  folga entre células (as reais têm).
- Cor por CATEGORIA (cada seção de uma cor) não entrou — uma cor global
  pela Config; por-categoria é polimento pós-1.0.

**PARADO no ponto de reauditoria.** Etapa C (F8.3 — O MARCO dos ~40) só
começa com o selo do arquiteto.

## SELO do arquiteto — Etapa B (2026-07-10): APROVADA

A lei da casa foi cumprida da forma mais forte possível: a seção NÃO EXISTE
no modelo — camada derivada recalculada da composição, reusando `ocupaveis`
+ ordem visual (a fonte única da verdade), com célula vazia quebrando o run
e o desenho ANTES do conteúdo (cobrir o trio é impossível por ordem de
pintura; o título mora na margem, nunca sobre células). O B4 confere por
pixel com seções ligadas E desligadas. O blindado do `fontes_dir=None` pego
antes do teste é o reflexo maduro. **294 verdes ×2, exit 0, zero skips
aceitos. Etapa C AUTORIZADA — O MARCO.** O tabloide categorizado de ~40 com
as artes reais: o self-check gera os artefatos e o arquiteto medirá e
inspecionará por conta própria, como sempre.

## Etapa C — F8.3: O MARCO — tabloide categorizado de ~40 itens

Ponta a ponta com as artes reais de `arte/quintou/` (frente+verso; páginas
extras se os 40 pedirem): importar tabela de ~40 itens (montar fixture real
a partir dos acervos existentes + categorias variadas), conciliar,
auto-preencher AGRUPADO, seções desenhadas, pré-voo, exportar PNG×N + PDF.
Self-check reproduzível (`selfcheck_f8`) gerando os artefatos para a
reauditoria do arquiteto (que medirá e inspecionará por conta própria).

## Resposta do builder — Etapa C executada (2026-07-10): O MARCO RODOU

Linha de base: **294 verdes, zero skips, exit 0**. Ao fechar: **295 verdes,
zero skips, exit 0 em DUAS rodadas** (o teste permanente do marco).

**Duas peças, como os marcos anteriores:**

1. **`test_marco_f8.py` (permanente, determinístico)** — 40 itens de cor
   única sobre as DUAS faces reais do Quintou + a página extra que os 40
   pedem (45 células, ids únicos conferidos); fila agrupada (Mercearia
   primeiro, "Outros" no fim); **pré-voo LIMPO** (zero avisos — foto,
   preço e nome em tudo; seções sem aviso falso); PNG×3 **1:1 com a arte**
   (1080×1300) + PDF de 3 páginas; **o trio de CADA célula por pixel nas
   três páginas**; seções visíveis (ligado ≠ desligado); congelado
   reaberto com seções ligadas e spot por pixel na página 2.
2. **`python -m app.scripts.selfcheck_f8` (o REAL)** — acervo real clonado
   via .atpkg (o vivo é só LIDO; tudo acontece em `saida_selfcheck_f8/raiz`):
   - **a IA REAL estava ligada e categorizou 34 produtos do acervo, zero
     sem palpite** (10 categorias distintas no clone — nenhuma categoria
     de demonstração foi necessária);
   - fixture canônica de **40 itens reais** gerada do acervo
     (`app/tests/fixtures/ofertas_quintou_40.txt` — nas próximas execuções
     é reutilizada, não regenerada);
   - **conciliação 40/40 🟢** (match exato — o acervo conhece os nomes);
   - auto-preencher AGRUPADO: 40 itens em 45 células, 3 páginas, e o
     script CONFERE a contiguidade — **9 blocos de categorias reais, cada
     uma num bloco único**: Bebidas → Congelados → Frios → Higiene →
     Hortifrúti → Limpeza → Mercearia → Padaria → Pet;
   - pré-voo com **22 pendências NOMINAIS** (produtos reais sem foto —
     a curadoria contínua do Almoxarifado, registrada desde a F5.8; cada
     uma com página+célula+nome, nada genérico);
   - export `marco_p1..p3.png` (1:1) + `marco.pdf` (3 páginas, medido);
     seções visíveis por comparação ligado/desligado;
   - projeto **congelado e reaberto idêntico** (mapa + seções + itens) —
     no clone, nunca no vivo.

**O que ficou de fora (Etapa C):**

- O selfcheck usa conciliação por match exato (nomes vêm do próprio
  acervo) — os caminhos fuzzy/juiz têm seus próprios gates fechados (F3,
  S1); aqui o objetivo é o fluxo completo, não re-testar a conciliação.
- As 22 células sem foto ficam como estão de propósito: são o retrato
  REAL do acervo e a demonstração do I2 (pendência nominal, nunca
  silêncio). Completá-las é curadoria de conteúdo, não código.
- O F8.3 **não recebe selo de aceitação aqui**: executado e verificável;
  a ACEITAÇÃO é do Otaviano, na sessão final (Etapa E prepara).

**PARADO no ponto de reauditoria.** Etapa D (performance dos 5.000 +
varredura do radar) só começa com o selo do arquiteto.

## Etapa D — F8.4: performance e varredura final do radar

- **D1.** Medir com acervo sintético grande (≥5.000 produtos): abertura do
  app, busca do Almoxarifado (virtualizada), conciliação de 40 itens
  (embeddings NUNCA leem o banco inteiro — conferir o plano de consulta),
  auto-preencher e export. Orçamentos: abrir < 5 s; conciliar 40 < 3 min
  com IA local; exportar < 30 s. Estourou → otimizar antes de fechar.
- **D2.** Varredura FINAL do radar acumulado (tudo que foi anotado nas
  ordens): gancho global de shutdown (workers em voo ao fechar o APP);
  layout linha-dupla entre as fases da portabilidade; foto original ao lado
  da tabela na conciliação (conferência do OCR); zoom do rodapé por tela;
  busca por nome no Dashboard/Ateliê. Cada item: corrigir OU registrar
  como pós-1.0 com justificativa — nada órfão.

## Etapa E — Preparação da REVISÃO GERAL (a volta do Otaviano)

O builder monta o **dossiê da revisão** (`docs/REVISAO_GERAL.md`): tudo que
foi adiado por decisão dele, em checklist acionável — as ressalvas de
fidelidade a coletar (F5.6 §16), a arte real do cartaz 10×15, o gate de
fidelidade visual contra os padrões-ouro, os pontos "decidir testando" do
plano (limiares, upscale, máscara não-retangular do doc C6), e o roteiro da
sessão ao vivo final (arquiteto na tela + Otaviano decidindo). O F8.3 só
recebe o selo de ACEITAÇÃO nessa sessão — é o selo humano que fecha a
construção e abre o Bloco G (empacotamento).
