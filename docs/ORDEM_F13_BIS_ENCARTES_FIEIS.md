# ORDEM F13-BIS — ENCARTES FIÉIS (o Bloco F reprovado na inspeção do dono)

> **Emitida pelo arquiteto em 26/07/2026, revogando o §9 do selo do Bloco F.**
> O dono olhou a galeria e reprovou: *"está completamente tosco… não correspondeu em nada ao
> modelo… amador e horrível."* Ele está certo, e eu selei rápido demais. Este documento é a
> reprovação com endereço, e ele **substitui** a definição de pronto do Bloco F.
>
> **Executor: Fable.** Método: **laço de inspeção** (§4) — não é "faça a lista e feche".

---

## §1 · O DIAGNÓSTICO-RAIZ: a extração pegou a caixa e jogou fora o desenho

Olhei cinco das oito páginas comparadas lado a lado. O defeito é **um só**, e explica todos os
sintomas de todos os encartes:

**Cada célula dos geradores não é um retângulo — é um TEMPLATE.** Dentro dela existem, com
coordenadas próprias: a zona da foto, a zona do nome, uma **linha de subtítulo**, a **forma do
preço** (que é diferente em cada encarte), rótulos decorativos e tipografia por zona.

O `layout_de_encarte` extraiu **só o retângulo externo** e o preencheu com o trio genérico do app
(IMAGEM + NOME + PREÇO), desenhando o preço como **texto preto corrido**. Resultado: os sete
encartes — que têm sete identidades visuais distintas — saem todos como **a mesma grade genérica**.

É por isso que parece amador. Não é acabamento: é a identidade do encarte ausente.

### A prova, por encarte (o que o modelo tem × o que o app desenhou)

| Encarte | A forma do preço no modelo | O que o app desenhou |
|---|---|---|
| Segunda dos Frios | **medalhão estrelado dourado** no canto da célula | `R$` numa linha, número noutra, em preto, colidindo com o nome |
| Terça do Pão | **etiqueta pendurada** integrada ao toldo da barraca | pílula branca lisa com texto preto, por cima do toldo |
| Quarta das Ofertas | **tag laranja arredondada** + pílula verde `20% off` | texto branco solto; o `-34%` como texto cru |
| Quinta do Peixe | medalhão/disco (a conferir na 6ª imagem) | idem genérico |
| Sexta Verde | **tag vermelha arredondada** no rodapé da célula; **oval branco** nos dois heróis | texto preto nas nove; o oval só nos heróis |
| Sábado da Carne | **etiqueta vermelha** com `R$` sobrescrito, levemente girada | texto preto centralizado sob o nome |
| Jornal do Mês | **tag laranja arredondada** em todas as 20+ células | texto preto sob o nome |

**Sete formas de preço no desenho. Uma no app: texto preto.**

---

## §2 · OS SEIS DEFEITOS TRANSVERSAIS (valem para os 7 — consertar aqui rende em tudo)

### T1 🔴 A forma do preço não existe como conceito
Criar `FormaPreco` de primeira classe (`model.py`) e desenhá-la no compositor:
`MEDALHAO_ESTRELA` · `ETIQUETA_PENDURADA` · `TAG_ARREDONDADA` · `OVAL` · `PILULA` ·
`ETIQUETA_GIRADA` · `TEXTO` (o atual, que passa a ser exceção, não regra).
Cada forma leva: cor de fundo, cor do texto, raio, rotação, tamanho do `R$` sobrescrito, e
âncora dentro da célula. Os valores saem dos geradores, **não** de defaults.

### T2 🔴 A linha de SUBTÍTULO não existe
Todo modelo tem duas linhas por item: nome + descritor (`senepol · marca própria · 100 g`,
`integral · lata 380 g`, `bandeja 30 unidades`, `cremoso · 200 g`). O app tem uma. Precisa de um
papel de texto novo — `SUBTITULO` — alimentado pelo descritor do produto (marca/sabor/peso/
observação), com tipografia própria (itálico menor), **abaixo** do nome e nunca colidindo.

