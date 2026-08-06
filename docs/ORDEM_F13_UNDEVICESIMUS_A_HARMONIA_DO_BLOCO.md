# ORDEM F13-UNDEVICESIMUS — A HARMONIA DO BLOCO DE TEXTO

> **Emitida pelo arquiteto em 04/08/2026.** O dono disse **"agora sim tá quase"** — a primeira vez
> nesta engenharia — e apontou o que sobrou: *"os textos das descrições parecem jogados. Tem que
> ser harmônico, com eles dando continuidade e as coisas fluindo. Invente para chegarmos no
> melhor possível, digno de designer sênior."*

---

# §0 · ERRATA DO ARQUITETO — O ITEM ZERO DA ORDEM ANTERIOR ERA MEU ERRO

Na DUODEVICESIMUS eu abri com *"o banco dele está três rodadas atrasado — nenhuma mudança
chegou"*, e listei oito campos supostamente velhos. **Estava errado, e o erro era de método.**

O SQLite do projeto roda em **modo WAL**. Eu copiei só o `core.db` e li — pegando um retrato
**anterior** às escritas que ainda viviam no `core.db-wal` (2,6 MB de transações pendentes).
Copiando as **três** peças (`.db`, `-wal`, `-shm`), o banco dele diz:

| campo | eu afirmei | **o real** |
|---|---|---|
| SUBTITULO | `#6E675C` / Italic / 10 pt | **`#4A443B` / Fraunces-Regular / 11,5 pt** ✅ |
| PREÇO | `#C9641A` / SemiBold / 20 pt | **`#A85212` / Archivo-Bold / 23 pt** ✅ |
| NOME | 13,5 pt | **14,0 pt** ✅ |
| grade p2 | sobrepondo −1,8 mm | **folga uniforme +7,9 a +8,0 mm** ✅ |

**Tudo tinha chegado.** O builder fez o trabalho, e ainda foi generoso ao atribuir o meu erro a
um "intervalo entre o commit e o reimport" — não foi intervalo nenhum, **foi leitura errada
minha**.

Três consequências que assumo:

1. **A L16 continua boa lei** (*a prova se compõe de onde o dono compõe*) — mas o §0 daquela
   ordem, que a motivou, **fica cancelado**. O gerador e o banco estavam de acordo.
2. **Lei nova, para mim antes de todos:** **ler banco em WAL sem o `-wal` é ler o passado.** Toda
   medição minha em `core.db` copia as três peças, ou usa `VACUUM INTO`.
3. Eu venho cobrando *"meça no banco do dono"* há dez rodadas. **Medi errado o que eu mesmo
   inventei como régua.** Fica registrado no lugar mais visível que eu tenho.

---

# §1 · O DIAGNÓSTICO DO "JOGADO" — em milímetros

A célula da p2 hoje, lida do banco **com o WAL**:

```
IMAGEM      29,6 .. 60,3   (30,7 mm)
PRECO       50,8 .. 61,9   ← sobrepõe a foto (o conserto da rodada passada, certo)
NOME        63,5 .. 70,9   caixa de 7,4 mm   corpo 14,0 pt   alinhamento_v = BASE
SUBTITULO   71,4 .. 80,4   caixa de 9,0 mm   corpo 11,5 pt   alinhamento_v = BASE
```

**A caixa do descritor tem 9,0 mm. Uma linha a 11,5 pt ocupa 5,1 mm.**

Com `alinhamento_v = BASE`, a linha única **cai no fundo da caixa** — e sobra um **buraco de
3,9 mm** entre o nome e o descritor. Quando o descritor tem **duas** linhas, ele preenche a caixa
e o buraco é **zero**.

**Na mesma fileira, células com descritor de 1 linha têm 3,9 mm de vão e as de 2 linhas têm 0.**
Some-se a isso o NOME, que também é `BASE` dentro de uma caixa de 7,4 mm, e cada célula acumula
**duas folgas variáveis empilhadas**.

É isso, exatamente, o "jogado": **o bloco de texto não tem uma âncora — tem duas, e as duas
flutuam.**

---

# §2 · O CONSERTO DE FUNDO — O BLOCO É UM SÓ

O dono já intuiu a solução: *"nem que faça o espaço todo ser um só"*. **É isso.**

Hoje são **duas regiões** que se compõem sozinhas e se ignoram. Passam a ser **um bloco
tipográfico único**, composto como um parágrafo:

```
┌─ ZONA DE TEXTO (da base da foto ao fim da célula) ─┐
│                                                     │
│   NOME DO PRODUTO           ← 14 pt, SemiBold       │  ancorado no TOPO
│   descritor · peso          ← 11,5 pt, Regular      │  entrelinha FIXA
│                                                     │
│   (o que sobrar cai aqui, embaixo, igual em todas)  │
└─────────────────────────────────────────────────────┘
```

**As três regras que produzem harmonia:**

