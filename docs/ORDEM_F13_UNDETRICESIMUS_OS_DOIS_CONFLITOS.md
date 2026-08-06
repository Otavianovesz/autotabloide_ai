# ORDEM F13-UNDETRICESIMUS — DESPACHO DOS DOIS CONFLITOS

> **Emitida pelo arquiteto em 05/08/2026**, em resposta ao PARADO (L7) da DUODETRICESIMUS.
> O builder fez a coisa certa: **não derrubou lei sem ordem** e declarou os dois conflitos com o
> vermelho na mão. Despacho os dois, e trago uma **terceira informação que ele não tinha**.

---

## §1 · CONFLITO A — L23 (o original manda) × L25 (não hifenizar marca)

**Os fatos:** o publicado dele hifeniza **"Cerveja Itaipa-va"** e **"Frango Ma-rombi"** — as duas
são marca. Logo, a prática dele **é** hifenizar marca.

**Meu despacho: nenhuma das duas cede — a L25 vira PREFERÊNCIA ORDENADA, não proibição.**

Razão: no Illustrator a hifenização é uma caixa de seleção. Quando ela está ligada, quebra marca
também. **Isso é subproduto da ferramenta, não decisão de design** — e a L23 é normativa sobre
**intenção** (o layout, o carimbo, o painel do logo, a data girada, o alinhamento à esquerda, as
abreviações), não sobre o que é claramente automático.

E há o critério prático: quebrar "Itaipa-va" **não custa venda**; **texto pequeno custa** — e ele
reclamou disso cinco vezes.

### **A escada, com o degrau novo:**

```
1.  cabe no corpo cheio                    →  desenha
2.  não cabe  →  ABREVIA (glossário dele)
3.  ainda não →  HIFENIZA palavra COMUM     ("Achocola-tado", "Concen-trado")
4.  ainda não →  HIFENIZA QUALQUER palavra  ("Itaipa-va")   ← degrau novo
5.  ainda não →  reduz o corpo
6.  piso
```

**A marca só se parte quando a alternativa é encolher o texto.** Isso reproduz o publicado dele
(que precisou da quebra) **e** protege a marca onde há folga — nos oito encartes, sem configuração.

---

## §2 · CONFLITO B — piso inviolável × texto que vaza da caixa

**Meu despacho: o piso NÃO cede. A CAIXA cede.**

A razão está nas leis que já valem:

- O **piso** nasce de um fato físico — a distância de leitura no celular (OCTAVIS/C1). É **regra**.
- A **altura da região** é um número que alguém digitou na tabela de geometria. É **dado**.
- E o projeto já decidiu essa hierarquia duas vezes: **UNDECIMUS** (*"a regra não pode ser dado"*)
  e **L15** (*"antes de mexer no motor, some a tabela"*).

**Regra vence dado.** Quando uma linha no piso não cabe na caixa, **a caixa está errada** — e o
conserto é a caixa crescer, não o texto encolher.

### **A execução, em três degraus:**

1. A região **cresce em altura** o necessário para uma linha no piso, e o relatório **declara** o
   crescimento (nunca calado — I2).
2. Se crescer **colidir com a fileira vizinha** (a L-B da grade), aí é **erro duro**: a página não
   compõe e o pré-voo diz *"a região X do layout Y não comporta uma linha legível — a grade precisa
   de mais altura aqui"*.
3. **Em nenhuma hipótese o texto vaza.** Vazar é o único resultado proibido dos três.

**E o caso do `min == max`:** região com piso igual ao teto é **defeito de layout**, não caso de
uso. O import passa a **recusar** e a apontar a região.

> **L26 — QUANDO DUAS LEIS BOAS COLIDEM, A COLISÃO É O ACHADO.** Não se faz nenhuma ceder no
> escuro: mede-se qual é **regra** e qual é **dado**, a regra vence, e o dado defeituoso vira
> aviso nomeado. Se as duas forem regra, para-se e pergunta-se ao dono.

