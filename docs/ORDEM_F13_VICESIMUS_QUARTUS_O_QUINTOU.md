# ORDEM F13-VICESIMUS-QUARTUS — OS TRÊS PEDIDOS E A AUDITORIA DO QUINTOU

> **Emitida pelo arquiteto em 04/08/2026.** O dono trouxe três pedidos diretos e mandou o
> **Quintou do Real** com a **tabela-fonte dele** ao lado — 31 itens, 06/08.
>
> Conferi **linha por linha** a tabela contra as duas páginas. **Há erro de conteúdo, e é o tipo
> mais grave que apareceu nesta engenharia: oferta cancelada que foi impressa, e marca trocada.**

---

# §1 · OS TRÊS PEDIDOS DIRETOS

## 1.1 · ACICAVE não existe mais
A bandeira está na **arte** (não há `ACICAVE` em nenhum `.py`) — sai do gerador do quadro de
pagamento e as artes se regeneram. Aproveitar para **conferir as outras onze** com ele antes de
gravar: bandeira de cartão muda, e errar isso é problema com o cliente no caixa.

## 1.2 · 🔴 O peso duplicado — "500ml · 497 ml"

**Achei.** `servico.py:770`:

```python
descritor = " · ".join(p for p in (
    juntar_com_ou(sabores) or None,
    "marca própria" if it.marca_propria else None,
    it.unidade) if p) or None          # ← o peso DA TABELA
```

E logo abaixo, a cadeia do `nome_fit` **desce a marca do NOME para o descritor** — trazendo junto
o peso que está no nome do **produto do banco**.

O comentário do próprio código diz que essa cadeia *"dedupa o peso repetido"*. **E dedupa — quando
é o MESMO texto.** `"500ml"` e `"497 ml"` não são o mesmo texto: são **dois pesos diferentes**.

- **500 ml** veio da tabela da oferta;
- **497 ml** é a correção que **ele** fez no cadastro.

O app tem os dois e imprime os dois.

**A regra que falta — e ela já existe em prosa, no K6 da ordem 12:**

> **UM ITEM TEM UM PESO SÓ.** Quando o peso da tabela e o do cadastro divergem, **vence o do
> cadastro** (é a verdade corrigida pelo dono). A divergência vira **aviso na tela da
> conciliação** — como o J10 já faz — e **nunca texto na arte**.

*Peça:* no ponto único que monta o descritor, o peso entra **uma vez**, vindo do produto; a
comparação com o da tabela produz **pendência**, não concatenação. Teste com 500 ml × 497 ml.

## 1.3 · O leque não pode ser do Jornal

`compositor.py:361` (`_leque_solo`) e `:525` estão atrás do gate de identidade "coluna com
mordida", que na prática é **só o Jornal**.

**Peça:** o leque é **capacidade do motor**, não do layout. Vale para os oito encartes e para
qualquer layout que o dono desenhar. O gate correto é **a célula ter zona replanejável e foto de
corpo único** — não o nome do encarte. Teste: a mesma foto estreita num slot do **Quintou** e do
**Sábado** também vira trio.

---

# §2 · 🔴 QUINTOU — ERROS DE CONTEÚDO (tabela dele × página)

Conferi os 31 itens. **Três achados que não podem ir para a rua:**

### **2.1 · DUAS OFERTAS RISCADAS NA TABELA FORAM IMPRESSAS**

Na tabela dele, dois itens estão **riscados** — o gesto universal de "esta não vai":

| # | linha da tabela | estado |
|---|---|---|
| **2** | ~~BIFE A MILANESA BB-X … 4,90~~ | **riscada** |
| **8** | ~~GELÉIA RITTER ALHO CARAMELIZADA 290 g … 9,90~~ | **riscada** |

**As duas estão na página 1**, com foto e preço, como oferta válida.

**Isto é o defeito mais grave que já apareceu:** o app anuncia preço de item que o dono cancelou.
No caixa, isso é conflito com o cliente.

*Peça:* o OCR **tem de enxergar tachado**. Onde a visão não garantir, a linha suspeita vira
**pendência vermelha** ("parece riscada — confirma?"), **nunca entra calada**. E o pré-voo
pergunta antes de exportar.

### **2.2 · MARCA TROCADA — Itamaraty virou Doce Dia**

