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
independentes**; mais o adversarial I1–I5 atualizado e verde. E, do selo do Bloco B (§5.6/§5.7):

1. **COND-4** — o contrato `carregar` (documento novo, zera histórico) × `atualizar_dados`
   (dados, preserva pilha) documentado **dentro de `canvas.py`**, nos dois docstrings.
2. **COND-5** — `marca_propria` no `ItemMesa` decidido no C11 ou registrado nominalmente no F.
3. **COND-3 ativada** — C1 inverte `test_mut2`, C3 inverte `test_mut3`, C5 inverte `test_mut4`.
   Inverter, nunca apagar nem `xfail`.
4. Junit do bloco em `saida_f13/` (suíte ×2, ordem invertida, janela real).

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
medições suas, **na máquina real, com as 30 ofertas reais do Quintou**. Número medido, não
estimado. E, do selo do Bloco C (§6.6):

1. **COND-6** — `itens.py:417` ganha `and self.isSelected()`, igualando ao `:391`; o teste do C
   volta ao alvo original (arraste perto da vizinha) e fica verde **pelo conserto**.
2. **COND-7** — os três vigias invertidos renomeados para dizer o que hoje afirmam.
3. Junit do bloco em `saida_f13/` (suíte ×2, ordem invertida, janela real).

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
| **E10** | **COND-8** — `exportar_dialog.py:57-59` e `publicar_dialog.py:268-271` ainda ensinam a lei morta ("sai com RASCUNHO até você aprovar"). Corrigir os dois **e** virar teste: grep por `"até você aprovar"` na produção volta vazio; nenhuma string de UI afirma carimbo automático ou aprovação obrigatória. | §7.4 do selo |

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
Mais, do selo do Bloco E (§8.3): **criar `docs/LEDGER_I2_F13.md`** com os remanescentes do E5
(ID, `arquivo:linha`, o que se perde, desfecho) — criar no F, zerar no G (COND-9).

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
- **H8. COND-10 — a caça ao segfault**, com orçamento de reprodução e as três saídas aceitáveis
  do §8.4 (reproduzido e consertado · reproduzido e cercado · não reproduzido em N execuções
  documentadas, com o risco escrito). Virar lenda de novo é inaceitável. Ligar ao §5.5: se a lei
  do `stop()` explicar as duas batidas, fecham-se duas coisas de uma vez.
- **H9. A medição refeita com FOTO** (§7.3b) e o **orçamento de ACERTO** de conciliação com item
  parecido-mas-não-idêntico num acervo grande (§7.3a — o M-03 segue aberto).
- **H10. A lição de casa do dono:** o `.exe` rodando em Windows limpo, fechando CA-01/02/03.

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

## §5 · SELO DO BLOCO B — reauditoria do arquiteto (25/07/2026)

**BLOCO B SELADO.** Pode começar o C — **C1+C2 juntos**, como você propôs e como a ordem
manda (derrubar a trava nº 2 sem resolver o E-01 troca um sintoma por outro).

### 5.1 · As três condições do §4.3, conferidas uma a uma

| | Verificado no disco |
|---|---|
| **COND-1** ✅ | `test_bancada_gesto_f13.py:105-112` — a asserção nova é `pai.findChild(QWidget,"veuDialogo") is None or not visible`, com a mensagem `"o véu CONTINUA NA TELA depois do diálogo morrer"`. É a asserção que eu pedi, com o texto certo. |
| **COND-2** ✅ **e ultrapassada** | `test_b2_cond2_modal_no_meio_do_crossfade_janela_volta_ao_brilho` (`test_bloco_b_f13.py:261`). Usa o **Shell real** e a **PaletaBusca real**, filtro **instalado** (o docstring diz "nada de belt-out aqui"), e o modal abre no `showEvent` da tela destino — a mecânica exata do §19. Confere por **conteúdo**: `_veus_troca` vazio, nenhum `veuTrocaTela` visível, nenhum `veuDialogo` visível, a tela destino na frente **e a paleta não atravessou a troca**. Esse último assert cobre o L-10, que eu não tinha exigido. |
| **COND-3** ✅ | `git diff f649732 5a4f0d0 -- app/tests/test_bancada_gesto_f13.py \| grep -c "mut2\|mut3\|mut4"` = **0**. Os três vigias de caracterização estão intocados, à espera do C. O único movimento no arquivo foi o `mut1` (COND-1) e a fixture `vida` migrando para o conftest — legítimo, a COND-2 também precisa dela. |

### 5.2 · Disciplina de escopo — o que eu mais valorizei

`git diff f649732 5a4f0d0 --stat` sobre os quatro arquivos que guardam os bugs do Bloco C:

```
app/qt/canvas.py            (nada)
app/qt/painel_camadas.py    (nada)
app/qt/itens.py             (nada)
app/rendering/compositor.py (nada)
```

**Zero linhas.** Com o E-01, o R-02, o E-08 e o R-01 abertos na sua frente por horas, você não
tocou em nenhum. 21 arquivos de produção mudados, 536 inserções, e nenhuma invasão do bloco
seguinte. Isso é o que faz a ordem funcionar.

### 5.3 · O §4.4 fechado

`saida_f13/` tem os quatro junit, e eu li os atributos: `bloco_b_suite_1.xml` e
`bloco_b_suite_2.xml` **886/0/0/0**, `bloco_b_invertida.xml` **886/0/0/0** (o critério do §4.5
cumprido), `bloco_b_janela.xml` **4/0/0/0**. A lacuna do selo anterior está fechada — agora eu
confiro placar, não só desenho.

### 5.4 · Os consertos que eu inspecionei na fonte

- **B1 está na camada certa.** Você consertou o *chamador* (`_aplicar_mapa(novo_documento=False)`
  por padrão), não a semântica do `carregar()`. Era a decisão certa: `carregar` **deve** zerar a
  pilha ao abrir documento novo; o bug era `_aplicar_mapa` chamar carregamento para refrescar
  dado. E o docstring cita `_excluir_item (:443)` — a lição que o próprio código já tinha.
