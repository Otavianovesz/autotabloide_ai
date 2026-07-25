# VISÃO F13 — o que o AutoTabloide ainda pode ser

> **Status: CADERNO DE VISÃO. Nada aqui foi implementado.** Segundo entregável da varredura
> paralela (`docs/BRIEFING_VARREDURA_CODE.md`, §7), irmão de `docs/VARREDURA_CODE_F13.md`.
> Ordem literal do dono: *"seja visionário e entenda adições e outras coisas para serem feitas
> e melhoradas enquanto você mesmo audita… tipo 'formas para melhorar o editor em algo digno
> de um programa da Adobe', ou sugestões de outras lógicas de execução, para ficar
> extremamente perfeito, sem falhas e com uma qualidade de vida absurda em tudo quanto é
> mínima função e feature."*
>
> Escrito enquanto ~120 arquivos estavam abertos na varredura. Cada sugestão cita
> **arquivo:linha do que já existe** — este programa tem quase tudo pela metade, e o caminho
> mais curto quase nunca é código novo.

---

## §1 · A tese: isto é um **Data Merge do InDesign** com OCR e recorte embutidos

Um layout com campos + uma fonte de dados = N peças. É literalmente o produto. O InDesign
chama isso de "mala direta de dados" e resolveu esses problemas há vinte anos. Vale roubar o
raciocínio dele, não a interface:

| o que o Data Merge tem | o AutoTabloide tem? | onde isso doeria menos |
|---|---|---|
| **prévia registro-por-registro** (passar item a item vendo a peça montada) | **não** | VC-001 · VC-028 |
| **"criar páginas múltiplas automaticamente"** | parcial (`auto-preencher` + "fora da grade") | VC-029 · A5 |
| **ajuste de imagem por campo** (como a foto se encaixa naquele campo) | parcial (`Ajuste.CONTER/PREENCHER`, com o vazamento R-03) | VC-046 |
| **tratamento de campo vazio** (o que fazer quando o dado falta) | **não** — pula em silêncio (R-07, I2) | **A1** |
| **relatório de overflow** (o que não coube) | **não** — o texto só encolhe (R-05) | VC-050 · **A1** |

E a diferença a favor dele: o AutoTabloide tem **OCR, conciliação semântica e recorte de
fundo** embutidos. O InDesign nunca teve. O produto que ele está construindo é um Data Merge
que **entende o que é um produto de supermercado** — e é aí que mora a vantagem que nenhuma
suíte gráfica dá.

---

## §2 · O fluxo real: hoje × ideal (§7.4 do briefing)

Foto da tabela do WhatsApp → tabloide de **30 itens** exportado. Números **medidos por mim
nesta máquina** estão marcados 📏; o resto é estimativa honesta a partir dos orçamentos do
próprio projeto.

| # | passo | **HOJE** | **IDEAL** | o que muda |
|---|---|---:|---:|---|
| 1 | abrir o app | 📏 0,5 s | 0,5 s | (1ª vez hoje: **+973 MB de download**, CA-01) |
| 2 | foto da tabela → OCR | ~45 s | ~45 s *(em 2º plano)* | máquina; ele já pode conferir enquanto roda |
| 3 | conciliar 30–40 itens (máquina) | ~120 s | ~120 s *(em 2º plano)* | orçamento do projeto: 180 s |
| 4 | **conferir o semáforo** (ele) | ~180 s | ~90 s | diálogo que lembra o tamanho (C-10) + Enter/N/A/R que funcionam + os verdes já aprovados em bloco |
| 5 | criar os ~8 vermelhos: buscar foto | ~50 s | ~0 s | 📏 pausa mínima 1,5 s/item + backoff até 10,5 s, **um por vez** → fila paralela pré-buscando (I-02 já existe pela metade) |
| 6 | **escolher a foto certa** (ele) | ~120 s | ~60 s | grade de candidatos com nota do avaliador (`ai/avaliador.py` já existe) |
| 7 | **remover fundo, 30 fotos** | 📏 **255 s com a tela travada** | **0 s de espera** | 📏 8,5 s/foto em regime; fila em 2º plano + barra "12 de 30" (I-01/I-03/X-02) |
| 8 | auto-preencher | 1 s | 1 s | — |
| 9 | **ajuste fino de 30 células** (ele) | ~300–420 s | ~120 s | 📏 cada tecla recompõe a página inteira (113 ms) síncrono (X-01); guias com medida; alinhamento vertical (R-01); subir/descer que sobem e descem (R-02) |
| 10 | pré-voo + exportar | ~30 s | ~30 s | — |
| | **TOTAL** | **≈ 18–22 min** | **≈ 6–8 min** | |

**A leitura da tabela em uma frase:** dos ~20 minutos, **cerca de 4 minutos são a máquina
segurando o dono no braço** (passo 7) e **cerca de 8 minutos são fricção de edição** (passos 4,
6 e 9). Nenhum dos dois exige algoritmo novo — o passo 7 exige **não bloquear a tela**, e o
passo 9 exige **um editor que diga onde as coisas estão**.

> **O corolário que vale mais que qualquer feature:** onde o tempo é da máquina (rembg, OCR,
> busca), a pergunta certa **não** é "como acelerar" — é **"como isso roda enquanto ele faz
> outra coisa?"**. O rembg já roda em `QThread` (`workers.py`); o que trava é o
> `OverlayOcupado` cobrindo o widget inteiro sem `WA_TransparentForMouseEvents`
> (`carregando.py:144-193`). **A maior economia de tempo deste programa é apagar um véu.**

---

## §3 · A colheita do "enquanto você está aí" (§7.3 do briefing)

Regra do briefing: ao terminar cada arquivo, gastar 60 segundos escrevendo 1 atalho, 1
feedback, 1 automação, 1 prévia e 1 valor padrão melhor. **Colhi 91 itens**, todos com
arquivo:linha. Não são features — são **defaults melhores, feedback e um atalho**, que é onde
mora a maior parte da "qualidade de vida absurda" que ele pediu. Os melhores, por tela:

### 3.1 · Editor / canvas
- **`historico.py`** — *coalescing por gesto*: `registrar(..., gesto="nome:uid")` funde estados
  consecutivos do mesmo gesto dentro de ~400 ms. Resolve o CD-04 (17 teclas = 17 undos) sem
  mexer em mais nada.
- **`canvas.py`** — guardar `pagina_atual` **dentro** do snapshot e navegar de volta ao
  desfazer, com toast *"desfeito na página 2"* (resolve CD-02).
- **`canvas.py`** — um `recompor_do_mapa(dados)` que troca dados **sem recriar o `Historico`**,
  para a Mesa usar no lugar de `carregar` (resolve CD-01 — e o padrão já existe em
  `atualizar_dados`, usado num único lugar).
- **`barra_editor.py`** — ligar `setEnabled` de Desfazer/Refazer em
  `pode_desfazer()/pode_refazer()` (já existem, `historico.py:62-66`). Botão apagado avisa
  sozinho o que hoje é silêncio (CD-08).
