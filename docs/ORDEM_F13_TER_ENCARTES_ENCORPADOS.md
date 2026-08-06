# ORDEM F13-TER — ENCARTES ENCORPADOS (3ª rodada do laço)

> **Emitida pelo arquiteto em 26/07/2026.** A F13-BIS acertou a **identidade** (as formas de
> preço, o subtítulo, os rótulos — o salto é real e visível). O dono olhou e reprovou por outro
> motivo: *"as imagens estão muito pequeneninhas… os tabloides poderiam ser mais encorpados…
> o Fica a Dica ficou ridículo… o símbolo ficou minúsculo."*
>
> Esta rodada é sobre **ESCALA, PREENCHIMENTO e CAMPOS QUE MUDAM**. Método: o mesmo laço do
> §4 da BIS. **Executor: Fable.**

---

## §1 · A CAUSA-RAIZ DO "PEQUENENINHAS" — uma só, e explica todos os 7

O dono perguntou: *"todos os itens estão sendo recortados adequadamente como era no projeto
original? Depois de tirar o fundo, o ideal era cortar até o limite pra foto ficar do tamanho que
o item é e caber ele da maior forma nos espaços."*

**A resposta é: o recorte acontece e é imediatamente desfeito.** `fundo.py::processar_imagem`:

```python
normalizado = normalizar(recortar_conteudo(sem_fundo), lado, padding_frac)
```

1. `recortar_conteudo` corta na bbox do alfa — **exatamente o que ele pediu.** ✅
2. `normalizar(..., lado=1000, padding_frac=0.06)` pega esse recorte justo e o **cola centralizado
   num quadrado 1000×1000 com 6% de folga em cada lado.** ❌

Resultado: a foto salva no acervo **não é o item — é um quadrado com o item pequeno no meio**.
Depois o compositor encaixa esse quadrado na zona da célula com `Ajuste.CONTER`, que ajusta o
**quadrado**, não o produto. **Dupla redução:**

- uma garrafa alta numa célula larga: o quadrado já desperdiçou as laterais; o CONTER desperdiça
  de novo ⇒ o produto ocupa **~40% da área disponível**;
- é exatamente o que se vê na Segunda: a lata do Ninho num canto de um painel azul enorme.

**V1 🔴 · O conserto:** a imagem de composição **preserva a proporção do item**, sem quadrado e
sem padding. `normalizar` continua existindo (é boa para a grade de miniaturas do Almoxarifado),
mas **sai do caminho da composição**. Guardar a versão justa (`_justa.webp`, alfa preservado) ao
lado da normalizada — sem destruir nada (curadoria não-destrutiva, trava da F10).
Na célula, o ajuste passa a ser **"encher a zona respeitando a silhueta"**: escala pelo maior
fator que ainda caiba na zona, âncora **no rodapé da zona** (produto assenta, não flutua), e
recorte só se estourar.

---

## §2 · O QUE EU ERREI — SENEPAL

O dono: *"você não mudou o Senepal pra Senepol."* **Ele está certo e a falha é minha.**
Quando conferi o F8 eu greppei `CENEPOL|SENEPOL`, achei `SENEPOL` no Sábado e escrevi no §13 do
dossiê que a correção "não era necessária". **Nunca greppei `SENEPAL`.** Está aqui:

```
Templates novos/geradores/gen_segunda3.py:235   Senepal
Templates novos/geradores/gen_carne_final.py:111  SENEPOL   ← este está certo
```

**S1 🔴:** `Senepal` → `Senepol` em `gen_segunda3.py:235`, **regerar** a BASE da Segunda, e
**varrer o pacote inteiro** por variantes da palavra (`Senep*`) em vez de confiar numa grafia.
E acrescente ao teste de varredura de strings: nenhuma ocorrência de `Senepal` no pacote.

---

## §3 · OS TRANSVERSAIS DE ESCALA (valem para os 7)

### V2 🔴 A foto vai POR BAIXO das formatações, para preencher o vazio
Pedido literal: *"arrumar o espaço dessas imagens urgente pra ser maior e acabar indo embaixo das
formatações, pra aparecer incluso no espaço mesmo e deixar ela preencher todo o vazio ali."*

