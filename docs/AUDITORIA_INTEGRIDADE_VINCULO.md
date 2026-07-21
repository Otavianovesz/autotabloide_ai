# Auditoria Pessimista de Integridade — vínculo imagem × texto × preço

> Emitida em 2026-07-09 pelo arquiteto/auditor (Cowork), a pedido do Otaviano, após
> leitura integral de `rendering/`, `qt/canvas.py`, `qt/telas/mesa.py`, `qt/telas/servico.py`,
> `core/projetos.py`, `rendering/persistencia.py`, `qt/historico.py`, `images/biblioteca.py`.
> **Este documento é normativo**: define o gate da construção (o que fecha antes de
> qualquer fase nova) e os invariantes que nenhuma fase futura pode violar.

---

## 0. Resposta à pergunta central: como o trio imagem/nome/preço fica junto hoje?

A cadeia tem **dois elos de natureza diferente**:

**Elo 1 — dentro do item (FORTE).** `ItemMesa` é o átomo: nome, preço, `produto_id`,
`imagem`, `mais18` viajam no mesmo objeto. A imagem é amarrada ao produto por **ID de
pasta** (`biblioteca_imagens/<produto_id>/atual.png`), e o banco guarda só o caminho
relativo. Não há como a foto do produto 12 "virar" a do produto 30 por acidente — o
ID está no caminho. **Este elo está bem projetado.**

**Elo 2 — do item para a célula do tabloide (FRÁGIL).** O vínculo é **posição de
lista, nada mais**:

```
mesa._produtos()          → lista na ordem de self._itens (ordem de importação)
compor_pagina(...)        → for i, slot in enumerate(pagina.slots): d = lista[i]
ordem de pagina.slots     → ordem de detecção das caixas vermelhas na arte
```

O `Slot` **não sabe qual produto o ocupa**. Nenhum ID cruza o elo 2. O projeto
congelado salva `itens` (lista) + `layout` (slots em ordem) e reconstrói o casamento
por índice de novo ao abrir.

**Por que ainda não explodiu:** hoje não existe NENHUMA operação que reordene uma
lista sem a outra — não dá para reordenar itens na Mesa, não dá para excluir/criar
célula no editor, multipágina não existe. O vínculo correto é uma **coincidência
disciplinada, não uma garantia**. As três próximas fases do plano (F5.6 agrupamento
livre = criar/duplicar/remover células; F5.8 multipágina; melhorias da Mesa) atacam
exatamente as duas listas. Sem correção, a primeira dessas features produz tabloide
com **preço de um produto sob a foto de outro** — o pior erro possível do domínio
(preço errado exposto ao cliente do mercado).

**Agravante já existente hoje (não precisa de fase futura):** dentro de uma célula
derivada, `propagar_mestre()` pareia as regiões com a mestra **por ordem na lista**
(`zip(fontes, derivadas)` por tipo). `mover_regiao()` (reordenar z-order no painel
de camadas) muda essa ordem. Sequência real que troca conteúdo de lugar: célula com
2 imagens → usuário reordena o z de uma célula → edita a mestra → a propagação
aplica o rect/estilo da imagem A sobre a B e vice-versa. **Bug de troca de slot já
alcançável hoje.**

---

## 1. Veredicto de gate

**F5.5 volta a ABERTA (vira F5.5b — "trava de integridade"). F5.6 NÃO começa antes
de F5.5b fechada com os testes adversariais da §4.** Justificativa: todos os achados
P0 ficam mais caros de corrigir depois que agrupamento livre e multipágina
multiplicarem os pontos que tocam as duas listas.

---

## 2. Achados P0 — fecham a F5.5b (bloqueiam F5.6)

### P0.1 — Vínculo slot→produto por identidade, não por posição
- `ItemMesa` ganha `uid: str` (uuid4 na criação; sobrevive ao to_dict/from_dict).
- O projeto/Mesa mantém um **mapa explícito `{slot.id → item.uid}`** (os slots já têm
  id estável: `celula_0`…). O auto-preencher cria o mapa uma vez, na ordem visual;
  depois disso, toda recomposição/exportação/miniatura resolve por mapa, nunca por índice.
- `compor_pagina` passa a aceitar `dict[slot_id, DadosProduto]` (mantendo a lista por
  compatibilidade com scripts/testes antigos, com aviso de depreciação em comentário).
- O mapa é **persistido no projeto congelado** e restaurado ao abrir.
- Regra de resiliência: slot sem entrada no mapa → célula vazia (arte pura); uid sem
  slot → item "fora da grade" listado na estante, nunca descartado em silêncio.

### P0.2 — Pareamento mestra↔célula por uid, não por ordem
- `Regiao` ganha `uid` (uuid4). Região derivada guarda `ref_mestre = uid da região da
  mestra`. `propagar_mestre()` casa por `ref_mestre`, não por `zip` ordenado.
- Reordenar z-order deixa de poder cruzar os pares. Região da mestra excluída →
  derivadas com `ref_mestre` órfão são removidas (comportamento atual preservado,
  agora correto por identidade).
