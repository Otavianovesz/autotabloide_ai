# FASE 2 — O Início revolucionado (caderno de 100 passos)

> Formato-lei do PLANO_PERFEITO. Cobre RG-50, R-152, R-001–R-012.
> **SELO DA FASE 1 (18/07, arquiteto):** inspeção visual feita — cartão-postal,
> Mesa escura e amostras das pastas aprovados; 410 verdes ×2 aceitos; os 8
> achados de bancada lidos; a ambiguidade do ícone (A×B) foi levada ao dono.

## SELO DO ARQUITETO — FASE 2 (18/07/2026): APROVADA COM RESSALVA VISUAL

Inspeção visual feita: `inicio_final_claro.png` (3 zonas vivas — saudação
por hora, data por extenso, busca, filtros Todos/Rascunhos/…, cartões de
evento com faixa de cor e contagem, indicadores de saúde no rodapé) e
`apresentacao_1.png` (tela cheia digna, navegação, aviso honesto). As
FUNÇÕES estão todas de pé e provadas: evento-entidade com migração por
conteúdo, status por hash, versões que nunca sobrescrevem, busca global,
lixeira 30 dias, duplicar-semana-passada. **428 verdes ×2, adversariais
16/16. Selo concedido.**

**RESSALVA (vira RG-59, refinada na Fase 5-UI ou antes se o dono quiser):**
os cartões de evento têm MUITO espaço vazio — a miniatura fica pequena e
centralizada num retângulo largo. O dono pediu "muito mais bonito e
elaborado". Alvo: capa preenchendo a largura do cartão (cover), overlay
com gradiente e o nome sobre a imagem, contagem/data como chips, altura
menor e mais densidade. NÃO bloqueia a Fase 2 (é polimento estético sobre
função pronta), mas é prioridade da próxima passada visual.

## Bloco A — Evento vira cidadão de primeira classe (passos 1–14)
**Por quê:** hoje "evento" é um texto solto no projeto. O Início sonhado
(cartões com cor, capa, dia da semana, agenda) exige o Evento como entidade
— com migração dos textos existentes, sem perder nada.

1. Modelo `Evento` em models.py: id, nome único, cor (hex), capa (caminho relativo opcional), dia_semana (0–6 ou None), ordem, notas (texto), criado_em.
2. Tabela nova via metadata + entrada no `_COLUNAS_NOVAS` se precisar de coluna em `projetos_salvos` (campo `evento_id` FK opcional — o texto `evento` FICA para compat).
3. Migração na abertura: cada `evento` texto distinto dos projetos vira linha em `Evento` (cor sorteada de paleta fixa por hash do nome — estável), `evento_id` preenchido.
4. Projetos novos gravam `evento_id` E o texto (redundância de leitura barata; a verdade é o id).
5. Serviço headless `app/qt/telas/eventos.py`: listar, criar, renomear, mudar cor, definir capa (internada em `layouts/capas/`, relativa — I3), definir dia_semana, reordenar, notas.
6. Excluir evento: só se vazio OU movendo os projetos para outro (diálogo com verbo; nunca órfão silencioso).
7. `dia_semana` alimenta o RG-24 existente (datas inteligentes leem do Evento; a Config antiga vira fallback).
8. Capa padrão quando não definida: miniatura do projeto mais recente do evento.
9. "Novo evento" (botão que a Fase 1 criou) abre diálogo: nome, cor (paleta de 12), dia da semana opcional, capa opcional.
10. Botão direito no cartão do evento: Renomear · Cor · Capa · Dia · Notas · Excluir.
11. Teste: migração de banco com 3 eventos-texto → 3 Eventos com projetos ligados.
12. Teste: excluir movendo projetos preserva todos (contagem por conteúdo).
13. Teste: capa internada relativa; banco sem caminho absoluto (I3).
14. **Checagem:** suíte parcial verde; screenshot do diálogo Novo evento (claro+escuro) em `saida_fase2/`.

## Bloco B — A nova cara do Início (passos 15–34)
**Por quê:** "o Início é a cara do programa" — painéis, não lista. O layout:
faixa-topo com saudação e busca; "PRODUZIR HOJE" quando for dia de campanha;
grade de CARTÕES DE EVENTO (capa, cor, contagem, último projeto); Avulsos ao
fim. Denso, bonito, animado (motor da Fase 1).

