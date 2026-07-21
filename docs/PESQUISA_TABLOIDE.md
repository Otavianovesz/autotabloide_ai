# A Ciência do Tabloide — pesquisa do arquiteto (RG-37/38/39, 17/07/2026)

> Pesquisa web + síntese, transformada em recomendações ACIONÁVEIS.
> Cada recomendação aponta a onda da REVISAO_GERAL onde entra. As novas
> ganham números RG-41..46 (apensadas ao dossiê).

## 1. Fundamentos de composição do encarte

- **Padrão Z de leitura**: destaques da semana no topo-esquerdo, ofertas
  premium no centro-direito, chamada final no rodapé-direito. O olho
  ocidental varre em Z — a capa deve ser montada nessa ordem.
- **Regra 60-30-10**: ~60% imagem de produto, 30% mensagem promocional,
  10% marca. Encarte moderno tende a grades mais LIMPAS, com respiro —
  menos fileiras entulhadas (o instinto do Otaviano de achar bordas
  "feias" e pedir organização é a tendência da indústria).
- **Capa com heróis**: itens mais procurados/agressivos na capa (âncora de
  tráfego) — prática brasileira explícita (hortifrúti/açougue baratíssimos
  na frente, como o Quintou faz com abóbora a 0,19).
- **Blocking por setor espelhando a LOJA**: distribuir as ofertas na ordem
  dos setores do mercado (hortifrúti → açougue → mercearia → limpeza…) —
  categorias adjacentes que combinam (massa ao lado de molho) estimulam
  compra conjunta.
- **Imagens REAIS dos produtos vendidos** (não genéricas) constroem
  confiança — valida o pipeline de packshot próprio do app.

## 2. Ciência da atenção (eye-tracking)

- Compradores fixam o PREÇO em ~62% das considerações — o preço é
  protagonista, não detalhe: caixas de preço grandes e legíveis são
  cientificamente corretas.
- Atenção cai conforme o produto se afasta do "nível do olho" — no papel,
  o equivalente é o terço superior e o centro: os heróis moram ali.
- Marca + produto lideram a atenção; rótulos e posição explicam o resto —
  nome limpo (a sanitização) e foto boa importam mais que enfeite.

## 3. Psicologia de preço

- **Terminação em 9 (charm pricing)**: ~24% de aumento médio de vendas nos
  estudos; 60,7% dos preços de varejo terminam em 9 (28,6% em 5). O efeito
  é MAIS FORTE com preço "de" riscado ao lado do "por" — exatamente o
  recurso que o app já tem no cartaz; levar o par de/por como opção também
  ao tabloide.
- **Efeito do dígito esquerdo**: 39,90 é "trinta e alguma coisa"; 40,00 é
  "quarenta". Sugerir (nunca impor) terminações ,99/,98/,90 na edição de
  preço é serviço ao dono.
- **Âncora**: apresentar o valor cheio antes do promocional aumenta a
  percepção de desconto — reforça o "de/por" e o selo de urgência
  ("Só Hoje" do Quintou é âncora temporal correta).

## 4. Fluxo de produção em massa (como a indústria faz)

Ferramentas líderes (LAGO, Pagination, InBetween, Relayter) operam TODAS no
mesmo desenho: **dados primeiro** (PIM/planilha de ofertas) → template
inteligente → geração em lote → ajuste fino manual → saída. Imagens vêm de
um **DAM** (biblioteca de packshots) pré-tratada, nunca buscadas na hora.
O AutoTabloide já é essa arquitetura em miniatura (banco = PIM; biblioteca
de imagens = DAM; layout = template; Mesa = geração+ajuste) — a conclusão
do benchmark é que o RG-03 ("editar tudo primeiro, fotos depois em lote") é
o fluxo canônico da indústria e deve virar o caminho feliz, com a busca
na-hora como exceção, não regra.

## 5. Fontes de imagem melhores que busca solta (a descoberta da pesquisa)

- **Open Food Facts**: base ABERTA de produtos alimentícios com fotos, API
  **sem chave e sem limite**, consultável por **código de barras (EAN)**;
  URLs de imagem deriváveis do EAN (com versão 400px). Produtos BR estão
  lá (a comunidade brasileira é ativa).
- **Cosmos (Bluesoft)**: base BRASILEIRA por GTIN/EAN com descrição e
  imagem — API com limites/planos (avaliar o gratuito).
- **Recomendação estrutural (RG-41)**: produto ganha campo **EAN** e a
  busca de imagem vira CASCATA: 1º EAN→Open Food Facts (packshot oficial,
  fundo já limpo), 2º Cosmos se configurado, 3º ddgs como hoje. O EAN pode
  vir da tabela de ofertas (muitos fornecedores mandam) ou digitado no
  Almoxarifado. Mata o problema "Ben 10 para coco ralado" na raiz para
  alimentos, e o strip de marca própria (RG-30) cobre o resto.

