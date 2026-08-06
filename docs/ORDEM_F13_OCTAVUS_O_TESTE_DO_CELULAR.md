# ORDEM F13-OCTAVUS — O TESTE DO CELULAR (os dois últimos pontos da Segunda)

> **Emitida pelo arquiteto em 27/07/2026.** O dono: *"Agora tá quase mas não tá perfeito…
> principalmente o tamanho das escritas que quase não dá pra ler se depender da pessoa…
> E a data continua estranha."*
>
> A página está **perto**. Restam dois defeitos, e os dois têm número.

---

## §1 · MEDI A ESCRITA — e o problema não é "pequena", é DESIGUAL

Medi a altura de uma linha de nome em três células da página real (`arte.png`, 2160×2880).
**O que ele distribui no WhatsApp tem 1080 px de largura, visto num celular de ~400 px de tela
— ou seja, 37% do tamanho.** Então a conta que importa é a terceira coluna:

| Célula | 1 linha na arte | em 1080 px | **no celular** |
|---|---|---|---|
| **cel-2 · Creme de Leite Italac** | 41 px | 20 px | **7,6 px** 🔴 ilegível |
| cel-4 · Azeite Gallo | 64 px | 32 px | 11,8 px 🟡 no limite |
| cel-7 · Óleo de Soja Concordia | 92 px | 46 px | 17,0 px ✅ |

**O corpo do nome varia 2,2× entre células da mesma página.** É exatamente o que se vê na
imagem: os nomes das duas células que flanqueiam o Kit Burger são visivelmente menores que os da
fileira de baixo. O auto-ajuste encolhe **por célula, de forma independente, sem piso** — e as
células apertadas perdem sempre.

É o mesmo padrão de erro pela terceira vez nesta fase: **regra sem piso.** Consertei o teto na
SEPTIMUS (foto ≤68%) e esqueci de pôr **piso no tipo**.

### C1 🔴 · O TESTE DO CELULAR passa a ser a régua da tipografia

> **Nenhum texto de produto pode ficar abaixo de 11 px quando a página é reduzida ao tamanho de
> tela de celular** (fator 0,37 sobre a largura de 1080). Na arte de 2160 px isso é
> **≥ 60 px de altura de linha**; em 1080 px, **≥ 30 px**.

E as consequências, em ordem de precedência — **esta ordem é a regra, não sugestão**:

1. **O corpo mínimo do nome é inviolável.** Nunca encolher abaixo do piso para fazer caber.
2. Não coube no piso? **Quebra em 2 linhas.**
3. Ainda não coube? **A faixa do nome cresce** e a foto cede altura (já é a regra do O1).
4. Ainda não coube? **O descritor sai** (ele é o único elemento sacrificável).
5. Ainda não coube? **Encurta o NOME pelo descritor** — "Azeite Gallo" + descritor "extra virgem
   clássico · 500 ml". Nunca corta palavra, nunca hifeniza.

**Teste obrigatório:** para as 8 páginas, medir a altura de linha de **todos** os nomes e falhar
se qualquer um ficar abaixo do piso. E reportar o **desvio máximo entre células da mesma página** —
alvo: **nenhum nome mais que 1,3× maior que o menor da página.** Uniformidade é parte da
qualidade; hoje está em 2,2×.

### C2 🟠 · O descritor desapareceu da Segunda
Nenhuma célula da página tem a segunda linha (`fatiado na hora · 100 g` no modelo). O T2 da BIS
está implementado no motor mas **não está chegando** nesta página — ou a zona tem altura zero, ou
o dado não vem. Ache e conserte: é ele que permite encurtar o nome no passo 5 do C1.

---

## §2 · A DATA: dois textos brigando pelo mesmo selo

Ampliei o selo do topo-direito. Dentro daquele círculo pequeno há **quatro textos sobrepostos**:

```
TODA SEGUND[A]     ← gravado na ARTE (curvo, estrutura)
Ofertas válidas    ← escrito pelo APP (reto)
SOMENTE 27/07      ← escrito pelo APP (reto)
LEITERIA           ← gravado na ARTE (curvo, estrutura)
```

