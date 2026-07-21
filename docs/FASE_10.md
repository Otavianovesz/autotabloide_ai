# FASE 10 — Imagens II + Estúdio IA (caderno de 100 passos)

> Formato-lei do PLANO_PERFEITO. Cobre **R-091 / RG-46** (Estúdio IA), R-094,
> R-095, R-096 (abas Web·Acervo), R-097, R-098, R-099, R-100, R-101, R-102,
> R-103 (refino do recorte), R-104.
> **Emissão em lote (19/07)** — ver cabeçalho da FASE_4.md. Chat novo por fase.
> **Intensidade: Alto.**
>
> **Por quê da fase:** a foto é 60% do encarte (pesquisa §1) e o acervo é
> patrimônio. Aqui entra o sonho do dono: foto de celular → packshot bonito.
> **Decisão travada:** o Estúdio IA tem dois degraus — o **degrau 1 (sem IA
> generativa)** é o padrão GARANTIDO (rembg + luz + sombra sintética, roda em
> qualquer PC); o **degrau 2 (img2img local)** é opção condicionada ao
> hardware do dono, NUNCA requisito. RG-46 não bloqueia a fase se a GPU não
> der: degrada com aviso e o degrau 1 entrega.

## Bloco A — Estúdio IA, o caminho garantido sem IA generativa (RG-46/R-091, degrau 1) · passos 1–16
**Por quê:** o dono fotografa no celular e quer "de vitrine". O degrau 1
resolve ~80% e roda em qualquer máquina — é o mínimo garantido.

1. Registrar a decisão travada: o caminho SEM IA generativa é o padrão GARANTIDO; o generativo é opção condicionada ao hardware, nunca requisito.
2. Estúdio IA degrau 1: pipeline foto física → packshot usando rembg (birefnet-general) + normalização de luz + sombra sintética.
3. Remoção de fundo com o birefnet-general (já decidido) sobre a foto do dono (celular/WhatsApp).
4. Normalização de luz/níveis: corrigir exposição e branco para o produto ficar "de vitrine" sem IA generativa.
5. Sombra sintética projetada sob o produto (suave, coerente com a luz) — dá volume ao packshot.
6. Enquadramento automático: centralizar o produto com a margem padrão de packshot.
7. Tudo isso roda em CPU, em qualquer PC (sem GPU) — é o mínimo garantido (I2).
8. Prévia antes/depois (foto crua → packshot) para o dono aprovar.
9. Parâmetros ajustáveis com padrões bons (intensidade da sombra, margem) — o dono não precisa mexer.
10. O packshot entra no acervo como versão nova da foto do produto (a original preservada) — I1, sem perda.
11. Lote: aplicar o Estúdio degrau 1 numa fila de fotos (a esteira "dados primeiro, fotos depois").
12. Degradação: qualquer etapa que falhe avisa e entrega o melhor possível (I2) — a foto nunca some.
13. Foto: antes/depois de 3 produtos (crua → packshot) claro/escuro.
14. Teste: o Estúdio degrau 1 gera packshot com fundo limpo + sombra — conferido POR PIXEL (fundo transparente, sombra presente).
15. Teste: roda sem GPU (o caminho garantido não depende de hardware).
16. **Checagem:** suíte parcial verde; o packshot sem-IA por pixel passa.

## Bloco B — Estúdio IA generativo, condicional ao hardware (degrau 2) · passos 17–28
**Por quê:** se a GPU do dono permitir, o img2img eleva o packshot — mas é
opção, nunca requisito. E jamais pode inventar outro produto.

