# ORDEM F13-DECIMUS — A VALIDADE SE RESOLVE SOZINHA

> **Emitida pelo arquiteto em 27/07/2026.** O dono: *"quando eu uso o app, ele nunca pega a data
> de validade da oferta direito. Aparece que não foi definida. E eu não faço a mínima ideia de
> como fazer isso. Deixe isso mais intuitivo."*
>
> Este é o **P-01/P-02 do dossiê original** — o defeito mais antigo ainda vivo desta auditoria.
> Achei a causa e ela é quase absurda de simples.

---

## §1 · A CAUSA: o app não sabe que "Segunda dos Frios" é segunda-feira

A cadeia inteira, com linha:

```
mesa.py:2796   sugestao = servico.sugerir_validade( self._evento )
servico.py     sugerir_validade(evento) → dia_do_evento(evento)
servico.py     def dia_do_evento(evento):
                   if not evento: return None          ← AQUI MORRE
```

E `self._evento` é atribuído em **exatamente dois lugares**: `mesa.py:919` (abrir projeto que já
tem evento) e `mesa.py:1025` (reabrir projeto salvo). **Abrir um LAYOUT pelo Ateliê não define
`_evento` em lugar nenhum.**

Então: ele abre "Segunda dos Frios" no Ateliê → `_evento = None` → `dia_do_evento(None)` → `None`
→ nenhuma sugestão → o pré-voo diz *"papel 'Validade da oferta' sem data — defina a validade"*.

**A automação existe e nunca dispara para ele**, porque ela depende de uma entidade *Evento* que
ele teria de cadastrar na tela de Eventos — coisa que ninguém lhe disse, e que ele não tem
motivo nenhum para adivinhar.

### E a solução está escrita no nome do arquivo

O layout se chama **"Segunda dos Frios"**. O dia da semana **está no nome**. Nos oito:

| Layout | Dia | Validade sugerida |
|---|---|---|
| Segunda dos Frios | segunda | `SOMENTE 03/08` |
| Terça do Pão | terça | `SOMENTE 28/07` |
| Quarta das Ofertas | quarta | `SOMENTE 29/07` |
| Quinta do Peixe | quinta | `SOMENTE 30/07` |
| **Quintou do Real** | quinta | `ATÉ 30/07` |
| Sexta Verde | sexta | `SOMENTE 31/07` |
| Sábado da Carne | sábado | `SOMENTE 01/08` |
| Jornal do Mês | mensal | `DE 01/08 A 27/08` |

---

## §2 · D1 🔴 · O ENCARTE SABE QUE DIA ELE É

`dia_do_evento` ganha uma **cascata de fontes**, nesta ordem:

1. **Evento cadastrado** (`dia_semana`) — o que existe hoje, continua mandando.
2. **Config `eventos.dias`** — o fallback legado que já existe.
3. **NOVO · o NOME DO LAYOUT** — casar por radical, sem acento e sem caixa:
   `segunda|seg` → 0 · `terça|terca|ter` → 1 · `quarta|qua` → 2 ·
   `quinta|quintou|qui` → 3 · `sexta|sex` → 4 · `sábado|sabado|sab` → 5 · `domingo|dom` → 6.
   `jornal|mês|mes|mensal` → **período do mês**, não dia.
4. Nada casou → `None`, e aí sim o app pergunta.

**Zero configuração.** Ele abre a Segunda, e a data já está lá.

**Guarda contra o falso positivo:** casar por **palavra inteira**, nunca por substring solta —
um layout chamado "Promoção Relâmpago" não pode virar segunda-feira porque contém "ão". É a mesma
disciplina do `extrair_marca` (trava da F9: só devolve o que é seguro, ambíguo fica None).

**E o cálculo da data:** o **próximo** dia daquela semana, contando hoje. Se hoje é segunda,
a validade é hoje. Se hoje é terça, a próxima segunda. Nunca uma data no passado.

