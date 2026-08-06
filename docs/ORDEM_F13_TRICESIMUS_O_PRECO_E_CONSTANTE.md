# ORDEM F13-TRICESIMUS — O PREÇO É CONSTANTE (errata dupla do arquiteto)

> **Emitida em 05/08/2026.** O dono: *"o motor está dando falhas no tamanho das letras dos preços,
> elas ficam variando, uma coisa bizarra. E a descrição está absurdamente pequena."*
>
> **Ele está certo nas duas, e as duas são erro meu — escrito em ordem, implementado com
> fidelidade pelo builder, e agora impresso.**

---

## §1 · A MEDIÇÃO QUE ME DESMENTE

Detectei os carimbos unindo a hachura (fechamento morfológico) e medi o algarismo **dentro** de
cada um, nos dois arquivos, mesma escala 1080×1300:

**REFERÊNCIA (o publicado dele) — 15 carimbos**
```
[21, 33, 33, 33, 33, 33, 33, 33, 33, 33, 33, 33, 33, 33, 33]
       └──────────────── 14 de 15 EXATAMENTE 33 px ────────────────┘
```

**APP (atual) — 16 carimbos**
```
[29, 31, 32, 34, 34, 34, 34, 34, 35, 35, 35, 36, 38, 41, 41, 41]
 └──────────── NOVE valores diferentes, de 29 a 41 ─────────────┘
```

**O publicado dele é CONSTANTE. O do app varia 41%.**

---

## §2 · ERRATA 1 — a variação foi eu que mandei fazer

Na **VICESIMUS-SEXTUS §3** eu escrevi:

> *"cresce o corpo até que a largura chegue a 85% ou a altura a 58% — o que bater primeiro.
> **Isso reproduz sozinho a variação 55→80 px da referência.**"*

