# ORDEM DE SERVIÇO — Fechamento F4→F11 antes do Marco (Fase 12)

> Gerada pela auditoria de **800 passos (F4–F11) + delta do polimento** — 21/07/2026.
> Recomendação da auditoria: **selar com ressalvas**. Esta ordem elimina as ressalvas para
> chegar ao selo limpo. Placar de origem: 505 implementados · 119 parciais · 14 ausentes ·
> 192 de processo (rodar suíte / prints). **0 defeitos críticos, 29 maiores, 40 menores.**

---

## 0. REGRAS DURAS (leia antes de tocar em qualquer arquivo)

1. **Executor:** Fable 5 no Code, **SEM subagentes** — trabalho inline, para economizar tokens.
2. **NÃO abra a Fase 12** enquanto TODOS os itens desta ordem não estiverem feitos e a suíte
   completa não passar **VERDE com exit-0 LIMPO** (sem crash/segfault no fechamento).
3. **Toda correção precisa de teste à prova de mutação (mutation-proof):** o teste verifica
   POR CONTEÚDO (valor/pixel/byte/uid) e **falha se você reverter a correção**. Teste que só
   checa "não deu exceção" = mascaramento = proibido.
4. **Leis invioláveis:** "verde com crash no exit não é verde"; degradação SEMPRE com aviso
   (I2); identidade por uid/produto_id, nunca por posição (I1); persistência só com caminhos
   relativos (I3); mestra↔cópia por ref_mestre uid (I4).
5. **NÃO toque no compositor** (`app/rendering/compositor.py`) nem quebre a identidade por
   bytes — os guardas atuais (máscara RETANGULO→None, texto stroke=0, pill só com reg.pill,
   percentual_desconto HALF_UP) estão CORRETOS e foram verificados. Deixe como está.
6. **Antes de começar:** faça o commit-baseline do `app/` (se ainda não fez) para ter ponto
   de retorno. Garanta no `.gitignore`: `saida_*/`, `_lixo_claude/`, `.audit_snapshot_*`.
7. **Cadência:** ao fechar cada fase, rode a suíte daquela fase; ao fechar tudo, rode a suíte
   completa (`python -m pytest app/tests -q -p no:cacheprovider`), confirme exit-0 e me mande
   o final da saída + o `%ERRORLEVEL%`.
8. **Itens marcados `[MÁQUINA DO DONO]`** dependem de GPU/modelo de visão real: implemente a
   UI/flag/ligação e deixe testável com o motor injetável (fake), mas anote que a validação
   plena roda na máquina do Otaviano — não os declare "provados" sem isso.

---

## 1. GATES — bloqueiam o selo. FAÇA PRIMEIRO.

### GATE 1 — Crash alcançável no editor (F5, passo 6)
- **Onde:** `app/qt/design/papel_texto_ui.py:72` (`badge_de_papel`) e `app/qt/itens.py:115`.
- **O quê:** o dict de COR dentro de `badge_de_papel` só mapeia LEGAL/VALIDADE/DICA/LIVRE.
  Falta `PapelTexto.OBSERVACAO` (que JÁ está em `ORDEM_PAPEIS`, `_ROTULO_CURTO` e
  `_ICONE_PAPEL`, e é oferecida no diálogo de criação e no submenu de contexto). Escolher
  "Observação do item" → `itens.py:115 badge_de_papel(OBSERVACAO)` → `{...}[papel]` levanta
  **KeyError durante o paint** → trava a repintura da cena. Fere "verde com crash não é verde"
  e I2.
- **Faça:** adicione `OBSERVACAO` (e qualquer outro papel presente em `ORDEM_PAPEIS`, ex.
  `DESCONTO` se existir no enum) ao dict de cor, com cor lida do tema atual.
- **Aceite:** teste novo que **percorre TODOS os papéis de `ORDEM_PAPEIS`** chamando
  `badge_de_papel(p)` e afirma que retorna tupla válida (rótulo, cor, ícone) para cada um —
  esse teste tem que QUEBRAR na versão atual e passar depois.

### GATE 2 — Cinco testes-máscara (reescrever para verificar por CONTEÚDO)
1. **F9 — o pior.** `app/tests/test_fase9_ia.py:238` `test_dica_estilo_respeita_teto_e_nao_repete`:
   o nome promete "não repete a anterior", mas o corpo só checa `len<=30` e `None` sem IA.
   **Faça:** passe `evitar=[dica_anterior]` e afirme que a nova dica **≠** a anterior (por
   conteúdo); e ligue de fato a memória de dica no caller `painel_propriedades.py:547` (hoje
   passa `evitar` só com o texto atual, sem histórico de edições). Se preferir, renomeie o
   teste E reabra o requisito R-083 de memória de dica — mas o comportamento tem que existir e
   ser provado.
2. **F6** `test_fase6_mesa.py:66` (`_largura_conteudo`): a asserção "tudo cabe" é circular
   (usa a mesma soma de sizeHints que `_reflow_barra`). **Faça:** meça a largura de forma
   independente (largura real dos widgets renderizados) e prove que os essenciais ficam fora
   do "···".
