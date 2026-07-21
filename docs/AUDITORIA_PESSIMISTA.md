# Auditoria Pessimista — resposta do builder (F5.5b fechada)

> 2026-07-09. Responde item a item a `AUDITORIA_INTEGRIDADE_VINCULO.md` (normativa,
> do arquiteto). Formato: **risco → o que foi blindado → como está provado**.
> Suíte: **174 testes verdes**, incluindo o adversarial da §4 (rodado 4× seguidas
> — é robusto ao embaralhamento aleatório interno).

## P0 — fechados (o gate da F5.5b)

### P0.1 Vínculo slot→produto por identidade ✓
- `ItemMesa.uid` (uuid4, sobrevive à serialização). A Mesa mantém **`_mapa
  {slot_id → uid}`**, criado UMA vez no auto-preencher; recomposição, exportação,
  miniatura do Dashboard e projeto congelado resolvem **pelo mapa, nunca por índice**.
- `compor_pagina` aceita `dict[slot_id → DadosProduto]` (lista/objeto único
  continuam para compatibilidade — legado).
- O mapa **persiste no projeto** (`estado_slots["mapa"]`) e volta no abrir; projeto
  antigo sem mapa cai no casamento por posição uma única vez (migração).
- Resiliência: slot fora do mapa → arte pura; item fora da grade → fica na estante
  **rotulado "· fora da grade"** (nunca descartado em silêncio).
- Provado: adversarial passos 3–4 e 7 (remover item do meio + **embaralhar a
  estante** + reabrir/duplicar → **pixel da imagem de cada célula confere com o
  produto do mapa**).

### P0.2 Pareamento mestra↔célula por uid ✓
- `Regiao.uid` + `ref_mestre`; `propagar_mestre` casa por identidade. A grade
  **nasce pela propagação** (células vazias + âncora → derivadas já nascem com
  `ref_mestre`); duplicar/colar geram uid próprio; layouts salvos sem uid migram
  por ordem uma única vez na primeira propagação.
- Provado: adversarial passo 1 — **reverti o z-order de 2 células e editei a
  mestra**: o rect novo foi para a IMAGEM certa e a cor para o PREÇO certo.

### P0.3 Parser de preço à prova de milhar ✓
- Novo `preco_decimal`: último separador com 1–2 dígitos = decimal; o resto é
  milhar. "R$ 1.299,00"→1299.00 · "1.299"→1299 · "17,7" · "<> R$ 17,71" ·
  "1,299.00" · "5.90" · lixo→None. Teste dedicado com 12 casos.
- Preço não parseado agora aparece **na estante** ("· sem preço") e no pré-voo.

### P0.4 Relatório pré-exportação ✓
- `validar_composicao()` por slot ocupado: imagem **sumida do disco**, item sem
  foto, **preço não entendido**, nome vazio, **fonte ausente** (avisa o fallback);
  no cartaz: sem "de" e **"de" ≤ "por" → risco PROCON**.
- Diálogo de pré-voo na Mesa (exportar E salvar projeto) e na Fábrica —
  **"seguir mesmo assim" é escolha, nunca padrão** (I2).
- Fonte ausente **não derruba mais a exportação**: cadeia pedida → Roboto →
  embutida do Pillow (compositor E text_fit), sempre anunciada no pré-voo.

## P1 — todos fechados nesta passada

| # | Risco | Blindagem |
|---|---|---|
| P1.1 | Caminhos absolutos no congelado (quebrava a portabilidade) | `estado_slots` agora grava **relativos à pasta do projeto** (I3); `abrir` resolve; legado absoluto passa. `duplicar_projeto` perdeu o hack de replace de string — copytree basta e o duplicado enxerga os próprios arquivos |
| P1.2 | Re-salvar sobre si mesmo → `SameFileError` | `_congelar_arquivo` devolve o relativo quando origem == destino |
| P1.3 | 2º import apagava a estante | Pergunta **Adicionar / Substituir** (adicionar deduplica por produto_id) |
| P1.4 | Sem edição de preço na Mesa | **Duplo-clique na estante** edita nome e preço "por"; recompõe na hora se o item está na grade |
| P1.5 | Descarte invisível na conciliação | Toast informa "N na estante · **M ficaram de fora**" |
| P1.6 | `salvar_layout` sobrescrevia por nome | Editor confirma sobrescrita |
| P1.7 | Unidade e validade não fluíam | `ItemMesa.unidade` (do peso do banco) → região UNIDADE; validade da oferta → TEXTO_LEGAL ("Ofertas válidas …") |

## O que fica (P2, registro do arquiteto — mantido no radar)

Detecção de grade Belo Brasil-específica; temp dirs `atb_*` sem varredura no
encerramento; undo não versiona o mapa slot→uid junto do layout (fazer quando o
arrastar-para-slot existir — é quando o mapa muda fora do auto-preencher); fundo
com aspecto divergente redimensiona sem aviso; conciliação sem a foto original ao
lado; miniatura de célula "capenga" quando a caixa de preço varia de tamanho entre
células (a propagação usa o tamanho da mestra — as artes têm caixas iguais).

## Invariantes I1–I5: como este código os cumpre

- **I1**: mapa slot→uid é a única verdade do preenchimento; região↔mestra por uid.
- **I2**: estante rotula pendências; pré-voo antes de exportar/salvar; fallback de
  fonte anunciado.
- **I3**: projeto congelado 100% relativo; banco já era relativo (biblioteca).
- **I4**: `ref_mestre` em toda derivada, desde o nascimento (grade nasce propagando).
- **I5**: `test_adversarial_vinculo.py` cobre os 8 passos da §4 e **verifica por
  pixel**; roda na suíte. Toda fase futura que tocar slot/item/região o atualiza.