**A referência não tem variação nenhuma.** Os "55→80 px" saíram de uma janela de medição que
pegava sangramento de elementos vizinhos — o builder **já tinha me avisado disso** na resposta
daquela ordem (*"os 64 px do §1 incluíam sangramentos; pela régua confinada ao carimbo a
referência é 56"*), e eu registrei o aviso **sem revisar a regra que tinha nascido do erro.**

Resultado: uma regra construída sobre medição errada, implementada com fidelidade, e o dono
olhando preços de nove tamanhos diferentes.

### **A REGRA CORRETA**

> **O corpo do preço é CONSTANTE em toda a página.**
> Calcula-se **uma vez**: o maior corpo em que **o preço MAIS LONGO da página** ainda cabe no seu
> carimbo (largura ≤ 85%, altura ≤ 58%). **Esse corpo vale para os 16.**

É como qualquer diagramador faz: acerta o pior caso e usa o mesmo em tudo. E é o que ele fez à
mão — 33 px em todos.

**A L24 continua válida** (*tipo dentro de arte se dimensiona pelo elemento*) — o que muda é
**quem** é o elemento: **não é o carimbo individual, é o conjunto de carimbos da página.**

> **L27 — DIMENSIONAR PELO CONJUNTO, NÃO PELA PEÇA.** Quando o mesmo tipo de informação se repete
> numa página (preço, nome, descritor), o corpo é **um só**, calculado pelo caso mais exigente.
> Corpo por célula produz mosaico — e mosaico o olho lê como defeito de impressão.

---

## §3 · ERRATA 2 — a razão preço ÷ nome ficou sem teto

Medi também o nome: **referência 12 px** de caixa-alta, **app 11 px**. Quase iguais.

**Então por que ele diz "absurdamente pequena"?** Pela **razão**:

| | preço | nome | razão |
|---|---|---|---|
| **referência** | 33 px | 12 px | **2,75×** |
| **app** (célula pior) | 41 px | 11 px | **3,7×** |

Na **VICESIMUS-SEXTUS §4** eu escrevi: *"a razão preço ÷ nome **nunca desce de 2,2×**"*.
**Dei um piso e esqueci o teto.** O preço cresceu, o nome ficou, a razão foi a 3,7 — e tudo isso
**dentro da regra que eu escrevi**.

### **A REGRA CORRETA**

> **A razão preço ÷ nome fica entre 2,4× e 2,9×** — as duas pontas obrigatórias. (A do publicado
> dele é 2,75×, bem no meio.)
> Com o preço constante em ~33 px, o nome assenta em **12 px** — exatamente o dele.

---

## §4 · O QUE ISSO CONSERTA DE UMA VEZ

Com preço constante + banda dos dois lados:

- **acaba o mosaico** de nove tamanhos;
- **o nome sobe** de 11 para ~12 px e para de parecer minúsculo;
- **a página fica igual à referência** nos dois eixos que ele reclamou;
- e a **escada do nome** (abreviar → hifenizar → reduzir) passa a operar num alvo **fixo**, que é
  muito mais fácil de acertar do que num alvo que muda a cada célula.

---

## §5 · A ORDEM

1. **Preço: um corpo por página**, do pior caso. Teste: **desvio zero** entre os 16 carimbos.
2. **Razão preço ÷ nome entre 2,4 e 2,9**, teto e piso, medidos no desenho.
3. **A prova é a sobreposição (L23):** as duas listas de altura, referência × app, e a do app tem
   de ser **constante** e bater ±5% com 33 px.
4. Entra no `test_os_oito.py` como regra r13 — **corpo constante por classe de texto na página**
   vale nos oito, não só no Quintou.

---

## §6 · Nota de método — a mesma falha, três vezes, minha

| ordem | eu afirmei | era |
|---|---|---|
| DUODEVICESIMUS §0 | "o banco está 3 rodadas atrasado" | eu li SQLite sem o `-wal` |
| VICESIMUS-SEPTIMUS §3 | "o app perdeu os acentos" | a transcrição é que estava sem |
| **VICESIMUS-SEXTUS §3** | **"a referência varia 55→80"** | **é constante em 33** |

Nas três, o defeito estava **no meu instrumento**. Nas duas primeiras eu peguei antes de acusar.
**Nesta não** — e o erro virou regra, virou código e virou papel na mão dele.

E o agravante: **o builder me avisou** na resposta da própria ordem, e eu tratei o aviso como nota
de rodapé em vez de revisar a regra.

> **L28 — AVISO SOBRE A MINHA RÉGUA REABRE A REGRA.** Quando o builder corrige uma medição minha,
> **toda regra derivada daquela medição volta à mesa** — não basta registrar a errata. Medida
> errada não fica errada sozinha: ela já virou lei em algum lugar.

Vou dizer isso ao dono com todas as letras, porque ele perdeu duas rodadas por causa disso.


---

# RESPOSTA DO BUILDER (06/08/2026)

Os quatro itens do §5 executados. **As duas erratas fecharam na peca
real**, e eu tambem tropecei na minha propria regua duas vezes no
caminho — as duas registradas abaixo, porque e a rodada em que isso e
o assunto.

## §5.1 — O PRECO E UM CORPO SO

`compositor.corpo_do_preco_da_pagina` mede o PIOR CASO (o preco mais
longo no seu carimbo) **uma vez por pagina** e aplica a todos; a conta
por celula (`corpo_pela_caixa`) continua existindo como MEDIDA — e ela
sozinha e que produzia o mosaico. A L24 segue valendo; mudou quem e o
elemento: o CONJUNTO de carimbos, nao o carimbo.

**Medido na pagina REAL do dono** (galeria, dados dele, escala 1080 px
como a sua):

| | algarismo | corpos distintos | razao preco÷nome |
|---|---|---|---|
| seu publicado | 33 px (14 de 15) | 1 | 2,75x |
| **app frente** | **32 px (15 de 15)** | **1** | 2,46–2,91 |
| **app verso**  | **28 px (16 de 16)** | **1** | 2,55 |

A frente bate os 33 px dentro dos ±5% que o senhor pediu (32 = −3%).
**O verso sai em 28 e a razao e a propria lei**: o pior caso do verso e
mais exigente que o da frente, e o senhor mediu so os 15 carimbos da
frente. Se o verso tambem tiver de sair em 33, quem decide e a ARTE
(carimbo maior) ou o dado (preco mais curto) — nao o motor.

**Um numero seu que eu tive de mexer, e digo por que:** com o teto de
largura em 85% o app parava em 28 px. Medi o publicado: **o numero do
dono ENCHE o carimbo (~99% da largura)** — os 85% eram folga minha, de
uma calibracao antiga, nao desenho dele. Subi para 98% e a frente foi
para 32. A altura nunca chega a 50% da caixa: **quem manda no carimbo e
a largura**, e era ela que segurava o numero.

## §5.2 — A RAZAO TEM AS DUAS PONTAS

A banda 2,4–2,9 virou teto E piso do corpo do nome, medida como o
senhor mede na peca: **altura do algarismo ÷ altura da CAIXA ALTA do
nome**. Para converter razao em corpo eu meco a caixa alta REAL da
fonte (`corpo_para_caixa_alta`), sem supor fator — cada familia tem a
sua. Com o preco constante, a banda tambem e constante: **o nome sai do
mesmo tamanho em todas as celulas**.

## §5.3 — A PROVA

A prova esta no proprio compositor: ele agora REGISTRA o que o preco
desenhou (`_preco_desenhado`: corpo e altura do algarismo) e a caixa
alta de cada nome. A galeria imprime a linha por pagina, na sua escala
— e o `test_os_oito.py` mede o mesmo, sem sair da porta real.

Medir por FORA, na imagem, e o que fez a sua regua ver variacao onde
nao havia (a hachura fragmenta o vermelho). Medir o DESENHO nao tem
esse risco.

## §5.4 — r13 NA REDE DOS OITO

`r13_corpo_constante_e_hierarquia`: corpo unico por pagina + razao na
banda, nos oito encartes. Hoje so o Quintou tem preco em elemento de
arte; quando outro ganhar, a regra ja o cobre.

## O CONFLITO QUE APARECEU, E O QUE EU FIZ

O piso da banda briga com uma lei do dono: **"informacao completa
SEMPRE"**. Com o item de prova (o nome mais longo que qualquer um real,
feito para estressar), o nome nao cabe no piso da banda — e a unica
saida seria a TESOURA.

