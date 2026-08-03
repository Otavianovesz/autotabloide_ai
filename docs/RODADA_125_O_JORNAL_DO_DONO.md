# RODADA-125 — O JORNAL DO DONO, PENTE-FINO (03/08/2026)

> O dono montou o Jornal do Mês no automático, mandou as 2 páginas em foto e pediu:
> *"quero que você ache mais umas 125 coisas para melhorar nesse jornal"*.
> Inventário: 7 frentes de auditoria de código + a leitura visual das páginas dele.
> Numeração CONTÍNUA — cada achado com causa (arquivo:linha) e conserto proposto.

## §0 · A LEITURA VISUAL DAS PÁGINAS (os defeitos que o dono VÊ)

1. Chip de seção ("Higiene…") POR CIMA do título "Creme Dental Kolynos" (p1).
2. Chip "Congelados" solto no meio da página, sobre área de produto (p1).
3. Moldura de seção atravessando o meio da página e cortando colunas (p1, moldura verde).
4. Moldura azul do rodapé deixa o PREÇO da Rosquinha do lado de fora (p1).
5. O preço do herói (R$ 6,90) flutua solto no vão, longe do Gatorade (p1).
6. Célula "Sardinha 125 g" SEM foto enquanto a lata Coqueiro mora na célula do chip vizinho (p1).
7. Carimbo "SUPER OFERTA · R$ 6,90" espremido em 2 linhas dentro da forma pequena (p1, Óleo).
8. "Refrigerante Kitubaina" com foto minúscula para o tamanho da célula (p1).
9. Selo +18 pequeno e deslocado na célula da Amstel (p1) — ancorar melhor quando há foto pequena.
10. Preços em alturas desalinhadas entre células da mesma linha (p1 e p2).
11. "Amaciante / 5 L" — a marca Mon Bijou e as fragrâncias SUMIRAM do descritor (p1).
12. "e Tio Bonini T1 · 5 kg" — o código de coluna T1 IMPRESSO (dado criado antes do aparo do L4; higienizar o produto no banco).
13. "Café 3 Corações 500g a Vacuo Todos" — lixo "Todos" no descritor (p2).
14. "Waffer Bulnez" — Wafer com grafia errada vinda da tabela (p2; vocabulário da ortografia).
15. "Agua Mineral Maraja" — sem acento (p2; ortografia: água, Marajá).
16. "Detg. Limpoll" e "Papel Hig." — abreviações feias; escrever por extenso quando couber (p2).
17. "Toalha de Papel Mili · 2x1" — "2x1" é PROMOÇÃO, não descritor (p2).
18. "Fica a Dica" repetindo a validade em vez de dica editorial (p2 — o K8 da QUINTUSDECIMUS).
19. Ano e Nº do jornal ausentes do cabeçalho (pedido explícito do dono).
20. "Batata 104g Tubo Pringles" — nome truncado estranho; reordenar Tipo+Marca ("Batata Pringles Tubo · 104 g").

## AS SEÇÕES (chips e molduras — o defeito mais gritante das fotos)

AUDITORIA — Seções (chips + molduras) no Jornal do Mês composto no automático. Arquivos-chave: app/rendering/secoes.py, app/rendering/compositor.py (~1123–1142), app/qt/telas/mesa.py (~2879–2948), app/rendering/encartes.py (~1080–1118), app/rendering/fluxo_jornal.py.

21. "Agrupar por categoria" liga seções em página que não foi desenhada para elas — app/qt/telas/mesa.py:2923-2924. O clique do auto-preencher força `pag.secoes_ligadas = chk_agrupar` em TODAS as páginas, sem definir `estilo_secoes`. O Jornal salvo na biblioteca nasce com `secoes_ligadas=False` de propósito (encartes.py:1084-1088, decisão F13-BIS §3.7.2: o contorno é "alienígena sobre o papel creme") e só o caminho do FLUXO (encartes.py:1103-1104) liga com estilo "JORNAL". Resultado: chips azuis + molduras CONTORNO (default global da Config) sobre a arte do Jornal. Conserto: ao ligar seções pela Mesa, respeitar o estilo do encarte — se a página tem `estilo_secoes` definido usar esse; se o layout é um encarte da biblioteca com seções vetadas, agrupar deve significar SÓ ordenação da fila (não ligar o desenho), ou ligar no estilo do encarte, nunca no CONTORNO global.

22. O chip de título é desenhado DENTRO da célula, em cima do nome do produto — app/rendering/secoes.py:328-342. O rótulo (pílula preenchida + texto branco) vai no canto sup-esq do 1º retângulo do run, que é a bbox da 1ª célula +1mm — exatamente onde mora a região NOME. Como a camada de seções entra ANTES do conteúdo (compositor.py:1125-1142), o nome do produto é escrito POR CIMA da pílula colorida: os "chips por cima de títulos" das fotos. O docstring do módulo ("jamais cobre o trio") é falso para o rótulo. Conserto: posicionar o rótulo na FOLGA acima do run (como o estilo JORNAL faz, com clamp à borda e à célula de cima), ou medir colisão com as regiões do slot e recuar; nunca dentro da área de conteúdo.

23. Run de 1 célula: sem caixa, mas o chip fica — solto no meio da página — app/rendering/secoes.py:320-321 + 329. RG-49 suprime a moldura de run com `n_celulas == 1`, mas o bloco do título roda mesmo assim: um chip "Bebidas" pousa sozinho em cima de um produto qualquer. Com o item 4 abaixo fragmentando os runs, a página enche de chips órfãos. Conserto: no run de 1 célula, ou suprimir também o rótulo, ou desenhá-lo na folga (nunca sobre o conteúdo); e decidir por regra explícita se run de 1 merece seção.

24. "Heróis nas maiores células" quebra a contiguidade das categorias e fragmenta os runs — app/qt/telas/mesa.py:2908-2918. A fila é ordenada por categoria (2894-2902), mas os N heróis (os mais baratos, de categorias diversas) são arrancados da fila e postos nas MAIORES células da página 1; o resto zipa nos "demais" em ordem visual. Um herói "Bebidas" no meio da faixa de "Higiene" corta o run em três → múltiplas seções de 1-2 células, cada uma com chip e/ou moldura própria, espalhadas. Conserto: quando agrupar está ligado, calcular as seções pelo MAPA real por slot é inevitável (já é), então a cura é no preenchimento — escolher heróis dentro da própria categoria da região, ou excluir as células de herói do cálculo de seções (tratá-las como capa/"Outros" que não desenha), ou re-ordenar o resíduo para que cada categoria fique contígua ao redor dos buracos.

25. Runs "contíguos" ignoram células fixas/decorativas fisicamente no meio — app/rendering/secoes.py:132-142. `calcular_secoes` itera só `ocupaveis(...)`: célula FIXA (a cesta da Terça) ou slot decorativo entre duas células da mesma categoria NÃO quebra o run, e a união por linha (167-172) atravessa a célula fixa por cima. Conserto: iterar TODOS os slots em ordem visual e quebrar o run em qualquer slot não-ocupável com geometria própria (mesma regra da célula vazia da linha 135-137).

26. União de linha por sobreposição de 50% mistura célula alta (herói) com linha de células baixas — app/rendering/secoes.py:155-166. `_mesma_linha` aceita como "mesma linha" qualquer caixa que sobreponha ≥50% da MENOR; um herói de altura 3× ao lado de células de linha entra no mesmo grupo e a união (`_uniao`, 74-79) estica o retângulo até a base do herói — a moldura desce atravessando as linhas de baixo (de outras categorias) e corta preços. Além disso a comparação é sempre contra `linhas[-1][0]` (a 1ª caixa da linha), não contra a linha toda. Conserto: agrupar por linha usando bandas de y (intervalo dominante da linha), comparar com a união corrente da linha, e nunca deixar a união de uma linha exceder o intervalo vertical comum às caixas do grupo (usar interseção de altura, não união, para a moldura da linha).

27. MARGEM de 1mm invade a célula vizinha em grade sem folga (o fluxo do Jornal é borda-com-borda) — app/rendering/secoes.py:27-28 + 170-172 e fluxo_jornal.py:197-200 (células geradas coladas, x0 + c*larg, sem gutter). O retângulo da seção é a união +1mm por lado; com folga zero entre células, a moldura de 0,8mm é desenhada DENTRO das células vizinhas de outra seção — cortando coluna e o preço encostado na borda. Conserto: clampar a expansão à metade da folga real com o vizinho (medir a distância à célula adjacente, como o RG-31 já ensinou ao reduzir 1.6→1.0), ou desenhar a moldura para DENTRO da união (inset) quando não há folga.

28. bbox da célula ignora rotação das regiões — app/rendering/secoes.py:63-71. `_bbox_slot` usa `r.rect` cru; região com `rotacao_graus` (a validade neon a 90°, carimbos de preço rotacionados do Jornal) ocupa na página um retângulo diferente do rect declarado — a moldura calculada corta o texto rotacionado ("preços de fora"). Conserto: expandir a bbox pela AABB da região rotacionada (mesma matemática que o canvas/compositor já usam para desenhar).

29. Estilo JORNAL desenha o cabeçalho ACIMA de y0 sem faixa reservada nem clamp — app/rendering/secoes.py:304-314. `y_fio = y0 - alt_t - grosso - 1.2mm` assume que o fluxo reservou `altura_cabecalho` acima do bloco (fluxo_jornal.py:174). Quando as seções são recalculadas na Mesa sobre um mapa que NÃO bate com o fluxo original (owner re-preencheu com itens/categorias diferentes; ou herói no meio — item 4), o cabeçalho é escrito por cima da última linha da seção anterior — texto de seção sobre títulos de produto. E na 1ª linha da página y_fio pode sair negativo (sem clamp, some no topo). Conserto: clampar y_fio ≥ topo da faixa e, se não houver folga ≥ (grosso+texto+fino) acima do bloco, desenhar o cabeçalho INLINE dentro de uma banda que o compositor efetivamente reserve; melhor ainda: quando `estilo_secoes=="JORNAL"`, derivar os retângulos dos BLOCOS do fluxo (que já têm `cabecalho` calculado) em vez de recalcular por contiguidade.

30. O fluxo planeja seções por (título, n_itens) mas ninguém garante que o preenchimento respeite esse plano — encartes.py:1091-1111 + mesa.py:2879-2920. As células `jf-NN` nascem posicionadas para uma distribuição exata de seções; o `_auto_preencher_miolo` zipa a fila (ordenada por categoria, mas com contagens possivelmente diferentes) na ordem visual — se as contagens divergem em 1 item, TODAS as fronteiras de seção deslizam uma célula: cabeçalhos/molduras caem no meio da seção errada. Conserto: quando o layout tem células de fluxo, o preenchimento deve mapear categoria→células do bloco daquela seção (o `BlocoSecao.secao` conhece o nome), com sobras nomeadas — não zip cego; ou re-gerar o fluxo a partir da estante atual antes de preencher.

31. Itens sem categoria viram seção "Outros" com moldura e chip — app/rendering/secoes.py:138 + 293-294. O fallback "Outros" só é suprimido no estilo JORNAL; em CONTORNO/PILL/SO_TITULO o hero e as chamadas da capa (sem categoria) ganham caixa azul + chip "Outros" sobre a manchete. Conserto: estender a exceção — slot de capa/chamada (ou run "Outros") não desenha em estilo nenhum, ou ao menos não desenha o rótulo.

32. O toggle por página é atropelado a cada clique de auto-preencher — mesa.py:734-740 vs 2923-2924. O dono desliga "Seções nesta página" (B3), clica auto-preencher de novo, e a linha 2924 re-liga tudo. Conserto: só forçar `secoes_ligadas` quando o ESTADO do check agrupar mudou, ou preservar o override por página (flag "escolha humana" que o repreencher não sobrescreve).

33. Cabeçalho JORNAL usa a largura só da 1ª linha do run — secoes.py:295. `x0, x1 = rects_px[0]` — run em escada (última linha centrada/esticada pelo fluxo, fluxo_jornal.py:188-196) ganha fio mais curto ou mais comprido que o bloco real. Conserto: usar min/max de x sobre todos os rects_px do run.

34. Título editado por categoria é global por página, e o diálogo lista categorias do `_mapa` inteiro filtrado por ids — mesa.py:749-753 — mas depois do item 4 os nomes exibidos podem não corresponder a nenhuma seção desenhada (run fragmentado repete o mesmo título N vezes; `titulos_secoes` renomeia TODOS os fragmentos). Menor, mas confunde: conserto natural cai junto com o 4/10.

35. `config_secoes`/`estilo_secoes` abrem um Database novo a cada composição — secoes.py:179-223, chamados por composição de página no compositor.py:1135-1136. Custo desnecessário (e engole exceção genérica retornando default em silêncio — mascara Config corrompida). Conserto: cachear por processo/raiz e logar o fallback (I2).

36. Clamp dos retângulos à folha usa `esp_px` como margem mínima mas não impede y1<y0/x1<x0 — secoes.py:273-279. Célula colada à borda em página pequena pode gerar rect invertido e o rounded_rectangle do Pillow levanta erro ou desenha lixo. Conserto: descartar rects degenerados (x1<=x0 ou y1<=y0) após o clamp.

RESUMO DA CAUSA-RAIZ das fotos: (1º) a Mesa liga o desenho de seções no estilo global CONTORNO sobre um encarte que veta seções (achado 1); (2º) o rótulo mora dentro da célula, sob/atrás do nome (achado 2); (3º) heróis + células fixas + linha-por-sobreposição fragmentam e esticam os runs (achados 4, 5, 6), gerando chips soltos (achado 3) e molduras que atravessam colunas e cortam preços (achados 6, 7, 8).

## A COMPOSIÇÃO GERAL DA PÁGINA (alinhamento, herói, calibração)

AUDITORIA DA COMPOSIÇÃO DO JORNAL DO MÊS — todos os caminhos são absolutos a partir de C:/Users/otavi/Documents/Projetos_programação/autotabloide_ai/. Coordenadas citadas em px do viewBox 1× (1080×1440).

37. HERÓI: preço carimbado em posição FIXA no vão, sem âncora na foto — app/rendering/encartes.py:761-764. O carimbo do herói nasce cravado em (384, 466, 106×48), no "vão entre o Splash e a legenda". Como a zona da foto (74,308,330×266) usa ASSENTAR (centra horizontal, ancora no rodapé), qualquer foto mais estreita/mais baixa que a zona abre um buraco e o carimbo fica flutuando no meio do nada — e quando o Splash não desenha (sem multi_preco, D2), o carimbo fica sozinho num campo vazio de 106×170. Conserto: ancorar o carimbo ao rect EFETIVO da foto (encostado no canto inferior-direito da tinta real, como o rects_subst do Q1 já permite), ou dar zona_flex ao herói (achado 2) para o vão nem existir.

38. HERÓI: a única foto grande da página NÃO é zona_flex — app/rendering/encartes.py:747 (`_img(74, 308, 330, 266)` sem `flex=True`). As chamadas (linha 785) e as linhas (linha 721) ganharam `flex=True` no J25; o herói — a maior célula da página — ficou de fora, então o foto_fit nunca replaneja e a foto afundada/estreita convive com o vão do achado 1. Conserto: `flex=True` no herói (a arte ali é lisa; o Fio de 3px em 236,308 já passa na régua do filete ≤2mm de foto_fit.py:225-227).

39. HERÓI: nome colide com o rodapé da foto — app/rendering/encartes.py:747 vs 768. A zona da foto termina em y=574 (308+266) e o nome começa em y=570: 4px de sobreposição por construção. Com foto que enche a altura, o título imprime por cima do produto. Conserto: nome para y=578+ ou foto até 566 (respiro de ~4px).

40. LINHAS: foto invade a caixa do nome — app/rendering/encartes.py:721 vs 725. A foto vai de y−20 a y+96 (116 de altura) e o nome começa em y+94: 2px de invasão em TODAS as 15+ células de linha. É a colisão "título × conteúdo" sistêmica das linhas. Conserto: foto com 112 de altura (y−20..y+92) ou nome em y+98.

41. LINHAS: carimbo rotacionado a −6°/+5° come o respiro do descritor — app/rendering/encartes.py:716 e 729. O descritor termina em y+138 e o carimbo (96×42) começa em y+147 — 9px de folga; girado 6°, o canto do carimbo sobe ~96/2·sen6° ≈ 5px, e a moldura tracejada de _desenhar_forma_preco desenha com espessura — o tracejado encosta/colide com o texto acima (o "título colidindo com chip"). O próprio código já aprendeu a lição em outro lugar: a célula de fluxo usa ±3° "para os preços da mesma linha alinharem" (encartes.py:1008-1009, comentário QUATER/J8). Conserto: rot ±3 também em _jornal_linha, e/ou preço em y+150.

