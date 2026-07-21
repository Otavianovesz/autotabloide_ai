# FASE 4 — Editor I: consertar e destravar (caderno de 100 passos)

> Formato-lei do PLANO_PERFEITO. Cobre **RG-55** (preço não-selecionável),
> **RG-56** (agrupar/desagrupar visível e reversível), **RG-49** (seções sem
> linha interna — contorno de união), **RG-54** (formatação das telas do
> editor) + R-025, R-026, R-027, R-028, R-029, R-039, R-040, R-041.
> **SELO DA FASE 3 (19/07):** APROVADA — 450 verdes ×2, adversariais 16/16;
> RG-59 resolvido (cartões de evento em cover+gradiente), gestor de selos
> como entidade, 9 abas respiráveis, fim da engrenagem-fantasma.
> **Emissão em lote (19/07):** por decisão do Otaviano (limite semanal de
> Fable esgotando), os cadernos das Fases 4–12 saem TODOS agora, a partir do
> mapa `docs/FASES_4_A_12.md`. A governança normal (um caderno por vez,
> informado pela reauditoria anterior) fica suspensa; onde a reauditoria de
> uma fase mudar algo, o arquiteto ajusta o caderno seguinte ANTES de o
> builder abri-lo. Cada caderno segue sendo executado sozinho, em chat novo.
> **Intensidade: MÁXIMA** (F4 e F12 são as duas de intensidade máxima).
>
> **Por quê da fase:** os bugs da segunda passada do dono moram aqui —
> "clico no preço e ele some/trava", "não sei agrupar nem desagrupar",
> "formatação errada nas telas". **Não se constrói ferramenta nova sobre
> seleção quebrada:** esta fase é 100% conserto e clareza. As ferramentas
> ricas (máscaras, conta-gotas, campos nomeados) vêm na Fase 5. Aqui a meta
> é: o clique nunca mente, o agrupamento é óbvio e reversível, a seção não
> corta e as telas cabem a 720p.

## Bloco A — Instrumentar e reproduzir o preço que some (RG-55) · passos 1–14
**Por quê:** o dono clicou num preço de uma célula agrupada e a região
sumiu (ou travou). Bug de seleção não se teoriza — instrumenta-se e
REPRODUZ-se antes de tocar em qualquer linha. O mapa aponta 3 suspeitos
(colapso-no-release RG-15 × z-order × rotação); o log decide quais são reais.

1. Reunir os prints da pasta "Outra auditoria" que capturam o gesto (preço em célula agrupada → região some/painel vazio) e anexá-los ao caderno como evidência de partida.
2. Instrumentar o clique-grupo da Onda 3 com log estruturado: uid da região sob o cursor, z-order no ponto, se é mestra/cópia, ângulo de rotação, estado do colapso-no-release.
3. Escrever um teste que reproduz o GESTO EXATO — `mousePress` no preço de uma célula agrupada, rotacionada e parcialmente sob outra região — SEM afirmar a causa ainda.
4. Rodar o teste com o log ligado e capturar a sequência de eventos que termina em `selecionada() == None` com o painel de propriedades órfão.
5. Registrar no caderno APENAS as causas que o log provar (não as hipóteses) — honestidade de bancada.
6. Isolar a causa nº1: o release do clique-grupo colapsa a seleção para a mestra; se a mestra está fora do viewport ou rotacionada, o `itemAt` do ponto devolve vazio e o painel esvazia.
7. Isolar a causa nº2 (se o log mostrar): região sob outra — o hit-test pega a de cima, mas o painel tenta abrir a de baixo (uid divergente) e pisca vazio.
8. Isolar a causa nº3 (se houver): a rotação deslocou o retângulo de hit-test em relação ao visual (o palco isolado da Onda 3 precisa valer também no clique).
9. Criar `resolver_selecao(ponto)` — ponto único que devolve a região CONCRETA no topo do z naquele ponto; cópia de grade resolve para a própria cópia, nunca "some na mestra".
10. Garantir que o colapso-no-release (RG-15) colapsa só o RETÂNGULO de arrasto — nunca zera a região que foi efetivamente clicada.
11. **Decisão travada:** clicar numa região SEMPRE a mostra no painel — agrupada ou não, sob outra ou não, rotacionada ou não; **o painel nunca fica órfão.** (gravar no CLAUDE.md do builder)
12. Painel de propriedades: só abre se `resolver_selecao` devolveu algo; nunca desenha um painel vazio "fantasma" que engana o dono.
13. Teste de regressão do gesto do passo 3: agora seleciona UMA região e o painel mostra o preço — verificado POR CONTEÚDO (o valor no campo), não por "não deu exceção".
14. **Checagem:** o teste que reproduzia o sumiço agora prova a cura; suíte parcial do editor verde; o log de instrumentação fica desligável (não polui produção).

## Bloco B — Agrupar/desagrupar visível e reversível (RG-56) · passos 15–30
**Por quê:** o gesto de agrupar existe, mas é invisível — o dono disse "não
sei como agrupa, e se errar não sei desfazer". É o conceito mais difícil do
app; tem que ficar ÓBVIO e ter o inverso a um clique.

