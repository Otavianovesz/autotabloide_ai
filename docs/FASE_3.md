# FASE 3 — Configurações dignas + gestor de selos (caderno de 100 passos)

> Formato-lei do PLANO_PERFEITO. Cobre RG-51, R-014, R-018, R-088, R-128,
> R-129, R-132, R-133, R-134, R-135 + gestor de selos (RG-33) + o RG-59
> (cartões de evento) no Bloco A como aquecimento.
> **SELO DA FASE 2 (18/07):** aprovada com ressalva RG-59.
> **Por quê da fase:** o dono chamou as Configurações de "horríveis, tudo
> espremido, com uma engrenagem-fantasma que não existe". É o painel de
> controle do app — tem que ser em ABAS, respirável, e reunir tudo que hoje
> está escondido (selos, IA, backups, sanitização).

## SELO DO ARQUITETO — FASE 3 (18/07/2026): APROVADA

Inspeção visual: `cartoes_novos_claro.png` (RG-59 RESOLVIDO — capa em cover,
gradiente, nome branco sobreposto, chips de contagem/data, densidade real:
a cara de dashboard que o dono queria) e `abas/2_ia_escuro.png` (9 abas
laterais claras, título+descrição, campos respiráveis, "Testar conexão →
Ligado, 4 modelos", prompt do Fica-a-Dica editável, tudo PT-BR simples — a
antítese do "espremido"). Gestor de selos como entidade com +18 imutável
por pixel, verificar-instalação/integridade/diagnóstico/máquina-fraca, de-
para sem perda. **450 verdes ×2, adversariais 16/16. Selo concedido.**
Os dois achados de bancada (toast fantasma ao abrir; ordem dos selos) são
o protocolo funcionando. A decisão do ícone A×B virou campo na aba Sobre —
o dono resolve na tela. Onda estética do RG-59 encerrada. Fase 4 autorizada.

## Bloco A — RG-59: os cartões de evento refeitos (passos 1–10)
**Por quê:** o dono viu o Início e quer "muito mais bonito". A capa preenche.

1. Delegate/card do evento: capa em modo COVER preenchendo toda a largura (altura fixa ~150 px), cantos arredondados.
2. Gradiente escuro de baixo pra cima sobre a capa (legibilidade do texto).
3. Nome do evento em branco SOBRE a capa (canto inferior-esquerdo), sombra suave.
4. Contagem e data como chips translúcidos no canto inferior-direito da capa.
5. Faixa de cor do evento vira uma borda-superior fina + o acento dos chips (não uma barra solta).
6. Sem capa definida: gradiente da cor do evento + inicial grande estilizada (sem retângulo vazio).
7. Hover: leve zoom da capa (scale 1.03, 200 ms) + elevação (motor da Fase 1).
8. Densidade: 3 colunas a 1600+, 2 a 1280; cartões mais baixos (cabe mais na tela).
9. Foto claro+escuro dos cartões novos (com e sem capa) em `saida_fase3/`.
10. **Checagem:** comparar com `saida_fase2/inicio_final_claro.png` — densidade e beleza visivelmente melhores.

## Bloco B — A carcaça em abas (passos 11–24)
**Por quê:** fim do formulário-monólito espremido. Abas laterais claras.

11. Reescrever `configuracoes.py` como carcaça de abas verticais à esquerda (ícone+nome): Aparência · Campanhas · IA · Imagens · Selos · Sanitização · Backups · Atalhos · Sobre.
12. Cada aba é um QScrollArea próprio (conteúdo nunca corta; rola se precisar).
13. Largura mínima da área de conteúdo 560 px; formulários em grid de 2 colunas com respiro ESPACO_3 (tokens da Fase 1).
14. Cabeçalho de cada aba: título grande + uma linha de descrição do que ela controla.
15. **Remover a engrenagem-fantasma**: decidir o lugar ÚNICO das Configurações — a aba no topo FICA; a engrenagem do canto vira menu rápido (tema, Sobre, Configurações completas, diagnóstico) — nunca uma segunda tela morta.
16. Migrar o conteúdo atual (limiares, glossário, ordem de categorias, etc.) para as abas certas SEM perder nenhuma opção existente.
17. Toda mudança salva na Config na hora (com toast discreto "salvo") — nada de botão "aplicar" global esquecível.
18. Estado inválido (ex.: limiar verde ≤ amarelo) trava o campo com borda vermelha + dica, não deixa salvar (regra que já existia — preservar).
19. Busca dentro das Configurações (campo no topo filtra as opções por palavra).
20. Navegação por teclado entre abas (Ctrl+Tab) e dentro dos campos (Tab correto).
21. Aba lembra a última aberta (Config `configuracoes.ultima_aba`).
22. Fotos: cada aba claro+escuro (9 abas × 2 = fotos em `saida_fase3/abas/`).
23. Teste: abrir cada aba não quebra; salvar um valor em cada persiste.
24. **Checagem:** nenhuma opção do configuracoes.py antigo se perdeu (lista de-para no caderno).

