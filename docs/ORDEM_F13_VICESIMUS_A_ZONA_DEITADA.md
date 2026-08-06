# ORDEM F13-VICESIMUS — A ZONA ESTÁ DEITADA E O PRODUTO É EM PÉ

> **Emitida pelo arquiteto em 04/08/2026.** O dono: *"agora tá quase, mas as imagens continuam
> muito pequenas... além de alguns muitos outros problemas."*
>
> **Achei a causa, e é uma conta de uma linha que quinze ordens não fizeram.**

---

## §1 · A CAUSA — proporção, não tamanho

```
zona de foto da p2 :  47,1 × 30,7 mm   →  proporção 1,53  (DEITADA)
produto de mercado :  garrafa, caixa, tetrapak, tubo, pote
                      proporção típica ~0,45  (EM PÉ)
```

**Toda vez que um produto em pé entra numa caixa deitada, ele para na ALTURA e sobra largura.**
Com 30,7 mm de altura, o produto retrato ocupa **29% da largura** da zona — **71% da caixa fica
vazia**, em todas as células de produto alto.

É por isso que só o Passatempo, o Wafer, o Papel Higiênico e a Margarina parecem do tamanho
certo: **são os quatro produtos deitados da página.** Todo o resto — Macarrão, Campari, Leite,
Água, Pringles, Detergente, Suco, Azeitona — está pequeno pela mesma razão.

**Ninguém errou o "tamanho da foto". A caixa está deitada.**

---

## §2 · O ORÇAMENTO — e o espaço existe

Abaixo do último texto de produto (313,3 mm) sobram **67,7 mm — 18% da página** — para quadro de
pagamento, expediente e slogan.

| zona | proporção | célula | 5 fileiras ocupam | sobra p/ rodapé | ganho de altura do produto |
|---|---|---|---|---|---|
| **47,1 × 30,7** | 1,53 | 48,2 | 294,6 | 86,4 | — *(hoje)* |
| 47,1 × 35,0 | 1,35 | 52,5 | 316,1 | 64,9 | **+14%** |
| **47,1 × 40,0** | **1,18** | **57,5** | **341,1** | **39,9** | **+30%** ← **peça** |
| 47,1 × 45,0 | 1,05 | 62,5 | 366,1 | 14,9 | +47% |
| 47,1 × 47,1 | 1,00 | 64,6 | 376,6 | 4,4 | +53% *(não cabe rodapé)* |

**Peça: zona 47,1 × 40 mm.** O produto cresce **30%** em altura, os 22 itens continuam na página,
e ainda sobram **~40 mm** de rodapé — que dá para o quadro de pagamento em **uma linha** e um
expediente de duas linhas.

**E se o rodapé encolher de verdade** (o quadro de 12 bandeiras em 3 fileiras vira 1 fileira:
−20 mm), a zona vai a **47,1 × 45** e o produto cresce **47%**.

> **A regra que fica:** **a zona de foto de um encarte de mercado nunca é mais larga que alta.**
> Proporção-alvo entre **1,0 e 1,2**. Quem manda na proporção é o produto, não a grade.

---

## §3 · OS OUTROS PROBLEMAS QUE ELE MANDOU EU ACHAR

### 🔴 Prioridade

1. **A etiqueta "ao lado" ficou longe demais.** No Macarrão, no Campari, no Leite, na Água e na
   Pringles ela pousou fora da silhueta — correto pela regra — **mas a 15–20 mm do produto**, no
   meio do creme. **A proximidade voltou, agora na horizontal.** *Peça: fora da silhueta sim,
   mas **encostada** — folga máxima de 3 mm da tinta do produto.*
2. **Metade das etiquetas ainda atravessa a barriga**: Milho Verde, Café 3 Corações, Suco de Uva,
   Sabonete, Batata Pré-frita. A regra do canto não pegou nesses. *Peça: a regra vale para os 42;
   teste que reprova qualquer célula com invasão > 25% da tinta.*
3. **O selo +18 do Campari pousou EM CIMA do gargalo** — cobre o produto e some no vermelho da
   garrafa. *Peça: o selo é aviso legal; vai no canto da CÉLULA, nunca sobre a tinta.*
4. **Duas fotos estão cortadas no topo**: Toalha de Papel Mili e Milho Verde Fugini. *Peça: foto
   cortada é falha de composição — o pré-voo tem de acusar, e o enquadramento respeitar a caixa.*
5. **A caixa "Fica a Dica" sumiu e deixou um buraco.** Sem texto ela não desenha (certo), mas o
   canto inferior direito ficou **vazio**, e a página fica torta. *Peça: sem dica, o quadro de
   pagamento ou o expediente **ocupa a lacuna** — a página nunca fica com um vão.*

### 🟠 Acabamento

6. **O Biscoito são três pacotes embolados** — ilegível a qualquer distância. *Uma embalagem só,
   ou uma foto de família tratada.*
7. **Escala desigual dentro da fileira**: o bloco do Sabonete tem ~4× a massa visual da Pringles
   ao lado. *Normalizar pela ÁREA de tinta, não pela caixa.*
8. **A 5ª fileira tem 2 produtos ao lado do quadro de pagamento** e parece órfã. *Ou completa a
   fileira, ou o quadro sobe e os 2 viram destaque.*
9. **"Detg."** continua abreviado. Com a zona nova sobra largura — cabe "Detergente".
10. **O expediente ocupa uma caixa grande para 3 linhas de 6 pt.**
11. **A marca continua no descritor** ("Creme de Avelã / Nutella", "Batata / Pringles"). É a
    **maior perda de venda da página** e segue esperando a palavra dele desde a ordem 18.

---

## §4 · PROVA DE ACEITAÇÃO

> Composta do banco do dono (com as três peças do WAL):
>
> 1. proporção da zona de foto **≤ 1,2** nas duas páginas;
> 2. **altura média da tinta do produto ≥ 85%** da altura da zona, medida nas 42 células;
> 3. **nenhuma etiqueta invade mais de 25%** da tinta de nenhum produto;
> 4. **nenhuma etiqueta a mais de 3 mm** da silhueta do seu produto;
> 5. **nenhuma foto cortada** pela borda da zona;
> 6. **nenhum vão vazio** maior que uma célula na página.

---

## §5 · Nota de método

Quinze ordens mexeram em `foto_fit`, `zona_flex`, `compactar_coluna`, no plano de fotos e no
pouso da etiqueta — todas para fazer a foto crescer. **Nenhuma perguntou qual era a proporção da
caixa.**

A conta que resolve é `47,1 ÷ 30,7 = 1,53`, e ela sempre esteve no banco.

> **L17 — ANTES DE ESCALAR, MEÇA A PROPORÇÃO.** Queixa de "a foto está pequena" começa comparando
> a proporção da ZONA com a do CONTEÚDO. Se a zona está deitada e o conteúdo é em pé, nenhum
> algoritmo de escala vai resolver — ele está otimizando dentro da caixa errada.

É irmã da **L15** ("antes de mexer no motor, some a tabela"). As duas dizem a mesma coisa:
**o erro estava nos dados declarados, e a busca foi toda no código.**
