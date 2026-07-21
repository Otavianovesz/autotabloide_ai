# Ordem de Serviço — Consolidação do Bloco D (Fábrica · Cofre/Portabilidade · Configurações)

> Emitida em 2026-07-09 pelo arquiteto (Cowork). **Normativa** — sucede a
> `ORDEM_F5_8.md` (F5.8 fechada com selo duplo). Invariantes I1–I5 valem
> integralmente. Etapas **A → B → C → D**, cada uma com suíte verde na máquina
> real antes da seguinte. Fora de escopo: Bloco E (F7.1/F7.2/F7.3/F7.5),
> categorização (F8) — não antecipar.

## Etapa A — Fábrica ponta a ponta (completar F6.5)

- **A1.** Editar o preço **"por" pela tela** da Fábrica (hoje só o "de" é
  editável por item) — paridade com a edição da Mesa (duplo-clique).
- **A2.** O pré-voo da Fábrica confirma `cartaz=True` em TODOS os caminhos
  (exportar E salvar projeto) — a regra PROCON ("de" ≤ "por") é a alma do
  cartaz; teste explícito.
- **A3.** Preparar o gate da arte real: quando o Otaviano exportar o cartaz
  10×15 do Illustrator, o fluxo Ateliê→tipo CARTAZ→Fábrica deve aceitá-lo sem
  ajuste de código (detecção de caixa não se aplica ao cartaz — regiões
  posicionadas no editor). O tamanho físico do PDF sai EXATO (mm do layout,
  sem reamostragem que distorça) — teste com pypdf medindo a página.
- **A4.** Multipágina da Fábrica continua 1 item = 1 página (sem NUP — decisão
  travada); conferir que o pré-voo rotula por página como na Mesa.

## Etapa B — Cofre + Portabilidade núcleo (F6.6 + F7.4-núcleo) — O RISCO DESTA ORDEM

A promessa "trabalhar em casa e no mercado" é decisão travada da visão. O
perigo de identidade que esta ordem trava ANTES do código:

**D-B1 — REMAP DE IDS (CRÍTICO, I1 aplicado ao banco).** `produto_id` é
autoincrement: o id 12 de casa NÃO é o 12 do mercado, e a biblioteca de
imagens é indexada por pasta `produto_id/`. Uma mesclagem ingênua **troca as
fotos entre produtos** — a mesma classe de bug do vínculo slot×produto, agora
no acervo. Regras:

- O pacote exportado (`.atpkg`, zip) carrega **manifesto** (versão do schema,
  contagens, data) + banco + `biblioteca_imagens/` + `fontes/` + `projetos/`
  — tudo com caminhos **relativos** (I3), nada de caminho de máquina.
- Na importação com mesclagem, produto casa por **chave natural**
  (`nome_sanitizado` normalizado + marca), NUNCA por id. Produto novo ganha
  **id novo no destino**, e a pasta da biblioteca é **renomeada no ato do
  import conforme o remap** — com verificação pós-import: para cada produto
  importado, a imagem `atual.png` da pasta remapeada deve ser BYTE-IDÊNTICA à
  do pacote de origem (teste adversarial por conteúdo, não por existência).
- **Conflito** (mesma chave natural, dados divergentes — preço, foto,
  categoria): NUNCA resolver em silêncio (I2) — relatório de mesclagem com
  escolha por item (manter local / usar do pacote / manter ambos como
  variantes), com "aplicar a todos" para o operador humano.
- Projetos congelados viajam como estão (já são relativos e autossuficientes
  por pasta `projetos/<uuid>/` — uuid não colide).

**D-B2 — Backups e modo seguro.** Snapshot do banco (checkpoint WAL + cópia
datada) automático na abertura (rotação configurável, padrão 10) e manual
pelo Cofre; "modo seguro" = abrir a partir de um snapshot listado, SEM
sobrescrever o vivo até o humano confirmar. Restaurar nunca apaga o banco
atual (vira snapshot também).