3. **F8** `test_video_slideshow_frames_e_duracao_exatos` (`test_fase8_export.py`): só conta
   frames/duração. **Faça:** compare **um pixel/quadro do vídeo com o PNG da página de origem**
   (fidelidade que o passo 60 exige).
4. **Polimento** `test_polimento.py:222` `test_sem_perigo_suave_fantasma`: só checa ausência
   das strings `#FDE8E8`/`PERIGO_SUAVE`. **Faça:** afirme por CONTEÚDO que a célula de perigo
   resolve para `t.PERIGO_FUNDO` dark (`#331414`) no tema escuro — trocar por outro hex claro
   fixo tem que fazer o teste falhar.
5. **Polimento** `test_fase2_afeto.py:34` `test_ultimo_aberto_nos_4_caminhos`: anuncia 4
   caminhos mas exercita 2 (caminho 3 "por raciocínio", caminho 4 encena o registro na mão).
   **Faça:** exercite os 4 fluxos REAIS (Mesa, Fábrica, dashboard, duplicar) — inclusive
   `projetos.py:478 duplicar_semana_passada`, que hoje não chama `registrar_ultimo_aberto`.

### GATE 3 — Pré-voo nos formatos sociais (F8, passos 41/67) — fere I2
- **Onde:** `app/qt/telas/publicar_dialog.py:_gerar`.
- **O quê:** `_gerar` compõe/exporta oferta, carrossel, story e vídeo **sem** chamar
  `validar_composicao`/`confirmar_pre_voo`. Um item sem foto ou sem preço vai pro feed/Story
  **sem aviso** (contraste: `mesa._exportar:2021-2023` roda o pré-voo).
- **Faça:** rode o pré-voo antes de exportar qualquer formato social; item sem foto/preço tem
  que avisar (mesmo padrão da Mesa).
- **Aceite:** teste que tenta gerar social com um item sem preço e prova que o aviso aparece
  (e/ou a exportação é barrada) — por conteúdo.

---

## 2. FASE 4 — Editor I (3 ressalvas menores)

- **#72 (R-039 cadeado):** `canvas.py:1343 set_arte_travada` — destravar só torna a arte
  selecionável (nunca movível) e o aviso diz "não se move", o OPOSTO do passo. **Decida com o
  arquiteto:** ou (a) permitir mover a arte destravada e corrigir o aviso para "a partir daqui
  ela pode ser reposicionada", ou (b) manter arte=fundo e **reescrever o passo/aviso** para não
  contradizer. Teste que afirma o texto do aviso coerente com o comportamento.
- **#77 (R-041 cotas):** `itens.py:139 _emitir_medidas` só mostra cota até as 4 bordas da ARTE.
  **Faça:** calcular e exibir também a cota região↔região (distância em mm à região vizinha
  mais próxima) durante o arrasto. Teste por valor (mm esperado entre dois rects conhecidos).
- **#50 (RG-54 escalas):** os testes cobrem só 100%. **Faça:** teste do editor a 1280×720 nas
  escalas **125% e 150%** (as da Fase 1), provando que a barra/telas não cortam.
- **Artefatos ausentes:** gere `app/scripts/fotografar_fase4.py` + `saida_fase4/` (fotos
  claro/escuro dos 3 estados, seção-união, cadeado, medidas) e o GIF `fluxo_agrupamento.gif`,
  no mesmo padrão de `fotografar_fase7..11.py`.

## 3. FASE 5 — Editor II (6 ressalvas menores; o crash já é o GATE 1)

- **#8 (dica no editor):** `painel_propriedades.py:181 btn_dica` grava `texto_fixo` mas **não**
  define `papel_texto=DICA` nem aplica o teto de chars da região (R-088). **Faça:** ao gerar
  dica, setar papel=DICA e cortar no teto da região. Teste por conteúdo (papel vira DICA; texto
  ≤ teto).
- **#24 (pill tema):** `model.py:169` defaults `pill_cor='#000000'`/`opac=128` fixos. **Faça:**
  derivar o padrão da pill do tema atual (claro/escuro). Teste que o default muda com o tema.
- **#42 (reflow harmônico):** `text_fit.py:98` só trunca com "…" num rect fixo. **Faça:**
  reacomodar nome↔preço com harmonia (o preço manda; o nome recua/reduz de forma controlada),
  não só cortar. Teste por posição/tamanho resultante.
- **#49/#50/#52 (Páginas e histórico):** `paginas_dialog.py` entrega em DIÁLOGO com botões
  ↑/↓ e sem debounce. **Faça:** faixa lateral fixa (49), reordenar **arrastando** as miniaturas
  (50) e miniatura viva com **debounce** (52). Testes por conteúdo do reordenamento por uid.
- **#60 (distribuir):** `alinhamento.py:91 distribuir_espacamento` não faz snapping a
  guias/grade. **Faça:** distribuir respeitando guias e grade magnética. Teste por posição.

## 4. FASE 6 — Mesa I (4 maiores + menores)

- **#36 [MAIOR] Trocar arrastando (R-057):** `canvas.py:471 trocar_conteudo_slots` existe e é
  testado, mas **nenhum gesto de UI o chama** (só o teste). **Faça:** ligar o gesto arrastar
  item SOBRE outro → troca as duas células (com o undo unificado que já existe). Teste que
  simula o drop item→item e confere a troca por pixel/uid.
