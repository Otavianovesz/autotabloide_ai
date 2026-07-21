"""Modo planilha da estante (R-051, Fase 6 — Bloco B).

A lógica de edição vive aqui (testável sem Qt): editar nome/preço/unidade/
categoria de um ItemMesa EM MEMÓRIA — a mesma fonte de verdade do canvas
(reflete por uid, I1). Nome passa pela sanitização (RG-20); preço pelo parser
P0.3 (rejeita ambíguo → não grava, com aviso, I2). O diálogo Qt (`DialogoPlanilha`)
é a casca; a decisão está em `aplicar_edicao`.
"""

from __future__ import annotations

# colunas na ordem que o dono mexe no dia a dia
COLUNAS = ("Foto", "Nome", "Preço", "Unidade", "Categoria", "Observação")
# colunas editáveis (Foto é só a miniatura/indicador)
EDITAVEIS = ("Nome", "Preço", "Unidade", "Categoria", "Observação")


def valor_da_coluna(item, coluna: str) -> str:
    """O texto atual de uma célula (para popular a grade)."""
    if coluna == "Nome":
        return item.nome or ""
    if coluna == "Preço":
        # promoção (R-070) mostra o texto do formato no lugar do valor vazio
        return item.preco or getattr(item, "multi_preco", None) or ""
    if coluna == "Unidade":
        return item.unidade or ""
    if coluna == "Categoria":
        return item.categoria or ""
    if coluna == "Observação":
        return getattr(item, "observacao", None) or ""
    return ""


def _persistir_cadastro(item, **campos) -> str | None:
    """OS F11.5 #68: a edição na planilha também grava no CADASTRO, por
    produto_id (I1) — Nome e Categoria são dados do ACERVO, não só da oferta.
    (O preço digitado é o "por" da OFERTA e segue no projeto — o `preco_atual`
    do banco é o "de", decisão da F6.) Falha vira AVISO (I2), nunca silêncio."""
    if not getattr(item, "produto_id", None):
        return None
    try:
        from app.core.database import Database
        from app.core.repositories import ProdutoRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                ProdutoRepositorio(s).editar(item.produto_id, **campos)
                s.commit()
        finally:
            db.engine.dispose()
        return None
    except Exception as e:
        return f"editado na oferta, mas não gravei no cadastro ({e})"


def aplicar_edicao(item, coluna: str, texto: str) -> tuple[bool, str | None]:
    """Aplica a edição de UMA célula ao ItemMesa (em memória) e, quando o
    campo é de CADASTRO (Nome/Categoria) e o item tem produto_id, grava
    também no banco (#68). Devolve (gravou, aviso|None). Preço não entendido
    NÃO grava (I2): devolve o aviso e mantém o valor anterior."""
    texto = (texto or "").strip()
    if coluna == "Nome":
        if texto:
            from app.core.sanitize import sanitizar
            item.nome = sanitizar(texto).nome_sanitizado or texto
        else:
            item.nome = texto
        return True, _persistir_cadastro(item, nome_sanitizado=item.nome)
    if coluna == "Preço":
        # R-070: "3 por R$10" / "leve 3 pague 2" é multi-preço (FORMATO), não
        # preço inválido — grava em multi_preco e desenha esse texto.
        from app.qt.telas.colagem import parse_multi_preco
        mp = parse_multi_preco(texto)
        if mp is not None:
            item.multi_preco = mp.texto
            item.preco = None
            return True, None
        item.multi_preco = None
        if texto:
            from app.qt.telas.servico import preco_decimal
            if preco_decimal(texto) is None:
                return False, (f"Preço “{texto}” não foi entendido "
                               "(ex.: use 5,00 — nada de “2x 5,00”).")
        item.preco = texto or None
        return True, None
    if coluna == "Unidade":
        item.unidade = texto or None
        return True, None
    if coluna == "Categoria":
        item.categoria = texto or None
        return True, _persistir_cadastro(item, categoria=texto or None)
    if coluna == "Observação":
        # R-071: observação por item ("limite 2 por cliente") — texto livre,
        # opcional; alimenta a região de papel OBSERVACAO (condicional).
        item.observacao = texto or None
        return True, None
    return False, None


def problema_na_celula(item, coluna: str) -> str | None:
    """Destaque de problema por célula (passo 26): o dono enxerga o que falta.
    Devolve o motivo (para tooltip) ou None."""
    from app.qt.telas.servico import preco_decimal
    if coluna == "Foto" and not (item.imagem or item.imagens):
        return "sem foto"
    if coluna == "Preço":
        if getattr(item, "multi_preco", None):
            return None                          # R-070: multi-preço TEM preço
        if not item.preco:
            return "sem preço"
        if preco_decimal(item.preco) is None:
            return "preço não entendido"
    if coluna == "Nome" and not (item.nome or "").strip():
        return "sem nome"
    return None