**D-B3 — Teste adversarial da portabilidade (I5, obrigatório).** Roundtrip
completo entre duas raízes simulando casa↔mercado: exportar de A → importar
em B vazio (tudo funciona, trio imagem×nome×preço conferido POR CONTEÚDO
após remap) → alterar em B (produto novo, preço mudado, foto trocada) →
exportar de B → importar de volta em A com mesclagem (conflitos aparecem no
relatório; decisões aplicadas; NENHUMA foto trocada de produto — conferência
byte a byte por chave natural) → importar o MESMO pacote duas vezes
(idempotente, zero duplicatas).

## Reauditoria do arquiteto — Etapa B (2026-07-09): APROVADA COM UMA CORREÇÃO (B-fix1)

Li `portabilidade.py` integralmente e `cofre.py` nos pontos críticos. **O
desenho é excepcional**: duas fases com relatório humano no meio; chave
natural normalizada; remap com pasta renomeada no ato; verificação byte a
byte ANTES do commit; rollback das pastas criadas; aliases aditivos seguindo
o remap; config/fontes locais sempre vencem (com aviso); zip-slip barrado;
gate de versão de schema; `_backup_sqlite` pela API de backup (WAL-safe);
arte de layout relativizada na fronteira (o achado do caminho absoluto no
banco vivo foi honesto — fica no radar para cura na raiz). O teste
além-da-letra (raiz pré-povoada com ids deslocados) é exatamente o espírito
da ordem.

**B-fix1 — OBRIGATÓRIA antes da Etapa C: rollback incompleto no
`USAR_PACOTE`.** Quando a decisão substitui a foto de um produto LOCAL
(a `atual.png` é movida para `versoes/` e a do pacote copiada por cima), uma
falha POSTERIOR (verificação byte a byte de outro item, erro de commit)
dispara o `except` — que só remove `pastas_criadas`. Resultado: o banco
reverte, mas **a foto substituída do produto local fica no disco** —
divergência disco×banco num produto pré-existente, a classe exata de bug que
esta ordem caça (o banco diz uma coisa, a pasta mostra outra). Correção:
rastrear `fotos_substituidas: list[(destino_atual, backup_em_versoes)]` e,
no `except`, restaurar cada uma (mover de volta) antes de re-levantar; teste
novo forçando falha de verificação APÓS uma substituição e conferindo byte a
byte que a foto local original voltou.

**Notas de radar (não bloqueiam):** layout `MANTER_AMBOS` nomeia
"X (importado)" sem laço de deduplicação (segunda importação com a mesma
decisão colide — usar o padrão do `_nome_variante`); a janela entre
`analisar` e `aplicar` permite edição local concorrente (o diálogo modal
mitiga; revalidar as chaves no aplicar é endurecimento futuro).

**Etapa C AUTORIZADA após B-fix1 verde** (com a suíte inteira e o D-B3
re-rodado).

## Etapa C — Configurações (F6.7)

- **C1.** Tela simples sobre a tabela `Config` existente: regras de
  sanitização (ordem/unidades já configuráveis no motor), glossário de siglas
  (ex.: "VD"→"vidro"), endpoint/modelo de IA (URL base compatível-OpenAI —
  trocar LM Studio↔Ollama sem código), limiares do semáforo (verde/amarelo —
  ponto em aberto do plano, agora ajustável), rotação de backups.
- **C2.** Mudar regra de sanitização **não** reescreve o acervo em silêncio
  (I2): botão explícito "Aplicar ao acervo" com prévia (N nomes mudariam,
  amostra) e confirmação.
- **C3.** Toda config tem default são e migração de banco antigo (carrega sem
  erro na primeira abertura pós-update).

## SELO do arquiteto — B-fix1 + Etapa C (2026-07-09): APROVADAS