15. Reestruturar `dashboard.py` em 3 zonas: topo (saudação + data + busca), destaque ("Produzir hoje"/"Esta semana"), grade de eventos.
16. Topo: "Boa tarde, Otaviano" (hora do sistema), data por extenso PT-BR, campo de busca global (Bloco F) à direita.
17. Zona destaque: se HOJE é dia_semana de algum Evento → cartão grande "Produzir hoje: [Evento]" com botão primário "Duplicar semana passada" (Bloco I) e "Começar do zero".
18. Sem campanha hoje → mostra "Esta semana" (próximos dias com evento, em chips clicáveis).
19. Cartão de evento: capa (ou miniatura), barra da cor, nome, contagem de projetos, data do último, botão "abrir" no hover (elevação da Fase 1).
20. Clique no cartão → visão do evento: projetos do evento em grade (a antiga prateleira, agora por dentro do cartão), com voltar.
21. "Ofertas da semana" (★): cartão fixo antes dos eventos com os projetos dos últimos 7 dias, qualquer evento.
22. Avulsos: cartão neutro ao fim (projetos sem evento).
23. Grade responsiva: 2 colunas a 1280, 3 a 1600+; cartões com mínimo 320 px (tokens da Fase 1).
24. Skeleton da grade no carregamento (componente da Fase 1).
25. Estado vazio do Início zero-projetos: hero de boas-vindas com os 3 cartões-ação (já existem — integrar).
26. Ações rápidas (Novo tabloide/cartaz/layout/evento) permanecem no topo, à direita da saudação.
27. Duplo-clique em projeto continua abrindo Mesa/Fábrica (nada regride).
28. Botão direito do projeto: adicionar "Mover para evento…" (lista de eventos).
29. Contexto visual: chip do status do projeto no cartão (Bloco C) — cinza rascunho, azul pronto, verde exportado, roxo publicado.
30. Fotos: Início novo claro+escuro, com 0, 1 e 4+ eventos (6 capturas).
31. Animações: entrada da grade em fade escalonado (60 ms entre cartões; helper novo `cascata()` no motor).
32. Teste: dashboard monta com 0/1/N eventos sem erro (smoke por estado).
33. Teste: "Produzir hoje" aparece exatamente quando `hoje.weekday() == evento.dia_semana`.
34. **Checagem:** suíte parcial + as 6 fotos inspecionáveis.

## Bloco C — Status do projeto e agenda da semana (passos 35–46)
**Por quê:** o dono quer ver a semana: o que está rascunho, pronto,
exportado, publicado — sem abrir projeto por projeto.

35. Coluna `status` em `projetos_salvos` via `_COLUNAS_NOVAS` (default "rascunho").
36. Transições automáticas: exportar PNG/PDF marca "exportado" (uma vez); salvar depois de exportado volta a "pronto"? NÃO — vira "rascunho" apenas se o conteúdo mudou (hash do estado_slots); documentar no código.
37. Ações manuais no botão direito do projeto: "Marcar como pronto" · "Marcar como publicado" (publicado é gesto humano — enviou no WhatsApp).
38. Chip de status no cartão do projeto (cores do passo 29) com tooltip explicando cada estado.
39. Agenda da semana no destaque: 7 colunas (dom–sáb), eventos nos seus dias, cada um com os chips dos projetos da semana corrente.
40. Clique num dia da agenda → filtra a grade para aquele evento.
41. Semana vazia → agenda recolhe para uma linha discreta.
42. Filtro rápido no topo da grade: Todos · Rascunhos · Prontos · Exportados · Publicados.
43. Teste: transição exportar→exportado; editar conteúdo→rascunho (por hash, não por salvar à toa).
44. Teste: status sobrevive a duplicar (cópia nasce rascunho) e a abrir/reabrir.
45. Foto: agenda cheia e vazia, claro+escuro.
46. **Checagem:** suíte parcial verde.

## Bloco D — Continuidade e afeto (passos 47–56)
**Por quê:** R-004/007/012 — o app lembra de você.

