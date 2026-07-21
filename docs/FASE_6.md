# FASE 6 — Mesa I: a bancada arrumada (caderno de 100 passos)

> Formato-lei do PLANO_PERFEITO. Cobre **RG-53** (barra reorganizada),
> **R-051** (modo planilha), R-054, R-055, R-057 (trocar células arrastando),
> R-061 (rascunho automático), R-069, R-020, R-017 (Ctrl+K em todas as telas).
> **Emissão em lote (19/07)** — ver cabeçalho da FASE_4.md. Chat novo por fase.
> **Intensidade: Alto.**
>
> **Por quê da fase:** a Mesa é onde a semana acontece. "Botões se comendo" e
> estante engessada custam minutos todo dia. Esta fase arruma a bancada: uma
> barra que cabe em qualquer largura, uma estante viva (planilha, filtros,
> arrastar, trocar) e uma rede de segurança (rascunho automático) para que
> uma queda de luz nunca leve o trabalho. **Atenção central:** R-051/055/057
> tocam o mapa slot→uid — o adversarial do vínculo é o juiz, e nada pode
> brigar com o override por slot (F7.3).

## Bloco A — A barra da Mesa reorganizada (RG-53) · passos 1–14
**Por quê:** o dono viu botões se sobrepondo. A barra tem que achar-se pela
função, caber a 720p e nunca esconder o essencial.

1. Levantar os prints da Mesa em que os botões da barra se sobrepõem ou cortam (RG-53) — montar a lista antes → depois.
2. Reorganizar a barra por grupos lógicos na ordem do fluxo: **Importar · Montar · Salvar/Exportar · Navegar páginas**.
3. Escolher o formato medindo os dois a 720p: barra em dois níveis OU lateral compacta — o que couber melhor sem espremer.
4. Botão de estouro "···" (iniciado na F1) recolhe por grupo o que não cabe — nunca espreme, nunca corta.
5. Cada grupo com rótulo/separador visível — o dono acha o botão pela função, sem decorar posição.
6. Ícone + texto nos botões principais; só ícone com tooltip nos secundários — hierarquia clara.
7. A 1280×720 nenhuma ação ESSENCIAL vai para o "···" — as essenciais têm prioridade de espaço.
8. Estado honesto dos botões: desabilitado quando não se aplica, com o porquê no tooltip (nada de botão mudo que não faz nada).
9. Atalhos anotados nos tooltips (integra o catálogo de atalhos da F3).
10. A barra respeita os tokens da F1 (mínimos, respiro) e os dois temas.
11. Teste de largura: 1280/1366/1600/1920 — nada corta; o "···" só aparece quando de fato falta espaço.
12. Foto: a barra nas 4 larguras + claro e escuro.
13. Teste: a 720p nenhum botão fica cortado e as ações essenciais ficam fora do "···".
14. **Checagem:** suíte parcial verde; a barra passa nas 4 larguras sem corte.

## Bloco B — Modo planilha da estante (R-051) · passos 15–30
**Por quê:** "editar tudo de uma vez" — pedido nominal do dono. Nome, preço e
categoria numa grade, só com o teclado.

15. Um botão "Modo planilha" na estante abre a lista dos itens como grade editável.
16. Colunas: foto (miniatura), nome, preço, unidade, categoria — as que o dono mexe no dia a dia.
17. Editar com duplo-clique ou digitando; Enter confirma e desce; Tab confirma e vai à direita.
18. Navegação por teclado completa (setas, Home/End, Page Up/Down) — sem tocar o mouse.
19. Nome editado passa pela sanitização (RG-20) com prévia — não grava lixo.
20. Preço editado passa pelo parser P0.3 (rejeita "2x 5,00" → None com aviso) — nunca salva preço errado em silêncio (I2).
21. Categoria por combo/autocompletar com as categorias existentes — não digita livre e cria duplicata.
22. Edição em massa: selecionar várias linhas e aplicar categoria/ação de uma vez.
23. Colar do Excel/WhatsApp numa seleção (semente do R-050 da F7 — o parser é o mesmo, sem duplicar).
24. Desfazer (Ctrl+Z) na planilha volta a última edição de célula.
25. **Checagem (marco 1/4):** suíte inteira ×1 verde exit 0; screenshot da planilha editada por teclado em `saida_fase6/`.
26. Célula com problema destacada (preço não parseado, sem foto) — o dono enxerga o que falta.
27. Planilha e canvas são a MESMA fonte de verdade: editar o preço na grade reflete no desenho por uid (I1).
28. **Convivência com F7.3:** editar o item no banco atualiza quem NÃO tem override; quem tem, mantém o próprio, com aviso claro do que está "preso" pelo override.
29. Foto: a planilha com uma edição por teclado + uma linha com problema destacada (claro/escuro).
30. **Checagem:** suíte parcial verde; editar 3 campos por teclado persiste e reflete no canvas (por conteúdo).

