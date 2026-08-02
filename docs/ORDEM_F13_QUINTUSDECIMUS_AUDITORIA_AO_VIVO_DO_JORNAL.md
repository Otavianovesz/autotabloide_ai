# ORDEM F13-QUINTUSDECIMUS — AUDITORIA AO VIVO DO JORNAL DO MÊS

> **Emitida pelo arquiteto em 01/08/2026.** O dono: *"Não funcionou… reveja isso melhor e rode
> por você mesmo todo o passo a passo… audite por sua conta e pontue absolutamente TUDO."*
>
> **Fiz.** Dirigi o app na máquina dele por computer-use: subi o programa, abri o Jornal do Mês
> pelo Ateliê, importei a foto real da tabela de agosto, esperei os 42 itens conciliarem, abri a
> curadoria, testei o "Criar" e o "Vincular…", e **cancelei sem gravar nada no banco dele.**
>
> **A queixa dele está certa, e a causa-raiz é UMA LINHA.**

---

## §1 · O ACHADO-MÃE: a detecção de "2 produtos" existe, funciona, e NUNCA é consultada

### 1.1 · A prova de que o detector funciona

Rodei o detector determinístico contra as **seis** linhas multi-produto da tabela real dele:

```
SIM  MOLHO TOMATE FUJINI e CAJAMAR 300 g ORIGINAL          pendencias=['multiplos']
SIM  ARROZ SOMAR e TIO BONINI 5 Kg                         pendencias=['multiplos']
SIM  BISCOITO BULNEZ e ADORALLE 270 g C. CRACKER/LEITE/…   pendencias=['multiplos']
SIM  MILHO VERDE FUGINI POUCH e BONARE 170 g LATA          pendencias=['multiplos']
SIM  AMACIANTE MON BIJOU 5 LTS PROTEÇÃO e CLASSICO         pendencias=['multiplos']
SIM  SARDINHA COQUEIRO 125 g TOMATE / OLEO e LIMÃO         pendencias=['multiplos']
```

**Seis de seis.** O `sanitizar()` acende a pendência `"multiplos"` em todas.

### 1.2 · E a prova de que ele é jogado fora

`servico.py::proposta_de_criacao` — os dois ramos são **exclusivos**:

```python
    # ── ramo SEM IA ───────────────────────────────────────────
    sugestao = (dividir_em_dois(descricao)
                if any(pd.codigo == "multiplos" for pd in res.pendencias)
                else [])
    return PropostaCriacao(..., possivel_composto=len(sugestao) == 2, ...)

    # ── ramo COM IA (o que rodou na máquina dele) ─────────────
    enr = enriquecer(descricao, motor)
    comps = [c.nome_sanitizado for c in enr.componentes]
    return PropostaCriacao(
        mais18=enr.mais18 or eh_bebida_alcoolica(enr.nome_sanitizado),  # ← OR!
        possivel_composto=len(comps) >= 2,                              # ← SEM OR
        ...)
```

**Com o LM Studio ligado, o código entra no 2º ramo e retorna — o `dividir_em_dois` nunca roda.**
A IA devolveu zero componentes para o "Fujini e Cajamar", e o sinal determinístico que estava
pronto foi descartado.

### 1.3 · E o conserto já está escrito TRÊS LINHAS ACIMA

Olhe o `mais18` na mesma função: `enr.mais18 **or** eh_bebida_alcoolica(...)`.
**A heurística é somada à IA.** Para o `possivel_composto`, não foi.

**J1 🔴 · O conserto:**

```python
possivel_composto = (len(comps) >= 2
                     or len(dividir_em_dois(descricao)) == 2)
componentes = comps or dividir_em_dois(descricao)
```

E a **lei** por trás, que vale para o motor inteiro:

> **A IA SOMA, nunca SUBSTITUI.** Todo sinal determinístico que o app sabe calcular continua
> valendo quando a IA está ligada. A IA pode acrescentar; nunca pode apagar o que a régua achou.
> *(Isto é o espelho da trava da F9 — "sem IA tudo degrada com aviso". Faltava o outro lado:
> "com IA, nada regride".)*

**Varredura obrigatória:** ache **todos** os pontos onde um ramo `if motor:` retorna cedo e
descarta um cálculo determinístico do ramo `else`. Reporte a lista. Suspeito que este não é o único.

---

## §2 · O QUE EU VI NA TELA, na ordem em que aconteceu

### 2.1 · Antes de importar

| # | Achado | Gravidade |
|---|---|---|
| **J2** | O app abriu na **Mesa restaurada** com o Quintou, e o chip da validade dizia **"sem data — clique"**. A cascata da DECIMUS roda no `carregar_layout` (abrir pelo Ateliê) mas **não na restauração de sessão**. Abrindo o Jornal pelo Ateliê, o chip preencheu certo. | 🟠 |
| **J3** | O botão **" Importar tabela/foto" da barra não respondeu** ao clique; o botão do painel vazio (à direita) abriu o diálogo normalmente. Confirme se é foco/hit-test ou se o da barra está mesmo morto. | 🟠 |
| **J4** | A miniatura do **"Jornal do Mês" no Ateliê está em branco**, enquanto as outras 14 têm conteúdo. Provavelmente a miniatura só compõe a página 1 e o Jornal falha por ser de 2 páginas. | 🟡 |