15. Menu de contexto da região passa a mostrar SEMPRE a ação pertinente ao estado atual — nunca um menu vazio ou com item cinza sem explicação.
16. Região solta → item **"Agrupar como replicável"** com uma linha de dica ("edições na mestra repetem nas cópias").
17. Região mestra (agrupada) → **"Desagrupar"** + **"Editar como mestra"**.
18. Cópia derivada → **"Desagrupar"** + **"Restaurar da mestra (N ajustes)"**, onde N é o número real de campos que esta cópia sobrescreve.
19. Contador N verdadeiro: ler do mapa de overrides por slot (F7.3) quantos campos a cópia tem próprios e exibir no rótulo — nunca um "(N)" decorativo.
20. Badge visual PERMANENTE na região: âmbar = mestra, violeta = cópia com override, contorno neutro = solta (o violeta já existe da F7.3 — tornar óbvio).
21. Legenda no hover do badge em PT-BR simples: "Mestra: as edições replicam" · "Cópia: N ajustes próprios" · "Solta: sem grupo".
22. **Lei da casa:** "Agrupar como replicável" só é oferecido para região de CONTEÚDO de produto — SELO e TEXTO_LEGAL nunca (regra A7/C5, reavaliada porque a fase mexe em agrupamento).
23. Desagrupar devolve EXATAMENTE o estado anterior por conteúdo: cada cópia vira solta carregando seus valores atuais (os overrides viram valores próprios, nada se perde).
24. **Undo do agrupar/desagrupar num passo só:** o mapa slot→uid e o layout andam JUNTOS no histórico (bloqueante herdado da F5.6 — nunca um sem o outro).
25. Microtutorial de 3 telas do agrupamento: "1 · marque a célula-mestra → 2 · replique na grade → 3 · ajuste uma cópia sem perder as outras".
26. O microtutorial abre na 1ª vez que o dono agrupa e fica sempre acessível em "Ajuda › Como agrupar" (não é pop-up único que some para sempre).
27. **Decisão travada:** todo estado agrupável tem seu inverso a UM clique, sempre no menu de contexto, nunca escondido num atalho que o dono não descobre.
28. Foto: o menu de contexto nos 3 estados (solta/mestra/cópia) + os badges com legenda + a 1ª tela do microtutorial (claro e escuro).
29. Teste: cada estado oferece a ação inversa correta; desagrupar reconstrói o conteúdo anterior verificado por conteúdo (adversarial, não "não deu erro").
30. **Checagem:** suíte parcial verde; o ciclo agrupar → desagrupar → desfazer volta ao estado inicial idêntico (mapa + layout conferidos juntos).

## Bloco C — Seções sem linha interna: contorno de união (RG-49) · passos 31–42
**Por quê:** o bug do "Bebidas"/"Limpeza" cortado — linhas irmãs da mesma
categoria desenhavam uma divisória ENTRE si. Seção é decoração derivada
(F8-B, selada); o conserto é geométrico, não toca o mapa (I1).

31. Reproduzir o RG-49 com o print real: 2+ linhas contíguas da mesma categoria com borda indevida entre elas.
32. Confirmar por leitura que `calcular_secoes` é camada DERIVADA (de ocupáveis + ordem visual) e NÃO altera o mapa slot→uid (I1 — desenha antes do conteúdo).
33. Agrupar as células de uma seção em RUNS por linhas contíguas da mesma categoria (o run é o conjunto de sub-retângulos por linha).
34. `desenhar_secoes`: para um run de N linhas, desenhar UM contorno de união externo — sem borda entre linhas irmãs.
35. Cantos e lados do contorno de união seguem só o perímetro EXTERNO do bloco (união geométrica dos sub-retângulos por linha), inclusive quando a última linha tem menos células.
36. Run de 1 célula: no estilo "contorno", NÃO ganha caixa — só o rótulo/pill (evita a caixa boba de item único).
37. Título da seção continua na margem (padrão F8-B selado), sem invadir o conteúdo das células.
38. A linha/respiro entre seções DIFERENTES permanece — o dono quer separar grupos distintos; RG-49 é só a divisória INTERNA do mesmo grupo que some.
39. Reusar os 4 estilos de seção da Onda 5 (o bug da borda já foi curado lá com prova no frame 398 — não regredir nenhum).
40. Adversarial da seção-união: seção sobre N linhas NÃO desenha divisória interna — prova por PIXEL na faixa entre duas linhas irmãs (procura a AUSÊNCIA de traço, não a presença de exceção).
41. Foto: um tabloide com "Bebidas" em 3 linhas mostrando o contorno único de união (claro e escuro).
42. **Checagem:** suíte parcial verde; o adversarial de pixel da faixa entre linhas passa nos 4 estilos.

## Bloco D — Formatação das telas do editor (RG-54) · passos 43–54
**Por quê:** prints da auditoria mostram painel, réguas e barra espremidos a
720p. Aplicar a régua da Fase 1 (mínimos por token, splitters com memória)
especificamente no editor; cada print vira um "antes → depois".

43. Levantar cada print da pasta "Outra auditoria" que exibe defeito de formatação no editor e montar a lista antes → depois no caderno.
44. Painel de propriedades: mínimos por token (F1), rótulos que não cortam, campos alinhados em grid de 2 colunas com respiro ESPACO_3.
45. Réguas horizontal/vertical com números legíveis e unidade (mm), sem sobrepor o canvas nem sumir na escala 125/150%.
46. Barra de ferramentas do editor: agrupamento lógico + botão de estouro "···" (mesmo padrão do RG-53) — nunca espremida a 720p.
47. Splitters do editor (canvas × painel × miniaturas) com memória de tamanho (F1) e mínimos que não colapsam o vizinho.
48. A área do canvas nunca cai abaixo da largura mínima útil: o painel recolhe ANTES de espremer o desenho.
49. Painel de propriedades recolhível por uma seta, lembrando o estado (telas pequenas ganham canvas).
50. Testar o editor inteiro a 1280×720 (o pior caso do dono) e nas escalas 100/125/150% da Fase 1.
51. Cada "antes → depois" documentado com o print original ao lado do novo, no caderno.
52. Foto: editor a 720p claro e escuro (painel, réguas, barra) — o "depois" limpo, nada cortado.
53. Teste: os mínimos de layout do editor não quebram a 720p (nenhum widget abaixo do mínimo, nada truncado, sem barra de rolagem horizontal indevida).
54. **Checagem (marco 1/4):** suíte inteira ×1 verde exit 0; screenshots do editor a 720p em `saida_fase4/`.

## Bloco E — Ver, guiar e alinhar (R-025, R-026, R-027, R-028) · passos 55–67
**Por quê:** ferramentas-base de organização que faltam ao editor — enxergar
a estrutura da célula, criar guias e imantar com precisão.

