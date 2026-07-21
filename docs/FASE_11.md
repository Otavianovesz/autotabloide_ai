# FASE 11 — Cartaz & Fábrica completos + inteligência (caderno de 100 passos)

> Formato-lei do PLANO_PERFEITO. Cobre R-105–R-114 (cartaz completo, 2-em-1,
> cartaz-relâmpago, QR, kit gôndola) + R-115–R-123 + R-126 (inteligência do
> negócio, só leitura). **VETADOS — não construir:** R-116/R-119/R-124/R-125
> (custo/margem, diário de alterações, backup em nuvem, ERP).
> **Emissão em lote (19/07)** — ver cabeçalho da FASE_4.md. Chat novo por fase.
> **Intensidade: Alto.**
>
> **Por quê da fase:** o cartaz de gôndola é metade do negócio, e o dono não o
> testou a fundo ainda; e a inteligência de preço/histórico é serviço direto
> a ele. **Decisões travadas que guiam tudo:** o cartaz é 1 item/página no
> tamanho físico exato (mm), RGB padrão; o 2-em-1 é imposição CONTROLADA só no
> cartaz e só se o dono ligar — NUNCA no tabloide; a inteligência é SÓ LEITURA
> e LOCAL, sem tocar nos vetos (custo/margem/ERP); o import de Excel reusa a
> disciplina de chave natural (I1) do Bloco D.

## Bloco A — Cartaz completo (R-105, R-107, R-109, R-110, R-111, R-113, R-114) · passos 1–20
**Por quê:** completar o produto que é metade do negócio — do balcão ao PDF
num clique, legível a 5 metros, com de/por e validade.

1. R-105 (biblioteca de layouts de cartaz): A4 retrato, A4 paisagem, meia folha (A5), etiqueta de prateleira — layouts prontos.
2. Cada layout de cartaz é 1 item por página, no tamanho físico exato (mm) — decisão travada (sem NUP no tabloide).
3. Escolher o layout na Fábrica (a tela do cartaz, Bloco D já fechado) e ver a prévia no tamanho real.
4. R-107 (preço gigante autoajustado): o "por" ocupa o máximo legível — ajusta o corpo da fonte ao espaço, legível a 5 metros.
5. O autoajuste respeita um mínimo/máximo são (não estoura a caixa nem some) — herda o reflow da F5 (o preço manda).
6. R-109 (de/por com % de desconto): calcular e mostrar o percentual a partir do "de" e do "por".
7. O % é calculado, não digitado: (de−por)/de; arredondamento claro; some se não houver "de".
8. R-110 (cartaz-relâmpago): no Almoxarifado, 1 clique num produto → PDF do cartaz pronto (do produto ao PDF sem montar nada).
9. O cartaz-relâmpago usa o layout padrão do dono + os dados do produto (de/por, foto oficial) — velocidade de balcão.
10. R-111 (validade discreta no rodapé): uma data pequena no rodapé para o dono caçar cartaz vencido na loja.
11. A validade vem do evento/regra (F3) e nunca fica vazia (regra RG-58) — some só se o dono desligar.
12. R-113 (kit ponta-de-gôndola): gerar cartaz + etiquetas do MESMO item de uma vez (o kit da promoção).
13. O kit mantém a coerência (mesmo preço/validade) entre o cartaz e as etiquetas (uma fonte de verdade).
14. R-114 (QR opcional): um QR opcional no cartaz (link do encarte, catálogo) — desligado por padrão.
15. O QR é gerado localmente (sem serviço externo) e é opcional — coerente com o app offline.
16. O "por" continua editável na Fábrica (Bloco D fechado) e o pré-voo do cartaz (cartaz=True) vale em todos estes caminhos.
17. Foto: a biblioteca de layouts, preço gigante, de/por com %, cartaz-relâmpago, validade no rodapé, kit, QR (claro/escuro).
18. Teste: cartaz-relâmpago gera PDF no tamanho exato (pypdf medindo mm); o % de desconto confere.
19. Teste: preço gigante autoajusta sem estourar; validade nunca vazia; kit mantém a coerência.
20. **Checagem:** suíte parcial verde; o PDF do cartaz medido em mm bate com o layout escolhido.

