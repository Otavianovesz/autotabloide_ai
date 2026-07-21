# FASE 8 — Exportação e publicação (caderno de 100 passos)

> Formato-lei do PLANO_PERFEITO. Cobre **R-064** (compartilhar direto),
> **R-065** (perfis), **R-066** (fila em lote), **R-067** (marca d'água
> RASCUNHO), **R-068** (aprovação em 2 etapas), R-139, R-140, R-141, R-142
> (Stories/carrossel/Oferta-do-Dia/vídeo-tabloide), R-145 (faixas/banners).
> **Emissão em lote (19/07)** — ver cabeçalho da FASE_4.md. Chat novo por fase.
> **Intensidade: Alto.**
>
> **Por quê da fase:** o tabloide nasce para o WhatsApp — o caminho até lá tem
> que ser de um gesto. E o dono sonha além do PNG: Oferta do Dia, carrossel,
> Stories, vídeo para o Status. **Decisão de arquitetura travada:** os
> formatos sociais são só OUTRO LayoutDef com outra proporção + a MESMA cadeia
> produto→slot; nada de motor novo. O MP4 sai via ffmpeg/imageio (opcional —
> degrada com aviso se ausente, nunca trava). O mínimo garantido do app é
> PNG/PDF + "copiar imagem".

## Bloco A — Exportar bem: perfis, compartilhar, lote (R-065, R-064, R-066) · passos 1–16
**Por quê:** o dono não pensa em pixel nem dpi — escolhe "WhatsApp" ou
"Impressão" e manda. O app cuida do número.

1. R-065 (perfis de exportação): presets prontos — **"WhatsApp (1080)"** · **"Impressão (300 dpi)"** · **"Stories (1080×1920)"** — com resolução/formato definidos.
2. Cada perfil define largura, dpi, formato (PNG/PDF/JPG) e qualidade; o dono escolhe e exporta, sem pensar em número.
3. Perfil de impressão sai em 300 dpi no tamanho físico exato (mm) — o mesmo pipeline medido em bytes das fases anteriores.
4. Perfil WhatsApp otimiza o tamanho do arquivo (compressão sã) para enviar rápido sem borrar.
5. Perfis editáveis/duplicáveis nas Configurações (o dono cria o dele se quiser) — a semente está na aba da F3.
6. R-064 (compartilhar direto): um botão que leva o PNG para a conversa.
7. No Windows, o garantido: "Copiar imagem" (área de transferência) + "Abrir pasta do arquivo" + "Abrir com…" (o WhatsApp Desktop, se instalado).
8. Documentar a limitação do SO com honestidade: o app não controla o WhatsApp; entrega o arquivo do jeito mais curto que o Windows permite (I2 — sem prometer o que não faz).
9. "Copiar imagem" testado: a imagem vai para a área de transferência pronta para colar na conversa.
10. R-066 (fila de exportação em lote): exportar vários projetos/perfis de uma vez, numa fila.
11. A fila mostra progresso por item e não trava a UI (worker; RG-05b cobre o shutdown).
12. Um item com erro na fila não derruba os outros (I2 — marcado e seguindo).
13. Destino da exportação configurável (pasta), com "abrir pasta ao terminar".
14. Foto: os perfis de exportação + o menu compartilhar + a fila em lote (claro/escuro).
15. Teste: cada perfil exporta na resolução certa (pypdf/PIL medindo largura/dpi/tamanho físico).
16. **Checagem:** suíte parcial verde; "copiar imagem" e a fila em lote testados.

## Bloco B — Rascunho e aprovação (R-067, R-068) · passos 17–28
**Por quê:** um encarte com preço errado publicado é o pesadelo. A marca
d'água e a aprovação em 2 etapas são a trava que impede publicar sem conferir.

