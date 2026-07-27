# ORDEM F13-SEPTIMUS — O ORÇAMENTO DA CÉLULA (e a regra que EU escrevi errado)

> **Emitida pelo arquiteto em 27/07/2026.** O dono olhou a Segunda de 27/07 montada no app e
> disse: *"as imagens estão imensas, chega ao bizarro. Enquanto isso, o texto está minúsculo…
> E o Kit Burguer ficou pequeneninho. E a data também ficou estranha."*
>
> Abri a página composta do projeto salvo (`projetos/57000fd5…/miniatura.png`). **Os quatro
> pontos dele estão certos, e o primeiro é culpa da minha régua.**

---

## §1 · O QUE EU FIZ DE ERRADO: dei um piso sem teto

Na QUINQUE §5 eu escrevi:

> *"Regra de aferição: a **foto** de cada item tem de ficar com **≥ 55% da área da célula**."*

O builder cumpriu — e **otimizou para o número**, porque era o único número na mesa. Sem limite
superior, "≥ 55%" virou "o máximo possível". Resultado na Segunda: a foto come ~85% da célula, a
faixa do nome virou uma tira, e o tipo encolheu para caber nela.

**Eu troquei um defeito por outro em duas rodadas:** da foto raquítica (o quadrado do
`normalizar`) para a foto gulosa. A culpa da segunda metade é minha, e o conserto é substituir o
piso solto por um **orçamento fechado**.

### O1 🔴 · O orçamento da célula (a régua nova, com faixa)

Toda célula de produto passa a ter um orçamento **declarado e verificado**, em % da altura útil:

| Zona | Faixa | Regra dura |
|---|---|---|
| **Foto** | **55 % – 68 %** | nunca abaixo de 55, **nunca acima de 68** |
| **Nome** | 20 % – 28 % | **mínimo 2 linhas** no corpo legível |
| **Descritor** | 8 % – 12 % | pode ser omitido se o nome precisar das 2 linhas |
| **Preço** | sobreposto | a forma vive por cima da foto, não rouba altura |

**E a regra que manda em todas:** existe um **corpo mínimo de nome** (a definir olhando, mas
calibrado pelo Quintou, que está aprovado). **Se o nome não couber no corpo mínimo em 2 linhas, a
FOTO cede altura — nunca o texto.** Hoje é o contrário: o texto cede até virar ilegível.

Teste: para as 8 páginas, reportar por célula o % de cada zona e falhar se sair da faixa.
Substitui a regra de "≥55%" da QUINQUE, que fica **revogada**.

---

## §2 · OS OUTROS TRÊS PONTOS DELE

### O2 🔴 O Kit Burguer é a menor foto da página, na maior célula
A célula fixa central (o oval "KIT BURGER") é a maior da Segunda, e a foto do saco kraft dentro
dela é um **selo minúsculo** acima do nome. Inverteu-se: a célula gigante ficou com a foto
pequena, e as células normais ficaram com fotos gigantes.

**Causa provável:** a zona de foto da célula fixa não foi reescalada quando o V1 mudou o ajuste —
ela ficou com a medida antiga, pensada para o placeholder do PREVIEW. **Confira e corrija:** a
foto do item fixo obedece ao mesmo orçamento do O1, calculado sobre o **oval**, não sobre um
retângulo herdado. E no oval a foto tem de respirar — é a peça de maior destaque do encarte.

### O3 🔴 A data não chegou à página
No selo do topo-direito está escrito `TODA SEGUNDA ★ LEITERIA` — **sem data nenhuma**. E o rodapé
diz *"Ofertas válidas somente na segunda ou enquanto durarem os estoques"* — o texto **genérico de
reserva**. A validade `SOMENTE 27/07` que a sua resposta afirma ter gravado **não está visível em
lugar nenhum da página composta**.

Isto é grave por dois motivos: (a) é o **M-02 do dossiê pela quarta vez** (a validade que não
chega); (b) sua resposta afirma um resultado que o artefato não contém — o **M-06**, a família do
"relatório que diz o que o PNG não mostra". Trace o caminho inteiro (dado → `validade_oferta` →
região do selo → composição) e prove por pixel que a data aparece.

