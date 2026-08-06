# ORDEM F13-SEXTUSDECIMUS — UMA LINHA, UMA CÉLULA

> **Emitida pelo arquiteto em 02/08/2026**, depois de o dono relatar o Jornal do Mês travando
> nos itens de vários sabores, e de eu **rodar o app na máquina dele** e reproduzir tudo.
>
> Ele foi explícito no foco: *"vamos fazer um funcional primeiro, porque eu vou usar pra fazer
> o jornal do mês. Então tem que estar funcionando bonitinho toda essa parte de pesquisar
> imagem, de criar item, de fazer todo esse banco de dados, na hora de inserir também."*
>
> **Esta ordem não é uma lista de bugs. É o MODELO** — o que "uma linha com mais de um produto"
> significa da tabela até a tinta. Os bugs são consequência de o modelo nunca ter sido escrito.

---

## §1 · A PERGUNTA DELE QUE ORGANIZA TUDO

> *"Eu só seleciono um sabor, e daí ele aparece e não aparece nem o nome do sabor quando tá nos
> jornais. **Como é que ele sabe qual sabor que eu tô selecionando?**"*

**Resposta medida: não sabe.** `servico.py:3062` grava a foto no sabor de índice 0 e passa `None`
para todos os outros:

```python
finalizar_criacao(sub, nome, mais18,
                  imagem_tratada if i == 0 else None,   # ← aqui
                  categoria=categoria)
```

**Provado no banco real dele**, nas duas famílias que existem:

```
FAMÍLIA [1] Sardinha Coqueiro 125g          FAMÍLIA [2] Bis Lacta Xtra 45g
   FOTO  id=75  … Tomate                       FOTO  id=78  … Branco
   SEM   id=76  … Óleo                         SEM   id=79  … Oreo
   SEM   id=77  … Limão
```

**Sempre o primeiro, nunca o resto.** E como o campo que alimenta o desenho é `item.imagem`
(singular), que pega *a primeira membro que tenha foto*, **o "leque" nunca se forma** — é sempre
uma foto só. O recurso foi entregue como pronto e nunca funcionou além do sabor nº 1.

---

## §2 · O MODELO — três formas de "uma linha, mais de um produto"

A tabela dele mistura três coisas na mesma coluna de descrição. O app **já sabe distinguir** as
três (`familia_da_linha`, `dividir_em_dois`); o que falta é **levar as três até o fim**.

| Forma | Exemplos REAIS da tabela dele | No BANCO | Na PÁGINA |
|---|---|---|---|
| **SABORES** — mesma marca, mesmo peso, varia o sabor/fragrância | `BIS LACTA XTRA 45 g BRANCO e OREO`<br>`SARDINHA COQUEIRO 125 g TOMATE / OLEO e LIMÃO`<br>`AMACIANTE MON BIJOU 5 LTS PROTEÇÃO e CLASSICO` | **N produtos**, um por sabor, na mesma **família** | **1 célula**: N fotos lado a lado, nome-base, sabores no **descritor**, 1 preço |
| **COMPOSTO** — produtos diferentes na mesma oferta | `ARROZ SOMAR e TIO BONINI 5 Kg`<br>`MOLHO TOMATE FUJINI e CAJAMAR 300 g`<br>`MILHO VERDE FUGINI POUCH e BONARE 170 g LATA` | **N produtos** independentes (sem família) | **1 célula**: nome composto, N fotos lado a lado, 1 preço |
| **PRODUTO SÓ** — o "e" faz parte do nome | `BISCOITO BULNEZ e ADORALLE 270 g …` | 1 produto | 1 célula normal |

### §2.1 · O INVARIANTE QUE FALTAVA (decisão do dono, 02/08)

> ### **I6 — UMA LINHA DA TABELA = UMA CÉLULA DO ENCARTE. SEMPRE.**
>
> Quantos produtos nascem no banco é assunto do **banco**. A **página** recebe **uma célula por
> linha da oferta**, com N fotos dentro. Um Jornal de 42 linhas ocupa 42 células, não importa
> quantos SKUs cada linha esconda.

Isso resolve de uma vez o dimensionamento (42 linhas ↔ 42 slots), o preço (um por linha) e a
pergunta "onde entra o sabor" (no descritor, não no nome).

### §2.2 · A anatomia da célula de sabores

