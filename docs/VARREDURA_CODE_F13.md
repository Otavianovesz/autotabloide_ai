# VARREDURA F13 — o lado do Code

> **Status: DIAGNÓSTICO. Nenhuma linha de `app/` foi alterada.** As únicas escritas desta
> fase são este arquivo e `docs/VISAO_CODE_F13.md`.
> Emitido pelo **builder (Claude Code)** em 24/07/2026, respondendo a
> `docs/BRIEFING_VARREDURA_CODE.md` (arquiteto) — frente paralela ao
> `docs/DOSSIE_AUDITORIA_F13.md` (133 achados, frentes T/V/E/R/P/C/I/X/F/D/A/U/N).
>
> **Método:** 8 agentes de auditoria em paralelo (um por frente do briefing), + 8 céticos
> adversariais tentando REFUTAR os próprios achados, + verificação pessoal do builder na
> fonte nos pontos em que um erro custaria credibilidade. **E — o que o arquiteto não pôde
> fazer — a bancada rodou de verdade:** 5 passadas completas da suíte na máquina do dono,
> mais a prova de mutação dirigida.
>
> **Prefixos:** `CA`(instalador) `CB`(arquivos/cofre) `CC`(scripts) `CD`(histórico)
> `CE`(seções/imposição) `CF`(teclado) `CG`(DPI/monitores) `CH`(código morto).

---

## §0 · O veredito em doze linhas

1. **A suíte não mede o programa — agora com número.** Quebrei de propósito as 6 linhas 🔴
   do dossiê do arquiteto e rodei os 851 testes: **5 das 6 não deixaram NENHUM teste
   vermelho.** A única pega (E-01) foi pega por acidente, por um teste que testa outra coisa.
2. **"851 verdes, zero skips" é uma propriedade da PASTA DE TRABALHO, não do código.** Da
   raiz do projeto: 851/0/0. De qualquer outra pasta: **10 falhas e 8 pulados**. E como
   `arte/` está no `.gitignore`, **nenhum clone deste repositório reproduz a prova** — nem
   o PC novo do dono.
3. **A suíte é dependente de ordem, e o vazamento é no módulo do véu.** Rodando os mesmos
   851 testes em ordem invertida: **2 vermelhos**, ambos porque `animacoes.py` ficou com 2
   animações vivas de um arquivo anterior. É a confirmação POR EXECUÇÃO do que o arquiteto
   provou por leitura (V-01/V-02).
4. **O boot do programa baixa 973 MB da internet, sem pedir, num app que é offline por lei**
   — e o `GUIA_RAPIDO.md` promete exatamente o contrário. Medido no disco do dono. (CA-01)
5. **Corrigir o preço de um item na Mesa APAGA a pilha inteira de desfazer.** É a explicação
   dos 9 Ctrl+Z da gravação: ele agrupou sem querer (E-01 do arquiteto), mexeu no preço, e o
   desfazer já não existia mais. (CD-01)
6. **A caixa "Não tem volta" do app inteiro tem o botão DESTRUTIVO como padrão e com o
   foco.** Apertar Enter apaga. Reproduzido em PySide6 real, 13 pontos de chamada. (CF-01)
7. **No programa instalado não existe registro de erro nenhum:** `console=False` faz
   `stdout`/`stderr` serem `None`, e todo o app reporta com `traceback.print_exc()`. O
   "Gerar diagnóstico para suporte" entrega um zip sem um único traceback. (CA-02)
8. **O snapshot automático do boot copia o banco JÁ corrompido** e a rotação empurra os
   backups bons para fora. Dez aberturas depois do estrago, não há de onde voltar. (CB-01)
9. **Ctrl+K está MORTO na Mesa** (dois donos da mesma tecla ⇒ o Qt não dispara nenhum) — e
   existe um teste chamado `test_ctrl_k_abre_em_duas_telas` **verde**, que nunca aperta a
   tecla. É o mascaramento em estado puro. (CF-02)
10. **O juiz IA pinta VERDE com qualquer confiança — inclusive 0,05.** A confiança é lida e
    nunca comparada a limiar nenhum. Verde significa "não precisa conferir": é assim que o
    produto errado entra na peça sem ninguém ver. Fere a decisão travada da F9
    ("ambíguo vira amarelo"). (CI-03)
11. **A foto ORIGINAL do produto é apagada em silêncio na 11ª troca** — viola a decisão
    travada da F10 (*"curadoria não-destrutiva, original sempre preservada"*). (CI-05)
12. **O `%TEMP%` do dono tem 40.462 pastas `atb_historico_*` (523 MB)**, cada uma com o JSON
    do trabalho dele. `Historico.limpar()` não tem um único chamador no app. (CD-03)

**O que eu verifiquei e está SÃO** (para ninguém gastar tempo): o boot é rápido de verdade
(114 ms de import medidos aqui); o `_grade_sintetica()` realmente segura o boot no PC limpo
— o "exe meio-morto" da F12 **foi** consertado no que era crash; não há import dinâmico
(`importlib`/`__import__`) em `app/`, então o risco de `hiddenimports` faltando é pequeno;
os `.pyc` órfãos de `src/`, `alembic/` e `tests/` são **inertes** (bytecode em `__pycache__`
não é importável sem o fonte) — é confusão, não risco.

---

## §1 · A bancada, medida de verdade (o que o arquiteto não pôde fazer)

Todos os números do dossiê do arquiteto são de leitura estática — o sandbox dele não tinha
PySide6. Rodei aqui, na máquina do dono, com `python -m pytest`.

### 1.1 · Cinco passadas completas

| passada | testes | falhas | pulados | tempo | exit |
|---|---:|---:|---:|---:|---:|
| raiz do projeto (1ª) | 851 | **0** | **0** | 219 s | 0 |
| raiz do projeto (2ª) | 851 | **0** | **0** | 289 s | 0 |
| **de outra pasta (CWD)** | 851 | **10** | **8** | 235 s | 1 |
| **ordem de arquivos invertida** | 851 | **2** | 0 | 229 s | 1 |
| **com as 6 mutações 🔴 aplicadas** | 851 | **1** | 0 | 240 s | 1 |

A linha 1 e 2 **confirmam a alegação do CLAUDE.md**: 851 verdes, zero skips, exit-0, duas
vezes. As três de baixo são o assunto deste documento.

> **Como reproduzir** (os `.xml`/`.txt` das cinco passadas ficaram fora do repositório de
> propósito — a Regra Zero só autoriza estes dois documentos, e deixar `_f13_*.xml` na raiz
> seria repetir exatamente o achado CH sobre entulho versionado):
> ```bash
> python -m pytest app/tests -q --junitxml=_run.xml                      # linhas 1 e 2
> cd /qualquer/outra/pasta && python -m pytest <repo>/app/tests -q       # linha 3
> python -m pytest $(ls app/tests/test_*.py | sort -r) -q                # linha 4
> ```
> A linha 5 (mutações) está descrita passo a passo em §1.4.

### 1.2 · O gesto real na bancada (números meus, conferindo §1 do dossiê)

| medida | meu número | dossiê |
|---|---:|---:|
| `def test_` | 832 | 832 ✅ |
| testes coletados (com parametrização) | **851** | — |
| `QTest.mouseClick` / `keyClick` | **0** | 0 ✅ |
| `.trigger()` de QAction | **0** | 0 ✅ |
| `QApplication.sendEvent` (chamada real) | **1** | 1 ✅ |
| `.click()` em botão real | **2** | 2 ✅ |
| `dropEvent` / `QMimeData` | **0** | 0 ✅ |
| **`contextMenuEvent` / `QContextMenuEvent`** | **0** | (não medido) |
| **`QSignalSpy`** | **0** | (não medido) |
| `instalar_vida` / `instalar_polimento` em testes | **0** | 0 ✅ |
| `confirmar_pre_voo` monkeypatchado | **6** | 5 (são 6) |

**Os dois números novos são os que doem.** `contextMenuEvent = 0` significa que **nenhum
teste da suíte abre um menu de contexto** — e é lá que moram carimbar, duplicar, agrupar,
travar, isolar e o override de célula. `QSignalSpy = 0` significa que nenhum sinal é
observado: prova-se o estado final, nunca a notificação que a tela recebe.

### 1.3 · Por que os testes de pixel não pegam nada de tipografia

A suíte tem **72 chamadas de `getpixel`** — amostragem absoluta de verdade, não é "não deu
exceção". Mas varrendo o que elas amostram: **todas** miram cor de imagem, canal alfa ou o
centro do slot. **Nenhuma afere a posição de um bloco de texto.** Somado a isso, as 25
comparações `getdata()` são **relativas** (`com != sem`), e uma mudança global de renderização
**se cancela** nos dois lados da comparação.

É exatamente por isso que a mutação R-01 (jogar TODO texto do produto para o topo da região,
em vez de centralizado) passou por 851 testes sem acender uma luz.

### 1.4 · A prova de mutação dirigida (§3.5 do briefing)

Método: quebrei a linha citada de 6 achados 🔴 do dossiê, rodei os 851 testes, depois
desfiz com `git checkout --` (árvore conferida limpa com `git diff --quiet`). Como o
resultado conjunto deu 1 vermelho, atribuí rodando cada mutação isolada contra o teste que
caiu.

| # | achado | linha quebrada | mutação aplicada | **testes vermelhos** |
|---|---|---|---|---:|
| 1 | **V-01** véu órfão | `animacoes.py:287` | remover o `destroyed.connect(...pop...)` | **0** |
| 2 | **E-01** região herda o slot | `canvas.py:1396` | `setSelected(it.regiao is reg)` → `setSelected(False)` | **1** |
| 3 | **R-02** subir/descer invertidos | `painel_camadas.py:67-72` | trocar os deltas de Subir e Descer | **0** |
| 4 | **E-08** rotação trava o resize | `itens.py:438` | remover a guarda de rotação | **0** |
| 5 | **F-01** etiqueta sem +18 | `servico.py:1858-1863` | tirar o **preço** da etiqueta em lote | **0** |
| 6 | **R-01** Y do texto incondicional | `compositor.py:312` | `oy = y + (rh-total_h)//2` → `oy = y` | **0** |

**Cinco das seis linhas mais críticas do programa podem ser destruídas sem que a bancada
pisque.** E a única que acendeu, acendeu por acaso: o vermelho foi
`test_adversarial_vinculo.py::test_c5_agrupar_nao_deixa_fantasma`, um teste de **agrupamento**
que depende de haver seleção — ele não testa a auto-seleção, tropeçou nela.

Nota de bancada: a mutação nº 5 é a mais eloquente. O achado F-01 do arquiteto é "a etiqueta
em lote sai sem o selo +18". Eu fui além e tirei **o preço**. Uma etiqueta de gôndola sem
preço saiu do forno, virou PDF, e os 851 testes seguiram verdes.

### 1.5 · O placar é da pasta, não do repositório (§3.1 do briefing)

Rodando os mesmos 851 testes com o CWD em outra pasta:

**10 vermelhos**, por quatro causas distintas:

| causa | testes |
|---|---|
| `"Frente Template.png"` (nome nu, na raiz do repo) | `test_consolidacao::test_gate_compoe_sobre_arte_real_1080x1300`, `test_fase2_busca::test_ctrl_k_abre_em_duas_telas`, `test_grade::test_detecta_15_caixas`, `test_grade::test_layout_grade_tem_15_slots` |
| `arte/quintou/...` sem guarda de skip | `test_fase5_editor::test_migracao_layout_antigo_real_do_acervo`, `test_fase12_marco::test_d_campanhas_descobertas_e_faltantes_nomeadas` |
| `app/tests/fixtures/...` relativo ao CWD | `test_mesa::test_importar_banco_vazio_fica_tudo_vermelho`, `test_mesa::test_importar_banco_cheio_fica_verde` |
| fontes reais ausentes | `test_onda1_desempenho::test_mapa_de_fontes_usa_cache_em_disco`, `test_onda3_editor::test_variantes_da_familia_bundled` |