## Bloco B — Impressão (R-106, R-108, R-112) · passos 21–34
**Por quê:** imprimir bem e econômico — sem jamais violar a decisão travada
(sem imposição no tabloide).

21. R-106 (2-em-1): dois A5 por folha A4 para economizar papel — imposição CONTROLADA.
22. **Decisão travada:** o 2-em-1 é SÓ no cartaz e SÓ se o dono ligar — NUNCA no tabloide (o tabloide é 1 item/página no tamanho exato).
23. O 2-em-1 é imposição de verdade (posiciona 2 cartazes A5 num A4 com margem de corte) — testar o tamanho físico com rigor.
24. Marcas de corte opcionais no 2-em-1 (para o dono cortar reto).
25. R-108 (lote por categoria): imprimir só uma categoria ("só o açougue") — filtra e manda o lote.
26. O lote por categoria reusa os filtros da estante (F6) — uma lógica só.
27. R-112 (imprimir direto na fila): mandar o cartaz/lote direto para a impressora do Windows (QPrinter), sem exportar PDF antes.
28. A impressão direta respeita o tamanho físico (mm) e a orientação — o que sai na bandeja bate com a prévia.
29. A prévia de impressão (da F5) vale para o cartaz e o 2-em-1 — o dono vê antes de gastar papel.
30. Impressão RGB padrão (CMYK opcional, decisão travada) — sem exigir perfil de cor do dono.
31. Foto: 2-em-1 com marcas de corte, lote por categoria, diálogo de impressão direta (claro/escuro).
32. Teste: o 2-em-1 posiciona 2 A5 num A4 com o tamanho físico certo (medido); o lote por categoria filtra certo.
33. Teste: a impressão direta respeita o tamanho (mock do QPrinter medindo a página).
34. **Checagem (marco 1/4):** suíte inteira ×1 verde exit 0; screenshots de impressão em `saida_fase11/`.

## Bloco C — Inteligência do negócio, só leitura (R-115, R-117, R-118, R-120, R-121, R-122, R-123, R-126) · passos 35–62
**Por quê:** serviço direto ao dono — ver o histórico, comparar, exportar —
sem tocar nos vetos (custo/margem/ERP).

