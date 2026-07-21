# MAPA DETALHADO — Fases 4 a 12 (o resto da reta final)

> Escrito em 18/07/2026 pelo arquiteto, a pedido do Otaviano ("todas as
> fases em mão com extremo detalhe, até a finalização"). **Formato:** cada
> fase traz Por quê · Blocos com escopo fino · Decisões de arquitetura
> TRAVADAS · Testes-chave · Riscos. O **caderno literal de ~100 passos**
> de cada fase é emitido pelo arquiteto NO INÍCIO dela (governança do
> PLANO_PERFEITO — nasce informado pela reauditoria da fase anterior), mas
> aqui já está tudo que ele vai conter, sem surpresa. Fases 1–3 SELADAS.
> Intensidade Fable: F4 e F12 máxima; demais Alto. Chat novo por fase.
> I1–I5 e "exit 0 limpo" + inspeção visual de TODOS os artefatos valem.

---

## FASE 4 — Editor I: consertar e destravar (RG-55, RG-56, RG-54, RG-49)

**Por quê:** os bugs da segunda passada do dono moram aqui. "Clico no preço
e ele some/trava", "não sei agrupar nem desagrupar", "formatação errada nas
telas". Não se constrói ferramenta nova sobre seleção quebrada — esta fase
é 100% conserto e clareza. **Intensidade máxima.**

**Bloco A — Reproduzir e curar o preço que some (RG-55).** Instrumentar o
clique-grupo da Onda 3 com log; reproduzir com os prints da pasta "Outra
auditoria" (o dono clicou num preço numa célula agrupada e a região sumiu).
Hipótese registrada: conflito entre o colapso-no-release (RG-15) e o
z-order/seleção quando a região está sob outra ou tem rotação. Cura por
teste que reproduz o gesto exato → seleção sempre resolve para UMA região
válida, nunca None-que-esconde-o-painel. Decisão travada: **clicar numa
região SEMPRE a mostra no painel; agrupada ou não, o painel nunca fica
órfão.**

**Bloco B — Agrupar/desagrupar visível e reversível (RG-56).** Hoje o gesto
existe mas é invisível ("não sei como agrupa, e se errar não sei desfazer").
Menu de contexto SEMPRE mostra a ação pertinente: solto→"Agrupar como
replicável"; agrupado→"Desagrupar" + "Restaurar da mestra (N ajustes)";
cópia→"Restaurar da mestra". Badge visual de quem é mestre × cópia (âmbar
mestra, violeta override — já existe, tornar ÓBVIO com legenda no hover).
Microtutorial próprio de 3 telas do agrupamento (o conceito mais difícil do
app). Decisão travada: **todo estado agrupável tem seu inverso a um clique,
sempre no menu, nunca escondido.**

**Bloco C — Seções sem linha interna (RG-49).** O bug do "Bebidas" cortado:
runs de linhas CONTÍGUAS da mesma categoria desenham UM contorno de união
(sem borda entre linhas irmãs). Run de 1 célula não ganha caixa no estilo
contorno (só pill). Reusar `calcular_secoes` (é camada derivada — não toca
mapa); o conserto é geométrico no `desenhar_secoes`. Adversarial: seção
sobre N linhas não desenha divisória interna (prova por pixel na faixa entre
as linhas).

**Bloco D — Formatação das telas do editor (RG-54).** Aplicar a régua da
Fase 1 (mínimos por token, splitters com memória) especificamente no editor
e nos prints com defeito: painel de propriedades, réguas, barra de
ferramentas em 720p. Cada print da pasta "Outra auditoria" vira um "antes→
depois" no caderno.

**Bloco E — Ferramentas de organização base.** R-025/026 (raio-x textual da
célula), R-027 (guias arrastáveis das réguas), R-028 (grade magnética
on/off), R-029 (zoom-para-seleção + 100%/Ajustar sempre visíveis), R-039
(cadeado explícito da arte), R-040 (modo raio-x só-regiões), R-041 (medidas
ao vivo + empurrar com setas 1mm/0,1mm Shift).

**Testes-chave:** clique-grupo resolve seleção única (reproduz o bug e prova
a cura); desagrupar devolve exatamente o estado anterior por conteúdo;
adversarial da seção-união; mínimos de layout no editor a 720p. **Riscos:**
o RG-55 pode ter causa múltipla (z-order + rotação + colapso) — instrumentar
ANTES de teorizar; adversarial do vínculo re-rodado (mexe em seleção/região).

---

## FASE 5 — Editor II: ferramentas de profissional (R-030–048, RG-57/R-153)

**Por quê:** é o "Illustrator do tabloide" que o dono imaginou. Com a
seleção consertada (F4), agora as ferramentas ricas.

**Bloco A — Campos de texto especiais com clareza total (RG-57/R-153).** O
dono: "como seleciono que aquele campo é pra Fica a Dica ou pra validade?".
Ao criar uma região de texto, um diálogo NOMEADO com prévia: "Aviso legal" ·
"Validade da oferta (de/até)" · "Fica a Dica (a IA escreve)" · "Texto
livre". A região carrega um BADGE visível no editor dizendo seu papel. O
`texto_fixo`/`texto_legal`/preset da região deixa de ser campo oculto e vira
escolha explícita. Decisão travada: **toda região TEXTO_LEGAL declara seu
papel na criação e o exibe como badge — nunca mais um campo mudo.**

**Bloco B — Imagem dentro da região.** R-036 (máscara de forma: círculo/
cantos arredondados — o doc C6, pendência antiga), R-037 (enquadrar: pan/
zoom da foto no slot), R-038 (arrastar arquivo sobre a célula troca a foto),
R-032 (centralizar na caixa da arte com 1 clique), R-035 (pill de fundo
atrás do nome), R-034 (sombra/contorno de texto para legibilidade sobre
foto).

**Bloco C — Estilo e reuso.** R-031 (conta-gotas de estilo copia/cola entre
regiões), R-048 (templates de célula salvos — trios prontos para carimbar em
qualquer arte), R-043 (salvar-como-novo-layout do editor), R-044 (célula
vitrine/herói com estilo de fábrica), R-045 (reflow: nome maior empurra o
preço com harmonia).

**Bloco D — Páginas e visão.** R-030 (miniaturas laterais das páginas,
arrastáveis para reordenar), R-042 (histórico de desfazer VISUAL com
miniaturas), R-046 (prévia de impressão com margens/sangria), R-047
(verificador de contraste: aviso de branco sobre foto clara), R-033
(distribuir por espaçamento fixo em mm).

**Testes-chave:** criar região→escolher papel→badge correto→compõe o texto
certo; máscara circular por pixel; conta-gotas replica estilo sem tocar
geometria; template de célula carimba idêntico. **Riscos:** máscara não-
retangular toca o compositor (adversarial do vínculo re-rodado); RG-57
mexe no modelo da região (migração de layout antigo testada).

---

## FASE 6 — Mesa I: a bancada arrumada (RG-53, R-051/054/055/057/061/020/017)

**Por quê:** a Mesa é onde a semana acontece; "botões se comendo" e estante
engessada custam minutos todo dia.

**Bloco A — Barra reorganizada (RG-53).** Já iniciada na Fase 1 (o "···"),
agora consolidada: barra em dois níveis OU lateral compacta; agrupamento
lógico (Importar · Montar · Salvar/Exportar · Navegar páginas); nada nunca
espremido em nenhuma largura.

**Bloco B — Estante viva.** R-051 (modo planilha: editar nome/preço/
categoria em grade com Tab/Enter — o pedido de "editar tudo de uma vez"),
R-054 (filtros: sem foto · sem preço · por categoria), R-055 (reordenar
arrastando — a mão manda, o mapa respeita por uid), R-057 (trocar dois itens
de célula arrastando um sobre o outro — I1: troca de uid no mapa, não de
posição). R-069 (duplicar item na estante), R-020 (estados vazios com ação).

**Bloco C — Segurança do trabalho.** R-061 (rascunho automático a cada 2 min
— queda de luz nunca leva trabalho; grava snapshot silencioso), R-017 (Ctrl+K
global também na Mesa).

**Testes-chave:** modo planilha edita 3 campos por teclado e persiste; trocar
células por arrasto conserva o trio por conteúdo (adversarial); rascunho
automático restaura após "queda" simulada. **Riscos:** R-055/057 tocam o
mapa slot→uid — adversarial do vínculo é o juiz; modo planilha não pode
brigar com o override por slot (F7.3).

---

## FASE 7 — Mesa II: produção em massa (R-049/050/052/053/056/058/059/060/062/063/070/071/072)

**Por quê:** "importar tudo de uma vez para otimizar o tempo" — o dono pediu
DUAS vezes. A pesquisa (§4) confirmou que "dados primeiro, fotos depois" é o
fluxo canônico da indústria. Esta fase o consolida.

**Bloco A — Entrada em massa.** R-049 (multi-arquivo: várias fotos/tabelas
de uma vez, fila única), R-050 (Ctrl+V inteligente: colar tabela do WhatsApp
Web/Excel direto na Mesa — parse de texto colado), R-052 (conciliação em
tela cheia com a FOTO ORIGINAL ao lado — conferência visual do OCR, radar
antigo).

**Bloco B — Decisão em lote.** R-053 (aceitar todos os verdes de uma vez,
revisar só amarelos), R-056 ("encher a página": distribui o que couber e
pergunta o destino do resto), R-070 (multi-preço "3 por R$10,00" como
formato), R-071 (observação por item "limite 2 por cliente" com região
própria).

**Bloco C — Conferência e memória.** R-058 (banco de frases prontas com
{data}/{evento}), R-059 (alerta de repetição "entrou 3 semanas seguidas"),
R-060 (medidor de densidade da página — pesquisa §1), R-062 (comparar com a
edição anterior: diff de preços e itens), R-063 (checklist final imprimível),
R-072 (estatística da montagem: tempo por edição).

**Testes-chave:** multi-import enfileira N arquivos sem perder nenhum; Ctrl+V
parseia tabela colada; "aceitar verdes" resolve só os verdes; diff acha
preço mudado entre edições. **Riscos:** Ctrl+V inteligente precisa de parser
robusto (reusa o P0.3 de preço + a regra dura RG-20 de nome); tela cheia da
conciliação não pode regredir o fluxo existente.

---

## FASE 8 — Exportação e publicação (R-064/065/066/067/068 + R-139/140/141/142/145)

**Por quê:** o tabloide nasce para o WhatsApp — o caminho até lá tem que ser
de um gesto. E o dono sonha além do PNG (Stories, carrossel, vídeo).

**Bloco A — Exportar bem.** R-065 (perfis: WhatsApp 1080 · Impressão 300dpi ·
Stories 1080×1920 — presets de resolução/formato), R-064 (compartilhar
direto: o PNG vai para a conversa — no Windows, abrir o WhatsApp com o
arquivo ou copiar para a área de transferência como imagem), R-066 (fila de
exportação de vários projetos em lote), R-067 (marca d'água RASCUNHO
automática até aprovação), R-068 (aprovação em 2 etapas: montou→conferiu).

**Bloco B — Além do encarte.** R-141 (Oferta do Dia: post único de destaque),
R-140 (carrossel Instagram: 1 card por produto do mesmo projeto), R-139
(Stories/Reels 1080×1920 com animação leve do preço → MP4), R-142 (vídeo-
tabloide: slideshow MP4 das páginas para o Status), R-145 (faixas/banners de
loja em formatos grandes no mesmo pipeline).

**Decisão de arquitetura:** os formatos sociais REUSAM o compositor (é só
outro LayoutDef com outra proporção + a mesma cadeia produto→slot); o MP4
sai via ffmpeg/imageio (dependência a confirmar; degradar com aviso se
ausente). Nada de motor de vídeo pesado.

**Testes-chave:** cada perfil exporta na resolução certa (pypdf/PIL medindo);
RASCUNHO some após aprovação; carrossel gera N cards; MP4 tem N frames.
**Riscos:** compartilhar-no-WhatsApp depende do SO (documentar limitação; o
mínimo garantido é "copiar imagem" + "abrir pasta"); MP4 é opcional.

---

## FASE 9 — Conteúdo & IA II (R-073/074/075/076/077/078/081/082/083/085/086/087/089/090)

**Por quê:** a IA vira colega de trabalho — proativa, revisora, sem
alucinar. Tudo local (LM Studio/Ollama), respeitando o veto de recursos que
o dono cortou.

**Bloco A — IA que ajuda a montar.** R-073 (chat da oferta: "monta o Quintou
com estas 20 linhas" → rascunho para ajustar — reusa conciliação+enriquecer
em lote), R-074 (manchete sugerida), R-083 (Fica-a-Dica com estilos: receita/
economia/curiosidade + memória do que já saiu — evita repetir).

**Bloco B — IA que protege.** R-081 (IA revisora do export: "lê" a peça
pronta e aponta preço trocado/nome cortado — usa o modelo de visão sobre o
PNG final), R-078 (sentinela de preço estranho: "R$79 num sabonete?"), R-085
(avaliador de foto: borrada/pequena/marca-d'água → aviso na escolha), R-075
(caça-duplicatas do acervo com fusão assistida).

**Bloco C — IA que aprende.** R-076 (dicionário de typos do fornecedor —
aprende "Huppers" ao confirmar 1×), R-077 (expansor de siglas com
aprendizado), R-086 (sinônimos regionais mandioca/macaxeira/aipim), R-087
(marca extraída do nome), R-082 (autodetecção de variações: sugere agrupar
sabores). R-089 (fila de IA com prioridade), R-090 (status da IA em
linguagem simples — já iniciado na F3, completar).

**Testes-chave:** revisora aponta um preço deliberadamente trocado; caça-
duplicatas funde por chave natural (I1, byte a byte nas fotos); typo
aprendido persiste como alias. **Riscos:** IA revisora é o item mais
ambicioso — se o modelo de visão local não der conta, degrada para
checagens heurísticas COM aviso; nunca bloqueia o export.

---

## FASE 10 — Imagens II + Estúdio IA (R-091/094/095/096/097/098/099/100/101/102/103/104 + RG-46)

**Por quê:** a foto é 60% do encarte (pesquisa §1) e o acervo é patrimônio.
Aqui entra o sonho do dono: foto de celular → packshot bonito.

**Bloco A — Estúdio IA (RG-46/R-091).** Foto física → packshot. Fase por
degraus: (1) SEM IA generativa — rembg + normalização de luz/níveis + sombra
sintética (resolve 80%, roda em qualquer PC); (2) COM img2img local (SDXL/
ComfyUI, denoise 0,4–0,6) SE a GPU do dono permitir — confirmar VRAM na
abertura da fase (pesquisa §6). Flag experimental "Estúdio IA" nas
Configurações. Decisão travada: **o caminho sem-IA é o padrão garantido; o
generativo é opção condicionada ao hardware, nunca requisito.**

**Bloco B — Curadoria melhor.** R-094 (girar/cortar/espelhar antes de
salvar), R-103 (pincel de refino do recorte: restaurar/apagar borda do
rembg), R-095 (detector de fundo-branco: pula rembg — só a chave veio na F3,
implementar), R-096 (busca em abas Web · Meu acervo), R-097 (foto favorita/
oficial), R-098 (comparador de versões lado a lado).

**Bloco C — Acervo saudável.** R-100 (compressão WebP — metade do disco),
R-101 (upscale sob demanda pela resolução-alvo da célula — nem mais nem
menos), R-102 (sombra projetada por tema), R-104 (alerta de foto repetida na
edição), R-099 (pacote offline de genéricas por categoria).

**Testes-chave:** Estúdio-sem-IA gera packshot com fundo limpo + sombra
(por pixel); WebP reduz tamanho mantendo aparência; upscale mira a resolução
da célula. **Riscos:** img2img local é o maior risco de hardware — a decisão
de degradar está travada; RG-46 NÃO bloqueia a fase se a GPU não der.

---

## FASE 11 — Cartaz & Fábrica + inteligência do negócio (R-105–114 + R-115–123 + R-126)

**Por quê:** o cartaz de gôndola é metade do negócio (e o dono não o testou
a fundo ainda); e a inteligência de preço/histórico é serviço direto a ele.

**Bloco A — Cartaz completo.** R-105 (biblioteca de layouts de cartaz: A4
retrato/paisagem, meia folha, etiqueta), R-107 (preço gigante autoajustado —
legível a 5 metros), R-109 (de/por com % de desconto calculada), R-110
(cartaz-relâmpago: do Almoxarifado ao PDF em 1 clique no produto), R-111
(validade discreta no rodapé para caçar cartaz vencido), R-113 (kit ponta-de-
gôndola: cartaz + etiquetas do mesmo item), R-114 (QR opcional).

**Bloco B — Impressão.** R-106 (2-em-1: dois A5 por A4 economizando papel —
ATENÇÃO: é imposição controlada, não NUP no tabloide; só no cartaz e só se o
dono ligar), R-108 (lote por categoria: imprimir só o açougue), R-112
(imprimir direto na fila da impressora).

**Bloco C — Inteligência (só leitura, sem os vetos).** R-115 (histórico de
preço por produto com gráfico "menor preço do ano"), R-117 (relatório da
edição: itens por categoria, distribuição de preços), R-118 (exportar/
importar acervo em Excel — ponte universal), R-120 (ranking dos mais
ofertados), R-121 (memória sazonal "ano passado nesta semana"), R-122 (meta
por evento), R-123 (alerta de preço divergente do mesmo produto entre
páginas), R-126 (saúde do acervo com metas). **Lembrete: R-116/124/125/119
foram VETADOS ou são futuro — não construir custo/margem/diário/ERP.**

**Testes-chave:** cartaz-relâmpago gera PDF no tamanho exato (pypdf); % de
desconto correta; histórico de preço reflete as edições; Excel ida-e-volta
preserva o acervo. **Riscos:** o 2-em-1 é imposição — testar tamanho físico
com rigor; Excel import reusa a disciplina de chave natural (I1).

---

## FASE 12 — Confiabilidade, MARCO FINAL e entrega (R-127/131/136/137/138/144/147/148/149/150 + RG-48/58 + Bloco G)

**Por quê:** fechar tudo, provar tudo, instalar no PC do mercado. É a fase
da aceitação do dono e do empacotamento. **Intensidade máxima.**

**Bloco A — Robustez final.** R-137 (recuperação de projeto corrompido do
último snapshot bom), R-131 (modo somente-leitura para o PC da loja), R-136
(exportar projeto como .atproj único), R-127 (auto-atualização com novidades
em PT-BR — ou, se offline, "verificar atualização" manual).

**Bloco B — Sonhos finais.** R-144 (etiquetas de prateleira em lote — dezenas
por folha), R-147 (gerador de artes de fundo por IA para datas comemorativas
— experimental, condicionado à GPU como o RG-46), R-148 (calendário
promocional anual: Páscoa/São João/Black Friday com lembretes e kits), R-149
(exportar layout como template compartilhável sem dados — presente para
outro mercado), R-150 ("Modo Pai": visão simplificada de aprovar e imprimir,
à prova de erro — o dono mencionou o pai várias vezes).

**Bloco C — O MARCO REFEITO (RG-48/RG-58).** O Sexta Verde com LAYOUT REAL
desenhado sobre a arte (células nos balões verdes, sem grade sintética),
"até" nunca vazio, inspeção visual total do arquiteto. Re-rodar o marco dos
~40 com as TRÊS campanhas reais + performance ≥5k. Este é o teste de
aceitação: o dono monta uma edição de verdade e aprova.

**Bloco D — Bloco G (entrega).** Instalador Windows (PyInstaller), primeira
execução, migração de assets da versão anterior, guia rápido em PT-BR +
checklist de instalação do LM Studio/modelos. O programa no PC do mercado.

**Testes-chave:** recuperação restaura projeto corrompido; .atproj ida-e-
volta idêntico; instalador migra sem perder acervo; o MARCO com Sexta Verde
REAL inspecionado peça a peça. **Riscos:** empacotamento com rembg/onnx/
torch é pesado (testar o instalador num Windows limpo); o marco só fecha com
o SELO HUMANO do Otaviano — é o fim da construção.

---

## Ordem de execução e governança (relembrando)

Uma fase por vez, chat novo por fase, caderno literal de ~100 passos emitido
no início de cada uma (este mapa é o esqueleto — o caderno é a carne fina).
Reauditoria com inspeção visual de TODOS os artefatos ao fim de cada fase.
Achado novo entra no dossiê com número RG. O selo final do programa é do
Otaviano, sobre o marco da Fase 12. Depois dele: só manutenção e os sonhos
que o dono marcar dos que ficaram no radar. **É o fim da estrada — e o
começo das quintas-feiras de manhã em que o tabloide é um clique.**
