# Auditoria de Cobertura — código × Documentação-Mestre

> Gerada em 2026-07-08 pelo builder (Claude Code), a pedido do Otaviano, cruzando o
> código atual com a **Documentação-Mestre** (.docx, que consolida o Pacote de Decisão
> e os Adendos 1–2), a `VISAO_COMPLETA.md` e o plano. Legenda:
> **✓ feito** · **▶ parcial** · **○ falta** (com a fase onde está prevista).
> Atualizar este arquivo quando fases fecharem.

## §1–2 Visão, escopo e arquitetura

| Item da doc | Estado | Nota |
|---|---|---|
| Um app, dois produtos, back-end compartilhado | ✓ | Mesa (tabloide) + Fábrica (cartaz) reusam serviço/conciliação/motor |
| Offline-first; IA local desacoplada (API padrão) | ✓ | `ClienteOpenAICompat`; degrada sem LM |
| Camadas UI / serviços / dados / IA / render independentes | ✓ | `app/qt` · `app/qt/telas/servico` · `app/core` · `app/ai` · `app/rendering` |
| System Root com as 8 pastas | ✓ | F0 |
| Portabilidade (exportar/importar banco + imagens, mesclar) | ○ | Cofre (F6.6) + F7.4 |
| Sem camada industrial / criptografia / mobile | ✓ | Cortado como decidido |

## §3 Banco de dados

| Item | Estado | Nota |
|---|---|---|
| Tabelas (Produto, Alias, Categoria, Layout, ProjetoSalvo, Config) | ✓ | Schema pronto |
| Vivo × congelado (projeto salvo com overrides por slot) | ▶ | **Schema existe; o fluxo salvar/reabrir projeto congelado não está ligado à UI** (F6.8/F7.3) |
| Padrão de nome + configurável | ▶ | Regras via `regras_de_config` ✓; tela de Configurações ○ (F6.7) |
| Aliases que crescem com o uso | ✓ | Conciliação + "Aceitar" da Mesa aprendem |
| Imagens em disco com versões | ✓ | Biblioteca (F4.4), poda configurável |
| **Enriquecimento persiste no banco** | ✓ | **Corrigido nesta auditoria**: fluxo 🔴 da Mesa persiste; `enriquecer_banco` (novo) atualiza o acervo (rodado: 35 nomes limpos) |

## §4 IA e conciliação

| Item | Estado | Nota |
|---|---|---|
| 3 camadas (embeddings → fuzzy → juiz), nunca o banco todo | ✓ | Gates fechados com Qwen real |
| Semáforo com aprovação humana; só avança tudo verde | ✓ | Diálogo de conciliação da Mesa/Fábrica |
| OCR foto→tabela + validade da oferta | ✓ | 42/42 no print real |
| Importa a tabela inteira, sempre | ✓ | |
| Categorização IA corrigível pelo usuário | ▶ | IA atribui e persiste ✓; correção manual = Almoxarifado (F6.3) |
| Trocar modelo / 4-8 bits nas Configurações | ○ | F6.7 |

## §5 Imagens

| Item | Estado | Nota |
|---|---|---|
| Busca web + pop-up de escolha | ✓ | **ddgs/DuckDuckGo** (a doc cita icrawler/Google — superado, o icrawler quebrou; atualizar a doc) |
| Colar / arquivo / URL | ✓ | Curadoria da Mesa |
| Arrastar para o slot; refinar busca (mudar termo) | ○ | Próxima fatia da Mesa |
| rembg birefnet + recorte/normalização | ✓ | |
| Upscale condicional (Real-ESRGAN) | ▶ | Motor pronto (F4.3); **não ligado ao fluxo da curadoria** (hoje só rembg) |
| Múltiplas imagens no slot (leque/lado a lado/repetir) | ▶ | Compositor pronto (F4.5); UI de escolher sabores/2 produtos ○ (F7.1/7.2) |

## §6 Motor visual e editor