47. "Continuar de onde parei": faixa fina no topo com miniatura + nome do último projeto aberto (Config `inicio.ultimo_projeto`), clique reabre direto.
48. Registrar o "último aberto" em TODO caminho de abertura (Mesa, Fábrica, duplo-clique, duplicar).
49. Favoritos: estrela no hover do cartão de projeto; favoritos sobem para o topo do seu evento.
50. Persistir favorito em coluna `favorito` (bool, `_COLUNAS_NOVAS`).
51. Notas do evento: ícone de nota no cartão quando há texto; clique abre popover editável (o "quinta que vem é feriado").
52. Notas aparecem também no cartão "Produzir hoje" do dia (o lembrete na hora certa).
53. Teste: último-aberto atualiza nos 4 caminhos de abertura.
54. Teste: favorito reordena dentro do evento sem tocar o mapa de nada (é só ordenação de exibição).
55. Foto: faixa continuar + favorito + nota no popover.
56. **Checagem:** suíte parcial verde.

## Bloco E — Linha do tempo de versões (passos 57–70)
**Por quê:** R-005 — "salvei por cima e me arrependi" nunca mais. Cada
salvamento guarda a versão anterior com miniatura; abrir versão = nova cópia
(NUNCA sobrescreve — identidade preservada, I1).

57. Ao salvar por cima de projeto existente: snapshot do `estado_slots` anterior + miniatura em `projetos/<uuid>/versoes/<timestamp>/`.
58. Metadados por versão: quando, nº de itens, páginas (json pequeno ao lado).
59. Poda: manter as últimas N versões (Config `projetos.versoes_max`, padrão 10; poda nunca apaga a atual).
60. UI: botão direito do projeto → "Versões…" abre diálogo com linha do tempo (miniatura, data, itens).
61. Ação única no diálogo: "Abrir como novo projeto" (clona a versão para projeto novo "Nome (versão de DD/MM)") — proibido restaurar por cima.
62. Versões viajam no `.atpkg`? NÃO (pacote leve) — documentado no diálogo ("versões são locais").
63. Lixeira e versões não se misturam: excluir projeto leva as versões juntas para a lixeira (Bloco G).
64. Teste: salvar 3× gera 2 versões + atual; poda em N=2 mantém as 2 mais novas.
65. Teste: abrir-como-novo clona por conteúdo (mapa/overrides idênticos, uuid NOVO).
66. Teste: miniatura da versão existe e abre.
67. Adversarial nominal: versões não tocam slot/uid do projeto vivo (conferir mapa intacto pós-fluxo completo).
68. Foto: diálogo de versões com 3 entradas, claro+escuro.
69. Perf: salvar com versão ≤ +150 ms sobre o salvar atual (medir e registrar).
70. **Checagem:** suíte parcial verde ×1.

## Bloco F — Busca global (passos 71–80)
**Por quê:** R-006/017 — um campo que acha tudo: projeto, produto, layout.

71. Serviço headless `buscar_global(texto)` → grupos {projetos, produtos, layouts} com limite 8/8/8 (LIKE case/acento-insensível).
72. Campo do topo do Início: dropdown de resultados agrupados com miniatura/preço/tipo.
73. Enter no resultado: projeto→abre; produto→Almoxarifado filtrado nele; layout→Ateliê nele.
74. Ctrl+K global (todas as telas) abre a MESMA busca em paleta flutuante (reusa `paleta_comandos` com aba "Buscar").
75. Debounce de 250 ms; buscas <2 letras não disparam.
76. Estado sem-resultado com dica ("tente parte do nome").
77. Teste: busca acha projeto/produto/layout por fragmento com acento trocado.
78. Teste: Ctrl+K abre em Mesa e Configurações (2 telas de amostra).
79. Foto: dropdown com resultados dos 3 grupos.
80. **Checagem:** suíte parcial verde.

## Bloco G — Lixeira de 30 dias (passos 81–90)
**Por quê:** R-008 — excluir sem medo. Nada some de verdade por 30 dias.

81. Soft-delete: coluna `excluido_em` (datetime null) em projetos, layouts e produtos (`_COLUNAS_NOVAS`).
82. TODAS as exclusões da UI viram soft-delete (a pasta de arquivos fica no lugar até a purga).
83. Listagens filtram `excluido_em IS NULL` (varrer os pontos de listagem — projetos, layouts, catálogo, busca global).
84. Tela "Lixeira" dentro do Cofre: itens excluídos com tipo, data, dias restantes; Restaurar · Excluir agora (verbo+confirmação).
85. Purga automática no boot: >30 dias → apaga linha E arquivos (log do que purgou).
86. Produto restaurado volta com fotos e vínculos intactos (byte a byte na pasta).
87. Teste: excluir→some das listas→restaurar→volta inteiro (projeto com mapa por conteúdo).
88. Teste: purga respeita 30 dias (relógio injetado) e apaga arquivos junto.
89. Foto: Lixeira com 3 tipos, claro+escuro.
90. **Checagem:** suíte parcial verde; adversarial da portabilidade nominal (exclusões não vazam para o pacote).

