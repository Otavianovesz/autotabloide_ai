# ORDEM F13-TRICESIMUS-PRIMUS - O NOME E CENTRADO (3a errata) E A SEXTA VERDE

(A ordem do arquiteto de 05/08/2026, transcrita pelo builder: a 3a errata do alinhamento, medida em 40 linhas do publicado, mais a auditoria da Sexta Verde e os 24 cronicos.)

---

# RESPOSTA DO BUILDER (06/08/2026)

## Parte I — o alinhamento, com a MINHA medicao ao lado da sua

Antes de mexer eu medi, porque a lei nova (L29) vale para os dois lados
da dupla. A faixa de nome do Quintou, na escala 1080:

```
x = 10 .. 144      CENTRO = 77,0     (as 15 celulas, identicas)
```

O senhor mediu 74,5–77,0 nas 40 linhas do publicado. **A caixa ja estava
certa; era so o alinhamento.** Trocado para CENTRO.

**O alvo de corpo virou DADO DECLARADO, nao razao derivada:**
`Regiao.alvo_caixa_alta_px = 12.0` no nome do Quintou (a medida da peca,
na escala 1080), e o compositor converte pela metrica REAL da fonte. A
banda 2,4–2,9 ficou como guarda-corpo, exatamente como o senhor pediu.

**Medido depois:** onde o nome cabe, a caixa alta sai em 12 px — o
numero do senhor. Onde nao cabe (nome mais longo que a caixa comporta),
a banda cede para o nome nao ser CORTADO: e a precedencia que ja estava
declarada na rodada passada, e o contador `_banda_cedeu` continua
nomeando as celulas.

## §1 — a contagem tabela x pagina (a guarda dos cronicos 1, 2 e 6)

`servico.itens_fora_da_pagina(itens, mapa)` conta e NOMEIA:

> "a tabela tem 12 itens e a pagina tem 11 — ficaram de fora: 'Mamao
> Formosa'"

Ligada nas DUAS portas da Mesa (salvar e exportar). Item RISCADO nao
conta como falta — esse ja tem aviso proprio. **Esta e a guarda que
pegaria o Mamao, o Bife riscado e a Toscana perdida.**

## §2 — o LOTE saiu

Saiu do GERADOR (`gen_verde5.py`) e das tres artes (BASE/MASTER/curvas),
e o BASE.png foi regerado pelo pipeline. Tirar so do SVG teria durado
ate a proxima regeracao — o guardiao cobre os dois.

## §3 / cronico 5 — a variante usa OU

`nome_fit.sem_conector_orfao`, aplicada a TODA celula no compositor
(venha o par da cadeia ou direto do item):

```
Tomate Salada / e Italiano  ->  Tomate / Salada ou Italiano
Maca Fuji     / e Gala      ->  Maca   / Fuji ou Gala
Mexerica      / e Murcot    ->  Mexerica / ou Murcot
Granola / "banana e canela · 250 g"  ->  intacto (o "e" do meio e frase)
```

A primeira variante DESCE do nome — e ela que perdeu o par — e nada se
apaga (lei do dono).

## O que NAO fiz nesta rodada, e por que

* **§4.5 (o carimbo transborda a celula da Sexta)** e os itens de
  composicao do §4 (dois estilos de preco, verde vazio, toldo, cantos):
  sao calibracao de ARTE da Sexta e cada um mexe na geometria de um
  encarte inteiro. Preferi entregar os TRES de conteudo fechados a
  entregar cinco pela metade.
* **Os cronicos 7, 8, 10 e 17** (acento, sigla crua, numero da linha,
  caixa da unidade): o 10 ja esta feito desde a DUODETRICESIMUS §3; os
  outros tres sao vocabulario e cabem numa rodada so, como o senhor
  escreveu — **e um deles eu quero mostrar antes de consertar**: na
  galeria de hoje sai "Bebela 8 4G" (o peso "84g" partido por um espaco
  no meio do numero). Nao e caixa: e um defeito NOVO que a sua auditoria
  me fez ver, e ele vale mais que os tres juntos.

## Bancada

suite x2 + invertida + janela real, zero skips, placar por junit
(`saida_f13/bloco_trip_*`); guardioes novos: o nome centrado + o alvo
medido sobrevivendo ao banco, a contagem tabela x pagina, a variante com
OU, e o LOTE ausente do gerador E das artes.
