# ORDEM F13-QUINQUE — ENTREGUE NO APP (o achado que invalida seis rodadas)

> **Emitida pelo arquiteto em 26/07/2026.** O dono tentou abrir o app para montar a Segunda e
> disse: *"simplesmente nada está lá."*
>
> **Fui ao banco dele. Ele está certo, e isto é o achado mais grave de toda a F13.**

---

## §1 · O FATO: seis rodadas de encarte, ZERO encartes no app

Consultei `AutoTabloide_System_Root/banco/core.db` — o banco real da máquina dele:

```
layouts: 9
  1  Tabloide Belo Brasil          6  Frente Quintou
  2  Cartaz 10×15 — exemplo        7  Sexta Verde        ← ANTIGO (de antes do F)
  3  Layout do projeto             8  Terça do Pão       ← ANTIGO (de antes do F)
  4  Quintou Verso                 9  Terça
  5  Quintou Frente+Verso
```

**São os nove layouts que eu vi na tela dele no dia 25/07, na sessão ao vivo — antes de existir
uma linha de `encartes.py`.** Não há "Segunda dos Frios". Não há "Quarta das Ofertas". Não há
"Quinta do Peixe". Não há "Sábado da Carne". Não há "Jornal do Mês". O Quintou que está lá é o
antigo, não o novo.

**E a prova do mecanismo:**

```
grep "Database|Session|importar_pacote|salvar_layout" app/scripts/inspecao_encartes.py
→ (vazio)
```

`inspecao_encartes.py` — o script que gera **toda** a galeria que eu venho auditando — monta o
`LayoutDef` em memória com `layout_de_encarte()`, compõe, salva o PNG, e **nunca toca o banco**.

Então existe um caminho onde a galeria fica bonita e o app fica vazio. **Foi exatamente isso que
aconteceu, seis rodadas seguidas.**

O botão existe (`atelie.py:81`, " Importar encartes…") e o `_BASES` está correto — inclusive o
`"./Quintou"` com `Quintou Frente Fundo.png`. **O mecanismo funciona e nunca foi rodado contra a
raiz real dele.** Só contra `tmp_path` de teste.

---

## §2 · POR QUE ISSO É PIOR QUE FEIO

É a **mesma família do §17 do dossiê** — o marco que selou a Versão 1.0 com um tabloide sem uma
única foto. A doença é a mesma e ela reincidiu num nível mais fundo:

> **O projeto certifica trabalho contra um artefato que não é o produto.**

Antes era "medimos tempo e bytes, não conteúdo". Agora é "compomos em memória, não no app".
Em ambos os casos a bancada fica verde, a galeria fica linda, e o dono abre o programa e não
tem nada.

**LEI NOVA (L10), e ela vale para o resto do projeto:**
> *Nenhum trabalho de encarte, layout ou template é considerado feito enquanto não estiver
> ALCANÇÁVEL PELO DONO na interface. A prova de pronto é a lista do Ateliê na máquina dele —
> não um PNG numa pasta de saída.*

---

## §3 · A1 🔴 · A GALERIA E O PRODUTO PASSAM A COMPARTILHAR A PORTA

Este é o conserto estrutural, e ele é mais importante que qualquer ajuste visual.

`inspecao_encartes.py` **para de compor em memória**. O fluxo novo, obrigatório:

```
1. importar_pacote(sessão, "Templates novos")     ← a MESMA porta do botão do Ateliê
2. carregar_layout(sessão, nome)                  ← lê do BANCO, como a Mesa lê
3. compor_pagina(...)                             ← só então compõe
4. galeria + medidor
```

Assim, **uma galeria correta passa a provar que o app funciona.** Hoje ela não prova nada sobre o
produto. Se o import falhar, a galeria falha — e é isso que se quer.

**A2 🔴 · Rode o import na raiz REAL dele e prove.** Ao fim desta rodada, o banco
`AutoTabloide_System_Root/banco/core.db` tem de conter os 8 encartes, e a resposta traz o
`SELECT id, nome FROM layouts` de verdade, copiado do terminal. Sem isso, a rodada não fecha.

**A3 🟠 · O import tem de ser óbvio e falar.** Se o dono clicar "Importar encartes…" e apontar a
pasta, ele precisa ver: quantos entraram, quais, e **o que falhou e por quê** (I2). Encarte que
não entrou sai NOMEADO na tela, nunca em silêncio.