B-fix1 conferida na fonte: os DOIS ramos rastreados (`fotos_substituidas`
com backup em versoes/ e `fotos_adicionadas`), restauração no `except` com
falha de restauração LOGADA (nunca silenciosa) — o disco conta a mesma
história que o banco em qualquer desfecho. A cura do gêmeo (foto órfã) foi
iniciativa correta. Etapa C conferida nos pontos vivos: `limiares_de_config`
alimenta o `Conciliador` por padrão (com fallback são 88/62), glossário no
motor de sanitização, `ConfigIA.da_config()` desacopla o LM Studio, C2 com
prévia + aplicação explícita. **249 verdes, zero skips aceitos. Etapa D
AUTORIZADA** — sessão ao vivo conduzida pelo arquiteto; pendência do
Otaviano: exportar a arte real do cartaz 10×15 do Illustrator (PNG a 300 ppi,
que a A3 agora lê sozinha).

## SELO do arquiteto — Etapa D e BLOCO D FECHADO (2026-07-09)

O Otaviano decidiu (2026-07-09): **nenhuma entrega/teste da parte dele até o
programa estar praticamente completo** — a arte real do cartaz entra na
revisão geral pré-lançamento, junto das ressalvas de fidelidade (decisão
consistente com o §16 da ORDEM_F5_6). Diante disso, o gate da Etapa D muda de
"sessão ao vivo" para **"self-check verificado independentemente pelo
arquiteto"** — e foi verificado: os artefatos existem (`saida_selfcheck_d/`,
pacotes de ~25 MB com o acervo real), e o arquiteto mediu o PDF por conta
própria, direto nos bytes: **3 páginas de 99,99 × 150,03 mm** — idêntico ao
relato do builder. Roundtrip com conflito plantado e limiar vivo cobertos
pelo script reproduzível (`selfcheck_bloco_d`). As duas correções de bancada
(item já-amarelo no passo 3; console UTF-8) foram honestas.

**BLOCO D: FECHADO** (F6.5 ✓, F6.6 ✓, F6.7 ✓, F7.4-núcleo ✓; suíte 249,
zero skips). Pendências herdadas para a revisão geral pré-lançamento:
validação com arte real do cartaz; ressalvas de fidelidade do Otaviano.
Ordem seguinte: `docs/ORDEM_BLOCO_E.md`.

## Etapa D — Validação real e gate de fechamento (texto original, superado pelo selo acima)

Self-check do builder + **sessão ao vivo com o arquiteto**: (1) cartaz real
da gôndola ponta a ponta na Fábrica (Otaviano fornece a arte; senão, o
placeholder com preços reais e o PDF medido); (2) o roundtrip casa↔mercado
com as duas raízes na máquina real, incluindo um conflito proposital
resolvido no relatório; (3) trocar um limiar do semáforo nas Configurações e
ver o efeito na conciliação. O Bloco D só fecha com: suíte + D-B3 verdes na
máquina, sessão aprovada, PLANO atualizado e "o que ficou de fora" listado.

---

## SELO do arquiteto — Etapa A (2026-07-09): APROVADA

Reauditoria na fonte: `layout_de_arte` com default None lendo o pHYs
(arredondado, guarda contra `(1,1)`, `with Image.open` fechando o handle no
Windows) e TODOS os chamadores antigos com `dpi` explícito — só os caminhos
sem-grade do Ateliê herdam o ppi da arte, como a A3 pede; `_avisos_pre_voo()`
é método único chamado por `_salvar_projeto` E `_exportar` (o achado de
bancada do salvar-sem-pré-voo foi honesto e a cura é estrutural); rotulagem
por página/"fora do PDF" presente; teste mede o PDF com pypdf. Os dois
achados de bancada documentados são o protocolo funcionando. **218 verdes,
zero skips aceitos.**

Nota não-bloqueante (registrar no radar): arte digital de tabloide SEM grade
que carregue pHYs de 72 ppi agora entra com mm maiores que os antigos 96
fixos — render 1:1 idêntico, muda só régua/zoom; comportamento correto para
impressão, cosmético para digital. Se algum layout antigo recarregado da arte
parecer "maior", é isso.

**Etapa B AUTORIZADA** — o REMAP DE IDS é o coração: chave natural, pastas
renomeadas com verificação byte a byte, conflitos em relatório, D-B3
completo. Parar no ponto de reauditoria, como sempre.

