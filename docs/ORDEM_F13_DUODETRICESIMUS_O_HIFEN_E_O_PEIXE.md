# ORDEM F13-DUODETRICESIMUS - O HIFEN QUEBRA MARCA, E A QUINTA DO PEIXE

(A ordem do arquiteto de 05/08/2026 — duas frentes: a varredura do
Quintou pos-escada e a primeira auditoria da Quinta do Peixe; mais o
§14, a peca de arquitetura: o teste unico parametrizado pelos oito.)

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
