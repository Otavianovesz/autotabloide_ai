# 150 Recomendações do Arquiteto — aprimoramentos e novas funcionalidades

> Compiladas em 18/07/2026 a pedido do Otaviano. Dez temas, R-001 a R-150.
> Marque as que quiser: viram RG numerados e entram nas sessões/ordens.
> (As que já têm RG aberto estão marcadas com †.)

## A · Início & Organização (R-001–012)

- **R-001** Dashboard em painéis: "Produzir hoje" (pela agenda de campanhas), "Esta semana", atalhos grandes. †RG-50
- **R-002** Eventos como ABAS/cartões com cor e capa próprias (Terça do Pão, Quintou, Sexta Verde, Quinta do Peixe…). †RG-50
- **R-003** Agenda visual da semana (qua/qui/sex) com status por projeto: rascunho → pronto → exportado → publicado.
- **R-004** "Continuar de onde parei": reabre o último projeto com um clique no topo do Início.
- **R-005** Linha do tempo de versões por projeto (cada salvamento com miniatura; voltar no tempo).
- **R-006** Busca global no topo (projetos, produtos, layouts — um campo só).
- **R-007** Fixar projetos favoritos no topo do Início.
- **R-008** Lixeira com restauração: nada excluído some de verdade por 30 dias.
- **R-009** "Duplicar semana passada": clona a edição anterior e abre já pedindo só os preços novos — o gesto nº 1 do dia a dia.
- **R-010** Indicadores de saúde no Início: produtos sem foto, sem categoria, backup ok, IA ligada.
- **R-011** Modo apresentação (tela cheia das peças prontas — mostrar pro seu pai aprovar).
- **R-012** Notas rápidas por evento ("quinta que vem é feriado → antecipar").

## B · Aparência & UX geral (R-013–024)

- **R-013** Dark mode completo por tokens, com claro/escuro/automático. †RG-52
- **R-014** Configurações em abas específicas (Aparência · Campanhas · IA · Imagens · Selos · Sanitização · Backups · Atalhos). †RG-51
- **R-015** Escala da interface (100/125/150%) para qualquer monitor.
- **R-016** Barra da Mesa em dois níveis ou lateral compacta com estouro "···" — botões nunca espremidos. †RG-53
- **R-017** Paleta de comandos (Ctrl+K) em TODAS as telas, não só no editor.
- **R-018** Atalhos configuráveis + folha de cola imprimível.
- **R-019** Tour guiado refeito com mini-demonstrações animadas por tela.
- **R-020** Estados vazios sempre com botão-ação ("estante vazia → Importar agora").
- **R-021** Som/feedback sutil opcional ao fim de exportações longas.
- **R-022** Toast com "Desfazer" embutido (excluiu → desfaz ali mesmo).
- **R-023** Janela lembra tamanho, posição e última tela aberta.
- **R-024** Acessibilidade: alto contraste, fonte maior, navegação 100% por teclado.

## C · Editor (R-025–048)

- **R-025** Desagrupar com um clique + rótulo visível de quem é mestre de quê. †RG-56
- **R-026** Painel "Estrutura da célula": o trio + selos + overrides num raio-x textual.
- **R-027** Guias arrastáveis das réguas (como Illustrator), com trava.
- **R-028** Grade magnética configurável (exibir/ocultar, espaçamento em mm).
- **R-029** Zoom para seleção + botões 100%/Ajustar sempre visíveis.
- **R-030** Miniaturas laterais das páginas, arrastáveis para reordenar.
- **R-031** Conta-gotas de estilo: copiar/colar estilo entre regiões.
- **R-032** "Centralizar na caixa da arte": alinhar preço ao balão da arte com 1 clique.
- **R-033** Distribuir por espaçamento fixo (ex.: exatamente 4 mm entre nomes).
- **R-034** Sombra e contorno de texto configuráveis (legibilidade sobre foto).
- **R-035** Fundo de região opcional (pill de cor atrás do nome).
- **R-036** Máscara de forma na imagem (círculo/cantos arredondados — o doc C6).
- **R-037** Enquadrar a foto DENTRO da região (pan/zoom da imagem no slot).
- **R-038** Arrastar arquivo de imagem direto sobre a célula para trocar a foto.
- **R-039** Cadeado explícito da arte de fundo (intocável por padrão, destravável).
- **R-040** Modo raio-x: só as regiões, sem a arte (organizar rápido).
- **R-041** Medidas ao vivo na seleção + empurrar com setas (1 mm / 0,1 mm com Shift).
- **R-042** Histórico de desfazer VISUAL (lista com miniaturas de cada passo).
- **R-043** "Salvar como novo layout" direto do editor (variação sem medo).
- **R-044** Célula "vitrine" (herói) com estilo diferenciado de fábrica.
- **R-045** Reflow interno da célula: nome maior empurra o preço com harmonia.
- **R-046** Pré-visualização de impressão com margens e sangria.
- **R-047** Verificador de contraste (aviso: branco sobre foto clara).
- **R-048** Templates de célula salvos (trios prontos para carimbar em qualquer arte).

