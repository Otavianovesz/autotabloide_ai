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