- **`painel_camadas.py`** — adiar o `recarregar()` do sinal `canvas.editou` com
  `QTimer.singleShot(0, ...)`, em vez de rodá-lo **dentro** do sinal que destrói o próprio botão.

### 3.2 · Mesa e Fábrica
- **`fabrica.py`** — pedir confirmação antes de `_escolher_preset` sobrescrever um layout vindo
  do Ateliê (`confirmar_destrutivo` já existe).
- **`fabrica.py`** — mostrar ao lado de "Dois por folha" **quantas folhas saem com e sem**:
  *"12 cartazes = 6 folhas | sem: 12 folhas"*. Um número mata o CE-03 sem nenhuma guarda nova.
- **`fabrica.py`** — trocar a guarda de tamanho absoluto (`:269`) por guarda de
  **aproveitamento**: habilitar só quando duas peças ocupem mais que ~60% da folha.
- **`mesa.py`** — item **"Renomear esta seção"** no menu de contexto da própria célula (hoje só
  pelo `btn_titulos` da barra, que ninguém acha).
- **`mesa.py`** — quando ele marcar "Agrupar por categoria" e a página não tiver categoria útil
  (0 seções, ou uma só chamada "Outros"), **dizer isso** em vez de desenhar um retângulo em
  volta de tudo (CE-06).
- **`mesa.py`** — `_avisos_orfaos` também acusar uid de mapa/override que não existe mais na
  estante (hoje só acusa slot inexistente).

### 3.3 · Imagens e IA
- **`almoxarifado.py`** — antes de disparar "Corrigir nomes (IA)", **prévia de 10 linhas em
  duas colunas** (nome de hoje → nome proposto). Resolve CC-01 e CC-02 de uma vez, e é o
  padrão do Data Merge: *veja antes de aplicar em massa*.
- **`almoxarifado.py`** — trocar o `Trabalhador` do passe em lote por `TrabalhadorFila` (que já
  tem `cancelar()`) e pôr o botão **"Parar"** dentro do overlay.
- **`fundo.py`** — **separar "carregar" de "baixar"**: `aquecer()` só aquece se o `.onnx` já
  estiver no disco; se faltar, em vez de puxar 973 MB calado, um cartão *"o recorte de fundo
  precisa baixar 973 MB uma vez — baixar agora / depois"* (resolve CA-01).

### 3.4 · Arquivos, Cofre e primeira execução
- **`cofre.py`** — marcar o snapshot automático com a **saúde do banco no próprio nome**
  (`..._auto_ok.db` / `..._auto_suspeito.db`) e **nunca deixar a rotação apagar o último "ok"**
  (resolve CB-01 com uma linha de nome de arquivo).
- **`cofre.py`** — antes de restaurar, dizer **o que muda**: *"este snapshot tem 412 produtos e
  18 projetos; o seu banco de agora tem 431 e 20"*. E, depois, oferecer o desfazer no toast
  (a `guarda` de pré-restauração já é criada, `cofre.py:157`).
- **`rascunho.py`** e **`historico.py`** — escrita atômica (`.tmp` + `os.replace`) e, na
  leitura, cair para o anterior quando o mais novo estiver truncado (resolve CB-09).
- **`atproj.py`** — manifesto com **sumário de arquivos esperados + tamanho**, conferido na
  importação, devolvendo a lista do que faltou (resolve CB-08; é I2 puro).
- **`lancar_autotabloide.py`** — um `garantir_raiz()` único que semeia as fontes **E prova a
  escrita** gravando/apagando um arquivo de teste (resolve CA-03 e CA-04 juntos).
- **`editor_app.py`** — instalar um `sys.excepthook` (e o gancho equivalente nos slots do Qt)
  que grava todo traceback em `<raiz>/logs/erros.log`. **É a linha que transforma o CA-02 de
  "não dá para dar suporte" em "manda o arquivo".**
- **`editor_app.py`** — quando cair na grade sintética, a Mesa abrir com um cartão explicando
  em vez de uma folha branca (resolve CA-05).
- **`recuperacao.py`** — incluir **as fontes** na `verificar_ao_abrir()` (hoje só olha PRAGMA e
  fotos): sem Quicksand/Roboto, avisar na abertura, não no pré-voo que se dispensa.

### 3.5 · Tela, DPI e teclado
- **`shell.py`** — atalho **"Trazer a janela para a tela"** (Ctrl+Shift+0) no catálogo e no
  Ctrl+K; e trocar o teste `intersects` por um **clamp de verdade** no `restaurar_estado`
  (resolve CG-02, que é do tipo "ele não consegue nem arrastar de volta").
- **`configuracoes.py`** — legenda viva ao lado de "Escala da interface" com o que o app **lê
  da máquina**: *"Sua tela: 3440×1440, Windows em 150%"*; e **prévia** da escala antes de
  aplicar, com uma faixinha `Aa — Arroz Camil 5 kg   R$ 24,99` nos três tamanhos.
- **`componentes.py`** — em `confirmar_destrutivo`, criar o **"Cancelar" ANTES** e chamar
  `setDefaultButton(cancelar)`. **Duas linhas trocadas de lugar** consertam o CF-01 nos 13
  pontos de chamada de uma vez.
- **`atalhos.py`** — `criar_atalho` **recusar (ou logar)** uma tecla que já tenha dono vivo no
  mesmo escopo. É a vacina contra o CF-02 nascer de novo.
- **`carregando.py`** — `OverlayOcupado.mostrar()` guardar `alvo.isEnabled()`, fazer
  `setEnabled(False)` e devolver no `esconder()` (resolve CF-05).
- **`polimento.py`** — somar ao `ordenar_tab` um `definir_default(dialogo, botao)` que faz
  `setDefault(True)` + dá foco inicial. Resolve os 36 diálogos do CF-03 num lugar só.
- **`barra_editor.py`** — no helper `_tool`, acrescentar `b.setAccessibleName(tip)`: **o texto
  já está na variável**, falta uma linha, e a acessibilidade sai de zero.

### 3.6 · Bancada e repositório
- **`app/tests/fixtures/`** — versionar uma **arte-fixture minúscula gerada em código** (4
  caixas de preço num PNG 300×400, ~5 KB) e apontar `test_grade` para ela. **É o conserto certo
  do CH-01** — não o caminho absoluto.
- **`pyproject.toml`** — registrar o marker `bancada` e ligar `--strict-markers`; gerar e
  versionar um lockfile; apagar as 5 dependências nunca importadas.
- **`app/tests/test_teclado.py` (novo)** — `QTest.keyClick` na janela real afirmando o
  **efeito**: Ctrl+K abre a paleta **na Mesa**; Enter no ImportarBanco importa; Enter no
  `confirmar_destrutivo` **cancela**. Três asserções que teriam pego CF-01, CF-02 e CF-04.
- **`modo.py`** — trocar a lista escrita à mão no docstring por um **teste que varra o código**:
  toda função de `app/core` e `telas/servico` que grava tem de chamar `exigir_escrita`. É a
  vacina contra o CB-02 (e contra a próxima porta que nascer aberta).
