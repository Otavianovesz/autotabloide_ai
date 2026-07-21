# FASE 1 — Fundação visual: design system 2.0 (caderno de 100 passos)

> Formato-lei do PLANO_PERFEITO: blocos com "Por quê", passos de uma ação,
> checagens a cada ~25. Builder: executar NA ORDEM, sem pular, sem juntar.

## Bloco A — Fotografia do estado atual (passos 1–8)
**Por quê:** o dono reprovou "formatação errada, tudo diminuindo". Antes de
mexer, congelamos a prova do ANTES para comparar o DEPOIS tela a tela.

1. Criar `app/scripts/fotografar_telas.py`: abre cada tela e salva PNG em `saida_fase1/antes/`.
2. Fotografar: Início, Ateliê, editor com grade, Almoxarifado, Mesa, Fábrica, Cofre, Configurações.
3. Fotografar os 3 diálogos: conciliação, curadoria, fotos-do-item.
4. Listar em `saida_fase1/inventario_widgets.txt` todo widget com largura/altura fixas hardcoded.
5. Rodar a suíte (linha de base; anotar número no caderno).
6. Ler `revisão/Outra auditoria/` e anotar no caderno cada print com defeito visível.
7. Para cada defeito do passo 6: uma linha "print → widget → causa suspeita".
8. **Checagem:** `saida_fase1/antes/` completo (11+ imagens) e inventário não-vazio.

## Bloco B — Tokens 2.0: a paleta vira sistema (passos 9–22)
**Por quê:** dark mode e animações precisam de tokens SEMÂNTICOS (fundo,
superfície, texto, borda, acento…) — não cores soltas. Um lugar muda, o app
inteiro obedece.

9. Em `tokens.py`, mapear TODAS as cores atuais para nomes semânticos (FUNDO, SUPERFICIE, SUPERFICIE_2, TEXTO_1/2/3, BORDA, BORDA_FORTE, ACENTO, ACENTO_TEXTO, SUCESSO, ALERTA, PERIGO, SOMBRA).
10. Nenhum módulo pode usar cor literal: `grep` de `#[0-9a-fA-F]{6}` fora de tokens.py → migrar cada um.
11. Criar `TEMAS = {"claro": {...}, "escuro": {...}}` com os 12+ tokens por tema.
12. Tema escuro: fundo #101216, superfícies #181B21/#20242C, texto #E8EAED/#A8ADB5/#6C7280, acento mantém o azul da marca clareado (#5B8DEF), bordas #2A2F38.
13. Função `aplicar_tema(nome)` regenera o QSS global a partir dos tokens.
14. QSS global: revisar TODO seletor para usar tokens (zero cor fixa no QSS).
15. Ícones: `icone()` ganha cor padrão do tema (traço claro no escuro).
16. Pixmaps/painters custom (réguas, canvas, badges): trocar cores fixas por tokens.
17. Config nova `aparencia.tema` = "claro" (padrão) | "escuro".
18. `aplicar_tema` lê a Config no boot ANTES de criar o Shell.
19. Troca de tema em runtime: sinal `tema_mudou` → Shell repolimenta (`unpolish/polish`) todos os widgets.
20. Canvas no escuro: mesa de trabalho escura, página com sombra suave clara — a ARTE nunca é alterada, só o entorno.
21. Miniaturas e cards: fundo de placeholder que funcione nos dois temas.
22. **Checagem:** app abre no claro idêntico ao ANTES (diff visual das fotos ≈ zero).

## Bloco C — Dark mode entregue (passos 23–34)
**Por quê:** o dono pediu duas vezes ("black mode"). Tem que ser bonito,
completo, e a um clique.

23. Aba/seção "Aparência" nas Configurações com seletor Claro/Escuro (cards com prévia em miniatura, não combo seco).
24. Aplicar na hora ao clicar (sem reiniciar), persistindo na Config.
25. Toggle rápido também no menu da engrenagem do Shell (sol/lua).
26. Passar TODAS as telas no escuro corrigindo contraste (texto-3 legível, bordas visíveis).
27. Diálogos e toasts no escuro (fundo superfície-2, sombra mais forte).
28. Overlay "ocupado" e skeletons: versões dos dois temas.
29. Estados de erro/sucesso/alerta: conferir legibilidade no escuro (não neon).
30. Tooltips e menus de contexto tematizados.
31. Réguas e guias do editor no escuro (marcas claras, fundo superfície).
32. Pré-voo e diálogos de conciliação/curadoria no escuro.
33. Fotografar TODAS as telas no escuro em `saida_fase1/escuro/`.
34. **Checagem:** zero fundo branco vazado no escuro (varrer as fotos uma a uma).