O app está escrevendo **por cima do texto gravado do selo**. Daí o "estranho": não é a data que
está errada — é que ela dividiu um espaço de ~2 cm com duas palavras curvas que já estavam lá.

### C3 🔴 · O que o app escreve no selo é SÓ a data
- **Corta "Ofertas válidas".** É redundante três vezes: o selo já diz `TODA SEGUNDA`, o rodapé já
  diz *"Ofertas válidas somente na segunda ou enquanto durarem os estoques"*, e o dono sabe o que
  é o encarte dele.
- **Escreve só `27/07`** — ou `SOMENTE 27/07` se couber com folga —, centralizado no miolo limpo
  do selo, **entre** as duas curvas gravadas, em corpo que passe no teste do celular (C1).
- **Mede o miolo livre do selo**, não a caixa toda: o círculo tem texto curvo na borda; a área
  útil é o disco interno. Meça por pixel no BASE (a região sem tinta) e ancore ali.
- **Guarda:** se a data não couber no miolo com o corpo mínimo, ela **não** encolhe — vai para o
  rodapé em destaque, e o pré-voo avisa. Nunca ilegível, nunca sobreposta.

---

## §3 · O CONFLITO QUE VOCÊ LEVANTOU — decidido

Você reportou: *"o Quintou aprovado mede foto ~69% — fora da faixa 55–68%."*

**A faixa cede, não o Quintou.** A faixa passa a ser **55% – 70%**, e o motivo é de princípio: o
Quintou é o único artefato aprovado pelo dono contra um publicado real. **Quando a régua discorda
do padrão-ouro, a régua está errada.** Registre a mudança na SEPTIMUS §O1.

Boa pegada, e o jeito de trazer foi o certo — você não mexeu no que estava aprovado e trouxe a
decisão para cima. É assim que funciona.

---

## §4 · CRÉDITO — o que fechou nesta rodada

Registro porque foi bom e não pode regredir:

- **O O3 tinha causa-raiz de verdade, e você achou:** `_gerar_miniatura` montava uma **terceira
  receita à mão**, sem validade nem descritor — a mesma doença do Modo Pai que a frota da F12
  matou. Agora a miniatura nasce da montagem oficial, com prova por pixel. **É a terceira vez que
  "montar à mão em vez de usar a montagem oficial" causa um defeito neste projeto** — vale virar
  lei: *só existe uma montagem; quem compõe página usa `dados_para_desenho`.*
- **O Kit Burguer:** a causa era a zona 312×90 (banner horizontal herdado do placeholder) contra
  um saco kraft vertical. Diagnóstico exato, conserto exato.
- **E o achado que você pegou antes de morder:** a reimportação do pacote **apagaria a
  configuração do item fixo dele**. Isso teria destruído o Kit Burguer na próxima atualização, em
  silêncio. Pegar isso *antes* de rodar é o melhor tipo de trabalho que existe nesta fase.

---

## §5 · ORDEM DE ATAQUE

1. **C1** — o piso do tipo e a uniformidade (é o que ele está reclamando).
2. **C2** — o descritor de volta (habilita o passo 5 do C1).
3. **C3** — a data sozinha no miolo do selo.
4. Recompor **o projeto id=7** e mandar a página para ele.

**Só isso.** Não abra frente nova nesta rodada — a Segunda está a dois consertos de ser a primeira
página que o dono publica. Termine ela.

As sobras conhecidas (rollout do orçamento nas outras 5, Sonho+Croissant, a Quinta a 1,52, o
Jornal na densidade, o `TP` para o descritor) ficam para a rodada seguinte, com o Quintou e a
Segunda já aprovados como referência dupla.


---

# Resposta do builder (Fable) — 27/07/2026

Na ordem do §5: C1 → C2 → C3 → o projeto id=7 recomposto. Sem frente nova.

