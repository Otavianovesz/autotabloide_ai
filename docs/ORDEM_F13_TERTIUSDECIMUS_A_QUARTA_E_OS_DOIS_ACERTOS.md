# ORDEM F13-TERTIUSDECIMUS — OS DOIS ACERTOS DA TERÇA + A QUARTA DAS OFERTAS

> **Emitida pelo arquiteto em 28/07/2026.** A Terça saiu **muito boa** — as três fotos fixas no
> lugar, o `+` entre o sonho e o croissant, os discos pendurados, a data nascida sozinha.
> O dono apontou **duas** coisas, e as duas são precisas.
>
> E ele já trouxe a **Quarta das Ofertas** — três fotos e a tabela, na raiz.

---

## PARTE 1 · OS DOIS ACERTOS DA TERÇA

### A1 🔴 · O nome está saindo POR CIMA do painel

Nas quatro cestas, a segunda linha do nome fica dentro do painel branco
("Rezende", "Sem Osso", "Paleta Senepol", "Coxa Sobrecoxa") e **a primeira linha sai para fora**,
atravessando a palha da cesta e o microtexto "PADARIA BELO BRASIL":

```
   Salsicha Hot Dog        ← FORA do painel, sobre a arte
 ─ PADARIA BELO BRASIL ─
        Rezende           ← dentro
          kg
```

**A causa provável:** o piso do tipo cresceu o bloco para 2 linhas (correto, é a regra nova), o
bloco é centralizado verticalmente no rect da região, e **o rect não cabe 2 linhas** — então
metade transborda para cima. O painel branco é **desenhado na ARTE (o BASE)**, então a região
não tem como "crescer para dentro dele": ela cresce para fora e atravessa o desenho.

**O conserto tem duas metades e as duas são necessárias:**

1. **Na arte (regenerar a Terça):** o painel branco das cestas cresce para caber 2 linhas no
   piso do celular + o descritor. É o **passo 3 da precedência aplicado ao GERADOR** — o mesmo que
   você fez na Segunda (bandas 52→80). A Terça ficou de fora.
2. **No motor (a guarda que faltava):** **nenhum texto pode ser desenhado fora do rect da sua
   região.** Se o bloco não couber, ele **não transborda** — ele aciona a precedência
   (descritor sai, nome encurta) até caber, e só então desenha. Hoje ele desenha por cima da arte,
   que é a pior saída possível.

> **Isto é uma lacuna de invariante, não um ajuste:** "o texto vive dentro do seu retângulo"
> deveria ser lei do compositor desde sempre. Adicione o teste: para as 8 páginas, **nenhum pixel
> de tinta de texto fora do rect da região**. É medível por máscara.

### A2 🔴 · A data voltou a escrever "Ofertas válidas"

No selo da Terça está:

```
     ⌒ SAIU DO FORNO ⌒        ← gravado na arte
        Ofertas válidas       ← escrito pelo app  ✗
       SOMENTE 28/07          ← escrito pelo app  ✓
     ⌄ TODA TERÇA ⌄           ← gravado na arte
```

**É exatamente o C3 da OCTAVUS**, que eu mandei consertar e que foi aplicado **só à Segunda**.
A frase "Ofertas válidas" é redundante três vezes (o selo já diz o dia, o rodapé já diz a frase
inteira) e ela **atravessa o texto curvo gravado**.

**Conserte para os oito**, não para a Terça: o que o app escreve no selo é **só a data**.
E aplique a mesma medição do C3 — o **miolo limpo** do selo medido por pixel no BASE, não a caixa
inteira.

**E a lição, porque é a segunda vez que isto acontece nesta fase:** quando um conserto é de
**regra**, ele vale para os oito encartes. Quando você consertar um encarte, **pergunte se o
conserto é da página ou do motor** — e se for do motor, aplique nos oito na mesma rodada.
*(Isto é a L11 outra vez: a regra não pode viver numa página.)*

### A3 🟡 · Uma dúvida minha, para você responder

Na página, as quatro cestas mostram **Salsicha Hot Dog Rezende · Toturguita/Músculo Sem Osso ·
Paleta Senepol · Coxa Sobrecoxa** com preços 9,90 · 3,39 · 3,95 · 0,77.

