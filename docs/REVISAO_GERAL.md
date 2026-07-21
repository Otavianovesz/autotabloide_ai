# REVISÃO GERAL — Auditoria do dono (17/07/2026) → dossiê normativo

> Compilado pelo arquiteto (Cowork) a partir de: **transcrição integral do
> áudio do Otaviano** (sessão de ~1h), **4 gravações do Gravador de Passos**
> (Ateliê 102 · Mesa 444 · Fábrica e Outros 324 · Configurações e Novo
> Tabloide 187 = 1.057 capturas, 17:59–19:00) e artes novas **Sexta Verde**
> (template + peça pronta — 3ª campanha real; entra como padrão-ouro).
> Amostra de capturas extraídas em `revisão/frames_arquiteto/`; o builder
> extrai o restante dos .mht quando precisar (base64 dos JPEG entre os
> boundaries `--=_NextPart_SMP_...`).
>
> **Este documento SUBSTITUI a ordem vigente.** O que restava da ORDEM_F8
> (Etapas C/D/E) foi absorvido: o marco dos ~40 vira o teste de regressão
> final da revisão (Onda 5) e os orçamentos de performance viram a Onda 1.
> Execução por ONDAS, na ordem; cada onda = uma etapa com reauditoria e
> selo, como sempre. I1–I5 e "exit 0 limpo" valem.

## O que o dono APROVOU (preservar — não "melhorar" o que já agrada)

Exportação final do tabloide ("ficou bom"); busca de imagem quando acerta
("perfeita", "corretíssima"); curadoria com re-busca; painel de preço
(subtipo/papel de-por: "esse aqui tá bom"); compor itens + editar nome do
composto ("maravilha"); leque ("ficou até que bonito"); OCR leu o print
inteiro certo; validade capturada da foto; criação de layout do zero
("plausível… gostei"); Ctrl+C/V de regiões no editor.

---

## ONDA 1 — DESEMPENHO (a reclamação nº 1, repetida 5×)

- **RG-01 Abertura lenta do app** ("demora demais… reclamo muito"). Provável:
  imports pesados no boot (rembg/onnx/torch/PySide tudo ansioso).
  Ordem: medir o boot (log por fase), lazy-import de TUDO que é pesado
  (rembg/upscale/IA só no primeiro uso), splash com progresso. Meta: < 5 s
  até o Dashboard (orçamento que já era do F8-D1).
- **RG-02 Pipeline de criação lento e sequencial** (enriquecer por item;
  rembg 26 s; busca lenta). Ordem: (a) **enriquecer em LOTE** todos os
  vermelhos logo após a conciliação (fila em background; ao abrir o Criar o
  nome já está pronto); (b) **pré-buscar candidatos** do próximo item
  enquanto o humano decide o atual; (c) **rembg: reusar a sessão/modelo**
  (o recarregamento por chamada é o suspeito dos 26 s — manter o birefnet
  vivo entre chamadas) + opção de modelo leve na Config; (d) paralelizar
  busca+download.
- **RG-03 Dinâmica "editar primeiro, fotos depois"**: checkbox por sessão
  "buscar fotos automaticamente? sim/não" — com NÃO, o fluxo cria tudo sem
  foto rapidinho e depois um "Buscar fotos em lote" processa a fila (com
  fila visível). É a dinâmica que o dono pediu para o PC fraco do mercado.
- **RG-04 OCR**: progresso por linha durante a leitura (percepção conta) e
  **cache da última importação na Fábrica/Mesa** (reimportar a mesma foto
  não re-roda OCR — aconteceu na auditoria e custou minutos).

## ONDA 2 — ESTABILIDADE (bugs vistos ao vivo)

- **RG-05 Travamentos (2×)**: após exclusões no Almoxarifado + na Mesa com
  zoom (captura Mesa_350/18:22: canvas cinza, zoom 2%, cursor de espera).
  Caçar com prioridade máxima: suspeitos = diálogo modal atrás (velho
  conhecido), worker sem encerrar, e o estado de zoom corrompido
  (fitInView com cena vazia?). Reproduzir, corrigir, e pôr watchdog de
  logging (traceback de travamento no log).
- **RG-06 Teclado**: Delete/Backspace excluem a região selecionada no
  editor; Ctrl+V cola na curadoria (o botão funciona, o atalho não);
  **desfazer/refazer NA MESA** (botões + Ctrl+Z/Y — hoje só o Ateliê tem).
- **RG-07 Estante sem gestão**: excluir item da estante (botão direito +
  tecla Del), limpar estante, contagem. Ele NÃO conseguiu excluir nada.
- **RG-08 Dessincronia**: editar layout no Ateliê não reflete na
  Mesa/Fábrica aberta (recarregar ao trocar de tela); salvar do editor de
  cartaz não persistiu gramatura/posição na percepção dele (investigar com
  as capturas de 18:52+); Almoxarifado não atualiza após salvar na Mesa
  (auto-refresh); indicador salvo/não-salvo confundiu — revisar quando ele
  liga/desliga.
- **RG-09 Botão "Editar" do Almoxarifado não faz nada** (painel já é
  inline — remover o botão morto ou dar função real).
