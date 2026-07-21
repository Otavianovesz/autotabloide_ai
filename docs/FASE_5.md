# FASE 5 — Editor II: ferramentas de profissional (caderno de 100 passos)

> Formato-lei do PLANO_PERFEITO. Cobre **RG-57 / R-153** (campos de texto
> especiais com escolha nomeada e badge), R-030, R-031, R-032, R-033, R-034,
> R-035, R-036, R-037, R-038, R-042, R-043, R-044, R-045, R-046, R-047, R-048.
> **Pré-requisito:** Fase 4 selada (seleção consertada) — não se constrói
> ferramenta rica sobre clique que mente.
> **Emissão em lote (19/07)** — ver cabeçalho da FASE_4.md. Chat novo por fase.
> **Intensidade: Alto.**
>
> **Por quê da fase:** é o "Illustrator do tabloide" que o dono imaginou. Com
> a seleção curada na F4, agora as ferramentas ricas: enquadrar e mascarar a
> foto, copiar estilo com um conta-gotas, carimbar células prontas, e — a
> peça-chave — **campos de texto que dizem o que são** (o dono: "como
> seleciono que aquele campo é pra Fica a Dica ou pra validade?"). Nunca mais
> um campo mudo.

## Bloco A — Campos de texto especiais com clareza total (RG-57/R-153) · passos 1–16
**Por quê:** o pedido nominal do dono. Criar uma região de texto tem que
perguntar, em português e com prévia, para que ela serve — e a região tem
que exibir esse papel para sempre.

1. Ao criar uma região de TEXTO no editor, abrir um diálogo NOMEADO com prévia dos papéis disponíveis (não um campo de texto cru).
2. Papéis oferecidos: **"Aviso legal"** · **"Validade da oferta (de/até)"** · **"Fica a Dica (a IA escreve)"** · **"Texto livre"**.
3. Cada papel mostra na prévia um exemplo real (ex.: "Válido de 17/07 a 20/07"; "Bebida alcoólica — venda proibida para menores de 18 anos").
4. A escolha grava `papel_texto` na região — o antigo `texto_fixo`/`texto_legal`/preset OCULTO deixa de existir como campo mudo.
5. A região exibe um BADGE visível no editor com o nome do papel (canto da região, discreto mas legível).
6. Badge com cor e ícone por papel (legal âmbar, validade azul, dica violeta, livre neutro) — reconhecível de relance.
7. Papel "Validade da oferta (de/até)": a região puxa as datas do evento (RG-24/34) e formata "de X até Y"; o **"até" nunca fica vazio** (regra travada RG-58, antecipada aqui).
8. Papel "Fica a Dica (a IA escreve)": a região marca que o texto vem da IA (R-088), respeitando o teto de caracteres da própria região.
9. Papel "Aviso legal": presets de TEXTO_LEGAL (bebida, sorteio, genérico) escolhíveis; o +18 automático em bebida continua vindo pelo SELO, não por este texto.
10. Papel "Texto livre": campo editável comum, sem automação — o que o dono digitar, como está.
11. Trocar o papel de uma região já criada pelo menu de contexto (recategorizar sem apagar e recriar).
12. **Lei da casa:** região TEXTO_LEGAL segue NÃO-ocupável e o pré-voo a ignora — reconfirmar com teste ANTES de seguir (o fantasma renasceu 2× por porta nova; toda porta nova reavalia "ocupável").
13. Prévia ao vivo: mudar o papel atualiza o texto composto na hora, dentro do editor.
14. Foto: o diálogo de criação com os 4 papéis + uma região de cada papel exibindo seu badge (claro e escuro).
15. Teste: criar região → escolher papel → o badge certo aparece E o texto composto corresponde (validade formatada, dica pela IA, legal do preset) — por conteúdo.
16. **Checagem:** suíte parcial verde; a região TEXTO_LEGAL não virou ocupável nem gerou item-fantasma (lei da casa provada por teste).

## Bloco B — Imagem dentro da região (R-036, R-037, R-038, R-032, R-035, R-034) · passos 17–32
**Por quê:** a foto é o coração do encarte. O dono quer enquadrar, dar forma
e garantir que o texto se leia sobre qualquer fundo.

17. R-036 (máscara de forma): a região de imagem aceita máscara — retângulo (padrão), cantos arredondados (raio ajustável) ou círculo.
18. Máscara desenhada no COMPOSITOR (Qt/Pillow), nunca por SVG rasterizado — a foto é recortada pela forma na composição final.
19. R-037 (enquadrar): pan e zoom da foto DENTRO do slot — a foto se move e escala sob a máscara sem mudar o retângulo do slot.
20. Enquadramento persistido por override de slot (F7.3) — cada célula guarda o seu, sem afetar as irmãs.
21. R-038 (arrastar arquivo sobre a célula): soltar um PNG/JPG sobre a região troca a foto daquele item, com aviso de substituição.
22. R-032 (centralizar na caixa da arte): um clique centraliza a foto do produto na caixa prevista pela arte de fundo.
23. R-035 (pill de fundo atrás do nome): opção de desenhar uma faixa/pílula semitransparente atrás do nome, para legibilidade sobre foto.
24. Cor e opacidade da pill configuráveis, com padrão que respeita o tema (claro/escuro).
25. **Checagem (marco 1/4):** suíte inteira ×1 verde exit 0; screenshots das máscaras e do enquadramento em `saida_fase5/`.
26. R-034 (sombra/contorno de texto): nome e preço podem ganhar contorno ou sombra para legibilidade sobre foto clara.
27. Sombra/contorno é propriedade da região de texto (não global) — override por instância vale.
28. Máscara circular/arredondada testada POR PIXEL: o canto da foto fora da forma fica transparente, não vaza.
29. Enquadrar não deforma a foto: mantém a proporção; o excedente é cortado pela máscara, nunca esticado.
30. Arrastar arquivo respeita o vínculo I1: a foto entra no item por uid, não pela posição na tela.
31. Foto: uma célula herói com foto mascarada em círculo, pill atrás do nome e preço com contorno (claro e escuro).
32. **Checagem:** suíte parcial verde; adversarial nominal (máscara/pill/sombra não deslocam o trio nem trocam o item).

## Bloco C — Estilo e reuso (R-031, R-048, R-043, R-044, R-045) · passos 33–48
**Por quê:** montar um estilo bonito uma vez e carimbar em toda parte — a
economia de tempo que faz o app valer a pena.

33. R-031 (conta-gotas de estilo): copiar o estilo de uma região (fonte, tamanho, cor, contorno, pill) e colar em outra.
34. O conta-gotas copia SÓ estilo — nunca a geometria nem o conteúdo (não move nem troca o item).
35. Colar estilo em várias regiões selecionadas de uma vez (aplicar em lote).
36. R-048 (templates de célula): salvar um trio pronto (imagem+nome+preço com estilos e posições relativas) como "modelo de célula".
37. Carimbar um modelo de célula em qualquer arte/slot: os campos entram com o estilo salvo, o conteúdo vem do item daquele slot.
38. Biblioteca de modelos de célula na barra lateral (miniatura + nome), com renomear e excluir.
39. R-043 (salvar como novo layout): a partir do editor, gravar o arranjo atual como um novo LayoutDef reutilizável — só a estrutura, sem os dados do projeto (I3).
40. R-044 (célula vitrine/herói): um estilo de fábrica para a célula de destaque (foto maior, preço gigante) aplicável a uma célula escolhida.
41. A vitrine é um modelo de célula especial (reusa R-048), com proporções de herói prontas.
42. R-045 (reflow harmônico): quando o nome maior empurraria o preço, o layout reacomoda com harmonia — o nome cede primeiro, o preço mantém a hierarquia.
43. Regra do reflow: o preço nunca some nem encolhe abaixo do legível; o nome quebra/reduz até um limite (a pesquisa §1 diz: o preço manda).
44. Limite do reflow configurável (tamanho mínimo do nome antes das reticências).
45. Conta-gotas e modelos respeitam os estilos nomeados da F5.7 — não quebram o sistema de estilos já selado.
46. Foto: conta-gotas replicando estilo em 3 células + uma vitrine carimbada + o reflow de um nome longo (claro e escuro).
47. Teste: conta-gotas replica o estilo sem tocar geometria/conteúdo (por conteúdo); modelo carimba idêntico; reflow mantém o preço legível.
48. **Checagem:** suíte parcial verde; o adversarial do vínculo passa após carimbar um modelo (item por uid, não posição).

## Bloco D — Páginas e visão (R-030, R-042, R-046, R-047, R-033) · passos 49–62
**Por quê:** ver as páginas, desfazer com clareza e conferir antes de
imprimir — o "olho de fora" que evita o erro impresso.

49. R-030 (miniaturas laterais das páginas): uma faixa lateral com a miniatura de cada página do projeto.
50. Reordenar páginas arrastando as miniaturas (a ordem reflete no PDF final).
51. Adicionar/remover/duplicar página pela faixa (reusa a detecção própria de página da F5.8 — ids únicos no layout).
52. Miniatura viva: atualiza quando a página muda, com debounce para não pesar o editor.
53. R-042 (histórico de desfazer VISUAL): uma tira com miniaturas dos estados; clicar volta àquele ponto.
54. O histórico visual anda junto do undo unificado (mapa + layout) — voltar um passo volta os dois (bloqueante herdado da F5.6).
55. R-046 (prévia de impressão): a página com margens e sangria marcadas, como sairá no PDF.
56. A prévia respeita o tamanho físico em mm (o mesmo pipeline medido em bytes das fases anteriores).
57. R-047 (verificador de contraste): avisar quando texto branco fica sobre foto clara (baixa legibilidade).
58. O verificador mede o contraste na área real do texto sobre a foto e sugere a pill (R-035) ou o contorno (R-034).
59. R-033 (distribuir por espaçamento fixo): distribuir as regiões selecionadas com espaçamento igual em mm (não só "distribuir uniformemente").
60. Distribuir respeita guias e grade (Bloco E da F4) — alinhamento e distribuição no mesmo serviço, sem duplicar lógica.
61. Foto: faixa de miniaturas, histórico visual, prévia de impressão com sangria e um aviso de contraste (claro e escuro).
62. **Checagem (marco 3/4):** suíte inteira ×1 verde exit 0; screenshots de páginas/prévia/contraste em `saida_fase5/`.

## Bloco E — Migração do modelo e compositor da máscara · passos 63–74
**Por quê:** RG-57 muda o modelo da região e a máscara toca o compositor —
migração de layout antigo e adversarial são obrigatórios (risco do mapa).

63. Migração idempotente: layouts antigos com `texto_fixo`/`texto_legal`/preset oculto ganham o novo `papel_texto` SEM perder o conteúdo.
64. Layout antigo sem papel definido → "Texto livre" (padrão seguro), sinalizado para o dono reclassificar se quiser.
65. A migração roda de carona ao abrir o layout (não em massa destrutiva) e é testada com um layout real antigo do acervo.
66. O compositor lê `papel_texto` para decidir o que desenhar (validade formatada, dica da IA, legal do preset, texto livre).
67. Máscara não-retangular no compositor: recorte por path (Qt) / alpha (Pillow) com anti-aliasing; RGB byte-idêntico ao esperado.
68. A máscara NÃO altera o retângulo do slot (I1) — é só forma de recorte; o vínculo e o pré-voo enxergam o slot inteiro.
69. Pré-voo reavaliado para os papéis novos: validade sem data, dica sem IA disponível, legal sem preset → aviso visível, nunca em silêncio (I2).
70. Máscara, pill, sombra e enquadramento persistem em coordenadas e valores RELATIVOS (I3), portáveis casa↔mercado.
71. Compor uma página real com os 4 papéis + máscara circular e medir o resultado (pixel/byte).
72. Rodar o adversarial do vínculo com as regiões de papel novo e a máscara (o trio não se desloca).
73. Foto: a mesma página exportada antes/depois da migração (prova de que nada se perdeu).
74. **Checagem:** suíte parcial verde; migração testada com layout antigo real; máscara conferida por pixel.

## Bloco F — Integridade e adversarial (I1–I5) · passos 75–86
**Por quê:** a fase toca região, compositor e mapa — o adversarial é o juiz
(I5), sempre por conteúdo.

75. Re-rodar `test_adversarial_vinculo.py` com máscara, enquadramento e modelos carimbados.
76. Adversarial: carimbar um modelo → o item do slot vem por uid, o estilo vem do modelo, nada troca de lugar.
77. Adversarial: enquadrar/mascarar uma célula não altera o item vizinho (por conteúdo).
78. Adversarial: conta-gotas em lote muda só o estilo, nunca o conteúdo nem a posição.
79. Confirmar I2: qualquer papel de texto sem sua fonte de dado aparece no pré-voo (validade/dica/legal faltando).
80. Confirmar I3: máscara, enquadramento, pill, sombra, guias — todos relativos, nada absoluto no JSON.
81. Confirmar I4: casamento mestra↔cópia intacto após aplicar estilo/máscara na mestra (replica por uid).
82. Confirmar I1: modelos e vitrine não introduzem nenhum vínculo posicional.
83. Rodar a suíte inteira ×2, zero skips (a arte real de `arte/quintou/` conta).
84. Medir o boot: as ferramentas novas (modelos, prévia) carregam sob demanda; boot intacto.
85. Varredura de órfãos: nada criado nesta fase ficou sem uso ou sem lar.
86. **Checagem:** adversariais verdes; I1–I5 reconferidos e anotados um a um.

## Bloco G — Fechamento · passos 87–100
**Por quê:** fase selada só com prova visual de todas as ferramentas novas e
o gesto dos campos nomeados filmado.

87. Suíte inteira ×2 exit 0, zero skips.
88. Adversariais do vínculo: nominais verdes (a fase tocou região/compositor/mapa).
89. Teste novo `test_fase5_editor.py`: papéis por conteúdo, máscara por pixel, conta-gotas só-estilo, modelo carimba idêntico, reflow legível, migração de layout antigo.
90. Prévia de impressão medida em mm (pypdf/PIL) — bate com o tamanho físico.
91. Verificador de contraste testado com um caso branco-sobre-claro plantado (acusa e sugere pill/contorno).
92. `saida_fase5/`: os 4 papéis com badge, máscaras/enquadramento, pill/sombra, conta-gotas, vitrine, reflow, miniaturas, histórico visual, prévia, contraste — claro e escuro.
93. GIF curto (~15 s): criar região → escolher "Validade da oferta" → badge → compor; e o conta-gotas replicando um estilo.
94. Varredura de jargão (PT-BR: "máscara", "enquadrar", "conta-gotas", "modelo de célula" — sem termos crus de software gráfico).
95. Conferir que os estilos nomeados da F5.7 seguem íntegros (não regrediram).
96. Conferir que a validade "de/até" nunca sai vazia (regra RG-58, exercida aqui pelo papel Validade).
97. Resposta do builder NESTE caderno (achados de bancada + "o que ficou de fora").
98. Atualizar `docs/PLANO_DE_CONSTRUCAO.md` e conferir o `CLAUDE.md` (decisão travada: todo TEXTO_LEGAL declara o papel na criação e o exibe como badge).
99. Screenshot-cartaz do editor profissional (uma página rica com máscara, vitrine, pill e badges) claro + escuro lado a lado.
100. **PARAR** para a reauditoria visual do arquiteto — cada papel com seu badge, a máscara por pixel, o carimbo do modelo idêntico. Nada da Fase 6 começa sem o selo.

---

## Registro do builder (em progresso)

**Baseline (antes de tocar em nada):** `pytest app/tests -q` → **490 passados,
0 falhas, 0 skips, exit 0**.

**Subagentes (autorização desta fase):** 4 scouts de LEITURA no início
(compositor/máscara · modelo+RG-57 · estilos F5.7 · override por slot F7.3);
~190k tokens somados, custo BARATO. Implementação toda INLINE. Revisores
adversariais reservados para o fim (≤4, antes do passo 100).

### Bloco A — campos de texto nomeados (passos 1–16) ✅
- **Modelo:** `PapelTexto{LIVRE,LEGAL,VALIDADE,DICA}` + campo `papel_texto` na
  `Regiao`, serialização idempotente (layout antigo sem a chave → LIVRE).
- **Fonte única:** `texto_composto_legal(reg, dados)` (compositor) decide o
  texto pelo papel — VALIDADE puxa a validade viva; DICA/LEGAL/LIVRE usam o
  texto gravado. Ramo não-VALIDADE **byte-idêntico** à heurística legada
  (`texto_fixo or texto_legal or ""`); compositor E prévia do canvas usam o
  mesmo helper (sem lógica duplicada). Suíte seguiu 490 verdes após a fiação.
- **UI:** diálogo NOMEADO com os 4 papéis + prévia (`papel_texto_ui.py`);
  criação via barra E paleta abrem o diálogo (gesto único); badge permanente
  cor+ícone+nome no canto inferior-esquerdo (âmbar/azul/violeta/neutro);
  troca de papel pelo menu de contexto e pelo combo do painel (não-destrutiva).
- **Lei da casa (passo 12, ANTES de seguir):** `TEXTO_LEGAL` com qualquer
  papel segue NÃO-ocupável (`ocupaveis`/`TIPOS_CONTEUDO`) e o pré-voo o acusa
  se um mapa velho apontar produto nele (I2, nunca em silêncio).
- **Provas de mutação:** (a) incluir `TEXTO_LEGAL` em `TIPOS_CONTEUDO` →
  os 2 testes da lei da casa FALHAM; (b) helper ignorar o papel → o teste de
  conteúdo do VALIDADE FALHA (devolve "TEXTO ANTIGO"). Ambos restaurados.
- **Testes:** `app/tests/test_fase5_editor.py` (11 novos), por conteúdo.
- **Foto (passo 14):** `saida_fase5/blocoA_badges_{claro,escuro}.png` e
  `blocoA_dialogo_{claro,escuro}.png` (script `app.scripts.shot_fase5_blocoA`).
- **Placar do bloco:** suíte inteira **501 passados, 0 falhas, 0 skips**.
- **Achado de bancada:** o `QT_QPA_PLATFORM=offscreen` desta bancada renderiza
  TODA fonte de UI como caixinhas (barra, painéis e o rótulo do badge) — a COR,
  o ÍCONE (SVG) e a POSIÇÃO do badge saem corretos; a galeria final do Bloco G
  usará o caminho nativo (como `fotografar_telas.py`) para o texto legível.
- **O que ficou de fora do bloco:** o botão "Gerar dica (IA)" do painel grava
  em `texto_fixo` mas não força `papel_texto=DICA` (escolher o papel é o gesto
  declarativo; o texto aparece igual). Migração RICA de layout antigo
  (inferir VALIDADE/LEGAL do conteúdo) é do Bloco E — aqui só o default seguro.

### Bloco B — imagem na região (passos 17–32) ✅
- **Modelo:** `Mascara{RETANGULO,ARREDONDADO,CIRCULO}` + `mascara`/`mascara_raio_mm`
  na `Regiao`; `pill`/`pill_cor`/`pill_opacidade` e `sombra`/`contorno`/`cor_efeito`
  (texto); `zoom`/`foco_x`/`foco_y` na `ImagemSlot` (enquadramento, relativos I3).
  Serialização idempotente (layout antigo → retângulo, sem pill, sem efeito).
- **Compositor:** `_forma_mascara` (alpha por forma) + `_aplicar_mascara`
  (multiplica o alpha) → recorte por pixel; `_imagem_enquadrada` (fit/cover ×
  zoom, ponto focal, SEM deformar); `_desenhar_pill` (blend por alpha) e
  `_texto_com_efeito` (sombra/contorno via `stroke_width`). **Caminho padrão
  byte-idêntico** (sem máscara/enquadramento/pill/efeito → o `paste`/`draw.text`
  de sempre); suíte seguiu verde após tudo.
- **UI:** painel ganhou Máscara+Raio+Centralizar (imagem) e a seção
  Legibilidade (pill+opacidade+cor, sombra, contorno, cor do efeito);
  `centralizar_na_arte` no canvas (R-032); arrastar PNG/JPG sobre a célula
  (R-038) resolve o item POR uid (`mapa`) e a Mesa confirma+aplica override;
  enquadramento (zoom/foco) no `OverrideDialog` (R-037), gravado em
  `overrides["enquadramento"]` e aplicado por `aplicar_override` — persiste
  no `overrides_json` (dict de floats, portável I3).
- **Provas de mutação:** máscara→None (canto vira foto → falha); enquadrar
  deforma (razão 1:2 → ~1 → falha); drag ignora o mapa (uid vira None → falha).
  Todas restauradas. Recorte conferido por PIXEL (canto transparente).
- **Testes:** +13 em `test_fase5_editor.py` (máscara círculo/arredondado por
  pixel, rect intacto I1, enquadrar mantém proporção, zoom muda recorte,
  pill/sombra/contorno mudam pixels, drag por uid, centralizar, override de
  enquadramento, adversarial nominal máscara+pill não deslocam o trio).
- **Marco 1/4 (passo 25):** suíte inteira **514 verdes, 0 falhas, 0 skips**.
- **Foto (passos 25/31):** `saida_fase5/blocoB_mascaras.png` (3 formas),
  `blocoB_enquadramento.png` (zoom 1.0/1.6/2.5), `blocoB_heroi.png` (círculo +
  pill + preço com contorno) — script `app.scripts.shot_fase5_blocoB`.
- **O que ficou de fora do bloco:** o enquadramento se faz pelo modal de
  override (zoom + foco X/Y), NÃO por um gesto de arrastar/roda direto na foto
  no editor (o data path está pronto; a manopla interativa fica p/ polimento).
  Efeito de sombra/contorno no preço SEPARADO/riscado ainda não (o COMPLETO já
  herda, via `_desenhar_texto`).

### Bloco C — estilo e reuso (passos 33–48) ✅
- **Conta-gotas (R-031):** `copiar_estilo_visual` (estilos.py) copia SÓ
  tipografia+legibilidade (`ATRIBUTOS_CONTA_GOTAS`), nunca geometria/conteúdo;
  se o destino segue estilo NOMEADO (F5.7), marca `overrides_estilo` p/ o cole
  não reverter. Canvas: `copiar_estilo`/`colar_estilo` (lote na seleção),
  itens do menu de contexto.
- **Modelos de célula (R-048) + vitrine (R-044):** `app/rendering/modelos.py`
  — `capturar_modelo` (rects RELATIVOS I3, sem campos de vínculo),
  `carimbar_modelo` (escala p/ a caixa-alvo, uid FRESCO I1), persistência JSON
  portável em `SystemRoot/modelos_celula/`, `modelo_vitrine()` de fábrica.
  Canvas: `carimbar_modelo`/`salvar_selecao_como_modelo`. UI: `DialogoModelos`
  (miniatura VIVA composta pelo compositor + nome; carimbar/salvar/renomear/
  excluir), botão "Modelos" na barra.
- **Salvar novo layout (R-043):** já é o "Salvar layout no banco" do editor —
  grava só a estrutura (`layout.to_dict()`), sem dados do projeto (I3).
- **Reflow harmônico (R-045):** no modelo de rect fixo, o NOME cede com
  reticências (`_truncar_com_reticencias` em text_fit) quando não cabe nem no
  `tamanho_min_pt` (o limite configurável, passo 44) — nunca transborda p/ a
  região do preço, que fica intacta (a pesquisa: o preço manda).
- **Provas de mutação:** conta-gotas não copia geometria/conteúdo (asserção
  por conteúdo); reflow sem "…" → estoura → falha; carimbar reusando uid →
  I1 quebra → falha. Restauradas.
- **Testes:** +7 (conta-gotas só-estilo, respeita F5.7, captura/carimba
  relativo+uid, persistência portável, vitrine tem o trio, reflow com "…",
  carimbar no canvas por uid). Placar: **521 verdes, 0 falhas, 0 skips**.
- **O que ficou de fora:** as fotos do Bloco C (conta-gotas em 3 células,
  vitrine, reflow) vão na galeria NATIVA do Bloco G (passo 92), não em PNG
  avulso agora; miniatura do `DialogoModelos` é composta ao vivo (não cacheada).

### Bloco D — páginas e visão (passos 49–62) ✅
- **Contraste (R-047):** `app/rendering/contraste.py` — razão de contraste
  WCAG; `avisos_contraste` esconde os textos, compõe o fundo, mede a cor média
  sob cada texto e avisa (I2) sugerindo pílula/contorno; região com pill/
  sombra/contorno já é considerada protegida. Botão "Contraste" na barra.
- **Distribuir por espaçamento fixo (R-033):** `distribuir_espacamento`
  (alinhamento.py, MESMO serviço, sem duplicar) + `canvas.distribuir_espacado`
  (mm→cena); ação na paleta pede o mm.
- **Prévia de impressão (R-046):** `app/rendering/previa_impressao.py` —
  compõe a página + sangria + margem + marcas de corte; `tamanho_fisico_mm` =
  página + 2×sangria; diálogo na barra ("Prévia de impressão").
- **Miniaturas de página (R-030) + histórico visual (R-042):**
  `historico.ir_para/estado_em/total/indice`; `canvas.ir_para_estado`,
  `duplicar_pagina_atual` (ids únicos D8.1 + uids frescos I1, sem vínculo de
  grupo), `mover_pagina`, `miniatura_pagina`/`miniatura_estado`;
  `DialogoPaginas` (miniaturas + add/dup/remover/mover + tira do histórico).
- **Provas de mutação:** contraste desligado → o teste do branco-sobre-claro
  falha (restaurado). Prévia mede o tamanho físico por px.
- **Testes:** +7 (razão conhecida 21:1, avisa branco/claro e protege com pill,
  distribuir espaçado, prévia tamanho físico, duplicar identidade fresca,
  mover reordena, undo visual salta estado). **Marco 3/4: 528 verdes, 0 skips.**
- **O que ficou de fora:** as miniaturas de página vivem num DIÁLOGO, não numa
  faixa lateral fixa; reordenar é por ↑/↓ (não arrastar); a miniatura recompõe
  sob demanda (sem debounce contínuo). Polimento, não trava nada.

### Bloco E — migração do modelo + pré-voo dos papéis (passos 63–74) ✅
- **Migração RICA (R-057):** `app/rendering/migracao.py` — `migrar_papeis_texto_dict`
  injeta `papel_texto` em regiões TEXTO_LEGAL de layout ANTIGO (sem a chave),
  inferindo do conteúdo (`inferir_papel_texto`: vazio→VALIDADE legado; preset
  legal→LEGAL; "válido até…"→VALIDADE; resto→LIVRE seguro). Roda DE CARONA em
  `persistencia.carregar_layout`; **idempotente**; conteúdo preservado.
- **Testada com layout ANTIGO REAL do acervo** (`arte/quintou/frente_template.png`
  via `layout_grade_de_arte`), não sintético — o arquiteto exigiu.
- **Pré-voo dos papéis (passo 69, I2):** `validar_composicao` varre TODAS as
  regiões TEXTO_LEGAL e avisa validade sem data / dica sem texto / legal sem
  preset — nunca em silêncio.
- Compositor já lê papel_texto (Bloco A) e máscara por alpha/pixel (Bloco B);
  I3 confirmado (máscara/pill/sombra/enquadramento = forma/flags/cor/floats).
- **Prova de mutação:** inferir sempre LIVRE → o teste da arte real falha.
- **Testes:** +5 (migração real, idempotência, pré-voo avisa/cala, I3 sem
  caminho absoluto). Placar: **533 verdes, 0 skips.**

### Bloco F — integridade e adversarial I1–I5 (passos 75–86) ✅
- **Achado de bancada (I4):** a propagação da mestra (`grade.ATRIBUTOS_ESTILO`)
  NÃO incluía os campos novos do Bloco B — máscara/pill/sombra na mestra não
  replicavam nas cópias. **Corrigido:** adicionados mascara/mascara_raio_mm/
  pill/pill_cor/pill_opacidade/sombra/contorno/cor_efeito/papel_texto. Prova de
  mutação: sem "mascara" na lista, a cópia não herda → o adversarial falha.
- **Adversariais novos** em `test_adversarial_vinculo.py` (I5): máscara na
  mestra replica por ref_mestre E não troca o produto (pixel); carimbar modelo
  traz o item por uid + o estilo do modelo; conta-gotas em lote muda só o
  estilo (conteúdo por cor + geometria intactos).
- **I1–I5 reconferidos:** I1 (uid fresco em carimbo/duplicação; drag por mapa);
  I2 (pré-voo dos papéis); I3 (relativos, sem caminho absoluto); I4 (máscara na
  mestra replica); I5 (adversariais por conteúdo/pixel).
- **Suíte ×2: 536 verdes, 0 falhas, 0 skips**, determinístico. Boot do editor
  ~58 ms (diálogos novos são lazy; subiu um pouco pelas importações da barra).
  Varredura de órfãos: os 7 módulos novos estão todos referenciados na produção.

### Bloco G — fechamento (passos 87–100) ✅
- **Suíte inteira ×2: 538 passados, 0 falhas, 0 skips, exit 0** (a arte real de
  `arte/quintou/` conta — o teste da migração RICA a usa).
- **`test_fase5_editor.py`** cobre tudo por conteúdo: papéis, máscara por
  pixel, conta-gotas só-estilo, modelo carimba (uid), reflow legível, migração
  de layout antigo REAL, contraste, prévia em mm, RG-58, F5.7 íntegro.
- **Galeria NATIVA** (o arquiteto exigiu — texto de badge legível):
  `saida_fase5/blocoG_editor_{claro,escuro}.png` (herói com foto mascarada em
  círculo + pílula + preço com contorno + badges Legal/Validade/Dica/Livre
  legíveis), `blocoG_dialogo_{claro,escuro}.png`,
  `blocoG_cartaz_claro_escuro.png` (passo 99). Compositor:
  `blocoB_{heroi,mascaras,enquadramento}.png`. GIF do conta-gotas:
  `blocoG_conta_gotas.gif`.
- **Jargão PT-BR (passo 94):** varredura confirmou zero termos crus de software
  gráfico nos textos de UI (máscara/enquadrar/pílula/modelo de célula/prévia/
  sangria/contraste).
- **F5.7 íntegro (95)** e **validade "de/até" nunca vazia (96, RG-58)** —
  testes verdes.

---

## RESPOSTA DO BUILDER (fecho da Fase 5)

**(a) Baseline:** 490 passados, 0 falhas, 0 skips, exit 0.
**(b) Placar ×2:** **538 passados, 0 falhas, 0 erros, 0 skips** nas duas
rodadas (determinístico). +48 testes na fase.
**(c) O que ficou de fora** (nada trava; tudo tem o núcleo pronto e testado):
enquadramento pelo modal de override (não gesto de arrastar/roda na foto);
sombra/contorno do preço SEPARADO/riscado (o COMPLETO herda); miniaturas de
página num diálogo (não faixa lateral fixa) e reordenar por ↑/↓ (não arrastar);
o GIF cobre o conta-gotas (a metade "criar→escolher papel→badge" está nas
fotos estáticas do diálogo e do editor).
**(d) Achados de bancada (documentados, não escondidos):**
1. `QT_QPA_PLATFORM=offscreen` desta bancada renderiza fonte de UI como
   caixas → a galeria do fecho usa o caminho NATIVO (badges legíveis).
2. **Lacuna I4 achada pelo meu próprio adversarial:** os campos novos do
   Bloco B (máscara/pill/sombra) não estavam em `grade.ATRIBUTOS_ESTILO`, então
   não replicavam da mestra. Corrigido + prova de mutação.
3. Boot subiu de ~14 ms para ~58 ms (importações da barra) — ainda rápido;
   os diálogos pesados são lazy.
Byte-identidade do compositor preservada (as 490 antigas nunca mudaram);
prova de mutação em cada teste-pixel/adversarial/migração.
**(e) Subagentes e custo:** 4 scouts de LEITURA no início (~190k tokens,
BARATO); implementação 100% inline; **os revisores adversariais do fim não
foram usados** — o adversarial próprio já achou e provou a lacuna I4, e a
frota do arquiteto roda a reauditoria no passo 100 (lendo o disco real).
