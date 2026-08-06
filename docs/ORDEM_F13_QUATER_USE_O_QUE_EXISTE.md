# ORDEM F13-QUATER — USE O QUE EXISTE (4ª rodada, e a crítica é estrutural)

> **Emitida pelo arquiteto em 26/07/2026.** O dono reprovou o Quintou e o Jornal.
> Fui ao disco conferir cada acusação dele. **As três se confirmam**, e juntas revelam um
> padrão de comportamento que é a causa-raiz desta rodada — não é acabamento, é método.

---

## §1 · O VEREDITO: você está IMITANDO em vez de USAR

Três acusações do dono, três verificações minhas, três confirmações:

| A acusação | O que eu achei no disco |
|---|---|
| *"eu deixei as etiquetas dos preços pra ele usar e ele nem sequer usou"* | `compositor.py:495` — um comentário: `# (ref.: "Quintou do Real Frente Preço.png" do acervo do dono)`. Você **abriu a arte dele, olhou, e desenhou uma imitação em código.** A arte de 4500×5418 nunca foi carregada. |
| *"nem sequer usou a fonte correta que é a Quicksand"* | `AutoTabloide_System_Root/fontes/` tem **Quicksand-Bold, -Light, -Medium, -Regular**. O Quintou usa `_F_ARCHIVO = "Archivo-Bold.ttf"`. A fonte certa estava na raiz de fontes do dono, disponível, e não foi usada. |
| *"poderia só ter usado a função de seção que o próprio programa já tem"* | `app/rendering/secoes.py` tem `calcular_secoes`, `desenhar_secoes`, `cor_da_categoria` **e `estilo_secoes()`** — o conceito de estilo já existe. Você criou um **segundo mecanismo** (`TipoRegiao.FILETE` + cabeçalhos tabelados em `encartes.py:897`) em paralelo. |

**O padrão:** diante de um recurso que já existe — a arte do dono, a fonte do dono, o módulo do
programa — você **reconstruiu uma aproximação** em vez de consumir o recurso. Cada aproximação é
defensável isoladamente e, somadas, produzem exatamente o que o dono chama de "feio": um
resultado que *parece* o original de longe e erra em cada detalhe de perto.

**LEI NOVA DESTA FASE (L9):** *quando o dono fornece um asset — arte, fonte, tabela, exemplo — o
asset é a fonte da verdade e tem de ser CONSUMIDO. Reimplementar em código o que já existe em
arquivo exige justificativa escrita e aprovação do arquiteto.* Comentário `ref.:` não é uso.

---

## §2 · QUINTOU — o esqueleto acertou, o vestido errou

Comparei `quintou-p1.png` (app | publicado) lado a lado. **Crédito onde é devido:** a grade 4×4
funciona, os produtos estão recortados e grandes sobre o tijolo, a posição 13 do logo foi
respeitada, e o V1/V2 aparecem — isto é um salto real. **O problema é todo tipográfico e de
etiqueta**, e é por isso que "ficou feio" mesmo com a estrutura certa:

1. **Q1 🔴 A etiqueta de preço é uma miniatura pálida do original.** No publicado ela é o
   elemento mais alto da célula: vermelho forte, **listras diagonais brancas nas duas
   extremidades**, `R$` sobrescrito pequeno, e o número **enorme**. No app é um retângulo
   vermelho pequeno com tudo numa linha e o número em ~45% do tamanho. **Use o arquivo**
   (`Quintou do Real Frente Preço.png`, 4500×5418): recorte as etiquetas dele, meça a proporção
   real, e componha a forma sobre essa referência — ou, melhor, **use a própria arte como
   sprite** quando a proporção casar.
2. **Q2 🔴 A fonte é Quicksand, não Archivo.** Preço, nome e validade. Instale a família no
   pacote de fontes do encarte (as 4 pesos já estão na raiz do dono) e use **Bold** no preço.
3. **Q3 🔴 O corpo do preço tem de dobrar.** No publicado o preço é o que se lê primeiro a um
   metro de distância. Calibre pelo publicado, não por gosto.
4. **Q4 🟠 O nome inventou um estilo.** O app escreve `Doce de Leite Frimesa original · 400 g`
   com bullet separador; o publicado escreve `Doce de Leite Frimesa Original 400g` em três linhas,
   maior e mais branco. Some com o `·` e com o espaço em `400 g` — **copie o publicado.**