42. LINHAS: preços da mesma linha em alturas visualmente diferentes por causa da rotação ASSIMÉTRICA — app/rendering/encartes.py:716 (`-6.0` vs `+5.0`). Magnitudes diferentes giram os carimbos vizinhos de forma desigual — o olho lê desalinhamento vertical mesmo com y idêntico. Conserto: mesmo módulo (±3) alternando só o sinal.

43. FOTO_FIT: o replanejamento é POR CÉLULA e destrói o alinhamento da linha — app/rendering/foto_fit.py:182-205 (_plano_vertical) e 136-179 (_plano_misto). Nos planos vertical/misto o y do preço passa a depender da ALTURA DA FOTO (que depende da proporção de cada foto): numa linha de 5 células, cada uma escolhe um arranjo diferente (ou nenhum, pela guarda GANHO_MINIMO=1.15 de foto_fit.py:39/264) e os carimbos terminam em 5 alturas distintas. Conserto: nas células de LINHA do Jornal, restringir o plano a arranjos que preservam o y do preço (só "abraco"/lateral, ou fixar os rígidos no y do template), ou aplicar coerência de linha: decidir UM arranjo para a linha inteira e alinhar os carimbos pelo y máximo comum.

44. FOTO_FIT: o plano lateral encosta a foto na borda da célula, "doando-a" visualmente à vizinha — app/rendering/foto_fit.py:118-124. O desempate `centro_txt >= centro_foto` (linha 120) manda os textos à direita e a foto para x0 do bbox no EMPATE (textos centrados sob a foto — o caso exato das linhas do Jornal); a foto gruda no fio esquerdo, a 16px da célula vizinha, e o leitor casa a foto com o produto errado (a "Sardinha sem foto com a foto na vizinha"). Conserto: no empate, manter a foto centrada (não migrar de lado); e impor margem mínima da foto às bordas laterais da célula (~6px) em qualquer plano.

45. FOTO_FIT: o plano lateral assenta a foto no RODAPÉ do bbox, abaixo dos textos — app/rendering/foto_fit.py:124 (`Retangulo(fx, y1 - h, w, h)`). O bbox inclui o preço (fundo da célula, y+189), então a foto pode descer até a linha do carimbo do vizinho — outra fonte do "foto parece da célula do lado". Conserto: no arranjo lateral, ancorar a foto no rodapé da ZONA ORIGINAL da foto, não do bbox inteiro.

46. SUPER OFERTA espremido em 2 linhas no carimbo: o texto composto não cabe no palco — app/rendering/compositor.py:675-678 + 640-642. O K2 concatena `"SUPER OFERTA · R$ 18,81"` e manda ao _desenhar_texto dentro do palco do CARIMBO, que é só 80%×66% de uma caixa de 96×42 (≈77×28 px 1×): o texto quebra em 2 linhas minúsculas e amassadas. Conserto: quando multi_preco + valor coexistem, desenhar em DUAS camadas tipográficas ("SUPER OFERTA" pequeno em cima, "R$ 18,81" grande embaixo, como um de/por), ou alargar o palco do carimbo para multi_preco (0.92×0.80) e impor 1 linha com corpo cedendo (sem quebra).

47. SUPER OFERTA no Splash (medalhão) também espreme: palco de altura 52% — app/rendering/compositor.py:630-633. Para MEDALHAO_ESTRELA o palco é lado·0.80 × lado·0.52; "SUPER OFERTA" a 11.5pt (encartes.py:757) não cabe em 1 linha em ~85px e quebra em 2 linhas coladas. Conserto: palco do medalhão com quebra CONTROLADA ("SUPER" / "OFERTA" com entrelinha própria) ou tam menor com 1 palavra por linha declarada; alternativa: tratar o papel OFERTA com um mini-layout próprio (arco/duas linhas centradas) em vez do _desenhar_texto genérico.

48. Corpo do preço varia POR CÉLULA na mesma linha (só-reduz individual) — app/rendering/compositor.py:747-753. O SEPARADO reduz a fonte para caber ("R$ 118,81" reduz, "R$ 6,90" não): na mesma linha, preços de tamanhos diferentes — lê-se como desalinhamento/despadronização. Conserto: compor_pagina calcular a ESCALA MÍNIMA da linha (células com mesmo y de origem) e aplicá-la a todos os carimbos da linha — preços uniformes como jornal de verdade.

49. BURACOS: célula sem produto fica simplesmente vazia, sem compactação — app/rendering/compositor.py:1153-1177. Na grade fixa do Jornal (3×5 na p1 + 4×5+2 na p2), item a menos = buraco no meio da página; só desenha texto fixo/filete. O mecanismo de fluxo que compacta já existe (encartes.py:1091-1111, _FAIXAS_JORNAL + fluxo_jornal) mas só liga com `secoes` — o caminho automático do dono usa a grade fixa. Conserto: no auto-preencher do Jornal, compactar a atribuição (preencher células na ordem de leitura sem deixar vãos) ou promover o fluxo por seções a caminho padrão do Jornal.

50. Mapeamento POSICIONAL legado ainda vivo — app/rendering/compositor.py:998-1005 (_dados_do_slot com `lista[i]`). Se o chamador passa lista, o vínculo é por índice: um item pulado desloca TODAS as fotos/nome/preço uma célula (a "foto da Sardinha na célula vizinha" nasce exatamente assim). Conserto: depreciar o caminho lista no Jornal (aviso I2) e garantir que toda porta monta o dict slot_id→DadosProduto.

51. CHAMADAS: coluna de texto colada na foto, gap zero — app/rendering/encartes.py:785-788. A foto vai até x+112 e o nome começa em x+112 — sem goteira; foto com tinta até a borda encosta na 1ª letra. Conserto: nome em x+118 (respiro de 6px), largura 162.

52. CHAMADAS: foto desce até y+112 e o carimbo começa em y+72 — app/rendering/encartes.py:785 e 792. A foto (x, y−dy, 112, 112+dy) e o carimbo (x+146, y+72) não colidem hoje, mas com zona_flex o plano pode alargar a foto sob o carimbo; não há guarda de não-sobreposição pós-plano. Conserto: após plano_da_celula, validar interseção entre rects substitutos e rígidos e descartar o plano que sobrepõe (hoje só _plano_misto tem clamp, foto_fit.py:169-175).

53. Truncamento SILENCIOSO de linhas de texto — app/rendering/compositor.py:423-426. Quando o bloco não cabe, `aj.linhas = aj.linhas[:n_cabem]` corta linhas sem aviso (viola o espírito do I2): um nome de 3 linhas vira 2 e ninguém sabe. Conserto: registrar aviso de composição (como avisos_fluxo) quando o clamp ampute linhas, para o pré-voo/revisora acusarem.

54. Nome com AlinhamentoV.BASE cria "degraus" entre células vizinhas — app/rendering/encartes.py:125 (BASE como padrão de _nome). Nome de 1 linha senta no FUNDO da caixa de 26px e o de 2 linhas enche desde o topo: na mesma linha do Jornal, os títulos começam em alturas diferentes (contribui para a leitura "desalinhada"). Para as linhas do Jornal (nome acima do descritor) o TOPO alinharia melhor: 1ª linha de todos os títulos na mesma altura. Conserto: alinhamento_v=TOPO nos nomes de _jornal_linha (encartes.py:725).

55. Baseline do preço SEPARADO ignora a rotação par a par — app/rendering/compositor.py:758 + 864-893. A baseline centra no rect e o RG-12 gira em torno do centro: com módulos de rotação diferentes (−6 vs +5) o desvio vertical aparente difere entre vizinhos (soma-se ao achado 6). Conserto: coberto ao igualar os módulos (achado 6); registrado para o teste de régua visual.

56. Guarda de célula "vestida" barra o plano do herói por causa do Fio de 3px A MENOS que ele meça ≤2mm — app/rendering/foto_fit.py:225-231. O Fio do herói (236,308,226×3 → 3px ≈ 0,79mm a 96dpi) passa; mas qualquer adorno futuro de 8px (2,1mm) mataria o plano da célula inteira em silêncio. Conserto: ao barrar plano por adorno, emitir aviso nomeando a célula e o adorno (hoje devolve None mudo) — diagnóstico do "por que esta célula não se adaptou".

57. FRACAO_CHEIA/GANHO_MINIMO tratam células IGUAIS de forma diferente — app/rendering/foto_fit.py:36-39 + 262-266. Foto A com 84% de ocupação replaneja, foto B com 86% não: duas células da mesma linha com geometrias diferentes (uma foto grande realocada, outra pequena no template) — heterogeneidade que o olho lê como bagunça. Conserto: além da coerência de linha (achado 7), suavizar o degrau: se ≥1 célula da linha replaneja, medir as irmãs com limiar relaxado (histerese) para a linha inteira mudar junta.

58. `_desenhar_adorno` redimensiona o fundo à página com resize simples (sem LANCZOS) — app/rendering/compositor.py:809-810. O fundo recolado sobre a foto (Fio das linhas) sai com reamostragem de qualidade inferior à da camada (que usa LANCZOS na linha 1117). Conserto: `resize(base.size, Image.LANCZOS)` para o recorte recolado casar com o fundo.

59. Preços grandes sem separador de milhar — app/rendering/compositor.py:218-222 (_reais_centavos). "R$ 1234,00" sai sem ponto ("1.234"); raro no Jornal, mas o carimbo do herói pode receber eletro/cestas. Conserto: formatar reais com separador pt-BR quando ≥1000.

PRIORIDADE sugerida: 1-2-3-4 (herói e linhas: as colisões e o vão), 7-8-9 (foto_fit × alinhamento de linha — a causa da Sardinha e dos preços dançando), 10-11 (SUPER OFERTA), 5-6-12-18 (a régua fina que faz a página parecer profissional), 13-14 (buracos e mapeamento), resto polimento.

## O ARRANJO MULTI-FOTO (a vitrine)

AUDITORIA DO ARRANJO MULTI-FOTO (app/rendering/arranjo.py + compositor.py). Medições de base: a zona chega inteira ao arranjo (compositor.py:322,367 passa rw×rh da região), então o problema é 100% dentro do arranjo. Escalas atuais medidas: LADO_A_LADO com n=2 garante teto de 50% da largura da zona por foto (fatia w/n) — e como packshots do rembg carregam margem transparente típica de 15–25%, a tinta visível cai para ~35–40% da largura ("duas coisas pequeneninhas", literal); n=3 → teto de 33%. LEQUE limita TODA foto a 72%×92% da zona, todas do MESMO tamanho. E o padrão do item composto (2 produtos) é justamente LADO_A_LADO (app/tests/test_item_composto.py:55), o pior modo.

60. LADO_A_LADO fatia a zona e é o padrão do composto — a causa-mãe da queixa. Causa: app/rendering/arranjo.py:42-46 (cel = w/n, _colar_centro em cada fatia, zero sobreposição) + o composto nascer LADO_A_LADO. Conserto: redesenhar como CAMADAS: foto da frente ~78-80% da zona (pós-crop de alfa, achado 3), assentada no rodapé e deslocada ~12% para um lado; as de trás ~62-68%, deslocadas ~30-35% da largura da frente para o lado oposto e alguns % para cima; paste trás→frente. Manter o nome LADO_A_LADO por compatibilidade de projetos salvos, mudando só a geometria (ou criar modo CAMADAS e migrar o padrão do composto).

61. LEQUE sem hierarquia: todas as fotos no mesmo tamanho (teto 0,72w×0,92h) e centradas. Causa: arranjo.py:61-70 (fits uniformes; cy centrado). Conserto: escala decrescente por profundidade (frente ~80%, cada camada atrás ×0,85), a da frente por último no paste, base alinhada (não centro) — "sobressaindo suavemente uma à outra" como o dono pediu.

62. Sem crop pela bbox do alfa antes de medir — packshots com moldura transparente encolhem em dobro. Causa: arranjo.py:31-34 (_contain mede img.width/height crus); o caminho de 1 foto ASSENTAR já cropa (compositor.py:334-337) e o multi não. Conserto: em compor_imagens, cropar cada RGBA por getchannel("A").getbbox() antes de qualquer _contain — ganho imediato de 15-25% de tamanho sem tocar em mais nada.

63. reg.ajuste (ASSENTAR) ignorado no caminho multi — as fotos flutuam centradas verticalmente enquanto as células vizinhas de 1 foto assentam no rodapé. Causa: compositor.py:365-367 não repassa reg.ajuste; arranjo.py:39,70 centra em y. Conserto: compor_imagens ganha parâmetro assentar (ou recebe o Ajuste) e alinha a base das fotos ao rodapé da zona, como o caminho de 1 foto.

64. Enquadramento por foto (zoom/foco/EspecImagem) descartado em silêncio no multi. Causa: compositor.py:367 `[im for _, im in pares]` joga fora a spec que _carregar_imagens devolveu de propósito (R-037). Conserto: passar os pares e aplicar zoom/foco por foto dentro do arranjo (ou, no mínimo, avisar no pré-voo — hoje viola o espírito do I2: o dono ajusta o enquadramento e nada muda).

65. Rotação do leque estoura a camada e o paste CLIPA a foto em silêncio. Causa: arranjo.py:68-71 (rotate expand=True alarga a peça; cx/cy podem ficar negativos; o comentário admite "paste clipa"). Conserto: após rotacionar, re-conter a peça em w×h (ou clampar cx/cy) para nunca cortar produto; corte silencioso de tinta é bug de conteúdo.

66. Sem sombra/separação entre camadas sobrepostas — fotos de fundo parecido viram uma mancha só, sem leitura de profundidade. Causa: arranjo.py:71 paste direto. Conserto: drop-shadow suave derivada do alfa (offset 2-3 px, blur, ~35% opacidade) atrás de cada camada da frente — o "sobressaindo suavemente" do pedido.

67. Rotação do leque aplicada também a 2 PRODUTOS diferentes — inclinar o arroz Camil e o Rei um contra o outro fica amador. Causa: arranjo.py:67 rotaciona sempre que n>1. Conserto: rotação só quando as imagens são a mesma foto repetida/sabores (ou parâmetro); para composto de 2 produtos, camadas retas.

68. Passo do leque degenera com fotos largas: (w-larg)/(n-1) fica minúsculo e a foto de trás some ~100% coberta. Causa: arranjo.py:63. Conserto: garantir passo mínimo (ex.: ≥30% da largura da peça da frente) reduzindo a escala das camadas de trás se preciso — cada foto sempre mostra uma fatia reconhecível.

69. GRADE com n=3 deixa célula vazia e a última linha desalinhada. Causa: arranjo.py:49-56 (cols=ceil(sqrt(n)), posição fixa col*cw). Conserto: centralizar a última linha incompleta ((cols - itens_da_linha)*cw/2 de offset).

70. _contain faz upscale ilimitado e sem resample explícito. Causa: arranjo.py:34 (escala pode ser >1; resize sem filtro nomeado). Conserto: LANCZOS explícito no downscale e teto de upscale (ex.: 1,5×) com aviso I2 — foto pequena hoje sai borrada e ninguém fica sabendo.

71. Sem teto de N fotos: 6+ fotos → todas minúsculas em qualquer modo. Causa: compor_imagens aceita lista arbitrária (arranjo.py:74-90). Conserto: desenhar no máximo ~4 camadas e sinalizar o excedente (pré-voo/revisora), em vez de encolher tudo.

72. Modo não se adapta à proporção da zona. Causa: compositor.py:64 padrão fixo LEQUE; arranjo.py não olha w/h. Conserto: nas camadas novas, deslocamento horizontal em zona larga e diagonal (lado+cima) em zona alta/quadrada — um if pela razão w/h dentro do próprio arranjo (o DIY do combo continua mandando no modo).

73. Testes não protegem o TAMANHO — o defeito passa verde. Causa: app/tests/test_arranjo.py só confere dimensão da camada e não-vazamento (linhas 12-36); nenhum assert de escala mínima. Conserto: teste por conteúdo (I5): com 2 packshots, a bbox de tinta da foto da frente ocupa ≥70% da altura da zona e as duas fotos têm tamanhos DIFERENTES (frente > trás); é o teste que teria pego a queixa.