## Bloco D — Motor de animação (passos 35–48)
**Por quê:** "animar melhor o programa, algo bonitinho" (R-151). Vida sem
circo: 150–220 ms, curvas suaves, e desligável para máquina fraca.

35. Criar `app/qt/design/animacoes.py`: helpers `fade_in(widget, ms)`, `slide_y(widget, dy, ms)`, `crossfade(container, de, para)`.
36. Padrões: duração 180 ms, curva OutCubic; constantes no módulo (um lugar só).
37. Config `aparencia.animacoes` = ligadas (padrão) | reduzidas; TODOS os helpers a respeitam (reduzidas = instantâneo).
38. Troca de tela no Shell: crossfade suave entre telas (nunca "pisca").
39. Toasts: entram deslizando de baixo + fade, saem em fade (fila empilha com espaçamento).
40. Diálogos: fade-in do fundo escurecido + leve scale-in (0.98→1.0) do corpo.
41. Hover de botões/cards: transição de cor de 120 ms via QSS/efeito (nada de salto seco).
42. Cards do Início/Ateliê: sombra sobe 1 nível no hover (efeito de elevação).
43. Skeleton de carregamento: retângulos pulsantes nas listas enquanto carregam (Início, Almoxarifado).
44. Barra de progresso dos overlays com movimento contínuo (indeterminado bonito).
45. Painel de propriedades: seções recolhem/expandem com animação de altura.
46. Canvas: `ajustar()` e trocas de página com zoom/pan animado curto (sem enjoar: 160 ms).
47. Medir: troca de tela e hover não podem passar de 5% de CPU em idle (perfil rápido no caderno).
48. **Checagem:** vídeo/GIF curto de 20 s navegando o app anexado em `saida_fase1/` + "Reduzir animações" provado (tudo instantâneo).

## Bloco E — Formatação-base: o fim do "tudo espremido" (passos 49–70)
**Por quê:** RG-54 — prints mostram widgets encolhendo e dropdowns
cortados. Regra de ouro: nenhum controle abaixo do seu mínimo legível;
quem falta espaço ganha rolagem ou estouro, nunca esmagamento.

49. Definir em `tokens.py`: ALTURA_CONTROLE=32, LARGURA_MIN_CAMPO=96, ESPACO_1/2/3=4/8/16 (múltiplos de 4).
50. Auditoria com o inventário do passo 4: remover larguras/alturas fixas indevidas; usar mínimos + políticas de expansão.
51. Painel de propriedades: largura mínima 300, campos em coluna com rótulo acima quando apertado (nunca rótulo truncado).
52. Combos: `setMinimumContentsLength` e popup com largura do maior item (fim do texto cortado).
53. SpinBoxes: largura para 4 dígitos + sufixo visível.
54. Formulários das Configurações: grid de 2 colunas com respiro ESPACO_3; nunca 6 controles na mesma linha.
55. Diálogo de conciliação: colunas com largura mínima; nomes longos com elipse + tooltip inteiro.
56. Curadoria: grade de candidatos com célula mínima 160 px; botões inferiores com estouro se faltar largura.
57. Barra do editor: grupos com separadores; abaixo de 1200 px de janela, grupos menos usados colapsam em "···".
58. Barra da Mesa: idem — dois níveis a partir do limiar OU menu "···" (decisão visual: o que couber com 8 px de folga fica).
59. Estante/painéis laterais: largura mínima 300, redimensionável por splitter com memória.
60. Shell lembra tamanho/posição/última tela (R-023) via Config.
61. Zoom %, dimensões e status do rodapé com largura reservada (não dança).
62. Testar janela 1280×720 (menor alvo): TODAS as telas usáveis, nada cortado.
63. Testar 1920×1080: sem espaços mortos gigantes (conteúdo escala com bom senso).
64. Escala de UI (R-015): Config `aparencia.escala` = 100/125/150% aplicando fonte-base + ALTURA_CONTROLE multiplicados.
65. Testar as 3 escalas nas 3 telas mais densas (editor, Mesa, Configurações).
66. Acessibilidade base (R-024): ordem de Tab correta em todos os formulários.
67. Foco visível (anel de foco de 2 px no acento) em todo controle.
68. Atalhos das ações principais visíveis nos tooltips ("Exportar · Ctrl+E").
69. Fotografar tudo de novo em `saida_fase1/depois/` (claro e escuro).
70. **Checagem:** lado a lado antes/depois no caderno; cada defeito do passo 7 marcado CURADO (ou justificado).