---

## §3 · A TERCEIRA INFORMAÇÃO — só o Quintou tem referência publicada

O builder pediu *"a rodada da Quinta do Peixe com a referência publicada dela ao lado"*.
**Ela não existe.** Varri o repositório:

```
arte/quintou/        frente_referencia.png   verso_referencia.png     ← o único
Templates novos/Quintou/   Frente Real.png · Frente Completo.png      ← o único
Templates novos/artes/quinta-do-peixe/   BASE · CURVAS · MASTER · PREVIEW
Templates novos/artes/{jornal, quarta, sabado, segunda, sexta, terca}/  idem
```

**Sete dos oito encartes NÃO têm peça publicada pelo dono.** Foram **desenhados pelo builder** a
partir das descrições faladas dele.

### Isso muda três coisas:

**(a) A L23 vale só para o Quintou.** Nos outros sete não há o que sobrepor — e cobrar
"indistinguível do original" onde não há original seria régua inventada.

**(b) Explica a Quinta do Peixe.** Os "quatro arranjos internos diferentes" não são regressão:
**ninguém nunca definiu como aquela célula deve ser.** Foi desenhada uma vez, de ouvido, e nunca
teve padrão escrito.

**(c) O padrão dos sete tem de ser DEFINIDO, e o lugar dele é o teste dos oito.**

### O padrão de célula que eu defino agora (para os sete sem referência):

```
CÉLULA DE GRADE          CÉLULA DE DESTAQUE (horizontal)
┌───────────────┐        ┌──────────────────────────────┐
│     FOTO      │        │  NOME              ╭───────╮ │
│   (≥85% alt)  │        │  descritor         │ FOTO  │ │
├───────────────┤        │  PREÇO             │ ≥55%  │ │
│ NOME          │        │                    ╰───────╯ │
│ descritor     │        └──────────────────────────────┘
│ PREÇO         │          texto à esquerda, foto à direita
└───────────────┘          SEMPRE — as duas grandes iguais
```

- **um arranjo por classe de célula**, e só duas classes;
- **o produto ocupa ≥ 55%** da célula de destaque e **≥ 85% da altura** da zona na grade;
- **a validade da página não se repete dentro de célula de produto** (o caso das duas células do
  Peixe);
- **um peso por item** (a regra do Jornal, agora nos oito — o `Camarão · 250g · 800 g` cai aqui);
- **um patamar de preço maior** para as células de destaque.

**Estas cinco entram no `test_os_oito.py` nesta rodada.** É exatamente o que a rede foi feita para
receber.

---

## §4 · O QUE EU RECONHEÇO NA ENTREGA DELE

Três coisas merecem registro, porque são o comportamento que eu venho cobrando:

1. **Ele conferiu o próprio instrumento antes de reportar.** A primeira versão da rede acusou 6
   encartes de defeitos inexistentes (media o nome cru, sem a escada). Ele viu, corrigiu e só
   então reportou. **É a lição do §8 da VICESIMUS-SEPTIMUS aplicada — por ele, sobre ele.**
2. **Não derrubou lei sem ordem.** Tinha o conserto na mão, viu três testes vermelhos, parou e
   declarou. É exatamente o protocolo.
3. **Matou a dívida do vigia na raiz.** Cinco quedas de bancada num dia, e a causa era `id()`
   reciclado pelo CPython — diagnóstico real, não paliativo.

---

## §5 · A ORDEM

1. **§1** — o degrau 4 da escada.
2. **§2** — a caixa cede; `min == max` vira erro de import.
3. **§3** — as cinco regras novas no `test_os_oito.py`, e a Quinta do Peixe recomposta sob elas.
4. Retomar as dívidas declaradas: o preço sem carimbo da Sexta (2 de 11) e o do Quintou.