35. R-115 (histórico de preço por produto): um gráfico do preço ao longo do tempo, com "menor preço do ano" marcado.
36. O histórico lê as edições passadas (chave natural, I1) — o preço de cada semana em que o produto entrou.
37. O gráfico é claro e leve (o dono lê de relance); sem custo/margem (VETADO — só preço de oferta).
38. R-117 (relatório da edição): itens por categoria, distribuição de preços, quantos sem foto — um resumo da edição.
39. O relatório é gerado do estado real do projeto e é imprimível/exportável (conversa com o checklist da F7).
40. R-118 (exportar/importar acervo em Excel): a ponte universal — o acervo vai para .xlsx e volta.
41. O import do Excel reusa a disciplina de CHAVE NATURAL (I1) — nunca troca produtos por id; conflito nunca em silêncio (lição da portabilidade do Bloco D).
42. O export leva nome/preço/categoria/EAN (não caminho de foto absoluto, I3) — ponte de dados, não de arquivos.
43. **Checagem (marco 2/4):** suíte parcial verde; o Excel ida-e-volta preserva o acervo (roundtrip por chave natural).
44. R-120 (ranking dos mais ofertados): quais produtos mais entram nos encartes — o dono vê seus carros-chefe.
45. R-121 (memória sazonal): "ano passado nesta semana você ofertou X" — lembrete do que funcionou.
46. A memória sazonal lê o histórico por data (chave natural) — sugestão, não imposição.
47. R-122 (meta por evento): definir uma meta simples por evento ("40 itens no Quintou") e ver o progresso na montagem.
48. A meta é do dono (ele define), informativa, sem cobrança — só o pulso ("32/40").
49. R-123 (alerta de preço divergente entre páginas): avisar se o MESMO produto aparece com preços diferentes em páginas do mesmo encarte.
50. O alerta usa a identidade do produto (uid/chave, I1) — pega a divergência real, não coincidência de nome.
51. R-126 (saúde do acervo com metas): um painel de saúde (quantos com foto, com EAN, com preço recente) com metas simples.
52. A saúde do acervo conversa com a integridade (R-129, F3) e o avaliador de foto (F9) — uma visão só.
53. **Lembrete dos VETOS (não construir):** R-116/R-119/R-124/R-125 — sem custo/margem, sem diário de alterações, sem backup em nuvem, sem ERP. Registrar no caderno para ninguém "completar" sem querer.
54. Toda a inteligência é SÓ LEITURA (não muda o acervo) e LOCAL (nada sai da máquina) — coerente com os vetos e o offline.
55. Os relatórios/gráficos carregam sob demanda (não pesam o boot nem a Mesa).
56. Nada aqui inventa número: os gráficos leem dados reais; sem dado, dizem "sem histórico ainda" (I2).
57. Foto: histórico de preço, relatório da edição, ranking, memória sazonal, meta por evento, alerta de divergência, saúde do acervo (claro/escuro).
58. Teste: o histórico reflete as edições (chave natural); o alerta de divergência dispara com o mesmo produto a dois preços.
59. Teste: ranking e memória sazonal leem o histórico certo; a meta por evento mostra o progresso.
60. Teste: nenhum recurso vetado existe (varredura por R-116/R-119/R-124/R-125 ausentes).
61. Teste: a inteligência é só-leitura (não altera o acervo, provado).
62. **Checagem (marco 3/4):** suíte inteira ×1 verde exit 0; screenshots da inteligência em `saida_fase11/`.

## Bloco D — Disciplina: imposição, Excel e vetos · passos 63–74
**Por quê:** o 2-em-1 é imposição (risco físico) e o Excel toca identidade
(risco de troca de produto) — os dois pedem rigor extra.

63. Bateria de medição do 2-em-1: A4 com 2 A5, margens e marcas — o tamanho físico de cada metade confere (mm).
64. O 2-em-1 nunca vaza para o tabloide (guarda testada: o tabloide segue 1 item/página, sem imposição).
65. Import de Excel adversarial: ids que colidem entre PCs, nomes iguais de produtos diferentes — casa por chave natural, conflito avisado (nunca troca em silêncio).
66. Export → edita → import roundtrip: o acervo volta idêntico por chave natural (byte a byte nos campos).
67. Excel com lixo (linha em branco, cabeçalho, célula vazia) → import honesto (ignora o que não é produto, avisa).
68. O cartaz-relâmpago e o kit respeitam o pré-voo cartaz=True (sem foto/preço avisa antes do PDF, I2).
69. Nenhuma função desta fase toca custo/margem (veto) — a varredura confirma a ausência.
70. Toda a inteligência é portável (I3): relatórios/gráficos não gravam caminho absoluto.
71. Rodar o adversarial do vínculo onde a fase toca identidade (Excel import, divergência entre páginas).
72. Compor um encarte com o mesmo produto em 2 páginas e provar o alerta de divergência (por identidade).
73. Foto: a medição do 2-em-1 + o roundtrip do Excel (antes → depois idêntico) claro/escuro.
74. **Checagem:** suíte parcial verde; 2-em-1 medido, Excel roundtrip por chave natural, vetos ausentes.

## Bloco E — Integridade e adversarial (I1–I5) · passos 75–86
**Por quê:** a fase toca cartaz (tamanho físico), Excel (identidade) e
histórico (chave natural) — o juiz é a régua de mm + o adversarial.

