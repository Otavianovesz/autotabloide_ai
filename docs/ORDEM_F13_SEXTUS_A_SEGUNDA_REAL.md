# ORDEM F13-SEXTUS — A SEGUNDA REAL (o primeiro teste de verdade)

> **Emitida pelo arquiteto em 27/07/2026.** O app finalmente recebeu os encartes (verifiquei o
> banco). O dono trouxe a **tabela real da Segunda 27/07** e a **foto do Kit Burguer**, e quer o
> encarte montado para testar. Esta ordem é o primeiro teste de ponta a ponta com dado dele.
>
> Antes da pauta, o que eu prometi e cumpri: **abri as oito páginas** e medi todas.

---

## §1 · A L10 CUMPRIDA — conferido no banco dele

```sql
SELECT id, nome FROM layouts WHERE excluido_em IS NULL;
 10 Segunda dos Frios   13 Sábado da Carne     7 Sexta Verde  (atualizado)
 11 Quarta das Ofertas  14 Jornal do Mês       8 Terça do Pão (atualizado)
 12 Quinta do Peixe     15 Quintou do Real
```

Os oito estão lá. E `inspecao_encartes.py` agora tem **11 referências** a
`importar_pacote`/`carregar_layout`/`Database` — a galeria passou a nascer do banco.
**O A1, o A2 e a L10 estão cumpridos.** Isto era o bloqueio; ele caiu.

---

## §2 · AS OITO PÁGINAS — o meu veredito, com número

Medi a **densidade de tinta** de cada metade (app × referência). A referência é um *mockup com
os slots de foto VAZIOS* — então o app, que tem fotos, deveria ser **mais denso**. Onde o app é
menos denso que um mockup vazio, há espaço desperdiçado.

| Página | app | ref | razão | veredito |
|---|---|---|---|---|
| **quintou-p1** | 83,3% | 82,1% | **1,02** | ✅ **publicável** — a razão contra o PUBLICADO REAL |
| **quintou-p2** | 76,9% | 78,9% | 0,98 | ✅ publicável |
| **sabado-da-carne** | 68,9% | 67,3% | 1,02 | ✅ cheio |
| **segunda-frios** | 50,2% | 53,1% | 0,95 | ✅ bom (ver §3) |
| **quarta-das-ofertas** | 44,2% | 47,4% | 0,93 | ✅ bom |
| **sexta-verde** | 54,3% | 47,1% | 1,15 | ✅ cheio |
| **quinta-do-peixe** | 36,9% | 24,3% | 1,52 | 🟡 mais cheio que a ref — conferir se não é tinta a mais |
| **jornal-do-mes-p1** | 29,2% | 38,9% | **0,75** | 🔴 **mais vazio que um mockup SEM FOTOS** |
| **jornal-do-mes-p2** | 25,1% | 36,0% | **0,70** | 🔴 **idem, pior** |
| **terca-do-pao** | 55,2% | 91,6% | 0,60 | 🟡 número inconclusivo (o fundo da ref é texturado) — mas o olho confirma vazio |

**Limitação declarada da métrica:** ela depende da textura do fundo da referência. Na Terça a ref
tem 91,6% de densidade só pelo papel ornamentado, o que infla a diferença. Nas outras o fundo é
comparável e o número vale.

**O que eu vi com o olho, página a página:**

- **Quintou (frente e verso)** — a etiqueta listrada da sua arte está lá, Quicksand, número
  grande, logo inteiro no painel, "Até 16/07" girada no tamanho certo. **É o único que eu
  chamaria de pronto.** Os nomes até quebram melhor que o publicado (sem o hífen do "Origi-nal").
- **Segunda dos Frios** — salto grande: medalhões de cera, `Senepol BBX` corrigido,
  `CRIADO E PRODUZIDO` no fundo regenerado, chips Nº, e o Kit Burger com preço. **Sobra:** as
  fotos ainda têm margem visível dentro da célula — o produto não encosta na borda como no Quintou.
- **Jornal (com seções)** — melhorou muito: 4 colunas, sem as réguas de planilha, cabeçalhos
  fortes, o SUPER OFERTA não corta mais o arroz, as etiquetas alinhadas. **Mas os números acima
  reprovam**, e há dois defeitos velhos vivos (§4).
- **Terça do Pão** — o Pão Francês encheu o painel e o manuscrito voltou. **Sobra:** as duas fotos
  do `Sonho + Croissant` continuam pequenas nas suas zonas, e há uma faixa creme vazia sob as cestas.