### 2.2 · A importação — e aqui há uma vitória grande

| # | Achado | |
|---|---|---|
| **J5** | **O OCR leu os 42 itens** da foto da tabela de agosto — colorida, com fundo amarelo, linhas alternadas e tipo pequeno. Somado à foto de monitor da Quarta, o OCR está sólido. **Não regrida isto.** | ✅ |
| **J6** | **A validade da tabela foi extraída:** o rodapé do diálogo mostra *"Validade da tabela: 03/08/2026 até 27/08/2026"*. | ✅ |
| **J7** | **A tela não travou.** O progresso saiu no rodapé ("Conciliando 20/42… há 25s") e a janela seguiu utilizável. O D1 está de pé. | ✅ |
| **J8** | **A conciliação levou ~1min40s** para 42 itens — e **desacelerou**: 20 itens em 25 s, 40 em 84 s. Não é linear. Algo cresce com o número de itens já processados (cache que vira lista? consulta que refaz o acervo?). **Meça e ache.** | 🟠 |

### 2.3 · A tela de conciliação

**J9 🔴 · DOIS itens multi-produto foram auto-aceitos VERDES** — ele não tem nem a chance de intervir:

| Linha da tabela | Casou com | Problema |
|---|---|---|
| `ARROZ SOMAR e TIO BONINI 5 Kg` | "Arroz Tio Bonini" | **duas marcas viraram uma**, em silêncio |
| `BISCOITO BULNEZ e ADORALLE 270 g C. CRACKER/LEITE/AGUA` | "Biscoito Bulnez 270g" | **duas marcas + três sabores** viraram um |

Um "verde" é um caminho sem porta: o item entra no tabloide sem passar pela curadoria.
**Enquanto o J1 não estiver de pé, linha com pendência `multiplos` NUNCA pode sair verde** —
no mínimo vira amarela ("Conferir").

**J10 🔴 · Verde errado por volume:** `REFRIGERANTE KITUBAINA 1,6 LT` casou **verde** com
`Refrigerante Kitubaina 1,3L`. São produtos diferentes. Procurei no `conciliacao.py` por uma
guarda de peso/volume no veredito (`_peso_bate`, `peso_incompativel`) — **não existe**. O trabalho
do B1 fez o peso **escolher entre candidatos**; falta ele **rejeitar um verde**.
> **Regra:** peso/volume divergente entre o importado e o candidato **rebaixa verde → amarelo**,
> sempre. Nunca casa calado.

**J11 🔴 · Os candidatos do "Vincular…" não têm piso.** Cliquei "Vincular…" no *Molho de Tomate
Fujini e Cajamar*. A lista:

```
Extrato de Tomate Só Fruta Pote 300g   (66)
Ração Gato Kit e Kat Carne ao Molho 70g (56)
Bala Gelatina Fini Tubes Tropical 80g   (56)
Doce de Leite Frimesa Original 400g     (55)
Milho Pipoca Camplar Premium 500g       (55)
```

`top_k = 5` sem nenhum piso de plausibilidade (`conciliacao.py:175`). **Ração de gato como
candidato para molho de tomate** é pior que lista vazia: parece defeito e é armadilha de clique.
> **Regra:** só entra na lista quem passar de um piso (sugiro **70**). Se ninguém passar, mostre
> só "Buscar no acervo…" com o texto *"nenhum parecido — busque pelo nome"*.

**J12 🔴 · O "Criar" vai direto para a busca de imagem.** Cliquei "Criar" no Fujini e Cajamar:
abriu **"Escolher imagem"** com o nome fundido, o checkbox **"+18 (Bebida alcoólica)"** (✅ existe),
a busca e 6 resultados — **todos Fujini, nenhum Cajamar** — e **uma única** foto escolhível.
**Nenhuma pergunta "São 2 produtos?"** apareceu. O checkbox existe no código
(`curadoria_dialog.py:84`) e veio desligado porque `possivel_composto` era False (§1).

---

## §3 · SABORES E VARIANTES — o pedido de cerne dele, ainda não atendido no fluxo

O Code criou as **famílias** no Almoxarifado. Mas **no caminho da importação elas não existem**:

