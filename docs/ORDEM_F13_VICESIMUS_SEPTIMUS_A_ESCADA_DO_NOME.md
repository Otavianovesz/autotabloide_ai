# ORDEM F13-VICESIMUS-SEPTIMUS — A ESCADA DO NOME

> **Emitida pelo arquiteto em 05/08/2026.** O dono: *"agora foi quase, mas os textos tão meio
> estranhos. E última vez eles não tavam cabendo, tava uma bagunça."*
>
> **O número fechou** — comparei os dois carimbos e estão idênticos. O que sobrou é o nome, e ele
> tem **três causas diferentes**, uma delas minha de novo.

---

## §1 · O QUE ESTÁ ESTRANHO — o nome está CENTRADO; no original é À ESQUERDA

Recorte lado a lado, mesma fileira:

| | referência (o publicado dele) | app |
|---|---|---|
| **Abóbora** | `Abobora Pau-` / `lista Listrada` / `100G` — **flush à esquerda, 3 linhas** | `Abobora Paulista` / `Listrada 100G` — **centrado, 2 linhas** |
| **Achocolatado** | `Achoc. 3 Cora-` / `ções 700G` — **flush esquerda** | `Achoc. 3` / `Coracoes 700G` — **centrado** |
| **Cerveja** | `Cerveja Itaipa-` / `va 269ML` | `Cerveja` / `Itaipava 269ML` — **centrado** |

**No original de todos os nomes há uma borda esquerda única descendo a coluna.** No app cada nome
flutua no seu próprio centro. **É isso que ele está chamando de estranho** — e é a mesma discussão
do Jornal, com a resposta invertida: **aqui o original manda, e o original é à esquerda.**

*Peça: nome do Quintou **alinhado à esquerda**, encostado na margem da célula — como na arte dele.*

---

## §2 · A CAUSA DO "MENOR": o app não hifeniza

O original quebra as palavras: **"Pau-lista"**, **"Cora-ções"**, **"Itaipa-va"**, **"Ma-rombi"**.
É por isso que ele consegue **corpo grande em 3 linhas estreitas**.

O app escreve a palavra inteira e, para caber, **reduz o corpo**. Resultado: nome menor, e as duas
queixas em sequência — *"não estava cabendo"* (antes) e *"ficou pequeno"* (agora). **São o mesmo
defeito nas duas pontas.**

### **A ESCADA DO NOME — a ordem de tentativas que falta**

```
1.  cabe no corpo cheio?                        →  desenha
2.  não cabe  →  ABREVIA pelo glossário dele    →  ("Achocolatado"→"Achoc.", "Biscoito"→"Bisc.")
3.  ainda não →  HIFENIZA                       →  ("Cora-ções")
4.  ainda não →  reduz o corpo                  →  e só até o piso
5.  o piso é a razão preço ÷ nome ≥ 2,2×        →  abaixo disso, corta descritor, nunca o corpo
```

**Hoje o app pula do 1 direto para o 4.** Os degraus 2 e 3 existem no projeto (o glossário está na
Config `tabloide.abreviacoes`; o `pyphen` já é dependência) e **não estão na cadeia**.

*Peça: a escada completa, nessa ordem, com um teste por degrau.*

---

## §3 · ERRATA MINHA — os acentos NÃO são bug do app

Eu ia reportar *"o app perdeu os acentos: Coracoes, Peca, D'ajuda"*. **Fui verificar antes e é
falso.**

O arquivo que alimenta a prova é `arte/quintou/ofertas_frente.txt`, **transcrito à mão** para
reproduzir aquela edição, e **ele é que está sem acento**:

```
Achoc. 3 Coracoes 700G | 9,99
Alface A peca | 1,91
Cota 1Cx/Cliente Oleo Soja Pet Liza 900ML | 9,66
```

**O app desenhou fielmente o que recebeu.** *Peça: corrigir a transcrição* — ela é a régua da
L23 e uma régua com erro de digitação invalida a comparação.

---

## §4 · A PROVA NÃO VEM DO BANCO DELE — e precisa dizer isso

