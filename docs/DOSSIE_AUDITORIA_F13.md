# DOSSIÊ DE AUDITORIA F13 — "o programa está uma bomba"

> **Status: DIAGNÓSTICO. Nenhuma linha de código foi alterada.**
> Emitido pelo arquiteto (Cowork) em 24/07/2026, a pedido do dono.
> Consome: gravação `Recording_20260724_1840.mht` (131 capturas, 18:37–18:39) + narração
> do dono (~2.500 palavras) + leitura da fonte real no disco (`app/`, 67.491 linhas).
> Método: 12 agentes de auditoria em paralelo, cada um lendo a fonte de uma frente,
> mais verificação manual do arquiteto nos pontos em que dois agentes discordaram.
>
> **Regra desta fase (ordem do dono, 24/07): NÃO CONSERTAR NADA.** Este documento
> cataloga. A ordem de serviço nasce depois, quando o dono mandar.
> Frente paralela: `docs/BRIEFING_VARREDURA_CODE.md` (o que o Code varre).

---

## §0 · O veredito em dez linhas

1. **A suíte não mede o programa.** 832 testes, **zero** `QTest.mouseClick`, **zero**
   `.trigger()` de menu, **uma** única `sendEvent` em toda a bancada. Ela prova que o
   *modelo de dados* não se corrompe; nada do que o dono toca com o mouse é testado.
   Tudo que ele encontrou em 3 minutos mora exatamente nesse ponto cego. **Este é o
   achado-mãe** — enquanto ele existir, "849 verdes" e "o programa é uma bomba" vão
   continuar sendo verdade ao mesmo tempo.
2. **A tela que escurece é um bug de 1 linha** (`animacoes.py:287`) que nunca foi
   testado porque o filtro que o causa (`instalar_vida`) nunca é instalado na bancada.
3. **O "tudo grudado" é comportamento determinístico, não intermitência:** toda região
   nova herda o slot da região anterior porque a criação auto-seleciona (`canvas.py:1396`).
4. **"Subir/Descer camada" está invertido** — o app faz o oposto do que o tooltip
   promete (`painel_camadas.py:67-72`). É por isso que "a imagem atrás do preço" nunca
   aconteceu, apesar de ser possível.
5. **Rotacionar desliga o redimensionar de propósito** (`itens.py:438`), e a alternativa
   prometida no comentário ("tamanho pelo painel") **não existe** — não há campo de
   largura/altura em `painel_propriedades.py`.
6. **A sanitização apaga palavra do nome do produto** (`enriquecimento.py:144-151`), e
   o aviso disso só aparece num caminho que o modo rápido do dono não passa.
7. **A categorização só roda para item NOVO** (`servico.py:1635`). Item já cadastrado
   sem categoria fica "Outros" para sempre, importação após importação.
8. **Etiqueta em lote sai sem selo +18 mesmo em bebida alcoólica** (`servico.py:1858`) —
   violação de decisão travada, silenciosa, e o pré-voo não pega.
9. **O alinhamento vertical de texto não existe no modelo** (`compositor.py:312` é uma
   linha incondicional). Não é bug de UI: é campo ausente.
10. **Alembic está morto** (pasta só com `.pyc`), a migração de schema é `ADD COLUMN`
    sem downgrade, e há 3 mecanismos de exclusão de produto concorrentes.

**O que NÃO está quebrado** (verificado, para o dono não gastar tempo aí): o cartaz sai
no mm exato (erro <0,03 mm); o % de desconto é calculado e blindado contra divisão por
zero; o 2-em-1 está mesmo contido no cartaz, com teste-guarda; a impressão respeita mm
e orientação; o MP4 é opcional de verdade; preview e exportação chamam o **mesmo**
`compor_pagina` — não há divergência tela↔arquivo; o boot já foi consertado (2.307 ms → 510 ms).

---

## §1 · O achado-mãe: por que 849 verdes convivem com isto

| Medida | Número real | Fonte |
|---|---|---|
| Arquivos de teste | 81 (19.939 linhas) | `app/tests/` |
| `def test_` | 832 | varredura |
| `QTest.mouseClick` / `keyClick` | **0** | varredura |
| `.trigger()` em QAction | **0** | varredura |
| `.click()` em botão real | **2** | `test_isolamento.py:201`, `test_multi_imagem.py:142` |
| `QApplication.sendEvent` | **1** | `test_isolamento.py:231` |
| `dropEvent` / `QMimeData` (drag real) | **0** | varredura |
| Módulos com zero teste | **18** | inclui `barra_editor.py` (408 linhas, a barra do editor) |

**T-01 🔴 · A bancada roda `QT_QPA_PLATFORM=offscreen` fixo** (`conftest.py:9`), na máquina
real inclusive. Sem compositing: hit-test, foco de janela, popup, tooltip e DPI ficam
fora por construção. O canvas — o coração do produto — nunca é testado com um clique real.

**T-02 🔴 · `instalar_vida()` (véu/hover/animação) tem 0 chamadas em `app/tests/`.** Todo
o comportamento visual que o dono relatou como quebrado está, por decisão explícita,
fora da bancada. `instalar_polimento` idem — `polimento.py:10-11` documenta a exclusão.

**T-03 🔴 · `confirmar_pre_voo` — o portão do I2 ("nunca em silêncio") — é monkeypatchado
em TODO teste que o alcança** (`test_fase8_export.py:338,474`; `test_os_f11_5.py:107,595,782`;
`test_bloco_d_etapa_a.py:100`). O `QMessageBox` real nunca roda. Isso explica por que
ninguém notou que "Exportar mesmo assim" torna o pré-voo dispensável com 1 clique.

**T-04 🟠 · O OCR nunca é testado com foto de verdade.** `test_ocr_pipeline.py:29-33`
usa `Image.new("RGB",(1200,1600),"white")` e um motor fake que ignora o pixel. E há uma
foto REAL de tabela de ofertas no repositório — `app/tests/fixtures/jornal_belo_brasil.jpeg` —
**que nenhum teste referencia** (só a versão `.txt` é usada).

**T-05 🟠 · Testes que provam a função, não o gesto.** `test_f54.py:23-29` chama
`v.duplicar_regiao(...)` direto — não prova que `itens.py:512` (o item de menu) está
ligado. Todo teste de "soltar imagem" chama `soltar_imagem` direto
(`test_os_f11_5.py:333,338`), pulando o parsing de MIME e o `acceptProposedAction`.

**T-06 🟠 · A própria suíte documenta o mascaramento e não o propagou.**
`test_isolamento.py:206-213` conta que testar `keyPressEvent` direto **mascarou um bug
real de foco** (Tab roubado); o conserto (`sendEvent`) ficou nesse único ponto, e o
padrão antigo segue em ~830 lugares.

**T-07 🟡 · Asserções vazias.** `test_f54.py:69-73`: `assert e.barra is not None` — as 408
linhas de `barra_editor.py` não são conferidas por conteúdo em lugar nenhum.

**T-08 🟡 · 3 `skipif` dependem de `Path("arte/quintou")` RELATIVO ao CWD do pytest.**
Rodar de outra pasta silencia os testes da arte real sem avisar — o que o CLAUDE.md
proíbe ("skip silencioso não é verde").

**T-09 🟡 · O caminho COM GPU (SDXL, degrau 2 do Estúdio) não tem teste nenhum.**

**T-10 🔵 · O adversarial é bom onde alcança.** `test_adversarial_vinculo.py` amostra
pixel de verdade (`_cor_no_slot:77-82`) e cobre I1–I5 com assert vizinho. Mas todo
`mapa` slot→uid nasce em Python puro; nunca passa pelo `CanvasView` com drag real. Ele
prova a integridade do modelo, não a interação que **gera** o modelo.

> **Consequência prática:** qualquer conserto desta auditoria que seja validado só pela
> suíte atual voltará a quebrar. A mudança de metodologia de teste é pré-requisito, não
> item opcional. Ver §7.

---

## §2 · FRENTE V — a tela que escurece e não volta

Sintoma do dono: *"ele começa a escurecer quando abre uma janela e vai escurecendo. Aí eu
tenho que abrir e fechar o programa."* Evidência: capturas 042, 065, 069, 072, 079, 087 —
janela inteira (barra + painéis + canvas) sob véu preto. A cor bate exatamente com
`VEU_DIALOGO = rgba(0,0,0,120)` do tema escuro (`tokens.py:119`) — **não** é o
`OverlayOcupado` nem o véu de isolamento do canvas.

**V-01 🔴 CONFIRMADO · O `destroyed` remove do dicionário mas não destrói o véu.**
`animacoes.py:287`:
```python
dlg.destroyed.connect(lambda _=None, d=id(dlg): _veus.pop(d, None))
```
Quem realmente esconde é `_remover_veu` (310-315), acionado pelo evento `Hide` (171-172).
Mas `~QWidget` **não emite `QEvent::Hide`** ao destruir um widget visível. Se o `QDialog`
morrer sem passar por `hide()`/`close()` — pai destruído por baixo, `deleteLater()` explícito,
exceção no meio do fluxo — a entrada é removida do mapa e o véu vira **widget órfão,
visível, opaco, filho da janela, para sempre**. Nada no app consegue removê-lo depois.
*Verificado pessoalmente pelo arquiteto lendo `animacoes.py:275-315` — um dos 12 agentes
afirmou o contrário ("é limpo via destroyed.connect"); o agente estava errado, e o erro
é instrutivo: à leitura rápida a linha parece uma limpeza.*

**V-02 🟠 · A chave é `id(dlg)`** (`animacoes.py:160,275,285,287`) — endereço CPython,
reciclável pelo GC. Não é o gatilho, mas **amplifica o V-01**: uma entrada órfã nunca
removida pode coincidir com o id de um diálogo novo, e então `id(dlg) not in _veus`
falha — o diálogo novo não ganha véu, e o vazamento fica *mascarado* em vez de sinalizado.
Mesmo padrão em `_hovers` (`animacoes.py:191,207`).

**V-03 🟡 · O véu não acompanha resize.** `veu.setGeometry(pai.rect())` (`:284`) roda só
na criação; não há `eventFilter` de Resize no pai. Compare com o padrão correto ao lado:
`OverlayOcupado` trata Resize (`carregando.py:185-192`).

**V-04 🔵 · `BoasVindasDialog.open()`** (`boas_vindas.py:169`) é o único diálogo do app
que usa `.open()` não-bloqueante com referência local solta — o mais frágil em tese.

**V-05 🔴 · Zero cobertura.** Nenhum teste lê `_veus`, chama `instalar_vida`, ou verifica
`findChildren(QWidget, "veuDialogo")`. Ver T-02.

> Nota de diagnóstico: o dono associou o escurecimento ao spinbox de rotação (captura 042).
> `painel_propriedades.py:212` **não abre diálogo nenhum** — é um `QDoubleSpinBox` cru. O
> gatilho real foi um diálogo *anterior* (Modelos de célula / Pré-voo) cujo véu já havia
> ficado órfão. Ele só notou no controle seguinte. Isso importa para o conserto: procurar
> o bug no painel de propriedades seria caça errada.

---

## §3 · FRENTE E — o editor: "tudo grudado", "não sei agrupar", "não sei carimbar"

**O mecanismo, em uma frase:** `Slot.regioes` (`model.py:274-276`) **é** a célula. Toda
região na mesma lista é irmã por definição — move junto, seleciona junto. Os 5 sintomas
são consequência de regiões acabarem no mesmo slot sem o dono ter pedido.

**E-01 🔴 CONFIRMADO · Toda região nova herda o slot da anterior.**
`_slot_para_novas_regioes()` (`canvas.py:1346-1367`): com seleção ativa, usa o slot da
região selecionada. E `adicionar_regiao()` (`canvas.py:1369-1399`) **sempre auto-seleciona
a região que acabou de criar** (`:1396-1397`). Sequência do dono: criar IMAGEM (nada
selecionado → slot novo, imagem fica selecionada) → criar TEXTO (imagem ainda
selecionada → texto cai no MESMO slot) → grudado. **Determinístico**, bate com "toda vez
a mesma coisa".

**E-02 🔴 · O arrasto em grupo não checa se o dono agrupou.** `_irmas()` (`itens.py:309-315`)
só verifica `it.regiao in slot.regioes`. Em `_selecao_por_clique` (`itens.py:324-373`), o
1º clique sem modificador seleciona todas as irmãs (`:372-373`) e o Qt arrasta a seleção
inteira. Dispara para QUALQUER par que compartilhe slot — inclusive o par acidental do E-01.