| Linha da tabela | O que ele quer | O que o app fez |
|---|---|---|
| `SARDINHA COQUEIRO 125 g TOMATE / OLEO e LIMÃO` | 1 produto, 3 sabores, marcar quais tem, 1 foto por sabor | um produto chamado "Sardinha Coqueiro Tomate Óleo e Limão 125g" |
| `AMACIANTE MON BIJOU 5 LTS PROTEÇÃO e CLASSICO` | 2 fragrâncias | "Amaciante Mon Bijou Clássico Proteção 5L" |
| `ROSQUINHA MABEL 600 g COCO e LEITE` | novo sabor da família Rosquinha Mabel | sugeriu "Rosquinha Mabel **Chocolate** 300g" (sabor E peso errados) |
| `MILHO VERDE FUGINI POUCH e BONARE 170 g LATA` | 2 marcas, 2 embalagens | "Milho Verde Fugini Pouch e Bonare 170g" |

**J13 🔴 · A curadoria precisa da terceira pergunta.** Hoje ela pergunta "é este?" (vincular) e
oferece "criar". Falta: **"são variantes do mesmo produto?"** — com os sabores detectados
(`TOMATE / OLEO e LIMÃO` → três), caixas de seleção para marcar quais existem, e **uma foto por
sabor marcado**. É o que ele descreveu com todas as letras.

E o detector já tem o sinal: a mesma pendência `multiplos` acende. **A diferença entre "2 produtos"
e "2 sabores" é uma pergunta, não um algoritmo** — deixe ele decidir com um botão de rádio:

```
Esta linha parece ter mais de um item:
  ○ São 2 produtos diferentes   (cria dois, compõe o nome)
  ○ São sabores do mesmo produto (cria a família, você marca quais tem)
  ○ É um produto só             (o nome é assim mesmo)
```

**J14 🟠 · A sugestão da Rosquinha ignorou peso E sabor** (600 g coco e leite → 300g chocolate).
Mesma raiz do J10: peso divergente não rebaixa nem reordena.

---

## §4 · PERDAS DE INFORMAÇÃO NO NOME (o "comeu informação", agora na importação)

| Importado | Virou | Perdeu |
|---|---|---|
| `SABÃO PÓ OMO 1.6 Kgs **CAIXETA L. PERFEITA**` | Sabão Pó Omo 1,6kg | a linha do produto |
| `CAFÉ 3 CORAÇÕES 500 g **A VACUO TODOS**` | Café 3 Corações 500g | embalagem e "todos os tipos" |
| `CREME LEITE PIRACANJUBA 200 g **TETRA**` | Creme de Leite Piracanjuba 200g | a embalagem |
| `MILHO VERDE … **POUCH** e … **LATA**` | Milho Verde Fugini Pouch e Bonare 170g | a associação embalagem↔marca |

**J15 🟠** O que sai do nome **tem de ir para o descritor**, nunca evaporar — é a mesma regra da
QUARTUSDECIMUS §2 (o qualificador desce, não some). Aqui está sumindo na *criação*, antes de
chegar à página.

**J16 🟠 · Dois erros de OCR não corrigidos:**
`MILHO **PICOCA** YOKI` (pipoca) e `**OLE O** de SOJA **CONCÓRCIA**` (Óleo / Concórdia) — a
palavra quebrada não foi juntada e o typo não foi corrigido. O corretor de grafia pegou o
`PÔ→PÓ` mas não estes. **Amplie o vocabulário com estes casos e rode a tabela inteira dele
como teste de regressão.**

---

## §5 · O QUE ESTÁ BOM (para não regredir)

- **O OCR venceu a tabela colorida de 42 linhas** e a foto de monitor da Quarta.
- **A validade da tabela** é extraída e mostrada.
- **O rodapé de progresso** substituiu o véu — a tela fica livre.
- **As miniaturas na coluna "No banco"** ajudam a reconhecer de relance.
- **O "→" para itens novos** (mostrar o nome que será criado) é uma boa ideia — mantenha, mas
  distinga melhor do casamento real (cor ou coluna própria), porque hoje os dois moram na mesma
  coluna e eu mesmo li errado na primeira passada.
- **O checkbox "+18"** está visível na criação.
- `AÇUCAR CRISTAL DOCE DIA 2 **Kgs**` e `QUEIJO MUSSARELA SZURA Kg` casaram certo — os plurais
  funcionaram.
- `LEITE PÓ NINHO INTEGRAL INSTANTANEO 380 g` casou certo — o `PÓ` foi corrigido.

---

## §6 · ORDEM DE ATAQUE

1. **J1** — o OR do `possivel_composto` + a varredura de todos os `if motor:` que descartam
   régua. **É uma linha e destrava a queixa inteira dele.**
2. **J9 + J10** — linha com `multiplos` nunca sai verde; peso divergente rebaixa para amarelo.
3. **J11** — piso de plausibilidade nos candidatos.
4. **J13** — a terceira pergunta (2 produtos × sabores × produto só), com foto por sabor.
5. **J15 + J16** — o que sai do nome vai ao descritor; os dois erros de OCR.
6. **J8** — a desaceleração da conciliação.
7. **J2 + J3 + J4** — o chip na restauração, o botão da barra, a miniatura do Jornal.