## D · Mesa & Fluxo de produção (R-049–072)

- **R-049** Importação multi-arquivo: várias fotos/tabelas de uma vez, fila única.
- **R-050** Ctrl+V inteligente na Mesa: colar tabela do WhatsApp Web/Excel direto.
- **R-051** Modo planilha da estante (editar nome/preço/categoria em grade, Tab/Enter).
- **R-052** Conciliação em tela cheia com a FOTO ORIGINAL ao lado (conferência visual).
- **R-053** "Aceitar todos os verdes" + revisar só amarelos, em um clique.
- **R-054** Filtros da estante: sem foto · sem preço · por categoria.
- **R-055** Reordenar a estante arrastando (a mão manda; o agrupar respeita).
- **R-056** "Encher a página": distribui o que couber e pergunta o destino do resto.
- **R-057** Trocar dois itens de célula arrastando um sobre o outro.
- **R-058** Banco de frases prontas (aviso legal, validade, chamadas) com variáveis {data}.
- **R-059** Alerta de repetição ("este item entrou 3 semanas seguidas").
- **R-060** Meta de itens por página com medidor visual de densidade. †RG-42
- **R-061** Rascunho automático a cada 2 min — queda de luz nunca leva trabalho.
- **R-062** Comparar com a edição anterior (diff de preços e itens).
- **R-063** Checklist final imprimível de conferência (preço a preço, com caixinhas).
- **R-064** Compartilhar direto no WhatsApp (o PNG cai na conversa do grupo).
- **R-065** Perfis de exportação: WhatsApp 1080 · Impressão 300 dpi · Stories 1080×1920.
- **R-066** Fila de exportação de vários projetos em lote.
- **R-067** Marca d'água "RASCUNHO" automática até a aprovação.
- **R-068** Aprovação em duas etapas (montou → conferiu) com registro de quem.
- **R-069** Duplicar item na estante (mesmo produto, dois preços — varejo/atacado).
- **R-070** Multi-preço por item ("3 por R$ 10,00" como formato de preço).
- **R-071** Observação por item ("limite 2 por cliente") com região própria no layout.
- **R-072** Estatística da montagem (tempo por edição — ver a própria evolução).

## E · Conteúdo & IA (R-073–090)