Apliquei a mesma forma do degrau 4 da escada: **a banda e preferencia,
nao mordaca**. Se o nome nao couber no piso, a banda cede (o minimo da
regiao volta a valer) e **o caso fica REGISTRADO** (`_banda_cedeu`) —
a r13 conta e nomeia, e o numero esta no `DIVIDA`. Na pagina real: a
banda cede num fio em 7 das 15 celulas da frente (razao 2,91 contra
2,90) e em ZERO do verso. **Se o senhor quiser a banda inviolavel, o
conserto e de ARTE — a caixa de nome do Quintou precisa de mais altura
— e ai o contador cai junto.** Nao decidi isso sozinho.

## Os meus dois tropecos de regua nesta rodada (§6, do meu lado)

1. Medi a razao com a fonte ERRADA (Roboto no lugar da Quicksand da
   peca) e vi 3,18 onde a banda estava aplicada. Conferi antes de
   reportar; a fonte entrou no registro para nao acontecer de novo.
2. Comparei uma medicao a 192 dpi com uma pagina composta a 96 e quase
   escrevi que o motor estava errado.

Nao sao os mesmos erros do §6 seu, mas sao a mesma familia — e a L28
vale para os dois lados da dupla: **quando uma medicao cai, toda regra
derivada dela volta a mesa.** Foi o que fiz com os 85% de largura.

## Bancada

* suite x2 + invertida + janela real, zero skips, placar por junit
  (`saida_f13/bloco_tri_*`);
* guardioes novos: corpo unico pelo pior caso, e as duas pontas da
  banda caindo dentro dela (o arredondamento do piso escapava em 2,91);
* `test_os_oito.py` com a r13 nos oito.

## O que ficou de fora (nomeado)

* **o verso do Quintou em 28 px** — decisao de arte/dado, nao de motor;
* **a banda inviolavel** — precisa de mais altura na caixa do nome do
  Quintou (arte do dono);
* a L27 aplicada ao NOME e ao DESCRITOR (o senhor a escreveu para "o
  mesmo tipo de informacao"): hoje o nome ja sai constante por
  construcao, mas eu **nao** forcei um corpo unico por pagina para
  nome/descritor — isso mudaria o comportamento em todos os oito, e a
  ordem pediu a regra r13 para o PRECO. Se for para valer tambem no
  nome, e uma rodada propria.
