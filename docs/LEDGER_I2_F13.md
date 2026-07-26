# LEDGER I2 — F13 (COND-9 do selo do Bloco E)

> O débito de degradação silenciosa (I2) NÃO vive em prosa — vive aqui,
> uma linha por item, com desfecho. Criado no Bloco F; **o G só fecha com
> zero ABERTO** (um item pode ser DISPENSADO PELO DONO com motivo; o que
> não pode é desaparecer — a lição do K-03). Fonte: varredura + dossiê
> (os 47), conferidos no código vivo pelo scout do Bloco E (25/07/2026).

Desfechos: **CONSERTADO (bloco)** · **DISPENSADO PELO DONO (motivo)** ·
**ABERTO**. Linhas de código = as de 25-26/07/2026; conferir ao mexer.

| ID | O que se perde em silêncio | Onde (hoje) | Desfecho |
|---|---|---|---|
| CA-01 | boot baixava 973 MB sem pedir; aquecer engolia tudo | editor_app/fundo | **CONSERTADO (E1)** |
| CA-02 | erro fatal no exe morria mudo (console=False) | spec/workers/entrypoints | **CONSERTADO (E2)** |
| CA-03 | pasta sem escrita matava o boot antes da janela | paths/editor_app | **CONSERTADO (E3)** |
| CA-04 | pythonw nunca recebe as fontes (semeio só se frozen) | lancar_autotabloide.py:40,71 | ABERTO |
| CA-05 | 1º boot: Mesa nasce com grade sintética sem explicação | editor_app.py:115-152 | ABERTO |
| CA-08 | check.svg e exportou.wav fora do datas do spec | autotabloide.spec:19-47 | ABERTO |
| CA-t1 | o app manda "ver o console" num exe sem console | editor_app.py:455,469 | ABERTO |
| CB-01 | snapshot do boot copiava banco corrompido | cofre.py | **CONSERTADO (B5)** |
| CB-02 | Cofre/.atpkg escreviam em somente-leitura | cofre/portabilidade | **CONSERTADO (E4)** |
| CB-03 | lixeira purga de vez em somente-leitura, no boot | editor_app.py:446-447 → lixeira.py:135 | ABERTO |
| CB-04 | recuperar de VERSÃO grava sem checar somente-leitura | recuperacao.py:203-255 | ABERTO |
| CB-05 | restauração de backup falha e o dono não vê NADA | qt/telas/cofre.py:419 (sem try) | ABERTO |
| CB-08 | .atproj não confere se os arquivos citados chegaram | atproj.py:53-66 | ABERTO |
| CB-09 | rascunho: último arquivo truncado = perde tudo, mudo | rascunho.py:108-117 | ABERTO |
| CB-t1 | migração antiga descarta peso/aliases do existente | migracao_antiga.py:87-99 | ABERTO (parcial: o lote conta) |
| CB-t2 | "a falha fica REGISTRADA" via logging sem basicConfig | projetos.py:111-116 | ABERTO |
| CC-01 | "Corrigir nomes" jogava a categoria calculada fora | enriquecer_banco.py | **CONSERTADO (E5)** |
| CC-02 | o botão que reescreve o acervo INTEIRO não pergunta | almoxarifado.py:862-894 | ABERTO |
| CC-06a | lote para no produto 10.000 sem contar o resto | enriquecer_banco.py:39,100 | ABERTO |
| CC-06b | selfcheck_marco apaga saida_marco/ inteira | selfcheck_marco.py:65-67 | ABERTO (bancada) |
| CC-06c | zip posicional no selfcheck; sobras somem sem nome | selfcheck_marco_f12.py:141-143 | ABERTO (bancada) |
| CC-06d | selfcheck conta pendências e nunca falha por elas | selfcheck_marco.py:199-201 | ABERTO (bancada; o H5 cobre) |
| CC-06e | 3 cópias de parser de preço ingênuo (1 na produção) | editor_app.py:32-36 + 2 scripts | ABERTO |
| CC-06f | renomear invalida o índice de significado sem avisar | conciliacao.py:259-262 + toast | ABERTO (menor) |
| CD-01 | editar nome/preço apagava a pilha de desfazer | mesa.py | **CONSERTADO (B1)** |
| CD-02 | desfazer não volta para a página do gesto | historico.py:36-41 + canvas.py:604 | ABERTO |
| CD-05 | a Mesa muta o mapa fora do histórico | mesa.py:449-470 | MITIGADO (contrato + desfazer por uid no toast) — dono decide no G |
| CD-08 | Ctrl+Z sem nada p/ desfazer é 100% mudo no Ateliê | barra_editor.py:58-61 | ABERTO |
| CD-t1 | desfazer lê do disco sem proteção (arquivo sumido) | historico.py:104-111 | ABERTO |
| CD-t2 | combo de modelo da Fábrica descarta o layout mudo | fabrica.py:265-278 | ABERTO |
| CE-01 | rótulo da seção desenhado antes; a foto o apaga | compositor.py (seções antes do conteúdo) | ABERTO |
| CE-04 | cor de seção inválida derruba o export com ValueError | secoes.py:192-193 | ABERTO |
| CF-04 | Enter no "Importar do banco" clica CANCELAR | importar_banco_dialog.py:58-68 | ABERTO |
| CF-t1 | Esc na Conciliação joga fora a importação inteira | conciliacao_dialog.py (reject sem confirmar) | ABERTO |
| CH-06 | 2 hard-deletes sem chamador + funções nunca chamadas | repositories/persistencia | **CONSERTADO (B10)** nos hard-deletes; `capa_do_evento` morta ABERTO |
| CI-01 | conciliação não enxergava a lixeira (excluído = VERDE) | conciliacao.py (_corpus) | **CONSERTADO (E5)** |
| CI-02 | categoria corrigida no Excel apagada pelo próximo passe | excel_acervo.py:421-431 (sem origem "humano") | ABERTO |
| CI-03 | o juiz pintava VERDE com qualquer confiança | conciliacao.py | **CONSERTADO (B7)** |
| CI-05 | a foto ORIGINAL apagada em silêncio na 11ª troca | biblioteca.py | **CONSERTADO (B4)** |
| CI-06 | recorte transparente virava retângulo PRETO no cartaz | upscale.py | **CONSERTADO (E5)** |
| R-06 | fundo ausente vira página branca; tamanho estica cru | compositor.py:653-659 | ABERTO |
| R-07 | imagem de produto ausente pulada no desenho | compositor.py:196-197 | COBERTO: o pré-voo acusa ANTES em toda porta (validar_composicao) — degradação com aviso |
| D-03 | fusão de duplicatas perde foto em silêncio | deduplicacao.py:136-137 + toast sem o contador | ABERTO (parcial: contador existe, toast não mostra) |
| D-04 | verificar_acervo é except-pass | recuperacao.py:295-296 | ABERTO |
| D-05 | rmtree(ignore_errors=True) na lixeira | lixeira.py:96,100 | ABERTO |
| A-04 | campo Peso apaga dado sem avisar (regex não casa) | almoxarifado.py:632-643 | ABERTO |
| L-09 | sair do editor sujo não perguntava | atelie.py | **CONSERTADO (B2e)** |
| — | (extra do scout) foto extra fora da biblioteca some da lista multi | servico.py:457-461 | ABERTO |
| — | (invalidado) selfcheck sem carimbo RASCUNHO | — | INVALIDADO pelo D8 (o padrão agora é limpo) |

**Placar em 26/07/2026: 47 rastreados + 1 extra do scout = 48 linhas ·
13 CONSERTADOS · 1 COBERTO (pré-voo) · 1 MITIGADO (decisão no G) ·
1 INVALIDADO · 32 ABERTOS · 0 DISPENSADOS.**
