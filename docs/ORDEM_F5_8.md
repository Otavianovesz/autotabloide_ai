# Ordem de Serviço — Fila S3–S6 + F5.8 (Multipágina)

> Emitida em 2026-07-09 pelo arquiteto (Cowork). **Normativa** — sucede a
> `ORDEM_F5_6.md` (F5.6 fechada, §16). Invariantes I1–I5 do CLAUDE.md valem
> integralmente. Ordem de execução: **Etapa A → Etapa B → Etapa C**, cada uma
> com suíte verde na máquina real antes da seguinte. As ressalvas de
> fidelidade do Otaviano foram adiadas por decisão dele para uma revisão geral
> pré-lançamento — não bloqueiam nada aqui.

## Etapa A — S3–S6 da sessão ao vivo (pequenas, alto valor)

- **A1 (S5a).** Região **TEXTO_LEGAL na barra e na paleta** do editor — era o
  objetivo do G3 ("Fica a Dica"/validade). Nasce pela regra C1 (slot da
  seleção ou slot livre). Bônus pequeno: propriedade "texto fixo" da região
  TEXTO_LEGAL editável no painel (hoje ela só desenha `dados.texto_legal`;
  para o "Fica a Dica" o texto é do LAYOUT, não do produto — campo
  `texto_fixo: str | None` na Regiao, precedência sobre `dados.texto_legal`,
  serializado).
- **A2 (S3).** Diálogo de curadoria ganha **campo de nome editável**
  (pré-preenchido com o enriquecido) — o humano corrige "Floccao"/"Po Trink"
  antes de cadastrar. O nome final vai para `nome_sanitizado`.
- **A3 (S4).** Curadoria ganha **"Buscar de novo"** com termo editável
  (pré-preenchido com o nome atual) — o caso Mococa→unhas se resolve na hora.
- **A4 (S5b).** Campo de cor do painel **valida** (regex `#RRGGBB`; inválido =
  borda vermelha e não aplica); "Salvar layout" **pré-preenche** o nome do
  layout em edição.
- **A5 (S6).** Trava de instância única: segunda instância detecta a primeira
  (lockfile + socket local) e traz a janela existente para frente em vez de
  abrir outra. Elevada ou não, nunca mais duas em silêncio.
- **A6.** Pendências que o builder listou na F5.7 seguem valendo; a F5.7 será
  reauditada pelo arquiteto junto com a entrega da Etapa A (nada a fazer além
  de manter os testes verdes).

## Etapa B — decisões de desenho da F5.8 (OBRIGATÓRIAS, modelo antes de UI)

A multipágina toca o terreno mais sensível (páginas × slots × mapa). Risco
novo que esta ordem trava ANTES do código:

**D8.1 — Colisão de ids entre páginas (CRÍTICO).** Hoje a detecção nomeia
`celula_0..N` por página: duas páginas do mesmo template = **ids duplicados**
e o mapa `{slot_id → uid}` quebra silenciosamente (I1 violado). Regra: ids de
slot são **únicos no LAYOUT inteiro**. Página nova gera slots
`celula_<uuid8>` (ou prefixo da página); a página 1 legada mantém os nomes
antigos (compat). `from_dict` valida unicidade e **recusa** layout com id
duplicado (erro claro, nunca silêncio). O mapa continua `{slot_id → uid}` —
plano, sem chave composta.

**D8.2 — Fundo POR PÁGINA.** `LayoutDef.arquivo_fundo` é único; frente+verso
têm artes diferentes. `Pagina.arquivo_fundo` (novo, serializado, default None
= herda o do layout — layouts antigos carregam sem mudança). Cada página nova
importa sua arte e roda sua própria detecção.

**D8.3 — Auto-flow na Mesa.** Auto-preencher varre as páginas na ordem
(página 1 → 2 → …), dentro de cada página na ordem visual (`ocupaveis` +
`ordenar_slots_visualmente` — regras existentes, agora por página). "Fora da
grade" só depois da ÚLTIMA página. O toast diz quantos por página.

**D8.4 — Navegação.** Editor e Mesa mostram UMA página por vez com navegação
explícita (abas ou ‹ ›). Adicionar/remover página no editor; remover página
remove as entradas do mapa dos slots dela (itens voltam à estante, aviso — e
undo restaura tudo, D5).

