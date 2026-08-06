# ORDEM F13-DUODETRICESIMUS — O HÍFEN QUEBRA MARCA, E A QUINTA DO PEIXE

> **Emitida pelo arquiteto em 05/08/2026.** Duas frentes: a varredura do Quintou (a escada do nome
> entrou e trouxe um efeito colateral sério) e a **primeira auditoria da Quinta do Peixe**.

---

# PARTE I · QUINTOU

## §1 · 🔴 A HIFENIZAÇÃO ESTÁ PARTINDO MARCAS

A escada entrou (degrau 3, `nome_fit:578`) — **e não tem guarda de marca.** Colhido das duas
páginas:

| saiu | é a marca |
|---|---|
| `Azeite de Oliva **Ando-** / **rinha** Lata 200ML` | **Andorinha** |
| `Milho Pipoca **Cam-** / **pilar** Premium 500G` | **Campilar** |
| `Adoçante Xilitol **Low-** / **çucar** 300G` | **Lowçucar** |
| `Maionese Hellmann's **Supre-** / **me** 330G` | **Supreme** (a linha do produto) |
| `Biscoito Belma **Cre-** / **am** Cracker 300G` | **Cream Cracker** |
| `Geléia Ritter **Gour-** / **met** Hortelã 310G` | **Gourmet** |

**Marca partida ao meio é o mesmo defeito do K3 do Jornal** ("Amaciante Mon / Bijou"), que já
custou uma ordem inteira — agora chegando por outro caminho.

> **L25 — O HÍFEN NÃO ENTRA EM NOME PRÓPRIO.** Marca, submarca e nome de linha são **átomos**:
> nunca se hifenizam, nunca se partem entre linhas. O hífen só entra em **palavra comum**
> (*"Achocola-tado"*, *"Concen-trado"*, *"Instan-tâneo"*). Antes de hifenizar, a cadeia consulta
> o mesmo `extrair_marca` que já protege o corte nome/descritor.

E há um segundo critério que o dicionário do `pyphen` não dá: **não hifenizar palavra estrangeira**
("Cream", "Supreme", "Gourmet"). *Regra prática: só hifeniza o que o dicionário PT-BR conhece.*

## §2 · 🔴 A ESCADA PULA PARA A ELIPSE em vez de subir os degraus

Dois nomes saíram **cortados com "…"**:

- `Chá Instantâneo Dina Tea…` (p1) — perdeu **"Melancia/Frutas Silvestres"**
- `Achocolatado Pirakids…` (p2) — perdeu **"200ml"**, que é o peso

**E os dois saíram em corpo MAIOR que os vizinhos** — que é o que ele descreveu:
*"em alguns pontos ela está grotesca de grande e não arruma como no Pirakids"*.

Diagnóstico: nesses dois a escada **não desceu** — manteve o corpo alto e cortou. Nos outros
desceu. **O degrau 4 (reduzir) não está sendo alcançado quando o degrau 3 falha.**

*Peça: elipse é o ÚLTIMO recurso, depois de esgotar abreviação, hifenização e redução até o piso.
E **o peso nunca entra na elipse*** — se algo tem de sair, sai o descritor, nunca a gramatura.

## §3 · 🔴 O NÚMERO DA LINHA DA TABELA VAZOU PARA O NOME

`**14** Bis Lacta Xtra Branco e o Oreo 45G`

O **"14"** é o número da linha na tabela dele. Entrou no nome do produto e foi impresso.

*Peça: a numeração de linha da tabela é metadado — **nunca** parte do nome. E o pré-voo acusa nome
que começa com número solto seguido de espaço.*

## §4 · 🔴 UM PREÇO SAIU SEM CARIMBO

Na p2, o **Ervilha Fugini Crocante 170G · 2,90** está em **texto branco solto sobre o azul** —
sem o carimbo vermelho. Todos os outros 15 têm.

*Peça: é a 16ª célula da página; provavelmente a grade de carimbos do template tem 15. **O
compositor tem de acusar** "célula sem carimbo" no pré-voo, nunca desenhar preço solto.*

## §5 · O nome não está centrado VERTICALMENTE contra o carimbo

Ele disse *"não está centralizada"*. Horizontalmente está certo (à esquerda, como o original).
**Verticalmente não:** o bloco do nome assenta no alto e o carimbo é mais alto que ele — na
referência os dois se **centram um contra o outro**.

*Peça: o bloco do nome centra-se verticalmente na altura do carimbo da sua célula.*

## §6 · O resto da varredura do Quintou

