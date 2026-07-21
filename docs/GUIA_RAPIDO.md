# AutoTabloide AI — Guia rápido (versão 1.0)

> O programa que monta o tabloide e o cartaz de gôndola do Belo Brasil.
> Tudo funciona **sem internet** — a IA local (LM Studio) é um acelerador,
> nunca uma exigência.

## As telas (na ordem da barra)

| Tela | Para quê |
|---|---|
| **Início** | O painel do dia: retomar de onde parou, números do acervo, criar novo. |
| **Eventos** | As campanhas ("Quintou", "Sexta Verde"…) com capa e cor. O **Calendário do ano** sugere as datas do varejo. |
| **Ateliê** | Os layouts (o desenho das células sobre a arte do Illustrator). |
| **Mesa** | O tabloide: importar a oferta → conferir → montar → exportar. |
| **Fábrica** | O cartaz de gôndola: 1 item por página no tamanho exato + **etiquetas em lote**. |
| **Almoxarifado** | O acervo de produtos: fotos, preços, Estúdio de imagem. |
| **Cofre** | Backups e portabilidade (levar tudo para outro PC). |
| **Modo simples** | A visão à prova de erro: ver o pronto, aprovar, imprimir, enviar. |

## O fluxo da quinta-feira (o dia do tabloide)

1. **Importar** — na Mesa, clique *Importar* e escolha a foto/print da tabela
   de ofertas (ou cole com Ctrl+V direto do WhatsApp/Excel).
2. **Conferir** — o semáforo mostra: 🟢 já existe · 🟡 conferir · 🔴 novo.
   Use **Aceitar todos os verdes** e resolva os poucos que sobrarem
   (atalhos: **N** próximo, **A** aceitar, **R** rejeitar).
3. **Montar** — *Auto-preencher a grade*. Ajuste o que quiser: arrastar
   troca de célula (segure **Alt**), duplo clique **entra** na célula para
   editar cada peça (Esc sai).
4. **Exportar** — o pré-voo avisa o que falta (foto, preço, validade).
   *Aprovar* tira a marca RASCUNHO. PNG para WhatsApp, PDF para impressão.
5. **Publicar** — Oferta do Dia, carrossel, story e vídeo saem do botão
   *Publicar* com a mesma arte.

## Quando algo falhar (as respostas do programa)

- **"Sem IA"** — o app continua 100%: a conferência vira manual/fuzzy e
  avisa. Para ligar a IA, veja `docs/INSTALAR_LM_STUDIO.md`.
- **Projeto não abre** — o programa oferece **recuperar** de um ponto bom
  (as versões automáticas). Nada se perde sem você confirmar.
- **Foto sumiu / banco estranho** — aviso na abertura + *Configurações →
  verificação da instalação* conserta o que dá e explica o resto.
- **Deu erro de verdade** — *Configurações → Sobre → Gerar diagnóstico
  para suporte* cria um .zip pequeno (sem fotos, sem dados seus) para
  mandar para quem cuida do programa.

## O PC da loja (o balcão)

- Ligue o **Modo somente-leitura** (Configurações → Backups): o PC aprova e
  imprime, mas não edita nada sem querer.
- O **Modo simples** pode ficar fixo: botões grandes, 3 passos, nenhum
  perigo. Ideal para quem só confere e imprime.

## Levar para outro PC

- **Um projeto**: *Abrir projeto → Levar (.atproj)* — um arquivo único com
  tudo (dados + fotos + arte). No outro PC: *Trazer (.atproj)*.
- **Tudo**: *Cofre → exportar* (o pacote completo do acervo).
- **Do programa antigo**: *Configurações → Backups → Migrar do AutoTabloide
  antigo* — com prévia; nada duplica.