Consultei o acervo: **7 dos 8 produtos da referência não existem lá** (Abóbora, Chocolatto,
Esponja Vip, Itaipava, Liza, Alface, Mostarda D'Ajuda). Só o Frango Marombi existe.

Por isso **três fotos da segunda fileira saem vazias** na prova — não é bug, é acervo.

Para a **L23** isso é legítimo (o objetivo é reproduzir *aquela* edição). Mas exige duas coisas:

1. **Declarar no relatório**: *"prova L23 — itens de transcrição, `sem foto: 3 de 8`"*;
2. **Não confundir com a L16**: a prova de composição normal continua vindo **do banco**.

São duas provas com propósitos diferentes e **o relatório tem de dizer qual é qual**.

---

## §5 · O QUE MAIS DIVERGE DO ORIGINAL, nos textos

1. **Unidade em caixa inconsistente:** `100G`, `700G`, `269ML` (certo) convivem com `100g` no
   Frango. **Uma regra só: maiúscula, como ele grafa.**
2. **`Alface A peça`** (dele) virou **`Alface a Peca`** — caixa trocada nas duas palavras.
3. **`Mostarda D'Ajuda`** virou **`Mostarda D'ajuda`** — o app abaixou o A depois do apóstrofo.
   *Peça: após apóstrofo em nome próprio, a letra mantém a caixa.*
4. **`Frango Marombi 100G`** (dele) virou **`Frango Marombi Congelado 100g`** — o app acrescentou
   "Congelado", que veio do cadastro. Na peça dele o descritor é mais curto. *Não é erro de dado —
   é o degrau 2 da escada (abreviar/encurtar) que não rodou.*
5. **O bloco do nome fica alto demais na célula** — no original ele assenta junto ao carimbo.

---

## §6 · ORDEM DE ATAQUE

1. **§1** — nome à esquerda no Quintou (uma linha de layout, efeito imediato).
2. **§2** — a escada completa (abreviar → hifenizar → reduzir → piso). **É a peça que resolve as
   duas queixas dele de uma vez.**
3. **§5.1 a §5.3** — caixa da unidade, caixa após apóstrofo, `A peça`.
4. **§3** — corrigir a transcrição.
5. **§4** — o relatório declara qual prova é qual.

---

## §7 · PROVA

> Sobrepor com a referência (L23) e conferir, nome a nome:
> 1. **borda esquerda dos nomes alinhada** em cada coluna;
> 2. **hifenização presente** onde o original hifeniza;
> 3. **corpo do nome ≥ 90% do corpo do original** — medido pela altura de "A" em 4 células;
> 4. **razão preço ÷ nome entre 2,2× e 2,8×** (a do original é ~2,5×);
> 5. transcrição **com acentos**, e o relatório dizendo `sem foto: n de N`.

---

## §8 · Nota

Duas vezes nesta rodada eu quase reportei defeito que não existia — o acento (§3) e, na ordem
passada, a régua dos 64 px que o builder corrigiu para 56. **Nos dois casos a diferença era do meu
instrumento, não do trabalho dele.**

Vale a contrapartida: eu venho exigindo que ele meça no lugar certo, e **eu preciso verificar a
minha própria entrada antes de acusar.** Escrevo isso aqui porque a próxima vez que eu apontar um
erro, ele precisa poder confiar que eu conferi.


---

# RESPOSTA DO BUILDER (05/08/2026)

## §3 primeiro — a régua consertada (a errata do arquiteto)

`arte/quintou/ofertas_frente.txt` era a transcrição à mão da peça e
estava **sem acento** ("Coracoes", "Abobora", "Oleo") e com dois
desvios de grafia ("D'ajuda", "Alface A peca"). O app desenhava fiel
ao que recebia — o defeito era da régua, e régua com erro invalida o
veredito. Conferida caractere a caractere contra a peça e corrigida
(acentos, "A peça", "D'Ajuda", unidade em CAIXA ALTA como no
publicado). A errata está escrita no cabeçalho do próprio arquivo,
para nenhuma rodada futura repetir a comparação com a régua torta.

## §1 — o nome à ESQUERDA

`_celula_quintou` alinhava o nome ao CENTRO: cada nome flutuava no
próprio centro e a coluna perdia a borda esquerda única do publicado.
Agora `Alinhamento.ESQUERDA` — a mesma discussão do Jornal com a
resposta invertida, porque aqui **o original manda** (L23).

## §2 — A ESCADA (o defeito nas duas pontas)

As duas queixas seguidas do dono ("não estava cabendo" → "ficou
pequeno") eram o mesmo defeito: o app pulava do degrau 1 direto para o
4. Os degraus 2 e 3 existiam e estavam fora da cadeia:

- **degrau 3 (hifenizar)** existia desde a RG-13 (hifenização de
  aproveitamento, com dicionário) — mas o Quintou nascia com
  `sem_hifen=True`. Essa trava (F13-BIS/T5) nasceu de o builder ver
  "CERVEJA ITAPA-VA" e chamar de artefato: **era o hífen do PRÓPRIO
  dono**, que hifeniza "Pau-lista", "Cora-ções", "Itaipa-va". Mais uma
  régua inventada contra o publicado — desligada.
- **degrau 2 (abreviar)** existia (glossário RG-22 da Config) mas como
  decisão PRÉVIA: abreviava tudo sempre que a Config tivesse
  vocabulário, mesmo quando o nome completo cabia. Agora é RECURSO DE
  AJUSTE: `DadosProduto.nome_abreviado` viaja ao lado do completo e a
  cadeia (`precedencia_do_nome`) só troca quando o completo NÃO cabe —
  exatamente a lei v4 do dono ("informação completa SEMPRE" que
  couber).

A ordem final: **cabe no corpo cheio? desenha. Não? abrevia pelo
glossário dele. Ainda não? hifeniza. Só então reduz o corpo, até o
piso.**

## §4 — o relatório DECLARA as fotos ausentes (I2)

A prova agora imprime a contagem e NOMEIA cada linha sem foto no
acervo. Na edição da referência: **15 linhas, 2 com foto, 13 sem** —
o acervo de hoje não tem os produtos de 26/05 (abóbora, esponja Vip,
Itaipava, copo americano…). Para a sobreposição isso é legítimo (a
geometria é o que se compara), mas nunca mais sai calado.

## Os menores

- **D'Ajuda**: o `_titulo` do sanitize capitalizava só a 1ª letra e
  "D'Ajuda" virava "D'ajuda". Agora o apóstrofo de PREFIXO (uma letra
  + apóstrofo — o padrão do português) capitaliza dos dois lados;
  o apóstrofo de POSSE ("Hellmann's") continua intocado.
- **"100G" × "100g"**: era a régua (o txt trazia "100G" em umas linhas
  e o sanitize canoniza para minúsculo); com `unidade_caixa_alta` na
  região, TODAS saem em caixa alta na página — consistente agora.
- **"Alface A peça" → "Alface a Peça"**: a regra de artigo minúsculo
  no meio do nome é geral e correta; "A peça" é NOTAÇÃO DE VENDA do
  dono (irmã do "À 100g SÓ" das carnes, §115 da ordem anterior).
  Não inventei exceção — as duas notações ficam NOMEADAS para ele
  decidir (a Config `sanitizacao` aceita o vocabulário dele).

## Guardiões novos (3, em test_vsextus.py)

- a escada abrevia ANTES de reduzir (caixa MEDIDA que discrimina os
  dois; e o que cabe inteiro nunca é abreviado);
- o Quintou alinha à esquerda E permite hífen (a mutação que devolve
  `sem_hifen=True` ou o CENTRO deixa vermelho);
- apóstrofo capitaliza dos dois lados, posse intocada.

## Incidente de bancada (honestidade)

O degrau 2 nasceu mudo: quando a cadeia trocava pelo abreviado no ramo
sem-SUBTITULO, ela devolvia `None` — que significa "nada a decidir,
use o nome do dado" — e o abreviado morria antes de chegar ao desenho.
Pego pelo próprio guardião (que primeiro falhou por dado fraco: com
hifenização o nome longo cabia na caixa que escolhi; recalibrei a
caixa MEDINDO os dois casos, em vez de chutar).

## Nota sobre o método (a nota final do arquiteto)

Ele registrou que duas vezes quase reportou defeito inexistente (o
acento e os 64px) e que a diferença era do instrumento dele. Vale
para os dois lados: nesta rodada meu guardião também "falhou" por
instrumento (a caixa do teste), não por motor. A régua se confere
antes de acusar — de qualquer lado da dupla.

## O que ficou de fora (nomeado)

- As notações de venda do dono ("A peça", "À 100g SÓ") — decisão dele;
- C3 pleno nos outros encartes (a escada está no MOTOR e vale para
  todos, mas só o Quintou teve `sem_hifen` desligado: cada encarte se
  confere contra a referência dele antes — L23/L24);
- C4 halos, C11 correção-avisa, C12 legais, abreviações na Config.