**D8.5 — Exportação.** PNG = um arquivo por página (`_p1`, `_p2`…); PDF =
**um arquivo multipágina** (Pillow multi-frame ou pypdf juntando). Pré-voo
varre TODAS as páginas (rotulando "página 2, célula X").

**D8.6 — Persistência e undo.** Projeto congelado guarda todas as páginas +
fundos (relativos, I3) + mapa único; undo versiona {layout completo, mapa}
como hoje. Miniatura do Dashboard = página 1.

**D8.7 — Teste adversarial estendido (I5).** Passos novos: layout com
frente+verso REAIS de `arte/quintou/` (30 células, ids únicos conferidos);
30 itens transbordando da página 1 para a 2 na ordem visual; remover a
página 2 → itens dela voltam "fora da grade" e undo restaura página+mapa;
salvar→reabrir→duplicar; exportar PNG×2 e PDF — **conferindo o trio por pixel
nas DUAS páginas** e que nenhum uid aparece em duas células.

## Etapa C — validação real e gate de fechamento da F5.8

O caso real completo, no fluxo do usuário: layout novo → frente_template
(página 1) + verso_template (página 2) → importar `ofertas_frente.txt` E
`ofertas_verso.txt` (Adicionar, P1.3) → 30 itens → auto-preencher →
pré-voo → exportar PNG×2 + PDF. O builder roda primeiro (self-check com as
referências); depois **sessão ao vivo com o arquiteto na tela** (como no gate
3) e reauditoria de código. A F5.8 só fecha com: suíte + adversarial
estendido verdes na máquina real, D8.1 provado (ids únicos), e a sessão ao
vivo aprovada.

Fora de escopo (não antecipar): arrastar produto entre células/páginas
(Bloco D), imposição de impressão, capa/miolo com templates mistos além de
frente+verso.

---

## Resposta do builder — Etapa A executada (2026-07-09)

- **A1 ✓** — TEXTO_LEGAL na barra e na paleta (nasce pela C1). `Regiao.texto_fixo`
  no modelo (serializado): precedência sobre `dados.texto_legal` e — a nuance
  que fazia o "Fica a Dica" impossível — **desenha mesmo em slot SEM produto**
  (o compositor ganhou o ramo do slot vazio). Campo "Texto fixo" no painel,
  visível só para TEXTO_LEGAL.
- **A2 ✓** — Curadoria com **campo de nome editável** (pré-preenchido com o
  enriquecido); `nome_final()` alimenta o cadastro na conciliação. No
  Almoxarifado (trocar imagem) o campo é somente-leitura — troca de foto não
  renomeia produto.
- **A3 ✓** — **"Buscar de novo"** com termo editável (pré-preenchido) + worker
  + overlay; os candidatos repovoam no lugar; estado vazio orienta a re-busca.
- **A4 ✓** — Cor valida `#RRGGBB` ("##ffffff" da sessão não aplica; borda
  vermelha + tooltip); "Salvar layout" **pré-preenche** o nome em edição
  (Ateliê injeta; re-salvar o próprio nome nem pede confirmação — sobrescrever
  OUTRO continua pedindo, P1.6 intacto).
- **A5 ✓** — `app/qt/instancia_unica.py` (QLocalServer/QLocalSocket): a
  segunda instância detecta a primeira, pede ativação e SAI; a primeira traz a
  janela para frente. Lock órfão de crash é limpo antes de escutar; a ativação
  dispara na CONEXÃO (não em readyRead — bytes que chegam antes do connect não
  perdem o sinal). Ligado no `editor_app.main`.
- **Bugs meus pegos pelos próprios testes da etapa**: `dpi` fora de escopo no
  ramo novo do compositor; import de QLineEdit faltando; sinal de ativação por
  readyRead perdia corrida — os três corrigidos antes de qualquer verde.
- **Testes**: `test_etapa_a.py` (8) — texto fixo em slot vazio POR PIXEL,
  precedência, serialização, barra/paleta, nome editável + re-busca +
  somente-leitura no Almox, cor inválida não aplica, Ateliê pré-preenche,
  segunda instância ativa a primeira. **Suíte: 203 verdes, zero skips.**

**Parado aguardando a reauditoria da Etapa A + F5.7** (A6). Etapa B (F5.8,
D8.1–D8.7) só após o selo.

---

## Reauditoria do arquiteto — Etapa A + F5.7 (2026-07-09)