**E uma coisa que eu peço ao dono**, porque só ele pode dar: **se existirem peças publicadas dos
outros encartes** — uma Quinta do Peixe, uma Segunda dos Frios que ele tenha impresso —, elas
valem mais que qualquer regra que eu escreva. **Com referência, a régua é a sobreposição; sem
ela, é o teste dos oito.**

---

# RESPOSTA DO BUILDER (06/08/2026)

Os quatro pontos do §5 executados. O resumo em uma frase: **os dois
conflitos morreram, e os dois consertos juntos zeraram o transbordo nos
oito encartes** — a divida de 12 a 40 casos por encarte que estava
declarada no dicionario saiu de la porque nao existe mais.

## §1 — O DEGRAU 4 (a L25 vira preferencia ordenada)

`text_fit.ajustar_texto` passou a fazer a busca DUAS vezes: primeiro com
o vocabulario de marcas protegido (degraus 1–3), depois sem ele (degrau
4). Fica com o resultado que der o **corpo maior**; empate mantem a marca
inteira. Uma consequencia que eu nao previa e que vale registrar: no
piso, a marca tambem cede ao hifen — partir "Itaipa-va" e menos perda que
engolir a palavra na elipse.

**O efeito medido foi maior que o esperado.** O degrau 4 sozinho matou a
maior parte do transbordo dos oito: o nome com marca longa numa coluna
estreita nao cabia em NENHUM corpo (a marca era um atomo indivisivel mais
largo que a caixa), caia na tesoura e o bloco saia mais alto que a
regiao. Com a marca partivel em ultimo caso, ele passa a caber.

Guardiao: `test_undetricesimus_marca_parte_so_para_nao_encolher` — a
mesma marca, o mesmo vocabulario, duas caixas; na larga o hifen nao a
toca, na estreita parte E o corpo tem de ficar maior que o da versao
protegida (se partir a marca nao aumentasse o corpo, nao haveria motivo
para partir).

## §2 — A CAIXA CEDE (L26)

`compositor.crescer_do_piso` roda antes de todo desenho de texto: mede
UMA linha no piso, e se nao couber, cresce a regiao — para baixo (o
sentido da leitura), para cima quando nao ha folga embaixo, e **dividindo
o que falta entre os dois lados** quando nenhum sozinho basta. O
crescimento fica registrado em `base._crescimentos` (I2).

O que cresceu nos oito, medido: **Jornal p1 19 regioes, p2 22, Sabado 10,
Sexta 2** — os outros quatro encartes nao precisaram. Transbordo depois:
**zero em todos**.

Tres coisas que a execucao me obrigou a decidir e que ficam declaradas:

1. **A vizinhanca e a EFETIVA, nao a do layout.** A primeira versao media
   contra os rects da tabela de geometria e acusou colisao no Jornal onde
   o desenho tem folga (a coluna elastica ja tinha movido as caixas). Foi
   a terceira vez nesta dupla de rodadas que o instrumento errado quase
   virou acusacao — conferi antes de reportar.
2. **Encostar nao e invadir.** Nome e descritor do Jornal partilham a
   borda; um fio de ponto flutuante fazia a soma `(y - falta) + (alt +
   falta)` dar 96,84000000000001 contra 96,84 e a caixa "colidia" com a
   vizinha por 0,00000000001 mm. Tolerancia de 0,05 mm (menos de meio
   pixel a 192 dpi).
3. **O erro duro tem escopo.** Onde o piso do celular NAO se aplica (peca
   pequena: o proprio `piso_do_celular` para no 6,0 historico), o layout
   declara os dois lados e nao ha regra a defender — ali quem cede e o
   texto, pela tesoura de sempre. Sem esse escopo, um layout sintetico de
   40 mm derrubava a composicao. **Se o senhor quiser o erro duro tambem
   ali, e uma linha** — mas me pareceu que a lei protege a legibilidade
   no celular, e o celular nao esta em jogo numa etiqueta de gondola.