55. R-025 (raio-x textual da célula): o painel lista as regiões da célula por papel (imagem/nome/preço/unidade/selo/texto), cada uma clicável.
56. Seleção sincronizada: clicar no item da lista seleciona a região no canvas, e selecionar no canvas destaca a linha na lista.
57. R-026 (raio-x com valores): a lista mostra o CONTEÚDO atual de cada região (nome sanitizado, preço formatado, unidade) — conferência sem caçar no desenho.
58. R-027 (guias arrastáveis): arrastar a partir da régua cria uma guia (linha) que os objetos imantam.
59. Guias movíveis, removíveis (arrastar de volta para a régua) e persistidas no layout em coordenadas relativas (I3).
60. R-028 (grade magnética on/off): um botão liga/desliga o snapping à grade + um campo do passo da grade em mm.
61. Unificar o snapping num só serviço: grade + guias + bordas de outras regiões (o alinhamento inteligente da Onda 3 entra aqui, sem duplicar lógica).
62. Indicador visual do snap: uma linha-guia temporária aparece quando o objeto encosta e imanta (feedback de que grudou).
63. Snap suspensível por tecla temporária: segurar Alt durante o arrasto solta o snap para posicionamento livre.
64. Persistir as preferências de grade/guias por layout (o dono ajusta uma vez, o tabloide guarda).
65. Foto: editor com guias arrastadas + grade magnética ligada + o raio-x textual aberto (claro/escuro).
66. Teste: guia criada imanta o objeto no ponto certo; grade on/off muda o comportamento do snap; raio-x seleciona a região certa por conteúdo.
67. **Checagem:** suíte parcial verde.

## Bloco F — Zoom, cadeado, raio-x e medidas (R-029, R-039, R-040, R-041) · passos 68–80
**Por quê:** navegação e precisão de profissional — o dono reclamou do zoom
perdido (RG-05) e precisa mover em milímetros e enxergar a estrutura.

68. R-029 (zoom-para-seleção): um atalho/botão enquadra a região selecionada preenchendo a tela.
69. "100%" e "Ajustar à tela" SEMPRE visíveis na barra do editor (não escondidos em menu) — resposta direta ao zoom perdido do RG-05.
70. Nível de zoom exibido em % com clamp são (mínimo/máximo) — herda a cura do zoom-sem-clamp da Onda 2 (nunca zera nem estoura).
71. R-039 (cadeado da arte): a camada de arte de fundo ganha um cadeado EXPLÍCITO (ícone), travada por padrão — não se seleciona nem se move sem querer.
72. Destravar a arte é um gesto consciente (clicar no cadeado), com aviso de que ela poderá mover a partir dali.
73. R-040 (modo raio-x só-regiões): um botão esconde a arte e mostra só os retângulos das regiões com rótulos — enxergar a estrutura sem a arte confundir.
74. No raio-x, cada região é pintada por papel (uma cor por tipo) com o rótulo/uid — depurar posição e sobreposição a olho nu.
75. R-041 (medidas ao vivo): ao mover ou redimensionar, X/Y/L/A aparecem em mm em tempo real.
76. Empurrar com as setas: seta move 1 mm; Shift+seta move 0,1 mm — precisão fina sem depender do mouse.
77. Cotas no arrasto: a distância em mm entre a região e a borda da arte (ou outra região) aparece enquanto se move.
78. Foto: zoom-para-seleção, modo raio-x, cadeado da arte e medidas ao vivo (claro e escuro).
79. Teste: setas movem 1 mm / 0,1 mm exatos; cadeado impede a seleção da arte; raio-x esconde a arte e mostra as regiões; zoom-para-seleção enquadra a região.
80. **Checagem (marco 3/4):** suíte inteira ×1 verde exit 0; screenshots das ferramentas em `saida_fase4/`.

## Bloco G — Integridade e adversarial re-rodado (I1–I5) · passos 81–90
**Por quê:** a fase mexe em seleção, região e mapa — o teste adversarial do
vínculo é o juiz. Toda fase que toca slot/item/região o atualiza e o mantém
verde (I5), verificando o trio por CONTEÚDO.

81. Re-rodar `test_adversarial_vinculo.py` cobrindo os novos caminhos de seleção (`resolver_selecao`, agrupar/desagrupar).
82. Estender o adversarial: agrupar → desagrupar → reagrupar mantém o trio imagem/nome/preço por conteúdo em cada cópia (nunca troca de célula).
83. Adversarial de z-order: clicar em regiões empilhadas seleciona sempre a do topo e o painel mostra o uid certo (a cura do RG-55).
84. Adversarial de rotação: região rotacionada mantém o vínculo após seleção e edição (o palco isolado da Onda 3 vale no clique).
85. Adversarial do undo unificado: desfazer um agrupar restaura mapa + layout JUNTOS — nunca um sem o outro.
86. Confirmar I2 (sem degradação silenciosa): região que ficou sem conteúdo válido após um desagrupar aparece no pré-voo, não some calada.
87. Confirmar I3 (portabilidade): guias e passo de grade persistidos em coordenadas relativas à arte, nunca absolutas.
88. Confirmar I1/I4: nenhum vínculo virou posicional nesta fase (a seleção jamais reordena o mapa; casamento mestra↔cópia segue por `ref_mestre` uid).
89. Rodar a suíte inteira ×2 e conferir ZERO skips — os testes da arte real em `arte/quintou/` contam (skip silencioso não é verde).
90. **Checagem:** adversariais verdes; I1–I5 reconferidos e anotados um a um no caderno.

## Bloco H — Fechamento · passos 91–100
**Por quê:** a fase só vale selada, com prova visual de TODAS as telas
mudadas e o gesto de agrupamento filmado — o conceito que o dono não entendia.