Hoje a zona da foto é um retângulo que **termina** onde começa a cesta/o toldo/a banda do nome.
Passa a ser uma **zona estendida**: começa no topo da célula e vai **até depois** do adorno,
com o adorno desenhado **por cima** da foto. O produto então "assenta" atrás da cesta (Terça),
atrás do toldo (Sexta), atrás da banda azul (Segunda) — e o vazio desaparece.
Isso é ordem de desenho: `foto → adorno da estrutura → nome → preço → selos`. Já temos o
z-order consertado (R-02/C3); aqui é só declarar a zona maior e a ordem certa por encarte.

### V3 🟠 Tipografia mais encorpada
*"os textos também talvez… poderiam ser mais encorpados e completos."*
Subir um degrau o **nome** (peso e corpo), manter o subtítulo legível, e **aumentar o preço**
dentro da forma. Regra: o nome de produto de 2 palavras tem de ser lido a 40 cm de distância no
celular. Calibre olhando, não por número — e registre o antes/depois na leitura do laço.

### V4 🔴 Os selos estão minúsculos — e o +18 precisa ser desenhado de novo
*"o símbolo ficou minúsculo e quase não dá pra ver o +18 ou o qualidade belo brasil."*
1. **Tamanho:** o selo passa a ter tamanho mínimo relativo à célula (não absoluto), e no
   Sábado/Segunda (bebida) ele é **destaque**, não enfeite.
2. **Desenho novo:** fazer um símbolo de **proibido para menores de 18** bonito e elaborado —
   vetorial próprio, legível em 24 px e em 200 px: círculo de proibição, o "18" forte, e a
   tarja. Duas variantes (fundo claro / fundo escuro). Entregar como asset do projeto, não
   como texto.
3. O selo "Qualidade Belo Brasil" idem — tamanho mínimo e contraste.

### V5 🟠 Provar o recorte ponta a ponta
Teste que pega uma foto real com fundo, roda o pipeline, e prova **por pixel** que a imagem de
composição **não tem faixa transparente** nas quatro bordas (a prova de que o quadrado morreu).

---

## §4 · CAMPOS QUE MUDAM — pare de cravar no desenho

Regra nova, e ela vale para tudo: **rótulo que não é sempre verdade não pode estar na
estrutura.** Ou vira campo alimentado por dado, ou sai.

### D1 🔴 Jornal: Número e Ano são REAIS
*"o Número e o Ano são de verdade. Eles mudam todo mês conforme a edição nova."*
`Nº 177 · ANO 42` está cravado na arte. Vira **campo do projeto**: a edição incrementa por
mês/publicação e o ano vem da data. Guardar no `Evento`/campanha, autopreencher como a validade
faz hoje (D7 do Bloco D), e **nunca** publicar com o número da edição anterior — pré-voo avisa.

### D2 🟠 Rótulos condicionais: "pesca do dia", "corte nobre", "direto da granja"…
*"tem duas coisas falando corte nobre e pesca do dia. Não é certeza que sempre vai ter algo
assim… então ou tira ou seja inteligente pra colocar as coisas certas no lugar."*
Inventário e decisão **um por um**: `★ PESCA DO DIA ★` e `CORTE NOBRE` (Quinta),
`★ DIRETO DA GRANJA ★` e `★ COLHEITA DA SEMANA ★` (Sexta), `★ O CORTE DA SEMANA ★` (Sábado),
`SUPER OFERTA` (Jornal). Cada um vira **etiqueta opcional da célula**, escolhida pelo dono num
menu curto (ou vazia). Vazia ⇒ **não desenha nada** — nunca um rótulo mentindo.

### D3 🟠 Jornal: "do dia 1 ao 27" está tosco
Trocar por algo melhor e mais atraente, com o período **editável** (já era o F8). Sugestões para
ele escolher: `OFERTAS DE 1º A 27 DE AGOSTO`, ou o período dentro de um selo de calendário, ou
`VÁLIDO TODO O MÊS DE AGOSTO · ATÉ DIA 27`. **Mostre 2 ou 3 opções renderizadas** e deixe o dono
apontar — isto é decisão de dono, não de builder.

