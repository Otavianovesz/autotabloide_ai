"""
Trabalhador — trabalho pesado fora da thread da UI
==================================================
As etapas lentas (OCR, conciliação, enriquecimento, busca de imagem, rembg)
rodam num ``Trabalhador`` (QThread). A UI liga os sinais no overlay/toast e
NUNCA congela.

Uso::

    trab = Trabalhador(lambda status: fazer_algo(status))
    trab.status.connect(overlay.mostrar)     # "Enriquecendo nome…"
    trab.ok.connect(quando_terminar)         # recebe o resultado
    trab.erro.connect(quando_falhar)         # recebe a mensagem
    trab.start()

Regra de ouro: o resultado deve ser **dados planos** (dataclass/dict/str) —
nada de objetos ORM presos a sessão, nem widgets. Banco: abra a PRÓPRIA
conexão dentro do worker (SQLite não cruza threads).
"""

from __future__ import annotations

import traceback
import weakref
from typing import Callable

from PySide6.QtCore import QThread, Signal


class Trabalhador(QThread):
    """Roda ``fn(status_cb)`` fora da UI. ``status_cb(str)`` publica progresso."""

    ok = Signal(object)      # resultado de fn
    erro = Signal(str)       # mensagem de erro amigável
    status = Signal(str)     # etapa atual ("Buscando imagem…")

    def __init__(self, fn: Callable[[Callable[[str], None]], object], parent=None):
        super().__init__(parent)
        self._fn = fn

    def run(self) -> None:  # noqa: D102 (QThread)
        try:
            resultado = self._fn(self.status.emit)
        except Exception as exc:
            traceback.print_exc()
            # R-133 (FASE 3): conta o erro por função — a aba Sobre mostra
            # o top 3 e prioriza o próximo conserto
            try:
                from app.core.manutencao import registrar_erro
                registrar_erro(getattr(self._fn, "__qualname__", "")
                               or "anonima")
            except Exception:
                pass
            self.erro.emit(f"{type(exc).__name__}: {exc}")
        else:
            self.ok.emit(resultado)


class TrabalhadorFila(QThread):
    """Fila em segundo plano (RG-02a): roda ``fn(valor)`` para CADA par
    ``(chave, valor)`` e emite ``item_pronto(chave, resultado)`` na hora —
    a UI vai colhendo um a um, sem esperar a fila inteira.

    Identidade: a chave é o **uid** do item (I1) — o dono da fila nunca
    casa resultado por índice/linha (a tabela reordena). ``cancelar()``
    interrompe entre itens (o item em curso termina).
    """

    item_pronto = Signal(str, object)   # (chave, resultado de fn)
    item_falhou = Signal(str, str)      # (chave, mensagem) — nunca em silêncio
    fila_terminou = Signal()

    def __init__(self, pares: list[tuple[str, object]],
                 fn: Callable[[object], object], parent=None):
        super().__init__(parent)
        self._pares = list(pares)
        self._fn = fn
        self._cancelado = False

    def cancelar(self) -> None:
        self._cancelado = True

    def run(self) -> None:  # noqa: D102 (QThread)
        for chave, valor in self._pares:
            if self._cancelado:
                break
            try:
                resultado = self._fn(valor)
            except Exception as exc:
                traceback.print_exc()
                self.item_falhou.emit(chave, f"{type(exc).__name__}: {exc}")
            else:
                self.item_pronto.emit(chave, resultado)
        self.fila_terminou.emit()


