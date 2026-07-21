# Ordem de Serviço — Bloco E (Casos avançados) + dívidas do radar

> Emitida em 2026-07-09 pelo arquiteto (Cowork). **Normativa** — sucede a
> `ORDEM_BLOCO_D.md` (Bloco D FECHADO). Invariantes I1–I5 valem. Etapas
> **A → B → C → D → E**, cada uma com suíte verde + zero skips na máquina
> real e PARADA no ponto de reauditoria. **Regra nova desta ordem (decisão do
> Otaviano): sem sessões ao vivo e sem lição de casa dele até o programa
> estar praticamente completo — o arquiteto valida por artefatos** (exports,
> PDFs medidos, screenshots dos scripts de demo). A validação humana final
> concentra tudo na revisão geral pré-lançamento (F8/G).

## Etapa A — Dívidas do radar (pequenas, zerar antes de coisa nova)

- **A1.** Dedup do "X (importado)" nos layouts `MANTER_AMBOS` (padrão do
  `_nome_variante`).
- **A2.** Janela `analisar→aplicar`: revalidar as chaves naturais no
  `aplicar` (produto criado localmente entre as fases → vira conflito novo,
  erro nominal pedindo re-análise; nunca duplicata silenciosa).
- **A3.** Cura na raiz do caminho absoluto da arte de layout no banco VIVO:
  arte importada pelo Ateliê passa a ser COPIADA para pasta gerenciada da
  raiz (`layouts/`) e gravada relativa; migração dos layouts existentes na
  primeira abertura (com aviso do que migrou); a relativização na fronteira
  do pacote continua como defesa em profundidade.
- **A4.** Matriz grade-override × estilo-override: documentar o contrato em
  docstring de produção (hoje só em teste).

## Etapa B — F7.3: override por slot + undo completo da Mesa

- **B1.** Modal de override por slot na Mesa (o `overrides_json` reservado
  desde o F6.8): editar por CÉLULA nome/preço/imagem/arranjo sem tocar no
  item da estante. Persistência por **`slot_id` → {campo: valor}** no projeto
  (identidade, nunca posição — I1). Precedência: override do slot > item da
  estante > banco (a cadeia da visão §3.1).
- **B2.** Célula com override ganha indicador visual e "Restaurar do item"
  (paridade com o padrão mestra/estilo — 3ª aparição do mesmo conceito, mesma
  UX).
- **B3.** O histórico da Mesa versiona {layout, mapa, overrides} — desfazer
  um override restaura o anterior. Adversarial: overrides sobrevivem a
  salvar→reabrir→duplicar e NÃO vazam entre células (por conteúdo).

## Etapa C — F7.1: vários sabores/fragrâncias num slot

- **C1.** Item da estante ganha modo multi-imagem pela UI (o motor F4.5 —
  `imagens` + `ModoArranjo` — já existe e o pré-voo já valida cada foto):
  na curadoria, "adicionar mais imagens" com busca assistida — a IA sugere
  TERMOS (sabores prováveis do produto), o humano escolhe as fotos.
  **IA nunca escolhe a imagem sozinha** (anti-alucinação da visão).
- **C2.** Arranjo (LEQUE/LADO_A_LADO/GRADE) selecionável por item na Mesa e
  por override de slot (B1).

## Etapa D — F7.2: dois produtos num slot (Camil e Rei)

**Decisão de identidade OBRIGATÓRIA:** o mapa é e continua **1 slot → 1
uid**. Dois produtos viram **UM item composto na estante** — uid próprio,
nome montado ("Arroz Camil e Rei 5kg"), 2 imagens (LADO_A_LADO por padrão),
preço único — com os `produto_id` de origem guardados no item (rastreável e
desfazível: "separar" devolve os dois itens). É PROIBIDO haver dois uids num
slot ou meio-uid em dois slots. Adversarial: tentar compor/separar/reabrir
não pode duplicar uid nem órfão no mapa.

## Etapa E — F7.5: exportação CMYK opcional

- **E1.** Conversão SÓ na exportação, via Ghostscript (que já está no
  ambiente), com perfil configurável na Config; **RGB continua o padrão e o
  caminho RGB fica byte-idêntico ao atual** (teste de regressão).
