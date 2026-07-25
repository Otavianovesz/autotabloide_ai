# ORDEM DE SERVIÇO F13 — RESGATE

> **Emitida pelo arquiteto (Cowork/Opus 5) em 25/07/2026.**
> **Executor: Fable 5.** O Otaviano dá o selo humano final.
> **Base:** `docs/DOSSIE_AUDITORIA_F13.md` (133 achados, arquiteto) +
> `docs/VARREDURA_CODE_F13.md` (123 achados, Opus 5 em Ultracode) +
> `docs/VISAO_CODE_F13.md` (87 sugestões + parecer de arquitetura).
> **256 achados, 41 🔴.** A fase de diagnóstico está FECHADA. Esta ordem constrói.

---

## §0 · Ritual de retomada (chat novo? comece exatamente aqui)

1. `CLAUDE.md` inteiro.
2. **Esta ordem**, na letra e na ordem dos blocos.
3. `docs/DOSSIE_AUDITORIA_F13.md` — leia o §0, o §1, o §14b e o **§14c** (a errata).
4. `docs/VARREDURA_CODE_F13.md` — leia o placar, a prova de mutação e as refutações.
5. `docs/VISAO_CODE_F13.md` — leia o §2 (fluxo hoje×ideal), o §5 (arquitetura) e o §7 (time dos dez).
6. `pytest app/tests -q` **da raiz do repositório**. Linha de base medida em 24/07:
   **851 passados, 0 falhas, 0 skips, exit 0.** Se não estiver assim, **PARE e reporte**.
7. Só então codifique.

---

## §1 · As leis desta fase (cada uma nasceu de um dado desta auditoria)

**L1 · VERMELHO ANTES DE VERDE. Sem exceção.**
Todo conserto entra em duas etapas: primeiro o teste que **falha** no código atual; depois
o conserto que o faz passar. Se você não conseguiu deixar o teste vermelho antes, você não
provou o bug — você escreveu um teste que já passava.
*Por quê:* das 6 linhas 🔴 que o Ultracode quebrou de propósito, **5 não deixaram nenhum
teste vermelho**. Tirar o preço da etiqueta em lote manteve 851 verdes. A suíte atual não
mede o programa.

**L2 · Gesto, não método.**
Teste de UI usa `QTest.mouseClick`/`keyClick` ou `QApplication.sendEvent`, e aciona a
`QAction`/o botão real com `.trigger()`/`.click()`. Chamar `canvas.duplicar_regiao(r)` **não
prova** que o menu funciona. Hoje a suíte tem 0 `QTest`, 0 `.trigger()`, 0 `dropEvent`.

**L3 · Conteúdo, nunca ausência de exceção.**
Asserção de render confere pixel/byte. `assert x is not None` não é teste.

**L4 · Nada de degradação silenciosa (I2).** Ferido **47×** na varredura do Ultracode — é a
doença crônica deste código. Toda vez que você tocar num `except: pass`, num `continue` que
pula conteúdo, ou num caminho que perde dado, **o dono precisa ver**.

**L5 · Identidade, nunca posição (I1).** Vale para tudo que você tocar.

**L6 · Honestidade de bancada.** Bug seu achado pelos seus testes vai **na resposta**, nunca
escondido. Se discordar de um achado dos dossiês, diga com `arquivo:linha` — o arquiteto já
teve três achados derrubados assim (§14c do dossiê), e isso melhorou o trabalho.

**L7 · PARE no fim de cada bloco.** Atualize `docs/PLANO_DE_CONSTRUCAO.md`, responda com "o
que ficou de fora", e **não comece o bloco seguinte** sem o selo do arquiteto.

**L8 · Não invente escopo.** Sugestão do caderno de visão só entra no bloco em que esta
ordem a cita. Ideia nova sua: anote no fim da sua resposta, não construa.

---

## §2 · As três travas que o dono DERRUBOU (autorização de 24/07/2026)

Registre as três no `CLAUDE.md` como decisões novas, junto com a data e o motivo:

1. **Marca d'água RASCUNHO deixa de ser lei.** Exportar sai **limpo por padrão**. RASCUNHO
   passa a ser opção explícita do dono (botão/atalho), disponível em todas as portas.
   *Motivo:* eram 9 portas carimbando, a aprovação era inalcançável (P-05/P-06) e a Fábrica
   não tinha nenhum caminho de aprovar (P-07) — todo cartaz de gôndola estava preso.
2. **Trio da célula (RG-15) cai.** Clique seleciona **só a peça clicada**. Mover a célula
   inteira passa a ter gesto próprio (borda/Alt/laço), a definir no Bloco C.
3. **Pré-voo da validade deixa de bloquear.** A validade se autopreenche pela campanha/evento
   e o pré-voo só avisa.

> **Atenção:** derrubar a #2 sem resolver a causa (E-01: região nova herda o slot da anterior)
> troca um sintoma por outro. As duas andam juntas no Bloco C.

---

## BLOCO A · A BANCADA QUE ENXERGA GESTO  🔴 pré-requisito

**Por quê:** é o único bloco que, se faltar, invalida todos os outros. Enquanto 5 de 6
mutações críticas passam despercebidas, "suíte verde" não significa "consertado".

**O que entra:**
- A1. Fixture de gesto: helpers `clicar(item)`, `arrastar(de, para)`, `teclar(w, key)`,
  `acionar(acao)` sobre `QTest`/`sendEvent`. Todo teste novo desta ordem usa isso.
