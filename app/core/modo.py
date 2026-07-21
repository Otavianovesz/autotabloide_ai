"""
Modo somente-leitura (FASE 12, Bloco A — R-131)
===============================================
O PC da LOJA aprova e imprime — não edita à toa (à prova de dedo). Com a
chave ligada (Config `app.somente_leitura`), as PORTAS DE ESCRITA do acervo
e dos projetos levantam `SomenteLeitura` com a mensagem em PT-BR (os workers
já a mostram como toast — nada falha em silêncio, I2).

PORTAS GUARDADAS (a frota adversarial da F12 achou 6 desguarnecidas — o
mapa vive aqui para a porta nova da próxima fase não nascer aberta):
produto (editar/excluir/criar/fundir/finalizar), projeto (salvar/excluir/
renomear/duplicar/abrir-versão-como-novo), foto (BibliotecaImagens.ingerir
— o funil do DISCO: Estúdio, Ajustar, Refinar, Restaurar do histórico),
Excel (aplicar_importacao_planilha), IA em lote (enriquecer_banco/
categorizar_acervo), trazer .atproj (importar_atproj), calendário
(criar_evento_comemorativo) e a migração antiga.

LIVRES DE PROPÓSITO (decisão, não esquecimento): aprovar, exportar,
imprimir, compartilhar — e os marcadores de fluxo que eles usam
(`marcar_status("exportado")`, favorito), que não alteram conteúdo.
Sair do modo é gesto consciente (confirmação na tela de Configurações).
"""

from __future__ import annotations

MENSAGEM = ("Este PC está no modo SOMENTE-LEITURA (aprova e imprime, não "
            "edita). Para editar, desligue o modo nas Configurações › "
            "Backups e segurança.")


class SomenteLeitura(RuntimeError):
    """Barreira do R-131 — a mensagem já nasce pronta para o toast."""

    def __init__(self, msg: str = MENSAGEM):
        super().__init__(msg)


def somente_leitura() -> bool:
    """A chave está ligada? Falha de leitura = desligado (o modo nunca
    prende o dono por acidente)."""
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                return bool(ConfigRepositorio(s).get(
                    "app.somente_leitura", False))
        finally:
            db.engine.dispose()
    except Exception:
        return False


def definir_somente_leitura(ligado: bool) -> None:
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio
    db = Database().init()
    try:
        with db.Session() as s:
            ConfigRepositorio(s).set("app.somente_leitura", bool(ligado))
            s.commit()
    finally:
        db.engine.dispose()


def exigir_escrita() -> None:
    """A guarda das portas de escrita: levanta `SomenteLeitura` se o modo
    está ligado. Uma linha por porta — barata e visível."""
    if somente_leitura():
        raise SomenteLeitura()