class FilaIA(TrabalhadorFila):
    """OS F11.5 #61/#63/#64 (R-089/R-090): a fila de IA com PRIORIDADE VIVA —
    `focar(chave)` põe na frente o item que o dono está olhando (vale a partir
    do PRÓXIMO item; o em curso termina), `comecou_item` diz o que roda agora
    (o painel mostra), `pendentes()` lista o que falta, `cancelar()` para
    entre itens. A identidade segue sendo a chave/uid (I1)."""

    comecou_item = Signal(str, str)     # (chave, rótulo humano)

    def __init__(self, pares, fn, rotulos: dict | None = None, parent=None):
        super().__init__(pares, fn, parent)
        import threading
        self._lock = threading.Lock()
        self._foco: str | None = None
        self._rotulos = dict(rotulos or {})
        self.atual: str | None = None

    def focar(self, chave: str | None) -> None:
        with self._lock:
            self._foco = chave

    def pendentes(self) -> list[str]:
        with self._lock:
            return [c for c, _v in self._pares]

    def run(self) -> None:  # noqa: D102 (QThread)
        from app.qt.telas.servico import ordenar_por_prioridade
        while True:
            with self._lock:
                if self._cancelado or not self._pares:
                    break
                self._pares = ordenar_por_prioridade(self._pares, self._foco)
                chave, valor = self._pares.pop(0)
                self.atual = chave
            self.comecou_item.emit(chave, self._rotulos.get(chave, ""))
            try:
                resultado = self._fn(valor)
            except Exception as exc:
                traceback.print_exc()
                self.item_falhou.emit(chave, f"{type(exc).__name__}: {exc}")
            else:
                self.item_pronto.emit(chave, resultado)
        self.atual = None
        self.fila_terminou.emit()


class GerenciadorTrabalhos:
    """Segura referências dos trabalhadores vivos (evita GC no meio do voo).

    Todo gerenciador nasce registrado no módulo (weakref): o fechamento da
    janela principal chama ``encerrar_todos()`` e NENHUM worker fica vivo
    sem dono, seja de que tela/diálogo for (RG-05b — política global).
    """

    def __init__(self):
        self._vivos: list[Trabalhador] = []
        _GERENCIADORES.append(weakref.ref(self))

    def rodar(self, trab: Trabalhador) -> Trabalhador:
        self._vivos.append(trab)
        trab.finished.connect(lambda: self._vivos.remove(trab)
                              if trab in self._vivos else None)
        trab.start()
        return trab

    def encerrar(self, espera_ms: int = 2000) -> None:
        """Espera (com teto) os trabalhos vivos — chame ao FECHAR o dono.

        QThread destruída ainda rodando derruba o processo inteiro (crash
        nativo do Qt). Quem não terminar dentro do teto (ex.: uma chamada
        de IA em voo) vai para o porta-vidas do módulo: o objeto Python
        sobrevive ao dono até a thread acabar sozinha (os sinais para o
        dono morto se desconectam sós — o resultado é descartado).

        Janela sutil (achada por flake de bancada na Onda 4): sob carga, o
        ``start()`` pode ainda não ter virado thread NATIVA — e ``wait()``
        devolve True para thread não-iniciada, "encerrando" um worker que
        nasceria DEPOIS do shutdown. Por isso o início é esperado antes.
        """
        import time as _t
        for trab in list(self._vivos):
            prazo = _t.monotonic() + espera_ms / 1000.0
            while (not trab.isRunning() and not trab.isFinished()
                   and _t.monotonic() < prazo):
                _t.sleep(0.005)          # o start() ainda não virou thread
            restante_ms = max(1, int((prazo - _t.monotonic()) * 1000))
            trab.wait(restante_ms)
            if trab.isRunning() or not trab.isFinished():
                if trab in self._vivos:
                    self._vivos.remove(trab)
                _ORFAOS.append(trab)
                trab.finished.connect(
                    lambda t=trab: _ORFAOS.remove(t) if t in _ORFAOS else None)


# threads que sobreviveram ao teto do encerrar (ver docstring acima)
_ORFAOS: list[QThread] = []

# todos os gerenciadores vivos do processo (weakref — diálogo morto sai só)
_GERENCIADORES: list[weakref.ref] = []


def encerrar_todos(espera_ms: int = 2000) -> None:
    """RG-05b: o gancho GLOBAL de shutdown — chame ao fechar a janela
    principal. Percorre TODOS os gerenciadores vivos do processo (telas,
    diálogos, trabalhos de boot) e encerra cada um; quem estourar o teto
    vai para o porta-vidas ``_ORFAOS`` como sempre. Fila em andamento
    (``TrabalhadorFila``) é cancelada antes de esperar."""
    for ref in list(_GERENCIADORES):
        g = ref()
        if g is None:
            continue
        for trab in list(g._vivos):
            if isinstance(trab, TrabalhadorFila):
                trab.cancelar()
        g.encerrar(espera_ms)
    _GERENCIADORES[:] = [r for r in _GERENCIADORES if r() is not None]