- A2. Uma suíte **com janela real** (sem `QT_QPA_PLATFORM=offscreen`), rodada antes de cada
  selo. Ela pode ser pequena — precisa existir. (T-01)
- A3. Fixture *autouse* que instala `instalar_vida` + `instalar_polimento` na suíte visual.
  Hoje: 0 instalações. (T-02)
- A4. `confirmar_pre_voo` e `confirmar_destrutivo` testados **pelo clique no botão real**,
  nunca por monkeypatch. (T-03, CF-01)
- A5. Consertar o `skipif` de `arte/quintou` — hoje depende do CWD e `arte/` está no
  `.gitignore`: **nenhum clone reproduz a prova da arte real**. Decida com o arquiteto entre
  versionar uma arte mínima de bancada ou marcar o teste como "requer arte do dono" de forma
  explícita e contada no relatório. Skip silencioso não é verde. (T-08 + a correção do Ultracode)
- A6. Teste de ordem: a suíte tem de passar em ordem invertida. Hoje **2 vermelhos** por
  estado vivo em `animacoes.py`.

**Definição de pronto:** as 6 mutações do §1.4 da varredura, reaplicadas uma a uma, deixam
**cada uma** ao menos um teste vermelho. Reporte a tabela `achado × teste que pega`.
**Não conserte nenhum dos 6 neste bloco** — só faça a bancada vê-los.

**PARE.**

---

## BLOCO B · AS HEMORRAGIAS  🔴 perda de trabalho, de dado, ou peça errada publicada

**Por quê:** são os achados em que o dono perde algo que não volta.

| # | Achado | Onde |
|---|---|---|
| B1 | **Editar preço/nome apaga a pilha de desfazer** (os 9 Ctrl+Z da gravação) | `canvas.py:210` cria `Historico()` dentro de `carregar()`; `mesa.py:2209→2344`. A lição já existe escrita em `mesa.py:443` — aplique-a nos sete métodos que a esqueceram. CD-01 |
| B2 | **A tela escurece e não volta** — **reproduzido ao vivo em 3 cliques** (Início → Ctrl+K → Esc → Mesa), sobrevive 6 trocas de tela | `animacoes.py:287` — o `destroyed` remove do dicionário e não destrói o véu. Troque `id()` por `QPointer`/parent no próprio diálogo, destrua no `destroyed`, trate Resize, e varra `findChildren(QWidget,"veuDialogo")` órfão ao trocar de tela. V-01..05, **L-01** |
| **B2b** | **São DOIS resíduos, não um.** O `crossfade` (`animacoes.py:318-371`) morre pela metade quando um `QMessageBox` modal abre durante a transição — a foto da tela antiga fica semi-transparente por cima (costura visível em x≈1237) — **e a paleta `Ctrl+K` fica órfã junto**, desenhada sobre 3 telas seguidas depois do Esc. Consertar só `_entrada_dialogo` **não resolve**. | **L-02, L-10** |
| **B2c** | **Os 17 `QMessageBox` estáticos falam INGLÊS** ("Yes"/"No") num app cuja lei é PT-BR — nenhum tradutor Qt é instalado. Visto na tela em "Recuperar rascunho?". | **L-03** |
| **B2d** | **No diálogo de recuperação, o X e o Esc APAGAM o rascunho** (`mesa.py:1362-1364`: tudo que não é `Yes` cai em `descartar_rascunhos()`). Não existe "depois eu vejo", e nada avisa. | **L-05** |
| **B2e** | **Sair do editor com alterações não salvas não pergunta nada** — título com "•", clique em "Biblioteca", volta em silêncio. 20 min de layout somem num clique errado de navegação. Viola I2. | **L-09** |
| B3 | **Enter na caixa "não tem volta" apaga** | `componentes.py:171-178` — sem `setDefaultButton(Cancelar)` nem `setEscapeButton`. 13 pontos de chamada. CF-01 |
| B4 | **A foto original é apagada na 11ª troca** | fere a trava da F10 ("original sempre preservada"). CI-05 |
| B5 | **O snapshot do boot copia o banco corrompido** e a rotação empurra os bons para fora | CB-01 |
| B6 | **Etiqueta em lote sai sem selo +18 em bebida alcoólica**, e o pré-voo não pega | `servico.py:1860` não passa `mais18`; o pré-voo olha outro dict. Unifique as duas receitas (`fabrica.py:593-601` vs `servico.py:1760-1784`) numa só — a divergência **é** a causa. F-01 |
| B7 | **O juiz IA pinta VERDE com confiança 0,05** | `conciliacao.py:378` lê `conf` e nunca compara; os limiares (`:420,425`) usam o score fuzzy. Fere a trava da F9. CI-03 |
| B8 | **A revisora pede nomes ao modelo de visão e os descarta** — preço trocado, a coisa que ela existe para pegar, passa limpo | CI-02 |
| B9 | **Purga do boot pode abortar inteira** por `IntegrityError` num FK sem `ondelete` | `models.py:288`, `lixeira.py:119-142`. D-06 |
| B10 | Os dois **hard-deletes públicos e testados** sem chamador (minas latentes) | `persistencia.py:214-218`, `repositories.py:179-183`. D-07 |

**Definição de pronto:** cada um com teste que ficou vermelho antes (L1), **mais as três
condições do §4.3 e o critério do §4.5**:

1. `mut1` cresce a asserção de que o **véu saiu da tela** (`findChild("veuDialogo")` ausente
   ou invisível) — hoje vermelha (COND-1).
2. Nasce um teste que reproduz o caminho **real** do §19: modal estático abrindo **durante o
   crossfade**, e a janela volta ao brilho normal depois (COND-2).
3. `pytest app/tests -q --ordem-invertida` sai **verde** (§4.5).
4. Os três testes de caracterização **não são tocados neste bloco** — eles invertem no C
   (COND-3).

**PARE.**

---

## BLOCO C · O EDITOR PARA DE BRIGAR  🔴

**Por quê:** é a tela onde ele desistiu. E é onde a trava #2 cai.

| # | Achado | Onde |
|---|---|---|
| C1 | **Região nova herda o slot da anterior** — a causa do "tudo grudado" | `canvas.py:1396-1397` auto-seleciona + `:1353-1357` usa o slot da seleção. E-01 |
| C2 | **Derrubar o trio (RG-15):** clique = só a peça. Definir e implementar o gesto novo de "mover a célula inteira" | `itens.py:324-373`, `:309-315`. E-02 |
| C3 | **Subir/Descer camada estão INVERTIDOS** — é por isso que "a imagem atrás do preço" nunca aconteceu | `painel_camadas.py:66-72`. **Some região nova nasce no fim da lista** (= na frente): decida a ordem de nascimento junto. R-02 |
| C4 | **Alinhamento vertical de texto não existe no modelo** — campo novo + `_y_alinhado` + combo | `model.py:64-68`, `compositor.py:312`. R-01 |
| C5 | **Rotacionar desliga o redimensionar** e a alternativa prometida não existe | `itens.py:438`; não há Largura/Altura em `painel_propriedades.py`. Conserte a conta do resize (usa `scenePos` cru, válido só em rotação 0) **ou** entregue os campos em mm. E-08 |
| C6 | **Duplicar duplica a peça, não a célula** — a UI destaca o trio e o comando ignora | `canvas.py:1937-1959`, `itens.py:512`. E-03 |
| C7 | **Carimbar modelo funciona e é invisível**: nasce do tamanho da página e não seleciona nada | `canvas.py:1571-1593` vs `:1396-1397`. E-04 |
| C8 | **"Novo layout" nasce com lixo**: detector de caixa por cor puro, sem área mínima nem proporção, sem revisão antes de salvar | `grade.py:201-219`, `atelie.py:212-242`. E-06/E-07 |
| C9 | **Agrupar recusa em bloco sem explicar**, e não confirma quando dá certo | `canvas.py:652-694`. E-05 |
| C10 | **`Ajuste.PREENCHER` vaza da célula no caminho rápido** (o padrão) | `compositor.py:252-258` não recorta para a região. R-03 |
| C11 | **Selos: existe âncora, não existe controle** — e o produto de exemplo do Ateliê nunca tem `mais18`, então nenhum selo aparece na prévia mesmo fazendo tudo certo | `atelie.py:54-55`, `painel_propriedades.py:487-505`. E-09/E-10 |
| C12 | **A mestra não propaga o texto** (`texto_fixo` fora de `ATRIBUTOS_ESTILO`) — a "tag inteligente que não funciona" | `grade.py:40-50`. E-11 |
| C13 | **Ctrl+K morto na Mesa** (dois donos ⇒ ambíguo), com teste verde que nunca aperta a tecla | `mesa.py:697` + `editor_app.py:322`. CF-02 |

**Do caderno de visão, autorizado neste bloco:** VC-004 + VC-010 (Transform em mm e medida
ao vivo — `_emitir_medidas` **já calcula e joga fora**) e VC-014 (guias com medida no arrasto).

**Definição de pronto:** um teste de gesto que reproduz a sequência da gravação — criar
IMAGEM, criar TEXTO, criar PREÇO, arrastar cada uma — e prova por conteúdo que **as três são
independentes**; mais o adversarial I1–I5 atualizado e verde.

**PARE.**

---

## BLOCO D · O DIA DE 5 MINUTOS  🟠

**Por quê:** é a promessa do produto. Hoje: 18–22 min. Meta: 6–8 min.

