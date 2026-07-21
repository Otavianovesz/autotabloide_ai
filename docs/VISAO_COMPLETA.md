# AutoTabloide AI — Visão Completa e Casos de Uso

> **Para quem programa (Claude Code):** este documento é a **referência-mãe da visão** do Otaviano — consolidada de tudo que ele imaginou, falou (áudios), anotou e decidiu ao longo do projeto. Leia-o junto com `CLAUDE.md` (decisões travadas) e `docs/PLANO_DE_CONSTRUCAO.md` (estado atual). O objetivo aqui não é só "o que fazer", mas **entender a cabeça dele para antecipar cada caso de uso e ir além** — construir prevendo o que ele vai precisar antes de ele pedir.
>
> Fale sempre **PT-BR**. O Otaviano é estudante de medicina, autor do projeto, **não é programador** — usa IA para programar. Seja didático; valide cada etapa com um caso real dele (a fixture do Belo Brasil e a arte real são o padrão-ouro).

---

## 1. Quem é o usuário e qual a dor

O Otaviano faz o material gráfico de ofertas do supermercado da família (**Belo Brasil Supermercados**). Hoje ele faz **tudo na mão no Adobe Illustrator**, e é um trabalho repetitivo que ele quer automatizar para que "a minha função aqui seja automatizada".

**O fluxo real do dia a dia (nas palavras dele):**
1. Num grupo de WhatsApp, alguém do mercado (o pai ou uma funcionária) manda uma **foto/print** de um documento Word com as ofertas — nomes e preços, muitas vezes **escritos errado e fora de padrão** ("DE SODORANTE", "OLE O de SOJA", lixo de OCR, duas marcas juntas).
2. Ele lê item por item, vê o que mudou de preço, o que é novo, e **padroniza o nome na cabeça**.
3. Ele **pesquisa a imagem no Google**, escolhe uma decente, baixa, **tira o fundo** e recorta.
4. Monta no Illustrator (coloca imagem, nome, preço nos espaços), exporta **PNG** e manda no WhatsApp.
5. Muda a data da oferta.

Cada passo acima usa **a inteligência dele** — é isso que a IA do app automatiza. O programa tem que fazer esse caminho inteiro, rápido, deixando para ele só a conferência e o capricho.

**Princípio que atravessa tudo (dito por ele várias vezes):** ele quer participar, quer **flexibilidade/DIY** ("quase tudo personalizável"), quer **qualidade de vida** (botão direito, atalhos, botões que fazem sozinho), e quer que fique **bonito** — nível de produto profissional, não engessado.

---

## 2. A visão em uma frase

Um **app desktop offline (Windows)** que transforma uma tabela/foto de ofertas num **tabloide** (encarte) ou em **cartazes de gôndola** prontos, automatizando OCR, padronização de nomes, busca e tratamento de imagem, e a montagem sobre a arte que ele desenha no Illustrator — com um **editor visual estilo Canva** próprio.

**Dois produtos, um app, back-end compartilhado:**
- **Tabloide** — encarte com vários produtos numa grade, para WhatsApp/Instagram (às vezes impresso). Saída PNG/PDF, 1+ páginas.
- **Cartaz de gôndola** — a etiqueta na prateleira, com preço "de"/"por". Saída PDF, 1 item por página, tamanho exato para impressão.

---

## 3. O fluxo completo automatizado (com TODAS as nuances)

### 3.1. Entrada e OCR
- A oferta chega como **foto/print do WhatsApp** (um Word fotografado) ou como **planilha** (Excel/CSV/tabela do sistema).
- Da foto, a **IA de visão (OCR)** extrai a tabela `{descrição, preço}`. Ela precisa lidar com: preços em formato diferente (ex.: "`<> R$ 17,71`" marcado como "S. OFERTA"), a coluna de numeração da linha (não confundir com preço), cores das linhas (ignorar), e capturar o rodapé de **validade da oferta** ("OFERTAS VÁLIDAS 01/07 ATÉ 27/07").
- O OCR **não precisa ser perfeito** — a conciliação absorve o ruído (provado: 42/42 produtos certos mesmo com erros de OCR).

