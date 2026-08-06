# BRIEFING DE VARREDURA PARALELA — para o Code (builder)

> **Emitido pelo arquiteto (Cowork) em 24/07/2026.** Ordem do dono: *"Você e o Code devem
> trabalhar em conjunto para acharem todas as quebras do programa e lógicas ruins. **Por
> enquanto não é pra consertar nada.** Vocês dois vão debulhar cada milímetro de código."*
>
> ## REGRA ZERO — ESTA FASE NÃO CONSERTA
> Você **não** edita nenhum arquivo de `app/`, `src/`, `alembic/` ou config.
> Você **não** abre PR. Você **não** "conserta enquanto passa".
> Se encontrar um bug de 1 linha óbvio: **anote e siga**. O dono decide depois o que entra.
> Ideia boa também não se implementa nesta fase — vai para o caderno de visão (§7).
> As únicas escritas permitidas são criar/atualizar **`docs/VARREDURA_CODE_F13.md`** (os
> defeitos) e **`docs/VISAO_CODE_F13.md`** (as melhorias e adições que você enxergar).
>
> **Este briefing tem DUAS metades de igual peso:** §2–§6 é o que está quebrado;
> **§7 é o que o programa ainda pode ser.** Não entregue só a primeira.

---

## 1 · Divisão de trabalho (não duplique o que já foi feito)

Eu já varri e catalogei **133 achados** em `docs/DOSSIE_AUDITORIA_F13.md`. Leia esse
documento **primeiro e inteiro** — ele é o seu mapa de "já coberto".

**JÁ COBERTO (não repita a varredura; só use como contexto):**

| Frente | Onde | Achados |
|---|---|---|
| Véu de diálogo / tela escura | `qt/design/animacoes.py` | V-01..05 |
| Seleção, trio, agrupar, duplicar, carimbar, selos, célula-mestre | `qt/canvas.py`, `qt/itens.py`, `qt/editor.py`, `telas/atelie.py`, `rendering/grade.py` | E-01..13 |
| Compositor: z-order, alinhamento, ajuste, hifenização | `rendering/compositor.py`, `text_fit.py`, `model.py`, `painel_camadas.py`, `painel_propriedades.py` | R-01..11 |
| Pré-voo, validade, aprovação, RASCUNHO (9 portas), rascunho automático | `telas/servico.py`, `telas/mesa.py`, `core/projetos.py`, `telas/prevoo.py`, `core/rascunho.py` | P-01..10 |
| Categoria, auto-preencher, heróis, sanitização que apaga, conciliação | `telas/servico.py`, `ai/enriquecimento.py`, `ai/pipeline.py`, `telas/conciliacao_dialog.py` | C-01..13 |
| Imagens: rembg, overlay, troca de foto | `images/*`, `qt/workers.py`, `qt/design/carregando.py` | I-01..06 |
| Desempenho: boot, recompose, miniaturas, N+1 | `qt/editor_app.py`, `canvas.py`, `atelie.py`, `faixa_paginas.py` | X-01..11 |
| Fábrica, cartaz, etiquetas, publicar, Modo Pai | `telas/fabrica.py`, `rendering/cartaz.py`, `imposicao.py`, `telas/publicar_dialog.py`, `telas/modo_pai.py` | F-01..06 |
| Banco, persistência, alembic, portabilidade | `core/models.py`, `database.py`, `repositories.py`, `portabilidade.py`, `lixeira.py`, `recuperacao.py`, `deduplicacao.py` | D-01..14 |
| Almoxarifado, Inteligência, IA colega | `telas/almoxarifado.py`, `telas/inteligencia.py`, `ai/revisora.py`, `core/aprendizado.py` | A-01..09 |
| Descoberta / UX / atalhos / jargão / tema / 720p | `qt/design/*`, todos os `telas/*` | U-01..19 |
| Suíte de testes (o achado-mãe) | `app/tests/` | T-01..10 |
| Encartes novos (geometria dos 7) | `Templates novos/geradores/*` | N-01..08 |

---

## 2 · SUAS 8 FRENTES (ninguém varreu — são suas)