---

## §5 · AS DUAS FEATURES NOVAS

### N1 🔴 Itens FIXOS com foto escolhida pelo dono
Pedido repetido em três encartes: *"as três ali são fixas… eu quero escolher as imagens ali e
deixar elas na melhor forma possível"* (Quarta); *"o Kit Burguer fixo toda semana, como que faço
pra escolher a imagem"* (Segunda); e o Pão Francês / Sonho+Croissant (Terça).

O `Slot.fixa` já existe (Bloco F). **Falta o vínculo:** um registro de **"itens fixos do
encarte"** — produto + foto escolhida + nome + preço opcional — guardado **com o template**,
editável num diálogo simples ("Itens fixos deste encarte"), que:
- **não** entra na fila do auto-preencher (já garantido);
- **sobrevive** à reimportação da tabela (é do encarte, não da semana);
- deixa o dono **escolher a foto** do acervo ou de arquivo, e ver a prévia na célula real;
- aceita **preço fixo OU preço da semana** (o Mini Salgadinho e o Pão de Queijo raramente mudam —
  ele mesmo disse que ainda está decidindo; então **suporte os dois** e deixe a escolha por item).

Sobre "ser reconhecida no OCR": **não force isso.** O item fixo não deveria depender de aparecer
na tabela da semana. Se aparecer, o app **atualiza o preço** (reusando a chave natural do D12);
se não aparecer, **mantém o que está**. Isso é mais simples e mais confiável que ensinar o OCR.

### N2 🔴 Jornal por SEÇÕES, com quantidade variável
*"vai ficar disposto os itens por seções, sabendo que as seções e a quantidade de itens varia, e
também como fica a formatação pra adaptar pra essa demanda."*

**Proposta de arquitetura (é uma pergunta de projeto, então respondo):** trocar a grade fixa do
Jornal por um **fluxo por seções**.

1. A página tem uma **faixa de conteúdo** (largura e altura conhecidas).
2. As seções vêm ordenadas; cada uma tem um **cabeçalho fino** no estilo do jornal (fio + nome,
   barato em altura vertical — não um bloco).
3. Os itens **fluem** da esquerda para a direita e quebram linha; a coluna é a unidade.
4. O motor calcula a altura necessária: `Σ(seções) [cabeçalho + ceil(itens/colunas) × altura_da_célula]`.
   Se estourar a faixa, ele **degrada em degraus declarados, nesta ordem**:
   (a) sobe o número de colunas (célula mais estreita);
   (b) desce um **degrau de altura** da célula (tamanhos tabelados, nunca contínuos — senão a
   página fica com células de alturas aleatórias);
   (c) **transborda para a página 2**, e avisa.
5. **A última linha de cada seção nunca fica quebrada:** ou as células esticam para preencher a
   largura, ou centralizam. Nunca 5 colunas com 2 células soltas à esquerda.
6. Seção com **1 item** não ganha uma linha inteira: ela compartilha a linha com a seção seguinte,
   ou o cabeçalho fica inline. Decida e registre.

E o estilo da seção tem de ser **do encarte** — as caixas azuis saturadas que apareceram na 2ª
rodada não pertencem a um jornal creme/laranja/verde. No Jornal, seção = fio + versalete, não
retângulo colorido.

### N3 🟠 O "Fica a Dica" é o pior elemento da página
*"ficou simplesmente ridículo de pequeno e ridículo por si só, quando a formatação e colocação."*
Ele é um dos pedidos originais do dono para o Jornal. Redesenhar como **bloco editorial de
verdade**: título, corpo em 2 ou 3 linhas legíveis, largura de coluna de jornal, e posição que
não seja uma tarja fina no rodapé. Se o espaço atual não serve, **mude o espaço** — a arte é
nossa e o gerador é editável.

---

## §6 · A LISTA POR ENCARTE (o que sobra além dos transversais)