**A4 🟠 · Teste de gesto (L2):** um teste que clica o botão real do Ateliê, escolhe a pasta, e
prova por CONTEÚDO que os 8 layouts estão no banco e abrem na Mesa. É a lição do Bloco A
aplicada aqui — "chamar `importar_pacote` não prova que o botão funciona".

---

## §4 · A MINHA FALHA: as seis artes que eu não voltei a conferir

O dono: *"você nem sequer viu se as outras artes da semana estão finalmente OKs. Você só pulou
pra outras demandas e deixou o resto pra trás."*

**Correto.** Nas rodadas TER e QUATER eu auditei o que estava novo (Quintou, Jornal) e **nunca
reabri** Terça, Segunda, Quarta, Quinta, Sexta e Sábado depois dos consertos. Auditei a novidade
e abandonei o acumulado — o mesmo pecado que critiquei no builder.

E a varredura por evidência sugere que ele **também** não fechou tudo:

| Item da ORDEM_TER §6 | Evidência no `encartes.py` |
|---|---|
| `PESCA DO DIA` opcional (Quinta, D2) | **0 ocorrências** |
| `COLHEITA DA SEMANA` opcional (Sexta, D2) | **0 ocorrências** |
| `+18` grande (Sábado, V4) | 1 ocorrência |
| `Pão Francês` preenchendo o painel (Terça) | 1 ocorrência |

Zero ocorrências dos dois rótulos condicionais significa que ou eles saíram por completo (o que é
uma decisão aceitável, mas **não registrada**), ou o D2 não chegou a esses dois. **Preciso saber
qual**, e é isso que a tabela de rastreio existe para responder.

**A5 🔴 (repetida da QUATER, agora obrigatória):** a tabela de rastreio de **todas** as ordens
(BIS §2–§3, TER §3–§9, QUATER §2–§6), uma linha por item, `FEITO (prova) · PARCIAL (o que falta) ·
NÃO FEITO (por quê) · DECIDIDO NÃO FAZER (motivo)`. **A rodada não fecha sem ela**, e eu não selo
mais nada sem ela na mão.

**Meu compromisso:** na próxima rodada eu abro **as oito** páginas, não a novidade. E digo, por
página, se está OK ou não.

---

## §5 · O JORNAL COM 40 ITENS — o problema de densidade, com números

*"Os itens ficaram minúsculos e também são 40 no total."*

**40 itens em 2 páginas = 20 por página.** Numa faixa de conteúdo de ~1000×1100 px, isso dá
~55.000 px² por item. Não é pouco — **o problema não é a quantidade, é o desperdício dentro da
célula.** Contas para trabalhar em cima:

| Colunas | Células/pág | Tamanho da célula | Veredito |
|---|---|---|---|
| 5 × 4 | 20 | ~200 × 275 | o atual — foto sobra ~200×150, e some com o padding |
| **4 × 5** | 20 | **~250 × 220** | **foto ~250×130, mais larga = produto maior de fato** |
| 4 × 4 + hero | 16+ | ~250 × 275 | menos itens/pág, exige 3 páginas |

**Recomendação: 4 colunas.** A célula fica 25% mais larga, e como quase todo produto de mercado é
mais largo que alto (caixa, pacote, lata deitada), largura vale mais que altura.

**E o que realmente faz o item crescer, na ordem de impacto:**
1. **J10 🔴 Zerar o padding interno da célula.** Hoje há moldura, respiro e painel; some com os
   três. O produto recortado encosta na goteira.
2. **J11 🔴 Nome em 2 linhas, no máximo.** Hoje 3 linhas + descritor comem metade da célula. O
   descritor entra na mesma linha do peso ou sai.
3. **J12 🔴 Cabeçalho de seção fino de verdade.** Se cada uma das ~5 seções gastar 60 px, são
   300 px — 27% da faixa. Alvo: **≤ 28 px** por cabeçalho (versalete forte + fio, sem caixa).
4. **J13 🔴 Usar a altura toda.** A faixa vazia no rodapé que eu apontei no J5 é altura de graça —
   distribua nas linhas.
5. **J14 🟠 A etiqueta de preço compacta**, ancorada no canto, sem caixa própria em volta.
6. **J15 🟠 Se ainda ficar apertado, o hero da capa cede.** Um hero gigante numa página que tem de
   caber 20 itens é luxo — ou ele encolhe, ou vira um item destacado no fluxo.

**Regra de aferição:** a **foto** de cada item tem de ficar com **≥ 55% da área da célula**. Meça
e reporte — é número, não gosto.

---

## §6 · ORDEM DE ATAQUE