1. **A quarta fileira da p1 tem só 3 produtos** + o logo — o original tem a mesma estrutura, ok.
2. Os **selos BB** seguem flutuando no canto superior das células, longe do produto.
3. **Coração e Língua BBX não tem selo BB** e é marca própria — critério inconsistente.
4. A **Ração Thor 7 kg** aparece do mesmo tamanho de um sachê de gelatina (área óptica).
5. **Fígado Bovino** e **Coração e Língua** são fotos de vísceras cruas em close — a esta escala
   ficam pouco apetitosas. *Sugestão ao dono: foto em bandeja, como o Bife.*
6. `Molho Tomate Cajamar 300G **Origi-nal**` — o descritor "Original" veio para o nome; deveria
   ficar no descritor e não precisaria hífen.
7. **`Açucar`** sem cedilha em "Açúcar Itamaraty" (p1, 1ª célula) — mas **`Açúcar Mascavo`** com.
   Inconsistente na mesma página.
8. A **validade "Até 06/08"** está só na p1; a p2 tem "ATÉ 06/08 Só Hoje" no cabeçalho. Ok, mas
   **a p1 não traz "enquanto durarem os estoques"**.

---

# PARTE II · QUINTA DO PEIXE — primeira auditoria

A arte é **bonita e a mais elegante das oito**. Os defeitos são de **composição**, não de estilo.

## §7 · 🔴 QUATRO ARRANJOS INTERNOS DIFERENTES NA MESMA PÁGINA

| célula | arranjo |
|---|---|
| Peixe Pintado | nome **em cima à esquerda**, foto **embaixo à direita**, preço embaixo à esquerda |
| Filé de Tilápia | foto **em cima**, nome **embaixo** |
| Camarão Dona Fresca | foto **em cima**, nome **embaixo** |
| Lombo Bacalhau | nome **à esquerda**, foto **à direita** |
| 3 de baixo | foto **em cima**, nome **embaixo** |

**Cinco células seguem um padrão e duas inventam o seu.** É a causa do "estranho".

*Peça: **um arranjo só** para as células de destaque e um para as de grade. Se a célula grande é
horizontal, o padrão é **foto à direita / texto à esquerda** — e vale para as DUAS grandes.*

## §8 · 🔴 A FOTO DO PEIXE PINTADO É MINÚSCULA na maior célula da página

A célula é a maior da peça e a foto ocupa talvez **15%** dela. O resto é creme vazio. É a mesma
doença do herói do Jornal — **a célula grande não tem produto grande**.

*Peça: na célula de destaque, o produto ocupa **≥ 55% da área**.*

## §9 · 🔴 O PESO DUPLICADO VOLTOU — `Camarão Dona Fresca · 250g · 800 g`

**Dois pesos no mesmo descritor**, exatamente o bug da Água Mineral (500ml · 497 ml) que foi
consertado no Jornal. **Não chegou aqui** — é a L22 outra vez.

E é pior neste caso: **o cliente não sabe se R$ 99,00 é o de 250 g ou o de 800 g.**

## §10 · "Ofertas válidas SOMENTE 06/08" aparece DENTRO de duas células

Está impresso dentro do cartão do **Peixe Pintado** e do **Lombo Bacalhau**, como se fosse
propriedade daqueles dois produtos. A validade é **da página** — e já está no selo do cabeçalho
("SOMENTE HOJE 06/08") e no rodapé.

**Três vezes a mesma informação, duas delas no lugar errado.**

## §11 · O resto do Peixe

1. **`kg` sozinho como descritor** do Pintado — fica órfão. Melhor: *"inteiro · por kg"*.
2. **Escala das fotos desigual**: Tambaqui e Sardinha grandes; Pintado e Camarão pequenos.
3. **O recorte do Peixe Pintado é ruim** — bordas sujas.
4. **Todos os preços no mesmo corpo** — R$ 199,00 e R$ 19,99 com o mesmo peso.
5. **Nenhum destaque**: sete ofertas, nenhuma marcada como a principal.
6. Os **três de baixo** têm o nome em corpo maior que os de cima — hierarquia invertida (célula
   menor, texto maior).
7. **Sem selo de marca própria** em nenhum, e sem "produto congelado" onde cabe.
8. As **duas células grandes de cima** têm alturas diferentes — a do Pintado é mais alta que a da
   Tilápia, e as bordas não fecham.
9. **`Camarão Descascado · Seara · 30/50 · 400 g`** — "30/50" é a contagem por kg; sem rótulo
   parece código.
10. O rodapé é **o melhor dos oito** (endereço, telefone, social, legais). *Peça: ele vira o padrão
    dos outros sete.*

---

# §12 · ORDEM DE ATAQUE

**Onda 1 — o que sai errado impresso:**
§3 (o "14") · §4 (preço sem carimbo) · §9 (peso duplicado no Peixe) · §1 (hífen em marca)

**Onda 2 — a escada e a composição:**
§2 (elipse por último; peso nunca sai) · §5 (centro vertical) · §7 (um arranjo só) · §8 (o
produto enche a célula grande)