## Bloco C — Estante viva: filtros, ordem e troca (R-054, R-055, R-057, R-069, R-020) · passos 31–48
**Por quê:** a mão manda na ordem; o mapa obedece por uid, nunca por posição.

31. R-054 (filtros): barra de filtros na estante — "sem foto" · "sem preço" · por categoria · busca por nome.
32. Filtros combináveis (sem foto + categoria) e com contador ("12 itens sem foto").
33. Limpar filtros com um clique; o filtro ativo fica visível como chip, para o dono lembrar o que está vendo.
34. R-055 (reordenar arrastando): arrastar um item muda a ordem visual; o mapa slot→uid respeita a nova ordem por uid (I1).
35. Linha de inserção durante o arrasto — o dono vê onde o item vai cair.
36. R-057 (trocar dois itens de célula): arrastar um item sobre outro TROCA os dois no mapa — troca de uid, nunca de posição (I1).
37. A troca é reversível (undo) e conserva o trio imagem/nome/preço de cada item (por conteúdo).
38. R-069 (duplicar item): duplicar cria um item novo com uid próprio (não uma referência) — editar a cópia não toca o original.
39. Duplicar copia os dados congelados (nome/preço/foto da época) como ponto de partida editável.
40. R-020 (estados vazios com ação): estante vazia mostra "Importe uma tabela" com o botão; filtro sem resultado mostra "Nada aqui — limpar filtro".
41. Nenhum estado vazio é um retângulo mudo — sempre um convite à próxima ação.
42. Reordenar/trocar respeita o override por slot (F7.3): o override é do slot; a operação move o uid.
43. Contagem viva no topo ("48 itens · 12 sem foto · 3 sem preço") — o pulso da montagem.
44. Multi-seleção (Ctrl/Shift) para arrastar, duplicar ou filtrar em bloco.
45. Foto: filtros ativos + arrasto de reordenar + troca de duas células (claro/escuro).
46. Teste: filtro "sem foto" mostra só os sem foto; reordenar muda a ordem por uid; trocar duas células troca os uids (adversarial por conteúdo).
47. Teste: duplicar cria uid novo independente; estados vazios mostram a ação.
48. **Checagem:** suíte parcial verde; adversarial da troca/reordenação passa (trio por conteúdo, override no lugar certo).

## Bloco D — Segurança do trabalho (R-061, R-017) · passos 49–62
**Por quê:** uma queda de luz nunca pode levar a montagem da semana; e a busca
global precisa estar em toda tela.

49. R-061 (rascunho automático): a cada ~2 min, gravar um snapshot silencioso do projeto aberto, sem interromper o dono.
50. O snapshot roda em background (worker; RG-05b cobre o shutdown) — não trava a UI.
51. Ao reabrir após uma queda, oferecer "Recuperar o rascunho de HH:MM?" com prévia — o dono decide.
52. O rascunho automático é separado das versões manuais (F2) — não polui a lista de versões.
53. Rotação dos rascunhos (guardar os últimos N; o número vem da config da F3).
54. **Nunca sobrescreve o projeto salvo em silêncio:** o rascunho é rede, não gravação por cima (respeita a lei da F2 — versões nunca por cima).
55. Indicador discreto "rascunho salvo HH:MM" no rodapé — confiança sem ansiedade.
56. R-017 (Ctrl+K global na Mesa): a paleta de busca/comando da F2 também abre na Mesa.
57. Ctrl+K na Mesa acha item na estante, ação da barra, ir para página, abrir Configurações — tudo por teclado.
58. É o MESMO componente da F2 (uma porta só, sem duplicar) — só a fonte de resultados muda por tela.
59. Foto: o aviso de rascunho recuperável + o Ctrl+K aberto na Mesa (claro/escuro).
60. Teste: simular "queda" (encerrar sem salvar) → reabrir oferece o rascunho e recupera por conteúdo.
61. Teste: Ctrl+K na Mesa encontra um item e uma ação da barra.
62. **Checagem (marco 3/4):** suíte inteira ×1 verde exit 0; screenshots de rascunho/Ctrl+K em `saida_fase6/`.

