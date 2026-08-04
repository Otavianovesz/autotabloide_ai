# ORDEM F13-DUODEVICESIMUS — CINQUENTA OLHARES SOBRE O JORNAL

> **Emitida pelo arquiteto em 04/08/2026.** O dono pediu: *"Olhe você mesmo e identifique umas
> 50 coisas a melhorar nesse tabloide. Use sua visão pra identificar e aprimorar esse layout,
> essas letras pequenas, as imagens pequenas, os preços facilmente confundíveis."*
>
> Olhei as duas páginas e medi a geometria do banco dele. **Achei o item zero — e ele explica
> por que as últimas quatro rodadas não mudaram nada do ponto de vista do dono.**

---

# §0 · O ITEM ZERO — O BANCO DELE ESTÁ TRÊS RODADAS ATRASADO

Comparei, campo a campo, o que a última rodada prometeu com o que existe em
`AutoTabloide_System_Root/banco/core.db`, layout 14 «Jornal do Mês»:

| | prometido | **no banco dele** |
|---|---|---|
| SUBTITULO cor | `#4A443B` | **`#6E675C`** (o velho) |
| SUBTITULO fonte | `Fraunces-Regular` | **`Fraunces-Italic`** (o velho) |
| SUBTITULO corpo | 11,5 pt | **10,0 / 10,5 pt** (o velho) |
| PREÇO cor | `#A85212` | **`#C9641A`** (o velho, 3,53:1) |
| PREÇO fonte | `Archivo-Bold` | **`Fraunces-SemiBold`** (o velho) |
| PREÇO corpo | 23 pt | **20 / 21 / 24 pt** (o velho) |
| NOME p2 | 14,0 pt | **13,5 pt** |
| passo da grade p2 | uniforme 58,8 mm | **53,5 / 61,4 / 53,4 / 61,4 — com −1,8 e −1,9 mm de sobreposição** |

**Nenhuma. Única. Mudança. Chegou.** O layout no banco dele é byte-a-byte o de três rodadas atrás.

**O que isso significa:** as páginas de prova que o builder mostra são compostas **a partir do
gerador (`encartes.py`)**. O app do dono compõe **a partir do banco**. São duas fontes
diferentes, e só uma delas recebeu os consertos. Quando ele abre o Jornal na Mesa e gera, ele
recebe **o layout velho** — cinza claro, itálico, preço 3,53:1 e a grade que se sobrepõe.

É a **UNDECIMUS pela sexta vez**, e desta vez custou quatro rodadas de frustração dele:

| rodada | certo | o que o dono tinha |
|---|---|---|
| §17 · QUINQUE · NONUS · UNDECIMUS · §1 · §12 | relatório · galeria · página · calibração · detector · +18 |
| **§0 desta ordem** | **o gerador inteiro** | **o banco de três rodadas atrás** |

### **A PEÇA MAIOR DESTA ORDEM — antes de qualquer melhoria de design:**

1. **Descobrir por que o "pacote reimportado (8 chaves)" não substitui geometria nem estilo.**
   Suspeita: o upsert preserva campos do dono (a guarda do `conteudo_fixo`, correta) e acabou
   preservando **também** cor, fonte, corpo e posição — que são do **autor da arte**, não do dono.
2. **Separar as duas coisas em lei:** o que é do DONO (conteúdo fixo, itens travados, overrides)
   **sobrevive** ao reimport; o que é da ARTE (geometria, cor, fonte, corpo) **é substituído**.
3. **O teste que fecha:** um teste que muda um valor no gerador, roda o import, e **lê o banco**
   provando que o valor novo chegou — e que o `conteudo_fixo` do dono continua lá.
4. **E a partir de agora, toda prova visual declara a FONTE:** *"composta do banco do dono"* ou
   *"composta do gerador"*. Prova que não diz de onde veio não vale.

> **L16 — A PROVA SE COMPÕE DE ONDE O DONO COMPÕE.** Página de prova renderizada a partir do
> código, enquanto o app renderiza a partir do banco, **não é prova** — é maquete.

