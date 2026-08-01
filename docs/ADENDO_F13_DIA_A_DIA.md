# ADENDO F13 — O ALMOXARIFADO E O OCR DO DIA A DIA (pedido direto do dono, 01/08/2026)

> *"Fui usar o programa e encontrei algumas coisas complicadas. Primeiro,
> não tem opção de eu criar itens no almoxerifado… Segundo, quando tem
> mais de um item que foi extraido do OCR, ele não está sabendo puxar
> dois itens diferentes, tô tendo que fazer manualmente. E tem vezes que
> já tem um item no banco de dados, mas ele não reconhece e me obriga a
> criar outro item igual. Queria ter uma opção pra poder forçar um item
> virar outro ali na importação do ocr. Inclusive, essa importação do
> OCR é bem debilitada, poderia ter muito mais coisas pra ajudar no dia
> a dia em todos os sentidos. veja o que pode fazer…"*

## O diagnóstico (frota de 4 scouts, causas REPRODUZIDAS no banco real)

1. **Criar item:** confirmado — não existia NENHUMA porta de criação
   avulsa na UI; o estado vazio do Almoxarifado mandava o dono para a
   Mesa importar.
2. **"Não sabe puxar dois itens diferentes":** três causas de código —
   (a) a chave de comparação do fuzzy remove o peso DE PROPÓSITO e o
   corpus usava `setdefault`: dois produtos irmãos de gramaturas
   diferentes COLIDIAM na mesma chave e o segundo ficava INVISÍVEL como
   candidato; (b) nada impedia duas linhas do lote de casarem VERDES com
   o MESMO produto em silêncio; (c) o motor calculava 5 candidatos e a
   UI só via o nº 1 — se o certo era o nº 2, restava criar duplicata.
3. **"Me obriga a criar outro igual":** além do (c) acima, o
   rebaixamento S1 não entendia "BB-X" (tokens de <3 letras não contam;
   o "bbx" do cadastro rebaixava verdes de score 94+), os aliases
   herdados do OCR antigo carregam o marcador "•" no texto cru e nunca
   mais casavam exato, e havia um registro CORROMPIDO real (id=50:
   nome de leite com apelidos de coxa) devolvendo score 100 errado.

## A execução

- **MOTOR** (`app/ai/conciliacao.py`, `app/core/repositories.py`):
  corpus com TODOS os irmãos por chave + desempate pelo PESO da oferta
  (base canônica g/ml; "PAO DE QUEIJO 1KG" prefere o cadastro de 1 kg);
  `exclusividade_de_lote` (a 2ª linha verde no mesmo produto desce a
  AMARELO com o motivo dito); divergência TOLERANTE (token presente sem
  espaços não é ausência; quase-igual difflib ≥0,8 é erro de leitura,
  não marca diferente); aliases limpos de marcadores nos DOIS sentidos
  (ao gravar e ao casar).
- **UI da conciliação** (`conciliacao_dialog.py` + `servico.py`): os
  TOP-5 candidatos viajam no `ItemMesa.candidatos`; o AMARELO ganhou
  **"Outro…"** (menu com os demais candidatos + "Buscar no acervo…");
  o VERMELHO ganhou **"Vincular…"** — o gesto pedido: o dono aponta o
  produto que o item É, vira VERDE e o banco APRENDE o alias
  (`aceitar_correspondencia(produto_id=…)`; F9: a escolha humana é a
  confirmação por excelência); corrigir o texto na célula RE-CONCILIA a
  linha na hora (`reconciliar_item`, uid preservado — I1); MINIATURA do
  palpite na coluna "No banco" + tooltip com os candidatos; o Ignorar
  ganhou **Desfazer** (toast de 6 s).
- **Almoxarifado**: botão **"Novo produto…"** — o nome basta (a porta
  única `importar` sanitiza e nunca duplica), o painel inline vira o
  formulário e a foto entra pelo "Trocar imagem…" de sempre
  (`criar_produto_manual`, com a guarda de somente-leitura).
- **Banco real** (backup `core_pre_diaadia_20260801.db`): os 2 apelidos
  de coxa do registro corrompido id=50 devolvidos ao id=21
  ("Coxa Sobrecoxa 100g") — "COXA SOB COXA" volta a casar certo.
- **Achado colateral consertado**: a prova de escrita do boot usava
  nome FIXO (".escrita_ok") e duas threads iniciando o banco ao mesmo
  tempo colidiam (WinError 32) — nome único por tentativa.

## Aberto nomeado (decisão do dono)

- O registro **id=50** em si ("• COXA SOB COXA 100g" com nome
  sanitizado "Leite Int. L.V. Triângulo 1L") é um Frankenstein de
  edição antiga — os apelidos já saíram; o registro fica no acervo até
  o dono decidir (fundir/excluir pela lixeira ou pelo caça-duplicatas).
- Nomeados para o futuro (da lista da frota, não incluídos nesta
  rodada): dividir linha em duas; "+ Adicionar item" no diálogo;
  importar .xlsx/.csv como OFERTA na Mesa (promessa da VISÃO §3.1);
  foto rolando junto da linha (exige bbox por linha no OCR — custo G).

## Testes

`app/tests/test_f13_diaadia.py` — 9 testes, TODOS vermelhos no código
antigo (L1): os 5 do motor (irmãos de gramatura ambos candidatos + peso
desempata; exclusividade de lote; BB-X não rebaixa; grafia OCR próxima
não rebaixa; alias com bullet casa exato) e os 4 de gesto (Novo produto
por clique; Vincular vira verde + o banco aprende e a MESMA grafia casa
exata na importação seguinte; corrigir o texto re-concilia; Ignorar tem
desfazer).

## Placares

**Suíte 1072 ×2 zero skips exit-0** (1063 + os 9 da rodada; runs 1 e 2 limpos, sem nenhum incidente); **invertida 1072/0/0**; **janela real 4/0/0**. Guardião do E3 virado com rastro (o probe da prova de escrita ganhou sufixo único).