1. **A1 + A2 + A3 + A4** — o app receber os encartes. **Nada mais antes disso.** Enquanto o banco
   dele estiver com 9 layouts antigos, todo o resto é decoração.
2. **A5** — a tabela de rastreio, para pararmos de discutir no escuro.
3. **J10–J15** — o Jornal, medindo os ≥55%.
4. **Os dois rótulos condicionais** (D2 da Quinta e da Sexta) — decidir e registrar.
5. Só então galeria nova — e ela **vem do banco**, não da memória.

---

## §7 · Autocrítica

Três coisas minhas, sem rodeio:

1. **Auditei seis rodadas de encarte e nunca perguntei "isto está no banco dele?"** Eu tinha o
   dado na mão desde a sessão ao vivo do dia 25 — vi os nove layouts no Ateliê com meus próprios
   olhos — e não cruzei com o trabalho que vinha sendo entregue. O dono descobriu abrindo o app.
2. **Aceitei a galeria como prova de produto** por três rodadas. Escrevi no §9.4 do selo do F que
   "aparato de geometria é teste, não é inspeção" — e depois tratei um script de memória como se
   fosse o app.
3. **Abandonei os seis encartes antigos** ao correr atrás da demanda nova. É o comportamento que
   critiquei no builder, cometido por mim.


---

# Resposta do builder (Fable) — 27/07/2026

Na ordem do §6: A1–A4 primeiro, e nada antes deles.

## A2 — O APP RECEBEU OS ENCARTES (a prova, copiada do terminal)

Backup antes: `AutoTabloide_System_Root/backups/core_pre_quinque_20260727.db` (802 KB).
Depois `importar_pacote` na raiz REAL — a MESMA porta do botão:

```
raiz real: …\autotabloide_ai\AutoTabloide_System_Root
importados pela porta: ['segunda-frios', 'terca-do-pao', 'quarta-das-ofertas',
                        'quinta-do-peixe', 'sexta-verde', 'sabado-da-carne',
                        'jornal-do-mes', 'quintou']

SELECT id, nome FROM layouts (banco REAL do dono):
    1  Tabloide Belo Brasil          9  Terça
    2  Cartaz 10×15 — exemplo       10  Segunda dos Frios    ← NOVO
    3  Layout do projeto            11  Quarta das Ofertas   ← NOVO
    4  Quintou Verso                12  Quinta do Peixe      ← NOVO
    5  Quintou Frente+Verso         13  Sábado da Carne      ← NOVO
    6  Frente Quintou               14  Jornal do Mês        ← NOVO
    7  Sexta Verde  ← ATUALIZADO    15  Quintou do Real      ← NOVO
    8  Terça do Pão ← ATUALIZADO
```

Os ids 7 e 8 foram **ATUALIZADOS pelo upsert por nome** — o comportamento projetado do import
("importar de novo atualiza, nunca duplica"); as versões antigas vivem no backup. Os demais
antigos (1–6, 9) ficaram intactos. **Quando você abrir o Ateliê, a lista é esta.**

## A1 — a galeria e o produto compartilham a PORTA (o conserto estrutural)

`inspecao_encartes.py` não compõe mais da memória: `layout_do_banco(chave, pacote)` faz
`importar_pacote` (a porta do botão) → `carregar_layout` (o BANCO, como a Mesa lê) → só então
`compor_pagina`. Se o import falhar, a galeria falha — testado
(`test_a1_galeria_compoe_do_banco_pela_porta`). O **medidor A6 também** mede o que vem do
banco. Até a demo do Jornal por seções passa por `salvar_layout` → `carregar_layout` (prova o
roundtrip do fluxo: células, estilo JORNAL por página, camada). E o furo que isso expôs NA
HORA: `Pagina.arquivo_camada` (L9) **não era internado** — o layout importado apontaria para a
pasta do pacote e quebraria em outra máquina; a internação/resolução da camada entrou na
persistência com teste (I3).

## A3 — o import fala

