# ORDEM F13-QUARTUSDECIMUS — A FOTO TEM DE ENCHER A ZONA (e a unidade nunca se perde)

> **Emitida pelo arquiteto em 28/07/2026.** O dono: *"na Terça ficou com mais espaço, mas comeu
> informações… na Quarta essas imagens ficaram toscas encostadas na parte mais baixa… o
> salgadinhos também é BB-X e 100 g e não aparece… dá pra reposicionar esses textos um pouco
> mais para baixo e deixar essas imagens mais imponentes."*
>
> Os dois problemas têm **causa medível**, e eu medi. Nenhum dos dois é questão de gosto.

---

## §1 · POR QUE AS FOTOS DA QUARTA ENCOSTAM NO CHÃO

Li a geometria das três células fixas no **banco dele** — e ela **confere** com o gerador
(o layout não está velho desta vez):

```
celula-fixa-1..3
   IMAGEM   244 × 432 px      ← zona ALTA e ESTREITA (proporção 0,56)
   NOME     296 × 120         ← à DIREITA da foto
   SUBTITULO 296 × 44
   PREÇO    216 × 104
```

E as fotos que ele mandou:

| Foto | Tamanho | Proporção |
|---|---|---|
| `Salgados.jpg` | 1080×1080 | **1,00** (quadrada) |
| `Pão de Queijo.jpg` | 1920×1080 | **1,78** (larga) |
| `Lanche na Chapa.jpg` | 1000×667 | **1,50** (larga) |

**As três são mais largas que altas. A zona é mais alta que larga.**

O `Ajuste.ASSENTAR` escala pela dimensão limitante (a largura, 244) e **ancora no rodapé**.
Uma foto quadrada vira 244×244 dentro de uma zona de 244×432:

```
   ┌─────────┐  ← 188 px de VAZIO em cima
   │         │
   ├─────────┤
   │  foto   │  244×244
   └─────────┘  ← encostada no chão
```

**A foto ocupa 56% da área da zona.** É exatamente o que ele descreveu: pequena e grudada
embaixo. Nas cinco células livres (zona 281×236, **larga**) as fotos largas se encaixam bem —
por isso a coluna da direita ficou bonita e a da esquerda não.

### Q1 🔴 · A REGRA NOVA: a foto enche a zona, ou a zona muda de forma

> **Toda foto tem de ocupar ≥ 85% da área da sua zona.** Se a proporção da foto e a da zona
> divergirem a ponto de impedir isso, **é a ZONA que se adapta — nunca a foto que encolhe e afunda.**

Três saídas, nesta ordem de preferência:

1. **Re-proporcionar a zona dentro da célula.** A célula fixa da Quarta tem 296 px de coluna de
   texto ao lado; o nome cabe em menos. Se a foto é larga, a zona pode **ficar mais baixa e mais
   larga**, e o texto desce para baixo dela — que é **exatamente o que o dono sugeriu**
   ("reposicionar esses textos um pouco mais para baixo").
2. **Inverter o arranjo interno da célula** quando a foto é larga: foto em cima ocupando a
   largura toda, texto embaixo. A célula vira **responsiva à foto**.
3. **Centralizar em vez de assentar**, se a foto não toca o rodapé de qualquer forma.
   O `ASSENTAR` foi feito para produto que **apoia** — garrafa, lata, pacote em pé. Uma foto que
   não preenche a altura não está apoiada em nada: está flutuando, e afundá-la só cria vazio em cima.

**Meça e reporte:** para as 8 páginas, o **% de área da zona ocupado pela foto**, célula a célula.
Hoje as três fixas da Quarta estão em ~56%. Alvo: **≥ 85%**.

*(E note: isto explica retroativamente o "Kit Burguer pequeneninho" da SEPTIMUS — a zona era
312×90, banner horizontal, e o saco kraft era vertical. Mesma doença, diagnóstico incompleto na
época: eu tratei o sintoma mudando a zona daquela célula, e não vi a regra por trás.)*

---

## §2 · A UNIDADE NUNCA É SACRIFICÁVEL

O dono: *"comeu informações"* (Terça) e *"o salgadinhos também é BB-X e 100 g e não aparece"* (Quarta).

Nas duas páginas o mesmo item perdeu o descritor:

| Página | Item | O que sumiu | Os vizinhos |
|---|---|---|---|
| Terça | Salsicha Hot Dog Rezende | **kg** | os outros 3 mostram "100 g" |
| Quarta | Mini Salgadinhos | **BB-X · 100 g** | o Pão de Queijo mostra "BB-X · 100 g" |