- **`.gitignore`** — trocar as 12 linhas nominais de rodada por um bloco só (`_*.txt`,
  `_*.xml`) — a rodada F13 já vazou de novo.

---

## §4 · As sugestões (VC-)

Formato do §7.5 do briefing, condensado numa linha de cabeçalho + os campos. **Grau**:
ESSENCIAL / ALTO VALOR / LUXO. **Custo**: P / M / G. Toda linha "já existe" foi conferida na
fonte. Nenhuma fere trava do CLAUDE.md, salvo onde eu digo explicitamente.

### 4.1 · O EDITOR (Ateliê/canvas) — a versão Adobe

| # | sugestão | já existe aqui | ganho | grau | custo |
|---|---|---|---|---|---|
| **VC-001** | **Prévia com PRODUTO REAL no Ateliê** — o *Preview* do Data Merge, com `◀ 1 de 40 ▶` | `atelie.py:54` (`_EXEMPLO` estático), `servico.py:660` (`dados_para_desenho`) | hoje: desenhar → salvar → ir à Mesa → ver a foto estourar → voltar. ~40 s por ida, várias por layout | ESSENCIAL | M |
| **VC-002** | **Ctrl+A e "Selecionar iguais"** (mesmo tipo / papel / estilo) | `canvas.py:1551` (`colar_estilo` já é lote), `:1987` (`selecionados()`) | trocar a fonte de todos os preços: 20 seleções × 12 s (~4 min) → ~15 s | ESSENCIAL | P |
| **VC-003** | **Lei da criação: tudo nasce SELECIONADO e onde o dono está olhando** | `canvas.py:1396` (o padrão certo já escrito), `:1520` (`_slot_no_ponto`) | mata a classe "cliquei e não aconteceu nada" — 3 dos 6 botões de adicionar. Resolve E-04 (carimbar invisível) | ESSENCIAL | P |
| **VC-004** | **Painel Transform: X / Y / Largura / Altura em mm**, com cadeado de proporção | `itens.py:166-193` — **`_emitir_medidas` JÁ calcula X/Y/L/A em mm** e vira um rótulo somente-leitura | resolve E-08 (rotação sem alternativa de resize); acertar a mestra: ~2 min no olho → ~20 s | ESSENCIAL | P |
| **VC-005** | **Coalescer digitação**: 1 recomposição e 1 undo por PALAVRA | o molde está na casa: `faixa_paginas.py:24,55-59` (`DEBOUNCE_MS = 400`) | dica de 60 caracteres: 60 `compor_pagina` + 60 JSONs gravados → ~4. Resolve X-01 e CD-04 | ESSENCIAL | P |
| **VC-006** | **Alinhar/distribuir com ALVO escolhível** (à seleção \| à página), nunca recusando calado | `alinhamento.py:38-67` (a matemática só precisa de outra caixa) | centralizar um preço na página: hoje impossível pela UI (ele faz no olho) → 1 clique | ESSENCIAL | P |
| **VC-007** | **Duplicar em SÉRIE** (linhas × colunas × espaçamento) — o *Step and Repeat* | `grade.py:281-288` (`carimbar_copia` já cria com `ref_grupo` e propagação por uid) | grade 4×5: 19 carimbos a olho (~5 min) → um diálogo de 4 campos (~20 s) | ESSENCIAL | M |
| **VC-008** | **Shift+seta = passo GRANDE** (hoje faz o contrário do mundo inteiro) | `canvas.py:1691-1699` (`nudge_selecao` já recebe delta em mm e agrupa em 1 undo) | mover 20 mm: 20 toques → 2. Mapa sugerido: seta 1 mm, Shift 10 mm, Alt 0,1 mm | ALTO VALOR | P |
| **VC-009** | **Shift = proporção travada, Alt = do centro** | `itens.py:442` — **a âncora JÁ é um dicionário parametrizado**, só falta escolher outra | ~20 s por célula de conserto de proporção no olho | ALTO VALOR | P |
| **VC-010** | **Medida grudada no objeto + cota de distância na cena** (guias inteligentes) | `itens.py:27-51` (`cota_entre_rects`) e `canvas.py:168-183` (`drawForeground` já pinta) | ~2 s por arraste × 5 arrastes × 30 células ≈ **5 min por tabloide** | ALTO VALOR | M |
| **VC-011** | **Snap de ESPAÇAMENTO IGUAL** — o alvo que falta no ímã | `canvas.py:1832-1859` (`alvos_snap`, o serviço único de alvos) | elimina o ciclo arrasta→erra→seleciona 3→distribui (~45 s por vão) | ALTO VALOR | M |
| **VC-012** | **Painel de Camadas em ÁRVORE** (célula → peças), arrastar para reordenar | `model.py:274-276` (a árvore **já está no dado**), `canvas.py:731-741` | achar "o preço da célula 14": rolar 60 linhas idênticas (~20 s, e erra) → 2 cliques | ALTO VALOR | M |
| **VC-013** | **Alt+clique no olho/cadeado = isolar** (esconder/travar todas as outras), reversível | `canvas.py:918-950` (`_aplicar_isolamento` já faz exatamente isso para interação) | 59 cliques → 1, e o inverso → 1 | ALTO VALOR | P |
| **VC-014** | **Modo "Prévia limpa" numa tecla** — a peça sem nenhuma marcação do editor | `canvas.py:1753-1761` (`set_raio_x` é exatamente o mecanismo: flag + `update()`) | exportar/abrir/voltar (~40 s por conferida, várias por layout) → uma tecla | ALTO VALOR | P |
| **VC-015** | **Pré-voo do LAYOUT dentro do Ateliê** (quantas células, fora da página, sobrepostas) | `grade.py:335` (`ocupaveis`), `rendering/contraste.py` (já ligado num botão) | mata a viagem "Ateliê → Mesa → faltam 6 células → volta" (~3 min cada) | ALTO VALOR | M |
| **VC-016** | **Alça de rotação no canto (Shift = 15°) + o resize que sobrevive à rotação** | `itens.py:93-97` (`aplicar_rotacao`), `:414-425` (o cursor diagonal **já** funciona girado) | destrava o caso hoje impossível; casa com o N-08 (os 7 encartes têm células rotacionadas) | ALTO VALOR | M |
| **VC-017** | **Editar o texto NO LUGAR** (duplo clique = digitar, com prévia ao vivo) | `itens.py:476-487` (o duplo clique já tem dono e já desarma o RG-15) | ~4 idas e voltas olho↔painel por texto (~30 s cada) → zero | ALTO VALOR | M |
| **VC-018** | **Ctrl+D repete o DESLOCAMENTO da última duplicata** (a metade útil do *Transform Again*) | `canvas.py:1937-1959` (onde mora o offset fixo) | fileira de 5: ~2 min com erro residual → 4 toques | LUXO | P |
| **VC-019** | **Dicionário de modificadores escrito na tela** (um gesto, um significado) | `canvas.py:2062` (zoom), `:1491` (troca), `itens.py:295` (suspender snap) | devolve a fuga do ímã na Mesa (hoje ele briga com o snap e desiste) | ALTO VALOR | P |