### F-A · Instalador e primeira execução em Windows limpo 🔴 prioridade máxima
`autotabloide.spec`, `lancar_autotabloide.py`, `dist/`, `AutoTabloide_System_Root/`.
O CLAUDE.md diz que o exe "meio-morto em Windows limpo" foi um dos 3 achados críticos da
frota da F12 e foi corrigido — **reverifique**, porque o dono está rodando por `pythonw`
(Etapa 1 da gravação: `Executar` → linha de comando), não pelo instalador.
- Todo `hiddenimports`/`datas` do `.spec` está coerente com os imports dinâmicos reais?
  Cace todo `importlib`, `__import__`, import dentro de função, e plugin de Qt.
- O que acontece na 1ª execução sem `AutoTabloide_System_Root`? Sem fontes instaladas?
  Sem modelo do rembg baixado? Sem LM Studio? Sem escrita permitida na pasta?
- A raiz IRMÃ e o "desinstalar preserva o acervo" ainda valem no código?
- **Onde o app grava** quando instalado em `C:\Program Files` (pasta sem permissão de escrita)?

### F-B · Arquivo corrompido, `.atproj`, `.attpl`, Cofre, somente-leitura 🔴
`core/atproj.py`, `core/template_compartilhavel.py`, `core/cofre.py`, `core/recuperacao.py`,
`core/modo.py`, `core/atualizacao.py`, `core/diagnostico.py`, `core/manutencao.py`.
- Abra mentalmente cada arquivo truncado / com JSON inválido / com `versao_schema` futura /
  com zip bomba / com caminho `../` no zip (**path traversal** — cheque `extractall`).
- `.atproj` de outra máquina com fonte que não existe aqui: o que acontece?
- Somente-leitura (R-131): tem furo? Alguma porta escreve mesmo assim? (Compare com o
  achado U-08 do dossiê: Ctrl+K furou o Modo Pai — procure o mesmo padrão aqui.)
- `atualizacao.py`: o que ele faz de fato? Baixa algo? De onde? Com que verificação?

### F-C · `app/scripts/*` — 12 arquivos fora do caminho de teste 🟠
`enriquecer_banco.py`, `selfcheck_marco.py`, `demo_pipeline.py` e os outros.
Já sei de um: `enriquecer_banco.py:55` descarta a categoria se o nome não mudou (C-02) e
`:29,86` reimplementa a checagem de IA (A-09). **Varra os 12.** Estes scripts alimentam
botões da UI — bug aqui é bug de produto, não de ferramenta.

### F-D · Histórico, undo/redo e desfazer sob estresse 🟠
`qt/historico.py`, `canvas.py` (`_registrar_hist`), `mesa.py` (Ctrl+Z / Ctrl+Shift+Z).
Na gravação o dono aperta **Ctrl-Z 9 vezes** em 4 rajadas (Etapas 28, 48, 57) — ele estava
tentando desfazer o estrago do agrupamento acidental.
- O que **não** entra no histórico? (Suspeitas: agrupar/desagrupar, carimbar modelo,
  propagação da mestra, override, reordenar camada, mudar página.)
- Desfazer depois de agrupar restaura o `Slot` original ou deixa órfão?
- Limite de pilha, consumo de memória, e se o histórico do editor e o da Mesa se confundem.
- **Teste-chave a propor:** desfazer/refazer 20× e conferir por CONTEÚDO (pixel) que a
  página voltou byte-idêntica.

### F-E · `app/rendering/secoes.py` e `imposicao.py` a fundo 🟡
O dono quer seções por categoria no Jornal do Mês, e o pacote de encartes **não traz seção
na arte** (achado N-05) — o app tem de desenhar. Audite `secoes.py` inteiro: como calcula a
faixa, o que acontece com 1 categoria só, com nome longo, com categoria vazia, e se respeita
o tema. Em `imposicao.py`: sobra da folha, marcas de corte, e o achado F-05 do dossiê.