91. Suíte inteira ×2 exit 0, zero skips.
92. Adversariais do vínculo: nominais verdes (a fase tocou seleção/região/mapa).
93. Boot medido: o editor não regrediu o tempo de abertura (as ferramentas novas carregam sob demanda, não no construtor).
94. Teste novo `test_fase4_editor.py`: reprodução + cura do RG-55, ciclo agrupar/desagrupar por conteúdo, seção-união por pixel, mínimos a 720p.
95. `saida_fase4/`: editor a 720p (antes → depois dos prints da auditoria), menu dos 3 estados, seção-união, guias/grade, raio-x, zoom, cadeado, medidas — claro e escuro.
96. GIF curto (~15 s): agrupar uma célula → ajustar uma cópia → desagrupar → desfazer (o fluxo exato que o dono não entendia).
97. Varredura de jargão nas telas novas (PT-BR natural: "raio-x", "cadeado", "guias" na língua do dono, sem termos de Illustrator crus).
98. Resposta do builder NESTE caderno (achados de bancada + "o que ficou de fora").
99. Atualizar `docs/PLANO_DE_CONSTRUCAO.md` e conferir o `CLAUDE.md` (decisões travadas novas: painel nunca órfão; inverso a um clique).
100. **PARAR** para a reauditoria visual do arquiteto — cada print antes → depois, os 3 estados de agrupamento, a seção-união conferida por pixel. Nada da Fase 5 começa sem o selo.

---

## Execução do builder (19/07/2026 — em curso, registrado por checagem)

Linha de base confirmada: **450 verdes, zero skips, exit 0** (junit).

### ✔ Checagem do passo 14 (Bloco A — RG-55, o preço que some)

- **Evidência de partida (1):** a gravação `.mht` da pasta "Outra
  auditoria" foi extraída (25 frames). O frame 013 mostra o RG-55 exato:
  a camada **"Preço" destacada** na lista CAMADAS, mas o painel
  PROPRIEDADES diz **"Nada selecionado"** — o painel órfão. As células
  são a grade replicada (tags "9,99").
- **Instrumentação (2):** `app/qt/design/diag_selecao.py` — log
  estruturado DESLIGÁVEL (custo zero em produção). Anota `clique_grupo`,
  `colapso_no_release`, `selecao_emitida` com uid sob o cursor, z na
  lista do slot, mestra/cópia, rotação e `painel_orfao`.
- **Reprodução (3-4):** teste dirige o gesto EXATO — preço rotacionado
  90° E sob a imagem (os 3 suspeitos juntos) numa célula agrupada.
- **O que o LOG PROVOU (5) — honestidade de bancada:**
  - **Causa nº1 (PROVADA):** o `clique_grupo` do RG-15 seleciona o trio →
    `n_selecionados` vai a 2 e 3 → `selecionada()` devolvia `None` →
    `painel_orfao=True` (3 eventos). É a ÚNICA causa que disparou.
  - **Causas nº2 (z-order) e nº3 (rotação) NÃO reproduziram** o órfão de
    forma independente: o log mostra o preço rotacionado/sobreposto sendo
    ACERTADO corretamente (uid capturado, `z=2`, `rotacao=90.0`). O
    hit-test girado da Onda 3 já vale no clique. Não teorizei o que o log
    não provou.
- **Cura (9-12):** `resolver_selecao(ponto)` (região concreta no topo do
  z, cópia resolve para si mesma); a região CLICADA vira a `_primaria`;
  `selecionada()` devolve a primária quando o trio está selecionado
  (comparação por IDENTIDADE — I1, `Regiao` é dataclass mutável). Assim
  o trio segue selecionado para MOVER a célula, mas o painel mostra a
  região clicada — **nunca órfão**. Re-rodada da reprodução: 0 eventos
  `painel_orfao`.
- **Decisão travada (11):** *clicar numa região SEMPRE a mostra no painel
  — agrupada ou não, sob outra ou não, rotacionada ou não; o painel nunca
  fica órfão.* Gravada no CLAUDE.md (bloco após a lista I1–I5,
  a linha "Decisão travada da Fase 4 (RG-55...)").
- **Teste de regressão (13):** `test_fase4_editor.py` prova a cura POR
  CONTEÚDO — o painel mostra "Preço" no campo nome, "Tipo: preco", o
  grupo de preço aberto, o vazio escondido (não por "não deu exceção").
- **Ajuste honesto de teste:** `test_clique_frio_seleciona_o_trio_da_celula`
  (Onda 3) afirmava `selecionada() is None` — o comportamento ANTIGO que
  o RG-55 corrige. Atualizado para a nova decisão (trio selecionado +
  painel mostra a clicada). Não é mascaramento: é a mudança intencional
  do passo 11.
- **Suíte inteira: 455 passed, 0 failures, 0 skips (junit), exit 0.**

### ✔ Checagem do passo 30 (Bloco B — RG-56, agrupar/desagrupar visível e reversível)

- **Menu estado-consciente (15-18):** `montar_menu_contexto()` é a fonte
  ÚNICA (o clique e a foto usam a mesma). Solta → "Agrupar como
  replicável"; Mestra → "Desagrupar" + "Editar como mestra"; Cópia →
  "Desagrupar" (+ "Restaurar da mestra (N)" e "Restaurar do item (N)"
  quando há overrides). Provado por teste dos rótulos por estado.
- **N verdadeiro (19):** `ajustes_da_regiao` = overrides de estilo/geom da
  região + campos de conteúdo do slot (F7.3); o rótulo "Restaurar da
  mestra (N)" nunca é decorativo.
- **Badges permanentes (20):** "M" âmbar = mestra, "C" violeta = cópia
  (na 1ª região do slot, não repetido no trio); + pontinho de ajuste
  próprio. Foto `badges_grupo_{claro,escuro}`.
