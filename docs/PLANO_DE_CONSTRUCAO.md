# Plano de Construção — AutoTabloide AI (v2, detalhado)

> Roadmap granular por blocos. Cada fase tem entregável e validação próprios. Construir de baixo para cima; serviços pesados (imagem, IA) nascem "headless" (testáveis sem tela) e ganham interface depois. Validar cada fase com um caso real do Otaviano.
> Documento de referência (colorido) em `docs/AutoTabloide_Roadmap_Detalhado.docx`.

Legenda: ✓ concluído · ▶ em curso · ○ a fazer

## Bloco A — Núcleo de dados e inteligência
- **F0 — Fundação limpa** ✓ — pacote `app/`, System Root, janela Qt, testes de fumaça.
- **F1 — Banco + sanitização** ✓ — schema síncrono (Produto, Alias, Categoria, Layout, Projeto, Config), CRUD, sanitização determinística + glossário de siglas. Validado na fixture real de 42.
- **F2 — Motor de composição (headless)** ✓ — coordenadas mm, compositor Pillow, ajuste de fonte (só reduz), preço de/por, aspect-fit, export PNG/PDF no tamanho exato. *Fidelidade com arte real: pendente, não bloqueante.*
- **F3 — IA + conciliação** ✓ — cliente API local (Qwen3.5 thinking-off), enriquecimento em 2 etapas (IA semântica + formatação F1), conciliação 3 camadas (embeddings Qwen3-Embedding 0.6B → fuzzy → juiz), OCR foto→tabela (+ validade da oferta), aprendizado por alias.
  - Gates reais fechados com o Qwen: enriquecimento, embeddings, juiz.
  - **OCR validado no print real:** 42/42 preços; a conciliação absorveu o ruído do OCR apontando 42/42 ao produto certo (prova da arquitetura).

## Bloco B — Aquisição e tratamento de imagens
- **F4.1** — Busca de imagem, serviço headless → candidatos. ✓ (backend **ddgs/DuckDuckGo** desde 2026-07-08 — o icrawler quebrou de vez e trazia lixo; query = nome enriquecido **sem peso/unidade** (`remover_peso`), região BR, pré-filtro pelas dimensões do buscador, defesas de rate-limit: timeout + pausa entre buscas + retry com backoff + pular item; dedup + filtro de resolução + degradação mantidos. **Integração dos 15 validada: 15/15 com foto relevante**, +18 automático na Amstel; 1 miss de auto-pick (sabão → clipart) = caso do pop-up da Mesa.)
- **F4.2** — Remoção de fundo (rembg birefnet-general) + recorte/normalização. ✓
- **F4.3** — Upscale condicional (Real-ESRGAN via spandrel, CPU) p/ fotos ruins e cartaz grande. ✓
- **F4.4** — Entrada manual (colar/arquivo/URL/arrastar) + troca + histórico de versões em disco. ✓
- **F4.5** — Múltiplas imagens no slot no compositor (LEQUE/LADO_A_LADO/GRADE, orientação por imagem). ✓
- **F4.6** — Selos na composição (+18 automático em bebida; "Qualidade Belo Brasil"). ✓ (**Bloco B completo**)

## Bloco C — Editor visual estilo Canva (o coração)
Tudo sobre QGraphicsScene; o **preview vem do MESMO compositor Pillow da F2** (garante WYSIWYG); o Qt cuida só da interação.

