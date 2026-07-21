"""
Trava de instância única (A5 da ORDEM_F5_8 / S6 da sessão ao vivo)
==================================================================
Na sessão do gate 3, uma instância ELEVADA da véspera ficou viva e invisível,
travando tudo até fechamento manual. Nunca mais duas em silêncio:

A primeira instância abre um ``QLocalServer`` nomeado; a segunda detecta o
servidor, manda "ativar" e **sai** — e a primeira traz a própria janela para
frente. Lock órfão de crash é removido antes de escutar (``removeServer``).
Elevada ou não: named pipes locais atravessam esse limite no Windows.
"""

from __future__ import annotations

from PySide6.QtNetwork import QLocalServer, QLocalSocket

NOME_TRAVA = "autotabloide_ai_instancia_unica"


def instancia_ja_existe(nome: str = NOME_TRAVA, timeout_ms: int = 400) -> bool:
    """True = já há uma instância viva (avisamos ela para se mostrar)."""
    sock = QLocalSocket()
    sock.connectToServer(nome)
    if sock.waitForConnected(timeout_ms):
        sock.write(b"ativar")
        sock.flush()
        sock.waitForBytesWritten(timeout_ms)
        sock.disconnectFromServer()
        return True
    return False


def travar_instancia(ao_ativar, nome: str = NOME_TRAVA) -> QLocalServer | None:
    """Assume a trava. ``ao_ativar()`` roda quando outra instância bater aqui.

    Devolve o servidor (segure a referência!) ou None se a trava falhou.
    """
    QLocalServer.removeServer(nome)          # lock órfão de crash anterior
    servidor = QLocalServer()

    def _conexao() -> None:
        con = servidor.nextPendingConnection()
        if con is not None:
            con.disconnected.connect(con.deleteLater)
            ao_ativar()   # a PRÓPRIA conexão é o pedido de ativação
            # (não depender de readyRead: os bytes podem já ter chegado
            # antes do connect — sinal perdido = janela que não sobe)

    servidor.newConnection.connect(_conexao)
    if not servidor.listen(nome):
        return None
    return servidor