**F5.7 (estilos): SELADA.** `estilos.py` espelha fielmente o padrão de
precedência do app; excluir estilo não muda a tela; captura/desvincular/
restaurar corretos; `estilo` propaga pela mestra sem arrastar `overrides_estilo`;
serialização completa (estilos no LayoutDef = viajam com o projeto, I3). A
matriz grade-override × estilo-override fica anotada como P2 (o painel marca
os dois juntos; caminho programático documentado só em teste — aceitável).

**Etapa A: A2–A5 SELADAS.** Curadoria com `nome_final()` alimentando o
cadastro e somente-leitura no Almoxarifado (distinção correta); re-busca com
worker; cor validada; prefill com P1.6 preservado; `instancia_unica.py` bem
resolvido (ativação na conexão — a corrida do readyRead foi bem pega; lock
órfão limpo). A honestidade de bancada (3 bugs próprios documentados) é o
padrão que este projeto exige.

**A1: APROVADA COM CORREÇÃO OBRIGATÓRIA — A7, o fantasma renasceu um andar
acima (bloqueia a Etapa B).** O slot do "Fica a Dica" agora TEM uma região
(TEXTO_LEGAL) — logo `ocupaveis` o considera ocupável, e o auto-preencher
**atribui um produto a ele**: com 16+ itens na estante, o 16º é consumido pelo
slot decorativo e some do tabloide sem aviso (o C5.2 só acusa slot SEM
regiões). Mesma classe de violação do I2 que a C5 matou — a definição de
"ocupável" ficou desatualizada quando A1 criou o slot decorativo.

- **A7.1** `ocupaveis` = slot com ao menos uma região **de conteúdo de
  produto** (IMAGEM, NOME, PRECO ou UNIDADE). Slot só-decorativo
  (TEXTO_LEGAL/SELO) não recebe produto. A regra continua morando num lugar só.
- **A7.2** Pré-voo: entrada do mapa apontando para slot decorativo → "item X
  está numa célula decorativa (só texto/selo) — não será desenhado".
- **A7.3** Testes: (a) grade + Fica a Dica + 16 itens → o 16º fica "fora da
  grade" e o pré-voo fica limpo; (b) mapa velho/congelado apontando para o
  slot decorativo → acusado. Suíte inteira verde na máquina real.

Fechada a A7, a **Etapa B (D8.1–D8.7) está AUTORIZADA** — modelo antes de UI,
começando pelo D8.1 (ids únicos no layout).

---

## SESSÃO AO VIVO DA ETAPA C EXECUTADA (2026-07-09) — F5.8 SELADA pelo arquiteto

Reauditoria prévia: A7 (regra `TIPOS_CONTEUDO` única + pré-voo decorativo),
D8.1 (`validar_ids_unicos` na carga E na adição — cinto e suspensório) e
self-check conferidos na fonte e nos artefatos. Depois, o fluxo REAL inteiro
na tela, conduzido pelo arquiteto: layout novo (frente) → **+página (verso)**
→ `‹ 2/2 ›` → Mesa → importar frente (15/15 conciliados, com a guarda S1
segurando "Itaipava×Amstel" no vermelho) → importar verso → **P1.3 "Adicionar
aos atuais"** → **a guarda S1 ao vivo: 4 AMARELOS nominais** (Campo
Largo×Aurora, Tio Urbano×Bulnez, Bonare×Cajamar, Passatempo×Nestle) →
decisões humanas corretas (3 "É novo" com A2/A3 usados — re-busca salvou a
Abóbora das telas de software; 1 "Aceitar" que aprendeu alias) →
auto-preencher **15+15 nas duas páginas na ordem visual** → **selo +18
automático na Itaipava** (decisão travada, funcionando) → pré-voo rotulando
"página 1, célula N" (32 pendências nominais — "sem foto" da esteira rápida,
não bugs) → **`etapaC_p1.png` + `etapaC_p2.png` + `etapaC.pdf` (2 páginas)**
→ projeto congelado salvo. O verso exportado confere com a referência:
**marcas certas, unidades limpas, preços 1:1**.

Achados residuais da sessão (fila de polimento, não bloqueiam):
- Enriquecimento trocou tipo ("Achoc." → "Chocolate com Leite") — o A2
  existe para isso; na esteira rápida o operador pulou a revisão. Reforça a
  recomendação: revisão de nome é passo obrigatório do fluxo humano.