### 4.2 · A MESA — a linha de montagem

| # | sugestão | já existe aqui | ganho | grau | custo |
|---|---|---|---|---|---|
| **VC-020** | **Central de trabalhos no rodapé** — a máquina mói enquanto ele trabalha | `workers.py:69-71` (`item_pronto`/`item_falhou`/`fila_terminou` já narram e **não estão conectados**) | **30 fotos × 8,5 s = ~4 min de tela sequestrada → 0**. É o maior item da tabela do §2 | ESSENCIAL | G |
| **VC-021** | **Painel de Pendências VIVO** — o pré-voo sai do portão e vira estação | `servico.py:1427-1526` (já produz a lista por célula com rótulo "página N, célula X") | 8-12 pendências × ~20 s de caça = **3-4 min por edição, toda edição** | ESSENCIAL | M |
| **VC-022** | **Barra de prontidão: "24 de 30 prontos"** no lugar de "30 item(ns)" | `servico.py:747-766` (`checklist_final` **já calcula** sem_foto/sem_preço/validade) | troca "está pronto?" por uma barra sempre visível; clicar filtra os 6 que faltam | ESSENCIAL | P |
| **VC-023** | **As nove estações escondidas** — tirar do Ctrl+K o que é o coração do fluxo | `mesa.py:158-183` (a barra já é agrupada por grupos na ordem do fluxo) | nove funções saem de 0% de uso para 2 cliques. Em especial **"Aprovar"** — sem ela, TODA peça sai com RASCUNHO (P-05/P-06) | ESSENCIAL | P |
| **VC-024** | **Clicar no item acende a célula (e vice-versa)** — o painel *Links* do InDesign | `mesa.py:1592-1616` (`_ir_para_aviso` **já** acha o slot pelo uid e troca de página) | ~10 s de caça × 30 itens = ~5 min por edição | ALTO VALOR | P |
| **VC-025** | **Miniatura da foto em toda lista** (estante, Fábrica, conciliação) | `modo_pai.py:88,177` (`setIconSize` + `QIcon` numa `QListWidget` — o padrão pronto) | pega a foto trocada em 1 s, na estante, em vez de depois do PDF (~10 min de retrabalho) | ESSENCIAL | P |
| **VC-026** | **"Editar no cadastro" a partir da estante** — o *Edit Original* | `it.produto_id` (`servico.py:38`) + `servico.editar_produto:220-241` | responde ao literal *"como é que eu edito dentro do banco de dados?"* (I-06). ~40 s × 3-5 por edição | ALTO VALOR | P |
| **VC-027** | **Ações em massa na estante** (selo, observação, categoria, promoção) | `planilha.py` — *"Aplicar categoria à seleção"* **já existe uma tela ao lado** | selo em 8 itens: ~40 cliques → 5 | ALTO VALOR | P |
| **VC-028** | **Conferir 1 a 1 com Ctrl+→** — a prévia registro-por-registro do Data Merge | `_ir_para_aviso` + `canvas.zoom_para_selecao` — os pedaços existem soltos | "olhar a página e torcer" → 30 passagens de ~3 s | ALTO VALOR | M |
| **VC-029** | **"Criar páginas automaticamente" quando sobra item** | `mesa.py:1133-1179` (`_perguntar_destino_resto` **já sabe duplicar a página**) | 15 itens órfãos por edição → 0, com 1 clique | ESSENCIAL | P |
| **VC-030** | **Auto-preencher com PRÉVIA e por afinidade** (slot grande ↔ item de destaque) | `ordenar_com_herois`, `densidade_da_pagina`, `ocupaveis` — tudo pronto | atende o pedido literal do dono que hoje é impossível (C-07) | ALTO VALOR | M |
| **VC-031** | **O override viaja com o ITEM, não fica preso à célula** | a chave certa já é usada em todo o resto: `_mapa[slot_id] = it.uid` (I1) | elimina uma classe de "publiquei o preço errado" que ele não tem como perceber | ESSENCIAL | M |
| **VC-032** | **Esc na conciliação pergunta antes de jogar 15 min fora** | `confirmar_destrutivo` (já usado em `mesa.py:471`) | evita perder 5-15 min de curadoria por acidente | ESSENCIAL | P |
| **VC-033** | **Cabeçalho da oferta (evento · validade · meta)** — e o `_evento` que nunca é atribuído | `montar_validade_oferta`, `sugerir_validade` (prontos, `servico.py:1171-1262`) | **uma linha** (`self._evento = evento`) ressuscita três funcionalidades construídas. Resolve P-01/P-02 | ESSENCIAL | P |
| **VC-034** | **Trocar o layout pela Mesa** sem perder a montagem em silêncio | `listar_layouts`/`carregar_layout` já importados dentro da Mesa (`mesa.py:790`) | com os 7 encartes novos ele troca de layout **toda semana** | ALTO VALOR | M |
| **VC-035** | **Recuperar rascunho deixa de bifurcar o projeto em dois** | o campo já é gravado (`mesa.py:1316`) | evita exportar do projeto errado semanas depois (P-10) | ALTO VALOR | P |

### 4.3 · IMAGENS — a versão "Photoshop" do Estúdio