**Checkpoint de consolidação (pré-F5.4) ✓** — antes de empilhar mais fases: editor **rodável em janela real** (`python -m app.editor_app` / `app.main --editor`); **salvar/carregar layout no banco** (`app/rendering/persistencia.py`, `LayoutDef`↔`Layout`); decisões puladas preenchidas: **alinhamento justificado**, **unidade automática** (anexa ao nome só se não há região UNIDADE), **região TEXTO_LEGAL** (destino da validade da oferta). *Prática nova: ao fim de cada fase, listar o que ficou de fora.* **Pendente: rodar interativo no Windows** (tudo foi testado offscreen — o Otaviano precisa abrir e clicar).
- **F5.1** — Canvas base: arte + preview WYSIWYG (compositor Pillow), zoom, pan, réguas. ✓ **Gate de fidelidade F2 FECHADO** com a arte real (Belo Brasil 1080×1300): produto composto 1:1 sobre o design (número na caixa, nome com hífen, imagem no topo). Suporte a **layout digital em px** via `layout_de_arte` + `Retangulo.de_px`.
- **F5.2** — Camadas interativas: selecionar/mover/redimensionar (alças), z-order, painel de camadas (ocultar/travar/reordenar). ✓ (editar muta o LayoutDef → recompõe pelo Pillow; alça leve no arraste, recompõe ao soltar)
- **F5.3** — Ferramentas de região: adicionar [IMAGEM]/[NOME]/[PREÇO]/[UNIDADE]/[SELO] + painel de propriedades (fonte, cor, alinhamento, subtipo/papel/mostrar_moeda, ajuste). ✓ Célula-mestre afinada sobre a arte real (imagem maior/centralizada, preço cheio na caixa).
- **F5.4** — Auxílio de alinhamento: snapping, alinhar, distribuir, réguas/guias. ✓ + **passe de polimento**: barra de ferramentas rotulada, menu de botão direito (duplicar/excluir/travar), seleção múltipla (rubber-band) + pan com espaço, tema QSS, salvar/carregar layout no banco pela barra.
- **F5.5** — Grade + célula-mestre. ✓ **COMPLETA** — `app/rendering/grade.py`: auto-detecta as caixas de preço da arte (15 no Belo Brasil), replica a célula-mestre; `compor_pagina` aceita lista slot→produto. **Propagação + override (2026-07-08):** `Slot.mestre`/`origem_mm` + `Regiao.de_mestre`/`overrides` no modelo (serializados → persistem no banco); `propagar_mestre()` propaga estilo + geometria relativa à âncora, cria/remove regiões conforme a mestra, e **respeita overrides** (edição numa célula marca o atributo como override, que tem precedência e persiste — mesmo princípio do projeto congelado). No editor: mestra em **âmbar**, editar mestra → 15 mudam; `python -m app.editor_app` abre a grade real. 9 testes novos (`test_celula_mestre.py`). *Pendências fechadas (2026-07-08): botão direito → "Restaurar da mestra (N ajustes)" limpa os overrides; pontinho âmbar no item indica célula com override. Undo = F5.10.*
- **F5.6** — Agrupamento livre replicável: ▶ **construída conforme `ORDEM_F5_6.md` (2026-07-09); aguardando o gate 3 (validação ao vivo com arte irregular real do Otaviano)** — D1: slots novos `grupo_<uuid8>`, nunca renumerados; D2: `Slot.ref_grupo` (serializado, migração de layout antigo), **propagação por grupo** (`mestres()`/`slots_do_grupo()` — grade + grupos coexistem); D3: `remover_slot` **promove a cópia mais antiga** a mestre (irmãs reapontam `ref_grupo` e `ref_mestre` remapeado), item removido volta "fora da grade"; D4: `carimbar_copia` nasce vazia e é povoada pela propagação (uid novo + `ref_mestre` do mestre do grupo); **D5: `Historico` versiona `{layout, mapa}`** — o mapa mora no canvas, a Mesa usa proxy, e desfazer a remoção restaura slot E entrada do mapa; D6: tudo serializado relativo. UI: menu do item ("Agrupar seleção como replicável", "Remover esta célula") + menu do fundo do canvas ("Carimbar cópia de X aqui"); auto-preencher na **ordem visual (y,x das âncoras)**; **órfão do mapa acusado no pré-voo**. Adversarial ganhou os **passos 9–14** + teste dos gestos do canvas. **F5.6c (reauditoria do arquiteto, §6 da ordem) executada**: C1 — região nova (e colar) respeita a seleção; sem seleção nasce em slot `livre_<uuid8>` (nunca cai no mestre da grade); C2 — agrupar **recusa com toast** derivadas e regiões de mestre (só livres agrupam); C3 — `test_fluxo_real_grade_mais_destaque` (grade+destaque, pixel + invariância uid-a-uid da grade). **C5 (2ª reauditoria) executada**: `grade.ocupaveis` é a regra única de slot ocupável (Mesa + testes, sem filtro local — "filtro só no teste = mascaramento"); pré-voo acusa item em **célula vazia**; agrupar remove o `livre_` esvaziado na raiz (fica se tiver papel no mapa → acusado); teste do fantasma nos dois ramos. **GATE 3 (sessão ao vivo, arquiteto no controle da tela, §14 da ordem): tabloide real do verso montado de PONTA A PONTA pela UI** — grade 15/15 ao vivo, região livre sem replicar, conciliação 5🟢/10🔴, criação 9×, pré-voo com 6 pendências nominais, `arte/quintou/saida_g3_verso.png` com o trio correto nas 15 células e preços 1:1 ("2.49" incluso), projeto congelado salvo. **S1 e S2 da sessão corrigidos com os pares reais** (§15): guarda de divergência de marca (Campo Largo≠Aurora, Bonare≠Cajamar — verde não-exato com termo do cadastro ausente da oferta desce a amarelo, fuzzy E juiz; contrato do juiz atualizado em teste) + unidade sem duplicar/normalizada (`_qtd_texto`, `nome_com_unidade`). **Suíte: 195 verdes, zero skips.** *Fila da sessão (S3–S6, Bloco D/polimento): campo de nome na curadoria; re-busca com termo editável; TEXTO_LEGAL na barra/paleta + validação de cor + nome pré-preenchido no salvar; trava de instância única. Pendente para fechar a F5.6: **selo visual do Otaviano** (saida_g3_verso × verso_referencia; +18 da Itaipava = diferença esperada, decidir).* *Fora: mover grupo como unidade (arrastar célula inteira); copiar grupo para outro grupo (fora de escopo da ordem); rótulo visual de "mestre de grupo" distinto do âmbar da grade; "des-derivar" região (ordem própria futura, como anotado no §6).*
- **F5.7** — Estilos de fonte nomeados + override por instância: ✓ **PRONTA (2026-07-09, autorizada pelo arquiteto durante a espera do gate 3)** — `app/rendering/estilos.py` (headless): `EstiloTexto` (fonte/tamanho/cor) mora em **`LayoutDef.estilos`** (serializa, congela no projeto, portável — I3); `Regiao.estilo` + `overrides_estilo` com a MESMA semântica de precedência da célula-mestre (local vence; re-aplicar respeita; "Restaurar" volta a seguir); **mudar o estilo muda o conjunto** (`definir_estilo` re-aplica no layout inteiro, 1 estado de undo); excluir mantém a aparência (regiões ficam soltas); **o vínculo `estilo` propaga da mestra** (entrou no `ATRIBUTOS_ESTILO`). Painel: combo Estilo + **Novo…** (captura da região) / **Atualizar** (empurra pro conjunto) / **Restaurar** (aparece só com ajustes próprios); editar fonte/tamanho/cor numa região com estilo marca override da instância. 7 testes (`test_estilos.py`). **Suíte: 186 verdes.** *Fora: biblioteca GLOBAL de estilos entre layouts (hoje por layout — decisão: congela e viaja com o projeto); gestor visual de estilos (renomear/lista dedicada); matriz de interação grade-override × estilo-override documentada só em teste (os dois sets marcam juntos no painel).*
- **F5.8** — Multipágina + auto-flow + navegação. ✓ **FECHADA COM SELO DUPLO (2026-07-09)** — sessão ao vivo da Etapa C conduzida pelo arquiteto na tela real: layout frente+verso criado pela UI, duas tabelas importadas ("Adicionar aos atuais"), **guarda S1 ao vivo** (Campo Largo×Aurora, Tio Urbano×Bulnez, Bonare×Cajamar, Passatempo×Nestle — todos amarelos nominais, nenhum falso-verde), nome editável + "Buscar de novo" em batalha real, auto-flow 15+15, +18 automático na Itaipava, pré-voo por página, e os artefatos `arte/quintou/etapaC_p1.png`, `etapaC_p2.png` e `etapaC.pdf` (2 páginas). Registro pós-sessão: nome duplicado da Itaipava (typo humano) **já corrigido no banco pelo builder**; ~20 produtos sem foto = curadoria contínua pelo Almoxarifado (não é bug). Histórico das etapas — Etapa A: TEXTO_LEGAL na barra + `texto_fixo` (desenha em slot vazio), curadoria com nome editável + "Buscar de novo", cor validada, salvar pré-preenchido, **instância única** (QLocalServer). **A7** (reauditoria): ocupável = região de **conteúdo de produto** (o "Fica a Dica" não engole item; pré-voo acusa célula decorativa). **Etapa B**: D8.1 ids únicos no layout inteiro (`validar_ids_unicos` recusa duplicata na carga; página nova = `celula_<uuid8>`); D8.2 fundo por página; D8.3 auto-flow páginas na ordem; D8.4 canvas por página atual + navegação no editor (±página, undo restaura página+mapa) e na Mesa; D8.5 PNG `_pN` + PDF multipágina + pré-voo rotulando página; D8.6 congelado com fundos por página; D8.7 adversarial com as **duas faces reais** (30 células, pixel nas 2 páginas, remover página+undo, nenhum uid duplicado) — verde de primeira. Self-check da Etapa C: 30 itens reais → 15+15 → pré-voo (21 pendências nominais) → `selfcheck_p1/p2.png` + `selfcheck.pdf`. **Suíte: 208 verdes.** *Fora: capa/miolo além de frente+verso, arrastar item entre páginas (Bloco D), imposição (decisão travada: sem NUP).*
- **F5.9** — Texto ao vivo no editor (só-reduz, hífen, alinhamentos, unidade dentro/fora) refletindo no preview.
- **F5.10** — Desfazer/refazer + conforto. ✓ **PRONTA (2026-07-08)** — `app/qt/historico.py`: snapshots do LayoutDef (JSON) **em disco**, limite generoso (300), dedup de estados idênticos, editar-após-desfazer corta o futuro. Registrado em TODAS as mutações do canvas (mover/redimensionar, propriedades, adicionar/duplicar/excluir, z-order, olho/trava, alinhar/distribuir, propagação da mestra, restaurar, colar). **Ctrl+Z / Ctrl+Shift+Z** + botões na barra + palette. **Copiar/colar entre slots** (Ctrl+C/Ctrl+V, cola no slot da seleção com offset; na mestra replica) + menu de contexto consolidado (copiar/colar/duplicar/excluir/travar/restaurar, com atalhos). Mesa relê `canvas._layout` no preencher/exportar (desfazer não diverge do export). 6 testes (`test_historico.py`). *Fora: coalescer edições contínuas de spinbox (cada passo vira 1 estado); undo do auto-preencher da Mesa (produtos não são LayoutDef); histórico não persiste entre sessões.*

### Missão de design (transversal ao Bloco C/D)
Sistema de design profissional sobre o Qt, sem tocar no motor. **Passo 1 ✓ (aprovado)** e **Passo 2 ✓ (aguardando reauditoria ao vivo)** — tudo em `app/qt/design/`:
- **Tokens** (`tokens.py`): primária 50–900, semânticas + fundos, neutros em níveis, canvas ≠ chrome, seleção/guia-snap (violeta), elevação (sombras 1–3), motion (120/200ms), tipografia com pesos.
- **Shell** (`shell.py`): top-bar wordmark + navegação das telas futuras (Início✓/Ateliê✓/demais desabilitadas até o Bloco D); status bar com dica, ● salvo/não salvo, dimensões, zoom %.
- **Editor aplicado de verdade**: barra com ícones+atalhos (tooltips "Ação · Ctrl+X"), painéis em cartões, canvas com vinheta+sombra da página, réguas nos tokens, guias violeta, hover de região antes do clique, alças estilo Figma com cursores por canto, menu de contexto com ícones.
- **Estados**: vazio com craft (EstadoVazio), spinner/overlay p/ IA-imagem (`carregando.py` — integração real com pipelines = Bloco D), toasts animados (`toast.py`), **command palette Ctrl+K** (`paleta_comandos.py`).
- Screenshots de todas as superfícies/estados: `python -m app.scripts.screenshots_design` → `saida_design/01..07`. Abrir ao vivo: `python -m app.editor_app`. Suíte verde (126).
- **Ficou de fora**: números tabulares via feature OpenType (Qt 6.7+, avaliar); transição animada de troca de tela no shell; QColorDialog é o nativo (só o swatch é custom); undo/redo é F5.10.