**A prova de aceitação desta rodada é literal:** *o dono importa a tabela de agosto e, das seis
linhas multi-produto, as seis o consultam.* Nenhuma sai verde calada, nenhuma vira um produto
com nome de dois.

---

## §7 · Nota de método

Esta foi a primeira vez que eu **dirigi o app inteiro** em vez de auditar artefato. Rendeu 16
achados em vinte minutos, e o principal — o `or` que falta — eu **só encontrei porque vi a
pergunta não aparecer na tela** e fui atrás do porquê. A resposta do builder dizia
*"8 linhas acenderam essa pergunta"*, e na máquina dele, com a IA ligada, **nenhuma acendeu**.

É a família de sempre (**verdade num artefato, falsa no que o dono usa**), agora com uma variante
nova que vale registrar: **a alegação era verdadeira no ambiente do builder (IA desligada) e
falsa no do dono (IA ligada).** Daqui em diante, toda alegação sobre a IA precisa dizer **em qual
dos dois estados** foi verificada — e a bancada deve rodar os dois.

---
---

# §8 · SEGUNDA SESSÃO AO VIVO — "TESTA O ARROZ" (01/08/2026)

> O dono pediu: *"testa o arroz, por exemplo, seleciona alguma imagem e veja como ele progride…
> nem que tenhamos que repaginar tudo."* Fiz o caminho inteiro na máquina dele, com o banco
> salvo antes (`backups/core_pre_auditoria_arroz_20260801_2225.db`, 2.256.896 bytes), até a
> página composta e a prévia de exportação.
>
> **Resultado: a linha do Arroz é a que menos porta tem no programa inteiro, e o Jornal saiu
> com 11 dos 42 itens — sem que nada avisasse.** Onze achados novos, J17–J27.

---

## J17 🔴 · A LINHA VERDE NÃO TEM PORTA NENHUMA — e é a linha que ele citou

`ARROZ SOMAR e TIO BONINI 5 Kg` casou com `Arroz Tio Bonini`, saiu **verde "No banco"**, e a
coluna **Ação veio vazia (`—`)**. Cliquei na linha: nada. Botão direito: **não abre menu**.

Não há como, nessa linha: **desvincular**, **trocar o casamento**, **dividir em dois**,
**escolher foto**, **digitar o preço**. Ela é o único item da tabela em que o dono não pode
fazer absolutamente nada.

E é exatamente o caso que ele descreveu duas vezes: *"tem vezes que já tem um item no banco de
dados, mas ele não reconhece… queria ter uma opção pra poder forçar um item virar outro ali na
importação do OCR"* — e *"arroz somar e chibonini"* pedindo para virar **dois** itens. São duas
marcas na mesma linha (**Somar** E **Tio Bonini**); o app casou com uma, **jogou a outra fora em
silêncio**, e fechou a porta.

**Peça:** **toda** linha, verde inclusive, tem no mínimo **"Trocar…"** (reabre a escolha contra o
acervo, com busca por nome) e **"Separar em 2"**. Verde quer dizer *"eu resolvo se você não
disser nada"*, nunca *"você não pode mais falar"*.

---

## J18 🔴 · O PREÇO DA SUPER-OFERTA SOME, e não existe onde digitar

As duas linhas `S. OFERTA` da tabela dele — `ARROZ… de 18,81 → por 6,90` e
`ÓLEO DE SOJA CONCÓRDIA… de 8,49 → por 6,90` — chegaram na conciliação com **Preço `—`**.

A causa está certa e o efeito está errado: `preco_decimal` recusa texto com mais de um número
(a guarda **P0.3b**, que existe para "2x 5,00" não virar 25,00 — correta). Mas **ninguém captura
a recusa**: não vira pendência, não rebaixa para amarelo, não abre campo. A linha sai **VERDE**.

Na página composta, a célula do Arroz e a do Óleo desenham um **carimbo decorativo
"SUPER OFERTA" no lugar onde deveria estar o preço**. O encarte iria ao cliente **sem preço nos
dois itens de maior destaque da página**. Isso é o **I2** violado no lugar mais caro possível.

**Peça:** o padrão "de X por Y" é o **mais comum do varejo** e tem de ser primeira classe, não
exceção rejeitada. Parsear os **dois**: `Y` é o preço, `X` é o riscado (o app já sabe desenhar
"de/por" — é o cartaz de gôndola). Enquanto não parsear, **a linha nunca sai verde** e o preço
vira **campo editável na própria tabela**.

---

## J19 🔴 · O ITEM-HERÓI DO JORNAL NÃO DESENHA PREÇO

`Isotônico Gatorade 500ml`, **R$ 6,90** no painel, ocupando a **maior célula da página**: saiu
com a garrafa, o nome em corpo minúsculo **fora da célula**, e **nenhum preço**. A célula-herói
do layout do Jornal ou não tem região de preço, ou tem e não é preenchida.

Três itens sem preço numa página de onze (J18 × 2 + J19) — e nenhum deles apareceu como erro.