- **E2.** Teste confere `/DeviceCMYK` no PDF convertido e o tamanho físico
  intacto (pypdf). Ghostscript ausente → degrada COM aviso (I2), nunca trava
  o export RGB.

## Resposta do builder — Etapa A executada (2026-07-09)

Linha de base: **249 verdes, zero skips**. Ao fechar: **256 verdes, zero
skips** na máquina real (7 testes novos) + **os dois adversariais (vínculo e
portabilidade) re-rodados verdes** — a A3 tocou persistência, então rodaram
por obrigação, não por hábito.

- **A1 ✓** — Layout `MANTER_AMBOS` deduplica no padrão do `_nome_variante`:
  "X (importado)", "X (importado 2)"… Teste importa DUAS vezes com a mesma
  decisão e confere os dois nomes.
- **A2 ✓** — `aplicar_importacao` **revalida as chaves naturais** contra o
  acervo FRESCO antes de gravar: produto criado localmente entre as fases →
  `ValueError` nominal ("criados aqui depois da análise: … — re-analise o
  pacote"); cobre também produto REMOVIDO e produto RENOMEADO entre as
  fases (o conflito apontaria para outra identidade). Teste: cria o produto
  entre analisar e aplicar → erro, zero duplicatas; re-análise enxerga o
  conflito novo e o fluxo segue.
- **A3 ✓ (a cura na raiz)** — `persistencia.py` ganhou o par
  `internar_arte`/`resolver_arte`: **salvar layout COPIA a arte para
  `<raiz>/layouts/` e grava RELATIVO** (coluna + `estrutura_json` + fundos
  por página), com nome anti-colisão (mesmo nome, bytes diferentes →
  sufixo) e sem duplicar no re-salvar; `carregar_layout` resolve de volta;
  o `LayoutDef` do chamador nunca é mutado (a tela segue usável).
  **Migração** `migrar_artes_absolutas` na abertura (gancho nos DOIS pontos
  de entrada, com toast no shell + detalhe no console — I2): layout antigo
  com caminho de máquina migra; arte sumida mantém o rastro e AVISA a cada
  abertura até o humano resolver. Semântica do resolver: relativo que não
  existe na pasta fica como veio (rastro visível ao pré-voo) em vez de
  apontar para um absoluto fantasma. Dependentes ajustados: miniatura do
  Ateliê resolve; `_layout_id_por_nome` dos projetos interna; a
  portabilidade **exporta resolvendo relativos da raiz de ORIGEM** e
  **importa gravando na convenção nova (relativo)** — a relativização na
  fronteira continua como defesa em profundidade. 5 testes novos
  (`test_arte_relativa.py`), incluindo o pacote ponta a ponta na convenção
  nova.
- **A4 ✓** — Matriz grade-override × estilo-override agora é **docstring
  normativa em `app/rendering/estilos.py`** (dois conjuntos independentes;
  edição em derivada-com-estilo marca os dois; propagação respeita
  `overrides` e não toca `overrides_estilo`; cada "Restaurar" limpa só o
  seu; precedência final: ajuste local > estilo > mestra), com referência
  cruzada no `propagar_mestre` da grade.

**O que ficou de fora (Etapa A):**

- A migração NÃO reescreve a arte congelada dos projetos salvos (eles têm
  cópia própria por pasta — não precisam e não devem ser tocados).
- Layout com arte sumida repete o aviso a cada abertura (decisão: lembrete
  até resolver, em vez de silenciar após o 1º aviso).
- `test_salvar_e_carregar_layout` (consolidação) segue passando SEM edição
  — a semântica "resolve só o que existe" foi escolha de produção, não
  ajuste de teste.
- A revalidação da A2 cobre produtos; layout criado localmente entre as
  fases com o mesmo nome de um "layouts_novos" do pacote ainda não é
  revalidado (viraria linha dupla na biblioteca, sem risco de acervo/foto
  — anotado para o radar).

**PARADO no ponto de reauditoria.** Etapa B (F7.3 — override por slot) só
começa com o selo do arquiteto.

## SELO do arquiteto — Etapa A (2026-07-09): APROVADA

Reauditoria na fonte: `internar_arte` com semântica completa (já-relativo
passa, absoluto da própria pasta só relativiza, sumida mantém rastro,
anti-colisão por BYTES com sufixo, re-salvar não duplica); `resolver_arte`
deixa o relativo inexistente como veio (rastro visível ao pré-voo — escolha
de produção correta, não ajuste de teste); `migrar_artes_absolutas`
idempotente com aviso repetido até o humano resolver (decisão certa: lembrete
> silêncio); revalidação da A2 com erro nominal cobrindo criado/removido/
renomeado entre as fases; A4 normativa em produção. O item novo de radar
(layout criado entre as fases → linha dupla na biblioteca, sem risco de
acervo) foi anotado com honestidade — fica para a próxima varredura de radar.
Os dois adversariais re-rodados por obrigação = o reflexo que o protocolo
queria criar. **256 verdes, zero skips aceitos. Etapa B (F7.3) AUTORIZADA** —
o overrides por `slot_id` é a 3ª aparição do padrão de precedência do app:
mesma semântica, mesma UX, e o adversarial B3 (overrides não vazam entre
células, por conteúdo) é o crítico.

## Resposta do builder — Etapa B executada (2026-07-09)

Linha de base: **256 verdes, zero skips**. Ao fechar: **263 verdes, zero
skips** na máquina real (6 em `test_override_slot.py` + 1 adversarial novo)
+ os DOIS adversariais re-rodados verdes.

- **B1 ✓** — Botão direito numa célula da Mesa → **"Conteúdo desta célula
  (override)…"**: `OverrideDialog` edita nome/preço/foto/arranjo SÓ daquela
  célula (campo vazio herda; o placeholder mostra o valor herdado do item).
  A regra mora na produção: `servico.aplicar_override` implementa a cadeia
  **override do slot > item da estante > banco** (§3.1), aplicada num ponto
  ÚNICO (`_dados_por_slot`) — preview, pré-voo, export e a miniatura do
  Dashboard enxergam a mesma precedência. Persistência por **`slot_id`**
  (I1) no `overrides_json` do projeto (o reservado do F6.8); a **foto do
  override congela na pasta do projeto** (relativa — I3), na mesma regra
  das fotos dos itens. Override de foto em item multi-imagem vira foto
  única (a foto forçada não se mistura). O gesto existe SÓ na Mesa (o
  canvas ganhou `ao_override`; no Ateliê a entrada nem aparece — não há
  item para sobrepor).
- **B2 ✓** — **Pontinho VIOLETA** nas regiões da célula com override
  (âmbar continua sendo o da grade — os dois convivem) + **"Restaurar do
  item (N campos)"** no mesmo menu, a 3ª aparição da UX de restaurar
  (mestra → estilo → item).
- **B3 ✓** — `Historico` versiona **{layout, mapa, overrides}** (o D5
  estendido; `test_historico` antigo passou SEM edição — o contrato usa
  `estado[0]`); `set_override` passa pelo MESMO caminho do undo
  (`ao_restaurar`) — desfazer um override restaura o ANTERIOR, estado a
  estado, e refazer volta. **"Substituir tudo" e abrir outro projeto zeram
  os overrides** (nada vaza entre tabloides). Override órfão (célula
  removida) **acusado no pré-voo** junto dos órfãos do mapa. **Adversarial
  (I5) atualizado**: `test_adversarial_override_por_slot` confere POR
  PIXEL/BYTE que o override rende só na célula dele (as vizinhas ficam com
  a cor do próprio item), não toca o item da estante, resiste a shuffle da
  estante + reordenação do mapa, sobrevive a salvar→reabrir→duplicar com a
  foto congelada **byte-idêntica** (apagar a original do disco não afeta o
  congelado), o JSON persistido é relativo (sem caminho de máquina), e o
  undo volta o anterior.

**Achado de bancada (documentado): `_avisos_orfaos` da Mesa só olhava os
slots da PÁGINA 1** — num layout frente+verso, itens da página 2 seriam
acusados como "célula removida" no pré-voo. Corrigido para todas as
páginas (mapa E overrides); a suíte inteira segue verde.

**O que ficou de fora (Etapa B):**

- O campo "arranjo" do override já funciona no motor (F4.5 é headless),
  mas só ganha efeito VISÍVEL quando o item tiver várias fotos pela UI —
  exatamente a Etapa C.
- O indicador violeta desenha em cada região da célula (não um selo único
  por célula) — consistente com o pontinho âmbar; polimento cosmético se
  incomodar.
- Override de "de"/validade não entrou (Mesa é tabloide; no cartaz esses
  campos já são por item na Fábrica).
- A foto do override não entra na biblioteca de imagens (decisão: a
  biblioteca é acervo do PRODUTO; o override é pontual da célula e viaja
  congelado com o projeto).
- Arrastar item→célula continua fora (nota antiga da F6.4 — candidata
  natural para quando o modal já existe).

**PARADO no ponto de reauditoria.** Etapa C (F7.1 — vários sabores num
slot) só começa com o selo do arquiteto.

## SELO do arquiteto — Etapa B (2026-07-09): APROVADA

`aplicar_override` é ponto único com a precedência exata da visão (vazio
herda com placeholder; foto do override vira foto única sem misturar com as
múltiplas do item; arranjo inválido de projeto velho degrada cosmeticamente
com o porquê em comentário — conteúdo nunca some). O adversarial B3 cobre o
que a lupa mirava: vazamento por pixel sob shuffle da estante e reordenação
do mapa, undo restaurando o override ANTERIOR estado a estado, foto congelada
byte-idêntica sobrevivendo a apagar a original, e `overrides_json` sem
caminho de máquina. O achado de bancada (órfãos do pré-voo só na página 1)
era real e a cura vale para o frente+verso inteiro. **263 verdes, zero skips
aceitos. Etapa C (F7.1 multi-sabores) AUTORIZADA** — a trava anti-alucinação
(IA sugere TERMOS, humano escolhe FOTOS) é inegociável; o arranjo do override
ganhando efeito visível fecha a ponta anotada no "ficou de fora".

## Resposta do builder — Etapa C executada (2026-07-10)

Linha de base: **263 verdes, zero skips**. Ao fechar: **270 verdes, zero
skips**, suíte rodada **duas vezes com exit 0** (o porquê está no achado de
bancada abaixo). 6 testes novos (`test_multi_imagem.py`) + 1 adversarial.

- **C1 ✓** — `ItemMesa.imagens` (a lista COMPLETA e ordenada que o slot
  desenha — a ordem da lista É a ordem do arranjo; vazia = foto única de
  sempre, zero migração) + botão direito na estante → **"Fotos deste item
  (sabores)…"**: lista ordenada com mover/remover, "Buscar e escolher…"
  reusa a MESMA curadoria de sempre (termo editável, arquivo, colar, URL) e
  a foto extra passa pelo MESMO pipeline (rembg), guardada em
  `biblioteca/<id>/extras/`. **A trava anti-alucinação na letra**:
  `sugerir_variantes` (enriquecimento.py) devolve SÓ TERMOS (máx. 6, dedup,
  degrada para lista vazia sem IA — a busca manual continua); na UI os
  termos viram **chips que preenchem o campo de busca** — teste explícito
  confere que clicar no chip NÃO adiciona foto nenhuma. **Congelamento
  preserva as N fotos NA ORDEM** (`imagens/{item}_{k}.png`, relativos — I3;
  foto sumida no salvar já foi acusada no pré-voo) e a miniatura do
  Dashboard compõe o multi.
- **C2 ✓** — Arranjo (leque/lado a lado/grade) selecionável **por item** no
  diálogo de fotos e **por override de slot** (a B1 já o tinha — agora com
  efeito visível); valor estranho em projeto velho degrada para leque.
- **Adversarial (I5) ✓** — `test_adversarial_multi_imagem_por_conteudo`,
  a mira anunciada da lupa: LADO_A_LADO amostrado TERÇO A TERÇO confere a
  cor de CADA posição na ordem da lista; **inverter a lista inverte os
  pixels** (a ordem é conteúdo); LEQUE mostra as três cores (sobreposição
  não engole ninguém); salvar→reabrir: **cada foto congelada byte-idêntica
  NA POSIÇÃO** (apagar as originais do disco não afeta), arranjo persistido,
  composição do congelado com os pixels na ordem; duplicado com cópias
  próprias; pré-voo acusa "(imagem 2/3)" sumida.

**Achado de bancada (o mais sério da etapa, documentado): a primeira
rodada completa da suíte terminou com TODOS os 270 pontos verdes e exit
-1073740791 (0xC0000409 — crash nativo no encerramento).** Verde com crash
no exit NÃO é verde. Causa: o diálogo novo dispara um worker (QThread) no
CONSTRUTOR; quando o dono morre com a thread viva, o Qt derruba o processo
— e nos testes a thread ainda podia estar consultando a IA/banco REAIS
depois do teardown. Cura em PRODUÇÃO (não no teste):
`GerenciadorTrabalhos.encerrar()` (espera com teto) + `done()` do diálogo
junta as pontas antes de morrer — o mesmo crash aconteceria no app real ao
fechar o pop-up com a sugestão em voo. A costura `sugestor` injetável
mantém os testes fora da IA/banco reais. Suíte re-rodada 2×: **exit 0 nas
duas**.

**O que ficou de fora (Etapa C):**

- Sugestões de variantes não são cacheadas (cada abertura do diálogo
  consulta de novo — barato e sempre fresco).
- A Fábrica (cartaz) segue foto única — multi-imagem é do tabloide; a
  Etapa D (item composto) decidirá o que o cartaz herda.
- Os `extras/` da biblioteca não têm poda automática (ficam até o humano
  limpar; o acervo oficial continua sendo `atual.png` + `versoes/`).
- Fechar o app com um worker LONGO em voo (ex.: export) ainda é a classe
  de risco geral pré-existente — o `encerrar()` cura os diálogos; um
  gancho global de `aboutToQuit` fica no radar.

**PARADO no ponto de reauditoria.** Etapa D (F7.2 — Camil e Rei, item
composto com uid único) só começa com o selo do arquiteto.

## SELO do arquiteto — Etapa C (2026-07-09): APROVADA

A trava anti-alucinação está na letra (chip só preenche o campo de busca —
com teste provando que clicar não adiciona foto; sem IA, chips somem e o
manual segue). O adversarial da ordem é prova real: terço a terço NA ordem da
lista, lista invertida inverte os pixels, leque exibe todas as cores,
congelado compõe idêntico com as originais apagadas. E o achado da etapa é
de moldura: **"verde com crash no exit não é verde"** — a causa (QThread viva
com o dono morto) era de produção e a cura foi em produção
(`GerenciadorTrabalhos.encerrar()` + `done()`), não no teste; o critério de
fechamento ganha um adendo permanente: **a suíte fecha com exit 0 limpo, sem
crash nativo no encerramento**. O radar do gancho global de shutdown (worker
longo em voo ao fechar o APP) fica anotado para a varredura final. **270
verdes ×2, zero skips aceitos. Etapa D (F7.2 — item composto) AUTORIZADA** —
é a mais sensível do bloco: 1 slot → 1 uid é inviolável, compor/separar sem
duplicar uid nem órfão no mapa, e o adversarial é o juiz.

## Resposta do builder — Etapa D executada (2026-07-10)

Linha de base: **270 verdes, zero skips, exit 0**. Ao fechar: **276 verdes,
zero skips, exit 0 em DUAS rodadas** (5 em `test_item_composto.py` + 1
adversarial novo).

- **A decisão de identidade, na letra** — o mapa é e continua **1 slot →
  1 uid**. `compor_itens(a, b)` cria UM `ItemMesa` com **uid próprio**;
  os dois originais viajam **INTEIROS** (to_dict, uid incluso) em
  `origem_composto` — `separar_item` devolve EXATAMENTE o que existia
  (teste compara os dicts completos). `produto_id` de origem rastreável
  dentro do composto. **Composto não compõe de novo** (profundidade 1 —
  erro nominal "separe primeiro"; sem bonecas russas de identidade).
- **Nome montado deterministicamente** — `nome_composto`: prefixo e
  sufixo comuns preservados, miolos distintos com "e" ("Arroz Camil 5kg"
  + "Arroz Rei 5kg" → "Arroz Camil e Rei 5kg"); sempre editável no
  diálogo. 2 imagens **LADO_A_LADO por padrão** (o F7.1 da etapa passada
  deu o motor de graça); **preço único** perguntado no compor; +18 por OR
  (bebida na dupla → selo na dupla).
- **Estante e mapa consistentes por construção** — a lógica mora em
  `_executar_composicao`/`_executar_separacao` (separada dos diálogos,
  testável): o composto **herda o slot do PRIMEIRO** item; a célula do
  segundo **esvazia à vista** (nunca dois uids); ao separar, o primeiro
  volta à célula dele e o segundo à estante. Badge "composto (2 em 1)"
  na estante; menu só oferece compor a itens simples e separar a
  compostos.
- **Congelamento com I3 completo** — as fotos dos itens de ORIGEM também
  congelam na pasta do projeto (`imagens/{i}_org{k}.png`, relativas):
  separar DEPOIS de reabrir devolve itens com foto viva, não caminho de
  outra máquina.
- **Adversarial (I5)** — `test_adversarial_item_composto`: **3 ciclos**
  compor/separar com invariantes conferidos a cada passo (nenhum uid
  duplicado no mapa, nenhum órfão, uids ORIGINAIS de volta); LADO_A_LADO
  **por pixel** (Camil à esquerda, Rei à direita) na Mesa E recomposto do
  congelado; originais apagadas do disco → o congelado nem percebe;
  separar o congelado devolve os dois com fotos **byte-idênticas** às de
  antes do salvar.

**O que ficou de fora (Etapa D):**

- Compor/separar não entra no undo do CANVAS (é gesto da ESTANTE, como o
  auto-preencher — o inverso explícito é o desfazer; mesma decisão
  registrada desde a F5.10: "produtos não são LayoutDef").
- A Fábrica desenha só a 1ª foto de um composto (cartaz é 1 produto por
  página por natureza; se um dia precisar, o motor já aceita).
- O diálogo do compor usa QInputDialog em 3 passos (par → nome → preço) —
  um diálogo único mais bonito é polimento.
- Compor exige os DOIS itens na estante (não há compor direto entre
  células do canvas — candidato natural junto do arrastar-item→célula).

**PARADO no ponto de reauditoria.** Etapa E (F7.5 — CMYK opcional, a
última do bloco) só começa com o selo do arquiteto.

## SELO do arquiteto — Etapa D (2026-07-09): APROVADA

`compor_itens`/`separar_item` na letra da decisão de identidade: uid próprio,
originais INTEIROS em `origem_composto` (separar devolve por dict completo —
uids originais inclusos), profundidade 1 com erro nominal, `mais18` por OU
(bebida em qualquer metade marca o composto — domínio correto), unidade só
quando igual, LADO_A_LADO padrão. Mapa consistente por construção (célula do
2º esvazia à vista; nunca dois uids). Congelamento com as fotos de ORIGEM
também na pasta do projeto — separar pós-reabrir devolve foto viva, provado
byte a byte. O adversarial-juiz cumpre a ordem: 3 ciclos com invariantes por
passo, pixel esquerda/direita, originais apagadas sem efeito. As duas
exclusões declaradas (compor/separar fora do undo do canvas — decisão antiga
e coerente; Fábrica desenha 1ª foto) estão aceitas e registradas. **276
verdes ×2, exit 0, zero skips aceitos. Etapa E (F7.5 CMYK) AUTORIZADA** — a
última do bloco: RGB byte-idêntico é o teste-rei, Ghostscript ausente degrada
COM aviso, `/DeviceCMYK` e tamanho físico conferidos no PDF.

## Resposta do builder — Etapa E executada + GATE do bloco cumprido (2026-07-10)

Linha de base: **276 verdes, zero skips, exit 0**. Ao fechar: **281 verdes,
zero skips, exit 0 em DUAS rodadas** (5 testes em `test_cmyk.py`).

- **E1 ✓** — `app/rendering/cmyk.py`: a conversão é PÓS-PROCESSO do PDF já
  gravado (`pos_processar_export`, ligado nos exports da Mesa E da
  Fábrica); `exportar_pdf*` não mudou UMA linha. Liga/desliga por
  `export.cmyk_pdf` (padrão **desligado**) + `export.perfil_icc` opcional,
  os dois com campo na tela de Configurações (com o tooltip honesto: "para
  WhatsApp/Instagram não mexa aqui"). **O teste-rei**: com CMYK desligado,
  o export fica **byte-idêntico** — hash sha256 antes/depois do
  pós-processo, nenhum byte muda; PNG nunca é tocado, ligado ou não.
- **E2 ✓** — Ghostscript REAL do ambiente (10.06, `gswin64c` no PATH):
  o convertido contém `/DeviceCMYK` (o RGB de origem não continha —
  sanidade testada), MESMO número de páginas e tamanho físico intacto
  (pypdf, < 0,2 pt). **gs ausente degrada COM aviso** (arquivo intocado
  byte a byte + "o PDF ficou em RGB" no toast — I2), o export jamais
  trava; conversão que falha idem; perfil ICC inexistente converte com o
  padrão E avisa qual perfil faltou.

**O que ficou de fora (Etapa E):**

- CMYK só para PDF (PNG é o fluxo digital por definição).
- Sem preview CMYK na tela — o editor segue RGB; prova de cor é da
  gráfica.
- O perfil ICC é aplicado via `-sOutputICCProfile`; perfis exóticos ficam
  por conta do Ghostscript (não validamos o conteúdo do .icc).

### Gate de fechamento — evidências

- **Suíte inteira**: 281 verdes, zero skips, **exit 0 em duas rodadas**
  (o critério novo do selo da Etapa C, cumprido desde então).
- **Adversariais atualizados e verdes**: `test_adversarial_vinculo.py`
  ganhou no bloco os passos do override (B3), do multi-imagem (C) e do
  composto (D) — todos por conteúdo; `test_adversarial_portabilidade.py`
  re-rodado nas etapas que tocaram persistência.
- **Artefatos de demonstração por etapa**:
  `python -m app.scripts.selfcheck_bloco_e` (reproduzível) → em
  `saida_selfcheck_e/`: `etapaB_override.png` (override só na célula
  dele), `etapaC_lado_a_lado.png` + `etapaC_leque.png` (ordem por pixel),
  `etapaD_composto.png` ("Arroz Camil e Rei 5kg" montado, separar
  devolvendo os originais), `etapaE_rgb.pdf` (hash intocado
  `46286d32e783…`) + `etapaE_cmyk.pdf` (`/DeviceCMYK`, 99,99×150,03 mm).
- **PLANO atualizado** (F7.1/F7.2/F7.3/F7.5 ✓ + as dívidas da Etapa A) e
  **"o que ficou de fora" listado por etapa** nas cinco respostas acima.

**PARADO no ponto de reauditoria — aguardando o SELO de fechamento do
Bloco E.** A próxima ordem é o F8 (categorização + tabloide de ~40 itens,
o marco de aceitação), onde o Otaviano volta ao circuito.

## SELO do arquiteto — Etapa E e BLOCO E FECHADO (2026-07-10)

Verificação independente dos artefatos: medi os dois PDFs nos bytes —
`/DeviceCMYK` presente SÓ no convertido, ausente no RGB, ambos com 99,99 ×
150,03 mm exatos e hashes distintos; inspecionei visualmente o
`etapaD_composto.png` ("Arroz Camil e Rei 5kg" com as duas fotos lado a lado
e preço único — correto). A conversão como pós-processo do PDF já gravado é
o desenho certo: o RGB fica byte-idêntico por CONSTRUÇÃO, não só por teste.
**281 verdes ×2, exit 0, zero skips. BLOCO E: FECHADO** (F7.1 ✓ F7.2 ✓
F7.3 ✓ F7.5 ✓ + radar zerado na Etapa A). Ordem seguinte: `docs/ORDEM_F8.md`
— o marco de aceitação.

## Gate de fechamento do Bloco E (texto original)

Suíte inteira + adversariais atualizados (B3 e D são os críticos — tocam
slot/item/mapa) verdes na máquina real; artefatos de demonstração por etapa
(script reproduzível + export) para o arquiteto verificar por conta própria;
PLANO atualizado; "o que ficou de fora" por etapa. Depois do Bloco E, a
próxima ordem é o **F8 — categorização e o tabloide de ~40 itens**, o marco
de aceitação onde o Otaviano volta ao circuito para a revisão geral.