- Migração: layouts salvos sem uid ganham uids no `from_dict` casando pela ordem
  atual (uma única vez, na carga).

### P0.3 — Parser de preço à prova de milhar e de lixo
- `preco_decimal("1.299,00")` hoje vira `None` e o preço **some do tabloide sem
  aviso**. Corrigir: remover separador de milhar antes da vírgula decimal; aceitar
  "R$ 1.299,00", "1299", "1.299", "17,7"; rejeitar explicitamente (não silenciar)
  o que não parsear.
- Invariante: **nenhum slot ocupado compõe com preço `None` sem constar no relatório
  pré-exportação** (P0.4).

### P0.4 — Relatório pré-exportação (fim da degradação silenciosa)
Hoje: imagem apagada do disco → célula sai **sem foto**, em silêncio
(`compositor._carregar_imagens` faz `continue`); fonte ausente → `truetype` explode
com erro críptico no worker; preço `None` → célula sem preço. Antes de exportar
(PNG/PDF) e antes de salvar projeto, rodar validação por slot ocupado:
imagem existe? preço parseado? nome não-vazio? fonte de cada região existe (com
fallback declarado para Roboto)? Resultado: diálogo curto "13 ✓ · 2 pendências:
célula 7 sem foto (Arroz Camil), célula 12 sem preço (Amstel)". Exportar mesmo
assim = escolha consciente do usuário, nunca padrão.

---

## 3. Achados P1 — entram como itens nomeados no PLANO (Bloco D/F7), antes do teste de aceitação

- **P1.1 Caminhos absolutos no projeto congelado.** `estado_slots` grava caminhos
  absolutos (arte, imagens congeladas). A decisão travada "portabilidade
  casa↔mercado" quebra 100% dos projetos ao trocar de PC. Congelar com caminhos
  **relativos à pasta do projeto** e resolver ao abrir. Isso também elimina o hack
  frágil de `duplicar_projeto` (replace de string no JSON — quebra com separadores
  mistos e deixa o duplicado apontando para os arquivos do original: excluir o
  original corromperia o duplicado).
- **P1.2 Re-salvar projeto sobre si mesmo.** `_congelar_arquivo` com origem ==
  destino lança `SameFileError`. Hoje a UI só cria projeto novo, então é bomba
  armada para quando "salvar por cima" existir. Guarda: `if origem == destino:
  return origem`.
- **P1.3 Importar substitui a estante.** Segundo import na Mesa faz
  `self._itens = [...]` — perde tudo que já estava montado. Perguntar
  substituir/adicionar (e deduplicar por `produto_id` como o "Do banco" já faz).
- **P1.4 Sem edição de preço na Mesa.** "Do banco" põe o preço de banco como preço
  de oferta e não há como editar → tabloide pode sair com preço não-promocional.
  Edição inline (nome e preço) na estante da Mesa.
- **P1.5 Descarte invisível na conciliação.** Confirmar o diálogo descarta 🟡/🔴
  sem contagem ("N prontos" não diz "M ficaram de fora"). Informar ambos.
- **P1.6 `salvar_layout` sobrescreve por nome.** Criar layout com nome já existente
  substitui o antigo em silêncio (`where nome == nome`). Confirmar ou versionar.
- **P1.7 Unidade e validade não fluem.** `ItemMesa` não tem `unidade`; regiões
  UNIDADE e TEXTO_LEGAL nunca recebem conteúdo no fluxo da Mesa (validade fica só
  no rótulo da barra). Ligar os dois quando o layout tiver as regiões.

---

## 4. Teste adversarial padrão (obrigatório no fechamento de F5.5b e de TODA fase que tocar slot/item/região)

Script `app/scripts/teste_adversarial_vinculo.py` + testes: montar grade real
(Belo Brasil, 15 células) com 15 itens de conteúdo distinguível (nome = "PROD-i",
preço = i, imagem = quadrado com o número i renderizado), então, em sequência:

1. reordenar z-order de regiões em 3 células e editar a mestra (estilo + rect);
2. desfazer/refazer 10× intercalado com edições;
3. remover um item do meio da estante e adicionar outro;
4. deixar 2 itens a mais que células; depois 2 células a mais que itens;
5. preço "1.299,00" e preço vazio em itens distintos;
6. apagar do disco a imagem de um item;
7. salvar projeto, fechar, reabrir, duplicar o projeto, abrir o duplicado;
8. exportar PNG.

Verificação: para cada célula, o trio renderizado (número na imagem, nome, preço)
confere com o mapa esperado — **por conteúdo do pixel/texto, não por "não deu
exceção"**. Passos 5–6 devem aparecer no relatório pré-exportação.

---

## 5. Invariantes permanentes (copiar para o CLAUDE.md — nenhuma fase pode violar)

- **I1. Identidade, nunca posição:** todo conteúdo dinâmico (produto↔slot,
  região↔região-mestra) rastreável por ID estável. Índice de lista não é vínculo.
- **I2. Sem degradação silenciosa no que sai do app:** conteúdo ausente/inválido em
  exportação ou salvamento aparece em relatório visível; "pular em silêncio" é bug.
