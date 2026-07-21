# FASE 9 — Conteúdo & IA II (caderno de 100 passos)

> Formato-lei do PLANO_PERFEITO. Cobre **R-073** (chat da oferta), R-074,
> R-075, R-076, R-077, R-078, **R-081** (IA revisora do export), R-082, R-083,
> R-084, R-085, R-086, R-087, R-089 (fila com prioridade), R-090.
> **Emissão em lote (19/07)** — ver cabeçalho da FASE_4.md. Chat novo por fase.
> **Intensidade: Alto.**
>
> **Por quê da fase:** a IA vira colega de trabalho — proativa, revisora, sem
> alucinar. Tudo LOCAL (LM Studio/Ollama pela API padrão compatível-OpenAI),
> respeitando os vetos do dono. **Três decisões travadas guiam tudo:** (1) a
> IA NUNCA bloqueia o export — só informa; (2) a IA NUNCA inventa marca,
> sigla ou protocolo — só aprende o que o dono confirmou; (3) sem IA, tudo
> degrada para fuzzy/manual COM aviso — o app produz o tabloide de qualquer
> jeito. A revisora do export é o item mais ambicioso e o de maior risco de
> hardware: se a visão local não der conta, cai para heurística com aviso.

## Bloco A — IA que ajuda a montar (R-073, R-074, R-083) · passos 1–18
**Por quê:** o dono descreve, a IA rascunha, ele ajusta. A IA propõe; o humano
dispõe — sempre.

1. R-073 (chat da oferta): um campo onde o dono cola/descreve as ofertas ("monta o Quintou com estas 20 linhas") e a IA devolve um RASCUNHO de projeto.
2. O chat da oferta REUSA a conciliação + o enriquecer em lote (não um pipeline novo) — a IA orquestra o que já existe.
3. O resultado é sempre um rascunho para AJUSTAR, nunca publicado direto — o dono manda no final (I2).
4. O chat mostra o que fez em linguagem simples ("casei 18, 2 são novos, 1 sem foto") — transparência.
5. Erros/ambiguidades viram amarelos na Mesa (não palpite silencioso) — o fluxo de conciliação vale.
6. R-074 (manchete sugerida): a IA sugere chamadas para o evento ("Quintou do Real — preços que gritam"); o dono escolhe/edita.
7. Manchetes como sugestões (lista), nunca imposição; o dono edita à vontade.
8. A manchete respeita o limite da região de texto (não estoura o espaço).
9. R-083 (Fica-a-Dica com estilos): a IA escreve a dica em estilos escolhíveis — receita · economia · curiosidade.
10. Memória do que já saiu: a IA evita repetir a mesma dica em edições seguidas (lê o histórico).
11. A dica respeita o teto de caracteres da região (R-088, da F3) e o estilo escolhido.
12. **Verificação de fato:** a dica não inventa dado (preço/marca) — é só texto de apoio; nunca cria sigla/protocolo (regra dura).
13. Prévia da dica antes de aplicar; regenerar com outro estilo num clique.
14. Todo texto gerado é editável pelo dono (a IA propõe, o humano dispõe).
15. Sem IA disponível: chat/manchete/dica degradam para manual com aviso (I2) — o app não depende da IA para funcionar.
16. Foto: o chat da oferta com um rascunho gerado + sugestões de manchete + a dica em 3 estilos (claro/escuro).
17. Teste: o chat da oferta produz rascunho reusando a conciliação (itens casados por uid); a dica respeita o teto e não repete a anterior.
18. **Checagem:** suíte parcial verde; degradação sem IA testada (tudo vira manual com aviso).

## Bloco B — IA que protege (R-081, R-078, R-085, R-075) · passos 19–40
**Por quê:** a revisora lê a peça pronta e pega o erro que cansa o olho humano
— preço trocado, nome cortado. É a proteção mais valiosa e a de maior risco.

