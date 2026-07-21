# Instalar o LM Studio (guia para RTX 8 GB)

O AutoTabloide fala com um servidor de IA local pela API padrão (compatível com
OpenAI). O LM Studio é esse servidor. Ele sobe em segundo plano; o app só conversa
com ele em `localhost`. Você pode trocar por Ollama depois sem mexer no código.

## 1. Baixar e instalar
- Baixe o LM Studio em https://lmstudio.ai e instale (Windows).

## 2. Baixar os modelos (aba "Discover"/buscar)
Para **8 GB de VRAM**, comece em **4-bit (Q4_K_M)** — cabe com folga e é rápido:

| Papel | Modelo sugerido | Quantização |
|---|---|---|
| **Texto** (sanitizar/enriquecer/juiz) | `Qwen2.5-7B-Instruct` | Q4_K_M (~4,5 GB) |
| **Visão / OCR** (ler o print do WhatsApp) | `Qwen2.5-VL-7B-Instruct` | Q4_K_M (se faltar memória, use a versão **3B**) |
| **Embeddings** (conciliação por significado) | `nomic-embed-text-v1.5` | leve (<1 GB) |

Dica 8 GB: não precisa manter os três na memória ao mesmo tempo. O LM Studio
carrega sob demanda — o texto para o enriquecimento, a visão só na hora do OCR.

## 3. Subir o servidor local
- Vá na aba **Developer** (ou "Local Server"), **carregue** o modelo de texto e
  clique em **Start Server**.
- O padrão é `http://localhost:1234/v1` — é o que o app espera (`ConfigIA`).

## 4. Validar o enriquecimento com o modelo REAL
No terminal, na pasta do projeto:

```
python -m app.scripts.demo_enriquecimento --real
```

Ele roda a sua lista (b) real (DE SODORANTE, Carbonell e Gallo, etc.) pelo Qwen e
mostra o antes→depois **de verdade** (sem fake). É o "gate" que confirma a
qualidade do enriquecimento antes de seguirmos para a conciliação.

## Se der erro
- **"LM Studio não acessível"**: confira se o servidor está com **Start Server**
  ligado e na porta 1234.
- **Nomes de modelo diferentes**: o identificador que o LM Studio expõe pode
  diferir do padrão do `ConfigIA`. Me chame que eu ajusto — ou rode isto para ver
  os nomes carregados:
  ```
  python -c "from app.ai.client import ClienteOpenAICompat; print(ClienteOpenAICompat().listar_modelos())"
  ```
- **Falta de memória (OOM) na visão**: troque o VL de 7B para 3B.
