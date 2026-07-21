# PLANO PERFEITO — 12 fases · ~1200 passos · a reta final do AutoTabloide

> Emitido em 18/07/2026 pelo arquiteto, sob comando do Otaviano: "escrever
> tudo com extremo detalhe, com o porquê, em ~1200 passos e várias fases".
> **Este documento é o MAPA (o quê e por quê de cada fase).** Cada fase tem
> seu caderno de ~100 passos finos (`docs/FASE_N.md`), emitido pelo
> arquiteto NO INÍCIO da fase — assim cada caderno nasce informado pela
> reauditoria da fase anterior, em vez de envelhecer na gaveta. A Fase 1 já
> está escrita (`docs/FASE_1.md`). O escopo COMPLETO das 12 está travado
> aqui: nada se perde, nada se inventa.

## Como cada caderno de fase é escrito (formato-lei)

Blocos de 8–15 passos; cada bloco abre com **"Por quê"** (a intenção do
dono, para o builder decidir os milímetros sem trair o espírito); cada
passo é UMA ação verificável de uma linha; a cada ~25 passos, um passo de
**checagem** (suíte/screenshot/medida); todo caderno termina com: suíte
inteira ×2 exit 0, adversariais se tocou slot/item/mapa, screenshots das
telas mudadas em `saida_faseN/`, resposta do builder no próprio caderno e
PARADA para reauditoria — que agora SEMPRE inclui **inspeção visual de
todos os artefatos** pelo arquiteto (lei da segunda passada).

## Decisões do dono registradas (18/07)

- **Curadoria das 150**: 141 aceitas. **VETADAS (não construir):** R-079
  (ditado por voz), R-080 (OCR de nota fiscal), R-092 (código de barras por
  câmera), R-093 (acervo compartilhado no pacote), R-124 (custo/margem),
  R-125 (diário de alterações), R-130 (backup em nuvem), R-143 (cardápio),
  R-146 (multi-loja). Na R-096, a aba "código de barras" saiu (a cascata
  EAN da Onda 4 continua funcionando por dentro, invisível — sem UI de
  scanner).
- **R-151 (novo)** Animações e microinterações em todo o app — transições
  suaves entre telas, fades de toasts/diálogos, hover com vida, skeletons
  de carregamento; 150–220 ms, sempre desligáveis ("Reduzir animações").
- **R-152 (novo)** A revolução do Início É a Fase 2 inteira — não um item.
- **R-153 (novo)** Campos de texto especiais com clareza TOTAL: criar uma
  região de texto abre escolha nomeada com prévia — "Aviso legal" ·
  "Validade da oferta (de/até)" · "Fica a Dica (IA escreve)" · "Texto
  livre" — com badge visível no editor dizendo o papel da região.

## As 12 fases (≈100 passos cada)

**FASE 1 — Fundação visual: design system 2.0.** Por quê: tudo que vem
depois (Início novo, Configurações, animações) precisa de alicerce de
tokens; é aqui que nascem o DARK MODE e a vida visual. Cobre: RG-52,
R-013, R-151 (motor de animação), R-015 (escala), R-021, R-022, R-023,
R-024, correções de formatação-base do RG-54 (políticas de tamanho mínimo
por widget). Caderno: `docs/FASE_1.md` (pronto).

**FASE 2 — O Início revolucionado.** Por quê: é a cara do programa e hoje
envergonha o resto; o dono pediu dashboard de verdade. Cobre: RG-50,
R-152, R-001–R-012 (painéis "Produzir hoje"/agenda, eventos como cartões
com cor e capa, continuar de onde parei, versões com miniatura, busca
global, favoritos, lixeira 30 dias, duplicar-semana-passada, indicadores
de saúde, modo apresentação, notas por evento).

**FASE 3 — Configurações dignas + selos.** Por quê: é o painel de controle
do dono; hoje está espremido e envergonha. Cobre: RG-51, R-014 (abas
Aparência·Campanhas·IA·Imagens·Selos·Sanitização·Backups·Atalhos), fim da
engrenagem-fantasma, R-018, gestor de selos completo (upload, automáticos,
por item), R-088, R-134, R-135, R-128, R-129, R-132 (perfil máquina
fraca), R-133.