17. R-067 (marca d'água RASCUNHO): enquanto o projeto não está aprovado, a exportação sai com um "RASCUNHO" discreto sobre a peça.
18. A marca d'água é automática (não depende de o dono lembrar) e só some quando ele aprova.
19. R-068 (aprovação em 2 etapas): o fluxo montou → conferiu → aprovado, com o estado visível (da F2: rascunho→pronto→exportado→publicado).
20. Exportar em rascunho é permitido (para conferência), mas o arquivo carrega a marca — ninguém publica rascunho por engano.
21. Aprovar exige a conferência (o checklist da F7 pode ser o gatilho) — não é um clique cego.
22. Depois de aprovado, a exportação "limpa" (sem marca d'água) é liberada.
23. Reabrir e editar um projeto aprovado volta o estado para rascunho (a marca d'água retorna até reaprovar) — coerência de estado.
24. O estado e a marca d'água respeitam as versões da F2 (aprovar uma versão não aprova as outras).
25. Foto: a mesma peça exportada com marca d'água (rascunho) e sem (aprovada), lado a lado (claro/escuro).
26. Teste: RASCUNHO aparece antes da aprovação e some depois; editar um aprovado volta a rascunho.
27. Teste: exportar limpo só é possível após a aprovação (guarda testada).
28. **Checagem:** suíte parcial verde; o ciclo rascunho → aprovado → editar → rascunho conferido.

## Bloco C — Além do encarte: social estático (R-141, R-140, R-145) · passos 29–46
**Por quê:** o dono quer levar a oferta ao feed e ao story. Tudo reusa o
compositor — é o mesmo produto→slot, outra moldura.

29. Registrar a decisão de arquitetura: os formatos sociais são só OUTRO LayoutDef com outra proporção + a MESMA cadeia produto→slot — não um motor novo.
30. R-141 (Oferta do Dia): um post único de destaque (1080×1080 ou 1080×1350) com 1 produto herói.
31. A Oferta do Dia reusa a célula vitrine (F5-C / R-044) — foto grande, preço gigante, de/por.
32. Gerar a Oferta do Dia a partir de um item selecionado na Mesa (1 clique → post pronto para ajustar).
33. R-140 (carrossel Instagram): 1 card por produto do mesmo projeto (N cards 1080×1080).
34. O carrossel usa a mesma cadeia produto→slot — cada card é uma página de 1 slot herói.
35. Ordem e seleção dos produtos do carrossel controláveis (quais entram, em que ordem).
36. Exportar o carrossel como N arquivos numerados (1 por card), prontos para subir.
37. R-145 (faixas/banners de loja): formatos grandes (banner de topo, faixa de gôndola) no mesmo pipeline.
38. As faixas reusam o compositor com proporções largas; texto e preço grandes, legíveis à distância.
39. Uma biblioteca de proporções sociais (post, story, carrossel, faixa) escolhível — o dono não decora pixels.
40. Todos os formatos sociais herdam a arte/identidade do projeto (não recomeçam do zero visual).
41. O pré-voo vale nos formatos sociais também (item sem foto/preço avisa antes de exportar, I2).
42. **Checagem (marco 2/4):** suíte parcial verde; o carrossel gera N cards e a Oferta do Dia sai no tamanho certo (PIL medindo).
43. Marca d'água RASCUNHO e aprovação (Bloco B) valem para os formatos sociais também.
44. Compartilhar (R-064) vale para os sociais (copiar imagem / abrir pasta).
45. Foto: Oferta do Dia + 3 cards de carrossel + uma faixa (claro/escuro).
46. Teste: o carrossel gera N cards numerados; Oferta do Dia e faixa saem nas proporções certas.

## Bloco D — Além do encarte: vídeo (R-139, R-142) + degradação · passos 47–62
**Por quê:** Stories/Reels e vídeo-tabloide para o Status — mas o MP4 é
opcional; sem o componente de vídeo, o app degrada com aviso e segue firme.

47. **Decisão travada:** o MP4 sai via ffmpeg/imageio; ausente → degrada com aviso, nunca trava. Nada de motor de vídeo pesado.
48. Confirmar a dependência de vídeo na abertura da fase (ffmpeg / imageio-ffmpeg) e registrar o achado no caderno.
49. R-139 (Stories/Reels 1080×1920): a peça vertical com uma animação leve do preço (aparecer/pulsar) exportada como MP4 curto.
50. A animação é simples e configurável (duração, entrada do preço) — leve, não um vídeo produzido.
51. R-142 (vídeo-tabloide): um slideshow MP4 das páginas do projeto (cada página N segundos) para o Status.
52. Transições simples entre páginas (corte/fade), duração por página configurável.
53. O vídeo reusa os PNGs já compostos das páginas (não recompõe do zero) — rápido e fiel.
54. Sem ffmpeg: os formatos de vídeo mostram "requer o componente de vídeo" com instrução, e o resto do app segue (I2).
55. Com ffmpeg: exportar o MP4 num worker com progresso, sem travar a UI.
56. O MP4 tem a contagem certa de frames/duração (medida no arquivo) — não um vídeo quebrado.
57. Marca d'água RASCUNHO vale no vídeo até a aprovação (frame a frame).
58. Quadro: um frame do Story com o preço animado + um frame do vídeo-tabloide (claro/escuro).
59. Teste: com ffmpeg, o MP4 tem N frames/duração certa; sem ffmpeg, degrada com aviso e não trava.
60. Teste: o vídeo-tabloide reusa os PNGs das páginas (o frame bate com o PNG — fidelidade).
61. Documentar no guia: o vídeo é opcional; o mínimo garantido do app é PNG/PDF + copiar imagem.
62. **Checagem (marco 3/4):** suíte inteira ×1 verde exit 0; screenshots/quadros dos formatos sociais e de vídeo em `saida_fase8/`.

## Bloco E — Arquitetura do reuso do compositor · passos 63–74
**Por quê:** garantir que "social = outro LayoutDef" seja verdade no código —
uma cadeia só, não um ramo paralelo que apodrece.

63. Um só compositor: os LayoutDefs sociais (post/story/carrossel/faixa) passam pela MESMA cadeia produto→slot do tabloide.
64. Cada proporção é um LayoutDef declarado (largura×altura, slots) — sem ramo de código próprio por formato.
65. A célula vitrine, os papéis de texto (F5), as máscaras e os selos valem em todos os formatos (reuso, não recriação).
66. Exportar em qualquer perfil/formato usa o mesmo motor de composição medido nas fases anteriores.
67. O pré-voo, o vínculo por uid (I1) e a portabilidade (I3) valem igual nos sociais.
68. Testar que um mesmo item, no tabloide e num card de carrossel, casa por uid (não duplica identidade).
69. Testar que trocar a arte/proporção não perde o vínculo produto→slot.
70. Nenhum formato social introduz caminho absoluto (I3) nem degradação silenciosa (I2).
71. Medir os tamanhos físicos/resoluções de TODOS os perfis num teste (a régua de bytes vale para todos).
72. Compor um projeto e exportá-lo em 4 formatos (tabloide, Oferta do Dia, carrossel, story) e conferir a fidelidade de cada.
73. Foto: o mesmo produto nos 4 formatos lado a lado (a prova do reuso) claro/escuro.
74. **Checagem:** suíte parcial verde; o teste de reuso do compositor (4 formatos, 1 cadeia) passa.

## Bloco F — Integridade e adversarial (I1–I5) · passos 75–86
**Por quê:** a fase reusa o compositor em novos formatos — o adversarial e as
réguas de bytes são o juiz.

75. Re-rodar `test_adversarial_vinculo.py` compondo em formatos sociais (o trio não migra entre cards).
76. Adversarial: no carrossel, cada card fica com o produto certo por uid (não pela ordem).
77. Adversarial: exportar em rascunho e limpo dá a MESMA composição — só a marca d'água muda.
78. Confirmar I1: item casa por uid em todos os formatos; o carrossel não duplica identidade.
79. Confirmar I2: compartilhar (limite do SO), MP4 sem ffmpeg, fila com erro — tudo avisado, nada em silêncio.
80. Confirmar I3: perfis e LayoutDefs sociais sem caminho absoluto; portáveis casa↔mercado.
81. Confirmar I4/I1: vitrine/herói replicável mantém o casamento por uid nos sociais.
82. Rodar a suíte inteira ×2, zero skips (a arte real conta).
83. Medir todos os perfis (largura/dpi/tamanho físico) num teste único.
84. Medir o boot: os formatos novos carregam sob demanda; boot intacto.
85. Varredura de órfãos: nenhum LayoutDef/handler social ficou sem uso.
86. **Checagem:** adversariais verdes; I1–I5 reconferidos; réguas de bytes de todos os perfis conferidas.

## Bloco G — Fechamento · passos 87–100
**Por quê:** fase selada só com o "montei e mandei no WhatsApp num gesto"
demonstrado ponta a ponta.

87. Suíte inteira ×2 exit 0, zero skips.
88. Adversariais do vínculo: nominais verdes (a fase reusa o compositor em novos formatos).
89. Teste novo `test_fase8_export.py`: perfis medidos, RASCUNHO/aprovação, carrossel N cards, MP4 N frames (com degradação sem ffmpeg), reuso do compositor.
90. Demonstração ponta a ponta: montar → aprovar → exportar WhatsApp → copiar imagem → gerar Oferta do Dia e um card de carrossel.
91. `saida_fase8/`: perfis, compartilhar, fila, rascunho × aprovado, Oferta do Dia, carrossel, faixa, frames de story/vídeo — claro e escuro.
92. GIF curto (~15 s): exportar no perfil WhatsApp → copiar imagem → gerar Oferta do Dia.
93. Varredura de jargão (PT-BR: "perfil de exportação", "copiar imagem", "Oferta do Dia", "carrossel").
94. Conferir a limitação honesta do compartilhar-no-WhatsApp documentada (guia + tooltip).
95. Conferir a degradação do MP4 sem ffmpeg (aviso claro, app não trava).
96. Boot e responsividade medidos com a fila de exportação cheia.
97. Resposta do builder NESTE caderno (achados de bancada + "o que ficou de fora").
98. Atualizar `docs/PLANO_DE_CONSTRUCAO.md` e conferir o `CLAUDE.md` (decisão travada: social = outro LayoutDef, uma cadeia só; MP4 opcional degradável).
99. Screenshot-cartaz da publicação (tabloide + Oferta do Dia + carrossel + story) claro + escuro lado a lado.
100. **PARAR** para a reauditoria visual do arquiteto — cada perfil medido, o RASCUNHO que some na aprovação, o reuso do compositor nos 4 formatos. Nada da Fase 9 começa sem o selo.

---

## Registro do builder (2026-07-20) — EXECUTADA até o passo 100

**Baseline:** 600 verdes (F7 selada). **Placar final: 631 verdes, 0 skips, exit 0
LIMPO ×5** (após os consertos da frota adversarial). Subagentes: **4 scouts de
LEITURA** no início (perfis/bytes ·
estado/RASCUNHO · reuso do compositor · degradação MP4) + **4 revisores
ADVERSARIAIS** no fecho (um por eixo, lendo o disco real). Implementação 100%
INLINE. Comecei pelo **teste-espelho pendente da F7**: `ConciliacaoDialog.done()`
cancela as filas + encerra os workers (prova de mutação: esvaziar o `done()` →
o teste falha).

### O que foi feito (modelo antes de UI, tudo testado)
- **Bloco A — perfis + compartilhar + lote:** `app/rendering/perfis.py` (3 perfis
  padrão; `aplicar_perfil` proporcional/encaixe SEM deformar; `exportar_com_perfil`
  PNG/PDF/JPG com dpi gravado; Config `export.perfis` editável). **Régua de bytes**
  (pypdf mediabox + `Image.info['dpi']`). `app/qt/telas/compartilhar.py` (copiar
  imagem / abrir pasta / abrir com — limitação do SO DOCUMENTADA, I2).
  `ExportarDialog` (perfis + **fila em lote** R-066 via `TrabalhadorFila` — um erro
  não derruba os outros; `done()` encerra).
- **Bloco B — RASCUNHO + aprovação:** `app/rendering/marca_dagua.py` (marca
  diagonal LADRILHADA — não recortável — sobre a Image composta, reusa
  `fonte_segura`); aprovação sem migração (`projetos.aprovar/esta_aprovado`, Config,
  espelha `registrar_export`); **editar aprovado volta a rascunho** (hook no ramo do
  hash do `salvar_projeto`, mesma sessão); `servico.aprovar_projeto` EXIGE o
  checklist da F7; `pode_exportar_limpo` (guarda). A marca entra no `_exportar` da
  Mesa ANTES do CMYK.
- **Bloco C/E — social reusa o compositor:** `app/rendering/social.py` — 5 formatos
  (Oferta do Dia 1080², carrossel, story 1080×1920, faixa) como OUTRO LayoutDef +
  a MESMA `compor_pagina`; herói de/por (`_regioes_oferta`, mesmos tijolos do
  cartaz) e vitrine (R-044) para os cards; `PublicarDialog` gera tudo (worker
  encerra no `done()`), marca d'água até aprovar, compartilha ao fim.
- **Bloco D — vídeo opcional:** `app/rendering/video.py` — MP4 via **binário
  ffmpeg** (`shutil.which`, subprocess — `imageio_ffmpeg` está ausente no ambiente,
  o binário existe); espelha o `cmyk.py`: `(resultado, aviso)`, NUNCA levanta; sem
  ffmpeg degrada com aviso honesto; slideshow (R-142) reusa os PNGs das páginas,
  frames/duração EXATOS; story (R-139) com respiro leve; `contar_frames`/
  `duracao_video` por ffprobe.
- **Bloco F — adversarial (I5):** `test_adversarial_f8_carrossel_por_uid` — o card
  casa por UID (não pela ordem), por CONTEÚDO (cor da foto). Provas de mutação nos
  testes-chave (marca d'água, done() dos diálogos, `_split_multi` do F7 revisitado).
- **Bloco G — fecho:** galeria NATIVA em `saida_fase8/{claro,escuro}` (perfis,
  publicar, Oferta do Dia, RASCUNHO×limpa, carrossel, faixa, story); GIF
  `fluxo_publicar.gif`; jargão PT-BR. Teste novo `test_fase8_export.py` (24).

### Achados de bancada
- **Régua de vídeo:** o `concat` do ffmpeg inflava a duração (o último frame ganha
  duração default) — troquei por REPETIÇÃO de frames (`round(seg*fps)` por página):
  contagem/duração ficam EXATAS e testáveis (3 pág × 1s × 24fps = 72 frames, 3.0s).
- **`salvar_perfis` sem commit** (achado próprio pelo teste): o `.set` não
  auto-commita — o perfil não persistia. Corrigido.

### Achados da FROTA ADVERSARIAL (4 revisores no disco real) — TODOS corrigidos
A frota que o dono liberou fez o trabalho dela e achou um **CRÍTICO real** que eu
tinha deixado passar. Honestidade de bancada:
- **[CRÍTICO] A Fábrica de cartazes publicava LIMPO sempre.** `fabrica._exportar`
  compunha e gravava o PDF SEM marca d'água e SEM checar aprovação — a 2ª PORTA de
  exportação, que eu esqueci (a lei "todo TIPO NOVO de porta reavalia" me pegou).
  Um cartaz de preço errado iria limpo ao PDV. **Corrigido:** `marca = not
  pode_exportar_limpo(self._projeto_id)` + `carimbar_rascunho` nas páginas, igual à
  Mesa. Teste novo `test_cartaz_da_fabrica_tambem_leva_a_marca_dagua` — e o 1º
  teste que escrevi era FRACO (byte-diff do PDF, que muda por timestamp; a mutação
  passava): troquei por comparar a IMAGEM EMBUTIDA (pypdf) — agora a mutação FALHA.
- **[MÉDIO] O lote de perfis perdia páginas em silêncio.** `ExportarDialog` usava
  só `paginas[0]` → tabloide multipágina no perfil Impressão virava PDF de 1 página
  (violava I2). **Corrigido:** exporta TODAS as páginas por perfil (_p1.._pN). Teste
  `test_lote_multipagina_nao_perde_paginas`.
- **[MASCARAMENTO — minha lei] O adversarial do carrossel tinha `shuffle` INERTE:**
  os dados eram remontados de um dict por uid em ordem fixa → o teste passaria com
  casamento por índice. **Corrigido:** reescrito para provar a preservação de ordem
  POR CONTEÚDO com uma MUTAÇÃO REAL (inverter a lista inverte os cards).
- **[TESTE FRACO] `..._sem_esticar` só checava o size** (passaria esticando).
  **Corrigido:** verifica as BANDAS de letterbox por conteúdo (topo/base = fundo).
- **[MENOR] Editar na Mesa sem salvar exportava limpo:** `esta_aprovado` agora
  exige salvo E aprovado (`_salvo` dirty flag) — editar em memória derruba a
  aprovação limpa. Teste `test_editar_sem_salvar_derruba_a_aprovacao_limpa`.
- **[MENOR] Reentrância do ExportarDialog** (clique-duplo → 2 filas): guarda
  `_ocupado` + overlay antes da composição. Ressalvas de vídeo (asserts
  ffprobe-gated) anotadas, não bloqueiam.

### O que ficou de fora (declarado)
- **Fila em lote multi-PROJETO:** a fila exporta o projeto ATUAL em vários PERFIS;
  vários projetos de uma vez fica para depois (o núcleo — worker, um-erro-não-para,
  progresso — está pronto e testado).
- **MP4 multipágina no ExportarDialog:** o lote exporta a 1ª página por perfil (o
  caso do WhatsApp/social); o PDF multipágina de impressão sai pela "Exportar"
  rápida. Declarado, não silencioso.
- **Animação do preço no Story (R-139):** entreguei o respiro/zoom leve do quadro
  inteiro; a animação isolada do preço (aparecer/pulsar só o número) fica para
  depois — o MP4 já sai correto.

**Estado: passo 100 alcançado. PARADO no ponto de reauditoria — aguardando o
arquiteto reauditar no disco real + inspecionar a galeria `saida_fase8/`
(perfis medidos, RASCUNHO×aprovada, reuso nos 4 formatos).**
