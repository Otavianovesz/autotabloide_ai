# Bloco D (F13) — o quadro hoje × ideal, MEDIDO

Máquina real do dono, 25/07/2026, IA desligada (`ia.usar=False` — tudo aqui
é o caminho 100% local). Campanha REAL: **Quintou, 30 ofertas, arte
frente+verso** (`arte/quintou/`, validade "ATÉ 26/05" lida do dado). Números
por `time.perf_counter`, mediana de 3 passadas onde marcado (×3).

## As medições

| # | O quê | Medido | Antes (auditoria/varredura) |
|---|---|---|---|
| 1 | Conciliar as 30 ofertas reais contra o acervo (fuzzy local, sem LM) | **0,07 s · 30/30 verdes** | — (o funil da F12 já era rápido; aqui é a prova no caminho recorrente) |
| 2 | Compor a frente REAL (286×344 mm, 96 dpi nativo da arte, 15 células) ×3 | **105 ms** | 113 ms/tecla (X-01) — e era UMA POR TECLA |
| 2b | A mesma página FORÇADA a 300 dpi (a arte do Illustrator nativa) ×3 | cheio **196 ms** → prévia 96 dpi **99 ms** (**2,0×**) | a prévia compunha SEMPRE no dpi do layout |
| 2c | O ganho REAL do D2 na digitação: rajada de 13 teclas | **1 recomposição** (~105 ms no fim do gesto) | **13 recomposições** (~1,4 s) + 13 estados de desfazer |
| 3 | Exportar frente+verso reais em PDF (dpi do layout) | **0,17 s · 323 KB** | — |
| 4 | Detector de fundo branco (D3, agora LIGADO por padrão) | **13 ms** e pula o rembg | **8–26 s** de rembg por foto que JÁ era packshot |
| 5 | Pré-voo das 2 páginas reais COM os sinais novos (revisora + nota da foto, D10) | **0,02 s · 15 avisos nominais** (as células da medição não têm foto — o aviso é legítimo) | o pré-voo devolvia `[]` para peça com defeito (achado H2 do dossiê) |

## O quadro hoje × ideal (§2 do caderno), reescrito com o que o bloco mudou

| Etapa do dia | Antes (medido na auditoria) | Agora (medido acima) |
|---|---|---|
| Tratar fotos que JÁ são packshot | 8–26 s CADA no rembg, com a tela SEQUESTRADA pelo véu | 13 ms por foto (detector, padrão ligado) e o véu virou RODAPÉ — a tela fica livre para continuar o resto (D1+D3) |
| Digitar/ajustar nome no editor | ~113 ms POR TECLA + um Ctrl+Z por letra | 1 recomposição por GESTO (~105 ms) + UM desfazer devolve a palavra (D2) |
| Conciliar a tabela recorrente | — | 0,07 s para as 30 reais, 30/30 verdes (o acervo da semana já casa) |
| A semana recorrente (mesma oferta, preços novos) | reimportar = "Substituir tudo" → mapa e overrides ZERADOS → remontar a arte inteira | "Atualizar os preços dos atuais" por chave natural: montagem intacta, prévia→confirma (D12) |
| Validade | digitada à mão, esquecida no export, rodapé fora de célula ficava VAZIO | autopreenche pela campanha no salvar E no export; a validade viva chega ao rodapé (o canal estrutural do compositor, D7) |
| Aprovar/exportar | aprovação inalcançável (9 portas carimbando RASCUNHO), Aprovar escondido na paleta | exportar sai LIMPO por padrão; RASCUNHO é opção explícita; botão Aprovar REAL na Mesa e na Fábrica (D8 — as travas #1 e #3 caíram) |
| Conferência final | o pré-voo mudo para nome cortado/foto ruim (só o botão Revisar sabia) | os sinais entram no pré-voo em 0,02 s (D10) |

*Ressalva honesta: a arte real do Quintou entra a 96 dpi (metadado da
própria arte), então NELA o ganho do D2 é a coalescência; o ganho do dpi
(2,0×) vale para arte 300 dpi (linha 2b). O rembg de foto NÃO-branca
continua pagando o preço do modelo — o detector só mata o caso covarde
(que é o caso comum do packshot de fornecedor).*
