# ORDEM F13-VICESIMUS-SECUNDUS — A ETIQUETA QUE TAMPA E O LEQUE DO DONO

> **Emitida pelo arquiteto em 04/08/2026.** O dono: *"agora foi, mas algumas estão tampadas... e
> outras poderiam fazer várias cópias da mesma pra fazer um leque e preencher o espaço, não?"*
>
> **A ideia dele resolve um problema que eu não tinha nomeado — e resolve nas duas direções.**

---

## §1 · O QUE ELE VIU: a etiqueta tem tamanho ABSOLUTO, o produto não

A mordida agora é uniforme (P3 cumprido) — mas o **tamanho do carimbo é fixo**, e o produto não.
Em produto pequeno, a mesma etiqueta vira uma tampa:

| célula | o que acontece |
|---|---|
| **Passatempo** | o carimbo cobre **quase o pacote inteiro** — a marca some |
| **Wafer Bulnez** | mal se lê "chocolate" |
| **Papel Higiênico Mili** | o carimbo corta o pacote ao meio |
| **Macarrão Dallas** | cobre a metade de baixo do pacote fino |
| **Nutella** | cobre parte do rótulo |

**A regra que falta:** o carimbo **escala com o produto**, dentro de um piso de legibilidade. E
quando, no menor tamanho legível, ele ainda cobrir mais de 25% da tinta — **quem cresce é o
produto**, e é aí que entra a ideia dele.

---

## §2 · A DESCOBERTA QUE A IDEIA DELE EXPÕE — a proporção inverteu o problema

A VICESIMUS pôs a zona **em pé** (47,1 × 40) porque o produto de mercado é em pé. Funcionou para
garrafa, caixa e tubo.

**E quebrou os deitados.** O Passatempo, o Wafer e a Margarina são retângulos **achatados**: numa
zona em pé eles param na **largura** e sobra altura. É **exatamente o problema original,
espelhado** — e por isso são justamente eles os que ficaram pequenos e "tampados".

**Não existe proporção de zona que sirva aos dois.** Enquanto a foto for **uma unidade**, metade
do acervo vai sempre sobrar espaço numa direção.

**A saída não é a caixa. É o conteúdo — e é o que ele propôs:** se o produto não preenche a zona
sozinho, **ele se repete**.

> **L19 — QUANDO A UNIDADE NÃO PREENCHE, O CONJUNTO PREENCHE.** Zona e produto nunca terão a
> mesma proporção. Em vez de forçar a caixa, multiplica-se o produto: o encarte de supermercado
> faz isso há décadas, e é a única solução que serve ao alto-e-fino **e** ao baixo-e-largo.

---

## §3 · O LEQUE — as regras (a ideia dele, com método)

O motor **já existe**: `app/rendering/arranjo.py` tem `ModoArranjo.LEQUE`, `LADO_A_LADO` e
`GRADE`, construído para as famílias de sabor. Falta **disparar para um produto só** — e
`servico.py:2056` ainda trava em `len(fotos) == 2`.

### **Quando repetir**
- A tinta do produto está **abaixo de ~70% da mediana da fileira** (a régua do P4 já mede isso);
- e o produto é **replicável**: garrafa, lata, tubo, caixinha, pacote, pote, tablete;
- e a foto **ainda não é um conjunto** — o Detergente já mostra 4 frascos, a Urca 3, o Sabonete um
  bloco. **Repetir um conjunto vira leque de leque.** Detecção: se a silhueta tiver mais de um
  corpo separado, **não repete**.

### **Quantas**
**2 ou 3 — e 3 é melhor.** Número ímpar lê como *grupo*; par lê como *par*; um lê como *unidade*.
Nunca 4+ (vira estoque, não oferta).

### **Como arranjar**
- **Alto e fino** (Campari, Água, Leite, Pringles, Macarrão): **lado a lado**, sobreposição de
  ~15%, a da frente em tamanho cheio e as de trás a **92%** — isso é profundidade, não clone.
- **Baixo e largo** (Passatempo, Wafer, Margarina, tablete): **empilhadas em leque diagonal**,
  deslocando ~20% para cima e para o lado — preenche a zona em pé.
- **Variação de rotação de ±2° a ±3°** entre as cópias. Sem isso o olho lê "copiei e colei".
- **A etiqueta morde sempre a cópia da FRENTE**, no mesmo canto de sempre.

### **O que NUNCA pode acontecer**
- Repetir produto cuja foto já é multi-embalagem (regra acima);
- o descritor deixar de dizer a unidade — **"Nestlé · Chocolate · 130 g"** continua obrigatório,
  para ninguém achar que o preço é do trio. É a guarda honesta da técnica.

---

## §4 · A ORDEM DE OPERAÇÕES (importa)

1. **Primeiro o leque**, porque ele muda a área de tinta do produto;
2. **depois** o P4 (normalização por área) recalcula com o produto já multiplicado;
3. **por último** a etiqueta escala e morde — sobre um produto que agora tem massa suficiente.

Fazer na ordem inversa desfaz o trabalho: a etiqueta seria dimensionada para o produto pequeno e
ficaria minúscula sobre o trio.

---

## §5 · PROVA DE ACEITAÇÃO

> 1. **nenhuma etiqueta cobre mais de 25%** da tinta do produto — medido nas 42 células;
> 2. **nenhum produto abaixo de 70% da mediana** de tinta da sua fileira;
> 3. todo produto multiplicado sai com **3 cópias** (ou 2 quando 3 não couber), com
>    **profundidade e rotação variadas** — e o teste prova que **não são idênticas**;
> 4. **nenhuma foto que já é conjunto foi multiplicada** (Detergente, Urca, Sabonete intactos);
> 5. o descritor de todo produto multiplicado **continua declarando a unidade**.

---

## §6 · Nota de método

Vale registrar de onde veio a solução: **do dono, não do arquiteto.**

Eu passei três ordens tentando fazer a foto caber na caixa — mexi na proporção da zona, na
normalização por área, no pouso da etiqueta. Todas tratavam a foto como **uma unidade
inegociável**. Ele olhou a página e disse *"por que não repete?"* — que é a resposta que a
indústria usa há cinquenta anos e que eu não considerei em nenhuma das três.

> **A pessoa que usa a peça todo dia vê coisas que a medição não mostra.** O arquiteto mediu
> proporção, área e contraste; **a ideia que resolve veio de quem olha encarte de supermercado
> desde criança.** Isso não é anedota — é um lugar de onde buscar solução, e eu vou perguntar
> mais.