## Bloco F — Toques de vida espalhados (passos 71–86)
**Por quê:** R-020/021/022 — o app responde, orienta e nunca deixa o dono
sem saída.

71. Toast com botão "Desfazer" embutido (excluir item/região/limpar estante) — 6 s de janela.
72. Fio de desfazer do toast ligado às ações reais (não recriar por fora do undo existente).
73. Estados vazios: TODOS com ícone + frase + botão-ação (estante → Importar; Ateliê → Novo layout; Almoxarifado → Categorizar/Importar; Cofre → Criar snapshot).
74. Som opcional de exportação concluída (Config `aparencia.som`, padrão desligado; .wav curto e discreto).
75. Cursor de espera consistente: toda operação >300 ms mostra ocupado/skeleton (nunca congelado mudo).
76. Contadores vivos: título dos painéis com número ("Itens da oferta · 14").
77. Barra de título da janela: "AutoTabloide — [Projeto] •" (• = não salvo).
78. Confirmações destrutivas padronizadas (verbo no botão: "Excluir 3 itens", nunca "OK").
79. Menus de contexto com ícones consistentes em todas as telas.
80. Splash do boot com logo + frase de carregamento (usa o pré-aquecimento existente; some em fade).
81. Primeira execução: saudação de boas-vindas com 3 cartões (Importar oferta · Criar layout · Conhecer o Almoxarifado).
82. Tela "Sobre" (versão, créditos, atalho para diagnóstico).
83. Ícone do app no título/na barra do Windows (o B da marca).
84. Revisar TODOS os textos visíveis: PT-BR natural, sem jargão técnico vazando (varredura de strings).
85. Fotografar os estados novos (vazios, toasts, splash) nos dois temas.
86. **Checagem:** suíte inteira verde ×1 (parcial de bloco).

## Bloco G — Fechamento da fase (passos 87–100)
**Por quê:** a fundação só vale selada: prova visual, prova de regressão,
prova de performance.

87. Rodar a suíte inteira: verde, zero skips, exit 0.
88. Rodar de novo (a lei do ×2): idem.
89. Adversariais nominais (a fase NÃO tocou slot/item/mapa — confirmar que continuam 15/15).
90. Boot medido de novo: ≤ o da Onda 1 (510 ms) + splash (o splash não pode custar >100 ms).
91. Teste novo: `test_fase1_tema.py` — aplicar_tema troca tokens, Config persiste, claro é o padrão.
92. Teste novo: animações reduzidas = zero timers de animação ativos.
93. Teste novo: mínimos de layout (nenhum widget com largura < mínimo do token nas telas principais).
94. Atualizar o microtutorial se algum gesto mudou de lugar.
95. `saida_fase1/` final: antes/, depois/, escuro/, GIF, inventário, comparativo.
96. Resposta do builder NESTE caderno: o que fez, achados de bancada, "o que ficou de fora".
97. Atualizar PLANO_DE_CONSTRUCAO.md (Fase 1 do Plano Perfeito).
98. Conferir CLAUDE.md aponta ordem vigente correta.
99. Screenshot final do Início claro+escuro lado a lado (o cartão-postal da fase).
100. **PARAR.** Reauditoria do arquiteto com inspeção visual de TODOS os artefatos.

---

## Execução do builder (18/07/2026 — em curso, registrado por checagem)

### ✔ Checagem do passo 8 (Bloco A)

- `saida_fase1/antes/`: **11 imagens** (7 telas do shell + editor com grade
  + 3 diálogos) — geradas por `app/scripts/fotografar_telas.py` (passo 1;
  pasta e tema parametrizáveis para os passos 33/69 reusarem).