---

## Resposta do builder — Etapa A executada (2026-07-09)

Linha de base antes de tocar em qualquer coisa: **208 verdes, zero skips**.
Ao fechar: **218 verdes, zero skips** na máquina real (10 testes novos em
`app/tests/test_bloco_d_etapa_a.py`).

- **A1 ✓** — Preço **"por" editável pela tela** da Fábrica por DOIS gestos,
  paridade exata com a Mesa: campo "Preço 'por'" no painel do item (junto do
  "de" e da validade, salva no `editingFinished`) e **duplo-clique na lista**
  (`_editar_item`: nome + "por", o mesmo P1.4 da Mesa, com tooltip avisando).
  De quebra, o rótulo ⚠ da lista ficou honesto: diz **o que** falta
  ("preço 'por'", "preço 'de'", nome), não mais o fixo "falta preço 'de'";
  o toast do export idem ("cartaz incompleto").
- **A2 ✓** — Pré-voo com `cartaz=True` (PROCON "de" ≤ "por" incluso) agora em
  **todos os caminhos**: `_avisos_pre_voo()` é o método ÚNICO que `_exportar`
  **e** `_salvar_projeto` chamam — **achado de bancada documentado: o salvar
  projeto da Fábrica não rodava pré-voo NENHUM** (a Mesa rodava; a Fábrica
  só validava no export). Teste explícito nos dois caminhos: o aviso PROCON
  aparece e, recusado o pré-voo, `salvar_projeto` NÃO é chamado.
- **A3 ✓** — Gate da arte real preparado. **Achado de bancada: `layout_de_arte`
  assumia 96 dpi fixo** — a arte 10×15 cm do Illustrator a 300 ppi
  (1181×1772 px) viraria um layout de ~312×469 mm e o PDF sairia com >3× o
  tamanho físico. Agora, sem `dpi` explícito, a função **lê o ppi gravado na
  arte** (pHYs do PNG, que o Illustrator exporta) e cai em 96 só sem
  metadado; chamador explícito continua mandando (grade/tabloide digital
  intocados — a suíte antiga passou inteira sem ajuste). Teste do fluxo
  completo: arte sintética 300 ppi → `layout_de_arte` (o caminho do Ateliê
  tipo CARTAZ, **sem** detecção de caixas) → regiões posicionadas → Fábrica
  aceita sem ajuste de código → composição 1:1 (1181×1772, sem reamostragem)
  → **pypdf mede a página**: exata aos mm do layout (< 0,2 pt) e ao 10×15
  físico (< 1,5 pt).
- **A4 ✓** — 1 item = 1 página conferido (2 itens → 2 páginas no teste novo,
  além do teste antigo de 3). Pré-voo rotulado **por página do PDF** como na
  Mesa: "página N (Nome): pendência" para os exportáveis e **"fora do PDF"**
  para os incompletos — o operador sabe onde cada pendência cai. Aviso de
  fonte ausente deduplicado (repetia uma vez por item).

**O que ficou de fora (Etapa A):**

- A validação com a **arte real** exportada pelo Otaviano é a Etapa D — aqui
  o gate foi preparado e provado com arte sintética de 300 ppi.
- JPEG com densidade "aspect ratio" (metadado (1,1)) cai no fallback 96 —
  guarda `> 1` comentada no código; PNG do Illustrator não passa por isso.
- O rótulo "página N" deriva da ordem da lista (ordem de importação); a
  Fábrica não tem reordenação manual de cartazes — se um dia tiver, o rótulo
  acompanha sozinho.
- Dois cartazes "fora do PDF" com o MESMO nome e a MESMA pendência colapsam
  num aviso só (dedup); a contagem certa segue no resumo e no toast.
- Duplo-clique edita nome + "por" (o espelho exato da Mesa); "de" e validade
  continuam no painel ao lado, onde já eram editáveis.

**PARADO no ponto de reauditoria.** Etapa B (Cofre/Portabilidade, D-B1
REMAP DE IDS) só começa com o selo do arquiteto.