DESENHO NOVO PROPOSTO (consolidando 1,2,3,4,7): compor_imagens vira "camadas inteligentes": (a) cropar todo RGBA pela bbox do alfa; (b) frente = 1ª foto da lista (a ordem do FotosItemDialog já é a ordem do desenho, fotos_item_dialog.py:48) contida em ~0,78w×0,88h; (c) cada camada atrás com escala ×0,85 da anterior, deslocada ~1/3 da largura da frente para o lado alternado e ~4% para cima; (d) todas com base alinhada ao rodapé (ASSENTAR) e sombra suave; (e) paste trás→frente; (f) rotação leve só para sabores/foto repetida. Nada disso muda a assinatura pública além de um parâmetro opcional, e a camada continua exatamente rw×rh (nada vaza).

## OS DESCRITORES E NOMES SUJOS

AUDITORIA — descritores/nomes sujos no Jornal do Mês (caminhos lidos: app/core/sanitize.py, app/core/ortografia.py, app/qt/telas/servico.py, app/qt/telas/colagem.py). Lista numerada de achados, cada um com causa (arquivo:linha) e conserto:

74. GRAMATURA DUPLICADA nome+descritor ("Kitubaina · 1,5 L · 1,6L") — servico.py:1978+1986 (compor_itens) e servico.py:768-771 (dados_para_desenho). O composto ganha o peso DUAS vezes: `nome_composto` já anexa "· 1,5 L" ao nome (peso da tabela, via separar_peso, grafia ESPAÇADA) e `compor_itens` ainda seta `unidade=a.unidade` (peso do BANCO, grafia COLADA "1,6L"), que o descritor imprime de novo. Conserto: em compor_itens, derivar `unidade` do próprio `separar_peso(nome_composto(...))` e NÃO anexar "· peso" ao nome (o peso vive só no campo unidade → região UNIDADE/descritor); ou, no mínimo, dados_para_desenho suprimir `it.unidade` quando `_regex_unidades` casa o FIM do nome.

75. FONTES DIVERGENTES 1,5 vs 1,6 sem reconciliação — servico.py:1986. `a.unidade` vem do cadastro do banco e vence calado o peso da oferta (o espírito do J18 é "o documento manda"; o J10 já rebaixa palpite com peso divergente, mas aqui o divergente IMPRIME). Conserto: no descritor, o peso da OFERTA (tabela) vence o do banco; divergência vira aviso (I2), nunca dois números na página.

76. GRAFIAS MISTAS "400 g" vs "500g" — três formatadores de peso convivem: separar_peso devolve espaçado "395 g" (sanitize.py:352), sanitizar cola "395g" (sanitize.py:191), e a unidade do banco cola `f"{_qtd_texto(v)}{u}"` (servico.py:2486). Conserto: criar UMA função pública `formatar_peso(valor, unidade)` (decidir a grafia oficial do encarte — sugiro espaçada "500 g", exceto L: "1,5 L") e fazer separar_peso, item_do_catalogo, conciliar_linhas e nome_composto passarem por ela.

77. item_do_catalogo imprime Decimal cru — servico.py:683: `f'{d["peso_valor"]}{d["peso_unidade"]}'` sai "1.500L" (ponto decimal e zeros à direita) em vez de "1,5L". Conserto: reusar `_qtd_texto` (servico.py:179) como a linha 2486 já faz.

78. OFERTA COM DUAS GRAMATURAS ("400 g · 500g" que deveria ser "400 g ou 500 g") — hoje não existe formato: quando os pesos diferem, compor_itens:1986 devolve `unidade=None` e cada peso fica preso dentro do nome de um componente; quando um vem do nome e outro do banco, saem os dois com "·". Conserto: quando a MESMA oferta cobre dois pesos (composto com pa≠pb, ou tabela≠banco confirmado pelo humano), o descritor deve ser `juntar_com_ou([pa, pb])` → "400 g ou 500 g" (a função já existe, servico.py:1934) — os pesos saem dos nomes e entram UMA vez no descritor.

79. CÓDIGO DE COLUNA "T1" IMPRESSO ("e Tio Bonini T1 · 5 kg") — causa 1: a limpa por frequência `_remover_codigos_de_coluna` roda SÓ na colagem (colagem.py:218); o caminho OCR (importar_ofertas, servico.py:2315-2336) nunca a chama — a foto real do dono entra por aqui. Conserto: aplicar a mesma limpa por frequência sobre `tabela.linhas` antes de conciliar_linhas.

80. `_RE_CODIGO_COLUNA` estreito demais — colagem.py:227 exige HÍFEN (`^[A-Za-z]{1,3}-\d{1,3}$`) e só olha o 1º/último token (236-246): "T1" sem hífen (leitura comum do OCR) e "T-1" no MEIO da linha ("ARROZ SOMAR T-1 e TIO BONINI T-1 5 Kgs" — o código fica antes do " e " e antes do peso, nunca na borda) escapam; no composto, o T1 comum aos dois lados vira SUFIXO preservado por `_juntar_com_e` (servico.py:1816-1818) e imprime. Conserto: hífen opcional (`-?`), manter a guarda VITAMINA/COMPLEXO, e na passada por frequência remover o token-código em QUALQUER posição (ou ao menos também o token imediatamente antes do peso final).

81. Mesma doença no `preco_inline_da_descricao` — servico.py:2252: `\b[A-Z]{1,2}-\d+$` exige hífen E fim de string; "T1" ou código no meio sobrevive nesse caminho (S. OFERTA) também. Conserto: `-?` no regex e alinhar com a regra do item 7.

82. "500g a Vacuo Todos" (lixo pós-peso) — sanitize.py:320-352: separar_peso só corta peso no FIM ou INÍCIO ("lei da camada"); com peso no MEIO ("LINGUIÇA … 500G A VACUO TODOS…") o rabo inteiro fica no nome. E "TODOS/TODAS (os sabores)" não está em `indicadores_variantes` (sanitize.py:68-71) — a linha nem levanta pendência. Conserto: adicionar "todos"/"todas" aos indicadores_variantes; em familia_da_linha (servico.py:3055) tratar "TODOS OS SABORES" como marcador de variantes (o rabo não vira sabor nem fica no nome); e permitir que peso+rabo CURTO de embalagem conhecida ("a vácuo") desça junto ao descritor.

83. "Vacuo" sem acento — ortografia.py:25-48: "vacuo"→"vácuo" não está no ACENTOS_MERCADO e é inequívoco no domínio. Conserto: adicionar ao seed.

84. "Agua Mineral" sem acento — ortografia.py:25: falta "agua"→"água", provavelmente a palavra mais frequente de encarte; também candidatas inequívocas: "alcool"→"álcool", "higienico"→"higiênico", "lingua"→"língua" (avaliar uma a uma pela regra conservadora). Conserto: adicionar ao seed.

85. "Waffer" — typo de OCR/tabela sem entrada; o mecanismo já existe ("picoca"→"pipoca", ortografia.py:47). Conserto: adicionar "waffer"→"wafer" ao ACENTOS_MERCADO (a chave aceita typo, não só acento).

86. "Detg. Limpoll" / "Papel Hig." (abreviações da tabela impressas) — duas causas: (a) `glossario_siglas` nasce VAZIO (sanitize.py:86) e não há seed de expansão de abreviações de tabela; (b) mesmo com seed, `_expandir_glossario` (sanitize.py:219-225) compara o TOKEN INTEIRO em upper — "Detg." com ponto nunca casaria a chave "DETG". Conserto: seed conservador (DETG→detergente, HIG→higiênico, DESOD→desodorante…) editável pela Config, e strip de bordas de pontuação antes do lookup (reusar o padrão `_RE_BORDAS` da ortografia), reanexando o que não for o ponto da abreviação.

87. "2x1" como descritor — dois suspeitos: (a) o multiplicador do separar_peso (sanitize.py:344, `(\d+\s*[xX×]\s*)$`) mastiga a MECÂNICA de promoção "2 X 1L" como gramatura "2x1 L" — multiplicador legítimo é "4x120g", nunca "2x1"; (b) `classificar_preco_ocr` (servico.py:2257) não reconhece "2X1"/"leve 2 pague 1" curto como multi_preco, então o texto sobra no nome/descritor. Conserto: em classificar_preco_ocr, padrão `^\d\s*[xX]\s*\d$` sem unidade = mecânica → multi_preco (R-070, desenha na bolha de preço); em separar_peso, recusar o prefixo multiplicador quando o resultado for Nx1 sem decimal (heurística: multiplicador exige peso com unidade E valor típico de fração).

88. DESCRITOR SEM DEDUP GERAL — servico.py:768-771: o join sabores + "marca própria" + unidade não confere se o NOME já termina com a mesma informação (o nome sanitizado PRESERVA o peso dentro dele por lei da camada, então todo item casado com `unidade` do banco imprime o peso 2x, ainda que igual: "… 1,6L · 1,6L"). Conserto: guarda canônica no dados_para_desenho — normalizar ("1,5 L" ≡ "1,5L", caixa/espaco) e omitir do descritor o que já fecha o nome; ou, melhor, aplicar `separar_peso(nome)` no momento do desenho e deixar o peso viver SÓ no descritor/região UNIDADE.

89. CONTRATO DE GRAFIA NÃO DECLARADO — o docstring do sanitize (sanitize.py:7-8) promete "5 Kgs → 5kg" COLADO, mas separar_peso formata ESPAÇADO "395 g" de propósito (sanitize.py:326-331) — a mistura na página é consequência direta de não existir a grafia oficial única. Conserto: decidir e documentar UMA grafia do encarte (item 3) e cobrir com teste de pixel que a página nunca imprime as duas grafias do mesmo peso.

## CABEÇALHO/RODAPÉ — ano, número, Fica a Dica

AUDITORIA — CABEÇALHO/RODAPÉ DO JORNAL DO MÊS (ano/nº ausentes + Fica a Dica repetindo a validade). Cadeia lida: app/rendering/encartes.py (jp1/jp2), app/rendering/compositor.py (texto_composto_legal + _campo_vivo_da_pagina), app/qt/telas/mesa.py, app/qt/telas/servico.py, e o publicado em "Templates novos/geradores/gen_jornal_final.py".

90. K8 — CAUSA-RAIZ: o papel DICA cai no fallback da VALIDADE. Em app/rendering/compositor.py:194-201, texto_composto_legal não tem ramo para PapelTexto.DICA: sem texto_fixo (o padrão — papel_texto_ui.py:116 diz "DICA → None, a IA preenche depois"), a função chega ao `return validade` final (linha 201). A região jp2-dica (encartes.py:857) e o painel Fica a Dica do Quintou (encartes.py:903) imprimem a validade da página como se fosse a dica. Conserto: ramo explícito `if papel == PapelTexto.DICA: return fixo` (e avaliar o mesmo para LEGAL) — o fallback legado de validade fica só para LIVRE, byte-idêntico nos layouts antigos.

91. ANO/Nº — a sugestão de edição só roda ao SALVAR o projeto. mesa.py:1002-1008: `sugerir_edicao` vive dentro de `_salvar_projeto`. Quem escolhe o layout do Jornal, auto-preenche e exporta direto (o fluxo "no automático" do dono) nunca recebe a sugestão e a região EDICAO (encartes.py:813) fica muda. Conserto: rodar a sugestão também ao abrir/escolher o layout do Jornal (onde a cascata da validade já roda, mesa.py:463/792) e no início de `_exportar` (mesa.py:3023), antes do pré-voo.

92. ANO/Nº — sem base registrada, a sugestão é SEMPRE None na primeira edição. servico.py:1503-1536 (`sugerir_edicao`) exige `eventos.edicao_base`, que só nasce em `registrar_edicao_publicada` (servico.py:1559-1567) — ou seja, só depois de o dono JÁ ter digitado uma edição à mão E exportado uma vez. Círculo vicioso: primeira vez = mudo. Conserto: semear a base do publicado ("Nº 177 · ANO 42", 2026-07 — o valor está na arte, gen_jornal_final.py:144) na primeira composição do Jornal, ou perguntar Nº/Ano num diálogo quando o layout tem papel EDICAO e não há base.

93. ANO/Nº — o campo "Edição" da barra é INVISÍVEL quando vazio (P-02, o mesmo pecado que o chip da validade já pagou). mesa.py:192-199 cria `QLabel("")` clicável; mesa.py:520-521 só escreve texto quando `_edicao` existe. Um rótulo vazio com tooltip é um segredo — o dono não tem como descobrir onde digitar o Nº/Ano. Conserto: chip permanente no padrão do `_atualizar_chip_validade` (mesa.py:475-504): sem dado mostra "Nº/Ano — clique ✎" em cor de alerta; some só quando o layout não tem papel EDICAO.

94. ANO/Nº — o aviso do pré-voo não diz ONDE agir. servico.py:2188-2189: "papel “Edição” sem número — defina a edição do jornal (Nº/Ano)" — sem apontar o clique, exatamente a frase que a lição D13-DECIMUS/D3 corrigiu na validade ("clique no 📅 na barra da Mesa"). Conserto: a mensagem aponta o chip da Edição na barra da Mesa.

95. ANO/Nº — `sugerir_edicao(evento)` não cai no nome do layout. mesa.py:1003 passa só `evento`; a validade usa `_evento or _layout_nome` (mesa.py:463, 792, 3031). Projeto sem evento definido nunca acha a base "jornal do mês". Conserto: mesmo fallback `getattr(self, "_evento", None) or self._layout_nome` na chamada.

96. ANO/Nº — o registro da edição publicada também depende de `_evento`. mesa.py:3113-3114 + servico.py:1548: sem evento (projeto exportado sem salvar), `registrar_edicao_publicada` retorna cedo e a base nunca nasce — perpetua o achado 3. Conserto: o mesmo fallback para `_layout_nome` aqui.

97. ANO/Nº — o dado "__pagina__" não carrega a edição. servico.py:803-814 (`dados_de_pagina`) monta só `texto_legal`; mesa.py:2865-2866 o injeta. Com o mapa ainda vazio (antes do auto-preencher), a região EDICAO fica muda no preview mesmo com `_edicao` definido — a validade ganhou esse canal no J24, a edição não. Conserto: `dados_de_pagina(validade, edicao)` e passar `self._edicao` na chamada.

98. K8 — a dica nunca é GERADA no fluxo automático. A geração por IA existe só no botão do painel de propriedades do EDITOR de layout (painel_propriedades.py:690-696, ESTILOS_DICA em app/ai/enriquecimento.py:419); a Mesa/auto-preencher não tem porta. Conserto: no auto-preencher de layout com papel DICA sem texto, gerar a dica pela IA quando disponível (gravando em texto_fixo, editável); sem IA, ficar mudo COM aviso (nunca a validade — achado 1).

99. K8 — o aviso do pré-voo da DICA aponta ação inexistente na Mesa. servico.py:2175: "gere a dica pela IA" — o botão mora no editor de layout, não na Mesa onde o dono está. Conserto: mensagem com o caminho real (ou oferecer a geração na hora, casando com o achado 9).

100. Provas visuais mascaravam os dois defeitos. app/scripts/inspecao_encartes.py:213-214 injeta `"edicao": "Nº 178 · ANO 42"` e :501/:555/:662 injetam a dica à mão — as galerias/provas sempre saíram corretas enquanto o caminho real da Mesa nunca preenche nenhum dos dois. Conserto: teste de pixel que compõe o Jornal pelo caminho OFICIAL (dados_para_desenho/_dados_por_slot, sem injeção) e afirma (a) região EDICAO muda gera o aviso e, com edição definida, tinta no cartucho (870,56); (b) a caixa da dica NÃO contém a data da validade.

101. Menor — corpo da Edição diverge do publicado. encartes.py:813-814: tam 9.0 numa caixa 160×24 em (870,56); o publicado escreve fs=12 bold centrado no cartucho (gen_jornal_final.py:144: T(950,74, fw='700', fs=12)). Mesmo quando o dado chegar, sairá menor e deslocado em relação ao "Nº 177 · ANO 42" original. Conserto: tam ≈12, negrito/centrado no cartucho (x 860-1040).

102. Menor — `texto_com_periodo_vivo` reescreve QUALQUER papel com texto fixo. compositor.py:194-200: o ramo final aplica a substituição de período também a DICA/LEGAL com fixo — uma dica editorial que mencione "do dia 1º ao 27" seria reescrita pela validade. Ao criar o ramo DICA do achado 1, decidir explicitamente (e testar) se a dica passa ou não pelo período vivo.