**Onda 3 — acabamento:**
§10 (validade uma vez só) · §6 · §11

---

# §13 · PROVA

> 1. **nenhuma marca hifenizada** em nenhum dos oito encartes — teste que lista as quebras e
>    confere contra o glossário de marcas;
> 2. **nenhum nome com "…"** nas páginas do Quintou;
> 3. **nenhum nome começando com número solto**;
> 4. **todo preço dentro de um carimbo** — ou o pré-voo avisa;
> 5. **um peso por item** no Peixe (a mesma regra do Jornal, rodando nos oito);
> 6. **um arranjo por classe de célula** na Quinta do Peixe;
> 7. produto ocupa **≥ 55%** da célula de destaque.

---

# §14 · Nota

**A L22 está sendo violada a cada encarte novo.** O peso duplicado foi consertado no Jornal e
reapareceu no Peixe. A mordida, o piso do celular, o teto da etiqueta — nenhuma atravessou.

Cada encarte novo que ele abre é uma **regressão a um estado que já foi consertado em outro
lugar**. Isso não é sequência de defeitos: **é um defeito só — o de as regras morarem no layout
em vez de morarem no motor** — e ele vai se repetir mais cinco vezes (Segunda, Terça, Quarta,
Sexta, Sábado) se não for atacado como causa.

*Peça de arquitetura, e é a mais importante desta ordem:* **um teste único, parametrizado pelos
oito layouts, que roda TODAS as regras de composição já conquistadas.** Um arquivo. Oito
parâmetros. Enquanto ele não existir, cada encarte novo vai custar uma ordem inteira.


---

# RESPOSTA DO BUILDER (05/08/2026)

## §14 PRIMEIRO — O TESTE DOS OITO existe (`app/tests/test_os_oito.py`)

**Um arquivo. Oito parâmetros. Oito regras nomeadas.** Cada lei
conquistada virou uma função que recebe a página COMPOSTA (do banco,
pela porta real — L16) e devolve as violações; o pytest parametriza
pelos oito encartes do pacote. Lei nova entra AQUI e passa a valer nos
oito no mesmo commit.

As regras de hoje, cada uma com a ordem que a criou: R1 hífen não
parte marca (L25), R2 nenhum nome elipsado, R3 nome sem número solto,
R4 um peso por item (QUARTUS §1.2), R5 a unidade nunca some
(QUARTUSDECIMUS §2), R6 texto dentro da região (TERTIUSDECIMUS/A1),
R7 piso do celular (UNDECIMUS/U1), R8 preço coerente na página (§4).

**Infraestrutura que nasceu com ele:** o compositor agora REGISTRA o
que desenhou (`base._texto_desenhado`: linhas, corpo final, altura,
rect) — a auditoria lê o desenho REAL em vez de recalcular por fora.
Isso não é conforto de teste: a primeira versão da rede recalculava e
acusou 6 encartes de defeitos que **não existiam** (media o nome cru
sem a escada, sem os rects substituídos, sem o piso de runtime).
Conferi o instrumento antes de reportar — a lição que o senhor
registrou na rodada passada, aplicada do meu lado.

### O que a rede achou de VERDADE (e um é grave)

**Defeito de motor, 27 ordens sem ver:** quando a região tem piso
IGUAL ao teto (sem margem de manobra), UMA linha podia sair mais alta
que a caixa e o texto **vazava** — a elipse corta por LINHAS e com uma
linha só não tem o que cortar. Conserto no `ajustar_texto`: em último
recurso o corpo cede abaixo do mínimo declarado até a linha caber (o
rect manda — A1). Achado no Jornal e no Sábado, consertado no motor,
vale nos oito.

**Dívida DECLARADA (não escondida):** a Sexta Verde tem 2 células de
destaque com preço em TEXTO puro enquanto as outras 9 têm carimbo — a
mesma classe do "Ervilha Fugini sem carimbo" do §4. Conserto é de
ARTE (a rodada da Sexta), então está no dicionário `DIVIDA` do teste,
com nome e motivo: defeito novo deixa vermelho, e quando a Sexta for
consertada o número tem de baixar junto (também vermelho) — a dívida
não pode ser esquecida nem crescer.

## PARTE I — QUINTOU

**§1 (o hífen partiu marca) — L25 no motor.** Duas guardas, porque
uma só não resolve: (a) o VOCABULÁRIO — marca conhecida é ÁTOMO e
nunca se parte (as marcas da página viram átomos no compositor e
descem até o `_quebrar_linhas`); (b) o PISO DE TAMANHO — só se parte
palavra com 8+ letras, que mata "Cream" (5), "Supre|me" (7),
"Gour|met" (7) sem precisar de dicionário de estrangeirismo. O seed
de marcas cresceu com as que o hífen estragou (Andorinha, Campilar,
Lowçucar, Bauducco, Anaconda, Belma, Cepera, Marombi, Predilecta,
Apti, Vitacoco, Negresco, Madremassa, Faisão).