| # | O quê | Fonte |
|---|---|---|
| D1 | **O véu vira rodapé** — o rembg já roda em thread; é o overlay que sequestra a tela | I-01, VC-020 passo 1. **~4 min** |
| D2 | **Coalescer a digitação + prévia em 96 dpi** — hoje cada tecla custa um `compor_pagina` | X-01, VC-005+A2. **~3 min** |
| D3 | **Ligar o detector de fundo branco que já existe desligado** (`fundo.py:88-105`) — 8 s → 0,3 s | VC-037. **~1,5 min** |
| D4 | **Categoria pelo vizinho mais próximo, sem IA** — 0% → ~80%; destrava "agrupar por categoria" e as seções | C-01/C-03/C-05, VC-051 |
| D5 | **A categorização passa a valer para item já cadastrado** (hoje só o vermelho) | `servico.py:1635`. C-01 |
| D6 | **A sanitização para de apagar palavra**, e o aviso chega nos 2 caminhos onde hoje se perde | `enriquecimento.py:144-151`; `conciliacao_dialog.py:465-478` e `:562-596`. C-08/C-09 |
| D7 | **Validade automática pela campanha/evento** + o cabeçalho da oferta (uma linha ressuscita 3 funções) | P-01..P-04, VC-033. **Aqui cai a trava #3** |
| D8 | **"Aprovar" com botão visível + aprovação na Fábrica**; e **derrubar a trava #1** — exportar limpo por padrão, RASCUNHO como opção | P-05..P-08, VC-023+VC-079 |
| D9 | **Item ↔ célula acesos + miniatura na estante** (o painel *Links* do InDesign; o fio já existe) | VC-024+VC-025. **~5 min** |
| D10 | **O piso da revisora e a nota da foto entram no pré-voo** — o app já sabe detectar e não pergunta na hora certa | VC-050+VC-040 |
| D11 | **Auto-preencher deixa de ser `zip` posicional**: destaque por **área do slot**, não só por preço | C-06/C-07, N-choque-2 |
| D12 | **Atualizar preços de uma oferta existente por chave natural** — a semana dele é recorrente | VC-081. **~6 min/edição recorrente** |
| D13 | **Diálogo de conciliação lembra geometria e largura de coluna** (o padrão `splitter_com_memoria` já existe ao lado) | C-10 |
| D14 | **Rascunho automático para de oferecer recuperação de projeto pronto** | `mesa.py:1324-1338`. P-10 |

**Definição de pronto:** refaça o quadro "hoje × ideal" do §2 do caderno de visão com
medições suas, **na máquina real, com as 30 ofertas reais do Quintou**. Número medido, não estimado.

**PARE.**

---

## BLOCO E · CONFIABILIDADE E PRIMEIRA EXECUÇÃO  🟠

| # | O quê | Fonte |
|---|---|---|
| E1 | **O boot para de baixar 973 MB sem pedir.** Modelo sob demanda, com pergunta, progresso e opção leve. E o `GUIA_RAPIDO` para de prometer o contrário | `editor_app.py:450-466`. CA-01 |
| E2 | **Log de erro no exe** (`console=False` ⇒ sem `stdout`; o "diagnóstico para suporte" sai sem traceback). Higiene, não camada industrial | CA-02 |
| E3 | **Pasta sem permissão de escrita** para de matar o boot antes da janela (`sqlite3.OperationalError` escapa) | CA-03 |
| E4 | **Cofre e `.atpkg` param de escrever em modo somente-leitura**, e o mapa de portas em `modo.py` para de se declarar completo | CB-02 |
| E5 | **Os 47 I2** — varredura sistemática: todo lugar que perde conteúdo em silêncio passa a relatar | dossiê + varredura |
| E6 | **Caminho absoluto (I3)** nos 4 pontos restantes, e o equivalente de `migrar_artes_absolutas` para `Produto.caminho_imagem` | D-02 |
| E7 | **Versão de schema** e backup antes de migrar (alembic está morto) | D-11, P7 do parecer |
| E8 | **As 3 conexões `sqlite3` cruas** que não passam pelo hook do `PRAGMA foreign_keys` — justamente as de backup/migração | D-12 |
| E9 | **Índices** em `excluido_em` das 3 tabelas e em `Layout.nome` | D-10 |

**PARE.**

---

## BLOCO F · OS 7 ENCARTES NOVOS  🟠

**Por quê:** é o que ele quer usar amanhã. E depende do Bloco C (rotação, propagação, seções).

- F1. **Célula FIXA** no modelo — não existe hoje; Terça (2), Segunda (1), Quarta (3) precisam.
  *Lei do projeto: todo tipo novo de slot reavalia "ocupável" **e** o pré-voo.*
- F2. **Extrator de geometria** dos geradores → `LayoutDef` (as 8 tabelas do §13 do dossiê).
  O Jornal precisa de caminho próprio: **0 `id="celula-N"`**, e o BASE zera o exemplo inteiro.
- F3. **Destaque por área do slot** (vem do D11).
- F4. **"Fica a Dica"** como região de texto que a mestra propaga (vem do C12).
- F5. **Seções por categoria desenhadas pelo app** — o pacote não traz seção na arte (N-05).
- F6. **Validade em posição rotacionada**, por encarte (as 7 coordenadas do §13 N-06).
- F7. **Oclusão da Terça**: o selo de 25% invade ~12×60 px do 1º slot (N-01).
- F8. **Correções factuais de arte** — mapa exato, conferido string por string no pacote
  (25/07). **Duas surpresas: uma correção que ele pediu não é necessária, e outra é em dobro.**

  | O quê | Onde EXATAMENTE | Nota |
  |---|---|---|
  | ~~CENEPOL→SENEPOL~~ | **não fazer nada** | **Já está SENEPOL.** `gen_carne_final.py:110` + as 3 artes do Sábado. Grep por `CENEPOL` no pacote: **vazio**. Ele lembrou de uma versão anterior — "corrigir" aqui estragaria o que está certo. |
  | "CRIADA E PRODUZIDA" → "CRIADO E PRODUZIDO" | `gen_carne_final.py:110` **e** `gen_segunda3.py:227` | **São DOIS encartes**, não um. Ele só citou a Segunda; o Sábado tem a mesma frase. |
  | remover "MARCA PRÓPRIA" | `gen_carne_final.py:110`, dentro do `<g id="marca-propria">` (a faixa vermelha fixa) | **CUIDADO:** "marca própria"/"m. própria" também aparece nos **subtítulos de exemplo** de 4 itens (`:126` e vizinhas, `'senepol · marca própria · 100 g'`). Esses são dados que o app substitui — **não** mexer neles. Remover só da faixa fixa. |
  | rever "queijos & frios fatiados na hora" | `gen_segunda3.py:171` (subtítulo do cabeçalho) | **Só esta linha.** `:318` é `'fatiado na hora · 100 g'` no subtítulo do Presunto — dado de exemplo e verdadeiro; deixar. A queixa é o genérico que promete o que não vale para todos. |
  | "mês inteiro" → período editável (1 ao 27) | `gen_jornal_final.py:137` (`'mês inteiro de'`, orelha "O TEMPO:") **e** o `MÊS INTEIRO` em caixa alta presente em `jornal-p1` **e** `jornal-p2` | Duas páginas, dois lugares por página. O período tem de virar campo que o app escreve. |
  | logo por caminho absoluto | topo dos 7 geradores (`/home/claude/encartes/brand/logo_semfundo.png`) | N-08. Vira relativo antes de qualquer regeração. |

  *Ficou para depois, por decisão dele: subir a cesta na Sexta e recomposições visuais.*