O toast do botão agora diz **quantos e QUAIS pelo nome** ("8 encarte(s) na biblioteca: Segunda
dos Frios, …") e o que ficou de FORA com o motivo ("arte incompleta na pasta — confira os
BASE.png"). Nunca um número mudo.

## A4 — o teste de GESTO

`test_a4_botao_do_atelie_importa_por_gesto`: clica o botão REAL do Ateliê (monkeypatch só no
diálogo de pasta) e prova por CONTEÚDO: os 8 nomes no banco e o Quintou ABRE com as 2 páginas
via `carregar_layout`. Passou de primeira — o mecanismo sempre funcionou; **o que nunca tinha
acontecido era alguém apertá-lo contra a raiz real.** Exatamente a lição da L10.

## §5 — o Jornal denso, com o número

- **4 colunas** (célula ~247×216, 25% mais larga), degraus de altura 216→196→178 (J13: a
  altura toda), cabeçalho de seção **≤28 px** (11 pt + gaps apertados — J12, testado).
- **J10** padding zero: foto (w−6)×(alt−80), encostada na goteira. **J11** nome em ATÉ 2
  linhas (caixa de 34 px), peso na mesma linha via canal da unidade — a região de descritor
  SAIU da célula do fluxo. **J14** carimbo compacto 96×38 ancorado no canto inferior-direito.
- **A régua**: foto/célula = **64% no degrau 216 · 61% no 196 · 57% no 178** — ≥55% em TODOS
  os degraus, travado por teste numérico (`test_j10_regra_dos_55_por_cento_de_foto`).
- **J15** não foi preciso — o miolo bateu a régua sem o hero ceder.

## Os dois rótulos condicionais (a decisão REGISTRADA que o §4 cobrou)

`PESCA DO DIA` e `COLHEITA DA SEMANA` têm zero ocorrências **de propósito, e agora está
registrado**: o D2 da TER converteu TODO rótulo condicional em etiqueta que NASCE VAZIA — o
texto não mora mais no código; é escolhido pelo dono quando é VERDADE (a varredura permanente
`test_d2_nenhuma_etiqueta_nasce_cravada_no_pacote` impede rótulo cravado). As REGIÕES de
etiqueta EXISTEM na Quinta e na Sexta (builders, nome "Etiqueta"). Nas demos ficam vazias
porque os produtos reais das páginas não são pesca nem colheita — rótulo nunca mente.
Status: **DECIDIDO NÃO CRAVAR (mecanismo FEITO)**.

## A5 — TABELA DE RASTREIO (todas as ordens)

**BIS §2–§3** (a identidade dos 7): T1 FormaPreco 8 formas **FEITO** (testes + galeria) ·
T2 SUBTITULO/descritor **FEITO** · T3 rótulos por zona **FEITO** (specs dos builders) ·
T4 chips Nº 02–08 **FEITO** (Segunda) · T5 sem_hifen **FEITO** (lei viva; divergência com o
publicado do Quintou DECLARADA na QUATER) · T6 regeração **FEITO** (o pipeline rodou 3×: BIS,
TER-N2, QUINQUE) · laço §4 dos 7 **FEITO** (LEITURA_DO_LACO por página).

**TER §3–§9**: tabela completa na resposta da QUATER (§A5 de lá). Abertos que restam:
V3 régua formal "2 palavras a 40 cm" NOMINAL · §6-Terça prova célula-a-célula NOMINAL ·
§6-Sexta varredura fina NOMINAL · D3/J9 período = DECISÃO DO DONO · N1 fotos definitivas das
fixas = ESCOLHA DO DONO (o diálogo existe). Todo o resto FEITO com prova citada lá.

**QUATER §2–§6**: L9 · Q1–Q8 · A4 · A6 · J1–J8 **FEITOS** (resposta da QUATER); J9 aberto
(dono).

**QUINQUE**: A1 **FEITO** (porta única + camada internada, 2 testes) · A2 **FEITO** (o SELECT
acima) · A3 **FEITO** (o toast nomeia) · A4 **FEITO** (gesto verde) · J10–J14 **FEITOS**
(régua ≥55% por teste) · J15 **NÃO PRECISOU** (motivo acima) · rótulos **DECIDIDO NÃO CRAVAR**.

## Placares (bancada real, `--timeout=120`, junit `bloco_fquinque_*` em `saida_f13/`)

- Suíte inteira ×2: **991 verdes / 0 falhas / 0 skips, exit 0** nas duas (987 da QUATER + 4 da
  QUINQUE).
- Ordem invertida: **991/0/0, exit 0**. Janela real: **4/0/0, exit 0**.
- As quatro rodadas passaram **de primeira** — segunda bancada seguida sem incidente.

## O que fica aberto, com nome

1. As DECISÕES do dono: painel A×B do Quintou; período do Jornal; o formato por seções.
2. A reauditoria do arquiteto nas OITO páginas (o compromisso do §4) — a galeria nova vem DO
   BANCO: `saida_f13/galeria_f13_bis/`.
3. Nominais (LEDGER + resposta da QUATER): morte plena do FILETE; curadoria do acervo
   (QU-02/03); varredura fina Sexta/Terça; menu curto das etiquetas.