Nota de contexto: "EXPEDIENTE" (gen_jornal_final.py:264-270) e o rodapé "PÁGINA 1 · JORNAL BELO BRASIL …" (:211) são ESTRUTURA — vivem na arte BASE e não dependem do app; não são causa dos sumiços. Os únicos conteúdos-exemplo zerados no cabeçalho que o app precisa repor são: período da orelha, validade, manchete/linha-fina (OK hoje) e o "Nº · ANO" (quebrado pela cadeia dos achados 2-8).

## A COMBINATÓRIA (marcas × sabores × reimportação)

AUDITORIA — combinatória sabores × marcas e reimportação (Jornal do Mês). Lido: app/qt/telas/servico.py, app/qt/telas/conciliacao_dialog.py, app/ai/conciliacao.py, app/core/repositories.py. Lista numerada de achados:

103. A LINHA DE FAMÍLIA NUNCA APRENDE ALIAS — reimportar obriga a re-curadoria inteira (o furo-mãe da pergunta b). servico.py:3084-3122 (criar_familia_de_sabores): a função cria os membros e liga a família, mas NUNCA chama aprender_alias(ids[0], item.descricao) com a linha CRUA do OCR ("SARDINHA COQUEIRO 125 G TOMATE/OLEO E LIMAO"). Os aliases que nascem (via finalizar_criacao→importar, repositories.py:170/184) são só os nomes COMPOSTOS de cada sabor ("Sardinha Coqueiro 125g Tomate"). Na importação seguinte a linha multi não casa exato (conciliacao.py:561), o fuzzy dificilmente pontua contra membros individuais, e a linha volta VERMELHA. Conserto: ao fim de criar_familia_de_sabores, aprender_alias(ids[0], item.descricao) — o exato da próxima importação devolve o membro-âncora e o conciliar já pendura a família no item (servico.py:2494-2497, _familia_em_lote); aí re-derivar os sabores DA LINHA via familia_da_linha e pré-marcar só os membros correspondentes no leque.

104. O COMPOSTO (2 marcas) TAMBÉM NÃO DEIXA MEMÓRIA DA LINHA. servico.py:1991-2020 (criar_como_composto): o comp resultante tem produto_id=None (1979) e a linha original só fica no rastro do item da sessão. Nenhum alias é aprendido para a descrição crua ("ARROZ SOMAR E TIO BONINI 5 KGS"), e alias aponta para UM produto só (repositories.py:137-148) — não existe como registrar "esta linha = composto de idA+idB". Reimportar = pendência multiplos de novo + curadoria de novo (os produtos não duplicam graças ao importar por nome_bruto, mas o trabalho humano se repete todo mês). Conserto: memória de linha composta — ou uma tabela leve (linha_crua → [produto_ids], tipo composto/família), ou alias com coluna papel; na conciliação, match dessa memória re-monta o compor_itens sozinho, VERDE via "composto-aprendido".

105. OBTER-OU-CRIAR POR SABOR SÓ FUNCIONA POR GRAFIA CRUA EXATA — sabor pré-existente vira duplicata (pergunta c). servico.py:3102-3108 → finalizar_criacao (3431) → repositories.py:164-166: o reaproveitamento é buscar_por_nome_bruto(nome_bruto) OU buscar_por_alias, e o nome_bruto do sub é o nome COMPOSTO "{nome_familia} {sabor}". Se o membro existente nasceu por outra porta (importação de linha simples, criação manual, grafia "Sardinha Coqueiro Tomate 125g" com ordem diferente, ou o dono editou o nome_familia no diálogo), nada casa e nasce produto DUPLICADO fora da família antiga. Conserto: em importar (ou num obter_ou_criar_por_sabor dedicado), fallback de match por nome_sanitizado (e pela chave natural de portabilidade) antes de criar; e em criar_familia_de_sabores, ANTES de criar, consultar os membros da família existente (item 5) e casar sabor↔membro por sabor_do_membro/fuzzy, criando SÓ o que falta.

106. REUSO SILENCIOSO SOBRESCREVE A CURADORIA DO MEMBRO EXISTENTE. servico.py:3436-3447 (finalizar_criacao): quando importar REUSA um produto existente, o fluxo mesmo assim reescreve nome_sanitizado, selo_mais18, bebida_alcoolica, categoria e — se a tela de fotos por sabor trouxe imagem — bib.ingerir substitui a foto curada (atual.png) sem aviso. Reimportar uma família existente com fotos novas apaga o packshot tratado anterior em silêncio (viola I2 e a não-destrutividade do Estúdio F10). Conserto: quando res.criado=False, não sobrescrever foto/categoria existentes (ou perguntar); o FotosPorSaborDialog deveria mostrar a foto ATUAL do membro já existente e só pedir foto para os sabores novos.

107. A CURADORIA NÃO CONSULTA O BANCO POR FAMÍLIA JÁ EXISTENTE. conciliacao_dialog.py:840 (familia_da_linha) + 979 (criar_familia_de_sabores): a 3ª pergunta nasce só do texto da linha — nunca pergunta ao banco "já existe família cujo nome/membros casam com esta base?". Cenário do dono: família "Sardinha Coqueiro 125g" existe com Tomate e Óleo; a linha nova traz Tomate/Óleo/LIMÃO — o app propõe criar tudo do zero. Conserto: um FamiliaRepositorio.buscar_por_nome_aproximado(base_fam) (nome normalizado + fuzzy) alimentando o diálogo com "família encontrada: N membros, faltam estes sabores" — o criar vira incremental (cria só Limão, liga ao fid existente).

108. FamiliaRepositorio.obter_ou_criar CASA POR STRING EXATA — "125 g" ≠ "125g" cria FAMÍLIA GÊMEA. repositories.py:232-241: o where é FamiliaProduto.nome == nome, sensível a caixa/espaço/acento, e definir_familia (209-217) re-liga os ids passados sem olhar a família anterior deles. Uma variação de grafia do nome-base entre dois meses divide os membros em duas famílias paralelas, e a família antiga pode ficar VAZIA (ninguém dissolve — lixo órfão). Conserto: normalizar o nome (sanitizar) antes do ==, fallback fuzzy; em definir_familia, se o produto tinha outra familia_id, avisar (I2) e limpar família que ficou sem membros.

109. DUAS MARCAS × SABORES NÃO TEM MODELO — a barra veta o composto e o " e " polui a base (pergunta a). servico.py:3032 (dividir_em_dois: "/" na linha → lista vazia, tratado como só-sabores) × servico.py:3055-3081 (familia_da_linha: tudo antes da última medida vira base — "PIZZA SADIA E PERDIGAO 460 G MUSSARELA/CALABRESA" gera base "Pizza Sadia e Perdigao 460g" com as DUAS marcas fundidas num nome, exatamente o produto-remendo que a rodada JM proibiu). Não existe caminho para o produto cartesiano (2 marcas, cada uma com sabores). Conserto (desenho): familia_da_linha passa a devolver também as MARCAS da base (reusando extrair_marca/marcas_do_acervo, servico.py:3138); quando base contém " e " entre 2 marcas conhecidas E há sabores no rabo, a curadoria oferece o híbrido: UMA família por marca ("Pizza Sadia 460g" + "Pizza Perdigao 460g", cada uma com os sabores), e o item da estante vira composto LADO_A_LADO de dois leques (ou um leque único com membros das duas famílias, decisão do dono no diálogo).

110. TRÊS MARCAS: o corte é só no PRIMEIRO " e " e o criador trunca em [:2]. servico.py:3034 (dividir_em_dois: re.search do primeiro " e " — "A e B e C" vira ["A", "A B e C"], a 2ª/3ª marcas fundidas num nome errado) + servico.py:2012 (criar_como_composto: nomes_componentes[:2] descarta o 3º calado) + 1970-1972 (compor_itens: profundidade 1, e imagens só quando len==2 em 1981). Conserto: dividir_em_N (split por todos os " e "/vírgulas entre marcas conhecidas), criar_como_composto aceitar N componentes, e compor_itens generalizar arranjo/imagens para N (ou, no mínimo, deve_revisar_no_lote detectar 3+ marcas e recusar com motivo dito em vez de truncar).

111. VÍRGULA NÃO SEPARA SABORES. servico.py:3073: o split do rabo é só "/" e " e " — "125 G TOMATE, OLEO E LIMAO" (grafia comum de tabela) produz o sabor errado "Tomate, Oleo". Conserto: incluir a vírgula no re.split (r"\s*/\s*|\s*,\s*|\s+e\s+").

112. UM SABOR NOVO SOZINHO NÃO TEM PORTA. servico.py:3081: familia_da_linha exige >=2 sabores para devolver a lista — a linha "SARDINHA COQUEIRO 125 G LIMAO" (sabor novo de família existente) devolve zero sabores, a 3ª pergunta não aparece e o produto nasce SOLTO, fora da família. Conserto: com 1 sabor detectado E família existente casando a base (item 5), oferecer "juntar à família X" na curadoria (e no Almoxarifado o gesto já existe — ligar).

113. O LEQUE PÓS-CRIAÇÃO ANUNCIA A FAMÍLIA INTEIRA, NÃO OS SABORES DA OFERTA. servico.py:3118-3121: aplicar_sabores(item, fam["membros"]) entra com TODOS os membros vivos da família — quando a família já tinha sabores de meses anteriores que NÃO estão na linha de hoje, o descritor da célula ("Tomate, Óleo ou Limão") e as fotos do leque incluem sabores fora da oferta (risco PROCON: anunciar variante que não está no preço). Conserto: aplicar_sabores com o subconjunto dos membros correspondentes aos sabores DA LINHA (interseção via sabor_do_membro), com o dono podendo marcar mais no SaboresDialog.

114. VINCULAR (aceitar_correspondencia) NÃO TRAZ A FAMÍLIA NEM O LEQUE NA HORA. servico.py:2905-2932: ao forçar o vínculo, o item ganha nome/imagem/mais18/preco_de, mas item.familia, item.imagens (RG-28) e item.sabores ficam como estavam — o dono vincula a linha multi ao membro-âncora e o leque só aparece na PRÓXIMA importação (quando o conciliar em 2494 pendura a família). Conserto: dentro do mesmo fluxo, item.familia = familia_do_item(produto_id) + aplicar_sabores com os sabores detectados da linha; de quebra, o mais18 na 2928 é `bool(p.selo_mais18)` seco — viola a L12 (a régua soma): deveria ser OR eh_bebida_alcoolica(p.nome_sanitizado).

115. A PENDÊNCIA "multiplos" REBAIXA ATÉ A LINHA QUE JÁ É FAMÍLIA CONHECIDA. servico.py:2425-2431: linha com " e " casada verde não-exato desce a AMARELO com "parece 2 produtos" mesmo quando o produto casado TEM familia_id (os "2 produtos" são sabores já modelados). Após o conserto do item 1 o exato resolve, mas o caminho fuzzy continua assustando o dono todo mês. Conserto: se p.familia_id existe e familia_da_linha detecta sabores cobertos pelos membros, suprimir o rebaixamento (ou trocar o motivo por "sabores da família X — confira o leque").

116. dividir_em_dois REPLICA SÓ O 1º TOKEN COMO TIPO — tipo de 2 palavras degrada o componente B. servico.py:3043-3046: "DOCE DE LEITE MU E TIA NAIR 400 G" → tipo replicado = "Doce" apenas; o componente B vira "Doce Tia Nair 400g" (perde "de Leite"). Conserto: replicar o prefixo até a 1ª marca conhecida (extrair_marca) em vez do 1º token, com fallback no token único.

117. FAMÍLIAS ÓRFÃS E MEMBROS ROUBADOS SEM AVISO. repositories.py:209-217 + 232-241: definir_familia re-aponta familia_id sem checar a família de origem — um fluxo de criação que reusa produto já familiado (item 3) o ROUBA da família antiga em silêncio, podendo esvaziá-la (e nada a remove; dissolver em 258 só roda por gesto manual). Conserto: em definir_familia, coletar as famílias de origem afetadas, avisar quando um produto troca de família, e apagar (ou reportar) família que ficou com zero membros.

Resumo do desenho do conserto (a espinha): (i) obter-ou-criar POR SABOR com match em degraus — nome_bruto/alias → nome_sanitizado/chave natural → fuzzy contra membros da família candidata — criando SÓ o que falta e sem sobrescrever curadoria; (ii) detecção marcas×sabores em familia_da_linha (marcas conhecidas na base + sabores no rabo) alimentando uma 4ª resposta na curadoria (N famílias, uma por marca, compostas no item); (iii) aprendizado da LINHA: alias da descrição crua no membro-âncora (família) e memória linha→[ids] para composto, de modo que a reimportação do mês seguinte saia VERDE com o leque montado, pré-marcando só os sabores presentes na linha. Arquivos-chave: C:/Users/otavi/Documents/Projetos_programação/autotabloide_ai/app/qt/telas/servico.py, app/qt/telas/conciliacao_dialog.py, app/core/repositories.py, app/ai/conciliacao.py.

## O ENRIQUECIMENTO/REORDENAÇÃO DOS NOMES

AUDITORIA — enriquecimento/reordenação da linha "BISCOITO BULNEZ e ADORALLE 270 g C. CRACKER/LEITE/AGUA". Todos os achados abaixo foram REPRODUZIDOS na bancada (python real sobre o código do repo). Saída real de hoje: sanitizar → "Biscoito Bulnez e Adoralle 270g C. Cracker/leite/agua", pendência ["multiplos"], dividir_em_dois → [], deve_revisar_no_lote → None (cria calado). Lista numerada:

118. GRAVE — A linha mista (2 marcas + sabores) é criada CALADA com o nome remendado. Causa: app/qt/telas/servico.py:3032-3033 (`dividir_em_dois` devolve [] se houver "/" no texto) + servico.py:3125-3135 (`deve_revisar_no_lote` só segura por `tokens_perdidos` ou `possivel_composto`; a pendência "multiplos" que o sanitize JÁ levantou e os sabores de `familia_da_linha` não contam). Resultado: `possivel_composto=False`, a pergunta da curadoria nunca acende e o produto nasce com o nome cru concatenado — exatamente o que o dono viu. Conserto: em `deve_revisar_no_lote`, segurar também quando `familia_da_linha(descricao)` detectar 2+ sabores OU quando a pendência "multiplos" existir mesmo sem sugestão pronta (o humano decide; nada calado — I2).

119. GRAVE — Peso no MEIO do nome nunca vai para o fim: a ordem Tipo+Marca+Sabor+Peso só existe no prompt da IA. Causa: app/core/sanitize.py (~linha 386, `separar_peso` só corta peso no INÍCIO ou no FIM) e app/ai/enriquecimento.py:77-78 (a ordem é pedido ao LM, não regra); o ramo determinístico (`_degradado`, enriquecimento.py:285-295, que até admite "nome pode não estar na ordem final") não reordena nada. Repro: "…ADORALLE 270 g C. CRACKER…" fica com "270g" no meio. Conserto: passo determinístico pós-sanitize que extrai a 1ª medida do MIOLO e a move ao fim do nome (ou ao descritor "· 270 g"), com teste de mutação.

120. GRAVE — `dividir_em_dois` desiste da linha INTEIRA por causa da barra (servico.py:3032: `if not texto or "/" in texto: return []`). A barra sinaliza sabores só no RABO pós-medida; o " e " das marcas está ANTES do peso. Conserto: primeiro separar o rabo com a mesma régua de `familia_da_linha` (texto até o fim da última unidade) e aplicar o corte no " e " apenas na parte antes do peso — "BISCOITO BULNEZ e ADORALLE 270 g" → ["Biscoito Bulnez 270g", "Biscoito Adoralle 270g"], sabores ["Leite", "Água"] à parte.

121. `familia_da_linha` classifica o TIPO como sabor e deixa as 2 marcas na base. Causa: servico.py:3055-3081 — o rabo "C. CRACKER/LEITE/AGUA" vira sabores ["C. Cracker", "Leite", "Agua"] e a base sugerida é "Biscoito Bulnez e Adoralle 270g" (com o " e " das marcas dentro). "C. Cracker" é descritor do tipo (Cream Cracker), não sabor. Conserto: quando a base tem " e " antes do peso (padrão de 2 marcas), o 1º segmento do rabo que for descritor de tipo (multi-palavra/abreviação com ponto, ou palavra do vocabulário de tipos) sobe para a base; e a curadoria recebe base SEM o " e " resolvido só depois da pergunta "são 2 produtos?".