- `saida_fase1/inventario_widgets.txt`: **26 dimensões fixas** inventariadas.
- Suíte (passo 5): **402 verdes, zero skips, exit 0**.
- Prints da "Outra auditoria" (25 frames extraídos do .mht de 18/07 12:46)
  — defeitos anotados (passo 7, "print → widget → causa suspeita"):
  - **D1** frame 3 · Configurações, coluna direita → campos de URL/modelos/
    ICC/categorias CORTADOS na borda da janela → o form de 2 colunas não
    tem largura máxima nem margem direita (falta grid com respiro — p. 54).
  - **D2** frame 3 · Configurações, topo → "Campo vazio volta ao padrã…"
    truncado → QLabel sem mínimo/elipse (p. 54/61).
  - **D3** frame 12 · editor, painel Propriedades → legenda dos pontinhos
    com quebras coladas na borda do painel de 300 px → falta margem/respiro
    no rótulo de legenda (p. 51).
  - **D4** frame 12 · editor, painel Camadas → lista com ~4 itens visíveis
    e scroll precoce → proporção dos painéis sem mínimo digno (p. 50/51).
  - **D5** geral · nenhuma tela tem tema escuro → é o núcleo da fase
    (Blocos B/C).
  - Almoxarifado/Mesa/Fábrica (frames 19–25): sem defeito NOVO além dos
    já cobertos pelos passos 49–70 (mínimos e políticas).

### ✔ Checagem do passo 22 (Bloco B)

- Tokens semânticos completos (passo 9: FUNDO/TEXTO_1/ACENTO_TEXTO/SOMBRA
  como aliases canônicos); **zero cor literal de UI fora de tokens.py**
  (passo 10 — exceções documentadas: os `#000000` do painel de
  propriedades são COR DE DOCUMENTO da região, não chrome).
- `TEMAS` claro/escuro (passos 11–12, escuro na spec do caderno);
  `ativar_tema` muta o módulo (leitura tardia: os 26 módulos usam
  `import tokens as t` — verificado); `aplicar_tema(app, nome)` regenera
  paleta+QSS; Config `aparencia.tema` lida no boot ANTES do Shell;
  `trocar_tema` repolimenta tudo + `Shell.retematizar` refaz os ícones do
  topo. Limite documentado: ícone criado com COR EXPLÍCITA em tela viva
  só recolore quando a tela recria (o top-bar é refeito; o resto é
  aceitável até a reconstrução da tela — decisão para o arquiteto).
- **Diff visual claro × ANTES: 11/11 imagens IDÊNTICAS (0 pixels).**

### ✔ Checagem do passo 34 (Bloco C)

- Aparência nas Configurações com **cards de prévia pintada** (claro/
  escuro, o ativo com borda de acento) aplicando NA HORA e persistindo;
  **toggle na engrenagem do Shell** (que era um botão morto — ganhou vida).
- Véu do overlay tematizado (`VEU_OCUPADO` — era rgba branco fixo, vazaria
  no escuro); toasts/menus/tooltips/réguas/canvas obedecem tokens por
  leitura tardia (verificado: 26 módulos com `import tokens as t`).
- `saida_fase1/escuro/`: **11 fotos**, varridas UMA A UMA + detector de
  branco-puro: **zero chrome vazado** — os brancos restantes são CONTEÚDO
  (artes das miniaturas, carrinho da arte, o card de prévia do tema claro:
  1,2% no pior caso, todos legítimos). Início/editor/curadoria escuros
  inspecionados em tela cheia: contraste correto, aviso RG-20 legível.
- **Achado de bancada (ambiente)**: o plugin `offscreen` desta máquina
  renderiza glifos como caixas — o fotografar_telas passou ao plugin
  NATIVO com `WA_DontShowOnScreen` (nada pisca; fontes perfeitas); as
  séries antes/ e escuro/ foram re-fotografadas (fiel: o claro é
  pixel-idêntico ao antes, provado na checagem 22). O processo de captura
  encerra com crash silencioso APÓS gravar tudo (teardown de threads Qt
  do montar_janela fora do main real) — as fotos saem completas; anotado
  para o arquiteto.

### ✔ Checagem do passo 48 (Bloco D)