17. Confirmar na abertura da fase a VRAM/GPU do dono (pesquisa §6: SDXL ~12GB) e registrar o achado — decide se o degrau 2 é ofertado.
18. Estúdio IA degrau 2: img2img local (SDXL/ComfyUI) com denoise baixo (0,4–0,6) sobre o packshot do degrau 1.
19. Denoise baixo preserva o PRODUTO (não inventa outro) — realça luz/fundo, mantém a identidade da embalagem.
20. Flag experimental "Estúdio IA (gerador)" nas Configurações — desligada por padrão; liga só quem tem hardware.
21. Sem GPU suficiente: o degrau 2 fica desabilitado com explicação honesta ("requer placa de vídeo dedicada") — o degrau 1 continua garantido.
22. Acesso ao gerador pela API padrão compatível (não acoplar a um motor específico — a mesma filosofia da IA de texto).
23. O resultado generativo é sempre uma versão nova para o dono APROVAR (nunca sobrescreve a original) — I1/I2.
24. Guarda anti-alucinação: se o img2img mudar demais o produto (métrica de diferença), avisa e sugere baixar o denoise.
25. O degrau 2 nunca é requisito de nenhum fluxo — o app inteiro funciona só com o degrau 1.
26. Foto: um packshot degrau 1 × degrau 2 lado a lado (onde houver GPU) claro/escuro.
27. Teste: sem GPU, o degrau 2 degrada (desabilitado com aviso) e o degrau 1 entrega; com GPU (se disponível), o img2img preserva o produto.
28. **Checagem:** suíte parcial verde; a decisão de degradar (RG-46 não bloqueia) testada.

## Bloco C — Curadoria melhor (R-094, R-103, R-095, R-096, R-097, R-098) · passos 29–50
**Por quê:** a foto certa, bem recortada e escolhida — o acervo é patrimônio e
nada aqui pode ser destrutivo.

29. R-094 (girar/cortar/espelhar): editar a foto antes de salvar (rotação, corte, espelho) com prévia.
30. As edições preservam a original (versão nova) — I1, nada destrutivo.
31. R-103 (pincel de refino do recorte): restaurar/apagar borda do rembg à mão (o rembg erra bordas finas).
32. O pincel trabalha sobre a máscara alfa (restaura pixel comido / apaga sobra) com zoom — precisão.
33. R-095 (detector de fundo-branco): fotos já com fundo branco pulam o rembg (a chave veio na F3; aqui IMPLEMENTA).
34. O detector mede o fundo (cantos claros uniformes) e decide pular o rembg — economiza tempo e evita estragar foto boa.
35. R-096 (busca em abas): a busca de imagem em abas "Web" · "Meu acervo" (a aba de scanner foi VETADA — não construir).
36. Aba "Meu acervo": procura a foto dentro do que o dono já tem (evita rebuscar o que existe).
37. Aba "Web": a busca online (ddgs, cascata EAN→OFF→ddgs da Onda 4) — sem UI de código de barras (veto).
38. R-097 (foto favorita/oficial): marcar uma versão como a oficial do produto (a que entra no tabloide por padrão).
39. A foto oficial é por produto (I1); trocar a oficial não apaga as outras versões.
40. R-098 (comparador de versões lado a lado): ver todas as versões de foto de um produto e escolher.
41. O comparador mostra resolução/qualidade de cada versão (conversa com o avaliador de foto da F9).
42. **Checagem (marco 2/4):** suíte parcial verde; o detector de fundo-branco pula o rembg (teste) e o refino corrige uma borda (por pixel).
43. Arrastar arquivo para o produto (integra o R-038 da F5) alimenta a curadoria.
44. Todas as fotos ficam em disco por caminho relativo (I3); o banco guarda o caminho + versões (decisão travada).
45. A curadoria respeita o congelamento do projeto: trocar a oficial no acervo não muda um projeto salvo (dados congelados).
46. Girar/cortar/refino/oficial disponíveis tanto no acervo quanto na curadoria da Mesa (uma porta lógica só).
47. Foto: girar/cortar, pincel de refino, abas Web/Acervo, foto oficial, comparador de versões (claro/escuro).
48. Teste: refino do recorte corrige borda por pixel; oficial troca sem apagar versões; comparador lista as versões certas.
49. Teste: busca no "Meu acervo" acha a foto existente antes de ir à Web.
50. **Checagem:** suíte parcial verde; a curadoria não é destrutiva (originais preservadas, provado).