---

## §3 · D2 🔴 · A VALIDADE PASSA A SER VISÍVEL — sempre

Hoje ela é um `QLabel` que **nasce vazio** (`mesa.py:149-157`) e só ganha texto depois de
definida. Um campo invisível não é um campo: é um segredo. Foi o **P-02** do dossiê e nunca caiu.

**Vira um chip permanente na barra da Mesa**, à direita, sempre com conteúdo:

```
   📅  SOMENTE 03/08   ✎          ← preenchida sozinha, clicável
   📅  sem data — clique  ✎        ← só se a cascata do D1 falhou (raro)
```

- **Sempre visível**, mesmo antes de existir data. Nunca um espaço em branco.
- **Cor de alerta** se estiver sem data ou com data fora do mês corrente.
- Clicar abre **um** popover — não os dois `QInputDialog` em sequência que existem hoje.

### O popover, com as respostas prontas

O dono não quer digitar data; ele quer escolher. Quatro botões e um calendário:

```
┌─ Validade da oferta ─────────────────┐
│  ● Somente segunda, 03/08   (sugerido)│
│  ○ Somente hoje, 27/07                │
│  ○ De 03/08 até 09/08                 │
│  ○ Enquanto durarem os estoques       │
│  ────────────────────────────────────  │
│  ○ Outra data…      [ 03/08/2026 📅 ] │
│                    [Cancelar] [Usar]   │
└──────────────────────────────────────┘
```

A primeira opção **já vem marcada** com o que o D1 deduziu. Um clique em "Usar" e acabou.

---

## §4 · D3 🟠 · A MENSAGEM DE ERRO TEM DE DIZER ONDE CLICAR

`servico.py:1801` diz: *"papel 'Validade da oferta' sem data — defina a validade"*.

Isso nomeia o problema e **esconde a porta** — é literalmente a frase que fez ele dizer "não faço
a mínima ideia de como fazer isso". Toda mensagem do pré-voo que pede uma ação do dono tem de
dizer **onde**:

> *"A validade da oferta está sem data. Clique no 📅 na barra, ao lado de Exportar."*

E melhor ainda: **o aviso do pré-voo vira clicável** e abre o popover direto. O projeto já tem
esse padrão — o `_ir_para_aviso` do D10 faz exatamente isso para os avisos da revisora. **Reuse
(L9), não invente.**

**Varredura junto:** ache as outras mensagens do pré-voo que pedem ação sem dizer onde, e
**liste-as** na resposta. Conserte só a da validade nesta rodada; as outras entram no G com nome.

---

## §5 · D4 🟡 · A GUARDA DE SANIDADE

Com a data preenchendo sozinha, aparece um risco novo: **data errada passar despercebida** — foi
o M-02 do dossiê (o marco publicado com validade de maio em julho).

- Data **no passado** → chip vermelho e aviso no pré-voo.
- Data em **mês diferente do corrente** → aviso (pode ser legítimo no Jornal, então é aviso, não veto).
- Validade que **não bate com o dia do encarte** (Segunda dos Frios com data de quarta) → aviso.

Nunca bloquear — a trava #3 caiu e continua caída. Só avisar, e avisar **onde clicar**.

---

## §6 · O TESTE DE ACEITAÇÃO — e é o mesmo da NONUS

**O dono abre o app, faz duplo-clique em "Segunda dos Frios", importa a tabela, e a data já está
certa na página — sem ele tocar em nada.**

Se ele precisar abrir a tela de Eventos, cadastrar coisa, ou clicar em algum lugar para a data
aparecer, **o conserto não está pronto.** A intuição que ele pediu é essa: **não ter de saber.**

Teste de gesto obrigatório (L2 + L11): duplo-clique no layout → a `_validade` da Mesa já vem
preenchida com o dia certo, **sem nenhum evento cadastrado no banco**. E um teste por pixel de que
a data chega ao selo da página composta.