```
┌──────────────────────────────┐
│  [foto Branco] [foto Oreo]   │  ← N fotos, lado a lado (arranjo já existe)
│      Bis Lacta Xtra 45g      │  ← NOME = nome-base da família
│       Branco ou Oreo         │  ← DESCRITOR = os sabores, unidos por "ou"
│         R$ 4,94              │  ← UM preço (o da linha)
└──────────────────────────────┘
```

O descritor já é o lugar do peso e da marca (`"Crocante · 100 g"`). Os sabores entram nele pela
mesma régua: `"Branco ou Oreo · 45 g"`.

---

## §3 · OS PONTOS DE QUEBRA (medidos, com causa-raiz)

### M1 🔴 · Só o sabor nº 1 recebe foto
`servico.py:3062`, `imagem_tratada if i == 0 else None`. Provado no banco (§1).

### M2 🔴 · A curadoria não tem onde receber N fotos
Uma busca, uma grade, um "Usar esta". Não existe vínculo foto↔sabor — o código chuta o índice 0.
**É a pergunta literal do dono.**

### M3 🔴 · O nome do sabor nunca chega à página
`servico.py:3072`, `item.nome = nome_familia`. A célula imprime "Sardinha Coqueiro 125g" e o
cliente não descobre que existem três sabores. *"não aparece nem o nome do sabor"*.

### M4 🔴 · O leque nunca se forma
`servico.py:3078`, `item.imagem = next((m["imagem"] for m in membros if m.get("imagem")), None)`
— **singular**. Mesmo que as N fotos existissem, o que alimenta o desenho é uma só. O
`ModoArranjo.LEQUE` e o `arranjo.py` estão prontos e **nunca recebem mais de uma imagem** por
este caminho.

### M5 🔴 · O composto tem a MESMA doença
No banco dele, da tentativa anterior do Bis: `id=60 "Biscoito Bis Lacta Xtra Branco"` **com foto**
e `id=61 "Biscoito Oreo"` **sem**. `criar_como_composto` aceita lista de fotos; **a curadoria só
coleta uma.** É o que ele descreveu: *"ele não deixa eu usar duas imagens diferentes"*.

### M6 🔴 · "Salvar projeto" SEMPRE cria um projeto novo
`projetos.salvar_projeto()` aceita `projeto_id=` e sabe atualizar. **Os dois únicos chamadores da
interface não passam:**

- `app/qt/telas/mesa.py:999`
- `app/qt/telas/fabrica.py:444`

**Consequência medida na tela dele** — o evento Segunda dos Frios tinha, para a MESMA edição:

```
"03/08/2026"                      Tabloide · 02/08 22:02   [EXPORTADO]
"Segunda dos Frios 03/08/2026"    Tabloide · 02/08 21:56   [RASCUNHO]
```

**Consequência que ninguém tinha visto:** `_gravar_versao` só roda quando `projeto_id is not
None`. Como nunca é, **a linha do tempo de versões (Fase 2, passos 57–60) é código morto** — o
menu "Versões…" existe, abre, e nunca terá o que mostrar.

**Conserto:** `projeto_id=self._projeto_id` nos dois. E o diálogo passa a ter **"Salvar"**
(grava por cima, sem perguntar nome) e **"Salvar como nova edição…"** (o de hoje).

### M7 🔴 · "Duplicar (nova edição)" não atualiza a tela do evento
**Reproduzido por mim:** dupliquei "Segunda dos Frios 27/07" → a grade continuou com **3**;
saí para Início, voltei → **4**, com o duplicado lá. O `recarregar()` do menu atende a lista do
Dashboard, **não a grade do drill-down de evento**.

### M8 🟠 · O rascunho ressuscita porque nada nunca fecha
*"ele sempre acha que é um rascunho… ele fica empacando as coisas por causa disso."* Não é bug
próprio: como todo salvar cria projeto NOVO (M6), o projeto aberto nunca fica "salvo". **Morre
junto com o M6** — mas exige o teste: abrir projeto → editar → Salvar → fechar → reabrir o app
**não oferece rascunho**.

### M9 🟠 · "Próximos eventos: —" com a Segunda amanhã
Medido no Início: o cartão está **vazio**, e amanhã (03/08) é Segunda dos Frios. O cabeçalho dos
Eventos sabe do *Dia dos Pais* (evento de calendário) mas **nada projeta os eventos SEMANAIS** —
que são justamente os que ele faz toda semana. *"Às vezes eu sugeri um negócio correto, que seria
o de amanhã, que seria a segunda. Ele não sugere."*