**CONFLITO DECLARADO (L23 × L25):** o publicado do dono hifeniza
"Cerveja Itaipa-va" — Itaipava É marca. Com a L25, o app deixa
"Itaipava" inteira e diverge da referência nesse ponto. Não escolhi
por ele: a L25 é a ordem vigente e está implementada; se o dono
preferir o comportamento do publicado (marca pode partir quando é o
único jeito de caber), é uma linha de configuração. **Pergunta ao
dono/arquiteto.**

**§3 (o "14" no nome).** A numeração da tabela é metadado e some —
mas a decisão é do LOTE, nunca da linha: "3 Corações" e "1 Kg" também
começam com número. `sem_numeracao_de_lote` só remove quando a maioria
das linhas abre com inteiro E a sequência é CRESCENTE (a assinatura de
uma coluna de numeração, que nome de produto não tem).

**§2 (a elipse) / §5 (centro vertical) / §6:** a elipse do "Chá
Instantâneo…" e do "Achocolatado…" caiu junto com o conserto do
transbordo (o corpo agora cede antes de cortar) — a rede confirma:
R2 verde nos oito. O centro vertical do nome contra o carimbo e os
itens do §6 ficam NOMEADOS (são calibração de layout do Quintou, e a
próxima rodada dele os pega com a referência ao lado).

**§4 (preço sem carimbo).** Virou a regra R8 da rede — e ela já achou
a irmã do defeito na Sexta Verde.

## PARTE II — QUINTA DO PEIXE

**§9 (peso duplicado).** A regra "um item, um peso" está no MOTOR
desde a QUARTUS e a rede prova que vale no Peixe (R4 verde nos oito
com o item de prova que tem peso no nome E unidade divergente). O
"250g · 800 g" da peça enviada vem de um projeto CONGELADO (composto
antes do conserto) ou de cadastro com os dois pesos no nome — ao
reimportar, sai um peso só. Se reaparecer numa composição nova, a
rede acusa.

**§7 (quatro arranjos) e §8 (a foto de 15%)** são conserto de LAYOUT
do Peixe (geometria das células) — a mesma classe da dívida da Sexta.
Ficam para a rodada da Quinta do Peixe, e a rede ganha as regras
"um arranjo por classe de célula" e "produto ≥55% da célula de
destaque" quando essa rodada acontecer (as duas precisam da
referência publicada do Peixe para calibrar — L23).

**§10, §11:** acabamento nomeado.

## Incidentes de bancada (honestidade)

1. A 1ª versão da rede acusou 6 encartes com defeitos inexistentes —
   instrumento errado (recalculava sem a escada). Consertado com o
   registro do compositor. **Não reportei nada antes de conferir.**
2. Duas réguas minhas nasceram tortas dentro da própria rede: o piso
   do celular cobrado acima do teto da região (layout que declara 14
   pt não pode ser cobrado por 16,6) e a condição do "corpo cedeu para
   caber" invertida. As duas corrigidas medindo o caso concreto.

## O que ficou de fora (nomeado)

- O CONFLITO L23×L25 (Itaipa-va) — decisão do dono;
- §5 centro vertical e §6 do Quintou (calibração com a referência);
- §7/§8/§10/§11 do Peixe — a rodada da Quinta, com a referência dela;
- a dívida da Sexta Verde (2 preços sem carimbo), declarada no teste;
- as pendências antigas: halos, correção-que-avisa, legais, Config.



## POST-SCRIPTUM — a divida "endurecer vigias" MORREU (5 quedas num dia)

O flake do `test_b1` derrubou a bancada 5 vezes hoje e cada rodada o
nomeava de novo. Com a suite mais pesada (o teste dos oito importa o
pacote 8x) ele virou bloqueio. Parei de adiar:

1. **O vigia deixou de matar a suite.** Ao esgotar o tempo ele
   DESISTIA calado e o `exec()` do modal ficava vivo — a suite INTEIRA
   morria de timeout, sem dizer qual dialogo. Agora ele FECHA o que
   estiver aberto, registra `esgotou` e o teste falha por ASSERCAO.
2. **E a assercao entregou a causa-raiz** (que 5 quedas nao tinham
   entregue): o vigia guardava os dialogos ja respondidos por
   `id(caixa)`. O 1o dialogo e destruido ao fechar e o CPython
   RECICLA o endereco — o 2o QInputDialog nascia com o MESMO id, o
   vigia o dava por respondido e ninguem clicava nele. Guardar o
   OBJETO (a referencia segura o id) matou o flake: 5 execucoes
   seguidas do teste, verdes.

O timeout do vigia tambem subiu de 4 s para 20 s (4 s e curto quando
a maquina importa oito layouts em paralelo).