## 6. Foto física → packshot com IA local (RG-27/39)

Viável em 2026 com GPU de consumo: SDXL roda em ~12 GB de VRAM; FLUX em
FP8 idem; ComfyUI é o padrão de pipeline (remoção de fundo por segmentação
→ cena/iluminação → refinamento img2img com denoise 0,4–0,6 → acabamento) e
o fluxo é empacotável num JSON reproduzível. **Recomendação**: fase
EXPERIMENTAL pós-marco (flag nas Configurações, "Estúdio IA"), começando
pelo caminho simples que já resolve 80% — rembg + normalização de luz/
níveis + sombra sintética (sem IA generativa) — e o img2img como evolução,
condicionado à GPU do PC do Otaviano (a confirmar VRAM na Onda 6).

## 7. Recomendações novas (apensadas ao dossiê como RG-41..46)

- **RG-41 (Onda 4)** Campo EAN no produto + cascata de imagem
  EAN→OFF→(Cosmos)→ddgs; EAN aceito na tabela importada.
- **RG-42 (Onda 5)** Presets de composição do tabloide: "capa com heróis"
  (itens mais baratos/procurados no terço superior), guia Z opcional no
  editor, e medidor de densidade por página (aviso de entulho).
- **RG-43 (Onda 5)** Assistente de preço: sugestão opcional de terminação
  (,99/,98/,90) na edição + par de/por riscado disponível no TABLOIDE
  (hoje só cartaz) — com o aviso PROCON de sempre.
- **RG-44 (Onda 4/5)** Preset de ordem de setores (hortifrúti, açougue,
  frios, mercearia, limpeza, bebidas, bazar) espelhando a loja — semente
  da config `categorias.ordem`, editável.
- **RG-45 (Onda 1 — confirma RG-03)** "Dados primeiro" como caminho feliz
  oficial: criar tudo sem foto em segundos, fila de fotos em lote depois.
- **RG-46 (pós-marco, experimental)** "Estúdio IA" para foto física →
  packshot (rembg+luz+sombra já; img2img ComfyUI/SDXL se a GPU permitir).

## Fontes

- [DesignWiz — Grocery flyers guide](https://designwiz.com/blog/grocery-showcase-flyers-guide-for-service-providers/) · [AdSpyder — Grocery ads best practices 2026](https://adspyder.io/blog/best-practices-for-grocery-ads/) · [IndoorMedia — Psychology tricks](https://www.indoormedia.com/blog/5-psychology-tricks-for-grocery-store-advertising/)
- [JR — Shoppers' price attention (eye-tracking)](https://ideas.repec.org/a/eee/jouret/v100y2024i3p439-455.html) · [ScienceDirect — Eye-tracking in retailing](https://www.sciencedirect.com/science/article/pii/S002243592400006X) · [PMC — Gaze path to purchase](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7546910/)
- [Stilo Arte — Diagramação de tabloides](https://www.stiloarte.com.br/diagramacao-tabloides-folhetos-ofertas/) · [Aliança — Como fazer tabloide de supermercado](https://aliancadistribuicao.com.br/como-fazer-um-tabloide-de-supermercado/) · [EconomizeBR — Panfleto de ofertas](https://www.economizebr.com/principal/criando-um-panfleto-de-ofertas/)
- [Wikipedia — Psychological pricing](https://en.wikipedia.org/wiki/Psychological_pricing) · [Capital One Shopping — Pricing stats](https://capitaloneshopping.com/research/pricing-psychology-statistics/) · [Price2Spy — Charm pricing](https://www.price2spy.com/blog/charm-pricing/)
- [Pagination — InDesign automation](https://pagination.com/indesign-automation/) · [Comosoft LAGO](https://www.comosoft.eu/software-solutions/print-publishing/) · [InBetween](https://inbetween.com/en/product-indesign-plugin/) · [The Grocer — Creative automation](https://www.thegrocer.co.uk/promotional-features/how-creative-automation-can-change-the-future-and-scale-of-retail-marketing/691370.article)
- [Open Food Facts — Data/API](https://world.openfoodfacts.org/data) · [OFF — Download de imagens](https://openfoodfacts.github.io/openfoodfacts-server/api/how-to-download-images/) · [Cosmos Bluesoft — API GTIN/EAN](https://cosmos.bluesoft.io/api)
- [DigitalApplied — Local image gen 2026 (Flux/SD/ComfyUI)](https://www.digitalapplied.com/blog/local-image-generation-flux-stable-diffusion-comfyui-2026) · [Hardwarepedia — Local AI 2026](https://hardwarepedia.com/blog/local-ai-image-video-generation-guide-2026)