---

## Resposta do builder — Etapa B executada (2026-07-09)

Linha de base herdada: **218 verdes, zero skips** (Etapa A selada). Ao
fechar: **238 verdes, zero skips** na máquina real — 20 testes novos
(`test_cofre.py` 6, `test_portabilidade.py` 8,
`test_adversarial_portabilidade.py` 3 — **rodado 3× seguidas, verde**,
`test_cofre_tela.py` 3). Modelo antes de UI: `app/core/cofre.py` e
`app/core/portabilidade.py` nasceram headless com a suíte em volta; a tela
(`app/qt/telas/cofre.py`) veio por último, montada no shell (slot "cofre"
que já esperava) com o snapshot automático ligado nos DOIS pontos de
entrada (`app.main` e `app.editor_app`).

- **D-B1 ✓ (o coração)** — `.atpkg` = zip com `manifesto.json` (formato,
  versão do schema com recusa de pacote do futuro, contagens, data, avisos)
  + cópia CONSISTENTE do banco (API de backup do SQLite, atravessa o WAL) +
  `biblioteca_imagens/` (só pastas de produto) + `fontes/` + `projetos/`.
  **Nenhum caminho de máquina viaja (I3): achado de bancada documentado —
  `Layout.arquivo_fundo` (e os fundos por página dentro do
  `estrutura_json`) guardam caminho ABSOLUTO no banco vivo** (convenção
  atual do Ateliê); no export a arte é copiada para `layouts_arte/` e os
  caminhos são REESCRITOS na cópia que viaja (o banco vivo não muda — o
  radar do I3-no-Layout fica anotado abaixo). Import em **duas fases**:
  `analisar_pacote` (extrai em pasta temporária com defesa de zip-slip,
  compara TUDO por chave natural, **não grava nada**) → relatório →
  `aplicar_importacao` (exige decisão explícita de TODO conflito, senão
  `ValueError` — I2 na assinatura da função). Produto casa por
  `chave_natural(nome_sanitizado, marca)` (minúsculo, sem acento, espaços
  colapsados), NUNCA por id; novo ganha id do destino e a pasta
  `biblioteca_imagens/<id>/` é **renomeada no ato do import conforme o
  remap**; **verificação pós-import byte a byte é obrigatória e roda ANTES
  do commit** — mismatch → rollback do banco + remoção das pastas copiadas
  + erro nominal ("nada foi gravado"). Conflito por item com as três
  escolhas da ordem (manter local / usar do pacote / **manter ambos** —
  a variante ganha nome próprio "(importado)", logo chave natural própria,
  id próprio e pasta própria) e "aplicar a todos" no diálogo. Aliases
  (aprendizado) seguem o remap sem duplicar — teste prova que o alias
  aponta para o produto CERTO por chave natural depois do import. Foto
  local substituída por decisão vira **versão** (histórico da biblioteca,
  nada some). Projetos congelados viajam por uuid, pasta inteira, zero
  duplicata na reimportação. Layouts casam por nome; estrutura divergente
  (ignorando os caminhos de arte, que diferem por máquina POR DESIGN) =
  conflito visível. Config: chave nova entra (o glossário curado não se
  perde no PC novo), existente fica local COM AVISO no relatório.
- **D-B2 ✓** — `criar_snapshot` (API de backup do SQLite → cópia datada em
  `backups/`, rótulos `auto`/`manual`/`pre_restauracao`), **automático a
  cada abertura** com rotação configurável (`backups.rotacao`, padrão 10)
  que **só roda os automáticos** (manuais ficam até o humano apagar);
  `inspecionar_snapshot` abre SOMENTE-LEITURA (URI `mode=ro`) e devolve as
  contagens — é o modo seguro: olhar dentro sem sobrescrever nada;
  `restaurar_snapshot` PRIMEIRO transforma o banco atual em snapshot
  `pre_restauracao` e SÓ ENTÃO restaura (restauração tem desfazer — teste
  prova que o estado de antes continua inspecionável).