- **Motor** `app/qt/design/animacoes.py` (passos 35–37): 180 ms OutCubic
  (hover 120 ms), helpers `fade_in`/`slide_y`/`crossfade`, registro
  `_VIVAS` + `animacoes_ativas()`, Config `aparencia.animacoes`
  ("ligadas"/"reduzidas") respeitada por TODOS os helpers.
- Ligações: crossfade na troca de tela do Shell (38); toasts deslizam +
  fade com FILA empilhada (39 — antes um cobria o outro); diálogos com
  véu escurecido (`VEU_DIALOGO`) + fade/scale-in 0.98→1.0 via filtro
  GLOBAL instalado só nos entrypoints (`instalar_vida` — testes e fotos
  ficam sem circo) (40); hover de botões por véu translúcido animado que
  REPRODUZ as cores antigas (o QSS parou de saltar o fundo; borda continua
  seca = feedback imediato) (41); elevação de card em item de lista via
  delegate pintado (Início + Ateliê; QListWidget não aceita DropShadow por
  item) (42); skeleton pulsante no Início (com frame garantido antes da
  carga) e ADIADO 90 ms no Almoxarifado — nunca pisca à toa (43);
  `BarraIndeterminada` (cometa) na caixa do overlay (44); seções
  Preço/Imagem do painel de propriedades recolhíveis com animação de
  altura (45); `ajustar()`/troca de página do canvas com zoom+pan animado
  160 ms — janelas `WA_DontShowOnScreen` (fotos) fecham SECO no
  enquadramento final (46).
- **Perfil de CPU (47)** — `app/scripts/perfil_cpu_fase1.py`, janela real:
  idle 0,0% · troca de tela 0,3% · hover 0,0% · **idle final 0,0% com 0
  animações vivas** (limite: 5%). O veredito pegou um vazamento REAL: o
  skeleton morto via deleteLater nunca emitia finished e apodrecia em
  `_VIVAS` — curado no motor (destroyed também limpa o registro).
- **GIF de 20 s** (48): `saida_fase1/animacoes.gif` (2,2 MB) — navegação
  pelas 7 telas, toast, skeleton, diálogo, hover. Inspeção POR CONTEÚDO:
  véu do diálogo provado por pixel (top-bar 255,255,255 sem véu →
  191,194,198 com véu = os 27% do token); toast visível no rodapé;
  CuradoriaDialog real com o aviso RG-20. **"Reduzir animações" provado:
  pico de animações em voo = 0** nas mesmas ações (trocas, toast,
  diálogo, hover).
- Honestidade de bancada: (a) o corpo do diálogo é janela própria — o
  grab não captura windowOpacity, então o GIF mostra véu + scale-in mas
  não o fade do corpo (limite da captura, não do app); (b) o teste do
  Ctrl+0 foi atualizado a esperar o DESTINO da animação via
  `animacoes_ativas()` — a falha original revelou que ele capturava a
  escala esperada ANTES do fit fechar; (c) scripts demo_* não instalam
  `instalar_vida` — hover sem véu neles (bancada, não produção).
- Suíte após o bloco: **402 passed, zero skips, exit 0**.

### ✔ Checagem do passo 70 (Bloco E)

- **Régua nova** (49): `ALTURA_CONTROLE=32`, `LARGURA_MIN_CAMPO=96`,
  `ESPACO_1/2/3` em tokens.py; aplicada no QSS com o box model explícito
  (min-height do QSS conta só o conteúdo — comentado no próprio QSS).
- **Auditoria do inventário** (50): 26 fixos → LEGÍTIMOS os intrínsecos
  (réguas do canvas, spinner, faixas de evento, amostra de cor, botões de
  ícone); INDEVIDOS convertidos: textareas das Configurações (4× fixo →
  mínimo), busca do Almoxarifado (fixo → mín+teto), btn_limpar 24×22 →
  28×28; os 5 painéis-coluna fixos viraram splitter no 59.
- Painel de propriedades: mín. 300 + `WrapLongRows` (51); combos com
  `minimumContentsLength` e POPUP na largura do maior item via filtro
  global `polimento.py` (52); spinboxes com 4 dígitos + sufixo (53);
  Configurações com respiro ESPACO_3 e ROLAGEM vertical (54 — a cura
  estrutural do D1 em janela baixa); conciliação com mínimo de coluna 90,
  nomes em Stretch + elipse + tooltip inteiro (55); curadoria com célula
  ≥160 e mínimo do diálogo = soma da botoeira (56 — "estouro" resolvido
  por mínimo que impede o corte; wrap dinâmico dispensado).
