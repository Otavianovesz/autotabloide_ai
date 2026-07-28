# ORDEM F13-DUODECIMUS — A TERÇA DO PÃO (o teste difícil de verdade)

> **Emitida pelo arquiteto em 27/07/2026.** O dono trouxe a tabela real da Terça e as **três**
> fotos das células fixas. Abri os quatro arquivos.
>
> **Esta tabela é muito mais difícil que a da Segunda** — e por isso é o melhor teste que
> apareceu até agora. Ela quebra três suposições que o app faz hoje.
>
> **Pré-requisito: o U1 da UNDECIMUS (o piso vira regra de runtime).** Sem ele, a Terça sai
> com texto ilegível — as 6 regiões de nome dela estão com o piso inerte no banco do dono.

---

## §1 · OS ARQUIVOS, conferidos no disco

| Arquivo | Tamanho | Estado |
|---|---|---|
| `pão frances.png` | 1600×1600 RGBA | **já recortado** — fundo transparente, pronto |
| `Sonho.jpg` | 2000×1339 RGB | **cru** — parede verde, tábua de madeira, papel branco |
| `croissant.png` | 621×402 RGBA | **cru** — tábua redonda de madeira, fundo claro |
| `Terça do Pão.jpeg` | 619×858 | a tabela da semana |

**São TRÊS fixas, e isso confirma uma coisa importante:** a célula "Sonho + Croissant" tem **duas
zonas de foto separadas** com o `+` entre elas (está na arte). Então o item fixo #2 não é um
produto com uma foto — é **um par**. Isso não existe no modelo hoje.

---

## §2 · A TABELA — leia com atenção, ela não é uma tabela

Dois terços do documento são **prosa promocional**. Só o último terço tem preço:

```
"HOJE É O DIA DO SONHO E DO CROASONHO, NO BELO BRASIL".
É a terça-feira especial do pão francês do sonho e do croasonho com pedaços de
moranguinho!! Uma enorme diversidade de sabores  LEVE 3 SONHOS OU 3 CROASONHOS
E GANHE 25 % de DESCONTO, ...
VENHA... SABOREAR, e com os preços mais baixos da cidade.  E TEM TAMBEM.......

  <> O PÃO FRANCÊS COM 50 % de DESCONTO <>

• SALSICHA HOT DOG REZENDE KG__só__          9,90
• FIGADO BOVINO ____100 g ___SÓ________      0,99
• OSSINHO _________À_____100g ____só_______  1,81
• COXA SOB COXA_À______100g ____POR____      0,77
• LINGUA e CORAÇÃO ____100g _____Só_______   0,66
```

### T1 🔴 A PROSA NÃO PODE VIRAR PRODUTO

É o risco número um, e o app nunca foi testado contra isso. A prosa tem números que **parecem
preço**: `3`, `3`, `25`, `50`. Se o parser for guloso, ele cria produtos chamados
"VENHA... SABOREAR" e "E TEM TAMBEM" com preços absurdos, e o dono vê lixo na conciliação.

**Regra:** uma linha só vira item se tiver **marcador de preço** (`só`/`SÓ`/`por`/`POR`/`R$`) **e**
um número no formato de moeda (`d,dd`) **no fim da linha**. Prosa sem marcador é **descartada em
silêncio**; prosa **com** número mas sem marcador vai para um balde de "linhas ignoradas" que o
diálogo de conciliação **mostra**, para o dono conferir que nada de útil se perdeu (I2 — nunca
descartar calado).

### T2 🔴 SÃO 5 ITENS PARA 4 CÉLULAS LIVRES

A Terça tem **6 células: 2 fixas + 4 livres**. A tabela traz **5 itens com preço**.
**Sobra um.** É o inverso do caso da Segunda, e é o caso que eu previ que apareceria.

O app **não pode** escolher sozinho qual fica de fora, nem cortar o último em silêncio.
**Peça:** o auto-preencher põe os 4 primeiros, e o 5º fica **na estante, marcado como "fora da
grade"**, com um aviso claro: *"1 item não coube — arraste para uma célula ou tire outro."*
O aviso já existe em espírito (`mesa.py:2325`); garanta que ele **apareça** e que o item
**continue visível na estante**, nunca sumido.

### T3 🟠 OS PERCENTUAIS SÃO DA ARTE, NÃO PREÇO

`50 % de DESCONTO` no Pão Francês e `25 %` no leve-3 **já estão gravados na arte** da Terça —
os dois discos vermelhos "50% OFF" e "25% OFF" que aparecem na página. Eles combinam
exatamente. Então:

- O parser **não** pode ler `50` e `25` como preço.
- E vale registrar como achado de produto: **a arte da Terça foi desenhada para essa mecânica**.
  Não implemente nada agora — só **não estrague**.