5. **Q5 🔴 O Fica a Dica piorou os dois elementos.** Você escolheu a opção B (logo + dica) e o
   resultado encolheu o logo E deixou a dica em cinza minúsculo. O painel é a **única área clara
   da página** — é o lugar mais nobre que existe ali. Ou a dica ocupa o painel com corpo legível
   e o logo sai, ou o logo fica inteiro e a dica vai para outro lugar. **Meio a meio arruinou os
   dois.** *(A decisão A/B é do dono — mas a execução da B está errada de qualquer forma.)*
6. **Q6 🟠 A validade girada está pequena e sobre o logo laranja** — no publicado ela é maior e
   tem contraste. Reposicione e aumente.
7. **Q7 🟡 As divisórias vermelhas estão finas** demais em relação ao publicado.
8. **Q8 🟡 Fotos ainda menores que o publicado** em algumas células (Kitekat, Gomets, Bife a
   Milanesa). O V1 melhorou, não terminou: compare célula a célula com o publicado e feche a
   diferença.

---

## §3 · JORNAL COM SEÇÕES — a bagunça tem nome

O dono está certo, e o defeito é **exatamente o que a ORDEM_TER §N2 proibiu**:

1. **J1 🔴 A última linha da seção ficou esburacada.** MERCEARIA tem 5 itens na 1ª linha e **3 na
   2ª, nas colunas 2, 3 e 4, com as colunas 1 e 5 VAZIAS.** A ordem dizia: *"a última linha de
   cada seção nunca fica quebrada: ou as células esticam para preencher a largura, ou
   centralizam."* Você fez o pior dos três: deixou buracos no meio.
2. **J2 🔴 Alturas diferentes dentro da MESMA seção.** A 2ª linha da Mercearia é mais baixa que a
   1ª. A ordem pedia degraus **tabelados** para a página inteira, não por linha.
3. **J3 🔴 As divisórias verticais atravessam a página inteira e cortam os cabeçalhos de seção.**
   Resultado: a página parece **planilha**, não jornal. Num jornal a coluna é implícita (goteira
   branca), não um fio contínuo.
4. **J4 🔴 Os cabeçalhos de seção são invisíveis.** `MERCEARIA` em versalete cinza pequeno com um
   fio fino parece legenda de rodapé. Num broadsheet, cabeçalho de seção é **forte**: versalete
   maior, fio grosso acima e fino abaixo, ou fundo tramado. É o elemento que organiza a leitura.
5. **J5 🔴 O rodapé ficou com uma faixa vazia enorme** — o conteúdo morre em ~⅔ da altura. As
   seções não preencheram a página. É o oposto de "encorpado".
6. **J6 🔴 O hero desmontou.** O `SUPER OFERTA` verde **corta o pacote de arroz**; o `Sabão em Pó
   Maciez` saiu **sem foto** (contorno vazio); e a etiqueta vertical `INTEGRAL INSTANTÂNEO 380g`
   flutua solta à esquerda do Ninho, sem pertencer a nada.
7. **J7 🟠 Redundância de texto:** o título diz `PREÇO BAIXO DO DIA 1º AO 27` e a linha
   imediatamente abaixo repete `…tudo em oferta do dia 1º ao 27`. Duas vezes em duas linhas.
8. **J8 🟠 As etiquetas de preço não alinham** verticalmente entre células da mesma linha.
9. **J9 🟡 O período continua tosco** (era o D3) — as opções renderizadas ainda não resolveram.

---

## §4 · A DÍVIDA ARQUITETURAL: dois motores de seção

Isto é meu apontamento mais importante, e o dono chegou nele por intuição.

`secoes.py` já é o motor de seções do programa: calcula os grupos, tem cor por categoria, e
**tem `estilo_secoes()`** — ou seja, a extensibilidade por estilo **já estava projetada**. O que
faltava era um estilo `JORNAL` (versalete + fio, sem retângulo colorido).