## Bloco D — Acervo saudável (R-100, R-101, R-102, R-104, R-099) · passos 51–70
**Por quê:** 5k+ produtos; o disco e a qualidade das fotos precisam se cuidar
quase sozinhos.

51. R-100 (compressão WebP): guardar as fotos em WebP corta o disco pela metade sem perda visível.
52. A migração para WebP é opcional e reversível (a chave veio na F3; aqui IMPLEMENTA) com prévia do ganho de espaço.
53. WebP preserva transparência (packshots recortados) — testar o alfa após a conversão.
54. R-101 (upscale sob demanda): ampliar a foto pela resolução-ALVO da célula — nem mais (desperdício) nem menos (borrado).
55. O upscale usa Real-ESRGAN (decidido) só quando a célula pede mais resolução do que a foto tem.
56. O upscale é sob demanda (na composição/exportação), não em massa — economiza tempo e disco.
57. R-102 (sombra projetada por tema): a sombra do packshot se ajusta ao tema (claro/escuro) da arte de fundo.
58. R-104 (alerta de foto repetida): avisar quando a mesma foto aparece 2× na edição (dois produtos com a mesma imagem).
59. O alerta usa hash de imagem (conteúdo), não nome de arquivo — pega a repetição real.
60. R-099 (pacote offline de genéricas): fotos genéricas por categoria (uma caixa, uma garrafa) para quando não há a foto real.
61. As genéricas são claramente marcadas como genéricas (o dono sabe que é placeholder) — nunca se confundem com a real.
62. O pacote de genéricas é offline (embarcado ou baixável 1×) — coerente com o app offline.
63. A integridade do acervo (R-129, F3) conversa com tudo isto (órfãs em quarentena, WebP, cache do upscale).
64. Todas as operações de acervo são reversíveis e logadas (sem perda silenciosa, I2).
65. Medir o ganho de disco da WebP num acervo real (antes → depois em MB).
66. Medir que o upscale sob demanda mira a resolução da célula (não amplia além do necessário).
67. Foto: WebP (ganho de espaço), upscale sob demanda, sombra por tema, alerta de foto repetida, genéricas marcadas (claro/escuro).
68. Teste: WebP reduz o tamanho mantendo a aparência e o alfa; upscale mira a resolução-alvo; foto repetida detectada por hash.
69. Teste: genérica nunca é tratada como foto real (marcada, avisa no pré-voo).
70. **Checagem (marco 3/4):** suíte inteira ×1 verde exit 0; screenshots do acervo saudável em `saida_fase10/`.

## Bloco E — Integridade e adversarial (I1–I5) · passos 71–84
**Por quê:** a fase mexe em fotos (versões, formatos, upscale) — o vínculo por
conteúdo é o juiz, e o generativo não pode virar requisito.

71. Re-rodar `test_adversarial_vinculo.py` após Estúdio/curadoria/WebP/upscale (a foto certa fica no produto certo).
72. Adversarial: trocar a foto oficial de um produto não afeta outro (por uid/conteúdo).
73. Adversarial: WebP e upscale preservam a identidade da foto (conteúdo esperado por byte/hash).
74. Confirmar I1: fotos por produto_id/uid; foto repetida detectada por conteúdo, não por posição/nome.
75. Confirmar I2: Estúdio, WebP, upscale, genéricas — tudo avisa (falha, placeholder, degradação), nada em silêncio.
76. Confirmar I3: todas as fotos por caminho relativo; WebP/versões portáveis casa↔mercado.
77. Confirmar que o Estúdio degrau 2 (generativo) NÃO é requisito: desabilitar a GPU e tudo funciona (degrau 1).
78. Confirmar o congelamento: trocar oficial/formato no acervo não altera projeto salvo (dados congelados).
79. Rodar a suíte inteira ×2, zero skips (a arte real conta).
80. Medir o boot: os modelos de imagem (rembg/esrgan) pré-aquecem pós-boot (Onda 1), não no construtor.
81. Medir a memória: o img2img (se ligado) não derruba a máquina; timeout são e degradação (RG-05b).
82. Varredura de órfãos: nenhum cache de upscale/WebP vira lixo sem gestão (integridade R-129).
83. Roundtrip de portabilidade com fotos WebP/versões (casa↔mercado) — byte a byte após remap.
84. **Checagem:** adversariais verdes; I1–I5 reconferidos; roundtrip de fotos passa.