## Bloco H — Saúde e apresentação (passos 91–96)
**Por quê:** R-010/011 — o Início informa e o pai aprova em tela cheia.

91. Faixa de indicadores discreta no rodapé do Início: "X sem foto · Y sem categoria · backup há Zh · IA ligada/desligada" (cada um clica e leva pra onde resolve).
92. Indicadores calculados em worker (nunca atrasam o boot; skeleton até chegar).
93. Modo apresentação: botão no cartão do evento → tela cheia com as peças exportadas do evento (setas ←→, Esc sai, fundo preto, zoom na peça).
94. Apresentação usa os EXPORTS (PNG) quando existem; senão a miniatura grande com aviso "não exportado".
95. Foto: indicadores + apresentação com 2 peças.
96. **Checagem:** suíte parcial verde.

## Bloco I — O gesto nº 1 e o fechamento (passos 97–100 + fecho padrão)
**Por quê:** R-009 — "duplicar semana passada e trocar preços" é a
segunda-feira do dono; e a fase só fecha com a prova de sempre.

97. "Duplicar semana passada" (no cartão do evento e no Produzir-hoje): clona o último projeto do evento como rascunho novo com data de hoje, validade recalculada pelo dia do evento (RG-24), status rascunho, e abre na Mesa com toast "Troque os preços pelo duplo-clique — modo planilha vem na Fase 7".
98. Nome sugerido: "[Evento] DD/MM" com dedup (2), (3).
99. Teste: duplicado tem uuid novo, mapa idêntico por conteúdo, validade re-sugerida, original intocado.
100. **Fecho padrão:** suíte inteira ×2 exit 0 zero skips; adversariais 15/15 nominais; fotos finais (Início completo claro+escuro + GIF de 15 s navegando); resposta do builder NESTE caderno com achados e "o que ficou de fora"; PLANO atualizado; **PARAR** para a reauditoria visual do arquiteto.

---

## Execução do builder (18/07/2026 — em curso, registrado por checagem)

Linha de base confirmada antes de tocar em qualquer coisa: **410 verdes,
zero skips, exit 0**.

### ✔ Checagem do passo 14 (Bloco A)

- Modelo `Evento` (nome único, cor, capa relativa, dia_semana, ordem,
  notas) + `evento_id` em `projetos_salvos` nos DOIS caminhos (modelo p/
  bancos novos e `_COLUNAS_NOVAS` p/ antigos; FK "solta" documentada —
  SQLite não adiciona FK via ALTER, a integridade é do serviço).
- Serviço `app/qt/telas/eventos.py`: migração idempotente (eventos-texto
  dos projetos + `eventos.extras` da Config + dias do RG-24 — NADA se
  perde), cor ESTÁVEL por crc32 numa paleta fixa de 12, criar/renomear
  (o texto de compat dos projetos acompanha)/cor/dia/notas/reordenar,
  capa internada em `layouts/capas/` RELATIVA (I3), capa padrão =
  miniatura do projeto mais recente, excluir só vazio OU movendo (nunca
  órfão em silêncio).
- `salvar_projeto` grava `evento_id` E o texto (a verdade é o id);
  `dia_do_evento` (RG-24) lê do Evento com a Config como fallback;
  migração ligada no boot (`_completar`).
- UI: `EventoDialog` (nome, paleta de 12 com anel no escolhido — o anel
  nasceu de defeito PEGO NA INSPEÇÃO da foto, o checked não se
  destacava —, dia opcional, capa opcional); "Novo evento" do Início usa
  o diálogo; botão direito no cabeçalho do evento (Editar/Notas/Excluir
  com destino) até o cartão do Bloco B assumir. Teste da Onda 5 do
  QInputDialog atualizado ao diálogo da casa.