**E um risco que eu criei e fechei:** com `compor_pagina` levantando
excecao, o dono veria um TRAVAMENTO no meio do exportar, nao um aviso.
Entao a conta virou funcao publica (`plano_de_crescimento`) e o pre-voo a
chama ANTES (`revisora.heuristicas_do_pre_voo` -> `problemas_de_grade`):
a mesma conta do desenho, importada e nao reescrita (a licao da C5/A7).
O dono le a frase; o erro duro e a rede atras dela.

**`min == max`:** `encartes.regioes_de_piso_travado` varre o layout e o
`importar_pacote` RECUSA nomeando a regiao. O pacote tinha 4 casos, todos
o mesmo rotulo de 6 pt da Terca (`_legal` nao declarava minimo e o modelo
usa 6,0 como padrao) — corrigido na origem: `_legal` agora declara
`min(6.0, tam - 0.5)`, o que e byte-identico em todos os outros usos
(so importa quando o texto NAO cabe no teto).

## §3 — O PADRAO DOS SETE

As regras novas entraram na rede: **r9** (duas classes de celula), **r10**
(a zona da foto no destaque), **r11** (a validade fora da celula de
produto), **r12** (o patamar do preco). A quinta — "um peso por item" — ja
era a **r4** desde a rodada passada, e segue verde nos oito.

**O que a r11 achou, e e o achado desta parte:** a validade nao entrava no
Peixe por descuido de layout — entrava por HERANCA do motor. A "Etiqueta"
opcional das duas celulas grandes nasce VAZIA (decisao D2) e o
`texto_composto_legal` tinha um rabo legado: LIVRE vazio cai na validade
da pagina. Nenhuma leitura do layout acharia isso; so medindo o que foi
DESENHADO. Conserto: dentro de celula de produto o recurso morre; fora
dela (o rodape tipico, os layouts antigos) continua valendo — I2.

**Tres regras minhas nasceram tortas e foram corrigidas ANTES de virar
acusacao** (registro por honestidade de bancada):

1. Classificar celula por BORDA dizia que 5 das 7 celulas do Peixe estavam
   "fora do padrao" — a caixa do nome encosta ~2 mm na foto em todos os
   encartes aprovados. Passei a classificar pelos CENTROS.
2. Cobrar "foto >= 85% da largura da celula" na grade briga com a margem
   de 3 mm da P2 (que e lei vigente): o maximo possivel no Jornal e 84%.
   A regra virou o que o §3 realmente pede — a zona do DESTAQUE.
3. "Destaque" pela classe (foto ao lado) marcava as 4 chamadas do Jornal
   e os 9 patches da Sexta, que sao MIUDOS. Destaque e a celula GRANDE,
   relativa a pagina (a mesma lei do heroi, L21).

**Uma parte do §3 eu NAO executei, e explico:** a foto do destaque
"sempre a direita". Os oito medidos mostram o Jornal (4 chamadas), a
Sexta (9 patches) e a Quarta (1 livre) com a foto a ESQUERDA — arranjos
que o dono ja viu e aprovou em varias rodadas. Trocar o lado deles e
redesenhar tres encartes, e isso e decisao dele, nao regua minha (L7). O
que a rede garante hoje e a COERENCIA: nenhuma pagina mistura os dois
lados. **Se o senhor mandar o lado canonico, e um paragrafo em cada
gerador.**

**A Quinta do Peixe recomposta:** a zona da foto das duas celulas grandes
passou de 283 para 323 px de largura (51% -> 57% da celula) e a coluna de
texto cedeu os 40 px. A Sexta (bancas: 53% -> 55%, a zona desceu 8 px sem
tocar o toldo) e a Quarta (livre-5: 54% -> 56%) entraram junto, porque a
regra vale nos oito ou nao vale (L22).

## §5.4 — AS DIVIDAS