### O4 🟠 O preço colide com o produto
Com a foto a 85% da célula, os medalhões de cera passaram a pousar **sobre o produto** (o
`R$ 2,44` no queijo, o `R$ 38,00` na caixa do azeite). Com o orçamento do O1 isso melhora sozinho;
se persistir, a âncora do medalhão desvia para o canto de menor tinta da foto.

---

## §3 · O QUE FICOU BOM — para não perder no próximo ajuste

Registro porque houve avanço real e ele não pode regredir:

- **`Azeite Gallo Extra Virgem Clássico 500ml`** saiu **inteiro, numa linha, sem hífen** — o S4
  funcionou.
- **`Suco de Uva Aurora Tinto TP 1,5L`** — o `1,5L` normalizado com **L maiúsculo**, a regra
  travada. *(Sobra: o `TP` ainda está no nome; devia ir para o descritor.)*
- **O Kit Burguer pegou o R$ 39,00 da tabela** pela chave natural — o N1 funcionou de verdade, no
  primeiro uso real.
- **O parser comeu os `POR ____` / `SÓ ____`** da tabela impressa dele.
- **Os 8 itens reais estão na página**, com os substitutos declarados.

**A correção de contas dele está aceita:** a Segunda tem 7 livres + 1 fixa, e a tabela de 8 fecha
exata. Minha regra do "redistribuir para 7" fica registrada para quando a conta **não** fechar —
e esse caso vai aparecer, porque a tabela dele raramente fecha o número exato.

---

## §4 · A LIÇÃO DE MÉTODO (para mim, e vale para o resto do projeto)

**Toda régua numérica que eu escrever tem de ter faixa, não piso.** Um piso solto num sistema que
otimiza vira teto. Já aconteceu duas vezes nesta fase:

1. *"≥ 55% de foto"* → foto a 85% e texto ilegível (esta ordem).
2. *"razão de densidade ≥ 0,95"* → risco de o builder encher a página de tinta para bater o
   número. **Corrijo agora:** a densidade alvo do Jornal passa a ser **0,95 – 1,15**, e a Quinta
   (hoje em 1,52) entra na lista de conferência exatamente por isso.

E a régua definitiva continua sendo o **Quintou**: ele está aprovado, tem razão 1,02 contra o
publicado real, e tem a proporção foto/texto que o dono aceita. **Calibre as outras sete por ele**
— meça as zonas do Quintou e use como referência do orçamento do O1.

---

## §5 · ORDEM DE ATAQUE

1. **O1** — o orçamento com faixa, medido nas 8 páginas. É o conserto que resolve "imagens
   imensas" e "texto minúsculo" de uma vez.
2. **O3** — a data, com prova por pixel. É defeito funcional, não estético.
3. **O2** — a foto do item fixo (Kit Burguer, e o mesmo vale para as 3 fixas da Quarta e as 2 da
   Terça).
4. **O4** — a colisão do preço, se sobrar depois do O1.
5. Só então a galeria e as sobras do §5 da SEXTUS (Sonho+Croissant, a Quinta a 1,52, o Jornal).

**E gere a página do PROJETO SALVO, não só a da galeria** — foi na `miniatura.png` do projeto
que estes quatro defeitos apareceram. A L10 diz que a prova é o que o dono abre; então a prova
desta rodada é o projeto na Mesa dele, recomposto e reaberto.


---

# Resposta do builder (Fable) — 27/07/2026

Na ordem do §5: O1 → O3 → O2 → O4 → o projeto salvo recomposto. E a prova desta rodada é a que
a L10 manda: **o projeto id=7 na Mesa, reimportado e recomposto** (a miniatura nova nasce da
montagem oficial).

## O3 — a data chegou, e a causa era a doença CONHECIDA (M-02 ×4 explicado)

