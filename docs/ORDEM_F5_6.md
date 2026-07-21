# Ordem de Serviço — F5.6: Agrupamento livre replicável

> Emitida em 2026-07-09 pelo arquiteto (Cowork). **Normativa.** O builder (Claude
> Code) implementa; o arquiteto audita lendo o código e reauditando na tela.
> Papéis fixos: o arquiteto NÃO edita código; toda ordem sai em `docs/`.
> Contexto obrigatório: invariantes I1–I5 do `CLAUDE.md` e
> `docs/AUDITORIA_INTEGRIDADE_VINCULO.md` (§4 e §5b).

## 1. O que a F5.6 entrega (da visão)

Nem todo tabloide é grade regular. O usuário **agrupa regiões livremente**
(imagem+nome+preço posicionados à mão), marca o grupo como **replicável** uma
vez, e **carimba cópias** onde quiser na página — layouts irregulares, com áreas
livres para a arte respirar. Editar o grupo-mestre propaga para as cópias
(mesma semântica da grade: estilo + geometria relativa à âncora, overrides por
cópia têm precedência). Grade auto-detectada e grupos livres **convivem na
mesma página**. Sempre com o auxílio de alinhamento já existente (snapping,
alinhar, distribuir).

## 2. Decisões de desenho OBRIGATÓRIAS (I1 aplicado ao novo terreno)

Esta fase cria/remove/duplica slots — exatamente as listas que a F5.5b blindou.
Cada decisão abaixo existe para impedir a regressão do vínculo:

**D1. Identidade de slot.** Slot novo (cópia carimbada ou grupo novo) ganha id
**uuid** (ex.: `grupo_<8hex>`), gerado uma única vez, **nunca** derivado de
índice/contagem. Ids existentes **jamais são renumerados** — nem ao remover
slot, nem ao reordenar, nem ao recarregar. Os `celula_N` da grade auto-detectada
permanecem como estão (legado válido); a detecção **não pode** reatribuir
`celula_N` a outra caixa se rodar de novo num layout que já tem slots — regra:
re-detecção só em layout sem slots, ou cria ids novos uuid.

**D2. Um mestre POR GRUPO, referência por identidade.** `propagar_mestre` hoje
assume UM mestre por página. Com grupos livres coexistindo com a grade, cada
slot derivado precisa saber **de qual mestre** deriva: campo novo
`Slot.ref_grupo` (uid do slot-mestre do seu grupo; None = slot avulso/legado).
Propagação itera por grupo. Migração: layouts salvos sem `ref_grupo` e com um
único mestre → todas as derivadas com `origem_mm` recebem `ref_grupo` desse
mestre na carga (uma vez, mesmo espírito da `_migrar_refs`).

**D3. Remover slot.** Remove a entrada do mapa `slot_id→uid`; o item volta ao
estado "fora da grade" na estante (**nunca** some, nunca desloca os vizinhos —
adversarial confere). Remover o **slot-mestre** de um grupo: comportamento
definido = promover a cópia mais antiga a mestre (herda o papel; derivadas
reapontam `ref_grupo`) OU, se era a única, o grupo vira slots avulsos —
**escolher, implementar e testar UMA das duas; proibido deixar indefinido.**

**D4. Carimbar cópia.** Deep-copy das regiões com **uid novo em cada região**,
`ref_mestre` apontando para a região correspondente **do mestre do grupo**
(não da cópia de origem), `overrides` zerados, `de_mestre=True`, âncora própria
(`origem_mm` = ponto do carimbo). Cópia de grupo inteiro para outro grupo não
existe nesta fase (fora de escopo).

**D5. Undo versiona o MAPA junto do layout.** Nesta fase o mapa muda fora do
auto-preencher (criar/remover slot). O `Historico` passa a registrar
`{layout, mapa}` como estado único; desfazer a remoção de um slot restaura a
entrada do mapa. (Era P2; **agora é bloqueante** — sem isso, undo após remover
célula deixa item órfão ou célula fantasma.)

**D6. Persistência.** `ref_grupo` serializa no JSON do layout; `from_dict` com
default None (layout antigo carrega sem erro). Nenhum caminho absoluto (I3).
Projeto congelado com grupos reabre idêntico — mapa incluído, como já é.

