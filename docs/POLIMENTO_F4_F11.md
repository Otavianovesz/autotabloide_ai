# Passe de POLIMENTO pré-F12 — auditoria com olhos frescos + a dívida de UI

> Builder: **Fable** (assumindo do ponto em que o Opus parou, F4–F11
> executadas). Ordem do arquiteto: auditar as fases 4–11, polir BELEZA e UI —
> polimento DISCIPLINADO, aditivo, sem reescrever o miolo selado.
> **Baseline (antes de tocar em nada): 714 verdes, 0 skips, exit 0** — bateu.
> **Placar final: 729 verdes (+15), 0 skips, exit 0 limpo** (detalhe no fim).

## Como foi auditado

4 scouts de LEITURA (read-only, nenhum escreveu): design system F1 +
inconsistências (cores hardcoded, dark mode) · modelos F9/F10 órfãos de UI ·
telas F6/F7/F11 com dívida declarada · auditoria visual "olhos frescos" de
TODOS os diálogos + o padrão de screenshot nativo. A lista de dívida veio dos
"o que ficou de fora" dos cadernos FASE_4..11 — implementação 100% inline.

## O que mudou, por fase de origem

### F6 (Mesa I — modo planilha)
- **Colar do WhatsApp/Excel (passo 23 adiado):** `Ctrl+V` no modo planilha
  cola nome×preço e ATUALIZA os preços **casando pelo nome** (o uso real: a
  lista da semana com preços novos). Reusa `parse_colagem` + `aplicar_edicao`
  (P0.3: ambíguo "2x 5,00" NÃO grava); linha sem par fica no aviso (I2).
- **Edição em massa (passo 22 adiado):** botão direito → "Aplicar categoria
  às selecionadas" — `aplicar_edicao` em loop, reflete no canvas por uid.
- Célula-problema usava um rosa FIXO (o token `PERIGO_SUAVE` referenciado
  nunca existiu — o fallback hardcoded valia sempre e clareava no tema
  escuro) → `PERIGO_FUNDO` real, nos dois temas (idem `colagem_dialog`).

### F7 (Mesa II)
- Multi-preço qtd+valor: **auditado, já estava completo** (`PromocaoDialog`
  com formato/qtd/valor/prévia) — nada a fazer; registrado para não "sobrar"
  na lista de dívida.

### F8 (Exportação/publicação)
- `ExportarDialog`: margens/spacing do design system (rodava nas margens de
  fábrica do Qt), tooltips, `EstadoVazio` quando não há perfis.
- `PublicarDialog`: margens, tooltips nos 4 formatos, "feed"→"redes",
  "slideshow MP4"→"páginas em MP4" (PT-BR), rótulo do destaque com papel.
- `SalvarProjetoDialog`/`AbrirProjetoDialog`: spacing do form, tooltips,
  `EstadoVazio` ("Nenhum projeto salvo ainda") no lugar do retângulo mudo.
- `cofre.MesclagemDialog`: margens + título com papel + tooltip no "Aplicar".