122. O FURO ANOTADO (QUINTUSDECIMUS, docs/ORDEM_F13_QUINTUSDECIMUS_AUDITORIA_AO_VIVO_DO_JORNAL.md:512) — `ordenar_tipo_marca` só roda no ramo SEM IA. Causa: servico.py:3174-3183 (ramo `motor is None`) vs. servico.py:3195-3219 (ramo com IA não chama `ordenar_tipo_marca` nem nenhuma reordenação determinística sobre `enr.nome_sanitizado`). Se o LM devolver o nome na ordem crua (o que aconteceu na máquina do dono), nada conserta — viola a lei "a IA SOMA, nunca substitui". Conserto: aplicar `ordenar_tipo_marca(enr.nome_sanitizado, marcas_do_acervo())` + o passo do peso (achado 2) TAMBÉM no ramo com IA, sempre por cima do que o LM devolver.

123. BUG NOVO (não anotado, pior que "inócuo") — `ordenar_tipo_marca` CORROMPE nome com 2 marcas ligadas por "e". Repro real: `ordenar_tipo_marca("Biscoito Bulnez e Adoralle 270g", ["Bulnez","Adoralle"])` → "Biscoito Adoralle Bulnez e 270g" (conector "e" órfão, marcas embaralhadas). Causa: app/core/aprendizado.py:93-112 move só a marca extraída (a mais longa) e ignora o conector. Conserto: se `extrair_marca` casar 2+ marcas conhecidas no nome, ou existir o padrão "Marca1 e Marca2", NÃO reordenar (devolver como veio — conservador) ou mover o bloco "Marca1 e Marca2" inteiro como uma unidade.

124. BUG — `ordenar_tipo_marca` assume tipo de UMA palavra. Repro real: `ordenar_tipo_marca("Firmesa Doce de Leite 400g", ["Firmesa"])` → "Doce Firmesa de Leite 400g" (a marca entra no MEIO da locução do tipo). Causa: aprendizado.py:112 (`[resto[0]] + marca_toks + resto[1:]` — insere sempre após o 1º token). Conserto: pular o bloco do tipo inteiro (tokens iniciais ligados por preposição "de/do/da") antes de inserir a marca.

125. Capitalização não atravessa a barra: "CRACKER/LEITE/AGUA" sai "Cracker/leite/agua". Causa: o formatador de caixa do sanitize (app/core/sanitize.py, `formatar_nome`) separa tokens só por espaço — os segmentos após "/" ficam minúsculos. Conserto: aplicar a regra de 1ª-maiúscula por segmento de "/" também.

126. "AGUA" fica sem acento: app/core/ortografia.py não tem "agua"→"água" no vocabulário (é inequívoco no mercado, o critério da própria ortografia determinística). Repro: `sanitizar("AGUA MINERAL 500 ML")` → "Agua Mineral 500ml". Conserto: acrescentar água (e vizinhos óbvios: açúcar/óleo já cobertos?) ao vocabulário.

127. Não existe expansão "C." → "Cream": `REGRAS_PADRAO.glossario_siglas` está VAZIO por padrão, e nada semeia "C. CRACKER"→"Cream Cracker". Hoje "Cream" só sobrevive à guarda `remover_inventados` POR ACASO (ver achado 11). Conserto: semear o glossário com abreviações de tabela consagradas (C. Cracker, Sob./Sobrecoxa etc.), sempre confirmáveis pelo dono na aba Sanitização.

128. Brecha na guarda anti-invenção: `tokens_inventados` (app/ai/enriquecimento.py:131-147) compara por SUBSTRING bidirecional e o bruto contém o token "c" (de "C."); como "c" ∈ "cream", QUALQUER palavra inventada pela IA que contenha a letra "c" passa como legítima nessa linha. Conserto: exigir comprimento mínimo (≥3) do candidato do bruto no teste de substring (`cand in tok` só se len(cand) >= 3), com teste adversarial.

129. O formato-alvo do dono não tem montador: "Biscoito Cream Cracker Bulnez e Adoralle · Leite/Água · 270 g" é composto (2 marcas) COM descritor de sabores, e `nome_composto` (servico.py:1832-1853) só produz "A e B · peso" — não existe o segmento "· Leite/Água ·". Além disso a 3ª pergunta da curadoria é mutuamente exclusiva (radio "2 produtos" × "sabores" × "um só" — conciliacao_dialog.py:836-850): a linha do Biscoito é as duas coisas ao mesmo tempo e não há caminho combinado. Conserto: `nome_composto` ganhar parâmetro `sabores` (insere "· Leite/Água" antes do peso) e a curadoria aceitar composto+sabores juntos quando `dividir_em_dois` (consertado, achado 3) e `familia_da_linha` (consertado, achado 4) acenderem simultaneamente.

130. Menor — `enriquecer_descricao` descarta a marca por componente da IA: servico.py:3197 achata `enr.componentes` para só `nome_sanitizado`; a `Componente.marca` (enriquecimento.py:33-37) poderia alimentar `ordenar_tipo_marca` e a busca de imagem por componente. Conserto: fazer a marca viajar na `PropostaCriacao` (lista paralela ou dataclass).

131. Menor — `PropostaCriacao` não carrega os sabores detectados: a curadoria recalcula `familia_da_linha` por conta própria (conciliacao_dialog.py:840), mas a fila em LOTE decide sem esse sinal (raiz do achado 1) e o worker de enriquecimento não tem como somar sabores da IA (variantes de `enr.variantes` também são descartadas em servico.py:3204-3219). Conserto: campo `sugestao_sabores` na `PropostaCriacao`, preenchido por `familia_da_linha` OR `enr.variantes` (a régua SOMA, L12).

CADEIA DO CONSERTO para a linha do Biscoito sair "Biscoito Cream Cracker Bulnez e Adoralle · Leite/Água · 270 g": (3) dividir antes do peso ignorando o rabo → (4) rabo separa tipo-descritor ("C. Cracker" sobe) de sabores (Leite/Água) → (10) glossário expande C.→Cream → (9)+(8) acento e caixa → (2) peso ao fim como "· 270 g" → (12) montador composto+sabores → (1)+(14) a fila segura e pergunta em vez de criar calado → (5)+(6)+(7) a reordenação determinística roda nos DOIS estados da IA sem corromper multi-marca.

---

**TOTAL: 131 achados numerados.**


## ADENDO DA ONDA 2 (executada em 03/08 — as decisões do dono)

132. O slot de textos do jornal ATRAVESSA a página e cegava a régua de folga
     (o bbox por slot escondia o subtítulo da manchete; o fio riscou o texto
     na 1ª tentativa) — consertado: as caixas viajam POR REGIÃO visível.
133. O Jornal estático de 42 células é DENSO (folgas reais de 2,4 mm entre
     fileiras): o cabeçalho de seção NÃO cabe entre fileiras — a régua nova
     cala em vez de riscar. EVOLUÇÃO NOMEADA (Onda 3): o gerador do Jornal
     reservar ~4 mm acima da fileira que inicia seção, aí o cabeçalho
     tipográfico aparece em todas.
134. Cabeçalho por categoria DEDUPADO no estático: só o maior run fala
     (a página do dono tinha "BEBIDAS" 2× por fragmentação).
135. Vizinho LARGO acima (manchete/subtítulo — território editorial) exige
     respiro dobrado: melhor calar que riscar texto.

**Onda 2 EXECUTADA**: anti-duplicata (membro_do_acervo casa bruto→alias→
chave natural; criar_familia_de_sabores casa existentes e cria só o que
falta — reimportar é idempotente, foto nova de membro existente vira
versão no próprio); cartesiano marcas×sabores (rotulos_marcas_x_sabores,
marca-major) com a régua do caber (MAX_FOTOS_CELULA=4 +
selecionar_fotos_da_celula espaçada — pega as duas marcas); a tela de
N espaços mostra "✓ já no acervo" com a foto atual; o Jornal ganhou
estilo_secoes="JORNAL" próprio no pacote (o Agrupar agora liga NELE) com
o cabeçalho medido na folga.


## ADENDO DA ONDA 3 (03/08, o print da conciliação do dono)

136. **A CONCILIAÇÃO PENSAVA POR PRODUTO ÚNICO** — o conceito que
     faltava, agora implementado: a linha MULTI casa com um CONJUNTO do
     acervo (`conjunto_do_acervo`): se TODOS os membros que ela declara
     já existem (nome → alias → chave natural, com a reserva sem-espaços
     "5kg"="5 kg"), o item nasce VERDE MONTADO (`item_do_conjunto`) —
     leque das fotos existentes, sabores no descritor, composto com as
     2 fotos — sem curadoria, sem busca, sem recriação. PARCIAL NÃO
     INVENTA (membro faltando → fluxo normal). Sabores vencem quando os
     dois detectores disparam (a divisão perde a marca do 2º).
137. "TEMPERO TIO JONAD 1 Kg TODO S" — "TODOS" partido pelo OCR
     ("TODO S") e "JONAD"≠"Jonas": candidatos ao vocabulário/bigramas
     da ortografia (nomeado).
138. Marcas×sabores no MESMO conjunto (o Biscoito 2×3) reconhecido na
     reimportação: depende da grafia com que o dono criar os 6 pela
     tela — nomeado para depois da primeira criação real dele.

## AS ONDAS DE EXECUÇÃO

**Onda 1 — JÁ EXECUTADA nesta rodada (o commit desta data):**
- A VITRINE EM CAMADAS: o `_lado_a_lado` fatiado morreu — fotos grandes
  (n=2 → ~75% da zona), sobrepostas de leve, a 1ª na frente e maior,
  base comum (arranjo.py; o adversarial I5 re-contratado por centroides).
- A DUPLA GRAMATURA: dois pesos consecutivos no fim descem JUNTOS
  ("400 g ou 500 g") — conserta Milho Pipoca, Kitubaina, Creme Dental e
  Rosquinha com UMA régua (sanitize.separar_peso em cascata guardada).
- O DESLIGAMENTO DO ESTRAGO DAS SEÇÕES: "Agrupar por categoria" deixa de
  LIGAR o desenho de seções em encarte que as veta (o Jornal da
  biblioteca nasce com secoes_ligadas=False de propósito) — o agrupar
  vale como ORDENAÇÃO; o desenho só liga onde a página define estilo
  próprio. Mata os chips sobre títulos e as molduras cortando colunas.

**Onda 2 — a combinatória (as 3 perguntas do dono; decisões dele abaixo):**
- Obter-ou-criar POR SABOR: a linha casa os membros que JÁ existem
  (chave/alias) e cria SÓ os que faltam, na mesma família; a curadoria
  mostra "já no acervo ✓" por sabor. Reimportar nunca recria.
- Marcas × sabores (Urca/Limpoll/Nivea "Diversos"): detector + alias da
  linha inteira; 3+ marcas: o composto sobe de 2 para N.

**Onda 3 — a página profissional:**
- Chips na FOLGA (nunca sobre conteúdo), moldura com inset em grade
  colada, herói escolhido DENTRO da categoria da região, runs quebrando
  em célula fixa, bbox com rotação.
- Ano/Nº no cabeçalho (campo da edição), Fica a Dica editorial (K8),
  alinhamento de preços por linha, carimbo SUPER OFERTA que cresce,
  abreviações por extenso, Wafer/Água/Marajá no vocabulário.
- Higienização dos dados: o "T1" e o "Todos" nos produtos já criados.

## PERGUNTAS AO DONO (decisões que são suas)
1. Linha "2 marcas × sabores" (ex.: Urca 2L Vários): na página, UMA
   célula com as fotos das duas marcas e "Vários" no descritor — ou
   prefere escolher UMA foto por marca?
2. O Ano/Nº do jornal: quer digitar uma vez ("ANO 40 · Nº 476") e o app
   só incrementar o Nº a cada edição nova?
3. As seções DESENHADAS no Jornal: quer o visual do próprio jornal
   (fio + título tipográfico, como o fluxo por seções já desenha) ou o
   Jornal SEM seções desenhadas (só a ordenação por categoria)?

## INVENTÁRIO v2 — A 2ª PROVA DO DONO (03/08, a frota de 6 auditores)

O dono recompôs o Jornal depois das 3 ondas e mandou as fotos da 2ª
prova com ~20 apontamentos diretos. A frota v2 (6 auditores lendo o
código real) transformou cada queixa em causa+conserto. Os relatórios
íntegros abaixo; a execução em "AS ONDAS v2" no fim.