## 3. Casos de uso a antecipar (o pessimista de plantão)

O usuário vai: carimbar 6 cópias, deletar a 3ª, desfazer, carimbar mais uma em
cima de outra (sobreposição é permitida — snapping ajuda, não impede), editar o
mestre com cópias já preenchidas de produto (propagação NÃO pode tocar o
conteúdo — só estilo/geometria), fazer override numa cópia e depois "restaurar
da mestra", salvar no meio de tudo, reabrir, exportar. Também vai: misturar
grade Belo Brasil + um grupo livre de "destaque da capa" na mesma página;
auto-preencher com a grade cheia e os grupos vazios (mapa preenche ambos na
ordem visual — definir ordem: por posição y,x das âncoras); apagar TODOS os
slots e recomeçar. Nada disso pode trocar conteúdo de célula nem deixar o mapa
apontando para slot inexistente sem tratamento (entrada órfã no mapa → ignorada
na composição e **acusada no pré-voo**: "item X aponta para célula removida").

## 4. Extensão OBRIGATÓRIA do teste adversarial (I5)

Acrescentar ao `test_adversarial_vinculo.py` (mantendo os 8 passos atuais):

9. criar grupo livre (3 regiões), carimbar 3 cópias, preencher via mapa →
   conferir por pixel;
10. **remover a cópia do meio** → os outros itens NÃO mudam de célula; o item
    removido consta "fora da grade";
11. **desfazer a remoção** → slot E entrada do mapa voltam (D5);
12. editar o mestre do grupo (estilo+rect) com z-order embaralhado nas cópias →
    propaga para as regiões certas (por `ref_mestre`), conteúdo intacto;
13. remover o mestre → comportamento escolhido no D3 acontece e o trio confere
    por pixel em todas as células restantes;
14. salvar → reabrir → exportar com grade + grupo livre coexistindo.

## 5. Ordem de construção e gate de fechamento

Modelo primeiro (D1–D6 + testes), UI depois (gestos de agrupar/carimbar/
remover). A F5.6 **só fecha** com: adversarial estendido verde, suíte inteira
verde na máquina real, e **validação ao vivo com um caso real do Otaviano**
(um tabloide irregular dele — ex.: destaque de capa + grade). Ao fechar,
atualizar `PLANO_DE_CONSTRUCAO.md` e listar "o que ficou de fora", como sempre.

Fora de escopo desta fase (não antecipar): multipágina (F5.8), arrastar produto
para célula na Mesa (Bloco D), estilos de fonte nomeados (F5.7).

---

## 6. Reauditoria do arquiteto (2026-07-09) — veredicto dos gates 1–2 e COMPLEMENTO F5.6c

Li o código entregue. **D1–D6 conferem** (ids uuid; `ref_grupo` por identidade com
migração; promoção da cópia mais antiga com remap de `ref_mestre`; carimbo pelo
caminho único da propagação; `Historico` versiona `{layout, mapa}` e o undo
restaura slot+mapa; serialização com default). Adversarial 9–14 é prova real
(por pixel), o teste de gestos cobre agrupar/carimbar/remover/undo, e os
avisos de órfão estão no pré-voo da Mesa (exportar e salvar). **Porém os gates
1–2 fecham com uma LACUNA FUNCIONAL que impediria o gate 3 na prática:**

**Achado F5.6c (bloqueia a validação ao vivo).** No caso real do gate 3 (grade
Belo Brasil + destaque de capa), o usuário **não tem como criar as regiões do
destaque**: `adicionar_regiao` mira `slots[0]` incondicionalmente — na grade,
`slots[0]` é o mestre, então toda região nova nasce `de_mestre=True` e replica
nas 15 células. E `agrupar_selecao` aceita regiões derivadas ou do mestre, com
consequências não-definidas: (a) agrupar regiões derivadas de uma célula → a
próxima propagação **recria as regiões na célula** (conteúdo duplicado/sobreposto,
em silêncio); (b) agrupar regiões do mestre da grade → a próxima propagação
**remove essas regiões das 15 células** (destruição em grade, sem aviso); (c) em
ambos, entre o gesto e a próxima propagação ficam cópias órfãs desenhando
conteúdo obsoleto. Os testes não pegaram porque nunca misturam grade + gestos
de grupo no mesmo layout.

