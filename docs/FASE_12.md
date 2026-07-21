# FASE 12 — Confiabilidade, MARCO FINAL e entrega (caderno de 100 passos)

> Formato-lei do PLANO_PERFEITO. Cobre R-127, R-131, R-136, R-137, R-138,
> R-144, R-147, R-148, R-149, **R-150 ("Modo Pai")**, **RG-48/RG-58 (o marco
> re-executado com layout REAL desenhado)** + o **Bloco G** (instalador,
> migração, guia rápido em PT-BR) + o **teste de aceitação do dono**.
> **Emissão em lote (19/07)** — ver cabeçalho da FASE_4.md. Chat novo por fase.
> **Intensidade: MÁXIMA** (F4 e F12 são as duas de intensidade máxima).
>
> **Por quê da fase:** fechar tudo, provar tudo, instalar no PC do mercado. É
> a fase da aceitação do dono e do empacotamento. O marco só fecha com o SELO
> HUMANO do Otaviano — é o fim da construção do AutoTabloide AI. Riscos
> travados: o empacotamento com rembg/onnx/torch é pesado (testar num Windows
> LIMPO); e a inspeção visual de TODOS os artefatos vale peça a peça (a lei da
> 2ª passada — nunca selar sem olhar).

## Bloco A — Robustez final (R-137, R-131, R-136, R-127, R-138) · passos 1–18
**Por quê:** o app vai morar no PC do mercado — tem que se defender sozinho de
corrupção, de dedo pesado e de desatualização.

1. R-137 (recuperação de projeto corrompido): ao detectar corrupção, restaurar do último snapshot bom (rascunho automático da F6 + versões da F2).
2. A recuperação é oferecida com prévia ("recuperar o último bom de HH:MM?") — nunca sobrescreve em silêncio (I2).
3. Detecção de corrupção honesta (JSON quebrado, referência perdida) com mensagem clara em PT-BR — sem stack trace na cara do dono.
4. R-131 (modo somente-leitura): um modo para o PC da loja onde se aprova/imprime, mas não se edita à toa (à prova de dedo).
5. O somente-leitura protege acervo/projetos de alteração acidental; sair dele é consciente (toggle claro ou senha simples opcional).
6. R-136 (exportar projeto como .atproj único): empacotar projeto + fotos + layout num arquivo só, para levar entre PCs.
7. O .atproj é a portabilidade do Bloco D num arquivo (zip com manifesto, caminhos relativos I3) — ida-e-volta idêntico.
8. R-127 (atualização): auto-atualização com as novidades em PT-BR; se offline, um "verificar atualização" manual honesto.
9. A atualização nunca é obrigatória nem intrusiva; as novidades aparecem em linguagem do dono (o changelog da aba Sobre, F3).
10. R-138 (robustez de dados): validação de integridade na abertura (banco PRAGMA, referências de foto) — conserta o que dá, avisa o resto (reusa a verificação da F3).
11. Toda recuperação/validação é reversível e logada (nada apaga sem confirmação).
12. O somente-leitura e o .atproj respeitam o congelamento (dados da época) e o vínculo por uid (I1).
13. Foto: recuperação de corrompido, modo somente-leitura, exportar .atproj, verificar atualização (claro/escuro).
14. Teste: um projeto deliberadamente corrompido é restaurado do último snapshot bom (por conteúdo).
15. Teste: .atproj ida-e-volta é idêntico (byte a byte nos dados; fotos por caminho relativo).
16. Teste: somente-leitura barra a edição acidental e é reversível de forma consciente.
17. Teste: "verificar atualização" offline degrada com honestidade (não trava, não mente).
18. **Checagem (marco 1/5):** suíte inteira ×1 verde exit 0; screenshots de robustez em `saida_fase12/`.

## Bloco B — Sonhos finais (R-144, R-148, R-149, R-147) · passos 19–34
**Por quê:** os desejos que o dono marcou para o fim — presentes que coroam o
app, todos opcionais e nenhum requisito.

19. R-144 (etiquetas de prateleira em lote): dezenas de etiquetas por folha (imposição controlada, como o 2-em-1) — reusa o pipeline do cartaz.
20. As etiquetas em lote leem os produtos selecionados (filtros da estante) e preenchem a folha no tamanho físico certo.
21. R-148 (calendário promocional anual): Páscoa, São João, Black Friday etc. com lembretes e kits de campanha prontos.
22. O calendário conversa com os Eventos (F2/F3) — cada data comemorativa vira um evento com cor/kit sugerido.
23. Os lembretes do calendário são locais e desligáveis (nada de notificação intrusiva).
24. R-149 (exportar layout como template compartilhável SEM dados): um presente para outro mercado — a estrutura, nunca os dados do dono.
25. O template compartilhável carrega o LayoutDef + estilos, jamais produtos/preços/fotos (I3 + privacidade) — testado por AUSÊNCIA de dado.
26. R-147 (gerador de artes de fundo por IA): fundos para datas comemorativas — EXPERIMENTAL, condicionado à GPU como o RG-46.
27. Sem GPU, o gerador de fundo fica desabilitado com aviso honesto (o app não depende dele) — a mesma disciplina do Estúdio degrau 2.
28. O fundo gerado é sempre um ponto de partida editável (a arte do Illustrator continua sendo o caminho principal do dono).
29. Todos os sonhos respeitam os vetos (nada de custo/margem/ERP) e o offline.
30. Nenhum sonho é requisito: o app essencial (tabloide + cartaz) funciona sem nenhum deles.
31. Foto: etiquetas em lote, calendário promocional, template compartilhável (sem dados), fundo gerado (onde houver GPU) — claro/escuro.
32. Teste: etiquetas em lote medem certo (mm); template compartilhável não leva nenhum dado do dono (varredura).
33. Teste: o calendário cria um evento comemorativo; o gerador de fundo degrada sem GPU.
34. **Checagem:** suíte parcial verde; template sem-dados e etiquetas-lote medidas passam.