## Bloco C — Aba Aparência (passos 25–32)
**Por quê:** reunir o que a Fase 1 criou num lar visível.

25. Seletor de tema (cards claro/escuro com prévia) — mover da Fase 1 pra cá.
26. Toggle de animações (ligadas/reduzidas) com explicação ("desligue no PC do mercado").
27. Escala da UI (100/125/150%) com prévia do efeito.
28. Som de exportação (liga/desliga) + botão "testar som".
29. "Reduzir transparências" (para máquinas fracas) — opcional.
30. Idioma: fixo PT-BR por ora (campo desabilitado com "em breve") — honestidade.
31. Foto da aba nos 2 temas.
32. **Checagem:** trocar cada opção reflete imediatamente no app.

## Bloco D — Aba Campanhas (passos 33–40)
**Por quê:** o dono trabalha por eventos (Quintou=qui, etc.); a config deles mora aqui.

33. Lista dos Eventos (da Fase 2) editável: nome, cor, dia da semana, capa, notas — mesma fonte de verdade, sem duplicar.
34. Ordem dos eventos arrastável (reflete no Início).
35. Ordem de setores/categorias (RG-44) editável aqui, com os presets da pesquisa como ponto de partida.
36. Data-padrão de validade da oferta por evento (RG-24/34): "válido por N dias" ou "até o próximo [dia]".
37. Frases prontas de aviso legal / validade com variáveis {data}, {evento} (semente do R-058 da Fase 7).
38. Foto da aba.
39. Teste: editar dia da campanha reflete no "Produzir hoje" do Início.
40. **Checagem:** suíte parcial verde.

## Bloco E — Aba IA (passos 41–48)
**Por quê:** o dono precisa trocar LM Studio↔Ollama e entender o que a IA faz — em linguagem simples.

41. Endpoint (URL base compatível-OpenAI) + modelos (visão/texto/embedding) editáveis — reusa o ConfigIA da Onda 4.
42. Botão "Testar conexão" (pinga o endpoint, diz "ligado/desligado" em verde/vermelho).
43. Painel de status em linguagem simples (R-090): modelo carregado, na fila, memória — sem jargão.
44. Limiares do semáforo (verde/amarelo) com explicação do que cada um faz.
45. Prompt do "Fica a Dica" editável (R-088) com prévia.
46. Toggle "usar IA" mestre (desligado = tudo degrada para fuzzy/manual, com aviso) — o perfil de máquina fraca (R-132) liga isto.
47. Foto da aba.
48. **Checagem:** testar conexão com endpoint falso mostra vermelho sem travar.

## Bloco F — Abas Imagens, Sanitização, Atalhos (passos 49–62)
**Por quê:** reunir o resto do que hoje está escondido ou não existe.

49. Aba Imagens: modelo de recorte (qualidade/rápido — da Onda 1), upscale (ligado/sob demanda), pasta da biblioteca (mostrar caminho), compressão WebP (R-100, só o toggle; a implementação é a Fase 10).
50. Detector de fundo-branco (pula rembg) como toggle (R-095, só a chave aqui).
51. Aba Sanitização: ordem Tipo+Marca+Sabor+Peso editável, caixa/unidades, glossário de siglas (VD→vidro), glossário de abreviações do tabloide (RG-22), glossário de marcas próprias (RG-30) — todos com "adicionar/remover linha" numa tabela limpa.
52. "Aplicar ao acervo" (o C2 da Etapa C) continua com prévia + confirmação — mover pra cá com botão claro.
53. Aba Atalhos (R-018): tabela de todos os atalhos, EDITÁVEIS (capturar tecla), com "restaurar padrão" e conflito acusado.
54. Folha de cola imprimível dos atalhos (botão "imprimir/exportar PDF").
55. Persistir atalhos customizados na Config; aplicar no boot.
56. Aba Sobre: versão, o que há de novo (changelog em PT-BR), créditos, ícone do app (a decisão A×B do dono entra aqui como campo se ele quiser trocar), botão diagnóstico.
57. Fotos das 3 abas.
58. Teste: adicionar sigla ao glossário e ver efeito na sanitização.
59. Teste: remapear um atalho aplica e persiste; conflito é barrado.
60. Teste: "aplicar ao acervo" mostra prévia e só aplica no confirmar.
61. Varredura: nenhuma opção antiga órfã (fechar o de-para do passo 24).
62. **Checagem:** suíte parcial verde.

## Bloco G — Gestor de SELOS completo (passos 63–78)
**Por quê:** RG-33 — o dono quer criar selos próprios ("Muito Barato",
"Destaque") e ter os automáticos (+18, BB Qualidade). LEI DA CASA: selo é
DECORATIVO — reavaliar ocupável/pré-voo ANTES do primeiro teste.

