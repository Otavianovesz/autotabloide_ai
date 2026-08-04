# ORDEM F13-SEPTIMUSDECIMUS — O JORNAL COMO PEÇA GRÁFICA

> **Emitida pelo arquiteto em 03/08/2026**, sobre as duas páginas que o dono recompôs na v4.1
> (`3f6c140`) e mandou com a queixa completa.
>
> Ele pediu explicitamente o **conceito, não o remendo**: *"não é só para esse item específico.
> É para você arrumar a ideia, o contexto ali. Pensa como é que faz para poder melhorar."*
>
> **Não opinei: medi.** Tudo abaixo sai da tabela de geometria do banco dele e do valor de cor
> das regiões. A queixa principal — *"a imagem fica em cima do preço do outro produto"* — **não é
> bug de desenho. A grade se sobrepõe por construção**, e dá para provar em milímetros.

---

## §1 · A PROVA EM NÚMEROS (banco real, layout "Jornal do Mês")

**A célula da página 2, peça por peça:**

```
IMAGEM      y   29,6 ..  56,1   (26,5 mm)
NOME        y   56,1 ..  64,0   ( 7,9 mm)
SUBTITULO   y   64,0 ..  73,6   ( 9,5 mm)
PRECO       y   73,8 ..  84,9   (11,1 mm)
                                ────────
CÉLULA INTEIRA:  29,6 .. 84,9  =  55,3 mm
```

**E o passo entre as linhas da grade:**

| gap | preço da linha termina em | foto da linha seguinte começa em | folga |
|---|---|---|---|
| 1 → 2 | 84,9 | **83,1** | **−1,8 mm** 🔴 |
| 2 → 3 | 138,4 | 144,5 | +6,1 mm |
| 3 → 4 | 199,8 | **197,9** | **−1,9 mm** 🔴 |
| 4 → 5 | 253,2 | 259,3 | +6,1 mm |

**Em duas das quatro emendas, o retângulo da foto da linha de baixo começa DENTRO do retângulo
do preço da linha de cima.** E como o desenho é por slot, na ordem da lista, **a foto de baixo é
pintada por cima do preço de cima**. É exatamente o que ele viu:

- o **Suco de Uva** em cima do preço da **Rosquinha**;
- o **Milho Pipoca** em cima do preço do **Biscoito**;
- o **Desinfetante Urca** em cima do preço do **Feijão**;
- o **Sabonete Nivea** em cima do preço do **Macarrão**;
- o **Papel Hig. Mili** em cima do preço do **Desinfetante**.

Não é coincidência nem foto "grande demais". **São as linhas 1→2 e 3→4 da tabela.**

Na **página 1** o quadro é o mesmo com outra roupa: as folgas 3→4 e 4→5 são de **+3,4 e +3,5 mm**
— e o carimbo de preço é desenhado **rotacionado**, então extravasa o próprio retângulo. Folga de
3 mm com carimbo torto é colisão na prática.

**E o passo é irregular:** 53,5 / 61,4 / 53,4 / 61,4. Linhas ímpares apertadas, pares folgadas.
É isso que dá a sensação de "descolado" que ele já tinha reclamado — o olho lê ritmo, e não há.

---

## §2 · N1 🔴 · AS TRÊS LEIS DO DIAGRAMADOR (o conceito que ele pediu)

Consertar a linha 1→2 do Jornal resolve hoje e volta a quebrar no próximo layout. O que falta é
**lei de grade**, válida para os oito encartes e para os que ele desenhar amanhã:

### **L-A · A CÉLULA É UMA CAIXA FECHADA**
Nada que uma célula desenha cruza o retângulo da própria célula. Foto que não cabe **encolhe**;
nunca extravasa. Hoje a foto respeita o *seu* retângulo, mas o retângulo dela invade o vizinho —
por isso a lei precisa da irmã abaixo.

### **L-B · O PASSO DA GRADE ≥ ALTURA DA CÉLULA + RESPIRO**
A tabela de geometria **não pode declarar linhas mais próximas do que a célula que ela mesma
define**. Respiro mínimo **4 mm** (com carimbo rotacionado, menos que isso encosta).

> **O teste que fecha isso é de TABELA, não de pixel:** um teste lê a geometria dos **oito**
> encartes, calcula `altura_da_célula` e `passo_da_linha` de cada um, e **reprova** qualquer
> layout onde `passo < altura + 4 mm`. Roda em milissegundos e pega o erro no lugar onde ele
> nasce — antes de virar tinta.

