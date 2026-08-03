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