## Bloco F — Fechamento · passos 85–100
**Por quê:** fase selada só com "foto de celular virou packshot" provado e o
disco mais leve, medido.

85. Suíte inteira ×2 exit 0, zero skips.
86. Adversariais do vínculo: nominais verdes (a fase mexeu em fotos/versões).
87. Teste novo `test_fase10_imagens.py`: packshot sem-IA por pixel, degrau 2 degradável, refino por pixel, WebP com alfa, upscale por resolução-alvo, foto repetida por hash.
88. Demonstração ponta a ponta: foto de celular de um produto → Estúdio degrau 1 → packshot → entra no tabloide.
89. Medição real: ganho de disco da WebP num acervo real (antes → depois em MB).
90. `saida_fase10/`: Estúdio antes/depois, degrau 1 × 2, refino, abas de busca, foto oficial, comparador, WebP, upscale, genéricas — claro e escuro.
91. GIF curto (~15 s): foto crua → Estúdio → packshot pronto.
92. Varredura de jargão (PT-BR: "Estúdio", "foto de vitrine" para packshot, "refino do recorte", "foto oficial").
93. Conferir que o caminho sem-IA é o padrão e roda sem GPU (o garantido).
94. Conferir que RG-46 (generativo) não bloqueia a fase (degrada com aviso).
95. Conferir a aba de scanner VETADA ausente (só Web e Acervo).
96. Boot/memória medidos com os modelos de imagem carregados.
97. Resposta do builder NESTE caderno (achados + "o que ficou de fora"; a VRAM do dono e se o degrau 2 foi ofertado — honestidade de bancada).
98. Atualizar `docs/PLANO_DE_CONSTRUCAO.md` e conferir o `CLAUDE.md` (decisão travada: sem-IA é o padrão garantido; generativo condicional ao hardware).
99. Screenshot-cartaz do Estúdio (foto crua → packshot → no tabloide) claro + escuro lado a lado.
100. **PARAR** para a reauditoria visual do arquiteto — o packshot por pixel, o degrau 2 degradável, a WebP com alfa. Nada da Fase 11 começa sem o selo.

---

## Registro do builder (2026-07-20) — EXECUTADA até o passo 100

**Baseline:** 650 verdes (F9 selada). **Placar final: 665 verdes, 0 skips, exit 0
LIMPO ×5.** Subagentes: **4 scouts de LEITURA** + **4 revisores ADVERSARIAIS**
(um por eixo, disco real). Implementação 100% INLINE.

### GPU do dono / degrau 2 (honestidade de bancada)
A bancada **NÃO tem GPU** (torch 2.10 **cpu**, `cuda.is_available()=False`). Então
o **degrau 1 (rembg+luz+sombra) roda de verdade** e o **degrau 2 (img2img SDXL) foi
provado no ENCANAMENTO** (motor fake + guarda anti-alucinação) e degrada com aviso
honesto. A prova com GPU/SDXL real fica para a máquina do dono — declarado, não fingido.

