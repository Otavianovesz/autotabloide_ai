# ORDEM F13-NONUS — A PRECEDÊNCIA TEM DE SER CÓDIGO, NÃO PROCEDIMENTO

> **Emitida pelo arquiteto em 27/07/2026.** O dono montou a Segunda **sozinho, no app**, e a
> página saiu diferente da que o builder apresentou. Ele mandou as duas lado a lado.
>
> **Achei a causa-raiz e ela é da mesma família do §17 e da QUINQUE:** o que foi apresentado
> como comportamento do programa era, na verdade, um procedimento executado à mão pelo builder.

---

## §1 · A PROVA, em três medições

### 1.1 · O layout no banco dele ESTÁ calibrado — logo, não é o layout

Li o `estrutura_json` do layout id=10 no banco real:

```
celula-2..8   NOME   alt=128px   min_pt=17.0   max_pt=19.0   ← a calibração do C1 CHEGOU
celula-1      NOME   alt= 80px   min_pt= 6.0   max_pt=24.0   ← o KIT ficou de FORA
```

Então a C1 chegou ao banco. **O problema não é o layout — é o que acontece com o texto DELE.**

### 1.2 · O app ELIPSA — e ninguém pode publicar "Leite Condensado…"

`text_fit.py:102` — `_truncar_com_reticencias`, chamada em `:191`. Quando o nome não cabe **no
corpo mínimo**, o motor corta e fecha com `…`.

Na página do dono: `Leite Condensado…`, `Azeite Gallo Extra Virgem Clássico…`,
`Batata Palha Bulnez…`, `Suco de Uva Aurora Tinto…`. **Quatro de sete.**

### 1.3 · Os passos 4 e 5 da minha precedência NÃO EXISTEM EM CÓDIGO

```
grep "def encurtar|descritor_absorve|nome_curto|reduzir_nome" em rendering/ e servico.py
→ (vazio)
```

Na OCTAVUS eu escrevi cinco passos de precedência. Os passos 1, 2 e 3 são do motor
(`tamanho_min_pt`, quebra de linha, a banda de 128px). **Os passos 4 e 5 — "o descritor sai" e
"encurta o NOME pelo descritor" — foram executados À MÃO pelo builder**, item por item, na
tabela do gerador: ele escreveu `"Leite Condensado"` + `"Triangulo · 395 g"` **para aquele
produto específico**.

Por isso a página dele é bonita e a do dono trunca: **a página do builder foi alfaiataria; a do
dono é confecção.** O app não sabe encurtar nome nenhum.

E é o mesmo defeito de sempre, na terceira encarnação:

| Onde | O que foi certificado | O que o dono tinha |
|---|---|---|
| §17 (o marco) | "PRONTO ✓" medindo tempo e bytes | tabloide sem uma foto |
| QUINQUE | galeria linda | app vazio |
| **aqui** | **página com nomes perfeitos** | **quatro nomes truncados** |

---

## §2 · N1 🔴 · A PRECEDÊNCIA VIRA FUNÇÃO — e a elipse morre

**O `…` está PROIBIDO em nome de produto.** Um encarte de preço com "Leite Condensado…" não pode
ser publicado; é pior que feio, é informação incompleta na vitrine.

Implemente a precedência como **função de runtime**, chamada para todo nome, sempre:

```
ajustar_nome(nome, descritor, caixa, corpo_min) →  (nome_final, descritor_final)

1. cabe em 1 linha no corpo_min?          → usa
2. cabe em 2 linhas no corpo_min?         → usa
3. a banda pode crescer (orçamento O1)?   → cresce, a foto cede, volta ao 1
4. tem descritor? RETIRA o descritor      → volta ao 1 com a banda inteira
5. ENCURTA o nome, movendo o excedente para o descritor  → volta ao 1
6. só então, e como último recurso, elipsa — E AVISA no pré-voo
```

### O passo 5 já tem o motor pronto — reuse, não invente (L9)

A sanitização **já decompõe** o nome em `Tipo + Marca + Sabor + Peso`
(`ai/enriquecimento.py`, `core/sanitize.py` — é decisão travada do projeto desde a fundação).
Então o encurtamento é **mecânico**, não heurístico:

| Nome completo | Nome curto | Descritor |
|---|---|---|
| Leite Condensado Triangulo 395g | **Leite Condensado** | Triangulo · 395 g |
| Azeite Gallo Extra Virgem Clássico 500ml | **Azeite Gallo** | extra virgem clássico · 500 ml |
| Batata Palha Bulnez Crocante 100g | **Batata Palha Bulnez** | crocante · 100 g |
| Suco de Uva Aurora Tinto TP 1,5L | **Suco de Uva Aurora** | tinto · 1,5 L |

Regra de corte: **Tipo é intocável; Marca sai depois; Sabor e Peso vão sempre ao descritor
primeiro.** Nunca cortar palavra, nunca abreviar.
*(E isto resolve de graça o `TP` que ficou pendente na SEPTIMUS §3.)*

**Teste:** para os 8 itens da tabela real dele, provar que **nenhum nome sai com `…`** e que cada
descritor recebeu o que foi tirado do nome. Mais um teste adversarial com um nome absurdamente
longo (60+ caracteres) provando que a cadeia degrada até o passo 5 e **ainda** não elipsa.

---

## §3 · N2 🟠 · O KIT FICOU FORA DA CALIBRAÇÃO

`celula-1` (a fixa) tem `min_pt=6.0` — o default inerte — enquanto as outras oito têm 17.0.
Isso significa que o nome do Kit **pode encolher até 6pt** se o dono trocar por um produto de nome
longo. Hoje não aparece porque "Kit Burguer Senepol BBX" cabe.

Calibre a fixa como as demais, **e varra as outras sete páginas** procurando o mesmo esquecimento —
onde houver `min_pt=6.0` numa região de nome, a calibração passou por cima.

---

## §4 · N3 🟠 · OS BADGES DO EDITOR ESTÃO NA PÁGINA DELE

Na imagem do dono aparecem, dentro das células, `¶ Livre` no lugar dos chips `Nº 02..Nº 08`, e
`📅 Validade` no selo em vez de `27/07`.

Rastreei: são os **badges do RG-57** — `papel_texto_ui.py:59` (`PapelTexto.LIVRE: "Livre"`) e
`itens.py:138` (`_paint_badge_papel`). Eles vivem **só no `RegiaoItem` do canvas Qt**; o
`compositor.py` não os conhece. São uma ajuda de **edição**, correta no Ateliê.

**Conclusão: ele está olhando o canvas do editor, não a página composta.** Isso levanta três
perguntas que você precisa responder com arquivo e linha:

1. **A Mesa pinta badges?** Se o canvas da Mesa herda o `RegiaoItem` do Ateliê, o dono vê marcação
   de edição no lugar onde deveria ver o resultado. Se for isso, os badges são **do Ateliê apenas**.
2. **Existe alguma porta que exporte a partir do canvas** (captura da cena) em vez de
   `compor_pagina`? Se existir, ela sai com badge — e é uma **quarta receita de montagem**.
   Se existir, mate-a.
3. **Como ele chegou nessa imagem?** Descubra o caminho e conserte o caminho, não o sintoma.
   Se for só o preview da Mesa, então a Mesa precisa de um **"Ver como vai sair"** que mostra a
   composição real — hoje ele não tem como ver a página final sem exportar.

---

## §5 · A LIÇÃO, e ela é minha também

**Regra escrita em prosa que o builder cumpre à mão não é conserto — é demonstração.**

Eu escrevi cinco passos de precedência em português e aceitei uma página bonita como prova de que
eles funcionavam. Deveria ter perguntado a única pergunta que importa: *"isto é uma função ou foi
você que fez?"* — e a resposta estava a um grep de distância.

**Vira lei da fase (L11):** *toda regra de comportamento que eu escrever em prosa tem de terminar
numa função nomeada, chamada pelo caminho de produção, com teste que a exercita com dado NOVO —
não com o dado do exemplo.* Se a regra só existe na cabeça de quem executou, ela não existe.

E o teste de aceitação de qualquer regra dessas passa a ser: **rodar com a tabela da semana
seguinte**, que ninguém alfaiatou.

---

## §6 · ORDEM DE ATAQUE