### F-F · Teclado ponta a ponta e acessibilidade 🟡
Tente navegar o app inteiro **sem mouse**, lendo o código: ordem de tabulação
(`setTabOrder`), foco inicial de cada diálogo, botão default, Esc fechando, e onde o foco
"desaparece". `test_isolamento.py:206-213` documenta que o Tab já foi roubado uma vez — ache
os outros. Cheque também `setAccessibleName` / rótulos para leitor de tela.

### F-G · Dois monitores, DPI fracionário, 3440×1440 🟡
O dono roda em **3440×1440** (as capturas provam) e o CLAUDE.md fala de caber em 720p.
Procure toda geometria em px absoluto, `setFixedSize`, `move()` com coordenada calculada,
`screen()` assumindo tela primária, e qualquer conta que não passe por `devicePixelRatio`.
Já sei de um: `conciliacao_dialog.py:170` `resize(1200,760)` (U-14).

### F-H · `src/` — o protótipo antigo ainda no repositório 🟡
`src/` tem código de dezembro/2025 que o CLAUDE.md manda **descartar** (rasterizador
CairoSVG, camada industrial). Ele ainda está lá. Verifique: algum módulo de `app/` importa
de `src/`? O `.spec` empacota `src/`? Há import morto que ainda arrasta dependência
pesada? Se é lixo, isto é dívida documentada — reporte, não apague.

---

## 3 · A SUA TAREFA MAIS IMPORTANTE: rodar a suíte de verdade

Eu não pude rodar `pytest` — este sandbox não tem PySide6. **Todos os números de teste do
meu dossiê são de leitura estática.** Você está na máquina real. Portanto:

1. `pytest app/tests -q` — reporte **passados, falhas, skips e o tempo**. Se houver skip,
   diga qual e por quê (§T-08 do dossiê: 3 `skipif` dependem de `Path("arte/quintou")`
   **relativo ao CWD** — rode de duas pastas diferentes e compare).
2. Rode **duas vezes** e compare — o projeto tem histórico de segfault intermitente.
3. `pytest app/tests -q -p no:randomly` vs ordem embaralhada, se disponível: alguma coisa
   depende de ordem? (§T-09: `lru_cache` em `fontes.py:64,145` e `servico.py:365` exige
   `cache_clear()` manual.)
4. **Confirme ou refute o achado-mãe com números seus**: quantos testes tocam o canvas por
   gesto real? Rode uma varredura sua de `QTest`, `sendEvent`, `.trigger()`, `dropEvent`.
5. **Prova de mutação dirigida** (não conserte — só prove): escolha 6 achados 🔴 do meu
   dossiê e, para cada um, **quebre de propósito** a linha citada e veja se **algum** teste
   fica vermelho. Depois **desfaça a mutação** (`git checkout -- <arquivo>`). Reporte:
   "achado X: 0 testes pegaram". Sugestões de alvo: `animacoes.py:287` (V-01),
   `canvas.py:1396` (E-01), `painel_camadas.py:67` (R-02), `itens.py:438` (E-08),
   `servico.py:1858` (F-01), `compositor.py:312` (R-01).
   **Isto é o dado mais valioso que você pode produzir nesta fase.**

---

## 4 · Formato obrigatório de cada achado

Escreva em `docs/VARREDURA_CODE_F13.md`, um bloco por achado, com prefixo da sua frente
(`CA-01`, `CB-01`, …). Nada de prosa sem linha.

```
### CA-07 🟠 Título curto e afirmativo
**Sintoma potencial:** o que o dono veria/perderia (em português de dono de mercado).
**Evidência:** arquivo.py:123-127 — cole as 2-4 linhas que provam.
**Mecanismo:** por que acontece, em 1-3 frases.
**Classe:** bug confirmado por leitura | risco não provado | lacuna (nunca foi feito)
           | lógica porca (funciona, mas mal) | reivindicação falsa do CLAUDE.md
**Coberto por teste?** sim (arquivo:linha) / NÃO
**Invariante ferida:** I1 | I2 | I3 | I4 | I5 | nenhuma
```

Severidade: 🔴 o dono perde trabalho, perde dado, ou publica peça errada · 🟠 o dono
trava ou perde muito tempo · 🟡 fricção/inconsistência · 🔵 dívida técnica.

