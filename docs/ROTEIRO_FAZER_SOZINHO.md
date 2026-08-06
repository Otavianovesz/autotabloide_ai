# ROTEIRO — fazer a Segunda sozinho, do zero ao arquivo

> **Verificado pelo arquiteto em 27/07/2026, no banco e no código reais.**
> Cada passo abaixo eu confirmei que existe como **botão ou menu**, não como script.

---

## O que eu confirmei no seu banco

```
layout id=10  "Segunda dos Frios"   →  9 slots, 1 FIXA (celula-1)
   celula-1  fixa=True
             conteudo_fixo = {nome: "Kit Burguer Senepol BBX",
                              descritor: "blend senepol · 4 un…"}
```

O Kit está **configurado dentro do template** — não é do projeto. Isso significa que ele sobrevive
a reimportar a tabela e a montar a semana seguinte. É o que você pediu.

E os oito encartes estão no Ateliê: Segunda dos Frios, Terça do Pão, Quarta das Ofertas,
Quinta do Peixe, Sexta Verde, Sábado da Carne, Jornal do Mês, Quintou do Real.

---

## O caminho, passo a passo

| # | Onde | O que fazer | Confirmado em |
|---|---|---|---|
| 1 | **Ateliê** | duplo-clique em **"Segunda dos Frios"** (ou botão direito → *Abrir na Mesa*) | `atelie.py:327` |
| 2 | **Mesa** | **" Importar tabela/foto"** → aponte a foto da tabela da semana | `mesa.py:67-72` |
| 3 | **Mesa** | confira o semáforo na conciliação: verde casou, amarelo confira, vermelho é produto novo | `conciliacao_dialog.py` |
| 4 | **Mesa** | **" Auto-preencher"** — o Kit vai para a célula fixa, o resto preenche as 7 | `mesa.py` |
| 5 | **Mesa** | falta foto de algum item? **" Do banco"** para pegar do acervo, ou botão direito na estante → *Fotos deste item* | `mesa.py:85-88` |
| 6 | **Mesa** | **" Aprovar"** (tira o RASCUNHO — e agora sai limpo por padrão de qualquer forma) | barra da Mesa |
| 7 | **Mesa** | **" Salvar projeto"** e **" Exportar"** | `mesa.py:135-138` |
| 8 | depois | reabrir: **" Abrir projeto"** → *"Segunda dos Frios 27/07"* | `mesa.py:135` |

**Para a semana seguinte** (o caminho recorrente, que era o pedido do "6 minutos"): abra o projeto
da semana passada, **" Importar tabela/foto"** com a tabela nova, e escolha o **3º botão —
"Atualizar os preços dos atuais"**. Ele troca só os preços casando por chave natural e **não
desmonta a arte**.

---

## ⚠️ A UMA COISA que você NÃO consegue achar sozinho

**"Itens fixos deste encarte…"** — o diálogo que deixa você **escolher a foto do Kit Burguer**,
o nome e se o preço é fixo ou da semana.

Ele **existe e funciona**, mas mora **só na paleta de comandos**: você tem de apertar **Ctrl+K**
na Mesa e digitar *"fixos"*. **Não há botão nenhum.**

Isso é irônico de um jeito específico: é a feature que você pediu explicitamente três vezes
("como que faço pra escolher a imagem"), e ela ficou no único lugar onde ninguém olha. É o mesmo
defeito que a auditoria catalogou como **P-06** (o "Aprovar" que só existia no Ctrl+K) e como
**U-01** (o "carimbar modelo" que ninguém achava).

**Por enquanto: Ctrl+K → "fixos".** Funciona.

> **Correção do builder (NONUS/F1, 27/07/2026):** o atalho acima estava DESATUALIZADO — desde
> a F13/C13 o **Ctrl+K é a busca global** (projetos/produtos/layouts, SEM ações); a paleta de
> ações da Mesa é **Ctrl+Shift+P**. O esconderijo era pior do que o descrito. Consertado na
> NONUS: agora os fixos têm **três portas visíveis** — botão direito na própria célula fixa
> ("Conteúdo fixo desta célula…"), o menu "···" da barra da Mesa (permanente), e a paleta
> Ctrl+Shift+P.

---

# ORDEM CURTA PARA O BUILDER

**F1 🔴 · "Itens fixos deste encarte…" ganha porta visível.**
Ele é a feature que o dono pediu três vezes e está escondido atrás do Ctrl+K.
Onde pôr, em ordem de preferência:

1. **No menu de contexto da própria célula fixa, no canvas da Mesa** — botão direito na célula do
   Kit → *"Conteúdo fixo desta célula…"*. É o gesto natural: ele clica no que quer mudar.
2. **E** no menu "···" da barra da Mesa, visível, junto com as outras ações de projeto.
3. Manter no Ctrl+K também (quem aprendeu não perde o caminho).

E aproveite a varredura: **procure outras ações que só existem na paleta** e que o dono
precisaria achar sozinho. O `_editar_itens_fixos` não é a única — a lista de tuplas do catálogo
em `mesa.py:1560-1582` tem pelo menos mais três candidatas ("O que mudou desde a última edição",
"Exportar o checklist em PDF", "Sugerir variações para agrupar"). Reporte quais têm porta visível
e quais não têm; **não** conserte todas nesta rodada — só nomeie, e conserte a dos itens fixos.

**F2 🟠 · Um teste de gesto para o caminho inteiro do dono** (a L2 aplicada ao fluxo, não a um
botão): Ateliê → duplo-clique no encarte → Mesa carrega o layout → importar tabela → auto-preencher
→ salvar → reabrir. Prova por conteúdo que o item fixo manteve o Kit e que o mapa sobreviveu.
Hoje cada peça tem teste; **o caminho não tem.**