---

## J20 🔴 · "ACEITAR TODOS OS VERDES" DESCARTA 31 DAS 42 LINHAS, EM SILÊNCIO

Medido, contador antes e depois de **um clique**:

| | verdes aceitos | para revisar | novos |
|---|---|---|---|
| antes | 11 | 4 | 27 |
| **depois** | **11** | **0** | **0** |

Os 27 "Novo" e os 4 "Conferir" **sumiram da tabela**. Não foram criados. Não foram ignorados por
escolha dele. A Mesa recebeu **"ITENS DA OFERTA (11)"** — e a página do Jornal do Mês, que tem
42 células, saiu **três quartos vazia**.

Existe um **"Desfazer"** depois do clique (bom), mas **nada avisa** que 31 linhas serão perdidas,
e o nome do botão promete o contrário: quem lê *"aceitar todos os verdes"* entende *"resolve os
fáceis e me deixa cuidar do resto"*.

**Peça:** o botão aceita os verdes e **as demais linhas permanecem na tabela**. Se houver motivo
para removê-las, a remoção é dita antes, com número: *"11 verdes serão aceitos. As 31 linhas
restantes continuam aqui para você resolver."*

---

## J21 🔴 · RESOLVER UMA LINHA REPINTA A COLUNA "NO BANCO" DE TODAS AS OUTRAS — com lixo

Antes de eu criar a Sardinha, cada linha "Novo" mostrava `→ Nome que será criado` (honesto, com
seta). **Depois de criar UMA única linha**, a mesma coluna passou a exibir — **sem a seta**, como
se fosse casamento — o top-1 do fuzzy:

| Importado | Passou a exibir |
|---|---|
| CERVEJA AMSTEL 269 ml PALITO | **Doce de Leite Frimesa Original 400g** |
| SABÃO PÓ OMO 1.6 Kgs CAIXETA L. PERFEITA | **Paleta Senepol 100g** |
| TOALHA de Papel MILI 2x1 | **Bife à Milanesa BBX 100g** |
| AMACIANTE MON BIJOU 5 LTS PROTEÇÃO e CLÁSSICO | **Azeite Gallo Extra Virgem Clássico 500ml** |
| REQUEIJÃO DANONE 200 g ORIGINAL | **Amido Milho Quero 200g** |
| TEMPERO TIO JONAD 1 Kg TODOS | **Arroz Tio Bonini** |
| MOLHO TOMATE FUJINI e CAJAMAR 300 g | **Extrato de Tomate Só Fruta Pote 300g** |
| ÁGUA MINERAL MARIA VA 500 ml S/ GÁS | **Sal Amoníaco Milha Gourmet 100g** |

O mecanismo se lê nos casos: *Mili* → *Mil**anesa***, *Tio* Jonad → *Tio* Bonini, *Tomate* →
*Tomate*. É o **J11 (sem piso de plausibilidade)** exibido no lugar mais visível da tela, e
agora sem a seta que era a única marca de "isto ainda não existe".

**Medição que salva o diagnóstico:** cliquei "Criar" na Amstel. O diálogo veio com o nome certo,
**"Cerveja Amstel Palito 269ml"**, e o **+18 já marcado sozinho**. Ou seja: **a criação acerta;
só a tabela mente.** Mas é pela tabela que ele decide o que clicar — e a tabela está dizendo que
a cerveja dele é um doce de leite.

**Peça:** (a) o repintar não pode trocar `→ nome a criar` por candidato; (b) candidato abaixo do
piso de plausibilidade **não se exibe** — exibe-se `—`; (c) quando exibir candidato numa linha
"Novo", que seja com rótulo (*"parecido: …"*), nunca no mesmo formato do casamento confirmado.

---

## J22 🟠 · O DIÁLOGO "ESCOLHER IMAGEM" NÃO OFERECE A DIVISÃO — e é onde ela faria falta

Abri o "Criar" de `SARDINHA COQUEIRO 125 g c/ TOMATE / ÓLEO e LIMÃO` — **três sabores separados
por "/"**, o caso que ele descreveu por extenso. O diálogo veio com **um nome só, uma imagem só**,
e **nenhuma caixa "são N produtos"**.

Detalhe que fecha o argumento: dos **6 candidatos** que a busca devolveu, havia latas de sabores
diferentes (vermelha/tomate, verde/óleo, o pack sortido). **A busca achou os três sabores; o
diálogo não consegue aceitar mais de um.** É o **J1** visto do outro lado da parede.

---

## J23 🟠 · O diálogo é pequeno demais para o que faz, e os botões estão cortados

"Escolher imagem" ocupa cerca de **1/6 da tela**; as miniaturas — a única coisa que importa ali —
ficam do tamanho de selo postal, e é com elas que ele escolhe 42 fotos seguidas. A fileira de
botões **não cabe na largura**: **"Sem imagem" aparece como "m image"** e "Usar esta" sai
truncado.

