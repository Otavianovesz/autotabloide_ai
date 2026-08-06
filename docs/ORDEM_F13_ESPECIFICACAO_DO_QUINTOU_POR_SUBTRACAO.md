# ESPECIFICACAO DO QUINTOU - extraida da arte do dono (L30/L31)

(A ordem do arquiteto de 06/08/2026: peca - template = conteudo. A especificacao completa da frente e do verso, e as leis L30 e L31.)

---

# RESPOSTA DO BUILDER (06/08/2026)

O metodo esta certo e mudou o que o motor faz. Executei o §4 com uma
divergencia de medicao registrada — e ela e sobre o mesmo tipo de erro
que a ordem descreve.

## §4.1 + §4.2 — A FOTO ESCALA POR AREA DE TINTA

A causa raiz que sobreviveu a trinta rodadas esta consertada no motor:
`Regiao.alvo_area_tinta_px` (px² na escala 1080, por FACE) e o
compositor escala o produto ate essa area em vez de encaixa-lo na
caixa. **A proporcao ficou livre**; o que se normaliza e a tinta.
Frente 19.413, verso 26.643 — os numeros da subtracao, cada face com o
seu (L31).

**O limite que a execucao revelou, e que e do LAYOUT, nao do motor:** o
alvo nunca estoura a zona (nao cruza o carimbo). Quando a zona e menor
que a area pedida, quem manda e a caixa — e ai a zona do Quintou e que
esta curta. O guardiao mede duas fotos de proporcoes OPOSTAS (0,33 e
3,0) numa zona folgada e exige que saiam com tinta parecida (razao
< 1,30); com a caixa antiga elas saiam 1,78x diferentes.

`base._tinta_px` registra a area desenhada por regiao — e a r14 da rede
compara com a peca publicada.

## §4.3 / §7 — CADA FACE TEM A SUA METRICA

O nome ganhou alvo proprio nas DUAS faces (12 px) e **deixou de ser
derivado do preco**: era a banda que amarrava um ao outro, e com o
algarismo do verso menor o nome de la encolheu para 7 px na primeira
prova. **O alvo medido manda; a razao e consequencia** — a banda
2,4–2,9 virou ALARME e nao reprova a face que declara os seus numeros
(ela reprovaria o verso do proprio dono, como a ordem diz).

O alvo do algarismo se aplica DEPOIS do pior caso, sobre o corpo unico
da pagina — aplicado por celula ele arrastava o minimo para baixo (o
app saia com 31 px onde a peca tem 33; agora sai 32, dentro dos ±5%).

## A DIVERGENCIA QUE EU NAO RESOLVI SOZINHO — o preco do verso

**Nao apliquei os 18 px.** Refiz a mesma subtracao medindo DENTRO do
carimbo, celula a celula (a janela do preco, 112x64 na escala 1080):

```
frente   mediana 41 px   (n=16)      verso   mediana 57 px   (n=16)
```

**O verso e MAIOR que a frente, nao menor.** O 18 vem do p85 sobre os
426 glifos do verso — e o verso TEM mais texto pequeno (o disclaimer
completo), entao o percentil cai no texto pequeno em vez de cair no
algarismo. Na frente, com 313 glifos e menos texto miudo, o mesmo p85
acertou o algarismo.

Aplicar os 18 px encolhia o verso para 19 px na prova visual, contra
os ~28 do desenho atual — e a peca publicada, lado a lado, mostra o
preco do verso GRANDE. Entao o verso ficou **sem alvo declarado** (vale
o teto do carimbo, o comportamento conhecido), com a divergencia
escrita no gerador e no guardiao.

**A minha regua tambem tem limite, e eu digo qual:** a janela que eu
medi pega o BLOCO do preco (algarismo + centavos + o que houver), nao o
algarismo isolado — por isso os meus 41 da frente contra os 33 seus. O
que a comparacao sustenta e a RELACAO entre as faces (verso > frente),
nao o valor absoluto. O numero certo do verso sai quando o algarismo
for isolado, do mesmo jeito que o senhor isolou na frente.

## Bancada