- Nome da Itaipava ficou duplicado no banco ("Cerveja Itaipva Cerveja
  Itaipava 269ml") por erro de digitação DO ARQUITETO no campo A2 — corrigir
  pelo Almoxarifado (renomear produto). Não é bug do app.
- 20+ produtos sem foto no banco (esteira rápida) — curadoria contínua pelo
  Almoxarifado (buscar candidatos → definir imagem), fluxo que já existe.

**F5.8: FECHADA** (suíte 208 + adversarial multipágina verdes na máquina,
D8.1 provado, sessão ao vivo aprovada pelo arquiteto; ressalvas de fidelidade
do Otaviano seguem adiadas por decisão dele para a revisão geral). Próxima
ordem do arquiteto: consolidação do Bloco D (Fábrica/cartaz ponta a ponta,
Cofre/portabilidade F6.6–F7.4, Configurações F6.7) rumo ao teste final
categorizado.

---

## Resposta do builder — A7 + Etapa B executadas; Etapa C em self-check (2026-07-09)

- **A7 ✓** — `ocupaveis` agora exige região de **conteúdo de produto**
  (`TIPOS_CONTEUDO` = IMAGEM/NOME/PRECO/UNIDADE, exportado de `grade.py` — a
  regra segue morando num lugar só); pré-voo acusa "célula decorativa (só
  texto/selo)"; testes A7.3a (grade + Fica a Dica + 16 itens → 16º fora,
  pré-voo limpo) e A7.3b (mapa congelado apontando pro decorativo → acusado).
  A lição do arquiteto está gravada no docstring da própria regra.
- **D8.1 ✓** — `Pagina` nova nasce com slots `celula_<uuid8>` (página 1 legada
  mantém `celula_N`); `LayoutDef.validar_ids_unicos()` roda no `from_dict` e
  **recusa** duplicata com erro nominal (testado com o caso exato do risco:
  duas páginas do mesmo template). `adicionar_pagina_de_arte()` valida de novo.
- **D8.2 ✓** — `Pagina.arquivo_fundo` (serializado, default None = herda);
  compositor prioriza explícito > página > layout; canvas passa o fundo legado
  só na página 1.
- **D8.3 ✓** — auto-preencher varre páginas na ordem, `ocupaveis` por página,
  "fora da grade" só após a última; toast informa a contagem por página.
- **D8.4 ✓** — canvas opera na PÁGINA ATUAL (15 pontos de `paginas[0]`
  trocados por acessor); navegação ‹ N/M › no editor (com +página/−página,
  confirmação e undo) e na Mesa (aparece só com 2+); remover página limpa o
  mapa dos slots dela e **o undo restaura página+mapa juntos** (D5); undo
  clampa a página atual quando o layout encolhe.
- **D8.5 ✓** — PNG = `_p1.._pN`; PDF = um arquivo multipágina; pré-voo varre
  todas as páginas rotulando "página N, célula X".
- **D8.6 ✓** — congelado guarda os fundos POR PÁGINA (`arte_pN`, relativos,
  I3) e resolve no abrir; miniatura = página 1; duplicar leva tudo.
- **D8.7 ✓** — `test_multipagina.py` com as DUAS faces reais: 30 células com
  ids únicos conferidos; 30 itens (30 cores HSV distintas) fluindo 15+15;
  **pixel por célula nas duas páginas**; remover página 2 + undo restaurando
  página E mapa; congelar→reabrir→duplicar; PNG×2 + PDF (pypdf: 2 páginas);
  nenhum uid em duas células. **Passou de primeira. Suíte: 208 verdes.**
- **Etapa C (self-check) ✓** — fluxo real: frente+verso + as duas tabelas
  (30 itens) → mapa 15+15 → pré-voo com 21 pendências nominais por página
  (itens sem foto no banco — esperado) → `arte/quintou/selfcheck_p1.png`,
  `selfcheck_p2.png` e `selfcheck.pdf` (2 páginas). **Nota honesta:** o script
  forçou todos os itens a verde para pular o diálogo humano; os nomes
  divergentes que aparecem no selfcheck (Aurora, Bulnez e Rei) são os AMARELOS
  da guarda S1 na UI real — a curadoria é justamente o papel da sessão ao vivo.

**Aguardando a sessão ao vivo da Etapa C** (arquiteto na tela) e a reauditoria
de código para o fechamento da F5.8.