63. Modelo `Selo`: id, nome, arte (PNG relativo em `selos/`, I3), tipo (manual/automático), regra (para automáticos: "bebida_alcoolica"→+18, "marca_propria"→Qualidade), ativo.
64. Semear os 2 automáticos existentes (+18, Qualidade BB) como linhas `Selo` (migração idempotente).
65. Aba Selos: grade dos selos com miniatura, nome, tipo; "Adicionar selo" (upload PNG + nome + regra opcional).
66. Editar/excluir selo (excluir automático desliga a regra, não some do conceito).
67. Regras dos automáticos editáveis: qual flag do produto dispara qual selo.
68. Selo manual: aparece no menu "Selos deste item…" da estante (Mesa) e do Almoxarifado.
69. Colocação por item: o item guarda a lista de selos manuais escolhidos (além dos automáticos por flag).
70. No editor, a região SELO é o ponto de ancoragem multifunção (já existe) — o gestor só alimenta QUAIS selos entram.
71. Composição: desenhar os selos do produto (automáticos por flag + manuais escolhidos) na região SELO/âncora — reusar o `desenhar_selos` existente, agora lendo do gestor.
72. LEI DA CASA: a região SELO continua NÃO-ocupável e o pré-voo a ignora — confirmar com teste ANTES de seguir (RG-19/A7 valem).
73. Selo sem arte (upload falhou) → aviso no pré-voo, nunca quadrado vazio silencioso (I2).
74. Foto: aba Selos + um tabloide com selo manual "Muito Barato" aplicado.
75. Teste: criar selo, aplicar a um item, compor → o selo aparece por PIXEL na âncora.
76. Teste: +18 automático continua saindo em bebida (regressão da decisão travada).
77. Teste (LEI DA CASA): layout com região SELO não vira ocupável nem gera item-fantasma.
78. **Checagem:** suíte parcial verde; adversarial nominal (selos não deslocam o trio).

## Bloco H — Manutenção e robustez (passos 79–90)
**Por quê:** R-128/129/134/135 — o dono precisa de botões de "consertar" e
"diagnosticar" sem chamar ninguém.

79. Aba Backups (junta o Cofre-config): rotação de snapshots (número), pasta, "criar snapshot agora", "abrir pasta de backups".
80. "Verificar instalação" (R-134): teste de fumaça embutido (banco ok? fontes ok? pastas ok? IA responde?) com relatório verde/vermelho por item.
81. "Compactar banco" (R-135): VACUUM do SQLite com aviso de espaço liberado.
82. "Verificar integridade do acervo" (R-129): fotos órfãs (arquivo sem produto), produtos sem arquivo, pastas soltas — lista + "corrigir" (mover órfãs para uma pasta de quarentena, nunca apagar).
83. "Gerar diagnóstico" (R-128): zip com logs (travamentos.log, etc.), versões, contagens do banco — SEM dados sensíveis nem imagens — salvo na Área de Trabalho, para mandar ao suporte (você).
84. Contador local de erros por função (R-133): try/except das operações-chave incrementa um contador na Config; a aba Sobre mostra "top 3 funções com erro" (prioriza o próximo conserto).
85. Perfil de máquina fraca (R-132): um toggle que liga de uma vez — animações reduzidas + IA desligada + upscale sob demanda + transparências off; para o PC do mercado.
86. Fotos das abas de manutenção.
87. Teste: verificar-instalação num ambiente saudável = tudo verde.
88. Teste: integridade detecta uma foto órfã plantada e a coloca em quarentena (não apaga).
89. Teste: perfil de máquina fraca liga as 4 chaves de uma vez.
90. **Checagem:** suíte parcial verde.

## Bloco I — Fechamento (passos 91–100)
**Por quê:** a fase só vale selada, com prova visual de TODAS as abas.

91. Suíte inteira ×2 exit 0 zero skips.
92. Adversariais nominais (a fase toca selos→composição): 16/16.
93. Boot medido: as Configurações em abas não podem atrasar o boot (carregam sob demanda ao abrir a tela).
94. Teste novo `test_fase3_config.py`: de-para completo (toda opção antiga tem lar novo), abas persistem, gestor de selos por pixel.
95. Varredura de jargão nas 9 abas (PT-BR natural).
96. `saida_fase3/` final: cartões novos, 9 abas ×2 temas, tabloide com selo, GIF de 15 s navegando as Configurações.
97. Resposta do builder NESTE caderno (achados + "o que ficou de fora").
98. Atualizar PLANO_DE_CONSTRUCAO.md e conferir CLAUDE.md.
99. Screenshot-cartaz das Configurações claro+escuro lado a lado.
100. **PARAR** para a reauditoria visual do arquiteto (todas as abas, uma a uma).

---

## Execução do builder (18/07/2026 — em curso, registrado por checagem)

Linha de base confirmada: **428 verdes, zero skips, exit 0**.

### ✔ Checagem do passo 10 (Bloco A — RG-59)