**FASE 4 — Editor I: consertar e destravar.** Por quê: os bugs da segunda
passada moram aqui; não se constrói ferramenta nova sobre seleção quebrada.
Cobre: RG-55 (preço não-selecionável), RG-56 (agrupar/desagrupar visível e
reversível), RG-54 (formatação das telas do editor), RG-49 (seções sem
linha interna — contorno de união), R-025, R-026, R-027, R-028, R-029,
R-039, R-040, R-041.

**FASE 5 — Editor II: ferramentas de profissional.** Por quê: é o
Illustrator-do-tabloide que o dono imaginou. Cobre: R-030–R-038, R-042–
R-048, RG-57+R-153 (campos especiais com escolha nomeada e badge), R-044
(célula vitrine), R-046 (prévia de impressão), R-047 (contraste).

**FASE 6 — Mesa I: a bancada arrumada.** Por quê: a Mesa é onde a semana
acontece; botões espremidos e estante engessada custam minutos todo dia.
Cobre: RG-53 (barra em dois níveis/lateral com "···"), R-051 (modo
planilha), R-054, R-055, R-057 (trocar células arrastando), R-061
(rascunho automático), R-020, R-017 (Ctrl+K em todas as telas).

**FASE 7 — Mesa II: produção em massa.** Por quê: "importar tudo de uma
vez" é a lógica que o dono pediu duas vezes. Cobre: R-049 (multi-arquivo),
R-050 (Ctrl+V inteligente), R-052 (conciliação em tela cheia com a foto),
R-053 (aceitar verdes), R-056 (encher a página), R-058 (frases prontas),
R-059, R-060, R-062 (diff da edição anterior), R-063, R-069, R-070
(multi-preço "3 por 10"), R-071, R-072.

**FASE 8 — Exportação e publicação.** Por quê: o tabloide nasce para o
WhatsApp — o caminho até lá tem que ser de um gesto. Cobre: R-064
(compartilhar direto), R-065 (perfis), R-066 (fila em lote), R-067
(RASCUNHO), R-068 (aprovação em 2 etapas), R-139–R-142 (Stories/carrossel/
Oferta-do-Dia/vídeo-tabloide), R-145 (faixas/banners).

**FASE 9 — Conteúdo & IA II.** Por quê: a IA vira colega de trabalho, não
ferramenta escondida. Cobre: R-073 (chat da oferta), R-074, R-075, R-076,
R-077, R-078, R-081 (IA revisora do export), R-082, R-083, R-084, R-085,
R-086, R-087, R-089 (fila com prioridade), R-090.

**FASE 10 — Imagens II + Estúdio IA.** Por quê: a foto é 60% do encarte
(pesquisa §1) e o acervo é patrimônio. Cobre: R-091/RG-46 (Estúdio IA),
R-094, R-095, R-096 (abas Web·Acervo), R-097, R-098, R-099, R-100, R-101,
R-102, R-103 (refino do recorte), R-104.

**FASE 11 — Cartaz & Fábrica completos + inteligência.** Por quê: o cartaz
é metade do negócio e a inteligência de preço é serviço direto ao dono.
Cobre: R-105–R-114 (inclui 2-em-1, cartaz-relâmpago, QR, kit gôndola) +
R-115–R-123 + R-126.

**FASE 12 — Confiabilidade, MARCO FINAL e entrega.** Por quê: fechar tudo,
provar tudo, instalar no PC do mercado. Cobre: R-127, R-131, R-136, R-137,
R-138, R-144, R-147, R-148, R-149, R-150 ("Modo Pai"), **RG-48/RG-58 (o
marco re-executado: Quintou + Sexta Verde com layout REAL desenhado,
inspeção visual total do arquiteto)**, teste de aceitação do dono, e o
Bloco G (instalador, migração, guia rápido em português).

## Governança

Uma fase por vez; caderno emitido no início dela; chat novo do Code por
fase (intensidade: F4 e F12 máxima; demais Alto); reauditoria com inspeção
visual sempre; achado novo em qualquer fase entra AQUI com número; o selo
final do programa continua sendo do Otaviano, sobre o marco da Fase 12.