- **R-073** Chat da oferta: "monta o Quintou com estas 20 linhas" → rascunho completo para ajustar.
- **R-074** Manchete sugerida pela IA ("SEXTA VERDE: hortifrúti até 40% OFF").
- **R-075** Caça-duplicatas do acervo (mesmo produto 2×) com fusão assistida.
- **R-076** Dicionário de typos do fornecedor (aprende "Huppers" ao confirmar 1 vez).
- **R-077** Expansor de siglas com aprendizado (VD→vidro, PCT→pacote, TP→tetra pak).
- **R-078** Sentinela de preço estranho ("R$ 79,90 num sabonete — confirmar?").
- **R-079** Ditado por voz: falar os itens no microfone → estante pronta.
- **R-080** OCR de nota fiscal e pedido de compra (não só foto de tabela).
- **R-081** IA revisora do export: "lê" a peça pronta e aponta erros (preço trocado, nome cortado).
- **R-082** Autodetecção de variações: IA sugere agrupar sabores do mesmo produto.
- **R-083** Fica-a-Dica com estilos (receita · economia · curiosidade) e memória do que já saiu.
- **R-084** Nome curto automático para célula apertada (com prévia da quebra). †RG-22
- **R-085** Avaliador de foto (borrada/pequena/marca d'água → aviso na escolha).
- **R-086** Sinônimos regionais (mandioca/macaxeira/aipim) no glossário.
- **R-087** Marca extraída automaticamente do nome para o campo marca.
- **R-088** Prompt do Fica-a-Dica editável nas Configurações (a voz do mercado).
- **R-089** Fila de IA com prioridade: o que você espera passa na frente do lote.
- **R-090** Painel de status da IA (modelo carregado, fila, memória) em linguagem simples.

## F · Imagens (R-091–104)

- **R-091** Estúdio IA: foto de celular → packshot (recorte + luz + sombra; img2img local se a GPU der). †RG-46
- **R-092** Cadastrar por código de barras com webcam/celular (bipa → OFF → foto oficial). †RG-41
- **R-093** Acervo de imagens viajando no pacote casa↔loja com fusão inteligente.
- **R-094** Ajustes rápidos na curadoria (girar, cortar, espelhar) antes de salvar.
- **R-095** Detector de fundo-já-branco: pula o rembg quando não precisa (velocidade).
- **R-096** Busca em abas: Código de barras · Web · Meu acervo — lado a lado.
- **R-097** Foto favorita por produto (a "oficial" que sempre entra primeiro).
- **R-098** Comparador de versões de foto lado a lado no histórico.
- **R-099** Pacote offline de imagens genéricas de qualidade por categoria (hortifrúti etc.).
- **R-100** Compressão interna do acervo (WebP) — metade do disco, mesma cara.
- **R-101** Upscale sob demanda pela resolução-alvo da célula (nem mais, nem menos).
- **R-102** Sombra projetada configurável por tema do tabloide.
- **R-103** Refino manual do recorte (pincel restaurar/apagar borda do rembg).
- **R-104** Alerta de foto repetida entre itens da mesma edição.

## G · Cartaz & Fábrica (R-105–114)

- **R-105** Biblioteca de layouts de cartaz prontos (A4 retrato/paisagem, meia folha, etiqueta).
- **R-106** Modo folha 2-em-1 (dois A5 por A4) para economizar papel na impressão.
- **R-107** Preço gigante autoajustado (cartaz de vitrine legível a 5 metros).
- **R-108** Lote por categoria (imprimir só os cartazes do açougue).
- **R-109** "De/Por" com % de desconto calculada e exibível.
- **R-110** Cartaz-relâmpago: do Almoxarifado ao PDF em 10 segundos (1 clique no produto).
- **R-111** Data de validade discreta impressa no rodapé (caçar cartaz vencido na loja).
- **R-112** Imprimir direto (fila da impressora sem abrir o PDF).
- **R-113** Kit ponta-de-gôndola: cartaz + etiquetas menores do mesmo item, juntos.
- **R-114** QR code opcional (aponta pro WhatsApp/catálogo do mercado).

## H · Dados & Inteligência do negócio (R-115–126)

- **R-115** Histórico de preço por produto com gráfico ("menor preço do ano!").
- **R-116** Alerta de margem (oferta abaixo do custo, se o custo for informado).
- **R-117** Relatório da edição (itens por categoria, distribuição de preços).
- **R-118** Exportar/importar acervo em Excel (ponte com qualquer sistema).
- **R-119** Planilha-padrão de integração com ERP do mercado (futuro).
- **R-120** Ranking dos produtos mais ofertados (o hall da fama do tabloide).
- **R-121** Memória sazonal ("ano passado nesta semana você ofertou…").
- **R-122** Meta de ofertas por evento com acompanhamento.
- **R-123** Alerta de preço divergente do MESMO produto entre páginas da edição.
- **R-124** Campo custo (opcional, oculto) + margem calculada só para o dono.
- **R-125** Diário de alterações (quem mudou o quê, mesmo entre 2 PCs).
- **R-126** Saúde do acervo com metas (fotos 90%, EANs 60%, categorias 100%).

## I · Confiabilidade & Infra (R-127–138)

- **R-127** Auto-atualização do app com novidades em português.
- **R-128** "Gerar diagnóstico" (zip de logs) com 1 clique para suporte.
- **R-129** Verificador de integridade do acervo (fotos órfãs, pastas soltas) com correção.
- **R-130** Backup em nuvem opcional (Drive) além do Cofre local.
- **R-131** Modo somente-leitura (PC da loja abre sem risco de editar).
- **R-132** Perfil de máquina fraca (desliga upscale/IA pesada sozinho no PC do mercado).
- **R-133** Contador local de erros por função (prioriza o próximo conserto com dados).
- **R-134** "Verificar instalação" nas Configurações (teste de fumaça embutido).
- **R-135** Compactar banco com 1 clique (manutenção agendada).
- **R-136** Exportar projeto como arquivo único .atproj (mandar 1 arquivo pro outro PC).
- **R-137** Recuperação de projeto corrompido a partir do último snapshot bom.
- **R-138** Instalador que migra sozinho da versão anterior (Bloco G).

## J · Além do tabloide (R-139–150)

- **R-139** Stories/Reels 1080×1920 com animação leve do preço, exportado em MP4.
- **R-140** Carrossel de Instagram: 1 card por produto, gerados do mesmo projeto.
- **R-141** "Oferta do Dia": post único de destaque com template próprio.
- **R-142** Vídeo-tabloide: slideshow MP4 das páginas para o Status do WhatsApp.
- **R-143** Cardápio/tabela de preços fixa (açougue, padaria) — mesmo motor, novo produto.
- **R-144** Etiquetas de prateleira em lote (o cartaz em miniatura, dezenas por folha).
- **R-145** Faixas e banners de loja (formatos grandes no mesmo pipeline).
- **R-146** Multi-loja: mesmo acervo, preços por unidade (segunda loja no futuro).
- **R-147** Gerador de artes de fundo por IA para datas comemorativas (variações da identidade).
- **R-148** Calendário promocional anual (Páscoa, São João, Black Friday) com lembretes e kits.
- **R-149** Exportar layout como template compartilhável (sem dados — presente para outro mercado).
- **R-150** "Modo Pai": visão simplificada de aprovar e imprimir, à prova de erro.
