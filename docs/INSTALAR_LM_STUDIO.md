# Instalar o LM Studio (a IA local do AutoTabloide)

> **A IA é um acelerador, nunca uma exigência.** Sem o LM Studio o
> AutoTabloide funciona 100%: a conferência vira fuzzy/manual, a revisora do
> export vira heurística e o app **avisa** ("Sem IA") em vez de travar.
> Instale quando quiser ganhar velocidade na conferência e no OCR.

O AutoTabloide fala com um servidor de IA local pela API padrão (compatível
com OpenAI) em `localhost` — nada sai do seu PC. O LM Studio é esse
servidor; dá para trocar por Ollama depois sem mexer no código.

## 1. Baixar e instalar
- Baixe o LM Studio em https://lmstudio.ai e instale (Windows).
- É o ÚNICO pedaço que precisa de internet — o AutoTabloide em si é offline.

## 2. Baixar os modelos (aba "Discover"/buscar)
Para **8 GB de VRAM**, comece em **4-bit (Q4_K_M)** — cabe com folga e é rápido:

| Papel | Modelo sugerido | Quantização |
|---|---|---|
| **Texto** (sanitizar/enriquecer/juiz/Fica-a-Dica) | `Qwen2.5-7B-Instruct` | Q4_K_M (~4,5 GB) |
| **Visão / OCR** (ler o print do WhatsApp; revisora do export) | `Qwen2.5-VL-7B-Instruct` | Q4_K_M (se faltar memória, use a versão **3B**) |
| **Embeddings** (conciliação por significado) | `nomic-embed-text-v1.5` | leve (<1 GB) |

Dica 8 GB: não precisa manter os três na memória ao mesmo tempo. O LM Studio
carrega sob demanda — o texto para o enriquecimento, a visão só na hora do OCR.

## 3. Subir o servidor local
- Vá na aba **Developer** (ou "Local Server"), **carregue** o modelo de texto e
  clique em **Start Server**.
- O padrão é `http://localhost:1234/v1` — é o que o app espera. Endereço e
  nomes de modelo são editáveis em **Configurações → IA**.

## 4. Conferir dentro do app
- **Configurações → IA → Testar conexão**: o app lista os modelos carregados
  e diz o que encontrou. Verde = pronto.
- A partir daí o semáforo da Mesa usa embeddings + juiz, o OCR lê prints e a
  revisora de export olha a arte final antes de você mandar.

## O que cada recurso usa

| Recurso do app | Precisa de quê |
|---|---|
| Conferência (semáforo) | embeddings + texto — sem eles, fuzzy com aviso |
| Importar por foto/print (OCR) | visão — sem ela, colar texto/planilha |
| Revisora do export (F9) | visão — sem ela, heurística (de≤por, nome cortado) |
| Estúdio degrau 2 (img2img) | **GPU + SDXL** (à parte do LM Studio) — sem GPU, o degrau 1 entrega |

## Se der erro
- **"LM Studio não acessível"**: confira se o servidor está com **Start Server**
  ligado e na porta 1234.
- **Nomes de modelo diferentes**: o identificador que o LM Studio expõe pode
  diferir do padrão. Ajuste em **Configurações → IA** (o teste de conexão
  mostra os nomes carregados).
- **Falta de memória (OOM) na visão**: troque o VL de 7B para 3B.
- **Ficou lento**: feche outros programas pesados; ou descarregue o modelo de
  visão quando não estiver importando por foto.