---

## §7 · Nota de método

Este defeito atravessou **dez ordens**. Ele foi diagnosticado corretamente no primeiro dossiê
(P-01, P-02, P-03), consertado três vezes por caminhos diferentes — o canal do compositor (D7), a
receita da miniatura (O3), o texto do selo (C3) — e **nunca funcionou para o dono**, porque as
três vezes consertaram o *transporte* da data e nenhuma consertou a *origem*: ele não tem evento
cadastrado e não tem por que ter.

**A lição:** quando um defeito volta três vezes, pare de consertar o caminho e vá ver **de onde o
dado deveria nascer**. E a resposta, aqui, estava escrita no nome do arquivo o tempo todo.


---

# Resposta do builder (Fable) — 27/07/2026

Na ordem: D1 → D2 → D3 → D4 → §6. O diagnóstico do §1 confere linha a linha — a automação
existia e morria em `dia_do_evento(None)` porque abrir um layout pelo Ateliê nunca definia
`_evento`, e o dono não tem por que ter evento cadastrado. A resposta estava no nome.

## D1 — o encarte sabe que dia ele é

`servico.dia_pelo_nome(nome)` (nova, pública): casa o dia por **palavra inteira**, sem acento
e sem caixa — a disciplina do `extrair_marca` ("Promoção Relâmpago" e "Terceirizados" ficam
None, por teste). `dia_do_evento` ganhou a cascata exata do §2: entidade → Config legada →
o nome → None. `jornal|mês|mensal` devolve a sentinela `PERIODO_MES` e `sugerir_validade`
responde **"DE 01/mm A 27/mm"** (o período do dono, 1º ao 27) — o mês corrente enquanto o 27
não passou, senão o seguinte, com a virada de dezembro testada.

**E o autopreenchimento ganhou a porta que faltava**: `mesa.carregar_layout` — abrir o
encarte JÁ preenche (validade definida nunca é sobrescrita, por teste). Os dois pontos do
D7 (salvar/exportar) agora passam `evento or self._layout_nome`. **Achado no caminho:** a
conciliação APAGAVA a validade nascida da cascata (`self._validade = dlg.validade`
incondicional zerava com None) — guardada: só sobrescreve quando a tabela TROUXE validade.

**Divergência declarada (L6):** a regra do §2 manda "o próximo dia CONTANDO hoje — se hoje é
segunda, a validade é hoje"; a tabela ilustrativa do §1 mostra Segunda → 03/08 com hoje
segunda 27/07 (parece computada de amanhã). Segui a REGRA: em 27/07, "Segunda dos Frios"
sugere `SOMENTE 27/07` — que é exatamente a página real desta semana.

## D2 — o chip permanente e o popover

O QLabel que nascia vazio morreu. O chip (`_atualizar_chip_validade`, ponto único — os 6
`setText` espalhados convergiram, e de quebra caiu o furo do rascunho recuperado que não
atualizava o rótulo): sempre com conteúdo — `📅 SOMENTE 27/07 ✎` ou `📅 sem data — clique ✎`
— em cor de alerta sem data, **vermelho com data no passado** (D4), tooltip com os avisos.
Clicar abre `ValidadeDialog` (`app/qt/telas/validade_dialog.py`): a sugerida da cascata JÁ
marcada ("Somente segunda, 27/07 (sugerido)"), "Somente hoje", "De X até Y" (o
`montar_validade_oferta` de sempre), "Enquanto durarem os estoques" e "Outra data…" com
calendário (o primeiro `QDateEdit` do app). Os dois `QInputDialog` em sequência morreram.

## D3 — a mensagem diz onde, e o aviso abre o campo

`servico.py` (pré-voo): *"papel “Validade da oferta” sem data — **clique no 📅 na barra da
Mesa, ao lado de Exportar**"*. E `_ir_para_aviso` (o padrão clicável do D10, estendido — L9)
ganhou o alvo novo: aviso que fala de validade abre o popover direto (por teste).