## Bloco C — Modo Pai (R-150) · passos 35–46
**Por quê:** o dono mencionou o pai várias vezes — uma visão à prova de erro,
só para aprovar e imprimir/enviar, e nada mais.

35. R-150 (Modo Pai): uma visão simplificada — só o essencial: ver o que está pronto, aprovar, imprimir/enviar.
36. No Modo Pai, os botões são grandes, poucos e claros; nada de editor, nada de configuração perigosa.
37. O fluxo do Modo Pai: abrir o projeto pronto → conferir → aprovar → imprimir OU enviar (copiar imagem) — 3 passos, à prova de erro.
38. Entrar/sair do Modo Pai é claro (um botão grande "Modo simples") e lembrado por perfil de uso.
39. O Modo Pai reusa a aprovação em 2 etapas (F8) e o compartilhar (F8) — nada novo por baixo, só a casca simples.
40. Nenhuma ação destrutiva no Modo Pai (não apaga, não reconfigura, não edita preço) — só aprova e publica.
41. Texto grande e linguagem simples (o dono pensou no pai) — acessibilidade real, não decorativa.
42. O Modo Pai combina com o somente-leitura (R-131) — o PC da loja pode nascer nele.
43. Foto: o Modo Pai (a tela simples de aprovar e imprimir) claro/escuro.
44. Teste: no Modo Pai só existem as ações seguras (aprovar/imprimir/enviar); nenhuma destrutiva alcançável.
45. Teste: o fluxo de 3 passos leva do projeto pronto ao envio sem passar por tela perigosa.
46. **Checagem (marco 2/5):** suíte inteira ×1 verde exit 0; screenshots do Modo Pai em `saida_fase12/`.

## Bloco D — O MARCO refeito (RG-48/RG-58) · passos 47–66
**Por quê:** o teste de aceitação do dono — o Sexta Verde com LAYOUT REAL
desenhado sobre a arte, "até" nunca vazio, tudo inspecionado peça a peça.

47. Corrigir o RG-48: o Sexta Verde ganha um LAYOUT REAL desenhado SOBRE a arte (células nos balões verdes), sem grade sintética bizarra.
48. Detecção/desenho das células nos balões verdes reais da campanha (não uma grade regular imposta) — o desenho respeita a arte.
49. RG-58: o "até" da validade NUNCA fica vazio no marco (a regra travada, exercida na peça real).
50. Reunir as TRÊS campanhas reais (Quintou do Real, Sexta Verde, Fim de Semana) como o padrão-ouro de regressão.
51. Montar o marco: tabloide ~40 itens categorizado, com as artes reais, seções com contorno de união (F4-C), selos e +18.
52. Performance ≥5k: o acervo com 5.000+ produtos; abrir/conciliar/exportar dentro dos tetos medidos (a régua das ondas).
53. Compor o marco ponta a ponta: importar ~40 → conciliar → categorizar → auto-preencher → pré-voo → exportar as 3 campanhas.
54. Medir cada PDF do marco em mm/bytes (o padrão-ouro) e comparar com a peça real de referência.
55. Inspeção visual TOTAL do arquiteto: cada página de cada campanha, célula a célula, selo a selo (lei da 2ª passada — selo só com inspeção de TODOS os artefatos).
56. O adversarial do vínculo re-rodado sobre o marco inteiro (o trio de cada um dos ~40 por conteúdo).
57. Conferir a fidelidade contra as referências (marcas certas, unidades limpas, preços 1:1, "até" preenchido).
58. O +18 automático nas bebidas confere na peça (decisão travada) — a diferença esperada vs. a referência anotada, não erro.
59. Nenhum item sem foto/preço entra sem aviso no marco (pré-voo, I2).
60. Foto: as 3 campanhas montadas e exportadas (todas as páginas) + o comparativo com a referência (claro/escuro).
61. Teste: o marco dos ~40 compõe as 3 campanhas com o layout real (sem grade sintética); "até" nunca vazio.
62. Teste de performance: 5k produtos, abrir/conciliar/exportar dentro dos tetos (medido, não estimado).
63. Teste adversarial do marco: os ~40 trios por conteúdo, seções-união por pixel, selos na âncora.
64. Registrar qualquer achado do marco como RG novo (não varrer para baixo do tapete).
65. Preparar o dossiê do marco para o dono (as 3 campanhas + medições + comparativos) — material da sessão de aceitação.
66. **Checagem (marco 3/5):** suíte inteira ×1 verde exit 0; o marco inteiro inspecionado peça a peça em `saida_marco/`.