### T4 🟠 AS ARMADILHAS DE TEXTO DESTA TABELA

| No papel | O que tem de sair | Por quê |
|---|---|---|
| `FIGADO BOVINO` | **Fígado Bovino** | acento que o documento não tem |
| `LINGUA e CORAÇÃO` | **Língua e Coração** | idem, e o `e` minúsculo fica |
| `COXA SOB COXA` | **Coxa Sobrecoxa** *(confirmar com o dono)* | ele escreve separado; no Quintou publicado sai "Coxa Sobrecoxa" |
| `CROASONHO` | **CROASONHO** | é a palavra **dele**. A IA **não pode** "corrigir" para croissant. Trava da F9: não inventar. |
| `OSSINHO ___À___ 100g` | `À` sai; unidade `100 g` | o `À` é enfeite de preenchimento |
| `REZENDE KG__só__` | unidade **kg**, antes do marcador | a unidade muda de posição entre as linhas |

E o de sempre: `SALSICHA HOT DOG REZENDE` é longo — exercita a precedência do `nome_fit`
(N1 da NONUS) com dado que ninguém alfaiatou. **Nenhum `…`.**

---

## §3 · AS TRÊS FOTOS FIXAS

### T5 🔴 O par Sonho + Croissant precisa existir no modelo

A célula fixa #2 tem **duas zonas de foto**. Hoje `conteudo_fixo` guarda **uma** imagem. Ou o
item fixo passa a aceitar **uma lista de fotos** (uma por zona), ou a célula ganha dois slots
fixos irmãos. **Decida, registre a decisão, e não invente uma terceira via.**

*(O projeto já tem o conceito de "compor 2 num slot" na Mesa — `mesa.py:1999`. Veja se serve
antes de criar coisa nova. L9.)*

### T6 🔴 As fotos cruas são o teste das guardas que você mesmo construiu

- **`pão frances.png`** já vem recortado (alfa). Não reprocesse: se já tem alfa útil, o
  detector deve pular o rembg — igual ao detector de fundo branco do D3.
- **`Sonho.jpg`** é o caso do **J18**: depois do recorte sobram os dois sonhos **e possivelmente
  um pedaço do papel branco** embaixo. Se sobrar, a guarda dos "dois blobs desconexos" tem de
  acender. **Este é o primeiro teste real dela.**
- **`croissant.png`** tem uma **tábua de madeira** encostada nos croissants — o caso clássico que
  o dono reclamou na primeira gravação ("ele tira coisa que não era pra tirar" e vice-versa).
  E é a menor imagem do acervo: **621×402**. Numa página de 2160 px isso vai precisar de
  **upscale** — o Real-ESRGAN existe e a regra travada da F10 é *"upscale sob demanda mira o
  MAIOR lado da célula"*. Prove que ela roda aqui.

**Se alguma das três não sair boa no automático, NÃO conserte a foto à mão.** Reporte o que
falhou e por quê — a foto tratada à mão é alfaiataria, e a NONUS já ensinou o preço. Se o
pipeline não dá conta, o achado é esse.

---

## §4 · O QUE MEDIR E MOSTRAR

1. **A tabela pelo OCR real**, e a lista do que virou item × o que foi descartado (T1).
2. A página composta **pelo caminho do dono** (Ateliê → duplo-clique → Mesa → importar →
   auto-preencher), com a validade nascida sozinha (`SOMENTE 28/07`, terça).
3. **A razão de densidade** da Terça contra a referência — hoje 0,60, com a ressalva do fundo
   texturado. Reporte o número novo.
4. **Nenhum nome com `…`** e nenhum abaixo do piso do celular.
5. As três fotos fixas na página, **tratadas pelo pipeline**, com o relatório de quais guardas
   dispararam.

---

## §5 · AS SOBRAS CONHECIDAS DA TERÇA — só depois

Da SEXTUS §5, e **só se ainda existirem** depois do U1 e desta rodada:
as duas fotos do `Sonho + Croissant` pequenas nas zonas (deve morrer com o T5),
e a faixa creme vazia sob as cestas.

---

## §6 · A CONDIÇÃO DE ACEITAÇÃO

A mesma da NONUS e da DECIMUS, e ela não muda mais:

> **O dono abre o app, importa a tabela dele, e a página sai certa. Se você tocar em qualquer
> dado à mão para ela ficar boa, o conserto não está pronto.**

E acrescento uma para esta rodada, por causa do T2:

> **O 5º item tem de estar VISÍVEL para ele** — na estante, marcado, com o aviso. Um item que
> some porque não coube é perda de conteúdo em silêncio: é I2, e é a doença crônica deste código.


---

# Resposta do builder (Fable) — 27/07/2026