**8 pulados em silêncio** (os 4 arquivos com `pytestmark = skipif(Path("arte/quintou")…)`):
3 em `test_deteccao_quintou`, 3 em `test_multipagina`, 1 em `test_marco_f8`, 1 em
`test_fase12_marco`.

**E o pedaço invisível, que é o pior.** Doze arquivos de teste (**205 testes**) fazem:

```python
reais = Path("AutoTabloide_System_Root/fontes")
if reais.exists():                       # ← sem else, sem aviso, sem skip
    for f in reais.glob("*.ttf"):
        shutil.copy(f, root.fontes / f.name)
```

Sem as fontes reais, `text_fit._fonte` cai em `ImageFont.load_default(px)`
(`text_fit.py:133-142`) — métricas completamente diferentes — e **os testes seguem VERDES**.
Confirmei rodando `test_adversarial_vinculo.py` de outra pasta: **32 testes, todos verdes,
sem uma única fonte real**. O teste-joia do I5 muda de significado e ninguém fica sabendo.

> **A causa-raiz não é só o CWD** (e isso importa para o conserto, senão se conserta errado):
> `git ls-files arte` = **0** e `git ls-files AutoTabloide_System_Root` = **0**.
> `.gitignore:78-82` ignora `arte/`, `Frente*.png`, `Verso*.png`. **Nenhum clone deste
> repositório tem os arquivos.** Trocar `Path("arte/…")` por um caminho absoluto a partir de
> `__file__` **não resolve nada** — o arquivo não existe no clone. O conserto é decidir se a
> arte de bancada entra no repositório ou se os testes passam a falhar alto quando ela falta.

### 1.6 · A suíte depende da ordem — e o vazamento é no módulo do véu

Rodando os 851 testes com os arquivos em ordem **invertida**: **2 vermelhos**, os dois em
`test_fase1_ui.py`, os dois pela mesma razão:

```
test_reduzidas_significa_zero_animacoes_em_voo
test_ligadas_registra_e_finaliza
    AssertionError: assert 2 == 0
      where 2 = animacoes.animacoes_ativas()
```

Duas animações de um arquivo de teste anterior continuavam registradas em `_VIVAS`
(`animacoes.py:80-89`). O módulo tem **cinco registros globais** — `_cache_config`, `_VIVAS`,
`_veus`, `_hovers`, `_veus_troca` — mais dois singletons, e **nenhum é zerado entre testes**.

**Mecanismo provável, e é irônico:** `_VIVAS` só é limpo por `finished` **ou** por
`destroyed`; mas o `conftest.py:38-46` — a lei nova da F12 contra o segfault — **descarta**
os `DeferredDelete` pendentes. Widget cuja destruição foi descartada **nunca emite
`destroyed`**, logo nunca sai de `_VIVAS` (nem de `_veus`). O conserto do segfault comprou,
de brinde, a garantia de que os registros do véu vazam na bancada.

*Isto é a confirmação por EXECUÇÃO do V-01/V-02 do arquiteto, que ele só pôde provar lendo.*
Nota de método: `pytest-randomly` não está instalado nesta máquina, então a inversão da ordem
dos arquivos foi a sonda possível. Ela já achou o suficiente.

---

## §2 · FRENTE CA — instalador e primeira execução em Windows limpo

### CA-01 🔴 O boot baixa 973 MB da internet sem pedir — num app que é offline por lei
**Sintoma potencial:** o dono abre o AutoTabloide no PC da loja e, sem clicar em nada, o
programa começa a puxar quase 1 GB do GitHub em segundo plano. Não há barra, não há aviso,
não há "agora não". Em internet fraca (ou no 4G do celular), a máquina fica lenta e o plano
de dados some; se ele fechar antes de terminar, recomeça do zero **no próximo boot, todo
boot**.
**Evidência:** `app/editor_app.py:452-457` — o pré-aquecimento é incondicional, em todo boot:
```python
from app.images.fundo import aquecer, modelo_configurado
aquecedor = Trabalhador(lambda _st, m=modelo_configurado(): aquecer(m))
shell._trabalhos_globais.rodar(aquecedor)
```
`app/images/fundo.py:41-45` → `new_session(modelo)`, que **baixa se faltar**. O próprio
comentário do arquivo, em `fundo.py:23`, admite: *"a 1ª chamada de um modelo novo BAIXA o
arquivo (precisa de internet 1×)"*.
**Medição no disco do dono:** `~/.u2net/birefnet-general.onnx` = **972.666.916 bytes (928 MiB)**.
**Mecanismo:** a intenção do RG-02 era pré-carregar um modelo **já baixado** (poupar ~7 s).
A API do rembg não separa "carregar" de "baixar". Como o aquecimento é incondicional no boot,
a 1ª execução vira um download de 973 MB. E `aquecer()` engole tudo em `except Exception: pass`
(`fundo.py:53-56`, comentado como "silêncio ABENÇOADO"), então nem a falha aparece.
**Classe:** bug confirmado por leitura + medição | **reivindicação falsa da documentação**
**Coberto por teste?** NÃO — nenhum teste toca `fundo.aquecer` nem `new_session`.
**Invariante ferida:** I2.
> **Contradição documentada:** `docs/GUIA_RAPIDO.md:7-10` promete *"as duas únicas exceções…
> o **primeiro recorte de foto** baixa o modelo (~900 MB)"*, e `:64-67` ensina ao dono a
> receita para o PC sem internet: *"ou simplesmente não use recorte lá"*. **A receita não
> funciona** — abrir o app já dispara o download.