### O que foi feito
- **Bloco A — Estúdio degrau 1 (o flagship):** `app/images/estudio.py` — `packshot_degrau1`
  (rembg injetável + `_normalizar_luz` autocontrast + `_enquadrar_com_sombra` sombra
  sintética; fundo transparente + sombra, prova POR PIXEL; roda em CPU). `tratar_estudio`
  (serviço worker-callable) reusa o mesmo modelo de recorte.
- **Bloco B — degrau 2:** `gerador_disponivel` (GPU), `refinar_com_gerador` (img2img via
  motor injetável; sem GPU → (None, aviso); nunca requisito, nunca levanta),
  `diferenca_demais` (anti-alucinação, passo 24).
- **Bloco C — curadoria não-destrutiva:** `app/images/curadoria.py` — girar/cortar/
  espelhar (R-094), `refinar_alfa` pincel (R-103, cópia, I1), `tem_fundo_branco` (R-095,
  4 cantos) **ligado** ao `processar_imagem` com o gate da Config, `salvar_webp`/
  `webp_disponivel` (R-100, alfa preservado).
- **Bloco D — acervo saudável:** genéricas por categoria marcadas (R-099,
  `app/core/genericas.py`, pré-voo avisa), `fotos_repetidas` por HASH de conteúdo
  (R-104, wired no `Mesa._avisar_foto_repetida`), `lado_alvo_da_celula` (R-101).
- **Bloco E/F:** adversarial `test_adversarial_f10_webp_e_foto_repetida_por_conteudo`
  (WebP preserva a identidade por pixel; repetida por conteúdo). Galeria NATIVA
  `saida_fase10/` (antes→depois do packshot, degrau 1×2, refino, genérica, ganho WebP),
  GIF, jargão PT-BR. Teste novo `test_fase10_imagens.py` (14).

### Achados da FROTA ADVERSARIAL (4 revisores) — todos tratados
- **[BUG real, corrigido]** o **upscale ampliava ALÉM do alvo** para foto não-quadrada:
  mirava o MENOR lado da foto contra o alvo (maior lado da célula) → panorama 900×300
  virava 2976×992 (3× o alvo, o "desperdício" que o R-101 proíbe) e reprocessava
  paisagens já adequadas. Corrigido: `upscale_para_cartaz` mira o MAIOR lado
  (`ampliar_sob_demanda`) e o curto-circuito usa `max(size) >= alvo*0.9`. Teste
  `test_upscale_nao_amplia_alem_do_alvo`.
- **[UX morto, corrigido]** os toggles "Comprimir em WebP" e "Pular recorte fundo-branco"
  ainda diziam "entra em ação na Fase 10" e não faziam nada (promessa silenciosa). O
  **fundo-branco foi LIGADO de verdade** (`_pular_rembg_fundo_branco` no pipeline, com
  gate da Config); o texto dos dois toggles ficou honesto.
- **[TESTE FRACO, blindado]** o teste de girar/espelhar só checava `.size` — agora prova
  a DIREÇÃO (canto marcado) por conteúdo; `cortar` degenerado devolve CÓPIA (sem aliasing).

### O que ficou de fora (declarado)
- **img2img SDXL real do degrau 2:** só o roteamento + a guarda anti-alucinação existem
  (provados com motor fake); ligar a um SDXL/diffusers real fica para quando houver GPU.
- **Migração automática do acervo para WebP:** a função `salvar_webp` está pronta e
  testada; converter a biblioteca inteira (atual.png→.webp atualizando o banco na mesma
  transação) é a próxima passada (evita o risco de órfã que o scout apontou).
- **UI rica da curadoria** (editor de girar/cortar com prévia, pincel de refino
  interativo, abas Web/Acervo, comparador de versões lado a lado): o MODELO está pronto e
  testado; os diálogos visuais ficam para o follow-up.

**Estado: passo 100 alcançado. PARADO no ponto de reauditoria — aguardando o
arquiteto reauditar no disco real + a galeria `saida_fase10/` (o packshot antes→depois,
o degrau 2 degradável, a WebP com alfa, o upscale que agora mira o alvo).**