- **I3. Persistência portável:** nenhum caminho absoluto em JSON persistido
  (banco/projetos). Relativo à raiz da pasta correspondente, sempre.
- **I4. Casamento mestra↔célula por uid** (`ref_mestre`), imune a reordenação.
- **I5. Fase que toca slots/itens/regiões só fecha com o teste adversarial da §4
  atualizado e verde** — teste que tenta ativamente trocar conteúdo de lugar, não
  só o caminho feliz.

## 5b. Reauditoria do arquiteto (2026-07-09, pós-F5.5b) — VEREDICTO

Reli o código entregue (host, arquivo por arquivo) e o `test_adversarial_vinculo.py`.
**Confirmo o fechamento da F5.5b e a liberação da F5.6**, com 1 correção obrigatória:

**Confirmado no código (não só no relatório):** mapa `slot_id→uid` criado no
auto-preencher, resolvido em `_dados_por_slot()` e persistido em
`estado_slots["mapa"]` (P0.1 ✓); `propagar_mestre` por `ref_mestre` com migração
única e derivadas nascendo da propagação; `colar`/`duplicar_regiao` regeneram uid
(P0.2 ✓); pré-voo na Mesa (exportar E salvar), Fábrica, com `fonte_segura` de
fallback (P0.4 ✓); congelado 100% relativo com `_resolver` para legado absoluto,
guarda de re-salvar, `duplicar_projeto` sem o hack de replace (P1.1–1.2 ✓);
Adicionar/Substituir, edição por duplo-clique, contagem de descartados, confirmação
de sobrescrita no Ateliê, `unidade`/`texto_legal` fluindo (P1.3–1.7 ✓). O teste
adversarial verifica **por pixel** e cobre os 8 passos (I5 ✓). Evidência
independente de execução: bytecode do pytest gerado às 00:52 de 2026-07-09.

**P0.3b — correção OBRIGATÓRIA (primeiro commit da F5.6, antes de qualquer feature):**
o novo `preco_decimal` remove letras/espaços e **funde grupos de dígitos**:
`"2x 5,00"` → **25,00** e `"3 por 10,00"` → **310,00** — preço ERRADO em silêncio,
pior que o `None` de antes (viola o espírito do I2: valor errado é mais perigoso
que valor ausente, porque o pré-voo não acusa). Formatos promocionais assim
aparecem em tabela de oferta real. Correção: extrair os tokens `[\d.,]+` do texto
ORIGINAL; se houver **mais de um token com dígitos** ("2x" e "5,00"), devolver
`None` (ambíguo → pré-voo acusa). `"R$ 5,90 UN"` continua ok (1 token). Adicionar
aos casos do teste: `"2x 5,00" → None`, `"3 por 10,00" → None`, `"Leve 3 10,00" →
None`, `"R$ 5,90 UN" → 5.90`.

**P0.3b IMPLEMENTADO pelo arquiteto (Cowork) em 2026-07-09:** `preco_decimal`
agora extrai os tokens `[\d.,]+` do texto original e devolve `None` quando há
mais de um número (ambíguo) — "2x 5,00", "3 por 10,00", "Leve 3 10,00",
"2 un 9,90" → `None` (pré-voo acusa); "R$ 5,90 UN", "17,71 /kg", "10,00." →
parseiam. Casos adicionados ao `test_preco_decimal_adversarial`. Validação
independente: 24/24 casos numa execução isolada da função. **Também aplicados
nesta passada:** pré-voo cobre multi-imagem (`d.imagens`, cada foto do slot é
validada); `_gerar_miniatura` loga a falha (warning com traceback) em vez de
`pass` mudo; comentário enganoso do `_auto_preencher` corrigido (cada clique
repreenche; fora do clique o vínculo é por uid). **Pendência do builder: rodar
`pytest app/tests -q` na máquina para reconfirmar a suíte inteira.**

**Notas menores (P2, somar ao radar):** `validar_composicao` só checa
`imagem_path`, não a lista `imagens` (multi-imagem F4.5) — incluir quando a Mesa
usar multi-imagem; docstring de `_auto_preencher` diz "constrói o mapa UMA vez"
mas ele reconstrói a cada clique (semântica correta — clique = repreencher na
ordem visual —, docstring enganosa); `_gerar_miniatura` engole toda exceção (by
design, mas um dia mascarará um erro de mapa — logar em vez de `pass` silencioso).

## 6. Registro P2 (não bloqueia; manter no radar)

Detecção de grade é heurística Belo Brasil-específica (thresholds de vermelho,
offsets fixos `_REL_IMAGEM/_REL_NOME`, bandas fundem em grade escalonada) —
documentado como limitação; futura detecção assistida com confirmação do usuário.
Temp dirs (histórico, curadoria, staging) nunca são limpos — chamar
`Historico.limpar()` e varrer `atb_*` no encerramento. Undo versiona só o layout —
quando o mapa slot→uid existir (P0.1), versionar junto. Fundo com aspecto divergente
é redimensionado (distorce) sem aviso. Diálogo de conciliação não mostra a foto
original ao lado da tabela extraída (conferência humana do OCR fica mais fraca).