Nos dois casos foi o **passo 4 da precedência** (o descritor sai para o nome caber) funcionando
como eu escrevi. **E eu escrevi errado.**

### Q2 🔴 · O descritor tem duas metades, e só UMA é sacrificável

**A unidade não é enfeite — é informação comercial, e a omissão dela é grave:**
"Salsicha Hot Dog Rezende — R$ 9,90" ao lado de três itens marcados "100 g" faz o cliente ler
**9,90 por 100 g**. O real é **9,90 por quilo**. É uma diferença de **dez vezes**, na vitrine, e
é o tipo de coisa que gera reclamação no balcão.

Divida o descritor:

```
descritor = [ qualificador ]  +  [ UNIDADE ]
            "BB-X", "tinto",     "100 g", "kg",
            "extra virgem"       "1 L", "220 g"
```

**Precedência corrigida (substitui o passo 4 da OCTAVUS):**

1. corpo mínimo do nome — inviolável
2. quebra em 2 linhas
3. a banda cresce / a foto cede
4. **sai só o QUALIFICADOR** do descritor; a **unidade fica**
5. encurta o NOME, movendo o excedente para o descritor
6. **a unidade só some se o item não tiver unidade nenhuma** — nunca por falta de espaço

**Teste:** nas 8 páginas, **todo item que tem unidade a exibe**. Falha se qualquer célula com
`unidade` no dado sair sem ela.

---

## §3 · A REAVALIAÇÃO DA QUARTA — o que mais dá para melhorar

Ele pediu explicitamente este tipo de análise, então varri a página inteira:

**Q3 🟠 A pílula do desconto está laranja; as dos fixos, verdes.**
Na coluna da esquerda, "Mini Salgadinhos R$ 4,99" e "Pão de Queijo R$ 4,99" usam pílula **verde**;
o "Lanche na Chapa **-20%**" usa **laranja** — a mesma cor das cinco células livres. No desenho
original o "20% off" da 3ª fixa era **verde**, como as irmãs. **A cor deve seguir a COLUNA (a
identidade da célula fixa), não o tipo do valor.** Confira no gerador e corrija.

**Q4 🟠 O formato do desconto.**
Hoje sai `-20%`. O desenho original diz `20% off`, e a tabela dele diz "COM 20 % de DESCONTO".
O `-` sugere subtração de preço, não desconto. Sugestão: **`20% OFF`** ou **`-20% no preço`** —
mas isto é decisão dele; **renderize as duas e pergunte.**

**Q5 🟡 A coluna verde tem vazio embaixo.**
Abaixo do "Lanche na Chapa" sobra uma faixa verde de ~8% da altura. Com o Q1 (zonas
re-proporcionadas) as três células podem crescer e ocupar isso — mais uma razão para o Q1
resolver o "imponentes" que ele pediu.

**Q6 🟡 `Leite Integral Parmalat L.V.`**
O `L.V.` (Longa Vida) veio da tabela e ficou no nome. É candidato natural a **qualificador do
descritor** — `Leite Integral Parmalat` + `L.V. · 1 L`. Mesma regra do `TP` da Segunda.

**Q7 · O que ficou BOM e não pode regredir:**
o selo de data `29/07 SÓ HOJE` preenchido (estava vazio há três rodadas); os nomes das cinco
livres em 1–2 linhas no piso certo; as fotos das livres cheias e bem enquadradas; o Óleo de Soja
na célula grande com a garrafa dominando; e o **OCR tendo vencido a foto de monitor** — que é a
melhor notícia técnica desta fase.

---

## §4 · A TERÇA — o que sobra

**Q8 🟠 A faixa creme vazia sob as cestas continua.** Está apontada desde a SEXTUS §5 e sobreviveu
a três rodadas. Com o Q1 valendo, as cestas e as fotos podem crescer para dentro dela.
Meça a densidade da Terça depois e reporte.

---

## §5 · ORDEM DE ATAQUE

1. **Q2** — a unidade nunca se perde. É o mais grave: é informação comercial errada na vitrine.
2. **Q1** — a foto enche a zona (≥85%), com a zona se adaptando. Resolve a Quarta, o Kit da
   Segunda, e provavelmente parte do vazio da Terça.
3. **Q3/Q6** — a cor da pílula e o `L.V.`.
4. **Q4** — as duas opções de formato do desconto, renderizadas, para ele escolher.
5. **Q8** — medir a Terça de novo.

**Condição de aceitação, a de sempre:** ele abre, importa, sai certo. Zero toque à mão.

---

## §6 · Nota de método — o que eu aprendi nesta rodada

Duas regras minhas produziram os dois defeitos que ele viu:

| Minha regra | O que ela causou | A correção |
|---|---|---|
| *"o descritor é o único elemento sacrificável"* (OCTAVUS) | a unidade sumiu em 2 páginas | o descritor tem duas metades; a unidade é protegida |
| *"a foto assenta no rodapé"* (SEPTIMUS/V1) | foto pequena grudada no chão em zona alta | a foto enche a zona; se não dá, a zona muda de forma |

**O padrão:** eu escrevo a regra olhando o caso que tenho na frente, e ela quebra no caso que
tem outra proporção. A defesa é a mesma da UNDECIMUS — **toda regra que eu escrever precisa de
um caso-limite explícito**: "e se a foto for quadrada numa zona alta?", "e se o item for por
quilo e o vizinho por 100 g?". Vou passar a escrever o caso-limite junto com a regra.


---

# Resposta do builder (Fable) — 28/07/2026

## Q2 — a unidade nunca é sacrificável (o mais grave, primeiro)

O descritor agora tem as duas metades EM CÓDIGO (`nome_fit.dividir_descritor`,
função nomeada — L11): o qualificador é sacrificável, a **unidade nunca**.
Três portas fechadas:

- **O passo 4** só derruba o descritor de item SEM unidade nenhuma ("marca
  própria" segue sacrificável, por teste); com unidade, a cadeia segue ao
  passo 5 — o nome encurta e a unidade fica.
- **A 2ª porta que ninguém tinha citado:** o SUBTITULO estreito elipsava por
  LARGURA ("BB-X · 10…" — reticências em cima do número). O desenho agora usa
  `descritor_que_cabe`: se o completo não cabe, o QUALIFICADOR sai e a unidade
  fica inteira.
- **O teste que a ordem pede:** `test_q2_toda_unidade_e_exibida_nas_8_paginas`
  — espião no caminho de produção, compõe as 8 com unidade no dado; falha se
  qualquer célula a perder (e pegou VERMELHO o código antigo: 2 células com
  `descritor_saiu` + unidade). Mais o par unitário da Salsicha: a MESMA
  geometria, com "kg" → passo 5 (kg fica) e com "marca própria" → passo 4
  (banda inteira) — a divergência exata da regra, testada dos dois lados.

**Na página real:** a Terça do DONO (id=12) recomposta — "Salsicha Hot Dog /
Rezende · kg" ao lado dos vizinhos "100 g". A leitura de dez-vezes-o-preço
morreu.

## Q1 — a foto enche a zona, ou a zona muda de forma

**A régua e o plano viraram código de runtime** (`app/rendering/foto_fit.py`):
`medir_ocupacao` (a régua pura) + `plano_da_celula` (o replanejamento). A
adaptação roda no laço de `compor_pagina`, ANTES da precedência do nome (a
cadeia trabalha sobre a célula já replanejada), por rects substitutos por uid
(I1 — o modelo nunca muda; a âncora dos selos ganhou os rects efetivos).

**Três arranjos candidatos**, o de maior área de foto vence (com guarda de
ganho ≥15%): *lateral* (foto de um lado, coluna de texto do outro — a coluna
preserva ≥85% da largura original: menos que isso a escada decapita o nome),
*vertical* (foto em cima, textos empilhados) e *misto* (nome/descritor no topo
na largura total, foto GRANDE embaixo, pílula ao lado — **a sugestão literal
do dono**, e o arranjo que venceu nas 3 fixas). Rede final: o *abraço*
centrado quando nada paga a mudança mas a foto está afundada.

**Onde a marca vale:** `Regiao.zona_flex` (aditivo, roundtrip testado) — o
template diz onde a arte é LISA e os textos podem se mover dentro do bbox da
célula. Marquei as 3 fixas da Quarta (o alvo da ordem). Guardas: célula
VESTIDA (ADORNO — as cestas da Terça, onde o pão assenta ATRÁS da borda
desenhada) nunca entra, por teste; rotação de verdade barra (o charme de
−1,5° não); multi-zona (o par Sonho+Croissant) fica fora.

**Caso-limite escrito com a regra (§6, na letra):** produto EM PÉ que já
enche a altura da zona (a garrafa do Óleo: 35% de área, 100% de altura,
vazio lateral simétrico) é APROVADO — o alvo de 85% de área vale para o
defeito *afundada* (limitada pela largura, paredão em cima), não para ele.
`test_q1_a_garrafa_em_pe_nao_regride` crava o Q7. **Declaro a divergência
(L6):** a régua literal de ≥85% de ÁREA reprovaria o Óleo, o Kit e metade da
Segunda — todos aprovados pelo dono; a exceção da altura-cheia é a leitura
que preserva o que ele elogiou.

**A medição pedida** (raiz real, fotos reais, `saida_f13/_quartusdecimus_medicao.log`):

| Página | Célula | Antes | Depois |
|---|---|---|---|
| Quarta | fixa-1 (Mini, foto 930×596) | **36%** | **100%** (misto; área da foto +74%) |
| Quarta | fixa-2 (Pão, 924×613) | **37%** | **100%** (misto; +74%) |
| Quarta | fixa-3 (Lanche, 889×390) | **25%** | **100%** (misto; +74%) |
| Quarta | var-1..5 | 85% · 35%ᵃ · 86% · 81%ᵃ · 38%ᵃ | — (ᵃ em pé, altura cheia) |
| Terça | Pão Francês / Sonho / Croissant | 84%ᵃ · 90% · 62%ᵃ | — |
| Terça | cestas 3..6 | 35–51% | — (VESTIDAS: a âncora é da arte) |
| Segunda | 1..8 (frios em pé) | 17–78%, todos h=100% | — (em pé) |

**O laço do OLHAR pegou o que a régua não vê** (registrado porque é o método):
a 1ª versão do plano lateral estrangulou a coluna e a escada decapitou os
nomes ("Mini", "Pão de"); a 2ª preservou a coluna mas a foto quadrada ainda
forçava o lateral. O arranjo MISTO — que é a sugestão do próprio dono na
ordem — resolveu os dois: nome completo numa linha limpa no topo E foto +74%.
Três recomposições até a página ficar certa; a que vai ao dono é a terceira.

## Q3 — a pílula verde · Q6 — o L.V.

- **Q3 conferido no gerador e corrigido nos DOIS lados:** o pctpod do
  `gen_final.py` estava LARANJA hardcoded (`fill={OR}`) — **nota factual
  (L6): não achei no pacote um "desenho original" verde; o PREVIEW de
  referência atual era laranja**. Corrigi pela REGRA que a ordem formula (a
  cor segue a COLUNA): pctpod com `fill=GREEN` + a região DESCONTO da fixa-3
  em `encartes.py` com `forma_cor=verde`. Regenerado por Playwright — o BASE
  saiu **byte-idêntico** (só o PREVIEW mudou; miolos do A2 intactos). Teste
  por pixel: verde presente, laranja ausente no recorte da pílula.
- **Q6:** "L.V." e "LV" entraram no glossário de siglas (`sanitize.py`) — na
  página real: "Leite Integral Parmalat" + "L.V. · 1 L", como o TP da
  Segunda. Bônus: a caixa preserva L.V. maiúsculo no cadastro.

## Q4 — os dois formatos, renderizados para o dono

`compositor.formato_do_desconto(pct, estilo)` — as duas opções nas imagens
`desconto-opcao-1-off.png` ("**20% OFF**") e `desconto-opcao-2-menos.png`
("**-20% no preço**"), enviadas com a pergunta. **Padrão provisório: "20%
OFF"** (o desenho de referência do pacote escreve "20% OFF" — L9), valendo
para o papel DESCONTO em TODA porta — inclusive o cartaz de gôndola
("-34%" → "34% OFF"; os dois guardiões que cravavam o texto viraram com
rastro). Uma linha troca se o dono escolher o outro.

## Q8 — a Terça medida de novo

Densidade 1,00 (células ocupáveis todas com item). A ocupação das zonas está
na tabela acima: as cestas são células VESTIDAS (o pão assenta atrás da borda
de arte — mover a foto descolaria o produto do desenho), e a faixa creme sob
elas é ARTE: crescer as cestas é decisão de GERADOR, não de runtime — fica
nomeada para o arquiteto decidir com o dono (o Q5 da Quarta, a faixa verde
sob o Lanche, é o mesmo caso: fora do bbox da célula, é arte).

## O guardião virado com rastro

`test_a1_nenhum_texto_fora_do_rect_nas_8_por_mascara`: a máscara era por
REGIÃO; com a célula replanejável por dentro, o invariante passou a valer
por CÉLULA (bbox da união, rot-aware) — e os dados do teste ganharam FOTO,
para o plano rodar e ser medido junto. O invariante continua o mesmo na
essência: tinta fora da célula é pintar a arte.

## A frota adversarial (19 agentes) — 5 defeitos confirmados, TODOS consertados

Revisão adversarial do diff antes da bancada (4 frentes → verificação por
achado, cada veredito com reprodução na bancada real):

1. **A pílula do plano misto podia VAZAR o bbox** (reproduzido: foto ~10:1
   nas fixas reais → tag verde 4,7mm abaixo da célula, sobre a arte — o
   exato invariante A1; as fotos atuais do dono não disparam por acidente
   geométrico, não por guarda). Conserto: clamp de fundo + plano inviável se
   a pílula não cabe + piso de altura da foto no misto; guardião novo varre
   6 proporções-sonda nas 3 fixas (`test_frota_o_misto_nunca_vaza_o_bbox`).
2. **O corte do qualificador no desenho derrubava a SIGLA DE EMBALAGEM** —
   "uva tinto suave TP · 1,5 L" num sub estreito saía só "1,5 L": o TP que o
   DONO mandou nunca omitir (adendo NONUS 27/07) sumia numa porta que a
   ordem §2 não previu. Conserto: a metade protegida de `dividir_descritor`
   agora inclui as siglas de embalagem conhecidas ("tinto TP · 1,5 L" →
   qualificador "tinto", protegido "TP · 1,5 L") — a palavra do dono vale em
   TODA porta.
3. **O corte era SILENCIOSO (I2)** — a marca/tokens do nome rebaixados pelo
   passo 5 podiam sumir da página sem a revisora nem o pré-voo verem (o
   antigo ao menos mostrava "…"). Conserto: a revisora heurística anuncia a
   MESMA decisão do desenho ("o descritor não coube inteiro — '…' vai sair
   como '…'"), por teste.
4. **A fixa duplicava o descritor em `unidade`** e o desempate classificava
   "marca própria" como unidade — bloqueando o passo 4 nas fixas. Conserto:
   a unidade da fixa é a METADE protegida do descritor.
5. **O guardião da máscara tinha afrouxado demais** (bbox de célula em TUDO
   = 75–225k px de vão interno virando zona cega). Conserto: máscara
   HÍBRIDA — por região nas células comuns, bbox só nas `zona_flex`
   (a frota provou a híbrida verde antes de eu aplicá-la).

Mais dois endurecimentos das notas refutadas-mas-latentes: a unidade do
DADO agora entra SEMPRE no descritor de trabalho da precedência (descritor
qualificador-puro com unidade só no campo não engana mais o passo 4), e o
"un." com ponto casa a régua. **Refutados com prova** (4): os dois cenários
da divergência revisora×plano (célula flex é FIXA — fora do dados_por_slot;
inalcançável hoje, nomeado abaixo), o gate com unidade-só-no-parâmetro e o
"600 ml embutido" (nenhum caminho de produção constrói o par; endurecidos
mesmo assim). Nota da frota que fica registrada: a classificação de
tamanho-letra (P/M/G/GG de fralda/vestuário) é inconsistente na régua de
unidade — pede o glossário DIY, decisão do arquiteto (nomeado).

## Abertos nomeados (sem consertar nesta rodada)

1. **Q5** (a faixa verde sob o Lanche) e a **faixa creme da Terça**: ocupar
   exige crescer a CÉLULA na arte/gerador — decisão de design, não de motor.
2. As demais páginas não têm `zona_flex` — a régua mediu e só a Quarta tinha
   o defeito *afundada*; se o arquiteto quiser a marca em mais células, é um
   `flex=True` por célula (com o OLHAR de cada arte).
3. O relatório da régua é script de bancada (`app/scripts/regua_da_foto.py`)
   — não há porta na UI para o dono ver ocupação por célula (nomeado).
4. A heurística da revisora usa os rects do TEMPLATE; em célula `zona_flex`
   a composição usa os replanejados — hoje inalcançável (célula flex é FIXA,
   fora do `dados_por_slot`), mas se um dia a fixa entrar no pré-voo, a
   heurística precisa replicar o gate do plano (nota da frota).
5. Tamanho-letra (P/M/G/GG) na régua da unidade — glossário DIY (frota).
6. Herdados: fio do desconto no parser do OCR; o diálogo dos fixos não mostra
   qual célula tem papel DESCONTO; critério do Concluir; reuso por nome;
   COND-10.

## Placares (junit `bloco_fquartusdecimus_*`)

**Suíte 1061 ×2 zero skips exit-0** (1043 + os 18 da QUARTUSDECIMUS; runs 1 e 2);
**invertida 1061/0/0**; **janela real 4/0/0**. *Incidente nomeado:* o run1 da 1ª
bancada crashou no teardown SEM escrever o junit (0xC0000005 — a família COND-10;
o rastro mostra um worker de enriquecimento com httpx vivo no encerramento do Qt,
pista nova para o COND-10) — re-rodado limpo. O OSError 22 transitório do save de
PNG (o mesmo da OCTAVUS) apareceu 2× no script da régua e ganhou retry declarado.