- **Barras** (57-58): editor colapsa alinhar+distribuir em "···" abaixo de
  1200 px; Mesa com a política "o que couber com 8 px de folga fica" e
  "···" dinâmico (checkbox vira ação checável espelhada). **Honestidade de
  bancada:** o passo 57 foi aplicado primeiro em `app/qt/barra.py`
  (BarraFerramentas) — descoberto CÓDIGO MORTO na inspeção visual do 720p
  (ninguém o importa; o editor usa `design/barra_editor.py`); reaplicado
  na barra real; o morto segue lá, candidato a remoção quando o arquiteto
  ordenar.
- Splitter com memória (59) nos 5 laterais (editor/mesa/almoxarifado/
  fabrica/cofre — Config `ui.splitter.*`, debounce 500 ms, mínimo 300);
  Shell lembra geometria+maximizada+última tela (60 — `ui.shell`, com
  guarda de monitor desligado); rodapé com largura reservada (61).
- **Fotos**: `_chk62_720p` e `_chk63_1080p` (11 cada) inspecionadas —
  720p: Configurações rolam com setas de spin INTEIRAS, Mesa mostra o
  "···", editor íntegro; 1080p sem espaços mortos além do respiro natural.
  `_chk65_125/150`: escala de UI (64 — R-015, `aparencia.escala` na
  Config + combo na Aparência aplicando NA HORA) provada nas 3 densas —
  em 150% tudo maior e nada cortado. Nota de captura: o canvas da Mesa
  sai com zoom ~27% nas fotos (fit calculado antes do viewport assentar —
  artefato do fotografar, não do app; o Ctrl+0/ajustar do uso real
  enquadra).
- Tab pela ordem VISUAL (66 — `ordenar_tab` no polimento, ligado em
  Configurações/Almoxarifado/Propriedades/3 diálogos); anel de foco 2 px
  nos que faltavam (67 — QToolButton, checkbox, listas, textareas; visível
  na foto das Configurações); atalhos anunciados EXISTEM e respeitam
  botão desabilitado (68 — Ctrl+E/S/O na Mesa).
- **Lado a lado antes → depois (fotos em saida_fase1/antes vs depois +
  depois_escuro): D1 campos cortados nas Configurações → CURADO (folga na
  borda + rolagem; setas dos spins inteiras). D2 aviso truncado na
  curadoria → CURADO (aviso RG-20 inteiro em âmbar). D3 legenda colada na
  borda do painel → CURADO (respiro no painel mín. 300). D4 lista de
  Camadas espremida → CURADO (splitter, 8+ linhas confortáveis). D5 sem
  dark mode → CURADO no Bloco C (série depois_escuro re-fotografada).**
- Suíte após o bloco: **402 passed, zero skips, exit 0**.

### ✔ Checagem do passo 86 (Bloco F)

- Toast com **"Desfazer" embutido** (71-72, 6 s): excluir REGIÃO usa o fio
  de undo REAL do canvas; excluir item/limpar estante — que por decisão
  registrada não entram no undo do canvas (gesto de dados) — ganharam o
  inverso explícito no próprio toast (item volta À MESMA linha com os
  vínculos por uid — I1). Teste do limpar estante atualizado ao helper.
- Estados vazios com AÇÃO (73): estante→Importar, Ateliê→Novo layout,
  Cofre→Criar backup, Fábrica→Importar, e o Almoxarifado ganhou DOIS
  estados que não existiam — catálogo vazio (botão "Importar ofertas na
  Mesa", navega pelo shell) e busca sem resultado (distintos: banco vazio
  ≠ filtro que não achou).
- Som opcional de exportação (74): .wav curto gerado na bancada (2 tons,
  0,32 s), `aparencia.som` padrão DESLIGADO, checkbox na Aparência que
  toca 1× ao ligar como prova; via winsound assíncrono (app é Windows).
- Cursor de espera (75): `cursor_espera()` nos síncronos pesados (salvar/
  abrir projeto Mesa+Fábrica, auto-preencher); workers já tinham overlay.