### **H1 · UMA ÂNCORA SÓ, NO TOPO**
O bloco inteiro ancora logo abaixo da foto. O espaço que sobra cai **embaixo do bloco**, nunca
entre o nome e o descritor. Sobra igual em todas as células = o olho lê como respiro da fileira,
não como buraco na célula.

### **H2 · ENTRELINHA FIXA, NÃO CAIXA FIXA**
A distância nome→descritor é **uma constante tipográfica** (proponho **1,15× o corpo do nome ≈
5,7 mm**), medida de linha de base a linha de base — **jamais** derivada da altura de uma caixa.
Isso mata o vão variável na origem.

### **H3 · O DESCRITOR É DE UMA LINHA**
Duas linhas quebram a fileira e é o que hoje faz o Biscoito e a Sardinha destoarem. Quando não
couber, **encurta-se por prioridade**, nesta ordem (a mais fraca sai primeiro):

```
embalagem  →  variante/sabor  →  submarca  →  [MARCA e PESO nunca saem]
```

E quando houver muitos sabores, **conta em vez de listar**:
`"Bulnez e Adoralle · C. Cracker, Leite, Água e Sal ou Maisena · 270 g"`
→ **`"Bulnez · 4 sabores · 270 g"`**

Isso é melhor **também como texto de varejo**: ninguém lê quatro sabores no encarte; lê "4
sabores" e escolhe na gôndola.

---

# §3 · A DECISÃO DE DESIGN QUE FALTA — CENTRADO × ALINHADO À ESQUERDA

Aqui está, na minha leitura, **a causa mais profunda** da falta de "continuidade" que ele sente.

**Hoje tudo é centrado** — foto, nome, descritor. Como cada nome tem uma largura diferente, as
bordas esquerda e direita ficam irregulares nas duas laterais, e **não existe nenhuma linha
vertical que o olho possa seguir** descendo a coluna. Cinco colunas centradas = cinco colunas sem
estrutura.

**Alinhar o bloco de texto à esquerda** cria **cinco linhas verticais limpas** descendo a página.
É o que dá o "fluindo" que ele pede — e é o padrão de praticamente todo encarte de rede grande.

**Contra:** o Jornal é um pastiche de jornal antigo, e legenda centrada é de época.

**Peça: fazer as DUAS e deixar ele escolher.** Recompor a p2 em duas versões — **(A) centrado
com H1–H3** e **(B) alinhado à esquerda com H1–H3** — e mandar lado a lado. É meia hora de
trabalho e encerra uma discussão que já custou cinco rodadas.

**Meu voto declarado, para ele ter uma referência:** **(B) nas páginas de grade**, mantendo
**centrado no herói e nas chamadas da capa** — a capa é editorial, o miolo é catálogo.

---

# §4 · REFINOS DE SÊNIOR (o que separa "bom" de "publicável")

1. **A etiqueta escolhe o canto mais vazio da foto.** Hoje ela vai sempre ao mesmo canto e às
   vezes cobre o rótulo (a Nutella, a tampa do Danone). *Conserto: medir a densidade de tinta
   nos quatro cantos da foto tratada e pousar no de menor densidade.*
2. **Um separador só, com um nível só.** `"Coqueiro · Tomate, Óleo ou Limão · 125 g"` tem vírgula
   e "ou" e ponto-médio disputando a mesma função. *Conserto: marca no NOME; o descritor fica
   `variante · peso`, com um único `·`.*
3. **O peso sempre por último e sempre presente.** É o que o cliente usa para comparar preço.
4. **Números tabulares no preço.** Se o Archivo tiver `tnum`, ligar: os preços passam a alinhar
   dígito com dígito entre células.
5. **Vírgula decimal menor, mas não os centavos.** Hoje o centavo caiu junto com a vírgula;
   o centavo deve ficar ≥ 55% do corpo do real, a vírgula pode ser menor.
6. **Otimizar o espaço óptico, não o matemático.** Um saco (Yoki) preenche a caixa; uma garrafa
   (Kitubaina) ocupa 30% da largura e parece pequena mesmo tendo a mesma altura. *Conserto:
   normalizar pela ÁREA de tinta visível, não pela caixa.*
7. **A capa precisa de um "herói" que mereça.** O Gatorade ocupa 6× a área de qualquer outro por
   R$ 6,90. *Conserto: o herói é escolha do dono (um clique "destacar"), não do slot.*

---

# §5 · PROVA DE ACEITAÇÃO

> Composta **do banco do dono** (L16), com as três peças do WAL na medição:
>
> 1. a distância nome→descritor é **idêntica em todas as 22 células** da p2 (variância = 0);
> 2. **nenhum descritor tem 2 linhas** na grade densa;
> 3. o espaço que sobra dentro da célula está **todo abaixo do bloco**, em quantidade igual;
> 4. as duas versões (A centrado / B esquerda) recompostas lado a lado para a escolha dele;
> 5. nenhuma etiqueta de preço cobre o rótulo principal de nenhuma foto.

---

# §6 · Nota de método

Duas coisas nesta rodada valem mais que o conserto:

**A primeira é minha.** Passei dez rodadas exigindo *"meça no banco do dono"* e então medi o banco
do dono **errado**, e transformei o meu erro no §0 de uma ordem inteira — cobrando do builder um
trabalho que ele já tinha feito. A régua estava certa; **eu segurei a régua torta**. Se eu não
disser isso com todas as letras, a próxima vez que eu acusar não vai valer nada.

**A segunda é do dono.** Ele disse *"agora sim tá quase"* — e depois de tantas rodadas duras, é
justo registrar que a peça de hoje **é boa**: a grade tem ritmo, o preço gruda no produto, o
descritor é legível, os acentos estão certos. O que falta agora não é conserto de defeito;
**é acabamento de designer.** É outro patamar de conversa, e chegar nele levou treze ordens.

---
---

# §7 · REAUDITORIA DE `dcfd6c1` — O VEREDITO SOBRE O A/B

O dono perguntou: *"Veja o que você acha e se de fato está satisfatório ou ainda podemos
melhorar."* Abri o `jm-escolha-A-B.png` e ampliei uma fileira dos dois lados em escala real.

## §7.1 · O QUE FICOU RESOLVIDO (e é para não mexer mais)

**O bloco de texto está certo.** Nome e descritor grudados, entrelinha idêntica em todas as
células, descritor escuro e romano, legível. Era **a** queixa desta rodada e ela morreu. Comparando
com a página de três rodadas atrás, é outro produto.

## §7.2 · A ESCOLHA A/B — **B, com uma correção**

**B (alinhado à esquerda) é melhor**: as cinco linhas verticais existem e o olho desce a coluna
sem tropeço. A é bonito isolado e sem estrutura no conjunto.

**Mas B está incompleto**, e dá para ver na ampliação: **o texto alinha à esquerda da CÉLULA e a
foto continua CENTRADA na célula.** São dois eixos disputando. "Milho Pipoca" começa antes de o
saco começar; "Feijão Carioca" começa depois. O olho registra como desalinho, não como escolha.

**Peça:** em B, o texto alinha ao **canto esquerdo da SILHUETA da foto** (a tinta real, não a
caixa) — ou a foto também alinha à esquerda. **Um eixo por coluna.** Feito isso, B fecha.

## §7.3 · 🔴 O NOVO PROBLEMA Nº 1 — A ETIQUETA ENGOLIU O PRODUTO

O carimbo saiu de "longe demais" e foi para "em cima demais". Medindo a fileira 2 da p2 (máscara
aproximada, mas a ordem de grandeza é inequívoca e salta aos olhos na ampliação):

| produto | largura da etiqueta × largura do produto |
|---|---|
| Água Mineral Marajá | **~110%** — a etiqueta é **mais larga que a garrafa** |
| Azeitona Verde | ~100% — cobre a metade de baixo do vidro |
| Leite Int. L.V. | ~100% — cobre a base da caixinha |
| Milho Pipoca | ~91% — cobre a tigela de pipoca da arte |
| Feijão Carioca | ~64% |

O encarte clássico **põe o preço sobre a foto — mordendo o CANTO**, ocupando algo como **um
quarto** dela. O que está lá hoje atravessa a barriga do produto.

**As regras que faltam (todas relativas à TINTA do produto, nunca à caixa da célula):**

- **largura da etiqueta ≤ 45%** da largura visível do produto;
- **área coberta ≤ 25%** da tinta do produto;
- a etiqueta **morde o canto** — o centro do produto nunca é coberto;
- **produto estreito e alto** (garrafa, caixinha): a etiqueta sai da silhueta e pousa **ao lado**,
  dentro da zona da foto — é o que se faz com item alto e fino;
- se, no tamanho mínimo legível, a etiqueta ainda violar as regras, **quem encolhe é a foto** —
  nunca o preço.

## §7.4 · Os três acabamentos que sobram

1. **O produto está pequeno dentro da zona.** Agora que o bloco de texto é compacto, sobra creme
   em volta de cada foto. **Alvo: o produto ocupa ≥ 85% da altura da zona.**
2. **Os 22 carimbos estão no mesmo ângulo.** Charme uma vez, defeito de impressão vinte e duas.
   *Peça: **0° na grade**; a inclinação fica só nos destaques da capa.*
3. **A caixa "FICA A DICA" continua vazia com as pautas desenhadas** — em peça impressa isso lê
   como falha de impressão. **Ou tem texto, ou a caixa não se desenha.** (Já era o item 41 da
   ordem anterior; segue aberto.)

## §7.5 · A resposta direta à pergunta dele

**Não, ainda não está satisfatório — mas está perto, e o que falta é uma coisa só com três
desdobramentos:** a relação entre a etiqueta e a foto. Resolvido o §7.3 (+ o eixo do §7.2 e os
três acabamentos do §7.4), eu assino a página.

E vale dizer o que mudou de patamar: **as últimas três ordens foram sobre defeito; esta é sobre
proporção.** A peça saiu do "está errado" e entrou no "está quase certo, ajuste fino" — que é
onde um encarte de verdade passa 90% do tempo.