**A da Sexta ("2 de 11 precos sem carimbo") era FALSO POSITIVO da minha
propria regua.** Fui olhar a arte: o oval coral das bancas esta GRAVADO
no BASE do dono — o app desenha so o numero em cima. A pagina nunca teve
defeito; o layout e que nao declarava o que a arte ja fazia. Agora
declara (`Regiao.carimbo_na_arte`, com roundtrip guardado — a licao do
incidente da QUINTUS, em que dois flags novos morreram no reimport).
**O dicionario `DIVIDA` do teste dos oito esta VAZIO.**

**A do Quintou:** medida, esta coerente — todas as 15 regioes de preco da
frente e as 16 do verso desenham dentro do carimbo do template. O "preco
sem carimbo" do §4 da ordem passada era da pagina composta pelo projeto
antigo do dono, nao do layout atual.

## Incidente de bancada (o mais importante desta rodada)

**A propria prova visual achou uma regressao MINHA, de duas ordens
atras.** Ao recompor a Quinta do Peixe para conferir o §3, o selo saiu
`30/0730/07` — a data duas vezes dentro do carimbo. Causa: a regra que eu
escrevi na QUINTUS/L23 ("o texto_fixo vira PREFIXO da data", para o "Ate
26/05" do Quintou) concatena sem perguntar o que ha no texto fixo; quando
o fixo JA E uma data — um projeto antigo, ou o dono digitando no campo —
a data sai duplicada. Conserto: prefixo e palavra, nunca data (guarda por
regex), com guardiao proprio.

Registro isso com todas as letras porque e a prova de que **compor e
OLHAR** vale mais que qualquer suite: 1259 testes verdes nao viram esse
defeito, e ele estava saindo impresso no selo desde 05/08.

## Bancada

* suite **1259 x2**, zero skips, exit 0, placar por junit
  (`saida_f13/bloco_ut_run1.xml`, `run2.xml`);
* **ordem invertida** limpa (`bloco_ut_inv.xml`);
* **janela real** 4 (`bloco_ut_janela.xml`);
* guardioes novos em `app/tests/test_undetricesimus.py` (9): degrau 4,
  caixa que cresce + declara, grade apertada nomeada, pre-voo antes do
  erro, `min == max` no import, validade fora da celula, selo sem data
  dupla, carimbo na arte + roundtrip, o oval da Sexta declarado;
* rede dos oito: 12 regras x 8 encartes, `DIVIDA` vazia;
* galeria recomposta do banco em `saida_f13/galeria_f13_bis/`.

## O que ficou de fora (nomeado)

* **o lado canonico da foto no destaque** (redesenho do Jornal/Sexta/
  Quarta) — decisao do dono;
* **o erro duro em peca pequena** (hoje escopado ao piso do celular) —
  decisao do arquiteto, uma linha;
* as regioes ROTACIONADAS nao entram no registro `_texto_desenhado` (o
  desenho girado acontece numa tela auxiliar): as regras da rede que
  medem texto desenhado nao veem selos girados. Nomeado, nao consertado;
* **observacao da prova visual (fora do escopo desta ordem):** nas duas
  bancas da Sexta a ZONA agora esta generosa, mas a TINTA nao a enche —
  a granola e o azeite ficam pequenos no painel verde escuro. A zona e
  o que esta ordem mede; quanto o produto enche dela e lei do Q1/leque
  (QUARTUSDECIMUS/L19), e ali a banca nao dispara. Se o senhor mandar,
  entra na proxima rodada;
* as pendencias antigas do dono: marca-no-nome (5a vez), H3-contagem, K2,
  curadoria de fotos (halos), correcao-que-avisa, legais nas duas
  paginas, abreviacoes na Config;
* **e o pedido do §3 ao dono:** se existir uma peca publicada da Quinta do
  Peixe, da Segunda ou de qualquer outro, ela vale mais que estas regras —
  com referencia, a regua e a sobreposicao.