E o diálogo **não diz de qual linha veio** nem **quantas faltam**. Numa sessão de 42 itens, ele
precisa ver o texto importado original ("SARDINHA COQUEIRO 125 g c/ TOMATE / ÓLEO e LIMÃO") e um
contador **"12 de 42"**.

---

## J24 🟠 · A manchete da data mente até alguém clicar em Auto-preencher

Ao concluir a importação, a manchete da página dizia **"PREÇO BAIXO DO DIA 1º AO 27"**, enquanto
a validade lida da tabela (correta) era **03/08/2026 a 27/08/2026**. Só **depois** do
Auto-preencher a manchete virou **"DIA 3 AO 27"**.

Quem salvar ou exportar sem auto-preencher publica a data errada. **A manchete é derivada; tem de
se recalcular quando a validade chega, não quando alguém aperta outro botão.**

---

## J25 🟠 · A foto ainda não enche a zona — a régua da QUARTUSDECIMUS não chegou ao Jornal

Na página composta: **Batata Palha**, **Refrigerante Kitubaina** e **Biscoito Bulnez** ocupam bem
menos que a célula. O refrigerante (garrafa alta e fina) deixa **mais de metade da largura
vazia**. A regra "a foto enche a zona" existe em código e **não alcançou este layout** — é a
mesma família da UNDECIMUS (regra viva no repositório, artefato do dono sem ela).

**Peça:** a prova desta rodada mede a taxa de preenchimento **das células do Jornal no banco
dele**, não numa página de fábrica.

---

## J26 🟠 · Nomes e descritores do Jornal seguem abaixo do teste do celular, e em serifada

"Batata Palha Bulnez", "Refrigerante Kitubaina", "Sardinha Coqueiro" saem pequenos; os
descritores (*"Crocante · 100g"*, *"Instantâneo · 380g"*, *"Szura · 1kg"*, *"Concordia · 900 ml"*)
estão **ilegíveis mesmo na tela do computador**, quanto mais no celular. O nome do **herói**
(Gatorade) é o **menor texto da página inteira** — e está desenhado **fora** da célula, no rodapé
dela. A família é **serifada**, não Quicksand.

---

## J27 🟢 · O QUE FUNCIONOU (não regredir)