19. R-081 (IA revisora do export): antes de aprovar, a IA "lê" o PNG final e aponta preço trocado, nome cortado, foto errada.
20. A revisora usa o modelo de VISÃO local (Qwen2.5-VL) sobre o PNG composto — o mesmo motor do OCR.
21. A revisora COMPARA o que vê na peça com os dados do projeto (preço/nome por slot) e acusa divergência.
22. **Decisão travada (risco do mapa):** se o modelo de visão não der conta, a revisora degrada para checagens HEURÍSTICAS (texto cortado por medida, preço fora de faixa) COM aviso — e NUNCA bloqueia o export.
23. O laudo da revisora é uma lista de avisos clicáveis (cada um leva ao slot) — o dono decide, a IA não veta.
24. R-078 (sentinela de preço estranho): avisar "R$79 num sabonete?" — preço fora da faixa histórica do produto/categoria.
25. A sentinela usa o histórico de preços (F11) e a categoria; é aviso, não trava.
26. Faixa aprendida por categoria (sabonete R$2–8): a sentinela calibra com o acervo, não com número mágico.
27. R-085 (avaliador de foto): marcar foto borrada, pequena ou com marca-d'água no momento da escolha.
28. O avaliador dá uma nota simples (boa/atenção/ruim) com o motivo ("resolução baixa para o tamanho da célula").
29. O avaliador conversa com o upscale (F10): foto pequena → sugere upscale sob demanda.
30. **Checagem (marco 2/4):** suíte parcial verde; a revisora aponta um preço DELIBERADAMENTE trocado num PNG de teste.
31. R-075 (caça-duplicatas do acervo): a IA encontra produtos duplicados e propõe fundir.
32. A fusão é ASSISTIDA (o dono confirma) e por CHAVE NATURAL (I1) — nunca funde dois produtos diferentes por engano.
33. Ao fundir, as fotos são reconciliadas por conteúdo (byte a byte): a oficial escolhida, as demais preservadas como versões.
34. A caça-duplicatas mostra o par lado a lado (nome, marca, foto) antes de fundir — evidência, não fé.
35. Fundir é reversível (undo) e logado (o que virou o quê) — sem perda silenciosa.
36. A revisora, a sentinela e o avaliador NUNCA bloqueiam o fluxo — só informam (I2).
37. Todas as proteções degradam com aviso se a IA cair (heurística no lugar) — o export sempre acontece.
38. Foto: o laudo da revisora sobre uma peça + a sentinela de preço + a caça-duplicatas com o par (claro/escuro).
39. Teste: caça-duplicatas funde por chave natural (I1) com as fotos conferidas byte a byte; a sentinela dispara no preço fora de faixa.
40. **Checagem:** suíte parcial verde; a degradação da revisora (sem visão → heurística) testada, export nunca bloqueado.

## Bloco C — IA que aprende (R-076, R-077, R-086, R-087, R-082, R-084) · passos 41–60
**Por quê:** cada correção do dono ensina o app; na semana seguinte ele erra
menos. Mas só aprende o que o dono CONFIRMOU — nunca inventa.

41. R-076 (dicionário de typos do fornecedor): ao confirmar "Huppers"→"Ruppers" 1×, o app aprende e corrige sozinho depois.
42. O typo aprendido vira um ALIAS persistido (I1) — na próxima importação, casa direto (verde).
43. O aprendizado é reversível e visível (uma lista de "correções aprendidas" nas Configurações) — o dono manda.
44. R-077 (expansor de siglas com aprendizado): "VD"→"vidro", "PT"→"pote"; aprende as do fornecedor ao confirmar.
45. As siglas aprendidas entram no glossário da F3 (uma fonte só, sem duplicar).
46. R-086 (sinônimos regionais): mandioca/macaxeira/aipim tratados como o mesmo produto na conciliação.
47. O dicionário regional é editável (o dono acrescenta os termos da região dele).
48. R-087 (marca extraída do nome): a IA identifica a marca dentro do nome ("Arroz Tio João 1kg" → marca "Tio João") e a usa na sanitização/agrupamento.
49. A marca extraída alimenta a ordem Tipo+Marca+Sabor+Peso (decisão travada) sem inventar marca inexistente (verificação).
50. R-082 (autodetecção de variações): a IA sugere agrupar sabores/variações do mesmo produto ("Refri Guaraná lata/2L/1L").
51. A sugestão de agrupar é uma proposta (o dono aceita/recusa) — reusa o multi-sabores (F7.1) e o item composto (F7.2).
52. R-084 (aprendizado incremental): as correções do dono (nome, categoria, marca, foto oficial) realimentam a conciliação da próxima edição — o app fica mais certeiro com o uso.
53. Todo aprendizado é LOCAL e auditável (nada sai da máquina; uma lista do que foi aprendido, editável).
54. **Regra dura:** o app NUNCA inventa marca, sigla ou protocolo — só aprende o que o dono confirmou; ambíguo vira amarelo.
55. Nada é aprendido em silêncio: cada aprendizado nasce de uma confirmação explícita do dono.
56. As coisas aprendidas convivem com o glossário/sanitização da F3 (uma casa só).
57. Foto: a lista de "correções aprendidas" + uma sugestão de agrupar variações + a marca extraída (claro/escuro).
58. Teste: typo confirmado 1× persiste como alias e casa na 2ª importação (verde); marca extraída não inventa (caso negativo testado).
59. Teste: sinônimo regional casa o mesmo produto; a sugestão de variações agrupa via F7.1 (não força).
60. **Checagem (marco 3/4):** suíte inteira ×1 verde exit 0; screenshots do aprendizado em `saida_fase9/`.