A tabela dele traz: Salsicha 9,90 · Fígado Bovino 0,99 · Ossinho 1,81 · Coxa Sob Coxa 0,77 ·
Língua e Coração 0,66.

**Dois dos quatro (3,39 e 3,95) não existem na tabela dele.** Ou a página foi composta com uma
mistura de fontes, ou houve substituição de item (não só de foto). **Explique com dado** — e se
foi substituição, ela tem de ser **declarada na tela**, nunca silenciosa (I2).

---

## PARTE 2 · A QUARTA DAS OFERTAS

### §1 · Os arquivos, conferidos

| Arquivo | Tamanho | Estado |
|---|---|---|
| `Salgados.jpg` | 1080×1080 RGB | cru |
| `Pão de Queijo.jpg` | 1920×1080 RGB | cru |
| `Lanche na Chapa.jpg` | 1000×667 RGB | cru |
| `Quarta de Ofertas Tabela.jpeg` | 899×1599 | **foto de uma TELA** |

### §2 · A tabela — e ela é o teste de OCR mais duro até agora

**Não é um documento: é uma FOTO DE MONITOR.** Dá para ver a moldura preta do monitor, o reflexo
da tela, a distorção de perspectiva e até um ícone de interface no canto. Todas as tabelas
anteriores eram arquivos limpos. **Esta é o caso real de quem fotografa a tela do PC do escritório**
— e é provavelmente o caso mais comum no dia a dia dele.

Transcrição (confira no OCR, não confie nesta cópia):

```
ANOTA-AI, PORQUE CHEGOU A QUARTA-FEIRA ESPETACULAR DE OFERTAS, BELO BRASIL
FAÇA SUAS COMPRAS COM MUITO MAIS ECONOMIA E COMPROVE O QUE ESTAMOS ANUCIANDO.
PREÇO IMBATIVEL É AQUI NO BELO BRASIL

▶ LANCHE NA CHAPA COM 20 % de DESCONTO              ← SEM PREÇO
▶ MINI SALGADINHOS BB-X __À__ 100g __ só ____       4,99
▶ PÃO DE QUEIJO TRADICIONAL BB-X   à _ 100g _ POR   4,99
▶ BOMBOM GAROTO / NESTLE 220G _________ só _______ 16,66
▶ LEITE INTEGRAL PARMALAT 1LT ________ POR _______  5,95
▶ BISCOITO BULNEZ 270G ______________ POR _______   4,90
▶ MILHO VERDE ETTI 170G _____________ só ________   3,88
▶ OLEO DE SOJA CONCORDIA 900ML ___ · _ POR _____    7,70
```

### §3 · O que esta tabela exerce

**Q1 🔴 A conta FECHA EXATA, e é a primeira vez.**
A Quarta tem **8 células: 3 fixas + 5 livres**. A tabela traz **3 itens fixos** (Lanche na Chapa,
Mini Salgadinhos, Pão de Queijo) **+ 5 itens livres** (Bombom, Leite, Biscoito, Milho, Óleo).
**3 + 5 = 8.** Nada sobra, nada falta. Se der certo, é a prova mais limpa possível.

**Q2 🔴 Um item com PERCENTUAL em vez de preço.**
`LANCHE NA CHAPA COM 20 % de DESCONTO` **não tem preço** — e a arte da Quarta tem, exatamente
naquela célula, a **pílula verde "20% off"**. Isto não é coincidência: a arte foi desenhada para
essa mecânica (o mesmo achado da Terça com os 50%/25%).

O app precisa entender: **item sem preço + com percentual → a célula mostra o percentual, não um
preço vazio.** Você já tem `PapelTexto.DESCONTO` e a pílula do `pctpod`. **Reuse (L9).**
E o pré-voo **não pode** reclamar de "item sem preço" nesse caso.

**Q3 🔴 A foto de tela é o teste do OCR de verdade.**
Moldura, reflexo, perspectiva. Se o Qwen2.5-VL não der conta, **o achado é esse** e ele vale mais
que a página: significa que o caminho mais comum do dono (fotografar a tela) não funciona.
**Não recorte nem endireite a imagem à mão para ajudar.** Se precisar de pré-tratamento
(deskew, recorte da área do documento), isso é **feature do app**, não conserto de bancada — e
entra declarada.

**Q4 🟠 As armadilhas de texto desta tabela**