---

# §1 · A LEI DA PROXIMIDADE — a resposta exata ao "preços confundíveis"

O dono disse: *"os preços facilmente confundíveis um com os outros produtos"*. Medi a célula
da página 2:

```
base da foto  56,1  →  topo do preço  73,8     =  17,7 mm até o PRÓPRIO produto
base do preço 84,9  →  foto de baixo  83,1     =  −1,8 mm até o produto SEGUINTE
```

**O preço está 17,7 mm do seu próprio produto e encostando no de baixo.** O olho agrupa por
proximidade — não há como não confundir. Não é impressão dele: é uma diferença de **19,5 mm**
apontando para o produto errado.

**A solução que todo encarte de supermercado usa há cinquenta anos: a etiqueta de preço encosta
na FOTO, não fica no fim da coluna.** Três formas, em ordem de preferência:

- **(a)** o carimbo **sobrepõe o canto inferior da foto** (o clássico — o preço "gruda" no produto);
- **(b)** o carimbo sobe para logo abaixo da foto, **antes** do nome (foto → preço → nome → descritor);
- **(c)** a célula inteira ganha um **fundo levemente tingido** ou fio de contorno, e aí a ordem
  pode continuar como está — mas o agrupamento passa a ser visual, não só espacial.

**Peça: (a) como padrão do Jornal**, com **(c)** como reforço nas páginas de grade densa.

---

# §2 · AS CINQUENTA (agrupadas por causa, com o conserto junto)

## A · HIERARQUIA E LEITURA (o que faz parecer amador)

1. **O preço não pertence visualmente ao seu produto** (§1). *Conserto: (a) do §1.*
2. **Todos os preços têm o mesmo tamanho.** R$ 55,05 do queijo e R$ 2,88 do creme de leite têm
   idêntico peso visual. *Conserto: 2–3 patamares de corpo por faixa de preço/destaque.*
3. **Não existe âncora de "melhor oferta".** A página inteira grita no mesmo volume, então nada
   grita. *Conserto: 3 a 5 itens por página em corpo maior, foto maior e selo de destaque.*
4. **O nome é a CATEGORIA e a marca foi para o descritor** — "Sardinha / *Coqueiro*",
   "Sabão em Pó / *Omo*", "Creme de Avelã / *Nutella*". No varejo o cliente procura **Nutella**,
   não "creme de avelã". *Conserto: a MARCA entra no nome; a categoria só quando ajuda.*
5. **Os centavos são pequenos demais para ler.** A hierarquia real/centavo é correta, mas o
   centavo caiu abaixo do limite. *Conserto: centavo ≥ 55% do corpo do real.*
6. **A borda tracejada do carimbo compete com o número.** A 42 repetições vira ruído.
   *Conserto: tracejado mais espaçado e mais fino, ou fio contínuo nos itens de destaque.*
7. **Dois laranjas disputam** — o do número e o (mais claro) da borda. *Conserto: um só tom.*
8. **Nada indica "de/por" ou economia** em 40 dos 42 itens. *Conserto: quando houver preço
   anterior no banco, mostrar riscado + "economize R$ X".*

## B · A GRADE E O RITMO

9. **A grade ainda se sobrepõe no banco dele** (−1,8 e −1,9 mm). Ver §0.
10. **O passo alterna 53,5 / 61,4 mm** — fileiras ímpares apertadas, pares folgadas. O olho
    procura ritmo e não acha; é a origem do "descolado". *Conserto: passo único.*
11. **Não há separação entre fileiras** — nem fio, nem tinta, nem folga suficiente.
    *Conserto: fio finíssimo ou faixa de tinta 3% alternada.*
12. **A p1 não tem seção**; a p2 diz "MERCEARIA". *Conserto: toda página com sua seção.*
13. **A última fileira da p2 tem 2 produtos e um vazio enorme ao lado.** *Conserto: a caixa de
    pagamento ocupa a lacuna, ou entram mais 3 itens.*