## Bloco D — Fila, status e degradação (R-089, R-090) · passos 61–74
**Por quê:** a IA local é finita; a fila prioriza o que o dono está olhando, e
o status fala a língua dele — sem caixa-preta nem jargão de LLM.

61. R-089 (fila de IA com prioridade): as tarefas de IA (conciliar, enriquecer, dica, revisar) entram numa fila com prioridade.
62. O que o dono está olhando agora tem prioridade (a conciliação em tela na frente da dica em lote).
63. A fila é visível e cancelável (o dono vê o que roda e pode parar) — sem caixa-preta.
64. R-090 (status da IA em linguagem simples): completar o painel da F3 — "ligado/desligado", quais modelos, o que faz agora.
65. O status usa só o que a API padrão compatível-OpenAI dá (decisão travada: não acoplar ao LM Studio) — sem inventar métrica que a API não expõe.
66. Interruptor mestre "usar IA" (da F3) respeitado em toda a fase: desligado → tudo degrada para fuzzy/manual com aviso.
67. Perfil de máquina fraca (R-132, F3) desliga a IA de uma vez — a fase inteira degrada com aviso, o app funciona.
68. Nenhuma função de IA é obrigatória para produzir um tabloide — a IA acelera, não gateia (I2).
69. Timeout são em cada chamada de IA; estouro → degrada, não congela (RG-05b vale).
70. A fila e o status leem/escrevem só o necessário; não pesam o boot (carregam sob demanda).
71. Foto: a fila de IA com prioridade + o painel de status completo (claro/escuro).
72. Teste: a fila prioriza a tarefa em foco; cancelar para a tarefa; o status reflete ligado/desligado real.
73. Teste: com "usar IA" desligado, todas as funções da fase degradam com aviso e nada trava.
74. **Checagem:** suíte parcial verde; a degradação global (IA off) testada em todas as funções.

## Bloco E — Integridade e adversarial (I1–I5) · passos 75–86
**Por quê:** a fase mexe em conciliação, acervo (fusão) e textos — o
adversarial e as regras duras (não inventar, não bloquear) são o juiz.

75. Re-rodar `test_adversarial_vinculo.py` após fusão de duplicatas e agrupamento de variações.
76. Adversarial: caça-duplicatas funde por chave natural — nunca funde dois produtos distintos (caso negativo).
77. Adversarial: a revisora não altera o projeto (só lê e aponta) — a peça exportada é idêntica com/sem revisora.
78. Confirmar a regra dura: nenhuma função inventa marca/sigla/protocolo (bateria de casos negativos).
79. Confirmar I1: typos/aliases/fusões por identidade, nunca por posição.
80. Confirmar I2: revisora/sentinela/avaliador/fila — tudo informa, nada bloqueia nem some em silêncio.
81. Confirmar I3: dicionários e aprendizados persistidos relativos/portáveis; fotos por caminho relativo.
82. Confirmar que a IA off degrada tudo com aviso (nenhuma trava dura na IA).
83. Rodar a suíte inteira ×2, zero skips (a arte real conta).
84. Medir o boot: fila/status carregam sob demanda; boot intacto.
85. Varredura de órfãos: nenhuma função de IA ficou sem lar ou sem degradação.
86. **Checagem:** adversariais verdes; regras duras (não inventar) verdes; I1–I5 reconferidos.