**O CONFLITO K2 (declarado para a reauditoria):** o K2 do arquiteto
(JQ-BIS) mandou desenhar o preço inline DENTRO do carimbo ("SUPER
OFERTA · R$ 18,81"). Na 2ª prova o dono decidiu o contrário: "a super
oferta tem o valor junto (não pode ter, tem que ser só o super
oferta)". A decisão do DONO vence (é o selo humano): o carimbo desenha
SÓ o texto; o valor extraído (L4) segue vivo no item — Excel, cartaz e
painel continuam enxergando o preço. O teste
`test_k2_carimbo_so_com_o_texto_por_pixel` teve o contrato INVERTIDO
de propósito (tinta idêntica com e sem preco_por) e o comentário no
compositor documenta o conflito.


### V-A · A HIERARQUIA DO NOME NA CÉLULA (o 'sem padrão nenhum')

AUDITORIA — HIERARQUIA DO NOME NA CÉLULA (linha grande × descritor)

DIAGNÓSTICO-MÃE (0): hoje a divisão nome-grande/descritor é decidida por GEOMETRIA, nunca por SEMÂNTICA. `precedencia_do_nome` (C:\Users\otavi\Documents\Projetos_programação\autotabloide_ai\app\rendering\nome_fit.py:246) só desce tokens ao descritor quando o nome NÃO CABE (passos 1-2 na linha 331 devolvem o nome inteiro se couber; o passo 5 na linha 364 poda do fim, um a um, até caber). Resultado: em célula larga a marca fica na linha grande ("Leite Int. L.V." + "Triângulo"), em célula apertada desce ("Leite Integral" + "Parmalat · L.V. · 1L") — o "sem padrão" que o dono viu é exatamente isso. A marca do produto NUNCA entra de propósito no descritor: `dados_para_desenho` (app/qt/telas/servico.py:768-771) monta o descritor só com sabores + "marca própria" + unidade. A estrutura tipo/marca/sabor que a IA devolve (`ProdutoEnriquecido.tipo/marca/sabor`, app/ai/enriquecimento.py:44-46) é DESCARTADA — só o `nome_sanitizado` plano sobrevive no ItemMesa.

REGRA CANÔNICA PROPOSTA (uma só, para os 3 casos):
- LINHA GRANDE (região NOME) = TIPO do produto (o "o que é": "Leite Integral", "Açúcar Cristal", "Batata", "Arroz", "Milho Verde").
- DESCRITOR (região SUBTITULO) = MARCA · qualificador/embalagem (siglas protegidas L.V./TP…) · peso/unidade — nesta ordem, com o dedupe do `_juntar_descritor` de sempre.
- COMPOSTO: tipo COMUM na linha grande ("Arroz"); "Marca A e Marca B (embalagens)" abre o descritor ("Somar e Tio Bonini · 5 kg").
- FAMÍLIA: nome-base/tipo na linha grande; sabores "A, B ou C" (M3, já existe) + marca + peso no descritor.
- A cadeia geométrica dos 6 passos do nome_fit segue existindo, mas como REDE DE SEGURANÇA depois da divisão semântica, nunca como o critério.

ACHADOS E CONSERTOS:

1. A divisão semântica não existe (a causa do "sem padrão" Triângulo × Parmalat). Causa: nome_fit.py:331 (retorno cedo quando cabe) + servico.py:768 (descritor sem marca). Conserto: criar `dividir_nome_canonico(nome, marcas_conhecidas, regras)` (módulo novo app/core/nome_celula.py ou no próprio nome_fit) que usa `extrair_marca` (app/core/aprendizado.py:30) + `separar_peso` (app/core/sanitize.py:320) + siglas de REGRAS_PADRAO para devolver (linha_grande=TIPO, partes=[marca, qualificador, siglas, peso]); nunca inventa — sem marca CONHECIDA no acervo, comportamento atual (F9: a IA/regra não inventa marca).

2. Ponto único de aplicação: `dados_para_desenho` (servico.py:739-800). Causa: é a montagem OFICIAL das 3 portas (Mesa/export/Modo Pai) e é onde o descritor nasce (linha 768). Conserto: chamar a divisão canônica ali, fundindo marca ao descritor ANTES de sabores/"marca própria"/unidade; passar `marcas_do_acervo()` (servico.py:~3420) carregada 1× POR LOTE/página (a lição de desempenho da Rodada JM — nunca 1 query por item).

3. "Doce Dia" partida ao meio ("Açúcar Cristal Doce" + "Dia · 2kg"). Causa: nome_fit.py:364-371 poda token a token e `_corte_parte_marca` (nome_fit.py:235) só conhece `_PARES_DO_MERCADO` hardcoded {extra virgem, mon bijou} (linha 224) e `_ABRE_PAR` (linha 230) — "Doce Dia" não está em lista nenhuma. Conserto: o passo 5 recebe as marcas conhecidas e trata cada marca do acervo como BLOCO indivisível (o span da marca desce inteiro ou fica inteiro); com o item 1 aplicado, a marca já nem chega ao passo 5. Deixar de manter pares hardcoded — o acervo É a lista.

4. "Batata 104g Tubo" + "Pringles · 104g" (peso no meio + duplicado). Causa: `separar_peso` (sanitize.py:337, `ultimo.end() != len(base)`) só corta peso no FIM — "104g" seguido de "Tubo" fica no nome grande, e a unidade do dado repete "104g" no descritor. Conserto: no bloco C2 do nome_fit (nome_fit.py:307-325) descer também "peso + embalagem" quando o que segue o peso é SÓ token de embalagem conhecido; e acrescentar "tubo" ao `_EMBALAGENS` (servico.py:1808-1811, hoje não tem). Resultado canônico: "Batata" grande + "Pringles · tubo · 104 g".

5. Composto desequilibrado ("Arroz Somar" grande + "e Tio Bonini T1 · 5 kg" pequeno). Causa: `nome_composto` (servico.py:1849-1870) devolve UMA string plana ("Arroz Somar e Tio Bonini · 5 kg") que o passo 5 depois re-corta por geometria — "e" está em `_ABRE_PAR` (nome_fit.py:230), então "e Tio Bonini" desce junto e "Somar" fica órfã na linha grande. Conserto: `nome_composto` passa a devolver o PAR (nome=prefixo comum de tipo, ex. "Arroz"; descritor="Somar e Tio Bonini · 5 kg") — o `_juntar_com_e` (servico.py:1822) já calcula o prefixo comum, é só não recolar; chamadores (criar_como_composto/curadoria) gravam o descritor no item. O humano segue podendo editar no diálogo.

6. "Milho Verde Fugini" + "Pouch e Bonare 170g Lata" (confuso). Causa: mesma raiz do 5 — o nome composto com parênteses "Fugini (pouch) e Bonare (lata) · 170 g" vira string plana e o passo 5 do nome_fit a fatia em ponto arbitrário; `_juntar_descritor` (nome_fit.py:72) ainda faz strip de "·" e embaralha a leitura. Conserto: com o par do item 5, a linha grande é "Milho Verde" e o descritor nasce pronto "Fugini (pouch) e Bonare (lata) · 170 g" — o nome_fit não re-corta descritor, só o mede (`descritor_que_cabe`, nome_fit.py:140, já protege a unidade).

7. Resíduo "T1" no descritor do composto. Causa: a limpa de código de coluna da colagem (JQ-BIS) reconhece "T-1" por frequência; a grafia sem hífen "T1" escapou e viajou até o nome do componente. Conserto: a regex da limpa por frequência (app/qt/telas/…colagem) aceita a variante sem hífen com o MESMO critério conservador (>=3 e >=30% do lote; "Vitamina B-12"/"B12" isolada fica — caso-limite escrito no teste).

8. Siglas de embalagem na linha grande ("Leite Int. L.V."). Causa: o abreviador RG-22 (`abreviar_para_tabloide`, servico.py:1749) roda ANTES de qualquer divisão e a sigla L.V. só desce se o passo 5 geométrico rodar. Conserto: na divisão canônica (item 1), sigla de embalagem conhecida (REGRAS_PADRAO.siglas) SEMPRE vai ao lado protegido do descritor (a regra do dono de 27/07 "embalagem nunca se omite" já vive em `dividir_descritor`, nome_fit.py:103 — passa a valer também na partição inicial, não só no sacrifício).

9. A estrutura da IA morre na praia. Causa: `enriquecer_descricao` (servico.py:3452) e o caminho determinístico (`ordenar_tipo_marca`, app/core/aprendizado.py:93) garantem a ORDEM Tipo+Marca+Sabor+Peso no nome plano, mas tipo/marca separados do `ProdutoEnriquecido` não persistem no ItemMesa/Produto. Conserto (mínimo, sem schema novo): a divisão canônica RE-EXTRAI marca do nome plano com o acervo (item 1) — funciona porque a ordem da casa garante marca na posição 2; alternativa maior (persistir `marca` no Produto) fica NOMEADA para o arquiteto, não é pré-requisito.

10. Testes obrigatórios da mudança (lei da bancada): teste por PIXEL/conteúdo (I5) com os 5 casos reais do dono como fixtures — Leite Triângulo×Parmalat saindo com a MESMA hierarquia, "Doce Dia" nunca partida, "Batata"+"Pringles · tubo · 104 g", "Arroz"+"Somar e Tio Bonini · 5 kg", "Milho Verde"+"Fugini (pouch) e Bonare (lata) · 170 g"; guardiões nonus/quartusdecimus/duodecimus verdes (contratos antigos que mudarem de propósito, listados); os DOIS estados IA ligada/desligada (lei L12 — a régua soma).

ORDEM DE ATAQUE SUGERIDA: 1→2 (a régua e o ponto único), depois 5→6 (composto devolve par), 3 (marca-bloco no passo 5 como rede), 4+8 (peso-no-meio e siglas), 7 (T1), 10 (testes) — o item 9 só se o arquiteto quiser persistência.


### V-B · O PESO DUPLICADO nome×descritor (as 5 células)

AUDITORIA — PESO/QUALIFICADOR DUPLICADO nome×descritor (Jornal, células de linha com NOME+SUBTITULO). Diagnóstico central: nas 5 células o peso está NO MEIO do nome do banco ("Sabão Pó Omo 1,6kg Caixeta L. Perfeita", "Detg. Limpoll 500ml Diversos", "Waffer Bulnez 60g Chocolate", "Sabonete Nivea 85g Diversos", "Batata 104g Tubo Pringles"). O `separar_peso` só corta peso no FIM (lei da camada); o passo 5 do `precedencia_do_nome` desce o rabo ("Caixeta L. Perfeita", "Diversos", "Pringles"...) ao descritor, o peso FICA na linha grande, e a `unidade` do dado entra sempre no descritor de trabalho → "…1,6kg / … · 1,6kg".

1. O strip do peso roda UMA vez, antes do encurtamento — causa: C:\Users\otavi\Documents\Projetos_programação\autotabloide_ai\app\rendering\nome_fit.py:308 (`nome_atual, peso = separar_peso(nome)` só no início; o laço do passo 5, linhas 364-378, nunca re-separa). Depois que o passo 5 desce "Diversos"/"Caixeta L. Perfeita", o candidato passa a TERMINAR em peso ("Detg. Limpoll 500ml") e ninguém o tira. Conserto: dentro do laço do passo 5, rodar `separar_peso(candidato)` (e a régua de unidade solta) a cada corte; o peso extraído se junta a `partes_desc` — o `_juntar_descritor`/`_norm` já dedupe contra a unidade.

2. Peso no MEIO nunca sai da linha, mesmo com a unidade no descritor — causa: nome_fit.py:302-325 (só fim/solta) + o caso "Batata 104g Tubo" onde nem após o passo 5 o peso fica no fim. Conserto: no ramo COM SUBTITULO, remover do nome o token cujo `_norm` seja igual ao `_norm(unidade)` (ou casável por `_RE_PARTE_UNIDADE` com o mesmo valor) quando o descritor final já carrega essa unidade — dedução por IGUALDADE com a unidade do dado, não reordenação genérica (a lei da camada segue de pé para o resto).

3. `_juntar_descritor` compara o `existente` INTEIRO, não parte a parte — causa: nome_fit.py:72-80 (`for p in partes + ([existente]...)`: "Diversos · 500ml" vira UMA string; `_norm("diversos·500ml")` nunca está contido em "500 ml" já emitido → sai "500 ml · Diversos · 500ml"). Atinge item BEM formado (peso no fim + sabor no descritor): o strip do C2 gera "500 ml" e o descritor0 re-traz "500ml" atrás do sabor. Conserto: fatiar `existente` em `split(" · ")` e deduplicar parte a parte (aproveitar `_norm` por parte, nos dois sentidos).

4. Passo 5 sacrifica a MARCA antes do qualificador quando a ordem do banco está errada — causa: nome_fit.py:364-371 pop do FIM assume ordem Tipo+Marca+Sabor+Peso; em "Batata 104g Tubo Pringles" o fim é a marca → o Jornal imprimiu "Batata 104g Tubo / Pringles · 104g" (marca no descritor, peso na linha). Conserto: é sintoma do achado 6 (nome do banco fora da ordem travada); com o banco na ordem, o pop volta a descer sabor/embalagem primeiro. Paliativo opcional: ao re-separar o peso (achado 1), tentar caber o nome de novo antes de descer mais tokens.

5. "Diversos" como sabor-vago no descritor — causa: o texto vem do NOME do banco (rabo descido pelo passo 5), não de `it.sabores`; a montagem do descritor em C:\Users\otavi\Documents\Projetos_programação\autotabloide_ai\app\qt\telas\servico.py:768-771 (`juntar_com_ou(sabores) + marca própria + unidade`) não filtra nada. "Diversos" sozinho ("Diversos · 500ml", "Diversos · 85g") não diz NADA ao cliente — é resíduo da coluna do OCR ("sabores/tipos diversos"). Vale? Meio: informa que há variedade, mas é vago. Sugestão: lista pequena de vagos ("diversos", "vários", "sortidos", "variados") que o descritor reescreve para "vários tipos" ou omite — decisão do dono; e a curadoria/importação deveria oferecer transformar "Diversos" em pergunta de sabores (a 3ª pergunta J13/J22 já existe).

6. Nomes do banco guardam peso NO MEIO (fora da ordem travada Tipo+Marca+Sabor+Peso) — causa: a criação do produto vermelho/manual usa a linha do OCR sanitizada SEM reordenar (servico.py:3721 `finalizar_criacao`, servico.py:2988 `criar_produto_manual`; C:\Users\otavi\Documents\Projetos_programação\autotabloide_ai\app\core\sanitize.py:331-332 e 372-373 declaram "peso no MEIO segue intocado"). Os 5 nomes citados são exatamente isso: "Sabão Pó Omo 1,6kg Caixeta L. Perfeita", "Detg. Limpoll 500ml Diversos", "Waffer Bulnez 60g Chocolate", "Sabonete Nivea 85g Diversos", "Batata 104g Tubo Pringles". Conserto: na PORTA DE NASCIMENTO (não em releitura em massa), quando `separar_peso` falha no fim mas a régua acha peso no meio, mover o peso para o FIM do nome sugerido (a decisão travada da sanitização manda nessa ordem) e mostrar ao dono na curadoria — nunca renomear produto existente em silêncio; para o acervo atual, uma higienização com prévia (como a do "Leite Pó Ninho").

7. (Menor) `nome_com_unidade` só evita ANEXAR, nunca REMOVE — causa: C:\Users\otavi\Documents\Projetos_programação\autotabloide_ai\app\rendering\compositor.py:983-995 (guarda S2 impede "200g 200g", mas se o nome já traz a unidade E a célula tem SUBTITULO desenhando a mesma unidade, ninguém tira do nome — compositor.py:1194-1198 só suprime o ANEXO). Conserto: coberto pelos achados 1-2 no nome_fit; alternativa cirúrgica é a mesma dedução por igualdade aplicada em `precedencia_do_nome` antes dos passos 1-2, para o caso em que o nome CABE inteiro e nem entra no passo 5 (ex.: "Waffer Bulnez 60g" curto numa chamada larga → duplicaria mesmo sem encurtamento).

8. (Menor) `descritor_que_cabe` pode duplicar unidade dentro do próprio SUBTITULO — causa: compositor.py:832-836 passa `dados.descritor` + `dados.unidade`; se o descritor vier sem a unidade (ex.: só "Diversos") o fallback não anexa a unidade (só usa `unidade` quando descritor é None, nome_fit.py:148) — inverso do bug: unidade SOME do SUBTITULO quando o item tem descritor qualificador-puro vindo de projeto velho congelado. Conserto: em `descritor_que_cabe`, juntar descritor+unidade com o `_juntar_descritor` consertado (achado 3) em vez de `descritor or unidade`.

Nota de verificação: a cadeia roda para TODA célula em compositor.py:1244-1254; as linhas do Jornal têm NOME+SUBTITULO (encartes.py:708-733, `_jornal_linha`), então o caminho auditado é o único que desenha essas 5 células. Os testes atuais de nome_fit cobrem peso no FIM; nenhum cobre peso no meio + rabo descido (o cenário exato das 5 células) — o teste novo deve compor a célula e ler que "1,6kg" aparece UMA vez no par nome/descritor (por conteúdo, I5).


### V-C · O FALSO MULTI-TAMANHO E O VOCABULÁRIO (Kitubaina/Limpoll/Waffer)

1. FALSO MULTI-TAMANHO — a régua RODADA-125 junta erro de OCR como oferta de dois pesos. Causa: app/core/sanitize.py:353-363 (`separar_peso`) — a recursão nova pega DOIS pesos consecutivos no fim e devolve "peso2 ou peso" SEM nenhuma crítica de plausibilidade; o próprio comentário da linha 356 cita "Kitubaina 1,5L 1,6L" como caso legítimo, e o dono confirmou que o 1,6L era ruído de leitura. Conserto (a guarda proposta): antes de devolver o par, converter os dois à base canônica (o `_FATOR_PESO` de app/ai/conciliacao.py:58 já faz g/ml — extrair a uma função reutilizável ou replicar local) e, se a MESMA dimensão (g↔g, ml↔ml) tiver razão max/min ≤ ~1,15, fica UM só (o primeiro, a leitura da coluna principal) — nunca imprimir os dois.

2. A SUSPEITA PRECISA SER DITA (I2) — `separar_peso` devolve tupla e não tem canal de pendência; se a guarda só descartar o 2º peso, o descarte é silencioso. Causa: sanitize.py:320-363 (assinatura) + `_detectar_pendencias` em sanitize.py:252-296 (não conhece peso duplicado). Conserto: espelhar a detecção em `_detectar_pendencias` sobre o `com_unidades` (regex de duas expressões de peso consecutivas no FIM, mesma dimensão, razão ≤1,15) → `Pendencia("peso_duplicado_suspeito", "dois volumes quase iguais (1,5L/1,6L) — provável erro de leitura; ficou 1,5L")` nomeando os DOIS valores; o item desce a amarelo e o humano decide.

3. CASO-LIMITE DO LIMIAR, escrever no teste — "Creme Dental 90g 102g" (citado como REAL em sanitize.py:355) tem razão 1,133 ≤ 1,15 e cairia na guarda. Causa: o limiar ~1,15 engole um multi-tamanho verdadeiro. Conserto: manter o limiar (falso positivo é SEGURO porque vira pendência dita, não supressão calada — a lei da F9/L12) e gravar os dois lados no teste: 400g/500g (1,25) passa como par; 1,5L/1,6L (1,07) e 90g/102g (1,13) viram um-peso+pendência; unidades de DIMENSÃO diferente (30m, 12 rolos) nunca entram na conta.

4. LIMPOLL→LIMPOL. Causa: app/core/ortografia.py:25-48 (`ACENTOS_MERCADO`) não tem a entrada — o mapa já é o canal de typo (precedente "picoca"→"pipoca", linha 47). Conserto: `"limpoll": "limpol"` (chave minúscula sem acento; a caixa do molde preserva "LIMPOLL"→"LIMPOL").

5. WAFFER→WAFER. Causa: idem, ortografia.py:25-48. Conserto: `"waffer": "wafer"`.

6. TIO JONAD→Tio Jonas. Causa: idem. Conserto: `"jonad": "jonas"` como token (o "Tio" fica intacto); se houver receio de colisão fora do contexto da marca, alternativa conservadora: bigrama `"tio jonad": "tio jonas"` em BIGRAMAS_QUEBRADOS (ortografia.py:52-57), que exige o par.

7. TODO S→Todos (o S órfão do OCR). Causa: ortografia.py:52-57 — BIGRAMAS_QUEBRADOS não tem o par; hoje o "S" isolado ainda dispara `letra_isolada` em sanitize.py:279 (aviso, não conserto). Conserto: `"todo s": "todos"` no bigrama (mesmo mecanismo de "ole o"→"óleo", linha 55); o pendência letra_isolada morre junto.

8. "LEITE PÓ"→"Leite em Pó". Causa: não é token — é INSERÇÃO de preposição; nenhum mapa atual cobre. O BIGRAMAS_QUEBRADOS aceita alvo com espaços (o `padrao.sub` da ortografia.py:96-104 troca substring por substring). Conserto: `"leite po": "leite em pó"` em BIGRAMAS_QUEBRADOS; a caixa final sai certa porque `_aplicar_caixa` (sanitize.py:228) baixa o "em" (palavras_minusculas) e titula o "Pó". Atenção colateral: o comentário de nome_fit.py:238-239 usa "Leite Pó" como exemplo de nome que encerra — atualizar o comentário, a régua em si não muda.

9. "SABÃO PÓ"→"Sabão em Pó". Causa: idem à 8. Conserto: `"sabao po": "sabão em pó"`. GRAVE A PEQUENO: o casamento de bigrama (ortografia.py:97-99) é IGNORECASE mas SENSÍVEL a acento — "SABÃO PÓ" (já acentuado no bruto) não casa a chave "sabao po". Registrar as duas grafias ("sabao po" E "sabão pó") ou, melhor, normalizar o texto pela `_chave` antes do match de bigrama (conserto único que vale para todos os pares futuros).

10. "DOCE DIA" par consagrado (a marca não se parte no corte K3). Causa: app/rendering/nome_fit.py:224 — `_PARES_DO_MERCADO = {("extra","virgem"), ("mon","bijou")}` não conhece a marca. Conserto: acrescentar `("doce", "dia")`; o `_corte_parte_marca` (nome_fit.py:235-243) passa a descer o par junto.

11. GRAVE A PEQUENO — grafia mista no descritor do dono ("1,5 L · 1,6L"): quando o 2º peso NÃO passa por `separar_peso` (item cujo peso veio do campo estruturado e o "1,6L" ficou no nome), o descritor de nome_fit.py:80 concatena o formatado com o cru. A guarda do item 1 resolve o caminho principal; vale um teste que cubra também o caminho campo-estruturado+resto-no-nome (o `_peso_do_produto` de conciliacao.py:99-107 já lê os dois lados e serve de espelho para detectar o duplicado aí também).

12. GRAVE A PEQUENO — dimensões diferentes na guarda: "400g 0,5kg" é o MESMO peso em unidades irmãs (razão 1,25 em base g... na verdade 400 vs 500 = 1,25; mas "1kg 1000g" = razão 1,0). A comparação da guarda deve ser feita SEMPRE em base canônica (g/ml), nunca na unidade escrita — razão 1,0 exata (mesmo valor em grafias diferentes) também é suspeita de OCR/coluna duplicada e fica UM.


### V-D · A CAPA (Kolynos deslocado), o carimbo e as fotos cortadas

AUDITORIA (branch polimento-pre-f12; NB: o working tree tem diff NÃO COMMITADO em compositor.py/nome_fit.py/ortografia.py/test_rodada_jq_ordem.py — "RODADA-125 v2" — que já ataca parte do pedido):

1. CARIMBO "SUPER OFERTA" SEM O NÚMERO — JÁ CONSERTADO NO WORKING TREE, FALTA COMMIT+PROVA. Causa: app/rendering/compositor.py:672-678 (versão commitada ae0f2a3) anexava o valor ao preço-texto ("SUPER OFERTA · R$ 18,81") no ramo multi_preco de `_desenhar_preco` — o K2 da reauditoria. Conserto: o diff pendente já remove o append e desenha só `dados.multi_preco` (compositor.py:672-680 novo), com teste por pixel invertido de propósito (app/tests/test_rodada_jq_ordem.py:451-479, `test_k2_carimbo_so_com_o_texto_por_pixel`: tinta idêntica com e sem preco_por). Falta: recompor as provas — saida_f13/jm-prova-p1.png/p2.png AINDA mostram "· R$ 18,81" e "· R$ 6,90" no pixel — e commitar. O valor extraído (L4) segue no item para Excel/cartaz/painel; a estrela Splash do herói (papel OFERTA, compositor.py:188-193) já usava só o texto cru — nada a mexer lá.

2. CHAMADA DA CAPA QUEBRADA (o Kolynos) — o `_plano_misto` do foto_fit destrói o arranjo lateral das jp1-ch. Causa: app/rendering/foto_fit.py:136-179 (`_plano_misto`) + app/rendering/encartes.py:782-796. A chamada é foto à ESQUERDA (zona 112×132, `flex=True`, encartes.py:785) com nome/descritor/preço à DIREITA; para foto DEITADA (larga, o creme dental fotografado na horizontal) a ocupação medida fica <85% (foto_fit.py:240-243) e o plano roda: o misto quase sempre vence por área (foto_fit.py:262-263) e REORDENA a célula — nome/descritor sobem ao TOPO do bbox na largura total (foto_fit.py:150-152; o bbox inclui o overhang decorativo da foto, y−dy = 20px ACIMA do miolo, então o título cai "no meio do vão"), a foto vai GRANDE embaixo-ESQUERDA (foto_fit.py:164-165, `fx=x0`, ancorada em `y1-h`) e a pílula do preço à DIREITA dela (foto_fit.py:177). CONFIRMADO POR PIXEL na prova commitada: "Arroz Tio Bonini" e "Leite Integral" já saem nesse arranjo (título flutuando no vão, carimbo embaixo). Conserto: em `plano_da_celula`, o plano candidato não pode INVERTER a identidade da célula — quando os textos do template vivem AO LADO da foto (centro dos textos fora da faixa vertical da foto), só valem `_plano_lateral` e o abraço; o misto/vertical ficam para células onde o texto já vive acima/abaixo. E o bbox do plano deve usar o miolo da célula (excluir o overhang y−dy da foto), senão qualquer plano põe texto no vão. Alternativa cirúrgica mínima (perde o Q1 nas chamadas): tirar o `flex=True` de encartes.py:785.

3. NOME DA CHAMADA INVADE A CÉLULA VIZINHA (6 px). Causa: encartes.py:788-791 — nome/descritor em x+112 com largura 168 terminam em x+280, mas o passo entre chamadas é 274 (488→762); ch1/ch3 encostam na zona de foto de ch2/ch4 (o slot vizinho é desenhado depois e a foto cobre o fim do texto). Conserto: largura 162 (ou mover a coluna para x+108).

4. FOTOS CORTADAS NAS CÉLULAS — três mecanismos reais, por linha:
   a) Foto com zoom/foco ajustado: compositor.py:288-304 (`_imagem_enquadrada`) recorta o excedente na camada rw×rh — em zona estreita a foto sai decepada; e o gate do Q1 (compositor.py:1224-1225) EXCLUI foto com zoom≠1/foco≠0,5 do replanejamento, então ela nem ganha a zona maior. Conserto: no ASSENTAR com zoom, clampar o zoom ao que cabe (ou avisar no pré-voo, I2) — cortar produto nunca é silencioso.
   b) Fotos novas do dono são JPG SEM ALFA (Salgados.jpg, Sonho.jpg, "Lanche na Chapa.jpg", "Pão de Queijo.jpg" — soltas na RAIZ do repo, fora do acervo): compositor.py:334-337 — sem canal A não há recorte pela bbox do alfa nem transparência; o quadro branco inteiro entra, cobre vizinhos e é "cortado" pelas bordas da zona. Conserto: ingerir pelo Estúdio (rembg degrau 1) antes de compor; no mínimo, bbox por fundo quase-branco quando mode!=RGBA + aviso de pré-voo.
   c) O Fio das linhas do Jornal é desenhado DEPOIS da foto: encartes.py:721-723 — a foto sobe até y−20 (recolado F13-TER) e o ADORNO "Fio" (6px em y−20) vem depois na lista de regiões, riscando o topo do produto quando a foto enche a altura. Conserto: desenhar o filete ANTES da zona de foto (reordenar as regiões) ou iniciar a foto em y−14.