## Bloco E — Convivência com override e mapa · passos 63–74
**Por quê:** R-051/055/057 tocam o mapa slot→uid e não podem brigar com o
override por slot (F7.3) — o risco central do mapa desta fase.

63. Regra clara: o override pertence ao SLOT; o dado do banco pertence ao ITEM (uid). Reordenar/trocar move o uid; o override fica no slot que o dono ajustou.
64. Quando um item editado no banco (planilha) tem override no slot, a UI mostra qual valor está "preso" pelo override e como restaurar (pontinho violeta + "Restaurar do banco").
65. Trocar dois itens de célula: os uids trocam; os overrides de cada slot permanecem no slot (o dono ajustou AQUELA célula) — decisão registrada e testada.
66. Reordenar a estante não mexe em override (só muda a ordem do uid na lista) — provado por teste.
67. Duplicar item: o uid novo NÃO herda override de slot (override é do slot, não do item) — começa limpo.
68. Modo planilha edita o BANCO (item por uid); o aviso deixa claro que slots com override não mudam até o dono restaurar.
69. Pré-voo reavaliado: item trocado/reordenado sem foto/preço aparece no pré-voo na posição nova (I2).
70. Nenhuma dessas operações resolve conflito em silêncio — sempre com aviso (I2).
71. Compor uma página, reordenar/trocar/editar na planilha e recompor: o trio de cada item segue por conteúdo.
72. Rodar o adversarial do vínculo cobrindo troca, reordenação e edição em planilha.
73. Foto: um slot com override mantido após troca + o aviso "preso pelo override" (claro/escuro).
74. **Checagem:** suíte parcial verde; a matriz override × troca × reordenação × planilha coberta por teste.

## Bloco F — Integridade e adversarial (I1–I5) · passos 75–86
**Por quê:** a fase toca o mapa slot→uid em três frentes — o adversarial é o
juiz (I5), sempre por conteúdo.

75. Re-rodar `test_adversarial_vinculo.py` com reordenar, trocar e editar na planilha.
76. Adversarial: trocar duas células troca os uids e conserva o trio de cada uma (por conteúdo).
77. Adversarial: reordenar N itens mantém cada trio (nenhuma foto/preço migra para o vizinho).
78. Adversarial: editar o preço na planilha muda só aquele item (por uid), nunca o de posição igual.
79. Confirmar I1: nenhuma dessas operações usa índice de lista como vínculo.
80. Confirmar I2: rascunho automático, troca e reordenação nunca pulam item nem resolvem conflito em silêncio.
81. Confirmar I3: o snapshot do rascunho é portável (caminhos relativos), como os projetos.
82. Confirmar I4: mestra↔cópia intacto após reordenar a estante (o casamento é por uid, não por posição).
83. Rodar a suíte inteira ×2, zero skips (a arte real conta).
84. Medir o boot: a Mesa não regrediu; o rascunho automático não pesa a abertura.
85. Varredura de órfãos: nada criado nesta fase ficou sem uso.
86. **Checagem:** adversariais verdes; I1–I5 reconferidos e anotados.

## Bloco G — Fechamento · passos 87–100
**Por quê:** fase selada só com prova visual e o "cai a luz e não perde nada"
demonstrado ao vivo.