## Bloco D — As telas e os fluxos completos
- **F6.1** — Dashboard (inicial): ✓ **PRONTO (2026-07-09)** — `app/qt/telas/dashboard.py`, **tela de chegada** do app: **prateleiras por evento** ("Terça do Pão"…, "Avulsos"), cada projeto com **miniatura real** (composta e cacheada em `projetos/<uuid>/miniatura.png` no salvar — fail-safe), nome, tipo e data; **duplo-clique reabre idêntico** na Mesa/Fábrica (`abrir_projeto_congelado`); botão direito: abrir/duplicar (nova edição)/renomear/excluir; **ações rápidas** (novo tabloide/cartaz/layout); recarrega no `showEvent`. `renomear_projeto` no serviço. Bug corrigido: projeto sem imagens/arte não criava a pasta → miniatura falhava. 4 testes (`test_dashboard.py`). *Fora: busca por nome/data; status de produção; empacotar (F7.4); mover projeto entre eventos pela UI (renomear já aceita evento).*
- **F6.2** — Ateliê (layouts): ✓ — **E-A3 do Bloco E (2026-07-09): arte de fundo agora é COPIADA para `<raiz>/layouts/` e o banco guarda caminho RELATIVO** (I3 curado na raiz, não só na fronteira do pacote); layouts antigos com caminho de máquina migram na abertura do app, com aviso nominal (arte sumida mantém o rastro e continua avisando). — **núcleo PRONTO (2026-07-08)** — `app/qt/telas/atelie.py`: biblioteca com **miniaturas** (arte ou composição de exemplo), nome + **tipo** (tabloide/cartaz/etiqueta, definido pelo usuário); **Novo layout** (importar arte → grade auto-detectada no tabloide → editor do Bloco C embutido → salvar); **editar/duplicar/renomear/excluir** (botão direito); **duplo-clique abre na Mesa ou Fábrica com aquele layout** (fim do hardcode — `carregar_layout` nas duas). Layouts padrão semeados por upsert ("Tabloide Belo Brasil", "Cartaz 10×15 — exemplo"). `persistencia` ganhou duplicar/renomear/excluir. 3 testes (`test_atelie.py`). **Achado do auditor corrigido: enriquecimento persiste** — fluxo 🔴 já persistia; novo passe `app/scripts/enriquecer_banco.py` limpou o acervo (35 nomes, ex.: "Ole o"→"Óleo"). *Fora: busca/filtro na biblioteca, "definir como padrão", tamanho de página manual.*
  - **Auditoria de cobertura código×docs**: `docs/AUDITORIA_COBERTURA.md` (novo) — mapa ✓/▶/○ de toda a Documentação-Mestre; maior lacuna conceitual = projeto congelado (priorizar após undo/redo).
- **F5.5b — trava de integridade**: ✓ **FECHADA (2026-07-09)** — resposta à auditoria pessimista do arquiteto (`AUDITORIA_INTEGRIDADE_VINCULO.md`, normativa): vínculo slot→produto por **mapa de uid** (I1) persistido no projeto; pareamento mestra↔célula por **`ref_mestre`** (I4, grade nasce propagando); **parser de preço** à prova de milhar (P0.3); **pré-voo de exportação** (I2: imagem sumida, sem preço, fonte ausente c/ fallback Roboto→Pillow, PROCON "de"≤"por"); **P1.1–P1.7 todos fechados** (caminhos relativos I3, guarda re-salvar, adicionar/substituir no 2º import, edição nome/preço na estante, descarte contado, confirmação de sobrescrita, unidade+validade fluem). **Teste adversarial §4** (`test_adversarial_vinculo.py`) verifica o trio **por pixel** sob reordenação/shuffle/undo/reabrir/duplicar — 4× verde. Relatório: `docs/AUDITORIA_PESSIMISTA.md`. **Reauditoria independente do arquiteto (leitura direta do código) confirmou o fechamento** e achou o **P0.3b** (parser fundia "2x 5,00"→25,00) — **corrigido pelo próprio arquiteto** (número ambíguo → None → pré-voo) junto com pré-voo multi-imagem e log da miniatura; o builder validou: **suíte 174 verdes na máquina real. Gate liberado: F5.6 pode começar** (P2 prioritário da F5.6: undo versionar o mapa slot→uid junto do layout, necessário para o arrastar-para-célula).
- **F6.3** — Almoxarifado (estoque): ✓ **PRONTO (2026-07-09)** — `app/qt/telas/almoxarifado.py`: **lista virtualizada de verdade** (`CatalogoModel`/QAbstractListModel com `fetchMore`, páginas de 50 — milhares não pesam a RAM), busca + filtro pelo **semáforo de qualidade** (🔴 sem imagem · 🟡 sem preço/categoria · 🟢 ok, com tooltip do que falta); painel de edição completo (nome/marca/sabor/peso com parse/preço/categoria/validade dd-mm-aaaa/álcool/+18/marca própria — salva no `editingFinished`); **trocar imagem** (curadoria ddgs/arquivo/colar/URL → rembg → biblioteca com versão) + **histórico com restaurar**; **"Corrigir nomes (IA)"** em lote (reusa `enriquecer_banco`, progresso no overlay); botão direito com **seleção múltipla** (excluir N). **Mesa destravada: " Do banco"** → `ImportarBancoDialog` com busca e **multi-seleção acumulativa** (cesta persiste entre buscas; dedup ao importar). 6 testes (`test_almoxarifado.py`). *Fora: filtro de qualidade só filtra páginas carregadas (filtrar no SQL quando o catálogo crescer); duplicar produto; edição em massa de campos; Image Doctor não avalia resolução da imagem (só existência).*
- **F6.4** — Mesa (tabloide): ▶ **primeira fatia PRONTA (2026-07-08)** — `app/qt/telas/` (mesa, conciliacao_dialog, curadoria_dialog, servico headless) + `app/qt/workers.py` (Trabalhador/QThread; UI nunca congela): **importar tabela/foto** (OCR se LM ligado; degrada com aviso) → **conciliação com semáforo 🟢🟡🔴** (aceitar 🟡 aprende alias; 🔴 → enriquecer → **curadoria de imagem** ddgs/arquivo/colar/URL/sem → rembg → cadastra na biblioteca com versionamento; ignorar por linha; Concluir só sem pendência) → **auto-preencher a grade na ordem** → **exportar PNG/PDF** (overlays "Enriquecendo nome…/Buscando imagem…/Removendo fundo…"). Validado ponta a ponta com a fixture real: **42/42 verdes** no banco semeado; export `frente_via_mesa.png`. 6 testes (`test_mesa.py`). Banco real semeado com o catálogo 42 + 5 fotos vinculadas à biblioteca. *Fora: importar do banco (multi-seleção) = com o Almoxarifado; arrastar item→slot e override modal por slot; xlsx/csv (só .txt e foto); zoom do rodapé reflete o Ateliê (religar por tela); validade→TEXTO_LEGAL automático.*
- **F6.5** — Fábrica (cartazes): ✓ **COMPLETA (Etapa A do Bloco D, 2026-07-09)** — `app/qt/telas/fabrica.py` + `app/rendering/cartaz.py` (layout placeholder 10×15cm programático): **1 item = 1 página**; reusa importar+conciliação da Mesa; exige descrição + **"de" + "por"** (incompletos marcados ⚠ dizendo O QUE falta e fora do PDF); **"de" riscado** (`Regiao.riscado` no modelo+compositor+painel, propaga na grade); **validade do item** (campo por item → TEXTO_LEGAL "Válido até X"); **preview ao clicar**; **exportar = PDF multipágina no tamanho exato** (`exportar_pdf_multipagina`, validado com pypdf). **Etapa A do Bloco D (2026-07-09):** "por" **editável pela tela** (campo no painel + duplo-clique nome/preço, paridade com a Mesa); **pré-voo `cartaz=True` nos DOIS caminhos** (`_avisos_pre_voo()` único no exportar E no salvar projeto — o salvar não validava nada, achado de bancada) **rotulado por página do PDF** ("página N" / "fora do PDF"); **gate da arte real preparado**: `layout_de_arte` **lê o ppi gravado na arte** (Illustrator 10×15 a 300 ppi entra como 100×150 mm exatos sem ajuste de código — antes assumia 96 fixo e o PDF sairia >3× maior), composição 1:1 sem reamostragem, página do PDF medida com pypdf. 5 testes (`test_fabrica.py`) + 10 (`test_bloco_d_etapa_a.py`). *Fora: validação com a arte REAL do Otaviano (= Etapa D do Bloco D); peso/imagem obrigatórios quando o layout pedir; reordenar cartazes na lista.*
- **F6.6** — Cofre: ✓ **PRONTO (Etapa B do Bloco D, 2026-07-09)** — `app/core/cofre.py` (headless) + `app/qt/telas/cofre.py`: **snapshots** do banco pela API de backup do SQLite (consistente com WAL aberto, sem fechar o app), datados em `backups/`; **automático a cada abertura** (gancho em `app.main` e `app.editor_app`) com **rotação configurável** (`backups.rotacao`, padrão 10 — só os automáticos rodam; manuais ficam); **modo seguro** = `inspecionar_snapshot` abre SOMENTE-LEITURA e mostra o que há dentro sem tocar no vivo; **restaurar nunca apaga o atual** (vira snapshot `pre_restauracao` antes — restauração tem desfazer). Tela: lista de snapshots + criar/inspecionar/restaurar/excluir + exportar/importar pacote. 6 testes (`test_cofre.py`) + 3 (`test_cofre_tela.py`). *Fora: agendamento por tempo (só na abertura + manual); backup das imagens fora do pacote .atpkg (snapshot é só do banco — as fotos têm versionamento próprio na biblioteca).*
- **F7.4-núcleo** — Portabilidade (casa↔mercado): ✓ **PRONTA (Etapa B do Bloco D, 2026-07-09)** — `app/core/portabilidade.py`: **exportar `.atpkg`** (zip com manifesto versionado + cópia consistente do banco + biblioteca de imagens por produto + fontes + projetos congelados; a arte dos layouts é copiada para `layouts_arte/` e os caminhos REESCRITOS relativos na cópia que viaja — **nenhum caminho de máquina no pacote, I3**); **importar com mesclagem em 2 fases** (`analisar_pacote` não grava nada → relatório → `aplicar_importacao`): produto casa por **CHAVE NATURAL** (nome_sanitizado normalizado + marca), NUNCA por id (**D-B1/I1**); produto novo ganha **id novo** e a pasta da biblioteca é **renomeada no ato conforme o remap**, com **verificação pós-import byte a byte obrigatória** (falhou → rollback, nada gravado); **conflito nunca se resolve em silêncio** (I2): relatório com decisão POR ITEM (manter local / usar do pacote / **manter ambos como variantes**) + "aplicar a todos" no `MesclagemDialog`; aliases seguem o remap (aditivos, sem duplicar); layouts casam por nome (divergência = conflito visível); projetos congelados viajam por uuid (não colide, não duplica); config nova entra, existente fica local com aviso; foto substituída vira versão (histórico). **D-B3 (adversarial I5, `test_adversarial_portabilidade.py`)**: roundtrip casa↔mercado completo na letra da ordem — exportar A → importar em B vazio (trio POR CONTEÚDO após remap, alias apontando certo) → alterar em B (novo/preço/foto) → mesclar de volta em A (conflitos nominais, decisões aplicadas, NENHUMA foto trocada — cores únicas conferidas byte a byte por chave natural) → mesmo pacote 2× idempotente; + teste do remap com **ids deslocados** (B pré-povoado — a mesclagem ingênua por id colaria a foto da Coca no Sabão). 8 testes (`test_portabilidade.py`) + 3 adversariais (3× verdes seguidas). *Fora: ver resposta da Etapa B na ORDEM_BLOCO_D.*
- **F6.7** — Configurações: ✓ **PRONTA (Etapa C do Bloco D, 2026-07-09)** — tela `app/qt/telas/configuracoes.py` sobre a tabela `Config`, com **tudo em default são (C3)**: banco antigo sem as chaves abre com os padrões, valor inválido cai no padrão (limiar quebrado nunca derruba a conciliação; config quebrada nunca derruba a IA). **C1 vivo de ponta a ponta**: `sanitizacao.siglas` (maiúsculas) + **`sanitizacao.glossario` novo no motor** (`RegrasSanitizacao.glossario_siglas`, expansão "VD"→"vidro" por token, antes da caixa — tokens numéricos/unidades imunes); `ia.base_url`/`ia.modelo_*` via **`ConfigIA.da_config()`** (trocar LM Studio↔Ollama sem código — `ClienteOpenAICompat()` sem config lê da tabela); **`limiares_de_config`** no `Conciliador` (sem limiares explícitos vale a Config — teste prova que trocar o limiar MUDA o semáforo do mesmo item, o gesto da sessão ao vivo da Etapa D); `backups.rotacao` exposto. **C2**: "Salvar e ver prévia do acervo" — `app/core/configuracao.py` (`previa_reformatacao`/`aplicar_reformatacao`): N nomes que mudariam + amostra + confirmação explícita; nada reescreve em silêncio (linha malformada do glossário é contada no aviso, não somem em silêncio); limiar incoerente (verde ≤ amarelo) recusa salvar. 10 testes (`test_configuracoes.py`). *Fora: selos e atalhos (a ordem do Bloco D não os incluiu — ficam para o polimento); palavras_minusculas/mapa_unidades configuráveis só em código (RegrasSanitizacao), sem chave na Config.*
- **F6.8** — Projeto salvo (congelar): ✓ **NÚCLEO PRONTO (2026-07-08)** — `app/core/projetos.py` (headless) + `projetos_dialog.py`: **congela tudo inline** no `estado_slots` (LayoutDef da época — editar no Ateliê depois NÃO muda o projeto; itens com nome/preços/validade/+18) e **copia imagens + arte** para `projetos/<uuid>/` (trocar a foto no banco não toca o projeto). Salvar (nome + **evento** p/ o Dashboard) / abrir (reabre idêntico e auto-preenche) / **duplicar** (pasta própria) / excluir — na **Mesa e na Fábrica**; indicador **salvo/não salvo do rodapé ligado de verdade**. `overrides_json` por slot reservado (modal de override = F7.3). Validado: banco mudou depois → projeto intacto; original apagado → cópia vive; layout editado → projeto usa o da época. 6 testes (`test_projetos.py`). *Fora: empacotar/importar .atpkg (F7.4); caminhos congelados são absolutos (relativizar no empacotamento); undo do auto-preencher (registrar itens no histórico junto do layout — agora possível, fazer com o modal de override); Dashboard consome os eventos (F6.1).*