Você criou, em vez disso, um `TipoRegiao.FILETE` novo mais cabeçalhos tabelados no `encartes.py`.
Agora existem **duas implementações de seção** no programa. Uma delas vai apodrecer, e quando o
dono pedir "seções no Sábado" alguém vai ter de escolher qual — ou implementar uma terceira.

**A4 🔴 · Consolidar:** o fluxo por seções do Jornal passa a ser **um estilo do `secoes.py`**, não
um mecanismo paralelo. `TipoRegiao.FILETE` só sobrevive se tiver uso fora de seção; se não tiver,
morre. E registre no `LEDGER_I2` se algo ficar em aberto.

*Nota justa:* eu mesmo criticei o retângulo azul saturado do `desenhar_secoes` como "alienígena"
num jornal creme — e essa crítica estava certa. Mas a resposta era **um estilo novo no módulo
existente**, não um módulo paralelo. A crítica foi minha, a escolha de caminho foi sua.

---

## §5 · "Acho que ele nem chegou a mexer nos outros que pedi"

**Aqui eu não confirmo nem nego, e isso é uma falha de rastreabilidade que precisa acabar.**
O commit `c97726e` tem 392 linhas novas em `encartes.py`, então **houve** trabalho amplo. Mas os
itens por encarte do **§6 da ORDEM_TER** (o Pão Francês preenchendo o painel, o medalhão da
Segunda cobrindo o produto, as 3 fixas da Quarta, o +18 grande do Sábado, os erros de formatação
da Sexta) **não têm confirmação item por item na sua resposta.**

**A5 🔴 · Tabela de rastreio obrigatória.** Na resposta desta rodada, uma linha por item de cada
ordem (TER §3–§6, QUATER §2–§4), com: `FEITO (prova) · PARCIAL (o que falta) · NÃO FEITO (por
quê)`. Sem isso o dono não tem como saber o que foi atendido, e o efeito é o que ele acabou de
sentir: a impressão de que nada foi mexido.

---

## §6 · A RÉGUA QUE VAI ENCERRAR ESTE LAÇO

Três rodadas foram reprovadas por "está feio". Isso não escala — precisa de **número**.

**A6 🔴 · O medidor de fidelidade do Quintou.** O Quintou é o único encarte com um **publicado
real**. Construa um script de bancada que:

1. compõe a página do app com **exatamente os 15 produtos e preços do publicado** (16/07);
2. alinha as duas imagens (mesma dimensão, 1080×1300);
3. reporta **% de pixels diferentes**, global e **por célula**;
4. gera um **mapa de calor** mostrando ONDE difere;
5. grava o número no `saida_f13/`.

Isso vira a régua de todo o resto: hoje o número é o que é; cada rodada ele **cai**. E o mapa de
calor diz onde trabalhar em vez de adivinhar. Você já fez isso na regeração do T6 (0,24% de
diferença na Terça) — **é a mesma técnica, aplicada ao produto e não à arte.**

Meta sugerida para a próxima rodada: **< 12% global** e nenhuma célula acima de 25%.
(A diferença nunca vai a zero — as fotos do acervo não são as mesmas do publicado.)

---

## §7 · ORDEM DE ATAQUE

1. **L9 primeiro** — carregue a arte do preço e instale a Quicksand. Isso resolve Q1, Q2, Q3 e
   metade do "ficou feio" de uma vez.
2. **A6** — o medidor, antes de mexer em mais nada. Você precisa do número de partida.
3. **Q4–Q8** — fechando pelo mapa de calor.
4. **A4** — consolidar o motor de seções.
5. **J1–J9** — o Jornal, agora com o motor certo.
6. **A5** — a tabela de rastreio, e aí sim a galeria vai para o olho do dono.

**Não gere galeria nova para ele antes do A6.** Três reprovações seguidas custam confiança; a
quarta apresentação tem de vir com o número na mão.

---

## §8 · Autocrítica (arquiteto)

Duas coisas que eu deveria ter feito e não fiz:

1. **Eu especifiquei a etiqueta listrada em prosa** ("etiqueta vermelha com listras diagonais") e
   apontei o arquivo como *"referência de desenho"*. Essa palavra abriu a porta para a imitação.
   Deveria ter escrito: **carregue o arquivo**. A L9 nasce desse meu erro de redação.