- **RG-10 Biblioteca do Ateliê**: itens arrastáveis bagunçam a grade ("não
  gostei disso") — lista fixa ordenada, sem drag.

## ONDA 3 — UX DO EDITOR (paridade Illustrator)

- **RG-11 Navegação**: roda = rolagem vertical; Ctrl+roda = horizontal;
  **Alt+roda = zoom** (confirmado por ele); barras de rolagem visíveis.
- **RG-12 Rotação de região** (a data deitada do template dele) — rotação
  no modelo/handles/composição (era o "ficou de fora" da F5.2; virou
  necessidade real).
- **RG-13 Hifenização automática** na quebra de texto (como o Illustrator)
  + justificado correto.
- **RG-14 Pesos da família de fonte** (Black/Bold/Light selecionáveis —
  "quero Black").
- **RG-15 Célula como GRUPO visível**: hover/seleção destaca o trio da
  célula (imagem+nome+preço) — "não consigo identificar qual é qual, clico
  e dá errado". Clique na célula seleciona o grupo; segundo clique entra na
  região.
- **RG-16 Painéis**: dropdowns cortados ("fica tudo coisadinho, não vejo
  as opções"), respiro, e rótulos claros ("Nome: Nome" → "Rótulo da
  camada"; "esse estilo serve pra quê?" → tooltip).
- **RG-17 Onboarding**: tooltip em TODO controle (pontinhos âmbar/violeta/
  laranja com legenda; "Agrupar como replicável" explicado), microtutorial
  de primeiro uso por tela ("o tutorial tá bem ruimzinho").
- **RG-18 Tamanho efetivo da fonte** exibido (o campo mostra o máximo, o
  desenho usa o ajustado — confundiu).
- **RG-19 Região SELO no editor**: desenhar rótulo/placeholder dentro dela
  (aparece vazia) e comunicar o comportamento multifunção.

## ONDA 4 — CONTEÚDO/IA

- **RG-20 Sanitização/enriquecimento**: ordem correta é Tipo+Marca+
  **Sabor/Variante**+Peso ("Doce de Leite Firmesa **Original** 400g", nunca
  "400g Original"); **enriquecer JAMAIS descarta palavra** do original
  (perdeu "Original", "Val") — regra dura: todo token do bruto presente no
  sanitizado ou o item vira amarelo para revisão; typo do fornecedor
  (Huppers) pode ser sugerido, nunca trocado sozinho.
- **RG-21 Enriquecimento em lote** (já na Onda 1/RG-02a — registrado aqui
  como exigência de conteúdo também).
- **RG-22 Abreviações de tabloide**: glossário reverso configurável
  ("Leite Condensado"→"Leite Cond.") aplicado ao NOME DO TABLOIDE (nunca ao
  banco), para evitar quebras feias — com prévia da quebra na célula.
- **RG-23 Categorizar na criação**: produto novo já sai categorizado (jun-
  to do enriquecer, mesmo prompt) — o "tudo Outros" da auditoria foi o
  lote nunca ter rodado; manter o botão de lote para o acervo antigo.
- **RG-24 Datas inteligentes**: campanha tem dia fixo (qua/qui/sex — con-
  figurável por EVENTO); "ATÉ [data]" sugerido = próxima ocorrência do dia
  da campanha a partir de hoje; editável; validade default presumida.
- **RG-25 "Fica a Dica" por IA**: gerar o texto (receita/dica/curiosidade)
  a partir dos itens da oferta, com **limite de caracteres derivado da
  região** (área ÷ tamanho da fonte) — o Qwen local dá conta; botão
  "Gerar dica" na região TEXTO_LEGAL com texto_fixo.
- **RG-26 Busca de imagem**: paginação "mais resultados"; strip de tokens
  de marca própria (BBX) do termo; investigar qualidade/limites do ddgs e
  alternativas (Onda 6); foto original ao lado da tabela na conciliação
  (radar antigo, promovido).
- **RG-27 Foto física → packshot por IA** (img2img local transformando a
  foto do produto real em imagem estilo estúdio): **pesquisa** na Onda 6 —
  se viável no hardware dele, é diferencial enorme; senão, pós-1.0
  documentado.
- **RG-28 Multi-fotos por PRODUTO no banco** (os sabores hoje só vivem no
  item/projeto; persistir no acervo para reuso).
- **RG-29 "Criar como composto"** direto na conciliação (linha "Coração e
  Língua" já nasce composta — hoje só compõe depois, na estante).
- **RG-30 Marcas do mercado**: glossário de marcas próprias (BBX, BB) →
  `marca_propria` automático + strip da busca de imagem.

## ONDA 5 — VISUAL DO TABLOIDE + o marco

- **RG-31 Seções**: estilos de verdade (SEM borda/só título/cor por
  categoria/pill), o bug da borda atravessando célula (capturas da Mesa),
  e agrupar-sem-desenhar como modo. A borda atual: "feia, não gostei".
- **RG-32 Cartaz**: item deve PREENCHER a área da arte (margens/ajuste por
  região no layout de cartaz); aplicar upscale no fluxo (imagem saiu
  "baixíssima qualidade"); testar com o cartaz real de/por dele.
- **RG-33 Gestor de SELOS nas Configurações**: upload de arte própria
  ("Muito Barato", "Destaque"...), automáticos (+18, BB Qualidade) e
  seleção por item — a região multifunção já existe; falta o gestor e a
  colocação por item na Mesa/Almoxarifado.
- **RG-34 Validade**: selo automático "De olho na validade" quando o item
  tem validade; conceito novo de **validade da OFERTA (de/até)** separado
  da validade do item.
- **RG-35 Início/Dashboard**: redesign completo ("o original era mais
  bonito") — pastas/eventos visuais, criação de evento pelo Início, aba de
  ofertas da semana; mais denso e mais bonito.
- **RG-36 O MARCO (~40 itens)**: com as Ondas 1–5 prontas, rodar o
  tabloide categorizado de ~40 ponta a ponta (Quintou + Sexta Verde) como
  teste de regressão final — inclusive performance com acervo ≥5k
  (orçamentos do F8-D1).

## ONDA 6 — PESQUISA (lição de casa do arquiteto, com o builder)

- **RG-37 A ciência do tabloide**: pesquisa profunda (princípios de
  encarte de varejo: item-âncora, leitura em Z, blocking por categoria,
  densidade por página, psicologia de preço, padrões brasileiros) → virar
  presets e opções no app. O dono quer o app "sabendo" fazer tabloide.
- **RG-38 Benchmark de fluxo** (como ferramentas grandes operam em massa:
  editar primeiro/fotos depois, planilhas, bibliotecas de packshot) →
  refinar a dinâmica dos tempos.
- **RG-39 Alternativas de busca de imagem** (qualidade, limites, custo
  zero, offline-friendly) e viabilidade do RG-27 (img2img local).
- **RG-40 Faxina da pasta raiz** do projeto: arquivar `src/` antigo, docs
  obsoletos e saídas de teste em `_arquivo/` (nada apagado), raiz limpa.

## RG-41..46 — Apenso da pesquisa (17/07, ver `docs/PESQUISA_TABLOIDE.md`)

- **RG-41 (Onda 4)** Campo **EAN** no produto + **cascata de busca de
  imagem**: EAN→Open Food Facts (API aberta, packshot por código de
  barras)→Cosmos (se configurado)→ddgs. EAN aceito na tabela importada e
  editável no Almoxarifado.
- **RG-42 (Onda 5)** Presets de composição: "capa com heróis", guia Z
  opcional, medidor de densidade por página.
- **RG-43 (Onda 5)** Assistente de preço: sugestão opcional de terminação
  ,99/,98/,90 + par de/por riscado no TABLOIDE (com aviso PROCON).
- **RG-44 (Onda 4/5)** Preset da ordem de setores espelhando a loja
  (semente do `categorias.ordem`).
- **RG-45 (Onda 1)** Confirma o RG-03 como fluxo canônico da indústria
  ("dados primeiro, fotos em lote depois").
- **RG-46 (pós-marco)** "Estúdio IA" experimental: foto física→packshot
  (rembg+luz+sombra primeiro; img2img local condicionado à GPU).

- **RG-47 (achado na revisão da Onda 1 — CORRIGIDO na própria onda; renumerado pelo arquiteto: RG-41 já era o EAN do apenso da pesquisa):** item
  AMARELO não tinha "Ignorar" — linha-lixo do OCR que casasse 65% encurralava
  o humano ("Aceitar" ensinaria um alias ERRADO para sempre; "É novo"
  poluiria o acervo; "Cancelar" jogaria fora a conciliação inteira). O
  amarelo ganhou a mesma saída limpa do vermelho.

## Resposta do builder — ONDA 1 executada (17/07/2026)

Linha de base: **295 verdes, zero skips, exit 0**. Ao fechar: **307 verdes,
zero skips, exit 0 em DUAS rodadas** (12 testes em `test_onda1_desempenho.py`).
Método: diagnóstico paralelo COM MEDIÇÃO antes de qualquer edição; os números
estão abaixo e o script de medição é reproduzível.

### RG-01 ✓ — abertura: 2.307 ms → **510 ms** até a janela (4,5×)

- **O diagnóstico derrubou a hipótese da ordem**: os imports pesados
  (rembg/torch/IA) JÁ eram preguiçosos. Os vilões medidos: (1) a varredura
  de **3.311 fontes do sistema** com fontTools no construtor do painel
  (966 ms, no caminho crítico); (2) a estrutura do boot — TODAS as 7 telas
  + 3 detecções de grade + snapshot ANTES do `show()`.
- Curas: fontes do sistema só na **1ª abertura do combo** + **cache em
  disco** (assinatura por arquivo — aberturas seguintes em ms); **boot em
  duas fases** (`_montar_shell` = Shell+Dashboard visíveis em ~0,5 s;
  `_completar_janela` monta o resto com a janela já pintada, via
  QTimer); snapshot/migração pós-show; grade do Belo Brasil detectada
  **1× por boot** (cache JSON = cópia profunda; cada consumidor recebe
  documento próprio).
- Medido depois (2 rodadas): **janela 510/504 ms; tudo completo
  1.119/1.107 ms** (bancada quente; a frio na máquina do dono escala, mas
  a meta < 5 s ficou folgada). **Splash elaborado ficou desnecessário** — a
  dica "Preparando as demais telas…" + clique precoce protegido com toast
  cumprem o papel (decisão documentada).

### RG-02 ✓ — pipeline: a hipótese dos 26 s foi REFUTADA com medição

- **Achado de bancada duplo**: (1) a sessão do rembg JÁ era cacheada — os
  26 s são carga (1ª vez) + **inferência real do birefnet em CPU**
  (medido: 15,4 s a 1ª chamada, 8,0 s a 2ª → ~7,4 s de carga + ~8 s de
  inferência numa imagem pequena); (2) **o ambiente poetry estava QUEBRADO**
  (pin onnxruntime 1.17.0 × numpy 2.x → ImportError) — o app vivo roda no
  python do sistema (saudável, onnxruntime 1.23); o pin do pyproject foi
  corrigido para `>=1.19.2,<2` (lock não regenerado — ver "fora").
- Curas: **pré-aquecimento do modelo pós-boot** (a 1ª foto da sessão não
  paga mais os ~7 s de carga); trava anti-dupla-carga na sessão; status
  separado **"Carregando o modelo de recorte (1ª vez)…"**; **modelo
  configurável** ("Qualidade máxima" birefnet PADRÃO travado / "Equilibrado"
  / "Rápido") na tela de Configurações.
- **RG-02a**: fila de **enriquecimento em lote** dos vermelhos dispara na
  abertura da conciliação (`TrabalhadorFila`, cache POR UID — I1; o nome
  enriquecido já aparece na coluna "No banco"); ao clicar "Criar", o nome
  está pronto. Motor sondado UMA vez por fila (era 1 probe de ~3 s por
  clique). De quebra, **bug latente consertado**: LM desligado estourava
  AttributeError no Criar — agora degrada para o determinístico.
- **RG-02b**: **pré-busca dos candidatos do próximo vermelho** enquanto o
  humano decide o atual (uma em voo por vez — respeito ao rate-limit do
  ddgs); com nome+candidatos prontos, a curadoria abre NA HORA.
- **RG-02d (parcial por decisão)**: o paralelismo entregue é
  busca×decisão-humana (pré-busca) e enriquecimento×tudo (fila); paralelizar
  os DOWNLOADS internos do ddgs brigaria com as defesas de rate-limit da
  F4.1 — registrado, não implementado.

### RG-03 ✓ — "editar primeiro, fotos depois"

- Checkbox **"Buscar fotos automaticamente"** no rodapé da conciliação
  (padrão LIGADO = fluxo de sempre). Desligado: "Criar" cadastra SEM foto
  na hora, e o botão **"Criar todos sem foto"** resolve TODOS os vermelhos
  numa fila em segundo plano (resolvendo por uid conforme fica pronto).
- Na Mesa: **"Buscar fotos em lote"** (habilita quando há item sem foto)
  percorre a fila com **posição visível no título** ("Foto 3 de 12 — Nome"),
  pré-busca do próximo enquanto você escolhe, "Sem imagem" pula, fechar
  interrompe COM aviso do que restou, e **erro num item pula com aviso e
  segue** (nunca mata a fila em silêncio).

### RG-04 ✓ — OCR: cache + progresso honesto

- **Cache por sha256 do arquivo** (modelo-aware, escrita atômica, teto de
  30, leitura vazia nunca gravada, SEM caminho de máquina — I3): reimportar
  a mesma foto pula o OCR **com aviso em toast** (o status que piscava não
  bastava — achado da revisão) e botão **"Limpar cache do OCR"** nas
  Configurações (a saída para leitura parcial presa — o OCR não é
  determinístico).
- Progresso por FASE honesto no `ler_tabela` ("preparando" → "lendo — a
  tabela inteira é lida de uma vez, pode levar minutos" → "N produtos
  encontrados"): a chamada de visão é única; **progresso por linha real
  exigiria streaming SSE** — proposto como decisão do arquiteto (fallback
  obrigatório), não improvisado.
- **Tempo decorrido no overlay** (após 3 s: "· há 1min32s") para TODOS os
  trabalhos longos — rembg de 26 s incluso: o app nunca mais parece travado.

### Revisão adversarial da onda (com a queda do limite, documentada)

A revisão por frota caiu 2× no limite de sessão; **um revisor completou** e
deixou 6 achados no diário — TODOS triados por leitura do código e curados:
RG-47 (acima); assinatura do cache de fontes por-arquivo (o falso-válido de
contagem+mtime morreu) + fonte desinstalada devolve None em vez de
FileNotFoundError engolido; fila de fotos resiliente a erro; cache de OCR
com aviso persistente + saída de releitura; guarda de geração no prefetch
(fila cancelada não contamina a nova); blindagem do `estilos` raso no cache
da grade (bomba latente desarmada com JSON como fronteira). As outras duas
lentes (threads-Qt e contratos) ficaram sem revisor independente — a
reauditoria do arquiteto cobre exatamente esses olhos.

**O que ficou de fora (Onda 1):**

- Streaming SSE para progresso por linha REAL do OCR — upgrade opcional
  especificado, aguardando decisão do arquiteto.
- `poetry.lock` não regenerado (o pin foi corrigido; rodar
  `poetry update onnxruntime` num momento calmo — o app vivo não usa esse
  ambiente).
- Pré-aquecimento carrega ~1–2 GB de RAM mesmo se nenhuma foto for tratada
  na sessão — troca consciente (1ª foto sem espera de 7 s).
- Pastas temporárias da busca de candidatos não são limpas (pré-existente,
  multiplicado pela pré-busca — anotado).
- O gancho GLOBAL de shutdown (workers em voo ao fechar o APP) continua
  sendo pauta da Onda 2 (RG-05) — o porta-vidas `_ORFAOS` do encerrar já
  reduz a janela.

**Medições reproduzíveis**: script de boot em 2 fases (scratchpad;
resultados 510/504 ms janela, 1.119/1.107 ms completo) e medição do rembg
(15,4 s/8,0 s). **PARADO no ponto de reauditoria — Onda 2 só com o selo.**

## SELO do arquiteto — ONDA 1 (17/07/2026): APROVADA

Reauditoria na fonte: varredura de fontes adiada via gancho no `showPopup`
(paga só na primeira abertura do combo — elegante); pré-aquecimento do
recorte em worker pós-boot; cache de OCR com aviso visível + "Limpar" nas
Configurações; "Criar todos sem foto" + fila de fotos em lote com posição;
amarelo com saída limpa (RG-47). **510 ms medidos aceitos; 307 verdes ×2,
exit 0.** As lentes órfãs da revisão que caiu (threads/contratos) foram
cobertas pela lupa do arquiteto por amostragem — com UMA exigência herdada
para a Onda 2: o pré-aquecimento criou mais um worker de boot, então o
**gancho GLOBAL de shutdown vira item obrigatório da Onda 2 (RG-05b)**,
não mais radar. Colisão de numeração corrigida no dossiê (o achado da
revisão virou **RG-47**; RG-41 segue sendo o EAN) — o builder atualiza as
referências em comentários de código/teste na abertura da Onda 2. Lição
operacional registrada: **frotas de subagentes queimaram contexto e caíram
sem entregar — o trabalho é inline e a segunda lente é a reauditoria do
arquiteto.** Onda 2 AUTORIZADA.

## Resposta do builder — ONDA 2 executada (18/07/2026)

Linha de base: **307 verdes, zero skips, exit 0** (os 307 da Onda 1).
Ao fechar: **331 verdes, zero skips, exit 0 em DUAS rodadas** (24 testes
novos em `test_onda2_estabilidade.py`) + **adversariais re-rodados
nominalmente** (`test_adversarial_vinculo` + `test_adversarial_portabilidade`:
14 verdes — a onda tocou slot/item/mapa). Pendência herdada cumprida:
RG-41→RG-47 nos comentários (`conciliacao_dialog.py`, teste renomeado
`test_rg47_amarelo_tem_saida_limpa`).

### RG-05 ✓ — a caça, com a prova visual reconstituída

Extraí as 4 gravações do Gravador de Passos (1.057 frames + timestamps;
extrator reproduzível no scratchpad). **O travamento 2 (Mesa_350) está
filmado de ponta a ponta na gravação da Mesa**: frames 250→262 — o dono
gira a roda com o cursor parado (rajada de ~6 eventos/s) e a página
ENCOLHE tick a tick; frames **241→361 = DOIS MINUTOS presos** (18:21→18:23)
com a página-pontinho num canvas cinza e cursor de espera; frame 362+ ele
escapa e segue trabalhando. O mesmo colapso de zoom aparece no editor do
Ateliê (gravação "Fábrica e Outros" 174-189) e na gravação do Ateliê
(frames 3-8) — **o dono lutou contra o zoom a sessão inteira, em 3
superfícies**.

Causa raiz TRIPLA, curada na raiz:

- **Zoom sem limite** (`wheelEvent` multiplicava 1/1.15 sem piso): 28
  ticks → 2%; a intenção dele era ROLAR (RG-11). Cura: `zoom()` com clamp
  **[5%, 800%]** (`ESCALA_MIN/MAX`), roda passa por ele.
- **Régua O(1/zoom)**: marca a cada 10 mm do viewport visível — em 2%,
  ~1.500 marcas × 2 réguas POR REPAINT (os "números borrados" das capturas;
  o peso do canvas cinza). Cura: **passo adaptativo** (`passo_da_regua`,
  10→50000 mm conforme px/mm, função pura testada) + teto duro de 600.
- **"Zoom 2%" do rodapé era MENTIRA estrutural**: o número vinha de um
  **editor órfão** criado no boot (nunca adicionado a tela nenhuma) cujo
  `fitInView` rodava com viewport de ~30 px. No frame 444 o canvas está a
  ~85% e o rodapé diz 2%. Cura: o editor órfão MORREU no caminho vivo
  (`montar_janela` compat mantém p/ screenshots); `Shell.registrar_zoom`
  mostra o zoom **da tela ativa** (Mesa/editor do Ateliê; vazio em tela
  sem canvas); `ajustar()` com viewport <80 px vira **fit pendente**
  consumido no primeiro show/resize real.
- Saídas do estado-armadilha: **Ctrl+0 enquadra** em qualquer canvas; o
  fit pendente elimina o estado de nascença.
- **Vigia de travamento** (`app/core/vigia.py` + pasta `logs/` no
  SystemRoot): batimento por QTimer de 1 s; thread daemon grava traceback
  de TODAS as threads em `logs/travamentos.log` quando a UI fica presa
  ≥5 s (1 dump por episódio) — o próximo congelamento na máquina dele
  vira prova técnica.

**Travamento 1 (após exclusões no Almoxarifado): sem captura direta nas 4
gravações** (varri as folhas de contato das 1.057) — a fonte é o áudio.
Endureci os caminhos suspeitos no código: **exclusão saiu do thread da UI**
(worker + overlay "Excluindo N…"); **estado podre curado** — `_rebuscar`
solta `_linha_atual`/painel ANTES do reset (worker de imagem/edição nunca
mais aterrissa no produto ERRADO da lista nova), `atualizar_linha` com
guarda de range (IndexError em slot de signal morreu), imagem que chega
após a lista mudar avisa por toast (o banco JÁ tem a foto). Se recorrer,
o vigia grava onde.

### RG-05b ✓ — gancho GLOBAL de shutdown

`GerenciadorTrabalhos` nasce **registrado no módulo** (weakref);
`encerrar_todos()` percorre todos os gerenciadores vivos do processo
(telas, diálogos, aquecedor do boot), **cancela filas em andamento** e
aplica o `encerrar()` de sempre (teto + `_ORFAOS`). O **`closeEvent` do
Shell** chama — nenhum worker vivo ao fechar, de qualquer origem, testado
fechando a janela com worker em voo.

### RG-06 ✓ — teclado

- **Delete E Backspace excluem no `CanvasView`** — o menu de contexto
  sempre PROMETEU "Excluir · Del" (inclusive na Mesa) e a tecla não
  existia; agora cumpre onde o canvas viver. Seleção múltipla sai como
  **UM gesto** (`excluir_regioes`, 1 estado de undo — testado: Del em 2
  regiões, 1 undo restaura as duas). Editor ganhou "Backspace" e o
  `_excluir_selecao` virou multi.
- **Ctrl+V na curadoria** (`QKeySequence.Paste` no diálogo): cola a
  imagem; num campo de texto focado continua colando texto (precedência
  nativa do campo); clipboard sem imagem avisa por toast (I2).
- **Desfazer/refazer NA MESA**: botões ↶ ↷ na barra + Ctrl+Z/Ctrl+Y/
  Ctrl+Shift+Z — o canvas já versionava {layout, mapa, overrides} (D5);
  faltava o gesto. Sem nada a desfazer, avisa (nunca silencioso).

### RG-07 ✓ — gestão da estante

Botão direito → **"Excluir da estante"** (rotulado com o atalho) + **Del
com o foco na lista** (WidgetShortcut — não rouba o Del do canvas);
**"Limpar estante"** no cabeçalho do painel com confirmação e aviso de que
o banco não é tocado; **contagem viva** no título ("Itens da oferta (12)"
— `Painel.set_titulo` + ação de cabeçalho novos). Excluir tira a entrada
do mapa (a célula esvazia à vista) preservando o histórico do canvas
(`atualizar_dados`, não `carregar`).

### RG-08 ✓ — dessincronia entre telas

- **Ateliê→Mesa/Fábrica**: `showEvent` compara a **assinatura JSON** do
  layout carregado com o banco e re-sincroniza SE o Ateliê editou —
  estante, mapa (por uid — I1) e overrides sobrevivem; toast nominal.
  **Projeto congelado NUNCA re-sincroniza** (`_congelado` — decisão
  travada testada: banco editado + congelado aberto = layout intacto).
- **A raiz do "salvei e não persistiu" (18:52+): achada e curada** — o
  semeio de boot era **upsert** e re-gravava os DOIS layouts padrão a
  CADA abertura, destruindo edição do dono neles no boot seguinte
  (perda silenciosa pré-existente). Agora o semeio **só cria os
  ausentes** (testado: edição no padrão sobrevive ao 2º semeio), e a
  Mesa do boot carrega o "Tabloide Belo Brasil" **do banco** (uids
  estáveis entre boots; a grade re-detectada, que mudava de uid por
  boot, virou fallback sem arte).
- **Almoxarifado auto-refresh**: `showEvent` → rebusca (produto criado
  na Mesa aparece ao trocar de tela; testado).
- **Indicador salvo/não-salvo POR TELA** (`set_salvo_de` + repinta no
  `ir_para`): o estado da Mesa não vaza para o Cofre; tela sem documento
  fica SEM estado (morreu o "Salvo" verde de fábrica do boot — a
  confusão do dono era o indicador único global).

### RG-09 ✓ / RG-10 ✓

- "Editar" do menu do Almoxarifado ganhou função real: seleciona E foca o
  campo Nome pronto para digitar (não havia botão morto na barra — era a
  ação do menu de contexto que só repetia o clique).
- **Grades de miniatura estáticas** (`Movement.Static`) em **5 pontos**:
  Ateliê (o RG nominal), curadoria, histórico de imagens, fotos do item
  (o drag ali MENTIA a ordem — visual mudava, ordem real não) e
  prateleiras do Dashboard. Teste cobre os 4 instanciáveis.

### Achados de bancada (documentados, não escondidos)

1. **Semeio destrutivo** (acima) — o mais grave da onda; pré-existente.
2. **Editor órfão do boot** — pagava uma composição Pillow por abertura e
   alimentava o rodapé com 2% eterno; removido do caminho vivo.
3. Meu primeiro edit no `Painel` (ação de cabeçalho) **engoliu a montagem
   do layout** — `EstadoVazio`/lista morriam no GC ("Internal C++ object
   already deleted", 5 testes vermelhos). Corrigido no ato; os testes da
   onda o pegaram (a suíte nunca ficou verde com ele).
4. `_editar_item` da estante usa `_aplicar_mapa` → **reseta o undo do
   canvas ao editar nome/preço** (pré-existente; anotado, não tocado — o
   excluir novo já usa o caminho que preserva).

### O que ficou de fora (Onda 2)

- **Travamento 1 sem reprodução filmada** — curas nos suspeitos + vigia
  armado; se recorrer, `logs/travamentos.log` conta onde estava preso.
- O vigia **não pega trava em código nativo que segura o GIL** (paint
  pesado do Qt solta; laço Python pesado é pego — os casos reais).
- **Excluir/limpar estante não entram no undo do canvas** (paridade com
  compor/importar: gesto de DADOS; o inverso explícito é reimportar).
- **Re-sincronizar do Ateliê zera o undo do canvas da Mesa** (o
  documento-base trocou — honesto; mapa/estante/overrides ficam).
- Roda do mouse continua = zoom (**RG-11/Onda 3** muda para Alt+roda; aqui
  entrou só o clamp — não antecipei a onda do dossiê).
- Indicador de **dimensões** do rodapé segue global (só zoom e salvo
  viraram por-tela); a Fábrica não tem canvas (preview QLabel) — rodapé
  de zoom fica vazio nela até o RG-32.
- `test_onda2_estabilidade` importa `_grade_4` de `test_adversarial_vinculo`
  (padrão já usado por `test_categorizacao`/`test_item_composto`).

**PARADO no ponto de reauditoria — Onda 3 só com o selo do arquiteto.**

## SELO do arquiteto — ONDA 2 (18/07/2026): APROVADA

A lupa pagou a dívida das lentes órfãs da Onda 1 (threads/ciclo de vida) e
o veredicto é forte: `_GERENCIADORES` global por weakref com
`encerrar_todos()` cancelando filas ANTES de esperar + porta-vidas
`_ORFAOS` + gancho no `closeEvent` do Shell (RG-05b exemplar); o
`VigiaTravamento` é daemon com batimento por QTimer e **limitação
documentada com honestidade** (congelamento em código nativo sem GIL não é
coberto — está escrito no módulo). A perícia do RG-05 com prova filmada
(roda→zoom 2% sem clamp + régua com ~3.000 marcas por repaint + rodapé
mentindo por causa de um editor órfão invisível de boot) é o melhor
trabalho forense da jornada. E o achado do SEMEIO-UPSERT que re-gravava os
layouts padrão a cada boot explica na raiz o "salvei e não persistiu" das
18:52 do dono — caçado, curado e testado. Exclusão da estante limpa o mapa
por uid com aviso. **331 verdes ×2, exit 0, adversariais re-rodados
nominalmente. ONDA 2 SELADA. Onda 3 (UX do editor) AUTORIZADA.**

## Resposta do builder — ONDA 3 executada (18/07/2026)

Linha de base: **331 verdes, zero skips, exit 0** (conferida na retomada).
Ao fechar: **351 verdes, zero skips, exit 0 em DUAS rodadas** (19 testes em
`test_onda3_editor.py` + 1 novo no adversarial do vínculo) + **adversariais
re-rodados nominalmente: 15 verdes** (RG-12 e RG-15 tocam slot/região).
Trabalho inline, modelo antes de UI — o RG-12 abriu a onda como mandado.

### RG-12 ✓ — rotação de região (a única mudança de modelo)

- **Modelo**: `Regiao.rotacao_graus` (default 0.0; horário; serializa;
  layout antigo abre com 0 — migração implícita testada). O **rect não
  muda**: o conteúdo gira em torno do CENTRO — âncora e vínculo estáveis
  (I1), e rotação 0 nem entra no caminho novo (o desenho reto fica
  byte-idêntico ao de sempre).
- **Composição**: `_desenhar_regiao_rotacionada` desenha o conteúdo reto
  num palco RGBA do tamanho da diagonal, gira (BICUBIC) e cola de volta
  com o mesmo centro — vale para texto, imagem e o texto_fixo de célula
  vazia (o "Fica a Dica" deitado também funciona).
- **Propagação**: `rotacao_graus` entrou em `ATRIBUTOS_ESTILO` — a data
  deitada da MESTRA replica nas células; override local vence (testado).
- **Editor**: campo "Rotação" no painel (passo 15°, tooltip); o item de
  seleção gira junto (`setTransformOriginPoint`+`setRotation` — hover e
  clique casam com o desenho; a propagação gira os contornos das irmãs na
  hora). **Região girada não redimensiona pelas alças** (a matemática do
  arrasto assume item reto — decisão documentada; mover funciona, tamanho
  pelo painel).
- **Adversarial (exigência do arquiteto)**:
  `test_adversarial_rotacao_nao_desloca_conteudo_de_celula` — girar o NOME
  de UMA célula deixa os 3 outros quadrantes **pixel-idênticos**, o mapa
  intacto e o trio conferido por conteúdo nas 4 células.

### RG-11 ✓ — navegação (paridade Illustrator)

Roda = rolagem vertical · Ctrl+roda = horizontal · **Alt+roda = zoom**
(com o clamp da Onda 2; detalhe Qt: com Alt o delta chega no eixo X —
tratado). Barras de rolagem **sempre visíveis**. Testado com QWheelEvent
nos três modos: rolagem não mexe na escala, Alt mexe.

### RG-13 ✓ — hifenização de aproveitamento + justificado

- `_quebrar_linhas` ganhou o passo Illustrator: antes de empurrar a
  palavra inteira para a próxima linha, tenta **encher a linha atual com
  prefixo hifenizado** (pyphen pt-BR já era dependência da quebra de
  emergência; guardas: ≥2 letras de cada lado, só `isalpha()` — "500g" e
  "R$" nunca ganham hífen, testado). Linhas mais cheias = o ajuste
  só-reduz para em tamanho MAIOR.
- Justificado: com as linhas cheias, os gaps encolhem e a borda direita
  fecha — provado por pixel (a tinta alcança a borda da região ±2 mm).
- A suíte inteira passou SEM regressão (os testes de composição comparam
  composição-contra-composição — imunes por construção).

### RG-14 ✓ — pesos da família ("quero Black")

- `fontes.py`: `familia_estilo`/`variantes_bundled`/`variantes_sistema`
  pela name table (fontTools); o cache de fontes do RG-01 agora guarda
  família+estilo por rótulo (cache antigo é invalidado sozinho pelo
  formato). Combo **"Peso"** no painel: as irmãs da família atual por
  ESTILO; as do sistema entram na 1ª abertura do combo (a MESMA técnica
  anti-boot-lento do RG-01); escolher = trocar o arquivo (`reg.fonte`) —
  o compositor nem fica sabendo. Testado com as Roboto reais do repo
  (e o acervo já tem Quicksand em 4 pesos — o caso do dono existe).

### RG-15 ✓ — célula como GRUPO ("clico e dá errado")

- **1º clique** numa região de célula fria seleciona o TRIO inteiro
  (imagem+nome+preço); **2º clique sem arrasto entra na região**
  (o colapso é no release — clique+arrasto MOVE a célula inteira, que o
  Qt já faz com a seleção múltipla); Ctrl/Shift preservam o gesto multi
  de sempre; rubber-band intocado.
- **Hover acende o trio** (contorno leve nas irmãs — some ao sair).
- `canvas.selecionada()` agora exige EXATAMENTE uma (com o grupo ativo o
  painel não mostra região arbitrária — mostra o estado neutro).
- 5 testes (grupo, colapso, arrasto preserva, Ctrl, hover) + adversarial
  re-rodado (a seleção não toca o vínculo).

### RG-16..19 ✓ — painéis, onboarding, tamanho efetivo, SELO

- **RG-16**: a linha do estilo foi REARRANJADA (combo em linha própria +
  botões embaixo — era a captura dos dropdowns cortados "(ne/Novo../
  tualiza"); "Nome" virou **"Rótulo da camada"**; tooltip no combo de
  estilo ("serve pra quê?").
- **RG-17**: tooltip em TODOS os campos do painel (fonte, tamanho,
  alinhamento, subtipo/papel do preço, ajuste, texto fixo…); **legenda
  dos pontinhos** no rodapé do painel (âmbar = ajuste próprio; violeta =
  conteúdo trocado; contorno âmbar = mestra); **microtutorial de 1º uso
  por tela** (`design/tutorial.py`): cartão com "Entendi" na primeira
  visita a Mesa/Ateliê/Almoxarifado/Fábrica, persistido na Config
  (`tutorial.vistos`), ligado num ponto único (`Shell.ir_para`), nunca
  em janela invisível, e falha de banco jamais bloqueia a navegação.
- **RG-18**: rótulo sob o campo Tamanho — "desenhado a N pt (reduziu
  para caber)" quando o efetivo difere do teto (`canvas.
  tamanho_efetivo_pt`, o MESMO ajustador da composição; atualiza a cada
  edição). Imagem/selo/preço devolvem None (não se aplica).
- **RG-19**: a região SELO desenha placeholder explicativo no CANVAS do
  editor ("+18 e Qualidade entram aqui automaticamente") — só no editor;
  a exportação não muda um byte (provado por render da cena).

### Achados de bancada

1. Meu teste do placeholder media tinta pelo canal AZUL — contornos e
   texto claros não contavam (0 pixels nos dois lados). Corrigido para
   luminância; o teste agora discrimina de verdade.
2. `selecionada()` devolvia a PRIMEIRA de N selecionadas — o painel podia
   mostrar (e EDITAR) uma região arbitrária da seleção múltipla. Com o
   RG-15 isso viraria bug visível; agora exige exatamente 1.

### O que ficou de fora (Onda 3)

- **Alças de rotação com o mouse** (girar arrastando, como o Illustrator)
  — a rotação entra pelo painel (spin de graus, passo 15°); handle
  circular fica para polimento futuro se o dono sentir falta.
- **Redimensionar região girada pelas alças** — bloqueado com decisão
  documentada (mover funciona; tamanho pelo painel).
- Rotação de PREÇO no subtipo SEPARADO compõe girada normalmente, mas o
  `tamanho_efetivo_pt` (RG-18) não cobre preço (fitting próprio de
  inteiro+centavos) — o rótulo simplesmente não aparece nele.
- Hifenização usa o dicionário pt-BR do pyphen — termo de marca fora do
  dicionário não ganha hífen de aproveitamento (só o de emergência, que
  já existia).
- Microtutorial cobre as 4 telas de trabalho (Início/Cofre/Config ficam
  sem — são autoexplicativas; textos são facilmente adicionáveis no
  dicionário `TEXTOS`).
- O justificado segue palavra-a-palavra (sem micro-tipografia de
  espaçamento entre letras) — paridade suficiente com o gesto do
  Illustrator para tabloide.

**PARADO no ponto de reauditoria — Onda 4 só com o selo do arquiteto.**

## SELO do arquiteto — ONDA 3 (18/07/2026): APROVADA

Lupa nos dois alvos declarados, ambos exemplares: **rotação** gira palco
isolado em torno do centro sem tocar o rect (âncora/vínculo intactos; cópia
interna zera a própria rotação — sem recursão; resize de região girada
desabilitado por decisão documentada; migração de layout antigo testada;
propagação da mestra com override local; adversarial dos quadrantes
byte-a-byte como exigido). **Clique-grupo** com colapso só no
release-sem-arrasto, hover do trio, e a correção do bug latente do
`selecionada()` (nunca mais região arbitrária ao painel em multi-seleção).
Hifenização via pyphen com "500g" imune, pesos por name table com a técnica
anti-boot, microtutorial persistido. **351 verdes ×2, exit 0, adversariais
15/15. ONDA 3 SELADA. Onda 4 (Conteúdo/IA) AUTORIZADA** — inclui o RG-41
(EAN→Open Food Facts) e o RG-44 (preset de setores) da pesquisa.

## Resposta do builder — ONDA 4 executada (18/07/2026)

Linha de base: **351 verdes, zero skips, exit 0**. Ao fechar: **383 verdes,
zero skips, exit 0 em DUAS rodadas** (32 testes em `test_onda4_conteudo.py`)
+ **adversariais nominais 15/15** (vínculo + portabilidade — o RG-28 tocou
o terreno produto↔pasta). PESQUISA_TABLOIDE lida no ritual (§5 fundou a
cascata do RG-41). Aberta pelo RG-20, como mandado.

### RG-20 ✓ — a REGRA DURA (a fundação da onda)

- **`tokens_perdidos(bruto, sanitizado)`** headless: todo token
  significativo do original precisa sobreviver no sanitizado (comparação
  sem caixa/acento e por SUBSTRING — typo corrigido "OLE O"→"Óleo" e
  reordenação NÃO acusam; **"Val" e "Original" sumindo — os casos da
  auditoria — acusam**; "Huppers"→"Ruppers" acusa: troca de marca é
  SUGERIDA, nunca aplicada sozinha). Stopwords/fragmentos ≤2 fora (sem
  alarme à toa). Multi-produto compara contra nome+componentes+variantes
  (repartir Camil e Rei não é perda).
- Corre SEMPRE sobre o resultado da IA (`ProdutoEnriquecido.tokens_perdidos`)
  + prompt reforçado (ordem com o exemplo real do dossiê e "NUNCA remova
  palavras"). **Na curadoria**: campo do nome acende âmbar com aviso
  NOMINAL ("A IA descartou: 'Val' — confira antes de criar"). **No lote do
  acervo**: nome com perda NÃO é aplicado (contado como "revisar" no
  resumo/toast — o banco jamais é mutilado em silêncio).
- Fakes que EXERCITAM (a lição): o dublê devolve nome COM perda de verdade
  e o teste confere a acusação; outro preserva e confere o silêncio.

### RG-22/23/24/25 ✓ — conteúdo

- **RG-22**: `abreviar_para_tabloide` aplicado no ponto único da composição
  da Mesa (`_dados_de`) — banco e estante intactos POR CONSTRUÇÃO; frase
  longa tem precedência; config `tabloide.abreviacoes` com campo próprio
  ("Leite Condensado = Leite Cond."); a prévia da quebra é o próprio
  canvas WYSIWYG (aplicou → viu).
- **RG-23**: `finalizar_criacao(categoria=…)` — o produto novo nasce
  categorizado com a categoria do MESMO prompt do enriquecer
  (`categoria_origem="ia"`; o humano segue soberano — F8.1); o lote do
  acervo antigo continua.
- **RG-24**: `dia_do_evento`/`proxima_ocorrencia`/`sugerir_validade`
  headless + config `eventos.dias` ("Quintou = qui"); ao salvar projeto de
  evento com dia fixo SEM validade, a Mesa sugere "ATÉ dd/mm" com toast
  (editável; sem evento configurado, sem palpite inventado).
- **RG-25**: `limite_caracteres(região)` (heurística documentada: área ÷
  fonte, piso 40/teto 600) + `gerar_dica(nomes, limite, motor)` que corta
  no teto SEMPRE (a região é lei); botão **"Gerar dica (IA)"** no painel
  do TEXTO_LEGAL, rodando em worker (UI nunca congela), com degradação
  avisada sem motor/sem itens.

### RG-26/30 ✓ — busca de imagem

Botão **"Mais resultados"** na curadoria (mesma busca, leva maior — 6→12→18;
busca nova re-começa do 6); glossário **`marcas.proprias`** (default BBX/BB,
campo na Config): produto com a sigla ganha `marca_propria` AUTOMÁTICO na
criação, e a sigla **sai do termo de busca** nos dois caminhos (fígado acha
fígado, não a sigla) — termo só-sigla nunca vira busca vazia.

### RG-41 ✓ — EAN + cascata (a descoberta da pesquisa)

- Coluna `ean` (migração F8.1-style testada com banco envelhecido);
  aceito na tabela (`descricao | preco | ean` E código colado no início da
  descrição — `parse_tabela_ean`; os 7 consumidores antigos seguem com o
  `parse_tabela` de 2-tuplas, compat testada); campo **"Cód. barras"** no
  Almoxarifado; `ItemMesa.ean` flui da tabela/banco (projetos antigos
  abrem — default None).
- **`app/images/off.py`**: Open Food Facts por EAN (API sem chave, UA
  próprio, timeout 8 s) — QUALQUER falha devolve None e a cascata segue
  avisando (I2), testado sem rede por monkeypatch.
- **Cascata em `buscar_candidatos_para`**: com EAN, o packshot oficial vem
  PRIMEIRO; "código não achado — buscando na web…" quando o OFF falha; o
  ddgs completa. Ligada nos 5 fluxos (criar da conciliação, pré-busca
  RG-02b, fila de fotos da Mesa, prefetch, trocar imagem do Almoxarifado).

### RG-28 ✓ — multi-fotos no ACERVO (o terreno sagrado)

- Coluna `imagens_json`: lista ordenada de caminhos **RELATIVOS À PASTA do
  produto** ("atual.png", "extras/…") — escolha deliberada: o remap de id
  da portabilidade renomeia a PASTA e a lista continua válida (I3/I1).
- Fechou o ciclo: o diálogo de fotos PERSISTE no acervo quando o item tem
  produto (`salvar_imagens_produto` — foto fora da biblioteca fica só no
  item, com aviso); a conciliação e o "Do banco" RECONSTITUEM
  (`imagens_do_produto` — foto sumida fica na lista e o pré-voo acusa,
  nunca some em silêncio); <2 fotos volta a foto única.
- **O teste de roundtrip pegou um bug REAL**: a mesclagem da portabilidade
  montava o produto novo com lista EXPLÍCITA de campos — `ean` e
  `imagens_json` ficavam para trás. Corrigido nos DOIS ramos (produto novo
  e USAR_PACOTE); o roundtrip com **ids deslocados** agora prova as 3
  fotos na máquina B **byte a byte** após o remap.

### RG-29 ✓ / RG-44 ✓

- **RG-29**: `criar_como_composto` — linha com DUAS marcas
  (`proposta.componentes` da IA) nasce composta NA CONCILIAÇÃO: cada
  componente vira produto PRÓPRIO no banco (nunca nome remendado), o item
  da estante é o composto de sempre (F7.2: separável, preço único, 1 slot
  → 1 uid); ligado nos dois fluxos (com curadoria — foto vai ao 1º
  componente — e "criar todos sem foto"); testado até o separar.
- **RG-44**: `ORDEM_SETORES_LOJA` (pesquisa §1) + botão **"Preset da
  loja"** ao lado do campo `categorias.ordem` — semente editável.

### Achados de bancada

1. **A mesclagem da portabilidade perdia colunas novas** (acima) — o
   roundtrip adversarial do RG-28 o pegou na primeira rodada.
2. **Janela real no shutdown global (RG-05b)**: um flake de bancada
   (2ª suíte quente) revelou que `QThread.wait()` devolve True para thread
   que AINDA NÃO INICIOU — sob carga, o `encerrar()` "encerrava" um worker
   que nasceria DEPOIS do fechamento (órfão de verdade). Curado em
   PRODUÇÃO (`workers.py`: espera o início real antes do wait, dentro do
   mesmo teto) e o teste ganhou poll de largada. As duas rodadas finais
   saíram limpas.

### O que ficou de fora (Onda 4)

- **Cosmos (Bluesoft)** como 2º degrau da cascata — a pesquisa o
  condiciona a "se configurado"; fica documentado para quando o dono
  quiser criar a conta (o desenho da cascata já comporta).
- OCR de foto **não extrai EAN** (a visão lê descrição+preço; EAN só por
  tabela/Almoxarifado por ora).
- A regra dura usa tokens por SUBSTRING — typo que é subpalavra do
  corrigido ("Frimesa"→"Firmesa" tem edição interna) acusa como perda
  (comportamento DESEJADO: revisão), mas o inverso raro (corrigido
  contido no typo) passa sem acusar.
- "Fica a Dica" gera por REGIÃO com os itens da página atual TODA (não por
  vizinhança de célula); 1 clique = 1 dica (sem histórico de versões).
- Multi-fotos do acervo alimentam a Mesa; a **Fábrica segue foto única**
  (cartaz é 1 produto/página — decisão da F7.1 mantida).
- Abreviações não aplicam no CARTAZ (a Fábrica compõe por outro caminho;
  o dossiê pediu "nome do tabloide" — anotado para a Onda 5 se o dono
  sentir falta).
- `sugerir_validade` usa "ATÉ dd/mm" (sem ano) — o formato das artes
  reais; validade de OFERTA de/até como conceito próprio é RG-34 (Onda 5).

**PARADO no ponto de reauditoria — Onda 5 só com o selo do arquiteto.**

## SELO do arquiteto — ONDA 4 (18/07/2026): APROVADA

Lupa nos três alvos declarados: **RG-20** com a nuance exata (substring sem
caixa/acento — "OLE O→Óleo" passa, "Huppers→Ruppers" ACUSA; perda de token
= âmbar nominal; lote não aplica nome com perda); **RG-28** com
`imagens_json` relativo à pasta do produto (o remap renomeia a pasta, a
lista sobrevive) e o bug da lista-explícita-de-campos da portabilidade
corrigido NOS DOIS RAMOS — pego pelo roundtrip adversarial, que é
exatamente o seu papel; **RG-41** com cascata degradando com aviso
("Código não achado — buscando na web…") e sem rede seguindo com o que
houver. O bônus da corrida do `QThread.wait()` em thread não-iniciada
(shutdown global) é achado de bancada de primeira linha — janela real,
cura em produção. **383 verdes ×2, exit 0, adversariais 15/15. ONDA 4
SELADA. ONDA 5 AUTORIZADA — a última: visual + O MARCO.**

## Resposta do builder — ONDA 5 executada (18/07/2026) — a última

Linha de base: **383 verdes, zero skips, exit 0**. Ao fechar: **402 verdes,
zero skips, exit 0 em DUAS rodadas** (19 testes em `test_onda5_visual.py`)
+ **adversariais nominais 15/15** (seções e selos tocam composição).
Aberta pelo RG-31 e fechada pelo MARCO, como mandado.

### RG-31 ✓ — seções com estilos + o bug da borda CAÇADO

- **A prova filmada**: frame 398 da gravação da Mesa — agrupar+seções
  ligados no Quintou real e o contorno saindo errado. Três causas no
  código: agrupamento de "linha" por topo±2mm (frágil com bboxes de
  alturas diferentes), margem fixa de 1,6mm invadindo a folga vizinha, e
  o TÍTULO desenhado a cavalo da borda (metade sobre a célula de cima).
- Curas: linha por **sobreposição de intervalos verticais**; margem 1,0mm;
  **etiqueta DENTRO do bloco**. E os ESTILOS de verdade
  (`secoes.estilo`): **CONTORNO** (curado) · **SO_TITULO** · **PILL**
  (fundo translúcido em camada RGBA) · **SEM_DESENHO** (o "agrupar sem
  desenhar" do dono) + **cor por categoria** (paleta estável por crc32 —
  o hash do Python é salgado por sessão e mudaria a cada abertura).
  Provado por conteúdo: SEM_DESENHO é byte-idêntico ao desligado; nenhum
  pixel de seção acima do bloco (a etiqueta não invade mais).

### RG-32 ✓ / RG-33 ✓ / RG-34 ✓

- **Cartaz**: `upscale_para_cartaz` NO FLUXO do export (Real-ESRGAN da
  F4.3 com o modelo em `modelos/`; sem ele, Lanczos COM aviso — I2),
  cache por conteúdo (o mesmo produto não paga o modelo 2×), original
  intacta; o alvo é a REGIÃO de imagem do layout em px; placeholder do
  cartaz com a foto PREENCHENDO (84×58mm — era 56×56 tímido).
- **Selos**: gestor nas Configurações (upload PNG normalizado para
  `<raiz>/selos/`, registro na Config com arquivo RELATIVO — I3),
  **seleção POR ITEM** na estante da Mesa (checkboxes; congela com o
  projeto — ItemMesa serializa), +18/Qualidade automáticos intactos.
  **LEI DA CASA (4ª aplicação) por construção**: selo entra no passe
  final por âncora — com TESTE provando ocupável e pré-voo imunes.
- **Validade**: badge âmbar **"De olho na validade"** automático quando o
  item tem validade; **validade da OFERTA (de/até)** como conceito
  próprio (`montar_validade_oferta` — "OFERTA VÁLIDA DE 17/07 ATÉ
  24/07"; só-fim mantém o "ATÉ dd/mm" das artes), editável pelo clique
  no rótulo da Mesa, alimentando o TEXTO_LEGAL sem duplicar o prefixo
  legado.

### RG-35 ✓ / RG-42 ✓ / RG-43 ✓

- **Início**: prateleira **"★ Ofertas da semana"** (≤7 dias) no topo;
  **"Novo evento"** cria a prateleira pelo Início (Config
  `eventos.extras` — aparece vazia, pronta); cabeçalho com **faixa de
  cor estável por evento** + contagem + o dia da campanha do RG-24
  ("· toda sexta").
- **Presets**: **"Capa com heróis"** (checkbox na Mesa — os mais baratos
  abrem a página 1; sem preço nunca vira herói); **guia Z** no editor
  (overlay no canvas via paleta de comandos — provado que NÃO muda um
  byte do export); **medidor de densidade** no auto-preencher (página
  >90% cheia avisa "um respiro valoriza as ofertas").
- **Preço**: `sugerir_terminacao` (10,00→9,99 · 5,30→5,29 · 5,07→4,99;
  já-charm → silêncio) como DICA no editar da estante, com o aviso
  PROCON no toast — nunca aplica sozinha. O de/por riscado JÁ funciona
  no tabloide por construção (região PREÇO papel DE + riscado no layout;
  `preco_de` flui da conciliação; pré-voo PROCON de sempre).

### RG-36 ✓ — O MARCO (selfcheck_marco, reproduzível)

`python -m app.scripts.selfcheck_marco` → `saida_marco/` com RELATORIO.txt:

- Acervo real clonado (o vivo só é LIDO) + **5.000 sintéticos = 5.007**.
- **ABRIR com 5.007: 0,04s** (teto 5s) · **CONCILIAR 40 sobre 5.007:
  126,3s** (teto 180s; embeddings reais — IA local LIGADA, registrado)
  · **EXPORTAR PNG×3+PDF: 0,4s** (teto 30s). Todos DENTRO.
- **Quintou frente+verso+extra**: 40 células agrupadas em blocos
  contíguos, seções, pré-voo nominal (40 sem foto — bancada), PNG 1:1
  (1080×1300) + PDF 3 páginas, congelado e reaberto idêntico.
- **Sexta Verde**: heróis + PILL/cor por categoria + "OFERTA VÁLIDA DE
  18/07 ATÉ 24/07" + selo do gestor — congelada. Artefatos inspecionados
  por mim; a medição independente é do arquiteto.
- **Dois achados honestos da bancada, registrados no relatório**:
  (a) esta máquina não tem o acervo dos 42 do Quintou (7 produtos reais)
  — os 🔴 são CRIADOS no clone pelo fluxo RG-03, com exigência dura de
  ≥30 células (grade vazia com "OK" seria silêncio); (b) **o layout
  "Sexta Verde" do banco está VAZIO** — as células desenhadas ao vivo na
  auditoria não foram salvas (consistente com o "salvei e não persistiu"
  do RG-08, curado DEPOIS daquela sessão); o selfcheck usa o layout do
  dono quando ele tem células e degrada para a grade programática 2×3
  com registro nominal.

### Achados de bancada

1. O layout da Sexta Verde vazio no banco (acima) — evidência póstuma do
   RG-08 original.
2. A arte da Sexta Verde tem caixas LARANJA (mediana RGB 244,152,73) —
   a detecção automática de grade é calibrada no vermelho
   Quintou/Belo Brasil e devolve 0 ali; o fluxo real da campanha foi
   "layout do zero" mesmo (capturas 19-165 de Config). Detecção
   multi-cor anotada como evolução (Onda 6/pós).
3. O teste antigo do Dashboard esperava 3 prateleiras — atualizado à
   verdade nova (a "semana" duplica os recentes de propósito).

### O que ficou de fora (Onda 5)

- **Estilo de seção por PÁGINA** (hoje é global na Config; o liga/
  desliga por página existe desde a F8.2).
- **Selos personalizados não congelam** na pasta do projeto (apontam
  para `<raiz>/selos/`; remover o selo do GESTOR preserva a arte no
  disco de propósito — anotado como polimento do congelador).
- Seleção de selos por item é da MESA (o Almoxarifado mantém os
  automáticos; selo é decisão de campanha, não de cadastro).
- Upscale só no EXPORT do cartaz (o preview usa a original — o modelo
  custa segundos; o WYSIWYG do preview segue fiel em conteúdo).
- Guia Z acessível pela paleta de comandos (Ctrl+K), sem botão dedicado
  na barra.
- Detecção de grade multi-cor (o laranja da Sexta Verde) — anotada.
- `test_onda5` monkeypatcha `estilo_secoes` (o cache de Config em teste);
  o caminho Config→estilo é coberto pelo selfcheck real.

**PARADO no ponto de reauditoria. O marco está rodado e os artefatos em
`saida_marco/` — SEM declaração de aceitação: a medição final é do
arquiteto e o SELO FINAL do programa é do Otaviano, na revisão dele.**

## SELO do arquiteto — ONDA 5 e REVISÃO GERAL CONCLUÍDA (18/07/2026)

Medição independente do MARCO, feita pelo arquiteto nos artefatos: RELATORIO
conferido (5.007 produtos; abrir 0,04 s / conciliar 40 em 126,3 s / exportar
0,4 s — os três orçamentos DENTRO); `quintou.pdf` medido nos bytes: **3
páginas de 285,8 × 344,0 mm**; `quintou_p1.png` inspecionado visualmente —
40 células com seções em pill discreto (a borda feia morreu), hifenização
real em produção ("Par-malat"), preços no estilo da arte, heróis no topo. Os
dois achados honestos do relatório (bancada sem o acervo dos 42; layout
Sexta Verde vazio no banco como evidência póstuma do RG-08 pré-cura) estão
corretos e documentados. A perícia do RG-31 com prova filmada (frame 398) e
cura tripla fecha o ciclo aberto pela auditoria do dono.

**402 verdes ×2, exit 0, zero skips. ONDA 5 SELADA.**

**AS SEIS ONDAS DA REVISÃO GERAL ESTÃO CONCLUÍDAS** (1–5 pelo builder com
selo do arquiteto; 6 pela pesquisa do arquiteto). Estado do programa: as 40+
exigências do dono executadas, 402 testes, três campanhas reais como
padrão-ouro, invariantes I1–I5 de pé desde a primeira auditoria.

**O QUE FALTA — e é todo do Otaviano:** (1) o test-drive final dele no app
(as ondas mudaram quase tudo que ele criticou); (2) o apanhado de ressalvas
que ele guardou; (3) a arte real do cartaz 10×15; (4) a PALAVRA DE
ACEITAÇÃO sobre o marco. Com o selo dele, abre-se a última ordem da
jornada: **Bloco G — empacotamento e entrega** (instalador, guia rápido,
migração de assets — o programa no PC do mercado).

## SEGUNDA PASSADA DO DONO (18/07/2026) — SELO DA ONDA 5 REABERTO

O Otaviano reviu o app e reprovou parte do entregue. **Erros do ARQUITETO,
registrados primeiro:** (1) selei a Onda 5 medindo o PDF mas SEM inspecionar
visualmente o `sexta_verde.png` — que está bizarro (grade sintética 2×3
ignorando os balões da arte, caixas translúcidas sujando o fundo, uma seção
por célula picotando tudo, "até " sem data). Lei nova: **selo só com
inspeção visual de TODOS os artefatos, um a um.** (2) O áudio dizia "black
mold" e eu li "peso Black da fonte" — ele queria **DARK MODE**; a
ambiguidade era minha de resolver perguntando. (3) Minhas ordens eram
grossas demais — itens de uma linha viram interpretação do builder. Lei
nova: **ordens em SESSÕES de ~100 passos finos e verificáveis (5 sessões =
~500 passos)**; cada passo pequeno o bastante para não ter dois jeitos de
entender.

**Achados novos (RG-48..RG-58):**
- **RG-48** Marco do Sexta Verde INVÁLIDO: refazer com layout REAL desenhado
  sobre a arte (células nos balões verdes), sem grade sintética; "até" nunca
  renderiza vazio (sem data = sem frase).
- **RG-49** Seções: runs de linhas CONTÍGUAS da mesma categoria desenham UM
  contorno de união (sem linha interna entre linhas irmãs — a divisão no
  meio do "Bebidas" do Quintou); run de 1 célula não ganha caixa própria no
  estilo contorno (só pill).
- **RG-50** Início: repaginação DE VERDADE (dashboard com painéis, eventos
  como abas/cartões com cor e capa, agenda da semana, "continuar de onde
  parei" — spec fina na Sessão 1).
- **RG-51** Configurações: repaginação em ABAS específicas (Aparência,
  Campanhas, IA, Imagens, Selos, Sanitização, Backups, Atalhos), remover a
  engrenagem-fantasma do canto, corrigir os tamanhos espremidos/ilegíveis.
- **RG-52** DARK MODE completo por tokens (claro/escuro), toggle na aba
  Aparência. (Os pesos de fonte da Onda 3 ficam — úteis de todo modo.)
- **RG-53** Mesa: barra reorganizada (dois níveis ou lateral + overflow) —
  botões nunca mais se comem.
- **RG-54** Ateliê/telas: caça aos erros de formatação dos prints da pasta
  "Outra auditoria" (elementos encolhendo, tamanhos errados) — dimensionar
  mínimos e políticas de layout tela a tela.
- **RG-55** Editor: preço não-selecionável/some ao clicar (provável conflito
  do clique-grupo com a grade) — reproduzir com os prints e curar.
- **RG-56** Agrupar/desagrupar: gesto claro, visível e REVERSÍVEL (menu
  "Desfazer grupo", "Restaurar da mestra" sempre visível quando aplicável,
  microtutorial próprio).
- **RG-57** TEXTO_LEGAL: presets visíveis (Aviso legal / Validade /
  Fica-a-Dica) como escolha nomeada na criação da região, não campo oculto.
- **RG-58** Reexecução do MARCO completa após as sessões, com inspeção
  visual do arquiteto em TODAS as peças.

**Plano de correção: 5 SESSÕES de ~100 passos finos cada** (emitidas pelo
arquiteto em docs/SESSAO_1.md..SESSAO_5.md, uma por vez): S1 Aparência
(Início+Configurações+dark mode+barra da Mesa) · S2 Editor (RG-55/56 +
formatação das telas) · S3 Seções+Sexta Verde+marco novo · S4 Fluxo em
massa (importação multi, planilha da estante, aceitar-verdes) · S5
Polimento+presets+revalidação total. O catálogo de visão de longo prazo
está em **docs/RECOMENDACOES_150.md** (150 recomendações do arquiteto).

## Execução

Ordem vigente = este dossiê. O builder executa **Onda 1 → 2 → 3 → 4 → 5 →
6**, uma onda por vez, parando na reauditoria de cada uma. Achado novo
durante as ondas entra AQUI com número RG. O selo final de aceitação do
programa é do Otaviano, sobre o marco (RG-36) rodado com as três campanhas
reais.