## Bloco E — Casos avançados e refino
- **F7.1** — Vários sabores/fragrâncias num slot: ✓ **PRONTA (Etapa C do Bloco E, 2026-07-10)** — a UI do motor F4.5. **`ItemMesa.imagens`** (lista COMPLETA e ordenada que o slot desenha; vazia = foto única de sempre) + **`arranjo`** por item; botão direito no item da estante → **"Fotos deste item (sabores)…"** (`FotosItemDialog`): lista ordenada com mover/remover, **"Buscar e escolher…"** reusa a curadoria de sempre, e a **IA sugere TERMOS como chips clicáveis** (`sugerir_variantes` em `enriquecimento.py` — só preenche o termo da busca; **quem escolhe cada foto é o humano, a IA nunca decide imagem** — teste explícito do chip que não adiciona foto). Foto extra tratada pelo mesmo pipeline (rembg) e guardada em `biblioteca/<id>/extras/`; **congelamento preserva as N fotos NA ORDEM** (`imagens/{i}_{k}.png` relativos — I3) e o arranjo; miniatura do Dashboard compõe multi. **C2**: arranjo (leque/lado a lado/grade) por item no diálogo + por override de slot (B1). **Adversarial (I5)**: `test_adversarial_multi_imagem_por_conteudo` — LADO_A_LADO amostrado TERÇO A TERÇO na ordem da lista, ordem invertida inverte os pixels, LEQUE mostra as 3 cores, congelado byte-idêntico por posição (originais apagadas não afetam), duplicado idem, pré-voo acusa "imagem 2/3" sumida. 6 testes (`test_multi_imagem.py`) + 1 adversarial. *Achado de bancada: worker disparado no construtor do diálogo → thread viva no encerramento derrubava o processo (0xC0000409) — curado em PRODUÇÃO: `GerenciadorTrabalhos.encerrar()` + `done()` do diálogo junta as pontas; costura `sugestor` injetável.* *Fora: sugestões de variantes não são cacheadas; Fábrica segue foto única (cartaz).*
- **F7.2** — Dois produtos no mesmo slot (Camil e Rei): ✓ **PRONTA (Etapa D do Bloco E, 2026-07-10)** — a decisão de identidade da ordem na letra: **o mapa é e continua 1 slot → 1 uid**. `servico.compor_itens(a, b)` → **UM item composto** com uid PRÓPRIO, **nome montado deterministicamente** (`nome_composto`: prefixo/sufixo comuns preservados, miolos com "e" — "Arroz Camil 5kg"+"Arroz Rei 5kg"→"Arroz Camil e Rei 5kg", sempre editável), **2 imagens LADO_A_LADO** (padrão da ordem), **preço único**, +18 por OR; os DOIS originais viajam **INTEIROS** em `origem_composto` (uid incluso — rastreável e desfazível); **composto não compõe de novo** (profundidade 1, erro nominal). `separar_item` devolve exatamente o que existia. Na Mesa: botão direito → "Compor com outro item…" (par + nome + preço único) / "Separar"; o composto **herda o slot do primeiro** e a célula do segundo esvazia à vista; ao separar, o primeiro volta à célula. **Congelamento**: as fotos de ORIGEM também congelam na pasta do projeto (I3) — separar depois de reabrir devolve itens com foto viva. **Adversarial (I5)** `test_adversarial_item_composto`: 3 ciclos compor/separar sem uid duplicado nem órfão no mapa, uids originais de volta, LADO_A_LADO por pixel (Camil à esquerda, Rei à direita) antes E depois do congelamento, originais apagadas do disco sem efeito. 5 testes (`test_item_composto.py`) + 1 adversarial. *Fora: compor/separar não entra no undo do canvas (gesto da estante — o inverso explícito é o desfazer, mesma semântica do auto-preencher); Fábrica desenha só a 1ª foto do composto (cartaz é 1 produto/página).*
- **F7.3** — Overrides por slot: ✓ **PRONTA (Etapa B do Bloco E, 2026-07-09)** — o `overrides_json` reservado desde o F6.8 entrou em serviço. **Botão direito numa célula da Mesa → "Conteúdo desta célula (override)…"**: modal edita nome/preço/foto/arranjo SÓ daquela célula (campo vazio herda; placeholder mostra o valor do item); precedência da visão §3.1 em `servico.aplicar_override` (**override do slot > item da estante > banco**), aplicada num ponto único (`_dados_por_slot`) — preview, pré-voo, export e miniatura enxergam o mesmo. **Persistência por `slot_id`, nunca por posição (I1)**; a foto do override **congela na pasta do projeto** (relativa, I3). **Indicador violeta** na célula + "Restaurar do item" (3ª aparição do padrão mestra/estilo, mesma UX). **Undo versiona {layout, mapa, overrides}** (D5 estendido — desfazer um override restaura o anterior); "Substituir tudo" e abrir outro projeto zeram (nada vaza entre tabloides); override órfão (célula removida) acusado no pré-voo. **Adversarial atualizado (I5)**: `test_adversarial_override_por_slot` — por pixel/byte, o override rende só na célula dele sob shuffle/reordenação, sobrevive a salvar→reabrir→duplicar com a foto congelada byte-idêntica (original apagada do disco nem faz cosquinha), e o undo volta estado a estado. 6 testes (`test_override_slot.py`) + 1 adversarial. *Achado de bancada: `_avisos_orfaos` só olhava a página 1 — corrigido p/ todas.* *Fora: arranjo do override ganha efeito visível com o multi-imagem da UI (Etapa C); arrastar item→célula segue fora (nota da F6.4).*
- **F7.4** — Portabilidade completa: **núcleo PRONTO na Etapa B do Bloco D** (ver F7.4-núcleo acima). Resta do escopo completo: empacotar UM projeto avulso (hoje o .atpkg leva tudo) e polimentos de UX do fluxo.
- **F7.5** — Exportação avançada: ✓ **PRONTA (Etapa E do Bloco E, 2026-07-10)** — `app/rendering/cmyk.py`: conversão **só na exportação**, como pós-processo do PDF já gravado (`pos_processar_export` nos exports da Mesa E da Fábrica); liga/desliga por `export.cmyk_pdf` (padrão: **desligado — RGB de sempre**) + `export.perfil_icc` opcional, os dois na tela de Configurações. **Teste-rei (E1)**: com CMYK desligado o export fica **byte-idêntico** (hash antes/depois — nenhum byte muda; PNG nunca é tocado). **E2**: Ghostscript REAL do ambiente (10.06) valida `/DeviceCMYK` no convertido + tamanho físico intacto (pypdf, mesmas páginas); **gs ausente degrada COM aviso** ("o PDF ficou em RGB") sem travar o export; perfil ICC inexistente converte com o padrão E avisa. 5 testes (`test_cmyk.py`). *Fora: CMYK só para PDF (PNG é digital por definição); sem preview de cores CMYK na tela (o editor segue RGB — conferência de prova é da gráfica).*