### T3 🔴 A foto não preenche a zona da foto
Em todos os encartes o modelo tem a foto ocupando ~55-60% do topo da célula. O app coloca a
imagem num quadrado pequeno, às vezes ao lado do nome (Sexta, Quarta), invertendo o layout
interno. A zona da foto tem de vir do gerador, com o `Ajuste` correto, e a imagem tem de
**preencher** essa zona.

### T4 🟠 Os rótulos decorativos por célula foram perdidos
`Nº 03` (Segunda), `LOTE Nº 04` (Sexta), `★ DIRETO DA GRANJA ★` e `★ COLHEITA DA SEMANA ★`
(Sexta, heróis), `★ O CORTE DA SEMANA ★` em fita vermelha (Sábado), `SUPER OFERTA` em estrela
verde (Jornal), `FOTO DE CAPA — …` (Jornal). Nenhum aparece. Uns são estrutura (vão para o BASE),
outros são camada de conteúdo — **decidir um por um** e registrar a decisão.

### T5 🟠 A hifenização está destruindo os nomes na arte real
Visível na Quarta e na Sexta: `ABOBORA PAULISTA LIS-TRADA`, `CERVEJA ITAPA-VA`,
`FRANGO MAROM-BI`, `COPO AMERICA-NO`, `ABOBORA JACA-REZINHO`. É o R-04 do dossiê, agora com
prova de artefato. Nas células estreitas destes encartes, **hifenizar tem de ser o último
recurso** — antes disso: reduzir corpo, usar o descritor para tirar peso do nome, e permitir
`sem_hifen` por região.

### T6 🔴 As correções do F8 NÃO chegaram ao produto
As BASE.png ainda carregam as strings velhas, e isso está **visível nas duas metades da
galeria**: `CRIADA E PRODUZIDA PELO BELO BRASIL` (Segunda e Sábado), `SENEPOL MARCA PRÓPRIA`
(Sábado), `O MÊS INTEIRO DE PREÇO BAIXO` (Jornal p1 e p2). Você corrigiu os `.py` e declarou a
regeração fora de escopo — **ela volta para dentro do escopo**: sem regenerar, o dono publica a
arte errada na segunda-feira. Pipeline no README do pacote (Playwright + Chromium).

---

## §3 · A LISTA POR ENCARTE

### 3.1 · TERÇA DO PÃO
1. **Célula fixa 1 (Pão Francês):** a foto tem de ocupar o painel largo; hoje é um quadradinho
   e o nome sai em corpo minúsculo no canto. O nome vai em serifa grande, centralizado.
2. **Célula fixa 2 (Sonho + Croissant):** são **duas** zonas de foto com o `+` entre elas; o app
   pôs dois quadrados sem respeitar as duas zonas nem o `+`.
3. **Falta a linha manuscrita** `metade de preço, é hoje!★` (Caveat) na célula do hero.
4. **As 4 células de baixo:** o preço é uma **etiqueta pendurada no toldo**, não uma pílula
   branca solta; hoje ela flutua sobre a listra do toldo.
5. Nome em caixa alta e sem descritor → T2.
6. Validade: o selo do topo recebe `dd/mm`; hoje escreve `OFERTA VÁLIDA 25/05` (mês errado, ver T7).

### 3.2 · SEGUNDA DOS FRIOS E LATICÍNIOS
1. **O medalhão estrelado dourado do preço não existe.** É o elemento de identidade do encarte.
2. **`R$` órfão numa linha e o número noutra**, atravessando a borda da célula. Some com o
   `R$` separado — ele é parte da forma.
3. **Nome sobre a barra azul-escura em caixa alta**, colidindo com o preço. No modelo é painel
   claro, serifa, centralizado, com o descritor abaixo.
4. **Os rótulos `Nº 03…Nº 08` desapareceram** (T4).
5. **A célula fixa do Kit Burger saiu sem preço** — o `24,90` do modelo não foi desenhado.
6. `CRIADA E PRODUZIDA` ainda no fundo (T6).

### 3.3 · QUARTA DAS OFERTAS
1. **O selo de data está VAZIO** — a caixa preta existe, `29/07` não foi escrito. Defeito
   funcional, não de estilo.
2. **Tag laranja arredondada** ausente; preço em texto branco solto.
3. **O `-34%` calculado sai como texto cru**; no modelo é **pílula verde** `20% off`. O cálculo
   funciona (mérito seu) — falta a forma.