| Encarte | Além de V1–V5 e D1–D3 |
|---|---|
| **Terça do Pão** | O Pão Francês tem de **preencher o painel largo inteiro** (é o hero — "fazer do encarte uma obra de arte"); o Sonho+Croissant idem nas duas zonas. Texto pequeno demais. |
| **Segunda dos Frios** | **`Senepal`→`Senepol`** (S1). A pior de todas na disposição: foto ancorada no canto superior-esquerdo de um painel azul enorme; o medalhão dourado **cobre o produto** em várias células. Kit Burger com foto escolhida (N1). |
| **Quarta das Ofertas** | As 3 fixas com foto escolhida (N1) — é o pedido mais explícito dele. Foto grande nas 8. |
| **Quinta do Peixe** | `PESCA DO DIA` e `CORTE NOBRE` viram opcionais (D2) ou saem. |
| **Sexta Verde** | `DIRETO DA GRANJA` / `COLHEITA DA SEMANA` opcionais (D2). Fotos minúsculas — "poderiam chamar mais atenção". **Varrer todos os erros de formatação** desta página e das outras. |
| **Sábado da Carne** | +18 **grande** e com o desenho novo (V4). Preenchimento harmônico do espaço. |
| **Jornal p1/p2** | D1 (Nº/Ano reais), D3 (o período), N2 (seções), N3 (Fica a Dica). Fotos minúsculas. "Um monte de formatações erradas" — varrer. |

---

## §7 · O MÉTODO — laço, com trabalho em massa onde couber

O dono pediu **workflow para trabalho em massa**. Onde ele cabe: os transversais (V1–V5, D2) são
uma passada só que rende nos 7 — faça-os primeiro, **em bloco**, e só depois entre no laço
por encarte. Uma frota lendo os 7 geradores em paralelo para inventariar zonas de foto, rótulos
condicionais e escalas de tipografia é bom uso; **a inspeção visual não se paraleliza** — essa é
sequencial e é olho.

**Ordem sugerida:** V1 (a causa-raiz) → V2 → V4 (o símbolo novo) → V3 → S1 → D2 → D1/D3 → N1 →
N2/N3 → laço por encarte na ordem do dono (Terça, Segunda, Quarta, Quinta, Sexta, Sábado, Jornal).

**Critério de saída, e é dele:** a página tem de parecer feita por um designer, não montada por
um programa. Quando você achar que chegou, gere a galeria com **dados reais** e **pergunte a
ele** — o selo desta rodada continua sendo do Otaviano. Duas rodadas já foram reprovadas; a
terceira só fecha quando ele disser que publicaria.

---

## §9 · O QUINTOU DO REAL — o 8º encarte, e o mais importante (acrescentado 26/07)

**Ele ficou de fora e é justamente o que o dono entrega toda semana.** O README do pacote dizia
*"a Quinta do Real usa a arte já existente do mercado — não está neste pacote"* — e o dono
**colocou depois**, numa pasta própria que ninguém abriu:

```
Templates novos/Quintou/
  Quintou Frente Real.png        1080×1300  ← o PUBLICADO (o padrão-ouro)
  Quintou Frente Fundo.png       1080×1300  ← o fundo LIMPO (a BASE)
  Quintou Frente Exemplo.png     1080×1300
  Quintou Verso Real.png / Fundo / Exemplo   (idem)
  Quintou do Real Frente Preço.png  4500×5418  ← a arte do PREÇO em alta
  Quintou do Real Verso Preço.png   4500×5418
```

Confira também `arte/quintou/` (`ofertas_frente.txt`, `ofertas_verso.txt`,
`frente_referencia.png`) — é o material das fases antigas e ainda vale como dado.

> **Nota de formato:** o Quintou é **1080×1300**, não 1080×1440 como os 7. Isso explica de
> passagem o M-11 do dossiê (o PDF de 285,8×344 mm que eu tinha achado "tamanho arbitrário" —
> é a proporção do Quintou, não um erro).

### 9.1 · A ESPECIFICAÇÃO, lida do `Frente Real.png`

**Estrutura (fica no fundo, não se toca):** o letreiro neon "Quintou Do Real" no topo-esquerdo;
o **painel branco-acinzentado arredondado** no topo-direito; o "B" laranja do carrinho no
rodapé-esquerdo; a parede de tijolo azul.