**Bloco E — todas as etapas executadas (A dívidas ✓, B override ✓, C multi-imagem ✓, D composto ✓, E CMYK ✓); artefatos do gate em `saida_selfcheck_e/` (`python -m app.scripts.selfcheck_bloco_e`). Suíte: 281 verdes, zero skips, exit 0 em duas rodadas. Aguardando o selo de fechamento do bloco.**

## Bloco F — Teste final e polimento
- **F8.1** — Categorização IA refinada (corrigível): ✓ **PRONTA (Etapa A da ORDEM_F8, 2026-07-10)** — **a regra que protege o Otaviano**: coluna nova `Produto.categoria_origem` ("humano"/"ia") com a **primeira migração real de schema** (`_migrar_schema` no `Database.init`: `ALTER TABLE ADD COLUMN` idempotente — banco antigo abre sem erro e ganha a coluna, testado com sqlite cru); categoria editada no Almoxarifado marca "humano" e **nenhum passe de IA a sobrescreve** (guarda no `enriquecer_banco` — teste força o passe a RENOMEAR o produto e confere que a categoria humana sobreviveu à edição real); botão **"Categorizar (IA)"** no Almoxarifado roda `categorizar_acervo` em lote **só no que falta** (categoria existente intocada; IA sem palpite deixa vazio → agrupa em "Outros", nunca some — I2). **A2**: toggle **"Agrupar por categoria"** na Mesa (padrão desligado) — `ordenar_por_categoria` (estável; ordem da Config `categorias.ordem`, campo na tela de Configurações; fora-da-lista alfabética; **"Outros" sempre por último**) ordena a FILA do auto-preencher; **o mapa continua slot→uid** (a estante não muda de ordem — agrupamento é ordenação prévia, nunca vínculo novo); `ItemMesa.categoria` preenchida na conciliação e no importar-do-banco. 6 testes (`test_categorizacao.py`). *Achado de bancada: o fake de IA com chave vazia nunca casava (`_casar` ignora chave falsy) — dois testes passavam por sorte compatível; corrigido com chave real do prompt e o teste do humano endurecido (edição real + guarda).*
- **F8.2** — Agrupamento por categoria com contorno + título: ✓ **PRONTA (Etapa B da ORDEM_F8, 2026-07-10)** — o visual dos áudios originais: **contorno arredondado azul + título ("Limpeza") em etiqueta na borda**. `app/rendering/secoes.py` (headless): seções são **camada DERIVADA** calculada do preenchimento agrupado a cada composição — runs de células CONTÍGUAS (ordem visual) da mesma categoria; run que atravessa quebra de linha vira **um sub-retângulo por linha** (título só no 1º); célula vazia quebra o run; sem categoria = "Outros". **A lei da casa (3ª aplicação) resolvida POR CONSTRUÇÃO**: seção NUNCA vira slot nem região — "ocupável" e pré-voo nem sabem que ela existe, **com teste provando** (grade completa + seções ligadas = zero aviso, ocupáveis idênticos). Desenho DEPOIS do fundo e ANTES do conteúdo (o contorno corre pela folga — o trio jamais é coberto); cor/espessura pela Config (`secoes.cor`/`secoes.espessura_mm`, campos na tela, defaults sãos). **DIY (B3)**: `Pagina.secoes_ligadas` + `titulos_secoes` (serializados → congelam no projeto); na Mesa: agrupar liga em todas, checkbox "Seções nesta página" desliga por página, "Títulos…" edita o rótulo por seção/página. **Adversarial B4 (I5)**: com seções LIGADAS, o trio de CADA célula é pixel-idêntico ao desligado (4 pontos por região), sob shuffle e depois de salvar→reabrir (liga/desliga + títulos persistem congelados). 6 testes (`test_secoes.py`) + 1 adversarial. *Fora: título sempre no 1º sub-retângulo (posição fixa na borda); contorno pode ficar parcialmente atrás de foto com fundo opaco na borda da célula (desenho-antes-do-conteúdo é a garantia de nunca cobrir).*
- **F8.3** — Tabloide categorizado de ~40 itens de ponta a ponta (marco de aceitação): ▶ **EXECUTADO (Etapa C da ORDEM_F8, 2026-07-10) — aguardando o selo de ACEITAÇÃO do Otaviano na sessão final**. Duas peças: **teste permanente** (`test_marco_f8.py`: 40 itens sintéticos de cor única, frente+verso reais + página extra = 45 células com ids únicos, fila agrupada com "Outros" no fim, pré-voo LIMPO, PNG×3 1:1 com a arte + PDF de 3 páginas, **trio por pixel em cada célula das 3 páginas**, seções visíveis, congelado reaberto com spot por pixel na página 2) e **selfcheck real** (`python -m app.scripts.selfcheck_f8`, acervo REAL clonado via .atpkg — o vivo só é lido): **a IA real (Qwen) categorizou 34 produtos, zero sem palpite**; fixture canônica de 40 itens reais gerada (`app/tests/fixtures/ofertas_quintou_40.txt`); **conciliação 40/40 🟢**; auto-preencher agrupado em **9 categorias contíguas reais** (Bebidas→Congelados→Frios→Higiene→Hortifrúti→Limpeza→Mercearia→Padaria→Pet); pré-voo com 22 pendências NOMINAIS (produtos reais sem foto — curadoria contínua do Almoxarifado, registrada desde a F5.8); export `saida_selfcheck_f8/marco_p1..p3.png` + `marco.pdf`; projeto congelado e reaberto idêntico. Suíte: 295 verdes ×2, exit 0.
- **F8.4** — Performance (listas grandes) e polimento de UX. ▶ **absorvida pela REVISAO_GERAL (ordem vigente)** — Onda 1 (desempenho) SELADA 17/07; **Ondas 2, 3 e 4 SELADAS 18/07; Onda 5 (visual + O MARCO) executada 18/07, aguardando reauditoria e o SELO FINAL do Otaviano** — seções com 4 estilos + cor por categoria + curas do bug da borda; cartaz com upscale no fluxo e área preenchida; gestor de selos com upload próprio e seleção por item; validade da oferta de/até + selo "De olho na validade"; Início com semana/eventos criáveis/faixas de cor; heróis + guia Z + medidor de densidade; assistente de preço charm. O MARCO (selfcheck_marco): 3 campanhas, 5.007 produtos, abrir 0,04s / conciliar 126s / exportar 0,4s — todos dentro dos orçamentos. Suíte: 402 verdes ×2. — regra dura do enriquecimento (nenhum token some; perda = revisão nominal), abreviações só-do-tabloide, categoria na criação, datas por evento, Fica-a-Dica com limite da região, paginação+marcas próprias na busca, multi-fotos persistidas no acervo (relativas à pasta — remap-imunes, roundtrip provado), composto na conciliação, EAN+cascata Open Food Facts, preset de setores. Suíte: 383 verdes ×2. — rotação de região no modelo/composição/painel com adversarial próprio; roda=rolagem/Ctrl=horizontal/Alt=zoom; hifenização de aproveitamento (pyphen) + justificado até a borda; pesos da família (Black/Bold/Light) por name table; célula como grupo (1º clique=trio, 2º=região); painéis sem corte + tooltips + legenda dos pontinhos + microtutorial de 1º uso; tamanho efetivo exibido; SELO com placeholder. Suíte: 351 verdes ×2, zero skips.: travamento do zoom curado na raiz (clamp + régua adaptativa + fit adiado + Ctrl+0 + zoom/salvo por tela), vigia de travamento em `<raiz>/logs/travamentos.log`, gancho GLOBAL de shutdown (`encerrar_todos` no closeEvent), teclado (Del/Backspace região, Ctrl+V curadoria, undo/redo na Mesa), gestão da estante, dessincronia entre telas (re-sync Ateliê→Mesa/Fábrica com congelado imune; Almoxarifado auto-refresh; **semeio de boot não sobrescreve mais os layouts padrão editados**), grades de miniatura estáticas. Suíte: 331 verdes ×2, zero skips.