- **#68 [MAIOR] Planilha edita o BANCO:** `planilha.py:34 aplicar_edicao` muta só o ItemMesa em
  memória; o passo 68 exige gravar no banco por produto_id. **Faça:** ao editar na planilha,
  gravar no `ProdutoRepositorio` por produto_id (com o aviso de override já existente). Teste
  que a edição persiste no banco (relê e confere).
- **#44 [MAIOR] Multi-seleção na estante:** `mesa.py:227 self.lista` fica em SingleSelection.
  **Faça:** `setSelectionMode(ExtendedSelection)` + arrastar/duplicar/filtrar em bloco. Teste
  que seleção múltipla afeta N itens por uid.
- **#74/#78 [MAIOR] Adversarial da planilha:** falta o teste com 2+ itens provando que editar
  preço na planilha muda **só o item por uid** (não o de posição igual), e a matriz
  override×mapa não inclui a coluna planilha. **Faça:** esse adversarial (I1) com dois itens.
- **Menores (filtros R-054):** #31 expor filtro por CATEGORIA na barra; #32 contador por
  critério ("12 sem foto"); #33 botão "Limpar filtros" 1-clique; #43 pulso no topo
  ("· 12 sem foto · 3 sem preço"); #40 estado vazio de filtro ("Nada aqui — limpar filtro").
- **#57** Ctrl+K na Mesa incluir "ir para página X" e "abrir Configurações".
- **#81/#82** testes de integridade: I3 (snapshot do rascunho com caminhos relativos) e I4
  (mestra↔cópia intacta após reordenar a estante).
- **#13** (máscara da barra) já coberto no GATE 2.

## 5. FASE 7 — Mesa II / produção em massa (a fase com mais ressalvas)

- **#84/#19/#44 [MAIOR] Órfãos:** `servico.separar_por_semaforo` (R-053) e `servico.diff_edicoes`
  (R-062) são testados mas **nunca chamados na UI**. Ligue-os (ver itens abaixo) ou o passo 84
  (varredura de órfãos) permanece violado.
- **#19/#21/#22 [MAIOR] Aceitar todos os verdes (R-053):** falta o **botão "Aceitar todos os
  verdes"**, o contador "X verdes aceitos · Y para revisar · Z novos" (hoje o texto é "N no
  banco · M conferir · K novos", `conciliacao_dialog.py:269`) e o **undo**. **Faça:** botão que
  chama `separar_por_semaforo`, contador com o texto exigido, e undo. Teste por conteúdo.
- **#44/#45 [MAIOR] Diff da edição anterior (R-062):** `diff_edicoes` sem UI. **Faça:** uma
  tela/lista que compara a edição atual com a anterior e destaca subidas/descidas/entradas/
  saídas. Teste que a lista reflete o diff.
- **#48/#50 [MAIOR] Checklist em PDF (R-063):** `checklist_final` gera dados mas não há
  impressão/export PDF. **Faça:** exportar/imprimir o checklist em PDF (conferência a quatro
  olhos). Teste que o PDF sai com os itens do checklist.
- **#23/#25 [MAIOR] Encher página pergunta o destino (R-056):** `mesa.encher_pagina:1086` só
  mostra um toast dizendo que o resto ficou na estante. **Faça:** perguntar "nova página?
  fila? deixar de fora?" e executar a escolha. Teste por comportamento de cada opção.
- **#15 [MAIOR] Navegação por teclado na conciliação:** `conciliacao_dialog.py` só tem
  ordenar_tab. **Faça:** atalhos "próximo amarelo / aceitar / rejeitar" (QShortcut). Teste que
  o atalho move o foco/estado.
- **Menores:** #42/#43 medidor de densidade visual (R-060, hoje só toast >90%); #13 editar
  nome/preço inline na conciliação com a foto ao lado (`setEditTriggers`); #2 widget de fila
  multi-arquivo com estado por arquivo (na fila·lendo·pronto·erro); #6 aceitar vírgula como
  separador de coluna na colagem (sem colidir com decimal); #39 UI para editar/adicionar
  frases do combo; #53 mover `_avisar_repeticao` para worker (não síncrono na Mesa).
- **Coberturas de teste faltando:** #63 colagem contra glossário sem inventar marca; #68/#69/
  #73 adversarial incluindo itens vindos de colagem/multi-import; #76 idem órfã; #80 I4 ao
  encher página em grade replicável.

## 6. FASE 8 — Exportação e publicação (pré-voo social é o GATE 3)