**A varredura pedida — mensagens que pedem ação sem dizer ONDE (nomeadas para o G, só a da
validade consertada):** foto GENÉRICA "troque pela foto real" (não diz que é no
Almoxarifado/fotos em lote); "Fica a Dica sem texto — gere a dica pela IA" (não aponta o
painel de propriedades); "Aviso legal — escolha um preset" (não diz onde); "Edição sem
número — defina a edição" e "a edição já foi publicada — incremente" (não apontam o rótulo
da barra); a sentinela "R$ X parece baixo/alto — confira" (sem destino). Seis ao todo.

## D4 — as guardas de sanidade

`servico.avisos_da_validade(validade, nome_layout, evento, hoje=)`: data no passado (chip
VERMELHO + aviso "já passou — clique no 📅"), mês diferente do corrente (aviso — legítimo no
Jornal), dia que não bate com o encarte (29/07 numa Segunda avisa, por teste), data
impossível (31/02) avisa; validade SEM data ("enquanto durarem os estoques") passa em
silêncio — as guardas são de data. Entram nos DOIS pré-voos da Mesa (salvar e exportar) como
avisos — **nunca veto** (a trava #3 segue caída). A Fábrica/cartaz não muda (a validade do
cartaz é do item, não da oferta).

## §6 — o teste de aceitação

`test_s6_duplo_clique_no_atelie_e_a_data_ja_esta_la`: o Ateliê REAL, o duplo-clique de
GESTO, **nenhum evento cadastrado no banco** — e `m._validade == "SOMENTE {próxima
segunda}"`, o chip mostrando, e a data chegando ao SELO da página composta por pixel (o
recorte do selo com a validade difere do sem — o molde do N1). Mais o teste de fio
`test_d1_abrir_o_layout_preenche_a_validade` (carregar → preenchida; já definida → intacta).

**E a raiz REAL:** o script do caminho do dono **parou de tocar a validade** — a linha
`m._validade = "SOMENTE 27/07"` morreu e virou `assert m._validade` ("a validade não nasceu
da cascata"). Re-rodado na raiz do dono: a data nasceu sozinha no carregar, atravessou
conciliação/auto-preencher/salvar (o projeto "Segunda 27/07 — caminho do dono" REUSADO por
nome, sem duplicar a lista dele) e está no selo da página composta. Zero toques, zero
cadastros — a intuição pedida: **não ter de saber**.

## O que fica aberto, com nome

1. As **6 mensagens sem-endereço** da varredura D3 (o G as fecha).
2. O formato "DE 01/mm A 27/mm" do Jornal parte do "1º ao 27" cravado na arte atual — se o
   dono mudar o período do Jornal, a regra vira Config (nominal).
3. Os abertos herdados da NONUS (preço-da-semana do fixo via estante; duplicação
   fixo×estante; vigia que retenta; os 8 sem-porta).

## Placares (junit `bloco_fdecimus_*`)

**Suíte 1026 ×2 zero skips exit-0** (1016 + os 10 da DECIMUS; runs 1 e 2);
**invertida 1026/0/0**; **janela real 4/0/0** — as quatro DE PRIMEIRA, sem incidente.
E a raiz REAL: `saida_f13/_decimus_raiz_real.log` — a linha da rodada é
`validade NASCIDA SOZINHA: SOMENTE 27/07 · chip: 📅 SOMENTE 27/07 ✎`.

*Senão declarado:* o reuso do projeto por nome no script NÃO pegou — saiu um projeto novo
(id=9) em vez de atualizar o id=8 da NONUS; os dois têm o mesmo nome na lista do dono (ele
pode apagar um). A causa fica para o G (o `_salvar_projeto` da Mesa parece ignorar o
`_projeto_id` semeado quando o projeto não foi aberto congelado) — nomeada, não consertada.