14. **A caixa de bandeiras de cartão ocupa a área de ~5 produtos** — 12 bandeiras em 3 linhas.
    *Conserto: uma linha só, ícones menores, ou rodapé de largura total com 20 mm.*
15. **O expediente é grande e de baixíssimo valor** para o leitor. *Conserto: 2 linhas.*
16. **As tarjas listradas verde/laranja comem ~12 mm** no topo e no pé de cada página.
    *Conserto: metade da altura devolve ~12 mm por página aos produtos.*

## C · AS FOTOS

17. **A foto-herói é 6× a maior das outras** (6.145 mm² × 1.019 mm²) — para um item de R$ 6,90.
    *Conserto: o tamanho segue o DESTAQUE, e destaque é decisão do dono, não do slot.*
18. **A foto do Gatorade está escura e sem definição** — a garrafa roxa lê como um borrão preto.
    *Conserto: normalização de luminância; foto que sai abaixo de X de contraste **avisa**.*
19. **As duas fotos do Arroz se sobrepõem** — o pacote Somar cobre o "NI" de BONINI.
    *Conserto: no arranjo lado a lado, as peças não se tocam; se não couber, reduz.*
20. **A foto do Arroz está cortada na direita.**
21. **A foto do Tempero está cortada**, mostrando a fatia de um segundo produto.
22. **As fotos não compartilham linha de base** — garrafas flutuam, sacos assentam.
    *Conserto: base comum por fileira.*
23. **A escala aparente varia demais** — o queijo tem 3× a massa visual do açúcar na mesma
    fileira. *Conserto: normalizar pela ALTURA aparente do produto, não pela caixa.*
24. **O sabonete Nivea é uma grade de 9 caixinhas** — lê como padronagem, não como produto.
    *Conserto: preferir foto de 1–3 unidades; "diversos" se resolve no descritor.*
25. **Detergente (4 frascos) e Desinfetante (3 frascos) parecem o mesmo produto.**
26. **Tratamento de fundo inconsistente** — alguns com sombra, outros chapados.
27. **Fotos com texto de embalagem ilegível** ocupam área sem informar. *Conserto: enquadrar
    pelo rótulo principal.*

## D · TIPOGRAFIA

28. **O descritor é pequeno demais** (10 pt no banco dele, com piso de 8,5). *Conserto: 11,5 pt,
    piso 10,5 — e o piso do celular vale para ele também.*
29. **O descritor é itálico serifado em cinza** — a pior combinação para papel.
    *Conserto: romano, `#4A443B`.*
30. **O nome e o descritor têm pesos próximos demais** — a hierarquia se perde a 1 m de distância.
31. **Tudo é serifado**, inclusive onde a leitura é rápida (preço, descritor).
    *Conserto: sem serifa para dado; serifada só para nome e títulos.*
32. **O nome do herói é o menor texto útil da página** (e está fora da célula).
33. **"Detg."** abreviado feio. *Conserto: "Detergente" — cabe se o corpo ceder 0,5 pt.*
34. **"Papel Hig."** idem.
35. **Nenhuma célula usa duas linhas de nome**, mesmo quando sobra espaço — o nome é cortado
    antes de tentar quebrar.

## E · CONTEÚDO E TEXTO

36. **"Agua Mineral"** sem acento; **"Maraja"** sem acento. *Conserto: o corretor ortográfico do
    projeto já existe — falta rodar nos nomes do encarte.*
37. **"Creme Dental / Kolynos"** com foto da **Sorriso** — nome e imagem discordam.
38. **O Biscoito tem descritor de 2 linhas** enquanto todos os outros têm 1 — quebra a fileira.
    *Conserto: teto de 1 linha na grade densa; o excedente vira "e mais sabores".*
39. **Os dois SUPER OFERTA continuam sem número.** O item de maior destaque da capa não diz
    quanto custa.