| No papel | O que sai | Nota |
|---|---|---|
| `OLEO DE SOJA` | **Óleo de Soja** | acento faltando |
| `IMBATIVEL` / `ANUCIANDO` | **não vira produto** | prosa com typo dele; a IA não corrige nem cria item |
| `BB-X` | **BB-X** | marca da casa; **não** "corrigir" para BBX ou Belo Brasil |
| `GAROTO / NESTLE` | **Garoto/Nestlé** | a barra é parte do nome; acento no Nestlé |
| `MILHO VERDE ETTI` | **Milho Verde Etti** | — |
| `▶` no início | descartado | marcador visual, não é texto |
| `20 %` na prosa | **não é preço** | T3 da DUODECIMUS |

**Q5 🟠 Os três fixos com foto escolhida — o segundo uso real do N1.**
Lanche na Chapa, Mini Salgadinhos e Pão de Queijo são as **três células fixas** da Quarta. As
fotos estão na raiz, cruas. E note: **dois deles têm preço na tabela** (4,99 e 4,99) — ou seja,
é o modo **"preço da semana"**, exatamente como o Kit Burguer. O terceiro (Lanche) tem percentual.
**Prove os três modos numa página só.**

*(Ele já tinha dito, meses atrás: "a única coisa que pode mudar raramente é o preço do mini
salgado e do pão de queijo" — a tabela confirma. O desenho do N1 estava certo.)*

---

## §4 · A ORDEM DE ATAQUE

1. **A2** — a data só com a data, **nos oito** (é regra, não página).
2. **A1** — a guarda "texto não sai do rect" no motor **+** o painel da Terça crescido na arte.
   Com o teste de máscara nas 8 páginas.
3. **A3** — explicar os dois itens que não são da tabela dele.
4. **A Quarta**, pelo caminho do dono, com os três fixos e a foto de tela.

**Condição de aceitação, a mesma de sempre:** ele abre, importa, e sai certo. Zero toque à mão.

E uma que vale a pena registrar: **se a foto de tela derrubar o OCR, pare e reporte.** Não force
a página a existir com dado digitado — o valor deste teste é justamente descobrir se o caminho
mais comum dele funciona.


---

# Resposta do builder (Fable) — 28/07/2026

## A1 — o texto nunca mais sai do painel (as duas metades + o invariante)

- **Na arte:** o remendo das cestas cresceu 66→96 px no gerador (`gen_terca_final.py`) e a
  Terça foi REGENERADA (Playwright); o builder acompanhou (rótulo/nome de 2 linhas/descritor
  reposicionados dentro do painel). O reimport preservou as fixas do dono (a guarda de sempre).
- **No motor, duas guardas:** (1) o passo 3 da precedência só cresce a banda **colada na
  foto** — com um VÃO de arte entre a foto e a banda (o caso da cesta), crescer pintaria texto
  sobre o desenho; a cadeia segue ao passo 4/5 (por teste); (2) a REDE do invariante em
  `_desenhar_texto`: bloco maior que o rect **não transborda pelo alinhamento** — clamp + corte
  ao que cabe (só dispara em bug; a precedência evita antes).
- **O teste de máscara pedido:** `test_a1_nenhum_texto_fora_do_rect_nas_8_por_mascara` — as 8
  páginas compostas COM e SEM textos; todo pixel que mudou tem de estar dentro do bbox
  (rot-aware, folga de sombra) de alguma região da célula. O invariante agora é medido.

## A2 — só a data, NOS OITO (regra, não página)

`so_data=True` nos selos redondos com curva gravada — Segunda (já tinha), **Terça, Quarta,
Peixe, Sexta, Sábado e o tijolo do Quintou** — com o miolo limpo de cada um **MEDIDO por pixel
no BASE** (a mesma medição do C3, automatizada: a faixa de menor variância dentro do rect):
Terça y 116–142 · Quarta y 367–393 · Peixe y 144–170 · Sexta y 154–180 · Sábado y 154–180.
**Exceções DE ARTE, declaradas:** o Jornal p1/p2 (a validade é a linha do cabeçalho — a frase
é o conteúdo) e o verso do Quintou (o disclaimer longo do publicado). Guardião novo
(`test_a2_o_selo_escreve_so_a_data_nos_oito`) crava os 8 + as exceções. A lição aceita: a
pergunta "é da página ou do motor?" agora tem teste que responde por mim.

## A3 — explicado com dado (e é a melhor notícia da fase)

O meu projeto (id=11) tem exatamente os 5 da tabela (Fígado 0,99 · Ossinho 1,81…), sem fotos.
A página com Toturguita/Músculo (3,39) e Paleta Senepol (3,95) é o **projeto id=12 "28/07" —
que EU não criei**: o DONO abriu o app, montou a Terça dele, TROCOU dois itens pelo acervo
(com fotos em tudo), corrigiu o "1kg" para "kg" na salsicha, e a validade nasceu da cascata no
fluxo DELE (validade "SOMENTE 28/07", evento "Terça do Pão" — lidos do banco). Não houve
mistura de fontes nem substituição silenciosa: **foi o dono usando o app sozinho** — a
condição de aceitação das últimas quatro ordens, acontecendo de verdade.

## PARTE 2 — a Quarta (o log: `saida_f13/_quarta_raiz_real.log`)

**Q3 — O OCR VENCEU A FOTO DE MONITOR.** Moldura, reflexo, perspectiva — o Qwen2.5-VL leu os
**8 itens com TODOS os preços exatos** (4,99 · 4,99 · 16,66 · 5,95 · 4,90 · 3,88 · 7,70) em
67s, e a prosa ("ANOTA-AI…", "PREÇO IMBATIVEL…") não virou produto. Nenhum tratamento na
imagem. O caminho mais comum do dono FUNCIONA.

**Q1 — a conta fechou exata:** 3 fixas + 5 livres = 8; estante 5, células 5, zero fora da
grade. **Q2 — o item com percentual existe:** o parser entende "COM 20 % de DESCONTO" (item
com valor comercial, não prosa — e o leve-3 da Terça continua no balde, por teste), o
`ItemMesa.desconto_pct` viaja, o papel DESCONTO desenha o dado quando não há de/por (a pílula
laranja **-20%** na célula do Lanche — a fixa que a arte desenhou para isso), o pré-voo cala,
e `atualizar_fixos_pela_tabela` atualiza o desconto da semana como atualiza o preço.
**Q5 — os três modos numa página:** Lanche (desconto declarado) + Mini Salgadinhos e Pão de
Queijo (preço da semana, 4,99/4,99 — "a única coisa que muda raramente", como o dono disse
meses atrás). **Q4:** BB-X intocado, "Garoto & Nestlé" com a dupla, ▶ descartado no parser,
acentos pelo caminho de sempre. As 3 fotos pelo degrau 1 real (20,5s/8,3s/7,3s · 1 objeto ·
nota boa nas três — J18 não precisou acender).

**Validade:** `SOMENTE 29/07` nascida sozinha (quarta, o dia da página). Projeto **id=13**.

## Achados nomeados (sem consertar nesta rodada)

1. O fio do **desconto não passa pelo caminho do OCR** — o Q2 vive no parser da COLAGEM; a
   linha do Lanche via OCR chegou sem `desconto_pct` (o template já tinha o 20%, a página saiu
   certa). Ligar o mesmo reconhecimento no parser do OCR: nomeado para o G.
2. A minha 1ª atribuição pôs o Lanche na fixa errada (a pílula do desconto vive na fixa-3) —
   corrigido no ato pelo OLHAR; o diálogo dos fixos poderia MOSTRAR qual célula tem papel
   DESCONTO (nomeado).
3. Os 5 itens do OCR entraram VERMELHOS e o Concluir liberou com 5 na estante — conferir o
   critério de liberação do diálogo com vermelho-resolvido (nomeado; a página saiu com os 5
   certos e fotos do acervo).
4. Herdados: reuso de projeto por nome; o crash 0xC0000409 da dupla isolada (COND-10).



## Placares (junit `bloco_ftertius_*`)

**Suíte 1043 ×2 zero skips exit-0** (1039 + os 5 da TERTIUSDECIMUS − 1 consolidado; runs 1 e 2);
**invertida 1043/0/0**; **janela real 4/0/0**. *Incidente nomeado:* o run2 da 1ª bancada
crashou no teardown SEM escrever o junit (o 0xC0000409 da família COND-10) — re-rodado limpo.

