# AutoTabloide AI

App desktop offline (Windows) que automatiza a produção de material gráfico de
ofertas de supermercado: importar tabela/foto → conciliar com o banco → sanitizar
nomes → tratar imagens → montar o layout → exportar. Ver `CLAUDE.md`, `docs/` e
`docs/PLANO_DE_CONSTRUCAO.md`.

> Reconstrução limpa em `app/` (o `src/` antigo é legado, será removido). Stack:
> Python 3.12 + PySide6/Qt6, SQLite (SQLAlchemy síncrono), Pillow para compor,
> rembg/Real-ESRGAN/icrawler para imagens, IA local via API compatível-OpenAI.

## Como rodar

A IA usa um servidor local (LM Studio) — ver `docs/INSTALAR_LM_STUDIO.md`.

```bash
# Abrir o EDITOR numa janela real (arte do Belo Brasil + célula-mestre):
python -m app.editor_app
#   (equivalente: python -m app.main --editor)

# Janela base:
python -m app.main

# Testes:
python -m pytest app/tests -q
```

### Demos (geram imagens numa pasta de saída)

```bash
python -m app.scripts.gate_fidelidade saida/frente.png   # produto sobre a arte real
python -m app.scripts.demo_editor saida/editor.png       # editor com camadas
python -m app.scripts.demo_multi_imagem saida_multi      # múltiplas imagens no slot
python -m app.scripts.demo_conciliacao                   # semáforo verde/amarelo/vermelho
python -m app.scripts.demo_busca_imagem "Nutella 350g Ferrero"
```

## Estrutura (`app/`)

- `core/` — banco, modelos, sanitização, repositórios.
- `rendering/` — compositor (Pillow), modelo de layout (mm/px), arranjo, selos, persistência.
- `images/` — busca (Bing), remoção de fundo (rembg), upscale (Real-ESRGAN), biblioteca.
- `ai/` — cliente IA, enriquecimento, conciliação (3 camadas), OCR, pipeline.
- `qt/` — editor visual (canvas WYSIWYG, camadas, propriedades).
- `AutoTabloide_System_Root/` — dados do sistema (banco, imagens, layouts, fontes…).