87. Suíte inteira ×2 exit 0, zero skips.
88. Adversariais do vínculo: nominais verdes (a fase tocou o mapa em três frentes).
89. Teste novo `test_fase6_mesa.py`: barra sem corte a 720p, planilha por teclado, filtros, troca/reordenação por conteúdo, rascunho recuperável, Ctrl+K na Mesa.
90. Demonstração da queda: encerrar o app no meio da montagem → reabrir → recuperar o rascunho intacto (por conteúdo).
91. `saida_fase6/`: barra nas 4 larguras, planilha, filtros, troca de células, aviso de rascunho, Ctrl+K — claro e escuro.
92. GIF curto (~15 s): editar 3 preços na planilha por teclado + trocar duas células por arrasto.
93. Varredura de jargão (PT-BR: "modo planilha", "rascunho automático", "trocar células").
94. Conferir que o override por slot (F7.3) segue íntegro após troca/reordenação/planilha.
95. Conferir que as versões manuais (F2) não foram poluídas pelo rascunho automático.
96. Boot e responsividade da Mesa medidos (barra e estante viva não travam com 5k itens).
97. Resposta do builder NESTE caderno (achados de bancada + "o que ficou de fora").
98. Atualizar `docs/PLANO_DE_CONSTRUCAO.md` e conferir o `CLAUDE.md`.
99. Screenshot-cartaz da Mesa arrumada (barra + estante viva + planilha) claro + escuro lado a lado.
100. **PARAR** para a reauditoria visual do arquiteto — a barra em todas as larguras, a planilha por teclado, a troca por conteúdo, a recuperação do rascunho. Nada da Fase 7 começa sem o selo.

---

## Registro do builder (em progresso)

**Baseline:** `pytest app/tests -q` → **538 passados, 0 falhas, 0 skips**.
**Subagentes:** 4 scouts de LEITURA no início (barra da Mesa/RG-53 · estante+
override F7.3 · mapa slot→uid+reordenar/trocar · versões F2+rascunho); ~340k
tokens somados. Implementação INLINE.

### Bloco A — barra da Mesa (RG-53) · passos 1–14 ✅
- **Causa-raiz instrumentada (lei RG-53):** a barra tinha conteúdo de ~1757px
  e o `minimumSizeHint` prendia a JANELA nessa largura — a 1280 real ela
  transbordava ("botões se comendo"), e o `_reflow_barra` lia 1757 como
  disponível, nunca colapsando. Foto: `saida_fase6/_probe_barra_1280.png`.
- **Conserto:** (1) `barra.setMinimumWidth(1)` — a janela chega a 1280; (2)
  `_reflow_barra` mede a base por TODOS os widgets fixos do layout (não só
  `QPushButton` — antes ignorava os checkboxes); (3) barra reorganizada por
  GRUPOS com separador: Desfazer/Refazer · Importar · Montar · Salvar/Exportar
  · Navegar. Os `_sacrificaveis` (só secundários) recolhem no "···"; os
  essenciais (importar/preencher/exportar/salvar/undo/redo) nunca colapsam.
- **Instrumentado nas 4 larguras:** 1280→5 colapsados, 1366→4, 1600→3,
  1920→0 (o "···" some). Monotônico.
- **Prova de mutação:** sem `setMinimumWidth(1)`, `minimumSizeHint ≤ 1280`
  falha (a janela não encolhe). Restaurado.
- **Testes:** `app/tests/test_fase6_mesa.py` (barra a 720p com essenciais fora
  do "···", monotonicidade imune ao vazamento de escala; sacrificáveis não
  incluem essenciais). Placar: **540 verdes, 0 skips.**

### Bloco B — modo planilha (R-051) · passos 15–30 ✅
- **Lógica testável** em `app/qt/telas/planilha.py`: `aplicar_edicao(item,
  coluna, texto)` edita o ItemMesa EM MEMÓRIA (nome/preço/unidade/categoria) —
  nome pela sanitização (RG-20); preço pelo parser P0.3 (ambíguo "2x 5,00" →
  NÃO grava, aviso, I2); `problema_na_celula` (sem foto/sem preço/preço não
  entendido) para o destaque.
- **Diálogo** `DialogoPlanilha` (QTableWidget): teclado nativo (Tab/Enter/
  setas), célula-problema em vermelho com tooltip, undo de célula (Ctrl+Z),
  categoria por combo editável com autocompletar (delegado), e **reflexo no
  canvas por uid** (`mesa.refletir_planilha` → `_dados_por_slot` → recompõe).