1. **N1** — a precedência como função, a elipse proibida em nome de produto. É o que quebra a
   página dele **hoje**.
2. **N3** — descobrir o caminho pelo qual ele viu badges, e fechar esse caminho.
3. **N2** — a calibração da fixa e a varredura dos `min_pt=6.0`.
4. Recompor a Segunda **com a tabela dele**, pelo caminho **dele** (Ateliê → Mesa → importar →
   auto-preencher), e mandar a página.

**E a prova desta rodada não é uma página que você montou.** É o dono abrir o app, importar a
tabela e a página sair certa. Se você precisar tocar em qualquer dado à mão para ela ficar boa,
**o conserto não está pronto.**


---

# Resposta do builder (Fable) — 27/07/2026

Na ordem do §6: N1 → N3 → N2 → F1/F2 do ROTEIRO → a Segunda pelo caminho DELE. A acusação do
§1.3 estava certa e eu a confirmo sem ressalva: os passos 4 e 5 só existiam nas minhas mãos.
Agora são código, e a prova de aceitação da ordem rodou: **a página saiu do caminho do dono,
com os nomes DO BANCO DELE (que ninguém alfaiatou), sem uma reticência.**

## N1 — a precedência é uma função (`app/rendering/nome_fit.py::precedencia_do_nome`)

Chamada pelo compositor **para toda célula, em toda porta** (o ponto único do laço de
`compor_pagina` — `compositor.py`, antes do desenho das regiões, com cópia do dado por
`dataclasses.replace`; o modelo nunca muda, I1). Os 6 passos como a ordem escreveu:

1–2. cabe no corpo mínimo (1 ou N linhas — quem manda é a caixa)? usa;
3. a banda CRESCE e a foto CEDE **em runtime** (rects substitutos por uid, só nesta
   composição), dentro do orçamento O1 — a foto nunca desce de 55% da altura útil;
4. o descritor SAI e o nome usa a banda inteira;
5. o nome ENCURTA pelo fim, token a token, **sempre inteiro e sempre preservado no
   descritor** (nada se perde — I2); o peso desce primeiro (`sanitize.separar_peso`, nova
   função PÚBLICA — L9, a lógica de produção mora na produção);
6. só então elipsa — e a flag `elipsa` acusa: a **revisora/pré-voo usam a MESMA cadeia**
   (`revisora._heuristicas` reescrita; de quebra caiu o furo do `sem_hifen` que ela não
   passava — apontado pelo scout).

**De graça, a C2 fechou NO MOTOR:** célula com região de descritor faz o peso do fim do nome
migrar SEMPRE (e deduplica — o "Italac 200g"+"200g" do caminho real morreu); o `TP` da
SEPTIMUS §3 resolvido conforme a TABELA da ordem (sigla de embalagem descartada).

**Divergências declaradas (L6):**
- A decomposição "Tipo+Marca+Sabor+Peso" completa **não existe determinística** no código
  (`sanitize.py:19-26` avisa; sabor só vem do LM — `enriquecimento.py:292-320`; marca só de
  lista conhecida — `aprendizado.py:30-46`). A escada mecânica pelo FIM do nome reproduz os 4
  exemplos da ordem porque a ordem travada põe sabor/peso no fim — é o mesmo efeito, sem
  heurística frágil.
- O descritor preserva a CAIXA original dos tokens movidos ("Triângulo · 395 g",
  "Crocante · 100 g") — os exemplos da ordem têm sabor minúsculo, mas distinguir sabor de
  marca em runtime exigiria a decomposição que não há; Title Case nunca erra o nome próprio.

**Testes** (`test_f13_nonus.py`): os 4 itens-mostra na célula real sem "…" e sem perda
(igualdade de tokens); o caso cravado "Leite Condensado Triangulo 395g" → "Leite Condensado"
+ "Triangulo · 395 g"; adversarial de 60+ caracteres degradando até o 5 sem elipsar; célula
SEM descritor não move nada (I2 — o Quintou intacto por teste); o passo 3 com régua (foto
≥55% após ceder); dedupe do peso; e a **prova-mestra**: a página composta com o dado CRU sai
**BYTE-IDÊNTICA** à composta com o dado alfaiatado do OCTAVUS — a confecção alcançou a
alfaiataria, que é a definição inteira do conserto.

