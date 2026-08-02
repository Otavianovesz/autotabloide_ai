# ADENDO F13 — A RODADA JORNAL DO MÊS (pedido do dono, 03/08/2026)

> *"Antes de você seguir, você me lista tudo que você vai arrumar, e
> tudo que você quer de pergunta e tudo mais… Pra fazer com que isso
> aqui funcione perfeitamente tanto no Jornal Belo Brasil, como no
> Quintou e como em todos os outros… a gente vai ter que estar mudando
> aqui talvez o cerne do aplicativo. […] você vai ter que passar a
> limpa por cima pra ver quais você fez meio errado, só pra aquele
> caso específico."*

O dono narrou o passo a passo REAL montando o Jornal com a tabela de
42 itens (a foto `Jornal do Mês Agosto.jpeg`). Três exploradores
mediram cada queixa contra o código e a tabela; o plano foi aprovado
pelo dono com **4 decisões**: (1) sabores = **FAMÍLIA de produtos
completos**; (2) composto = "Arroz Somar e Tio Bonini · 5 kg", embalagem
por componente entre parênteses; (3) **"SUPER OFERTA"** por extenso
dentro da forma do preço; (4) os textos fixos do Jornal seguem a
**validade viva**.

## O que entrou (5 blocos, cada um com teste vermelho antes)

1. **A limpa transversal (B1)** — plurais "Kgs/LT/LTS" nas 3 réguas de
   peso (conciliação, busca de imagem, nome_fit); metragem "30M" com o
   caso-limite ("3M" é marca); `separar_peso` corta metragem/contagem no
   fim e peso no início (o meio segue lei); a colagem limpa `<>` e o
   código de coluna "T-1" por FREQUÊNCIA no lote; `app/core/ortografia.py`
   (PÔ→PÓ, AÇUCAR→AÇÚCAR, bigramas do OCR "inte gral"/"de sinfetante" —
   os dois medidos na foto real); o item VERMELHO nasce sanitizado; a
   guarda RG-20 enxerga tokens de 2 letras; desempenho (1 GET de vida
   por lote, categoria pelos candidatos do veredito, 1 commit por lote).
2. **Validade viva (B2A)** — `app/core/validade.py` (o parser único);
   a validade DA TABELA vence o vazio e a cascata, NUNCA a escolha do
   dono (`validade_vence` + origem rastreada); avisos comparam com a
   data-FIM (o falso "já passou" do dia 04/08 em diante morreu);
   `so_data` imprime o FIM; ValidadeDialog com De/Até; "do dia 1º ao
   27" gravado vira o período REAL na composição.
3. **SUPER OFERTA (B2B)** — reconhecida nas 3 grafias (OCR e colagem;
   a linha não vai mais ao balde); a forma do preço desenha ATRÁS do
   preço-texto; `PapelTexto.OFERTA` alimenta a estrela do Jornal;
   `descontos_de` ressuscitado nos 3 chamadores.
4. **Composto sem-IA + +18 (B3)** — a pendência "multiplos" do sanitize
   vira a pergunta "são 2 produtos?" na curadoria (sem IA: check
   desmarcado, sugestão determinística `dividir_em_dois`; com IA:
   pré-marcado e desmarcar CANCELA); o lote nunca compõe por chute;
   foto por componente; `nome_composto` no formato do dono;
   `app/core/mais18.py` (a Amstel não passa mais sem selo) e
   `finalizar_criacao` grava `bebida_alcoolica` (o furo do round-trip).
5. **FAMÍLIAS de sabores (B4, schema v2→v3 padrão E7)** —
   `familias_produto` + `Produto.familia_id`; check de sabores
   (`SaboresDialog`) pela estante; famílias nascem do uso (pergunta
   pós-agrupamento) e do Almoxarifado (ligar/desligar); o leque congela
   no ITEM (o `imagens_json` RG-28 não entra — I3); o agrupador da Mesa
   ganha o degrau por família antes da heurística de marca.

## Banco real

Migrado v3 com backup duplo (`core_pre_jornal_20260803.db` +
`pre_migracao_*` do E7). Higienização pela régua conservadora: **1 hit
único** — id=70 "Leite Pô Ninho…" → "Pó" (nenhum falso positivo).

## A prova real

OCR de verdade na foto de agosto: **42 itens (20+22 exato, zero
sobras)**; validade canônica "OFERTA VÁLIDA DE 03/08 ATÉ 27/08"; os 2
"S. OFERTA" DENTRO da etiqueta; 8 pendências "multiplos"; +18 na
Amstel e no Campari; manchete **"PREÇO BAIXO DO DIA 3 AO 27"** viva.
Páginas em `saida_f13/jm-prova-p1.png` e `jm-prova-p2.png`.

## Incidentes nomeados (honestidade de bancada)

- A fixture de gestos chamava `isDefault()` em todo `QAbstractButton` —
  o QCheckBox novo não tem, a exceção era engolida pelo laço do Qt e o
  `exec()` pendurava (consertado: `isinstance QPushButton`).
- `test_os_f11_5` ISOLADO crasha 0xC0000409 também no HEAD limpo
  (pré-existente, provado por A/B em worktree; na suíte completa roda).
- Crashes intermitentes de teardown nas varreduras agrupadas (família
  COND-10) — re-rodados limpos em metades.

## Fica para a rodada 2 (nomeado)

Vista em árvore das famílias no Almoxarifado; `ProdutoEnriquecido.variantes`
da IA sugerindo criar família; 2ª curadoria de foto do componente 2;
multi-foto no Almoxarifado; glossário ortográfico na tela de
Configurações; fluxo dinâmico por seções (o estático de 42 é o caminho).

## Placares

Suíte **1136 ×2 zero skips** + invertida + janela real
(`bloco_jm_*` em `saida_f13/`). 64 testes L1 novos em
`test_rodada_jm_*.py`; asserts antigos editados de propósito listados
no commit.