| # | sugestão | já existe aqui | ganho | grau | custo |
|---|---|---|---|---|---|
| **VC-036** | **Fila de imagem VISÍVEL: "X de N", cancelar, e quem falhou pelo NOME** | `workers.py:59-94` (`TrabalhadorFila` com `item_pronto`/`item_falhou`/`cancelar` — **nada conectado**) | 4 min de tela morta → 4 min de tela viva; cancelar devolve até 3 min (I-03) | ESSENCIAL | M |
| **VC-037** | **Detector de fundo branco LIGADO por padrão** | `fundo.py:88-105` (`_pular_rembg_fundo_branco` **existe e está desligado**) | **8 s → 0,3 s** por foto de fundo branco (metade das fotos de varejo) | ESSENCIAL | P |
| **VC-038** | **Cache do recorte por conteúdo** — o mesmo hash que o upscale já usa | `servico.py:417-425` (cache por sha256) e `:1720-1740` (`_hash_foto`) | lote de 30 com 6 repetidas: −48 s; um dia de refazeres: −80 s | ALTO VALOR | P |
| **VC-039** | **UMA receita de packshot (perfil), aplicável e REaplicável na peça inteira** | `estudio.py:66-81` (`packshot_degrau1` já tem todos os parâmetros) | acaba com a peça de 30 iluminações diferentes; 1 clique reaplica o que são 30 idas ao Almoxarifado | ESSENCIAL | M |
| **VC-040** | **A nota da foto entra no PRÉ-VOO** (pegar a foto ruim antes da gráfica) | `avaliador.py:53` (`avaliar_foto`) + `servico.py:1427` (onde a linha entra) | ~2 s de checagem contra um encarte reimpresso | ESSENCIAL | P |
| **VC-041** | **Resolução EFETIVA** (do produto na bbox do alfa) em vez de resolução do arquivo | `avaliador.py:41-89` + `fundo.py:110-123` (`recortar_conteudo` já acha a bbox) | devolve utilidade a um módulo que hoje **sempre diz "foto boa"** | ALTO VALOR | P |
| **VC-042** | **Refazer o recorte com OUTRO modelo no ponto da correção** | `fundo.py:25-29` (`MODELOS`) + `refino_dialog.py:82-98` (a barra onde os botões cabem) | ~40 s de pincel numa foto difícil → ~8 s; 5 por edição ≈ 3 min (I-05) | ALTO VALOR | M |
| **VC-043** | **Prévia por amostra + DESFAZER O LOTE inteiro** | `previa_estudio_dialog.py:51` (o comparador pronto) + `biblioteca.listar_versoes` | lote errado de 30: ~10 min de restauração → ~5 s | ALTO VALOR | M |
| **VC-044** | **Pincel de refino digno: zoom, traço contínuo, borda macia, Ctrl+Z por pincelada** | `refino_dialog.py:110-147` (o gesto já isolado em `pintar`, testável) | correção de borda hoje impossível → ~20 s | ALTO VALOR | M |
| **VC-045** | **O Estúdio na MESA** — tratar as fotos desta edição de onde o olho está | `almoxarifado.py:812-851` (o lote **já é headless**: `tratar_estudio` + `definir_imagem`) | ~40 s de ida-e-volta × 10 fotos ruins ≈ **7 min por edição** | ALTO VALOR | M |
| **VC-046** | **Enquadrar a foto na célula ARRASTANDO** — não digitando `0,05` | `compositor.py:210-226` (o motor) + `override_dialog.py:70-95` (a UI numérica atual) | ~20 s por célula → ~3 s; 10 células ≈ 3 min | ALTO VALOR | G |
| **VC-047** | **Curadoria com NOTA, ORDEM e prévia do RECORTE** (não da foto crua) | `curadoria_dialog.py:93-122` (a grade) + `avaliador.py:53` (a nota pronta) | escolha errada descoberta 8 s tarde × 30 ≈ 4 min por edição | ALTO VALOR | M |
| **VC-048** | **A busca CONTA o que jogou fora** | `busca.py:207-245` (basta contar) | evita 3-4 rebuscas cegas por produto difícil (~10 s + 1,5 s de pausa cada) | ALTO VALOR | P |
| **VC-049** | **O lote não pode PIORAR foto boa**: marcar o já tratado e perguntar | `almoxarifado.py:812-851` (a caixa de confirmação, onde a pergunta cabe) | evita estragar N fotos boas num clique; e o lote cai pela metade | ALTO VALOR | P |

### 4.4 · IA — o copiloto que ela ainda não é

| # | sugestão | já existe aqui | ganho | grau | custo |
|---|---|---|---|---|---|
| **VC-050** | **O piso determinístico da revisora roda no PRÉ-VOO**, não só no botão "Revisar" | `revisora.py:72-111` (`_heuristicas` já recebe layout+fontes e **nunca levanta**) | pega 3-6 nomes cortados por encarte de 30. Custo: uma chamada | ESSENCIAL | P |
| **VC-051** | **Categoria pelo vizinho mais próximo — o piso SEM IA** | `conciliacao.py:346-352` (os candidatos ordenados **já são calculados e descartados**) | **0% → ~80% do acervo categorizado sem LM Studio ligado.** Resolve C-03 | ESSENCIAL | M |
| **VC-052** | **O "porquê" do semáforo aparece na linha** (hoje é escrito com capricho e só os testes leem) | `conciliacao.py:414-416` (o texto pronto) + `ItemMesa` (onde falta o campo) | ~20 s por amarelo × 5 × 8 tabelas/semana ≈ **13 min/semana** | ESSENCIAL | P |
| **VC-053** | **O alias aprende o texto que o dono CORRIGIU, nunca o que o OCR errou** | `conciliacao_dialog.py:323-336` (onde o original é perdido) | erro recorrente de OCR: ~10 min/semana, permanente | ALTO VALOR | P |
| **VC-054** | **Existe "não é esse"** — hoje o app só sabe aprender SIM | `conciliacao_dialog.py:347-349` (o botão "É novo" já captura o gesto) | ~3 falsos amarelos recorrentes × 15 s × 8 tabelas ≈ 6 min/semana, **permanentes** | ALTO VALOR | M |
| **VC-055** | **O OCR lê 3 campos e poderia ler 6 na MESMA passada** (unidade, observação, promoção) | `ocr.py:23-45` (o prompt) e `:48-59` (os dataclasses a ampliar) | ~2 min de digitação por edição, custo zero de máquina | ESSENCIAL | M |
| **VC-056** | **O OCR confere a si mesmo** ("li 11 de 12 linhas") | `ocr.py:23-45` — bastaria pedir `total_de_itens` e o `numero` de cada linha | a semana real teve 94 itens em 8 tabelas; **uma linha perdida por tabela = 8 produtos fora do encarte sem ninguém saber** | ESSENCIAL | P |
| **VC-057** | **O OCR devolve a POSIÇÃO da linha** → conferir com a foto ao lado | `conciliacao_dialog.py:244-268` (`_painel_foto`, com o `QLabel` guardado **justamente para isso**) | ~5 s × 30 linhas × 8 tabelas ≈ **20 min/semana** | ALTO VALOR | M |
| **VC-058** | **Nenhum lugar do app diz se a IA está viva** — o dono descobre errando | `servico.py:163-167` (`_motor_se_disponivel`, o ponto único a instrumentar) | 1 ciclo de erro por sessão + até 3 s de congelamento por clique | ESSENCIAL | P |
| **VC-059** | **Enriquecer em LOTE de 5, não 1 requisição em série por item** | `enriquecimento.py:201-208` (o prompt de sistema reenviado a cada item) | 20 vermelhos: ~100 s → ~25 s; ~10 min/semana | ALTO VALOR | M |
| **VC-060** | **"Fica a Dica" sem IA devolve algo** (a manchete sem IA já devolve — mesma casa, `_MANCHETES_PADRAO`) | `enriquecimento.py:422-425` (o padrão certo, no mesmo arquivo) | tira o beco sem saída: ~2 min de digitação ou 1 pré-voo ignorado por edição | ALTO VALOR | P |
| **VC-061** | **A memória sazonal e o ranking sugerem no lugar onde a oferta nasce** | `inteligencia.py:82-110` (`ranking_ofertados`, `memoria_sazonal`, por chave natural) | montar a lista de 30 é a maior parte do tempo de decisão da semana | ALTO VALOR | M |
| **VC-062** | **A curadoria pergunta à visão "isto é mesmo este produto?"** | `client.py:168-186` (`visao`) + `avaliador.py:53-88` | 6 candidatos × 5 s = ~30 s → ~15 s, e o suspeito marcado | ALTO VALOR | G |

### 4.5 · DADOS — o que o banco já sabe e não conta