- `_CartaoCapa` (widget PINTADO): capa em COVER preenchendo o cartão
  inteiro (150 px, cantos arredondados, clip por path), gradiente escuro
  de baixo para cima, nome em BRANCO sobreposto com sombra de 1 px,
  contagem/data como chips translúcidos no canto inferior-direito com o
  texto na cor do evento clareada, borda-superior fina de 3 px na cor
  (fim da barra solta); sem capa → gradiente da própria cor + inicial
  gigante translúcida (nunca retângulo vazio); hover com zoom 1.03 em
  200 ms + elevação da Fase 1 (e a lei da captura: WA_DontShowOnScreen
  não anima).
- Ajuste de inspeção: o cover ancorou no TOPO para tabloide vertical —
  o cartão mostra o CABEÇALHO da arte (o neon "Quintou Do Real", o logo
  Belo Brasil), não produtos aleatórios do miolo. É a marca da campanha
  como identidade do cartão.
- **Comparação com saida_fase2/inicio_final_claro.png:** antes, miniatura
  de ~110 px perdida num retângulo branco de 700×200 com 70% de vazio;
  agora a arte preenche 100% do cartão de 150 px com o nome sobreposto —
  mais denso (cartão 25% mais baixo) e visivelmente mais bonito
  (fotos: cartoes_novos_{claro,escuro}.png + cartoes_sem_capa_claro.png).
- Testes do dashboard adaptados à leitura por conteúdo do widget pintado
  (`_titulo`/`_chips`); `_cartao_base` antigo removido (morto).
- Suíte: verde (placar acima), zero skips, exit 0.

### ✔ Checagem do passo 24 (Bloco B — o de-para completo)

Carcaça: lista de abas vertical (190 px, ícone+nome, ativa em destaque) +
QStackedWidget onde CADA página é um QScrollArea com conteúdo ≥560 px e
cabeçalho título+descrição (12-14). Salvar NA HORA com debounce de 700 ms
e toast "Salvo." discreto (17); limiar inválido trava com borda vermelha
e não sobrescreve o valor válido (18 — provado); busca no topo esconde as
linhas de formulário sem match e apaga as abas sem resultado (19,
`setRowVisible` do Qt 6.4); Ctrl+Tab circula (20); última aba lembrada
(21 — provado). A engrenagem do Shell virou o MENU RÁPIDO definitivo
(tema · Configurações completas · Sobre) — lugar ÚNICO, fim do fantasma
(15). O botão "Salvar" global morreu (redundante com o salvar-na-hora); o
"aplicar ao acervo" (C2) mora na aba Sanitização com prévia+confirmação.

**DE-PARA (nenhuma opção perdida — 25/25):**
| opção antiga | aba nova |
| seletor_tema, combo_escala, chk_som | Aparência |
| campo_categorias (+Preset da loja), campo_eventos (dias), campo_secao_estilo/por_cat/cor/esp | Campanhas |
| campo_url, campo_mod_texto/visao/emb, campo_verde, campo_amarelo | IA local |
| campo_cmyk, campo_icc, campo_rembg, btn_ocr (esquecer leituras) | Imagens |
| lista_selos + adicionar/remover | Selos |
| campo_siglas, campo_glossario, campo_abreviacoes, campo_marcas*, aplicar-ao-acervo | Sanitização (*marcas em Campanhas) |
| campo_rotacao | Backups |
| — (novas nesta fase) | Atalhos, Sobre (recheiam nos passos 53-56) |

- Fotos (22): 18 em saida_fase3/abas/ (9 abas × 2 temas), inspecionadas —
  a aba IA mostrada acima do dobradiça: título grande, descrição,
  formulário respirado. Ajustes da inspeção: botão Salvar global removido
  e a busca alargada.
- Testes (23): 9 abas abrem; salvar-na-hora persiste (rotação=7);
  inválido marca e não sobrescreve; última aba lembrada.
- Suíte: **430 passed, zero skips, exit 0**.

### ✔ Checagem do passo 32 (Bloco C — aba Aparência)

- Reunida no lar: tema em cards (25, da Fase 1), escala 100/125/150%
  aplicando NA HORA (27 — a aplicação imediata É a prévia), animações
  ligadas/reduzidas com a explicação do PC do mercado (26, persiste +
  `recarregar_config` na hora), som + "Testar som" (28 — o teste toca sem
  depender da chave), "Reduzir transparências" (29) com CONSUMO REAL: o
  véu escurecido dos diálogos e o véu de hover deixam de ser pintados
  (chave de mentira não entra na casa), idioma PT-BR desabilitado com
  honestidade (30).
- **Defeito de fase anterior pego na inspeção da foto:** a regra
  `QCheckBox:focus::indicator` (Fase 1, passo 67) era sintaxe malformada
  e o Qt vazava uma borda azul na LARGURA TOTAL de todo checkbox — curada
  para `QCheckBox::indicator:focus`.