- F9. **"20%" hardcoded** no gerador da Quarta → parâmetro, compatível com o % calculado (N-02).
- F10. **"Pão de Queijo" em Baloo 2 com "ã"** — o glifo é defeituoso nessa instância (N-03).

**Definição de pronto:** os 7 encartes montados no app com as ofertas reais dele, conferidos
por pixel contra os PREVIEW, e **inspecionados visualmente** — nada de selo só com a suíte verde.

**PARE.**

---

## BLOCO G · QUALIDADE DE VIDA  🟡

O resto do caderno de visão, na ordem do quadro ganho×custo (§6). Começa pelo mais barato
que destrava mais: **VC-067 — a Inteligência abrir com a edição aberta é uma linha** e
ressuscita uma tela inteira, construída e testada, que hoje mostra relatório vazio.
Inclui o §12 do dossiê (as 20 fricções de descoberta: jargão na tela, atalhos que mentem,
feedback ausente, estados vazios) e os 91 "enquanto você está aí" do §3 do caderno.

**Fica FORA desta ordem** (registrado, não construído): o padrão Command completo — o próprio
Ultracode registrou objeção, e o arquiteto concorda: `Historico` + coalescência + rótulo
entregam o ganho por uma fração do custo.

---

## BLOCO H · O MARCO DE VERDADE — porta de saída de toda a ordem  🔴

**Por quê:** a terceira onda da auditoria (§17 do dossiê) abriu os arquivos que o programa já
produziu e achou que **o artefato que selou a Versão 1.0 não tem uma única foto de produto**,
tem validade de **maio** num tabloide de julho, teve **acerto de conciliação zero** (30
vermelhos em 5.000 produtos), duas campanhas **faltando**, e um `RELATORIO.txt` que descreve
uma validade que o PNG não contém. Os orçamentos do marco mediram **tempo e bytes, nunca
conteúdo**. A lei do dono — *"selo só com inspeção visual de TODOS os artefatos"* — foi
escrita e não cumprida.

**Portanto: a Versão 1.0 não é 1.0.** Reexecutar o marco é a última coisa desta ordem, e o
critério muda:

- H1. **Orçamento de ACERTO, não só de tempo.** A conciliação de 30 itens reais contra o
  acervo real tem de reportar 🟢/🟡/🔴 e o marco **falha** se os verdes forem zero.
- H2. **O pré-voo tem de pegar**, antes do export: célula sem foto, validade fora do mês
  corrente, nome com hifenização suspeita, unidade em maiúscula, nome sobreposto ao preço.
  Hoje ele devolveu `"avisos_pre_voo": []` para uma peça com todos esses defeitos.
- H3. **Inspeção visual página por página**, com as imagens no relatório e uma frase por
  página dizendo o que foi conferido. Sem isso, não há selo.
- H4. **Uma pasta por run, com data no nome.** `saida_marco/` hoje mistura 18/07 e 21/07 e
  carrega um `quintou_p3.png` órfão de um run de 3 páginas — apresentado como uma galeria só.
- H5. **Relatório gerado a partir do artefato**, nunca escrito à parte: se o rodapé diz
  "quando durarem os estoques", o relatório não pode afirmar "VÁLIDA DE 18/07 ATÉ 24/07".
- H6. **Todas as campanhas ou nenhuma.** `campanhas_faltantes` não vazio ⇒ marco reprovado.
- H7. Os 11 defeitos M-01..M-11 conferidos um a um no artefato novo.

**Definição de pronto:** o Otaviano olha as páginas e diz "é isso que eu publicaria".
Esse é o único selo que conta.

---

## §4 · SELO DO BLOCO A — reauditoria do arquiteto (25/07/2026)

Lido no disco real (não no relatório do builder). **BLOCO A SELADO.** Pode começar o B com
as três condições do §4.3.

### 4.1 · O que eu confirmei, lendo a fonte