### F9 (IA colega)
- **Fusão de duplicatas (dívida nº 1):** `duplicatas_dialog.py` — o par LADO
  A LADO (foto+nome+marca+preço), motivo visível ("mesmo EAN"/"mesmo nome e
  marca"), decisão POR PAR; botão "Duplicatas" no Almoxarifado. Serviços
  novos finos em `servico.py` (`pares_duplicatas`/`fundir_duplicatas`) sobre
  o modelo selado (`deduplicacao.py` — que não tinha NENHUM chamador de UI).
- **Estilo da dica (R-083):** combo receita/economia/curiosidade no painel de
  propriedades — `gerar_dica` sempre aceitou `estilo=`/`evitar=`; a UI nunca
  os passava (o texto atual agora entra em `evitar`, não repete).
- **Manchetes (R-084):** botão "Sugerir manchetes (IA)" no diálogo de papel
  de texto (papel LIVRE) — `sugerir_manchetes` rodava só em script; degrada
  sem IA para a lista padrão com o evento (sempre útil, I2). Worker com
  encerramento no `done()` (lei exit-0).

### F10 (Imagens II / Estúdio)
- **Editor de ajuste** (`ajuste_imagem_dialog.py`): girar ⟲⟳ / espelhar /
  **cortar por seleção de arrasto** (QRubberBand mapeada widget→imagem) com
  prévia ao vivo — sobre o `curadoria.py` puro; o resultado vira NOVA versão
  (não-destrutivo, I1). Botão "Ajustar…" no painel do produto.
- **Estúdio ligado:** botão "Estúdio" no painel chama `tratar_estudio` (o
  packshot degrau 1 — que estava DEFINIDO E NUNCA CHAMADO por nenhuma UI).
- **Comparador de versões:** o `HistoricoImagensDialog` agora mostra ATUAL ×
  ESCOLHIDA lado a lado, em grande — o dono compara antes de restaurar.
- **Fonte "Do acervo…"** na curadoria (`acervo_picker_dialog.py`): grade das
  fotos já na biblioteca com filtro por nome — devolve o MESMO contrato
  ("arquivo", caminho) do fluxo de sempre (mudança mínima; a foto é COPIADA
  para o produto, nunca compartilhada — I1). *(A "aba Web/Acervo" da dívida
  foi entregue como fonte no mesmo diálogo — sem reestruturar um diálogo
  premium usado por 4 fluxos.)*

### F11 (Cartaz & Fábrica + inteligência)
- **RG-53 na barra da Fábrica:** a barra ganhou muitos controles na F11 e
  NÃO aplicava o padrão da Mesa — a 720p pinava a janela mais larga que a
  tela (risco real, sem teste). Portado por inteiro: `setMinimumWidth(1)`,
  grupos com separador, combos que encolhem, "···" com sacrificáveis
  (checkbox vira ação checável — nada some), reflow genérico em
  `showEvent`/`resizeEvent` + **teste-espelho** do da Mesa.
- **Prévia de impressão NATIVA:** `QPrintPreviewDialog` entre o QPrintDialog
  e a impressão — o dono VÊ as folhas antes de gastar papel; cancelar na
  prévia não imprime.
- **Opções do relâmpago** (`relampago_dialog.py`): QR opcional (desligado por
  padrão — decisão travada R-114) e nº de etiquetas do kit — parâmetros que o
  serviço sempre aceitou e nenhum widget oferecia.
- **Meta viva na barra da Mesa (R-122):** com meta definida, o "N item(ns)"
  vira o pulso "32/40" (tooltip diz a meta; atingiu ganha ✓) — informativo.
- **Eixos rotulados no histórico de preço:** R$ (máx/mín) à esquerda, datas
  (primeira/última edição) embaixo, linhas de grade leves — antes era uma
  linha sem referência.
- `InteligenciaDialog`/`ImportarPlanilhaDialog`: margens/spacing tokens,
  títulos com papel, `EstadoVazio` com craft em TODAS as abas vazias,
  tooltips, e o **"Cancel" em inglês** do QDialogButtonBox relabelado
  ("Importar"/"Cancelar"). Preview de conflito já sai o antes→depois por
  campo (consertado no fecho da F11).

### F4/F5 (editor)
- Auditados por leitura (scout 4): os diálogos do editor e o
  `conciliacao_dialog`/`curadoria_dialog` **já estavam no padrão premium**
  (margens, papéis, EstadoVazio, tooltips) — só tooltips pontuais somados na
  curadoria. As dívidas declaradas da F4 (cota região↔região, reposicionar
  arte) são de FUNCIONALIDADE deferida pelo arquiteto, não de beleza — não
  tocadas (mudança mínima).

## Leis respeitadas (o que NÃO mudou)
- **Nenhuma linha do compositor/render** (`compor_pagina`, `_desenhar_*`,
  export, imposição) foi tocada — os testes de pixel/byte selados seguem
  sendo o juiz, todos verdes.
- Nenhum serviço selado foi reescrito: as cascas chamam os MESMOS serviços
  (`deduplicacao`, `curadoria`, `tratar_estudio`, `parse_colagem`,
  `aplicar_edicao`, `progresso_meta`, `sugerir_manchetes`…).
- Workers novos encerram no `close`/`done` (manchetes no `done()` do diálogo;
  fusão/ajuste/estúdio rodam no `GerenciadorTrabalhos` do Almoxarifado, que o
  gancho global já cobre).
- Adversarial do vínculo re-rodado (a fase não tocou slot/região — verde).

## Bugs reais achados na auditoria (consertados COM teste)
1. **Fábrica sem RG-53** (overflow a 720p — funcional, não só estética) →
   portado + `test_barra_fabrica_720p_essenciais_e_estouro`.
2. **`PERIGO_SUAVE` fantasma** (`hasattr` sempre falso → rosa fixo hardcoded
   no tema escuro) em `planilha_dialog` + hardcodes irmãos em
   `colagem_dialog` → tokens reais + `test_sem_perigo_suave_fantasma`.
3. **"Cancel" em inglês** no import de Excel → relabel + teste.

## Dívida de UI: fechada × restante
**Fechada:** fusão de duplicatas · girar/cortar com prévia · comparador de
versões · fonte Acervo · Estúdio ligado à UI · estilo da dica · manchetes ·
QR/etiquetas do relâmpago · prévia de impressão nativa · meta na barra ·
eixos do gráfico · colar+massa na planilha · consistência (margens, PT-BR,
EstadoVazio, tooltips, dark mode dos destaques).
**Restante (declarado, não silencioso):** pincel de refino interativo
(`refinar_alfa` tem modelo e teste; a UI de pincel pixel-a-pixel é candidata
a pós-F12) · QR como REGIÃO editável do layout (hoje é opção do relâmpago) ·
fila multi-projeto do export (F8, funcionalidade) · paleta de eventos e preto
do modo apresentação (hardcoded POR DESIGN — documentado, não é bug).

## Fecho
- Galeria NATIVA (grab() real, sem offscreen) em `saida_polimento/claro` e
  `saida_polimento/escuro` — 12 artefatos × 2 temas, inspecionados.
- **Suíte: 729 verdes ×2, ZERO skips, exit 0 limpo; exit-0 5× no total.**
- Subagentes: 4 scouts de leitura (~0 escrita). Implementação inline.

**PARADO para a reauditoria do arquiteto** (foco: inspeção visual das telas
polidas claro+escuro; diffs × suíte selada). A Fase 12 não começa sem o selo.

---

## Rodada 2 do polimento (pedidos diretos do dono, 20/07 à noite)

**O dono apontou:** (1) o desenquadramento — telas recortadas ao trocar de
aba, botões sem espaço pro texto, só sair/entrar da tela cheia consertava;
(2) o Início sem o dashboard planejado, com os grupos de ofertas ocupando
tudo; (3) conferir a implementação e a lógica das fases; (4) a logo/ícone.
Tudo inline, sem subagentes.

### O desenquadramento — CAUSA-RAIZ achada e curada (3 pernas)
1. **`crossfade` punha `QGraphicsOpacityEffect` na PÁGINA VIVA** — no
   Windows isso renderiza o widget num cache e a tela ficava
   recortada/mal pintada até um resize externo (exatamente o
   sair/entrar da tela cheia). Agora o fade é numa **FOTO estática** da
   tela antiga (QLabel morto) por cima — a tela real pinta direto, sempre;
   troca sobre troca remove o véu anterior na hora.
2. **Resize SINTÉTICO pós-troca** (`Shell._reenquadrar`): a tela que estava
   oculta podia carregar geometria velha (a janela mudou de tamanho com
   outra tela na frente) — agora, um `QTimer.singleShot(0)` ativa o layout
   e despacha um `QResizeEvent` com o tamanho REAL; as barras RG-53 e os
   canvases re-medem com o número certo.
3. **Guarda de medição** nos `_reflow_barra` (Mesa e Fábrica): barra com
   largura irreal (<60 px, layout não assentado) não mede — evita colapsar
   botões por número falso; o resize sintético re-chama na hora certa.

### O Início virou o dashboard planejado (2 abas)
- **"Visão geral"**: cartões de número (produtos no acervo, % com foto,
  edições salvas, próximo evento pela agenda), **"Retomar de onde parou"**
  (últimas edições, duplo-clique reabre) e a **saúde do acervo em barras**
  — dados por worker no showEvent (boot intacto), reusando a inteligência
  SÓ-LEITURA da F11.
- **"Ofertas por evento"**: os grupos/prateleiras que antes ocupavam a tela
  inteira moram nessa aba (comportamento interno preservado — os testes do
  dashboard seguiram verdes sem mudança).

### Logo e ícone
- `pixmap_logo` (splash.py): a marca de verdade — encarte inclinado +
  etiqueta de desconto "%", 100% vetorial (nítida de 16 a 512 px), com a
  variante laranja Belo Brasil (chave `app.icone` da F3 preservada).
- Splash e ícone da janela usam a MESMA logo; `app/scripts/gerar_logo.py`
  grava `assets/logo.png`, `logo.ico` (multi-tamanho, p/ o instalador da
  F12) e `logo_belo_brasil.png`.
- **Barra de tarefas do Windows:** `SetCurrentProcessExplicitAppUserModelID`
  no boot — sem isso o processo agrupava como "python" e o ícone da barra
  saía o do interpretador.

### Auditoria de completude e lógica (honesta)
- Varredura de `TODO/FIXME/NotImplementedError` no `app/`: **zero** achados
  reais (só "TODO"=«todo» em prosa PT-BR).
- A dívida declarada dos cadernos F4–F11 foi cruzada na rodada 1 (acima) —
  fechada ou declarada; nada silencioso.
- **2 lógicas burras achadas e corrigidas COM teste:** (a) o colar da
  planilha casava por nome SEM tirar acento — "CAFE 500G" do WhatsApp nunca
  casaria com "Café 500g" da estante; agora usa a normalização da chave
  natural; (b) o cartaz-relâmpago NUNCA tinha o preço "de" (o acervo só
  guarda o atual) — o diálogo agora coleta de/por (o "por" vem preenchido).

**Placar: 729 verdes ×2, ZERO skips, exit 0 limpo.** Artefatos novos:
`saida_polimento/*/inicio_visao_geral.png`, `inicio_ofertas_por_evento.png`,
`logo_folha_contato.png`.

---

## Rodada 3 (pedidos do dono, 20/07 mais tarde)

1. **Configurações sem redundância:** a aba saiu da navegação — a tela mora
   SÓ na engrenagem ("Configurações completas…"). `ir_para("configuracoes")`
   segue funcionando por código (TELAS_CHAVES a mantém navegável).
2. **Aba EVENTOS própria** entre Início e Ateliê (`EventosTela`): os grupos
   de ofertas (grade de campanhas + prateleiras + visão do evento) saíram do
   Início — a EventosTela ADOTA a `_pilha` do Dashboard (mesmos objetos e
   métodos; nenhum fluxo mudou; os testes de conteúdo seguem achando tudo
   porque a pilha nasce filha oculta do Dashboard até a adoção). O botão
   "Novo evento" mudou para lá (onde as campanhas vivem).
3. **Dashboard deslumbrante:** cartões `_CartaoIndicador` pintados à mão
   (barrinha viva no topo na cor do assunto, chip de ícone colorido, número
   grande, hover, CLICÁVEIS — produtos/foto → Almoxarifado, edições/evento →
   Eventos; leem os tokens NA PINTURA, acompanham o tema); barras de saúde
   SEMÂNTICAS (verde ≥80, âmbar ≥50, vermelho <50); "Retomar de onde parou"
   com MINIATURA da edição.
4. **VALIDADE — a regra do negócio corrigida (auditoria de lógica):**
   - A campanha de dia fixo vale **SÓ NO DIA**: `sugerir_validade` agora
     devolve "SOMENTE dd/mm" (era "ATÉ dd/mm", que lia como intervalo);
     `montar_validade_oferta(de==até)` → "OFERTA VÁLIDA SOMENTE dd/mm".
   - A exceção do jornal do mês: a regra "válido por N dias" (Config F3)
     segue "ATÉ hoje+N", e — **bug real achado** — a validade ESCRITA NA
     TABELA era extraída pelo parser e IGNORADA na importação (só valia ao
     reabrir projeto); agora `Mesa._conciliar` a aplica na hora ("Validade
     veio da tabela"), sem sobrescrever uma definida à mão.
   - Testes das fases 2/3/onda-4 atualizados para a regra nova (mudança de
     comportamento PEDIDA pelo dono, documentada — não mascaramento).

**Placar: 729 verdes ×2, ZERO skips, exit 0.** Artefatos:
`saida_polimento/*/inicio_visao_geral.png` (o dashboard novo),
`tela_eventos.png` (a aba própria), claro+escuro.