| tabela | página |
|---|---|
| `AÇUCAR ITAMARATY CRISTAL 2 Kgs · 4,90` | **Açúcar Cristal *Doce Dia* 2kg · R$ 4,90** |

A conciliação casou com um produto **de outra marca** do acervo e saiu **verde**. O cliente vê
Doce Dia anunciado a 4,90 e o mercado tem Itamaraty.

*Peça:* **marca conhecida diferente = nunca verde.** O `extrair_marca` já reconhece marca com
fronteira de palavra; se a marca da linha e a do candidato **existem e diferem**, o semáforo cai
para vermelho — é a irmã da regra de peso do J10. Teste com Itamaraty × Doce Dia.

### **2.3 · Informação perdida e grafias erradas**

| tabela | página | correto |
|---|---|---|
| LINGUIÇA PERDIGÃO **TOSCANA** 100 g | Linguiça Perdigão · 100g | **perdeu "Toscana"** |
| WAFFER Bauducco | **Waffer** Bauducco | **Wafer** |
| GELATINA PREDIECTA | **Prediecta** | **Predilecta** |
| ADOÇANTE **XILITROL** | **Xilitrol** | **Xilitol** (Lowçucar) |
| CORAÇÃO e **LINGUA** BOV. | Lingua Bovina | **Língua** |
| CHA INST. DINA TEA … MELANCIA/**F. SILVESTRES** | Melancia/f. Silvestres | **Frutas Silvestres** |

As quatro do meio são erro **da tabela dele** — e é justamente para isso que existe o
`app/core/ortografia.py`. **Marca é vocabulário inequívoco:** Wafer, Predilecta, Xilitol e
Hellmann's (esta o app já acertou — prova de que o mecanismo funciona e o vocabulário é que está
curto).

### **2.4 · Dois itens de sabor ficaram inteiros**
- `BIS LACTA XTRA BRANCO e o OREO 45 g` → uma célula, uma foto (a Oreo). É **família de 2 sabores**.
- `CHA … MELANCIA/F. SILVESTRES` → idem.

O mecanismo existe desde a SEXTUSDECIMUS. **No Quintou ele não disparou** — provável mesmo gate
de layout do §1.3.

---

# §3 · QUINTOU — O DESIGN

### 3.1 🔴 **A etiqueta hachurada cobre o NOME do produto**
O carimbo vermelho listrado é **enorme**, fica **entre as colunas** e **por cima do nome**:
"Achocolatado Pirakids 200ml" e o "R$ 1,19" se atropelam; o mesmo em quase todas as células.

**É o problema da proximidade e da mordida — que o Jornal já resolveu — ainda intacto aqui.**
As leis L20/P3 e o teto de 35%/40% valem para os oito encartes, não só para o Jornal.

### 3.2 🔴 **O "R$" é minúsculo e o número é branco sobre listras**
A hachura diagonal atrás do número quebra a leitura do algarismo. *Peça: fundo chapado atrás do
número (a hachura pode ficar na borda), e o "R$" em corpo proporcional.*

### 3.3 · **Nomes em branco sobre azul, corpo pequeno** — o teste do celular vale aqui também.

### 3.4 · **A célula do canto inferior esquerdo é um logo gigante com "80/90" girado** — parece
sobra de arte. Ou é conteúdo (e precisa de sentido), ou o slot recebe produto.

### 3.5 · **"ATÉ 80/90 Só Hoje"** na p2 sai com o "80/90" **girado na vertical** entre as palavras.
Ilegível como frase.

### 3.6 · **Os selos "BB" flutuam** sobre dois itens, descolados da foto.

### 3.7 · **Fica a Dica** é uma caixa branca sobreposta ao letreiro de neon — briga com a arte. E
o texto ainda é convite de compra, não dica de uso (a regra do §13.5 da ordem 17).

### 3.8 · **Fundos inconsistentes**: uns produtos com halo branco (Achocolatado, Cotonete, Leite),
outros recortados. Na arte escura o halo salta.

---

# §4 · ORDEM DE ATAQUE

**Onda 1 — o que não pode ir para a rua:**
§2.1 (riscado) · §2.2 (marca trocada) · §1.2 (peso duplicado) · §1.1 (ACICAVE)

**Onda 2 — o motor deixa de ser do Jornal:**
§1.3 (leque universal) · §3.1 e §3.2 (mordida e legibilidade do preço nos oito) · §2.4 (sabores)

**Onda 3 — conteúdo e acabamento:**
§2.3 (vocabulário) · §3.3 a §3.8

---

# §5 · PROVA DE ACEITAÇÃO

> 1. importar a tabela do Quintou de 06/08: as **duas linhas riscadas** ou ficam de fora, ou
>    param em vermelho perguntando — **nenhuma entra calada**;
> 2. `AÇUCAR ITAMARATY` **não casa verde** com Doce Dia;
> 3. a Água Mineral sai com **um peso só**;
> 4. **ACICAVE fora**, e as outras onze bandeiras conferidas com o dono;
> 5. o trio de leque aparece **no Quintou e no Sábado**, não só no Jornal;
> 6. nenhuma etiqueta cobre nome de produto em **nenhum** dos oito encartes.

---

# §6 · Nota de método

Todas as vinte e três ordens anteriores foram sobre o Jornal do Mês. **O Quintou mostra o preço
disso:** as leis que custaram vinte rodadas — a mordida, a proximidade, o teto da etiqueta, o
leque, o piso do celular — **não atravessaram para os outros sete encartes**, porque nasceram
presas à identidade do layout onde foram descobertas.

> **L22 — LEI DESCOBERTA NUM LAYOUT VALE EM TODOS.** Regra de composição pertence ao **motor**,
> nunca ao encarte onde apareceu. Toda lei nova fecha com o teste rodando nos **oito** — e é o
> mesmo teste, não oito cópias.

E o achado do riscado merece uma segunda: **a tabela dele tem gramática** — o tachado quer dizer
"cancelei". O app leu as letras e ignorou o gesto. **Ler o texto não é ler o documento.**


---

# RESPOSTA DO BUILDER (05/08/2026)

Executada na ordem do §4 (Onda 1 → 2 → 3). Guardiões novos em
`app/tests/test_vquartus.py` (15). Backup do banco ANTES de qualquer
escrita: `core_pre_vquartus_20260805.db` (VACUUM INTO — a lei do WAL).

## Onda 1 — o que não podia ir para a rua

**§2.1 (riscado).** O OCR aprendeu o gesto: o prompt ensina a marcar
`"riscada": true` em linha tachada ("na dúvida, marque — o app pergunta
ao humano"; o hash do prompt invalida o cache antigo sozinho; o cache
novo guarda o trio e lê o par legado). A linha riscada ENTRA marcada
(L15 — sumir linha é o pecado maior): semáforo VERMELHO, pendência
`riscada`, produto NUNCA casado por baixo (o candidato fica à vista no
motivo: "casaria com …"), FORA das filas automáticas do diálogo
(enriquecer/criar em lote — o pulo é dito por toast), e o pré-voo de
salvar E exportar pergunta se um riscado estiver NA PÁGINA
(`avisos_de_riscadas` — aviso, nunca veto, trava #3).

**§2.2 (marca trocada).** A caça no banco REAL achou a causa: o alias
141 (`"1 AÇÚCAR ITAMARATY CRISTAL 2 Kgs" → produto 68 Doce Dia`) nasceu
ONTEM às 16:20 — uma confirmação errada na importação virou verde
permanente e calado (o caminho exato/alias não passava por guarda
nenhuma: "a escolha do dono vale"). Três consertos: (1) a guarda nova
`_vermelho_se_marca_troca` — marca conhecida da linha × marcas do
candidato (nome + campo `marca`) disjuntas ⇒ VERMELHO com produto=None
(nada se pré-aceita; roda ANTES do S1/J10); (2) o ALIAS com marcas
conflitantes NUNCA mais passa verde — desce a AMARELO com o conflito
dito todo import (o vínculo do dono fica, mas nunca calado); (3)
higienização: alias 141 REMOVIDO; "itamaraty" entrou no seed de marcas
(inequívoca — açúcar/rosquinha do próprio acervo). Teste com o juiz IA
confirmando a 0,95 (o cenário da máquina dele) → VERMELHO.

**§1.2 (peso duplicado).** Como o senhor localizou — e com um agravante
medido: o "500ml" nem vinha da tabela; vinha do campo estruturado
`peso_valor=500` que NÃO acompanhou a correção do nome ("497ml") feita
pelo dono. O conserto no ponto ÚNICO (`dados_para_desenho`): o peso do
NOME DO CADASTRO vence a unidade divergente — `unidade_arte` alimenta o
descritor E a régua de dedupe do nome_fit (um peso só, sempre); a cauda
do nome_fit ganhou o cinto (peso do resto igual à unidade nunca entra).
A divergência vira o aviso J10 da conciliação (que agora dispara de
verdade: `peso_valor` 500→497 higienizado). Testes: 500ml×497ml,
peso igual intacto, e a cadeia inteira com UM peso por contagem.

**§1.1 (ACICAVE).** Fora do gerador (`gen_jornal_final.py`); a fileira
incompleta de 5 agora CENTRA (não fica buraco); artes regeneradas (T6)
e pacote reimportado no banco real. **As 11 restantes, para o dono
conferir ANTES de valer:** VISA, MASTERCARD, ELO, MAESTRO, AMEX, ALELO,
SODEXO, TICKET, VR, DINERS, PIX (recorte em
`saida_f13/_vq_quadro_pagamento.png`).

## Onda 2 — o motor deixa de ser do Jornal

**§1.3 (leque universal).** O gate de identidade caiu: o leque dispara
em QUALQUER zona ASSENTAR de foto recortada, pela régua da tinta. Dois
achados de régua no caminho (L21 aplicada duas vezes):
- o HERÓI fixo de 60 mm faria TODA célula do Quintou (67 mm) e do
  Sábado (81 mm) virar "herói" — editorial agora é RELATIVO à página
  (pré-passe: >60 mm E >1,25× a mediana das zonas, OU página com <3
  zonas — o cartaz/destaque solo segue UM produto; o cartaz usa CONTER
  e nem entra);
- o plano Q1 e o leque são estratégias CONCORRENTES de preencher: onde
  o plano ATUOU (o abraço do banner da Quarta — contrato do dono), o
  leque cede (`_q1_uids`); onde ele devolve None, quem preenche é a
  L19. Guardião: a MESMA garrafa vira trio no Quintou E no Sábado
  (um teste só, nos layouts reais do banco — L22/L16), com a mutação
  do gate antigo deixando-o vermelho.

**§3.2 (o número legível).** Na ETIQUETA_LISTRADA o número ganha fundo
CHAPADO na cor dominante da PRÓPRIA etiqueta (amostra NEAREST do miolo
— o bilinear misturava o vermelho da listra com o azul do fundo e o
chapado saía ROXO na 1ª prova; consertado), a hachura fica na borda, o
"R$" gravado minúsculo da arte some sob o chapado e o app desenha o
"R$" em corpo PROPORCIONAL (`_moeda_na_listrada`). Por pixel: a faixa
central perde as listras.

**§3.1 (a etiqueta que cobre) — a restrição descoberta e DECLARADA:**
no Quintou a etiqueta hachurada é a CAMADA do dono (QUATER/L9, selada:
"o asset é consumido, nunca imitado") — arte COLADA na página; o motor
não pode movê-la nem escalá-la sem derrubar aquela decisão. O que o
motor manda (pouso pela silhueta, teto, mordida) já era estrutural e
vale nos oito; a legibilidade veio pelo §3.2. **Fica NOMEADO ao
arquiteto/dono decidir:** manter a etiqueta-arte (como está) ou trocar
pela sintética escalável que obedece mordida/teto (derruba QUATER/L9).

**§2.4 (sabores) — a investigação desmentiu a suspeita:** não era o
gate do §1.3. O Bis Branco e Oreo virou COMPOSTO pela mão do dono na
importação (2 componentes, UMA foto — a curadoria do 2º componente foi
pulada); o Chá casou por ALIAS com o cadastro que já nasceu cru
("Melancia/f. Silvestres"). Consertos executáveis feitos (vocabulário +
higienização abaixo); transformar os dois em FAMÍLIA com foto POR SABOR
é curadoria do dono (as fotos não existem no acervo) — NOMEADO.

## Onda 3 — vocabulário e acabamento

**§2.3.** Seed da ortografia: `prediecta→Predilecta`,
`xilitrol→Xilitol`, `lingua→língua`, `coracao→coração` (achado do
próprio teste) + expansão por par `"f. silvestres"→"frutas silvestres"`
("f." solto é ambíguo — só o par entra). "waffer→wafer" JÁ estava no
seed — o "Waffer" da página era CADASTRO sujo (item casado usa o nome
do banco). Higienização nominal (6 produtos): Wafer Bauducco,
Predilecta, Xilitol, Língua ×2, Chá Melancia/Frutas Silvestres.
**O Toscana** ganhou a guarda-espelho
`_rebaixar_se_qualificador_perdido`: qualificador CONHECIDO da oferta
ausente do candidato (vocabulário conservador: toscana/calabresa/
defumada·o) rebaixa a amarelo com o motivo dito — o S1 só olhava a
direção cadastro→oferta.

**§3.6.** O selo ENCOSTA no produto: a âncora desce até o topo da TINTA
(respiro de 2 mm) — a irmã vertical do desvio do §3.3; o BB flutuava no
vazio do topo da zona porque a foto assenta no chão.

**§3.4/§3.5 — CONFLITO arquiteto × dono, não executado:** a data
girada (o "06/08" no tijolo, o neon entre "ATÉ" e "Só Hoje") é DECISÃO
DO DONO registrada no adendo de 30/07 ("o publicado escreve a data em
neon vertical ali" — medida do publicado dele, `rot=90` deliberado no
builder). Ambiguidade do dono se pergunta, não se escolhe — só ele
desempata. Idem o destino da célula do logo (§3.4: arte ou produto).

**§3.3/§3.7/§3.8 — NOMEADOS (curadoria/arte):** corpo dos nomes já tem
o piso do celular de runtime (U1); a caixa do Fica a Dica é arte do
fundo + o TEXTO é conteúdo do projeto (regenerar pela IA com a regra
§13.5 é 1 clique do dono); os halos brancos (Cotonete/Achocolatado/
Leite) são fotos sem recorte — Estúdio degrau 1, curadoria.

## Incidentes de bancada (honestidade)

1. O guardião do leque exigia 1,8× e mediu 1,77× no Quintou — régua
   MINHA arbitrária (flancos a 88% entrando atrás); baixada a 1,5×,
   que ainda mata a mutação do gate antigo (com ele, com==sem).
2. O teste do chapado com listras 50/50 deixou o AZUL vencer o sorteio
   da cor dominante — o dado do teste virou vermelho-dominante como a
   arte real (dado, não motor).
3. `test_q1_por_pixel_a_foto_sobe_do_chao` quebrou DE PROPÓSITO: o
   contrafactual sem-flex agora é preenchido pelo leque (o paredão
   nunca mais fica vazio por caminho nenhum); o teste mede o plano Q1
   ISOLADO (leque desligado só ali) — inventariado no próprio teste.
4. O 1º chapado saiu ROXO (mistura bilinear) — consertado com NEAREST
   no miolo; visível no antes/depois de `saida_f13/`.
5. A família 0xC0000005 apareceu 3× em runs PARCIAIS fora de ordem
   (test_rodada_125_v3 sem o warmup do os_f11_5 na frente — COND-10
   conhecida; "endurecer vigias" segue prioridade da fila).

## Prova de aceitação (§5)

1. riscada nunca entra calada — guardião verde (vermelho perguntando);
2. Itamaraty não casa verde com Doce Dia — guardião verde (fuzzy/juiz
   → VERMELHO; alias → AMARELO dito) + alias 141 removido do banco;
3. a Água Mineral sai com UM peso (497ml) — guardião por contagem;
4. ACICAVE fora + as 11 conferíveis no recorte — FALTA o dono conferir;
5. o trio no Quintou e no Sábado — guardião verde nos layouts do banco;
6. nenhuma etiqueta cobre nome nos oito — no Quintou a etiqueta é ARTE
   do dono (restrição declarada acima); o pouso/teto do motor valem
   nos oito por estrutura; a legibilidade resolvida pelo §3.2.

## O que ficou de fora (nomeado)

- A decisão etiqueta-arte × etiqueta-sintética no Quintou (§3.1 pleno);
- Bis/Chá como FAMÍLIA com foto por sabor (curadoria + fotos);
- a data girada e a célula do logo (decisão do dono, conflito declarado);
- Fica a Dica do Quintou (texto do projeto; 1 clique regenera);
- halos brancos (Estúdio, curadoria);
- endurecer vigias (COND-10/test_b1 — prioridade da fila);
- pendências antigas do dono: marca-no-nome (4ª vez), H3-contagem, K2.