- **B7 cobre os dois ramos** ("é novo" e candidato escolhido), com o piso validado
  (`0 < juiz <= 1`, inválido cai no padrão — o mesmo padrão do "limiar quebrado nunca derruba a
  conciliação"), e o desfecho é AMARELO **com o melhor palpite à vista** — honra a trava da F9
  em vez de inventar.
- **`perguntar` conserta o padrão-raiz do CF-01**: `setDefaultButton` **declarado** (o "não",
  salvo indicação explícita) + `setEscapeButton(b_nao)`. E o `instalar_traducao_qt` fecha o L-03
  além das 8 perguntas, alcançando os nativos do Qt.
- **B2d ficou melhor do que eu tinha pedido**: três saídas, e o X/Esc caem em "deixar para
  depois". O docstring articula o princípio certo — *"fechar a janelinha é o gesto universal de
  'decido depois', nunca uma destruição calada"*.
- **B10** removeu o hard-delete apontando para a porta oficial no comentário.
- **Uma única exceção larga nova** em 536 inserções (`instalar_traducao_qt`), e ela é
  I2-compatível por argumento explícito no docstring: falta de arquivo de tradução **não perde
  conteúdo**, só deixa botão de fábrica em inglês — o dono vê com os próprios olhos. Aprovada.

### 5.5 · O achado do `stop()` — promovido a lei do projeto

Sua caça aos 2 vermelhos da ordem invertida achou algo que nenhum dos dois dossiês tinha, e que
é maior que o Bloco B: **`QAbstractAnimation::stop()` não emite `finished`** — o Qt só emite no
fim NATURAL. Toda animação interrompida ficava registrada "em voo" para sempre. Confirmei o
conserto na raiz (`animacoes.py:92-124`: `stateChanged→Stopped` + `_prazo` de autoencerramento,
com o caso do `stop()` numa já-parada tratado à parte).

Isso entra no `CLAUDE.md` como lei, com a redação sua:

> **Animação no Qt: `stop()` NÃO emite `finished`.** Quem precisa saber que uma animação
> terminou escuta `stateChanged → Stopped`, nunca `finished` — e `stop()` numa animação já
> parada não emite nada. Todo registro de "animação viva" precisa de prazo de
> autoencerramento como rede.

E um pedido: quando estiver no Bloco E, **verifique se essa lenda explica o segfault
intermitente** que a F12 tratou com a regra do DeferredDelete. Pode ser a mesma raiz.

### 5.6 · As duas condições que entram no Bloco C

**COND-4 · O contrato do `carregar` vs `atualizar_dados` tem de morar no `canvas.py`.**
Hoje ele está documentado no docstring do `_aplicar_mapa`, em `mesa.py` — do lado de quem
chama. O próximo chamador (e o C1/C2 vão criar caminhos novos) vai repetir o erro. Ponha a
regra no docstring de `CanvasView.carregar` e de `atualizar_dados`, em `canvas.py`:
*"`carregar` = DOCUMENTO novo, zera o histórico. `atualizar_dados` = dados novos, preserva a
pilha. Refrescar dado com `carregar` é o bug CD-01."*

**COND-5 · `marca_propria` ausente do `ItemMesa` — não deixe virar dívida órfã.**
Você declarou como fora de escopo, e está certo para o B. Mas o B6 unificou a receita do cartaz
e esse campo **ainda não flui** — então o selo de marca própria tem o mesmo furo que o +18
tinha, só que num campo diferente. Decida no C11 (a frente dos selos) ou registre nominalmente
no Bloco F. Não pode sumir da lista.

### 5.7 · Contrato dos vigias, ativado agora

O C1 inverte o `test_mut2`; o C3 inverte o `test_mut3`; o C5 inverte o `test_mut4`.
**Inverter, nunca apagar nem marcar `xfail`** — e o `git log` está limpo (`f649732`, `5a4f0d0`)
para mostrar a linha antiga de cada um.

---

## §6 · SELO DO BLOCO C — reauditoria do arquiteto (25/07/2026)

**BLOCO C SELADO**, com **uma correção de diagnóstico sua** (§6.4) que vira COND-6 no D.

### 6.1 · COND-3 — a inversão dos três vigias, conferida assert por assert

Os três existem, **zero `xfail`, zero `skip`** no arquivo, e as asserções viraram de verdade:

| vigia | antes (fixava o bug) | agora (exige o certo) |
|---|---|---|
| `mut2` / E-01 | slot herdado da seleção | `assert slot_img is not slot_nome` — a 2ª criação **não gruda** na 1ª |
| `mut3` / R-02 | `index(alvo) == 0` | `index(alvo) == 1` **+** `topo is alvo` — "Subir" traz para a frente |
| `mut4` / E-08 | `larg_mm == approx(larg0)` | `larg_mm > larg0 + 1.0` **+** `abs(ancora_depois − ancora_cena) < 3.0` |

O `mut4` ficou **mais forte do que eu pedi**: além de exigir que redimensione, exige que a
**âncora oposta fique parada** — isto é, que a conta do resize sob rotação esteja *certa*, não
só ativa. Era a parte difícil do C5 e você a testou.

### 6.2 · COND-4 e COND-5, cumpridas

**COND-4** — `canvas.py:192-197` (`carregar`) e `:652-653` (`atualizar_dados`) carregam o
contrato na letra, com a referência ao CD-01 e aos "9 Ctrl+Z mortos da gravação". O próximo
chamador não tem como errar sem ler o aviso.

**COND-5** — `marca_propria` flui pela cadeia inteira: `ItemMesa:44` → dict `:191` →
`from_dict:615` → `dados_cartaz_de_produto:697` → export `:721` → fusão de duplicatas `:1406`.
Não virou dívida órfã.

### 6.3 · O C1 é mais elegante do que o dossiê pedia

Eu diagnostiquei o E-01 como "auto-seleção + slot-da-seleção" e teria aceitado matar a
auto-seleção. Você fez melhor: **separou as duas intenções.**
`_slot_para_novas_regioes` continua existindo para **colocação deliberada** (colar, diálogo
nomeado), onde herdar o slot da seleção é o comportamento certo; a **criação pela barra** passou
a usar `_slot_novo_avulso`. A auto-seleção — que é útil, você quer estilizar o que acabou de
criar — sobreviveu sem o efeito colateral.

E você resolveu a **segunda metade** do que eu vi ao vivo sem eu pedir: a `_cascata_criacao`
(8 degraus cíclicos) faz cada região nova nascer deslocada. No L-07 eu registrei que as duas
nasciam no *retângulo idêntico*; agora nascem em cascata, como o paste-in-place do Illustrator.
Slot **e** geometria consertados.

### 6.4 · CORREÇÃO — o "custo de alças pegáveis" não é custo, é bug

Você fechou o último vermelho da ordem invertida movendo o alvo do arraste ("agora arrasta para
longe da vizinha") e concluiu: *"não é bug do editor (é o custo de alças pegáveis)"*.
**Fui olhar, e é bug.** Em `itens.py`:

```
:391  alca = self._handle_em(event.pos()) if self.isSelected() else None   ← hover: com trava
:417  if not self.regiao.travado:                                          ← press: SEM trava
:418      h = self._handle_em(event.pos())
```

O **hover** só oferece alça quando a região está selecionada. O **press** não checa nada. Então
uma região **não selecionada** captura o resize se o clique cair a ±`TAM` de um canto dela — sem
nenhum aviso de cursor antes, porque o hover disse que ali não tinha alça. Consequências:

1. **O cursor mente.** A única dica visual está desligada justo no caso que dispara.
2. **É o roubo de clique que você mediu** — não o custo de alças, e sim alças em objeto não
   selecionado. Todo editor sério (Illustrator, Figma, Affinity) só materializa alça na seleção.
3. **O C5 ampliou o alcance:** a condição antiga era `not travado and not rotacao`; ao derrubar a
   guarda de rotação, sobrou só `not travado` — regiões giradas passaram a roubar clique também.
4. **É da mesma família do que você acabou de matar.** O dono vai dizer "clico no nome e ele pega
   o preço" — a versão pequena do "tudo grudado".

O próprio código já sabe a regra e a aplica numa das duas portas. **O conserto é uma condição**,
igualando `:417` ao `:391`. E aí o seu teste original — o que arrastava perto da vizinha — passa
sem ser movido.

Nada disso desmerece o bloco: **você achou o fenômeno**, mediu, e só errou a atribuição da causa.
Foi a ordem invertida entregando o terceiro achado, como você disse.

### 6.5 · Placar e escopo

Junit em `saida_f13/`: `bloco_c_suite_1` e `bloco_c_suite_2` **904/0/0/0**,
`bloco_c_invertida` **904/0/0/0**, `bloco_c_janela` **4/0/0/0**. Evolução 851 → 862 → 886 → 904.

Escopo: 12 arquivos de produção, todos em território do C. Os toques em `mesa.py` (13 linhas) e
`servico.py` (9) são o C13 e a COND-5. **Nada de `images/`, `ai/`, rembg, validade ou aprovação**
— o Bloco D está intacto para o Bloco D.

### 6.6 · COND-6 e COND-7 para o Bloco D

**COND-6 · A alça só existe na seleção.** Iguale `itens.py:417` ao `:391`
(`and self.isSelected()`), **restaure o teste do C** ao alvo original (arrastando perto da
vizinha) e deixe-o verde pelo conserto, não pelo desvio. É o fecho honesto do §6.4.

**COND-7 · Renomeie os três vigias invertidos.** As asserções viraram; os **nomes** ainda
descrevem o bug — `test_mut4_..._nao_redimensiona` hoje afirma que **redimensiona**;
`test_mut3_..._mexe_o_indice_para_tras_caracterizacao` afirma que vai para a frente e não é mais
caracterização. Um nome que diz o contrário da asserção é armadilha para o próximo leitor. Minha
COND-3 falou de asserção e esqueceu o nome — a culpa é minha, o conserto é seu.

---

## §7 · SELO DO BLOCO D — reauditoria do arquiteto (25/07/2026)

**BLOCO D SELADO.** Uma pendência (§7.4) e duas leituras de medição (§7.3) entram no E.

### 7.1 · COND-6 e COND-7, cumpridas — e a 6 melhor do que eu pedi

**COND-6** — `itens.py:430`: `if not self.regiao.travado and self.isSelected():`, com o
comentário dizendo a razão certa (*"sem ela o press dava a alça que o cursor negava"*).
E o teste do C não foi só restaurado: ficou **mais hostil**. O arraste agora é
`centro + QPointF(60, 45)` — **desce em direção ao preço de propósito**, com o comentário
"o alvo ORIGINAL, restaurado". Você podia ter voltado ao alvo antigo e parado; preferiu
apontar o teste para o bug. É o fecho honesto do §6.4.

**COND-7** — os três nomes agora dizem o que as asserções afirmam:
`..._criacoes_nascem_selecionadas_e_cada_uma_no_seu_slot`,
`..._botao_subir_traz_a_regiao_para_a_frente`,
`..._alca_de_regiao_rotacionada_redimensiona_com_ancora_parada`.

### 7.2 · As travas #1 e #3 caíram de verdade

Varri as 9 portas: **nenhuma decide mais por "não aprovado"**. As chamadas de
`carimbar_rascunho` que sobraram estão todas sob a opção explícita —
`exportar_dialog.py:122` (`if self.chk_rascunho.isChecked():`), `publicar_dialog.py:65`,
`fabrica.py:697`, `mesa.py:2675`, `servico.py:1938` — e as assinaturas nasceram
`rascunho=False` com o docstring declarando *"sai LIMPA por padrão"*. A #3 idem: a validade
se autopreenche no salvar **e** no export, e o canal estrutural leva a validade viva ao rodapé
fora de célula (o furo que o marco da F12 contornava na mão).

Escopo: 21 arquivos, todos em território do D. Nada de instalador, Cofre, `.atproj`,
somente-leitura ou encartes — **os Blocos E e F seguem intactos**.

### 7.3 · Duas leituras da medição (a sua ressalva está certa; faltam duas)

O `bloco_d_medicoes.md` é honesto — a ressalva final sobre o 96 dpi da arte real e sobre o
rembg de foto não-branca é o tipo de coisa que auditor normalmente tem que arrancar. Duas
leituras a acrescentar, para ninguém ler o quadro errado depois:

**(a) "0,07 s · 30/30 verdes" NÃO retira o M-03.** Você escreveu "o acervo da semana já casa",
e está certo — mas o número mede o **caminho recorrente** (itens já cadastrados casando com
eles mesmos). O M-03 do dossiê é outro caso: 30 itens contra **5.007** produtos, dando
**0 verdes**. Nenhuma das duas medições testa o que importa de verdade — item que **deveria**
casar com um cadastro **parecido, não idêntico** (abreviação, erro de OCR, ordem trocada), num
acervo grande. Esse é o orçamento de acerto do **H1**, e continua em aberto.

**(b) O 105 ms de composição é sem foto.** Você registrou no item 5 que "as células da medição
não têm foto" — o que valida o pré-voo — mas o mesmo vale para o item 2. Compor 15 células
**com** as fotos tratadas é mais caro. O número não está errado; está incompleto. Refaça-o no H
com as fotos reais, junto com o H1.

### 7.4 · PENDÊNCIA — duas telas ainda ensinam a lei morta

O motor caiu, a **legenda não**. Dois rótulos continuam afirmando a regra revogada:

- `exportar_dialog.py:57-59` — *"A peça sai com "RASCUNHO" até você aprovar o projeto."*
- `publicar_dialog.py:268-271` — a mesma frase.

Hoje isso é **falso**, e no `exportar_dialog` a contradição está **dentro do mesmo diálogo**:
o rótulo diz que sai carimbado, e o checkbox logo abaixo diz que o carimbo é opcional. É a
mesma família de defeito que abriu esta auditoria — o programa contando ao dono algo que não é
verdade (M-06: o relatório do marco afirmando uma validade que o PNG não tinha). O dono lê,
acredita que o arquivo saiu marcado, e ou caça um botão que já não precisa, ou desconfia da
saída limpa.

**COND-8 (Bloco E):** os dois rótulos passam a descrever a regra viva, e a varredura vira
teste — nenhuma string de UI pode afirmar carimbo automático ou aprovação obrigatória. Grep
por `"até você aprovar"` na produção deve voltar vazio.

---

## §8 · SELO DO BLOCO E — reauditoria do arquiteto (25/07/2026)

**BLOCO E SELADO** (parcial no E5, ver §8.3). Pode começar o F.

### 8.1 · Conferido no disco

| | Verificado |
|---|---|
| **COND-8** ✅ | `grep "até você aprovar"` na produção: **vazio**. A varredura virou teste permanente (`test_bloco_e_f13.py:59`, com as três variantes de escrita). E a legenda nova conta a regra viva: *"Projeto aprovado (selo do checklist) — a peça sai limpa"* — a aprovação aparece como **selo informativo**, não como condição. |
| **E1** ✅ | `servico.py:195-201`: três saídas (completo 973 MB / leve ~5 MB / "Agora não"), `setDefaultButton(b_nao)` **e** `setEscapeButton(b_nao)`, com o comentário *"a lei do B3: Enter não baixa 1 GB"*. Você aplicou a lei do B3 a um diálogo novo sem ninguém pedir — é assim que se sabe que uma lei pegou. |
| **E2** ✅ | `instalar_rede_de_erros()` em `editor_app.py:429-430` — depois da checagem de instância única e do AppUserModelID, e **antes** do `QApplication`, do `SystemRoot` e do `Database.init()`, que eram os caminhos do CA-03. *Resíduo marginal registrado: falha durante o **import** de `editor_app` ainda morre muda; não vale caçar.* |
| **Placares** ✅ | 935/0/0 ×2, invertida 935/0/0, janela 4/0/0. E você gravou `bloco_e_baseline.xml` (924) — **a linha de base do bloco como artefato**. Boa prática; adote nos blocos seguintes. |
| **Escopo** ✅ | 21 arquivos, todos em território do E (`erros.py` novo, `paths`, `modo`, `portabilidade`, `models`, `fundo`, `upscale`, `biblioteca`). Nada de `grade.py`, nada de encarte — o **Bloco F está intacto**. |

### 8.2 · Evolução da fase

851 → 862 (A) → 886 (B) → 904 (C) → 924 (D) → **935 (E)**. Zero skips em toda a série.

### 8.3 · DECISÃO 1 — o E5 fica parcial, mas os 26 saem da prosa

**Selo parcial concedido.** Sua triagem está certa: I2 não é uma categoria única. Os que perdem
**conteúdo do dono** (a lixeira invisível à conciliação, o alfa morto no cartaz ampliado, a
categoria jogada fora) são hemorragias e você os tratou; os ~26 restantes são "a operação falhou
e ninguém contou", que é fricção de confiança — território do G.

**Mas não herdam como parágrafo.** A F13 já tem um precedente ruim disso registrado no §18 do
dossiê: o **K-03** — as recomendações R-116/R-119 foram *aceitas* pelo dono e depois viraram
"vetadas" num caderno de fase, **sem ninguém avisar**. Débito que vive em texto corrido evapora.

**COND-9 (entra no G, criar agora no F):** os pontos remanescentes viram
`docs/LEDGER_I2_F13.md` — uma linha por item, com **ID** (`I2-01`…), `arquivo:linha`, o que se
perde, e uma coluna de desfecho: `CONSERTADO` · `DISPENSADO PELO DONO (motivo)` · `ABERTO`.
Números exatos, não "~26". A definição de pronto do G exige **zero `ABERTO`** — cada item
consertado ou dispensado *por decisão registrada do Otaviano*. Um item pode legitimamente ser
dispensado; o que não pode é desaparecer.

### 8.4 · DECISÃO 2 — o segfault não vai para o G

**Não bloqueia o selo do E** — ele é anterior ao bloco, e esta é a primeira vez em toda a
história do projeto que ele tem **endereço** em vez de lenda. Isso é progresso, e é seu.

**Mas ele não pode ir para o G.** O G é qualidade de vida; um *crash* é a classe mais severa de
defeito que existe neste programa e não pode esperar atrás de renomear rótulos. E há um risco de
calendário: o **H** é a sessão em que o Otaviano dirige o app de ponta a ponta, repetidamente —
que é exatamente a condição que faz um crash intermitente aparecer. Um segfault no meio da
sessão de aceitação dele é o pior momento possível.

**COND-10 (vira condição do H, com orçamento):** o segfault entra no **H** como item nomeado,
com **orçamento de reprodução** — não "olhar se acontece". Registre no `docs/` os frames exatos
das duas batidas, e a caça tem três saídas aceitáveis:
1. **reproduzido e consertado** (ideal);
2. **reproduzido e cercado** (guarda que impede o crash, com o mecanismo explicado);
3. **não reproduzido em N execuções documentadas** — e aí a decisão é do dono, com o risco
   escrito na cara dele, não escondido.
A saída inaceitável é a quarta: virar lenda de novo. E ligue a caça ao §5.5 — se a lei do
`stop()` explicar as duas batidas, você fecha duas coisas com uma.

### 8.5 · A lição de casa dele segue aberta

O `.exe` **nunca foi executado em Windows limpo**. E1/E2/E3 têm código e teste, mas o CA-01/02/03
descrevem o que o código *fará*. Isso não é falha sua — é o §3 desta ordem, e é do Otaviano.
Vai junto com o H.

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

---

## RESPOSTA DO BUILDER — BLOCO B (Fable 5, 25/07/2026)

O Bloco A foi fechado no commit `f649732` (pedido do §4). Todos os itens
abaixo seguiram a L1 na letra: **cada conserto tem a rodada VERMELHA
registrada nesta bancada antes do conserto** (para os itens cujo conserto
precisei escrever antes de rodar, o vermelho foi registrado por *stash
dance* — os arquivos de produção voltam ao estado anterior via
`git stash`, a rodada vermelha executa, o `git stash pop` devolve o
conserto; a saída bruta com os 11 vermelhos nominais está no histórico da
sessão). Todos os testes novos moram em `app/tests/test_bloco_b_f13.py`
(24 testes) e usam a bancada de gesto do Bloco A.

### A tabela item × prova (vermelho → conserto → verde)

| # | conserto | teste (vermelho antes) | onde mexi |
|---|---|---|---|
| B1 | editar nome/preço PRESERVA a pilha de desfazer; `_aplicar_mapa` só recria o histórico com `novo_documento=True` (reabrir congelado); mapa novo vira ESTADO na pilha viva (D5), dedup engole o resto | `test_b1_editar_nome_e_preco_preserva_o_desfazer` (gesto: mover região + 2 diálogos reais respondidos pelo vigia + desfazer pelo botão real) | `mesa.py` `_aplicar_mapa`/`abrir_projeto_congelado` |
| B2 | o véu do diálogo é um widget de verdade (`_VeuDialogo`): acompanha Resize da mãe, e o `destroyed` o DESTRÓI (não só tira do dict — COND-1) | `test_mut1_v01_*` CRESCEU: `pai.findChild("veuDialogo")` ausente/invisível (nasceu vermelha) | `animacoes.py` `_VeuDialogo`/`_matar_veu` |
| B2b | foto do crossfade ganhou nome (`veuTrocaTela`) + prazo de morte (ms+400) + `_fim` idempotente e blindado; `varrer_veus_orfaos()` roda na fronteira de TODA troca de tela; a paleta do Ctrl+K fecha no `ir_para` | `test_b2_cond2_modal_no_meio_do_crossfade_janela_volta_ao_brilho` (COND-2: a sequência REAL do §19, filtro INSTALADO; o vermelho registrado foi exatamente "a paleta atravessou a troca", L-10) | `animacoes.py` crossfade, `shell.py` ir_para |
| B2c | os 8 `QMessageBox.question` Yes/No viraram `perguntar()` (PT-BR, VERBO nos botões, padrão declarado no seguro, Esc no não); tradutor `qtbase` pt-BR nos 2 entrypoints (nativos tipo QInputDialog); varredura por IDENTIFICADOR na bancada | `test_b2c_varredura_nenhum_question_estatico_na_producao` + `test_b2c_perguntar_fala_portugues_pelo_clique_real` | `componentes.py`, `configuracoes.py` ×3, `almoxarifado.py`, `mesa.py`, `modo_pai.py`, `projetos_dialog.py`, entrypoints |
| B2d | o diálogo de recuperação tem TRÊS saídas: Recuperar (Enter), **Descartar de vez** (só ele destrói) e **Deixar para depois** (Esc/X — o rascunho FICA). De carona: "1 itens" → "1 item" (L-04) | `test_b2d_esc_no_recuperar_rascunho_deixa_para_depois` + `_descartar_explicito` + `_recuperar_recupera_e_fala_portugues` (os 3 pelo diálogo REAL) | `mesa.py` `_oferecer_recuperacao` |
| B2e | sair do editor sujo PERGUNTA nos DOIS pontos: o "← Biblioteca" (a expectativa) e o `_editar` por cima de edição suja (o ponto da perda real) | `test_b2e_voltar_com_edicao_suja_pergunta_e_ficar_fica` + `test_b2e_sair_sem_salvar_sai_e_reabrir_pergunta_no_ponto_da_perda` (gesto: sujar pela barra real, sair pelo botão real) | `atelie.py` `_voltar`/`_editar` |
| B3 | `setDefaultButton(Cancelar)` + `setEscapeButton` nos DOIS diálogos de confirmação — Enter nunca mais destrói/exporta | 4 testes `test_b3_*` (Enter/Esc pelo diálogo real; fechado logo após o selo do A) | `componentes.py`, `prevoo.py` |
| B4 | a poda de versões NUNCA toca a mais antiga — a original (ou a sobrevivente mais antiga em acervo já podado) é eterna; o limite vale para as derivadas | `test_b4_a_original_sobrevive_a_11a_troca_por_conteudo` (7 trocas com cores únicas, limite 3 — a COR original tem de sobrar) | `biblioteca.py` `_podar` |
| B5 | `quick_check` ANTES do snapshot do boot: corrompido não vira snapshot, não rotaciona os bons, e deixa rastro em `logs/cofre.log` (I2) | `test_b5_snapshot_do_boot_pula_banco_corrompido_e_preserva_os_bons` (o vermelho revelou que o código velho nem chegava a rotacionar: ESTOURAVA `sqlite3.DatabaseError` cru no boot) | `cofre.py` |
| B6 | receita ÚNICA `dados_cartaz_de_item()` — as 3 receitas divergentes (Fábrica local, etiquetas em lote, dict do projeto reaberto) agora delegam; o +18 chega à etiqueta, e o projeto CARTAZ reaberto (Modo Pai incluso) não perde mais18/categoria | `test_b6_etiqueta_em_lote_diferencia_mais18_por_conteudo` (bytes da imagem embutida no PDF, porta inteira) + `test_b6_projeto_cartaz_reaberto_*` + `test_b6_fabrica_compoe_do_mesmo_dado_*` | `servico.py`, `fabrica.py` |
| B7 | o juiz COMPARA a confiança: abaixo do piso (`conciliacao.juiz_confianca`, padrão 0,6, C3-são) vira AMARELO com o candidato à vista — nos DOIS ramos (confirmou e "é novo") | `test_b7_juiz_com_confianca_baixa_vira_amarelo` (0,05 pintava VERDE) + regressão `_confiante_segue_verde` | `conciliacao.py` |
| B8 | a revisora pede e USA os pares nome+preço: preço do item A na célula do item B (os dois preços existem no projeto — o conjunto fechava!) agora vira aviso nominal "parece PREÇO TROCADO" | `test_b8_revisora_pega_preco_trocado_entre_dois_itens` + regressão anti-alarme-falso | `revisora.py` |
| B9 | purga por ITEM (linha primeiro, commit, ARQUIVOS depois): FK vivo pula SÓ aquele item COM relato nominal ("FICOU na lixeira — algo vivo aponta"); `excluir_agora` com a mesma ordem; o toast do boot separa purgados de presos | `test_b9_purga_com_projeto_vivo_apontando_nao_aborta` (o vermelho: `IntegrityError` do ORM anulando o FK NOT NULL abortava TUDO, com os arquivos já apagados) | `lixeira.py`, `editor_app.py` |
| B10 | os dois hard-deletes públicos REMOVIDOS (+ o import morto de `atelie.py`; o único teste que usava `excluir_layout` passou à lixeira oficial) | `test_b10_hard_deletes_sem_chamador_foram_removidos` (varredura por identificador — a lei dos vetos) | `persistencia.py`, `repositories.py`, `atelie.py`, `test_atelie.py` |

### A definição de pronto do bloco, ponto a ponto

1. **COND-1** ✅ — `test_mut1_v01` cresceu a asserção do véu FORA da tela;
   nasceu vermelha ("o véu CONTINUA NA TELA... L-01", registrado) e o B2 a
   deixou verde.
2. **COND-2** ✅ — o teste da sequência real existe (Shell de verdade, vida
   INSTALADA, modal abrindo no `showEvent` DENTRO do crossfade, paleta
   aberta); nasceu vermelho pelo resíduo nº 2 (a paleta atravessando).
3. **`--ordem-invertida` VERDE** ✅ (§4.5) — **886/0/0** na árvore final
   (`saida_f13/bloco_b_invertida.xml`). A caça custou três rodadas e valeu:
   os 2 presos eternos eram `QVariantAnimation` do zoom de ajuste do canvas
   em estado `Stopped` DENTRO de `_VIVAS` — porque **`stop()` NÃO emite
   `finished`** (finished só sai no fim NATURAL). O comentário da casa em
   `_hover_saiu` ("remove de _VIVAS via finished") era uma LENDA. Conserto
   na raiz: `_registrar` escuta `stateChanged→Stopped` (cobre os dois
   desfechos) + prazo de autoencerramento para animação finita congelada +
   o pulso do Skeleton se desliga no 1º tick invisível (ancestral escondido
   não manda hideEvent ao filho — CPU a zero também em produção).
4. **Os três de caracterização intocados** ✅ (COND-3) — `test_mut2/3/4`
   não foram tocados neste bloco; invertem no C, como manda o contrato.

### Os placares (junit versionado em `saida_f13/`)

| prova | resultado |
|---|---|
| suíte da raiz ×2 | **886 verdes ×2, 0 falhas, 0 skips, exit 0** (`bloco_b_suite_1.xml`, `bloco_b_suite_2.xml`) |
| ordem invertida (árvore final) | **886/0/0, exit 0** (`bloco_b_invertida.xml`) |
| janela real (antes do selo, como manda o A2) | **4/0/0** (`bloco_b_janela.xml`) |

*(O `.gitignore` ganhou `!saida_f13/` — o junit viaja no repo para a sua
reauditoria, §4.4.)*

### Achados próprios de bancada (L6)

1. **A lenda do `stop()`/`finished`** (acima) — não estava em nenhum dossiê;
   a prova de ordem invertida a desenterrou. As duas asserções de
   `test_fase1_ui` agora imprimem QUEM ficou em voo (`_vivas_nominais`) —
   fica como instrumento permanente.
2. **O snapshot do boot com banco corrompido nem chegava à rotação**: a
   rodada vermelha do B5 mostrou `sqlite3.DatabaseError` CRU subindo do
   `_backup_sqlite` — o boot real morreria ali (CA-03 vizinho). O
   quick_check agora barra antes.
3. **O vigia de diálogo não pode assertar dentro do timer** — exceção em
   slot é engolida pelo laço do Qt e o `exec()` fica aberto para sempre
   (uma rodada pendurou a bancada). O vigia ganhou `faltou_botao` +
   `reject()` e a asserção mora depois do `with`. E ganhou `vezes=N` para
   fluxos com dois diálogos seguidos.
4. **Rodar duas suítes pytest em paralelo pendura** (provável trava de
   instância única/QLocalServer) — desde então, uma suíte por vez nesta
   bancada; fica o registro para os próximos blocos.

### O que ficou de fora (e por quê)

- **`marca_propria` não existe no `ItemMesa`** — a receita única a passa
  como False para itens da Mesa/Fábrica (o Almoxarifado, que tem o dado,
  continua passando). Adicionar o campo ao ItemMesa é mudança de
  serialização de projeto — não citada no B6; anoto para o arquiteto.
- **QInputDialog nativo (editar nome/preço) fala inglês** de fábrica; o
  tradutor qtbase pt-BR instalado nos entrypoints cobre no app real, mas
  não há teste disso (depende do arquivo de tradução do PySide6 no pacote
  — o spec do instalador precisa conferir isso no Bloco E, CA-08).
- **Guarda de "fechar o APP com trabalho não salvo"**: implementei e
  REVERTI — o `closeAllWindows()` do teardown penduraria a bancada inteira
  num modal, e o caso citado pela ordem (L-09) é o do editor. Anotada como
  ideia (com a solução do `event.spontaneous()` a discutir) — L8.
- **O rascunho recuperado NÃO é consumido** — decisão minha registrada em
  teste: ele só some no salvar de verdade ou no descarte explícito
  (consumir na recuperação abriria janela de perda até o 1º auto-save).
- A purga com item preso conta o preso no toast do boot separado
  ("N apagados e M FICARAM") — o texto antigo somava tudo como "apagados".

**PARADO no fim do Bloco B (L7). O Bloco C não foi iniciado. Aguardando o
selo do arquiteto.**

---

## RESPOSTA DO BUILDER — BLOCO C (Fable 5, 25/07/2026)

O Bloco B foi fechado no commit `5a4f0d0` e selado no §5. Todos os itens
abaixo seguiram a L1: **cada conserto tem a rodada VERMELHA registrada nesta
bancada antes de virar verde** (*stash dance* nos consertos escritos antes
de rodar — produção estashada, rodada vermelha executada e registrada,
`git stash pop`). Os testes novos moram em `app/tests/test_bloco_c_f13.py`
e usam a bancada de gesto do A. Comecei por **C1+C2 juntos**, como o §5
mandou.

### A tabela item × prova (vermelho → conserto → verde)

| # | conserto | teste (vermelho antes) | onde mexi |
|---|---|---|---|
| C1 | região nova NUNCA herda slot: cada criação nasce em `livre_<uuid8>` **PRÓPRIO**, em cascata (offset 4% da página, passo circular de 8). O vermelho do mut2 invertido revelou que o E-01 tinha **DUAS pernas**: a herança pela seleção E o reuso do MESMO slot avulso para toda criação sem seleção — as duas mortas | `test_mut2` **INVERTIDO** (agora exige slot próprio e independência) + o DoD da gravação | `canvas.py` `_slot_novo_avulso`/`adicionar_regiao` (cascata zerada no `carregar`) |
| C2 | **o trio caiu (trava nº 2)**: clique E arrasto pegam SÓ a peça clicada (`_selecao_por_clique` sem trio; o colapso-em-2-tempos virou costura vazia). Mover a célula inteira ganhou **gesto próprio**: menu → "Selecionar a célula inteira" (`selecionar_celula_inteira`) | `test_c2_arrastar_uma_peca_move_so_ela` + `test_c2_celula_inteira_pelo_menu`; os testes do trio em `test_adversarial_vinculo`/`test_fase4_editor`/`test_isolamento`/`test_onda3_editor` **FLIPADOS** com docstring "FLIPADO na F13/C2" | `itens.py` |
| C3 | Subir/Descer **desinvertidos** (Subir = para a frente de verdade) e o painel exibe **topo = frente** (convenção Illustrator). Decisão de nascimento tomada junto: região nova SEGUE nascendo na frente — agora isso é VISÍVEL no painel, que era o que faltava | `test_mut3` **INVERTIDO** (de caracterização do bug a exigência do certo) + `test_c3_painel_topo_e_frente` | `painel_camadas.py` `_mover`/`recarregar` |
| C4 | alinhamento vertical EXISTE: enum `AlinhamentoV` (TOPO/CENTRO/BASE) no modelo (serializado, default CENTRO — layout antigo abre igual), `_y_alinhado` no compositor, combo no painel | `test_c4_topo_centro_base_por_pixel` (tinta medida na caixa; TOPO/BASE/CENTRO distintos) + `test_c4_combo_no_painel` | `model.py`, `compositor.py`, `painel_propriedades.py` |
| C5 | **resize sob rotação ligado**: a conta saiu do `scenePos` cru para coordenadas LOCAIS do item (`event.pos()`), com reancoragem (`setTransformOriginPoint` no centro novo) e compensação de deriva do canto fixo. E os campos **Posição e tamanho (mm)** entraram no painel (VC-004) — as DUAS alternativas da ordem, não uma | `test_mut4` **INVERTIDO** (arrastar a alça a 30° REDIMENSIONA e o canto oposto não deriva) + `test_c5_campos_mm_mudam_o_rect` | `itens.py` `mouseMoveEvent`, `painel_propriedades.py` `grp_pos` |
| C6 | duplicar a CÉLULA inteira: comando novo `duplicar_celula` (slot novo, uids frescos, +4 mm, nasce selecionada) no menu da peça quando o slot tem >1 região — a peça sozinha continua com o duplicar de sempre | `test_c6_duplicar_celula_inteira_por_conteudo` (trio duplicado por pixel, uids todos novos, original intacta) | `canvas.py`, `itens.py` |
| C7 | carimbar sem caixa desenhada deixa de nascer do tamanho da página: nasce CENTRAL (35% da página), em slot avulso próprio, **visível e selecionado** | `test_c7_carimbar_sem_caixa_nasce_central_e_selecionado` | `canvas.py` `carimbar_modelo` |
| C8 | o detector de grade ganhou **área mínima E proporção** (risco de 3 px e respingo de 30×20 caem; caixas reais ficam) e o "Novo layout" ganhou **revisão ANTES de salvar**: "Criar com N células" / "Criar sem grade (marcar no editor)" | `test_c8_detector_ignora_risco_e_respingo` (arte sintética com 3 caixas + lixo → 3 células exatas) + `test_c8_novo_layout_revisa_antes_de_salvar` (pelo diálogo REAL, vigia; "sem grade" = layout limpo) | `grade.py` `detectar_caixas_preco`, `atelie.py` `_novo` |
| C9 | agrupar **explica cada recusa** (toast nominal: qual região, por quê — derivada/mestra, em QUALQUER origem) e **confirma o sucesso** (toast + tutorial só quando agrupou). E ficou multi-slot de verdade: `agrupar_como_mestre` junta soltas de VÁRIAS origens | `test_c9_recusa_explicada_e_sucesso_confirmado`; `test_fluxo_real_grade_mais_destaque` atualizado ao contrato novo (3 slots → 1 mestre com as 3 por identidade) | `canvas.py` `agrupar_selecao`, `grade.py` |
| C10 | `Ajuste.PREENCHER` **recorta no caminho rápido**: `img.crop` para a janela da região quando a foto redimensionada excede a célula — nunca mais vaza | `test_c10_preencher_nao_vaza_da_celula` (pixel FORA da região tem de ficar limpo; vermelho mostrou o vazamento real) | `compositor.py` |
| C11 | selos com **CONTROLE**: grupo "Selos" no painel (canto do +18 e do selo de qualidade → `definir_canto_automatico` + recompor; `migrar_selos` idempotente antes da busca). E o exemplo do Ateliê agora tem `mais18=True` — o selo **aparece na prévia** de quem faz tudo certo | `test_c11_canto_do_selo_muda_por_pixel` + `test_c11_exemplo_do_atelie_mostra_selo` | `painel_propriedades.py`, `selos.py`, `atelie.py` `_EXEMPLO` |
| C12 | a mestra **propaga o texto**: `texto_fixo` (e o `alinhamento_v` novo do C4) entraram em `ATRIBUTOS_ESTILO` — a "tag inteligente" funciona | `test_c12_mestra_propaga_texto_fixo_por_pixel` | `grade.py` |
| C13 | Ctrl+K com **UM dono**: o QShortcut cru da Mesa foi removido; a paleta da Mesa virou `mesa.paleta` (Ctrl+Shift+P) no catálogo oficial de atalhos. O teste novo **APERTA a tecla** (o antigo chamava o método) | `test_c13_ctrl_k_um_dono_so` (por `teclar`, janela ATIVADA — ver achado nº 4) + `test_fase2_busca::test_ctrl_k` reescrito por gesto | `mesa.py`, `atalhos.py` |
| VC-010 | o `_emitir_medidas` que "calculava e jogava fora" agora alimenta um **chip de medidas VIVO** no viewport (nome + mm), visível DURANTE o arrasto e some no soltar | `test_vc010_chip_vivo_durante_o_arrasto` (visível no meio do gesto, invisível após o release) | `canvas.py`, `itens.py` |
| VC-014 | as guias de arrasto ganharam a **medida em mm** escrita (rótulo na escala da cena, acima das linhas) | `test_vc014_guia_com_medida` (texto "N mm" presente na cena durante o gesto) | `canvas.py` `mostrar_guias` |

### A definição de pronto do bloco, ponto a ponto

1. **O teste da gravação** ✅ — `test_c_dod_sequencia_da_gravacao_tres_criacoes_independentes`:
   criar IMAGEM, criar TEXTO, criar PREÇO pelos TRÊS botões reais da barra,
   arrastar CADA uma (na ordem topo→fundo do z, porque a cascata as
   sobrepõe de propósito), e a prova por conteúdo: cada arrasto move SÓ a
   sua, os três slots são distintos, os três pixels respondem independentes.
   É a sequência exata da gravação do dono — e nasceu VERMELHA no código do
   Bloco B.
2. **Adversarial I1–I5 atualizado e verde** ✅ — `test_adversarial_vinculo`
   com o contrato novo: o fluxo real agora cria 3 regiões em 3 slots
   distintos (C1) e o agrupar as JUNTA por identidade (r1/r2/r3 no mestre,
   `len==3`); os testes que fixavam o trio flipados, nunca apagados.
3. **COND-3** ✅ — mut2 (C1), mut3 (C3) e mut4 (C5) **INVERTIDOS no mesmo
   arquivo, mesmos nomes** (docstrings citam a COND-3); nenhum apagado,
   nenhum xfail. As formas antigas estão no `git log` (`5a4f0d0`), como o
   §5.7 pediu.
4. **COND-4** ✅ — o contrato mora DENTRO de `canvas.py`, nos docstrings de
   `carregar` ("DOCUMENTO novo — zera o histórico… Refrescar dado com
   carregar é o bug CD-01") e `atualizar_dados` (dados novos, preserva a
   pilha).
5. **COND-5** ✅ **decidida no C11, como a ordem preferia** —
   `ItemMesa.marca_propria` existe e FLUI: catálogo → conciliação → item
   composto (OR, como o +18) → `dados_para_desenho` →
   `dados_cartaz_de_item`. O selo de marca própria não tem mais o furo que o
   +18 tinha.
6. **Junit em `saida_f13/`** ✅ (§4.4) — os quatro placares abaixo.

### Os placares (junit, máquina real, 25/07)

| prova | resultado |
|---|---|
| suíte da raiz ×2 | **904 verdes ×2, 0 falhas, 0 skips, exit 0** (`bloco_c_suite_1.xml`, `bloco_c_suite_2.xml` — a 2ª regravada na árvore final) |
| ordem invertida (árvore final) | **904/0/0, exit 0** (`bloco_c_invertida.xml`) |
| janela real | **4/0/0** (`bloco_c_janela.xml`) |

Evolução: 851 (§0) → 862 (A) → 886 (B) → **904 (C)**.

### Achados próprios de bancada (L6)

1. **O trio mordia no ARRASTO, não no clique** — o clique parado JÁ
   colapsava para a peça (o release do Qt desfaz multi-seleção). Os testes
   antigos do trio fixavam um contrato que só existia no arrasto — por isso
   o C2 real foi consertar o `_selecao_por_clique` (que o arrasto usa), e os
   flips dizem isso no docstring.
2. **Wrapper de item MORRE no commit do arrasto** — o canvas RECONSTRÓI
   `_itens` ao gravar o gesto; qualquer teste (ou código futuro) que guarde
   o wrapper atravessando um arrasto fala com um morto. Repescar por
   `regiao is` — duas rodadas vermelhas da ordem invertida vieram daí.
3. **Zona de disputa do z no clique**: a área de acerto de uma peça inclui a
   margem das alças (±9 px); se o centro da peça clicada cair dentro dessa
   margem da vizinha ACIMA no z, a vizinha rouba o clique. Não é bug — é o
   custo de alças pegáveis — mas os testes de gesto precisam arrastar para
   LONGE da vizinha. Só a ordem invertida pegou (a 3ª rodada dela).
4. **Atalho de janela exige janela ATIVA** — offscreen nada ativa sozinho;
   `QShortcut` com contexto de janela fica surdo. A bancada ganhou
   `ativar_janela` (`gestos.py`) e o teste do C13 só fala a verdade por
   causa dela (CF-06 vizinho).
5. **TOPO no C4 tem folga de ~5 px** — é a entrelinha do glifo (métrica da
   fonte), não bug do `_y_alinhado`; a tolerância do teste (≤8 px) documenta
   isso.
6. **`layout_de_arte` sempre traz o slot-base `pagina`** — o assert do C8
   ("sem grade" = limpo) confere ausência de `celula_*` e de regiões, não
   lista vazia.

### O que ficou de fora (e por quê)

- **`Regiao.grupo`/P5 NÃO foi construído** (L8) — o Bloco C não o pediu; o
  vínculo célula continua sendo o slot, e "mover a célula inteira" opera
  por ele. Se o arquiteto quiser grupo como entidade própria, é ordem nova.
- **Região nova DENTRO de uma célula da grade**: com o C1, criar nunca mais
  cai no slot da seleção — o caminho para povoar uma mestra é colar/mover.
  Declarado aqui para não parecer regressão.
- **Toasts e tutorial do C9 sem teste de pixel** — a prova é do CONTEÚDO da
  recusa/sucesso (a mensagem certa dispara), não do desenho do toast.
- **QInputDialog nativo em inglês** — segue como no B: o tradutor qtbase
  cobre no app real; a conferência do arquivo de tradução no pacote é do
  Bloco E (CA-08).

**PARADO no fim do Bloco C (L7). O Bloco D não foi iniciado. Aguardando o
selo do arquiteto.**

---

## RESPOSTA DO BUILDER — BLOCO D (Fable 5, 25/07/2026)

O Bloco C foi fechado no commit `ee15eb9` e selado no §6 — com a correção
de diagnóstico do arquiteto que virou a COND-6. Ritual: linha de base da
raiz conferida ANTES de tocar (904/0/0, `bloco_d_baseline.xml`); 5 scouts
de LEITURA mapearam o terreno (D1-D3, D4-D5, D6/D13/D14, D7-D8, D9-D12 —
nenhum escreveu uma linha). Todos os itens na L1: **cada conserto tem a
rodada VERMELHA registrada nesta bancada** (stash dance onde o conserto
veio antes; as saídas estão nos logs `saida_f13/_run_*.log`). Testes novos
em `app/tests/test_bloco_d_f13.py`.

### As duas condições do selo do C, primeiro

| | O que ficou |
|---|---|
| **COND-6** ✅ | O press igualou o hover (`itens.py`: alça SÓ em região selecionada) **e fui além onde a sua condição não alcançava**: o `shape()` default é o `boundingRect()` com a margem ±TAM SEMPRE — a entrega do clique pelo Qt e o `resolver_selecao` (via `scene.items`) davam a região de cima COM margem, selecionada ou não. A margem virou condicional à seleção (com `prepareGeometryChange` no `ItemSelectedChange`). O teste original foi RESTAURADO ao alvo (o arrasto desce em direção ao preço) e o novo `test_cond6_alca_so_existe_em_regiao_selecionada` registrou o vermelho: arrasto no canto de região NÃO selecionada a redimensionava de 40×12 para 28,8×3,4 mm. **Prova de que o seu diagnóstico fecha o caso de ponta a ponta: suíte 905/0/0 ×2 E `--ordem-invertida` 905/0/0 com o alvo original** (`_d_cond6_suite.xml`/`_d_cond6_invertida.xml`). |
| **COND-7** ✅ | Os três vigias RENOMEADOS para o que agora exigem: `test_mut2_e01_criacoes_nascem_selecionadas_e_cada_uma_no_seu_slot`, `test_mut3_r02_botao_subir_traz_a_regiao_para_a_frente`, `test_mut4_e08_alca_de_regiao_rotacionada_redimensiona_com_ancora_parada` — docstrings citam a COND-7 e os nomes antigos (git log `5a4f0d0`/`ee15eb9`). |

### A tabela item × prova (vermelho → conserto → verde)

| # | conserto | vermelho registrado | onde mexi |
|---|---|---|---|
| D1 | **o véu virou FAIXA DE RODAPÉ**: `OverlayOcupado` cobria a tela inteira e comia todo clique (e SÓ o mouse — o teclado atravessava, a assimetria CF-05, que morreu por simetria); agora é uma tira no pé, com spinner+texto+decorrido, e a tela fica LIVRE. Um ponto consertou os 9 chamadores (API intacta). De carona: o lote do Estúdio ligou o `item_pronto` que nunca usara (texto estático de ponta a ponta) | `test_d1_veu_virou_rodape...` — hit-test REAL (`childAt`): "o miolo da tela está coberto por OverlayOcupado" | `carregando.py`, `almoxarifado.py` |
| D2 | **a digitação coalesce**: cada tecla custava `_registrar_hist` (JSON no disco) + `compor_pagina` inteiro + 1 estado de desfazer. `notificar_edicao(adiar=True)` nas fontes de RAJADA; o gesto fecha em ~300ms em `despachar_edicoes()` (flush no desfazer/refazer, troca de seleção, editingFinished, documento novo). E a **prévia compõe a 96 dpi e estica de volta ao tamanho da cena** (alças/réguas/snap intactos — a armadilha do scout) | `test_d2_digitacao_coalesce...` (stash dance): UM desfazer devolvia "Nome Zero"→"Nome"? Não — a rajada era um estado POR TECLA. + guarda `test_d2_previa_rapida_mantem_cena...` | `canvas.py`, `painel_propriedades.py`, `compositor.py` (param `dpi`) |
| D3 | **o detector de fundo branco NASCE ligado** (estava pronto e testado desde a F10, escondido atrás de default False que o dono nunca achou); False explícito na Config continua respeitado; checkbox nasce marcado | `test_d3_detector_fundo_branco_nasce_ligado` (padrão desligado) + o guardião `test_fase10_imagens` VIRADO (a prova de mutação trocou de lado: o False explícito é que precisa vencer) | `fundo.py`, `configuracoes.py` |
| D4 | **categoria pelo VIZINHO, sem exigir o LM**: `Conciliador.categoria_do_vizinho()` público (a linha que a conciliação sempre calculou e jogava fora, VC-051) com DOIS degraus — embeddings com o LM vivo, fuzzy 100% local sem ele; `categorizar_acervo` não aborta mais sem LM (vizinho 1º, IA 2º degrau); origem `"vizinho"` | `test_d4_d5_categoria_pelo_vizinho_sem_lm` (stash dance): "o lote ABORTOU sem o LM Studio" | `conciliacao.py`, `enriquecer_banco.py` |
| D5 | **a categorização vale para o acervo**: na conciliação, produto casado SEM categoria ganha a do vizinho na hora (o índice já está quente; humano nunca é vencido — só escreve onde está VAZIO; PC da loja pula sem drama). E a FRESTA que o scout achou: a grade da Mesa gravava categoria sem `categoria_origem="humano"` — o lote podia vencer o dono | o mesmo teste, partes 2 e 3 | `servico.py` (conciliar_linhas), `planilha.py` |
| D6 | **a sanitização para de apagar palavra**: `remover_inventados` agora DEVOLVE a palavra do dono quando o inventado a SUBSTITUIU (typo da IA: HUPPERS→Ruppers→**Huppers**; limiar 0,75 — reescrita total como "produto"×"bruto" a 0,67 segue o contrato antigo); acréscimo puro (INMETRO/NBR) segue caindo. E o aviso chega nos 2 furos: o modo rápido abre a CURADORIA quando há perda (`_cadastrar_ou_revisar`); o lote NÃO cadastra nome com perda (política RG-20 do enriquecer_banco) e NOMEIA quem ficou | `test_d6_typo...` (a marca sumia inteira) + `test_d6_modo_rapido...` (nenhum aviso; cadastro silencioso) + `test_d6_lote...` (cadastrou VERDE mutilado — provado por conteúdo no banco) | `enriquecimento.py`, `conciliacao_dialog.py` |
| D7 | **a validade viva + o evento (trava #3)**: o ACHADO ESTRUTURAL do scout (fora de todos os dossiês) consertado — o `vazio` do compositor herda o `texto_legal` da página, então o rodapé "Validade da oferta" FORA de célula recebe a validade viva (o marco da F12 contornava com texto_fixo); `self._evento` vive (salvar + reabrir + rascunho — as "duas linhas" que ressuscitam meta/pulso/{evento}); `sugerir_validade` roda TAMBÉM no export | `test_d7_validade_viva_chega_ao_rodape...` (rodapé VAZIO por pixel) + `test_d7_evento_vive...` (evento jogado fora; export sem sugestão) | `compositor.py`, `mesa.py` |
| D8 | **exportar limpo por padrão + Aprovar visível (trava #1)**: as 9 portas viradas — Mesa (`_exportar(rascunho=False)` + paleta "Exportar como RASCUNHO"), perfis/lote (checkbox), Fábrica ×3 (checkbox RASCUNHO na barra), Modo Pai (limpo), Publicar (checkbox), relâmpago/kit/etiquetas (param `rascunho=False`). Botão **Aprovar REAL na barra da Mesa E da Fábrica** (a Fábrica nunca teve caminho — P-07); `checklist_final(cartaz=True)` sem a pergunta da validade da oferta (era o que tornava a aprovação inalcançável lá); a Fábrica ganhou `_salvo` real. A aprovação segue viva como SELO por versão (hash R-068) | `test_d8_etiquetas_saem_limpas_por_padrao...` (o default carimbava) + `test_d8_botao_aprovar_visivel...` (não existia em nenhuma das duas) | `mesa.py`, `fabrica.py`, `servico.py`, `exportar_dialog.py`, `publicar_dialog.py`, `modo_pai.py` |
| D9 | **item↔célula acesos + miniatura**: estante→canvas (selecionar a linha acende a célula, com troca de página), canvas→estante (clicar a célula destaca a linha), guarda anti-laço `_sinc_estante` (o padrão do painel de camadas); a linha da estante ganhou a MINIATURA da foto (26px, cache por caminho+mtime — `setIcon` não aparece sob `setItemWidget`, o molde é o do painel de camadas) | `test_d9_estante_e_celula_acesos...` (stash dance): nenhum dos dois sentidos existia; linha só texto | `mesa.py` |
| D10 | **o pré-voo ganhou o piso da revisora e a nota da foto**: `heuristicas_do_pre_voo` público (nome cortado por medida, preço fora da faixa aprendida, de≤por — dedupe do PROCON no cartaz) + `avaliar_foto` com cache (caminho+mtime) no laço de imagens — só nota RUIM avisa | `test_d10_pre_voo_ganha...` (o pré-voo mudo para os dois sinais) | `servico.py`, `revisora.py` |
| D11 | **o destaque vai para a célula GRANDE**: `area_do_slot` em `grade.py` (a régua mora onde a lei do A7 manda); com heróis ligados, os N mais baratos vão para as N MAIORES células da página 1; o resto segue o zip visual de sempre | `test_d11_heroi_vai_para_a_celula_grande` (o herói caía na 1ª célula da leitura) | `grade.py`, `mesa.py` |
| D12 | **atualizar preços por chave natural**: o 3º botão na caixa do reimport ("Atualizar os preços dos atuais", só aparece quando HÁ par), motor prévia→confirma (`plano_atualizar_precos`/`aplicar_atualizacao_precos` — o molde da ponte Excel R-118); muda SÓ preço/preço_de/multi_preco dos itens da ESTANTE: uid, mapa, overrides e a pilha de desfazer intactos (I1/CD-01); sem-par e não-citados NOMEADOS (I2) | `test_d12_atualizar_precos...` (o botão não existia; "Substituir tudo" zerava mapa e overrides) | `servico.py`, `mesa.py` |
| D13 | **a conciliação lembra**: geometria da janela (chaves por modo foto/tabela, validação dura, molde do ui.shell), colunas de nome viraram Interactive (eram Stretch — o dono nem conseguia arrastar), `resizeColumnsToContents` só na 1ª carga, tudo gravado no `done()` (a saída única); o splitter do modo foto virou `splitter_com_memoria` | `test_d13_conciliacao_lembra...` (860×560 fixo; largura zerada a cada recarga) | `conciliacao_dialog.py` |
| D14 | **o rascunho não ressuscita projeto PRONTO**: o tick de 2 min regravava o estado JÁ salvo (o salvar descartava e o timer recriava — nada olhava a dirty flag); agora projeto LIMPO não gera rascunho; o par anti-exagero prova que sujar DEPOIS do salvar volta a ter rede | `test_d14_projeto_salvo_nao_regrava_rascunho` (regravou) + `test_d14_edicao_depois_do_salvar_volta_a_ter_rede` (o anti-mutação, verde dos dois lados) | `mesa.py` |

### Os guardiões do contrato antigo, VIRADOS (nunca apagados)

`test_fase8_export` (Mesa: aprovação ligava/desligava a marca → limpo por
padrão + rascunho explícito; Fábrica: o monkeypatch de `pode_exportar_limpo`
— o P-07 fossilizado — virou o checkbox real), `test_fase11_cartaz`
(relâmpago "sempre RASCUNHO" → limpo por padrão, opção carimba),
`test_fase12_marco` (etiquetas "o PADRÃO carimba" → o padrão é LIMPO),
`test_fase10_imagens` (detector "padrão desligado" → ligado; o False
explícito vence), `test_onda1_desempenho` (o fake do modo rápido perdia
palavra — com o D6 abriria curadoria; dado sem perda + a prova do motor
virou o `mais18`). Todos com docstring "VIRADO na F13/D8|D3|D6" e o rastro
no git log. O `esta_aprovado`/hash (R-068) segue INTACTO — é o selo.

### O quadro hoje × ideal, MEDIDO (DoD do bloco)

Números na máquina real com as 30 ofertas REAIS do Quintou —
**`saida_f13/bloco_d_medicoes.md`** (tabela completa + ressalvas). Os
destaques: conciliar as 30 reais = **0,07s (30/30 verdes)**; compor a
frente real = **105ms** (e o D2 fez a rajada de 13 teclas custar UMA
recomposição, não 13 ≈ 1,4s); arte 300dpi: prévia **2,0×** mais rápida;
detector de fundo branco **13ms** contra 8–26s de rembg; export
frente+verso **0,17s**; pré-voo com os sinais novos **0,02s**. Ressalva
honesta no arquivo: a arte real do Quintou é 96dpi de fábrica — nela o
ganho do D2 é a coalescência; o ganho do dpi vale para arte 300dpi.

### Os placares (junit em `saida_f13/`)

| prova | resultado |
|---|---|
| suíte da raiz ×2 | **924 verdes ×2, 0 falhas, 0 skips, exit 0** (`bloco_d_suite_1.xml`, `bloco_d_suite_2.xml`) |
| ordem invertida (árvore final) | **924/0/0, exit 0** (`bloco_d_invertida.xml`) |
| janela real | **4/0/0** (`bloco_d_janela.xml`) |

Evolução: 851 (§0) → 862 (A) → 886 (B) → 904 (C) → **924 (D)**. Todas as
quatro rodadas com o para-quedas (`--timeout=120 --timeout-method=thread`)
e log em arquivo.

### Achados próprios de bancada (L6)

1. **A bancada ganhou um para-quedas: `pytest-timeout` (novo dev-dep) é
   LEI das rodadas** (`--timeout=120 --timeout-method=thread`) — duas
   suítes desta bancada penduraram PARA SEMPRE (o D6 mudou um contrato e
   um teste antigo ficou esperando um modal que ninguém responde; sem
   timeout, a fila parava por 40+ min sem diagnóstico). Com o para-quedas,
   o culpado sai NOMEADO com stack trace em segundos. Junto: as rodadas
   pararam de esconder a saída (`Out-Null` → log em arquivo).
2. **Fora do pytest, a bancada fala com o LM Studio REAL da máquina** — o
   diálogo de conciliação dispara a fila de enriquecer ao abrir; num repro
   solto, ela foi ao LM de verdade. Testes de diálogo agora desligam o
   interruptor mestre (`ia.usar=False`) e controlam a corrida da fila
   (semear a proposta SÓ depois de a fila resolver — senão ela sobrescreve).
3. **`Database().init()` concorrente custa ~5s POR CHAMADA sob contenção**
   (medido: 3 threads ≈ 12s; isolado: 0,00s). As filas do diálogo abrem
   uma conexão por chamada (`_motor_se_disponivel`, enriquecer,
   finalizar) — é o mesmo mal do "uma conexão por imagem" que o scout
   apontou no detector. **Anoto nominal para o Bloco E** (é vizinho do
   D-12: as conexões cruas).
4. **Foto de cor chapada tem Laplaciano ZERO** — o avaliador (agora no
   pré-voo, CORRETO) a marca "borrada — RUIM". As fotos sintéticas de 4
   bancadas antigas (50–400px chapadas) viraram o helper
   `acervo.foto_de_bancada` (xadrez nas bordas = nitidez; MIOLO de cor
   pura = os testes de pixel amostram o centro).
5. **`Set-Content` sem `-Encoding` num pipe PowerShell mastiga UTF-8**
   (o arquivo virou mojibake; a pegadinha da memória da bancada Windows
   confirmada da pior forma) — restaurado do git na hora; edições de
   arquivo SÓ pela ferramenta de edição.
6. **O undo RECONSTRÓI o layout do snapshot** — referência guardada a uma
   `Regiao` de antes do desfazer fala com um objeto MORTO; asserts pós-undo
   repescam a região (a lição do wrapper morto do C, agora no modelo).

### O que ficou de fora (e por quê)

- **A porta 10 do scout (miniatura do projeto)** nunca carimbou — com o
  padrão limpo ela ficou COERENTE por natureza (nada a fazer); registrada.
- **O texto do diálogo de recuperação (D14)** não mudou ("fechado sem
  salvar") — com a guarda, o diálogo só abre quando isso é VERDADE; os
  rótulos dos 3 botões são contrato de teste do B2d.
- **O Estúdio (packshot) segue FORA do gate do detector** — o degrau 1
  corta o objeto mesmo em fundo branco por desenho (sombra sintética
  precisa do recorte); não é o caso do VC-037. Nominal para o arquiteto.
- **`disponivel()` tem timeout de 3s** (conferido) — o CA do Bloco E não
  precisa mexer aí; o chat de 300s é que merece olhar lá.
- **A validade do reimport no caminho "Atualizar preços"** fica como está
  (o dono edita pelo rótulo); anotado como refinamento possível.
- **R-116/119/124/125 seguem VETADOS** — nada aqui os tocou.

**PARADO no fim do Bloco D (L7). O Bloco E não foi iniciado. Aguardando o
selo do arquiteto.**

---

## RESPOSTA DO BUILDER — BLOCO E (Fable 5, 25-26/07/2026)

Bloco D fechado no `d7bb6b9`, selado no §7. Baseline conferida antes de
tocar (924/0/0). 3 scouts de LEITURA (boot/exe/log; os 47 I2 + I3;
modo/schema/PRAGMA/índices + §5.5). L1 em tudo — **rodada vermelha em
LOTE registrada** (9 vermelhos de uma vez, produção intocada; logs em
`saida_f13/_run_e_red.log`) + stash dance no E6. Testes em
`test_bloco_e_f13.py`.

### A tabela item × prova

| # | conserto | vermelho | onde |
|---|---|---|---|
| E10/COND-8 | as 2 legendas da lei morta caíram — os rótulos contam a regra viva ("sai LIMPA por padrão; o RASCUNHO é o checkbox"; aprovação = selo); a varredura virou teste PERMANENTE (nenhuma string de UI pode afirmar carimbo automático) | `test_e10_cond8...` (a varredura pegou as duas) | `exportar_dialog.py`, `publicar_dialog.py` |
| E1 | o boot NUNCA baixa: `modelo_baixado()` (o molde do ESRGAN) + `aquecer` no-op sem o .onnx; a PERGUNTA no 1º recorte (`garantir_modelo_recorte`: completo 973 MB / leve ~5 MB gravando na MESMA chave do combo / agora não — Enter no "não", lei do B3) ligada nos 6 chamadores de UI; GUIA_RAPIDO corrigido (as 4 frases: quem baixava era o BOOT, não o recorte — agora o texto é verdade) | `test_e1_aquecer_nao_baixa...` (spy no rembg: o boot carregava sem o arquivo) + `test_e1_primeiro_recorte_pergunta...` | `fundo.py`, `servico.py`, `editor_app.py`, 4 telas, `GUIA_RAPIDO.md` |
| E2 | a rede de erro do exe: `app/core/erros.py` (excepthook encadeado → `logs/erros.log`, append tolerante — molde do vigia) instalada nos entrypoints; o zip de diagnóstico leva os 4 logs (ia SÓ travamentos — o suporte recebia um zip cego) | `test_e2_rede...` + `test_e2_diagnostico...` | `erros.py` (novo), `diagnostico.py`, `editor_app.py` |
| E3 | pasta sem escrita morre CONTANDO: prova de escrita no `criar_estrutura` (mkdir passava; o SQLite morria depois, sem janela) + a fase 1 do boot embrulhada (`_montar_shell_seguro`: caixa crítica legível + traceback no log; `sqlite3.OperationalError` não herda de OSError — o except do launcher nunca pegava) | `test_e3_criar_estrutura_prova...` + `test_e3_fase_nua...` | `paths.py`, `editor_app.py` |
| E4 | Cofre (criar/restaurar/excluir) e `.atpkg` (`aplicar_importacao` — a porta que sobrescreve banco E disco) ganharam `exigir_escrita()`; o snapshot do boot PULA sem drama em somente-leitura; o mapa de `modo.py` parou de se declarar completo (lista o que guardou + nomeia o que segue FORA: lixeira, layouts, eventos, selos, manutenção) | `test_e4_cofre_e_atpkg...` | `cofre.py`, `portabilidade.py`, `modo.py` |
| E6 | `migrar_produtos_absolutos` (o gêmeo do migrar_artes): dentro→relativo, fora-mas-viva→copia para a biblioteca, sumida→aviso com rastro; gancho no boot ao lado do irmão | `test_e6_fotos_com_caminho_absoluto...` (stash dance) | `biblioteca.py`, `editor_app.py` |
| E7 | versão de schema (`PRAGMA user_version`, `VERSAO_SCHEMA=2`) + **backup ANTES de migrar DENTRO do init** — a ordem fica certa por construção (no entrypoint real o ALTER rodava ANTES do snapshot do boot, achado do scout; e com banco machucado a migração rodava SEM backup nenhum); banco do FUTURO não é rebaixado (aviso no log, nunca veto) | `test_e7_migracao...` (banco antigo CRIADO NA MÃO: sem versão, sem backup, backup pós-ALTER) | `database.py` |
| E8 | o PRAGMA chega às conexões fora do hook: as cruas do cofre (×2) e da portabilidade (UPDATE layouts) + **o 8º caminho que o D-12 não citava** — `_sessao_pacote` criava engine SQLAlchemy DIRETO, sem listener (a mesclagem corria sem FK) | `test_e8_sessao_do_pacote...` | `cofre.py`, `portabilidade.py`, `database.py` |
| E9 | índices em `excluido_em` ×3 + `Layout.nome` nos MODELOS **e no migrador** (`_INDICES_NOVOS` + CREATE INDEX IF NOT EXISTS — create_all pula tabela existente: índice novo nunca chegava a banco antigo) | dentro do `test_e7...` (banco antigo ganha os 4 índices) | `models.py`, `database.py` |
| E5 | **PARCIAL — declarado abaixo** | — | — |

### E5 — os 47 I2: o placar honesto (L6)

O scout rastreou os 47 um a um (a tabela completa com arquivo:linha de
HOJE está no relatório; resumo): **6 já consertados** por blocos
anteriores da F13 (CB-01/B5, CD-01/B1, CH-06-hard-deletes/B10, CI-03/B7,
CI-05/B4, L-09/B2e); **2 mitigados com decisão documentada** (CD-05,
CB-t1); **1 invalidado** pelo D8 (o carimbo do selfcheck). Neste bloco
consertei os de PERDA REAL mais graves + toda a frente CA/CB estrutural:

- **CI-01**: a conciliação não enxergava a LIXEIRA — produto excluído
  voltava VERDE calado (o corpus agora filtra `excluido_em`);
- **CI-06**: o upscale do cartaz MATAVA o alfa (`convert("RGB")`) —
  recorte transparente virava retângulo preto; o alfa viaja à parte e
  volta redimensionado;
- **CC-01**: a categoria calculada era jogada fora quando o nome já
  estava certo (o `if` do nome governava o dict inteiro);
- e os estruturais acima (CA-01/02/03 = E1/E2/E3; CB-02 = E4; R-07 fica
  **coberto pelo pré-voo** — a imagem sumida é acusada ANTES, em toda
  porta, pelo validar_composicao; o `continue` do desenho é a degradação
  correta com o aviso já dado).

**Os ~26 restantes ficam NOMINAIS** — cada um com arquivo:linha de hoje
na tabela do scout (CB-03/04/05/08/09/t2, CC-02/06a-f, CD-02/08/t1/t2,
CE-01/04, CF-04/t1, CI-02, R-06, D-03/04/05, A-04, CA-04/05/08/t1 + o
achado novo do scout em `servico.py:457`). Não os escondi: o critério
foi perda de conteúdo real primeiro, e o bloco tem um teto de sessão.
**Peço ao arquiteto: selo parcial do E5 com a lista herdada pelo G, ou a
extensão do E** — os consertos são mecânicos (relatar em vez de engolir)
e o mapa está pronto.

### §5.5 — a lenda do stop() × o segfault do DeferredDelete (a resposta)

Com os fatos do código: **é a mesma FAMÍLIA, não necessariamente a mesma
raiz única.** Os dois lados do mesmo defeito — "objeto agendado para
morrer cujo dono morre primeiro, em registros globais que ninguém zera":
(1) toda animação `DeleteWhenStopped` (4 pontos) e todo véu com
`deleteLater` (6 pontos) têm PAI widget que pode destruí-los antes de o
evento pendente ser entregue — exatamente a condição que o conftest da
F12 descreve ("a entrega É o access violation"); (2) a lenda do stop()
mantinha animações presas em `_VIVAS` — referências Python vivas para
C++ possivelmente morto (o `except RuntimeError` do `_prazo` documenta
que esse estado OCORRE na bancada). **Limites honestos:** o conserto do
B2 mexeu só em `_VIVAS` — não desagenda deleteLater nem muda a
DeletionPolicy; se a lenda fosse a raiz única, a regra do conftest teria
ficado desnecessária, e nada indica isso. E não há dump que nomeie o
objeto do EXIT=139. Conclusão: a regra do conftest (descartar, nunca
entregar) CONTINUA necessária; `animacoes.py` é o maior produtor
conhecido dos dois lados. Recomendação anotada: a fixture `vida` chama
`deleteLater` direto em vez de `morrer()` (o eventFilter do pai fica
instalado) — candidato a arrumação na próxima ordem de bancada.

**E o segfault REAPARECEU nesta própria bancada — pela primeira vez
NOMEADO**: a 2ª passada da suíte do E morreu com 0xC0000005 (access
violation) e o faulthandler do pytest apontou o frame:
`test_ctrl_k_abre_em_duas_telas` (test_fase2_busca.py:74), dentro de
`gestos.drenar()` — o laço de eventos entregando a um objeto Qt já
destruído, no teste que abre o shell INTEIRO (duas telas = crossfade +
véus + animações, o maior produtor). É a assinatura exata da família:
evento pendente × dono morto. Intermitente (a 1ª passada e a invertida,
com os MESMOS testes, passaram; a recadeia também). O dump completo
ficou no histórico da sessão; o alvo agora tem nome e endereço para a
ordem que o caçar.

### Os placares (junit em `saida_f13/`)

| prova | resultado |
|---|---|
| suíte da raiz ×2 | **935 verdes ×2, 0 falhas, 0 skips, exit 0** (`bloco_e_suite_1/2.xml`) |
| ordem invertida | **935/0/0, exit 0** (`bloco_e_invertida.xml`) |
| janela real | **4/0/0** (`bloco_e_janela.xml`) |

Evolução: 924 (D) → **935 (E)**. **Nota honesta das rodadas:** até os
placares fecharem, a bancada do E sofreu (a) o segfault intermitente
0xC0000005 da família §5.5 **duas vezes** — os frames estão nomeados
acima — com a rodada seguinte do MESMO código passando; (b) flakes de
contenção (a poda de versões e as filas da onda1) que passam isolados e
caíram sob carga — a raiz é a contenção do `Database().init()`
concorrente (o achado do D, nominal); e (c) UMA regressão minha real,
pega pela própria bancada: o primeiro fast-path do E7 confiava só na
versão e pulava um banco fabricado com colunas faltando — consertado
(a conferência é sempre pelas colunas/índices DE VERDADE; a versão só
decide se há write).

### O que ficou de fora (e por quê)

- **Os ~26 I2 nominais do E5** (acima — pedido de decisão ao arquiteto).
- **A execução real em Windows limpo** é lição de casa do Otaviano (§3 da
  ordem) — CA-01/02/03 agora têm código e teste, mas nunca foram VISTOS
  rodando no exe.
- **O % numérico do download do modelo**: o pooch manda o progresso ao
  stderr morto; o rodapé do D1 narra com tempo decorrido, mas sem
  percentual (precisaria de downloader custom — nominal).
- **CB-07/CD-t/CB-10** (I3 extras do scout): os leitores toleram legado
  por desenho; o congelado com arte sumida ainda grava o rastro absoluto
  — mexer no formato congelado pede adversarial próprio (nominal).
- **A contenção de ~5s do Database().init concorrente** (achado do D):
  confirmada como vizinha do D-12, NÃO consertada aqui (mudar o ciclo de
  vida do engine é cirurgia de arquitetura — nominal para ordem própria).

**PARADO no fim do Bloco E (L7). O Bloco F não foi iniciado. Aguardando o
selo do arquiteto.**

---

## RESPOSTA DO BUILDER — BLOCO F (Fable 5, 26/07/2026)

Bloco E fechado no `a04c411`, selado no §8. **COND-9 cumprida ANTES de
tudo**: `docs/LEDGER_I2_F13.md` criado com os números exatos — 48 linhas
(47 + 1 extra do scout) · 13 CONSERTADOS · 1 COBERTO (R-07, pré-voo) ·
1 MITIGADO (CD-05) · 1 INVALIDADO · **32 ABERTOS** · 0 DISPENSADOS. O G
zera. Scout único de leitura (§13 + geradores + o lado do app — as 8
tabelas célula-a-célula que o dossiê não tinha). Testes em
`test_bloco_f_f13.py` (16 novos), L1 nos consertos (F1 4/4 vermelhos
registrados em `_run_f1_vermelho.log`; F2 por ImportError em
`_run_f2_vermelho.log` e `_run_f2b_vermelho.log`).

### LEI NOVA DA BANCADA (L6 — mudança declarada): o LM Studio REAL fica FORA

A baseline do F falhou 2× ANTES de qualquer edição minha: o LM Studio
aberto no desktop do dono respondia ao probe de 3 s do
`ClienteOpenAICompat` DENTRO do pytest — teste pendurado/placar
dependente de um app alheio (o mesmo mal do offscreen pré-conftest).
Fixture autouse `_lm_studio_fora_da_bancada` no conftest (patch de
`disponivel()` → False), com escape explícito `@pytest.mark.lm_real` —
usado no teste do interruptor (`test_fase3_config`), que exercita o
código REAL (sem rede: `ia.usar` decide antes). Baseline então travada:
**935/0/0, zero skips, exit-0** (`bloco_f_baseline.xml` — a prática do
artefato de baseline adotada, como o arquiteto pediu no §8).

### A tabela item × prova

| # | o que ficou | prova | onde |
|---|---|---|---|
| F8 | a tabela EXATA, na letra: SENEPOL intocado (grep CENEPOL segue vazio); "CRIADA E PRODUZIDA"→"CRIADO E PRODUZIDO" nos DOIS (`gen_carne_final.py` + `gen_segunda3.py`); "MARCA PRÓPRIA" só da faixa fixa (os subtítulos de exemplo `:126+` intocados); "fatiados na hora" só no cabeçalho (`:318` fica); o período do Jornal EDITÁVEL (orelha, manchete e título-p2 movidos est→ex — o app escreve; + a linha-fina "até o fim do mês", a MESMA alegação em paráfrase, movida e declarada como extra); logo relativo nos 7 (`_RAIZ` por `__file__`) | grep de conferência limpo + `py_compile` dos 7 = exit 0 | `Templates novos/geradores/` (fora do git) |
| F8+ (extras N-08, declarados) | os 21 caminhos de SAÍDA absolutos (`/home/claude/encartes/final-*`) também viraram relativos (→ `artes/<encarte>/`) — sem isso "antes de qualquer regeração" era letra morta; e os writes ganharam `encoding='utf-8'` (no Windows o `open('w')` cru sai cp1252 e mastiga os acentos do SVG — a pegadinha do Set-Content que virou lei no D) | idem | idem |
| F1 | célula FIXA no modelo: `Slot.fixa` (aditivo, molde do `rotacao_graus`; layout antigo carrega False); `ocupaveis` é o PONTO ÚNICO — fixa fora da fila e fora do aviso de vazios/pré-voo (a lei do tipo novo aplicada); gesto RG-56 no menu da célula ("Célula fixa (fora do auto-preencher)" ⇄ "Devolver…"), com undo | 4 vermelhos → 4 verdes: roundtrip+migração, ocupaveis, **adversarial I5 na Mesa real** (a fixa GIGANTE entre 2 livres — sem o filtro, o D11 entregaria o herói JUSTAMENTE a ela; por uid), menu marca-e-desmarca | `model.py`, `grade.py`, `canvas.py`, `itens.py` |
| F2 | o extrator por DADOS: `app/rendering/encartes.py` — as 8 tabelas do scout transcritas na escala 1× do viewBox (96 dpi), página do BASE.png real a 192 dpi (2160×2880 = ×2 exato ⇒ 285,75×381 mm, composição 1:1); 92 células; fontes do pacote por região (Archivo/Fraunces/Nunito/Anton); `layout_de_encarte` + `chaves_do_pacote` + `importar_pacote` (upsert por NOME, arte internada I3, fontes copiadas) + botão "Importar encartes…" no Ateliê (encarte incompleto NOMEADO no toast, I2) | contagens/fixas/mm/roundtrip por encarte + I3 (grep "Templates novos" no JSON persistido = vazio) + importar 2× não duplica | `encartes.py` (novo), `atelie.py` |
| F2/Jornal (N-04) | o caminho próprio: 20+22 células das listas `ch`/`linha(y, ids)` num LayoutDef de DUAS páginas (fundo POR página; ids únicos `jp1-*`/`jp2-*`, D8.1 validado no roundtrip); validade/nº da edição/Fica-a-Dica desenhados pelo app (o BASE zera o exemplo INTEIRO) | teste próprio (42 ocupáveis + DICA e VALIDADE nas duas + seções ligadas) | `encartes.py` |
| F3 | destaque por área VALIDADO no encarte real: na Quarta, o herói cai no BANNER (celula-var-5, a maior LIVRE — o que o gerador reservava ao destaque) e nunca nas 3 fixas da Coluna do Dia | teste na Mesa real com o layout extraído (por uid) | teste |
| F4 | Fica-a-Dica: região TEXTO_LEGAL papel DICA nas duas páginas do Jornal (slot decorativo, não-ocupável por A7); a propagação da mestra é o C12 (já selado) | dentro do teste do Jornal | `encartes.py` |
| F5 | seções: o Jornal nasce com `secoes_ligadas=True` nas 2 páginas (N-05 — a arte não traz seção; quem desenha é `secoes.py`, F8.2) | idem | idem |
| F6 | validade ROTACIONADA por encarte: papel VALIDADE na posição/rotação do selo de cada arte (Terça 8°, Segunda 10°, Quarta −2°, Peixe −7°, Sexta −6°, Sábado 9°, Jornal 0°) — o compositor já gira pelo RG-12; **prova por PIXEL no DoD** (com/sem texto → tinta na área do selo, nas 8 páginas) | teste das 7 rotações + a prova de tinta do DoD | `encartes.py`, compositor (intocado) |
| F7 | oclusão da Terça (N-01): o 1º slot de foto do combo nasce ENCOLHIDO (210→194 px) — nenhum canto de caixa de foto dentro do círculo do selo de 25% gravado no BASE (centro 964,392, R54) | teste geométrico (distância canto→centro ≥ raio, com os 4 cantos de TODAS as fotos) | `encartes.py` |
| F9 | o "20%" vira PARÂMETRO no gerador (`pctpod(..., pct='20%')`, chamador explícito) **e a ponta do app**: a 3ª fixa da Quarta declara papel DESCONTO — o % é CALCULADO de (de−por)/de (R-109), nunca digitado; na galeria aparece o **−34% real** dos dados de teste | teste da fixa-3 + inspeção visual | `gen_final.py`, `encartes.py` |
| F10 | o "ã" do Baloo: no gerador, os minis saem do Baloo 2 → Nunito 800 (o ÚNICO ã/Ã em Baloo do pacote era "Pão de Queijo"); no app, NENHUMA região da Quarta usa a instância defeituosa (produto variável pode ter "ã") | teste (varredura de fonte no layout) | `gen_final.py`, `encartes.py` |

### O DoD — os 7 montados, por pixel, e a inspeção visual que MORDEU

`test_f_dod_os_sete_montados_por_pixel_vs_preview`: os 7 encartes (8
páginas) compostos com as **30 ofertas REAIS do Quintou** (o padrão-ouro
do marco: `campanhas_do_marco` + `itens_reais_da_campanha`; fotos de
bancada nítidas do D10), a 2160×2880, comparados ao PREVIEW do pacote:

- **régua rigorosa (app)**: nenhum slot de foto sai vazio — diff>3% vs o
  BASE na caixa da foto, nos 100% dos slots das 8 páginas;
- **régua cruzada (PREVIEW)**: onde o exemplo põe conteúdo no bbox da
  célula (diff>2%, limiar 16), o app também põe. *Achado honesto da 1ª
  rodada:* o miolo da foto NÃO serve de régua no PREVIEW — o exemplo usa
  placeholder semitransparente, invisível por pixel sobre célula clara;
  a régua foi movida ao bbox da célula (onde vive o carimbo/bandeira) e
  o desvio ficou NOMEADO no próprio teste (teto de 3 exceções);
- **galeria lado-a-lado** (app | PREVIEW) em
  `saida_f13/galeria_bloco_f/` — 8 imagens, TODAS inspecionadas
  visualmente por mim, uma a uma.

**A inspeção visual pegou 3 defeitos que a suíte verde não pegou** (a
lei do dono funcionando) — consertados e re-inspecionados:

1. **Sábado**: as caixas de UNIDADE e PREÇO dividiam faixa ("100 g"
   espremido sobre o "R$") nas células curtas E altas — retabelado;
2. **Segunda**: o nome centrado na banda alcançava a área do selo de
   cera — as etiquetas ganharam coluna do lado do selo (`'d'/'e'`) e o
   texto DESVIA, como o exemplo faz;
3. **Jornal**: o BASE.png atual é o PRÉ-regeração — manchete/orelha/
   título-p2 que o F8 moveu para o app ainda estão GRAVADOS no fundo, e
   escrever ali duplicava o texto (sopa de letras). As caixas ficam
   PRONTAS e SEM tinta até a regeração (comentadas no código); a
   validade oficial fica na faixa/linha que o BASE já zera — limpa nas
   duas páginas.

### Os placares (junit em `saida_f13/`)

| prova | resultado |
|---|---|
| baseline (pré-bloco) | **935/0/0, zero skips, exit 0** (`bloco_f_baseline.xml`) |
| suíte da raiz ×2 | **946 verdes ×2, 0 falhas, 0 skips, exit 0** (`bloco_f_suite_1/2.xml`) |
| ordem invertida | **946/0/0, exit 0** (`bloco_f_invertida.xml`) |
| janela real | **4/0/0** (`bloco_f_janela.xml`) |

Evolução: 935 (baseline) → **946 (F)** — os 11 testes do bloco. Nota
honesta: as 4 rodadas do fecho passaram de primeira, sem segfault e sem
flake — a primeira bancada de bloco SEM incidente desde o C; a fixture
do LM real tirou a variável de fora.

### O que ficou de fora (e por quê)

- **A regeração dos BASE/MASTER/PREVIEW**: o pipeline do pacote é
  Playwright+Chromium (README §"Como regenerar") e as fontes precisam
  estar instaladas no sistema — não roda nesta máquina sem instalação
  que não fiz por conta. As FONTES `.py` estão corrigidas e portáteis;
  os PNGs atuais seguem com as strings velhas (a faixa do Sábado, a fita
  da Segunda, o "mês inteiro" do Jornal) até o dono/arquiteto regenerar.
  Por isso as 3 caixas do período do Jornal nascem sem tinta.
- **Estilo fino da composição** (cores/pesos por região, preço em disco
  vs texto reto, quebra "R$"/valor em caixa estreita): as regiões nascem
  com as FAMÍLIAS do pacote e caixas fiéis, mas o acabamento visual
  (pill, contorno, cor por papel) é trabalho de estilo no editor — G.
- **O pivô das cestas da Terça**: o gerador rotaciona em (cx, 1000); o
  modelo rotaciona por região no CENTRO — em ≤0,7° a diferença é <2 px
  (declarado no cabeçalho de `encartes.py`).
- **O combo da célula-2 da Terça** tem 2 caixas de IMAGEM no MESMO slot
  fixo (Sonho + Croissant) — a mesma foto sai nas duas até o dono trocar
  no editor (DIY); separar em 2 slots quebraria "1 célula fixa = 1
  conteúdo do dono". Decisão declarada.
- **A moldura de seção do Jornal na galeria** é o estilo padrão
  (CONTORNO) com dado uniforme do teste (categoria única ⇒ UMA seção
  gigante azul). Com categorias reais o app desenha grupos menores; o
  estilo/títulos são configuráveis (F8.2). Não mexi no desenho de seções.

**PARADO no fim do Bloco F (L7). O Bloco G não foi iniciado. Aguardando o
selo do arquiteto.**