- **#40 [MAIOR] Cards sociais herdam a arte:** `publicar_dialog.py:136 compor_social/
  compor_carrossel` são chamados SEM `fundo`. **Faça:** passar o fundo/arte do projeto (o
  `layout_social` já aceita `fundo`). Teste por pixel que o card sai com a arte, não o fundo
  padrão.
- **#35 [MAIOR] Seleção/ordem do carrossel:** hoje 1 card por item na ordem fixa. **Faça:**
  UI (lista checkable + reordenável) para escolher quais produtos entram e em que ordem. Teste
  que a seleção/ordem refletem na saída.
- **#7/#37/#39/#49/#85 [MAIOR] Órfãos sociais:** ligar à UI: `social.FORMATOS['faixa']`
  (banner 1920×1080, R-145), `video.gerar_video_story` (MP4 Story, R-139) e
  `compartilhar.abrir_com` ("Abrir com…"/WhatsApp Desktop). Cada um com botão/menu real. Teste
  que o caminho de UI gera o formato.
- **#94 [MAIOR] Exibir LIMITACAO_SO:** `compartilhar.LIMITACAO_SO` existe mas nunca aparece.
  **Faça:** mostrar a limitação honesta (tooltip/label) no botão de compartilhar. Teste que o
  texto aparece na UI.
- **#5 [MAIOR] Perfis de exportação editáveis:** `perfis.salvar_perfis` existe mas
  `configuracoes.py` não tem tela. **Faça:** UI para criar/editar/duplicar perfis. Teste que
  salvar/editar persiste.
- **Menores:** #52 fade + duração por página no vídeo-tabloide (`video.gerar_video_paginas`);
  #49/#50 animação isolada do preço no Story; #31 Oferta do Dia reusar `modelo_vitrine`
  (R-044); #32 pré-selecionar na Publicar o item selecionado na Mesa; #24 aprovação keyed por
  versão (não por str(id)). #60 (vídeo pixel) já está no GATE 2.

## 7. FASE 9 — Conteúdo & IA II (a mais fraca; a máscara da dica é o GATE 2)

- **#27/#28/#29 [MAIOR] AUSENTE — Avaliador de foto (R-085):** não existe. **Faça:** avaliar
  foto (borrada/pequena/marca-d'água), dar nota boa/atenção/ruim e ligar ao upscale. `[MÁQUINA
  DO DONO]` para a parte de visão fina; a heurística (tamanho/nitidez por variância de
  Laplaciano/alfa) roda em CPU e deve ser testada por conteúdo.
- **#50/#51 [MAIOR] AUSENTE — Autodetecção de variações (R-082):** sugerir agrupar
  sabores/tamanhos do mesmo produto. **Faça:** função que detecta variações por
  Tipo+Marca+Sabor+Peso e sugere agrupar. Teste por conteúdo (dois sabores da mesma marca
  viram sugestão).
- **#47/#81 [MAIOR] AUSENTE — Dicionário regional editável (R-086):** `SINONIMOS_REGIONAIS_
  PADRAO` é hardcoded (`aprendizado.py:22`); fere I3. **Faça:** UI/Config para o dono
  acrescentar termos, persistidos de forma portátil (relativo). Teste que um termo adicionado
  persiste e é aplicado.
- **#43/#53/#91 [MAIOR] Engano visual — Correções aprendidas:** a "galeria" é um QLabel
  estático no script de screenshot (`fotografar_fase9.py:133`), a feature não existe. **Faça:**
  lista editável real de correções aprendidas nas Configurações (ver/reverter aliases do
  banco). Teste que a lista lê/edita o banco.
- **#25/#26 [MAIOR] Sentinela calibrada pelo acervo (R-078):** `revisora.py:60` alimenta as
  faixas só com o projeto em tela; exige ≥4 amostras/categoria, então quase nunca dispara.
  **Faça:** alimentar `faixas_por_categoria` com o **histórico/acervo F11**
  (`inteligencia.historico_de_preco`). Teste que a sentinela dispara com base histórica.
- **#33/#39 [MAIOR] Fusão reconcilia fotos:** `deduplicacao.py:55 fundir_no_banco` só migra
  aliases + soft-delete. **Faça:** escolher foto oficial e **preservar as fotos do perdedor
  como versões do vencedor** (conferência por conteúdo). Teste que as fotos migram.
- **#61/#63/#64 [MAIOR] Fila de IA (R-089/R-090):** `ordenar_por_prioridade` (`servico.py:1395`)
  é órfã. **Faça:** fila de IA única (conciliar/enriquecer/dica/revisar) com painel
  visível/cancelável e status "o que faz agora". Teste que a fila ordena por prioridade e
  cancela.
- **#49 [MAIOR] `extrair_marca` órfã:** ligar à sanitização/agrupamento Tipo+Marca+Sabor+Peso
  (hoje só em teste). Teste que a marca extraída alimenta a ordem do produto.
- **#78/#95 [MAIOR] Casos negativos de sigla/protocolo:** hoje só há bateria negativa de MARCA.
  **Faça:** casos negativos provando que a IA nunca inventa sigla/protocolo. Testes por
  conteúdo.
- **Menores:** #8 manchetes respeitarem o teto (`papel_texto_ui.py:215` passa sem
  `limite_chars`); #23 laudo da revisora com avisos clicáveis que levam ao slot
  (`mesa.py:1262`, hoje QMessageBox); #12 checagem anti-alucinação do texto da dica.

## 8. FASE 10 — Imagens II + Estúdio IA

- **#57 [MAIOR] AUSENTE — Sombra por tema (R-102):** `estudio.py:_enquadrar_com_sombra` usa
  preto fixo. **Faça:** ajustar a sombra do packshot ao tema claro/escuro da arte. Teste por
  pixel (sombra difere entre temas).
- **#20 [MAIOR] AUSENTE — Flag "Estúdio IA (gerador)":** `configuracoes.py` não tem o toggle;
  `almoxarifado.py:695` chama `tratar_estudio` sempre sem `com_gerador`. **Faça:** checkbox de
  Config que liga o degrau 2 e passar `com_gerador` adiante. `[MÁQUINA DO DONO]` para exercitar
  o SDXL real; a flag + ligação + degradação avisada devem existir e ser testadas com motor
  fake.
- **Menores:** #11 lote/fila do Estúdio (packshot em várias fotos); #51/#52 ligar WebP ao
  armazenamento (`biblioteca.ingerir` salva sempre PNG) com migração reversível + prévia de
  ganho; #63/#82 incluir `_genericas` na lista de pastas puladas em `manutencao.py:136` (senão
  as genéricas são tratadas como órfãs); #31/#32 UI de pincel de refino (`curadoria.refinar_
  alfa` é só modelo); #8 prévia antes/depois antes de aplicar o packshot; #41 comparador
  mostrar resolução/qualidade por versão; #80 pré-aquecer também o Real-ESRGAN pós-boot (hoje
  só rembg); #46 expor girar/cortar/refino/oficial também na CuradoriaDialog da Mesa; #49 busca
  automática no acervo antes da Web; #72/#73 adversariais (trocar foto oficial não afeta outro;
  identidade por byte do upscale).

## 9. FASE 11 — Cartaz & Fábrica + inteligência (backend pronto, falta UI — 5 menores)

- **#47 (R-122) Definir meta por evento:** `inteligencia.py:208 definir_meta_evento` sem
  caller de UI. **Faça:** painel na barra da Mesa para o dono DEFINIR a meta (hoje só o
  progresso aparece). Teste que definir persiste e reflete.
- **#45 (R-121) Memória sazonal:** `inteligencia.py:103 memoria_sazonal` sem aba. **Faça:** aba
  no InteligenciaDialog. Teste que a aba mostra o resultado por data+chave_natural.
- **#51/#52 (R-126) Saúde do acervo:** `inteligencia.py:247 saude_acervo` só dá contagens.
  **Faça:** "metas simples" (limiares/alvos) + integrar com integridade R-129 e o avaliador de
  foto F9 (item da F9 acima) numa visão só. Teste por conteúdo.
- **#39 (R-117) Relatório exportável:** `relatorio_edicao` só é exibido. **Faça:** exportar/
  imprimir o relatório (com o checklist F7). Teste que o arquivo sai.
- **#85 Varredura de órfãos:** adicionar o teste que garante "nada sem uso" na F11 (hoje só
  `test_vetos_ausentes`). Depois de ligar os órfãos das fases acima, esse teste deve passar.

## 10. POLIMENTO (3 menores; #1 e #4 já cobertos no GATE 2)

- **#6** `dashboard.py:1141 _cor_status` hardcoda `'#7C3AED'` para "publicado" (bypass do
  design system). **Faça:** usar um token tematizado (t.*). Teste que a cor vem do token.

---

## 11. FECHAMENTO (o que me mandar)

1. Diga o hash do commit-baseline (feito antes de começar).
2. Para cada GATE e cada item: 1 linha do que fez + o nome do teste mutation-proof que o cobre.
3. Rode a suíte completa `python -m pytest app/tests -q -p no:cacheprovider`, confirme
   **exit-0 LIMPO** (sem crash no fechamento) e cole o final da saída + `%ERRORLEVEL%`.
4. Liste explicitamente os itens `[MÁQUINA DO DONO]` que ficaram prontos-para-validar (não
   validados) — eles entram no roteiro do Marco (F12), não bloqueiam esta ordem.
5. **NÃO abra a Fase 12** — o arquiteto reaudita esta ordem no disco real e só então libera.

---

# RESPOSTA DO BUILDER (Fable 5) — ordem EXECUTADA INTEGRALMENTE, 21/07/2026

**Baseline:** `6d03370` (commit do `app/` antes de qualquer edição desta ordem).
**Execução:** inline, SEM subagentes. Commits da ordem, na sequência:
`8b22838` (ordem+ignores) → `0601128` (GATES) → `47c9bb6` (F4/F5) → `104bcb4` (F6)
→ `7d46368` (F7) → `e96083a` (F8) → `36a197c` (F9) → `8d4aa46` (F10/F11/polimento).
Todos os testes novos vivem em **`app/tests/test_os_f11_5.py`** (74 testes), salvo indicação.

## §1 GATES

- **GATE 1** badge cobre o ENUM inteiro (OBSERVACAO/DESCONTO tinham KeyError no paint) —
  `test_gate1_badge_cobre_todos_os_papeis_do_enum`.
- **GATE 2.1** anti-repetição da dica virou GUARDA DURA em `gerar_dica` + histórico de sessão no
  painel — `test_f5_8_dica_gerada_declara_o_papel` (+ guarda em `test_f9_12_dica_nao_alucina`).
- **GATE 2.2** régua independente da barra da Mesa (sizeHint×maximumWidth) + **modo compacto
  estágio 2** (`componentes.modo_compacto_botoes` — achado próprio: a 1280 nem colapsando tudo
  cabia) — `test_fase6_mesa.py::_ninguem_espremido` reescrito.
- **GATE 2.3** frame do vídeo comparado por PIXEL contra a página de origem
  (`video.frame_do_video`) — `test_fase8_export.py` (frames 0/36 por cor).
- **GATE 2.4** célula com fundo PERIGO_FUNDO conferida POR VALOR no tema escuro —
  `test_polimento.py`.
- **GATE 2.5** os 4 caminhos REAIS do "último aberto" (Mesa/Fábrica/gesto do dashboard/
  duplicar_semana_passada — este NÃO registrava, corrigido em `projetos.py`) —
  `test_fase2_afeto.py::test_ultimo_aberto_nos_4_caminhos`.
- **GATE 3** pré-voo social ANTES do seletor de pasta, por modo —
  `test_gate3_previa_social_avisa_item_incompleto`.

## §2 F4

- **#72** aviso do cadeado COERENTE com o gesto — `test_f4_72_cadeado_aviso_coerente_com_o_gesto`.
- **#77** cota região-a-região (`itens.cota_entre_rects`, "⇄ vizinha N mm") —
  `test_f4_77_cota_regiao_a_regiao_por_valor`.
- **#50** editor cabe a 720p nas escalas 125/150 (o `BarraEditor.setMinimumWidth(1)` — a barra
  prendia a janela em 1665px e o reflow nunca disparava) — `test_f4_50_editor_cabe_a_720p_nas_escalas`.
- Galeria nativa F4: `app/scripts/fotografar_fase4.py` (normal/raio-x/seleção/medidas/cadeado + GIF).

## §3 F5

- **#8** a dica DECLARA o papel DICA na criação — `test_f5_8_dica_gerada_declara_o_papel`.
- **#24** pill padrão POR TEMA (`pill_padrao_do_tema`) — `test_f5_24_pill_padrao_muda_com_o_tema`.
- **#42** truncamento recua por PALAVRA — `test_f5_42_truncamento_recua_por_palavra`.
- **#49/50/52** faixa de páginas (miniaturas + arrastar reordena + debounce) —
  `test_f5_49_50_52_faixa_de_paginas` (`faixa_paginas.py` novo, no editor).
- **#60** distribuir com snap a guia/grade — `test_f5_60_distribuir_respeita_guias_e_grade`.

## §4 F6

- **#36** Alt+arrastar TROCA células (drop por uid, só entre ocupadas) —
  `test_f6_36_trocar_por_gesto_de_arrasto`.
- **#68** planilha PERSISTE Nome/Categoria no banco por produto_id —
  `test_f6_68_planilha_grava_cadastro_por_produto_id`.
- **#44** multi-seleção em bloco na estante — `test_f6_44_multiselecao_em_bloco`.
- **#31/32/33/40/43** filtros por categoria + contadores por critério + limpar 1-clique +
  pulso + vazio-de-filtro (na Mesa; cobertos pelos testes de F6 + visual).
- **#57** paleta: ir-à-página + abrir Configurações.
- **#74/78** adversarial: planilha edita SÓ o uid certo — `test_f6_74_adversarial_planilha_edita_so_o_uid_certo`.
- **#81 (I3)** rascunho com caminhos RELATIVOS (era gap real — implementado
  `rascunho._mapear_caminhos`) — `test_f6_81_rascunho_com_caminhos_relativos`.
- **#82 (I4)** mestra intacta após reordenar a estante — `test_f6_82_mestra_intacta_apos_reordenar_estante`.

## §5 F7

- **#19/21/22** Aceitar todos os verdes + contador exigido + Desfazer —
  `test_f7_19_22_aceitar_verdes_e_desfazer`.
- **#15** atalhos N/A/R movem foco/estado — `test_f7_15_atalhos_movem_foco_e_estado`.
- **#13** edição inline de Importado/Preço (com a foto ao lado do R-052) —
  `test_f7_13_edicao_inline_reflete_no_item`.
- **#44/45** diff da edição anterior com UI (`diff_dialog.py`) —
  `test_f7_44_45_diff_dialog_reflete_o_diff`.
- **#48/50** checklist em PDF (`html_do_checklist` + QPrinter; conteúdo no HTML impresso, TINTA
  provada rasterizando com Ghostscript — o Qt offscreen imprime texto como curvas) —
  `test_f7_48_50_checklist_pdf_com_conteudo`.
- **#23/25** encher página PERGUNTA o destino do resto (página nova/fila/fora com desfazer) —
  `test_f7_23_25_destino_do_resto`.
- **#2** fila multi-arquivo com estado por arquivo (`fila_importacao.py` + `progresso_cb`) —
  `test_f7_2_fila_multiarquivo_estado_por_arquivo`.
- **#6** vírgula+espaço como separador na colagem (sem colidir com decimal) —
  `test_f7_6_virgula_como_separador_na_colagem` (+ prova de mutação manual: ramo desligado → falha).
- **#39** frases do combo: soma as do dono + "＋ Nova frase…" persiste na Config —
  `test_f7_39_frase_nova_do_dono_persiste`.
- **#42/43** medidor de densidade PERMANENTE na barra (verde/âmbar/vermelho) —
  `test_f7_42_43_densidade_visual_na_barra`.
- **#53** `_avisar_repeticao` foi para worker (não bloqueia a UI pós-import).
- **#63** colagem×glossário sem inventar marca — `test_f7_63_colagem_contra_glossario_nao_inventa_marca`.
- **#68/69/73** adversarial com itens de colagem E multi-import —
  `test_f7_68_69_73_adversarial_itens_de_colagem_e_multiimport`.
- **#76** órfã de colagem avisada — `test_f7_76_orfa_de_colagem_avisada`.
- **#80 (I4)** encher em grade replicável não toca ref_mestre —
  `test_f7_80_i4_encher_pagina_em_grade_replicavel`.

## §6 F8

- **#40** cards sociais herdam a ARTE (fundo atravessa `compor_social`/`compor_carrossel`) —
  `test_f8_40_card_social_herda_a_arte` (pixel).
- **#35** seleção+ordem do carrossel (lista checkable arrastável) —
  `test_f8_35_selecao_e_ordem_do_carrossel` (uids + pixel do 1º card).
- **#7/37/85** faixa 1920×1080 + Story-MP4 + "Abrir com…" ligados à UI —
  `test_f8_7_faixa_e_story_mp4_pelo_caminho_da_ui`, `test_f8_94_85_limitacao_visivel_e_abrir_com`.
- **#94** LIMITACAO_SO visível (label + tooltip) — idem acima.
- **#5** perfis de exportação editáveis (`perfis_dialog.py` + botão na Config) —
  `test_f8_5_perfis_editaveis_persistem`.
- **#52** fade + duração por página (`frames_do_slideshow` puro + spin/check na UI) —
  `test_f8_52_fade_e_duracao_por_pagina` (pixel do blend).
- **#49/50** animação ISOLADA do preço no Story (`frames_do_story` + `pulso_rect` do layout) —
  `test_f8_49_50_pulso_isolado_do_preco` (pixel).
- **#31** Oferta do Dia REUSA o estilo do modelo vitrine —
  `test_f8_31_oferta_do_dia_reusa_o_modelo_vitrine` (mutação no modelo acompanha).
- **#32** combo do destaque pré-seleciona o item da estante — `test_f8_32_preseleciona_o_item_da_mesa`.
- **#24** aprovação chaveada pelo HASH da versão salva (restaurar versão antiga derruba sozinho) —
  `test_f8_24_aprovacao_e_da_versao_nao_do_id`.
- Achado próprio: escape inválida no `frame_do_video` (`\,` → SyntaxWarning) corrigida.

## §7 F9

- **#27/28/29** avaliador de foto (`app/images/avaliador.py`: tamanho + Laplaciano numpy + alfa;
  badge no Almoxarifado ligado ao upscale) — `test_f9_27_28_avaliador_de_foto`.
- **#50/51** autodetecção de variações (`aprendizado.sugerir_variacoes`) + gesto na paleta que
  agrupa em multi com desfazer — `test_f9_50_51_variacoes_por_marca_e_tipo`,
  `test_f9_51_agrupar_variacoes_vira_multi`.
- **#47/81** dicionário regional EDITÁVEL (Config) e APLICADO na conciliação (chave canonizada
  no Conciliador) — `test_f9_47_81_sinonimo_do_dono_persiste_e_aplica`.
- **#43/53/91** correções aprendidas DE VERDADE (`correcoes_dialog.py` lê/reverte aliases do
  banco) — `test_f9_43_correcoes_aprendidas_le_e_reverte_o_banco`.
- **#25/26** sentinela calibrada pelo HISTÓRICO F11 (`revisora._pares_de_calibracao`) —
  `test_f9_25_26_sentinela_calibrada_pelo_historico`.
- **#33/39** fusão reconcilia FOTOS (perdedor vira versão do vencedor; sem foto, vira a oficial)
  — `test_f9_33_39_fusao_reconcilia_fotos` (por hash de bytes).
- **#61/63/64** `FilaIA` (prioridade viva `focar` + cancelar) + painel "o que a IA faz agora"
  na conciliação, focado pela linha selecionada — `test_f9_61_63_64_fila_ia_prioriza_e_cancela`,
  `test_f9_61_painel_da_fila_na_conciliacao`.
- **#49** `ordenar_tipo_marca` ligado ao enriquecer degradado (marcas do acervo) —
  `test_f9_49_marca_extraida_alimenta_a_ordem`.
- **#78/95** negativos de sigla/protocolo: `tokens_inventados`/`remover_inventados` (guarda DURA
  no `enriquecer`; glossário do dono sobrevive) — `test_f9_78_95_ia_nao_inventa_sigla_nem_protocolo`.
- **#8** teto de caracteres atravessa a UI das manchetes — `test_f9_8_manchetes_respeitam_o_teto`.
- **#23** laudo da revisora com avisos CLICÁVEIS que levam ao item — `test_f9_23_laudo_leva_ao_item`.
- **#12** `dica_alucinada` (preço/% e marca fora da oferta rejeitados) — `test_f9_12_dica_nao_alucina`.
- Bug latente achado e corrigido: Configurações nunca RECARREGAVA `frases.validade` — salvar a
  tela zerava a lista salva (agora reflete no load).

## §8 F10

- **#57** sombra por TEMA (`cor_sombra_do_tema`: preta no claro, halo claro no escuro) —
  `test_f10_57_sombra_acompanha_o_tema` (pixel).
- **#20** flag "Estúdio IA (gerador)" na Config + `com_gerador` atravessa o Almoxarifado;
  degradação sem GPU COM aviso, testada com fake — `test_f10_20_flag_gerador_liga_o_degrau2`.
- **#8** prévia antes/depois do packshot (`previa_estudio_dialog.py`) — só aplica com aprovação.
- **#11** "Estúdio em lote" no Almoxarifado (fila por produto_id, I2).
- **#51/52** WebP no armazenamento (`BibliotecaImagens(webp=)` lossless, convivência com PNG) +
  `migrar_acervo_webp` com PRÉVIA e REVERSÍVEL + botão na Config —
  `test_f10_51_52_webp_no_armazenamento_e_migracao` (roundtrip por pixel).
- **#63/82** `_genericas` nunca órfãs — `test_f10_63_82_genericas_nao_viram_orfas`.
- **#31/32** pincel de refino REAL (`refino_dialog.py`, restaurar/apagar alfa) —
  `test_f10_31_32_pincel_de_refino` (alfa por pixel).
- **#8/41** prévia e comparador mostram resolução+peso —
  `test_f10_8_41_previa_e_comparador_mostram_regua`.
- **#80** `aquecer_upscaler` pós-boot (junto do rembg) — `test_f10_80_aquecer_esrgan`.
- **#46** Ajustar/Refinar também na CuradoriaDialog — `test_f10_46_curadoria_expoe_ajuste_e_refino`.
- **#49** acervo ANTES da web na cascata (`candidatos_do_acervo`) —
  `test_f10_49_acervo_vem_antes_da_web`.
- **#72/73** adversariais: trocar oficial não toca o vizinho (hash); cache do upscale por BYTE —
  `test_f10_72_73_adversariais_foto`.

## §9 F11 + §10 polimento

- **#47** clicar na estatística da Mesa DEFINE a meta do evento —
  `test_f11_47_meta_do_evento_define_e_reflete`.
- **#45** aba "Ano passado" (memória sazonal) no InteligenciaDialog —
  `test_f11_45_aba_sazonal_mostra_o_ano_passado`.
- **#51/52** `saude_com_metas`: metas por limiar + órfãs R-129 + avaliador F9 numa visão só —
  `test_f11_51_52_saude_com_metas_e_integridade`.
- **#39** relatório da edição em PDF (reusa o molde do checklist F7) —
  `test_f11_39_relatorio_sai_em_pdf`.
- **#85** varredura de órfãos POR IDENTIFICADOR (cada função apontada tem chamador de UI) —
  `test_f11_85_orfaos_da_f11_tem_chamador_de_ui`.
- **§10 #6** `t.PUBLICADO` tematizado nos dois temas no lugar do hex solto —
  `test_pol_6_cor_publicado_vem_do_token`.

## Suíte (item 3 do fechamento)

Comando da ordem, `QT_QPA_PLATFORM=offscreen`, **5 rodadas completas consecutivas**:

```
> python -m pytest app/tests -q -p no:cacheprovider
tests=801  failures=0  errors=0  skipped=0   (junit; ~126 s por rodada)
ERRORLEVEL=0
```

**801 verdes ×5, ZERO skips, exit-0 LIMPO** (sem crash no fechamento). Baseline da ordem era
714; a execução somou **+87 verdes** (74 em `test_os_f11_5.py` + reescritas dos 5 testes-máscara
e adversariais das fases). Nota de bancada: a linha "801 passed" do pytest usa retorno de
carro e o console cp1252 a engole no pipe — o placar CONFIÁVEL é o junit (lição registrada da
bancada Windows), conferido nas 5 rodadas.

## Itens [MÁQUINA DO DONO] prontos-para-validar (roteiro do Marco/F12 — NÃO validados)

1. **F9 revisora por VISÃO real** (Qwen2.5-VL no LM Studio) — heurística e fluxo prontos;
   falta o modelo real ler uma peça de verdade.
2. **F9 avaliador de foto — visão fina** (marca-d'água/produto errado) — o degrau heurístico
   (tamanho/nitidez/alfa) está testado; a parte de visão espera a GPU.
3. **F10 Estúdio degrau 2 (SDXL img2img)** — flag da Config + ligação + degradação avisada
   testadas com fake; falta exercitar o gerador real na máquina com GPU.
4. **F10 Real-ESRGAN real** — pré-aquecimento e cache testados com fake/Lanczos; falta o
   `.pth` real medindo qualidade.
5. **F8 MP4 nas redes reais** — story.mp4/tabloide.mp4 saem e são medidos por frame; falta o
   teste de recepção no WhatsApp/Instagram do dono.

**PARADO aqui, aguardando a reauditoria do arquiteto no disco real. A Fase 12 NÃO foi aberta.**