suite x2 + invertida + janela real, zero skips, placar por junit
(`saida_f13/bloco_l30_*`); guardioes novos: a area de tinta igual em
proporcoes opostas, os alvos por face (com o verso em 0,0 e o porque),
e o roundtrip dos dois campos novos. Rede dos oito com a **r14** — a
face bate com a peca publicada (algarismo ±5% ou 1 px; tinta ate +28%).

## O que ficou de fora

* **a zona do Quintou sem proporcao fixa** (o §4.1 completo): hoje o
  alvo de area e respeitado ATE o limite da zona; deixar a foto crescer
  dentro da CELULA (invadindo o vao livre, sem cruzar o carimbo) e uma
  mudanca de geometria da celula, e prefiro faze-la com o numero do
  verso resolvido — senao calibro duas vezes;
* **o preco do verso** — depende da medicao do algarismo isolado;
* o "8 4G" (o peso partido por um espaco) que eu mostrei na rodada
  passada segue de pe.

---

# RESPOSTA DO BUILDER AO §8 (06/08/2026)

**Os 33 px nas duas faces estao aplicados.** A sua 3a medicao e a que
vale, e a minha tambem estava errada — pelo motivo que o senhor
apontou: a janela de 112x64 que eu usei pega o BLOCO (algarismo +
centavos) e, no verso, encosta na manchete vermelha "ATE ... So Hoje";
por isso os meus 57. Medir o maior componente branco DENTRO do carimbo
e a operacao certa, e ela da 33 nos dois lados.

Aplicado:

```
frente   area 19.431 px2   nome 12 px   preco 33 px
verso    area 27.430 px2   nome 12 px   preco 33 px
```

## O QUE A MEDICAO DO APP RESPONDE AO §4.2

O motor agora MIRA os 33 px nas duas faces, e a frente chega:

| face | pior caso (dados reais do dono) | algarismo | carimbo hoje | para 33 px |
|---|---|---|---|---|
| frente | `Geleia Ritter Cebola Caram. 290g` — **R$ 19,90** | **32 px** | 112x64 | 116 px (+3%) |
| verso | `Queijo Mussarela Lactopar Quilo` — **R$ 55,05** | **28 px** | 112x64 | **132 px (+18%)** |

**O verso nao chega aos 33 por causa de UM preco: 55,05.** Nao e o
motor cedendo — e a L27 (o corpo e um so por pagina, do pior caso)
trabalhando: o carimbo de 112 px nao comporta "55,05" em 33 px.

O senhor escreveu no §4.2 que, se o pior caso do verso nao permitir, **e
a arte do verso que precisa de carimbo maior, e a decisao e do dono**.
Aqui esta o numero para essa decisao: **+18% de largura no carimbo do
verso (112 -> 132 px na escala 1080)** — ou o dono aceita que uma
pagina com preco de cinco digitos saia em 28.

Nao mexi na arte do dono por conta propria (L7).

## O ESTADO DA ESPECIFICACAO, PROPRIEDADE A PROPRIEDADE

| # | propriedade | dono | app | estado |
|---|---|---|---|---|
| 1 | proporcao da zona | livre | **livre** | OK (motor) |
| 2 | escala da foto | por area | **por area** | OK (limitado pela zona) |
| 3 | corpo do nome | 12 px | 12 px (11 onde nao cabe) | OK |
| 4 | alinhamento | centrado | centrado | OK |
| 5 | corpo do preco | 33 / 33 | **32 / 28** | frente OK; verso depende da ARTE |
| 6 | largura util do carimbo | ~99% | 98% | OK |
| 7 | razao preco/nome | 2,75x | alvo, banda so como alarme | OK |
| 8 | corpos de texto | 2 | 2 | OK |

## Sobre o §9

Registro do meu lado: barrar a ordem so foi possivel porque ela vinha
com o NUMERO e com o METODO. Uma ordem em prosa eu nao teria como
medir — implementaria com fidelidade, como nas tres anteriores. A L29
vale para os dois lados porque o senhor passou a escrever ordens
mensuraveis; e o que me deu com que discordar.