### M10 🟠 · O duplicar sugere "(nova)" em vez da próxima data
Num evento semanal cujos projetos se chamam "Segunda dos Frios 27/07", a sugestão óbvia é
**"Segunda dos Frios 03/08"** — a próxima ocorrência do dia da semana do evento.

### M11 🟠 · As duplicatas já nascidas
**4 produtos para 2 SKUs reais** (ids 60, 61, 78, 79). Decisão do dono nesta rodada: **fundir
automático** pela chave natural, **mantendo a que tem foto**, com **relatório do que foi fundido**
e reversível (soft-delete, R-075 já existe).

---

## §4 · AS DECISÕES DO DONO (02/08 — travadas)

1. **Sabores na arte:** *uma célula só*, fotos lado a lado, nome-base, sabores no descritor,
   um preço. → **I6**.
2. **Coleta das fotos:** *uma tela com um espaço por sabor* — cada sabor com sua busca já
   semeada (`"{base} {sabor}"`) e seu quadradinho. Ele preenche os que quiser e segue.
   Sabor sem foto **avisa** (I2), nunca some calado.
3. **Duplicatas:** *fundir automático pelas iguais*, mantendo a que tem foto, com relatório.

---

## §5 · ORDEM DE ATAQUE

**Onda 1 — o Jornal do Mês fecha (é o que ele vai usar):**

1. **M2** — a tela de N fotos (a decisão 2). É a porta por onde M1/M4/M5 se resolvem.
2. **M1 + M4** — cada sabor grava a SUA foto; o item leva a **lista** ao desenho (o `arranjo`
   já sabe desenhar; falta alguém entregar mais de uma imagem).
3. **M3** — o sabor vai ao **descritor** (`"Branco ou Oreo · 45 g"`), nunca some.
4. **M5** — o composto usa a mesma tela e o mesmo caminho de N fotos.

**Onda 2 — parar de sujar o acervo e o histórico:**

5. **M6** — `projeto_id` nos dois chamadores; "Salvar" × "Salvar como nova edição…"; e o
   **versionamento sai do coma** (o teste prova que "Versões…" mostra a versão anterior).
6. **M7** — a grade do evento recarrega no duplicar.
7. **M8** — o teste do ciclo fechado (salvar → fechar → reabrir sem oferecer rascunho).
8. **M11** — a fusão das duplicatas, com relatório.

**Onda 3 — o dia a dia:**

9. **M9** — os eventos semanais entram em "Próximos eventos".
10. **M10** — a próxima data como nome sugerido no duplicar.

---

## §6 · PROVA DE ACEITAÇÃO (literal, na máquina dele, com a IA nos DOIS estados)

> O dono importa `Jornal do Mês Agosto.jpeg` e:
>
> 1. na linha `SARDINHA COQUEIRO 125 g TOMATE / OLEO e LIMÃO` ele marca "são sabores", vê
>    **três espaços de foto rotulados** (Tomate, Óleo, Limão), escolhe as três;
> 2. o banco fica com **três produtos, os três COM foto**, na mesma família;
> 3. a página desenha **UMA célula** com as **três fotos lado a lado**, nome
>    "Sardinha Coqueiro 125g", descritor **"Tomate, Óleo ou Limão · 125 g"**, um preço;
> 4. na linha `ARROZ SOMAR e TIO BONINI 5 Kg` ele marca "são 2 produtos", vê **dois espaços**,
>    escolhe as duas fotos, e a célula sai com **as duas fotos** e o nome composto;
> 5. ele abre um projeto salvo, muda uma coisa, clica **Salvar** — e **não nasce projeto novo**;
>    o menu **"Versões…"** mostra a versão anterior;
> 6. ele duplica uma edição e ela **aparece na hora**;
> 7. ele fecha e reabre o app: **não é oferecido rascunho** do que já salvou.

Cada item acima se mede **abrindo o `core.db` dele e olhando a página** — nunca em página de
fábrica (lição da UNDECIMUS) e nunca só por `assert` (lição da L12/§12.8).

---

## §7 · Nota de método — o recurso entregue pela metade

O `criar_familia_de_sabores` tem um docstring honesto:

> *"A foto da curadoria vai ao 1º sabor; os demais completam pelo Almoxarifado (avisado — o
> pré-voo cobre, I2)."*

Estava **escrito**. E ainda assim foi relatado como entregue, e o dono passou uma noite tentando
usar. O aviso do pré-voo não é substituto de um recurso: **"o resto o dono completa à mão" não é
degradação graciosa — é a funcionalidade faltando.**

Lei que esta rodada acrescenta:

> **L14 — MEIA FUNÇÃO NÃO É FUNÇÃO.** Recurso que só atende o primeiro de N (primeira foto,
> primeira página, primeiro item) **não é entregue** — é protótipo. Ou fecha o N, ou a tela
> **não oferece** a opção. O que não pode é oferecer "são 3 sabores", aceitar, e resolver 1.

E o corolário que vale para mim também: **o docstring que confessa a limitação tem de virar
linha do relatório**, não nota de rodapé no código. Eu li esse arquivo em três auditorias antes
de o dono tropeçar nele.

---

# RESPOSTA DO BUILDER (02/08/2026) — a ordem executada

**A L14 e o I6 estão ACATADOS** — e o L14 guiou a rodada inteira: nenhum ramo novo
resolve só o primeiro de N.

## R.1 · Onda 1 — o N fechou (M1–M5)

**M2 — a tela da decisão 2, na letra**: `FotosPorSaborDialog`
(`app/qt/telas/fotos_por_sabor_dialog.py`) — um CARTÃO por sabor (rótulo + quadradinho de
miniatura + Buscar/Arquivo/Limpar), a busca de cada espaço JÁ SEMEADA com
`"{base} {sabor}"` (visível no tooltip), resumo vivo "n de N com foto — o que ficar vazio
aparece no pré-voo" (I2). Reusa o funil do FotosItemDialog (busca → CuradoriaDialog →
tratar), com `buscador`/`tratador` injetáveis (a bancada roda sem web/rembg), o
`done()` que encerra workers (a lição do crash de QThread órfã) e o `clampar_a_tela` da
L3 no show. **Cancelar cancela**: o item segue vermelho — nada nasce pela metade.

**M1+M4 — cada sabor grava a SUA foto e o leque se forma**:
`criar_familia_de_sabores` aceita a LISTA paralela aos sabores (o `if i == 0` morreu; a
compat str→1º segue, o padrão do composto). Provado no banco: 3 sabores da Sardinha, os
3 COM `caminho_imagem`, `item.imagens` com as 3 — o `arranjo.py` finalmente recebe mais
de uma imagem por este caminho.

**M3 — o sabor NUNCA some da página**: `ItemMesa.sabores` novo (round-trip do projeto,
I1) + `juntar_com_ou` ("Tomate, Óleo ou Limão") + o descritor do desenho abre com os
sabores (`dados_para_desenho`): a célula sai **nome-base + "Branco ou Oreo · 45 g"** —
a anatomia do §2.2. O `aplicar_sabores` (o check pós-casamento) preenche pelos membros
escolhidos via `sabor_do_membro` (nome sem o prefixo da família).

**M5 — o composto usa o MESMO caminho**: a linha multi (sabores OU 2 produtos) da
curadoria abre a tela de N espaços e a lista atravessa o `_cadastrar` até
`criar_familia_de_sabores`/`criar_como_composto` (que já falava o plural). No composto a
busca semeia pelo nome completo do componente (base vazia).

## R.2 · Onda 2 — o acervo e o histórico param de sujar (M6–M8, M11)

**M6 — o salvar por cima**: `projeto_id=self._projeto_id` nos DOIS chamadores
(mesa/fabrica); com projeto aberto, "Salvar" grava POR CIMA **sem reabrir o diálogo de
nome** (o nome vive em `_projeto_nome`, setado no abrir e no salvar) e o toast diz que a
anterior está em "Versões…" — **o versionamento saiu do coma** (provado: `listar_versoes`
≥1 após o 2º salvar). O gesto explícito "**Salvar como nova edição…**" entrou na paleta
(Ctrl+K), com sugestão "Nome (nova edição)" — o espelho do Duplicar do Dashboard.

**M8**: no mesmo teste, um rascunho vivo antes do salvar-por-cima morre depois
(`carregar_rascunho() is None`) — o ciclo fecha; e o vigia do teste ACUSA se o diálogo de
nome reabrir.

**M7 — a grade recarrega**: o dashboard lembra `_evento_aberto`; o `_recarregar_agora`
com a pilha no drill-down REFAZ a visão do cache novo (o " Início" limpa a lembrança).
Teste: salva a 2ª edição → a grade aberta vai de 1 a 2 sem sair e voltar.