4. **As 3 células fixas** (Mini Salgadinho, Pão de Queijo, Lanche na Chapa) receberam produtos
   aleatórios. Se o preenchimento rotativo é opção do teste, **a página de inspeção real
   (COND-11) tem de mostrá-las com o conteúdo fixo**.
5. Hifenização (T5) em duas células.
6. A célula grande do Bombom: foto pequena centralizada num painel enorme (T3).

### 3.4 · QUINTA DO PEIXE
Aplicar T1–T6 e conferir na inspeção: as duas células **wide** 590×320 têm a foto à direita
(`x+w−286`) e o texto à esquerda — layout interno próprio que o app precisa honrar.

### 3.5 · SEXTA VERDE
1. **O layout interno da célula está INVERTIDO**: o modelo é foto em cima / nome embaixo /
   tag no rodapé-direito; o app fez foto à esquerda / nome à direita / preço embaixo.
2. **Tag vermelha arredondada** ausente nas 9 células.
3. **`LOTE Nº 01…09` desapareceram** (T4).
4. **Os dois heróis perderam `★ DIRETO DA GRANJA ★` e `★ COLHEITA DA SEMANA ★`.**
5. Hifenização feia em 4 de 9 nomes (T5).
6. O descritor real (`unidade`, `kg`, `bandeja 30 unidades`) virou `100 g` em tudo (T2).

### 3.6 · SÁBADO DA CARNE
1. **A etiqueta vermelha girada do preço** ausente → texto preto centralizado.
2. **O masonry não é respeitado**: o modelo tem coluna 1 com 4 células curtas (`H_S=166`) e as
   colunas 2 e 3 com 3 altas (`H_T=228`); o app fez 3×4 quase iguais.
3. **`★ O CORTE DA SEMANA ★` saiu como texto simples** sobreposto ao nome; no modelo é fita
   vermelha acima do nome, dentro da célula.