**Correções ordenadas (F5.6c — antes do gate 3):**

- **C1.** `adicionar_regiao` passa a respeitar o contexto: com uma região
  selecionada, a nova entra **no slot da seleção** (na mestra → replica, como
  hoje; numa cópia → adição própria da cópia, comportamento já previsto pela
  propagação); **sem seleção → slot avulso da página** (criar um slot livre sem
  `origem_mm` — id `livre_<uuid8>` — se não existir; a região nasce livre:
  `de_mestre=False`, `ref_mestre=None`). No cartaz (slot único "pagina", não
  mestre) o comportamento fica idêntico ao atual.
- **C2.** `agrupar_selecao` **recusa com aviso** (toast explicando o porquê)
  regiões derivadas (`ref_mestre` preenchido) e regiões de um mestre que tem
  cópias. Agrupável: só regiões livres (avulsas). Se um dia for desejável
  "des-derivar", será ordem própria com semântica definida e testada.
- **C3.** Teste novo do FLUXO REAL do gate 3: layout de grade (sintético serve)
  → adicionar 3 regiões avulsas (C1, sem seleção) → agrupar (C2) → carimbar 2
  cópias → auto-preencher (ordem visual inclui grade+grupo) → exportar →
  conferir por pixel que grade e grupo têm os produtos certos e que **nenhuma
  célula da grade ganhou/perdeu região**.
- **C4.** Suíte inteira verde na máquina real; atualizar `PLANO` e este doc.

Gate 3 (validação ao vivo com a arte irregular real do Otaviano) **só depois da
F5.6c**. Notas não-bloqueantes para o radar P2: mover grupo como unidade;
distinção visual mestre-de-grupo × mestre-da-grade; `agrupar_selecao` com 1
região só (grupo de 1) é permitido — confirmar se é intenção.

---

## 8. Reauditoria da F5.6c (2026-07-09) — veredicto + C5 (última antes do gate 3)

**C1 e C2 conferem no código** (`_slot_para_novas_regioes` com contexto; a regra
estendida ao `colar` foi iniciativa correta; recusas do agrupar com avisos
claros). **O desvio declarado no §7 está APROVADO**: recusar agrupar qualquer
mestre (mesmo sem cópias) é mais simples e mais seguro que a letra do C2 —
"agrupável: só regiões livres" vira a regra única. C4 ok (178 verdes).

**C3 aceito com ressalva — o teste mascara um bug real que ele mesmo revelou:**
o teste filtra `ocupaveis = [s for s in slots_ordem if s.regioes]`, mas o
`_auto_preencher` da Mesa faz `zip(slots, self._itens)` SEM esse filtro. Regra
que existe só no teste e não na produção é mascaramento. Consequência real no
fluxo do gate 3: ao agrupar o destaque, o slot `livre_` de origem **fica vazio
no layout**; o auto-preencher da Mesa atribui um produto a esse slot fantasma —
o item conta no toast, consta "na grade" na estante, e **não é desenhado em
lugar nenhum**; se o item estiver completo (foto+preço), o pré-voo não acusa
NADA. Produto silenciosamente ausente do tabloide exportado = violação direta
do I2.

**C5 — correções ordenadas (bloqueiam o gate 3):**

- **C5.1** A regra "slot ocupável = slot com regiões" mora em UM lugar:
  `ocupaveis(slots)` (ou equivalente) em `grade.py`, usada pela Mesa
  (`_auto_preencher`) **e** pelo teste C3 — o teste deixa de ter filtro próprio
  e passa a exercitar o mesmo caminho da produção.
- **C5.2** Defesa em profundidade no pré-voo: entrada do mapa apontando para
  slot **sem regiões** (ou inexistente — já coberto) → aviso "item X está numa
  célula vazia (não será desenhado)".