| # | sugestão | já existe aqui | ganho | grau | custo |
|---|---|---|---|---|---|
| **VC-063** | **Sentinela de preço POR PRODUTO no momento da importação** (não por categoria, no fim) | `inteligencia.py:46,66` (`historico_de_preco`, `serie_de_um` → `menor`) | pega o erro na conciliação (~2 min depois da foto) em vez de no balcão | ESSENCIAL | M |
| **VC-064** | **Coluna "Δ vs. semana passada"** na conciliação e na planilha | `servico.py:799` (`diff_edicoes`, por chave natural) e `:988` (`diff_contra_ultima_edicao`) | varrer 40 linhas atrás de anomalia: ~80 s (ou nada) → ~10 s | ESSENCIAL | M |
| **VC-065** | **"Menor preço do histórico" como selo na própria linha** | `inteligencia.py:66-77` (`serie_de_um` já calcula `menor` e `menor_marcado`) | a pergunta "isto vale destaque?" custa ~25 s por item hoje | ALTO VALOR | P |
| **VC-066** | **A lista que falta: "nunca ofertado"** (o acervo menos o ranking) | `inteligencia.py:82` + `:247` (`saude_acervo` já varre o acervo vivo) | responde "o que eu tenho pronto e não estou usando?" em 1 clique | ALTO VALOR | P |
| **VC-067** | **A Inteligência abre COM a edição aberta** (hoje o relatório está permanentemente vazio) | `inteligencia_dialog.py:126` (**a assinatura já aceita `itens`**), `:290-323` (a aba pronta) | **uma linha na Mesa** destrava uma tela inteira já construída e testada | ESSENCIAL | P |
| **VC-068** | **Saúde do acervo no Início, como cartão** — não atrás do 9º botão do Almoxarifado | `inteligencia.py:247,286` (`saude_com_metas`, com `ok` por métrica pronto) | transforma um número que ele nunca viu em 3 palavras que ele lê todo dia (C-04) | ALTO VALOR | M |
| **VC-069** | **Heróis por desconto REAL contra o histórico**, não pelo preço mais baixo do dia | `servico.py:1236` (`ordenar_com_herois`) + `inteligencia.py` (o histórico) | a capa deixa de ser sorteada pelo item mais barato. Sem trabalho novo: um combo com 3 opções (C-07) | ALTO VALOR | M |
| **VC-070** | **O calendário do varejo puxando a memória sazonal** — *"Páscoa em 21 dias; ano passado você ofertou…"* | `calendario.py:70` (`proximas_datas`, com `faltam`) + `memoria_sazonal` | montar a Páscoa: ~20-30 min de arqueologia → um lembrete pronto (P-04) | ALTO VALOR | M |
| **VC-071** | **`preco_atual` com data** — o "de" do cartaz envelhece em silêncio | `models.py:113,133` (`atualizado_em` prova que o padrão de coluna-data existe) | evita o cartaz "de R$ 5,49 por R$ 5,29" | ALTO VALOR | M |
| **VC-072** | **Edição em lote no Almoxarifado reusando o motor de prévia da ponte Excel** | `excel_acervo.py` (o padrão prévia→confirma **completo**: `_plano_local:238`, `_exibir_campos:260`) | categorizar 50 itens: ~10 min → ~30 s (A-02) | ALTO VALOR | M |
| **VC-073** | **A purga de 30 dias NOMEIA o que apagou** (hoje diz "log no console" — e no exe não há console) | `lixeira.py:132-135` (o log **já é montado com nome e data**) | evita "cadê a foto daquele produto?" meses depois; e um aviso 7 dias antes | ESSENCIAL | P |
| **VC-074** | **O semáforo de qualidade olha peso e marca** — os dois campos que a sanitização travada exige | `servico.py:196` (`qualidade_produto`, 6 linhas, ponto único) | fecha o furo entre "o acervo diz 🟢" e "a peça sai com o nome pela metade" | ALTO VALOR | P |
| **VC-075** | **"3ª semana seguida" na própria linha**, não num toast que passa | `servico.py:901` (`semanas_seguidas` **já devolve o inteiro** e a frase joga fora) | o dado já é calculado por item e é reduzido a uma frase truncada em 3 nomes | ALTO VALOR | P |

### 4.6 · O FLUXO E AS TELAS QUE SOBRARAM

| # | sugestão | já existe aqui | ganho | grau | custo |
|---|---|---|---|---|---|
| **VC-076** | **Ctrl+S salva POR CIMA do mesmo projeto**; "Salvar como…" vira outro comando | `projetos.py:171` (`projeto_id` já implementado e testado) | ~20 s × 5 salvamentos por encarte; e acaba a proliferação de cópias | ESSENCIAL | P |
| **VC-077** | **Uma porta só para foto**: toda imagem que entra numa célula passa pelo recorte | `servico.py:2191` (`tratar_imagem`) — o caminho certo **já está** em `mesa.py:2168` | resolve I-06 (o gesto mais natural é o único sem rembg): ~90 s × 3-5 fotos por edição | ESSENCIAL | M |
| **VC-078** | **Toda espera longa tem "Cancelar"** e diz o que está fazendo agora | `workers.py:80` (`TrabalhadorFila.cancelar`) + `carregando.py:144` | 1 arquivo errado/semana × 150 s; e **acaba o "tenho que abrir e fechar o programa"** | ESSENCIAL | M |
| **VC-079** | **"Aprovar" ganha botão visível — e o CARTAZ ganha aprovação** (hoje não tem nenhuma) | `servico.py:769-779` (`aprovar_projeto`) + `checklist_final` | imprimir 30 cartazes com RASCUNHO atravessado e refazer: ~10 min + 30 folhas (P-07) | ESSENCIAL | M |
| **VC-080** | **Nome de arquivo sugerido e última pasta lembrada** nas 14 saídas | `ConfigRepositorio` (o mesmo mecanismo das ~30 chaves) | ~25 s × 4 saídas/semana ≈ 100 s/semana | ESSENCIAL | P |
| **VC-081** | **Atualizar os PREÇOS de uma oferta existente com uma tabela nova** — o Data Merge de verdade | `servico.py:789-796` (`chave_natural`: produto_id > ean > nome — o casamento certo por identidade) | **a semana recorrente cai de ~10,7 min para ~4,2 min.** É o item de maior alavanca da lista | ESSENCIAL | M |
| **VC-082** | **Pré-voo clicável**: cada pendência leva ao item | `mesa.py:1551-1616` (`_mostrar_laudo` + `_ir_para_aviso`, prontos) | 8 avisos × ~20 s de caça ≈ 160 s por export; e some o "…" que esconde o 13º problema | ALTO VALOR | P |
| **VC-083** | **Publicar com prévia** — hoje ele gera no escuro e vai olhar a pasta | `fabrica.py:603-609` (`_compor_preview`, o padrão pronto) | ~60 s por formato × 2-3 formatos por campanha | ALTO VALOR | M |
| **VC-084** | **Modo Pai: compor em worker, prévia da peça REAL, "página 1 de N"** | `workers.Trabalhador` + `OverlayOcupado`, **ambos já importados em `modo_pai.py`** | tira 5-15 s de congelamento por seleção (o "travou" que faz fechar o app) | ALTO VALOR | M |
| **VC-085** | **Prévia de impressão (sangria + margem de segurança)** na Mesa e na Fábrica | `previa_impressao.py:20` — **pronto, testado, no tamanho físico real, e não ligado** | evita a folha cortada errada (~30 cartazes reimpressos) | ALTO VALOR | P |
| **VC-086** | **COMUNICADO: o cartaz de recado/aviso de mural** | `cartaz.py:50-118` (`_cartaz_padrao` — as regiões por FRAÇÃO já resolvem qualquer tamanho) | tira o Photoshop do fluxo: ~15 min por recado × 2-4/mês ≈ **1 h/mês** | ALTO VALOR | M |
| **VC-087** | **Biblioteca de cartazes com prévia visual** (e mais de um desenho) | `cartaz.py:50` (variantes novas são poucas linhas) | escolha errada de formato custa refazer o lote (~5 min) | LUXO | M |