- recarregar reflete os 3 toggles sem disparar (blockSignals).
- Fotos (31): 0_aparencia_{claro,escuro} refeitas e inspecionadas.
- Suíte (32): verde (placar acima), zero skips, exit 0.

### ✔ Checagem do passo 40 (Bloco D — aba Campanhas)

- Gestor de eventos NA CONFIGURAÇÃO (33-34): `_caixa_eventos()` com a
  lista dos eventos (swatch da cor 14px + "· toda qui"), arrastar
  reordena e persiste (`rowsMoved` → `reordenar` do serviço), duplo
  clique abre o MESMO EventoDialog do Início (renomear/cor/dia/capa —
  uma porta só, zero código duplicado).
- Validade padrão por evento (36): combo "até o próximo dia da campanha"
  | "válido por 3/5/7 dias", persistido em `eventos.validade_regra`
  {nome: "dia"|N}. **Com CONSUMO**: `sugerir_validade` agora consulta a
  regra — N dias → "ATÉ hoje+N"; "dia"/sem regra → o clássico RG-24
  (próxima ocorrência). Teste data-fixa: qua 15/07 com N=3 → "ATÉ 18/07";
  com "dia" → "ATÉ 16/07" (a quinta). Chave sem consumo não entra.
- Frases prontas (37, semente do R-058): `campo_frases` com variáveis
  {data}/{evento}, grava `frases.validade` (uma por linha, vazias fora).
- Fotos (38): 1_campanhas_{claro,escuro} refeitas com 3 campanhas reais
  semeadas e inspecionadas — a "Fim de Semana" selecionada mostra o
  combo refletindo "válido por 3 dias".
- Teste do passo 39: editar o dia do evento PELA ROTA das Configurações
  (`definir_dia`, a mesma do EventoDialog) liga/desliga o "Produzir
  hoje:" do Início — conferido por conteúdo dos QLabel.
- **Registro honesto:** o campo legado "Dias das campanhas" (RG-24,
  texto `Evento = dia`) segue na aba COEXISTINDO com o gestor visual —
  nenhuma opção se perdeu, mas há duplicidade de porta para o mesmo
  dado; a resolução (rebaixar o campo texto ou removê-lo do de-para)
  fica anotada para o fechamento do de-para no passo 61.
- Suíte parcial: **56 verdes** (fase3_config 5 · configuracoes ·
  fase2_eventos · fase2_inicio · dashboard · onda4), zero skips, exit 0.

### ✔ Checagem do passo 48 (Bloco E — aba IA)

- Endpoint (41): já vinha da carcaça (URL + 3 modelos, ConfigIA da
  Onda 4); agora com "Testar conexão" (42) NUM WORKER (Trabalhador +
  GerenciadorTrabalhos — a tela nunca congela; RG-05b cobre o shutdown).
  Teste da checagem: porta morta 127.0.0.1:9 → "● Desligado — o servidor
  não respondeu…" em VERMELHO (cor conferida pelo styleSheet com
  t.PERIGO), botão reabilitado em <15 s, zero travamento.
- Status em linguagem simples (43, R-090): após o teste, um papel por
  linha — "✓ O modelo de texto (nomes, conciliação) está no servidor" /
  "✗ … não apareceu na lista; confira o nome". **Adaptação honesta:**
  memória e fila NÃO são expostas pela API padrão compatível-OpenAI
  (decisão travada: não acoplar ao LM Studio) — o painel mostra o que a
  API dá: ligado/desligado + quais dos 3 modelos o servidor conhece.