**E-03 🟠 · "Duplicar" nunca duplica a célula, só a peça.** Três caminhos convergem no
mesmo alvo único: menu de contexto (`itens.py:512`, a região literalmente clicada) e
Ctrl+D (`editor.py:176-179` → `canvas.selecionada()`, que devolve a *primária* por design
do RG-55). `duplicar_regiao` (`canvas.py:1937-1959`) clona só esse `Regiao`. Bate com a
captura 055: só "Imagem" virou "Imagem cópia". A UI destaca o trio (sugerindo "isto é uma
coisa só") e o comando ignora a seleção múltipla — **a promessa visual mente**.

**E-04 🟠 · "Carimbar no layout" funciona e é invisível.** `DialogoModelos._carimbar()`
(`modelos_dialog.py:93-98`) chama `carimbar_modelo(modelo)` sem caixa-alvo;
`carimbar_modelo` (`canvas.py:1571-1593`) tem default `x=0,y=0,larg=layout.largura_mm,
alt=layout.altura_mm` — **o trio nasce do tamanho da PÁGINA INTEIRA**. E, diferente de
`adicionar_regiao`/`duplicar_regiao`/`colar`, ela **nunca chama `setSelected`** nas
regiões novas (compare `:1583-1593` com `:1396-1397`): nenhuma alça, nenhum destaque.
Um contorno tracejado do tamanho exato da página se confunde com a borda da arte.
O teste `test_fase5_editor.py:536-545` prova que as 3 regiões SÃO criadas — o bug é 100%
de visibilidade. *Ou seja: o dono carimbou várias vezes e cada carimbo cobriu a página.*

**E-05 🟠 · "Agrupar como replicável" recusa em bloco, sem explicar.**
`agrupar_selecao()` (`canvas.py:652-694`) exige TODAS as regiões no MESMO slot (`:665-669`)
e todas em `TIPOS_CONTEUDO` (`grade.py:331-332`). Dado o E-01, é fácil ter 2 de 3 peças
num slot e a 3ª em outro; a recusa é total e o dono lê como "um item ficou de fora".
Não há toast de sucesso quando funciona (`canvas.py:688-694`) — só o tutorial, e só na 1ª vez.

**E-06 🔴 · "Novo layout" nasce com regiões que o dono não pediu — culpa de um detector
ingênuo.** `_novo()` (`atelie.py:212-242`) → `layout_grade_de_arte` (`grade.py:378-405`)
→ `detectar_caixas_preco` (`grade.py:201-219`): heurística de cor pura (vermelho>150,
verde/azul<90), ignora só os 30% do topo (`cabecalho_frac=0.3`, número mágico sem UI),
**sem filtro de área mínima nem de proporção**. Qualquer elemento vermelho abaixo do
cabeçalho — faixa "OFERTA", linha fina, ornamento — vira uma "caixa" e ganha 3 regiões
(`montar_slot_celula`, `grade.py:222-243`), sem limite de quantidade. O layout é **salvo
no banco antes de qualquer preview** (`atelie.py:236-239`); não existe diálogo para
revisar/aceitar a grade detectada nem opção "tabloide sem grade".

**E-07 🟠 · "Editar layout" mostra o mesmo lixo — não é migração inventando.**
`carregar_layout` (`persistencia.py:127-140`) só desserializa; `migrar_papeis_texto_dict`
(`migracao.py:41-52`) apenas rotula TEXTO_LEGAL existente, não cria região. A causa é o
E-06. E `adicionar_pagina_de_arte` (`grade.py:348-375`) reusa o mesmo detector — o
problema se repete a cada página nova.

**E-08 🔴 · Rotacionar desliga o resize de propósito, e a alternativa não existe.**
`itens.py:438`:
```python
if not self.regiao.travado and not (self.regiao.rotacao_graus % 360):
```
Com rotação ≠ 0 a condição é falsa → `super().mousePressEvent()` (`:446`) → `self._resize`
fica `None` → `mouseMoveEvent` (`:456`) cai em mover puro. O comentário (`:436-437`) diz
"tamanho pelo painel". **Varredura completa de `painel_propriedades.py` (86-307, todo
`addRow`/`QDoubleSpinBox`): existe Rotação (212-219, 271) e NÃO existe Largura nem
Altura.** Hoje, rotacionar uma região a deixa sem nenhum caminho de redimensionar.
*Ironia técnica: o hit-test já funcionaria girado — `event.pos()` chega em coordenadas
locais, o Qt já desfez a rotação (`_handle_em`, `:429-433`; `hoverMoveEvent`, `:414-425`
até mostra o cursor diagonal certo sobre a alça girada). O que quebraria é a conta do
resize, que usa `event.scenePos()` cru e `mapToScene` (`:443`) — matemática alinhada ao
eixo da cena, válida só em rotação 0. A guarda esconde a conta errada em vez de corrigi-la.*

**E-09 🟡 · Selos: existe âncora, não existe controle.** `TipoRegiao.SELO` é adicionável
pela barra (`barra_editor.py:117`), mas a região é **só uma âncora de posição**
(`_ancora_selos_slot`, `compositor.py:542-551`, prioridade SELO>IMAGEM>página). Ela não
desenha nada nem escolhe qual selo. Quem liga o selo são as flags do produto
(`mais18`/`marca_propria`) marcadas no **Almoxarifado** (`almoxarifado.py:401-402`), e
canto/arte/liga-desliga ficam em **Configurações** (`configuracoes.py:2094-2194`) — três
telas distantes. `painel_propriedades.py:487-505`: com uma região SELO selecionada, o
painel esconde grp_preco/grp_img/grp_leg e sobra só "Rótulo" e "Rotação" — **nenhum campo
de selo**. Pior: o produto de exemplo do Ateliê (`atelie.py:54-55`) nunca tem
`mais18`/`marca_propria`, então **nenhum selo aparece na prévia mesmo fazendo tudo certo**.
Isso explica literalmente "todos deveriam ter um selo, não tá dando certo, não sei por quê".

**E-10 🟠 · Selo criado sem seleção prévia nunca propaga.** Adicionar selo sem antes
selecionar uma região da célula-mestre cria slot avulso (E-01) → `_apos_edicao` só
propaga se `slot.mestre` (`canvas.py:1108-1120`) → o selo fica numa célula só, **sem aviso**.

**E-11 🟠 · A célula-mestre não propaga o texto.** `ATRIBUTOS_ESTILO` (`grade.py:40-50`)
propaga fonte, tamanhos, cor, alinhamento, subtipo/papel, moeda, riscado, ajuste, estilo,
rotação, máscara, pill, sombra, papel_texto — e geometria à parte. **Não propaga
`texto_fixo`** (nem `nome`, `visivel`, `travado`): editar o texto da "Fica a Dica" na
mestra não muda as cópias, só o estilo. Feedback: um toast ao *selecionar* a mestra
(`canvas.py:769-784`), nada depois de editar nem ao salvar. É a "tag inteligente que não funciona".

**E-12 🟡 · Salvar no Ateliê pode falhar sem dizer nada.** `salvar()` (`editor.py:295-319`)
não tem `try/except` no commit — erro de E/S sobe cru; `if layout is None: return`
(`:297-298`) sai mudo. `recarregar`/`_editar` (`atelie.py:162-177,310-313`) também sem
proteção: um layout com ids duplicados (barrado só na leitura por `validar_ids_unicos`,
`model.py:388-406`) **quebra a biblioteca inteira ao abrir o Ateliê**.

**E-13 🔵 · Lógica porca do Ateliê.** `except Exception: pass` em `atelie.py:200`
(miniatura falha → ícone genérico, sem log) e `atelie.py:231-232` (engole a exceção real
da detecção e sempre diz "sem grade detectada"). Mensagem sem sentido "Grade detectada:
0 células." (`atelie.py:230`).

---

## §4 · FRENTE R — o motor de composição

**R-01 🔴 · Alinhamento vertical de texto NÃO EXISTE no modelo.** `Alinhamento`
(`model.py:64-68`) só tem ESQUERDA/CENTRO/DIREITA/JUSTIFICADO — todos horizontais, usados
em `_x_alinhado` (`compositor.py:160-165`). O Y vem de **uma linha incondicional**:
```python
oy = y + max(0, (rh - total_h) // 2)   # compositor.py:312
```
sem `if`, sem campo. O preço repete em `:419` (SEPARADO) e `:380` (COMPLETO riscado). A
dataclass `Regiao` (`model.py:111-191`) não tem `valinhar`/`ancora_vertical`, e o painel
não tem um segundo combo (`painel_propriedades.py:103-105`). **Não é bug de UI: é campo
ausente no modelo.** O pedido do dono ("mais pra cima, mais pra baixo, centralizado")
exige enum novo + `_y_alinhado` + combo.

**R-02 🔴 · "Subir" e "Descer" camada estão INVERTIDOS.** `painel_camadas.py:67-72`:
"Subir / Trazer para a frente" chama `_mover(-1)`; "Descer / Levar para trás" chama
`_mover(1)`. Em `mover_regiao` (`canvas.py:1185-1196`), `j=i+delta` troca a posição **na
lista**. Como o Pillow pinta em sequência sobre o mesmo `base` (`compositor.py:654-655`),
**quem vem DEPOIS fica visualmente NA FRENTE**. Logo "Subir" empurra para trás e "Descer"
empurra para a frente. Agravante: região nova nasce no FIM da lista
(`canvas.py:1391,1091,1952`), então uma foto colada depois do nome/preço **já nasce na
frente deles**, e "Descer" a empurra ainda mais para a frente.
> **Esta é a resposta para "a imagem fica atrás do preço — falei um monte de vezes e nunca
> vi acontecer".** É possível hoje: `compor_pagina` respeita a ordem da lista, não há
> hardcode por tipo. O que existe é um controle que faz o oposto do que promete.

**R-03 🟠 · `Ajuste.PREENCHER` vaza da célula no caminho mais comum.** Há dois caminhos.
O lento (`_imagem_enquadrada`, `compositor.py:210-226`) cria uma tela do tamanho exato da
região antes de colar — corta certo. O **rápido** — usado sempre que há 1 imagem sem
máscara e sem zoom/foco custom, isto é, o caso padrão — faz
`escala = max(rw/img.width, rh/img.height)` (`:252-253`) e cola **direto na página inteira**
(`:258`), **sem recortar para o tamanho da região**. Como PREENCHER por definição estoura
uma dimensão, a imagem pinta por cima das células vizinhas, sem aviso. *"Ajuste preencher…
não sei se deu certo aqui o negócio" — não deu.*

**R-04 🟠 · "Bauduc-co": hifenização genérica de pt-BR aplicada a nome de marca.**
`pyphen.Pyphen(lang="pt_BR")` (`text_fit.py:20`) aplica padrões fonéticos a QUALQUER
palavra, inclusive marca estrangeira/inventada. Em `_quebrar_linhas` (`:71-83`) a única
guarda é `p<2 or len(palavra)-p<2` (`:74`) — 2 letras de cada lado, nada sobre soar bem —
e o laço escolhe o MAIOR ponto que ainda cabe (`:73-79`): guloso, não bonito.
`_quebrar_palavra` (`:31-56`) nem tem a guarda de 2 letras e cai em corte
caractere-a-caractere (`:43-48`). Não existe "não hifenizar esta região" nem "largura
mínima do prefixo" no modelo nem no painel.

**R-05 🟠 · Não existe "encher o espaço".** `ajustar_texto` só REDUZ a fonte, nunca cresce
além do teto `tamanho_max_pt` (`text_fit.py:4,156-159`) — texto curto em caixa grande fica
pequeno e sobra vazio. Imagem usa `Ajuste.CONTER` por padrão (`model.py:159`) — letterbox
por definição. Trocar para PREENCHER esbarra no R-03. *"Tá muito vazio o jornal, podia
preencher mais o espaço" — não há autoscale-up em lugar nenhum.*

**R-06 🟠 VIOLA I2 · Fundo ausente vira página BRANCA em silêncio** (`compositor.py:611-617`).
E fundo com tamanho diferente do w×h calculado é **esticado sem preservar proporção nem
avisar** (`:613-615`).

**R-07 🟠 VIOLA I2 · Imagem de produto ausente é pulada em silêncio:**
`if not e.caminho or not Path(e.caminho).exists(): continue` (`compositor.py:183-184`).

**R-08 🟡 · `except Exception:` genérico engole erro do banco de selos** —
`_selos_do_produto` (`compositor.py:512-519`) cai num `cfg={...}` default sem log nem aviso.

**R-09 🟡 · Números mágicos inconsistentes no preço riscado:** posição do traço `0.62` no
COMPLETO (`compositor.py:382`) vs `0.32` no SEPARADO (`:431`), calculados de referências
diferentes (topo vs baseline). Nada garante a mesma altura visual entre os dois subtipos.

**R-10 🟡 VIOLA I1 · `_dados_do_slot` ainda aceita lista posicional "legado"**
(`compositor.py:584-591`) — contradiz "identidade, nunca posição" se algum chamador
passar lista em vez de dict.

**R-11 🔵 · Selos ficam num passe fixo sempre por último** (`compositor.py:470,657-660`),
fora do z-order do usuário. Intencional, mas indocumentado na UI.

---

## §5 · FRENTE P — pré-voo, validade e o RASCUNHO eterno

**P-01 🔴 · "Texto Legal sem data": o dono preencheu o campo errado, e o app não tem como
ele saber.** O pré-voo (`servico.py:1516-1518`) avisa quando uma região `TEXTO_LEGAL` com
`papel_texto=VALIDADE` produz `texto_composto_legal` vazio (`compositor.py:101-122`), que
lê **só** `dados.texto_legal`. Esse campo vem de `dados_para_desenho(..., validade)`
(`servico.py:660-699`), e `validade` é `self._validade` **da Mesa** (`mesa.py:2259-2261`).
Isso é um campo **completamente separado** do "Validade" por item (`it.validade`,
`servico.py:45`), que só gera um selo "perto de vencer" (`servico.py:679-681`).
> Preencher a Validade no Almoxarifado (`almoxarifado.py:460`) **não** preenche isso.
> Criar a região "Validade da oferta" no Ateliê (`papel_texto_ui.py:23,38`) **não** preenche isso.

**P-02 🔴 · A única UI que preenche é indetectável.** Um `QLabel` minúsculo na barra da
Mesa, que **nasce vazio** e só ganha texto depois de definido (`mesa.py:149-157,409-410`).
Sem placeholder convidando o clique; só tooltip no hover. Clicar abre 2 `QInputDialog`
(`mesa.py:395-414`).

**P-03 🟠 · A automação existe e está desligada do export.** `sugerir_validade(evento)`
(`servico.py:1171-1201`) roda **só** dentro de `_salvar_projeto` (`mesa.py:836-842`) —
**nunca** em `_exportar` (`mesa.py:2400`). E exige um "Evento" com regra manual em Config
ou `dia_semana` cadastrado. O OCR até preenche `self._validade` ao conciliar, se ainda
estiver vazio (`mesa.py:1050-1054`).

**P-04 🟠 · O calendário do varejo tem a data exata e ninguém liga o fio.**
`datas_do_ano()` (`calendario.py:44-67`) tem as 9 datas calculadas (Páscoa por Gauss,
`:17-28`). `criar_evento_comemorativo` (`:98-114`) grava só nome+cor (`eventos.py:104-119`),
e o modelo `Evento` (`models.py:228-244`) **não tem campo de data fixa anual**, só
`dia_semana` semanal. É exatamente o "tem lógica aqui que existe mas não está aplicada".

**P-05 🔴 · A aprovação é praticamente inalcançável.** `MesaTela.esta_aprovado()`
(`mesa.py:2375-2381`) exige `self._salvo` **e** `projetos.esta_aprovado()`
(`projetos.py:591-613`), que compara sha256 do estado atual com o hash salvo na aprovação
(`:616-635`). Qualquer edição derruba `_salvo` na hora — **inclusive editar a validade**,
que chama `_marcar_salvo(False)` (`mesa.py:411`). E salvar de novo com conteúdo diferente
**apaga a aprovação sozinho** (`projetos.py:299-308`), sem aviso na tela.

**P-06 🔴 · O botão "Aprovar" só existe na paleta Ctrl+K** (`mesa.py:1396-1397`). Nenhum
botão ou menu visível na barra. *"Não sei nem onde marca isso" está literalmente correto.*

**P-07 🔴 · A Fábrica (cartaz) não tem NENHUMA ação de aprovar** — grep vazio em
`fabrica.py`. O teste que prova a marca no cartaz (`test_fase8_export.py:460-499`) faz
monkeypatch em `servico.pode_exportar_limpo` **porque não existe caminho de UI real**.
**Todo cartaz de gôndola está estruturalmente preso ao RASCUNHO.**

**P-08 · Inventário das 9 portas de exportação que carimbam RASCUNHO:**

| # | Porta | Linha |
|---|---|---|
| 1 | Mesa / tabloide | `mesa.py:2411,2429-2430` |
| 2 | Exportar por perfis (lote) | `exportar_dialog.py:113-115` |
| 3 | Fábrica / cartaz PDF | `fabrica.py:663-665,727` |
| 4 | Etiquetas em lote | `fabrica.py:690-694` |
| 5 | Impressão direta | `fabrica.py:761` |
| 6 | Modo Pai | `modo_pai.py:271,280-281` |
| 7 | Publicar / social | `publicar_dialog.py:57-89,332` |
| 8 | Cartaz-relâmpago | `servico.py:1827` — sempre rascunho, hardcoded |
| 9 | Kit ponta-de-gôndola | `servico.py:1901,1907` — idem |

**P-09 🟠 · RG-58 ("a validade nunca fica vazia") é uma reivindicação FALSA.**
`confirmar_pre_voo` (`prevoo.py:13-29`) **sempre** oferece "…mesmo assim" (AcceptRole) —
1 clique ignora qualquer pendência. `_completo` (`fabrica.py:479-482`) não exige validade
para o cartaz entrar em "prontos", e `fabrica.py:201` rotula o campo como opcional. Dá
para exportar cartaz com rodapé de validade em branco.

**P-10 🟠 · "Recuperar rascunho?" aparece em projeto já salvo e pronto.** O timer
`_salvar_rascunho_bg` (`mesa.py:1324-1338`) roda a cada ~2 min **sem checar se algo mudou**,
sem checar `_congelado` (projeto aberto só para reimprimir, `mesa.py:933`) e sem checar se
já exportou — só `if not self._itens: return` (`:1327`). Só "Salvar projeto" limpa
(`descartar_rascunhos()`, `mesa.py:859-860`); fechar o app só **para** o timer
(`closeEvent`, `:711-713`) sem apagar nada; exportar (`:2459-2469`) também não limpa.
Deixar um projeto pronto aberto por 2 minutos gera um rascunho idêntico, oferecido na
próxima abertura. *Risco de perda ao clicar "No": nenhum — `descartar_rascunhos()`
(`rascunho.py:124-127`) só mexe em `rascunhos/`, nunca em `projetos/<uuid>/`. Mas o texto
do diálogo (`mesa.py:1356-1361`) não diz isso.*

---

## §6 · FRENTE C — categorização e Mesa: por que tudo é "Outros"

**C-01 🔴 · A categorização só roda para item NOVO.** `conciliar_linhas`
(`servico.py:1590-1638`) dá o semáforo; só o VERMELHO passa por `enriquecer_descricao`
(`servico.py:2080-2107`), disparado em fila ao abrir o diálogo (`conciliacao_dialog.py:183-212`),
e `finalizar_criacao` (`servico.py:2271-2293`) persiste via `_garantir_categoria`
(`repositories.py:104,154`). Para VERDE/AMARELO, `conciliar_linhas` **só lê** o que já
está no registro (`servico.py:1635-1636`). **Produto já cadastrado sem categoria nunca é
recategorizado** — reimportação após reimportação, fica "Outros" para sempre.
Fontes de produto sem categoria: migração do protótipo antigo (`migracao_antiga.py:126-127`,
carrega o campo cru do banco velho) e criação com LM Studio desligado.

**C-02 🟠 · Furo secundário: "Corrigir nomes (IA)" descarta a categoria calculada.**
`enriquecer_banco.py:54-64`: o `if` da linha 55 governa o dict inteiro — só grava se o
**nome** ou o **+18** também mudaram. Nome já certo ⇒ categoria computada é jogada fora
em silêncio.

**C-03 🔴 · Não existe piso determinístico sem IA.** `_degradado()`
(`enriquecimento.py:238-248`) devolve o produto sem tocar `categoria` (fica `None`) quando
`motor.disponivel()` é `False`. Sem LM Studio, nada é categorizado. *O desenho existe ao
lado e não foi reusado: `SINONIMOS_REGIONAIS_PADRAO` + Config (`aprendizado.py:22-27`) e
`marcas_do_acervo()` (`servico.py:2054-2077`) já são exatamente o padrão "dicionário
padrão + o que o dono confirmou".*

**C-04 · Medição real.** Consulta (só leitura) a `AutoTabloide_System_Root/banco/core.db`:
**40/40 produtos com `categoria_id`** (39 "ia", 1 "humano"). O mecanismo do caminho
vermelho funciona; o ponto cego do C-01 é estrutural e aparece em acervo mais velho/migrado.
> O painel que mede isso já existe e o dono não sabe: **Inteligência → saúde do acervo**
> (`inteligencia.py:264,276`, campo `pct_categoria`, meta 80% em `METAS_SAUDE:282`).

**C-05 🟡 · "Agrupar por categoria" e "Seções" refletem o banco fielmente.**
`ordenar_por_categoria` (`servico.py:1084-1107`) joga sem-categoria em `OUTROS`
(`servico.py:744`), sempre por último; `chk_agrupar` (`mesa.py:2303-2314`) reordena e liga
`pag.secoes_ligadas=True` (`:2322`) → contorno por categoria (`compositor.py:623`). **Não
é bug de agrupamento** — é o C-01 aparecendo na tela.

**C-06 🟠 · Auto-preencher é `zip` posicional puro.** `_auto_preencher_miolo`
(`mesa.py:2291-2342`): slots ocupáveis em ordem visual × fila da estante, `zip(slots, fila)`
1:1 (`:2323`). **Não olha foto, preço, categoria nem tamanho do slot** para decidir.
Item sem foto entra igual; sobra vira "fora da grade" (aviso, `:2325-2326`); densidade só
avisa (`:2328-2335`). *"Depois de categorizar, preencheu direito" — categorizar é o único
jeito de influenciar o resultado, porque só a ORDEM da fila importa.*

**C-07 🟠 · "Heróis" usa só preço e ignora o tamanho do slot.** `ordenar_com_herois`
(`servico.py:1236-1247`): mais barato primeiro. Sem % de desconto, sem histórico, e sem
noção de área — só reordena a fila; o herói cai nos primeiros slots em ordem visual y,x,
**que podem não ser os maiores**. *O pedido do dono ("os slots maiores recebem os produtos
de mais destaque") não é atendível hoje.* Já existe e não está ligado:
`ranking_ofertados` (`inteligencia.py:82`, popularidade) e `historico_de_preco`/`serie_de_um`
(`:46,66`, permite achar menor preço histórico e desconto real).

**C-08 🔴 · A sanitização APAGA palavra do nome — o achado mais grave desta frente.**
`app/core/sanitize.py` está limpo (não descarta token; `_limpar` só tira `®©™°` e runs de
`_`/`~`, `:122,126-131`). O apagamento está em `remover_inventados`
(`enriquecimento.py:144-151`), chamado em `:490` **depois** de `_montar` (`:486`) e
**antes** de `tokens_perdidos` ser calculado (`:495-498`): remove do `nome_sanitizado`
qualquer token sem overlap por substring com o bruto — inclusive quando a IA "corrige" um
typo de forma agressiva. **O próprio teste do projeto prova a perda**:
`test_onda4_conteudo.py:47-52`, caso "Huppers"→"Ruppers" — o token é removido de verdade e
só depois registrado como perdido. Quando a guarda percebe, a palavra já sumiu.

**C-09 🔴 · E o aviso da perda não chega ao dono em 2 caminhos.**
*Furo A* — `conciliacao_dialog.py:465-478`: com "Buscar fotos automaticamente" desmarcado
(RG-03, o **modo rápido**), `_criar` cadastra direto sem abrir `CuradoriaDialog`, que é o
único lugar que exibe `aviso_tokens` (`curadoria_dialog.py:60-72`).
*Furo B* — `_criar_todos_sem_foto` (`conciliacao_dialog.py:562-596`): `_criar_um` calcula
`proposta.tokens_perdidos` e passa para `finalizar_criacao`, cuja assinatura
(`servico.py:2271`) **nem tem parâmetro** para isso. `ItemMesa` (`servico.py:31-73`)
também não tem o campo — a informação é **irrecuperável** depois de criado o produto.
`test_onda1_desempenho.py:141-155` testa esse caminho só quanto a "criou tudo".
> Ironia: o caminho do dono apressado é justamente o que perde a rede de segurança.

**C-10 🟠 · O diálogo de conciliação não lembra nada.** `conciliacao_dialog.py:170`
`self.resize(1200, 760)` (modo foto) e `:174` `resize(860,560)` — **fixo em px, hardcoded,
recalculado do zero a cada abertura**. Sem `QSettings`, `saveGeometry`/`restoreGeometry`
nem `setMinimumSize`. O app **tem** o padrão certo ao lado: `splitter_com_memoria`
(`componentes.py:181-212`) grava em Config e é usado pela Mesa (`mesa.py:338`) — e o
diálogo não usa nem para o splitter interno (`:163-169`) nem para a janela.
Colunas 1/3 (os NOMES) são `Stretch` (`:95-96`), `resizeColumnsToContents()` (`:318`) é
ignorado nelas, e a única rede são tooltips (`:306,312`) que exigem hover. *"Tenho que
ficar arrastando o tamanho, aqui não dá pra ver direito."*

**C-11 🟠 VIOLA I1 (latente) · Índice como identidade na conciliação.**
`_aceitar/_criar/_cadastrar/_resolvido` (`conciliacao_dialog.py:448-625`) usam `li=linha`
capturado em closure. Hoje mascarado porque o overlay bloqueia o diálogo inteiro e
serializa os cliques — **é uma armadilha para qualquer conserto de performance**: parar
de bloquear reintroduz trocar item de linha. O padrão certo existe ao lado
(`mesa.py:2086-2187` e `conciliacao_dialog.py:216-221,278-284` usam uid).

**C-12 🟡 · Listas paralelas por posição:** `multi_precos[i-1]` pareado por índice com
`linhas` em `conciliar_linhas` (`servico.py:1611-1616`) e em `colagem.py`. Funciona só
porque nada filtra entre criação e uso.

**C-13 🟡 · O que a Mesa NÃO deixa editar** (obriga ir ao Almoxarifado/Ateliê):
marca/sabor/peso estruturados, EAN, +18/álcool (`servico.editar_produto:220-241`), e
qualquer coisa de layout. Editável na Mesa: nome e preço por F2/duplo-clique
(`mesa.py:2188-2216`); nome/preço/unidade/categoria/observação no modo planilha
(`planilha.py:13-15,34-53`); nome/preço/imagem/arranjo/enquadramento por override
(`servico.py:620-657`).

---

## §7 · FRENTE I — imagens: remover fundo, trocar foto, os 20 minutos

**I-01 🔴 · O recorte de fundo roda em worker, mas o overlay bloqueia a TELA INTEIRA.**
`tratar_imagem` (`servico.py:2191` → `processar_imagem`, `fundo.py:126`) sempre roda em
`Trabalhador`/QThread (`mesa.py:2168-2172`, `almoxarifado.py:685-693`,
`conciliacao_dialog.py:555-558`, `fotos_item_dialog.py:264-269`). Mas cada tela usa
`OverlayOcupado(self)` cobrindo o **widget inteiro** (`almoxarifado.py:506`, `mesa.py:347`)
e o overlay **não tem** `WA_TransparentForMouseEvents` (`carregando.py:144-193`) —
intercepta clique. O processo não trava; a tela trava, ~8 s por foto.
*"Ele podia estar removendo fundo no background, não precisa ficar me ocupando aqui" — está
em background; o véu é que não deixa trabalhar.*

**I-02 🟠 · Existe pré-busca do próximo item, mas só da BUSCA — não do rembg.**
`_pre_buscar_lote` (`mesa.py:2117-2141`). O recorte do escolhido só começa depois do
clique "Usar esta" e bloqueia (`mesa.py:2168-2176`).

**I-03 🟠 · O lote do Estúdio não mostra progresso.** `_estudio_lote`
(`almoxarifado.py:812-851`) processa N fotos em `TrabalhadorFila` com overlay ligado do
início ao fim e texto estático "Estúdio em lote (N fotos)…" (`:850`) — **sem contador
"X de N"**, apesar de `TrabalhadorFila.item_pronto` (`workers.py:69`) já existir e não
estar conectado.

**I-04 🟠 · O rembg roda cru, sem nenhum pós-processamento de máscara.**
`fundo.py:77-81`: `remove(img.convert("RGBA"), session=_sessao(modelo))` — **sem nenhum
parâmetro extra**. Defaults do rembg: `alpha_matting=False`, `post_process_mask=False`.
Ou seja: alpha matting **não** é a causa; não há erode nem threshold custom. É a saída
crua do birefnet-general, sem preencher buraco nem suavizar borda. `recortar_conteudo`
(`:110-113`) só faz crop pela bbox do alfa. **"Comer" pedaços da paçoca e do pé-de-moleque
vem do modelo em textura irregular, e não há nada no código para compensar.**
O modelo só é trocável globalmente em Configurações (`configuracoes.py:473-477`,
`imagem.modelo_rembg`) — não por imagem no fluxo de curadoria.

**I-05 🟡 · A correção manual existe e está escondida em dois lugares.** Pincel no canal
alfa: `refinar_alfa` (`curadoria.py:39-51`), exposto em `RefinoDialog`
(`refino_dialog.py`, slider de raio `:86-89`, "Restaurar"/"Apagar"), alcançável pelo botão
"Refinar…" do Almoxarifado (`almoxarifado.py:439-443`, handler `:788-810`) e dentro da
`CuradoriaDialog` (`:155-160`, handler `:293-301`). **Não existe** "refazer com outro
modelo" no ponto de correção.

**I-06 🔴 · Trocar imagem: três caminhos, e o mais óbvio é o pior.**
- *Almoxarifado (o "banco")*: produto → "Trocar imagem…" (`almoxarifado.py:417-420`,
  handler `:663-674`) ou botão direito na linha (`:903`) → Curadoria → "Usar esta" →
  `tratar_imagem`+`definir_imagem` (`:685-693`). Bem sinalizado, tem tutorial (`tutorial.py:28-31`).
- *Mesa, caminho A*: botão direito na estante → **"Fotos deste item (sabores)…"**
  (`mesa.py:1845`, handler `:1951-1982`) → busca + rembg (`servico.py:486-497`), persiste
  no banco. Funciona — mas o rótulo "sabores" não sugere "trocar a foto principal".
- *Mesa, caminho B*: botão direito **no slot do canvas** → "Conteúdo desta célula
  (override)…" (`itens.py:588-592`) → "Trocar foto…" (`override_dialog.py:58-59`,
  `_escolher_imagem:125-131`) → **`QFileDialog` puro: sem busca, sem rembg, sem gravar no
  banco.** É o gesto mais natural (clicar na célula) e o único que **não** remove fundo.
- **Não há nenhuma referência a "Almoxarifado" em `mesa.py`** — nenhum atalho "editar
  produto no cadastro" a partir da Mesa. *"Como é que eu edito dentro do banco de dados?"*

---

## §8 · FRENTE X — onde estão os 20 minutos

Boot **já resolvido** (`editor_app.py:353-508`, duas fases; 2.307 ms → **510 ms** até a
janela, `REVISAO_GERAL.md:207-225`). Imports pesados (rembg/torch/onnxruntime) já são
locais dentro de função. O tempo está em outro lugar:

**X-01 🔴 · Recompose síncrono a cada tecla digitada.** `notificar_edicao()`
(`canvas.py:1617-1629`) chama `_registrar_hist()` + `_compor_fundo()` (`:1628`)
**sincronamente, sem QTimer, sem debounce**. Gatilhos: `nome.textEdited`
(`painel_propriedades.py:82` — **por tecla**), `tam.valueChanged` (`:88`),
`rotacao.valueChanged` (`:218-219` — em rajada ao arrastar). Cada disparo = um
`compor_pagina` inteiro na thread da UI. O único debounce de todo o pipeline protege a
*miniatura* da faixa de páginas (`faixa_paginas.py:56-59`, 400 ms) — não o canvas.

**X-02 🔴 · rembg sequencial, 8 s por imagem, sem paralelismo.**
`TrabalhadorFila.run` (`workers.py:83-94`) processa um item por vez. Medido:
**15,4 s na 1ª chamada / 8,0 s depois** (`REVISAO_GERAL.md:227-238`), numa imagem
**pequena** de teste. 30 itens ⇒ **≈4 minutos só de recorte**. `birefnet-general` é o
padrão travado e o próprio rótulo diz "lento" (`fundo.py:22,26`).

**X-03 🟠 · Conciliar 30–40 itens: orçamento próprio do projeto é 180 s**
(`selfcheck_marco.py:145,147`, acervo de 5 k).

**X-04 🟠 · `compor_pagina` nunca tem cache nem dirty-rect.** `compositor.py:594-661`
reabre/redimensiona o fundo (`:613-615`) e redesenha **todas** as regiões de todos os
slots (`:638-660`) a cada chamada. Chamado de 5 pontos sem throttle: `canvas.py:1628`
(edição), `canvas.py:616` (miniatura de página), `atelie.py:199` (miniatura da biblioteca),
`mesa.py:1521` (Revisar), `exportar_dialog.py:108` (perfis).

**X-05 🟠 · Miniatura da biblioteca do Ateliê: 300 DPI cheio, sem cache.**
`atelie.py:189-205` — para todo layout sem arte estática, chama `compor_pagina` em 300 DPI
(`:199`) só para o ícone da lista, recalculado a cada `recarregar()` (todo save, toda visita).

**X-06 🟠 · Miniatura da faixa de páginas compõe em resolução cheia e só depois reduz**
(`canvas.py:611-620`, `QPixmap.scaled` em `:618-620`) — sem caminho de rascunho, sem cache.
E `faixa_paginas.py:69-82` recarrega **todas** as páginas por burst.

**X-07 🟡 · "Revisar" compõe tudo na UI antes de acionar o worker** (`mesa.py:1521`).

**X-08 🟡 · "Exportar por perfis" congela a UI de propósito** — o comentário admite:
"compõe TODAS as páginas UMA vez (na thread da UI)… feedback antes do freeze"
(`exportar_dialog.py:105-108`).

**X-09 🟡 · N+1 na biblioteca do Ateliê:** `recarregar()` (`atelie.py:162-177`) faz 1
`session.get` + `json.loads` + reconstrução de `LayoutDef` **por layout** (`:167`), a cada
recarga.

**X-10 🟡 · Busca de imagem: 1,5 s de pausa mínima + backoff exponencial até 3 tentativas**
(`busca.py:85,123-144`) — pior caso ~10,5 s de `time.sleep` por item, um item por vez.

**X-11 🟡 · `Database.init()` roda `create_all` + `_migrar_schema` (com `PRAGMA table_info`
por tabela) em TODA chamada isolada** de qualquer serviço — e o padrão do projeto é abrir
sessão por função. Idempotente, mas repetido centenas de vezes por sessão.

**Conta do fluxo real de 30 itens:** boot ~1 s + conciliar até 3 min + **4 min de rembg** +
ajuste fino de 30 células (dezenas de travadas curtas do X-01) + export ~30 s ⇒ **piso
realista de 8–12 min**, batendo com a reclamação mesmo com o boot corrigido.

---

## §9 · FRENTE F — Fábrica, cartaz, etiquetas, social, Modo Pai

**F-01 🔴 VIOLA DECISÃO TRAVADA · Etiqueta em lote sai SEM selo +18, mesmo em bebida
alcoólica.** `servico.py:1858-1863` monta o `DadosProduto` de cada etiqueta sem as chaves
`"mais18"`/`"alcool"`; em `dados_cartaz_de_produto` (`:1780`),
`mais18 = bool(produto.get("mais18") or produto.get("alcool"))` vira sempre `False`.
O cartaz normal faz certo (`fabrica.py:599`). **E é silencioso duas vezes:**
`validar_composicao` (`servico.py:1427-1526`) nunca checa `mais18`, e o pré-voo mostrado
antes do lote (`fabrica.py:634`) usa `self._dados(it)` — que TEM `mais18` correto — então
o aviso nunca dispara mesmo a etiqueta saindo errada. *Causa-raiz: duas receitas
quase-iguais para o mesmo dado (`fabrica.py:593-601` vs `servico.py:1760-1784`) que
divergiram.*

**F-02 🟠 · O Modo Pai imprime sem a rede de segurança que a Fábrica tem.**
`modo_pai.py:325-326`: `previa.paintRequested.connect(lambda pr: imprimir_imagens(...))`
sem try/except. `fabrica.py:798-804` embrulha a MESMA chamada com toast ("I2: falha
visível, nunca calada"). Impressora offline/sem papel ⇒ exceção crua na tela feita para o
usuário menos técnico. `modo_pai.py:340` (`_enviar`) idem.

**F-03 🟠 · CMYK ligado na Config não vale para 3 das 5 rotas de PDF.**
`pos_processar_export` só é chamado em `fabrica.py:733/739` e `mesa.py:2432/2442`.
`gerar_etiquetas_lote` (`servico.py:1871-1874`), `gerar_kit_gondola` (`:1911`) e
`cartaz_relampago` (`:1830`) fecham o PDF direto — saem em RGB **sem avisar que a
conversão foi pulada**.

**F-04 🟡 · No Publicar, a mensagem de erro do vídeo mente.** `_SEM_FFMPEG`
(`video.py:27-29`) diz "Os PNGs das páginas foram salvos normalmente — só o MP4 não saiu."
Mas no modo "Vídeo do tabloide" (`publicar_dialog.py:62-72`) a única saída tentada é o MP4
— não há `exportar_png` nesse ramo (diferente de story/oferta/faixa, `:83-89`).
Sem ffmpeg, **nada foi salvo em disco** e a frase afirma o contrário (`:357-358`).

**F-05 🟡 · "Dois por folha" fica habilitado para a etiqueta pequena.**
`_atualizar_2em1_disponivel` (`fabrica.py:266-271`) só checa `<=148.5×210.5 mm` — a
etiqueta de 100×70 passa e imprime **2 etiquetas numa A4 inteira**, quando a ferramenta
certa é "Etiquetas em lote" (`imposicao.py:93+`).

**F-06 🔵 · `modo_pai.recarregar()` (`:161-184`) lista TODOS os projetos salvos**, sem
filtrar por tipo ou completude, apesar do estado vazio dizer "Nenhuma oferta **pronta**".

**Verificado e SÃO** (para o dono não gastar tempo): tamanho físico exato — `units.py:18`
+ `round()` em `compositor.py:607-608` ⇒ cartaz 100×150@300dpi vira 99,996×150,001 mm
(erro <0,005 mm); A4 erro <0,03 mm; na impressão direta nem esse arredondamento entra
(`impressao.py:34-40` monta `QPageSize`/`QPageLayout` direto dos mm), testado com
tolerância de 1 mm em 3 formatos (`test_fase11_cartaz.py:302-324`). % de desconto
blindado: `compositor.py:81-98` devolve `None` se `de<=0 or por>=de`, único chamador é o
papel DESCONTO (`:129-135`), nunca digitado. 2-em-1 contido: `imposicao.py` não é
importado por `mesa.py`, com teste-guarda que varre a fonte (`test_fase11_cartaz.py:628-639`).
Orientação de impressão: o contorno do "Qt normaliza para retrato" está feito
(`impressao.py:36-40`). MP4 opcional: `shutil.which("ffmpeg")` (`video.py:35`).

---

## §10 · FRENTE D — banco, persistência, risco de perder trabalho

**D-01 🟠 VIOLA I1 · Miniatura de projeto casa item↔slot por posição quando falta o mapa.**
`_gerar_miniatura` (`projetos.py:89-104`): `itens[: len(layout.paginas[0].slots) or 1]` —
truncamento de lista. O próprio comentário admite "sem [mapa], por posição (legado)"
(`:61-62`). Projeto antigo mostra item errado no slot errado no Dashboard.
*Fora daí, `salvar_projeto`/`abrir_projeto` (`:162-319,689-745`) usam `mapa: slot_id→uid`
corretamente.*

**D-02 🟠 VIOLA I3 · Caminho absoluto ainda passa em 4 pontos.** `resolver_arte`
(`persistencia.py:36-49`) e `internar_arte` (`:52-82`): "absoluto legado… passa direto".
`_token` (`portabilidade.py:112-114`) e `_foto_local` (`:317-321`). `_resolver`
(`projetos.py:138-143`). Mitigação parcial: `migrar_artes_absolutas`
(`persistencia.py:143-181`) roda no boot (`editor_app.py:336-350`) e relativiza
`Layout.arquivo_fundo` — **mas não existe equivalente para `Produto.caminho_imagem` /
`imagens_json`**: se um caminho de produto for absoluto, fica absoluto no banco vivo para
sempre; só é neutralizado na CÓPIA do `.atpkg`, nunca no original.

**D-03 🟠 VIOLA I2 · Fusão de duplicatas perde foto em silêncio.** `_migrar_fotos`
(`deduplicacao.py:136`): `except Exception: return copiadas`. `fundir_no_banco` (`:55-96`)
não tem campo `avisos`, e o toast final (`almoxarifado.py:1053-1058`) nunca mostra o
número de fotos migradas (`servico.py:1968` devolve e ninguém usa).

**D-04 🟠 VIOLA I2 · `verificar_acervo` é `except Exception: pass`**
(`recuperacao.py:295-296`) — enquanto o bloco irmão (`:283-286`) sempre relata falha do
`integrity_check`. Incoerência entre checagens vizinhas.

**D-05 🟡 VIOLA I2 · `shutil.rmtree(..., ignore_errors=True)`** em `lixeira.py:89,149` —
falha ao apagar arquivo físico nunca aparece.

**D-06 🟠 RISCO REAL · A purga do boot pode abortar inteira.** `ProjetoSalvo.layout_id` é
`nullable=False` **sem `ondelete`** (`models.py:288`) e `PRAGMA foreign_keys=ON`
(`database.py:30`). Apagar um Layout enquanto QUALQUER `ProjetoSalvo` — mesmo já na
lixeira, ainda não purgado — o referencia estoura `IntegrityError` não tratado; como
`purgar()` (`lixeira.py:119-142`) processa produto/layout/projeto **no mesmo commit**, um
único conflito **aborta a purga daquele boot**. `s.delete(row)` sem try/except em
`:103-116,119-142`.

**D-07 🟡 MINAS LATENTES · Dois hard-deletes públicos e testados, hoje sem chamador.**
`excluir_layout` (`persistencia.py:214-218`) — hard-delete sem soft-delete e sem guarda de
FK; importado em `atelie.py:46` e **nunca usado** (a exclusão real usa
`lixeira.excluir_suave`, `atelie.py:294-296`), mas coberto por teste (`test_atelie.py:58`).
`ProdutoRepositorio.excluir` (`repositories.py:179-183`) — hard-delete que ignora a lixeira
de 30 dias, sem chamador. Ambos contradizem "TODA exclusão vira soft-delete" (`lixeira.py:4`).

**D-08 🟡 · Janela de inconsistência disco↔banco na portabilidade.**
`portabilidade.py:891-923`: em queda de energia ENTRE a cópia dos arquivos e o
`sl.commit()` (`:904`), o banco reverte e **o disco já tem a foto trocada**. O rollback
manual só cobre `except Exception`.

**D-09 🟡 · `ProjetoSalvo.evento_id` não tem FK real** (`models.py:293`) — `database.py:69`
admite "FK 'solta' de propósito: SQLite não adiciona FK via ALTER". Apagar um Evento nunca
é barrado nem avisado; fica órfão em silêncio.

**D-10 🟡 · Índices ausentes em coluna usada em toda listagem.** `Produto.excluido_em`,
`Layout.excluido_em`, `ProjetoSalvo.excluido_em` (`models.py:115,205,300`) são filtradas em
praticamente toda tela (`repositories.py:74,85`; `projetos.py:754,786,807`;
`persistencia.py:186`) e **nenhuma tem índice** — varredura completa a cada tela.
`Layout.nome` (`models.py:201`) não é unique nem indexado e é buscado por igualdade
(`persistencia.py:116`; `projetos.py:148`).

**D-11 🟠 · Alembic está MORTO.** `alembic/` contém só `__pycache__/env.cpython-312.pyc` —
sem `env.py`, sem `alembic.ini`, sem `versions/`; `pyproject.toml:43` lista alembic entre as
dependências **descartadas**. A migração real é `_migrar_schema`/`_COLUNAS_NOVAS`
(`database.py:62-90`): só `ALTER TABLE ADD COLUMN`, idempotente, **sem downgrade**,
incapaz de renomear/retipar/remover. Banco de versão **futura**: nenhuma checagem de
versão de schema (diferente do `.atpkg`/`.atproj`, que travam `versao_schema` —
`portabilidade.py:392-395`, `atproj.py:100-106`); colunas desconhecidas são ignoradas sem aviso.

**D-12 🟡 · Três conexões `sqlite3` cruas fora do engine** (`cofre.py:43-52`,
`portabilidade.py:92-155`, `migracao_antiga.py:27`) — **não passam pelo hook que liga
`PRAGMA foreign_keys=ON`** (só em `database.py:26-31`): integridade referencial não
garantida nessas operações, que são justamente as de backup/migração.

**D-13 🔵 · Três mecanismos de exclusão de produto coexistem sem hierarquia:** soft-delete
(lixeira), hard-delete direto (`repositories.py`) e fusão por duplicata
(`deduplicacao.py`). Nenhum documento define qual é "a" forma correta.

**D-14 🟡 · `sqlite-vec` é anunciado e não é usado.** `pyproject.toml:56,63` o lista como
opcional; **nunca é importado em nenhum `.py`** (grep vazio). O que existe é a tabela
`produto_embeddings` (`models.py:332-355`) + cosseno em numpy puro em memória
(`conciliacao.py:232-293`). Funciona sem a extensão, e a invalidação por chave ao renomear
é real (`:256-257`). Mas carrega a tabela **inteira** para RAM a cada `Conciliador`
(`:255-259`, sem limite). *Desalinhamento entre CLAUDE.md/pyproject e o código.*

---

## §11 · FRENTE A — Almoxarifado, Inteligência, IA colega

**A-01 🔴 · O filtro "Sem imagem/Incompletos" mente em escala.** `CatalogoModel.fetchMore`
(`almoxarifado.py:80-91`) busca 50 do banco com `offset=len(self._linhas)` — mas com o
filtro ativo, `self._linhas` guarda a contagem **pós-filtro**, não quantos registros já
foram escaneados. E `if len(pagina) < _PAGINA: self._esgotado = True` (`:85`) declara fim
de lista assim que a página filtrada tiver menos de 50 — **o que quase sempre acontece já
na primeira leitura**. Resultado: com "Sem imagem" ligado, a lista só enxerga os itens que
caem nos primeiros ~50 produtos em ordem alfabética (`repositories.py:71-79`,
`ORDER BY nome_sanitizado`) e trava ali. **Tudo depois de "B…" nunca é escaneado.**
Sem filtro, a paginação funciona.

**A-02 🔴 · Não existe edição em lote.** Campos editáveis (`almoxarifado.py:403-415`) são
todos por-item. Para corrigir a categoria de N produtos escolhidos, a única via são os dois
botões de IA que processam **o banco inteiro** (`enriquecer_banco.py:39`,
`repo.listar(limit=10_000)`) — não dá para selecionar 50 itens e forçar um valor.
*"Como é que eu edito dentro do banco de dados? Aqui vai ser muito dentro do banco de dados."*

**A-03 🟠 · Ações em massa irreversíveis não pedem confirmação; apagar 1 produto pede.**
"Corrigir nomes (IA)" (`almoxarifado.py:855`) e "Categorizar (IA)" (`:876`) disparam direto,
**sem `confirmar_destrutivo`** — que existe e é usado em Excluir (`:938`) e no Estúdio em
lote (`:822-828`). Reescrever nomes de milhares de produtos é mais destrutivo que um
soft-delete reversível de 30 dias.

**A-04 🟠 VIOLA I2 · O campo Peso apaga dado sem avisar.** `_salvar_peso`
(`almoxarifado.py:633-644`): regex que não casa (um typo do dono) grava
`peso_valor=None, peso_unidade=None` **sem nenhum toast** — enquanto `_salvar_validade`,
4 linhas abaixo, valida e avisa.

**A-05 🟠 · O campo Preço pode estourar exceção crua.** `_para_decimal`
(`repositories.py:23-33`) chama `Decimal(str(valor))` sem tratar `InvalidOperation`; nada
na cadeia `_salvar_campo→editar_produto→ProdutoRepositorio.editar` trata, e **não há
`sys.excepthook` em nenhum lugar do projeto** (grep vazio).

**A-06 🟡 · Menu de contexto ignora a multi-seleção** exceto no Excluir:
`_menu:896-940` — Editar/Trocar imagem/Histórico/Cartaz-relâmpago/Kit todos chamam
`self._selecionou(index)` (só o item clicado) mesmo havendo seleção múltipla.

**A-07 🟡 · Busca sem debounce:** `_rebuscar` (`almoxarifado.py:276`) dispara
`Database().init()` + query nova **por tecla**.

**A-08 🟡 · Carregam a tabela inteira em memória sem paginação:** `pares_duplicatas()`
(`servico.py:1928`), `correcoes_aprendidas()` (`:1982-1986`), `saude_acervo()`
(`inteligencia.py:258`). Tolerável em 5 k, não escala.

**A-09 🟡 · O ponto único de degradação sem IA não é único.** `_motor_se_disponivel()`
(`servico.py:163-167`) é usado por `conciliacao_dialog.py`, `painel_propriedades.py:530`,
`papel_texto_ui.py:242`, `fotos_item_dialog.py:196`, `mesa.py:1541`. **Escapa:**
`enriquecer_banco.py:29,86` — que alimenta justamente os botões do Almoxarifado —
reimplementa a checagem na mão (`motor.disponivel()`). Duplicação que pode divergir.

**Verificado e SÃO:** a IA **nunca** bloqueia — `revisar_export` (`revisora.py:132-157`)
tem o corpo inteiro sob `try` e é chamada só pelo botão manual "Revisar"
(`mesa.py:1514-1549`), **desacoplado do export**; `sentinela.preco_suspeito`
(`sentinela.py:37-53`) só devolve `str|None`; `avaliador.avaliar_foto` (`:53-89`) só gera
nota. `extrair_marca` (`aprendizado.py:30-46`) só devolve marca CONHECIDA, casando por
fronteira de palavra — provado adversarialmente (`test_os_f11_5.py:700-708`: "Camila
fatiado 200g"→None mesmo com "Camil" cadastrada). Deduplicação, genéricas e aprendizado
estão de fato ligados (`almoxarifado.py:1024-1058`; `servico.py:1468-1475`;
`conciliacao.py:178`, `servico.py:2089-2096`, `mesa.py:1441-1442`).

---

## §12 · FRENTE U — as 40 vezes que ele disse "não sei"

Isto não é lista de bugs: é o catálogo dos lugares onde o app **age sem dizer o que fez**.
Régua usada: o próprio `app/qt/design/toast.py` — quem usa e quem não usa.

**U-01 🟠 · Botão direito no canvas vazio simplesmente não abre menu** se não existe
célula-mestre ainda (`canvas.py:1631-1643` retorna). Parece que o botão direito não funciona.
**É a razão de "não sei como carimba"**: carimbar só existe nesse menu (`:1632-1654`),
e a única outra pista é um tooltip em `barra_editor.py:123`.

**U-02 🟠 · "Ignorar" na conciliação apaga a linha sem toast, sem confirmação e sem
desfazer** (`conciliacao_dialog.py:457-459`) — ao lado de um botão irmão que tem os dois
(`btn_desfazer_verdes`, `:124-128`).

**U-03 🟠 · 31 conexões de campo de estilo em `painel_propriedades.py`, 5 toasts.**
`_set`/`_set_enum` (`:749-764`) mutam via `canvas.notificar_edicao` sem confirmar nada.

**U-04 🟡 · Sem feedback:** reordenar camada (`painel_camadas.py:213-217`), arrastar item
na estante (`mesa.py:1822-1832`), travar/destravar região (`itens.py:521-522`).

**U-05 🟡 · Toasts genéricos:** `"Layout «X» salvo no banco."` igual para 1 ou 40 mudanças
e sem dizer se sobrescreveu (`editor.py:319`); `"Configurações salvas."` para 1 ou 30
campos (`configuracoes.py:2293`); `"{n} selo(s) neste item."` diz quantos, não quais
(`mesa.py:1949`).

**U-06 🟠 · Atalhos que MENTEM.** `itens.py:503,507,511,514,532` — Ctrl+C/V/D/Del/Esc
**hardcoded como texto** no menu de contexto, fora do catálogo `atalhos.py`. Se o dono
remapear "Duplicar região" em Configurações, o menu continua mostrando "Ctrl+D".
Mesma lacuna em `planilha_dialog.py:83,87` e `curadoria_dialog.py:203`.

**U-07 🟡 · Atalhos invisíveis:** Ctrl+Shift+Z (`mesa.py:374`) e Ctrl+K (`mesa.py:697`)
são `QShortcut` direto, fora de `criar_atalho` — não aparecem na tabela de Configurações
(`configuracoes.py:1191-1198`, que só lê `CATALOGO`) nem na folha de cola.
Teclas N/A/R soltas sem modificador na conciliação (`conciliacao_dialog.py:82-86`),
documentadas só num tooltip (`:87-88`).

**U-08 🔴 · Ctrl+K furou o Modo Pai.** `shell.py:191-197` esconde a barra de navegação em
`modo_pai`, **mas** o atalho é registrado no nível da janela (`WindowShortcut`,
`editor_app.py:318-323`) e continua ativo — abre a paleta, que o próprio código comenta ser
"Ctrl+K em QUALQUER tela" (`paleta_comandos.py:262-263`) e navega para Almoxarifado /
Ateliê / Mesa / qualquer projeto. **Toda ação que o Modo Pai promete não deixar alcançável
fica a um atalho de distância.** Entrar no Modo simples também não liga o somente-leitura
(`modo.py`) — são chaves independentes.

**U-09 🟡 · Itens de menu habilitados sem pré-condição:** "Duplicar semana passada" sempre
habilitado, sem checar se existe semana passada (`dashboard.py:819-830`); "Mover para
evento…" pode abrir submenu **vazio** (`:1365-1373`). Em contrapartida, "Agrupar"/"Isolar"
**somem** do menu sem explicar por que (`itens.py:609-617`) — o oposto do problema, igualmente ruim.

**U-10 🟡 · Painel de camadas não tem estado vazio** — layout com 0 regiões vira lista em
branco, sem dica de usar a barra. O padrão bom existe ao lado (`painel_propriedades.py:312-314`:
"Nada selecionado / Clique numa região…").

**U-11 🟠 · Jargão de programador na tela.** Cada um destes é texto que o dono lê:
`painel_propriedades.py:465` → **"Tipo: TEXTO_LEGAL"**, "Tipo: PRECO" cru;
`painel_camadas.py:131,137` → tooltip com `reg.tipo.value` cru e rótulo **"Texto_Legal"**
(o underscore sobrevive ao `.title()`); combos com enum cru: "SEPARADO"/"COMPLETO",
"UNICO"/"DE"/"POR", "CONTER"/"PREENCHER" (`painel_propriedades.py:108,111,119`);
**"Conteúdo desta célula (override)…"** (`itens.py:589`, `override_dialog.py:42`);
`"Override aplicado só nesta célula."` (`mesa.py:539`); **"Compor 2 num slot"** em três
diálogos (`mesa.py:1999,2006,2010`); tooltip "Adicionar região IMAGEM/PRECO" (`barra.py:58`).

**U-12 🟡 · Badge M/C (mestra/cópia) pintado sem tooltip** (`itens.py:249-263`); só
explicado numa legenda escondida (`painel_propriedades.py:325-330`).

**U-13 🟡 · Cores hardcoded fora dos tokens (divergem entre temas):**
`apresentacao.py:26,33,47,59` (`#000000`/`#9AA0AA` fixos — o Modo apresentação não segue
tema); `dashboard.py:171,227` (`QColor("#FFFFFF")` fixo); `painel_propriedades.py:91,350,373,590`
(`"#000000"` como padrão de cor de texto novo — **texto nasce preto mesmo no tema escuro**,
ao contrário da pílula, que tem `pill_padrao_do_tema`, `papel_texto_ui.py:105-106`).

**U-14 🟠 · O único diálogo que estoura 768 px é o mais usado.**
`conciliacao_dialog.py:170` `self.resize(1200, 760)` — abre exatamente quando a importação
vem de FOTO. Em 1366×768 sobram ~680 px úteis: os botões "Concluir"/"Cancelar" do rodapé
(`:176`) correm risco real de ficar fora da tela. Os demais diálogos (560–720 px) cabem.

**U-15 🟡 · Botões "Novo tabloide" / "Novo cartaz" prometem mais do que entregam.**
`dashboard.py:291-297` → `_novo("mesa")` (`:1321-1323`) só faz `shell.ir_para("mesa")`:
não chama `carregar_layout`, não zera `_itens`/`_projeto_id`/`_mapa`. A Mesa abre com o que
já estava carregado. *"Não testei esses botões, se de fato funcionam para alguma coisa."*

**U-16 🟡 · "Continuar de onde parou" não registra o primeiro salvamento.**
`registrar_ultimo_aberto` (`projetos.py:638-652`) só é chamado ao **reabrir** um projeto
(`mesa.py:919-920`, `fabrica.py:434-435`) ou duplicar — **nunca** no primeiro "Salvar"
(`mesa.py:830-864`), apesar do docstring (`projetos.py:640`) dizer "chamado em TODO caminho
de abertura". Terminar e salvar um tabloide novo **não** atualiza a faixa.

**U-17 🟡 · Cartões "Visão geral" do Início ficam mudos durante o boot** — `_indicador_clicado`
(`dashboard.py:392-402`) só é ligado na fase 2 (`editor_app.py:299-317`); antes disso o
clique não faz nada visível.

**U-18 🔵 · A aba "Campanhas" das Configurações mistura Eventos com "Seções"**
(estilo visual do agrupamento por categoria) — dois assuntos sem relação
(`configuracoes.py:562-565`). *"Tá um meio termo que não tá certo, tá estranho."*

**U-19 🔵 · `except Exception: pass` engolindo falha de gravação de config sem avisar:**
`configuracoes.py:1757-1815` (animações/transparência/som), `modo_pai.py:53-65`
(`lembrar_modo_pai`), `fabrica.py:374,813-815`, `publicar_dialog.py:140-141`.

**Verificado e SÃO:** não achei configuração órfã — as ~30 chaves gravadas
(`configuracoes.py:2208-2295`, mais `app.icone:1370`, `ia.usar:1459`,
`aparencia.*:1757-1815`) têm consumidor real (`sanitizacao.*`→`enriquecimento.py`;
`ia.*`→`ai/client.py`; `secoes.*`→`rendering/secoes.py:187-213`;
`frases.validade`→`servico.py:826-875`; `sinonimos.regionais`→`conciliacao.py:170`).
O Modo Pai reusa serviços reais (aprovação, `compor_pagina`, impressão) — não é fachada.
Vazamentos: `_veus`/`_hovers`/`_veus_troca` **crescem** mas não vazam memória de forma
relevante; todo `QTimer` tem parent; os dois `lru_cache` (`fontes.py:145` maxsize=512;
`servico.py:365` maxsize=1) são pequenos e intencionais; `GerenciadorTrabalhos`
(`workers.py:143-213`) já implementa a lição do segfault (`_ORFAOS`, `:192-193`).

**LACUNA DE PRODUTO (não é bug) · Não existe "comunicado".** Busca por `comunicado`,
`edital`, `mural`, `recado`, `aviso` em todo `app/`: **zero ocorrências**. `tipo_midia` só
tem TABLOIDE/CARTAZ de oferta. O cartaz de recado que o dono faz no Photoshop não tem
lugar no app. O calendário do varejo (`calendario.py:44-67`) tem 9 datas fixas com
cor/frase, e "Criar evento desta data" (`:98-114`) gera só nome+cor+dia vazios, sem conteúdo.

---

## §13 · FRENTE N — os 7 encartes novos: mapa e lacunas

Todos: **viewBox `0 0 1080 1440`, BASE.png 2160×2880 (escala ×2 exata)**.
Convenção do pacote: `estrutura` (vai para o BASE) + `<g id="conteudo-exemplo">` (o que o
app substitui). Fonte da geometria: as listas nos geradores.

| Encarte | Células | Fixas | Destaque (maior) | Slot de foto (padrão) |
|---|---|---|---|---|
| **Terça do Pão** | 6 | **2** (Pão Francês, Sonho+Croissant) | hero 600×352 | cestas `(x+18,756,190,150)`, x=[64,306,548,790] |
| **Segunda dos Frios** | 8 (+2 decorativos) | **1** (Kit Burger) | oval 500×304 | ROW_A `(82/406/730, 664-674, 268,138)` |
| **Quarta das Ofertas** | 8 | **3** (Mini Salgado, Pão de Queijo, Lanche na Chapa) | banner 616×426 | fixas `(88, 560/806/1052, 112,204)` |
| **Quinta do Peixe** | 7 | 0 | 2 "wide" 590×320 | wide `(x+w−286,y+24,262,h−48)`; vert `(x+22,y+22,w−44,140)` |
| **Sexta Verde** | 11 | 0 | 2 bancas 460×348 | bancas `(x+36,y+106,388,92)`, x=[54,566]; patch `(x+14,y+14,120,134)` |
| **Sábado da Carne** | 10 (masonry 3 col) | 0 | célula-1 "Corte da Semana" | destaque `(406,542,274,104)`; normal `(x+16,y+14,274,124)` |
| **Jornal p1** | 20 | 0 | hero `(74,328,384,234)` | 3 linhas de 5, `(178×96)`, x=[68,266,464,662,860], y=[660,882,1104] |
| **Jornal p2** | 22 | 0 | — | 4 linhas de 5, y=[132,334,566,768] + linha final de 2 (y=1000) |

**N-01 🟠 · Oclusão real na Terça do Pão** — o único caso do pacote, e viola a regra do
próprio README ("slots nunca podem ser ocluídos pela estrutura"). O selo fixo de 25% da
célula-2 (centro 964,392, R54) invade o canto superior-direito do 1º slot de foto:
distância centro→canto (922,386) = 42,4 px < R 54 ⇒ **overlap de ~12×60 px**.

**N-02 🟠 · "20%" está HARDCODED no gerador da Quarta.** `pctpod()` renderiza a string
"20%" no código, não como parâmetro — se o desconto real mudar, é preciso editar o
gerador, não só os dados. Incompatível com o `%` calculado do app (`compositor.py:81-98`).

**N-03 🟡 · "Pão de Queijo" (fixo) usa Baloo 2 com "ã"** — a **única** ocorrência de ã/Ã
em Baloo em todo o pacote, e o README avisa que **o glifo Ã dessa instância é defeituoso**.

**N-04 🟠 · O Jornal do Mês não segue a convenção do pacote.** Grep: **0 ocorrências de
`id="celula-N"`** no gerador do Jornal. A geometria só existe como coordenadas calculadas
dentro de `ch=[...]` e da função `linha(y, ids)`. Além disso o BASE zera
`conteudo-exemplo` inteiro (`base_ex = '<g id="conteudo-exemplo"></g>'`) em vez de usar
`.replace()` como os outros 6 — **não há resíduo de estrutura para a validade**: o app tem
de desenhar validade (540,193 / 790,90) e nº da edição (950,74) do zero.
⇒ O extrator de geometria precisa de um caminho separado para o Jornal.

**N-05 · Correção ao briefing do dono:** "SUPER OFERTA" (`splash_super`) e "Fica a Dica"
(caixas em p1 `64,1314,952,60` e p2 `650,1214,366,88`) são **exclusivas do Jornal** —
nenhum dos outros 6 encartes tem. E **não há seções fixas por categoria** em nenhum deles:
o próprio código do Jornal comenta "sem rótulo de seção — grade livre p/ o AutoTabloide";
as divisórias são linhas decorativas. ⇒ O "agrupar por seções" do Jornal precisa ser
desenhado pelo app (`rendering/secoes.py`), não vem da arte.

**N-06 · Validade por encarte** (onde o app deve escrever a data):
Terça selo topo `(946,128,R54,rot8)`; Segunda `(935,96,R54,rot10)`; Quarta
`(80,348,176,88)` + data em `(168,392)`; Peixe medalhão `(952,146,R62,rot−7)`; Sexta
bilhete `(934,140,rot−6)`; Sábado carimbo `(936,168,R66,rot9)`; Jornal `(540,193)`/`(790,90)`.
Nos 6 primeiros, o rodapé `(238,~1348)` tinha a data e ela é removida no BASE via
`.replace()` — **confere com o pedido do dono de ignorar a data de baixo**.

**N-07 · Fontes por encarte:** Terça/Segunda/Peixe/Sexta/Sábado = Archivo + Fraunces +
Caveat. Quarta = Anton + Nunito + **Baloo 2** + Caveat. Jornal = Archivo + Fraunces +
**UnifrakturMaguntia**. Gotchas do README: famílias com espaço precisam de aspas em SVG
(`font-family="'Baloo 2'"`); Nunito registra como "Nunito ExtraLight"; nunca aplicar
`stroke` em texto grande de fonte instanciada.

**N-08 🟡 · Caminho absoluto nos geradores:** todos carregam a logo de
`/home/claude/encartes/brand/logo_semfundo.png` (constante no topo). Precisa virar
relativo antes de qualquer regeração.

**Choque com o app (o que precisa nascer para os encartes funcionarem):**
1. **Célula FIXA** não existe no modelo — hoje todo slot é ocupável e entra no
   auto-preencher. Terça (2), Segunda (1) e Quarta (3) precisam de slots que carregam
   produto fixo e **não** entram na fila. *Atenção à lei do projeto: "todo TIPO NOVO de
   slot/região reavalia 'ocupável' e o pré-voo".*
2. **Destaque por área** — o C-07 (heróis só por preço, sem noção de tamanho de slot)
   impede o pedido "os slots maiores recebem os produtos de mais destaque".
3. **Rotação de célula** — Terça (cestas −0,7°..+0,7°), Sexta, Sábado, e os selos
   rotacionados. Casa direto com o E-08 (rotação desliga o resize).
4. **Validade em posição rotacionada** com fundo já sem a data.
5. **"Fica a Dica"** = região de texto livre que a mestra **não propaga** (E-11).

**Correções factuais de arte autorizadas pelo dono** (para quando ele liberar a execução):
CENEPOL → **SENEPOL**; "criada e produzida" → **"criado e produzido"**; **remover
"marca própria"** do Sábado; revisar **"queijos e frios fatiados na hora"** (sensacionalista
/ não é verdade); Jornal: **"mês inteiro" → período editável** (dia 1 ao 27).
*(Ficaram para depois, por decisão dele: subir a cesta na Sexta e recomposições visuais.)*

---

## §14 · Contradições resolvidas pelo arquiteto

Registro de honestidade de bancada — pontos em que dois agentes discordaram e eu fui à fonte:

1. **O véu vaza ou é limpo?** Um agente afirmou que `_veus` "é limpo via
   `destroyed.connect(...pop...)`" e classificou o risco como descartado. **Errado.**
   Leitura direta de `animacoes.py:275-315`: `_veus.pop(d, None)` remove a *entrada do
   dicionário*, não o *widget*. Só `_remover_veu` (`:310-315`) chama `hide()`/`deleteLater()`,
   e ele depende do evento `Hide`. **V-01 confirmado.** Lição: a linha *parece* limpeza —
   é exatamente o tipo de bug que sobrevive a revisão por leitura rápida.
2. **A ordem de desenho é hardcoded por tipo?** Não — `compositor.py:654-655` respeita a
   ordem da lista. O que está errado é o controle (R-02). O pedido do dono é atendível hoje.
3. **`alpha_matting` agressivo come o produto?** Não — está desligado por default
   (`fundo.py:77-81` não passa parâmetro). A causa é o modelo cru sem pós-processamento (I-04).
4. **"O cartaz perde a medida em mm"?** Não. Erro máximo medido <0,03 mm (§9).

---

## §14b · Reverificação manual do arquiteto (8 alegações que sustentam o dossiê)

Antes de emitir, reabri a fonte no disco e confirmei, uma por uma, as alegações em que um
erro me custaria credibilidade. Todas confirmadas:

| # | Alegação | Prova lida |
|---|---|---|
| V-01 | `destroyed` só remove do dicionário | `animacoes.py:287` — `_veus.pop(d, None)`, sem `hide()`/`deleteLater()` |
| E-01 | criação auto-seleciona ⇒ próxima região herda o slot | `canvas.py:1396-1397` `it.setSelected(it.regiao is reg)` + `canvas.py:1353-1357` `sel = self.selecionada(); if sel is not None: return slot` |
| R-02 | Subir/Descer invertidos | `painel_camadas.py:66-72` — tooltip "Trazer para a frente" → `_mover(-1)`; índice menor = pintado antes = **atrás** |
| E-08 | guarda de rotação + painel sem largura/altura | `itens.py:438` `not (self.regiao.rotacao_graus % 360)`; varredura de `painel_propriedades.py`: nenhum campo Largura/Altura (só `limite_caracteres` em `:540`, que lê o rect e não o edita) |
| R-01 | Y do texto é incondicional | `compositor.py:312` `oy = y + max(0, (rh - total_h) // 2)` — sem `if` |
| F-01 | etiqueta em lote sem `mais18` | `servico.py:1860-1863` — o dict tem `nome/preco/preco_de/imagem/validade` e **nada de `mais18`/`alcool`** |
| C-01 | categoria só é lida para item conhecido | `servico.py:1635-1636` `categoria=(p.categoria.nome if p and p.categoria else None)` |
| T-01..03 | números da suíte | 832 `def test_` · 81 arquivos · 19.939 linhas · **QTest: 0** · `.trigger()`: 0 · `dropEvent`/`QMimeData`: 0 · `instalar_vida` em testes: 0 · `sendEvent`: 1 (fonte) |
| D-11 | alembic morto | `find alembic -type f` devolve **só** `alembic/__pycache__/env.cpython-312.pyc` |

---

## §14c · REAUDITORIA (25/07/2026) — o que a varredura do Code corrigiu em mim

A varredura independente (`docs/VARREDURA_CODE_F13.md`, 123 achados) derrubou três coisas
minhas. Reabri a fonte no disco e **os três estão certos** — registro aqui, e o texto
original acima fica como está, com esta errata mandando nele:

1. **U-14 ERRADO — RETIRADO.** Eu disse que `conciliacao_dialog.py:170` (`resize(1200,760)`)
   deixaria os botões fora da tela em 768 px. Falso: a linha seguinte (`:171`)
   é `self._tela_cheia = True  # o chamador maximiza no exec()` — no modo foto o diálogo
   **abre maximizado**, e o `resize` é só reserva. O 720p do caminho mais usado está são.
   *(O C-10 — não lembrar geometria nem largura de coluna entre sessões — continua válido.)*
2. **U-08 INVERTIDO — a conclusão vira ao contrário, e o bug é pior.** Eu disse que Ctrl+K
   "furou o Modo Pai". A verdade: `mesa.py:697` cria `QShortcut(Ctrl+K, self)` **e**
   `editor_app.py:322` cria `criar_atalho("geral.busca", shell, …)` — duas teclas iguais em
   hierarquias que se sobrepõem, ambas em contexto de janela ⇒ *ambiguous shortcut overload*
   do Qt ⇒ **nenhuma das duas dispara. Ctrl+K está MORTO na Mesa.** Não é vazamento de
   permissão: é função anunciada que não existe. Pior ainda, há um teste verde chamado
   `test_ctrl_k_abre_em_duas_telas` que nunca aperta a tecla (CF-02 do Code).
3. **U-11 parcialmente errado:** a linha que citei sobre `barra.py:58` é **código morto** —
   o tooltip com enum cru não chega ao usuário por ali. Os outros sete casos de jargão do
   U-11 (`TEXTO_LEGAL` no painel, "override", "Compor 2 num slot", combos com enum) seguem
   válidos e verificados.

**E confirmei pessoalmente, na fonte, os cinco achados 🔴 mais graves dele:**

| Achado | Prova que eu li |
|---|---|
| **CD-01** editar preço apaga o desfazer | `canvas.py:210` `self._historico = Historico()` **dentro** de `carregar()` — objeto novo, pilha perdida. `mesa.py:2209` (`_editar_item`) → `_aplicar_mapa` (`:2344`) → `area.carregar(...)`. E `mesa.py:443` prova que o projeto **sabia**: "atualizar_dados preserva o histórico do canvas (carregar o zeraria)" — a lição foi aplicada num método e esquecida nos outros. **É a explicação dos 9 Ctrl+Z da gravação.** |
| **CA-01** boot baixa ~973 MB | `editor_app.py:450-466`: pré-aquece rembg (`aquecer(modelo_configurado())` → `new_session("birefnet-general")`, `fundo.py:43-45`) **e** o Real-ESRGAN, incondicionalmente, em thread de fundo, a cada boot. Em app declaradamente offline, sem pedir. |
| **CF-01** Enter na caixa destrutiva apaga | `componentes.py:171-178`: `addButton(verbo, DestructiveRole)` + `addButton("Cancelar", RejectRole)` e **nenhum `setDefaultButton`/`setEscapeButton`**. O default fica ao critério da heurística do Qt numa caixa cujo único desfecho seguro é Cancelar. *(O comportamento do Enter ele reproduziu na máquina real; eu confirmo a ausência das duas chamadas que evitariam a dúvida.)* |
| **CI-03** juiz IA pinta VERDE com confiança 0,05 | `conciliacao.py:378` lê `conf = float(dados.get("confianca", 0.0))`; as **únicas** comparações de limiar (`:420,425`) usam `melhor.score` (fuzzy), nunca `conf`. A confiança é parseada e descartada — fere a trava da F9 ("ambíguo vira amarelo"). |
| **CI-05** foto original apagada na 11ª troca | Verificado na frente de imagens — fere a trava da F10 ("original sempre preservada, curadoria não-destrutiva"). |

**O dado que muda a estratégia:** ele quebrou de propósito as 6 linhas 🔴 que eu indiquei e
**5 não deixaram nenhum teste vermelho**. Tirou o **preço** da etiqueta em lote e os 851
seguiram verdes. Rodando de outra pasta: 10 falhas + 8 pulados, e `arte/` está no
`.gitignore` — **nenhum clone reproduz a prova da arte real**. Em ordem invertida: 2
vermelhos, por estado vivo em `animacoes.py` — **o vazamento do véu (V-01) provado rodando**,
não só por leitura.

⇒ Isso promove o achado-mãe de "problema de qualidade" para **pré-requisito de execução**:
sem bancada que enxergue gesto, nenhum conserto desta auditoria é verificável. Ver
`docs/ORDEM_F13_RESGATE.md`, Bloco A.

---

## §15 · Placar por severidade

| | 🔴 Crítico | 🟠 Alto | 🟡 Médio | 🔵 Baixo | Total |
|---|---|---|---|---|---|
| T · Testes | 3 | 3 | 3 | 1 | 10 |
| V · Véu / tela escura | 2 | 1 | 1 | 1 | 5 |
| E · Editor / Ateliê | 5 | 6 | 1 | 1 | 13 |
| R · Compositor | 2 | 4 | 4 | 1 | 11 |
| P · Pré-voo / rascunho | 5 | 4 | 0 | 0 | 9 |
| C · Categoria / Mesa | 4 | 5 | 4 | 0 | 13 |
| I · Imagens | 2 | 3 | 1 | 0 | 6 |
| X · Desempenho | 2 | 4 | 5 | 0 | 11 |
| F · Fábrica / social | 1 | 2 | 2 | 1 | 6 |
| D · Banco / dados | 0 | 6 | 7 | 1 | 14 |
| A · Acervo / IA | 2 | 2 | 5 | 0 | 9 |
| U · Descoberta / UX | 3 | 5 | 9 | 3 | 20 |
| N · Encartes novos | 0 | 4 | 2 | 0 | 6 |
| **TOTAL** | **31** | **49** | **44** | **9** | **133** |

Mais 5 violações declaradas de invariante (I1: D-01, R-10, C-11; I2: R-06, R-07, D-03,
D-04, D-05, A-04; I3: D-02) e 2 reivindicações do CLAUDE.md refutadas por leitura
(RG-58 "a validade nunca fica vazia" → P-09; "sqlite-vec" → D-14).

---

## §17 · TERCEIRA ONDA (25/07) — o que ninguém tinha olhado: os pixels

As duas varreduras leram código e rodaram a suíte. **Nenhuma das duas abriu os arquivos que o
programa já produziu.** Abri `saida_marco/` — a pasta do "MARCO FINAL" que selou a Versão 1.0 —
e comparei os PNG, o `RELATORIO.txt` e o `medicoes.json` entre si.

### M-01 🔴 O artefato que selou a Versão 1.0 não tem uma única foto de produto

`saida_marco/quintou_p2.png` (1080×1300): as 15 células têm **quadrados de cor sólida** no
lugar das fotos — ciano, roxo, oliva, lima, vermelho, verde-água, magenta, bege, marrom. Nenhum
produto. O `RELATORIO.txt` registra `OK EXPORTAR Quintou (PNG×3 + PDF): 0.4s` na linha seguinte.
Nenhum aviso, nenhuma pendência. **O pré-voo deixou passar um tabloide inteiro sem foto.**

### M-02 🔴 A validade do marco está em MAIO, num tabloide de JULHO

`medicoes.json` (21/07/2026): `"validade": "ATÉ 26/05"`. E na mesma estrutura:
`"avisos_pre_voo": []`. O pré-voo, que existe para pegar exatamente isto (RG-58, papel
VALIDADE), **não achou nenhuma pendência** numa peça com data de dois meses antes.

### M-03 🔴 A conciliação encontrou ZERO correspondências em 5.000 produtos

`medicoes.json`: `"semaforo": {"verdes": 0, "amarelos": 0, "vermelhos": 30}`. Os 30 itens reais
do Quintou, conciliados contra um acervo de 5.000, saíram **todos vermelhos** — nenhum casou.
O `RELATORIO.txt` do run anterior diz o mesmo (`🟢0 🟡0 🔴40`) e conclui `OK`. As três camadas
(embeddings → fuzzy → IA) entregaram acerto zero, e isso foi lido como sucesso porque o
orçamento medido era **tempo**, não **acerto**. Confirma o C-01/C-03 com número: o
`RELATORIO.txt` chega a admitir na própria linha — *"IA real categorizou 0"*.

### M-04 🔴 Duas das três campanhas do marco não foram feitas — e o marco foi declarado executado

`medicoes.json`: `"campanhas_faltantes": ["sexta_verde", "fim_de_semana"]`.

### M-05 🔴 A pasta `saida_marco/` mistura dois runs diferentes

`quintou_p3.png` e `sexta_verde.png` são de **18/07 12:28**; `quintou_p1.png` e `quintou_p2.png`
são de **21/07 19:01**. O `RELATORIO.txt` é de 18/07, o `medicoes.json` de 21/07 — e este diz
`"paginas": 2`. Ou seja: **`quintou_p3.png` é órfão de um run de 3 páginas** e a "galeria do
marco" é uma colagem de duas execuções, apresentada como uma.

### M-06 🔴 Relatório e artefato se contradizem sobre a validade

`RELATORIO.txt` afirma: *"Sexta Verde: … + "OFERTA VÁLIDA DE 18/07 ATÉ 24/07" + selo do gestor
— congelada"*. O `sexta_verde.png` **do mesmo dia e da mesma pasta** mostra, no rodapé,
`"Oferta valida até quando durarem os estoques"` — o texto genérico de reserva, sem data (e sem
o acento de "válida"). O relatório descreve algo que o arquivo não contém.

### M-07 🟠 `sexta_verde.png`: seis defeitos visuais somados

Na mesma imagem: (a) nenhuma foto de produto — **manchas verdes** (folhas decorativas) espalhadas
fora de lugar; (b) nomes em cinza-escuro sobre foto de supermercado — contraste insuficiente,
quase ilegível; (c) o logotipo da folha "SEXTA VERDE" **sobre** o nome "Creme Dental Kolinos 90g";
(d) o logo Belo Brasil renderizado **sobre um retângulo roxo** — o PNG transparente perdeu o
alfa; (e) preços em branco flutuando sem pílula sobre fundo claro; (f) um **quadrado vermelho
órfão** no topo. Confirma R-06 (fundo esticado), R-07, e a U-13 (cor fora dos tokens).

### M-08 🟠 A hifenização e a caixa das unidades, provadas no artefato

`quintou_p2.png`, texto real renderizado: **"Creme de Lei-te Italac 200G"** (o R-04 ao vivo:
"Lei-te"); e as unidades **em maiúscula em 15 de 15 células** — `200G`, `500G`, `120ML`, `1,5L`,
`25G`, `750ML`, `395G`, `100G`, `1Kg`, `6Kg`, `130G`, `125G`, `170G`, `90G`. A decisão travada do
projeto é explícita: *"unidades minúsculas (g, kg, ml) exceto L"*. Some: **"Racao P/ Cao Adulto
Nino Dog"** (acentos perdidos — Ração, Cão), **"Coxa Sob Coxa"** (palavra truncada — Sobrecoxa),
**"Passatempo Choc/Mor."** (abreviação não expandida).

### M-09 🟠 Nome e preço se sobrepõem, e a última fileira fica vazia

Na fileira 2 e 3 de `quintou_p2.png` o selo de preço é desenhado **por cima** do nome do produto
("Pote Jaguar Multi-Uso 750ML", "Racao P/ Cao Adulto Nino Dog 6Kg"). E a última fileira tem 3 de
4 células, deixando um vazio de ~180 px — o *"tá muito vazio o jornal"* dele, no artefato oficial.

### M-10 🟡 O instalador ocupa 2,7 GB

`medicoes.json`: `"pasta_dist_mb": 2738.0`, `"zip_portatil_mb": 1580.4`, `"arquivos": 10341`,
`"build_segundos": 460.1`. Casa com o CA-01 (os ~973 MB de modelo baixados no boot) — o app
offline pesa mais que muitos jogos.

### M-11 🟡 O PDF do marco sai num tamanho que não é papel nem encarte

`285,8 × 344,0 mm` (proporção 0,831), coerente com os PNG de 1080×1300 — mas não é A4
(210×297), não é o 3:4 (1080×1440) dos 7 encartes novos, e não é um formato de impressão.

---

> ### O que o §17 significa
>
> A lei que o próprio dono escreveu em 18/07 — *"selo só com inspeção visual de TODOS os
> artefatos"* — **foi declarada e não foi cumprida**. Os orçamentos do marco mediram
> **tempo** (0,4 s para exportar, 126 s para conciliar) e **bytes**, nunca **conteúdo**. Por
> isso um tabloide sem nenhuma foto, com validade de maio, com acerto de conciliação zero e
> com duas campanhas faltando passou como "MARCO EXECUTADO".
>
> Isto rebaixa a conclusão do §1. O achado-mãe não é só "a suíte não enxerga gesto": é
> **"nada neste projeto verifica CONTEÚDO na saída"** — nem a suíte, nem o pré-voo, nem o
> relatório do marco. As três camadas de garantia medem a coisa errada.
>
> **Consequência para a ordem:** a Versão 1.0 não é 1.0, e o marco tem de ser reexecutado
> como **porta de saída** de toda a `ORDEM_F13_RESGATE.md` — com inspeção visual página por
> página e com o acerto da conciliação como orçamento, não só o tempo.

---

## §18 · Conformidade: o que ele pediu e nunca foi construído

Frente nova da terceira onda. As duas varreduras procuraram **bugs no que existe**; nenhuma
procurou **ausências**. Cruzei `VISAO_COMPLETA.md`, as 3 transcrições de áudio (nov–dez/2025),
`PESQUISA_TABLOIDE.md`, `REVISAO_GERAL.md` e as 150 recomendações contra o código.

**Veredito honesto: este projeto construiu quase tudo que foi pedido.** A disciplina de
documentação→construção é real, e a maioria dos pedidos obscuros de novembro está implementada.
Os buracos são poucos e específicos:

**K-01 🟠 Produto vendido por peso variável não existe.** Para um supermercado, isso é grande:
`Produto` (`models.py:93-94`) tem `peso_valor`/`peso_unidade` só para compor o NOME ("500g").
Não há flag "vendido por peso" nem exibição "R$/kg". Grep vazio em todo `app/` para `por kg`,
`vendido_por_peso`, `pesavel`, `balanca`. `quilo` só aparece em `sanitize.py:61` como
normalização de texto. ⇒ Carne, frios, hortifrúti — metade dos encartes dele — não têm
como mostrar preço por quilo de forma estruturada.

**K-02 🟡 R-147 (gerador de arte de fundo por IA para datas comemorativas)** estava entre as
141 recomendações **aceitas** e não foi construído. Grep vazio em `app/images`. Isto conecta
direto com o pedido novo dele de "comunicado por data" (§12 do dossiê).

**K-03 🟡 R-116 e R-119 foram aceitas em 18/07 e viraram "vetadas" em `FASE_11.md:5`** sem que
a reversão apareça na lista original dos 9 vetos (`PLANO_PERFEITO.md:25-29`). **Aceite revertido
em silêncio** — o dono aprovou e depois perdeu, sem ser avisado.

**K-04 🟠 O `CLAUDE.md` — a lei do projeto — está desatualizado num ponto que importa.** Ele
ainda manda usar `icrawler` (GoogleImageCrawler) para busca de imagem. O código usa **ddgs
(DuckDuckGo)** desde 08/07, porque "o icrawler quebrou de vez e trazia lixo"
(`PLANO_DE_CONSTRUCAO.md:17`). A troca é justificada; a lei ficou mentindo. *Relevante porque
ele pediu Google explicitamente em nov/2025 e até antecipou o captcha — e nunca soube que a
fonte mudou.*

**K-05 🔵 A IA tem temperatura fixa em todas as tarefas.** `client.py:156`: `temperatura=0.2`
em todo chat; `:182`: `0.0` na visão. Ele imaginou personalidades diferentes por tarefa
(determinística para sanitizar, criativa para Fica-a-Dica/manchete). Nunca diferenciado, nem
exposto em Configurações.

**K-06 🟡 Progresso do OCR é por FASE, não por linha** (adiado de propósito — exigiria
streaming SSE). E a **cascata de imagem por EAN funciona por dentro e é invisível**: a UI de
"Código de barras · Web · Meu acervo" foi cortada (`PLANO_PERFEITO.md:29-31`).

### O pedido mais repetido e menos atendido

Não é uma função. É a primeira coisa que ele disse, antes da primeira linha de código
(*Software*, 19/11/2025): **"Você não vai entregar pronto, assim... eu quero ter muita
participação nisso... você vai ser um guia."** Em 18/07 ele reprova um selo porque o arquiteto
mediu o PDF por bytes e **não olhou a arte** — nasce aí a lei "selo só com inspeção visual".
Em 21/07 o marco é declarado executado medindo tempo e bytes (§17). Em 24/07 ele reabre e diz
"uma bomba". **O padrão se repete a cada marco: certifica-se "PRONTO" por medição de dados, ele
testa com a própria mão, e não resiste ao toque.** Isso não está nas 150 recomendações porque
não é feature — é o contrato de confiança pedido no primeiro dia, e segue sem solução
estrutural. O Bloco A e o Bloco H da ordem existem para virar esse contrato em mecanismo.

---

## §19 · SESSÃO AO VIVO (25/07, 22:26–22:31) — o programa rodando na máquina do dono

Nenhum dos dois auditores havia **executado** o app. O dono liberou o acesso e eu dirigi a
máquina dele por 5 minutos. Tudo abaixo foi visto na tela, não lido no código.
**Nada foi salvo; o layout dele saiu intacto** (desfiz tudo com Ctrl+Z e conferi o painel).

### L-01 🔴 O véu reproduzido em TRÊS CLIQUES, e ele é permanente

Sequência: Início → `Ctrl+K` → `Esc` → clicar em **Mesa**. Aparece o diálogo
**"Recuperar rascunho?"** — o mesmo do quadro 82 da gravação dele. A partir daí a janela
inteira fica sob o véu e **não volta mais**: confirmei em Mesa → Ateliê → editor de layout →
Biblioteca. **Seis transições de tela, ~8 minutos, o véu não saiu.** Só fechar o app resolve.
Isto valida o V-01 por observação, não por leitura.

### L-02 🔴 O gatilho é diálogo modal abrindo DURANTE a troca de tela — e há um SEGUNDO resíduo

Na captura da Mesa, além do véu, aparecem **fantasmas da tela Início** (os cards "40",
"100%", "6", as barras verdes) por baixo da Mesa vazia, com uma **costura vertical visível em
x≈1237**. Isso é a foto estática do `crossfade` (`_veus_troca`, `animacoes.py:318-371`) que
**nunca terminou de desvanecer**: o `QMessageBox.question` estático abriu no meio da
transição, o `exec()` travou o laço de eventos, e a animação morreu pela metade.
E a **paleta de comandos ficou órfã junto** — a caixa "Buscar projeto, produto ou layout…"
continuou desenhada sobre a Mesa, sobre o Ateliê e sobre o editor, mesmo depois de `Esc` e de
clicar fora. **Dois overlays permanentes de uma vez.** O conserto do V-01 sozinho não resolve
isto: o `crossfade` e a paleta precisam de guarda própria.

### L-03 🔴 O diálogo de recuperação está EM INGLÊS

Os botões são **"Yes"** e **"No"** — num app cuja lei é "nomes/UI em PT-BR". Causa:
`QMessageBox.question` **estático** (`mesa.py:1356`) usa os botões padrão do Qt e o app
**não instala tradutor**. Vale para os **17 `QMessageBox` estáticos** do código
(`editor_app.py:498`, `papel_texto_ui.py:307`, `editor.py:346`, `almoxarifado.py:823`,
`cofre.py:396,500`, `configuracoes.py:1061,1090,1122,1152`, `mesa.py:1356,1451`,
`modelos_dialog.py:108,114,126`, `modo_pai.py:291`, `projetos_dialog.py:225`).

### L-04 🟠 "Encontrei um rascunho automático de 20:38 (1 itens)"

Concordância errada — "1 itens". Texto lido na tela, `mesa.py:1358-1360`.

### L-05 🔴 O X e o Esc DESTROEM o rascunho — não existe "depois eu vejo"

`mesa.py:1362-1364`: só `Yes` recupera; **todo o resto cai no `else` → `descartar_rascunhos()`**.
Como `QMessageBox.question` devolve `No` para o X e para o Escape, fechar a janelinha pelo X
— o gesto universal de "me deixa decidir depois" — **apaga o trabalho recuperável**. E o
diálogo não avisa isso em lugar nenhum.

### L-06 🔴 O botão afirmativo é o que tem o foco

Na ampliação, o **"Yes" está com o anel de foco** — Enter o acionaria. Aqui é inofensivo
(recuperar), mas confirma visualmente o padrão que o CF-01 encontrou em
`confirmar_destrutivo` (`componentes.py:171-178`, sem `setDefaultButton`/`setEscapeButton`):
**nas caixas destrutivas, é o botão que apaga que ganha o Enter.**

### L-07 🔴 O "tudo grudado" (E-01), provado com dois cliques

No editor da **Terça do Pão**: clico na ferramenta de imagem → nasce uma região IMAGEM em
`(629-738, 292-337)`, já selecionada. Clico na ferramenta de texto → nasce a região NOME
**no retângulo idêntico**: `(629-738, 292-337)`, mesmas alças, mesma caixa. O painel de
propriedades confirma que são duas regiões distintas ("Tipo: IMAGEM" → "Tipo: NOME") com
geometria coincidente e no mesmo slot. **Nasceram grudadas sem ninguém pedir** — é
determinístico, como o E-01 previu.

### L-08 🔴 Rotação desliga o redimensionar (E-08), provado com um arraste

Pus Rotação = 15° no painel (o texto inclinou, alças nos cantos girados). Arrastei a alça
inferior-direita de `(731,349)` para `(800,400)`: a região **transladou +66,+55 px** — o
próprio vetor do arraste — **mantendo o tamanho**. Não redimensionou.
E varri o painel inteiro na tela: Rótulo, Estilo, Fonte, Tamanho (da fonte), Cor, Alinhar,
Rotação, Peso, Pílula, Opacidade, Sombra, Contorno. **Nenhum campo de Largura ou Altura.**
⇒ Uma região rotacionada não tem, hoje, **nenhum** caminho para mudar de tamanho.

### L-09 🔴 Sair do editor com alterações não salvas NÃO pergunta nada

O título mostrava "AutoTabloide AI **•**" (não salvo). Cliquei em "Biblioteca" e o app
**voltou direto, sem uma palavra**. No meu caso eu já tinha desfeito tudo — mas para ele isso
significa que 20 minutos de layout desaparecem com um clique errado na navegação, **em
silêncio**. Viola I2 e é uma hemorragia do mesmo naipe do CD-01.

### L-10 🟠 A paleta `Ctrl+K` abre fora de lugar e o Esc não a fecha

Ela abre **descentralizada**, flutuando sobre os cards do Início (não no centro da janela).
E depois do `Esc` a caixa continua desenhada — perde o anel de foco e fica de enfeite.

### L-11 🟡 A tela Início desperdiça dois terços do monitor

Maximizada em 3440×1440, o conteúdo termina a ~⅓ da altura; o resto é vazio. Também na tela:
**"Próximo evento: —"** (vazio) e **"Com código de barras: 0%"**. Do lado bom: "Com foto 100%",
"Com preço 100%", **"Com categoria 100%"** — o acervo dele de 40 produtos está categorizado,
confirmando a medição C-04 (o furo do C-01 é estrutural, aparece em acervo migrado/maior).

### L-12 🟠 As medidas ao vivo EXISTEM e são jogadas num rótulo de 6 pixels

Durante o arraste, a barra superior direita mostrou:
`X 149 Y 149 · L 57 A 22 mm → 148 → 19 → 145 → 120 mm · vizinha 2 mm`.
Ou seja: `_emitir_medidas` **já calcula posição, tamanho em mm e distância às vizinhas** — o
material exato da "versão Adobe" (VC-004/VC-010 do caderno de visão) — e despeja num rótulo
minúsculo no canto, ilegível durante o gesto.

### L-13 🔵 Correção de uma suspeita minha

Achei que o painel de camadas não listava as regiões novas. **Errado** — elas estão lá; o
painel só **não rola até a região recém-criada e selecionada**. Achado menor, e fica
registrado que eu errei a primeira leitura.

### L-14 🔵 O marcador "•" de não-salvo não limpa depois de desfazer tudo

Desfiz as três criações com Ctrl+Z, o painel voltou ao estado original e o título continuou
"AutoTabloide AI •".

---

> ### O que a sessão ao vivo mudou
>
> Três coisas. **(1)** O véu deixou de ser hipótese: é reproduzível em 3 cliques e tem
> **dois** resíduos, não um — o conserto proposto no Bloco B precisa cobrir o `crossfade` e a
> paleta, não só `_entrada_dialogo`. **(2)** Apareceram **quatro achados novos que nenhuma
> leitura de código pegaria** (L-03 inglês, L-05 o X que apaga, L-09 sair sem perguntar,
> L-10 a paleta órfã) — três deles no mesmo diálogo de 4 linhas. **(3)** Os dois 🔴 do editor
> que eu tinha afirmado por leitura (E-01, E-08) estão confirmados por gesto — e é exatamente
> isso que a suíte de 851 testes não sabe fazer.
>
> Cinco minutos com a mão no programa renderam 14 achados. É a medida do quanto a bancada
> atual não vê.

---

## §16 · O que este dossiê NÃO cobriu

Vai para a varredura paralela do Code — ver `docs/BRIEFING_VARREDURA_CODE.md`:
instalador/PyInstaller e primeira execução em Windows limpo; `.atproj`/`.attpl`/Cofre em
caso de arquivo corrompido; `app/scripts/*` (12 arquivos fora do caminho de teste);
`src/` (protótipo antigo ainda no repositório); histórico/undo-redo sob estresse;
`app/core/atualizacao.py` e `diagnostico.py`; acessibilidade de teclado ponta a ponta
(navegar o app inteiro sem mouse); comportamento com 2 monitores e DPI fracionário;
`app/rendering/secoes.py` e `imposicao.py` em profundidade; e a **execução real da suíte
na máquina do dono** (aqui o sandbox Linux não tem PySide6 — todos os números de teste
deste dossiê são de leitura estática).

---

*Fim do dossiê. Nenhum arquivo do programa foi modificado nesta auditoria.*