> **VC-086 é LACUNA DE PRODUTO, não bug** — a busca por `comunicado`/`edital`/`mural`/`recado`
> em todo `app/` dá **zero ocorrências** (§12 do dossiê). Nunca existiu. O dono precisa saber a
> diferença entre "quebrou" e "nunca foi feito".

---

## §5 · Parecer de arquitetura (§7.2 do briefing)

As 8 propostas do briefing, avaliadas contra a fonte real. **Regra que eu segui: preferir o
incremental — são 67 mil linhas funcionando, e o programa já está frágil demais para uma
reescrita.**

| # | proposta | parecer | custo |
|---|---|---|---|
| **P1** | Undo como objeto (**Command**) | **NÃO reescrever.** O `Historico` por snapshot é bom (dedup, corte de futuro, disco). Basta `registrar(..., rotulo=)` + coalescência de ~600 ms por `(uid, atributo)`. O Command completo é **veto meu**: paga caro e entrega o que o rótulo já entrega | P |
| **P2** | Renderização **incremental** | **Sim, em 3 degraus.** (1) cache do fundo por `caminho+mtime+tamanho` — tira o `open/convert/resize` de 6 MP de **cada** recomposição; (2) debounce de 400 ms (o molde está em `faixa_paginas.py:24`); (3) cache por slot **só depois** dos dois. Estimativa: 30-50% já no degrau 1 | M |
| **P3** | **Fila de trabalho única** | **Sim, mas na ordem INVERSA da proposta.** Passo 1: trocar o véu de tela cheia por um rodapé — **devolve ~4 min por edição sozinho**. Passo 2: promover `FilaIA` (`workers.py:97-140`, que **já é 80% de uma job queue**: prioridade por foco, `comecou_item`, `pendentes()`, `cancelar()`) a `app/core/fila.py` | M |
| **P4** | **Barramento de eventos** | **Sim, mas MÍNIMO e com AVISO** — nunca atualização automática por baixo do dono. Um `app/core/eventos.py` singleton com 4 sinais. O padrão já nasceu em `configuracoes.py:58` (`mudou = Signal()`), só não é global. Modelo mental: o painel **Links** do InDesign ("mudou lá fora — quer atualizar?") | M |
| **P5** | **Camada de projeção** Slot ↔ célula | **Sim, e é MENOR do que parece.** Não precisa de view-model: precisa de **um campo**, `Regiao.grupo: str\|None`. (1) `_irmas()` passa a ser "mesmo `grupo` não-nulo" — 3 linhas, **E-02 morre**; (2) `adicionar_regiao` cria com `grupo=None` — **E-01 morre sem tocar em slot**; (3) `agrupar_selecao` **carimba** um grupo em vez de **mover** regiões entre slots (hoje agrupar muda quem é `ocupavel()`, e isso é um **risco de I1 latente**); (4) migração de 1 passada: `grupo = slot.id` para todo slot com ≥2 regiões de conteúdo. **Nada em `compor_pagina`, `mapa`, `propagar_mestre`, I1 ou I4 muda.** Três eixos ortogonais, como o Illustrator faz com seleção/grupo/símbolo | M |
| **P6** | **Pipeline declarativo** de composição | **O monólito NÃO é `compor_pagina` — é a SAÍDA.** `compor_pagina` é coeso. O que está espalhado são as **10 portas de exportação**, cada uma remontando a receita (é a causa-raiz do F-01 e do F-03). Proposta: `app/rendering/producao.py` com `produzir(pedido) -> Resultado` e a lista de passos [montar dados → pré-voo → compor → RASCUNHO → CMYK → gravar]. `_compor_cartaz` (`servico.py:1787-1805`) **já é um pipeline de 3 passos** — falta generalizar | M |
| **P7** | **Esquema versionado** de verdade | **NÃO ressuscitar o Alembic.** Versão em `config.schema_versao` (a tabela chave-valor já existe, `models.py:363-388`) + lista ordenada `(versao, descrição, função)` em `app/core/migracoes_banco.py`, ~60 linhas, **com backup antes de migrar**. O `.atpkg` e o `.atproj` já travam `versao_schema`; só o banco vivo não | M |
| **P8** | **Modelo de receita** dos 7 encartes | **São DADOS, e o formato já existe.** `.attpl` (`template_compartilhavel.py:30-61`) já é o `LayoutDef` inteiro em JSON, sem dados do dono, com versão. Proposta `.atenc` = zip com `fundo.png` (o BASE 2160×2880) + `layout.attpl` + `manifesto.json` (nome, dia da semana, âncoras da validade). **Se cada encarte novo exigir código, o dono depende de programador para sempre — que é o oposto do produto** | M |

**Sete propostas minhas, que o briefing não listou:**

| # | proposta | por quê |
|---|---|---|
| **A1** | **`compor_pagina` PRESTA CONTAS**: devolver `(imagem, RelatorioComposicao)` com `faltou_imagem[]`, `texto_cortado[]`, `fundo_ausente`, `fundo_redimensionado` | **O I2 vira estrutural em vez de disciplinar.** R-06 e R-07 morrem juntos, e o truncamento com reticências (`text_fit.py:175-183`), que **já acontece e é descartado**, passa a existir |
| **A2** | **Prévia em DPI de rascunho** (96 dpi) enquanto edita; 300 dpi só no export | (96/300)² ≈ 10% dos pixels: os ~113 ms medidos caem para a casa de ~25 ms |
| **A3** | **Índice `uid → slot`** em vez de varredura linear com `__eq__` de dataclass | elimina o custo de hover/seleção em página cheia |
| **A4** | **Um engine de banco no processo** (matar 125 `Database().init()`) | 124 dos 125 `create_all`+`PRAGMA` desaparecem (X-11) |
| **A5** | **Sobrou item? Oferecer CRIAR A PÁGINA** | `duplicar_pagina_atual` (`canvas.py:278-296`) **já clona com ids e uids frescos**; o toast vira ação |
| **A6** | **Conferência célula a célula** com `list[Aviso(slot_id, texto, gravidade)]` em vez de `list[str]` | é o que destrava VC-021, VC-028 e VC-082 de uma vez |
| **A7** | **Uma tabela de campos para o `DadosProduto`** | **é a causa-raiz do F-01**: hoje há N receitas quase-iguais que divergiram. Uma `dados_de(fonte) -> DadosProduto` com os campos declarados **uma vez** |

