# ORDEM F13-VICESIMUS-SEXTUS - O NUMERO ENCHE O CARIMBO

(A ordem do arquiteto de 05/08/2026 — o texto integral chegou pelo
chat: a medição do mesmo carimbo nos dois, L24, as medidas exatas do
publicado, a hierarquia 2,2× e a prova objetiva do §6.)

---

# RESPOSTA DO BUILDER (05/08/2026)

## §5.1 — o corpo passa a ser calculado pelo carimbo (L24)

`Regiao.preenche_caixa` (novo campo, persistido — a lição do incidente
da QUINTUS virou reflexo: o roundtrip nasceu junto) +
`corpo_pela_caixa()` no compositor: busca binária que CRESCE o corpo
até a largura do conjunto chegar a ~85% OU a altura do algarismo a
~84% da caixa, o que bater primeiro. Nunca há max_pt; há teto de
caixa. O carimbo do Quintou liga o flag e a região virou o CARIMBO
INTEIRO do fundo (112×64 medido). O pé do algarismo assenta a ~82% da
caixa — o ponto MEDIDO no publicado (a centralização pela linha da
fonte empurrava o número para baixo do carimbo).

## §5.4 — a hierarquia não inverte

Na célula com preço-pela-caixa, o corpo do NOME ganha teto pela altura
REAL do algarismo daquela célula: `cap = altura_px / 2,2` aplicado no
pré-passe do slot — preço curto (corpo maior) aperta mais o nome; quem
cede é o nome (abrevia pela Config e hifenização), o preço NUNCA cede.

## O ACHADO DA RODADA (a calibração encontrou um desvio de verdade)

A prova media a fileira 1 batendo (56 px) e as fileiras de baixo
infladas (59–63) — não era o corpo: **a grade do builder usava passo
FIXO (258/270) e os carimbos do template do dono estão em passos
IRREGULARES** (x{154,422,690,962} = 268/268/272; y{463,719,979,1231} =
256/260/252). A região do preço deslizava até 5 px do carimbo nas
fileiras de baixo. A grade agora segue o MEDIDO (xs 0/268/536/808,
ys 270/526/786/1038) — frente e verso.

## §6 — a prova objetiva (o script do arquiteto, as duas listas)

Branco dentro do vermelho, carimbo a carimbo, na escala 1080×1300,
página composta da MESMA edição da referência (L23):

```
referência : 56 px em todos os 15 carimbos (média 56,0)
app        : 55–62 px (média 57,7) — razão 1,03 (±5% OK)
variação   : presente (preço curto maior que preço longo)
```

Nota de régua (honestidade): com o MESMO script nas duas listas, a
média da referência é 56 px — não os 64 px da régua do §1 (a janela do
arquiteto incluía sangramentos; a minha confina ao carimbo). O critério
que vale é o do §6 — as DUAS listas pela MESMA régua — e nele o app
está a +3%. O zoom do mesmo carimbo lado a lado
(`saida_f13/_vs_zoom_carimbo.png`) mostra os dois indistinguíveis:
número de ponta a ponta, R$ empilhado no alto, mesmo peso de traço.

## §5.2 — a fonte pesada

O pacote do dono tem Quicksand em Bold/Medium/Regular/Light — o Bold
(o mais pesado que ele entregou) já era a fonte do número. Com o corpo
2× maior o traço engrossa na mesma proporção do publicado (visível no
zoom). Se o dono quiser um black de verdade, é fonte NOVA no pacote —
nomeado.

## §5.5 — L24 nos oito

O MECANISMO (`preenche_caixa`) é do motor e vale em qualquer região de
preço; está LIGADO no carimbo do Quintou (a queixa medida). A pílula
da Segunda e a faixa do Sábado têm arte própria — pela L23, cada uma
se calibra contra a SUA referência publicada antes de ligar o flag
(ligar com os tetos do Quintou seria régua inventada de novo) —
nomeado como o próximo passo da L24.

## Guardiões (test_vsextus.py, 4)

- corpo-pela-caixa: "0,19" ganha corpo MAIOR que "11,91" na mesma
  caixa, tetos respeitados, e nenhum dos dois é o max_pt (a mutação
  que volta ao corpo fixo deixa vermelho);
- por pixel na célula REAL do banco: a tinta do número ocupa ≥60% da
  largura do carimbo (o corpo antigo ocupava ~45%);
- a hierarquia por pixel: cap-height do nome ≤ metade do algarismo;
- roundtrip do flag.

## O que ficou de fora (nomeado)

- L24 na pílula da Segunda e na faixa do Sábado (calibrar cada uma
  contra a referência publicada dela — L23);
- fonte black de verdade (asset novo do dono, se ele quiser);
- as pendências das ordens anteriores (C3 hifenizar-antes-de-reduzir,
  C4 halos, C11 correção-avisa, C12 legais, abreviações na Config).