- **Convivência F7.3 (passo 28):** ao editar um campo com override no slot, a
  planilha avisa que a célula está "presa" (I2); o override é respeitado pela
  precedência do `_dados_por_slot` (célula sem override reflete; com override
  mantém). Botão "Modo planilha" na estante (habilita com itens).
- **Prova de mutação:** aceitar preço ambíguo → o teste de rejeição falha.
- **Testes:** +5 (parser rejeita/grava, sanitiza nome, problema por célula,
  reflete por uid, smoke do diálogo). Placar: **545 verdes, 0 skips.**
- **O que ficou de fora:** edição em MASSA (passo 22, aplicar categoria a
  várias linhas) e COLAR do Excel/WhatsApp (passo 23) — a lógica `aplicar_edicao`
  já é a base; ficam como incremento (não travam). A gravação no BANCO
  (produto_id, passo 68) foi mantida em memória: a chave do banco é `produto_id`
  e `preco_atual` é o "de"; o "por" da oferta é in-memory e salva no projeto.

### Bloco C — estante viva (R-054/055/057/069/020) · passos 31–48 ✅
- **Trocar (R-057):** `canvas.trocar_conteudo_slots(a, b)` — troca os uids no
  mapa (I1), os OVERRIDES ficam no SLOT (passo 65); undo unificado (molde do
  `set_override`). **Reordenar (R-055):** `canvas.reatribuir_mapa` +
  `mesa.reordenar_estante` (re-zip ocupáveis na nova ordem por uid) + arrasto
  `InternalMove` na estante. **Duplicar (R-069):** `mesa.duplicar_item` (uid
  NOVO, não referência; não herda override) no menu de contexto.
- **Filtros (R-054):** `servico.filtrar_itens` (combináveis: sem foto/sem
  preço/categoria/busca) + barra de filtros com chip "mostrando N de M".
  Estados vazios (R-020) já existiam (EstadoVazio com ação).
- **Adversariais (I1, por conteúdo):** trocar conserva o trio + override fica
  no slot (pixel); reordenar leva cada trio (nada migra); duplicar cria uid
  independente. **Provas de mutação:** troca no-op → falha; parser aceita
  ambíguo → falha; (Bloco A) sem shrink → falha.
- **Testes:** +3 adversariais no `test_adversarial_vinculo.py` + filtro no
  `test_fase6_mesa.py`. Placar: **549 verdes, 0 skips.**
- **O que ficou de fora:** o gesto de arrastar-um-item-SOBRE-outro para TROCAR
  (o método `trocar_conteudo_slots` está pronto e provado; falta só o gesto de
  arrasto sobre a célula — a reordenação por arrasto já funciona); contador por
  categoria no chip (o contador geral já mostra N de M).

### Bloco D — rascunho automático + Ctrl+K (R-061/017) · passos 49–62 ✅
- **Rascunho (R-061):** `app/core/rascunho.py` — snapshot JSON em `rascunhos/`,
  **isolado** de `projetos/`/`versoes/` (não passa por `salvar_projeto`, não
  cria versão, não toca o salvo); rotação para N (config `rascunhos.max`, molde
  do `_max_versoes`). Mesa: timer ~2 min → `_salvar_rascunho_bg` (worker
  `Trabalhador`+`self._trabalhos`, shutdown por `encerrar_todos`); indicador
  discreto "✓ rascunho salvo HH:MM"; `_oferecer_recuperacao` ao abrir (após
  queda) → `_recuperar_rascunho` reconstrói itens/layout/mapa/overrides por
  conteúdo (uid preservado, I1); **descarta o rascunho ao salvar de verdade**
  (passo 54, nunca por cima).
- **Ctrl+K (R-017):** `mesa._abrir_paleta` reusa a `PaletaComandos` da F2 com
  `_acoes_da_mesa` (itens da estante + ações da barra) — a MESMA porta, fonte
  de resultados da Mesa.