75. Re-rodar `test_adversarial_vinculo.py` com Excel import e cartaz-relâmpago.
76. Adversarial: import de Excel casa por chave natural — nunca troca fotos/dados entre produtos (lição do remap do Bloco D).
77. Adversarial: cartaz-relâmpago pega os dados do produto certo (por uid), preço de/por e foto oficial.
78. Confirmar I1: histórico, ranking, sazonal, divergência — tudo por identidade, nunca por posição/nome.
79. Confirmar I2: 2-em-1 sem foto, Excel com conflito, meta sem dado — tudo avisa, nada em silêncio.
80. Confirmar I3: cartazes, relatórios e Excel sem caminho absoluto; portáveis casa↔mercado.
81. Confirmar a decisão travada: sem imposição no tabloide (guarda testada); 2-em-1 só no cartaz e só se ligado.
82. Rodar a suíte inteira ×2, zero skips (a arte real conta).
83. Medir os PDFs de cartaz/2-em-1 em mm (a régua de bytes) num teste único.
84. Medir o boot: inteligência/relatórios carregam sob demanda; boot intacto.
85. Varredura de órfãos e de vetos: nada sem uso; R-116/R-119/R-124/R-125 ausentes.
86. **Checagem:** adversariais verdes; I1–I5 reconferidos; réguas de mm do cartaz conferidas.

## Bloco F — Fechamento · passos 87–100
**Por quê:** fase selada só com o cartaz completo medido e o Excel
indo-e-voltando sem trocar nada.

87. Suíte inteira ×2 exit 0, zero skips.
88. Adversariais do vínculo: nominais verdes (a fase tocou cartaz/Excel/histórico).
89. Teste novo `test_fase11_cartaz.py`: cartaz-relâmpago em mm, % de desconto, 2-em-1 medido, Excel roundtrip por chave natural, alerta de divergência, vetos ausentes.
90. Demonstração ponta a ponta: no Almoxarifado, 1 clique num produto → cartaz-relâmpago PDF → kit com etiquetas → 2-em-1 para imprimir.
91. `saida_fase11/`: layouts de cartaz, preço gigante, de/por %, relâmpago, validade, kit, QR, 2-em-1, lote, histórico, relatório, ranking, sazonal, meta, divergência, saúde — claro e escuro.
92. GIF curto (~15 s): cartaz-relâmpago do Almoxarifado ao PDF em 1 clique.
93. Varredura de jargão (PT-BR: "cartaz-relâmpago", "dois por folha", "histórico de preço").
94. Conferir a decisão travada (sem imposição no tabloide) por teste.
95. Conferir os vetos ausentes (R-116/R-119/R-124/R-125) por varredura.
96. Boot e responsividade medidos com a inteligência aberta num acervo de 5k.
97. Resposta do builder NESTE caderno (achados de bancada + "o que ficou de fora").
98. Atualizar `docs/PLANO_DE_CONSTRUCAO.md` e conferir o `CLAUDE.md`.
99. Screenshot-cartaz do produto cartaz + inteligência (relâmpago + histórico) claro + escuro lado a lado.
100. **PARAR** para a reauditoria visual do arquiteto — o cartaz medido em mm, o 2-em-1 físico, o Excel roundtrip por chave natural. Nada da Fase 12 começa sem o selo.

---

## Resposta do builder (2026-07-20) — PARADO no passo 100

**Ritual de retomada:** CLAUDE.md + FASE_11.md + PLANO lidos; baseline
`pytest app/tests -q` **ANTES de tocar em nada = 665 verdes, 0 fail/err/skip,
exit 0**. 4 scouts de LEITURA no início (cartaz/mm+2-em-1 · Excel/chave natural ·
inteligência só-leitura+vetos · impressão/lote/worker), ~lidos os arquivos-núcleo
no disco real. Implementação **100% INLINE**.