**Tudo o mais é composição do app** — e isto é a melhor notícia do encarte: o `Fundo` **não tem
nenhuma linha de grade, nenhum contorno de célula.** As divisórias vermelhas que aparecem no
`Real` são **conteúdo**, não fundo. Ou seja: **a grade inteira do Quintou é nossa**, sem
geometria herdada para respeitar. É o encarte mais flexível dos oito.

**A célula do Quintou (o que a torna diferente dos 7):**
1. **Foto grande, recortada, direto sobre o tijolo** — sem painel branco atrás. Os produtos
   quase se tocam e **passam por cima das divisórias vermelhas**. É o V2 no seu estado puro, e é
   o encarte que melhor mostra o que o dono quer dizer com *"preencher todo o vazio"*.
2. **Faixa inferior compartilhada:** nome à **esquerda** (2–3 linhas, branco, corpo pequeno) e
   preço à **direita**.
3. **A forma do preço é uma etiqueta vermelha com listras diagonais brancas nas bordas**, `R$`
   sobrescrito pequeno no topo-esquerdo e o número grande. **É uma FormaPreco nova** —
   `ETIQUETA_LISTRADA`. Use `Quintou do Real Frente Preço.png` (4500×5418) como referência de
   desenho: ela existe justamente para isso.
4. **Grade 4×4 = 16 posições, e a posição 13 (rodapé-esquerdo) é o LOGO**, não produto. Confira
   no `Real`: a última fileira tem 3 produtos e o "B". Logo: **15 slots ocupáveis + 1 reservado.**

### 9.2 · O FICA A DICA vai no painel do topo-direito

Pedido literal: *"O lugar de Fica a Dica do Quintou é no canto superior direito, onde ficava a
logo do mercado, em um espaço levemente branco."*

Confirmei no `Fundo`: **aquele painel está VAZIO na arte limpa** — a logo Belo Brasil que aparece
no `Real` é **conteúdo**, não estrutura. Então o espaço já está reservado e livre.

- Zona aproximada, a **medir com precisão** (diff `Fundo` × `Real`): **x ≈ 568–1080, y ≈ 0–270**
  no espaço 1080×1300, com o canto inferior-esquerdo arredondado.
- Texto escuro sobre o painel claro (é a única área clara da página — contraste fácil).
- **Não é uma tarja fina** (o erro do Jornal, N3): é um bloco com título e 2–3 linhas legíveis.
- **Decisão do dono, pergunte:** o Fica a Dica **substitui** a logo, ou os dois convivem (logo
  menor + dica ao lado)? Renderize as duas e deixe ele apontar.

### 9.3 · As datas, como ele entrega

No `Real`, a validade é **"Até 16/07" girada 90°, em vermelho**, na área do rodapé-esquerdo, ao
lado do "B". Reproduza: papel `VALIDADE`, rotação −90°, vermelho, alimentado pela campanha
(o canal do D7 já existe). **Frente e verso levam a mesma data.**

### 9.4 · O que entregar

**O Quintou pronto como ele entrega toda semana: FRENTE + VERSO**, com as ofertas reais, as fotos
reais recortadas, os preços em etiqueta listrada, a validade girada, e o Fica a Dica no painel.
Ele publica isso semanalmente — é o encarte que tem de ficar perfeito primeiro.

### 9.5 · Como derivar a geometria (método, não chute)

Não existe gerador Python do Quintou (ele veio do Illustrator). Então:

1. **Diff `Fundo` × `Real`** por pixel: tudo que difere é conteúdo. Isso entrega, de graça, os
   bboxes das 15 fotos, das 15 faixas de nome, das 15 etiquetas de preço, da logo e da validade.
2. Cruze com `ofertas_frente.txt` / `ofertas_verso.txt` para saber quantos itens por página.
3. Tabele em `encartes.py` no **mesmo formato dos 7** — o Quintou passa a ser o 8º do pacote,
   com `importar_pacote` reconhecendo a pasta `Quintou/`.