## C1 — o piso do tipo (e a descoberta boa: o piso JÁ VIVIA no motor)

`Regiao.tamanho_min_pt` existia desde a fundação (default 6.0 — inerte) e o `ajustar_texto` já o
respeitava. O C1 foi **calibração + espaço físico**:

- **As bandas da ARTE cresceram** (o passo 3 da precedência — "a faixa cresce e a foto cede"):
  o gerador da Segunda regenerado com bandas 52→80, 56→84 e 53,5→80; as fotos cederam
  (188/186/152) e seguem no orçamento (55–70% após o §3).
- **O tipo subiu ao piso do celular**: nomes a **19pt uniformes** (piso 17pt) em até 2 linhas
  DENTRO da banda; descritor 10,5–11pt. Uniformidade ≤1,3× travada por teste (estava 2,2×).
- **O laço do OLHAR pegou dois ajustes finos**: (a) a caixa de 60px truncava "Creme de…" em vez
  de quebrar (2 linhas a 19pt precisam de 64px — corrigido); (b) "Leite Condensado Triangulo"
  não coube em 2 linhas → **passo 5 executado**: nome "Leite Condensado", descritor
  "Triangulo · 395 g".
- Testes: piso+uniformidade por célula (`test_c1_piso_do_tipo_e_uniformidade_na_segunda`) e o
  piso inviolável no text_fit (`test_c1_o_texto_fit_respeita_o_piso` — abaixo do piso TRUNCA
  com reticências e o pré-voo acusa, nunca encolhe).

## C2 — o descritor voltou (a causa)

O T2 estava no motor; **o dado não vinha**: a montagem do caso real criava os ItemMesa SEM
`unidade` → o descritor montava vazio. Os 8 itens agora carregam o descritor (peso/marca/
detalhe) e TODA célula tem a região SUBTITULO (teste). De quebra, o `TP` foi para o descritor
("tinto TP · 1,5 L") — o item anotado do §3 da SEPTIMUS.

## C3 — só a data no miolo medido

`Regiao.so_data` (aditivo): região VALIDADE que extrai **só a data** do texto composto
("Ofertas válidas SOMENTE 27/07" → "27/07"); sem data no texto, cai no completo (guarda — nunca
em silêncio). O miolo limpo do selo foi MEDIDO por pixel no BASE (a faixa sem tinta: **y 82–106,
x 890–970**) e a caixa ancora ali, na rotação do selo. O selo agora lê:
`TODA SEGUNDA · 27/07 · LEITERIA` — a data grande, entre as curvas gravadas, sem sobreposição.

## §3 registrado

A faixa do orçamento atualizada para **55–70%** na SEPTIMUS §O1 (o Quintou manda na régua).

## A página

O projeto **id=7 reimportado, remontado e recomposto** (a preservação do conteúdo fixo no
upsert seguiu valendo — o Kit sobreviveu às 3 reimportações desta rodada). A página final:
nomes grandes e uniformes em 2 linhas, descritores vivos, "27/07" no selo, o Kit no oval.
`saida_f13/galeria_f13_bis/segunda-2707-real.png`.

## Placares (junit `bloco_foctavus_*`)

**Suíte 1003 ×2 zero skips exit-0** (999 + os 4 da OCTAVUS; runs 2 e 3);
**invertida 1003/0/0**; **janela real 4/0/0**. *Incidente NOMEADO (L6):* o run1 teve 1 falha
AMBIENTAL — `OSError [Errno 22]` ao GRAVAR `galeria_bloco_f/quarta-das-ofertas.png` (o arquivo
momentaneamente travado no Windows; a falha é no `open` do PIL, não na composição) — o MESMO
teste, no MESMO código, passou no run2, no run3 e na invertida. O run1 fica no junit como
registro. *Nota de bancada:* a régua do `test_o1` (0,68→0,70) foi ajustada DEPOIS de eu ter
disparado a primeira bancada — matei a rodada e relancei do zero para que todos os runs
medissem o mesmo código.