5. GRAVETO DE HIGIENE: as fotos do dono e "Ativo 2.png"/croissant.png/"pão frances.png"/AutoTabloide.bat estão soltas na raiz do git (untracked) — acervo do dono sempre ficou FORA do git (regra das rodadas); mover para a pasta de imagens do app ou ignorar no .gitignore antes do próximo commit.

Arquivos-chave: app/rendering/foto_fit.py (planos 91-205, gate 208-287), app/rendering/encartes.py (capa `_jornal_p1` 736-832, chamadas 778-796, linhas 708-733), app/rendering/compositor.py (`_desenhar_preco` 652-724, desenho de imagem 318-370, gate Q1 1210-1237), app/qt/telas/colagem.py:317-329 (`preco_texto_oferta`, o canônico — intocado, segue certo).


### V-E · O CARTESIANO NÃO OFERECIDO (Bulnez e Adoralle × 3 sabores)

1. "AGUA E SAL" é partido em dois sabores falsos — Causa: app/qt/telas/servico.py:3107 — `familia_da_linha` divide o rabo pós-medida com `re.split(r"\s*/\s*|\s+e\s+", ...)`, tratando TODO " e " como separador; para "C. CRACKER/LEITE/AGUA E SAL" devolve 4 sabores ["C. Cracker", "Leite", "Agua", "Sal"] em vez de 3. Conserto: dividir primeiro SÓ por "/"; dentro de cada segmento, só quebrar por " e " se o par não for sabor consagrado — vocabulário `_SABORES_COMPOSTOS` no padrão do `_PARES_DO_MERCADO` do K3 ("agua e sal", "doce de leite", "milho e ervilha", ...), protegendo o par ANTES do split (o "TOMATE / OLEO e LIMÃO" da Sardinha continua quebrando em 3 porque "oleo e limão" não está no vocabulário).

2. dividir_em_dois devolve [] para a linha inteira — a barra do rabo veta as marcas da frente — Causa: app/qt/telas/servico.py:3066 — `if not texto or "/" in texto: return []`: o veto da barra (pensado para sabores) olha a LINHA INTEIRA, mas em "BISCOITO BULNEZ e ADORALLE 270 g C. CRACKER/LEITE/AGUA E SAL" a barra está no rabo de SABORES e o " e " das marcas está ANTES da medida. Conserto: cortar a linha na última medida (o mesmo `_regex_unidades` que `familia_da_linha` já usa) e aplicar o veto de "/" e a busca do " e " SÓ na cabeça pré-medida ("BISCOITO BULNEZ e ADORALLE 270 g") — aí devolve ["Biscoito Bulnez 270g", "Biscoito Adoralle 270g"].

3. Sem componentes, a pergunta "são 2 produtos?" nunca nasce — Causa: app/qt/telas/servico.py:3481 e 3503 — `possivel_composto = len(comps)>=2 or len(det)==2`; com det=[] (achado 2) e a IA da máquina do dono devolvendo zero componentes, `possivel_composto=False` e `sugestao_componentes=[]`. Na curadoria os campos comp_1/comp_2 nascem vazios e o radio "São 2 produtos" fica sem sugestão. Conserto: o achado 2 já cura a régua; garantir por teste que esta linha real produz `possivel_composto=True` com os 2 nomes preenchidos (o cenário exato do J1/L2, agora com rabo de sabores).

4. O CARTESIANO é inalcançável pela UI — os radios são mutuamente exclusivos — Causa: app/qt/telas/conciliacao_dialog.py:938 exige `sab and len(proposta.componentes)>=2 and len(sab[1])>=2`, mas `componentes_finais()` (curadoria_dialog.py:359-366) devolve [] se `chk_composto` não está marcado e `sabores_finais()` (curadoria_dialog.py:368-371) devolve None se `rb_sabores` não está marcado — e os dois são QRadioButton no MESMO QButtonGroup (curadoria_dialog.py:115-117). O dono nunca consegue dizer "2 marcas E 3 sabores" ao mesmo tempo: o ramo do cartesiano é código morto pela UI (a linha 924 ainda sobrescreve `proposta.componentes` com [] quando ele escolhe sabores). Conserto: quando o detector vê marcas (dividir na cabeça, achado 2) E sabores (rabo) na MESMA linha, a curadoria ganha a 4ª opção explícita "São 2 MARCAS × N SABORES (criar os 6)" — radio próprio que habilita comp_1/comp_2 E os checks de sabores juntos; `componentes_finais`/`sabores_finais` passam a responder também nesse estado, e o `_curadoria` monta os rótulos com o `rotulos_marcas_x_sabores` (servico.py:3158) que já existe pronto e hoje nunca roda por esse caminho.

5. O nome sugerido da família carrega as DUAS marcas — Causa: app/qt/telas/servico.py:3105 — `base = sanitizar(texto[:ultimo.end()])` devolve "Biscoito Bulnez e Adoralle 270g" como `nome_familia_sugerido`; no cartesiano isso contaminaria os 6 nomes ("Biscoito Bulnez e Adoralle 270g Cream Cracker"). Conserto: quando a cabeça pré-medida divide em 2 marcas, `familia_da_linha` (ou uma irmã `marcas_e_sabores_da_linha`) devolve também as marcas separadas e a base SEM elas ("Biscoito 270g"), para a marca-major do `rotulos_marcas_x_sabores` gerar "Biscoito Bulnez Cream Cracker 270g" etc.

6. conjunto_do_acervo nunca reconhece o conjunto de 6 — Causa: app/qt/telas/servico.py:3210-3215 — com sabores>=2 ele monta nomes "base+sabor" usando a base que contém as 2 marcas (achado 5) e com a divisão errada do "Agua e Sal" (achado 1); nenhum nome casa com o acervo e devolve None (o próprio docstring 3203-3204 nomeia a limitação marcas×sabores). Conserto: após os achados 1/2/5, acrescentar o ramo marcas×sabores — nomes = `rotulos_marcas_x_sabores(marcas, sabores)` com a base limpa — para que, criados os 6 uma vez, a reimportação da mesma linha nasça VERDE montada.

7. Teste de regressão com a linha real do dono — Causa: nenhum teste cobre "BISCOITO BULNEZ e ADORALLE 270 g C. CRACKER/LEITE/AGUA E SAL" (a suíte tem Sardinha e Arroz, os casos puros de servico.py:3090-3094, não o misto). Conserto: teste L1 que afirma marcas=["Bulnez","Adoralle"] (via divisão da cabeça), sabores=["C. Cracker","Leite","Agua e Sal"] (3, não 4), e o gesto da curadoria com a 4ª opção produzindo os 6 rótulos do cartesiano — mais o caso-limite escrito de que "TOMATE/OLEO e LIMÃO" segue dando 3 sabores e "ARROZ SOMAR e TIO BONINI 5 Kgs" segue dando zero sabores e 2 componentes.


### V-F · A PÁGINA COMO UM TODO (dica, ano/nº, o Amaciante mudo)

AUDITORIA — a 2ª prova do Jornal (página como um todo). Lista numerada; caminhos absolutos a partir de C:/Users/otavi/Documents/Projetos_programação/autotabloide_ai/.

1. K8 CONFIRMADO — o Fica a Dica desenha a VALIDADE por fallback. Causa: app/rendering/compositor.py:194-201 — `texto_composto_legal` não tem ramo próprio para PapelTexto.DICA; a região cai no rabo genérico (`if fixo: … return validade`). O slot `jp2-dica` do Jornal nasce SEM `texto=` (app/rendering/encartes.py:857), então `fixo=""` e a função devolve `validade` — a caixa editorial imprime "OFERTA VÁLIDA DE 03/08 ATÉ 27/08" de novo. Conserto: ramo explícito `if papel == PapelTexto.DICA: return fixo` (vazia não desenha nada — condicional como OBSERVACAO/EDICAO); o comentário "validade legada é último recurso" vale para LIVRE/LEGAL, nunca para a dica.