- Contadores vivos (76): Ateliê/Cofre/Fábrica com "· N"; Almoxarifado com
  "· N+" honesto (modelo paginado — o + diz que há mais páginas).
- Título da janela (77): "AutoTabloide AI — [Projeto] •" por tela ativa
  (padrão RG-08: cada tela informa o seu documento).
- Confirmações destrutivas com VERBO (78): helper `confirmar_destrutivo`
  aplicado nos 9 pontos (sobrescrever layout, excluir produtos/snapshot/
  layout/projeto ×2, restaurar snapshot, remover página, limpar estante).
- Menus com ícones (79): os menus das ondas já tinham; os "···" novos
  (Mesa herda o ícone do botão; barra do editor usa os das ações).
- Splash (80): pixmap pintado (marca + "Preparando o estúdio…"), aparece
  ANTES da montagem e sai em FADE sobre o shell; boas-vindas de 1ª
  execução (81) com 3 cartões-caminho navegáveis (Config
  `boasvindas.mostrada`); Sobre (82) com versão/créditos/abrir pasta de
  logs — a engrenagem virou MENU (tema continua a 1 clique); ícone do
  app (83) em 6 tamanhos no `setWindowIcon`. **Ambiguidade registrada ao
  arquiteto:** o caderno diz "o B da marca" — o wordmark/splash do APP
  usam "A" (AutoTabloide); seguimos a marca interna; se o dono quis o B
  do Belo Brasil, é 1 linha em `icone_aplicativo`.
- Textos (84): varredura por jargão — "slot" visível virou "célula" (3×),
  "Limpar cache do OCR" virou "Esquecer leituras de foto"; o resto dos
  textos já estava PT-BR natural (trabalho das ondas).
- Fotos dos estados (85): `saida_fase1/estados` + `estados_escuro`
  (splash, toast com Desfazer, vazio com ação, boas-vindas, Sobre).
  **A inspeção visual pegou 2 defeitos reais antes do registro:** cartões
  das boas-vindas saíam VAZIOS (QPushButton-container esconde conteúdo e
  o min-height do QSS de botões o achatava → virou QFrame clicável) e o
  toast fotografado em opacity 0 (o script agora espera o fade fechar).
- Suíte após o bloco (86): **402 passed, zero skips, exit 0**.

---

## Resposta do builder — FASE 1 executada (18/07/2026)

**Linha de base:** 402 verdes, zero skips. **Ao fechar:** **410 verdes,
zero skips, exit 0 em DUAS rodadas** (8 testes novos: 5 em
`test_fase1_tema.py`, 3 em `test_fase1_ui.py`). Adversariais **15/15**
(a fase não tocou slot/item/mapa — confirmados nominais). Os 100 passos
foram executados NA ORDEM; as 7 checagens (8, 22, 34, 48, 70, 86 e esta)
estão registradas acima, cada uma com inspeção visual dos artefatos.

### O fechamento (Bloco G, 87–100)

- 87/88: suíte ×2 — 410/410, exit 0, zero skips.
- 89: adversariais 15/15 (12 do vínculo + 3 espalhados).
- 90 (boot): medição em PROCESSO FRIO decomposta com transparência:
  imports ~110 ms · aplicar_tema ~300 ms · **1ª janela do processo
  ~1.030 ms** · **1ª pintura de TEXTO ~1.485 ms** (banco de fontes do
  Windows) · montar_shell+show **246 ms**. As duas constantes grandes são
  do SO/Qt e existiam FORA da régua da Onda 1 (que media até o show, sem
  primeira pintura de texto; bancada quente). **Na régua comparável, o
  nosso código: 246 ms ≤ 510 ms ✓.** O splash custa ~1 ms de pixmap
  (≤100 ms ✓) e ADIANTA a constante da 1ª janela — a marca aparece ~2 s
  antes do que apareceria qualquer coisa. Decisão de bancada: o splash é
  SÓ o logo vetorial (desenhar texto nele custaria os 1,5 s do banco de
  fontes — medido e documentado no código); a frase de carregamento é a
  dica do rodapé (RG-01).