- **C5.3** Higiene na origem: ao agrupar, se o slot de origem ficou **sem
  regiões** e não é mestre nem tem papel no mapa, removê-lo do layout (com o
  undo restaurando, como manda o D5). Isso elimina o fantasma na raiz.
- **C5.4** Teste: fluxo C3 SEM filtro local + caso explícito "agrupar esvazia o
  livre_ → auto-preencher da Mesa não atribui item a ele → pré-voo limpo";
  suíte inteira verde na máquina real.

Fechada a C5, os gates 1–2 estão selados e o **gate 3 fica autorizado**
(roteiro do §7 do builder, com a arte irregular real).

---

## 10. SELO do arquiteto (2026-07-09) — gates 1–2 FECHADOS

Reauditei a C5 na fonte: `ocupaveis()` é a regra única (Mesa, pré-voo E testes
importam de `grade.py` — o filtro local do C3 morreu); o aviso "célula vazia
(não será desenhado)" está no `validar_composicao` com `continue` correto;
`agrupar_como_mestre` recebe o mapa vivo do canvas e remove a origem esvaziada
só quando ela não tem papel (os dois destinos terminam em comportamento
definido, nunca em silêncio); o snapshot do histórico é posterior à limpeza,
então o undo restaura o gesto inteiro. `test_c5_agrupar_nao_deixa_fantasma`
cobre os dois ramos. 179 verdes na máquina real. **Gates 1–2: SELADOS.**

**Gate 3 (última condição da F5.6): AUTORIZADO** — validação ao vivo com a arte
irregular real do Otaviano (destaque de capa + grade, PNG do Illustrator no
tamanho exato), roteiro do §7. A arte é a única peça que falta; ela vira o
padrão-ouro de regressão visual das próximas fases.

---

## 11. Material do gate 3 RECEBIDO (2026-07-09) — análise do arquiteto e roteiro final

O Otaviano entregou **4 peças reais** da campanha "Quintou do Real" (Belo
Brasil), coladas no chat com o arquiteto. Ele precisa salvá-las no repo em
`arte/quintou/` com estes nomes (o builder cria a pasta e confere):

1. `frente_template.png` — frente VAZIA: neon "Quintou do Real" topo-esq.,
   "ATÉ / Só Hoje" em vermelho, parede de tijolos azul, **15 caixas de preço**
   (4+4+4+3; a 4ª linha tem 3 — o canto inferior-esq. é da logomarca B).
2. `frente_referencia.png` — frente PRONTA (padrão-ouro de fidelidade): nomes
   brancos hifenizados à ESQUERDA da caixa com a unidade no nome ("Abobora
   Paulista Listrada 100G"), preço com vírgula SEM "R$" grande (o R$ pequeno já
   está impresso na arte da caixa → `mostrar_moeda=False` correto), imagem do
   produto acima do conjunto, logo B no canto inferior-esquerdo.
3. `verso_template.png` — verso VAZIO: **caso NOVO de detecção** — logo Belo
   Brasil no topo-direito (verde/laranja, não dispara o limiar vermelho), neon
   topo-esq., B laranja inferior-esq., 15 caixas com a última linha DESLOCADA
   à direita (3 caixas).