2. K8 (a raiz de "a dica nunca nasce") — `gerar_dica` só existe atrás de um botão do editor. Causa: app/qt/painel_propriedades.py:200/609 — `_gerar_dica` roda apenas quando o dono seleciona a região DICA no editor de layout e clica o botão; o fluxo da Mesa (importar → compor → exportar) nunca chama app/ai/enriquecimento.py:426 (`gerar_dica`). Conserto: cascata igual à da validade/edição — ao montar a página (ou no salvar da Mesa), região DICA vazia + motor vivo ⇒ gerar com os nomes dos itens da página e gravar em `texto_fixo`; sem IA, cair no texto-padrão editorial (ver item 3).

3. Inconsistência Quintou × Jornal no default da dica. Causa: o painel-dica do Quintou tem texto editorial default no tom do publicado (app/rendering/encartes.py:903-909), mas o `jp2-dica` do Jornal nasce mudo (encartes.py:857). Conserto: dar ao Jornal um default no mesmo espírito (1-2 frases genéricas de mês), para a degradação sem IA nunca imprimir validade nem vazio.

4. Aviso do pré-voo da dica mente sobre o que sai no papel e não diz ONDE agir. Causa: app/qt/telas/servico.py:2194-2195 — o aviso "papel Fica a Dica sem texto — gere a dica pela IA" (a) contradiz a página, que na verdade desenha a validade (item 1); (b) viola a lição D3 ("a mensagem diz onde"): não existe caminho na Mesa para gerar a dica — só no editor de layout. Conserto: após o item 1/2, o aviso passa a ser verdadeiro; e a frase deve apontar o gesto real (ou o botão novo na Mesa).

5. Ano/Nº — onde nasce (resposta ao mapeamento): o campo é `edicao` do projeto (app/core/projetos.py:48-49), desenhado pelo papel `PapelTexto.EDICAO` (app/rendering/model.py:104; compositor.py:183-187; região única em encartes.py:813), viaja por `dados_para_desenho(..., edicao=)` (servico.py:742/799) e `_campo_vivo_da_pagina` (compositor.py:1181); a sugestão vem de `sugerir_edicao` (servico.py:1520) a partir de `eventos.edicao_base`, realimentada por `registrar_edicao_publicada` no export (mesa.py:3113).

6. Ano/Nº ausentes — o arranque a frio NUNCA destrava sozinho. Causa: servico.py:1540-1543 — sem base registrada, `sugerir_edicao` devolve None; a base só nasce quando o dono digita uma edição UMA vez e exporta (registrar_edicao_publicada, mesa.py:3113). Como ele nunca digitou (ver item 8), a região fica muda para sempre e o pré-voo só avisa (servico.py:2207-2209). Conserto: o aviso do pré-voo vira clicável/abre o diálogo `_editar_edicao`; ou, na primeira vez, sugerir "Nº 1 · ANO <ano>" explicitamente marcado como palpite editável.

7. `sugerir_edicao` só considera o EVENTO, não o nome do layout. Causa: app/qt/telas/mesa.py:1003 — `servico.sugerir_edicao(evento)`; compare com a validade duas linhas acima (mesa.py:993-994), que cai para `evento or self._layout_nome`. Jornal composto sem campanha atribuída nunca recebe sugestão. Conserto: mesmo fallback (`evento or self._layout_nome`).

8. O alvo de clique para digitar a edição é INVISÍVEL quando vazio. Causa: mesa.py:192 — `self._edicao_lbl = QLabel("")`; com `_edicao=None` o texto fica "" (mesa.py:520-521, 1107-1108): um label de largura zero com cursor de mão que ninguém encontra — o único jeito de nascer a 1ª edição está escondido. Conserto: placeholder permanente ("Edição: — (clique para definir)").

9. A sugestão da edição roda SÓ no salvar, nunca no compor. Causa: mesa.py:1002-1008 — o bloco vive dentro de `_salvar_projeto`; a página composta/prevista antes do 1º salvamento sai sem Nº/ANO (e a lição J24 da manchete diz que texto de página é DERIVADO desde o primeiro instante). Conserto: rodar a mesma cascata ao carregar o layout/definir o evento (o espelho do que o J24 fez com a validade).

10. A página 2 do Jornal não tem edição nem data de capa. Causa: encartes.py:835-861 — `_jornal_p2` só tem título + validade + dica; a única região EDICAO do encarte é da p1 (encartes.py:813). Jornal profissional repete nº/edição/data no rodapé de toda página (o "expediente"); não existe bloco de expediente algum no arquivo (grep por "expediente" = zero hits em app/). Conserto: região EDICAO (corpo pequeno, cinza) no cabeçalho/rodapé da p2 — o dado já viaja por `_campo_vivo_da_pagina`.

11. Amaciante "Amaciante / 5 L" — por que a família casada pelo CONJUNTO mostra sabores e a casada pelo fluxo antigo NÃO. Causa: dois caminhos assimétricos. (a) Caminho do conjunto: `conjunto_do_acervo` → `item_do_conjunto` preenche `sabores=list(conjunto["rotulos"])` + leque (servico.py:3254-3264) — daí a Sardinha sair "Tomate, Óleo ou Limão". (b) Fluxo antigo (exato/alias/fuzzy com UM produto): o conciliar preenche apenas `familia=` (servico.py:2526-2531) e NUNCA `sabores` — `aplicar_sabores` (servico.py:1962) só roda pelo menu de contexto manual da estante ("Sabores da família…", mesa.py:2414-2421/1849), que o dono não descobre. O descritor (servico.py:768-771) então só tem a unidade ⇒ "5 L". Conserto: quando o conciliar casa item com produto que TEM `familia_id`, pré-preencher `sabores`/leque com TODOS os membros (ou ao menos acender pendência/toast "família com N sabores — marque quais estão na oferta"); a escolha fina continua do dono, mas o padrão nunca é o silêncio.

12. Amaciante — a MARCA some do nome-base da família. Causa: `familia_da_linha` (servico.py:3089-3115) corta o base no fim da ÚLTIMA MEDIDA — numa linha "AMACIANTE 5 LTS MON BIJOU …" o base vira "Amaciante 5L" (a marca cai para o lado dos "sabores" ou some); `criar_familia_de_sabores` grava `item.nome = nome_familia` (servico.py:3403) e `item_do_conjunto` grava `nome=conjunto["base"]` (servico.py:3256) — a célula desenha "Amaciante / 5 L" sem Mon Bijou nem fragrâncias. Conserto: no detector, se houver token de MARCA CONHECIDA (extrair_marca/F9) depois da medida, puxá-lo para o base; e na curadoria J13 o campo "nome da família" deveria sugerir `nome_de_familia` dos membros (prefixo comum, servico.py:1880 — este preserva a marca) em vez do base cru da linha.

13. O descritor nunca fala a marca. Causa: servico.py:768-771 — descritor = sabores · "marca própria" · unidade; não há campo marca. Quando o nome vira o base da família sem marca (item 12), a marca não tem NENHUM lugar para aparecer na célula. Conserto: ou garantir marca no nome-base (item 12), ou acrescentar a marca ao descritor quando o nome não a contém.

14. Item casado com produto de família SÓ ganha o menu de sabores se `familia_id` existir no banco. Causa: servico.py:2528-2531 — `familia=None` para produto avulso antigo (pré-B4, ex.: o "Amaciante 5L" criado antes das famílias); mesa.py:2417 só oferece "Sabores da família…" com `it.familia` preenchido. O acervo velho nunca é convidado a virar família no fluxo de importação. Conserto: quando o casamento é com produto sem família mas a LINHA detecta sabores (`familia_da_linha`), oferecer "agrupar como família?" (a pergunta já existe no gesto de agrupar da Mesa, mesa.py:1942 — falta chamá-la aqui).

15. (Menor) `sugerir_edicao` ignora `hoje` na chamada real e abre uma conexão própria de banco por chamada (servico.py:1530-1537) — inócuo hoje (1 chamada por salvar), mas se entrar na cascata do compor (item 9), reusar a sessão do lote como o `_familia_em_lote` faz.

16. (Menor) O pré-voo da EDICAO avisa "defina a edição do jornal (Nº/Ano)" (servico.py:2208-2209) sem dizer ONDE — a mesma doença D3 do item 4; e o "onde" hoje é o label invisível do item 8. Os três consertos (4, 8, 16) se resolvem juntos.

RESUMO DO PADRÃO: os três defeitos da página têm a mesma anatomia — o mecanismo existe (papel DICA + gerar_dica; papel EDICAO + sugerir_edicao; famílias + aplicar_sabores) mas o GATILHO no fluxo real da Mesa não existe ou está escondido: a dica só nasce por botão do editor, a edição só por um label invisível + base que nunca arranca, os sabores só por menu de contexto. O conserto transversal é o espelho do J24/DECIMUS: todo dado de página é DERIVADO e se auto-preenche na composição, com o dono editando por cima — nunca o contrário.

## AS ONDAS v2 — O QUE FOI EXECUTADO (03/08, a resposta do builder)

### Onda v2-A · A HIERARQUIA CANÔNICA (o "sem padrão nenhum" morre)

A regra nova de motor, a decisão do dono: **a linha grande diz O QUE
É; a MARCA desce ao descritor SEMPRE** — não só quando falta espaço
(era a causa do Triângulo grande numa célula e o Parmalat descido na
outra). O mecanismo:

- **`app/core/marcas.py` (novo)** — o vocabulário de MARCAS do
  mercado, o espelho conservador do `mais18.py`/`ortografia.py`: só
  entra a palavra que nunca é tipo de produto (casos-limite escritos:
  "Ninho", "União", "Brilhante" e "Todos" ficam FORA — ambíguos);
  `marcas_no_nome` casa multi-palavra por janela com fronteira, a
  grafia devolvida é a DO NOME. Motivo do seed: o banco real tinha
  **116 produtos e ZERO marcas preenchidas** (medido) — sem seed, a
  hierarquia seria letra morta na máquina do dono.
- **`marcas_para_exibicao()`** (servico) = seed + `Produto.marca` do
  acervo + `marcas.proprias` da Config, carregada **1× por lote**;
  `dados_para_desenho(marcas=)` extrai as `marcas_nome` do item e o
  `DadosProduto` as leva ao compositor.
- **`nome_fit._descer_marca`** — a divisão canônica RODA SEMPRE que a
  célula tem SUBTITULO: o span vai da 1ª à última marca (conectores
  "e"/"ou" e parênteses de embalagem descem juntos — "Fugini (pouch)
  e Bonare (lata)" inteiro); o que vem depois da marca desce como
  qualificador; marca no token 0 não divide (o tipo não pode sumir);
  sem marca conhecida, nada muda (F9). Célula SEM SUBTITULO fica
  intacta (mover marca para lugar nenhum seria perda, I2).
- **`finalizar_criacao` grava `Produto.marca`** — o acervo alimenta a
  hierarquia sozinho daqui pra frente; e a higienização retroativa
  gravou **42 marcas** nos produtos reais (relatório nominal na
  sessão; backup `core_pre_v2_20260803.db`).
- O composto sai equilibrado: "Arroz" grande + "Somar e Tio Bonini ·
  5 kg" (o `_descer_marca` come o "·" órfão do formato do composto).

### Onda v2-A · O PESO NUNCA DUPLICA (as 5 células)

- **`_tirar_peso_repetido`** (nome_fit) — o peso que mora no MEIO do
  nome do banco e é IGUAL à unidade sai da EXIBIÇÃO (a unidade já o
  leva ao descritor); a embalagem colada a ele ("104g Tubo") desce
  junto. O banco fica intacto — a lei da camada do sanitize segue.
- **`_juntar_descritor` parte a parte** — o existente entra fatiado
  em " · " (comparado inteiro, "Diversos · 500ml" nunca continha o
  "500 ml" já emitido → "500 ml · Diversos · 500ml").
- **O passo 5 re-separa o peso a cada corte** — "Detg. Limpol 500ml"
  após descer "Diversos" termina em peso; agora ele desce ao
  descritor em vez de ficar na linha grande.
- **O peso do C2 não entra no meio** — quando a unidade já é o mesmo
  peso, quem o escreve é o descritor0, no FIM (ordem canônica marca ·
  sabores · peso; antes saía "Mabel · 600 g · Coco ou Leite").
- **`descritor_que_cabe` corta qualificador POR PARTE** — a marca
  sobrevive quando cabe ("Mon Bijou · 5 L" em vez do "5 L" mudo).
- **`separar_peso` com a guarda do falso multi** — razão ≤1,10 na
  mesma unidade é releitura do OCR ("1,5L 1,6L" → "1,5 L", o dono
  confirmou); 90g/102g (razão 1,13) segue "ou" — dois tubos reais.

### Onda v2-B · O BISCOITO (o cartesiano alcançável)

- **`_SABORES_COMPOSTOS`** — "AGUA E SAL" é UM sabor: o split da
  `familia_da_linha` virou dois tempos (barra primeiro; o " e " só
  quebra fora do vocabulário consagrado). "TOMATE/OLEO e LIMÃO"
  segue dando 3 (caso-limite escrito).
- **`_cabeca_pre_medida`** — `dividir_em_dois` corta a linha na
  última medida: a barra do RABO de sabores não veta mais o " e "
  das marcas da frente (a linha real do dono agora dá 2 componentes).
- **`marcas_e_sabores_da_linha`** — base LIMPA sem as marcas (o nome
  de família nunca mais carrega "Bulnez e Adoralle") + marcas + sabores.
- **A 4ª resposta na curadoria** — rádio próprio "São N MARCAS × M
  SABORES (criar todos)": o gate antigo exigia dois rádios exclusivos
  marcados juntos (o cartesiano era código morto pela UI).
- **`conjunto_do_acervo` com o ramo marcas×sabores** — criados os 6
  uma vez, a reimportação nasce VERDE montada; e `membro_do_acervo`
  ganhou a reserva de tokens ORDENADOS (a ordem das palavras não
  separa — as duas grafias de nascimento casam).

### Onda v2-C · A PÁGINA

- **A DICA nunca desenha validade** — ramo explícito no
  `texto_composto_legal` (vazia não desenha NADA; o rabo genérico
  imprimia a validade 2× na caixa do Fica a Dica); o `jp2-dica` do
  Jornal nasce com default editorial no tom do publicado.
- **A EDIÇÃO destrava** — a cascata roda no `carregar_layout` (o
  espelho J24: texto de página é derivado desde o primeiro instante),
  com fallback do nome do layout; o label nunca mais é invisível
  ("Edição: — (definir)" quando o layout usa o papel); a p2 ganhou a
  região EDICAO de expediente (condicional). O nº continua nascendo
  do dono (número inventado é rótulo mentindo, §4 da TER).
- **Item multi casado com produto de FAMÍLIA** ganha leque + sabores
  na hora e o nome vira o base ("Amaciante / 5 L" mudo morreu); a
  linha segue amarela (J9) — a escolha fina é do dono.
- **T1 sem hífen** na limpa por frequência da colagem (mesmo critério
  conservador; "B12" isolada fica).

### Onda v2-D · A CAPA E AS FOTOS

- **Célula LATERAL nunca inverte** (foto_fit) — chamada com textos AO
  LADO da foto só aceita plano lateral/abraço; o misto empilhava o
  título no vão e deitava a foto embaixo (o Kolynos da capa).
- **Largura das chamadas 168→162** — o texto entrava 6 px na zona de
  foto da vizinha (desenhada depois, cobria o fim).
- **O Fio desenha ANTES da foto** — o filete é separador de fundo,
  não risco por cima do produto.

### O banco real (backup `core_pre_v2_20260803.db`)

42 marcas gravadas (nominal); higienização cirúrgica nomeada pelo
dono: "Leite em Pó Ninho…", "Sabão em Pó Omo…", "Wafer Bulnez…",
"Detg. Limpol…", o " T1 " dos Arroz (ids 81/82) e o peso 1,6→1,5 do
Kitubaina (id 71 — o erro de OCR confirmado). Pacote reimportado
(8 chaves, upsert). Prova recomposta: **0 sem foto, 0 avisos, 0
sobras nas 2 páginas** — o Arroz voltou a casar o conjunto após o T1.

### Ficou de fora (nomeado)

- "Todos"/"Ninho"/"3 Corações" fora do seed (ambíguas) — o Café e o
  Açúcar Todos ganham hierarquia quando o dono as puser na Config ou
  o acervo as aprender.
- A ordem travada nos nomes NOVOS de membro de família (hoje nasce
  "base + sabor" por compat; a reserva ordenada já casa as duas).
- Cascata da DICA por IA na composição (o default editorial cobre a
  degradação; gerar por IA segue no botão do editor).
- J8 (medição da desaceleração), J3/J4 e K5-K9 — como antes.