### CA-02 🔴 No programa instalado não existe registro de erro: `stdout` e `stderr` são `None`
**Sintoma potencial:** o dono clica em Exportar e não acontece nada. Nenhuma mensagem,
nenhuma janela, nenhum log. Ele não tem o que mandar para quem cuida do programa — e o
"Gerar diagnóstico para suporte" devolve um zip **sem um único traceback**.
**Evidência:** `autotabloide.spec:75` → `console=False,`; e a rede de todo trabalho pesado é
`app/qt/workers.py:44-45`:
```python
except Exception as exc:
    traceback.print_exc()
```
Prova empírica (pythonw + DETACHED_PROCESS, a condição exata do exe): `stdout=None`,
`stderr=None`, `print()` e `traceback.print_exc()` viram no-op. `grep sys.excepthook app/` = vazio.
**Mecanismo:** o único ponto do boot com rede é `_completar_seguro` (`editor_app.py:487-504`),
que mostra `QMessageBox` — e o comentário em `:488` já reconhece o problema *("com
console=False, uma exceção aqui era INVISÍVEL")*. O conserto foi aplicado em **um** lugar só.
Todo o resto confia em `print_exc()` / `logging` sem `basicConfig` (lastResort → stderr → None).
**Classe:** bug confirmado por leitura | **Coberto por teste?** NÃO | **Invariante:** I2.

### CA-03 🔴 A proteção contra pasta sem escrita só cobre `OSError` no `mkdir` — a falha real não é `OSError`
**Sintoma potencial:** se o dono descompactar o programa numa pasta que aceita criar subpastas
mas não aceita gravar arquivo (Documentos/Área de Trabalho com Proteção contra Ransomware
ligada, pasta de rede, OneDrive somente-leitura), **o exe abre e some**. Sem janela, sem
mensagem, sem log (CA-02). Ele conclui que "o programa não instala".
**Evidência:** `lancar_autotabloide.py:50-59` protege só o `criar_estrutura()`; e
`app/core/paths.py:61-66` **só faz `mkdir`**, nunca grava um arquivo de teste:
```python
def criar_estrutura(self) -> "SystemRoot":
    self.raiz.mkdir(parents=True, exist_ok=True)
    for nome in SUBPASTAS.values():
        (self.raiz / nome).mkdir(parents=True, exist_ok=True)
```
**Mecanismo:** quem falha de verdade é o SQLite ao criar `core.db`, e ele levanta
`sqlite3.OperationalError` — que **não herda de `OSError`**. O `except` do launcher não alcança.
E a exceção nasce na **fase 1** do boot (`_montar_shell`), enquanto a única rede
(`_completar_seguro`) protege a **fase 2**. Processo morre antes de qualquer janela.
**Classe:** bug confirmado por leitura | **Coberto por teste?** NÃO — `grep lancar_autotabloide app/tests/` = 0 arquivos | **Invariante:** I2.

### CA-04 🟠 Quem roda por `pythonw` (o jeito do dono HOJE) nunca recebe as fontes
**Evidência:** `lancar_autotabloide.py:39-40,71` — `_semear_raiz_nova` só roda dentro de
`if getattr(sys, "frozen", False)`. **Classe:** lacuna | **Teste:** NÃO | **Invariante:** I2.
Consequência: raiz nova fora do congelado nasce sem Quicksand/Roboto e o tabloide sai com
tipografia trocada. O pré-voo avisa "fonte não encontrada" (`servico.py:1495-1498`) — mas é
um aviso que se dispensa com um clique (P-09 do dossiê).

### CA-05 🟠 1º boot do exe num PC limpo: a Mesa nasce com uma grade branca sintética, sem explicação
**Evidência:** `autotabloide.spec:19-27` — o `datas` leva só a semente de fontes/logos; a arte
de fundo não entra em lugar nenhum. `app/editor_app.py:100-105` engole a falha do semeio com
`except Exception: pass` (*"sem a arte → segue sem o tabloide padrão"*), e
`_layout_padrao_do_banco` cai em `_grade_sintetica(), None`.
**Classe:** bug confirmado (silêncio) | **Teste:** NÃO | **Invariante:** I2.
> **Crédito onde é devido:** o *crash* que a frota F12 chamou de "exe meio-morto" **foi**
> consertado — o comentário em `editor_app.py:128-132` documenta o conserto e ele está lá.
> O que sobrou não é crash: é **silêncio**. O dono instala, abre, vê uma folha A4 em branco
> com uma grade 3×5 e nenhuma frase explicando por quê.

### CA-06 🟠 A fumaça do instalador prova que o processo está VIVO, não que o programa ABRIU
**Evidência:** `app/scripts/fumaca_instalador.py:31-34,44-50` — `Popen`, `sleep(12)`,
`proc.poll() is None`. **Classe:** teste que não mede o que promete | **Invariante:** I5.
O estado "meio-morto" (janela parada em *"Um instante — as telas…"*) passa verde.

### CA-07 🟠 2,7 GB de pasta e 1,58 GB de zip — os `excludes` do spec não alcançaram
**Evidência:** `saida_marco/medicoes.json` (medição do próprio builder): `"pasta_dist_mb": 2738.0`.
**Classe:** lógica porca | **Teste:** `empacotar.py` MEDE, mas nada FALHA por tamanho.

### CA-08 🟡 Dois assets que o app lê em disco ficaram FORA do `datas` — **provado contra o `dist/` construído**
**Evidência:** `app/qt/design/tema.py:22` (`_ASSETS = Path(__file__).parent / "assets"`,
usado em `:208` como `image: url(check.svg)` do `QCheckBox::indicator:checked`) e
`app/qt/design/som.py:14` (`parents[2]/"assets"/"sons"/"exportou.wav"`).
```
$ find dist/AutoTabloide -name "check.svg" -o -name "exportou.wav"
(vazio)
```
**Mecanismo:** o `datas` do spec só declara `app/assets/semente/*`. O PyInstaller não copia
arquivo não-Python sozinho. **Efeito real, calibrado honestamente:** o `:checked` também
pinta `background: PRIMARIA`, então a caixa marcada vira um quadrado sólido colorido **sem o
tique** — degrada, não some a informação. O som simplesmente nunca toca.
**Classe:** bug confirmado por artefato | **Teste:** NÃO | **Invariante:** I2 (menor).

### CA-09 🟡 A lista de fontes do sistema é cacheada para a sessão inteira, sem caminho de recarga
**Evidência:** `app/qt/fontes.py:64` `@lru_cache(maxsize=1)` em `_mapa_sistema()`;
`grep cache_clear app/` fora dos testes = **zero**. Instalar uma fonte com o app aberto ⇒ ela
nunca aparece até reiniciar, sem nenhuma dica. **Classe:** lógica porca | **Teste:** NÃO.

**Também nesta frente (🟡/🔵):** o programa manda "ver o console" em `editor_app.py:433-435`
e no exe não existe console (I2); quando o acervo cai no `LOCALAPPDATA` as três promessas do
guia (desinstalar/pendrive/Cofre) deixam de valer (I3); a semente copia `logo.png`/`logo.ico`
para a raiz e **nada no programa lê esses arquivos**; a única "prova" de 1ª execução congelada
no disco foi feita com o CWD errado (`dist/AutoTabloide_System_Root/layouts/Frente Template.png`
existe, 464.135 bytes — a arte da bancada vazou para dentro do artefato de entrega).

**Refutado por mim nesta frente (para o arquiteto não gastar tempo):** não há **nenhum**
`importlib` nem `__import__` em `app/` — o risco de `hiddenimports` faltando por import
computado é nulo. Os imports dentro de função (`ddgs`, `qrcode`, `fontTools`, `torch`) **são**
vistos pelo PyInstaller, que analisa o bytecode inteiro do módulo.

---

## §3 · FRENTE CB — arquivo corrompido, `.atproj`, `.attpl`, Cofre, somente-leitura

### CB-01 🔴 O snapshot do boot copia o banco JÁ corrompido e empurra os backups bons para fora da rotação
**Sintoma potencial:** o banco corrompe numa terça. O dono abre o app (não entende o aviso),
fecha, abre de novo. **A cada abertura nasce um backup do banco quebrado e o mais velho — que
era bom — é apagado.** Dez aberturas depois, não há de onde voltar: produtos, preços e
apelidos aprendidos morreram juntos.
**Evidência:** `app/editor_app.py:421-424` — o snapshot é a **primeira** coisa de `_completar()`:
```python
def _completar() -> None:
    # D-B2: snapshot automático a cada abertura (antes de qualquer edição)
    from app.core.cofre import snapshot_automatico
    snapshot_automatico()
```
`app/core/cofre.py:112-121` — a rotação apaga sem olhar a saúde (a única checagem é
`if not root.caminho_banco.exists()`):
```python
caminho = criar_snapshot(root, rotulo="auto")
manter = _rotacao_configurada(root)
autos = [s for s in listar_snapshots(root) if s["rotulo"] == "auto"]
for velho in autos[manter:]:
    Path(velho["caminho"]).unlink(missing_ok=True)
```
**Mecanismo:** a verificação R-138 (`PRAGMA integrity_check`) roda ~45 linhas **depois**
(`editor_app.py:465-470`), em worker, e só avisa — nunca protege a rotação. Pior: se a
corrupção for grave, `src.backup(dst)` levanta `sqlite3.DatabaseError` **dentro** de
`_completar()`, abortando migração de artes, purga, montagem das telas **e a própria
verificação de integridade** — o dono cai no "abriu pela metade" e a mensagem que diria
"restaure um backup" nunca chega a rodar.
**Classe:** bug confirmado por leitura | **Coberto por teste?** NÃO — `test_cofre.py:49-64`
prova a rotação com banco **sadio**; nenhum teste corrompe o banco antes do snapshot, e
nenhum roda a sequência real do boot | **Invariante:** I2.

### CB-02 🔴 O Cofre restaura o banco INTEIRO e o `.atpkg` mescla o acervo INTEIRO sem checar somente-leitura
**Sintoma potencial:** no PC da loja em modo somente-leitura (o que "aprova e imprime, não
edita"), qualquer pessoa abre Cofre › Restaurar snapshot e substitui o acervo inteiro por uma
cópia de semanas atrás — **preços velhos voltam ao balcão**. O modo trava editar o nome de UM
produto e libera trocar o banco todo.
**Evidência:** `app/core/cofre.py:157-168` e `app/core/portabilidade.py:544-550` — nenhuma
chamada a `exigir_escrita` em nenhum dos dois arquivos.
**Mecanismo:** `grep exigir_escrita app/` devolve 14 pontos (projetos, servico, biblioteca,
excel_acervo, calendario, atproj, migracao_antiga, enriquecer_banco). `cofre.py` e
`portabilidade.py` **não aparecem**. É o padrão do U-08 do dossiê — a porta lateral que
ninguém lembrou: a irmã pequena (`atproj.importar_atproj`, `atproj.py:92-93`) está guardada;
a irmã grande (`aplicar_importacao`) não. E o mapa de portas em `modo.py:9-16` **se declara
completo**.
**Classe:** bug confirmado por leitura | **Teste:** NÃO — `test_fase12_marco.py:769-814`
enumera as portas cobertas e nenhuma das duas está lá | **Invariante:** I2.

### CB-03 🟠 A lixeira apaga de vez em modo somente-leitura — inclusive sozinha, no boot
**Evidência:** `app/editor_app.py:429-431` (purga no boot, sem guarda) → `app/core/lixeira.py:133-137`.
**Classe:** bug confirmado | **Teste:** NÃO | **Invariante:** I2.

### CB-04 🟠 Recuperar de VERSÃO grava sem checar somente-leitura — a irmã pelo rascunho checa
**Evidência:** `app/core/recuperacao.py:188-196` — o caminho do RASCUNHO respeita o modo (e o
comentário admite que é intencional); o caminho da VERSÃO, no mesmo diálogo, não.
**Classe:** bug confirmado | **Teste:** NÃO | **Invariante:** I2.

### CB-05 🟠 Se a restauração do backup falhar, o dono não vê NADA
**Evidência:** `app/qt/telas/cofre.py:406-421` — a chamada mais perigosa da tela é a única
**sem `try/except`**. Momento pior possível: o acervo já quebrou e ele foi ao Cofre.
**Classe:** bug confirmado | **Teste:** NÃO (só o caminho feliz) | **Invariante:** I2.

### CB-06 🟠 A faxina de fotos órfãs joga na quarentena TODO o histórico de imagens
**Evidência:** `app/core/manutencao.py:132-142` — `rglob` que só perdoa três pastas por
convenção de nome; a pasta `versoes/` de cada produto (a preservação não-destrutiva do I1 da
F10) não está entre elas. O dono vê "3.480 foto(s) órfã(s)" e, se aceitar, perde o histórico.
**Classe:** bug confirmado | **Teste:** NÃO | **Invariante:** I1.

### CB-07 🟠 Arte de fundo que sumiu vira CAMINHO ABSOLUTO no projeto e depois página em branco
**Evidência:** `app/core/projetos.py:254-264` — quando o congelamento falha, o `or` devolve o
caminho absoluto da máquina. **Classe:** bug confirmado | **Teste:** NÃO | **Invariante:** I3.

### CB-08 🟠 `.atproj` não confere se os arquivos que o estado cita chegaram
**Evidência:** `app/core/atproj.py:58-65` — a exportação empacota o que houver, sem conferir.
No outro PC a prévia diz "31 itens, 2 páginas" e a peça sai furada. **Invariante:** I2.

### CB-09 🟠 O rascunho automático perde tudo se o último arquivo estiver truncado — e não conta
**Evidência:** `app/core/rascunho.py:108-117` — só o mais novo é tentado, e qualquer defeito
vira `None` mudo. O app travar **no meio do autosalvamento** é exatamente quando ele trava.
**Invariante:** I2.

### CB-10 🟠 O `uuid` que vem dentro do pacote vira caminho de disco sem validação
**Evidência:** `app/core/portabilidade.py:867-874` — o uuid vem do banco do pacote e é
concatenado direto na raiz de projetos. **Classe:** risco não provado (não consegui provar a
escrita fora da raiz; provei que o valor vem de fora sem validação) | **Invariante:** I3.

**Também nesta frente (🟡/🔵):** o `.attpl` "presente para outro mercado" leva os títulos de
seção que o dono digitou e não checa versão de schema (I3); o botão "Verificar atualização"
(`atualizacao.py`) **nunca funciona para o dono** — a única porta que define `url_atualizacao`
é um pacote importado, então é código morto na prática (e, respondendo à pergunta do briefing:
**ele não baixa nada sozinho, não fala com a internet no boot**); a migração do banco antigo
descarta peso e apelidos de produtos que já existem, sem contar (I2); "detalhes no console" e
"a falha fica REGISTRADA" não existem no app instalado (I2, cruza com CA-02); nenhum leitor de
arquivo externo limita tamanho e a prévia do `.atproj` lê o zip na thread da tela; o zip de
diagnóstico promete "sem dados sensíveis" e leva o caminho e o nome de usuário do dono.

**Sobre path traversal (a pergunta explícita do briefing):** varri todo `extractall`/`extract`.
`portabilidade.py:59` valida os membros do zip antes de extrair (`test_portabilidade.py:59`
cobre), e o `.atproj` idem. **Não achei traversal explorável.** O que achei foi o CB-10, que é
o mesmo problema por outra porta: um identificador vindo de fora virando caminho.

---

## §4 · FRENTE CC — `app/scripts/*`

**Primeiro, a correção de escala.** O briefing fala em "12 arquivos". São **47 módulos,
6.049 linhas** — 8% de todo o `app/`. Deles, **39 (5.311 linhas) não são citados por nenhum
teste**. E o grupo que realmente importa é minúsculo:

**Grupo (a) — alimentam botão da UI ou o produto (bug aqui é bug de produto): SÃO DOIS.**
- `enriquecer_banco.py` → `almoxarifado.py:856` ("Corrigir nomes (IA)") e `:878` ("Categorizar (IA)")
- `importar_tabela.py` → `servico.py:1584` (`parse_tabela_ean`, o import de ofertas da Mesa),
  `core/marco.py:64`, `editor_app.py:66`

**Grupo (b) — bancada descartável: os outros 45.**

### CC-01 🟠 "Corrigir nomes (IA)" joga a categoria calculada no lixo quando o nome já está certo
**Sintoma potencial:** o dono clica, o LM Studio trabalha minutos no acervo inteiro, e o aviso
final diz "3 corrigidos, 850 já certos". Ele acha que categorizou — e nada foi categorizado.
**Evidência:** `app/scripts/enriquecer_banco.py:54-62` — o `if` da linha 55 governa o dict
inteiro; a categoria computada só é gravada se o **nome** ou o **+18** também mudaram.
**Classe:** bug confirmado | **Teste:** NÃO | **Invariante:** I2.
*(Confirma o C-02 do dossiê — e é a mesma raiz do C-01: acervo velho fica "Outros" para sempre.)*

### CC-02 🟠 O botão que reescreve o acervo INTEIRO não pergunta nada, não dá para cancelar, não tem volta
**Evidência:** `app/qt/telas/almoxarifado.py:855-865` — `_corrigir_nomes` dispara direto, sem
`confirmar_destrutivo` (que existe e é usado no Excluir, `:938`). **Invariante:** I2.
*(Confirma o A-03 do dossiê, com a agravante do CC-01: o que ele destrói, destrói calado.)*

### CC-03 🟠 O marco da F12 compõe a peça por uma montagem PARALELA — não usa `dados_para_desenho`
**Sintoma potencial:** o PDF que vai para a sessão de aceitação do dono **não é a peça que o
programa produz**. Falta o selo +18, falta o multi-preço ("3 por R$10"), falta a observação.
**Evidência:** `app/scripts/selfcheck_marco_f12.py:145-147` monta `DadosProduto` na mão.
**Mecanismo:** é exatamente o bug que a frota F12 achou no Modo Pai (*"o Modo Pai compondo
DIFERENTE do export"*), consertado lá com "UMA montagem só" — e que **sobreviveu no script
que produz a prova de aceitação**. **Invariante:** I1 | **Teste:** NÃO.

### CC-04 🟠 `tabloide_real` baixa fotos da web e grava DENTRO da biblioteca viva do dono
**Evidência:** `app/scripts/tabloide_real.py:78-79` — `SystemRoot().biblioteca_imagens/"_auto"`.
Rodar o script despeja PNGs tratados no acervo real. **Classe:** lógica porca (perigo real).

### CC-05 🟠 Quatro scripts de bancada rodam contra a raiz VIVA por não setarem `AUTOTABLOIDE_ROOT`
**Evidência:** `fotografar_telas.py`, `gif_fase1.py`, `screenshots_design.py`,
`perfil_cpu_fase1.py` — ao contrário dos outros onze do mesmo diretório.
> **Correção de bancada (honestidade):** o enunciado original deste achado, escrito pelo meu
> agente, dizia que as galerias *"fotografam uma janela que o dono nunca vê"*, porque
> `montar_janela` seria um caminho de compatibilidade. **Meu cético refutou e ele estava
> certo:** `editor_app.py:327-333` chama exatamente `_montar_shell` + `_completar_janela`, as
> MESMAS funções do app real — a docstring fala do *momento* (o app monta a 2ª fase depois do
> `show()`), não de uma janela diferente. O achado foi reduzido ao que sobrevive à prova.

### CC-06 🟡 (seleção do resto, todos com linha)
- `enriquecer_banco.py:39,96-97` — o passe em lote para no produto 10.000 e **nunca conta
  quantos ficaram de fora** (I2).
- `selfcheck_marco.py:65-67` — apaga a pasta `saida_marco/` inteira, **inclusive o dossiê da
  aceitação e as medições do instalador** (I2).
- `selfcheck_marco_f12.py:140-143` — casa item↔célula com `zip` posicional e o que sobra
  **some sem ser nomeado** (I2); `:152-158` — o PDF do marco sai **sem o carimbo RASCUNHO**,
  e não há projeto aprovado por trás (a 10ª porta de exportação, somando às 9 do P-08).
- `selfcheck_bloco_d.py:4-5` vs `:49-50` — a docstring jura que o banco vivo "é só LIDO", e o
  script roda `create_all` + `ALTER TABLE` nele.
- `selfcheck_marco.py:199-201` — conta as pendências do pré-voo, **não as nomeia**, e nunca
  falha por elas (I2).
- `perfil_cpu_fase1.py:26-32` — mede um event loop artificialmente lento; o número sai **menor**
  que o real (a medição de desempenho favorece a si mesma).
- `editor_app.py:29-32` — **três cópias** de um parser de preço ingênuo, e **uma delas está no
  código de produção** (idêntica em `tabloide_real.py:45` e `cartaz_exemplo.py`). O
  `preco_decimal` blindado do P0.3 (que recusa "2x 5,00") está ao lado e não é usado (I2).
- `importar_tabela.py:54-65` — `importar_arquivo` cria produto no banco **sem passar pela
  guarda do somente-leitura** (mais uma porta para a lista do CB-02).
- `ai/conciliacao.py:255-259` — o passe em lote invalida o índice de significado de cada
  produto que renomeia, e a mensagem continua dizendo que está tudo certo (I2).

---

## §5 · FRENTE CD — histórico, undo/redo sob estresse

> Esta é a frente que explica a gravação. O dono aperta **Ctrl+Z nove vezes em quatro
> rajadas** (etapas 28, 48, 57) tentando desfazer um agrupamento acidental. O dossiê do
> arquiteto explica **por que ele agrupou sem querer** (E-01/E-02). Aqui está por que
> **o desfazer não trouxe nada de volta**.

**Antes dos achados, o inventário que o briefing pediu — e ele desmente a suspeita.**
`_registrar_hist` tem **32 pontos de chamada** em `canvas.py`. Conferi um a um: agrupar
(`:690`), desagrupar (`:705`), carimbar (`:1589`), duplicar (`:1954`), colar (`:1093`),
excluir região (`:1137`), reordenar camada (`:1193`), travar, propagar da mestra, adicionar
página, mover, redimensionar — **todos entram no histórico**. O `Historico` é bem desenhado:
snapshot de `{layout, mapa, overrides}` em disco, limite de 300, não duplica estado igual,
corta o futuro ao editar depois de desfazer. **A suspeita do briefing ("agrupar/carimbar não
entram") está errada, e é bom que esteja.** O problema é outro, e é pior.

### CD-01 🔴 Editar o nome/preço de um item na Mesa APAGA a pilha inteira de desfazer
**Sintoma potencial:** o dono ajusta uma célula no canvas (move, agrupa, exclui uma região),
depois corrige o preço de um item na estante — **e a partir daí Ctrl+Z responde "Nada para
desfazer"**. Todo o trabalho de canvas anterior vira irreversível. É exatamente o sintoma da
gravação.
**Evidência:** `app/qt/telas/mesa.py:2204-2208` (`_editar_item`) → `_aplicar_mapa()` →
`app/qt/telas/mesa.py:2344-2346` → `area.carregar(...)` → `app/qt/canvas.py:209-212`:
```python
self.ajustar()
from app.qt.historico import Historico
self._historico = Historico()          # ← pilha nova, do zero
self._historico.registrar(layout, self.mapa, self.overrides)
```
**Mecanismo:** `_aplicar_mapa` tem **10 chamadores** e **sete deles são edições banais de
item**: `_editar_item` (:2208), `_promocao_do_item` (:2232), `_observacao_do_item` (:2250),
`_fotos_do_item` (:1980), `_foto_lote_definida` (:2183), `_executar_composicao` (:2041),
`_executar_separacao` (:2060). De quebra, `carregar` também zera `_pagina_atual = 0`
(`canvas.py:193`) e chama `ajustar()` — corrigir um preço estando na página 2 joga o dono de
volta para a página 1 com o zoom reenquadrado.
**O código já sabia:** `mesa.py:443` traz o comentário
`# atualizar_dados preserva o histórico do canvas (carregar o zeraria)` — a lição foi aplicada
em `_excluir_item` e **nunca nos sete irmãos**.
**Classe:** bug confirmado por leitura | **Coberto por teste?** NÃO — nenhum teste edita um
item e depois desfaz; os testes de undo nunca passam por `_aplicar_mapa` antes | **Invariante:** I2.

### CD-02 🔴 Desfazer não volta para a página onde a coisa aconteceu
**Sintoma potencial:** no tabloide de 2 páginas (o Quintou real), o dono edita algo na página
2, navega para a 1, aperta Ctrl+Z: a página 2 **é** desfeita, mas ele não vê nada mudar. Ele
aperta de novo, e de novo — cada tecla desmonta em silêncio um passo do trabalho da outra página.
**Evidência:** `app/qt/historico.py:38-41` guarda só `{layout, mapa, overrides}` — a página
corrente **não faz parte do estado**. `app/qt/canvas.py:571-573` apenas **grampeia**:
```python
# D8.4: o undo pode restaurar um layout com MENOS páginas — clampa
self._pagina_atual = min(self._pagina_atual, len(layout.paginas) - 1)
```
**Classe:** bug confirmado | **Teste:** NÃO — `test_multipagina.py:143-148` desfaz e confere
`len(paginas)` e `mapa`, nunca `pagina_atual` | **Invariante:** I2.

### CD-03 🟠 O histórico vaza pastas temporárias para sempre — **40.462 já estão no disco do dono**
**Evidência:** `app/qt/historico.py:29` `self._dir = Path(tempfile.mkdtemp(prefix="atb_historico_"))`,
instanciado em `app/qt/canvas.py:210`. `Historico.limpar()` existe e **tem zero chamadores em
todo o app**; nada remove o diretório no fechamento.
**Medição na máquina do dono (agora):**
```
pastas atb_historico_* em %TEMP% ....... 40.462   (523 MB)
mais antiga ............................ 2026-07-17   (7 dias)
criadas hoje pelas MINHAS 4 passadas ... 651
de uma amostra de 3.000, com JSON dentro  2.999
```
**Honestidade de bancada:** a maior parte vem de passadas da suíte (≈163 por passada), não do
uso do dono — **as minhas 4 passadas de hoje contribuíram com 651**. Mas o vazamento é do
código de produção, e cada pasta guarda o **JSON do trabalho dele** espalhado pelo `%TEMP%`.
**Classe:** bug confirmado por medição | **Teste:** NÃO.

### CD-04 🟠 Cada TECLA digitada vira um estado de histórico — a pilha de 300 evapora
**Evidência:** `app/qt/painel_propriedades.py:82` `self.nome.textEdited.connect(...)` (por
tecla) e `:88`/`:157` (`valueChanged` das setinhas). Renomear uma camada para "Preço do arroz"
= 17 passos de desfazer. **Classe:** lógica porca | **Teste:** NÃO.
*(Casa com o X-01 do dossiê: o mesmo `notificar_edicao` que enche a pilha recompõe a página
inteira, síncrono, a cada tecla.)*

### CD-05 🟠 A Mesa muta o mapa slot→uid FORA do histórico
**Evidência:** `app/qt/telas/mesa.py:438-442` (`_excluir_item`) — `self._mapa.pop(sid)` sem
`registrar`. Um Ctrl+Z depois desfaz o gesto **anterior** do canvas e ressuscita vínculos
mortos. **Invariante:** I2 | **Teste:** NÃO (e o teste que existe mascara).

### CD-06 🟠 Abrir outro layout na Mesa mantém a estante e o mapa do anterior
**Evidência:** `app/qt/telas/mesa.py:666-678` (`carregar_layout` não zera `_itens`, `_mapa`,
`_overrides`) — e o histórico novo **congela essa mistura como estado zero**.
**Invariante:** I1 | **Teste:** NÃO.
*(Cruza com o U-15 do dossiê: "Novo tabloide" também não zera nada.)*

### CD-07 🟠 Abrir "Páginas e histórico" congela o app por dezenas de segundos
**Evidência:** `app/qt/telas/paginas_dialog.py:72-79` — `_recarregar_historico` roda no
`__init__` e compõe **uma miniatura por estado**. Medi `compor_pagina` em regime: **113 ms**.
Com 100–300 estados (o normal depois do CD-04), são **11 a 34 segundos** de tela branca.

### CD-08 🟠 No Ateliê, Ctrl+Z sem nada para desfazer é 100% mudo (a Mesa avisa; o editor não)
**Evidência:** `app/qt/design/barra_editor.py:57-61` — o botão "Desfazer" continua aceso e
clicável mesmo com a pilha no fundo. **Invariante:** I2.

**Também nesta frente (🟡):** arrastar uma guia custa **dois** Ctrl+Z e o passo do meio deixa a
guia sumida (`canvas.py:2222-2224`); desfazer lê do disco **sem proteção** — arquivo sumido faz
o Ctrl+Z falhar em silêncio (`historico.py:104-111`, I2); fundo gerado por IA troca a arte
**fora do histórico** e grava caminho absoluto (`editor.py:286-291`, I3); ligar/desligar seções
e renomear o título não entram no histórico (`mesa.py:624-629`); **a Fábrica não tem desfazer
nenhum** e o combo de modelo descarta o layout do Ateliê em silêncio (`fabrica.py:252-259`, I2);
o olho/cadeado do painel de camadas destrói o próprio botão de dentro do sinal dele
(`painel_camadas.py:150-155`).

> **Correção de bancada (o cético me pegou).** O meu agente afirmou que *"nenhum teste de undo
> confere CONTEÚDO — I5 não vale para o histórico"*. **Falso, e eu teria publicado errado.**
> `test_adversarial_vinculo.py:129-137` faz 5 edições, `for _ in range(5): v.desfazer()`,
> `for _ in range(2): v.refazer()` e então chama `_conferir` (`:85-101`), que é
> `compor_pagina` + `getpixel` por célula. `test_multipagina.py:75-92,150` faz o mesmo por
> página. **O histórico TEM verificação por pixel pós-undo.** O que ele não tem é verificação
> do que os achados CD-01/CD-02 quebram: ninguém testa desfazer **depois de editar um item**,
> nem confere **em que página** o canvas ficou.

**O teste-chave que o briefing pediu (§F-D.7), e o que ele quebraria hoje:** desfazer/refazer
20× conferindo byte-identidade **já existe em espírito** (o `_conferir` acima). O que falta é
o cenário: `MesaTela` → agrupar no canvas → `_editar_item(preço)` → `desfazer()` → conferir
que a peça voltou. Hoje ele fica vermelho na hora (CD-01), e é por isso que ele não existe.

---

## §6 · FRENTE CE — `rendering/secoes.py` e `imposicao.py`

### CE-01 🟠 O rótulo da seção é desenhado ANTES do conteúdo e a foto do produto o apaga
**Sintoma potencial:** o dono marca "Agrupar por categoria" para o Jornal do Mês, exporta, e
o nome da categoria ("Limpeza", "Bebidas") **simplesmente não aparece** — a foto pintou por cima.
**Evidência:** `app/rendering/compositor.py:621-638` desenha a seção e **só depois** o conteúdo.
**Medição em `compor_pagina` real:** **21 de 1.518 px** do rótulo sobrevivem quando a célula
tem foto (1,4%); sem foto, 1.155 sobrevivem.
**Classe:** bug confirmado por medição de pixel | **Invariante:** I2.
**Coberto por teste?** NÃO — e o motivo é o CE-02.

### CE-02 🟠 O cenário de teste da seção não tem região de IMAGEM — é o que mascara o CE-01
**Evidência:** `app/tests/test_onda5_visual.py:370-380` (`_pagina_2_categorias`, o helper de
**todos** os testes de estilo de seção) monta células **sem `TipoRegiao.IMAGEM`**.
**Classe:** mascaramento (lei do CLAUDE.md) | **Invariante:** I5.
*A bancada diz que as seções estão provadas por pixel. Na máquina real, com foto na célula, o
rótulo some. O verde não mede o caso do dono.* — e o dono quer seções justamente no Jornal do
Mês, que é todo de fotos.

### CE-03 🟠 "Dois por folha" habilitado em 3 dos 5 modelos — com a etiqueta gasta 4× mais papel
**Evidência:** `app/qt/telas/fabrica.py:268-269` — a guarda só olha o tamanho absoluto
(`<=148.5 × 210.5 mm`) — contra `app/rendering/cartaz.py:149-155`, cujo `PRESETS_CARTAZ`
**começa** por "Cartaz 10×15 — exemplo" (100×150), ou seja, o item **selecionado por padrão**
ao abrir a Fábrica (`fabrica.py:73`). **Medição: 8 etiquetas de 100×70 em 4 folhas A4 = 22%
de aproveitamento; a ferramenta certa (`impor_etiquetas`) faria em 1.**
> **Discordo do dossiê na severidade.** O F-05 está classificado 🟡 e descrito só para a
> etiqueta. São **três dos cinco modelos**, incluindo o **padrão**, e o custo é 4× papel.
> Isto é 🟠.

### CE-04 🟠 Cor de seção inválida na Configuração derruba a exportação inteira com `ValueError` cru
**Evidência:** `app/rendering/secoes.py:192-193` — a guarda confere a **forma** (`startswith("#")`),
não o conteúdo. Um `O` no lugar do zero, ou um `#1D4ED8;` colado com o ponto-e-vírgula, e o
próximo export morre. **Invariante:** I2 | **Teste:** NÃO.

### CE-05 🟡 Categoria com nome longo estoura a caixa e é cortada muda na borda da folha
**Evidência:** `app/rendering/secoes.py:294-305` não consulta a largura da seção nem a da folha.

### CE-06 🟡 Sem categoria em nada: uma caixa gigante "Outros" em volta da página inteira, com rótulo invisível
**Evidência:** `app/rendering/secoes.py:135` transforma ausência de categoria numa categoria real.
*Este é o C-01 do dossiê chegando à arte: acervo migrado, tudo "Outros", e a peça sai com um
retângulo em volta de tudo.*

### CE-07 🟡 Slot decorativo não-ocupável ("Fica a Dica") no meio da linha é engolido pela caixa
**Evidência:** `app/rendering/secoes.py:127-129` filtra os decorativos **antes** de formar os runs.

### CE-08 🟡 Célula fora da folha faz a exportação morrer com `ValueError` cru do Pillow
**Evidência:** `app/rendering/secoes.py:270-275` clampa cada lado independentemente, e nada
garante `x0 < x1`. **Classe:** risco não provado pela interface (provei a explosão dentro de
`desenhar_secoes` e provei que **não há clamp** em `canvas.py` — `nudge_selecao:1810-1813`,
`_commit_regiao_sem_hist:1826`, `_aplicar_posicoes:1992` gravam `x_mm` cru).

### CE-09 🟡 TODAS as marcas de corte do 2-em-1 caem na zona não-imprimível
**Evidência:** `app/rendering/imposicao.py:35-43` desenha tudo colado na aresta do papel.
Impressora jato/laser comum não imprime os ~5 mm de borda: **as marcas não saem**. **Invariante:** I5.

**Também nesta frente (🔵):** `impor_etiquetas` **não tem** a guarda "só no cartaz, nunca no
tabloide" que a própria docstring promete (`imposicao.py:96-97`); as marcas de corte da folha
parcial limitam as **linhas** mas não as **colunas** (`:126-137`), ao contrário do que o
comentário afirma; a folha da imposição não é escolhível e a impressão assume A4 paisagem por
hardcode (`:48,:94`); cada composição de página abre e fecha o banco **duas vezes** só para ler
4 preferências (`compositor.py:631-632`); a miniatura de projeto sem mapa **não desenha seções**
— o Dashboard mostra uma peça diferente da exportada (`projetos.py:103-107`, I1).

> **Discordo do dossiê (§9, "2-em-1 contido, com teste-guarda").** A guarda existe e cobre
> `impor_2em1` — mas o módulo tem **duas** portas. `impor_etiquetas` (`imposicao.py:93+`) faz a
> mesma promessa na docstring, tem **zero** teste-guarda, e seu único importador de produção é
> `servico.py:1850` — o módulo **compartilhado com a Mesa**, não a Fábrica. A afirmação
> "contido" é verdadeira para metade do módulo.

> **E sobre o N-05** (o app precisa desenhar as seções do Jornal, porque a arte não traz):
> concordo com o diagnóstico e discordo da conclusão implícita de que basta **ligar** o que
> existe. Ligar `secoes.py` no Jornal do Mês hoje entrega o CE-01: rótulo apagado pela foto em
> 98,6% dos pixels.

---

## §7 · FRENTE CF — teclado ponta a ponta e acessibilidade

### CF-01 🔴 A confirmação de exclusão do app inteiro abre com o botão DESTRUTIVO como padrão e com o foco
**Sintoma potencial:** o dono manda excluir 12 produtos, aparece "Não tem volta", ele aperta
**Enter** para tirar a caixa da frente (o reflexo de todo mundo) — e os 12 vão embora. Para
**cancelar** ele precisa do mouse ou de um Tab. O botão seguro é o único que não responde ao Enter.
**Evidência:** `app/qt/design/componentes.py:171-177` — o helper único, **13 pontos de chamada**:
```python
botao = caixa.addButton(verbo, QMessageBox.ButtonRole.DestructiveRole)
caixa.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
caixa.exec()
```
**Prova, reproduzida por mim em PySide6 real (offscreen):**
```
'Cancelar'                default=False  foco=False
'Excluir 12 produto(s)'   default=True   foco=True
defaultButton() = None
>>> ENTER resultou em confirmar_destrutivo() == True   (True = APAGOU)
```
**Mecanismo:** nenhum `setDefaultButton` é chamado. Sem default explícito, o `QMessageBox`
promove o **primeiro botão adicionado** — que é justamente o destrutivo (linha 175, antes do
Cancelar da 176). O app **já sabe fazer certo**: `mesa.py:1146` é o único lugar do código que
chama `setDefaultButton(...)`, e escolhe a opção segura.
**Classe:** bug confirmado por reprodução | **Coberto por teste?** NÃO — os testes
*substituem o helper inteiro* por monkeypatch (`test_onda2_estabilidade.py:410`) ou mockam
`QMessageBox.exec` (`test_fase3_config.py:337-339`). Trocar o botão padrão não deixa nenhum
dos 851 testes vermelho | **Invariante:** nenhuma (é dano direto).
> **Nota para o arquiteto:** o §11 do dossiê (linha 796) cita `confirmar_destrutivo` como o
> **bom padrão** que falta em outros lugares e pede que ele se espalhe. Espalhá-lo **como
> está** espalha o defeito.

### CF-02 🟠 Ctrl+K está MORTO na Mesa — e há um teste verde com o nome do atalho
**Sintoma potencial:** na tela onde o dono passa o dia, Ctrl+K não faz absolutamente nada. Em
todas as outras, abre a busca. Ele conclui "esse atalho não funciona".
**Evidência:** dois donos da mesma tecla na mesma janela —
`app/editor_app.py:322-323` `criar_atalho("geral.busca", shell, ..., WindowShortcut)` e
`app/qt/telas/mesa.py:697-698` `QShortcut(QKeySequence("Ctrl+K"), self)`. O Qt declara
**ambiguidade** e não dispara nenhum.
**Coberto por teste?** Existe `test_fase2_busca.py:54-71` chamado
`test_ctrl_k_abre_em_duas_telas` — **verde** — e ele nunca aperta a tecla:
```python
shell.ir_para(tela)
shell._paleta_busca.abrir()        # ← chama o método, não o atalho
assert shell._paleta_busca.isVisible()
```
**Classe:** bug confirmado + mascaramento. **É a lei nova desta auditoria em estado puro:
chamar o método interno não prova que o atalho funciona.**
> **Correção ao U-08 do dossiê.** Não refuto que o Ctrl+K fure o Modo Pai — furo confirmado.
> Corrijo a **explicação**: ele funciona no Modo Pai justamente porque ali a Mesa está
> escondida e só o dono do shell casa o contexto. Com a Mesa visível, os dois casam e **nenhum
> dispara**. A conclusão prática inverte-se: não é "um atalho a mais que escapou", é
> "o mesmo registro duplicado mata o atalho onde ele é mais útil e o deixa vivo onde não devia".

### CF-03 🟠 36 diálogos, ZERO com botão padrão declarado, apenas 1 com foco inicial
**Evidência:** varredura de todas as 36 classes `QDialog` de `app/qt/`: `setDefault(` = **0**
ocorrências; `setFocus()` em diálogo = **1**. O Enter é decidido pela ordem em que os widgets
foram criados. **Classe:** lacuna | **Teste:** NÃO (0 testes sobre foco/default).

### CF-04 🟠 "Importar do banco": Enter no campo de busca clica CANCELAR e joga a cesta fora
**Evidência:** `app/qt/telas/importar_banco_dialog.py:44-46,58-64` — o Cancelar nasce **antes**
do Importar. O dono digita "Coca", aperta Enter (o gesto que todo campo de busca ensina), e
perde a cesta que montou item por item — **o recurso que ele mesmo pediu**. **Invariante:** I2.

### CF-05 🟠 O véu de "ocupado" bloqueia o mouse mas NÃO bloqueia o teclado
**Evidência:** `app/qt/design/carregando.py:144-152,210-212` — nada de modal, nada de
`setEnabled`, nada de `grab`. Enquanto a tela mostra "Excluindo 12 produto(s)…", o botão
embaixo do véu continua com o foco e obedecendo ao Enter: dá para disparar a mesma operação
destrutiva duas vezes. **Teste:** NÃO.

### CF-06 🟠 Nenhum teste da suíte aperta uma tecla — o caminho do `QShortcut` nunca é exercitado
É a razão de CF-01, CF-02 e CF-04 conviverem com 851 verdes. **Invariante:** I5.

**Também nesta frente (🟡):** na Conciliação — o diálogo mais usado — o botão padrão cai num
botão **escondido** ("Parar IA") e o Enter não faz nada (`conciliacao_dialog.py:138-151`);
Esc na Conciliação **joga fora a importação inteira** sem perguntar (`:631-638`, I2); os menus
de contexto abertos pela tecla Menu/Shift+F10 agem no item do **centro da lista**, não no
selecionado (`mesa.py:1436-1443`, I1); **14 das 17 telas não têm atalho nenhum** — a Fábrica,
metade do produto, não tem Ctrl+S nem Ctrl+E; **oito** atalhos existem no código e não no
catálogo (invisíveis nas Configurações e na folha de cola — a lista completa está no dossiê do
agente); "Importar do banco" não tem caminho de teclado para montar a cesta;
**acessibilidade é zero absoluto** — nenhum `setAccessibleName`, nenhum `setBuddy`, 18 botões
só-ícone sem nome acessível.

> **Refuto duas suspeitas naturais desta frente** (testadas em PySide6, não deduzidas):
> as teclas soltas N/A/R da Conciliação **não** roubam a edição inline — o Qt manda
> `ShortcutOverride` ao widget em foco e o `QLineEdit` editável fica com a tecla (provado:
> campo editável ⇒ `atalho: []`, `texto: 'N'`; campo readOnly ⇒ `atalho: ['atalho-N']`).
> Pelo mesmo motivo, o Ctrl+V de tabela da Mesa (`mesa.py:700-701`) **não** rouba o colar do
> campo de busca. Registro para ninguém "consertar" o que não está quebrado.

---

## §8 · FRENTE CG — dois monitores, DPI fracionário, 3440×1440

### CG-01 🟠 A janela nasce MAIOR que a tela inteira em qualquer Windows a 125% ou 150%
**Sintoma potencial:** o dono (ou o pai, no PC da loja) abre pela primeira vez e a janela já
nasce estourando: o rodapé "Salvo / 210 × 297 mm / Zoom 100%" fica embaixo da barra de tarefas.
Ele não pediu nada — abriu e já está torto.
**Evidência:** `app/editor_app.py:402` `shell.resize(1440, 900)`, sem consultar a tela.
**Mecanismo:** a 125%, um monitor 1920×1080 vira um desktop **lógico** de 1536×864 (≈824 úteis
de altura); a 150%, 1280×720 (≈680 úteis). O Qt 6.10 usa arredondamento `PassThrough` por
padrão (verificado). 900 > 824 e 1440 > 1280. **Classe:** bug confirmado | **Teste:** NÃO —
`grep '1440' app/tests/` = 0.

### CG-02 🟠 A geometria lembrada é conferida por "encosta em alguma tela", nunca CLAMPADA
**Evidência:** `app/qt/design/shell.py:307-318`. O dono trabalha no 3440×1440, no dia seguinte
abre no notebook: a janela volta com o tamanho do monitor grande, metade fora da tela, e ele
não alcança a borda para arrastar de volta. **Classe:** bug confirmado | **Teste:** NÃO.

### CG-03 🟠 Modo Pai: as letras "gigantes" ENCOLHEM quando o dono aumenta a escala da interface
**Sintoma potencial:** o pai reclama que não enxerga. O dono vai em Configurações › Escala da
interface e põe 150% — que promete "aumenta a letra e os controles… bom para vista cansada" —
e o Modo Pai fica **menor** em proporção.
**Evidência:** `app/qt/telas/modo_pai.py:35-36,78,82,86` — `_QSS_GIGANTE` fixa `font-size: 17px`
(px absoluto), enquanto o resto da UI escala em pt. **Classe:** bug confirmado | **Teste:** NÃO.

### CG-04 🟠 A política anti-corte roda na produção e NUNCA nos testes
**Evidência:** `app/qt/design/polimento.py:10` — a docstring **admite** que `instalar_polimento`
fica fora da bancada. Os testes RG-53/54 medem uma árvore de widgets mais magra que o app real.
**Invariante:** I5. *(É o T-02 do dossiê aplicado ao layout: o placar "cabe a 720p" mede uma
janela que não é a do dono.)*

### CG-05 🟠 Os testes de tamanho medem só LARGURA, e a bancada não vê DPI nem 2º monitor
**Evidência:** `conftest.py:9` fixa `offscreen`. A prova do RG-53 cobre a largura de duas
barras. **Nada nos 851 verdes garante que a JANELA cabe em 720p.** **Invariante:** I5.

**Também nesta frente (🟡):** toda prévia composta em Pillow é mostrada com
`devicePixelRatio` 1 — **borrada** em tela 125%/150% (`canvas.py:34-38`); o splash em DPR 1 e
ícones com DPR 2 chumbado, em cache **sem o DPR na chave** (`splash.py:24-25`); altura de lista
com 26 px por linha chumbado (`dashboard.py:1105-1107`); a 3440×1440 o Início **trava em 3
colunas** e os cartões viram tarjas de 1100×150 (`dashboard.py:741-751`) e as Configurações
esticam o formulário até o infinito, sem teto de largura de coluna de texto
(`configuracoes.py:654,670-673`); nenhum dos 20 diálogos consulta a tela e dois estouram a
altura útil de um 1080p a 150%; `setFixedWidth` briga com a própria política anti-corte da casa
(`barra_editor.py:198-203`); e **"Zoom 100%" mente** em qualquer tela com escala do Windows
(`canvas.py:1722-1726`).

> **Refuto o U-14 do dossiê.** `conciliacao_dialog.py:170` `resize(1200, 760)` **nunca chega a
> valer**: os **dois** chamadores do diálogo fazem `showMaximized()` antes do `exec()`
> exatamente no ramo em que o 1200×760 é aplicado (`conciliacao_dialog.py:171`
> `self._tela_cheia = True   # o chamador maximiza no exec()`; `mesa.py:1055-1057` e o
> equivalente na Fábrica). O risco descrito ("os botões Concluir/Cancelar podem ficar fora da
> tela em 1366×768") não se materializa.
>
> **E refuto uma hipótese natural desta frente, para ninguém gastar tempo:** não há bug de
> coordenada global-vs-local em popup nenhum, e o app **não** precisa de
> `AA_EnableHighDpiScaling`. A paleta, o toast e o tutorial usam `move()` em widgets **filhos**
> (coordenada de pai, que é o correto); o dropdown da busca do Início é top-level
> (`Qt.WindowType.ToolTip`) e por isso o `mapToGlobal` está certo; `polimento.py:40-41` usa
> `obj.screen()`, não a primária.

---

## §9 · FRENTE CH — código morto e dívida no repositório

### CH-01 🟠 A prova de "851 verdes, zero skips" não se reproduz do repositório
**Evidência:** `.gitignore:78-82`:
```
arte/
*.jpeg
Frente*.png
Verso*.png
test_ean.xlsx
```
`git ls-files arte` = **0**; `git ls-files AutoTabloide_System_Root` = **0**.
Onze testes exigem essa arte; **três a usam sem guarda de skip** (`test_grade.py:19-24`,
2 testes; `test_fase5_editor.py:655-656`).
**Mecanismo + medição minha:** de outra pasta (o proxy do clone limpo) → **10 vermelhos,
8 pulados** (§1.5). **Classe:** reivindicação do CLAUDE.md que não se reproduz | **Invariante:** I5.
> **Refinamento importante ao T-08 do dossiê.** O arquiteto atribui o skip silencioso ao **CWD
> relativo**. A causa é maior: rodar da pasta certa **também** silencia — para qualquer pessoa
> que não seja o Otaviano — porque o arquivo **não existe em nenhum clone**. Consertar só o
> CWD (caminho absoluto a partir de `__file__`) **não resolve nada**.

### CH-02 🟠 Sem lockfile: o ambiente não é reproduzível
**Evidência:** `poetry.lock`, `uv.lock`, `requirements*.txt` — **os três ausentes**;
`git log --diff-filter=D` mostra o `poetry.lock` **apagado** no commit de limpeza. Se o dono
formatar o PC, não existe receita que devolva o ambiente que hoje dá 851 verdes.

### CH-03 🟡 `src/`, `alembic/` e `tests/` são três pastas-fantasma
**Evidência:** `find src -type f | wc -l` → **356**; `find src -name "*.py" | wc -l` → **0**.
Idem `alembic/` (só `__pycache__/env.cpython-312.pyc`) e `tests/` da raiz.
**Respondendo à pergunta técnica do briefing:** bytecode em `__pycache__/` **não é importável**
sem o fonte (isso exigiria o `.pyc` na própria pasta, o modo *sourceless* legado). Varri
`find . -name "*.pyc" -not -path "*__pycache__*"` → **vazio**. **É inerte: dívida e confusão,
não risco de execução.** Nenhum módulo de `app/` importa de `src/`, e o `.spec` não os empacota.
**Confirma D-11 do dossiê** (alembic morto) por comando meu.

### CH-04 🟡 O README manda rodar `python -m app.main`, uma porta congelada em 10/07
**Evidência:** `app/main.py:51-58` — roda de verdade (todos os imports resolvem), mas abre uma
janela antiga. Duas portas de entrada divergentes documentadas ao mesmo tempo.

### CH-05 🟡 Cinco dependências declaradas que o app nunca importou
**Evidência:** `pyproject.toml` — declaradas com **zero** import em todo `app/`. Peso morto no
ambiente e no instalador (cruza com CA-07: 2,7 GB).
**Confirma D-14 do dossiê:** `sqlite-vec` é anunciado no CLAUDE.md e no pyproject e **nunca é
importado** — e eu acrescento que ele **nem está instalado** nesta máquina (o índice de
significado roda com cosseno em numpy puro, e funciona).

### CH-06 🟡 Dois hard-deletes vivos sem chamador, e seis funções públicas nunca chamadas
**Evidência:** `app/core/repositories.py:179-183` (zero chamadores no repositório inteiro);
`persistencia.py:214-218` (importado em `atelie.py:46`, nunca usado). **Confirma D-07.**
Novas: `app/qt/telas/eventos.py:190-197` e mais cinco — **uma delas é um recurso do dono que
nunca foi ligado**. **Invariante:** I2 (contradizem "toda exclusão vira soft-delete").

### CH-07 🔵 Quatro arquivos entre 2.250 e 2.473 linhas; `servico.py` é um god-module com 96 funções de topo
**Evidência:** os 10 maiores `.py` de `app/` por `wc -l`. É a fronteira natural de quebra a
discutir no caderno de visão, não aqui.

**Também nesta frente:** `app/qt/barra.py` é código morto **identificado na Fase 1**, polido
por engano depois, e ainda no disco — e **o dossiê o cita como jargão que o dono lê na tela**
(U-11, `barra.py:58`), quando na verdade `BarraFerramentas` não é importada por ninguém: o
editor usa `app/qt/design/barra_editor.py`. **Refuto essa linha do U-11**; as outras do U-11
(painel de propriedades, painel de camadas, combos com enum cru, "override") continuam válidas.
Mais: `.gitignore` por nome-de-rodada (uma linha nova por bancada, escrita **depois** do
estrago — e a rodada F13 já vazou); **4,3 GB de `dist/`** e mais três depósitos de entulho na
pasta do dono; e a mensagem do commit de limpeza afirma que `test_ean.xlsx` foi poupado
"porque um teste vivo usa" — **nenhum teste o usa**.

---

## §9b · Dois achados que nasceram na frente de VISÃO (e viraram bug)

Procurando **oportunidade** no que o banco já guarda, a frente de visão tropeçou em dois bugs
reais. Conferi os dois pessoalmente na fonte. Ficam aqui, não no caderno de ideias.

### CI-01 🟠 A conciliação não enxerga a lixeira — produto excluído volta VERDE, calado
**Sintoma potencial:** o dono exclui um produto (soft-delete, lixeira de 30 dias). Na
importação seguinte, o item **casa VERDE** com esse produto morto e entra na estante com a
foto e o preço dele. Não há aviso: verde significa "já existe, está tudo certo".
**Evidência:** `app/ai/conciliacao.py:191-193` — o corpus varre **todos** os produtos:
```python
for pid, nome in self.session.execute(
    select(Produto.id, Produto.nome_sanitizado)
).all():
```
O filtro certo está escrito **duas vezes** no projeto, ao lado: `repositories.py:74`
(`.where(Produto.excluido_em.is_(None))    # F2: lixeira esconde`) e
`excel_acervo.py:418-419`.
**Mecanismo:** `_corpus` e `_indice` do `Conciliador` não filtram `excluido_em`. A lixeira
esconde o produto de **toda tela**, menos daquela que decide o semáforo.
**Classe:** bug confirmado por leitura | **Coberto por teste?** NÃO | **Invariante:** I2
(e I1 na prática: o vínculo aponta para um uid que o dono já mandou embora).

### CI-02 🟠 A categoria que o dono corrigiu no Excel é apagada pelo próximo passe de IA
**Sintoma potencial:** ele exporta o acervo para o Excel, corrige 300 categorias na mão
(~25 min — é o **único** caminho de lote que existe, A-02), reimporta, e depois clica em
"Categorizar (IA)". O trabalho todo é sobrescrito, sem aviso.
**Evidência:** `app/core/excel_acervo.py:421-432` grava a categoria e **não marca a origem**:
```python
def _aplicar_campos(prod: Produto, plano: dict) -> None:
    prod.categoria_id = _categoria_id(plano["categoria"])
    prod.preco_atual = plano["preco"]
    ...                                   # nunca escreve categoria_origem
```
**A proteção existe e funciona** — `app/scripts/enriquecer_banco.py:59`:
```python
if p.categoria_origem != "humano" and enr.categoria:
```
e a regra certa está escrita em `app/qt/telas/servico.py:231`:
`campos["categoria_origem"] = "humano" if campos["categoria"] else None`.
**Mecanismo:** a ponte Excel é o único caminho de escrita de categoria que **não arma o
escudo**. O passe de IA então se considera livre para reescrever.
**Classe:** bug confirmado por leitura | **Coberto por teste?** NÃO | **Invariante:** I2.
*Combina com o CC-01: o mesmo botão que descarta categorias novas também apaga as que o dono
digitou à mão.*

### CI-03 🔴 O juiz IA pinta VERDE com qualquer confiança — inclusive 0,05
**Sintoma potencial:** a IA responde *"é o candidato 2, confiança 5%"* e o item entra **VERDE**
na estante. Verde, na lei deste projeto, significa "existe, está certo, não precisa conferir" —
então o dono passa direto. O produto errado vai para a peça com a foto e o preço errados.
**Evidência:** `app/ai/conciliacao.py:377-386` — a confiança é lida e **nunca comparada a nada**:
```python
conf = float(dados.get("confianca", 0.0))
...
if isinstance(indice, int) and 0 <= indice < len(candidatos):
    escolhido = candidatos[indice]
    return Veredito(nome_bruto, Semaforo.VERDE, escolhido.produto, candidatos,
                    conf, "juiz IA: confirmou candidato", "juiz")
```
**Mecanismo:** `LimiaresConciliacao` (`:97-101`) tem `verde=88.0` e `amarelo=62.0`, e
`limiares_de_config` (`:104-122`) até se protege de limiar quebrado — mas esses limiares valem
para o **score do fuzzy**, não para a confiança do **juiz**. O caminho do juiz não tem limiar
nenhum: qualquer índice válido vira verde.
**Viola decisão travada (F9):** *"a IA NUNCA inventa… ambíguo vira amarelo"*. Um match de
confiança baixa é a definição de ambíguo, e está sendo pintado de verde.
**Classe:** bug confirmado por leitura | **Coberto por teste?** NÃO | **Invariante:** I2.

### CI-04 🟠 A revisora pede os NOMES ao modelo de visão e joga fora — preço trocado entre dois itens passa limpo
**Sintoma potencial:** o preço do arroz aparece na célula do feijão e o do feijão na do arroz.
O dono clica em "Revisar" (a rede de segurança por visão), e ela diz que está tudo bem.
**Evidência:** o prompt **pede** os nomes (`app/ai/revisora.py:23-28`):
```python
"Olhe a imagem e liste, em JSON, os PREÇOS e os NOMES de produto que você "
'consegue LER claramente. Responda só o JSON: {"precos": [...], "nomes": [...]}'
```
E a comparação lê **só os preços** (`:118-129`), num **conjunto** sem dono:
```python
esperados = {_fmt_preco(d.preco_por) for d in dados_por_slot.values() ...}
lidos = [_norm_preco(p) for p in obj.get("precos", []) if str(p).strip()]
for p in lidos:
    if p and esperados and p not in esperados:
```
**Mecanismo:** dois preços trocados **entre si** continuam ambos dentro de `esperados` — a
troca é invisível para uma comparação de conjunto. Os `nomes`, que permitiriam parear
nome↔preço e pegar exatamente esse caso, são pedidos ao modelo, recebidos, e descartados na
linha seguinte.
**Classe:** lacuna (o dado é colhido e não usado) | **Teste:** NÃO | **Invariante:** nenhuma
(a revisora é aviso, nunca veto — F9 — então não bloqueia nada; o dano é a **falsa segurança**).

### CI-05 🔴 VIOLA DECISÃO TRAVADA (F10) · A foto ORIGINAL é apagada em silêncio na 11ª troca
**Sintoma potencial:** o dono troca a foto de um produto ao longo dos meses. Na 11ª troca, a
**foto original — a única boa, a que ele escolheu a dedo — é apagada do disco**. Sem aviso,
sem lixeira, sem volta.
**Evidência:** `app/images/biblioteca.py:139-142`:
```python
def _podar(self, produto_id: int) -> None:
    versoes = self.listar_versoes(produto_id)
    for v in versoes[: max(0, len(versoes) - self.max_versoes)]:
        v.unlink()
```
`listar_versoes` (`:82-86`) devolve `sorted(...)` sobre nomes com prefixo de timestamp — ou
seja, **da mais antiga para a mais nova**. A fatia `[: len - max_versoes]` pega justamente as
**mais antigas**, e a mais antiga de todas é a original. `max_versoes` tem default **10**
(`:47`).
**Viola decisão travada (F10, no CLAUDE.md):** *"Curadoria **não-destrutiva** (original sempre
preservada, versão nova, I1)"*.
**Classe:** bug confirmado por leitura | **Coberto por teste?** NÃO | **Invariante:** I1 + I2.

### CI-06 🟠 O recorte transparente vira um RETÂNGULO PRETO no cartaz que precisa de ampliação
**Sintoma potencial:** o cartaz de gôndola grande sai com o produto dentro de uma **caixa preta**
— o fundo que o rembg tirou volta, sólido, preto. Ele descobre no papel, depois de imprimir.
**Evidência:** `app/images/upscale.py:105-107`:
```python
def ampliar_sob_demanda(imagem, upscaler, alvo_px) -> Image.Image:
    """Export (ex.: cartaz A2): amplia sob demanda até ~alvo_px no maior lado; NÃO guarda."""
    original = Image.open(imagem).convert("RGB")
```
`.convert("RGB")` **descarta o canal alfa**; o transparente é achatado contra preto. O único
chamador é `app/qt/telas/servico.py:432` (`upscale_para_cartaz`) — exatamente a rota do cartaz
grande. Ironia: a decisão travada do R-100 fez o WebP lossless justamente para **preservar o
alfa do packshot**; ele sobrevive ao arquivo e morre na ampliação.
**Classe:** bug confirmado por leitura | **Coberto por teste?** NÃO | **Invariante:** I2.

---

## §10 · O QUE EU CONFIRMEI DO DOSSIÊ

Reabri a fonte e conferi pessoalmente (não por agente) as alegações do arquiteto em que um
erro dele custaria caro. **Todas confirmadas:**

| # | Alegação do dossiê | Como eu confirmei |
|---|---|---|
| **T-01/02/03** | a bancada não mede o gesto | números meus, §1.2: `QTest`=0, `.trigger()`=0, `sendEvent`=1, `dropEvent`=0, `instalar_vida`=0, `confirmar_pre_voo` monkeypatchado em 6 pontos. **E dois números novos: `contextMenuEvent`=0 e `QSignalSpy`=0** |
| **V-01/V-02** | `_veus` vaza; `destroyed` só tira do dicionário | **provado por EXECUÇÃO** (§1.6): em ordem invertida, `animacoes_ativas()` devolve 2 em vez de 0 — estado global sobrevivendo entre arquivos de teste |
| **E-01** | criação auto-seleciona ⇒ a próxima região herda o slot | `canvas.py:1396-1397` lido; **e é a única das 6 mutações que algum teste pegou** |
| **R-02** | Subir/Descer invertidos | `painel_camadas.py:66-72` (tooltip "Trazer para a frente" → `_mover(-1)`) contra `compositor.py:654-655` (`for reg in slot.regioes: _desenhar_regiao(...)` — quem vem depois fica na frente). **Confirmado, e quebrá-lo não acende nenhum teste** |
| **E-08** | rotação desliga o resize e não há alternativa | `itens.py:438` lido; varredura de `painel_propriedades.py`: **nenhum campo Largura/Altura** (23 `addRow`, a única ocorrência de "altura" é um comentário sobre animação de seção, `:278`) |
| **R-01** | o Y do texto é uma linha incondicional | `compositor.py:312` lido; **e a mutação que joga todo texto para o topo passa por 851 testes** |
| **F-01** | etiqueta em lote monta `DadosProduto` sem `mais18` | `servico.py:1858-1863` lido; **e tirar o PREÇO da mesma linha também não acende nada** |
| **C-01** | categoria só é lida para produto conhecido | `servico.py:1635-1636` lido |
| **A-01** | o filtro "Sem imagem" mente em escala | `almoxarifado.py:80-91` lido: o `offset` usa `len(self._linhas)` (contagem **pós-filtro**) e o `if len(pagina) < _PAGINA` roda **depois** do filtro — declara fim de lista na 1ª página quase sempre. Confirmado nos dois defeitos |
| **D-11** | alembic morto | `find alembic -type f` → só `__pycache__/env.cpython-312.pyc` |
| **D-14** | sqlite-vec anunciado e não usado | zero imports **e nem instalado** nesta máquina |
| **C-02 / A-03** | "Corrigir nomes (IA)" descarta categoria; ações em massa não confirmam | CC-01 e CC-02, confirmados |
| **F-05** | "Dois por folha" habilitado para a etiqueta | CE-03 — confirmado e **agravado** (3 dos 5 modelos, inclusive o padrão; 22% de aproveitamento) |
| **§9 "boot já resolvido"** | o boot não é o gargalo | medi: 114 ms de import até a casca. **Confirmado** |
| **§9 "MP4 opcional", "cartaz em mm", "% blindado"** | verificados e sãos | não reabri — aceito, são medições dele com teste ao lado |

E confirmo, com medição própria, o **X-02**: rembg numa foto real de 1000×1000 do acervo do
dono → **17,12 s** na 1ª chamada, **9,08 s / 7,95 s** em regime. 30 itens ⇒ **≈4 min 15 s**
só de recorte, um por vez, com a tela bloqueada (I-01).

---

## §11 · O QUE EU REFUTO DO DOSSIÊ

Discordância documentada vale mais que concordância — e cada uma abaixo tem arquivo:linha.

1. **U-14 — REFUTADO.** *"O único diálogo que estoura 768 px é o mais usado"* —
   `conciliacao_dialog.py:170` `resize(1200, 760)` **nunca vale nesse ramo**: os dois
   chamadores fazem `showMaximized()` antes do `exec()` exatamente quando `_tela_cheia` é
   `True`, que é o mesmo ramo em que o 1200×760 é aplicado (`conciliacao_dialog.py:171`;
   `mesa.py:1055-1057` e o irmão na Fábrica). Os botões do rodapé não correm risco de sair da
   tela. *(O C-10 continua válido: o diálogo não lembra nada entre aberturas.)*

2. **U-11, a linha do `barra.py` — REFUTADO.** O dossiê lista o tooltip
   *"Adicionar região IMAGEM/PRECO"* (`barra.py:58`) entre os jargões que **o dono lê na tela**.
   `BarraFerramentas` **não é importada por ninguém** — é código morto identificado desde a
   Fase 1 (`docs/FASE_1.md:393`), e o editor usa `app/qt/design/barra_editor.py`. Esse tooltip
   nunca chega à tela. *(As outras linhas do U-11 continuam válidas.)*

3. **T-08 — CONFIRMADO, mas a CAUSA está incompleta e leva ao conserto errado.** O dossiê
   atribui o skip silencioso ao CWD. Rodar da pasta certa **também** silencia — para todo mundo
   que não seja o Otaviano — porque `arte/` está no `.gitignore` (`:78-82`) e
   `git ls-files arte` = 0. Trocar por caminho absoluto a partir de `__file__` **não resolve**.
   E o problema é maior que "3 skipif": são **10 vermelhos + 8 pulados**, mais **205 testes que
   degradam em silêncio** para a fonte embutida do Pillow (§1.5).

4. **U-08 — CONFIRMADO com a explicação INVERTIDA.** O Ctrl+K fura o Modo Pai, sim. Mas não
   porque "o atalho de janela continua ativo em toda parte": ele funciona lá porque a Mesa
   está escondida e só um dono casa o contexto. **Com a Mesa visível, os dois donos casam, o Qt
   declara ambiguidade e nenhum dispara — Ctrl+K está MORTO na Mesa** (CF-02). A conclusão
   prática se inverte: o conserto não é "restringir o atalho no Modo Pai", é "ter um dono só".

5. **§9, "o 2-em-1 está contido, com teste-guarda" — VERDADEIRO PELA METADE.** A guarda cobre
   `impor_2em1`. `impor_etiquetas` (`imposicao.py:93+`) faz a **mesma** promessa na docstring
   (`:96-97`), tem **zero** teste-guarda, e seu único importador de produção é `servico.py:1850`
   — o módulo compartilhado com a Mesa (CE, 🔵).

6. **F-05 — severidade contestada para CIMA:** 🟡 → 🟠 (CE-03).

7. **N-05 — diagnóstico correto, conclusão incompleta.** "O app precisa desenhar as seções do
   Jornal" está certo. Mas **ligar** o que existe hoje não entrega: o rótulo é desenhado antes
   do conteúdo e a foto o apaga (CE-01, medido: 21 de 1.518 px sobrevivem).

8. **"§16: `app/scripts/*`, 12 arquivos" — são 47 módulos / 6.049 linhas**, 39 deles sem
   nenhuma citação em teste. Muda a natureza do problema: não é uma sobra pequena, é **8% do
   código de `app/`** e o esconderijo de dois módulos de produção (CC).

**E o que eu refuto de MIM MESMO** (bugs meus, achados pelos meus próprios céticos — lei da
honestidade de bancada):

- Meu agente da frente CD escreveu *"nenhum teste de undo confere CONTEÚDO — o I5 não vale para
  o histórico"*. **Falso.** `test_adversarial_vinculo.py:129-137` faz 5 desfazer + 2 refazer e
  chama `_conferir` (`:85-101` = `compor_pagina` + `getpixel` por célula);
  `test_multipagina.py:75-92,150` idem por página. **Achado retirado.**
- Meu agente da frente CC escreveu que as galerias *"fotografam uma janela que o dono nunca
  vê"*. **Falso:** `editor_app.py:327-333` chama as MESMAS `_montar_shell`/`_completar_janela`
  do app real. **Achado reduzido** ao que sobrevive: quatro scripts rodam contra a raiz viva
  (CC-05).
- Eu mesmo suspeitei que faltassem `hiddenimports` no `.spec` para `ddgs`/`qrcode`/`fontTools`
  por serem importados dentro de função. **Errado:** o PyInstaller analisa o bytecode inteiro,
  inclusive imports em função. O que **de fato** falta no spec são **dados**, não módulos (CA-08).

---

## §12 · PROVA DE MUTAÇÃO — a tabela

Está em **§1.4**, com o método completo. O resumo, porque é o dado mais importante desta fase:

> **Seis linhas 🔴 quebradas de propósito. 851 testes rodados. Um único vermelho — e por acaso.**
>
> | achado | testes que pegaram |
> |---|---:|
> | V-01 · véu órfão | **0** |
> | E-01 · região herda o slot | 1 (incidental) |
> | R-02 · subir/descer invertidos | **0** |
> | E-08 · rotação trava o resize | **0** |
> | F-01 · etiqueta em lote (mutei o **preço**) | **0** |
> | R-01 · Y do texto incondicional | **0** |
>
> Árvore restaurada e conferida: `git checkout --` nos 6 arquivos + `git diff --quiet` limpo.

---

## §13 · Placar por severidade

| frente | 🔴 | 🟠 | 🟡 | 🔵 | total |
|---|---:|---:|---:|---:|---:|
| **CA** · instalador / 1ª execução | 3 | 4 | 5 | 1 | 13 |
| **CB** · arquivos, Cofre, somente-leitura | 2 | 8 | 4 | 2 | 16 |
| **CC** · `app/scripts/*` | 0 | 6 | 12 | 1 | 19 |
| **CD** · histórico / undo | 2 | 6 | 6 | 0 | 14 |
| **CE** · seções / imposição | 0 | 4 | 6 | 5 | 15 |
| **CF** · teclado / acessibilidade | 1 | 5 | 7 | 0 | 13 |
| **CG** · DPI / monitores | 0 | 5 | 7 | 1 | 13 |
| **CH** · código morto / repositório | 0 | 2 | 7 | 5 | 14 |
| **CI** · achados nascidos na frente de visão | 2 | 4 | 0 | 0 | 6 |
| **TOTAL** | **10** | **44** | **54** | **15** | **123** |

*(118 levantados nas 8 frentes − 1 retirado pelos meus próprios céticos (§11) + 6 nascidos na frente de visão (§9b).)*

**Invariantes feridas: 67** — **I2 × 47** (a degradação silenciosa é, de longe, a doença
crônica deste programa), I5 × 9, I1 × 6, I3 × 5.
**Sem cobertura de teste: 114 dos 123 (93%).**

**Somando ao dossiê do arquiteto (133):** **256 achados** catalogados, **41 🔴**.

---

## §14 · O que ficou de fora da MINHA varredura

Honestidade de bancada — o que eu **não** cobri, e por quê:

1. **Não executei o `.exe`.** Rodar `dist/AutoTabloide/AutoTabloide.exe` criaria raiz de dados,
   banco e snapshot — escrita, proibida pela Regra Zero. Toda a análise do congelado é
   inventário estático do build de 21/07 (listagem do `_internal`, índice do `PYZ.pyz` com
   16.391 módulos) + leitura de código + a busca por assets dentro do bundle. **Os achados
   CA-01, CA-02 e CA-03 descrevem o que o código FARÁ; nenhum foi observado rodando.**
2. **Não rodei a suíte num clone limpo de verdade** — usei outra pasta de trabalho como proxy.
   Os números (10 vermelhos / 8 pulados) são reais; num clone limpo a composição pode diferir
   um pouco (lá `arte/` some de vez, aqui ela existe em caminho absoluto).
3. **Não medi corte de texto em Windows real:** a bancada roda offscreen com fonte substituta
   (Segoe UI ausente — `QFontDatabase` confirma), então larguras absolutas saem infladas. Por
   isso **não** reportei dois suspeitos que dependem da largura exata do Segoe UI
   (`configuracoes.py:599` `setFixedWidth(190)` e `faixa_paginas.py:33`).
4. **Não abri o app de verdade em nenhuma frente** — a ordem de foco final das 36 telas com
   dados reais não foi observada; foi reproduzida em PySide6 puro, fielmente mas fora do app.
5. **Não auditei o interior de `dist/`** (4,3 GB) além da busca por assets e do índice do PYZ.
6. **Não provei o CB-10** (uuid do pacote virando caminho): provei que o valor vem de fora sem
   validação, não que se consegue escrever fora da raiz. Está marcado como risco não provado.
7. **Não toquei nas frentes do arquiteto** (V/E/R/P/C/I/X/F/D/A/U/N) exceto para confirmar,
   refutar ou cruzar.
8. **Prova de mutação:** rodei nos 6 achados 🔴 que o briefing indicou. Os outros 25 🔴 do
   dossiê e os 8 🔴 meus **não** foram submetidos a mutação — dado o resultado (5 de 6 sem
   cobertura), a expectativa é que a maioria também não tenha.

---

*Fim da varredura. Nenhum arquivo de `app/`, `src/`, `alembic/` ou config foi modificado.*
*As mutações do §1.4 foram desfeitas e a árvore conferida limpa.*
*O caderno de visão está em `docs/VISAO_CODE_F13.md`.*