---

## 5 · Régua de julgamento (use as leis do próprio projeto)

- **I1** vínculo por ID estável, nunca por índice/posição.
- **I2** nada de degradação silenciosa — conteúdo ausente/inválido em salvar/exportar/importar
  tem de aparecer para o dono.
- **I3** nenhum caminho absoluto em JSON persistido.
- **I4** mestra↔célula por `ref_mestre` (uid), imune a z-order.
- **I5** teste adversarial verifica por CONTEÚDO (pixel/byte), nunca por "não deu exceção".
- **Lei do CLAUDE.md:** "teste que precisa de filtro próprio para passar = mascaramento".
- **Lei do CLAUDE.md:** "skip silencioso não é verde".
- **Lei nova, desta auditoria:** *chamar o método interno não prova que o menu funciona.*

E duas perguntas que devem acompanhar cada arquivo que você abrir:
1. **"O dono saberia que isso aconteceu?"** Se não, é candidato a violação de I2.
2. **"Se eu quebrasse esta linha, algum teste ficaria vermelho?"** Se não, anote junto ao achado.

---

## 6 · Honestidade de bancada

Lei do projeto: bug seu, achado pelos seus próprios testes, é **documentado na resposta**,
nunca escondido. Vale também para esta varredura: se você discordar de um achado meu do
dossiê, **diga com a linha** — eu já tive de derrubar a conclusão de um dos meus 12 agentes
lendo a fonte (§14 do dossiê, o caso do véu: a linha *parece* limpeza e não é).
Discordância documentada vale mais que concordância.

---

## 7 · A SEGUNDA METADE DO SEU TRABALHO: SER VISIONÁRIO

Ordem literal do dono: *"seja visionário e entenda adições e outras coisas para serem feitas
e melhoradas enquanto você mesmo audita. Aproveita que vai analisar um monte e faz desse
trabalho algo eficiente — tipo 'formas para melhorar o editor em algo digno de um programa
da Adobe', ou sugestões de outras lógicas de execução, para ficar extremamente perfeito, sem
falhas e com uma qualidade de vida absurda em tudo quanto é mínima função e feature."*

Você vai abrir ~120 arquivos nesta varredura. **Cada arquivo aberto é uma oportunidade
paga.** Enquanto o contexto daquele módulo está na sua cabeça, escreva também o que **falta**
ali — não só o que está errado. É a diferença entre uma auditoria e um projeto.

**A regra continua: escrever, não construir.** Ideia visionária vai para o caderno, não para
o código. Segundo entregável, arquivo separado: `docs/VISAO_CODE_F13.md`.

### 7.1 · A régua: qual é a versão "Adobe" disto?

Para cada tela, pergunte-se: **como Illustrator / InDesign / Affinity / Figma / Canva
resolvem este exato problema, e por que a solução deles é melhor?** Não para copiar a
interface — para roubar o *raciocínio*.

O insight de posicionamento que deve guiar tudo: **este app é, no fundo, um
`Data Merge` do InDesign com OCR e recorte de fundo embutidos.** InDesign chama de "mala
direta de dados": um layout com campos, uma fonte de dados, N peças geradas. É literalmente
o produto. Então vale estudar o que o Data Merge tem e o AutoTabloide não: pré-visualização
de registro por registro, "criar páginas múltiplas automaticamente", ajuste de imagem por
campo, tratamento de campo vazio, e relatório de overflow. **Cada um desses tem um paralelo
direto aqui.**

Perguntas-régua por frente:

- **Editor (Ateliê)** — o que um editor gráfico sério tem que este não tem? Pense em: réguas
  arrastáveis e guias, guias inteligentes com medida ao vivo, snapping a objeto e a margem,
  alinhar/distribuir com "espaçamento igual", ferramenta de transformação com ponto de
  âncora escolhível, `Ctrl+D` como "repetir última transformação" (não duplicar),
  estilos de parágrafo/caractere reusáveis, biblioteca de componentes, máscara de recorte
  não-destrutiva, painel de camadas em **árvore** (célula → peças) com arrastar para
  reordenar, zoom para seleção, modo contorno, teclas de seta com Shift para passo grande,
  Alt+arrastar para duplicar, bloqueio/ocultar por camada, e **medida em tempo real durante
  o arrasto**. Diga quais desses valem para o caso dele e quais são luxo.