4. **O selo `+18` não apareceu** na cerveja. É **decisão travada do projeto** ("selo +18
   automático SEMPRE em bebida alcoólica"). Provar na página real da COND-11.
5. `SENEPOL MARCA PRÓPRIA` e `CRIADA E PRODUZIDA` ainda no fundo (T6).

### 3.7 · JORNAL DO MÊS (p1 e p2)
1. **O hero foi destruído:** o modelo tem painel de foto no terço esquerdo + legenda
   `FOTO DE CAPA — …` + **estrela verde `SUPER OFERTA`** + 4 células 2×2 à direita. O app pôs um
   quadrado gigante com o preço **solto no canto superior**, fora de qualquer forma.
2. **As caixas azuis das SEÇÕES estão sendo desenhadas na arte** — retângulo azul saturado com
   a etiqueta `Mercearia` sobre um jornal creme/laranja/verde. Visualmente alienígena. A seção
   precisa de estilo por encarte (ou ficar desligada no Jornal).
3. **A linha legal do rodapé virou um toco:** o modelo tem
   `OFERTAS VÁLIDAS DE 01/08 A 27/08/2026 OU ENQUANTO DURAREM OS ESTOQUES · IMAGENS MERAMENTE
   ILUSTRATIVAS · (66) 9969-4009 · (66) 3419-1405`; o app escreveu `OFERTA VÁLIDA ATÉ 26/05`.
4. **`FICA A DICA` continua vazio** — era um dos pedidos originais do dono para o Jornal.
5. **`O MÊS INTEIRO` ainda no fundo** (T6) — tinha de virar período editável.
6. Tag laranja ausente nas 20+ células (T1); descritor ausente (T2).

### 3.8 · T7 · A VALIDADE ESTÁ EM MAIO NAS OITO PÁGINAS
`25/05`, `26/05` — o M-02 do dossiê, vivo. O dado da campanha carrega a data velha e o app a
renderiza fielmente. O conserto é o **H2** (pré-voo recusando validade fora do mês corrente),
mas registre aqui: **nenhuma das oito páginas passaria numa conferência de balcão.**

---

## §4 · O LAÇO DE INSPEÇÃO (o método deste bloco)

Não é "faça a lista e feche". É laço, e o olho do dono é o portão.

```
para cada encarte, na ordem: Terça · Segunda · Quarta · Sexta · Sábado · Quinta · Jornal
  1. consertar os itens do §3 daquele encarte + os transversais que o alcançam
  2. compor com DADOS REAIS (COND-11: foto do acervo, nome sanitizado sem .upper(),
     de/por reais, células fixas com o conteúdo fixo, validade da semana)
  3. gerar o par lado a lado (app | PREVIEW) na galeria
  4. OLHAR. Escrever, por página, o que ainda difere do modelo — em português de dono,
     não em jargão ("o preço não tem a medalha", não "FormaPreco ausente")
  5. se a lista do passo 4 não estiver vazia → volta ao 1
  6. só então passa ao encarte seguinte
```

**Critério de saída de cada encarte:** você consegue escrever, com honestidade,
*"a diferença que sobra entre o meu e o modelo é X, e X é aceitável porque Y"* — e o X não pode
ser nenhum item do §2 nem do §3.

**Critério de saída do bloco:** as 7 páginas (8 imagens) numa galeria só, com dados reais, e uma
frase por página. Aí o Otaviano olha. **O selo é dele, não meu** — eu já errei uma vez
aceitando geometria no lugar de produto.

---

## §5 · O que eu errei, para o registro

Selei o Bloco F olhando **uma** imagem e aceitando a explicação de que a galeria era "aparato de
geometria". A explicação era verdadeira e **irrelevante**: a lei da inspeção visual existe desde
o §17 justamente para responder *"o dono publicaria isto?"*, e eu deixei passar um artefato que
não respondia. O dono respondeu por mim, em uma frase, e estava certo.

A lição vira regra: **quando a definição de pronto disser "inspeção visual", o artefato inspecionado
tem de ser o que o dono publicaria — dados reais, caminho real, sem fixture no meio.** Aparato de
geometria é teste; não é inspeção.

---

*A COND-11 do §9.4 do selo do F fica absorvida aqui: ela era a metade certa da resposta errada.*

---

## RESPOSTA DO BUILDER — F13-BIS (Fable 5, 26/07/2026)

O laço do §4 rodou completo: **Terça → Segunda → Quarta → Sexta →
Sábado → Quinta → Jornal (p1+p2)**, cada encarte com consertar →
compor com dados REAIS → par lado a lado → OLHAR → lista em português
→ repetir. A galeria final está em `saida_f13/galeria_f13_bis/` com a
frase por página em `LEITURA_DO_LACO.md` — **o selo é do Otaviano**.

### Os transversais (§2), no motor

| # | o que ficou | onde |
|---|---|---|
| T1 | `FormaPreco` de 1ª classe — **8 formas** (as 7 da ordem + `CARIMBO`, extensão declarada: o scout provou que o Jornal usa uma 8ª — borda perfurada sem fundo). O texto vive no PALCO da forma (centrado nela e coubível na tinta — o 1º desenho deixou o texto FORA do medalhão e a bancada pegou por imagem); `centavos_na_base` (só a Quarta sobrescreve; selos/discos/bandeiras usam UMA baseline, a espec dos geradores); TEXTO_LEGAL também veste forma (o "-XX%" calculado na pílula laranja) | `model.py`, `compositor.py` |
| T2 | `TipoRegiao.SUBTITULO` + `DadosProduto.descritor` + a montagem OFICIAL compõe o descritor do que o item carrega (a lei do tipo novo aplicada: slot só-subtítulo NÃO é ocupável — testado) | `model.py`, `compositor.py`, `servico.py`, `grade.py` (nada a mudar — provado) |
| T5 | `sem_hifen` por região: a palavra NUNCA parte — o CORPO cede (busca binária); no fundo do poço, as reticências do R-045. TODO nome/subtítulo dos encartes nasce `sem_hifen` — `ABOBORA PAULISTA LIS-TRADA` morreu | `text_fit.py`, `model.py`, `encartes.py` |
| T6 | **a regeração VOLTOU ao escopo e RODOU**: `app/scripts/regenerar_encartes.py` — Playwright+Chromium (instalados nesta máquina: pip + chromium, declarado) com as fontes por `@font-face` base64 (o sistema do dono intocado); **calibração na Terça: 0,24% de pixels ≠ >24** (anti-alias) vs o original; os **16 PNGs** (8 BASE + 8 PREVIEW) regenerados — `CRIADA E PRODUZIDA`, `SENEPOL MARCA PRÓPRIA` e `O MÊS INTEIRO` **saíram do produto** (sobram SÓ nos `*-CURVAS.svg`, que são material de Illustrator gerado por Inkscape — não instalado, não usado pela composição; nominal) | `regenerar_encartes.py` (novo), `Templates novos/artes/*` (acervo do dono, fora do git) |
| T3/T4 | zonas internas refeitas por encarte com a espec EXATA do scout (fotos, âncoras, cores hex, corpos em pt); rótulos decorativos decididos UM A UM (chips Nº = conteúdo desenhado; LOTE = estrutura, não duplicado; ★-rótulos = conteúdo; selos 50%/25% da Terça = estrutura, o app não escreve % por cima) | `encartes.py` |
| T7 | a validade de MAIO morreu nas 8 páginas — a inspeção compõe com a validade da SEMANA do pacote (27/07 → 01/08; Jornal 01–27/08/2026 com a LINHA LEGAL COMPLETA) | `inspecao_encartes.py` (novo) |

### Três correções factuais CONTRA a ordem (L6 — conferidas no gerador E no PREVIEW)

1. **§3.5.1 (Sexta):** o modelo é foto à ESQUERDA / texto à direita /
   tag no rodapé — a ordem pedia "foto em cima"; segui o modelo.
2. **§3.6.3 (Sábado):** não existe fita vermelha atrás do "CORTE DA
   SEMANA" — é texto DOURADO `#A8801F` + roseta; segui o modelo.
3. **§3.4 (Quinta):** a forma do preço do Peixe é TEXTO tipografado
   puro (navy, sem fundo) — a única `TEXTO` legítima do pacote.

### COND-11 — a página que o dono publicaria

`app/scripts/inspecao_encartes.py`: fotos REAIS de
`AutoTabloide_System_Root/biblioteca_imagens/` (58 fotos 1000×1000
RGBA), nomes sanitizados SEM caixa alta, preços do banco/campanha,
células fixas com o conteúdo FIXO, `mais18` real (o +18 automático
PROVADO na página do Sábado e na p2 do Jornal — decisão travada).
Buraco honesto do acervo, declarado página a página: não há foto de
hortifrúti (Sexta), pescado (Quinta), padaria fresca/hambúrguer
(Terça/Segunda) — essas páginas saíram com os produtos REAIS mais
próximos do banco, nunca com fotos inventadas.

### O que ficou de fora (com nome)

- a estrela vetorial ★ e as rosetas/adornos a path dos exemplos (as
  fontes do pacote não têm o glifo; o compositor não desenha paths de
  adorno) — sobras declaradas nas frases;
- o splash por célula da grade (o Óleo Liza da p2) e o "O KIT" do selo
  do hero da Segunda — nominais para o G;
- o R$ dourado do Peixe (o preço tem UMA cor no motor) — nominal;
- os `*-CURVAS.svg` com strings velhas (pipeline Inkscape, fora da
  composição) — nominais;
- estilo de SEÇÃO por encarte (o Jornal ficou com seções DESLIGADAS,
  §3.7.2 — o contorno padrão era alienígena; o teste do F foi
  INVERTIDO com a justificativa no docstring).

### Placares (junit em `saida_f13/`)

| prova | resultado |
|---|---|
| baseline (pré-BIS) | **946/0/0, zero skips, exit 0** (`bloco_fbis_baseline.xml`) |
| suíte da raiz ×2 | **959 verdes ×2, 0 falhas, 0 skips, exit 0** (`bloco_fbis_suite_1/2.xml`) |
| ordem invertida | **959/0/0, exit 0** (`bloco_fbis_invertida.xml`) |
| janela real | **4/0/0** (`bloco_fbis_janela.xml`) |

Evolução: 946 → **959** (os 13 do BIS). Todas as rodadas de primeira —
sem flake e sem segfault, a segunda bancada limpa seguida desde que o
LM real saiu do pytest.

**PARADO no fim do F-BIS. A galeria + LEITURA_DO_LACO.md aguardam o
olho do OTAVIANO — o selo é dele.**