**Placar final: baseline 665 → 708 verdes ×2, ZERO skips, exit 0 LIMPO nas duas
rodadas** (+43: `app/tests/test_fase11_cartaz.py` 42 casos + 2 adversariais novos
em `test_adversarial_vinculo.py`). Placar por junit XML (bancada Windows).

### O que foi feito, por bloco
- **A (cartaz completo):** biblioteca de layouts em mm (`PRESETS_CARTAZ`), preço
  gigante (já existia, max generoso), **% de desconto CALCULADO** ((de−por)/de,
  `percentual_desconto` + `PapelTexto.DESCONTO`, some sem "de"), cartaz-relâmpago
  + kit no Almoxarifado, validade no rodapé (papel VALIDADE, RG-58), QR (qrcode
  real). Prova por PIXEL do "-XX%" (recorte da região com/sem tinta) + mutação.
- **B (impressão):** 2-em-1 (`impor_2em1`, A4 paisagem, marcas de corte, medido
  em px), lote por categoria (reusa `filtrar_itens`), impressão direta (QPrinter
  em mm+orientação via `QPageLayout`, provado medindo o PDF), **Fábrica ganhou
  closeEvent** (lei exit-0). Achado próprio corrigido: retrato×paisagem.
- **C (inteligência só-leitura + Excel):** módulo `inteligencia.py` (funções
  PURAS injetáveis) + `inteligencia_dialog.py` (sparkline PIL) + `excel_acervo.py`
  (roundtrip por chave natural, prévia→confirma, I2/I3) + `importar_planilha_dialog`.
  Vetos ausentes por varredura de identificador de código.
- **D (disciplina):** guarda testada "2-em-1 nunca no tabloide"; Excel sem coluna
  id; nomes iguais/marcas diferentes = produtos distintos; kit respeita pré-voo.
- **E (adversarial):** `test_adversarial_vinculo.py` +2 — Excel casa por chave
  natural (edita os 2 preços, cada um no SEU lugar, fotos intactas) e relâmpago
  compõe o produto certo (por conteúdo). 31 adversariais verdes.
- **F (fechamento):** galeria `saida_fase11/` claro+escuro (biblioteca, cartaz
  de/por %, relâmpago, QR, kit, 2-em-1, saúde, ranking, histórico), GIF do
  relâmpago, jargão PT-BR testado, boot medido.

### Achados de bancada (meus, pelos próprios testes/smoke) — corrigidos
1. **Impressão saía RETRATO num layout paisagem** — o Qt normaliza o `QPageSize`
   para retrato e trata a orientação à parte; `setPageOrientation` sozinho não
   pegou. Corrigido com `QPageLayout(tam_retrato_normalizado, orientação)`.
   Medido no PDF: paisagem 297×210, retrato 210×297, A5 148×210 (tol. 0,2 mm).
2. **A reescrita de `layout_cartaz_exemplo`** (5→6 regiões, imagem 84→90 mm)
   quebrou 3 testes que CRAVAVAM a estrutura incidental (`test_atelie` ×2,
   `test_fase10` upscale) → consertados DERIVANDO da produção (nº de regiões e
   maior lado da célula), não mascarando (I5).
3. **A varredura de vetos pegava PROSA** ("nada sai para a nuvem" do sobre.py; a
   minha própria docstring de vetos) → refeita por IDENTIFICADOR de código (a
   ausência da FEATURE, não da palavra).

### O que ficou de fora (declarado)
- A **IA local não roda na bancada** (sem LM Studio/GPU): a inteligência é toda
  determinística e testada com edições fabricadas + o banco real (seeds); nada
  aqui depende de IA.
- **UI mais rica** possível na F12/polimento: gráficos da inteligência com eixos
  rotulados, painel de meta na barra da Mesa, prévia de impressão nativa
  (`QPrintPreviewDialog`) — hoje a prévia é a imagem `previa_impressao` da F5.
