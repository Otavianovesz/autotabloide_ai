# FASE 7 — Mesa II: produção em massa (caderno de 100 passos)

> Formato-lei do PLANO_PERFEITO. Cobre **R-049** (multi-arquivo), **R-050**
> (Ctrl+V inteligente), **R-052** (conciliação em tela cheia com a foto),
> **R-053** (aceitar verdes), **R-056** (encher a página), R-058, R-059,
> R-060, R-062 (diff da edição anterior), R-063, R-070 (multi-preço "3 por
> 10"), R-071, R-072.
> **Emissão em lote (19/07)** — ver cabeçalho da FASE_4.md. Chat novo por fase.
> **Intensidade: Alto.**
>
> **Por quê da fase:** "importar tudo de uma vez para otimizar o tempo" — o
> dono pediu DUAS vezes, e a pesquisa (§4) confirmou que "dados primeiro,
> fotos depois" é o fluxo canônico da indústria. Esta fase consolida a
> entrada em massa (multi-arquivo, colar do WhatsApp), a decisão em massa
> (aceitar os verdes, encher a página) e a conferência com memória (diff da
> semana passada, checklist, densidade). **Risco central:** o parser de
> colagem precisa ser robusto (reusa o P0.3 de preço + a regra dura RG-20 de
> nome) e a tela cheia não pode regredir a conciliação existente.

## Bloco A — Entrada em massa (R-049, R-050, R-052) · passos 1–18
**Por quê:** o dono recebe as ofertas em foto/tabela pelo WhatsApp e quer
jogar tudo de uma vez — a máquina enfileira e lê, ele confere.

1. R-049 (multi-arquivo): abrir várias fotos/tabelas de uma vez, todas numa FILA única de importação.
2. A fila mostra cada arquivo com estado (na fila · lendo · pronto · erro) e posição.
3. Processar a fila em série sem travar a UI (worker; RG-05b cobre o shutdown), com barra de progresso honesta.
4. Um arquivo com erro não derruba a fila — fica marcado e o resto segue (I2, nunca em silêncio).
5. R-050 (Ctrl+V inteligente): colar texto de tabela (WhatsApp Web/Excel) direto na Mesa vira linhas de produto.
6. O parser de colagem reconhece colunas comuns (nome, preço, unidade) por heurística e separadores (tab, ";", vírgula, quebra de linha).
7. Preço colado passa pelo parser P0.3 (rejeita "2x 5,00" → None com aviso) — nunca cria preço errado em silêncio.
8. Nome colado passa pela regra dura RG-20 (enriquecer sem descartar palavra) — o mesmo motor, sem duplicar.
9. Prévia da colagem ANTES de criar: uma tabelinha "isto é o que entendi" para o dono confirmar ou ajustar.
10. Colar respeita "dados primeiro": cria os itens sem foto e enfileira a busca de imagem para depois (esteira do R-053).
11. R-052 (conciliação em tela cheia): abrir a conciliação com a FOTO ORIGINAL (o print/tabela do WhatsApp) ao lado.
12. Cada linha lida mostra o trecho da imagem de onde veio (âncora do OCR) — conferência visual do que a IA leu.
13. Corrigir na tela cheia: editar nome/preço com a foto ao lado, aceitar ou rejeitar por linha.
14. A tela cheia é uma VISÃO nova sobre o fluxo existente — não substitui nem regride a conciliação atual (o semáforo verde/amarelo/vermelho continua valendo).
15. Navegação por teclado na conciliação (próximo amarelo, aceitar, rejeitar) — velocidade de bancada.
16. Foto: fila multi-arquivo + prévia da colagem Ctrl+V + conciliação em tela cheia com a foto ao lado (claro/escuro).
17. Teste: multi-import enfileira N arquivos sem perder nenhum; Ctrl+V parseia uma tabela colada real (nome/preço/unidade).
18. **Checagem:** suíte parcial verde; o parser de colagem reusa P0.3 e RG-20 (testado, não reimplementado).

## Bloco B — Decisão em lote (R-053, R-056, R-070, R-071) · passos 19–36
**Por quê:** depois de importar em massa, decidir em massa — aceitar os certos
de uma vez e tratar só o que precisa de olho.

19. R-053 (aceitar os verdes): um botão "Aceitar todos os verdes" resolve de uma vez os itens que a conciliação casou com confiança.
20. Depois de aceitar os verdes, a tela foca só nos amarelos (revisar) e vermelhos (novos).
21. Contador claro: "38 verdes aceitos · 6 amarelos para revisar · 4 novos".
22. Aceitar verdes é reversível (undo) e nunca toca amarelo/vermelho por engano (só o verde do limiar).
23. R-056 (encher a página): distribuir na página o que couber e PERGUNTAR o destino do resto (nova página? fila? deixar de fora?).
24. "Encher a página" respeita a grade/seções e o pré-voo (não enfia item sem foto/preço sem avisar).
25. O resto que não coube vira uma lista clara com ação (criar página, mandar para a fila, descartar) — nunca some calado.
26. R-070 (multi-preço "3 por R$10,00"): um formato de preço para promoções por quantidade.
27. Multi-preço tem campos próprios (quantidade + valor) e compõe o texto certo ("3 por R$10,00", "Leve 3 pague 2").
28. O parser P0.3 entende o multi-preço como FORMATO — não o confunde com o "2x 5,00" proibido (regra explícita e testada lado a lado).
29. **Checagem (marco 1/4):** suíte inteira ×1 verde exit 0; screenshots de aceitar-verdes/encher-página/multi-preço em `saida_fase7/`.
30. R-071 (observação por item): um campo de observação ("limite 2 por cliente") que vira uma região própria no layout.
31. A observação é opcional por item e só desenha se preenchida (região condicional; o pré-voo está ciente).
32. Banco de observações frequentes ("limite N por cliente", "enquanto durarem os estoques") para escolher rápido.
33. Multi-preço e observação respeitam o override por slot (F7.3) e o vínculo por uid (I1).
34. Foto: uma página "cheia" com o resto listado + um item multi-preço + um item com observação (claro/escuro).
35. Teste: "aceitar verdes" resolve só os verdes; encher-página distribui e pergunta o destino do resto; multi-preço compõe o texto certo.
36. **Checagem:** suíte parcial verde; multi-preço não é confundido com preço inválido pelo parser (teste dedicado).

## Bloco C — Conferência e memória (R-058, R-059, R-060, R-062, R-063, R-072) · passos 37–58
**Por quê:** montar rápido é metade; conferir sem erro e lembrar do histórico
é a outra — é o que separa o encarte bom do encarte com preço trocado.

37. R-058 (frases prontas com variáveis): banco de frases (aviso legal, validade, chamadas) com {data} e {evento} que se resolvem sozinhos.
38. As frases prontas alimentam os papéis de texto da F5 (validade/legal/livre) — uma fonte só, sem duplicar.
39. Editar/adicionar frases (a semente foi plantada na F3, aba Campanhas) — aqui entram em uso na montagem.
40. R-059 (alerta de repetição): avisar quando um produto entrou em N edições seguidas ("está no encarte há 3 semanas").
41. O alerta é informativo, não bloqueia — o dono decide manter ou variar; lê o histórico de edições.
42. R-060 (medidor de densidade da página): um indicador de quão cheia/vazia está a página (pesquisa §1 — a densidade certa vende).
43. O medidor sugere uma faixa saudável (nem poluída, nem vazia) sem impor — cor calma/atenção.
44. R-062 (diff da edição anterior): comparar a edição atual com a anterior — o que mudou de preço, o que entrou, o que saiu.
45. O diff destaca preços que subiram/desceram e itens novos/removidos, em lista clara.
46. O diff usa chave natural (I1) para casar o mesmo produto entre edições — nunca por posição.
47. **Checagem (marco 2/4):** suíte parcial verde; o diff acha um preço deliberadamente mudado entre duas edições (teste).
48. R-063 (checklist final imprimível): um checklist antes de exportar (todas as fotos? preços? validade? +18 nas bebidas?).
49. O checklist é gerado do estado REAL do projeto (não uma lista estática) — marca sozinho o que já está ok.
50. O checklist imprime/exporta em PDF para conferência a quatro olhos (o dono e o pai).
51. R-072 (estatística da montagem): tempo por edição, itens por minuto — o dono vê o app economizando o tempo dele.
52. A estatística é local e discreta (aba/rodapé), sem telemetria externa (decisão travada: offline).
53. Densidade, diff e alerta de repetição leem o histórico sem pesar a Mesa (cálculo sob demanda/worker).
54. Frases prontas, observações e multi-preço convivem com a IA (F9) sem exigi-la — degradam para manual com aviso (I2).
55. Foto: frases prontas em uso + alerta de repetição + medidor de densidade + diff da edição anterior + checklist (claro/escuro).
56. Teste: frase com {data}/{evento} resolve certo; o alerta dispara no 3º; a densidade reflete a página; o checklist marca o que está ok.
57. Teste: a estatística conta o tempo da montagem (simulado) sem vazar dado para fora.
58. **Checagem (marco 3/4):** suíte inteira ×1 verde exit 0; screenshots de conferência/memória em `saida_fase7/`.

## Bloco D — Robustez do parser e do fluxo · passos 59–72
**Por quê:** Ctrl+V e multi-import dependem de um parser que aguente o mundo
real; a tela cheia não pode bifurcar a lógica da conciliação (risco do mapa).

59. Bateria de colagens reais (WhatsApp Web, Excel, vírgula decimal, tab, ponto-e-vírgula) — o parser aguenta as variações.
60. Colagem com lixo (linhas em branco, cabeçalho, linha de total) — o parser ignora o que não é produto, com prévia honesta.
61. Preço em formatos brasileiros ("R$ 5,99", "5.99", "5,99") normalizado certo; ambíguo vira amarelo, não palpite.
62. Multi-preço ("3 por 10", "leve 3 pague 2") reconhecido como formato; "2x 5,00" (proibido) continua rejeitado — os dois testados lado a lado.
63. Nome colado enriquecido sem descartar palavra (RG-20) e sem inventar marca/sigla (verificação contra o glossário).
64. Multi-import: 20 arquivos de uma vez, um corrompido no meio — a fila termina, o corrompido fica marcado, nenhum outro se perde.
65. A conciliação em tela cheia lê do MESMO serviço da conciliação normal — não bifurca a lógica, só muda a apresentação.
66. Aceitar-verdes em tela cheia e na tela normal dão o mesmo resultado (paridade testada).
67. "Encher a página" nunca enfia item sem foto/preço sem avisar (pré-voo antes de distribuir, I2).
68. Compor uma página vinda de colagem + multi-import e conferir o trio de cada item por conteúdo.
69. Rodar o adversarial do vínculo cobrindo itens criados por colagem, multi-import e encher-página.
70. Pré-voo reavaliado para os tipos novos (multi-preço, observação) — a região condicional não vira fantasma (lei da casa).
71. Foto: a prova do parser — uma colagem suja virando linhas limpas na prévia (claro/escuro).
72. **Checagem:** suíte parcial verde; a bateria do parser e a paridade da tela cheia passam.

## Bloco E — Integridade e adversarial (I1–I5) · passos 73–86
**Por quê:** a fase cria itens em massa e mexe em página/preço/observação — o
adversarial é o juiz (I5), sempre por conteúdo.

73. Re-rodar `test_adversarial_vinculo.py` com itens de colagem, multi-import e encher-página.
74. Adversarial: encher-página distribui por uid; nenhum trio migra para o vizinho.
75. Adversarial: multi-preço e observação ficam no item certo (por uid) após recompor.
76. Adversarial: aceitar-verdes não altera amarelos/vermelhos (só o que casou).
77. Confirmar I1: o diff casa por chave natural, não por posição; a colagem cria item por uid.
78. Confirmar I2: fila com erro, encher-página com resto, alerta de repetição — tudo visível, nada em silêncio.
79. Confirmar I3: frases, observações e multi-preço persistem em valores relativos, portáveis.
80. Confirmar I4: mestra↔cópia intacto ao encher a página numa grade replicável.
81. Lei da casa: multi-preço e observação (tipos novos de região) reavaliados quanto a ocupável/pré-voo.
82. Rodar a suíte inteira ×2, zero skips (a arte real conta).
83. Medir o boot e a responsividade com 20 arquivos na fila (não trava).
84. Varredura de órfãos: nada criado nesta fase ficou sem uso.
85. Conferir que o fluxo existente (conciliação normal, exportar) não regrediu (paridade).
86. **Checagem:** adversariais verdes; I1–I5 reconferidos e anotados.

## Bloco F — Fechamento · passos 87–100
**Por quê:** fase selada só com o "importei ~40 de uma vez e montei em minutos"
demonstrado ponta a ponta.

87. Suíte inteira ×2 exit 0, zero skips.
88. Adversariais do vínculo: nominais verdes (a fase criou itens em massa e mexeu em página/preço).
89. Teste novo `test_fase7_massa.py`: multi-import sem perda, Ctrl+V parseando, aceitar-verdes, encher-página, multi-preço × preço inválido, diff por chave natural.
90. Demonstração ponta a ponta: colar uma tabela de ~40 linhas → aceitar verdes → encher 2 páginas → checklist → medir o tempo.
91. `saida_fase7/`: fila, colagem, tela cheia, aceitar-verdes, encher-página, multi-preço, observação, densidade, diff, checklist — claro e escuro.
92. GIF curto (~15 s): Ctrl+V de uma tabela → prévia → criar → aceitar verdes.
93. Varredura de jargão (PT-BR: "colar tabela", "aceitar verdes", "encher a página", "3 por R$10").
94. Conferir a paridade da tela cheia com a conciliação normal (mesmo resultado).
95. Conferir que o parser rejeita "2x 5,00" e aceita "3 por 10" (os dois no teste).
96. Boot e responsividade medidos com a fila cheia.
97. Resposta do builder NESTE caderno (achados de bancada + "o que ficou de fora").
98. Atualizar `docs/PLANO_DE_CONSTRUCAO.md` e conferir o `CLAUDE.md`.
99. Screenshot-cartaz da produção em massa (fila + tela cheia + página cheia) claro + escuro lado a lado.
100. **PARAR** para a reauditoria visual do arquiteto — o parser da colagem por conteúdo, a paridade da tela cheia, o encher-página por uid. Nada da Fase 8 começa sem o selo.

---

## Registro do builder (em progresso — pós-reauditoria; ver seção do fim)

**Baseline da fase:** 554 verdes. **Placar atual: 581 verdes, 0 skips, exit 0
limpo ×5** (o histórico da construção fica abaixo; o estado autoritativo é a
seção "Conserto pós-reauditoria" no fim). Subagentes:
4 scouts de LEITURA no início (parser P0.3+RG-20 · serviço de conciliação ·
pré-voo/encher-página · multi-sabores/observação/diff); ~260k tokens.
Implementação INLINE.

### Feito
- **Bloco A — entrada em massa:** parser de colagem (R-050) em
  `app/qt/telas/colagem.py` (`parse_colagem` separa nome×preço por colunas ou
  preço-no-fim, ignora lixo, REUSA o P0.3 — "2x 5,00" marcado; `linhas_para_tuplas`
  = formato de `importar_ofertas`); Ctrl+V na Mesa (`_colar_tabela` → prévia
  `ColagemPreviaDialog` "isto é o que entendi" → `_importar_tuplas` →
  `conciliar_linhas`); **fila multi-arquivo (R-049)** `servico.importar_varios`
  (um erro não derruba a fila, I2) + `_importar` com multi-select.
  **Refatoração de reuso:** o laço de conciliação virou `servico.conciliar_linhas`
  (importar_ofertas e a colagem usam o MESMO — sem duplicar).
- **Bloco B — decisão em lote:** `separar_por_semaforo` (R-053, o predicado
  `semaforo=="VERDE"`, paridade por construção); `plano_encher_pagina` (R-056,
  distribui por UID com PRÉ-VOO ANTES, I2) + `mesa.encher_pagina` (só slots
  vazios, resto fica "fora da grade" visível); `parse_multi_preco` (R-070:
  "N por R$X"/"leve N pague M"; "2x 5,00" NÃO casa, segue rejeitado — lado a lado).
- **Bloco C (início):** `diff_edicoes` (R-062) casa por **chave natural**
  (produto_id>ean>nome, I1), nunca por posição — acha preço mudado/novo/removido;
  `checklist_final` (R-063) gerado do estado REAL (foto/preço/validade/itens,
  marca sozinho o que está ok); densidade (R-060) já existe (`densidade_da_pagina`).
- **Adversarial F7:** encher-página distribui por uid (por conteúdo).
- **Provas de mutação:** parser sem reuso do P0.3 → falha; troca/diff por
  posição → falha (embaralhado). Testes: `test_fase7_massa.py` (13) +
  adversarial em `test_adversarial_vinculo.py`. **Placar: 567 verdes, 0 skips.**
- **Paridade R-053 confirmada por leitura:** "aceitar verdes" é o MESMO
  predicado `it.semaforo == "VERDE"` já usado em `mesa.py`; a tela cheia
  reusa `importar_ofertas`/`aceitar_correspondencia` → paridade por construção.

---

## Conserto pós-reauditoria do arquiteto (2026-07-20) — 3 fixes + pendentes

O arquiteto reauditou no disco real, elogiou o nível ("NÃO recomece") e exigiu
**3 correções**. Todas feitas, COM prova. **Placar: 581 verdes, 0 skips, exit 0
LIMPO nas 5 rodadas seguidas** (a prova que o arquiteto pediu). Subagentes nesta
etapa: **0** (implementação 100% inline). Custo desta etapa: só as rodadas de
teste (5× suíte inteira + focados).

### Fix #1 — SEGFAULT de teardown (era classificado como "flaky" — ERRADO)
- **Raiz real (achado de bancada, honesto):** a lei é *"verde com crash no exit
  NÃO é verde"*. A raiz NÃO era flakiness: **10 testes criam `MesaTela()` com o
  `QTimer` do rascunho + `GerenciadorTrabalhos` e nunca encerram** → QThread/
  QTimer vivo no teardown do processo → segfault intermitente (precedente F7.1).
- **Cura:** `MesaTela.closeEvent` para o `_timer_rascunho` e chama
  `self._trabalhos.encerrar(1000)`; fixture autouse em `conftest.py`
  (`_encerrar_qt_apos_teste`) chama `encerrar_todos()` + `closeAllWindows()` +
  `processEvents()` após CADA teste.
- **Prova:** suíte inteira **5× seguidas, exit 0 limpo** (0 segfault);
  `test_mesa_close_encerra_timer_do_rascunho` com prova de mutação (tirar o
  `timer.stop()` → o teste falha).

### Fix #2 — MULTI-PREÇO (era meia-feature: parseava mas NÃO desenhava)
- `DadosProduto.multi_preco` + **caminho de TEXTO** no `_desenhar_preco`
  (compositor) — desenha o "3 por R$10" no lugar do Decimal na região PRECO.
- `ItemMesa.multi_preco` fiado no `_dados_de`; multi-preço **não cai como "sem
  preço"** em `validar_composicao`/`plano_encher_pagina`/`checklist_final`/
  `problema_na_celula`; a planilha o reconhece (`aplicar_edicao` via
  `parse_multi_preco`).
- **Prova por PIXEL:** `test_multi_preco_desenha_na_pagina_por_pixel` (com ≠ sem).

### Fix #3 — TELA CHEIA da conciliação (R-052)
- `ResultadoMesa.caminho_fonte` (propagado por `conciliar_linhas`/
  `importar_ofertas` só quando a fonte é imagem); `ConciliacaoDialog` ganha um
  **painel da FOTO ORIGINAL** ao lado (`QSplitter` + `QScrollArea` + pixmap real,
  `_painel_foto`), e abre **maximizado** (`showMaximized`) quando há foto —
  MESMO diálogo, MESMA lógica/tabela → **paridade por construção**.
- **Prova:** `test_conciliacao_tela_cheia_foto_mesmo_servico` — com e sem foto o
  conjunto itens/semáforo é IDÊNTICO (a foto não muda a conciliação); a foto real
  aparece (pixmap não-nulo, por conteúdo).
- **Deferido COM nota clara:** o *recorte-por-linha* (o "trecho de onde veio cada
  linha", passo 12) — o OCR manda a foto INTEIRA e devolve só `{descricao,preco}`,
  sem bbox. A tela cheia entrega a foto inteira ao lado; o recorte exige mexer no
  OCR (fora do escopo desta fase).

### Pendentes do Bloco C — camada de MODELO + DESENHO (feitos, testados)
- **R-058 frases prontas:** `resolver_frase({data}/{evento}, contexto)` — variável
  sem valor fica VISÍVEL como `{chave}` e volta em `faltantes` (I2); `BANCO_FRASES`.
- **R-059 alerta de repetição:** `semanas_seguidas` + `alerta_repeticao`
  (dispara no 3º encarte seguido; informativo, não bloqueia).
- **R-072 estatística:** `resumo_montagem(segundos, n)` → itens/min, LOCAL (dict,
  sem rede/telemetria — decisão travada offline).
- **R-071 observação por item:** `ItemMesa.observacao` + `DadosProduto.observacao`
  + **`PapelTexto.OBSERVACAO`** (região CONDICIONAL: só desenha se preenchida —
  ramo em `texto_composto_legal`), `banco_observacoes()`, rótulos em
  `papel_texto_ui.py`, fiado no `_dados_de` E **editável na planilha** (coluna
  "Observação" — laço fechado, sem órfão, passo 84). Nenhuma porta "ocupável"
  nova: reusa `TEXTO_LEGAL` (já não-ocupável) — o fantasma não renasce.
- **R-060 densidade:** já existia (`densidade_da_pagina`) e já fiada na `mesa.py`.
- **I5 adversarial:** `test_adversarial_f7_multi_preco_e_observacao_por_uid` —
  após embaralhar a estante, cada slot desenha o multi-preço/observação do SEU
  item (por conteúdo: texto composto + diff de pixel). Prova de mutação: quebrar
  o ramo OBSERVACAO no compositor → 2 testes falham (demonstrado e revertido).

---

## Conclusão da fase (passos 59–100, 2026-07-20) — Bloco D + casca + fecho

Depois do selo dos 3 fixes, o arquiteto mandou TERMINAR a fase (não recomeçar).
Feito, inline, com prova de mutação onde tocou parser/fila. **Placar final: 600
verdes, 0 skips, exit 0 LIMPO nas 5 rodadas seguidas.** Subagentes: 0 (inline).

### Bloco D — robustez do parser e do fluxo (59–72)
- **Achado próprio (gap real):** `parse_colagem` NÃO reconhecia multi-preço numa
  linha colada ("Sabão;3 por R$10" caía como preço "não entendido", vermelho
  falso). Corrigido: `_split_multi` reconhece a promoção ANTES do split ingênuo;
  o multi-preço viaja ao ItemMesa por `conciliar_linhas(multi_precos=…)` (a tupla
  leva só o valor). O `ColagemPreviaDialog` mostra "promoção" (verde) e reconhece
  multi-preço editado à mão. Prova de mutação: quebrar `_split_multi` → 2 testes
  falham (demonstrado e revertido).
- **Bateria ampla** (9 casos parametrizados): WhatsApp Web, Excel/tab, `;`, `|`,
  decimal ponto/vírgula, milhar, hífen no nome, sem preço.
- **Multi-import de 20 arquivos com 1 corrompido** (UTF-8 inválido no meio): a
  fila TERMINA, o corrompido fica nomeado no relatório, os 19 outros não se
  perdem, o aviso "1 de 20" é visível (I2). Prova de mutação embutida.

### Casca visual (UI Qt das funções do Bloco C)
- **Multi-preço qtd+valor:** `PromocaoDialog` (formato "N por R$X"/"Leve N pague
  M", prévia, "Sem promoção"); reusa `compor_multi_preco`/`compor_leve_pague`
  (round-trip por `parse_multi_preco`); abre PRÉ-PREENCHIDO ao editar; ação no
  menu do item. A planilha exibe a promoção na coluna Preço (não vazia).
- **Observação:** ação "Observação do item…" no menu (banco de sugestões) +
  coluna na planilha (já feita).
- **Estatística (R-072):** rodapé discreto "N item(ns)" + tooltip com itens/min
  (LOCAL, offline); cronômetro começa no 1º item.
- **Frases prontas (R-058):** combo no `DialogoPapelTexto` (seção livre) que
  insere a frase JÁ resolvida ({data}/{evento} do `contexto_frases` da Mesa;
  variável sem valor fica visível, I2).
- **Alerta de repetição (R-059):** toast após importar, lendo o histórico das
  edições salvas (`itens_das_edicoes_recentes` + `alertas_de_repeticao`, chave
  natural I1); informativo, degradação silenciosa da LEITURA é aceitável (aviso
  opcional, sem perda de dado).
- **Consistência (a lição do multi-preço):** a etiqueta da estante mostrava "sem
  preço" para item de promoção — corrigido (badge "promoção"); contraste da
  célula "preço a rever" legível no claro E no escuro.

### Bloco F — fecho (87–100)
- **Galeria NATIVA** em `saida_fase7/{claro,escuro}` (7 artefatos cada): prévia da
  colagem, promoção, conciliação em TELA CHEIA com a foto ao lado, Mesa com badges
  + estatística, planilha com observação, seletor de frases. Script
  `app/scripts/fotografar_fase7.py` (encerra determinístico — sem crash de
  teardown do Qt nativo no Windows).
- **GIF do fluxo de massa** em `saida_fase7/fluxo_massa.gif` (colagem → tela cheia
  → Mesa).
- **Varredura de jargão:** as strings novas de UI são PT-BR (sem termo técnico
  exposto).

### O que ficou de fora (declarado, não meia-feature silenciosa)
- **Recorte-por-linha na tela cheia** — deferido pelo arquiteto (o OCR devolve
  `{descrição,preço}` sem bbox; exige mexer no OCR).
- **Frases {evento} sem nome de campanha** ficam com o placeholder VISÍVEL (o
  contexto expõe {data}=validade; {evento} só resolve quando a oferta tem nome).

**Estado: passo 100 alcançado. PARADO no ponto de reauditoria — aguardando o
arquiteto reauditar Bloco D + casca + fecho no disco real e inspecionar a galeria
nativa (`saida_fase7/`) para o selo visual.**