4. **Regra:** nada de coordenada mágica sem comentário. Cada número vem do diff, com o bbox
   medido citado ao lado.

### 9.6 · Ordem de trabalho revisada

O Quintou **entra na frente** do laço por encarte — é o que ele publica:

> V1–V5 e S1 (feitos) → **QUINTOU frente+verso** → D1/D2/D3 → N1 → N2/N3 → laço nos 7 na ordem
> dele (Terça, Segunda, Quarta, Quinta, Sexta, Sábado, Jornal)

Motivo: o Quintou é o único dos oito que já tem um **publicado real** para comparar pixel a
pixel. Ele é a régua mais honesta que existe neste projeto — se o app reproduzir o
`Quintou Frente Real.png` de forma convincente, os outros sete têm um padrão de qualidade
aferido. Comece por ele.

---

## §8 · Nota de método para mim mesmo (arquiteto)

Errei duas vezes nesta frente: selei a 2ª rodada olhando uma imagem, e afirmei que o `SENEPOL`
estava correto por ter greppado só duas grafias. Correções de método, para valer daqui em frente:
**(a)** varredura de string se faz por radical (`Senep*`), nunca por palavra inteira que eu
suponho; **(b)** inspeção visual minha = **todas** as páginas, não uma amostra.

---

# Resposta do builder (Fable) — 27/07/2026

Executada na ordem revisada do §9.6: V1–V5 e S1 (já reportados) → **QUINTOU frente+verso** →
D1/D2/D3 → N1 → N2/N3 → laço com a galeria recomposta. Tudo em L1 (rodada VERMELHA registrada
antes de cada conserto — logs `_d1_vermelho.log`, `_n1_vermelho.log`, `_n2_vermelho.log` em
`saida_f13/`).

## §9 · QUINTOU — frente E verso no pacote (o 8º encarte)

- **Geometria por DIFF, nunca chute** (§9.5): `Fundo × Real` por pixel — frente: grade 4×4,
  célula 270×258 a partir de y=270, colunas x=0/270/540/810, posição 13 = o "B" (estrutura);
  painel topo-direito (588,18,468,226) VAZIO no fundo (a logo é conteúdo); validade a 90° em
  (221,1080,36,192). Verso: as **16 posições** (sem B, sem painel — o neon "Quintou do Real" e o
  "Só Hoje" são arte), validade no **disclaimer do topo** (y 7–41). Cada número no builder tem o
  bbox citado (`encartes.py::_quintou/_quintou_verso`).
- **Forma nova de 1ª classe**: `FormaPreco.ETIQUETA_LISTRADA` (retângulo vermelho + listras
  diagonais brancas recortadas + sombra — a forma do publicado, medida das artes 4500×5418).
- **O peso no nome, como ele publica**: o publicado escreve "Doce de Leite Frimesa Original
  400g" — o canal `nome_com_unidade` passou a ser suprimido também por região **SUBTITULO**
  (compositor.py), então o Quintou (sem subtítulo) ganha o peso no nome e os outros 7 (com
  subtítulo) nunca o duplicam.
- **`importar_pacote` reconhece `Quintou/`** — o teste do pacote atualizado 7→8 com rastro.
- **Régua**: par `quintou-p1/p2.png` app|PUBLICADO na galeria. Sobra declarada: divisórias
  vermelhas finas (ornamento), tipografia do nome (Archivo vs a fonte do Illustrator dele) e a
  data neon vertical "16#07" do verso.
- **As DUAS opções do painel renderizadas** (`quintou-opcoes-painel.png`): B = logo+dica ·
  A = só-dica. **Decisão do dono.**

## §4 · Campos que mudam