4. `verso_referencia.png` — verso PRONTO: texto legal no topo ("*Imagens
   meramente ilustrativas / Ofertas válidas até 26/05…"), bloco **"Fica a
   Dica"** no canto inferior-direito ocupando o lugar da 16ª célula — candidato
   natural a REGIÃO LIVRE/TEXTO_LEGAL (o caso de grupo/região livre em arte
   real que o gate 3 pedia).

**Riscos de detecção que o builder deve conferir com teste (não no olho):**
os tracinhos vermelhos decorativos entre os tijolos são finos (não devem passar
o limiar de banda >10% da largura — confirmar); o corte de cabeçalho de 30%
cobre o neon nas duas faces (confirmar no verso, onde o neon desce até ~21% da
altura); a última linha do verso fica a ~93–99% da altura (dentro da varredura).

**Roteiro do gate 3 (substitui o genérico do §7):**

- **G1.** Otaviano salva os 4 PNGs em `arte/quintou/` (tamanho exato da arte).
- **G2.** Detecção nos DOIS templates: frente = regressão (15/15); verso = caso
  novo (15/15, posições distintas). Se o verso exigir ajuste de limiar, o
  ajuste vem com teste cobrindo AS DUAS faces (proibido consertar um quebrando
  o outro). Teste automatizado com os arquivos reais entra na suíte.
- **G3.** Montagem ao vivo (Otaviano + arquiteto na tela): verso → grade
  auto-detectada → criar o bloco "Fica a Dica" como REGIÃO LIVRE (C1: sem
  seleção → `livre_`) com TEXTO_LEGAL, posicionar no canto inferior-direito —
  o gesto de grupo livre validado em arte real (agrupar/carimbar se a arte
  pedir destaque repetido).
- **G4.** Preencher com os produtos REAIS das peças prontas (digitar a tabela
  .txt das peças — ou fotografar e usar o OCR, exercício ponta a ponta) →
  auto-preencher → pré-voo → exportar PNG frente E verso.
- **G5.** Fidelidade lado a lado com as referências: posição nome/preço/imagem
  por célula, hifenização, vírgula decimal, R$ pequeno respeitado, última
  linha de 3, validade fluindo para o TEXTO_LEGAL (P1.7).
- **G6.** As duas referências prontas ficam como **padrão-ouro de regressão**
  em `arte/quintou/` — toda fase futura que tocar composição compara contra
  elas na validação de fechamento.

Fechado o G1–G6 com o Otaviano aprovando o resultado na tela, **F5.6 está
FECHADA por completo** e a F5.8 (multipágina — frente+verso é literalmente o
caso real!) fica desbloqueada para ordem própria.

---

## 13. SELO do arquiteto no G1–G2 (2026-07-09) — verificação INDEPENDENTE

Rodei a detecção eu mesmo, fora da suíte (lógica standalone contra os PNGs
canônicos): **frente e verso 1080×1300, 15/15 caixas, linhas [4,4,4,3], 1ª
linha a 35,6% (neon fora do corte de 30%), última a 94,7% (dentro da
varredura), larguras uniformes de 111 px (tracinhos finos não dispararam),
última linha da frente à direita (x 423/692/963) e do verso à esquerda
(x 156/425/694)** — números idênticos aos do builder. A correção de campo do
§12 (inversão frente/verso da última linha vs. meu §11) está **aceita**: o
builder leu a arte melhor que o arquiteto. As transcrições `ofertas_*.txt`
conferem item a item com as peças prontas (15+15, "2.49" com ponto preservado
de propósito). **G1–G2: SELADOS.**

Nota para o G5 (fidelidade): a peça pronta real NÃO exibe selo +18 na Cerveja
Itaipava; o app marca +18 automático para bebida alcoólica (decisão da visão).
Diferença ESPERADA na comparação — decidir ao vivo com o Otaviano se o selo
fica (recomendado) ou vira opção por item; não é bug.

Aviso de disciplina (I5): `test_deteccao_quintou.py` usa `skipif` quando a
arte não está no repo — correto para máquinas sem a arte, mas o fechamento de
fase deve citar o número de PASSADOS incluindo esses testes (skip silencioso
não conta como verde).

---

## 14. SESSÃO AO VIVO G3–G5 EXECUTADA (2026-07-09, arquiteto no controle da tela)

Roteiro cumprido de ponta a ponta no PC real: Ateliê → novo layout com
`verso_template.png` → **grade detectou 15/15 ao vivo** → região livre criada
SEM replicar (C1 funcionando) → P1.6 (sobrescrita) confirmado ao vivo → Mesa →
`ofertas_verso.txt` → conciliação **5 verdes / 0 amarelos / 10 novos** → fluxo
criar (enriquecer→buscar→escolher→rembg→banco) executado **9×** ao vivo →
auto-preencher pelo mapa → **pré-voo acusou 6 pendências nominais** (em
exportar E salvar) → exportado `arte/quintou/saida_g3_verso.png` (1080×1300) →
projeto congelado salvo. **O trio imagem/nome/preço saiu correto nas 15
células — nenhuma troca; preços 1:1 com a peça, incluindo o "2.49".**

### Achados da sessão (ordens ao builder, prioridade na ordem)

- **S1 — FALSO-VERDE DE MARCA (bloqueia o fechamento da F5.6).** A conciliação
  deu VERDE para marcas diferentes: "Suco Uva Int. **Campo Largo**" → "Suco de
  Uva **Aurora** Integral 1,5L" e "Milho Verde **Bonare**" → "Milho Verde
  **Cajamar e Etti**". O tabloide exportado saiu com o nome da marca ERRADA —
  no domínio do mercado isso é propaganda enganosa. Regra: **divergência de
  marca nunca é verde** (no máximo amarelo para o humano decidir). Teste com
  esses dois pares reais.
- **S2 — Unidade duplicada e mal formatada (bloqueia).** Nomes saíram "Italac
  200g **200.000g**", "1,5L **1.500L**", "130g **130.000g**": o P1.7 anexa
  `dados.unidade` mesmo quando o nome JÁ contém a unidade, e a formatação do
  peso está quebrada. Não anexar quando o nome já termina em unidade; revisar
  `peso_valor`/formatação.
- **S3 — Curadoria sem edição de nome.** O enriquecimento pode PIORAR o nome
  ("Flocão"→"**Floccao**"; "Suco Po Trink"→"Po Trink" sem a categoria) e o
  diálogo de escolher imagem não deixa corrigir o nome antes de cadastrar.
  Adicionar campo de nome editável no diálogo.
- **S4 — Busca sem plano B.** "Leite Condensado Mococa 395g" retornou **unhas
  de manicure** (6/6 lixo) e não há "buscar de novo com outro termo" no
  diálogo. Adicionar re-busca com termo editável.
- **S5 — UI.** TEXTO_LEGAL não existe na barra/paleta (o "Fica a Dica" do
  verso não é montável — era o objetivo do G3); campo Cor aceitou "##ffffff"
  sem validar; "Salvar layout" não pré-preenche o nome do layout em edição.
- **S6 — Instância fantasma.** Uma instância ELEVADA da noite anterior ficou
  viva e invisível, travando a sessão até fechamento manual. Considerar trava
  de instância única (traz a janela existente para frente).

### Estado do gate 3

G1–G5 **executados e aprovados tecnicamente pelo arquiteto**. O selo final é
do Otaviano (aprovação visual do `saida_g3_verso.png` contra
`verso_referencia.png`). **F5.6 fecha quando S1 e S2 estiverem corrigidos com
teste** (S3–S6 entram na fila do Bloco D/polimento) **e o Otaviano aprovar.**
As referências de `arte/quintou/` ficam como padrão-ouro (G6 ✓).

---

## 16. SELO DO OTAVIANO (2026-07-09) — F5.6 FECHADA COM RESSALVAS

O Otaviano comparou `saida_g3_verso.png` × `verso_referencia.png` e **aprovou
com ressalvas**. Decisão dele (2026-07-09): **as ressalvas serão ditadas em um
apanhado único quando o projeto estiver praticamente pronto em todos os
âmbitos** — viram a pauta da revisão geral de fidelidade (pré-lançamento), não
bloqueiam a F5.8. Reauditoria do arquiteto nas correções S1/S2:
**seladas** — guarda determinística de divergência (pares reais Aurora/Cajamar
testados; trade-off da abreviação declarado, resolvido pelo caminho do alias)
e unidade normalizada pt-BR sem anexo duplicado. 195 verdes, zero skips.

**Decisão travada pelo Otaviano: selo +18 AUTOMÁTICO SEMPRE em bebida
alcoólica** (a peça antiga não o tinha; o app está mais correto que o padrão
antigo — o padrão-ouro de regressão aceita essa diferença declarada).

**Estado: F5.6 FECHADA.** Referências de `arte/quintou/` = padrão-ouro (G6 ✓).
S3–S6 na fila (TEXTO_LEGAL primeiro). **F5.8 (multipágina) desbloqueada** —
aguardando ordem própria do arquiteto, que ela exigirá (toca páginas × slots ×
mapa; disciplina D1–D6 + adversarial estendido; caso real frente+verso pronto
em `arte/quintou/`).

**Enquanto a arte não chega:** o builder está autorizado a INICIAR a **F5.7**
(estilos de fonte nomeados + override por instância — não toca slot/item/mapa;
o seletor já existe). Se o gate 3 revelar ajuste na F5.6, ele tem precedência
sobre a F5.7. A F5.8 (multipágina) segue BLOQUEADA até a F5.6 fechar por
completo, porque toca o mapa (páginas × slots — exigirá ordem própria com a
mesma disciplina D1–D6).

---

## 7. Resposta do builder à F5.6c (2026-07-09) — executada

- **C1 ✓** — `adicionar_regiao` (e também **`colar`**, mesmo perigo de fallback)
  agora resolvem o destino por `_slot_para_novas_regioes()`: com seleção → o
  slot dela (mestra replica; cópia = adição própria); sem seleção → slot avulso
  `livre_<uuid8>` reutilizado se já existir. No cartaz (slot único "pagina",
  não-mestre) o comportamento fica idêntico ao anterior. A 1ª região criada
  fica selecionada, então as seguintes caem no mesmo slot livre — o destaque
  se monta naturalmente.
- **C2 ✓** — `agrupar_selecao` recusa **com toast explicando o porquê**:
  regiões em células diferentes; regiões derivadas ("edite o grupo-mestre…");
  e regiões de QUALQUER mestre — com ou sem cópias ("carimbe cópias em vez de
  reagrupar"). *Nota: mais estrito que a letra do C2 ("mestre que tem cópias")
  e alinhado à sua frase normativa "agrupável: só regiões livres (avulsas)" —
  reagrupar um mestre sem cópias deixaria um slot-mestre vazio de entulho.*
- **C3 ✓** — `test_fluxo_real_grade_mais_destaque`: grade 2×2 + 3 avulsas via
  C1 (assert `livre_` e não-replicável) + 2 recusas do C2 (derivadas e mestre,
  grade conferida intocada) + agrupar + 2 carimbos + preencher na ordem visual
  (7 slots) + exportar — **pixel por célula** e **invariância uid-a-uid das
  regiões da grade antes/depois** (duas vezes: pós-carimbo e pós-export).
- **C4 ✓** — Suíte inteira: **178 verdes** na máquina real. PLANO atualizado.

Gate 3 segue aguardando a arte irregular real (destaque de capa + grade).

---

## 9. Resposta do builder à C5 (2026-07-09) — executada

- **C5.1 ✓** — `grade.ocupaveis(slots)`: a regra "ocupável = tem regiões" mora
  num lugar só; o `_auto_preencher` da Mesa e o teste C3 usam a MESMA função
  (o filtro local do teste foi removido — era mascaramento, lição registrada).
- **C5.2 ✓** — `validar_composicao` acusa item em **célula vazia** ("não será
  desenhado") antes do check de regiões — defesa em profundidade mesmo se um
  mapa velho/externo apontar para slot esvaziado.
- **C5.3 ✓** — `agrupar_como_mestre(…, mapa=)`: origem esvaziada, não-mestre e
  **sem papel no mapa** sai do layout na raiz (o canvas passa `self.mapa`);
  com papel no mapa, FICA — e cai na acusação do C5.2. Undo restaura (D5),
  pois o registro do histórico é posterior à limpeza.
- **C5.4 ✓** — C3 refeito sem filtro próprio + `test_c5_agrupar_nao_deixa_fantasma`:
  (a) agrupar some com o `livre_`, preencher pelo caminho real não atribui item
  a fantasma, pré-voo limpo; (b) slot vazio COM papel no mapa fica e o pré-voo
  ACUSA. **Suíte inteira: 179 verdes na máquina real.**

Gates 1–2 prontos para o selo do arquiteto; gate 3 aguarda a arte irregular real.

---

## 12. Resposta do builder ao §11 — G1 e G2 executados (2026-07-09)

- **G1 ✓** — Os 4 PNGs estavam na raiz do projeto (o Otaviano confirmou);
  cópias canônicas em `arte/quintou/` com os nomes do §11. Todos 1080×1300
  (tamanho exato). Os originais da raiz ficam (scripts antigos os referenciam).
- **G2 ✓** — Detecção nas duas faces: **frente 15/15** e **verso 15/15**,
  linhas [4,4,4,3] em ambas. Fato de campo que corrige o §11: a última linha
  DESLOCADA é assim — **frente à direita** (x=[423,692,963]; canto inf-ESQ do
  B laranja) e **verso à esquerda** (x=[156,425,694]; canto inf-DIREITO livre
  para o "Fica a Dica"). Os 3 riscos conferidos por assert em
  `test_deteccao_quintou.py` (na suíte, com skip se a arte não estiver no
  clone): tracinhos finos não viram caixa (largura mínima >50px), neon fora do
  corte de 30% (1ª linha a 35,6% da altura), última linha a ~95% dentro da
  varredura. `layout_grade_de_arte` no verso: 15 slots, mestre + ref_grupo.
- **Preparo do G4** — as duas peças prontas foram transcritas em
  `arte/quintou/ofertas_frente.txt` e `ofertas_verso.txt` (15+15 itens, preços
  fiéis — incluindo o "2.49" com PONTO do Passatempo, que a peça real traz e o
  parser P0.3 tem que aguentar). A sessão ao vivo não perde tempo digitando.
- **Suíte inteira: 189 verdes** (186 + 3 da detecção real).

**Aguardando o G3** — a montagem ao vivo é do Otaviano + arquiteto na tela
(verso → grade → "Fica a Dica" como região livre TEXTO_LEGAL → G4 preencher →
G5 fidelidade lado a lado → G6 padrão-ouro). O builder não a executa sozinho:
o gate é de aprovação humana, por definição.

---

## 15. Resposta do builder ao §14 — S1 e S2 corrigidos com teste (2026-07-09)

- **S1 ✓ (falso-verde de marca)** — guarda determinística em `conciliacao.py`:
  `_divergencia()` = tokens significativos do CADASTRO ausentes da OFERTA
  (≥3 letras, fora de conectivos/embalagens/números). Qualquer verde
  **não-exato** com divergência desce para AMARELO com motivo nominal
  ("cadastro tem termos ausentes na oferta (aurora) — confira a marca") — nos
  DOIS caminhos: fuzzy **e juiz** (nem a IA confirma marca divergente; §14:
  "nunca"). Exato/alias intocados (identidade aprendida). Testes com os pares
  REAIS da sessão: Campo Largo→Aurora e Bonare→Cajamar (com limiar forçando o
  caminho verde), match legítimo continua verde (Kitubaina), alias continua
  verde, e juiz confiante é rebaixado. **Trade-off aceito e testado**: 
  abreviação real ("REFRI"→"Refrigerante") agora é amarelo na primeira vez —
  a confirmação vira alias e as seguintes são verdes por identidade
  (`test_conciliacao` atualizado para o contrato novo, com justificativa).
- **S2 ✓ (unidade duplicada/quebrada)** — dupla correção: `_qtd_texto()` em
  `servico.py` normaliza o Decimal de verdade (o ":g" do Decimal NÃO normaliza:
  200.000→"200", 1.500→"1,5" pt-BR) e alimenta importação, catálogo e "do
  banco"; `nome_com_unidade()` no compositor NÃO anexa quando o nome já contém
  a unidade (normalização de espaço/vírgula/ponto: "1.5 L" pega "1,5L").
  Testados os três casos reais da tela (Italac 200g, Campo Largo 1,5L,
  Passatempo 130g) + anexo bom preservado + região UNIDADE presente.
- **Suíte: 195 verdes na máquina real, zero skips** (arte presente — os testes
  de detecção contam, como manda o §13).
- **S3–S6**: na fila do Bloco D/polimento, como ordenado (S5-TEXTO_LEGAL na
  barra é a primeira da fila — era o objetivo do G3 e é 3 linhas).

**F5.6 agora aguarda só o selo visual do Otaviano** (`saida_g3_verso.png` ×
`verso_referencia.png`) — lembrando a nota do §13: o +18 na Itaipava é
diferença ESPERADA (decidir se fica automático ou vira opção por item).