- **Mesa** — se isto é uma linha de montagem, onde estão as estações? O que seria uma "fila
  de trabalho" de verdade (o que está pronto, o que falta foto, o que falta preço, o que
  está suspeito), com progresso visível e a possibilidade de o dono trabalhar em outra coisa
  enquanto a máquina mói?
- **Imagens** — qual é a versão "Photoshop" do Estúdio? Pense em curadoria em lote, fila com
  progresso, comparação antes/depois, sombra e luz consistentes entre fotos da mesma peça,
  e detecção automática de foto ruim antes de ela chegar ao tabloide.
- **IA** — qual é o papel de copiloto que ela ainda não cumpre? Não "mais IA": IA no lugar
  certo, sempre como sugestão clicável, nunca como veto (lei F9 do projeto).
- **Dados** — o app já guarda histórico de preço e ranking e quase não usa. O que dá para
  responder com o que já está no banco?

### 7.2 · Lógicas de execução (arquitetura) — o pedido explícito dele

O dono pediu "**sugestões de outras lógicas de execução**". Isso é convite para propor
mudanças estruturais. Avalie e escreva parecer sobre, no mínimo:

1. **Comando/undo como objeto** (padrão Command) em vez do histórico atual por snapshot —
   habilita undo granular, macros, "repetir última ação", e log de auditoria. Cruze com a
   sua frente F-D.
2. **Renderização incremental**: dirty-rect / cache por slot em vez de `compor_pagina`
   inteiro a cada tecla (achados X-01 e X-04 do dossiê). Vale um cache por região com
   invalidação por hash dos dados?
3. **Fila de trabalho única** (job queue com prioridade, progresso, cancelar, retomar) em
   vez de `Trabalhador`/`TrabalhadorFila` espalhados — resolve I-01, I-03, X-02 de uma vez.
4. **Barramento de eventos / modelo observável** em vez de cada tela chamar `recarregar()`:
   a dessincronia entre estante, canvas e banco é sintoma disto.
5. **Camada de projeção (view-model) entre `Slot` e o canvas**: hoje `Slot.regioes` **é** a
   célula, e é essa fusão que causa o "tudo grudado" (E-01/E-02). Existe um desenho em que
   agrupamento visual e slot de dados são coisas separadas? Se sim, esboce.
6. **Pipeline declarativo de composição** (lista de passos plugáveis) em vez do
   `compor_pagina` monolítico de 70 linhas — abriria espaço para efeitos, seções, selos e
   marca d'água sem mais `if`.
7. **Esquema de dados versionado de verdade** (achado D-11: alembic morto) — o que substitui?
8. **Modelo de plugin/receita** para os 7 encartes: eles são dados ou código? Se cada encarte
   novo exigir código, o dono depende de programador para sempre — o que é o oposto do produto.

Para cada uma: **o que resolve, o que custa, o que quebra, e se dá para fazer por partes.**
Prefira propostas incrementais a reescritas — o projeto tem 67 mil linhas funcionando.

### 7.3 · A lei do "enquanto você está aí"

Ao terminar de auditar **cada arquivo**, gaste 60 segundos escrevendo:

- **1 atalho** que faltou ali;
- **1 feedback** que o dono deveria receber e não recebe;
- **1 automação** que eliminaria um passo manual;
- **1 pré-visualização** que evitaria um erro antes de acontecer;
- **1 valor padrão** melhor que o atual (padrão bom vale mais que opção nova).

Isso é o que o dono chama de "qualidade de vida absurda em tudo quanto é mínima função".
A maioria das melhorias reais deste app não são features novas — são **defaults melhores,
feedback e um atalho**.

### 7.4 · A meta que mede tudo: 20 minutos → 5 minutos