40. **"Isotônico" como nome** — categoria no lugar da marca (ver A4).
41. **A caixa "FICA A DICA" está VAZIA**, com as pautas desenhadas. Numa peça impressa isso lê
    como defeito de impressão. *Conserto: sem dica, a caixa **não se desenha**.*
42. **A validade aparece duas vezes na mesma página** (cabeçalho e sub-cabeçalho da p2).
43. **"SE É B, É SHOW!" aparece duas vezes na p2** (faixa e rodapé).
44. **O número da edição ("Nº 177 ANO 42") sumiu da p1** e ficou só na p2.
45. **Nenhum item traz preço por unidade de medida** (R$/kg, R$/L) — útil e, em várias
    categorias, exigido.
46. **Não há "enquanto durarem os estoques" nem limite por cliente** em lugar nenhum.

## F · DETALHES QUE DENUNCIAM

47. **"MERCEARIA" está sublinhado colidindo** com o fio do cabeçalho da p2.
48. **Dois losangos decorativos** flutuam ao lado do título sem função.
49. **A tarja pêssego atrás do subtítulo da p1** começa e termina em pontos arbitrários.
50. **Os carimbos de preço estão rotacionados em ângulos aleatórios** — charmoso uma vez,
    ruidoso 42 vezes. *Conserto: 2 ou 3 ângulos fixos, alternando.*
51. **Os fios verticais entre as colunas do herói** parecem sobra de grade, não separador.
52. **O logo do rodapé da p1 está desalinhado** em relação à linha de texto ao lado.
53. **A p1 e a p2 têm o mesmo desenho de grade** — nada diferencia capa de miolo além do título.

---

# §3 · ORDEM DE ATAQUE

**Zero (antes de tudo):** **§0** — o banco recebe o pacote. Sem isso, nada do que vier abaixo
chega ao dono, e a próxima rodada repete esta conversa pela quinta vez.

**Onda 1 — o que resolve "confundível" e "pequeno":**
§1 (o preço encosta na foto) · 9 · 10 · 11 · 28 · 29 · 30 · 4 · 2

**Onda 2 — o que resolve "imagens pequenas" e o ritmo:**
17 · 22 · 23 · 19 · 20 · 21 · 14 · 15 · 16 (os mm liberados vão para foto e corpo)

**Onda 3 — o que tira o ar de amador:**
41 · 39 · 36 · 37 · 33 · 34 · 42 · 43 · 44 · 47 · 48 · 50

**Onda 4 — o que eleva a peça:** 3 · 8 · 24 · 25 · 45 · 53

---

# §4 · PROVA DE ACEITAÇÃO

> A prova desta ordem é **composta do banco do dono** (L16), e traz no rodapé do relatório:
>
> 1. distância do preço à própria foto **< 6 mm**, e à foto seguinte **> 12 mm**;
> 2. passo da grade **uniforme**, folga entre fileiras **≥ 4 mm** nas duas páginas;
> 3. contagem de tinta: `#6E675C` = **0 px**, `#C9641A` = **0 px** nas células;
> 4. corpo do descritor **≥ 11,5 pt**, do preço **≥ 23 pt** — **lidos do banco**;
> 5. **nenhuma foto cortada** e **nenhuma foto tocando outra** no arranjo lado a lado;
> 6. a caixa "Fica a Dica" **ou tem texto do modelo, ou não existe na página**;
> 7. os dois SUPER OFERTA com **número**.

---

# §5 · Nota de método

Quatro rodadas seguidas o builder consertou o gerador, mediu o gerador, provou no gerador — e o
dono abriu o app e viu o banco. **Cada rodada foi honesta e nenhuma chegou.**

Não é falta de rigor: é falta de **endereço**. O rigor todo foi aplicado ao lugar errado.

E a minha parte na conta: eu escrevi cinco ordens medindo geometria e cor **no banco** e nunca
perguntei *"o conserto anterior chegou aqui?"*. A pergunta custava um `SELECT` e teria poupado
três semanas do dono. **Toda reauditoria minha, daqui em diante, começa por ela.**