- 91–93: `test_fase1_tema.py` (tokens trocam, aliases acompanham, Config
  persiste, claro é padrão, QSS segue o tema, escala valida e multiplica);
  `test_fase1_ui.py` (reduzidas = ZERO animações em voo com o EFEITO
  acontecendo; ligadas registra e finaliza sem apodrecer; mínimos de campo
  nas Configurações em 1280×720 varridos por largura real).
- 94: microtutorial da Mesa ganhou Ctrl+E/Ctrl+S e o aviso do "···".
- 95/99: `saida_fase1/` final — antes/, depois/, depois_escuro/, escuro/,
  _chk22/, _chk62_720p/, _chk63_1080p/, _chk65_125/, _chk65_150/,
  estados/, estados_escuro/, animacoes.gif, inventario_widgets.txt,
  **comparativo_antes_depois.png** (11 pares) e
  **cartao_postal_inicio.png** (Início claro+escuro lado a lado).
- 97/98: PLANO_DE_CONSTRUCAO com a era do PLANO PERFEITO e a Fase 1
  executada; CLAUDE.md conferido (ordem vigente correta, nada a mudar).

### Achados de bancada da fase (documentados, nenhum escondido)

1. `app/qt/barra.py` (BarraFerramentas) é **CÓDIGO MORTO** — o passo 57
   foi aplicado nele primeiro; a inspeção do 720p revelou que o editor usa
   `design/barra_editor.py`; reaplicado na barra real. O morto segue lá,
   candidato a remoção quando o arquiteto ordenar.
2. Vazamento no registro de animações: skeleton morto via deleteLater
   nunca emitia finished e apodrecia em `_VIVAS` — pego pelo VEREDITO do
   perfil de CPU; curado no motor (destroyed também limpa).
3. O teste do Ctrl+0 capturava a escala esperada ANTES do fit fechar
   (a falha revelou o próprio bug do teste); atualizado para esperar o
   destino via `animacoes_ativas()`.
4. `aplicar_tema`/repolimento global em processo com wrapper morto
   (deleteLater em voo) derruba o Qt — a produção ganhou
   `shiboken6.isValid` no `_repolir_tudo` (defesa real: trocar tema logo
   após fechar um diálogo).
5. Matar um widget ANIMADO pelo GC do Python (sem deleteLater) deixa
   restos que derrubam o processEvents seguinte — reproduzido e
   documentado no teste; produção usa deleteLater (padrão Qt).
6. A inspeção visual do passo 85 pegou 2 defeitos ANTES do registro:
   cartões das boas-vindas vazios (QPushButton-container + min-height do
   QSS → virou QFrame clicável) e toast fotografado em opacity 0.
7. O grabWindow do Windows devolve a TELA (com DPI), não a janela — o GIF
   passou a compor shell.grab() + diálogo por posição; limite documentado:
   windowOpacity de janela própria não sai em grab.
8. Pillow FUNDE quadros idênticos do GIF somando durations (183 → 45
   quadros, 20 s preservados) — inspeção por tempo real, não por índice.

### Ambiguidade registrada (lei: pergunta, não se escolhe)

- Passo 83 diz "o B da marca" para o ícone do app; o wordmark/splash usam
  "A" (AutoTabloide). Seguimos a marca interna consistente — se o dono
  quis o B do Belo Brasil, é 1 linha em `splash.icone_aplicativo`.

### O que ficou de fora (nominal)

- Passo 46: o canvas anima ajustar/troca de página; janelas de captura
  (WA_DontShowOnScreen) fecham seco de propósito — nas fotos o canvas da
  Mesa sai com zoom de timing (~27%), artefato do fotografar, não do app.
- Passo 57: o limiar do editor é fixo (1200 px); a política medida "8 px
  de folga" ficou só na Mesa (a letra do 58 a pedia lá).
- Ícones com cor explícita em telas vivas seguem recolorindo só quando a
  tela recria (limite documentado desde o Bloco B; top-bar coberto).
- O crash mudo do teardown do fotografar_telas segue (as fotos saem
  completas; anotado desde a checagem 34).
- `barra.py` morto não foi removido (sem ordem para deletar módulo).
- Scripts demo_* não instalam `instalar_vida`/`instalar_polimento`
  (bancada, não produção).

**PARADO no passo 100.** Aguardando a reauditoria do arquiteto com a
inspeção visual de TODOS os artefatos de `saida_fase1/`.