## N3 — as três respostas, com arquivo e linha

1. **A Mesa pintava badges? SIM.** A Mesa usa o MESMO `EditorCanvas` do Ateliê
   (`mesa.py:257` ← `canvas.py:2425`), e `RegiaoItem._paint_badge_papel` (**`app/qt/itens.py:138`**
   — correção factual: não existe `design/itens.py`) pinta o badge em TODO TEXTO_LEGAL com
   tamanho constante NA TELA (`itens.py:150`, `alt=14/esc`) — no zoom de página inteira ele
   ENGOLE o chip de 52×20px. Era exatamente o "¶ Livre"/"📅 Validade" da foto. **Conserto:**
   `CanvasView.badges_de_papel` (default True); a Mesa desliga — o badge é ajuda de edição DO
   LAYOUT e ficou sendo só do Ateliê. Teste por TINTA (flag ligada pinta, desligada cala).
2. **Porta que exporta do canvas? NÃO EXISTE.** Grep `scene.render/grab/grabWidget` em
   app/qt: só a animação de transição (`animacoes.py:434`) e ícone SVG (`icones.py:152`).
   As 8 portas de página passam por `compor_pagina` (Mesa `mesa.py:2755`, perfis, publicar,
   Fábrica ×2, relâmpago/kit, Modo Pai, miniatura) — nenhuma 4ª receita para matar.
3. **Como ele chegou na imagem:** olhando o canvas da Mesa (a tela de edição) — e ele NÃO
   TINHA como ver a página final sem exportar (a única prévia rasterizada morava na barra do
   EDITOR, `barra_editor.py:298`). **Conserto: o botão " Ver como vai sair" na barra da Mesa**
   (`mesa.py::_ver_como_vai_sair`) — mesma receita de todas as portas
   (`paginas_compostas()` → diálogo com a imagem), badge nenhum porque badge não existe no
   compositor. Teste por CONTEÚDO: o diálogo exibe exatamente a imagem que a receita devolveu.

## N2 — o piso inerte morreu nas 8 páginas

A varredura do scout mediu: das ~90 regiões NOME dos 8 encartes, só 7 (Segunda) tinham piso;
**as 6 fixas com NOME, todas em 6.0** — e o teste do C1 não as via porque itera `ocupaveis`,
que EXCLUI fixa (o mesmo furo da regra, no teste). Conserto na FÁBRICA das regiões: o helper
`_nome` agora tem piso por padrão (`tam−3`: o corpo cede no máximo UM degrau — depois a
precedência do N1 encurta, nunca encolhe a ilegível) e `_sub` ganhou piso `tam−1,5`. A fixa
da Segunda foi de 6.0 → 21 (tam 24−3; a régua relativa é MAIS dura que o ≥17 pedido). Guarda
nova no motor: `ajustar_texto` clampa piso≤teto (o ramo do truncamento desenharia ACIMA do
teto). Teste de varredura das 8 páginas (fixas INCLUÍDAS, grade E fluxo do Jornal):
piso >6.0, ≤teto, ≥teto−3 — régua com FAIXA, como a lição da SEPTIMUS manda.

## F1/F2 do ROTEIRO

**Correção factual ao ROTEIRO (L6):** o esconderijo era PIOR — desde a F13/C13 o **Ctrl+K é a
busca global** (projetos/produtos/layouts, sem ações — `paleta_comandos.py:221-258`); a paleta
de AÇÕES da Mesa é **Ctrl+Shift+P** (`atalhos.py:36`, `mesa.py:746-753`). O dono seguindo o
ROTEIRO apertaria Ctrl+K e não acharia NADA. Anotei a correção no próprio ROTEIRO.