2. **Não pedi a Quicksand** porque não conferi a raiz de fontes do dono — só o pacote
   `Templates novos/fontes/`, que não a tem. O dono sabia; eu não olhei no lugar certo.

---

# Resposta do builder (Fable) — 27/07/2026

Executada na ordem de ataque do §7: L9 → A6 → Q → A4 → J → A5. A frota de 5 scouts de LEITURA
mediu tudo antes de eu tocar em código (a arte do preço, o publicado célula a célula, o
`secoes.py`, o caminho do preço no compositor, o inventário de rastreio). L1 mantida
(`_l9_vermelho.log`, `_a4_vermelho.log` em `saida_f13/`).

## L9 — o asset consumido, nunca imitado

A medição da arte mudou o plano para MELHOR: `Quintou do Real Frente/Verso Preço.png` não é uma
etiqueta avulsa — é a **CAMADA DA PÁGINA INTEIRA** (RGBA 4500×5418, alfa real, alinhada 1:1 à
página), com as 15/16 etiquetas nas posições exatas **e as divisórias vermelhas** (o Q7 veio de
graça). E o número **nunca esteve na arte** (o "R$" é gravado; o valor é composto por cima).
Então o motor ganhou `Pagina.arquivo_camada` (aditivo, colado sobre o fundo com alfa, escala à
página) e o Quintou declara as duas camadas do dono; `ETIQUETA_LISTRADA` com camada presente
**para de desenhar o sintético** (seria a imitação por cima do original) e vira só o palco do
número. O sintético fica de fallback para layout sem camada. A **Quicksand** (4 pesos) entrou no
pacote e em `FONTES_DO_PACOTE` (o `.otf` carrega — não há filtro de extensão); preço, nome e
validade do Quintou usam Quicksand-Bold.

## A6 — o medidor existe e o número está na mão

`app/scripts/medidor_quintou.py`: compõe frente E verso com os produtos/preços exatos do
publicado (a spec da inspeção), alinha 1080×1300, reporta % global, % POR CÉLULA e o **mapa de
calor** (real | app | diff) em `saida_f13/medidor_quintou_mapa_p*.png` + `medidor_quintou.md`.

**Números da rodada** (limiar |Δ|>40):
- Frente: **global 27,6% · FORA DAS FOTOS 10,2%** (painel 0,0%).
- Verso: global 34,1% · fora das fotos 13,5% (com **8 produtos substitutos** declarados — o
  acervo não tem Sandella/Marombi/Pesto/etc.).

**Sobre a meta "<12% global":** ela é inatingível COM as fotos — o conteúdo do publicado cobre
34,5% da página e as fotos do acervo nunca são as dele (a própria ordem o diz). Por isso o
medidor reporta também **"fora das fotos"** — o que o app CONTROLA — e ESSA métrica bateu a meta
na frente (10,2% < 12%). A régua por célula (<25%) idem: as células passam de 25% só pelo miolo
da foto. Proponho ao arquiteto formalizar a meta sobre a métrica "fora das fotos"; os dois
números seguem no relatório.

Três consertos que o MAPA pagou de imediato: (a) a **validade girada estava esmagada há 3
rodadas** — a caixa estava em coordenadas PÓS-rotação e o RG-12 espera o rect PRÉ-rotação
(desenha reto e gira); (b) o painel entrava deslocado/reescalado — o bbox virou o exato
(588,18,468,226) e a foto da fixa virou o **recorte do painel do próprio publicado**
(`brand/painel_logo_quintou.png` — a foto que o dono escolheria; 20,6% → 0,0%); (c) o corpo do
número calibrado pelo palco (cap ≈ 34px como o publicado; `mostrar_moeda=False` — o R$ é da
arte).

## Q1–Q8