## Bloco F — Fechamento · passos 87–100
**Por quê:** fase selada só com a revisora pegando um erro real e a degradação
sem IA provada — a IA é colega, não muleta.

87. Suíte inteira ×2 exit 0, zero skips.
88. Adversariais do vínculo: nominais verdes (a fase tocou conciliação/acervo/textos).
89. Teste novo `test_fase9_ia.py`: chat da oferta reusando conciliação, revisora pega preço trocado (com degradação heurística), caça-duplicatas por chave natural, typo aprendido persiste, IA off degrada tudo.
90. Demonstração ponta a ponta na máquina real (LM Studio aberto): montar pelo chat da oferta → revisora aponta um preço trocado plantado → aprender um typo → reimportar e casar verde.
91. `saida_fase9/`: chat da oferta, manchetes, dica em 3 estilos, laudo da revisora, sentinela, avaliador de foto, caça-duplicatas, correções aprendidas, fila/status — claro e escuro.
92. GIF curto (~15 s): a revisora lendo a peça e apontando o preço trocado.
93. Varredura de jargão (PT-BR: "colega de IA", "revisora", "correções aprendidas" — sem jargão de LLM cru).
94. Conferir que NADA da IA bloqueia o export (todas as proteções são avisos).
95. Conferir a regra dura em toda a fase (não inventar marca/sigla/protocolo) com casos negativos.
96. Boot e responsividade medidos com a fila de IA cheia.
97. Resposta do builder NESTE caderno (achados + "o que ficou de fora"; se a visão local revisou de fato ou caiu na heurística — honestidade de bancada).
98. Atualizar `docs/PLANO_DE_CONSTRUCAO.md` e conferir o `CLAUDE.md` (decisões travadas: IA nunca bloqueia; nunca inventa; degrada com aviso).
99. Screenshot-cartaz da "IA colega" (chat + revisora + aprendizado) claro + escuro lado a lado.
100. **PARAR** para a reauditoria visual do arquiteto — a revisora pegando o erro, a fusão por chave natural, a degradação sem IA. Nada da Fase 10 começa sem o selo.

---

## Registro do builder (2026-07-20) — EXECUTADA até o passo 100

**Baseline:** 631 verdes (F8 selada). **Placar final: 650 verdes, 0 skips, exit 0
LIMPO ×5.** Subagentes: **4 scouts de LEITURA** no início (revisora/visão ·
caça-duplicatas · nunca-inventa · fila/status) + **4 revisores ADVERSARIAIS** no
fecho (um por eixo, disco real). Implementação 100% INLINE.

### O que foi feito (modelo antes de UI, tudo testado)
- **Bloco B — a IA que protege (o flagship):** `app/ai/revisora.py` (R-081) — a
  revisora lê o PNG com o modelo de VISÃO e compara os preços lidos × os dados do
  projeto; SEM visão degrada para HEURÍSTICA (nome cortado via `text_fit`, de≤por,
  preço fora de faixa) COM aviso; **NUNCA bloqueia, NUNCA altera a peça, NUNCA
  levanta**. `app/core/sentinela.py` (R-078: faixa aprendida do acervo, mediana±IQR).
  Casca: `Mesa._revisar` (worker; laudo informativo; encerra no closeEvent).
- **Bloco B — caça-duplicatas (R-075):** `app/core/deduplicacao.py` — acha pares por
  CHAVE NATURAL (reusa `portabilidade.chave_natural`) ou EAN forte; `fundir_no_banco`
  migra aliases + SOFT-DELETE o perdedor (reversível). Marca diferente NUNCA vira par (I1).