## Bloco E — Bloco G: empacotamento e entrega · passos 67–84
**Por quê:** o programa tem que morar no PC do mercado — instalador, primeira
execução, migração do acervo antigo, guia em PT-BR.

67. Instalador Windows (PyInstaller): empacotar o app com as dependências (rembg/onnx, Real-ESRGAN, Qt) num instalador único.
68. **Risco travado:** o empacotamento com rembg/onnx/torch é pesado — testar o instalador num WINDOWS LIMPO (não a máquina de dev).
69. Primeira execução: um assistente que cria o banco, as pastas e faz a verificação de instalação (F3) — verde antes de usar.
70. Migração de assets da versão anterior: importar o acervo/projetos do protótipo antigo sem perder nada (chave natural, I1).
71. A migração é testada com o acervo real do dono (os 69+ produtos do roundtrip; os 5k do marco) — byte a byte.
72. Checklist de instalação do LM Studio + modelos (Qwen visão/texto/embedding) em PT-BR, passo a passo (o `INSTALAR_LM_STUDIO.md` atualizado).
73. Guia rápido em PT-BR: as telas, o fluxo da quinta-feira, o que fazer quando algo falha — na linguagem do dono.
74. O app sem LM Studio funciona (degrada com aviso, F9) — o guia deixa isso claro (a IA é acelerador, não requisito).
75. Ícone do app definido (a decisão A×B da F3 resolvida pelo dono) + versão 1.0 no Sobre.
76. O instalador não exige internet para o essencial (offline); só o LM Studio/modelos são baixados à parte, com instrução.
77. Desinstalar limpo (sem deixar lixo) e preservar o acervo do dono (não apaga os dados dele).
78. Teste do instalador num Windows limpo: instala, abre, verifica, monta um tabloide simples — ponta a ponta.
79. Teste da migração: o acervo antigo entra íntegro (chave natural; fotos por caminho relativo).
80. Teste de tamanho/tempo do instalador (o pacote pesado não pode ser inviável) — medir e registrar.
81. Guia e checklist revisados em PT-BR (sem jargão, sem passo faltando).
82. Foto: o instalador, a primeira execução, o guia rápido (claro/escuro).
83. Empacotar também os artefatos de suporte (diagnóstico da F3) para o dono mandar se precisar.
84. **Checagem (marco 4/5):** o instalador roda num Windows limpo e monta um tabloide; a migração preserva o acervo.

## Bloco F — Integridade final e SELO HUMANO · passos 85–100
**Por quê:** é o fim da construção — só fecha com o adversarial final, a
varredura do radar e o selo do Otaviano sobre o marco.

85. Suíte inteira ×2 exit 0, zero skips (a arte real das 3 campanhas conta).
86. Adversarial do vínculo final: o marco inteiro e todos os fluxos (I5) — o trio por conteúdo em toda parte.
87. Varredura final do radar: NADA órfão — cada R aceito construído ou justificado como pós-1.0; cada veto ausente.
88. Reconferir I1–I5 no app inteiro (identidade, sem degradação silenciosa, portabilidade, mestra↔cópia, adversarial).
89. Medir tudo do marco uma última vez (5k, tetos de tempo, PDFs em mm) e arquivar as medições.
90. Teste novo `test_fase12_marco.py` + `test_instalador` (fumaça no Windows limpo): marco das 3 campanhas, .atproj idêntico, recuperação, Modo Pai seguro.
91. `saida_fase12/` + `saida_marco/`: robustez, sonhos, Modo Pai, as 3 campanhas do marco, instalador, guia — claro e escuro.
92. GIF curto (~15 s): do zero ao tabloide — importar → montar → aprovar → exportar (o app em 15 s).
93. Varredura de jargão em todo o app (PT-BR natural, a língua do dono, do boot ao export).
94. Atualizar `docs/PLANO_DE_CONSTRUCAO.md` (estado final) e o `CLAUDE.md` (versão 1.0, marco fechado).
95. Preparar o dossiê de aceitação para o Otaviano: as 3 campanhas montadas, as medições, o comparativo com as referências, o instalador.
96. Sessão de aceitação com o Otaviano: ele monta uma edição de verdade (test-drive), dita o apanhado de ressalvas, aprova a arte do cartaz.
97. As ressalvas do dono viram a lista final de ajustes pós-selo (o que ele decidir; nada bloqueia o marco a não ser o que ele disser).
98. **O SELO HUMANO do Otaviano sobre o marco da Fase 12** — é o fim da construção do AutoTabloide AI.
99. Pós-selo: só manutenção e os sonhos que o dono marcar dos que ficaram no radar (nada novo sem a palavra dele).
100. **PARAR** — o programa está no PC do mercado. As quintas-feiras de manhã em que o tabloide é um clique começam aqui.