| Alegação | Verificado |
|---|---|
| Nenhum dos 6 bugs foi consertado | `git diff --stat -- app/ ':!app/tests*'` devolve **só** `editor_app.py`. `animacoes.py`, `canvas.py`, `painel_camadas.py`, `itens.py`, `servico.py`, `compositor.py` **intocados**. A ordem foi respeitada. |
| A1 usa gesto real | `gestos.py` usa `QTest.mouseClick`/`keyClick`, `.trigger()`/`.click()`, e `sendEvent` com movimentos intermediários no arraste. O detalhe de que `QTest.mouseMove` mexe no cursor da máquina e `sendEvent` não mostra que a escolha foi pensada. E `clicar`/`acionar` **recusam** alvo desabilitado — "desabilitado não é gesto, é trapaça". Aprovado. |
| A2/A3 janela real | `tests_janela/conftest.py:19` faz `os.environ.pop("QT_QPA_PLATFORM")` **antes** do Qt subir (a ordem importa e está certa), e `:29-33` instala `instalar_vida`+`instalar_polimento` como autouse. Real. |
| A5 skip contado e estampado | `conftest.py:32-35` estampa `ACERVO DO DONO AUSENTE` com `red=True, bold=True`; `acervo.py:25` define o prefixo `REQUER ACERVO DO DONO`. O skip silencioso morreu de fato. |
| mut5 (F-01) verifica CONTEÚDO | Atravessa a porta pública inteira (`gerar_etiquetas_lote` → compor → impor → PDF no disco), extrai os **bytes da imagem embutida** com pypdf e compara com preço × sem preço. É o padrão-ouro deste arquivo. |
| mut6 (R-01) verifica PIXEL | Limiariza, pega a bbox da tinta e afere folga de topo × base. Correto. E a nota está certa: centralizar é o único comportamento que existe; o C4 acrescenta o campo, não muda o padrão são. |

### 4.2 · Correção na sua honestidade de bancada (L6)

Você declarou: *"o boot morria com `FileNotFoundError` antes da janela quando rodado de outra
pasta"*. **Overstated.** `montar_editor()` é alcançado só por `montar_janela()`
(`editor_app.py:338`), e `montar_janela` é chamado **apenas por 4 scripts** de bancada —
`fotografar_telas.py`, `gif_fase1.py`, `perfil_cpu_fase1.py`, `screenshots_design.py`.
**`main()` não passa por lá** (usa as duas fases). Quem morria eram os scripts de foto/GIF,
não o boot do dono.

Isso **não invalida** a edição — ela está correta e é a mesma lição do método irmão. Muda o
julgamento: como é caminho de bancada, o `except Exception:` largo que degrada para
`_grade_sintetica()` **sem aviso** é tolerável. **Se algum dia esse caminho virar caminho de
usuário, ele precisa de aviso** (I2). Deixe o comentário dizendo isso.

Declaração corrigida para o registro: *"os 4 scripts de bancada morriam; o boot do dono não."*

### 4.3 · As três condições que entram no Bloco B

**COND-1 · mut1 não prova o que precisa provar — e você já disse isso.** O teste afirma só que
a entrada sai de `_veus`; **nunca que o véu saiu da tela**. Tanto o código bugado quanto um
conserto correto passam. O B2 tem de fazer o teste crescer a segunda asserção —
`pai.findChild(QWidget, "veuDialogo")` ausente ou invisível — que **hoje é vermelha**. Enquanto
ela não existir, o B2 não fecha.

**COND-2 · mut1 fabrica o caminho de falha em vez de reproduzir o real.** Ele faz
`removeEventFilter` para isolar a linha 287 — legítimo como vigia de mutação, e você foi honesto
ao escrever "o belt sai para provar o suspender". Mas o caminho **real**, que eu reproduzi na
mão em 3 cliques (§19, L-01/L-02), tem o filtro **instalado**: um `QMessageBox` estático abrindo
**durante o crossfade**, o `exec()` travando o laço, a animação morrendo pela metade. O B2 tem
de ganhar um teste que reproduza **essa** sequência — Início → paleta → trocar de tela com
modal no meio — e provar que a janela volta ao brilho normal. **Sem isso, consertamos a linha e
não o defeito.**

**COND-3 · os três testes de caracterização precisam de contrato, não só de docstring.**
`test_mut2_e01_*`, `test_mut3_r02_*` e `test_mut4_e08_*` **afirmam o bug**. Isso é correto no
Bloco A e é uma armadilha depois: quando o C1/C3/C5 consertarem, os três ficam vermelhos, e o
reflexo errado é "consertar o teste". Contrato, agora normativo:

> **Os três invertem, nunca desaparecem.** O passo C1 inverte o `test_mut2`; o C3 inverte o
> `test_mut3`; o C5 inverte o `test_mut4`. "Inverter" = a asserção passa a exigir o
> comportamento CERTO, com o `git log` mostrando a linha antiga. Apagar ou marcar `xfail`
> qualquer um dos três **reprova o bloco**.

### 4.4 · O que eu NÃO pude verificar

Não rodei a suíte: este sandbox não tem PySide6 (falta `libEGL`, sem root para instalar).
**Os placares 862×2 / 0 skips / exit 0, o vermelho de outra pasta e o vermelho da ordem
invertida ficam por sua conta** — e não há junit novo no repositório para eu conferir (os
`.xml` da raiz são todos de 21/07). Sob o nosso protocolo isso é aceitável: a máquina real é
a sua bancada. Registro para ninguém confundir depois: **eu selei o desenho e o código dos
testes, não o placar.** Se quiser fechar essa lacuna, deixe o junit do bloco em
`saida_f13/` que eu confiro na próxima reauditoria.

### 4.5 · Ruling sobre a ordem invertida vermelha

