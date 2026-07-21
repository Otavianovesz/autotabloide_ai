"""
Histórico de edição (F5.10 + D5 da ORDEM_F5_6 + B3 do Bloco E) — desfazer/refazer
=================================================================================
Snapshots de **{layout, mapa, overrides}** como estado ÚNICO (D5: o mapa
slot→uid muda fora do auto-preencher — desfazer a remoção de uma célula
restaura o slot E a entrada do mapa juntos; B3/F7.3: o override de conteúdo
por slot também volta junto — desfazer um override restaura o anterior).
Gravados em disco (pasta temporária da sessão) — histórico generoso sem
pesar a RAM.

Semântica clássica: registrar após cada mutação; desfazer volta um estado;
registrar depois de desfazer **corta o futuro** (o refazer descartado).
Estados idênticos consecutivos não duplicam (edições que não mudaram nada).
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from app.rendering.model import LayoutDef


class Historico:
    def __init__(self, limite: int = 300):
        self.limite = limite
        self._dir = Path(tempfile.mkdtemp(prefix="atb_historico_"))
        self._pilha: list[Path] = []   # estados na ordem; _idx aponta o atual
        self._idx = -1
        self._contador = 0

    # --- registrar -------------------------------------------------------------

    def registrar(self, layout: LayoutDef, mapa: dict | None = None,
                  overrides: dict | None = None) -> None:
        estado = json.dumps({"layout": layout.to_dict(),
                             "mapa": dict(mapa or {}),
                             "overrides": dict(overrides or {})},
                            ensure_ascii=False)
        if self._idx >= 0 and self._ler(self._pilha[self._idx]) == estado:
            return                                  # nada mudou — não duplica
        # desfez e editou → o "futuro" morre
        for arq in self._pilha[self._idx + 1:]:
            arq.unlink(missing_ok=True)
        self._pilha = self._pilha[: self._idx + 1]

        self._contador += 1
        arquivo = self._dir / f"{self._contador:06d}.json"
        arquivo.write_text(estado, encoding="utf-8")
        self._pilha.append(arquivo)
        self._idx = len(self._pilha) - 1

        # limite generoso: cai o estado mais antigo
        while len(self._pilha) > self.limite:
            self._pilha.pop(0).unlink(missing_ok=True)
            self._idx -= 1

    # --- navegar ---------------------------------------------------------------

    def pode_desfazer(self) -> bool:
        return self._idx > 0

    def pode_refazer(self) -> bool:
        return self._idx < len(self._pilha) - 1

    def desfazer(self) -> tuple[LayoutDef, dict, dict] | None:
        if not self.pode_desfazer():
            return None
        self._idx -= 1
        return self._carregar(self._pilha[self._idx])

    def refazer(self) -> tuple[LayoutDef, dict, dict] | None:
        if not self.pode_refazer():
            return None
        self._idx += 1
        return self._carregar(self._pilha[self._idx])

    # --- histórico VISUAL (R-042): pular para um estado qualquer ---------------

    def total(self) -> int:
        return len(self._pilha)

    def indice(self) -> int:
        return self._idx

    def ir_para(self, i: int) -> tuple[LayoutDef, dict, dict] | None:
        """Salta direto para o estado ``i`` (clicar numa miniatura do histórico
        visual). Não corta o futuro — é navegação, como desfazer/refazer."""
        if not (0 <= i < len(self._pilha)) or i == self._idx:
            return None
        self._idx = i
        return self._carregar(self._pilha[self._idx])

    def estado_em(self, i: int) -> tuple[LayoutDef, dict, dict] | None:
        """Lê o estado ``i`` SEM mover o cursor (para compor a miniatura)."""
        if not (0 <= i < len(self._pilha)):
            return None
        return self._carregar(self._pilha[i])

    # --- interno ---------------------------------------------------------------

    @staticmethod
    def _ler(arquivo: Path) -> str:
        return arquivo.read_text(encoding="utf-8")

    def _carregar(self, arquivo: Path) -> tuple[LayoutDef, dict, dict]:
        d = json.loads(self._ler(arquivo))
        return (LayoutDef.from_dict(d["layout"]), d.get("mapa", {}),
                d.get("overrides", {}))

    def limpar(self) -> None:
        shutil.rmtree(self._dir, ignore_errors=True)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._pilha = []
        self._idx = -1