## Bloco G — Empacotamento e entrega
- **F9.1** — Instalador/executável Windows (PyInstaller), primeira execução, migração de assets.
- **F9.2** — Guia rápido de uso + checklist de instalação do LM Studio/modelos.

## Pendências de validação real (não esquecer; limpar antes das fases que dependem delas)
- Fidelidade da renderização com **arte real** do Illustrator (da F2) — antes de fechar o Bloco C.
- (Gates da F3 — enriquecimento, OCR, juiz — ✓ fechados com o Qwen real.)

## Pontos em aberto (decidir testando)
- Limiares do semáforo; guardar upscale ou gerar sob demanda; limites de histórico; quanto do tabloide categorizado é desenho custom.
- **Máscara circular / forma não-retangular da imagem** (doc C6) — pendente (Ajuste só tem CONTER/PREENCHER).
- Resolvidos: modelo de embeddings = **Qwen3-Embedding 0.6B**; busca de imagem = **ddgs/DuckDuckGo** (icrawler quebrou; a "estratégia de captcha" virou defesa de rate-limit).

## PLANO PERFEITO — a reta final em 12 fases (era vigente)

- **FASE 1 — Fundação visual: design system 2.0**: ▶ **EXECUTADA (18/07/2026)
  — os 100 passos na ordem; aguardando a reauditoria do arquiteto (passo 100)**.
  Blocos: A fotografia (11 fotos + inventário + defeitos D1–D5); B tokens
  semânticos com leitura tardia + diff pixel-idêntico 11/11 no claro; C dark
  mode completo (spec do caderno, seletor com prévia, toggle na engrenagem,
  zero chrome vazado); D motor de animação (180 ms OutCubic, Config
  "reduzidas"=instantâneo, crossfade/toasts empilhados/diálogos com véu/hover
  por véu translúcido/skeletons/BarraIndeterminada/seções recolhíveis/canvas
  animado; CPU ≤0,4%, GIF de 20 s + prova reduzidas=0); E régua anti-corte
  (ALTURA_CONTROLE=32, mínimos por QSS, splitters com memória nos 5 laterais,
  Shell lembra geometria/tela, 720p/1080p/escala 100-125-150% fotografados,
  Tab visual, anel de foco, D1–D5 CURADOS no lado a lado); F vida (toast com
  Desfazer ligado ao undo real, estados vazios com ação, som opcional,
  cursor de espera, contadores vivos, título com •, confirmações com verbo,
  splash instantâneo, boas-vindas, Sobre, ícone do app, varredura PT-BR);
  G fechamento (suíte ×2 verde zero skips, adversariais 15/15, testes novos
  de tema/animações/mínimos, GIF + comparativo + cartão-postal em
  saida_fase1/). Caderno com as 7 checagens registradas: `docs/FASE_1.md`.
- **FASE 2 — O Início revolucionado**: ▶ **EXECUTADA (18/07/2026) — os
  100 passos na ordem; aguardando a reauditoria do arquiteto (passo 100)**.
  Evento ENTIDADE (cor/capa/dia/notas, migração sem perda, RG-24 lê do
  Evento); Início em 3 zonas (saudação+busca, "Produzir hoje"/agenda de 7
  colunas, grade de cartões responsiva com capa/status/favorito); status
  rascunho→pronto→exportado→publicado por HASH de conteúdo; continuar de
  onde parei; linha do tempo de VERSÕES (snapshot completo, abrir = clone,
  poda N, +21 ms medidos); busca global acento-insensível (Início +
  Ctrl+K; paleta do editor → Ctrl+Shift+P); LIXEIRA de 30 dias (soft
  delete nas 3 entidades, purga no boot com log, portabilidade filtra);
  indicadores de saúde em worker; modo apresentação tela cheia; e o gesto
  nº 1: "Duplicar semana passada". 428 verdes ×2; caderno com as 8
  checagens: `docs/FASE_2.md`.
- **FASE 3 — Configurações dignas + gestor de selos**: ▶ **EXECUTADA
  (19/07/2026) — os 100 passos na ordem; aguardando a reauditoria do
  arquiteto (passo 100)**. RG-59 curado (capa em COVER preenche o cartão,
  gradiente + nome sobreposto); Configurações reescritas em 9 abas
  verticais com busca de opções, salvar NA HORA (debounce 700 ms,
  inválido não sobrescreve), última aba lembrada, tela PREGUIÇOSA (não
  pesa no boot); aba Campanhas = gestor visual de eventos (arrastar
  reordena, duplo clique edita) + validade por evento COM consumo no
  sugerir_validade + frases prontas; aba IA = testar conexão em worker,
  status em linguagem simples (R-090), prompt do Fica a Dica editável
  com consumo e prévia real (R-088), interruptor mestre (ia.usar) com
  consumo no cliente; aba Imagens = upscale desligável com consumo,
  pasta da biblioteca, chaves-semente WebP/fundo-branco rotuladas
  Fase 10; aba Sanitização = glossários em TABELA (TabelaPares), ordem
  do nome reordenável consumida no prompt do enriquecer, palavras
  minúsculas, marcas próprias; aba Atalhos = catálogo central R-018
  (19 atalhos, remap aplica NOS VIVOS e persiste, conflito barrado,
  folha de cola em PDF, restaurar padrão); aba Sobre = novidades PT-BR,
  ícone A×B como CAMPO com consumo, top de erros, diagnóstico R-128;
  aba Backups = snapshot manual + verificar instalação (R-134) +
  compactar (R-135) + integridade com QUARENTENA (R-129) + perfil de
  máquina fraca (R-132, 4 chaves de uma vez); gestor de SELOS como
  ENTIDADE (migração idempotente, +18 TRAVADO em bebida, Qualidade
  desligável, composição lê o gestor, lei da casa 5ª aplicação, arte
  sumida avisa no pré-voo). **450 verdes ×2, zero skips; adversariais
  16/16**; caderno com as 7 checagens + resposta: `docs/FASE_3.md`.
- **FASE 4 — Editor I: consertar e destravar (INTENSIDADE MÁXIMA)**: ▶
  **EXECUTADA (19/07/2026) — os 100 passos na ordem; PARADO no passo 100
  aguardando a reauditoria do arquiteto**. RG-55 (preço que some)
  instrumentado e REPRODUZIDO antes de teorizar — o log provou a causa
  única (clique-grupo do RG-15 → painel órfão) e desmentiu z-order/rotação;
  cura: `resolver_selecao`, região `_primaria` clicada, `selecionada()`
  devolve a primária com o trio selecionado — **painel nunca órfão**
  (decisão travada no CLAUDE.md). RG-56 agrupar/desagrupar VISÍVEL e
  reversível: menu estado-consciente (solta→agrupar, mestra/cópia→
  desagrupar+inverso), `desagrupar_grupo` no modelo (nada se perde, undo
  num passo), badges permanentes M/C + legenda PT-BR, microtutorial de 3
  telas (memória + Ajuda › Como agrupar), lei da casa (SELO/TEXTO_LEGAL
  nunca agrupam). RG-49 seções sem linha interna: `_contorno_uniao`
  (fecha os vãos + perímetro externo, staircase quando a última linha é
  menor; run de 1 célula sem caixa) — adversarial por PIXEL da ausência de
  traço nos 4 estilos. RG-54 editor a 720p: Propriedades num QScrollArea
  (cabe em 720), lateral recolhível com memória, Camadas com fôlego.
  R-025/026 raio-x textual (valores + seleção 2 vias); R-027 guias
  arrastáveis (mm relativas, GuiaItem movível/removível, undo); R-028
  grade magnética on/off + passo; snap unificado (`alvos_snap`); Alt
  suspende. R-029 zoom-para-seleção + 100% + % com clamp; R-039 cadeado
  da arte (proteção/clareza — a arte é fundo de página, decisão travada);
  R-040 raio-x por cor (esconde a arte); R-041 medidas ao vivo (X/Y/L/A +
  cotas) + setas 1mm/0,1mm. Adversarial re-rodado (I1–I5) com 5 casos
  novos. **484 verdes ×2, zero skips; adversariais 21/21; boot do editor
  14ms (sem regressão)**; caderno com 8 checagens + resposta:
  `docs/FASE_4.md`. **SELADA pelo arquiteto (19/07/2026)** — reauditoria no
  disco real confirmou os consertos; o "must-fix #5" era falso positivo (o
  staging do arquiteto servia CLAUDE.md obsoleto).