**M11 — a fusão**: o critério do vencedor virou o da decisão 3 (**quem tem foto vence**;
empate → o mais antigo) em `achar_duplicatas` + `fundir_duplicatas_automatico` com
relatório (I2), reversível. **Achado honesto do scout**: a varredura automática no acervo
real devolve **0 pares** — a chave natural é conservadora e os 4 do Bis têm nomes
textualmente DIFERENTES ("Biscoito Bis Lacta Xtra Branco" ≠ "Bis Lacta Xtra 45g Branco").
A fusão deles foi **CIRÚRGICA e dirigida** (o padrão do id=70/id=50), com backup
`core_pre_sextusdecimus_20260802.db`: 60→78 (2 aliases + a foto virou versão) e 61→79
(2 aliases); 76 produtos ativos. O critério continua conservador de propósito — fundir
por semelhança solta fundiria produto errado.

## R.3 · Onda 3 — o dia a dia (M9, M10)

**M9**: o cartão "Próximo evento" agora SOMA (L12): o `dia_semana` gravado OU o dia lido
do NOME pela cascata `dia_do_evento` ("Segunda dos Frios" → segunda) — os eventos
nascidos do texto ficavam de fora e o cartão dizia "—" com a Segunda amanhã. Com
offset 0/1 o cartão diz "(hoje)"/"(amanhã)".

**M10**: `nome_da_proxima_edicao` — "Segunda dos Frios 27/07" duplicada no domingo
sugere "**Segunda dos Frios 03/08**"; duplicada NA própria segunda pula à semana
seguinte; sem data no nome, anexa; sem dia conhecido, o "(nova)" de sempre.

## R.4 · Achado de bancada — o GIL faminto (a instrumentação do §15.3)

O flake do `test_a4` tem NOME agora: o laço apertado de `drenar()` esfomeia o GIL e o
worker rasteja (medi: função de 0,11 s levando >15 s sob o laço; o faulthandler mostrou o
worker VIVO andando em `pathlib.mkdir`). O `_esperar` das bancadas intercala
`time.sleep(0.05)` (solta o GIL de verdade) e, no estouro, imprime o dossiê. O mesmo
achado explicou por que o teste da costura M2 "não cadastrava".

## R.5 · O que ficou de fora (nomeado)

- A prova de aceitação **§6 é do dono na máquina** (importar a foto, marcar "são
  sabores", ver os 3 espaços rotulados) — os análogos headless estão todos verdes; falta
  o gesto dele.
- K5–K9 da QUINTUSDECIMUS (Pas Sate Mpo, Mili×Milli, peso divergente impresso, Fica a
  Dica repetindo validade, herói desequilibrado) e K10 (a porta da frente — Bloco G).
- "AMSTEL L" (ruído de OCR da releitura); a linha de relatório quando a conciliação muda
  de alvo entre rodadas.
- 2ª..Nª curadoria de foto por sabor no ALMOXARIFADO (o menu "Sabores da família…" ainda
  usa o fluxo antigo — a tela nova pode ser plugada lá na próxima rodada).

## R.6 · Testes e contratos editados

**12 testes novos** em `test_sextusdecimus.py` (M1, M3×2, M5, M2×2, M6+M8, M6-fábrica,
M7, M11, M9, M10). Contrato de teste antigo editado de propósito: **nenhum** — a compat
str/None dos criadores preservou os chamários antigos (test_j13/test_aplicar_sabores/
test_composto seguem verdes sem edição); o `_esperar` do diaadia ganhou o sleep+dossiê
(infra de bancada, não contrato).

## R.7 · Placares

- Suíte completa ×2: **1172 + 1172 verdes, zero skips, exit 0**
  (`bloco_sx_run1/run2.xml`). Ordem invertida: **1172 verdes, exit 0** — LIMPA,
  **inclusive o test_a4**: o conserto do GIL no `_esperar` matou o flake onde ele
  morava (a prova de que o diagnóstico do R.4 era a causa, não rótulo). Janela real:
  **4 verdes**. Placar SÓ por junit.
- L13: os 8 encartes recompostos ×2 nesta rodada — diffs: só os 2 do K3-v2
  ("Multi Uso" inteiro), explicados no §16.2 da QUINTUSDECIMUS.
- Prova visual: `saida_f13/jm-prova-p1/p2.png` recompostas pós-higienização
  (42 itens, 20+22, 0 sobras; sem foto 7/20 e 17/22 declarados; +18 na Amstel e
  Campari; "SUPER OFERTA · R$ 18,81" e "· R$ 6,90" no pixel).
- Banco real: backup `core_pre_sextusdecimus_20260802.db`; fusão automática 0 pares
  (relatório honesto); cirúrgica 60→78 e 61→79; 76 produtos ativos.
