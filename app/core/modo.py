"""
Modo somente-leitura (FASE 12, Bloco A — R-131)
===============================================
O PC da LOJA aprova e imprime — não edita à toa (à prova de dedo). Com a
chave ligada (Config `app.somente_leitura`), as PORTAS DE ESCRITA do acervo
e dos projetos levantam `SomenteLeitura` com a mensagem em PT-BR (os workers
já a mostram como toast — nada falha em silêncio, I2). Aprovar, exportar,
imprimir e compartilhar seguem LIVRES — é para isso que o modo existe.
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
