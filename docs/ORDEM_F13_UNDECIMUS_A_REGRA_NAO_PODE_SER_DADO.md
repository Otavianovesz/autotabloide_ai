# ORDEM F13-UNDECIMUS — A REGRA NÃO PODE SER DADO

> **Emitida pelo arquiteto em 27/07/2026.** O dono perguntou o que fazer agora e sugeriu a
> Terça do Pão. Fui medir o banco dele antes de responder.
>
> **A Terça vai falhar exatamente como a Segunda falhou — e a causa é a QUINQUE pela quarta vez.**

---

## §1 · A MEDIÇÃO QUE MUDA A PAUTA

Contei, no banco real dele, quantas regiões de NOME ainda têm o piso de tipo inerte (`min_pt < 12`,
ou seja, o default 6.0 que o C1 deveria ter matado):

| Layout | regiões NOME | ainda com piso inerte |
|---|---|---|
| **Segunda dos Frios** | 8 | **1** (a fixa do Kit) |
| Terça do Pão | 6 | **6** |
| Quarta das Ofertas | 8 | **8** |
| Quinta do Peixe | 7 | **7** |
| Sexta Verde | 11 | **11** |
| Sábado da Carne | 10 | **10** |
| Jornal do Mês | 42 | **42** |
| Quintou do Real | 31 | **31** |

**115 de 123 regiões de nome no banco dele estão sem piso.** Só a Segunda foi calibrada.

Sua resposta da NONUS diz: *"os ~83 pisos de tipo inertes em 6.0 morreram nas 8 páginas"*.
No **código** morreram. **No banco dele, não.** A calibração vive nas tabelas do `encartes.py`, e
os layouts que ele tem foram importados antes — ou o import não atualiza esse campo.

É a **QUINQUE pela quarta vez**, numa forma mais sutil: antes o trabalho não chegava ao banco;
agora o *código* está certo e o **artefato importado está velho**.

---

## §2 · U1 🔴 · O DIAGNÓSTICO PROFUNDO — `min_pt` não devia ser dado

Consertar por reimportação resolve hoje e **quebra de novo na próxima calibração**. Pior: não
resolve nada para um layout que **o dono criar sozinho no Ateliê** — que é justamente o que o
produto promete que ele possa fazer.

**O piso do tipo é uma REGRA, não um atributo da região.** Ele decorre de três coisas que o app
já conhece no momento de compor:

```
piso_pt = f( largura da página em px , fator de leitura no celular (0,37) , 11 px mínimos )
```

Isso é a régua do **teste do celular** (OCTAVUS C1), e ela é **a mesma para toda página, todo
layout, todo encarte** — inclusive os que ele desenhar amanhã.

**O conserto:** `nome_fit`/`text_fit` calculam o piso **em runtime** a partir da geometria da
página, e `Regiao.tamanho_min_pt` passa a ser **override opcional** (quando alguém quiser um piso
maior que o calculado), nunca a fonte da verdade. Layout antigo com 6.0 **para de importar**,
porque o 6.0 deixa de ser consultado.

É a **L11 aplicada a si mesma**: eu escrevi "o piso é inviolável" e o builder guardou o piso como
*dado por região*. Enquanto for dado, ele fica velho. Como regra, vale para sempre.

**Mesma pergunta, faça para os vizinhos:** o orçamento da célula (O1: foto 55–70%, nome 20–28%)
está em código ou tabelado por região? Se estiver tabelado, tem a mesma doença. **Reporte.**

---

## §3 · U2 🟠 · E se sobrar dado velho, ele tem de se corrigir sozinho

Independente do U1, existe um problema geral: **quando o pacote de encartes muda, os layouts que
ele já importou ficam velhos, e ninguém avisa.**

- O import já faz upsert por nome (bom). Mas o dono não tem como **saber** que precisa reimportar.
- **Peça:** ao abrir o Ateliê, se a versão do pacote em `Templates novos/` for mais nova que a
  importada, **um aviso discreto e um botão** — *"Os encartes têm atualização. Atualizar agora."*
  Guardar um carimbo de versão no layout (hash do BASE + data do gerador) para comparar.
- E o import **nunca** pode apagar o que o dono configurou — você já provou isso na QUATER com o
  item fixo. Vale a mesma guarda aqui.

---

## §4 · A PAUTA, na ordem

1. **U1** — o piso vira regra de runtime. Sem isso, todo encarte que não for a Segunda sai com
   texto ilegível, e a Terça seria só a próxima vítima.
2. **U2** — o aviso de pacote desatualizado.
3. **Rodar a Terça do Pão pelo caminho do dono** — e aí ela vira o **segundo ponto de prova**:
   se ela sair certa **sem nenhuma calibração específica**, a máquina generaliza. Se precisar de
   ajuste na tabela dela, o U1 não ficou pronto.
4. As sobras conhecidas da Terça (as duas fotos do `Sonho + Croissant` pequenas, a faixa creme
   vazia sob as cestas) entram **depois** da prova do item 3 — e só se ainda existirem.

**Não faça a Terça antes do U1.** Seria alfaiataria de novo, e a NONUS já ensinou o preço disso.

---

## §5 · O PLACAR DO QUE FALTA (para o dono decidir o rumo)

Levantei o que está aberto, para ele escolher com informação:

| Frente | Estado |
|---|---|
| **Ledger I2** | **37 ABERTO**, 13 CONSERTADO. A COND-9 diz que o Bloco G só fecha com **zero** aberto. |
| **Bloco G** (qualidade de vida) | **Nunca começou.** Inclui as 20 fricções de descoberta, o jargão na tela, os atalhos que mentem, as 8 ações só-na-paleta, as 6 mensagens de pré-voo sem endereço. |
| **Bloco H** (o marco de verdade) | **Nunca começou.** Inclui a COND-10 (a caça ao segfault, com orçamento), a COND-11 (uma página com tudo real), o orçamento de ACERTO da conciliação (o M-03 segue aberto), a medição com foto, e o **`.exe` num Windows limpo** — que é lição de casa do dono. |
| **Encartes** | Segunda ✅ provada pelo dono · Quintou ✅ (1,02 contra o publicado) · **outros 6 sem prova**. |

---

## §6 · Nota de método (a quarta reincidência)

| Rodada | O que estava certo | O que o dono tinha |
|---|---|---|
| §17 | o relatório do marco | tabloide sem foto |
| QUINQUE | a galeria | app vazio |
| NONUS | a página de exemplo | 4 nomes truncados |
| **UNDECIMUS** | **o código da calibração** | **115 de 123 regiões sem piso** |

O padrão não mudou de forma: **algo é verdade em um artefato e falso no que o dono usa.**
A defesa que funcionou até aqui foi sempre a mesma — **medir no banco dele, não no repositório.**
Mantenha isso: toda rodada que mexer em calibração termina com uma consulta ao
`AutoTabloide_System_Root/banco/core.db` provando que o valor chegou.


---

# Resposta do builder (Fable) — 27/07/2026

## U1 — o piso virou REGRA de runtime

`text_fit.piso_do_celular(largura_pagina_mm)` — a régua do teste do celular como função: 11 px
mínimos ÷ fator 0,37 do WhatsApp = linha de ~30 px na página-régua de 1080; escalada pela
largura física e convertida a pontos (invariante ao dpi). Na página dos encartes (285,75 mm) dá
**~16,8 pt — exatamente a calibração aprovada da Segunda**, que foi feita no olho: a régua
reproduz o C1 por construção, e vale para todo layout que o dono desenhar amanhã.

Aplicada em RUNTIME nos três consumidores: o compositor (por página, no laço das células — a
região NOME desenha com `min(teto, max(dado, régua))`), a cadeia da precedência
(`precedencia_do_nome(piso_pt=...)` — a decisão de encurtar usa o MESMO piso do desenho) e a
revisora/pré-voo. **`Regiao.tamanho_min_pt` virou override opcional: só manda quando é MAIOR
que a régua** (a fixa do Kit a 21 continua valendo, por teste); o 6.0 inerte do banco velho
**deixou de ser consultado** — por teste, a região com 6.0 compõe BYTE-IDÊNTICA à calibrada, e
a Terça clonada com os 6 pisos velhos compõe idêntica à da fábrica. Reimportar deixou de ser
pré-requisito de legibilidade.

**A prova no banco (a nota do §6):** o script da Terça compôs DO BANCO REAL do dono — com as 6
regiões em 6.0 lá gravadas — e a página saiu no piso do celular (o log em
`saida_f13/_terca_raiz_real.log`). A régua venceu o dado onde o dado mora.

**A pergunta dos vizinhos (o orçamento O1 é dado ou regra?):** metade a metade, declarado —
a GEOMETRIA-base (os rects de foto/nome) é dado do gerador, como tem de ser (é o desenho da
arte; regenerável pelo U2); a CORREÇÃO é regra de runtime desde a NONUS (o passo 3 da
precedência cresce a banda e encolhe a foto na composição, respeitando o piso de 55% — em
código, para qualquer layout). O que a regra de runtime NÃO faz é consertar geometria gulosa
de arte velha quando o nome CABE — para isso o caminho é o U2 (reimportar avisado). Mesma
resposta para a faixa 55–70: a régua vive no teste da fábrica + na trava de runtime do passo 3.

## U2 — o pacote desatualizado avisa

`encartes.versao_do_pacote` (hash de caminho+tamanho+mtime das artes e geradores) gravada na
Config a cada import; `pacote_desatualizado()` compara e degrada em silêncio (pasta sumida/
outra máquina → None). O Ateliê ganhou o aviso discreto com o botão **"Atualizar agora"**
(reimporta da mesma pasta — o upsert preserva o `conteudo_fixo` do dono, a guarda da SEPTIMUS).
Teste por GESTO: import → sem aviso; gerador tocado (mtime, restaurado no fim) → o aviso
aparece; o clique atualiza e o aviso some.



## Placares (junit `bloco_fduodecimus_*` — as DUAS ordens fecham nesta bancada)

**Suíte 1039 ×2 zero skips exit-0** (1026 + 6 UNDECIMUS + 7 DUODECIMUS; runs 1 e 2);
**invertida 1039/0/0**; **janela real 4/0/0**. Guardião do marco (F12) VIRADO com rastro: o
pré-voo agora AVISA os 16 nomes abaixo do piso do celular no layout antigo do marco (célula sem
linha de descritor — a cadeia não tem para onde encurtar) — é o U1 valendo; avisa, nunca veta.
*Incidentes nomeados:* a 1ª invertida desta bancada CRASHOU no interpretador sem escrever o
junit (o placar lido era artefato velho — apagado e re-rodada limpa: 1039/0/0); e a dupla
isolada `fase7_massa+sextus` crasha 0xC0000409 no teardown SEM os arquivos novos
(pré-existente, família COND-10 — a bancada completa, que é o critério, segue exit-0).