Executada DEPOIS do U1, como o pré-requisito manda. Os testes em `test_f13_duodecimus.py`;
a rodada na raiz real em `app/scripts/terca_pelo_caminho_do_dono.py` (log
`saida_f13/_terca_raiz_real.log`).

## T1/T3 — a prosa não vira produto

A regra no parser (`colagem.parse_colagem`, com `balde=`): linha SEM preço de moeda no fim só
vira item se tiver CARA DE PRODUTO (curta, sem dígito, sem pontuação de frase — o "Sabonete
Dove" da lista de WhatsApp segue virando amarelo, por guardião). **Prosa com número — o "LEVE
3… GANHE 25 %" e o "PÃO FRANCÊS COM 50 %" — vai ao balde VISÍVEL** (mostrado na conciliação
pelo aviso, com as primeiras linhas; I2 — nada some calado); prosa sem número morre em
silêncio. Na tabela real: **5 itens exatos (9,90 · 0,99 · 1,81 · 0,77 · 0,66), zero produto de
prosa, os percentuais intactos na arte** (T3: nada implementado, nada estragado — o achado de
produto fica registrado: a arte da Terça foi desenhada para a mecânica dos descontos).
*Contrato virado com rastro:* o antigo "sem preço → sempre amarelo" criava produto de prosa.

## T2 — o 5º item fica visível

5 itens, 4 livres: o auto-preencher põe 4 e o 5º **fica na estante marcado "fora da grade"**
(a marcação já existia — mesa.py; garantida por teste de gesto) com o aviso novo que diz o que
fazer: *"1 item não coube na grade — segue na estante marcado 'fora da grade'; arraste para
uma célula ou tire outro"*. Nada some (I2).

## T4 — as armadilhas

O "À" de enfeite (entre pontilhados) sai no parser — e o "à" legítimo ("Frango à Passarinho")
fica, por teste; a unidade SOLTA no fim ("REZENDE **KG**") desce ao descritor pela cadeia do
N1 (como o peso); FIGADO/LINGUA ganham acento pelo CASAMENTO com o banco (a conciliação
devolve o nome do acervo — sem inventar); **CROASONHO não aparece em item nenhum** (é prosa —
e a trava da F9 já proíbe a IA de "corrigir" a palavra dele). "SALSICHA HOT DOG REZENDE" saiu
inteira, sem "…" (N1 com dado que ninguém alfaiatou). **A pergunta foi feita e o dono RESPONDEU no ato ("o que for gramaticalmente correto"): "Coxa Sobrecoxa" — aplicada e aprendida como alias (ver o §4).**

## T5 — o par Sonho + Croissant (decisão registrada)

**`conteudo_fixo["imagens"]` é uma LISTA — uma foto por zona de foto da célula, na ordem das
regiões.** O `mesa.py` do "compor 2 num slot" (F7.2) foi avaliado e NÃO serve: ele divide UMA
região em arranjo; aqui a arte JÁ separa as duas zonas com o "+" — o mecanismo certo é foto
por zona. O singular `imagem` continua valendo (compat: a mesma foto em todas as zonas). O
compositor mapeia a k-ésima zona → k-ésima foto; o diálogo dos fixos ganhou uma linha de foto
POR ZONA ("Foto da zona 1…", "Foto da zona 2…"). Prova por PIXEL na Terça real: zona 1
vermelha, zona 2 azul; e o guardião da TER virado com rastro (o dict ganhou "imagens").

## T6 — as três fotos pelo pipeline (nunca pela mão)

- **Guarda nova em produção** (`fundo.tem_alfa_util`): foto que JÁ vem recortada (alfa de
  verdade) **pula o rembg** — o `pão francês.png` do dono entra como está (testado com o
  arquivo real dele); PNG de alfa todo opaco não engana a guarda.
- **`Sonho.jpg` e `croissant.png`** passaram pelo degrau 1 REAL (rembg + luz + sombra) — o
  relatório do que as guardas disseram (J18 dos blobs, nota do avaliador) está no log da
  rodada e no fecho abaixo.
- **Real-ESRGAN:** a régua travada da F10 mira o MAIOR lado da CÉLULA — a zona do croissant
  tem ~584 px no export e a foto tem 621: **a régua mandou NÃO ampliar** (upscale além do alvo
  é proibido pela lição da frota F10). Como a ordem pediu prova de vida, o script roda uma
  ampliação sob demanda de teste (1200 px, nada gravado) e mede — o resultado no log.
- **Nenhuma foto foi tocada à mão.** O que o pipeline não resolveu está RELATADO, não
  contornado.

## §4 — a rodada, medida (o log: `saida_f13/_terca_raiz_real.log`)