- **FASE 5 — Editor II: ferramentas de profissional**: ▶ **EXECUTADA
  (19/07/2026) — os 100 passos, inline; PARADO no passo 100 aguardando a
  reauditoria do arquiteto (frota lendo o disco real)**. Blocos A–G:
  **A** campos de texto com PAPEL nomeado (RG-57): `papel_texto`
  {LIVRE/LEGAL/VALIDADE/DICA}, diálogo nomeado com prévia, badge cor+ícone,
  troca por menu/painel, helper único `texto_composto_legal`, lei da casa
  reconfirmada (TEXTO_LEGAL não-ocupável). **B** máscara de forma (ret/arred/
  círculo, recorte por alpha, byte-idêntico no caminho padrão), enquadrar
  (zoom/foco por override de slot), pill atrás do nome, sombra/contorno,
  arrastar foto por uid (I1), centralizar na arte. **C** conta-gotas de estilo
  (só estilo, respeita F5.7), modelos de célula (rects relativos I3, uid
  fresco I1) + vitrine de fábrica, salvar-novo-layout, reflow harmônico (o
  nome cede com reticências; o preço manda). **D** miniaturas de página +
  histórico visual (salto de estado), prévia de impressão em mm (sangria/
  margem/corte), verificador de contraste WCAG, distribuir por espaçamento
  fixo. **E** migração RICA de layout antigo (infere o papel do conteúdo, de
  carona ao abrir, idempotente, testada com arte REAL de `arte/quintou/`) +
  pré-voo dos papéis novos (I2). **F** adversariais de máscara/modelo/conta-
  gotas por conteúdo; **achado próprio: lacuna I4** (campos do Bloco B não
  propagavam da mestra) corrigido + prova de mutação; I1–I5 reconferidos.
  **G** galeria NATIVA (badges legíveis), GIF do conta-gotas, jargão PT-BR,
  F5.7 íntegro, validade nunca vazia (RG-58). **538 verdes ×2, zero skips;
  prova de mutação em cada teste-pixel/adversarial/migração; boot ~58ms**;
  caderno + resposta do builder: `docs/FASE_5.md`. Subagentes: 4 scouts de
  leitura (~190k, barato); implementação 100% inline. **SELADA pelo arquiteto
  (reauditoria no disco real item-a-item + inspeção visual da galeria nativa).**

- **FASE 6 — Mesa I: a bancada arrumada**: ✓ **SELADA pelo arquiteto
  (reauditoria no disco real + inspeção visual)** — os 100 passos, inline.
  **A** RG-53: barra da Mesa por grupos+separadores,
  `setMinimumWidth(1)` (a janela chega a 1280 — antes presa em ~1757),
  `_reflow_barra` mede todos os widgets fixos; essenciais nunca no "···".
  **B** R-051 modo planilha (`planilha.py`+`DialogoPlanilha`): grade editável
  por teclado, sanitização RG-20, parser P0.3 (rejeita ambíguo, I2), célula-
  problema, reflete por uid, respeita override. **C** estante viva:
  `trocar_conteudo_slots` (R-057, uid troca/override fica no slot),
  `reordenar_estante` (R-055, arrasto), `duplicar_item` (R-069, uid novo),
  `filtrar_itens` (R-054)+barra de filtros. **D** R-061 rascunho automático
  (`core/rascunho.py`, ISOLADO de projetos/versoes, worker ~2min, recuperação
  por conteúdo, descarta ao salvar) + Ctrl+K na Mesa (R-017). **E** matriz
  override×mapa por teste. **F** adversariais F6 por conteúdo, I1–I5. **G**
  galeria NATIVA + jargão PT-BR. **554 verdes ×2, zero skips; prova de mutação
  em cada teste-chave; boot da Mesa 35,6ms**; caderno + resposta:
  `docs/FASE_6.md`. Subagentes: 4 scouts de leitura (~340k, barato); inline.

- **FASE 7 — Mesa II: produção em massa**: ✓ **SELADA pelo arquiteto (disco real
  + inspeção visual, 2026-07-20)**. Depois do selo dos
  3 fixes, o arquiteto mandou TERMINAR: **Bloco D** — `_split_multi` reconhece
  multi-preço na colagem (achado próprio: caía como preço "não entendido"), viaja
  ao ItemMesa por `conciliar_linhas(multi_precos=…)`; bateria de 9 colagens reais;
  multi-import de 20 arquivos com 1 corrompido (fila termina, corrompido nomeado,
  nenhum outro se perde, I2). **Casca visual:** `PromocaoDialog` (campo qtd+valor,
  pré-preenchido ao editar), observação no menu, estatística no rodapé (R-072,
  offline), combo de frases prontas no diálogo de papel (R-058, {data}/{evento}
  do `contexto_frases`), alerta de repetição por toast (R-059, lê o histórico das
  edições salvas por chave natural). **Bloco F:** galeria NATIVA claro+escuro (7
  artefatos), GIF do fluxo, jargão PT-BR. **600 verdes ×5, 0 skips, exit 0 limpo;
  prova de mutação onde tocou parser/fila.** Caderno: `docs/FASE_7.md` (seção
  "Conclusão da fase"). Fora (declarado): recorte-por-linha na tela cheia (OCR sem
  bbox). Subagentes: 0 (inline). **Aguardando a reauditoria final (disco real +
  galeria `saida_fase7/`).**  ⟨HISTÓRICO da reauditoria parcial abaixo⟩ O arquiteto
  reauditou no disco real e exigiu **3 fixes**, todos feitos COM prova: **#1** o
  segfault de teardown
  (raiz real: testes criam `MesaTela` com QTimer/worker vivos → `closeEvent` para
  o timer + `_trabalhos.encerrar()` + fixture autouse no conftest; **prova: 5×
  suíte exit 0 LIMPO**); **#2** multi-preço agora DESENHA (caminho de texto no
  `_desenhar_preco`, não cai como "sem preço"; prova por pixel); **#3** tela cheia
  R-052 (foto original ao lado no `ConciliacaoDialog` via `caminho_fonte`, MESMO
  serviço = paridade testada; recorte-por-linha deferido — OCR sem bbox). **Bloco
  C (modelo+desenho):** frases prontas {data}/{evento} (R-058), alerta de
  repetição (R-059), estatística offline (R-072), `PapelTexto.OBSERVACAO`
  condicional + coluna na planilha (R-071), diff por chave natural (R-062),
  checklist (R-063); densidade já existia (R-060). Adversarial dos tipos novos por
  conteúdo+pixel (I5). **581 verdes ×5, 0 skips, exit 0 limpo; prova de mutação em
  cada teste novo.** Subagentes desta etapa: 0 (inline). **Ficou de fora:** casca
  visual UI (seletor de frases, alerta como toast, rodapé de estatística, campo
  qtd+valor do multi-preço), Bloco D (bateria ampla do parser, multi-import de 20),
  Bloco F (galeria nativa/GIF/jargão), recorte-por-linha. Caderno: `docs/FASE_7.md`
  (seção "Conserto pós-reauditoria").