Você deixou os 2 vermelhos de `animacoes.py` de propósito e não limpou o estado na bancada.
**Concordo, e promovo isso a critério.** Limpar seria exatamente o que a lei do projeto proíbe
("teste que precisa de filtro próprio para passar = mascaramento"). O teste que falha **é** a
especificação:

> **Critério de pronto do B2, acrescentado:** `pytest app/tests -q --ordem-invertida` sai
> **verde**. Enquanto `animacoes.py` guardar estado vivo entre testes, ele fica vermelho — e
> deve ficar.

---

## §3 · O que esta ordem NÃO resolve

- O `.exe` nunca foi executado (a Regra Zero do diagnóstico proibia escrita): CA-01/02/03
  descrevem o que o código **fará**, não o que foi observado rodando. **O Bloco E precisa de
  uma execução real em Windows limpo** — e isso é lição de casa do Otaviano.
- Prova de mutação existe só para 6 dos 41 🔴. Os outros 35 ganham a sua no bloco em que entrarem.
- Corte de texto em Windows real não foi medido (bancada offscreen, fonte substituta).
- Máquina com GPU (revisora F9 com visão, SDXL do degrau 2 da F10) segue sem teste.

---

*A fase de diagnóstico está fechada. Esta ordem é a pauta do builder até o dono dizer o contrário.*

---

## RESPOSTA DO BUILDER — BLOCO A (Fable 5, 25/07/2026)

**§0 cumprido na ordem:** CLAUDE.md → esta ordem → dossiê (§0/§1/§14b/§14c) →
varredura (placar/prova de mutação/refutações) → visão (§2/§5/§7) →
`pytest app/tests -q` da raiz ANTES de tocar em qualquer coisa:
**851 passados, 0 falhas, 0 skips, exit 0** (junit).

### O que entrou

- **A1 · `app/tests/gestos.py`** — a fixture de gesto: `clicar`
  (QTest.mouseClick), `teclar` (keyClick), `acionar` (QAction.trigger/click;
  recusa acionar o desabilitado), `arrastar` (press/move/release por
  QMouseEvent + `QApplication.sendEvent` — QTest.mouseMove mexe no cursor da
  máquina), `clicar_na_cena`/`arrastar_na_cena` (QGraphicsView, pontos em cena),
  `botao_por_texto`/`botao_por_tooltip` (a barra do editor não dá objectName aos
  botões) e **`vigia_dialogo`** — responde o próximo diálogo modal por CLIQUE
  REAL dentro do laço de eventos do próprio `exec()`, registrando
  título/botões/foco/botão-padrão.
- **A2 · `app/tests_janela/`** — suíte com janela REAL (o conftest desfaz o
  offscreen herdado do ambiente). 4 testes: plataforma ≠ offscreen; vida
  instalada de verdade; clique real na barra cria região (com compositing);
  véu do diálogo nasce e some no ciclo NORMAL (o ciclo anormal — morrer sem
  Hide — é o B2). Roda antes de cada selo: `pytest app/tests_janela -q`.
  **4 verdes na máquina real.**
- **A3** — `instalar_vida` + `instalar_polimento` AUTOUSE no conftest de
  `app/tests_janela`. Na suíte offscreen, a fixture `vida` de
  `test_bancada_gesto_f13.py` instala/desinstala por teste (fora dele a bancada
  segue determinística, como o docstring de `instalar_vida` promete).
- **A4 · `app/tests/test_dialogos_reais_f13.py`** — 5 testes;
  `confirmar_destrutivo` e `confirmar_pre_voo` rodam o QMessageBox REAL e são
  respondidos por clique de gesto; sem avisos, o pré-voo não abre diálogo (o
  vigia prova a ausência). Zero monkeypatch. O default do Enter (CF-01) NÃO foi
  tocado — é o B3.
- **A5 · `app/tests/acervo.py` + conftest + 19 arquivos de teste** — decisão
  implementada: **"requer arte do dono" explícito e CONTADO** (não versionei
  arte — ver "decisões que ficam com o arquiteto"). Caminhos ancorados na raiz
  do repositório via `__file__`; os 4 skipif de `arte/quintou` usam
  `acervo.requer_arte_quintou`; a arte do Belo Brasil (`Frente Template.png`)
  ganhou marker próprio nos 3 testes que a usam; o padrão de copiar fontes
  reais (13 arquivos) virou `acervo.copiar_fontes_reais` — fontes ausentes =
  skip nominal "REQUER ACERVO DO DONO", nunca mais a fonte embutida do Pillow
  em silêncio (§1.5 da varredura); `pytest_terminal_summary` ESTAMPA a faixa
  "ACERVO DO DONO AUSENTE" com a contagem. O `pytest.fail` do test_onda1 foi
  unificado na mesma lei.
- **A6 · flag `--ordem-invertida`** no conftest de `app/tests` — inverte os
  ITENS coletados (mais agressiva que inverter arquivos).

### Definição de pronto — a tabela achado × teste

Método: cada mutação aplicada ISOLADA na linha citada, suíte rodada, árvore
restaurada com `git checkout --` e `git diff --quiet` conferido limpo.