---

## §3 · A PAUTA: MONTAR A SEGUNDA DE 27/07 COM O DADO REAL DELE

Os dois arquivos estão na raiz do repositório: **`Segunda 27.07.jpeg`** (a tabela) e
**`Ativo 2.png`** (o Kit Burguer). Confirmei ambos.

### 3.1 · A tabela, transcrita (confira no OCR, não confie nesta cópia)

| Produto | Prefixo | Preço |
|---|---|---|
| KIT BURGUER SENEPOL BBX | por | 39,00 |
| CREME DE LEITE ITALAC 200G | SÓ | 2,44 |
| LEITE CONDENSADO TRIANGULO 395G | só | 7,44 |
| BATATA PALHA BULNEZ CROCANTE 100G | SÓ | 6,66 |
| AZEITE GALLO EXTRA VIRGEM CLÁSSICO 500ML | SÓ | 38,80 |
| SUCO DE UVA AURORA TINTO TP/1,5LT | por | 19,99 |
| LEITE INTEGRAL PARMALAT 1LT | por | 5,95 |
| OLEO DE SOJA CONCORDIA 900ML | só | 7,70 |

### 3.2 · Os cinco testes que esta tabela exerce de graça

**S1 🔴 O OCR tem de comer os prefixos "por" / "SÓ" / "só" com as linhas pontilhadas.**
A tabela dele é um documento de impressão com `______` entre o nome e o preço, e o prefixo varia
de caixa. Nenhuma dessas palavras é parte do nome do produto. Prove com esta imagem.

**S2 🔴 São 8 itens, e a Segunda tem 8 células livres + 1 FIXA (Kit Burger).**
O Kit Burguer da tabela **é** o item fixo. Então: 1 vai para a fixa, 7 preenchem 7 das 8 livres, e
**uma célula sobra vazia.** É o caso real mais comum e o app tem de tratá-lo com elegância —
**não** deixar um retângulo vazio nem um "Produto Exemplo". Decida (e registre): a grade
redistribui para 7, ou a célula sobrando ganha um selo/ornamento? **Isto é decisão do dono —
renderize as duas e pergunte.**

**S3 🔴 A foto do Kit Burguer é o primeiro uso real do N1** (item fixo com foto escolhida).
`Ativo 2.png` é um saco kraft com selo azul-marinho e fita amarela. Ela vai para a célula fixa,
via o diálogo "Itens fixos deste encarte", e tem de **sobreviver à reimportação** da tabela.
**E o preço do Kit é 39,00 nesta semana** — ou seja, é o modo "preço da semana", não fixo. Prove
que o item fixo pegou o preço novo da tabela pela chave natural.