**Ordem de ataque recomendada** (barato/alto retorno → caro):
**P6** (porta única de saída — impede a 5ª porta esquecida e já cobre F-01/F-03) → **A1**
(`compor_pagina` presta contas — I2 estrutural) → **P2 degraus 1-2 + A2** (devolve o "digitar"
ao dono) → **P7** (é o único item onde a falha custa **o acervo**) → **P5** (`Regiao.grupo` — a
raiz de 5 sintomas do dono) → **P3** (fila única + fim do véu) → **P8** (receita `.atenc`) →
**P4** (barramento discreto) → **P1** por último.

---

## §6 · Quadro de priorização (ganho × custo)

| | **custo P** | **custo M** | **custo G** |
|---|---|---|---|
| **ganho ALTO** | VC-003 VC-004 VC-005 VC-022 VC-023 VC-025 VC-029 VC-033 VC-037 VC-050 VC-056 VC-067 VC-073 VC-076 VC-080 · **A1 A5 A7** | VC-001 VC-020¹ VC-021 VC-036 VC-039 VC-051 VC-077 VC-078 VC-079 VC-081 · **P2 P3 P5 P6** | VC-020 |
| **ganho MÉDIO** | VC-002 VC-006 VC-008 VC-009 VC-013 VC-014 VC-024 VC-026 VC-027 VC-032 VC-035 VC-040 VC-041 VC-048 VC-052 VC-058 VC-060 VC-065 VC-066 VC-074 VC-075 VC-082 VC-085 · **A2 A3 A4** | VC-007 VC-010 VC-011 VC-012 VC-015 VC-016 VC-017 VC-028 VC-030 VC-031 VC-034 VC-042 VC-043 VC-044 VC-045 VC-047 VC-054 VC-055 VC-057 VC-059 VC-061 VC-063 VC-064 VC-068 VC-069 VC-070 VC-071 VC-072 VC-083 VC-084 VC-086 · **P4 P7 P8 A6** | VC-046 VC-062 |
| **ganho BAIXO** | VC-018 VC-019 VC-053 · **P1** | VC-087 | — |

¹ VC-020 (central de trabalhos) aparece nas duas colunas de propósito: **o passo 1 (trocar o
véu por um rodapé) é M e entrega quase todo o ganho**; a fila completa é G.

---

## §7 · O TIME DOS DEZ — as dez que, juntas, mais aproximam dos 5 minutos

Escolhidas por **minuto devolvido por unidade de esforço**, e não por elegância. As cinco
primeiras, sozinhas, tiram ~10 dos ~20 minutos.

| # | o quê | por que esta | tempo devolvido |
|---|---|---|---|
| **1** | **VC-020 passo 1 · o véu vira rodapé** (`carregando.py` + `workers.py:69-71`) | o rembg **já roda em thread**; é o véu que sequestra a tela. Um `WA_TransparentForMouseEvents` e uma barra no rodapé | **~4 min/edição** |
| **2** | **VC-081 · atualizar preços de uma oferta existente** (`chave_natural`, `servico.py:789`) | a semana dele é **recorrente**: mesma arte, preços novos. Hoje ele remonta tudo | **~6 min/edição recorrente** |
| **3** | **VC-005 + A2 · coalescer a digitação e compor a prévia em 96 dpi** | o ajuste fino de 30 células é o maior bloco humano da tabela; hoje cada tecla custa um `compor_pagina` de 113 ms | **~3 min/edição** |
| **4** | **VC-037 · detector de fundo branco LIGADO** (`fundo.py:88-105`, existe e está desligado) | metade das fotos de varejo já vem em fundo branco: 8 s → 0,3 s | **~1,5 min/edição** |
| **5** | **VC-023 + VC-079 · "Aprovar" com botão visível, e aprovação no cartaz** | hoje **toda** peça sai com RASCUNHO porque o botão só existe no Ctrl+K e a Fábrica não tem nenhum (P-05/P-06/P-07) | evita reimprimir o lote |
| **6** | **VC-024 + VC-025 · item ↔ célula acesos, e miniatura na estante** | transforma conferência em olhada. É o painel *Links* do InDesign, e o fio (`_ir_para_aviso`) já está escrito | **~5 min/edição** |
| **7** | **VC-050 + VC-040 · o piso da revisora e a nota da foto entram no PRÉ-VOO** | o app **já sabe** detectar nome cortado e foto ruim — só não pergunta na hora certa | evita reexportar/reimprimir |
| **8** | **VC-051 · categoria pelo vizinho mais próximo (piso sem IA)** | 0% → ~80% do acervo sem LM Studio; e é o que faz "agrupar por categoria" e as seções finalmente valerem | destrava C-01/C-05 |
| **9** | **VC-004 + VC-010 · Transform em mm e medida ao vivo no arrasto** | `_emitir_medidas` **já calcula X/Y/L/A em mm** e joga num rótulo. É a versão Adobe mais barata que existe aqui | **~5 min/tabloide** |
| **10** | **VC-033 + VC-022 · cabeçalho da oferta e barra de prontidão** | uma linha (`self._evento = evento`) ressuscita 3 funcionalidades prontas; e `checklist_final` já calcula tudo | resolve P-01/P-02 |

**Fora do time, mas o mais barato do caderno:** VC-067 (a Inteligência abrir com a edição
aberta) é **uma linha** e destrava uma tela inteira, construída e testada, que hoje mostra um
relatório permanentemente vazio.

---

## §8 · Vetos que eu questionaria (seção separada, como o briefing pediu)

Não misturei isto com as propostas. São **dois**, e ambos são de redação, não de mérito:

1. **"Sem camada industrial"** foi escrito contra o watchdog/RAG/resiliência do protótipo
   antigo, e está certíssimo. Mas hoje ele está sendo lido de forma larga demais e cobre coisas
   que são **higiene**, não indústria: (a) **backup do banco antes de migrar schema** (P7);
   (b) **um arquivo de log de erro** (`<raiz>/logs/erros.log`, CA-02) — sem ele, o programa
   instalado é impossível de socorrer. Sugiro tratar os dois como higiene e deixar o veto
   apontando para o que ele realmente quis barrar.
2. **"Sem módulo mobile/foto"** também está certo — mas note que o fluxo do dono **começa numa
   foto de WhatsApp**. Não estou propondo app mobile: estou registrando que, se um dia ele
   quiser arrastar a foto direto do celular para a Mesa, isso é *entrada de arquivo*, não
   "módulo mobile". Vale o dono saber que a fronteira está aí.

**E um veto que eu REFORÇO:** o Command completo do P1. O `Historico` atual é bom; trocar por
Command paga um custo alto para entregar o que um rótulo e uma coalescência entregam. Se
alguém propuser isso adiante, esta é a minha objeção registrada.

---

*Fim do caderno de visão. Nada aqui foi implementado — a Regra Zero desta fase é diagnóstico.*
*Os defeitos estão em `docs/VARREDURA_CODE_F13.md`.*

---