### 3.2. Conciliação com o banco (o "semáforo")
- **Importa-se a tabela inteira, sempre** (sem diff com o dia anterior — mais simples, menos erro). Só cria os itens novos.
- Cada item é conciliado com o banco em **3 camadas**: embeddings (significado) → fuzzy (texto) → IA juiz (só nos ambíguos, com poucos candidatos, nunca o banco todo).
- **Semáforo:** 🟢 verde (existe), 🟡 amarelo (a IA achou provável, confira), 🔴 vermelho (novo). O usuário aprova/corrige/cria. Só avança quando tudo está verde.
- Cada correção humana vira **alias** — o banco fica mais esperto com o tempo (aprende como aquela loja escreve).

### 3.3. Sanitização + enriquecimento do nome
- **Padrão do nome:** Tipo + Marca + Sabor + Peso. Primeira letra maiúscula, resto minúsculo. Unidades minúsculas (g, kg, ml) **exceto L**. Número colado à unidade (500g, 1kg, 2L). Siglas configuráveis (ex.: TP = Tetra Pak em maiúsculo). **Tudo configurável.**
- Parte **determinística** (regras: caixa, unidade, ordem básica) + parte **semântica pela IA** (consertar "DE SODORANTE"→Desodorante, "OLE O"→Óleo, pôr acentos, reordenar, separar 2 marcas, categorizar, marcar +18). A IA faz o entendimento; as regras garantem a formatação sempre certa.

### 3.4. Imagem do produto
- **Busca na internet** (backend **ddgs/DuckDuckGo**, região BR; a query usa o nome enriquecido **sem o peso/unidade**). Retorna candidatos relevantes de sites de varejo BR.
- **Curadoria:** o auto-pick pega o 1º; mas o usuário **escolhe** a foto certa num pop-up (essencial quando o auto-pick erra — ex.: sabão em pó). Ele também pode **colar/arquivo/URL/arrastar** a própria imagem.
- **Tratamento:** remoção de fundo (rembg birefnet-general) → recorte no conteúdo → normalização. Upscale condicional (Real-ESRGAN) para fotos ruins e cartazes grandes.
- As imagens ficam **em disco** (não no banco); o banco guarda o caminho + **histórico de versões** (a anterior não é apagada ao trocar).

### 3.5. Montagem e exportação
- O produto (nome, preço, imagem, selos) é composto sobre a **arte de fundo** (imagem do Illustrator), na **grade** do layout. O app desenha só as camadas dinâmicas — a arte decorativa vem pronta do Illustrator, com fidelidade total (WYSIWYG).
- Confere, ajusta, exporta. Tabloide → PNG/PDF (RGB padrão). Cartaz → PDF multipágina, 1 item/página, **tamanho exato**.

---

## 4. O motor visual — nuances essenciais (o coração)

- **Camadas** (de baixo p/ cima): fundo/arte → realces → grade de slots → faixas de categoria → textos legais. Dentro de cada célula: fundo do slot → imagem(ns) → textos → preço. **Ordem personalizável.**
- **Grade E agrupamento livre:** nem todo tabloide é grade regular. Marca-se a **célula-mestre uma vez** e replica; a grade pode ser auto-detectada da arte (as caixas de preço vermelhas). Também há agrupamento livre para layouts irregulares. Sempre com **auxílio de alinhamento** (snapping, alinhar, distribuir).
- **Regiões nomeadas** no slot: `[IMAGEM]`, `[NOME]`, `[UNIDADE]`, `[PREÇO]`, `[SELO]`.
- **Preço:** dois modos — **separado** (inteiro grande + centavos pequenos) e **completo** (R$ 19,90 corrido). Papel **de/por** (cartaz), com o "de" podendo vir **riscado**. Importante: **o "R$" e a caixa podem ser da arte** — nesse caso o app desenha **só o número** (`mostrar_moeda` desligado). Criar parâmetro que distingue o slot de preço-antigo do preço-novo (para nunca trocar).
- **Nome:** quebra de linha **com hífen**; ajuste de fonte que **só reduz, nunca aumenta**; alinhamentos (esquerda/centro/direita/justificado). **Unidade dentro/fora do nome**: se o slot não tem região `[UNIDADE]`, a medida é anexada ao nome; se tem, sai do nome.
- **Fontes:** seletor livre (bundled + do sistema); a fonte do encarte dele é **Quicksand**. Estilos reutilizáveis, com override por instância.
- **Selos:** **+18 automático** em bebida alcoólica (canto sup. esquerdo, configurável); **"Qualidade Belo Brasil"** quando é marca própria do mercado. Vários selos podem coexistir.
- **Texto legal / validade:** campo repetível fora dos slots (datas, validade da oferta, "beba com moderação"), editável ao abrir. A validade capturada no OCR alimenta esse campo.
- **Máscara de imagem:** padrão retângulo; **círculo/forma opcional** (raro — pendente).
- **Múltiplas páginas:** um layout pode ter 1+ páginas (jornais têm 1–2, aberto a mais); auto-flow quando os itens excedem. Também prever o caso de **feed de Instagram** (muitas páginas com poucos itens cada).