- Testes 11-13: migração de 3 eventos-texto com projetos LIGADOS por
  conteúdo + idempotência + cor estável; excluir movendo preserva os 3
  por conteúdo; capa relativa byte-idêntica (I3, sem `:` nem `\`).
- Fotos: `saida_fase2/dialogo_novo_evento_{claro,escuro}.png`
  inspecionadas. Suíte parcial: **413 verdes, zero skips, exit 0**.

### ✔ Checagem do passo 34 (Bloco B)

- Início em **3 zonas** (15): topo com saudação pela hora + data por
  extenso PT-BR + busca (campo pronto; o Bloco F liga) + ações rápidas
  (16/26); zona destaque (17-18): cartão **"Produzir hoje: [Evento]"**
  quando `hoje.weekday() == dia_semana` com "Duplicar semana passada"
  (o gesto REAL chega no passo 97 — botão avisa com honestidade) e
  "Começar do zero"; sem campanha hoje, chips "Esta semana" na COR de
  cada evento, ordenados pela proximidade do dia.
- **Grade de cartões de evento** (19/21/22/23): ★ Ofertas da semana
  antes, capa (definida > miniatura do projeto mais recente), faixa da
  cor, contagem + "último em", "toda quinta", botão Abrir + ELEVAÇÃO no
  hover (sombra da Fase 1); Avulsos neutro ao fim; responsiva 2/3
  colunas (1600 px) com refluxo no resize; entrada em CASCATA (31 —
  helper novo `cascata()` no motor, 60 ms por cartão).
- Visão do evento (20): a prateleira antiga POR DENTRO do cartão (agora
  em grade com quebra de linha), com voltar, faixa/nome/contagem e o
  menu do evento também ali; duplo-clique abre Mesa/Fábrica (27 — teste
  prova); "Mover para evento…" no botão direito do projeto (28 — serviço
  `mover_projeto`); PONTINHO de status no delegate (29 — cores
  rascunho/pronto/exportado/publicado; o chip completo vem no Bloco C);
  skeleton do carregamento herdado da Fase 1 (24); estado vazio
  zero-projetos = hero com os 3 cartões-caminho REUTILIZADOS do
  boas-vindas (25 — `cartao_caminho` extraído público).
- **Achado de bancada:** a `cascata()` escondia os cartões e agendava
  fades por timer — a PRIMEIRA foto saiu com a grade VAZIA; curada no
  MOTOR com a lei da Fase 1 (janela WA_DontShowOnScreen mostra seco).
- Testes: os 2 antigos do dashboard ADAPTADOS ao contrato novo (grade
  por conteúdo + visão com o projeto certo); novos 32-33 (smoke 0/1/N;
  "Produzir hoje" aparece EXATAMENTE no dia, e vira chips quando o dia
  sai de hoje).
- Fotos (30): **8 em saida_fase2/** — 0 eventos (hero), 1 evento com
  "Produzir hoje", 4+ eventos (grade 2 colunas, chips da semana, evento
  vazio com placeholder) ×2 temas, + BÔNUS acervo real ×2 (miniaturas
  reais do Quintou). Inspecionadas.
- Suíte parcial: **415 passed, zero skips, exit 0**.

### ✔ Checagem do passo 46 (Bloco C)

- Coluna `status` (35 — modelo + `_COLUNAS_NOVAS`, banco antigo lê
  "rascunho"); transições por CONTEÚDO (36): exportar marca "exportado"
  na Mesa E na Fábrica (as telas agora rastreiam `_projeto_id` no salvar
  e no abrir congelado); salvar por cima só rebaixa a rascunho se o HASH
  do estado mudou — re-salvar igual não rebaixa (decisão documentada no
  código); "pronto"/"publicado" são gestos humanos no botão direito (37,
  com o "publicado = enviei no WhatsApp" no tooltip).
- CHIP de status pintado no delegate (38 — pill com texto e cor:
  cinza/azul/verde/roxo; tooltip explica cada estado); duplicado nasce
  rascunho e herda evento_id (44).
- **Agenda da semana** (39): 7 colunas dom–sáb no destaque, hoje
  destacado, eventos nos seus dias nas suas CORES, até 3 chips de
  projetos da semana por evento; clique filtra a grade com chip
  "filtrando: X ✕" visível (40); semana sem projeto recolhe para a linha
  de chips do passo 18 (41); filtro rápido por status no topo da grade
  (42: Todos · Rascunhos · Prontos · Exportados · Publicados).
- Testes (43-44): exportado fica ao re-salvar IGUAL (a 1ª rodada acusou
  o teste fabricando itens com uid novo — corrigido para a estante
  estável, fiel ao app) e cai a rascunho por hash quando o preço muda;
  cópia nasce rascunho, original mantém, abrir/reabrir não transiciona.
- Fotos (45): agenda_cheia/agenda_vazia ×2 temas em saida_fase2/,
  inspecionadas (7 colunas com chips ✓; a vazia recolhida na linha).
- Suíte parcial: verde (placar acima), zero skips, exit 0.

### ✔ Checagem do passo 56 (Bloco D)

- "Continuar de onde parei" (47): faixa clicável no topo com miniatura +
  nome, Config `inicio.ultimo_projeto`; registrado nos caminhos de
  abertura (48): `abrir_projeto_congelado` da Mesa e da Fábrica (o funil
  por onde diálogo E dashboard passam) + duplicar (o novo vira o último).
- Favoritos (49-50): coluna `favorito`, ★ âmbar pintada no delegate,
  favoritos sobem DENTRO do evento (só ordenação de exibição). **Desvio
  registrado da letra:** "estrela no hover" clicável exigiria widget por
  item — a lista é estática por lei (RG-10); o gesto vive no botão
  direito ("★ Favoritar"), a estrela é o INDICADOR. O arquiteto decide se
  quer o clique direto (delegate com hit-test é o caminho, ~30 linhas).
- Notas (51-52): "✎ tem nota" no cartão (tooltip mostra o texto inteiro;
  o editor é o multiline do menu do evento — popover flutuante
  simplificado para o diálogo da casa, registrado); a PRIMEIRA linha da
  nota aparece no cartão "Produzir hoje" em âmbar (o lembrete na hora).
- Testes (53-54): último-aberto nos 4 caminhos; favorito reordena SEM
  tocar o mapa congelado (comparado por conteúdo — I1).
- Fotos (55): continuidade_{claro,escuro} + favorito_visao_{claro,escuro}
  em saida_fase2/, inspecionadas. **Defeito pego na inspeção:** o glifo
  🗒 virava caixinha (fonte sem o emoji) → trocado por "✎".
- Suíte parcial (56): **419 passed, zero skips, exit 0**.

### ✔ Checagem do passo 70 (Bloco E)

- Versões (57-58): ao salvar POR CIMA, o estado anterior vira snapshot
  COMPLETO da pasta (arte + imagens + miniatura — o recongelamento
  sobrescreve `imagens/*.png`, então o snapshot é gravado ANTES; se o
  hash não mudou, a versão recém-criada é descartada) + `estado.json` +
  `overrides.json` (pego na construção: os overrides da época vivem em
  coluna própria e ficariam de fora) + `meta.json` (quando/itens/páginas).
- Poda (59): `projetos.versoes_max` (padrão 10), a ATUAL vive fora de
  `versoes/` e nunca é podada. Lixeira (63): o soft-delete do Bloco G
  deixa a pasta inteira no lugar — versões viajam junto POR CONSTRUÇÃO.
- UI (60-62): `VersoesDialog` com linha do tempo (miniatura/data/itens/
  páginas), ação ÚNICA "Abrir como novo projeto" ("Nome (versão de
  DD/MM)"), e as duas regras DITAS na tela: nada é sobrescrito; versões
  são locais (não viajam no .atpkg).
- Testes (64-67): 3 salvamentos = 2 versões + atual e poda N=2; clone
  com uuid NOVO e estado DA ÉPOCA por conteúdo (original intocado);
  miniatura da versão existe; adversarial nominal — o MAPA do vivo confere
  byte a byte após o fluxo completo (I1).
- Perf (69): salvar com versão = **+21 ms** no projeto de teste
  (orçamento ≤ +150 ms; projeto real com arte de ~2 MB deve ficar em
  ~60-100 ms — o snapshot é cópia de pasta local).
- Fotos (68): dialogo_versoes_{claro,escuro} com 3 entradas em
  saida_fase2/, inspecionadas.
- Suíte parcial ×1 (70): verde (placar acima), zero skips, exit 0.

### ✔ Checagem do passo 80 (Bloco F)

- Serviço `buscar_global` (71): {projetos, produtos, layouts} 8/8/8, case
  E acento-insensível por normalização NFD ("acucar" acha "Açúcar";
  produtos casam por nome sanitizado + bruto + marca); <2 letras devolve
  vazio (75 — o serviço também se defende).
- Início (72-73/75-76): dropdown ancorado no campo com debounce de
  250 ms, grupos com cabeçalho/ícone, Enter abre o primeiro; projeto
  abre Mesa/Fábrica, produto aterrissa no Almoxarifado FILTRADO nele,
  layout seleciona no Ateliê (`selecionar_layout` novo); sem resultado →
  "Nada encontrado — tente parte do nome".
- **Ctrl+K global** (74): `PaletaBusca` (a casca da paleta de comandos)
  em QUALQUER tela via atalho no Shell. **Decisão registrada:** Ctrl+K
  era a paleta de comandos do editor — dois donos do mesmo atalho =
  ambiguidade Qt (nenhum dispararia); a paleta de comandos migrou para
  **Ctrl+Shift+P** (padrão de editores) e Ctrl+K é a busca, como o passo
  74 pede. O arquiteto avalia se prefere outra combinação.
- Testes (77-78): os 3 grupos por fragmento com acento/caixa trocados +
  guarda de <2 letras; a paleta abre na Mesa e nas Configurações.
- Fotos (79): busca_dropdown_{claro,escuro} com os 3 grupos.
  **Defeito pego na inspeção:** "R$ 9.99" com ponto → vírgula PT-BR.
- Suíte parcial (80): verde (placar acima), zero skips, exit 0.

### ✔ Checagem do passo 90 (Bloco G)

- Soft-delete (81-82): `excluido_em` em projetos/produtos/layouts
  (modelo + `_COLUNAS_NOVAS`); TODAS as exclusões da UI viram suaves
  (excluir_projeto, excluir_produtos do Almoxarifado, excluir layout do
  Ateliê) — pastas e fotos ficam no lugar.
- Listagens filtram (83): listar_projetos, listar_layouts,
  ProdutoRepositorio.listar/buscar (o catálogo paginado), busca global.
- Lixeira no Cofre (84): painel com contador vivo, tipo+nome+quando+dias
  restantes, Restaurar (volta inteiro — passo 86, por construção: os
  arquivos nunca saíram) e "Excluir agora" com verbo+confirmação.
- Purga no boot (85): >30 dias apaga linha E arquivos com log no console
  + toast quando purgou algo (I2); relógio INJETÁVEL.
- Portabilidade (90): a análise/mesclagem filtram excluídos dos DOIS
  lados (13 queries) — item da lixeira não vira "novo" no destino;
  adversarial da portabilidade nominal na suíte.
- **Achado de bancada:** o Edit da tela do Cofre deixou o loop dos
  snapshots ÓRFÃO dentro do método da lixeira (NameError latente +
  backups sumidos da lista) — pego pelo teste do Cofre, devolvido ao
  recarregar. Teste antigo do excluir-projeto ATUALIZADO à semântica nova
  (a pasta fica; `excluir_agora` a leva — provado nos dois passos).
- Testes (87-88): excluir→some→restaurar→volta com o mapa por conteúdo;
  purga respeita 30 dias com relógio injetado (29 fica / 31 morre com a
  pasta) e loga.
- Fotos (89): lixeira_{claro,escuro} com os 3 tipos, inspecionadas.
- Suíte (90): **427 passed, zero skips, exit 0**.

### ✔ Checagem do passo 96 (Bloco H)

- Indicadores de saúde (91-92): `indicadores_saude()` headless (sem foto
  por caminho vazio/nulo, sem categoria, idade do backup pelo MTIME do
  snapshot mais novo, IA alcançável por ping de 1 s ao /models) rodando
  em WORKER — a faixa do rodapé nasce "Verificando o acervo…" e os
  números chegam sem tocar o boot; cada indicador é um LINK que leva pra
  onde resolve (sem foto → Almoxarifado filtrado em ● Sem imagem; sem
  categoria → ● Incompletos; backup → Cofre; IA → Configurações).
- Modo apresentação (93-94): menu do evento → tela CHEIA fundo preto,
  ←/→/espaço navegam, Esc sai, re-escala no resize; usa o EXPORT real
  registrado (o exportar agora grava `projetos.exports` na Config) e cai
  na miniatura com o aviso "⚠ não exportado" — nunca mente (I2).
- Fotos (95): indicadores_{claro,escuro} (faixa com números do acervo
  REAL: backup há 9h, IA local ligada) + apresentacao_1/2 (o Verso
  Quintou real em tela cheia com o rodapé honesto). Inspecionadas.
- Suíte (96): verde (placar acima), zero skips, exit 0.

---

## Resposta do builder — FASE 2 executada (18/07/2026)

**Linha de base:** 410 verdes. **Ao fechar:** **428 verdes, zero skips,
exit 0 em DUAS rodadas** (13 testes novos em 6 arquivos test_fase2_*).
Adversariais **16/16** (15 herdados + o nominal das versões). Os 100
passos na ordem; as 8 checagens (14/34/46/56/70/80/90/96) registradas
acima com inspeção visual.

### O fecho (passos 97-100)

- **O gesto nº 1 (97-98)**: `duplicar_semana_passada` — clona o último
  projeto do evento como "[Evento] DD/MM" (dedup (2), (3)), validade
  re-sugerida pelo dia da campanha (RG-24), status rascunho, e ABRE na
  Mesa com o toast do caderno; vive no cartão "Produzir hoje" E no menu
  do evento. Teste (99): uuid novo, mapa por conteúdo, validade
  re-sugerida, original intocado, dedup provado.
- Fotos finais: inicio_final_{claro,escuro} (acervo real com a faixa de
  saúde viva) + **inicio_navegacao.gif** (15 s, 137 quadros, 291 KB:
  home → visão do evento → volta → busca com dropdown composto).

### Achados de bancada da fase (nenhum escondido)

1. `cascata()` escondia os cartões em janela de captura — 1ª foto saiu
   com a grade VAZIA; curado no motor (lei da Fase 1: WA_DontShowOnScreen
   mostra seco).
2. O Edit da tela do Cofre deixou o loop dos snapshots ÓRFÃO dentro de
   um método da lixeira (NameError latente) — pego pelo teste, devolvido.
3. Worker de saúde no CONSTRUTOR do Início derrubou a suíte (segfault em
   teste que fecha rápido) — a MESMA lição da F7.1; movido ao showEvent.
4. As versões esqueceriam os OVERRIDES da época (coluna própria, fora do
   estado_slots) — pego na construção, `overrides.json` no snapshot.
5. O teste de status fabricava itens com uid novo e acusava o hash — o
   "re-salvar igual" de verdade usa a estante estável; teste corrigido.
6. Swatch de cor sem anel no escolhido; glifo 🗒 sem fonte; "R$ 9.99" com
   ponto — três defeitos visuais pegos por inspeção, curados.
7. Ctrl+K tinha DOIS donos (busca global × paleta do editor) — ambiguidade
   Qt mataria os dois; a paleta migrou para **Ctrl+Shift+P** (decisão
   registrada na checagem 80, aberta ao arquiteto).

### Adaptações registradas da letra (o arquiteto decide)

- Passo 49: "estrela no hover" clicável → estrela-indicador no delegate +
  gesto no menu (lista estática por lei RG-10; hit-test no delegate é o
  caminho se o dono quiser o clique direto).
- Passo 51: popover de notas → diálogo multiline da casa.
- Passo 30: "4+ eventos" fotografado com estado SINTÉTICO (o acervo real
  tem 2 eventos) + bônus do acervo real.
- Passo 91: "sem foto" conta por caminho vazio no banco (a régua fina de
  arquivo-sumido é o filtro ● do Almoxarifado — contar existência de 5k
  arquivos no worker toda hora seria caro).

### O que ficou de fora (nominal)

- O texto longo dos itens da Lixeira corta à direita (scroll horizontal
  existe; elipse melhor fica para o polimento).
- A visão do evento não tem animação própria de entrada (a pilha interna
  troca seca — o crossfade do Shell não a cobre).
- `holder["inicio"]`/`almox`/`atelie` ganharam referências no editor_app
  para a navegação da busca — scripts antigos que usavam montar_janela
  continuam funcionando (compat preservada).
- Eventos do acervo real ainda sem dia_semana (o dono nunca preencheu
  `eventos.dias`) — a agenda aparece quando ele configurar pelo diálogo.

**PARADO no passo 100.** Aguardando a reauditoria visual do arquiteto
sobre `saida_fase2/` (22 imagens + 1 GIF).