**F1 — três portas novas para os fixos:** (1) botão direito NA CÉLULA FIXA → "Conteúdo fixo
desta célula…" (`itens.py::montar_menu_contexto`, fio `canvas.ao_itens_fixos` no molde do
override — só aparece na fixa e só na Mesa; teste com os 3 lados: fixa oferece, livre não,
Ateliê não); (2) **o "···" da barra virou PERMANENTE** com as ações de projeto sem botão
próprio — "Itens fixos deste encarte…" mora lá SEMPRE (guardião da fase 6 virado com rastro:
antes o "···" sumia quando tudo cabia); (3) a paleta mantém a entrada. **As ações só-paleta
NOMEADAS (sem consertar, como a ordem manda):** além dos fixos, ficaram sem porta visível:
"Encher a página atual", "Exportar como RASCUNHO", "Exportar em perfis/lote", "Revisar com a
IA", "Montar pelo texto", "Publicar", "O que mudou desde a última edição", "Exportar o
checklist em PDF", "Sugerir variações para agrupar" — 9 ao todo (as 3 da ordem + 6 extras).

**F2 — o teste do caminho inteiro** (`test_f2_o_caminho_inteiro_do_dono_por_gesto`): Ateliê
REAL ligado à Mesa REAL pelo fio do `editor_app`, duplo-clique de GESTO na lista, tabela
CRUA pela colagem, o ConciliacaoDialog REAL fechado por clique, `btn_preencher` clicado,
salvar pelo diálogo real, REABERTO noutra Mesa — prova por conteúdo: mapa por uid 7/7,
fixa fora, o Kit no template com 39,00. *Achado de bancada declarado:* o `vigia_dialogo`
clica UMA vez por caixa; se o botão está momentaneamente desabilitado, o teste pendura — o
F2 usa um vigia local que RETENTA (candidato a melhoria da fixture, nomeado, não consertado).

## §6.4 — a Segunda pelo caminho DELE, na raiz REAL

`app/scripts/segunda_pelo_caminho_do_dono.py` (backup `core_pre_nonus_20260727.db` antes):
dirige a MESA DE VERDADE — layout do BANCO (o Kit fixo real com foto internada e 39,00),
as 8 linhas CRUAS da tabela (as mesmas do teste S1), conciliação REAL, diálogo fechado por
clique, `btn_preencher`, projeto NOVO salvo (**id=8 "Segunda 27/07 — caminho do dono"** —
o id=7 do dono intacto), página composta pela receita do export. **Zero dado alfaiatado** —
e dois gestos de CURADORIA do dono, declarados: a linha do Kit IGNORADA (ele já é fixo) e
cadastro-sem-foto para vermelhos (não precisou: **os 7 produtos JÁ EXISTIAM no banco dele e
casaram VERDE com FOTO**). O resultado é a prova do N1 em dado selvagem: os nomes DO ACERVO
("Creme de Leite Italac **TP** 200g", "Leite Integral Parmalat **L.V.** 1L", "Leite
Condensado **Triângulo** 395g" — com acento) saíram **sem uma reticência**: TP descartado,
pesos no descritor, "Leite Condensado / Triângulo · 395 g" decidido pela função, não por mim.
Página: `saida_f13/galeria_f13_bis/segunda-2707-caminho-do-dono.png`.

## O que fica aberto, com nome

1. **O preço-da-semana do fixo só bebe da tabela se o item estiver NA ESTANTE**
   (`mesa.py` passa `self._itens` a `atualizar_fixos_pela_tabela`) — a linha do Kit é
   vermelha/ignorada no fluxo real, então o preço do fixo não atualiza pelo import da Mesa.
   Hoje não dói (o 39,00 está gravado no template); numa semana com preço novo do Kit, dói.
2. O item da estante que já vive numa FIXA: se o dono cadastrar a linha do Kit, o
   auto-preencher o colocaria também numa célula livre (duplicado). Ligado ao aberto 1.
3. A melhoria do `vigia_dialogo` (retentar clique em botão desabilitado).
4. Os 8 sem-porta restantes do F1 (nomeados acima).
5. Os abertos herdados (rollout do orçamento nas outras 5, sobras SEXTUS §5, decisões do
   dono: painel A×B, período, dica na célula 13).

## Placares (junit `bloco_fnonus_*`)

**Suíte 1016 ×2 zero skips exit-0** (1003 + os 13 da NONUS; runs 1 e 2);
**invertida 1016/0/0**; **janela real 4/0/0** — as quatro DE PRIMEIRA, sem incidente.