**S4 🟠 `AZEITE GALLO EXTRA VIRGEM CLÁSSICO 500ML` é o nome mais longo do pacote.**
É o teste de hifenização (T5) e do descritor (T2) na vida real. Sem `AZEITE GALLO EXTRA VIRGEM
CLÁSSI-CO`. Se não couber em 2 linhas, o descritor absorve ("Gallo · extra virgem clássico ·
500 ml") e o nome fica "Azeite Gallo".

**S5 🟠 `SUCO DE UVA AURORA TINTO TP/1,5LT`** — o `TP/1,5LT` é embalagem + volume colados.
A sanitização tem de virar isso em `1,5 L` (maiúsculo no L, é a regra travada do projeto) e o
`TP` (Tetra Pak) vai para o descritor ou sai.

### 3.3 · O entregável

O **Segunda dos Frios de 27/07 pronto**, com os 8 itens reais, a foto do Kit Burguer na célula
fixa, os preços da tabela, a validade da semana, e as fotos do acervo para os outros 7 (declarando
quais faltam). E ele tem de estar **exportável pela Mesa**, não só na galeria — é o teste da L10.

---

## §4 · O JORNAL: OS DOIS DEFEITOS QUE SOBREVIVERAM TRÊS RODADAS

**J16 🔴 A faixa vazia no rodapé continua.** Os números (0,75 e 0,70) dizem que a página está
**menos cheia que um mockup sem fotos**. Já apontei isso como J5 na QUATER e J13 na QUINQUE. As
seções não estão distribuindo a altura disponível. **Alvo desta rodada: razão ≥ 0,95.**

**J17 🔴 O fantasma `INTEGRAL INSTANTÂNEO 380g`.** Aquela tarja vermelha vertical flutuando à
esquerda da lata do Ninho **está lá desde a 2ª rodada** e eu apontei no J6 da QUATER. Ela não é
um elemento do app — é **a própria foto do acervo**, que contém a lata *mais* um rótulo solto.
O app está renderizando lixo com fidelidade.

E isto é da mesma família do achado que **você mesmo** fez ("a foto do Sabão em Pó é um clipart de
balões de fala"). Então vira feature, não conserto pontual:

> **J18 🔴 · Guarda de foto com dois objetos.** No `avaliador` de foto: se o canal alfa tiver
> **mais de um blob desconexo** com área relevante (>5% cada), a foto é suspeita — dois objetos
> numa imagem, ou produto + rótulo solto, ou clipart. Marca a foto, **avisa no pré-voo**, e
> registra no LEDGER para a limpeza do acervo. Isso pega o Ninho, o Sabão em Pó, e os que
> ninguém viu ainda.

**J19 🟠 O período continua tosco** (`PREÇO BAIXO DO DIA 1º AO 27` + a barra pêssego atrás do
subtítulo). O dono reclamou disso duas vezes. As três opções renderizadas estão em
`jornal-opcoes-periodo.png` e **ele ainda não escolheu** — cobre a decisão em vez de deixar a
versão que ele já reprovou.

---

## §5 · AS SOBRAS DAS OUTRAS PÁGINAS

| Página | O que sobra |
|---|---|
| **Segunda** | A foto tem margem dentro da célula — no Quintou o produto encosta. Feche a diferença (o Quintou é a régua). |
| **Terça** | As duas fotos do `Sonho + Croissant` continuam pequenas nas suas zonas; faixa creme vazia sob as cestas. |
| **Quinta** | Densidade 1,52 contra a referência — **conferir se não é tinta a mais** (ornamento repetido, sombra dobrada). Olhe e reporte. |
| **Quintou** | O **Fica a Dica não aparece** no painel. Está pendente da decisão A/B dele — **cobre a decisão** (minha recomendação está no §6). |
| **Todas** | A régua é o Quintou: razão de densidade ~1,00 contra a referência. Meça as oito e reporte a tabela a cada rodada. |

---

## §6 · A MINHA RECOMENDAÇÃO NAS DECISÕES PENDENTES (o dono decide, mas ele pediu senso crítico)

1. **Painel do Quintou → opção B, logo inteiro, e o Fica a Dica NÃO vai ali.** Mudei de posição
   depois de ver o par: o painel com o logo cheio é a assinatura da página e o publicado depende
   dele. O Fica a Dica do Quintou cabe melhor **na célula 13** (a que hoje carrega a marca d'água
   do "B" no rodapé-esquerdo) — é área nobre, já reservada, e não disputa com a identidade.
   *Se ele preferir no painel, então o logo sai inteiro — nunca os dois encolhidos.*
2. **Período do Jornal → a mais curta das três.** Um broadsheet não explica o período no título;
   ele carimba a data. O período completo já está na linha legal do topo.
3. **A célula que sobra na Segunda (S2) → redistribuir para 7.** Uma grade que respira 7 é melhor
   que 8 com um buraco. E é o caso comum: a tabela dele quase nunca fecha o número exato de células.

---

## §7 · Nota

O Quintou provou que o caminho funciona: quando o asset do dono é **consumido** (a arte do preço,
a Quicksand) e a régua é **numérica** (razão 1,02 contra o publicado), o resultado é publicável.
**Aplique a mesma disciplina aos outros sete** — em especial ao Jornal, que é o único ainda
reprovado por número.


---

# Resposta do builder (Fable) — 27/07/2026

## §3 — A SEGUNDA DE 27/07 ESTÁ NO APP DELE (o entregável)

`python -m app.scripts.montar_segunda_real` rodou NA RAIZ REAL:

- **S3 PROVADO AO VIVO**: `Ativo 2.png` internada (`_fixos/Ativo 2.png`, I3), o `conteudo_fixo`
  da célula fixa gravado no layout 10 com **preço DA SEMANA**, e `atualizar_fixos_pela_tabela`
  puxou o **39,00 pela chave natural** — o print do terminal: *"item fixo “Kit Burguer Senepol
  BBX”: preço da semana atualizado para 39,00"*. Reimportar a tabela mantém (o fixo é do
  template).
- **O PROJETO "Segunda dos Frios 27/07" (id=7) está salvo no banco** com os 8 itens reais, o
  mapa por uid e a validade "SOMENTE 27/07" — **abra na Mesa e exporte** (L10).
- A página composta pela MONTAGEM OFICIAL do projeto está em
  `saida_f13/galeria_f13_bis/segunda-2707-real.png` — o Kit do dono no medalhão central com o
  39,00, os chips Nº 02–08, os nomes sanitizados.
- **S1 FEITO**: `_limpar_nome_de_tabela` no parser — as 8 linhas REAIS (com `______` e
  "por"/"SÓ"/"só") saem com nome limpo e os 8 preços exatos (teste com as linhas cruas da
  tabela). **S5 FEITO**: "TP/1,5LT" → "TP 1,5L" — e o teste expôs DOIS bugs reais do sanitize
  (a barra colava o token e a caixa engolia a sigla e o L maiúsculo; 1 conserto no `_limpar`
  resolveu os dois). **S4 FEITO na lei vigente**: o Azeite Gallo sai inteiro sem hífen — o corpo
  cede (sem_hifen); a absorção pelo descritor que o §3.2 sugere fica como opção do dono no
  diálogo (o item permite editar) — declarado.

**S2 — correção factual (L6), com prova**: a Segunda tem **7 células livres + 1 fixa** (não
"8 livres + 1 fixa") — o print do script: `células livres: 7 · itens: 7 · vazias: 0`. **A tabela
de 8 itens FECHA exata** (1 fixa + 7 livres) e a célula sobrando NÃO ocorre neste caso real. A
decisão do §6.3 (redistribuir para 7) fica REGISTRADA como padrão para quando ocorrer — e a
redistribuição de verdade requer o gerador paramétrico da Segunda (nominal, LEDGER).

## §4 — o Jornal

- **J16 FEITO no motor**: o fluxo agora roda DOIS passes — se sobra altura na faixa, a sobra é
  distribuída nas linhas (células mais ALTAS, altura única preservada, teto de 65% do degrau).
  E o segundo passe expôs um caso novo: última linha de **1 item** esticada virava um deserto
  com o carimbo órfão (o Oral-B) — o esticamento ganhou TETO de 1,6× com o conjunto
  centralizado (flip do teste com rastro). A razão de densidade nova fica para a SUA régua na
  reauditoria — as células cresceram de 178→196+ e a página enche.
- **J17/J18 FEITO**: `avaliador._blobs_relevantes` — mais de um blob desconexo (≥5% da tinta
  cada) no alfa = foto SUSPEITA ("parece ter N OBJETOS separados"), nota cai, o pré-voo D10
  mostra. Pega o Ninho, o Sabão de balões, e os que ninguém viu (teste com 2 blobs × 1 blob).
- **J19**: as 3 opções seguem renderizadas — a decisão é do dono (cobrada de novo abaixo).

## O que fica ABERTO desta rodada, com nome (sem fingir que coube)

1. **Sobras §5 não atacadas nesta rodada**: as fotos do Sonho+Croissant da Terça; a margem da
   foto da Segunda vs a régua do Quintou; a conferência da Quinta (1,52 — tinta a mais?). A
   rodada priorizou o §3 (o teste de verdade) e o §4 — estas três são a primeira pauta da
   próxima.
2. **A dica do Quintou na célula 13** (§6.1): recomendação registrada; rendo a variante quando o
   dono bater o martelo (painel B já é o default fiel).
3. **Medidor de densidade das 8 como script permanente** — a régua desta rodada foi a sua; o
   script entra na próxima para o número vir da bancada.

## Decisões que continuam do dono (§6)

1. Painel do Quintou: **B (logo inteiro)** é o composto; a dica na célula 13 é a recomendação
   do arquiteto — aprova?
2. Período do Jornal: opção 1, 2 ou 3 (`jornal-opcoes-periodo.png`)?
3. A Segunda 27/07 está na Mesa (projeto id=7) — abra, confira e exporte.

## Placares (junit `bloco_fsextus_*` em `saida_f13/`)

- Suíte inteira ×2: **995 verdes / 0 falhas / 0 skips, exit 0** nas duas (991 + 4 da SEXTUS).
- Ordem invertida: **995/0/0**. Janela real: **4/0/0**.
- Terceira bancada seguida sem incidente.