- **FASE 8 — Exportação e publicação**: ✓ **SELADA pelo arquiteto (disco real +
  inspeção visual, 2026-07-20)** — a frota adversarial caçou 1 crítico (Fábrica sem
  marca d'água) que foi corrigido antes do selo. **Decisão travada:
  social = OUTRO LayoutDef com a MESMA cadeia produto→slot (nenhum motor novo,
  reusa `compor_pagina`); MP4 opcional (ffmpeg via `shutil.which`+subprocess —
  degrada com aviso, nunca trava).** Blocos: **A** perfis (`app/rendering/perfis.py`
  — WhatsApp/Impressão/Stories, régua de bytes) + compartilhar (`compartilhar.py`,
  limite do SO honesto) + fila em lote (`ExportarDialog`, `TrabalhadorFila`, um erro
  não derruba). **B** marca d'água RASCUNHO (`marca_dagua.py`, ladrilhada) +
  aprovação sem migração (Config, editar volta a rascunho + editar-sem-salvar
  derruba a aprovação limpa) + `pode_exportar_limpo`. **C/E** `social.py` (Oferta do
  Dia de/por, carrossel, story, faixa — reuso genuíno do compositor). **D** `video.py`
  (slideshow R-142 frames/duração exatos; story R-139; degrada sem ffmpeg). **F**
  adversarial do carrossel por conteúdo (ordem load-bearing). **G** galeria NATIVA
  `saida_fase8/`, GIF, jargão. **631 verdes ×5, 0 skips, exit 0 limpo.**
  **A FROTA ADVERSARIAL (4 revisores) achou 1 CRÍTICO + consertos:** a Fábrica de
  cartazes exportava LIMPO sem marca (2ª porta esquecida) — corrigido + teste por
  conteúdo (imagem embutida no PDF); lote multipágina perdia páginas em silêncio —
  corrigido; adversarial do carrossel com shuffle inerte e teste "sem esticar" fraco
  — endurecidos. Caderno: `docs/FASE_8.md`. Fora (declarado): fila multi-projeto,
  MP4 multipágina no lote, animação isolada do preço no Story. Subagentes: 4 scouts
  + 4 revisores (inline). **Aguardando a reauditoria final (disco real + galeria
  `saida_fase8/`).**

- **FASE 9 — Conteúdo & IA II (a IA colega)**: ✓ **SELADA pelo arquiteto (disco
  real + inspeção visual, 2026-07-20)** — a frota achou 1 bug real (o "2x 5,00"
  WhatsApp) corrigido antes do selo. **TRÊS DECISÕES
  TRAVADAS:** (1) a IA NUNCA bloqueia o export — só informa; (2) NUNCA inventa
  marca/sigla/protocolo — só aprende o confirmado, ambíguo→amarelo; (3) sem IA,
  tudo degrada para fuzzy/manual COM aviso (ponto único `_motor_se_disponivel`).
  **Flagship:** `app/ai/revisora.py` (R-081) — revisora do export por VISÃO
  (compara lido×dados) com degradação HEURÍSTICA (nome cortado/de≤por/preço fora de
  faixa), nunca bloqueia/altera/levanta. `sentinela.py` (R-078), `deduplicacao.py`
  (R-075, funde por chave natural, soft-delete reversível, marca diferente nunca é
  par), `aprendizado.py` (R-087 marca só conhecida — nunca inventa; R-086 sinônimos).
  Chat da oferta (R-073, reusa conciliação), manchete (R-074), dica com estilos
  (R-083), fila com prioridade (R-089). **650 verdes ×5, 0 skips, exit 0 limpo.**
  **A FROTA (4 revisores) achou:** um BUG real ("2x 5,00" WhatsApp aceito calado —
  corrigido), um teste fraco (marca Camil/Camilo — blindado), robustez da revisora
  (nunca levanta — corrigido), teste dedicado do worker da revisora. Caderno:
  `docs/FASE_9.md`. Fora (declarado): UI de fusão de duplicatas, avaliador de foto
  (R-085), autodetecção de variações (R-082), demo com LM Studio real (rodou com IA
  fake — a máquina de bancada não tem o servidor de visão). Subagentes: 4 scouts +
  4 revisores (inline). **Aguardando a reauditoria final (disco real + galeria
  `saida_fase9/`).**

- **FASE 10 — Imagens II + Estúdio IA**: ▶ **EXECUTADA até o passo 100 (2026-07-20);
  PARADA no ponto de reauditoria; NÃO SELADA.** **DECISÃO TRAVADA:** o Estúdio tem 2
  degraus — o DEGRAU 1 (rembg + luz + sombra sintética, `app/images/estudio.py`) é o
  PADRÃO GARANTIDO (roda em CPU, prova por pixel: fundo transparente + sombra); o
  DEGRAU 2 (img2img SDXL) é opção condicionada à GPU, NUNCA requisito (degrada com
  aviso; guarda anti-alucinação `diferenca_demais`). **Bancada sem GPU** → degrau 1
  real, degrau 2 provado no encanamento (motor fake) e declarado. Curadoria
  não-destrutiva (`curadoria.py`: girar/cortar/espelhar R-094, refino R-103,
  fundo-branco R-095 ligado ao pipeline, WebP com alfa R-100); genéricas marcadas
  (R-099), foto repetida por hash (R-104), upscale que mira o alvo (R-101). **665
  verdes ×5, 0 skips, exit 0 limpo.** **A FROTA achou:** um BUG real (upscale
  ampliava 3× além do alvo para foto não-quadrada — corrigido, mira o MAIOR lado) +
  toggles WebP/fundo-branco mortos (fundo-branco ligado; textos honestos) + teste
  fraco de girar (blindado por conteúdo). Caderno: `docs/FASE_10.md`. Fora
  (declarado): SDXL real do degrau 2, migração automática do acervo para WebP, UI rica
  da curadoria. Subagentes: 4 scouts + 4 revisores (inline). **Aguardando a
  reauditoria final (disco real + galeria `saida_fase10/`).**
- **FASE 11 — Cartaz & Fábrica completos + inteligência**: ▶ **EXECUTADA até o passo
  100 (2026-07-20); PARADA no ponto de reauditoria; NÃO SELADA.** **DECISÕES
  TRAVADAS:** cartaz = 1 item/página no tamanho FÍSICO exato (mm), RGB; biblioteca de
  layouts (`app/rendering/cartaz.py` `PRESETS_CARTAZ`: A4 retrato/paisagem, A5,
  etiqueta); **% de desconto CALCULADO (de−por)/de, nunca digitado**
  (`compositor.percentual_desconto` + `PapelTexto.DESCONTO`); validade no rodapé nunca
  vazia (papel VALIDADE + pré-voo, RG-58); **2-em-1 (R-106) SÓ no cartaz e SÓ se ligado,
  NUNCA no tabloide** (`app/rendering/imposicao.py`, A4 paisagem + marcas de corte,
  guarda testada); **cartaz-relâmpago (R-110) do Almoxarifado ao PDF num clique,
  sempre RASCUNHO**; kit ponta-de-gôndola (R-113, cartaz+etiquetas coerentes, uma
  fonte de verdade); QR opcional (R-114, `app/rendering/qr.py`); **impressão direta
  (R-112, `app/rendering/impressao.py`) respeita mm E orientação** via `QPageLayout`
  (Fábrica ganhou closeEvent, lei exit-0); lote por categoria (R-108, reusa
  `filtrar_itens`); **Excel (R-118, `app/core/excel_acervo.py`) casa por CHAVE
  NATURAL, prévia→confirma, conflito nominal (I2), sem foto/caminho (I3), roundtrip
  idempotente**; **inteligência SÓ LEITURA e LOCAL** (`app/qt/telas/inteligencia.py` +
  `inteligencia_dialog.py`: histórico de preço R-115, relatório R-117, ranking R-120,
  sazonal R-121, meta R-122, divergência-por-uid R-123, saúde R-126); **VETADOS
  ausentes por varredura de identificador: R-116/119/124/125**. **714 verdes ×5, 0
  skips, exit 0 limpo** (+49: `test_fase11_cartaz.py` 48 + 2 adversariais). **A FROTA
  (4 revisores adversariais no fecho) achou 6 bugs reais (refutou 2), TODOS corrigidos
  antes do selo:** [CRÍTICO] o Excel casava o conflito por ID em vez de chave natural
  (renomear entre analisar/aplicar corromperia o produto errado, I1) — corrigido com a
  guarda E-A2 que a portabilidade já tinha; [ALTO] `_parse_data` não lia a célula de
  DATA real do Excel (validade sumia calada); [ALTO] o 2-em-1 cortava calado com preset
  >A5 (guarda dura + o toggle só habilita no A5); [MÉDIO] histórico não deduplicava por
  edição; +2 baixos (preview do conflito, pré-voo do lote). **Achados próprios:** a
  impressão saía RETRATO num layout paisagem (o Qt normaliza o `QPageSize`) — corrigido
  com `QPageLayout`; a reescrita do `layout_cartaz_exemplo` quebrou 3 testes que
  cravavam estrutura incidental — consertados derivando da produção (I5); a varredura
  de vetos pegava prosa — refeita por identificador. Boot: saúde em 5k = 48ms; Fábrica 14ms;
  InteligenciaDialog 14ms (inteligência sob demanda). Caderno: `docs/FASE_11.md`.
  Galeria `saida_fase11/` claro/escuro + GIF do relâmpago. Subagentes: 4 scouts + 4
  revisores (inline). Próxima após o selo: `docs/FASE_12.md` (a última — precisa do
  Otaviano). **Aguardando a reauditoria final.**