- **O +18 marcou-se sozinho** na Cerveja Amstel. (A dúvida dele — *"não sei se ele identificou
  que é bebida alcoólica"* — está respondida: identifica.)
- O painel da Mesa **avisa** `1 sem foto · 2 sem preço` e tem chips de filtro clicáveis. A
  degradação não é totalmente silenciosa **ali** — é silenciosa na conciliação, que é antes.
- O **rembg rodou em ~30 s** e a Sardinha entrou com fundo limpo; na página ficou boa.
- A prévia **"Ver como vai sair" não desenha as guias das células vazias** — o que exporta está
  limpo.
- A **busca automática de fotos acertou em todos os casos que abri** (sardinha, cerveja): 6
  candidatos, todos do produto certo.

---

## §9 · ORDEM DE ATAQUE — REVISADA (substitui a §6)

**Onda 1 — sem isto o dono não consegue fechar UM Jornal:**

1. **J20** — "Aceitar todos os verdes" para de descartar as outras 31.
2. **J18 + J19** — "de X por Y" vira preço de primeira classe; a célula-herói desenha preço.
   Nenhum item chega à página sem preço sem que a página **diga**.
3. **J17** — "Trocar…" e "Separar em 2" em **toda** linha, verde inclusive.
4. **J1 + J22** — o `or` do `possivel_composto`, e a caixa "são N produtos" **dentro** do
   diálogo de imagem, com **uma foto por componente**.

**Onda 2 — a tela para de mentir:**

5. **J21 + J11** — piso de plausibilidade; candidato fraco não se exibe; "Novo" nunca perde a seta.
6. **J24** — a manchete recalcula quando a validade chega.
7. **J23** — o diálogo cresce, mostra o texto importado e o contador "n de N".

**Onda 3 — a página fica publicável:**

8. **J25 + J26** — foto enche a zona **e** nome/descritor passam o teste do celular **medidos no
   banco dele**, no layout Jornal.
9. **J9, J10, J13, J15, J16, J8, J2, J3, J4** — como estavam na §6.

---

## §10 · A PROVA DE ACEITAÇÃO DESTA ORDEM (literal, medida na máquina dele)

> O dono importa `Jornal do Mês Agosto.jpeg` e, **sem digitar nada**, chega a uma página onde:
>
> 1. **os 42 itens estão na Mesa** (nenhum descartado sem ele mandar);
> 2. **nenhum item tem preço vazio** — as duas super-ofertas mostram "de 18,81 por 6,90";
> 3. **a célula-herói tem preço**;
> 4. **as seis linhas multi-produto o consultaram** — nenhuma virou um produto com nome de dois;
> 5. **nenhuma linha "Novo" exibe um casamento que não existe**;
> 6. a manchete diz **3 ao 27** desde o primeiro instante.

**Nada disso se demonstra em página de fábrica.** Cada item acima se mede abrindo o
`AutoTabloide_System_Root/banco/core.db` do dono e a página que ele vê — a lição da UNDECIMUS,
que J25 acabou de reincidir.

---

## §11 · Nota de método (a sexta reincidência, e uma nova)

| Rodada | O que estava certo | O que o dono tinha |
|---|---|---|
| §17 | o relatório do marco | tabloide sem foto |
| QUINQUE | a galeria | app vazio |
| NONUS | a página de exemplo | 4 nomes truncados |
| UNDECIMUS | o código da calibração | 115 de 123 regiões sem piso |
| QUINTUSDECIMUS §1 | a detecção de composto (IA off) | nenhuma pergunta (IA on) |
| **§8 (J25)** | **"a foto enche a zona"** | **garrafa em 40% da célula, no Jornal** |

**A variante nova desta sessão** vale registro próprio: em **J21**, o *código está certo e a
tela está errada* — o "Criar" da Amstel monta o nome certo com o +18 certo, e a tabela ao lado
exibe "Doce de Leite Frimesa". Até aqui o padrão era *artefato certo × uso errado*; agora é
**motor certo × vitrine errada**, dentro da mesma tela.

Consequência de método, que passa a valer: **toda alegação de que "o app resolve X" tem de dizer
o que aparece na tela quando resolve.** Um `assert` no resultado da função não cobre a coluna que
o dono lê. É a **L10** ("nada é feito enquanto não estiver alcançável pelo dono na interface")
puxada um passo adiante: **alcançável e legível — o que a tela afirma também é entregável.**

---

# RESPOSTA DO BUILDER (03/08/2026) — a ordem executada

## A lei nova está de pé — e testada nos DOIS estados

**J1 🔴 CONSERTADO** (o `or` + a régua a bordo): `enriquecer_descricao`
ramo COM IA agora soma `dividir_em_dois` — `possivel_composto = len(comps)>=2
OR len(det)==2`, com a sugestão determinística nos campos e o check
desmarcado (a IA que deu componentes pré-marca; a régua nunca). Teste
`test_j1_composto_com_ia_ligada_e_sem_componentes_da_ia` roda com um
FAKE LIGADO devolvendo zero componentes — o cenário exato da sua
máquina. **Provado no LM real:** `possivel_composto=True` para o
Fujini e Cajamar com a IA ligada.

**A varredura dos `if motor:`** (frota de leitura): além do J1, um
furo menor (`ordenar_tipo_marca` só no ramo sem-IA — inócuo por ser
conservador, anotado) e uma causa-raiz registrada: as `pendencias` do
sanitize não viajam no `ProdutoEnriquecido` — por isso o ramo IA não
tinha como somar sem re-sanitizar (agora re-sanitiza). O resto do
motor JÁ somava (conciliador, embeddings, revisora — o modelo da lei).

## Onda 1 — o dono fecha UM Jornal

- **J20** — "Aceitar todos os verdes" NÃO remove mais linha nenhuma:
  os verdes contam como aceitos e as demais PERMANECEM (toast diz os
  números). Contrato do teste antigo atualizado de propósito.
- **J18** — "de X por Y" é 1ª classe (`preco_de_por` + 3º canal no
  `classificar_preco_ocr` + listas paralelas até o ItemMesa; o "de" da
  TABELA vence o do banco e DESENHA no tabloide: riscado + % calculado).
  Preço ilegível NUNCA sai verde calado: pendência `preco_ilegivel` +
  amarelo + motivo dito; a célula Preço da conciliação avalia a edição
  na hora (aceita "de 8,49 por 6,90"). De brinde a frota achou: o
  `_RE_N_POR` da colagem mastigava "…5,99 por 4,99" como "99 por
  R$ 4,99" — o de/por agora tem precedência.
- **J19** — o herói do Jornal ganhou região de PREÇO (carimbo das
  chamadas, corpo 24 — a hierarquia do herói). Na página real: o
  Gatorade sai com R$ 6,90.
- **J17** — a linha VERDE ganhou porta: "Trocar…" (o menu do vínculo)
  e "Separar em 2" (abre a curadoria com a pergunta LIGADA e a
  sugestão nos campos). Verde = "eu resolvo se você não disser nada".
- **J22/J13** — a TERCEIRA PERGUNTA está na curadoria: rádio
  "São 2 produtos / São SABORES do mesmo produto / É um produto só",
  com os sabores DETECTADOS (o que vem depois da medida é sabor:
  `familia_da_linha` — a Sardinha dá Tomate/Óleo/Limão; o Arroz de 2
  marcas dá zero), checkboxes por sabor, nome da família sugerido.
  "São sabores" cria um produto POR sabor + FAMÍLIA (B4) + o item vira
  leque (`criar_familia_de_sabores`, headless e testada).

## Onda 2 — a tela para de mentir

- **J21** — linha NOVA nunca perde a seta: o `_recarregar` mostra
  "→ nome a criar" (proposta da fila ou o nome sanitizado); candidato
  de vermelho vive só no "Vincular…". (E o getattr defensivo matou uma
  cascata de 8 falhas de bancada — a fila era lida antes de nascer.)
- **J11** — `PISO_CANDIDATO_EXIBIDO = 70`: ração de gato nunca mais
  aparece como sugestão de molho de tomate; o motor segue com os top-5
  por dentro.
- **J24** — a manchete é DERIVADA: a adoção da validade dispara
  re-render na hora, e o dado "__pagina__" leva a validade ao
  compositor MESMO com a página vazia (o "1º ao 27" morre no primeiro
  instante, não no auto-preencher).
- **J23** — a curadoria cresceu (1040×680), mostra a LINHA IMPORTADA
  original e o contador "item n de N" (a fila dos vermelhos).

## Onda 3 — no que deu para ir com qualidade

- **J9** — linha com pendência "multiplos" casada verde DESCE a
  amarelo com motivo (o exato/alias do dono fica — escolha humana; e
  com a porta nova do J17 até ela tem saída). `ItemMesa.motivo` novo:
  o amarelo DIZ por quê.
- **J10** — `_rebaixar_se_peso_diverge`: peso/volume divergente rebaixa
  o verde ("1,6 LT × 1,3L — confira"); o peso igual segue verde, por
  teste (o Kitubaina do seu achado é o caso do teste).
- **J16** — "PICOCA→pipoca" e o bigrama "OLE O→óleo" no corretor
  (com os testes antigos do sanitize atualizados de propósito: o
  OLE O agora é CONSERTADO em vez de só avisado).
- **J25** — zona_flex nas chamadas E nas linhas do Jornal; a guarda da
  célula-vestida aprendeu o FILETE (ADORNO ≤2 mm é separador, não
  roupa — a cesta da Terça continua barrando, por teste); a tolerância
  de rotação cobre o charme de −6°/−8° (rotação de verdade segue
  barrando).
- **J26** — corpos do Jornal: herói 9,4→15 (nome) e 8→10,5; chamadas
  13→14,5/9,4→10,5; linhas 11→12,5/8,5→10. A família segue Fraunces —
  a serifada É a identidade do publicado (L9); a queixa mensurável era
  corpo, não família (declarado).
- **J2** — a restauração de sessão roda a MESMA cascata da validade
  das outras portas (o chip "sem data" com layout carregado morreu).

## O que ficou de fora, NOMEADO (não coube com qualidade nesta rodada)

- **J8** (a desaceleração ~não-linear da conciliação): o scout apontou
  suspeitos (juiz por ambíguo = rede por item; identity map);
  medição instrumentada fica para a próxima — não mexi às cegas.
- **J3** (o botão da barra): o connect existe e nunca é sacrificado
  pelo reflow; sem reprodução na bancada. Suspeita: overlay da
  restauração por cima. Fica aberto com esta nota.
- **J4** (miniatura do Jornal em branco no Ateliê).
- **J15** (o que a IA descarta ir ao DESCRITOR em vez de evaporar) —
  a guarda RG-20 segue avisando e segurando o lote; a devolução
  automática ao descritor fica nomeada.
- **J14** (a Rosquinha) — o J10 do peso já rebaixa o palpite de 300g
  para a linha de 600g; a sugestão por família entra quando o dono
  criar a família Mabel.
- A série de curadorias de foto POR SABOR além do 1º (a foto escolhida
  vai ao 1º; os demais completam no Almoxarifado, avisados).

## A prova §10, medida na máquina (IA LIGADA, a foto real)

1. **42 itens** na conciliação (nenhum descartado) ✓
2. **0 itens sem preço** ✓
3. **O herói desenha preço** (R$ 6,90 na página recomposta) ✓
4. **As 10 linhas multi-produto: ZERO verdes caladas** — amarelas com
   motivo, vermelhas (a curadoria pergunta) ou verde-EXATO (o alias que
   VOCÊ ensinou na sua sessão — escolha humana, agora com "Separar em
   2" disponível) ✓
5. **Linha "Novo" nunca exibe casamento falso** (a seta é lei no
   recarregar) ✓
6. **Manchete "3 AO 27" desde o primeiro instante** (o __pagina__) ✓

Páginas recompostas do banco real: `saida_f13/jm-prova-p1.png` / p2.
Pacote reimportado (8 chaves, upsert) — o layout 14 do banco do dono
tem o herói com preço, os corpos novos e o flex.

## Método (o §11 acatado)

Toda alegação desta resposta diz o estado da IA em que foi verificada;
os testes-chave do composto rodam com fake LIGADO (zero componentes — a
sua máquina) e DESLIGADO. Placares em `saida_f13/bloco_jq_*.xml`.