`_gerar_miniatura` montava uma **TERCEIRA receita à mão** — `DadosProduto` sem `texto_legal`
(a validade!), sem descritor, sem edição. A MESMA doença do Modo Pai que a frota F12 matou
("montava à mão e imprimia diferente"). Por isso a MINHA composição (galeria) tinha a data e a
SUA página (a miniatura do projeto) não — e a minha resposta afirmou o que o seu artefato não
mostrava (o M-06: eu olhei o artefato errado). A miniatura agora compõe pela **montagem
oficial** (`dados_para_desenho` com validade + edição) — teste por pixel
(`test_o3_a_validade_chega_a_miniatura_do_projeto`) e o "SOMENTE 27/07" está no selo da página
recomposta.

## O1 — o orçamento com faixa (a régua ≥55% da QUINQUE está revogada)

Confirmei por número o que o dono viu: **a celula-2 estava com 87% de foto**. O orçamento novo
na Segunda: fotos 55–68% da altura útil (flancos 248→190, etiquetas 245→186 e 209→160) e o TIPO
SUBIU (nomes 12,75→14,5 · 15→16 · 13,9→15; descritores idem) — a regra que manda: o texto nunca
cede. Teste `test_o1_o_orcamento_da_celula_na_segunda`: faixa 55–68% de foto + zona de texto
≥16% + corpo do nome ≥14pt, por célula. *Nota declarada:* a banda azul é DA ARTE (60px) — o
orçamento nominal pleno (nome 20–28%) na Segunda exigiria regenerar a banda (nominal); dentro
dela, 2 linhas legíveis cabem e estão medidas.

## O2 — o Kit respirou (a causa exata)

A zona de foto da fixa era um **banner largo e baixo (312×90)** — herdada do placeholder
horizontal do PREVIEW; o saco kraft é ALTO, o ASSENTAR limitava pela altura e saía um selo.
A zona virou alta (192×112 no miolo do oval) — o Kit agora é visível como o destaque que é.
Teste `test_o2_a_foto_do_kit_respira_no_oval`.

## O4 — melhorou com o O1

Com as fotos no orçamento, os medalhões pousam nas bordas (o R$ 2,44 saiu do queijo). A âncora
desviante fica de reserva se a reauditoria ainda apontar colisão.

## O achado do rollout (e o conserto de motor que ele pagou)

Ao reimportar o pacote na sua raiz para o orçamento chegar ao banco, detectei ANTES de rodar:
**o upsert do import APAGARIA o `conteudo_fixo` do Kit** — a configuração N1 do dono morreria a
cada atualização de encarte. O import agora **preserva o conteúdo fixo por slot.id** no upsert
(teste `test_upsert_do_import_preserva_o_conteudo_fixo`). Reimportei com a preservação, remontei
o projeto (id=7 reaproveitado por nome, sem duplicar) e recompus.

## §4 — as réguas com faixa

A densidade do Jornal 0,95–1,15 anotada como a régua vigente; a Quinta (1,52) segue na lista de
conferência. **Conflito a decidir (L6):** o QUINTOU APROVADO mede **foto ≈69% da área / ~74% da
altura útil** — fora da faixa 55–68 do O1. Ou a faixa ganha teto 70% para acomodar o
padrão-ouro, ou o Quintou é exceção declarada (é o publicado dele). Não mexi no Quintou.

## O que fica aberto, com nome

1. O rollout do orçamento O1 nas OUTRAS páginas (Terça/Quarta/Quinta/Sexta/Sábado — a Segunda
   foi o piloto medido; o teste está pronto para estender por encarte).
2. As sobras da SEXTUS §5 (Sonho+Croissant; Quinta 1,52; Jornal na densidade 0,95–1,15).
3. O `TP` do Suco para o descritor (anotado no §3 da ordem).
4. As decisões do dono (painel/período/dica na célula 13).

## Placares (junit `bloco_fseptimus_*` em `saida_f13/`)

- Suíte inteira ×2: **999 verdes / 0 falhas / 0 skips, exit 0** nas duas (995 + 4 da SEPTIMUS).
- Ordem invertida: **999/0/0**. Janela real: **4/0/0**.
- Quarta bancada seguida sem incidente.