- O **QR** desenha-se sobre a composição no relâmpago; incluí-lo como REGIÃO
  editável do layout (posição/tamanho no editor) fica para o polimento.

### Subagentes
- **Início:** 4 scouts de LEITURA (Explore), read-only, um por eixo.
- **Fecho:** frota adversarial de 4 revisores (Workflow) + verificadores céticos
  independentes por achado. Resultado e correções na subseção abaixo.

**A FROTA ADVERSARIAL (4 revisores + verificadores céticos independentes por
achado) leu o disco real e confirmou 6 bugs — os 2 refutou corretamente. TODOS
corrigidos ANTES do selo, com teste (honestidade de bancada):**

1. **[CRÍTICO] `excel_acervo.py` casava o conflito por ID, não por chave natural.**
   Se o produto fosse renomeado ENTRE analisar e aplicar (id igual, chave nova),
   `USAR_PACOTE` gravava no produto ERRADO em silêncio (viola I1). A portabilidade
   tem a guarda E-A2; o Excel não tinha. **Corrigido:** o conflito casa por
   `chave_natural` (não `s.get(id)`); identidade mudada → pula com aviso (I2).
   Teste: `test_excel_conflito_casa_por_chave_natural_nao_por_id`.
2. **[ALTO] `_parse_data` não lia a célula de DATA real do Excel.** O openpyxl
   devolve `datetime` para célula de data; `str()` virava "2026-07-06 00:00:00" e
   os formatos não casavam → a validade sumia calada e o roundtrip virava conflito
   fantasma. **Corrigido:** `_ler_linhas` normaliza data→dd/mm/aaaa e `_parse_data`
   aceita `datetime`/`date` + formatos com hora. Teste:
   `test_excel_validade_data_real_roundtrip`.
3. **[ALTO] o 2-em-1 cortava/sobrepunha em silêncio** com um preset maior que a
   metade A5 (o `chk_2em1` não estava atrelado ao preset; o `Image.paste` corta
   sem exceção). **Corrigido:** guarda dura em `impor_2em1` (recusa com erro
   nominal, nunca corta calado) + o "Dois por folha" só habilita para A5/etiqueta
   na Fábrica. Testes: `test_impor_2em1_recusa_cartaz_grande`,
   `test_fabrica_2em1_so_habilita_no_a5`.
4. **[MÉDIO] `historico_de_preco` não deduplicava** o mesmo produto na mesma
   edição (ao contrário do ranking) — um item duplicado ("Duplicar item" mantém o
   produto_id) gerava 2 pontos na mesma data. **Corrigido:** dedup por edição.
   Teste: `test_historico_de_preco_deduplica_por_edicao`.
5. **[BAIXO] o preview do conflito** só mostrava preço/categoria; quando a
   divergência era em validade/EAN/peso/flags, os valores exibidos eram idênticos.
   **Corrigido:** `_exibir_campos` monta o antes→depois SÓ dos campos que divergem;
   o diálogo os renderiza.
6. **[BAIXO] o pré-voo** numerava "página N" pelo catálogo inteiro, mas o export
   emitia só o lote filtrado — números não batiam. **Corrigido:** o pré-voo filtra
   pelo lote da categoria.

**Refutados (corretamente) pelos verificadores:** EAN coagido a número pelo Excel
(o openpyxl grava `inlineStr`, preserva o zero à esquerda) e preço R$ 0,00 falsy
(só afeta o par None↔0,00, sem produto real com preço zero).

**Suíte após os consertos: 714 verdes ×5, exit 0 limpo em todas as 5 rodadas,
zero skips.**

**PARADO no passo 100.** Aguardando a reauditoria visual do arquiteto (o cartaz
medido em mm, o 2-em-1 físico, o Excel roundtrip por chave natural). Nada da
Fase 12 começa sem o selo.