### **L-C · O PREÇO É A ÚLTIMA CAMADA**
Em qualquer ordem de desenho, **os carimbos de preço de TODA a página são pintados depois de
TODAS as fotos**. É o cinto de segurança para o dia em que a L-A falhar: o pior caso vira "foto
encostou no preço", nunca "preço sumiu embaixo da foto".

### **L-D · O RESPIRO SE PAGA NO RODAPÉ — NUNCA NA FOTO NEM NO CORPO**
Quando faltar milímetro, ele sai da faixa inferior. **Jamais** encolhendo foto ou tipo: foi
exatamente o erro da v4 que o dono já reprovou ("as imagens diminuíram ainda mais").

---

## §3 · O ORÇAMENTO DA PÁGINA — de onde saem os milímetros

A página tem **381 mm**. O último preço da p2 termina em **314,6 mm**. **Sobram 66,4 mm de
rodapé — 17% da página** para faixa de pagamento, expediente e Fica a Dica.

**Conta do passo uniforme:**

```
célula 55,3 + respiro 4,0            = 59,3 mm de passo
5 linhas: 29,6 + 4×59,3 + 55,3       = 322,1 mm
rodapé restante: 381 − 322,1          = 58,9 mm
```

**Cabe.** O passo uniforme de 59,3 mm mata as duas colisões, dá ritmo constante à página **e
ainda deixa 58,9 mm de rodapé** — sem tirar um milímetro de foto ou de texto.