Toda sugestão deve responder: **quantos segundos ou quantos cliques isso tira do dia dele?**
Reconstrua o fluxo real (foto da tabela → tabloide exportado, 30 itens) em passos com
estimativa de tempo, e proponha o fluxo ideal ao lado, também cronometrado. Um quadro
"hoje × ideal", passo por passo, vale mais que dez parágrafos. Onde o tempo é da máquina
(rembg, OCR), a pergunta é "como isso roda enquanto ele faz outra coisa?"; onde é dele,
é "como isso vira um clique?".

### 7.5 · Formato de cada sugestão

Em `docs/VISAO_CODE_F13.md`, prefixo `VC-`:

```
### VC-014 · Guias inteligentes com medida ao vivo no canvas
**Dor que resolve:** achado E-01/U-04 — ele arrasta às cegas e não sabe se alinhou.
**A versão Adobe:** no Illustrator, arrastar mostra a distância às vizinhas e "gruda" nas
bordas e no centro; as guias aparecem só durante o gesto.
**O que existe aqui já:** `app/qt/alinhamento.py` (snapping) — falta o desenho e a medida.
**Ganho para o dono:** monta uma célula sem abrir o painel; ~15 s por célula × 30 células.
**Custo:** M (pintura no canvas + 1 flag em Config).
**Depende de:** nada.
**Trava do CLAUDE.md ferida:** nenhuma.
**Grau:** ESSENCIAL | ALTO VALOR | LUXO
```

Feche o caderno com um **quadro de priorização**: ganho (alto/médio/baixo) × custo (P/M/G),
e o **"time dos 10"** — as dez que, juntas, mais aproximam do "5 minutos".

### 7.6 · Limites — para a visão não virar fantasia

- **Não proponha nada nos vetos travados** do CLAUDE.md: custo/margem de lucro, diário de
  alterações, backup em nuvem, ERP, scanner de código de barras, imposição NUP no tabloide,
  camada "industrial" (watchdog, resiliência de missão crítica, RAG), criptografia pesada,
  kit de campanha social. Se achar que um veto envelheceu, **argumente em uma seção
  separada** ("vetos que eu questionaria e por quê") — não misture com as propostas.
- **Offline e local continuam sendo lei.** Nada que exija nuvem, conta, assinatura ou
  internet obrigatória.
- **Nada que exija GPU como requisito** — GPU só como degrau opcional.
- **O dono não é programador.** Toda sugestão precisa passar no teste: "ele consegue usar
  isso sozinho, sem manual?"
- **Separe honestamente ESSENCIAL de LUXO.** Uma lista de 200 ideias sem grau é inútil;
  30 ideias graduadas mudam o produto. Se uma sugestão sua é gold-plating, diga que é.
- **Marque o que é lacuna de produto e não bug** (como o "comunicado" do §12 do dossiê:
  zero ocorrências em todo `app/`) — o dono precisa saber a diferença entre "quebrou" e
  "nunca existiu".

---

## 8 · Ao terminar

1. `docs/VARREDURA_CODE_F13.md` com todos os achados no formato do §4.
2. `docs/VISAO_CODE_F13.md` com as sugestões no formato do §7.5, o quadro de priorização,
   o "time dos 10", o quadro "hoje × ideal" do §7.4 e o parecer de arquitetura do §7.2.
3. No fim do primeiro documento, três seções:
   - **"O QUE EU CONFIRMEI DO DOSSIÊ"** — achados meus que você reproduziu, com prova.
   - **"O QUE EU REFUTO DO DOSSIÊ"** — com arquivo:linha.
   - **"PROVA DE MUTAÇÃO"** — a tabela dos 6 achados 🔴 × quantos testes pegaram.
4. **PARE.** Não comece conserto nenhum, nem implemente sugestão nenhuma. Responda ao
   arquiteto e ao Otaviano com: placar por severidade, os 10 piores achados seus, as 10
   melhores ideias suas, e o que ficou de fora da sua varredura.

O plano de conserto — e o de evolução — só nasce depois que os dois dossiês e os dois
cadernos de visão estiverem na mesa e o Otaviano disser por onde começar.

O plano de conserto só nasce depois que os dois dossiês estiverem na mesa e o Otaviano
disser por onde começar.