- **Bloco C — a IA que aprende, sem inventar:** `app/core/aprendizado.py` — `extrair_marca`
  (R-087: só marca CONHECIDA, fronteira de palavra, nunca inventa) + sinônimos
  regionais (R-086: canoniza sem descartar token). Typo/alias (R-076) já vive em
  `aprender_alias`.
- **Bloco A — a IA que ajuda:** `montar_pelo_chat`/`resumo_do_resultado` (R-073, reusa
  a conciliação); `sugerir_manchetes` (R-074, degrada) e `gerar_dica(estilo, evitar)`
  (R-083, teto é lei). Casca: `Mesa._chat_oferta`.
- **Bloco D — fila e status:** `ordenar_por_prioridade` (R-089: o foco roda primeiro);
  o painel de status e o interruptor "usar IA" já existiam (F3); degradação num
  ponto único (`_motor_se_disponivel() → None`).
- **Bloco E/F:** adversarial `test_adversarial_f9_revisora_nao_altera_a_peca` (peça
  byte-idêntica com/sem revisar). Galeria NATIVA `saida_fase9/` (laudo da revisora,
  chat, manchetes+dica, correções aprendidas), GIF, jargão PT-BR (sem termo de LLM
  cru na UI). Teste novo `test_fase9_ia.py` (18).

### Achados da FROTA ADVERSARIAL (4 revisores no disco real) — todos tratados
- **[BUG real, corrigido]** o "2x 5,00" PROIBIDO era aceito CALADO como preço "5,00"
  quando separado por ESPAÇO (WhatsApp) — só a forma em coluna rejeitava (herança do
  parser da F7, que o chat da F9 reusa). Corrigido com `_RE_AMBIGUO_FIM`: todas as
  formas marcam "preço a rever" (I2). Teste `test_colagem_rejeita_2x_500_em_todas_as_formas`.
- **[TESTE FRACO, blindado]** `test_extrair_marca` não cobria a colisão de substring
  (Camil/Camilo) — passaria com fronteira frouxa. Adicionado o caso-armadilha.
- **[ROBUSTEZ, corrigida]** `revisar_export` tinha `disponivel()`/heurística FORA do
  try — feria o "nunca levanta". Agora TODO o corpo está sob try.
- **[lei exit-0, teste dedicado adicionado]** faltava provar o worker da revisora
  encerrando no fechamento — `test_revisora_worker_encerra_no_fechamento`.
- **[MENOR, corrigido]** `_revisar` usava caminho temp FIXO (corrida entre revisões)
  → nome único por revisão.
- **Ressalvas anotadas (não bloqueiam):** `fundir_no_banco` confia no chamador para a
  chave (a fusão é assistida — confirmação humana é a barreira; UI de fusão não
  construída ainda); `ordenar_por_prioridade` é primitiva testada mas ainda não ligada
  a uma fila de IA viva (integração é UI); EAN forte sobrepõe a trava de marca
  (semântica intencional de identidade global).

### O que ficou de fora (declarado)
- **UI de fusão de duplicatas** (o par lado a lado + confirmar) — o modelo está pronto
  e testado (achar/fundir), a casca visual fica para depois.
- **Integração de `ordenar_por_prioridade` numa fila de IA viva** (a primitiva está
  pronta; conectá-la à fila de enriquecimento é UI).
- **avaliador de foto (R-085)** e **autodetecção de variações (R-082)** — mapeados,
  não construídos nesta passada (o avaliador conversa com o upscale da F10).
- **Manchete/dica com a UI de seleção completa** — as funções existem (com estilos);
  o seletor rico fica para a integração.
- **Demonstração com LM Studio real:** rodou com a IA FAKE determinística (o ambiente
  de bancada não tem o servidor de visão ligado); a revisora por VISÃO está provada no
  encanamento (fake lê o preço trocado) e a degradação heurística roda de verdade. A
  prova com o modelo real fica para a máquina do dono.

**Estado: passo 100 alcançado. PARADO no ponto de reauditoria — aguardando o
arquiteto reauditar no disco real + a galeria `saida_fase9/` (a revisora pegando o
preço trocado, a fusão por chave natural, a degradação sem IA).**