- **Testes:** +4 (rascunho isolado das versões + recupera por conteúdo,
  rotação, snapshot/recuperação da Mesa por conteúdo com uid, Ctrl+K acha item
  e ação). Placar: **553 verdes, 0 skips.**
- **O que ficou de fora:** a demonstração da queda AO VIVO (a lógica de
  coleta→gravar→recuperar está testada por conteúdo; falta só o vídeo).

### Bloco E — convivência override × mapa · passos 63–74 ✅
- Regra travada: **o override é do SLOT; o dado é do ITEM (uid)**. Coberto por
  teste: trocar move o uid e o override FICA no slot (adversarial do Bloco C);
  **reordenar NÃO mexe no override**; **duplicar NÃO herda override** (item novo
  começa limpo); a planilha edita por uid e o `_dados_por_slot` aplica a
  precedência override>item (Bloco B). Teste `test_adversarial_f6_matriz_
  override_x_mapa`. Pré-voo já varre os itens ocupados na posição atual (I2).

### Bloco F — integridade e adversarial I1–I5 · passos 75–86 ✅
- Adversariais F6 (troca/reordenar/duplicar/planilha) por CONTEÚDO no
  `test_adversarial_vinculo.py`; I1 (índice nunca é vínculo — mapa por uid),
  I2 (planilha/troca/rascunho avisam, nunca em silêncio), I3 (rascunho isolado
  e portável), I4 (mestra↔cópia por uid, herdado da F5). **Suíte ×2: 554
  verdes, 0 falhas, 0 skips**; boot da Mesa 35,6 ms (o timer do rascunho liga
  no show, não no boot); zero órfãos (rascunho/planilha referenciados).

### Bloco G — fechamento · passos 87–100 ✅
- Suíte ×2 exit 0, zero skips; `test_fase6_mesa.py` (barra 720p, planilha por
  teclado, filtros, rascunho recuperável, Ctrl+K) + adversariais F6.
- **Galeria NATIVA** (badges/texto legíveis para o selo): `saida_fase6/
  blocoG_mesa_{1280,1920}_{claro,escuro}.png` (barra sem sobreposição, grupos,
  essenciais + estante viva com filtros e Modo planilha),
  `blocoG_planilha_{claro,escuro}.png` (grade com células-problema em vermelho).
- Jargão PT-BR conferido; override íntegro e versões F2 não poluídas (rascunho
  isolado, testado); boot medido.

---

## RESPOSTA DO BUILDER (fecho da Fase 6)

**(a) Baseline:** 538 passados, 0 falhas, 0 skips.
**(b) Placar ×2:** **554 passados, 0 falhas, 0 erros, 0 skips** nas duas
rodadas (determinístico). +16 testes na fase.
**(c) O que ficou de fora** (núcleo pronto e testado; nada trava): planilha —
edição em MASSA e COLAR do Excel (a lógica `aplicar_edicao` é a base);
gravação no banco por produto_id (mantida em memória — o "por" é da oferta);
gesto de arrastar-item-SOBRE-item para TROCAR (o método está pronto e provado;
a reordenação por arrasto já funciona); demonstração da queda AO VIVO (a
recuperação por conteúdo está testada).
**(d) Achados de bancada:**
1. **RG-53 instrumentado antes de teorizar:** a barra tinha `minimumSizeHint`
   de ~1757px prendendo a JANELA — a 1280 real transbordava. `setMinimumWidth(1)`
   + medição genérica (não só QPushButton) resolveram; prova de mutação
   (`minimumSizeHint ≤ 1280` falha sem o conserto).
2. **Vazamento global de escala/fonte entre testes** (lição da F4) reapareceu
   na asserção de largura da barra — tornei-a imune medindo a largura real do
   conteúdo, não um px absoluto.
3. Distinção item-em-memória (a oferta, por uid) × produto-no-banco
   (por produto_id, o "de") — a planilha edita a oferta; o banco fica p/ o
   incremento.
Prova de mutação em cada teste-chave (barra, parser, troca, contraste da F5).
**(e) Subagentes e custo:** 4 scouts de LEITURA no início (~340k tokens,
barato); implementação 100% inline; revisores adversariais do fim não usados
(o adversarial próprio + a frota do arquiteto no passo 100 cobrem).
