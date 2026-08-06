# ORDEM F13-VICESIMUS-SEPTIMUS - O NOME A ESQUERDA E A ESCADA

(Os tres achados do arquiteto sobre os TEXTOS, apos o numero fechar:
o nome centrado x a esquerda; a escada que falta - abrevia, hifeniza,
so entao reduz; e a ERRATA dele mesmo: a regua da prova estava sem
acento e o app desenhava fiel. Mais a declaracao das fotos ausentes.)

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