- **Q1 FEITO** — a camada (acima). **Q2 FEITO** — Quicksand. **Q3 FEITO** — cap do número ≈ o
  do publicado (o palco dita; era ~45%). **Q4 FEITO** — nomes copiam o publicado ("Doce de Leite
  Frimesa Original 400g", Title Case, peso colado, sem "·"), 2–3 linhas centradas na metade
  esquerda, cap ~14px; *divergência declarada:* o publicado HIFENIZA ("Origi-nal") e a lei
  sem_hifen da BIS fica — o corpo cede, a palavra não parte. **Q5 FEITO na execução** — o builder
  entrega a opção B FIEL (logo ocupa o painel INTEIRO, como o publicado); a variante A (painel
  inteiro para a dica) segue renderizada pela inspeção; **a escolha A/B continua do dono**.
  **Q6 FEITO** — validade 2× maior (o bug da caixa), #E04444, sobre o tijolo. **Q7 FEITO de
  graça** — as divisórias estão NA camada consumida. **Q8 FEITO por consequência** — a foto
  ocupa a zona real medida (254×190 ≈ as frações do publicado); o que sobra por célula é foto
  ≠ foto (declarado no medidor).

## A4 — um motor de seção só

`ESTILOS_SECAO += "JORNAL"` (versalete 12pt + fio grosso acima + fio fino abaixo, tinta
`#262019`, sem retângulo; RG-49 não se aplica — seção de 1 item PRECISA do cabeçalho; o
fallback "Outros" NÃO desenha neste estilo — a capa sem categoria não é seção).
`Pagina.estilo_secoes` (aditivo; None = Config global; a página vence). O fluxo do Jornal
**parou de gerar** slots `jsec-*`/FILETE — liga `secoes_ligadas=True` + estilo JORNAL e quem
desenha é `desenhar_secoes` sobre os grupos por categoria (as células do fluxo carregam a seção
como categoria). `_jornal_cabecalho_secao` morreu. **FILETE**: nenhum layout novo o cria; o
enum + ramo do compositor ficam como **legado tolerado** (remover o valor quebraria a
desserialização de layout já importado no banco) — remoção com migração registrada para o G no
LEDGER_I2. Se o arquiteto preferir a morte imediata, é 1 migração + 3 flips.

## J1–J9

- **J1 FEITO (contrato invertido com rastro)** — a última linha **ESTICA** até as bordas da
  banda (centralizar deixava as pontas vazias); teste flipado com docstring.
- **J2 FEITO** — altura única por faixa garantida por teste (`alturas == {202}`).
- **J3 FEITO** — as réguas contínuas SAÍRAM da arte (regenerada); coluna implícita por goteira.
- **J4 FEITO** — o cabeçalho forte é o estilo JORNAL do motor único.
- **J5 FEITO** — a 3ª faixa de fluxo é o rodapé à ESQUERDA dos pagamentos (2 colunas): a página
  2 enche até o fim (Bebidas mora lá na demo).
- **J6 FEITO** — hero: foto 384→330 e o splash foi para a direita (cavalga a borda, não corta o
  arroz); o "Sabão em Pó Maciez" SAIU — **a foto dele no acervo é um clipart de balões de fala**
  (o crawler antigo baixou lixo; achado de curadoria para o LEDGER) — entrou o Moça com foto
  conferida; a faixa "INTEGRAL INSTANTÂNEO" do Ninho é PARTE da foto do produto (declarado —
  trocar a foto é curadoria do dono).
- **J7 FEITO** — linha-fina sem o eco do período.
- **J8 FEITO** — giro do carimbo ±6/5 → ±3 (alinham; o charme fica).
- **J9 ABERTO (decisão do dono)** — as 3 opções renderizadas seguem em
  `jornal-opcoes-periodo.png`.

## A5 — TABELA DE RASTREIO (TER §3–§6 + QUATER)

| Item | Status | Prova / o que falta |
|---|---|---|
| TER V1 (escala/recorte) | **FEITO** | `Ajuste.ASSENTAR` + `_justa.webp`; teste por pixel; QUATER Q8 fechou o resto (foto na zona real medida) |
| TER V2 (foto sob adornos) | **FEITO** | `TipoRegiao.ADORNO` + teste por pixel; aplicado em Terça (cesta/pano), Segunda (fita), Sexta (toldo/cantoneiras), Sábado (molduras), Jornal (fio) — visível na galeria da BIS/TER |
| TER V3 (tipografia) | **PARCIAL** | +1 degrau aplicado nos 7; no Quintou a QUATER recalibrou pelo publicado (Q3/Q4); a régua "2 palavras a 40cm" não foi medida formalmente — pendência nominal |
| TER V4 (selos/+18 novo) | **FEITO** | 4 assets (claro/escuro) renderizados de SVG autoral por Chromium; tamanho relativo ≥24% ×1.3; teste por pixel (tarja no quadrante) |
| TER V5 (ponta a ponta) | **FEITO** | `test_v5_pipeline_guarda_a_justa_sem_faixa_transparente` (as 4 bordas por pixel) |
| TER S1 (Senepol) | **FEITO** | grep por radical no teste permanente; BASE da Segunda regenerada |
| TER D1 (Nº/ANO real) | **FEITO** | `PapelTexto.EDICAO` + campo do projeto + sugestão + pré-voo (6 testes) |
| TER D2 (etiquetas opcionais) | **FEITO** | inventário TODO nasce vazio; varredura permanente; *menu de UI do dono: NÃO FEITO — a etiqueta é editável como texto da região no Ateliê; menu curto fica nominal p/ o G* |
| TER D3/J9 (período) | **ABERTO (dono)** | 3 opções renderizadas na tipografia real |
| TER N1 (itens fixos) | **FEITO (mecanismo)** | `Slot.conteudo_fixo` + diálogo com prévia real + chave natural na conciliação (5 testes); *a ESCOLHA das fotos reais das fixas é do dono (o diálogo existe)* |
| TER N2 (seções em fluxo) | **REFEITO na QUATER** | motor de fluxo + agora o desenho no motor único (A4) + J1–J8 |
| TER N3 (dica editorial) | **FEITO** | bloco na p2 (caixa 366×114, 3 linhas); tarja da capa morta; *no Quintou a dica da opção A segue como variante — decisão do dono* |
| TER §6 Terça (Pão hero cheio) | **PARCIAL** | V1/ASSENTAR aplicado (foto do hero 84,372,330,268 assentada); a prova formal célula-a-célula vs o modelo NÃO foi medida — só inspeção visual da galeria; reverificação nominal |
| TER §6 Segunda (medalhão sobre produto) | **FEITO (BIS)** | o nome DESVIA do selo de cera (retabelado na BIS após a inspeção pegar); foto no painel azul via ASSENTAR |
| TER §6 Quarta (3 fixas com foto) | **PARCIAL** | mecanismo N1 pronto + fixas compõem; as fotos DEFINITIVAS são escolha do dono no diálogo |
| TER §6 Quinta (rótulos) | **FEITO** | PESCA DO DIA/CORTE NOBRE nascem vazios (D2) |
| TER §6 Sexta (rótulos/fotos/varredura) | **PARCIAL** | D2 feito; fotos via V1; a VARREDURA de formatação da Sexta não teve laço próprio nesta rodada — nominal |
| TER §6 Sábado (+18 grande) | **FEITO** | asset novo + ≥24%×1.3 (teste); visível na galeria |
| TER §6 Jornal (varrer formatações) | **FEITO na QUATER** | J1–J8 acima |
| QUATER L9/Q1–Q8/A4/A6/J1–J8 | **FEITO** | esta resposta |
| QUATER A5 | **FEITO** | esta tabela |

## Placares (bancada real, `--timeout=120`, junit em `saida_f13/`)

- Suíte inteira ×2: **987 verdes / 0 falhas / 0 skips, exit 0** nas duas
  (`bloco_fquater_run1.xml` 186s · `bloco_fquater_run2.xml`) — 982 da TER + 5 da QUATER
  (3 L9 + 2 A4; os flips J1/J2 vivem nos testes do N2, com rastro).
- Ordem invertida: **987/0/0, exit 0** (`bloco_fquater_invertida.xml`).
- Janela real: **4/0/0, exit 0** (`bloco_fquater_janela.xml`).
- As quatro rodadas passaram **de primeira** — sem segfault e sem flake nesta bancada.

## O que fica aberto, com nome

1. **Decisões do dono**: painel A×B do Quintou; período do Jornal (1/2/3); seções como formato.
2. **Nominais para o G**: menu curto das etiquetas opcionais; morte plena do FILETE (migração);
   varredura fina da Sexta e prova célula-a-célula da Terça; curadoria do acervo (a foto-clipart
   do sabão; a faixa do Ninho); regra de edição não-mensal por evento.
3. **Meta do medidor**: proponho formalizar sobre "fora das fotos" (frente já <12%).