| Item | Estado | Nota |
|---|---|---|
| Editor de camadas próprio (não SVG rasterizado), WYSIWYG Pillow | ✓ | Gate de fidelidade fechado com a arte real |
| Grade + célula-mestre com propagação e override por célula | ✓ | F5.5 completa (âmbar, restaurar da mestra, indicador) |
| Agrupamento livre replicável | ○ | F5.6 (a âncora `origem_mm` já prepara) |
| Multipágina / auto-flow / feed Instagram | ○ | F5.8 |
| Regiões nomeadas (todas) + preço separado/completo, de/por, **riscado**, moeda da arte | ✓ | Riscado entrou na F6.5 |
| Texto só-reduz, hífen, justificado, unidade dentro/fora | ✓ | |
| Estilos nomeados reutilizáveis + override por instância | ▶ | Seletor de fontes ✓ (F5.7 parcial); estilos nomeados ○ |
| Texto ao vivo no canvas (digitar direto) | ○ | F5.9 (hoje edita pelo painel) |
| Máscara círculo/forma | ○ | Ponto em aberto da doc |
| Camadas globais (faixas de categoria, textos legais fora do slot) | ▶ | TEXTO_LEGAL por slot ✓; faixas de categoria ○ (F8.2) |

## §7 As telas

| Tela | Estado | O que falta |
|---|---|---|
| Dashboard | ○ | F6.1 (pastas por evento, histórico) — depende de projeto salvo |
| **Ateliê** | ✓ (núcleo, 2026-07-08) | Busca/filtro por tipo, "definir padrão", tamanho de página manual, importar PDF |
| Almoxarifado | ○ | F6.3 (lista virtualizada, Image Doctor, edição em massa) |
| **Mesa** | ▶ | Feito: importar tabela/foto, semáforo, curadoria, auto-preencher, exportar. Falta: **importar do banco (multi-seleção)**, **arrastar item↔slot**, **override modal por slot**, estante com busca, trocar layout mantendo itens, aviso de slot sem imagem, auto-save |
| **Fábrica** | ▶ | Feito: 1 item/página, de riscado + por, validade do item, preview, PDF exato. Falta: **gate com a arte real do cartaz**, editar o "por", peso/imagem obrigatórios por layout |
| Cofre | ○ | F6.6 (backups, snapshots, mesclagem) |
| Configurações | ○ | F6.7 (sanitização, siglas, selos, modelo IA, atalhos) |
| Transversais | ▶ | Botão direito no canvas ✓ / nas listas ▶; **undo/redo ○ (F5.10 — próximo)**; empacotar projeto ○; Ctrl+K ✓ |

## §8 Exportação

| Item | Estado | Nota |
|---|---|---|
| Tabloide PNG/PDF; cartaz PDF multipágina tamanho exato, sem NUP | ✓ | Validado com pypdf (páginas e mm) |
| CMYK opcional via Ghostscript + ICC | ○ | F7.5 |

## §9–10 Casos avançados e teste final

| Item | Estado |
|---|---|
| Sabores no slot (IA sugere, usuário aprova) | ○ F7.1 (motor de leque pronto) |
| Dois produtos no slot (Camil e Rei) | ▶ enriquecimento detecta `componentes` ✓; slot ○ F7.2 |
| Repetir a mesma foto | ▶ compositor ✓; UI ○ |
| Projeto congelado + overrides por slot | ○ F6.8/F7.3 (schema pronto; princípio já provado na célula-mestre) |
| **Tabloide categorizado (aceitação final)** | ○ Bloco F |

## Riscos/débitos anotados (pequenos, não bloqueiam)

1. Zoom do rodapé reflete o canvas do Ateliê, não a tela ativa (religar por tela).
2. `poetry.lock` desatualizado (ddgs instalado via pip; `pyproject` já declara).
3. Doc-mestre §5.1 cita icrawler/Google — superado por ddgs (atualizar o .docx quando conveniente).
4. Upscale não roda no fluxo da curadoria (decidir: sempre, ou só cartaz grande — ponto em aberto da doc).
5. `montar_editor` (editor solto) continua por compatibilidade de testes; o caminho oficial é o Ateliê.

## Leitura do auditor (resumo executivo)

O **caminho crítico do dia a dia está de pé e provado**: foto/tabela → OCR → conciliação
com semáforo → criação com curadoria → grade da arte real → export (os dois produtos).
As **fundações difíceis** (WYSIWYG fiel, conciliação 3 camadas, célula-mestre com
overrides, design system) estão sólidas e testadas (146+ testes). O que falta é, na
maioria, **composição de peças que já existem** (telas de gestão, casos avançados de
slot, undo/redo) — não motores novos. Maior lacuna conceitual: **projeto salvo
congelado** (o coração da §3.1) ainda não tem fluxo na UI; recomendo priorizá-lo logo
após undo/redo, antes do Dashboard (que depende dele).