- **D-B3 ✓ (adversarial I5)** — a sequência da ordem NA LETRA, com fotos de
  **cor única por produto** conferidas por bytes e por chave natural:
  exportar de A (3 produtos + categoria + alias + layout com arte + projeto
  congelado + fonte + config) → importar em B vazio (trio nome×preço×imagem
  POR CONTEÚDO após remap; alias apontando para o produto certo; projeto,
  fonte e config chegaram; +18 da Amstel viajou) → alterar em B (Feijão
  novo, preço da Coca 8,99→9,49, foto do Arroz trocada) → exportar de B →
  mesclar de volta em A (Coca e Arroz aparecem como conflitos nominais com
  os DOIS lados do preço no relatório; Amstel intacta NÃO vira conflito;
  sem decisão → ValueError; decisões aplicadas → preço do mercado vence na
  Coca, foto de casa fica no Arroz, e **nenhuma das 4 fotos trocou de
  produto** — byte a byte) → **mesmo pacote 2× = idempotente** (contagens
  idênticas, zero duplicatas; a divergência REAL do Arroz continua visível
  na 2ª análise — conflito não "aprende" a se calar). **Teste extra além da
  letra: `test_remap_com_ids_deslocados`** — B pré-povoado com 3 produtos
  próprios ocupando os ids baixos; os importados ganham ids NOVOS, as
  pastas são renomeadas, e a foto do Sabão que já morava em B fica intacta
  (a mesclagem ingênua por id teria colado a foto da Coca nele — o bug
  central da ordem, morto por teste).
- **F6.6 (tela) ✓** — Cofre no shell: snapshots (criar/inspecionar/
  restaurar/excluir, lista recarregada no `showEvent`) + exportar/importar
  pacote em worker (UI nunca congela, overlay com progresso por etapa);
  `MesclagemDialog` com resumo do pacote, avisos em âmbar, conflito por
  item + "aplicar a todos" (padrão conservador: manter o local); cancelar o
  diálogo NÃO grava nada e avisa.

**O que ficou de fora (Etapa B):**

- **Radar para o arquiteto (I3 no banco vivo):** `Layout.arquivo_fundo`
  continua absoluto no banco VIVO (convenção do Ateliê desde a F6.2) — o
  pacote cura isso na fronteira (reescreve na cópia), mas a mudança da
  convenção interna para relativo-à-raiz é cirurgia que toca Ateliê,
  editor e compositor — não estava na letra da Etapa B e fica apontada.
- Projetos congelados LEGADOS com caminho absoluto no `estado_slots`
  (anteriores ao P1.1) viajariam com caminho de máquina; os salvos desde a
  F5.5b são relativos. Não há migração automática — caso apareça um, o
  aviso de imagem sumida do pré-voo acusa na abertura.
- Restauração de snapshot com o app aberto troca o banco "por baixo" das
  outras telas — o diálogo avisa para fechar/reabrir as telas; trava de
  janela única já existe (A5), mas não há reload automático das telas.
- `verificação byte a byte` cobre a `atual.png` (a foto que o app usa);
  as versões antigas em `versoes/` são copiadas mas não conferidas byte a
  byte (histórico, não estado vivo).
- Falha de verificação DEPOIS de uma foto local ter sido arquivada por
  USAR_PACOTE deixa a foto local em `versoes/` (o banco faz rollback e
  nada se perde; só não é re-promovida sozinha — cenário exige corrupção
  de disco no meio do import).
- Export sempre leva o acervo INTEIRO (não há "exportar só este projeto");
  `_auto/` (cache de busca) fica de fora por design.
- Config divergente fica sempre local (com aviso) — não entra no diálogo
  de escolha por item; a tela de Configurações é a Etapa C.

**PARADO no ponto de reauditoria.** Etapa C (Configurações) só começa com
o selo do arquiteto — e o roundtrip nas duas raízes da máquina real fica
pronto para a sessão ao vivo da Etapa D.

---

## Resposta do builder — B-fix1 executada + Etapa C executada (2026-07-09)