- **D1 — a edição é REAL**: `PapelTexto.EDICAO` (condicional: sem dado a região fica MUDA — a
  regra nova do §4 aplicada à letra: o "Nº 177 · ANO 42" cravado morreu do layout);
  `DadosProduto.edicao` + canal de página (o cabeçalho é slot decorativo); campo do PROJETO
  (`ProjetoAberto.edicao`, congela/volta); `sugerir_edicao` (nº incrementa por mês corrido, ANO
  vira com o ano civil; sem base, sem palpite); `registrar_edicao_publicada` no export (realimenta
  a base: o dono digita UMA vez e os meses seguintes se sugerem sozinhos); a recorrência
  (`duplicar_para_evento`) já clona com o número novo — e sem sugestão **limpa** a herdada (nunca
  repetir o Nº antigo calado); pré-voo avisa "sem número" e "já foi publicada" (aviso, nunca
  veto); rótulo clicável na barra da Mesa (espelho da validade). 6 testes.
- **D2 — etiquetas opcionais**: o inventário inteiro (PESCA DO DIA/CORTE NOBRE na Quinta,
  DIRETO DA GRANJA/COLHEITA na Sexta, CORTE DA SEMANA no Sábado, SUPER OFERTA no Jornal) nasce
  **vazio** — vazia não desenha nem a forma (o medalhão oco não existe); varredura PERMANENTE
  no teste (`test_d2_nenhuma_etiqueta_nasce_cravada_no_pacote`).
- **D3 — o período do Jornal**: 3 opções RENDERIZADAS na tipografia real
  (`jornal-opcoes-periodo.png`). **Decisão do dono** (o campo segue editável, F8).

## §5 · As duas features novas

- **N1 — itens fixos**: `Slot.conteudo_fixo` (aditivo, congela COM o template) = produto + foto
  ESCOLHIDA + preço **fixo OU da semana**; o compositor desenha em TODA porta (Mesa, export,
  miniatura, Modo Pai — ponto único); `atualizar_fixos_pela_tabela` por CHAVE NATURAL (D12) roda
  na conciliação — aparece na tabela? atualiza o preço e avisa NOMEADO; não aparece? mantém;
  preço fixo nunca é tocado. **Sem OCR forçado** (§5: "não force isso" — cumprido à letra).
  Diálogo "Itens fixos deste encarte" na paleta da Mesa: lista as fixas, escolhe foto (do acervo
  relativiza; de fora INTERNA em `_fixos/`, I3) e mostra a **prévia na célula real** (a página
  composta recortada no slot). 5 testes.
- **N2 — Jornal por seções em FLUXO**: motor puro `app/rendering/fluxo_jornal.py` com a escada
  DECLARADA do §5: (a) colunas — no Jornal cravadas em **5 pela arte** (réguas contínuas; o
  motor suporta o degrau, o Jornal o declara inexistente), (b) altura tabelada 202→178→156,
  (c) transborda para a página seguinte e avisa; o que não coube em faixa nenhuma é NOMEADO.
  **Decisões registradas**: última linha CENTRALIZA (nunca 2 células soltas à esquerda); seção
  de 1 item compartilha a linha da seguinte com cabeçalho INLINE na largura da célula. Cabeçalho
  = fio + versalete (**`TipoRegiao.FILETE`** novo no motor — lei do tipo novo cumprida: fora do
  ocupável e do pré-voo, testado). A arte foi regenerada (T6): réguas de coluna CONTÍNUAS no
  lugar dos tiques por linha (o look clássico de jornal — valem para qualquer altura), fios de
  linha e divisória 866/1088 removidos. `layout_de_encarte("jornal-do-mes", pacote, secoes=…)`;
  sem `secoes`, o layout estático de sempre (compat total). Página demo com 26 itens REAIS em 6
  seções: `jornal-secoes-p1/p2.png` — degrau 178 em ação, continuação nomeada, Pet inline.
  4 testes de motor.
- **N3 — Fica a Dica editorial**: virou **UM bloco por edição, na página 2** — a caixa da arte
  cresceu (366×88 → 366×114, corpo do app 336×70 em corpo 10 = 3 linhas legíveis; o título é o
  chip verde com o lápis da própria arte) e **a tarja fina da capa MORREU** (gerador editado +
  regenerado; o rodapé da capa ganhou o respiro). Guardião antigo (DICA nas duas páginas)
  INVERTIDO com rastro no docstring.

## Fora da letra, com motivo (L6)