| # | mutação (§1.4 da varredura) | teste que ficou VERMELHO |
|---|---|---|
| 1 | V-01 · remover o `destroyed.connect(…_veus.pop…)` (`animacoes.py:287`) | `test_mut1_v01_destroyed_limpa_o_registro_do_veu` |
| 2 | E-01 · `setSelected(it.regiao is reg)` → `setSelected(False)` (`canvas.py:1397`) | `test_mut2_e01_botao_da_barra_cria_regiao_e_ela_nasce_selecionada` |
| 3 | R-02 · trocar os deltas Subir/Descer (`painel_camadas.py:71-72`) | `test_mut3_r02_botao_subir_mexe_o_indice_para_tras_caracterizacao` |
| 4 | E-08 · remover a guarda de rotação (`itens.py:438`) | `test_mut4_e08_arrastar_alca_de_regiao_rotacionada_nao_redimensiona` |
| 5 | F-01 · tirar o PREÇO do dict da etiqueta em lote (`servico.py:1861`) | `test_mut5_f01_etiqueta_em_lote_desenha_o_preco_no_pdf` |
| 6 | R-01 · `oy = y + max(0,(rh-total_h)//2)` → `oy = y` (`compositor.py:312`) | `test_mut6_r01_texto_centralizado_na_vertical_por_pixel` |

Como os vigias enxergam: nº 2/3/4 são GESTO puro (clique real no botão da
barra, na linha do painel e no botão " Subir"; arraste real na alça pelo
viewport); nº 5 é conteúdo pela porta pública INTEIRA (dois PDFs gravados no
disco; a imagem embutida, extraída por pypdf, tem de DIFERIR com/sem preço);
nº 6 é pixel (folga de topo da tinta na caixa); nº 1 isola a linha removendo o
filtro antes da destruição — o caminho real do vazamento L-01, em que o Hide
NÃO passa pelo filtro.

**Honestidade de bancada (L6): os vigias nº 2, 3 e 4 são testes de
CARACTERIZAÇÃO — fixam o comportamento ATUAL, que é o próprio bug** (E-01
auto-seleção, R-02 invertido, E-08 rotação sem resize). Estão nomeados e
documentados assim, de propósito: o Bloco A não conserta os 6, só faz a
bancada vê-los. Quando C1/C3/C5 consertarem, cada um flipa junto (vermelho
antes, verde depois).

### Os placares (junit, máquina real, 25/07)

| prova | ANTES (reproduzido por mim) | DEPOIS |
|---|---|---|
| suíte da raiz | 851/0/0 | **862 verdes ×2, 0 falhas, 0 skips, exit 0** |
| de OUTRA pasta | **10 vermelhos + 8 pulados** (a mesma lista da varredura) | **862/0/0, exit 0** |
| ordem invertida | 2 vermelhos (arquivos invertidos) | **os MESMOS 2** (`test_fase1_ui::test_ligadas_registra_e_finaliza` e `::test_reduzidas_significa_zero_animacoes_em_voo`), agora pela flag |
| janela real | (não existia) | **4/0/0** |

Os 2 vermelhos da ordem invertida são o estado vivo de `animacoes.py` — pela
definição de pronto do Bloco B, eles ficam vermelhos ATÉ o B2 (não os mascarei
com limpeza de bancada; seria matar a prova do B2). Fora eles, NENHUM teste da
suíte depende de ordem, mesmo com itens invertidos.

### Consertos fora dos testes que precisei fazer (L6 — declarados)

1. **`app/editor_app.py` (produção):** `ARTE`/`FIXTURE` eram relativos ao CWD
   ("Frente Template.png" nu) e `montar_editor()` chamava `_grade_real()` SEM a
   proteção que a frota F12 escreveu 60 linhas abaixo em
   `_layout_padrao_do_banco` — rodar de outra pasta morria com
   `FileNotFoundError` da PIL ANTES da janela (era o vermelho do
   `test_ctrl_k_abre_em_duas_telas`). Apliquei a MESMA lição do irmão: os dois
   caminhos ancorados no pacote e o `montar_editor` com fallback para a grade
   sintética; sem a fixture de exemplo, o editor abre vazio. Se o arquiteto
   entender que isso pertencia ao Bloco E (CA-05), o código já está pronto
   para a reauditoria lá.
2. **`test_fase12_marco.py:533`:** `campanhas_do_marco()` com o default
   CWD-relativo dentro do teste do marco — ancorado explícito. Achado na 1ª
   passada da prova de outra pasta DESTA resposta (862 com 1 vermelho →
   conserto → 862/0/0).
3. Imports órfãos criados pelas minhas edições foram limpos (`ruff --select F`
   zerado nos arquivos tocados; um F821 real meu em test_onda3 corrigido).

### O que ficou de fora (e por quê)

- **A escolha "versionar uma arte mínima de bancada" NÃO foi tomada por mim** —
  a ordem diz "decida com o arquiteto". Implementei a alternativa conservadora
  (skip explícito e contado), que não publica nada do acervo do dono no git.
  Se o arquiteto preferir arte sintética versionada (que faria os testes de
  arte rodarem em clone), o `acervo.py` a recebe num ponto só.
- **Os 2 vermelhos da ordem invertida** ficam vermelhos até o B2 (acima).
- **O default do Enter nos diálogos (CF-01)** — B3, não tocado.
- `app/tests_janela` NÃO entra no `testpaths` padrão (abre janelas de
  verdade); roda explícita antes de cada selo, como a ordem pede.
- Ideia anotada (L8, não construída): o `vigia_dialogo` já registra o botão
  com foco e o botão padrão — o teste vermelho do B3 nasce dele em 3 linhas.

**PARADO aqui (L7). O Bloco B não foi iniciado. Aguardando o selo do arquiteto.**