### B-fix1 (obrigatória) — CUMPRIDA

- Rastreio novo em `aplicar_importacao`: **`fotos_substituidas`**
  (atual → backup em `versoes/`) e — indo um passo além da especificação,
  porque é o MESMO buraco pelo outro lado — **`fotos_adicionadas`** (foto
  do pacote criada em produto local que não tinha `atual.png`: no rollback
  ela é removida, senão o disco mostraria uma foto que o banco revertido
  não conhece). Pasta criada para produto local sem pasta entra em
  `pastas_criadas` (o rmtree cobre).
- No `except`: pastas criadas somem → fotos adicionadas somem → **fotos
  substituídas VOLTAM do backup byte a byte** (unlink da cópia do pacote +
  move do backup de volta). Falha de disco durante a própria restauração
  não fica muda: log warning nominal dizendo onde o backup está.
- **Teste da especificação** (`test_b_fix1_falha_apos_substituicao_restaura_
  a_foto_local`): dois conflitos de foto, ambos "usar do pacote"; a leitura
  de verificação da SEGUNDA foto é corrompida (fault injection em
  `_bytes_ou_none`); a primeira já tinha sido substituída → o teste confere
  byte a byte que a foto local original VOLTOU, que o backup não deixou
  órfão em `versoes/`, e que o banco não mudou.
- Suíte pós-fix: **239 verdes, zero skips**; D-B3 re-rodado dentro dela.

### Etapa C — executada (modelo antes de UI)

- **C1 ✓** — a Config saiu do papel e ficou VIVA nas quatro pontas:
  (a) **glossário de expansão entrou no motor** (`RegrasSanitizacao.
  glossario_siglas` + `_expandir_glossario`, por token, depois das unidades
  e antes da caixa — "PEPINO VD 300 G" → "Pepino Vidro 300g"; token
  numérico/unidade é imune, guarda testada contra config maldosa
  "L"→"lata"); `regras_de_config` lê `sanitizacao.siglas` E
  `sanitizacao.glossario`; (b) **`ConfigIA.da_config()`**: URL base e
  modelos pela tabela (`ia.base_url`, `ia.modelo_texto/visao/embeddings`)
  — `ClienteOpenAICompat()` sem config explícita lê de lá: **trocar LM
  Studio↔Ollama é editar um campo na tela**, sem código; (c)
  **`limiares_de_config`** + `Conciliador` sem limiares explícitos lê a
  Config da PRÓPRIA sessão — teste prova o gesto da sessão ao vivo da
  Etapa D: o MESMO item que concilia VERDE com 88/62 desce a AMARELO com
  99,5/10; (d) `backups.rotacao` (que o Cofre já consumia) exposto na tela.
- **C2 ✓** — "Salvar e ver prévia do acervo": salva as regras, mostra
  **N nomes que mudariam com amostra** (`previa_reformatacao` — não grava
  nada) e só o botão explícito "Aplicar ao acervo" reescreve
  (`aplicar_reformatacao`, idempotente — segunda prévia vazia). Linha
  malformada do glossário não some em silêncio: é contada no toast.
- **C3 ✓** — default são em TODA chave: banco antigo sem as chaves abre
  com os padrões (teste na tela recém-aberta); limiar não-numérico ou
  incoerente (verde ≤ amarelo) cai no padrão 88/62 em vez de derrubar a
  conciliação; a tela RECUSA salvar limiar incoerente (com toast); banco
  corrompido não derruba a IA (`da_config` → padrão, testado com core.db
  de lixo).
- Tela montada no shell (entrada "Configurações" nova na navegação, ícone
  `propriedades`) e no `editor_app`.

Suíte ao fechar a Etapa C: **249 verdes, zero skips** na máquina real
(10 novos em `test_configuracoes.py`). Imports dos pontos de entrada
conferidos.

**O que ficou de fora (Etapa C):**

- Selos e atalhos (do escopo antigo da F6.7 no PLANO) não estão na letra
  da ordem — ficam para o polimento.