- Limiares (44): explicação em uma legenda corrida ("cada item ganha uma
  NOTA de 0 a 100 de parecença… verde casa sozinho; entre amarelo e
  verde pede conferência; abaixo, produto novo") acima dos dois campos.
- Prompt do Fica a Dica (45, R-088): `PROMPT_DICA_PADRAO` extraído para
  constante; chave `ia.prompt_dica` (vazio = padrão; {limite} trocado
  por replace, imune a chaves digitadas pelo usuário); `gerar_dica`
  CONSOME (teste com motor-espião confere o system prompt recebido).
  Prévia real por botão, em worker, com aviso honesto sem IA.
- Interruptor mestre (46): `ia.usar` com CONSUMO no
  `ClienteOpenAICompat.disponivel()` (False sem tocar a rede) + aviso
  visível de degradação na aba e toast ao desligar (I2). R-132 (Bloco H)
  vai ligar esta chave.
- **Bancada com IA REAL** (LM Studio aberto na máquina): teste de
  conexão verde com 4 modelos; `gerar_dica` ponta a ponta devolveu dica
  de 176 chars ≤ teto 180.
- **Defeito pego na FOTO do 47:** abrir a tela disparava um salvamento
  fantasma (o `recarregar()` do showEvent dispara textChanged dos
  QPlainTextEdit → debounce → toast "Salvo." sem o usuário tocar em
  nada). Cura: o fim do recarregar mata o debounce agendado — refletir
  não é editar. Fotos refeitas limpas: 2_ia_{claro,escuro}.
- Suíte parcial: fase3_config (8) + configuracoes + onda4 (50) +
  etapa_a + conciliacao (19) — todos verdes, zero skips, exit 0.

### ✔ Checagem do passo 62 (Bloco F — Imagens, Sanitização, Atalhos, Sobre)

- **Aba Imagens (49-50):** upscale automático desligável COM consumo
  (`upscale_para_cartaz` checa `imagem.upscale_auto` e, desligado, avisa
  no status — nunca em silêncio); pasta da biblioteca visível com "Abrir
  pasta"; WebP (R-100) e detector de fundo branco (R-095) como chaves
  ROTULADAS "preparação — entra em ação na Fase 10" no próprio texto do
  checkbox (semente autorizada pela ordem; sem fingir função).
- **Aba Sanitização (51-52):** glossário de siglas e abreviações do
  tabloide viraram TABELAS limpas (componente `TabelaPares`: 2 colunas +
  adicionar/remover; linha incompleta conta como ignorada — I2); ordem
  do nome REORDENÁVEL por arrasto (`sanitizacao.ordem`, consumida no
  prompt do enriquecer via `ordem_do_nome()` — só aceita os 4 blocos
  permutados); "Palavras minúsculas" editável (`regras_de_config`
  consome); marcas próprias MUDARAM de Campanhas para cá (RG-30 é regra
  de nome). **Adaptação honesta:** unidades (g/kg/ml/L) ficam travadas
  (decisão de fidelidade) — a aba explica em tooltip, não finge opção.
  "Aplicar ao acervo" continua com prévia + confirmação (teste 60 na
  TELA: cancelar deixa intacto, confirmar reformata).
- **Aba Atalhos (53-55, R-018):** catálogo central novo
  (`app/qt/design/atalhos.py`, 19 atalhos em 3 grupos) — TODAS as telas
  criam atalhos por ele (editor, barra, Mesa, Ctrl+K do shell, Ctrl+Tab
  da config); tabela editável com captura de tecla (QKeySequenceEdit);
  CONFLITO BARRADO por escopo (mesmo grupo, e "Geral" cruza com todos —
  lição do Ctrl+K); remap APLICA NA HORA nos QShortcut vivos (vivário
  com weakref + setKey) e persiste (`atalhos.custom`, só os diferentes
  do padrão); "Restaurar padrões"; folha de cola em PDF (QTextDocument →
  QPrinter). Espelhos fixos preservados: Backspace (excluir) e
  Ctrl+Shift+Z (refazer da Mesa) não entram no catálogo.
- **Aba Sobre (56):** versão, novidades em PT-BR, créditos; a decisão
  A×B do ícone virou CAMPO com consumo real (`app.icone` →
  `icone_aplicativo()` desenha "A" azul ou "B" laranja BB e aplica na
  janela na hora — o dono decide sozinho, sem mexer em código);
  diagnóstico para suporte (R-128 ANTECIPADO do Bloco H para não nascer
  botão morto: `app/core/diagnostico.py` gera zip com versões, contagens
  e fim do log de travamentos — SEM banco, fotos ou textos do dono).
- **Passo 61 (de-para fechado):** nenhuma opção órfã — 25/25 do de-para
  do passo 24 seguem com lar; a DUPLICIDADE anotada na checagem 40
  (campo-texto "Dias das campanhas" × gestor visual) foi RESOLVIDA:
  o campo-texto saiu (mesma função no gestor, via `definir_dia`);
  `eventos.dias` fica só como legado lido pela migração.
- Fotos (57): {1_campanhas, 3_imagens, 5_sanitizacao, 7_atalhos,
  8_sobre} × 2 temas refeitas e inspecionadas (as tabelas com semente,
  o QKeySequenceEdit por linha, a pasta real no campo).
- Testes 58-60 verdes: sigla na TABELA muda `formatar_nome` ponta a
  ponta; remap persiste + troca o atalho VIVO + conflito barrado +
  restaurar; prévia do acervo só aplica no confirmar.
- **Suíte INTEIRA: 439 passed, 0 failures, 0 skips (junit), exit 0.**

### ✔ Checagem do passo 78 (Bloco G — gestor de SELOS como entidade)

- **Modelo (63):** entidade `Selo` (nome único, arquivo RELATIVO a
  selos/ — I3, tipo manual/automático, regra, canto, ativo) + serviço
  `app/core/selos.py` (migração, CRUD, `config_automaticos`).
- **Migração (64):** idempotente (teste: 2ª rodada cria 0) — semeia +18
  (regra bebida_alcoolica) e Qualidade Belo Brasil (marca_propria) e
  importa os manuais da Config legada `selos.personalizados` (que fica
  intocada); roda de carona em `selos_disponiveis`/na aba.
- **Aba Selos (65-67):** grade com MINIATURA real (arte do disco, ou o
  badge interno desenhado via render_selo → QImage), tipo rotulado em
  linguagem simples; Adicionar (PNG+nome), Editar (nome, canto, trocar
  arte, e nos automáticos ligar/desligar a regra), Excluir/desligar.
- **Decisão travada respeitada:** o +18 em bebida alcoólica NÃO desliga
  — `definir_ativo`/`excluir_selo` recusam, o checkbox do editar aparece
  travado com a explicação, e o teste 76 prova por PIXEL que o badge sai
  mesmo após a tentativa de desligar. Interpretação registrada para o
  arquiteto: o passo 66 ("excluir automático desliga a regra") vale para
  o Qualidade; no +18 a decisão travada tem precedência.
- **Composição (71):** `_selos_do_produto` agora lê o GESTOR
  (canto/arte custom valem; Qualidade desligado não sai — teste por
  pixel de ambos os lados); sem banco cai no clássico (C3, mesmo padrão
  do config_secoes). Interface `selos_disponiveis`/adicionar/remover
  preservada (os testes RG-33 da Onda 5 seguem verdes) — 1 cura de
  fidelidade: `listar_selos` devolve ordem de INSERÇÃO (o teste antigo
  acusou a alfabética).
- **Lei da casa (72):** confirmada ANTES de seguir — o teste da 4ª
  aplicação (Onda 5) verde + teste NOVO da 5ª aplicação (77): com a
  TABELA populada e selo manual aplicado, região SELO segue fora do
  ocupável e o pré-voo imune (célula única, nunca fantasma).
- **I2 (73):** pré-voo NOVO acusa "a arte do selo X sumiu do disco —
  sai o selo genérico no lugar" (teste apaga o PNG e confere o aviso).
- Fotos (74): 4_selos_{claro,escuro} (miniaturas + tipos) e
  `tabloide_selo_manual.png` — "Muito Barato" dourado no canto do arroz,
  +18 automático na cerveja, tudo composto de verdade.
- Testes novos: 6 (migração, pixel manual, +18 travado, Qualidade
  desligável, lei da casa 5ª, arte sumida no pré-voo).
- **Suíte INTEIRA: 445 passed, 0 failures, 0 skips (junit), exit 0;
  adversariais nominais 16/16 verdes.**

### ✔ Checagem do passo 90 (Bloco H — manutenção e robustez)

- **Aba Backups (79):** rotação (de sempre) + pasta visível + "Criar
  snapshot agora" (manual, fora da rotação) + "Abrir pasta de backups".
- **Verificar instalação (80, R-134):** `app/core/manutencao.py::
  verificar_instalacao` — banco (PRAGMA quick_check), pastas do estúdio,
  fontes (Roboto), IA; relatório verde/vermelho POR ITEM em worker.
  Honestidade de contrato: a IA é marcada OPCIONAL (fora do ar = âmbar
  informativo, não instalação quebrada — o app degrada com aviso).
  Na foto da máquina real: 4/4 verdes (a IA respondeu de verdade).
- **Compactar banco (81, R-135):** VACUUM com o espaço liberado no toast
  ("N KB liberados (antes → depois)").
- **Integridade do acervo (82, R-129):** fotos órfãs detectadas
  (quarentena e cache do upscale não contam) e produtos com foto sumida
  listados; órfãs vão para `biblioteca_imagens/_quarentena/` SÓ com
  confirmação e preservando a subpasta — NUNCA apaga (o teste 88
  confere que o arquivo segue vivo e que a 2ª varredura fica limpa).
- **Diagnóstico (83, R-128):** já nascido no Bloco F; agora o diálogo
  sugere a ÁREA DE TRABALHO como destino, como o passo pede.
- **Contador de erros (84, R-133):** `registrar_erro`/`top_erros`
  (Config `erros.contadores`) com CONSUMO em dois pontos: o except do
  `Trabalhador` (toda operação pesada do app conta sozinha) e a aba
  Sobre mostra o top 3 em linguagem simples ("prioriza o próximo
  conserto"); contador jamais levanta (não pode piorar o erro que conta).
- **Máquina fraca (85, R-132):** UM toggle na aba Backups liga as 4
  chaves de uma vez (animações reduzidas + transparências reduzidas +
  IA desligada + upscale desligado) e desligar devolve os padrões; o
  teste 89 confere as 4 chaves E o consumo real (`ConfigIA.da_config()
  .usar is False`); o recarregar espelha os toggles individuais.
- Fotos (86): 6_backups_{claro,escuro} (com o relatório da verificação
  pintado) e 8_sobre_{claro,escuro} refeitas (top de erros no Sobre).
- Testes 87-89 + contador: 4 novos, todos verdes.
- **Suíte INTEIRA: 449 passed, 0 failures, 0 skips (junit), exit 0.**

---

## Resposta do builder (19/07/2026) — FASE 3 executada, passos 1–99; PARADO no 100

### Placar final
- **Suíte inteira ×2: 450 passed / 0 failures / 0 skips (junit), exit 0**
  (linha de base 428 → 450: +22 testes novos na fase).
- Adversariais nominais: **16/16** verdes (selos não deslocam o trio; a
  composição nova lendo o gestor passou pelo adversarial de vínculo).
- Boot (93): a ConfiguracoesTela custava ~180 ms na fase 2 do boot —
  virou tela PREGUIÇOSA no shell (`adicionar_tela_preguicosa`): constrói
  na 1ª visita, o boot não paga nada.

### Bugs meus, achados pelos meus testes/fotos (honestidade de bancada)
1. **Salvamento fantasma ao abrir a tela** — o `recarregar()` do
   showEvent disparava textChanged dos campos → debounce → toast "Salvo."
   sem o usuário tocar em nada. PEGO NA FOTO do passo 47; curado
   (refletir não é editar: o fim do recarregar mata o debounce).
2. **Ordem dos selos** — meu `listar_selos` ordenava por nome; o teste
   RG-33 da Onda 5 acusou (contrato era ordem de inserção). Curado na
   produção.
3. **`test_ia_fake.py` inexistente** numa suíte parcial abortou a coleta
   em silêncio (saída vazia) — detectado e substituído pelos arquivos
   certos; nenhuma checagem foi registrada com esse buraco.

### Interpretação registrada para o arquiteto decidir
- Passo 66 ("excluir automático desliga a regra") × decisão travada
  ("+18 automático SEMPRE em bebida alcoólica"): apliquei a precedência
  da decisão travada — o +18 não desliga (recusa no serviço, checkbox
  travado com explicação na UI, teste por pixel); o Qualidade BB
  desliga normalmente. Se o dono quiser +18 desligável, é 1 guarda a
  remover — mas a trava está testada como lei.

### Adaptações honestas (registradas nas checagens)
- R-090: memória/fila do modelo NÃO saem da API padrão compatível-OpenAI
  (não acoplar ao LM Studio é decisão travada) — o painel mostra o que a
  API dá: ligado/desligado + os 3 modelos conferidos por papel.
- Unidades (g/kg/ml/L) seguem travadas na Sanitização (decisão de
  fidelidade), com explicação na própria aba — sem opção de mentira.
- R-128 (diagnóstico) foi ANTECIPADO do Bloco H para o F: a aba Sobre
  nasceria com botão morto (lição RG-09); o H o completou (destino
  sugerido = Área de Trabalho).
- A duplicidade campo-texto × gestor visual de campanhas (anotada na
  checagem 40) foi resolvida no passo 61: o campo-texto saiu;
  `eventos.dias` é só legado de migração.

### O que ficou de fora (para ninguém descobrir depois)
- **WebP (R-100) e detector de fundo-branco (R-095):** SÓ as chaves,
  rotuladas "preparação — entra em ação na Fase 10" no próprio checkbox
  (é o que a ordem pede; nada finge funcionar).
- **Prévia do Fica a Dica** usa 3 itens fictícios fixos (arroz/feijão/
  óleo) — a tela de Configurações não conhece o projeto aberto; a prévia
  real por projeto é o próprio canvas.
- **Atalhos:** os espelhos fixos (Backspace = excluir; Ctrl+Shift+Z =
  refazer da Mesa) e teclas internas de diálogo (Esc da paleta, Ctrl+V
  da curadoria) ficaram FORA do catálogo de propósito — remapeá-los
  criaria conflitos de convenção; a folha de cola lista o catálogo.
- **Contador de erros (R-133)** conta o que passa pelo `Trabalhador`
  (todas as operações pesadas); exceção síncrona de UI não conta — o
  vigia de travamentos cobre a outra metade.
- **GIF (96):** navegação por cortes de aba (1 quadro/aba, ~15 s) — não
  é gravação contínua de mouse; o Gravador de Passos do dono cobre isso
  na revisão geral.
- **Ícone "B" laranja** usa o âmbar do design system (#F59E0B) como
  laranja BB — se o dono tiver o tom exato da marca, é 1 linha.

### Artefatos para a reauditoria visual (saida_fase3/)
- `cartoes_novos_{claro,escuro}.png`, `cartoes_sem_capa_claro.png` (RG-59)
- `abas/{0..8}_{chave}_{claro,escuro}.png` — **as 18, todas refeitas no
  estado final** (Campanhas com gestor; IA com status verde REAL do LM
  Studio; Sanitização em tabelas; Selos com miniaturas; Backups com o
  relatório da verificação; Atalhos com captura por linha; Sobre com
  novidades + ícone A×B + top de erros)
- `tabloide_selo_manual.png` — selo "Muito Barato" + o +18 automático
  compostos de verdade
- `configuracoes_navegacao.gif` — 9 abas, ~15 s
- `cartaz_configuracoes_claro_escuro.png` (passo 99)

**Passo 100: PARADO.** Aguardo a reauditoria visual do arquiteto, aba por
aba. Nada da Fase 4 foi iniciado.