1. **§5.4(a) no Jornal**: o degrau "sobe colunas" existe no MOTOR mas o Jornal o declara
   indisponível — as réguas de coluna são ARTE (5 colunas cravadas). Subir para 6 colunas
   brigaria com a arte regenerada. Se o arquiteto quiser 6 colunas, é regenerar a arte sem
   réguas (1 linha no gerador) e trocar a tupla.
2. **N3 "mude o espaço"**: mantive o bloco na coluna direita do rodapé da p2 (vizinho do
   expediente — onde uma nota editorial mora num jornal), maior; não o movi para o miolo. A
   tarja da capa saiu de vez — se o dono quiser a dica TAMBÉM na capa, é 1 slot de volta.
3. **Placar do pacote 7→8** e **DICA só na p2**: dois guardiões antigos flipados com rastro
   (`test_bloco_f_f13.py`), nunca apagados.

## Ficou de fora, com nome

- Divisórias vermelhas finas do Quintou (frente) e a data neon "16#07" (verso) — ornamento.
- Splash por célula (Óleo Liza), R$ bicolor do Peixe, estrela/rosetas vetoriais — nominais do G
  (herança da BIS).
- UI de EDITAR as seções do Jornal (nomes/ordem/atribuição por item) — o motor, o builder e a
  composição estão prontos; a tela de montagem por seção é trabalho de UI do G (a Mesa hoje
  compõe o Jornal estático; o fluxo entra pela biblioteca/inspeção).
- `sugerir_edicao` assume publicação mensal (é o Jornal do MÊS); campanha quinzenal precisaria
  de regra por evento (config existe, regra não).

## Placares (bancada real, `--timeout=120`, UMA suíte por vez, junit em `saida_f13/`)

- Suíte inteira ×2: **982 verdes / 0 falhas / 0 skips, exit 0** nas duas
  (`bloco_fter_run1.xml` 173s · `bloco_fter_run2.xml` 219s) — 959 da baseline BIS + 23 do TER.
- Ordem invertida: **982/0/0, exit 0** (`bloco_fter_invertida.xml`, 183s).
- Janela real: **4/0/0, exit 0** (`bloco_fter_janela.xml`).
- **Nota honesta das rodadas (L6)**: a 1ª tentativa da rodada 2 morreu no **segfault
  intermitente já NOMEADO no Bloco E** — `0xC0000005` aos 65%, em
  `test_onda1_desempenho.py::test_boot_em_duas_fases_liga_os_sinais` →
  `editor_app._completar_janela` → `almoxarifado.py:64/335 __init__` (construção do
  Almoxarifado com o shell inteiro; stack completo em `bloco_fter_run2.log` da época, incidente
  registrado aqui) — a repetição do MESMO código passou 982/0/0. Mesma família do E (§5.5): a
  caça segue com a ordem própria. Houve também uma 1ª tentativa da rodada 1 invalidada por
  **lock de PNG do Windows** na galeria (`OSError 22` ao regravar `galeria_bloco_f/` — a
  pegadinha já registrada; galeria limpa e rerun verde) e por eu ter deixado a suíte correr
  em paralelo com edições minhas — as rodadas valendo rodaram com a árvore PARADA.
- Achado de bancada novo (L6, virou comentário no código): `QPixmap.fromImage(ImageQt(...))`
  derruba o processo (o QImage emprestado do buffer PIL morre com o objeto) — a prévia do
  diálogo N1 vai por arquivo temporário. E o `regenerar_encartes` filtra por CHAVE
  (`jornal-do-mes`), não pelo nome do gerador — chave errada sai CALADO (me custou uma
  regeneração fantasma; o rastro está nesta resposta).

## A pergunta ao dono (o selo é dele)

1. **Painel do Quintou**: opção **B** (logo + dica) ou **A** (só a dica)?
   → `quintou-opcoes-painel.png`
2. **Período do Jornal**: opção **1**, **2** ou **3**? → `jornal-opcoes-periodo.png`
3. **O Jornal por seções** (`jornal-secoes-p1/p2.png`) está no caminho? (o estático continua
   vivo — os dois formatos existem)
4. **A dica saiu da capa** do Jornal (virou bloco editorial na p2) — aprova?