E o dono autorizou apertar o rodapé (*"pode trazer a linha um pouco mais para baixo para ter mais
espaço para os itens"*). **Cada 10 mm que o rodapé ceder viram +2 mm por linha** — que devem ir,
nesta ordem: **(1) corpo do texto, (2) altura da foto**.

**Alvos de corpo** (hoje → proposto), a confirmar no teste do celular:

| | hoje | proposto |
|---|---|---|
| NOME (p2) | 12,5 pt | **14,0 pt** |
| SUBTITULO | 10,0 pt | **11,5 pt** |
| PREÇO (p2) | 20,0 pt | **23,0 pt** |

---

## §4 · N2 🔴 · O PREÇO É O TEXTO MENOS LEGÍVEL DA PÁGINA (medido)

Calculei o contraste de cada cor sobre o creme do fundo (`#F7F2E7`):

| elemento | cor | contraste | veredito |
|---|---|---|---|
| NOME | `#201B12` | **15,3 : 1** | ótimo |
| SUBTITULO | `#6E675C` | **5,0 : 1** | passa, mas ver §5 |
| **PREÇO** | `#C9641A` | **3,5 : 1** | 🔴 **abaixo do mínimo (4,5:1)** |

**O elemento mais importante do encarte é o de pior contraste da página.** O dono pediu
*"negrito, mais chamativo"* por instinto; a medição confirma com número.

**Três consertos que se somam:**

1. **Cor** — descer para algo na faixa `#A8410E`–`#96340B` (**≥ 7:1**). O vermelho `#C0392B` que
   a própria arte já usa na forma também serve.
2. **Peso** — **atenção: não existe Fraunces Bold no projeto.** Só há `Fraunces-Regular`,
   `Fraunces-Italic` e `Fraunces-SemiBold`. Então "negrito" exige uma decisão:
   **(a)** trazer `Fraunces-Bold`/`Black` para a pasta de fontes, **(b)** usar o
   `Archivo-Bold.ttf` que já existe no projeto só para o preço, ou **(c)** engrossar por contorno
   no compositor. **Peça: (a)** — mantém a família da peça. Se não for possível, **(b)**.
3. **Tamanho** — 20 → 23 pt, conforme §3.

---

## §5 · N3 🟠 · O cinza some na impressão

`SUBTITULO` = `#6E675C`, **itálico**, **10 pt**. Passa no WCAG de tela (5,0:1) e **falha no
papel** — que é a régua certa aqui, porque ele imprime.

Itálico serifado, cinza médio, 10 pt: as hastes finas do Fraunces itálico não seguram tinta nesse
corpo. **Peça:** `#4A443B` (≈ 8:1), **11,5 pt**, e **avaliar largar o itálico** abaixo de 12 pt —
o itálico é ornamento; a informação (peso, marca, sabores) é o que o cliente lê no carrinho.

> **Régua nova a adotar:** o contraste do encarte se mede **contra o papel**, não contra a tela.
> Elemento de venda (nome, preço, peso) exige **≥ 7:1**; ornamento pode 4,5:1.

---

## §6 · N4 🔴 · O descritor da família repete o nome três vezes

Na p2, a Rosquinha saiu:

> **Rosquinha** — *Mabel · Coco e Leite · **Rosquinha Mabel 600g Coco** ou **Rosquinha Mabel 600g
> Leite***

**"Rosquinha" três vezes, "Mabel" três vezes, "600g" três vezes.** O descritor está concatenando
os **nomes completos dos membros** da família em vez de listar só o que os diferencia.

**A regra:** o descritor da família diz **a base uma vez e as diferenças uma vez**:

> **Rosquinha Mabel** — *Coco ou Leite · 600 g*

Ou seja: **fatorar**. O que é comum a todos os membros sobe para o nome; só o que varia entra na
lista de sabores. O app já sabe fazer isso — a Sardinha saiu certa (*"Coqueiro · Tomate, Óleo ou
Limão · 125 g"*) e o Amaciante também. **A Rosquinha caiu num caminho diferente** (provável: a
família nasceu com os nomes já completos, e o fatorador só age quando o sabor vem separado).

**Peça:** o fatorador roda **sempre**, sobre os nomes dos membros — encontra o prefixo/sufixo
comum, tira-o, e o que sobra vira a lista. Teste com a Rosquinha e com um caso onde os membros
**não** têm prefixo comum (aí o descritor lista os nomes mesmo — e isso é correto).

---

## §7 · N5 🔴 · O "Fica a Dica" é texto cravado na arte — a IA nunca é chamada

O dono desconfiou: *"parece que não foi gerado pela IA. Quem fez isso aqui parece que foi você."*

**Ele está certo.** `app/rendering/encartes.py:882`:

```python
texto=("Monte o carrinho pelo Jornal do Mês: as "
       "ofertas valem o mês inteiro — aproveite "
       "para abastecer a despensa de uma vez só."),
```

Três problemas empilhados:

1. **É texto fixo do layout**, escrito pelo builder, não pelo modelo.
2. **É factualmente falso** — a oferta vale **de 3 a 27**, não "o mês inteiro". A própria página
   diz "DE 03/08 ATÉ 27/08" duas linhas acima.
3. **Não é uma dica.** É um convite a comprar. O dono foi claro sobre o que a seção é:
   *"era pra dar alguma dica dos itens que tem ali pra você fazer um preparo, alguma história."*

**E a função existe:** `app/ai/enriquecimento.py:426` `gerar_dica(nomes, limite, motor, …)`. Ela
recebe os nomes dos itens da página, respeita um teto de caracteres, tem prompt configurável e
guarda contra repetir dicas anteriores. **Está pronta e é inalcançável na prática** — o único
gatilho é um botão (`btn_dica`) dentro do painel de propriedades, que só aparece se o dono
selecionar exatamente aquela região e souber que o botão existe.

**É a L10 outra vez** (*"nada é feito enquanto não estiver alcançável pelo dono"*), agora numa
função de IA inteira.

**Peça:**
- O papel `DICA` **chama `gerar_dica` sozinho** quando a página compõe, com os nomes dos itens
  daquela página, e grava o resultado no projeto (congela — a dica da edição é da edição).
- Sem IA, **degrada com aviso** (I2) e escreve uma dica **neutra e verdadeira**, derivada da
  validade real — nunca "o mês inteiro".
- O botão do painel continua, agora como **"gerar outra"**.
- O texto cravado em `encartes.py` **sai** — no lugar, o papel nasce mudo (como o `EDICAO`, que
  o próprio arquivo já faz: *"sem dado fica MUDO"*).

---

## §8 · N6 🟠 · Não existe como editar o texto de um item na Mesa

*"quando preciso alterar o texto em si no tabloide, ele não deixa e faz com que eu edite só algo
que nem funciona."*

O único campo de texto do painel é `texto_fixo` (`painel_propriedades.py:190`), cujo próprio
tooltip diz: *"Texto do **LAYOUT**"* e cujo placeholder diz *"vazio = usa a validade do projeto"*.
Ou seja: ele edita **o molde**, e o dado vivo do projeto sobrescreve na composição. **Editar e não
mudar nada** é exatamente o que ele descreveu.

**Peça:** editar o texto **daquele item, naquele slot** — nome e descritor —, gravado como
override do projeto (I1, por uid), **sem tocar no acervo**. O mecanismo de override por slot já
existe (F7.3, `overrides` viaja no `salvar_projeto`); falta a porta: **duplo-clique no texto da
célula abre a edição**, e um badge discreto marca "editado nesta edição".

---

## §9 · N7 🟠 · Todo arquivo exportado se chama "tabloide"

`app/qt/telas/mesa.py:3181`:

```python
self, "Exportar tabloide", "tabloide.png",
```

Nome cravado. Ele exporta o Jornal de agosto, a Segunda do dia 3 e a Terça do dia 4 — e os três
querem gravar `tabloide.png` na mesma pasta, um por cima do outro.

**Peça:** o nome nasce do que a peça É:
`{evento ou layout} {data da edição}{ – pág N se houver}.png`
→ `Jornal do Mês 03-08 a 27-08 – pág 1.png`, `Segunda dos Frios 03-08.png`.

Barra e dois-pontos viram hífen (Windows). Se o arquivo já existir, sufixo ` (2)` — **nunca
sobrescrever calado** (I2).

---

## §10 · ORDEM DE ATAQUE

**Onda 1 — a página para de se atropelar (é o que ele vê primeiro):**

1. **N1/L-B** — o passo uniforme de 59,3 mm no Jornal, **e o teste de tabela nos oito encartes**.
2. **N1/L-C** — preço na última camada.
3. **N1/L-A** — a célula como caixa fechada (a lei geral, com o teste adversarial).
4. **N2** — a cor, o peso e o corpo do preço (com a decisão da fonte).
5. **N3** — o cinza do descritor.

**Onda 2 — a informação fica certa:**

6. **N4** — o fatorador do descritor de família (a Rosquinha).
7. **N5** — o Fica a Dica pela IA, com degradação honesta.

**Onda 3 — o dia a dia:**

8. **N6** — editar o texto do item por override de projeto.
9. **N7** — o nome do arquivo exportado.

E o **rodapé** (§3) entra junto da Onda 1: ele cede o que for preciso, e o ganho vai para corpo
e foto, nessa ordem.

---

## §11 · PROVA DE ACEITAÇÃO

> 1. **Nenhum retângulo de célula encosta no de outra** — provado pelo teste de tabela nos
>    **oito** encartes, com o número (`passo − altura`) impresso no relatório de cada um.
> 2. Na página composta com os **42 itens reais dele**, **nenhuma foto toca nenhum carimbo de
>    preço** — medido por pixel, não a olho.
> 3. O preço mede **≥ 7:1** de contraste e sai em peso **Bold** de verdade.
> 4. A Rosquinha sai **"Rosquinha Mabel · Coco ou Leite · 600 g"** — cada palavra uma vez.
> 5. O Fica a Dica da edição **veio do modelo**, cita itens que estão na página, e **não afirma
>    "o mês inteiro"**.
> 6. Ele dá duplo-clique num nome na Mesa, corrige, e a correção **sai na página e não muda o
>    acervo**.
> 7. Ele exporta três peças diferentes na mesma pasta e **fica com três arquivos**.

---

## §12 · Nota de método — a terceira família de erro

Já registrei duas: *"verdade num artefato, falsa no que o dono usa"* e *"motor certo, vitrine
errada"*. Esta rodada acrescenta a terceira, e ela é a mais barata de evitar:

> **O erro estava na TABELA, e todo mundo foi procurar no DESENHO.**

Cinco rodadas mexeram em `foto_fit`, `nome_fit`, `compositor` e `zona_flex` para consertar
sobreposição e tamanho de foto. **A colisão nunca esteve no desenho** — está em duas linhas da
tabela de geometria do `encartes.py`, e aparece com uma subtração de dois números.

> **L15 — ANTES DE MEXER NO MOTOR, SOME A TABELA.** Toda queixa de "está sobrepondo / está
> apertado / está torto" começa medindo a **geometria declarada**. Se `passo < altura`, o motor
> está inocente. Um teste de tabela custa milissegundos e vale por cinco rodadas de pixel.