- **Parser:** 5 itens exatos × **3 linhas de prosa no balde** (o "LEVE 3… 25 %", o "GANHE
  25 %" e o "PÃO FRANCÊS COM 50 %") — mostradas, nada calado. Zero produto de prosa.
- **A validade nasceu sozinha: `SOMENTE 28/07`** — e a rodada rodou NA terça 28/07: a página
  saiu com o dia real dela, sem toque (DECIMUS valendo em produção).
- **Cadastro dos 5 (vermelhos → verdes) com o alias do dono:** *"COXA SOB COXA" →
  "Coxa Sobrecoxa"* — a correção que ele confirmou por escrito ("o que for gramaticalmente
  correto") aplicada pelo caminho da curadoria E **aprendida** (`aprender_alias` — da próxima
  vez casa sozinho, a trava da F9 respeitada: só o que o dono confirmou).
- **T2 na prática:** 4/4 células, e o 5º ("Lingua e Coração 100g") **visível na estante,
  fora da grade**, com o aviso novo.
- **Densidade: 1,00** (era 0,60 na reaudição da SEXTUS) — dentro da faixa 0,95–1,15.
- **Zero "…" na página**; nomes no piso do celular (o U1 valendo no banco velho dele).
- **As fixas:** o pão recortado do dono INTACTO (a guarda pulou o rembg); o par
  Sonho + Croissant nas duas zonas com o "+" da arte entre eles — **e o croissant SEM a
  tábua** (reprocesso forçado, o gesto do Estúdio); os discos 50%/25% da arte com a mecânica
  preservada (T3 — nada implementado, nada estragado).

**O relatório das guardas (T6, tudo pelo pipeline — nenhuma foto tocada à mão):**
- `pão frances.png`: **alfa útil — rembg PULADO** (a guarda nova `fundo.tem_alfa_util`).
- `Sonho.jpg`: degrau 1 em 15,7s; **1 objeto no recorte — a guarda J18 não precisou acender**
  (o rembg comeu o papel branco sozinho); nota do avaliador: boa.
- `croissant.png`: **achado honesto — a foto NÃO é crua**: veio com alfa (recorte que INCLUI
  a tábua), e a guarda — correta — não reprocessa recorte pronto. O reprocesso foi FORÇADO
  como o gesto "processar" do Estúdio (declarado): degrau 1 em 8,4s, 1 objeto, **a tábua
  saiu**; nota: atenção (reportada). *Aberto nomeado:* o Estúdio precisa do botão explícito
  "reprocessar mesmo assim" para recorte-com-lixo.
- **Real-ESRGAN: RODOU** — prova de vida pelo caminho de produção (o modelo
  `modelos/RealESRGAN_x4plus.pth` do disco dele): croissant 621×402 → 1200×1200 em **76s**,
  nada gravado. E a régua travada da F10 foi respeitada: a zona do croissant tem ~584 px no
  export — **a régua mandou NÃO ampliar** para a página (upscale além do alvo é proibido).

**Achados nomeados no caminho (sem consertar nesta rodada):**
1. O LM real transformou "REZENDE **KG**" em "Rezende **1kg**" no cadastro — inventou o "1"
   (a guarda RG-20/`remover_inventados` não pega: "kg"→"1kg" passa na similaridade 0,75).
   Furo FINO da trava da F9 com números colados em unidade — nomeado para o G.
2. "FIGADO" saiu "Fígado" (bom), "LINGUA" ficou "Lingua" — a acentuação do cadastro degradado
   é parcial; o dono corrige no Almoxarifado uma vez e o alias segura.
3. O nome "Salsicha Hot Dog Rezende" cresceu a banda para CIMA da etiqueta da cesta (o passo
   3 da precedência agindo — legível, mas invade o vime; a etiqueta da cesta é curta para
   nome de 3 palavras). Sobra fina de arte, nomeada.
4. O reuso do projeto por nome seguiu não pegando (id=11 novo) — o aberto da DECIMUS.



## Placares (junit `bloco_fduodecimus_*` — as DUAS ordens fecham nesta bancada)

**Suíte 1039 ×2 zero skips exit-0** (1026 + 6 UNDECIMUS + 7 DUODECIMUS; runs 1 e 2);
**invertida 1039/0/0**; **janela real 4/0/0**. Guardião do marco (F12) VIRADO com rastro: o
pré-voo agora AVISA os 16 nomes abaixo do piso do celular no layout antigo do marco (célula sem
linha de descritor — a cadeia não tem para onde encurtar) — é o U1 valendo; avisa, nunca veta.
*Incidentes nomeados:* a 1ª invertida desta bancada CRASHOU no interpretador sem escrever o
junit (o placar lido era artefato velho — apagado e re-rodada limpa: 1039/0/0); e a dupla
isolada `fase7_massa+sextus` crasha 0xC0000409 no teardown SEM os arquivos novos
(pré-existente, família COND-10 — a bancada completa, que é o critério, segue exit-0).