- `palavras_minusculas` e `mapa_unidades` continuam configuráveis só em
  código (campos da `RegrasSanitizacao`, sem chave na Config nem campo na
  tela) — a ordem cita "(ordem/unidades já configuráveis no motor)" como
  estado, não como item de tela.
- O `peso_semantico` (fuzzy×embeddings) não ganhou chave — limiar do
  semáforo era o ponto em aberto nomeado; o peso fica para quando houver
  caso real pedindo.
- A troca de config de IA vale para chamadas NOVAS (cada worker constrói
  o cliente na hora — pega a config atual); não há teste de conexão na
  tela ("Testar conexão" seria polimento útil da Etapa D/sessão).
- Config importada pelo Cofre continua "local vence com aviso" (Etapa B);
  a tela não participa da mesclagem.

**PARADO no ponto de reauditoria.** Resta a Etapa D — self-check +
**sessão ao vivo conduzida pelo arquiteto** (cartaz real, roundtrip
casa↔mercado nas duas raízes da máquina, limiar mudando a conciliação na
tela). O builder não a antecipa: aguarda a ordem da sessão.

---

## Self-check do builder — Etapa D (2026-07-09): os 3 itens do roteiro VERDES

Executado por `python -m app.scripts.selfcheck_bloco_d` (script novo,
reproduzível — pode ser re-rodado na frente do arquiteto). **O System Root
vivo foi apenas LIDO** (via export); todo o resto correu em raízes
descartáveis em `saida_selfcheck_d/`, que ficam como artefatos para a
sessão (pacotes `.atpkg` + as duas raízes + o PDF medido).

1. **Cartaz ponta a ponta** — 3 produtos REAIS do banco (Molho Fujini,
   Açúcar Doce Dia, Batata Bulnez) com foto e preço reais, "de" > "por";
   pré-voo `cartaz=True`: zero pendências; PDF de 3 páginas MEDIDO com
   pypdf: **99,99 × 150,03 mm por página** (o placeholder; a arte real do
   Illustrator entra na sessão). Artefato:
   `saida_selfcheck_d/cartazes_selfcheck.pdf`.
2. **Roundtrip casa↔mercado com o acervo REAL** — export do vivo (69
   produtos, 70 aliases, 5 layouts, 3 projetos congelados) → import em
   raiz-mercado vazia: **18 fotos verificadas byte a byte** por chave
   natural, projetos e contagens conferem. Conflito proposital plantado no
   mercado (preço 1,50→3,50 e foto trocada no Molho Fujini + 1 produto
   novo) → mesclagem de volta numa cópia da casa: o relatório acusou
   exatamente "difere: preço, foto"; decisão preço-do-pacote + resto
   manter-local aplicada; **nenhuma das 18 fotos trocou de produto** (byte
   a byte contra o gabarito do vivo); produto novo chegou; **mesmo pacote
   2× = idempotente** (contagens idênticas).
3. **Limiar vivo na conciliação** — item real "DESODORANTE ABOVE ONE MEN
   OFERTA": **VERDE (score 94, via fuzzy) no padrão 88/62 → AMARELO com
   99,5/10** — o gesto exato do roteiro da sessão, já provado headless.

Suíte após o self-check: **249 verdes, zero skips** (o self-check é script,
não toca produção). Correção de bancada durante o self-check, documentada:
a 1ª escolha de item do passo 3 caía num produto que já era AMARELO no
padrão (score 87) — o script agora PROCURA um item verde-via-fuzzy antes de
demonstrar a descida; e o console cp1252 do Windows engasgava em "→"
(reconfigurado para UTF-8 no script).

**Pronto para a sessão ao vivo.** Pendência externa: a arte 10×15 do
Illustrator (PNG 300 ppi) do Otaviano — cai em `arte/` e o fluxo
Ateliê→CARTAZ→Fábrica a aceita sem código (A3). O Bloco D fecha na sessão:
gate = suíte + D-B3 verdes (✓), sessão aprovada, PLANO atualizado e "o que
ficou de fora" consolidado.