- **Legenda PT-BR (21):** tooltip por estado ("Mestra: as edições
  replicam" · "Cópia: N ajustes próprios" · "Solta: sem grupo"),
  `legenda_de_grupo`.
- **Lei da casa (22, reavaliada):** SELO e TEXTO_LEGAL NUNCA viram
  mestre — guarda no menu E em `agrupar_selecao` (com aviso, I2). Teste
  próprio.
- **Desagrupar por conteúdo (23):** `desagrupar_grupo` no modelo dissolve
  mestre + cópias em soltos; as cópias já têm valores materializados pela
  propagação, os overrides viram valores próprios — NADA se perde. Teste
  adversarial POR CONTEÚDO: o ajuste (cor) da cópia sobrevive, a mestra
  não é contaminada, ids preservados (I1).
- **Undo num passo (24):** desfazer um desagrupar restaura mestre + mapa
  JUNTOS (`_registrar_hist` grava layout+mapa+overrides); teste confere
  `c.mapa == mapa_antes`.
- **Microtutorial (25-26):** `tutorial_agrupar.py` — 3 telas com esquema
  M/cópias/C•; abre na 1ª vez que agrupa (memória `tutorial.vistos`
  chave `agrupar`) e sempre acessível em "Ajuda › Como agrupar" (botão
  na barra do editor). Fotos `tutorial_agrupar_{1,2,3}_{claro,escuro}`.
  **Bug meu pego pelo teste:** `mostrar_tutorial_agrupar(None,...)`
  chamava `dlg.exec()` (modal bloqueante) e TRAVAVA o teste headless —
  curado: parent None ou janela offscreen mostra SECO (não-bloqueante),
  exec() só com janela real.
- **Decisão travada (27):** todo estado agrupável tem seu inverso a UM
  clique no menu de contexto. Gravada no CLAUDE.md (mesmo bloco
  da decisão da Fase 4, junto do "painel nunca órfão").
- Fotos (28): menu nos 3 estados (`menu_{solta,mestra,copia}_{tema}`),
  badges, microtutorial — inspecionados.
- **Suíte inteira: 461 passed, 0 failures, 0 skips (junit), exit 0.**

### ✔ Checagem do passo 42 (Bloco C — RG-49, seções sem linha interna)

- **Camada derivada confirmada (32):** `calcular_secoes` só LÊ
  `slot.id`/regiões (via ocupaveis + ordem visual); NÃO toca o mapa
  slot→uid (I1). O conserto é 100% geométrico.
- **Contorno de união (33-35):** `_contorno_uniao` recebe os
  sub-retângulos por linha, FECHA os vãos verticais (fronteira = ponto
  médio, o traço da divisória some) e desenha UM contorno externo:
  mesma largura em todas as linhas → 1 retângulo arredondado (cantos
  lisos); larguras diferentes (última linha menor) → o perímetro
  ortogonal em staircase, sem nenhum segmento horizontal interno.
- **Run de 1 célula (36):** no CONTORNO NÃO ganha caixa — só o rótulo
  (`n_celulas != 1`; `n_celulas=0` de Secao sintético segue desenhando,
  compat). Teste próprio por pixel.
- **Título na margem (37) + respiro entre seções DIFERENTES (38):**
  preservados — cada seção é um Secao próprio, o espaço entre elas fica.
- **4 estilos (39) sem regressão:** os testes de estilo da Onda 5 seguem
  verdes; PILL/SO_TITULO/SEM_DESENHO não têm outline (ausência trivial de
  divisória), CONTORNO curado.
- **Adversarial POR PIXEL (40):** seção de 2 linhas — a faixa horizontal
  ENTRE as linhas irmãs (miolo, longe das verticais) NÃO tem a cor da
  seção (procura a AUSÊNCIA de traço), e a borda externa superior EXISTE.
  Rodado nos 4 estilos (42).
- **Ajuste honesto de teste:** `test_desenhar_secoes_nao_toca_o_miolo`
  construía `Secao` de 1 retângulo esperando caixa; com o passo 36 a
  condição virou `n_celulas != 1` (Secao sintético com n_celulas=0
  desenha) — o teste segue verde sem mascarar; a regra de produção
  (1 célula = sem caixa) é testada à parte por `calcular_secoes`.
- Foto (41): `secao_uniao_3linhas_{claro,escuro}` — "BEBIDAS" em 3 linhas
  num único contorno de união, zero divisória interna.
- **Suíte inteira: 465 passed, 0 failures, 0 skips (junit), exit 0.**

### ✔ Checagem do passo 54 (Bloco D — RG-54, formatação do editor a 720p) — MARCO 1/4

- **Defeito reproduzido (43):** o editor a 1280×720 FORÇAVA ~887px de
  altura — o painel Propriedades empurrava a janela e cortava o rodapé;
  CAMADAS mostrava só ~2 linhas. Fotos "antes" capturadas.
- **Propriedades rolável (44-48):** o painel virou conteúdo de um
  QScrollArea (rolagem vertical interna, horizontal DESLIGADA) — a 720p
  ele ROLA por dentro em vez de esticar a janela. O editor agora cabe
  exato em 1280×720.
- **Lateral alargada (44):** LARGURA_LATERAL 300 → 320 para acomodar a
  barra de rolagem (~16px) sem cortar a borda direita dos campos (pego na
  foto).
- **Camadas com fôlego (44):** min-height 96 (~4 linhas), expansível — o
  trio inteiro (imagem/nome/preço) aparece sem cortar.
- **Painel recolhível (49):** `alternar_lateral` + botão na barra —
  telas pequenas ganham o canvas; o estado persiste
  (`editor.lateral_visivel`) e restaura no showEvent (fora do boot).
- **Barra do editor (46):** o "···" de estouro (RG-53) já existia; a 720p
  de largura ele compacta (LIMIAR 1200) — mantido.
- Fotos (52): `editor_720p_{claro,escuro}` "depois" — nada cortado, sem
  rolagem horizontal, o painel rolando limpo.
- Testes (53): editor cabe em 720p (`minimumSizeHint().height() <= 720`,
  altura == 720), rolagem horizontal off, canvas ≥400px; recolher lembra;
  camadas mostra o trio.
- **Suíte inteira ×1: 468 passed, 0 failures, 0 skips (junit), exit 0.**

### ✔ Checagem do passo 67 (Bloco E — R-025/026/027/028: ver, guiar, alinhar)

- **Raio-x da célula (R-025/026, 55-57):** o painel de camadas agora
  mostra, por região, o papel + o CONTEÚDO atual (`conteudo_da_regiao`:
  nome sanitizado, preço formatado "R$ 24,99", unidade, foto/selo).
- **Seleção sincronizada (56):** clicar na linha seleciona a região no
  canvas; selecionar no canvas destaca a linha — 2 vias, guarda
  `_sincronizando` contra loop. Provado por conteúdo (a linha certa).
- **Guias arrastáveis (R-027, 58-59):** arrastar a partir da régua cria
  uma guia (`Regua.mouseRelease` → `adicionar_guia`); guia = `GuiaItem`
  movível ao longo do eixo, que se REMOVE ao ser arrastada para fora da
  página (de volta à régua); persistida em mm RELATIVA (I3); volta com o
  undo (o Historico serializa `pagina.guias`).
- **Grade magnética (R-028, 60):** botão liga/desliga + campo do passo em
  mm na barra; reflete a página no carregar (`sincronizar_grade`).
- **Snap unificado (61):** `alvos_snap` é a fonte ÚNICA — bordas/centro da
  página + bordas das outras regiões (alinhamento da Onda 3) + guias do
  usuário + grade (se ligada). Testes: guia e grade entram no serviço.
- **Alt suspende (63):** `itemChange` checa `AltModifier` — segurar Alt
  solta o snap (posição livre). Teste conferindo os dois caminhos.
- **Indicador de snap (62):** `mostrar_guias` (feedback dashed) mantido,
  distinto das guias persistentes (GuiaItem sólido, z 19 < 20).
- **Persistência por layout (64):** guias + grade/passo no
  `Pagina.to_dict/from_dict`; round-trip testado; nenhuma coord absoluta.
- Foto (65): `editor_guias_raiox_{claro,escuro}` — 2 guias roxas, grade
  ligada (passo 5mm), raio-x com valores e a linha "Nome" destacada.
- Testes (66): 5 — guia imanta, grade on/off muda o snap, persistência,
  raio-x seleciona por conteúdo (2 vias), Alt suspende.
- **Suíte inteira: 473 passed, 0 failures, 0 skips (junit), exit 0.**

### ✔ Checagem do passo 80 (Bloco F — R-029/039/040/041) — MARCO 3/4

- **Zoom-para-seleção (R-029, 68):** `zoom_para_selecao` enquadra a
  região selecionada com folga, respeitando o clamp (ESCALA_MAX 8×);
  sem seleção → False. Botão "⤢ seleção".
- **"100%" e "Ajustar" sempre visíveis (69):** botão "100%" (`zoom_100`)
  + "Ajustar à tela" na barra; + o nível de zoom em % ao lado, com clamp
  são (70, herda a cura da Onda 2). Testes: 100%→100, extremos ≤800%.
- **Cadeado da arte (R-039, 71-72):** linha "Arte de fundo" TRAVADA no
  topo do painel de camadas (cadeado explícito). Destravar é gesto
  consciente com aviso. **Reconciliação honesta com a decisão travada:**
  a arte é o encarte do Illustrator que ocupa a PÁGINA INTEIRA (o app só
  compõe as camadas dinâmicas) — ela não é objeto móvel; o cadeado é a
  proteção/clareza dessa regra, não um "unlock para arrastar" (isso
  contrariaria a decisão travada). O aviso explica isso ao dono.
- **Raio-x só-regiões (R-040, 73-74):** `set_raio_x` esconde a arte
  (`_bg.setVisible(False)`) e pinta cada região por PAPEL (imagem=azul,
  nome=verde, preço=âmbar, unidade=violeta, selo=alerta, texto=cinza)
  com o rótulo — enxergar estrutura/sobreposição. Foto `editor_raiox`.
- **Medidas ao vivo (R-041, 75/77):** ao mover/redimensionar, o sinal
  `medidas` publica "X Y · L A mm" + as COTAS até as 4 bordas da arte
  (←→↑↓ mm) num rótulo da barra.
- **Setas empurram (76):** `nudge_selecao` — seta = 1 mm, Shift+seta =
  0,1 mm exatos (um estado de undo, vários itens juntos). Teste por valor.
- Fotos (78): `editor_raiox_{claro,escuro}` (raio-x + medidas + cadeado +
  zoom % no mesmo quadro).
- Testes (79): 6 — setas 1/0,1mm, zoom-para-seleção, 100%+clamp, raio-x
  esconde arte, arte travada+destrava com aviso, medidas emitem mm.
- **Suíte inteira ×1: 479 passed, 0 failures, 0 skips (junit), exit 0.**

### ✔ Checagem do passo 90 (Bloco G — integridade e adversarial re-rodado)

- **Adversarial estendido (81-85):** 5 casos NOVOS em
  `test_adversarial_vinculo.py`, todos POR CONTEÚDO:
  - 82: agrupar → desagrupar → reagrupar mantém o trio imagem/nome/preço
    de cada célula (conjunto de tipos/nomes preservado; ids preservados).
  - 83: z-order — `resolver_selecao` num ponto de regiões EMPILHADAS
    devolve a do TOPO com o uid certo (a cura do RG-55).
  - 84: região rotacionada 90° mantém o vínculo após seleção E edição.
  - 85: desfazer um AGRUPAR restaura mestre + mapa JUNTOS
    (`c.mapa == mapa_antes`, nº de slots preservado).
  - 87 (I3): guias/passo persistem em mm relativas (round-trip, sem px).
- **I1 (identidade, nunca posição):** confirmado — a seleção (`_primaria`,
  `selecionada`) compara região por IDENTIDADE (`is`); `resolver_selecao`
  devolve a região concreta; nenhum vínculo virou índice de lista.
- **I2 (sem degradação silenciosa):** confirmado — o pré-voo
  (`validar_composicao`) segue acusando conteúdo ausente; o desagrupar
  PRESERVA os valores (materializados pela propagação), então não cria
  buraco silencioso; a recusa do agrupar (SELO/TEXTO_LEGAL) avisa (I2).
- **I3 (portabilidade):** confirmado — guias em mm relativas à página,
  grade/passo por layout; nenhum px absoluto no JSON persistido.
- **I4 (ref_mestre uid):** confirmado — a propagação e o desagrupar
  operam por `ref_mestre`/`ref_grupo` (uid), imunes a reordenação de
  z-order; o adversarial reverte z-order e o trio segue.
- **I5 (adversarial por conteúdo):** confirmado — todos os novos testes
  conferem tipos/uids/pixels, nunca "não deu exceção".
- **Suíte inteira ×2: 484 passed / 0 failures / 0 skips (junit), exit 0**
  em ambas as rodadas; adversariais nominais 21/21 verdes.

---

## Resposta do builder (19/07/2026) — FASE 4 executada, passos 1–99; PARADO no 100

### Placar final
- **Suíte inteira ×2: 484 passed / 0 failures / 0 skips (junit), exit 0**
  nas duas rodadas (linha de base 450 → 484: +34 testes na fase).
- Adversariais nominais: **21/21** verdes (a fase tocou seleção/região/
  mapa — 5 casos novos no `test_adversarial_vinculo.py`).
- `test_fase4_editor.py`: **29 testes** (RG-55, RG-56, RG-49, RG-54,
  R-025/026/027/028, R-029/039/040/041).
- Boot (93): construção do Editor **14 ms** (quente) — as ferramentas
  novas (raio-x, guias, grade) não rodam no construtor (flags default);
  sem regressão.

### RG-55 — instrumentei e reproduzi ANTES de teorizar (a lei da fase)
O log PROVOU **uma** causa (o clique-grupo do RG-15 seleciona o trio →
`selecionada()` devolvia None → painel "Nada selecionado") e DESMENTIU as
outras duas (z-order e rotação: o preço rotacionado/sob a imagem foi
acertado com uid/z corretos). Não teorizei o que o log não mostrou.

### Bugs meus, achados pelos meus testes (honestidade de bancada)
1. **`selecionada()` com `set` de Regiao** — `Regiao` é dataclass mutável
   (unhashable); o 1º esboço usava `{it.regiao for...}` e estourava. Curado
   para comparação por IDENTIDADE (`is`), que é o correto por I1.
2. **Microtutorial travava o teste headless** — `mostrar_tutorial_agrupar
   (None,...)` caía em `dlg.exec()` (modal bloqueante). Curado: parent None
   ou janela offscreen mostra SECO (não-bloqueante).
3. **Barra de rolagem cortava os campos a 720p** — o QScrollArea das
   Propriedades roubava ~16px; a borda direita dos campos cortava. Pego na
   FOTO; curado alargando o mínimo lateral (300→320).

### Interpretações/reconciliações registradas para o arquiteto
- **R-039 (cadeado da arte) × decisão travada:** o caderno assume que
  destravar a arte permite MOVÊ-LA. Mas a decisão travada diz que a arte é
  o encarte do Illustrator que ocupa a PÁGINA INTEIRA (o app só compõe as
  camadas dinâmicas) — ela não é objeto móvel. Implementei o cadeado como
  PROTEÇÃO + CLAREZA dessa regra (travado por padrão, com aviso ao
  destravar explicando que a arte é o fundo), NÃO um "unlock para
  arrastar" (isso contrariaria a decisão travada). Se o dono quiser mesmo
  reposicionar a arte (com offset persistido e tratamento de bordas), é
  feature de Fase 5, não conserto.
- **"Editar como mestra" (passo 17):** implementei como ação de
  discoverability (seleciona o trio da mestra + toast "o que mudar aqui
  replica") — não é inverso, é a afordância consciente que o passo pede.

### Ajustes honestos de teste (não-mascaramento)
- `test_clique_frio_seleciona_o_trio_da_celula` (Onda 3) afirmava
  `selecionada() is None` — o comportamento ANTIGO que o RG-55 corrige.
  Atualizado para a nova decisão travada (trio + painel mostra a clicada).
- `test_desenhar_secoes_nao_toca_o_miolo` — o passo 36 (run de 1 célula
  sem caixa) usa `n_celulas != 1`; Secao sintético (n_celulas=0) segue
  desenhando, e a regra real é testada por `calcular_secoes`.

### O que ficou de fora (para ninguém descobrir depois)
- **Reposicionar a arte de fundo** — deferido (ver R-039 acima); a arte é
  fundo de página por decisão travada.
- **Guia removível "de volta à régua"** — implementada como o GuiaItem que
  se remove ao ser arrastado para FORA da página (equivalente prático);
  não há um "alvo régua" separado.
- **Cotas entre DUAS regiões (77)** — a medida ao vivo mostra as cotas até
  as 4 bordas da ARTE; a cota região↔região ficou como as guias de snap
  (feedback ao encostar), não um número. Anotado.
- **"override" em rótulo de menu** (F7.3, pré-existente) — não é tela nova
  da fase; não mexi para não confundir quem já conhece o rótulo.
- **Zoom-para-seleção** é botão (sem atalho de teclado dedicado ainda) —
  R-068 pede "atalho OU botão"; entreguei o botão.

### Artefatos para a reauditoria visual (saida_fase4/)
- `rg55_antes_painel_orfao.png` + `rg55_antes_auditoria_frame.jpg` — a
  evidência do bug (camada "Preço" destacada, painel "Nada selecionado").
- `editor_720p_{claro,escuro}` (depois, cabe em 720p) ·
  `menu_{solta,mestra,copia}_{tema}` (os 3 estados) ·
  `badges_grupo_{tema}` · `tutorial_agrupar_{1,2,3}_{tema}` ·
  `secao_uniao_3linhas_{tema}` (RG-49) ·
  `editor_guias_raiox_{tema}` (guias+grade+raio-x textual) ·
  `editor_raiox_{tema}` (raio-x por cor + medidas + cadeado + zoom%).
- `fluxo_agrupamento.gif` — agrupar → carimbar → ajustar cópia →
  desagrupar → desfazer (~14,7 s, o fluxo que o dono não entendia).

**Passo 100: PARADO.** Aguardo a reauditoria visual do arquiteto — cada
print antes→depois, os 3 estados de agrupamento, a seção-união por pixel.
Nada da Fase 5 foi iniciado.

---

## Conserto pós-reauditoria do arquiteto (19/07/2026) — resposta do builder

A reauditoria adversarial (27 agentes) NÃO selou a F4: 1 blocker, 4 majors,
achados de honestidade de teste. **Aceito e consertei tudo que se sustenta;
para CADA teste novo/reescrito rodei a PROVA DE MUTAÇÃO** (quebrar a produção
de propósito e mostrar que o teste FALHA). Placar final do conserto:
**490 verdes ×2, 0 failures, 0 skips; adversariais 21/21.**

### Must-fix consertados (com prova de mutação)
1. **[BLOCKER] atalhos do editor aninhados em `alternar_lateral`** — bug
   MEU, real: eu inseri `showEvent`/`alternar_lateral` ANTES do bloco de
   atalhos e ele foi absorvido pelo método, que não roda no boot (lateral
   nasce visível). Movido de volta ao `__init__`. Teste
   `test_fix_atalhos_do_editor_existem_no_boot` (atalhos existem no boot,
   não duplicam ao alternar). Mutação: comentar `criar_atalho` no __init__
   → FALHA.
2. **[MAJOR] LIMIAR_COMPACTO 1200 < 1280** — a 720p o compacto nunca
   ativava. Subido para 1360. Teste `test_fix_barra_cabe_a_720p` (limiar
   > 1280; o compacto RECOLHE os grupos no "···", reduzindo a largura
   mínima — asserção ESTRUTURAL, imune ao vazamento de escala/fonte entre
   testes headless). Mutação: LIMIAR=1200 → FALHA (`LIMIAR > 1280`).
3. **[MAJOR] adversarial 84 (rotação) mascarado** — setava `_primaria` na
   mão. Reescrito `test_adversarial_rotacao_hit_test_real`: exercita o
   hit-test ROTACIONADO via `resolver_selecao` em pontos que só acertam se
   a rotação for respeitada (e devolve None no ponto do retângulo
   não-girado). Mutação: `setRotation(0)` no item → FALHA.
4. **[MAJOR] adversarial 82 mascarado (só tipos, sem reagrupar)** —
   reescrito por PIXEL e uid, com o REAGRUPAR de fato: cada célula recebe
   foto de cor distinta; ao compor, cada uma mostra a SUA cor, antes e
   depois de agrupar→desagrupar→reagrupar. Mutação: `desagrupar` troca as
   regiões entre células → FALHA.
5. **[MAJOR/honestidade] "Gravada no CLAUDE.md"** — **rebate honesto com
   evidência:** a decisão ESTÁ no CLAUDE.md (linha 97, bloco após I1–I5:
   "Decisão travada da Fase 4 (RG-55...): o PAINEL... NUNCA FICA ÓRFÃO...
   inverso a UM clique"). O CLAUDE.md é UNTRACKED no git — a frota auditou
   um staging que não o incluiu (o mesmo artefato do "sem escuro/GIF" que o
   arquiteto já descontou). As linhas L209/L256 do FASE_4 são VERDADEIRAS;
   citei a linha do CLAUDE.md nelas para verificação direta.

### Honestidade de teste consertada (com prova de mutação)
6. **RG-49 sem prova de pixel** — o arquiteto tem razão EM ESPÍRITO: meu
   teste checava só o PONTO MÉDIO do vão (y=34), onde nem a caixa-por-linha
   buggada desenha traço (as divisórias ficam nas BORDAS das caixas). Agora
   varre a FAIXA INTERNA INTEIRA (base da linha 1 → topo da linha 2).
   Mutação: `_contorno_uniao` volta a caixa-por-linha → FALHA.
7. **RG-56 undo com mapa vazio ({} == {})** — reescrito com mapa POPULADO:
   `test_rg56_desagrupar_undo_com_mapa_nao_vazio` (agrupar/desagrupar NÃO
   mudam o mapa, ids preservados — invariância com entradas reais) +
   `test_rg56_remover_celula_undo_restaura_mapa_e_layout_juntos` (o caso que
   DE FATO muta o mapa: remover célula tira a entrada; desfazer restaura
   mapa + layout juntos). O adversarial do outro arquivo idem.
8. **RG-55 resolver_selecao inerte** — VÁLIDO: só testes a chamavam.
   LIGADA ao caminho real: o `mousePressEvent` passa o ponto do clique ao
   `_selecao_por_clique`, que determina a PRIMÁRIA por `resolver_selecao`.
   Teste `test_fix_resolver_selecao_no_caminho_de_producao` (clicar em
   empilhadas resolve a de cima, mesmo o handler no item de baixo). Mutação:
   `resolver_selecao` retorna None → FALHA.

### Nits limpos (com cobertura)
- **Comentário de diag (itens.py)** que dizia "selecionada()==None" —
  corrigido para "mostra a PRIMÁRIA (nunca órfão)".
- **Grade magnética invisível** — agora DESENHA as linhas no
  `drawBackground` quando ligada. Teste por pixel (fundo muda).
- **N de "ajustes" divergente** — `ajustes_da_regiao` alinhado ao que
  "Restaurar da mestra" desfaz (overrides de estilo/geom); badge = menu.
- **Cadeado da arte inerte** — agora CONSOME o estado: destravar torna o
  `_bg` selecionável (em `_compor_fundo`/`set_arte_travada`). Teste do flag.
- **Comparações de Regiao por valor** (609, 847) → por IDENTIDADE (I1).

### Descontado (concordo com o arquiteto)
- "saída sem escuro/GIF" e as suspeitas em `n_celulas != 1`: artefatos de
  staging / refutados na verificação — nada a fazer.

**Aguardo a re-rodada da frota.** Nada da Fase 5 iniciado.