---

## 5. As telas (fluxos e pop-ups)

- **Dashboard (inicial):** histórico e **projetos salvos em pastas por evento** (ex.: "Terça do Pão" — cada edição por data, com layout e imagens congelados; copiar uma antiga para fazer a nova). Status de produção.
- **Ateliê (layouts):** grid de layouts; importar a arte de fundo e **marcar grade/slots**; editar nome/duplicar/excluir; tipo de mídia. O usuário define **manualmente** se é tabloide ou cartaz e dá o nome (o app não adivinha).
- **Almoxarifado (estoque):** lista virtualizada (lazy loading, libera itens fora de tela); editar preço/nome sanitizado; **semáforo de qualidade** e "Image Doctor"; painel de propriedades; botão direito.
- **Mesa (montagem do tabloide — a mais importante):** selecionar layout (pop-up de miniaturas, ou duplo-clique do Ateliê); **importar do banco** (pop-up com busca e **multi-seleção** — pesquisa "Coca", clica, pesquisa outro sem perder a seleção) **ou importar tabela/foto** (pop-up de **conciliação lado a lado** verde/amarelo/vermelho, com criação dos novos: sanitiza → busca imagem → escolhe → trata); **arrastar** para os slots **ou botão auto-preencher** (na ordem importada); **modal de override** (botão direito); painéis de camadas e propriedades; atalhos.
- **Fábrica (cartazes):** mesma conciliação; **preenche automático** (cada item = 1 folha); exige descrição + **preço "de" + preço "por"** (+peso/imagem quando o layout pedir); **validade do item** quando perto de vencer (só no cartaz); preview ao clicar; **exportar = PDF multipágina no tamanho exato** (sem imposição/NUP — imprime na folha designada).
- **Cofre:** backups, snapshots, **importar/exportar banco** (mesclar), modo seguro.
- **Configurações:** sem login/conta; padrões de sanitização, glossário de siglas, selos, escolha do modelo de IA (4/8-bit, trocar), atalhos.

**Qualidade de vida transversal (ele pede muito):** menu de **botão direito universal** (editar, override, trocar imagem, +18, duplicar, limpar, travar; no item: editar, duplicar, excluir, histórico); **desfazer/refazer** (Ctrl+Z / Ctrl+Shift+Z, histórico generoso em disco); copiar/colar entre slots; empacotar/importar projeto (os dois lados).

---

## 6. Casos avançados — "ir além", antecipando o uso

Estes são os casos que o Otaviano enfatizou como **importantes** e que separam um gerador cego de uma ferramenta de verdade:

1. **Vários sabores/fragrâncias num slot** (ex.: "Suco Tang, sabores"; "Giovanna Baby fragrâncias"): várias fotos no mesmo slot, dispostas em **leque sobreposto** (padrão), com orientação; o usuário **escolhe quais sabores** entram — a **IA sugere a partir do banco e ele aprova** (para ela **não alucinar** sabores). Ele pode tirar um sabor que não está na oferta.
2. **Dois produtos diferentes no mesmo preço** (ex.: Arroz Camil e Rei): duas fotos **lado a lado** (cada uma nítida, para ler que são dois itens), e **um texto combinado** ("Arroz Tipo 1 Camil e Rei 1kg") — montado pelo enriquecimento (`componentes`).
3. **Repetir a mesma foto** (ex.: triplicar o pacote de macarrão) para encher o slot e ficar bonito.
4. **Tabloide categorizado (o teste de aceitação final):** ~40 itens agrupados por **categoria** (Mercearia, Limpeza, Bebidas…), cada seção dentro de um **contorno** (ex.: 5 itens de Limpeza num contorno azul, com "Limpeza" escrito na linha). A IA categoriza; a grade agrupa. Pode exigir desenho custom além da edição comum. **Se esse caso roda, o programa inteiro está provado.**
5. **Preço especial "S. OFERTA"** ("`<> R$ 17,71`") — reconhecer e extrair certo.
6. **Item novo (vermelho)** — o fluxo de criação (sanitiza → imagem → cadastra) tem que ser fluido.
7. **Item sem imagem** — degrada sem quebrar (slot fica sem foto; o usuário resolve depois).
8. **Projeto congelado:** abrir um tabloide antigo mostra **exatamente** o preço/nome/imagem/gramatura da época. O banco é ponto de partida; **overrides por slot têm precedência**. Mudança de gramatura (90g→70g) é override.
9. **Portabilidade casa ↔ mercado:** exportar/importar banco + pasta de imagens + fontes, **sem criptografia**, com mesclagem (adiciona o que é novo).

Ao construir qualquer tela ou recurso, **pense**: "que ação do Otaviano isso gera depois? que exceção ele vai querer? como isso vira qualidade de vida?" — e já deixe previsto.

---

## 7. Decisões travadas (não violar)

- **Stack:** Python 3.12 + PySide6/Qt; SQLite síncrono + SQLAlchemy; sqlite-vec (embeddings); **IA local via LM Studio pela API padrão compatível-OpenAI** (trocável), modelos **Qwen3.5-9B (thinking off)** para texto+visão e **Qwen3-Embedding 0.6B**; rembg (birefnet-general), ddgs (DuckDuckGo) para busca, Real-ESRGAN para upscale; Ghostscript + pypdf na exportação.
- **Renderização NÃO é SVG rasterizado** (CairoSVG estraga sombra/gradiente). Arte de fundo = imagem do Illustrator; o app compõe as camadas dinâmicas com Pillow (export) e Qt (editor), lendo o **mesmo modelo em mm** → WYSIWYG. Layouts digitais podem ser em pixels (derivados da arte).
- **Flexibilidade/DIY** em tudo; **qualidade de vida** sempre; **simples e legível** (nem simplório, nem "industrial").
- **Sem:** criptografia pesada, módulo mobile/foto, kit campanha social, camada "industrial" de missão crítica (watchdog/RAG/resiliência) do protótipo antigo.
- **Cor:** RGB padrão (tabloide digital); CMYK opcional (cartaz impresso). Sem imposição NUP.

---

## 8. Estado atual da construção (jul/2026)

Reconstruído do zero em `app/` (árvore limpa). **Blocos A e B completos** (banco, sanitização, motor de composição em mm, IA de ponta a ponta com enriquecimento/conciliação/OCR, e imagens: busca ddgs/fundo/upscale/biblioteca/múltiplas/selos). **Bloco C (editor) até F5.5 núcleo** (canvas WYSIWYG, camadas, ferramentas de região, alinhamento, grade auto-detectada + slot→produto) + **sistema de design profissional aplicado** (tokens, shell, ícones, estados, toasts, command palette Ctrl+K). O programa já gera um **tabloide autêntico** da fixture real (nomes enriquecidos + imagens reais + preços na arte + selo +18).

**Próximos passos:** completar a F5.5 (propagação da célula-mestre + override por célula no editor) → F5.6–F5.10 → **Bloco D (as 6 telas)** herdando a casca nova → Bloco E (casos avançados) → **Bloco F (teste final: tabloide categorizado)** → Bloco G (instalador Windows).

> Detalhe de fluxo do projeto: o **Cowork (Claude) atua como arquiteto/auditor e comando**; o **Claude Code é o builder**. Ao fim de cada fase, o Code **lista o que ficou de fora**; o arquiteto **audita lendo o código e reabrindo o app na tela real**. Mantenha o `PLANO_DE_CONSTRUCAO.md` sempre atualizado — é a memória viva entre chats.
