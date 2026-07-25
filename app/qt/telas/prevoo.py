"""
Pré-voo de exportação (P0.4 / invariante I2)
============================================
Antes de exportar ou salvar projeto: mostra as pendências por célula e deixa
a escolha consciente com o usuário — "seguir mesmo assim" nunca é o padrão.
"""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


def confirmar_pre_voo(parent: QWidget, avisos: list[str],
                      acao: str = "Exportar") -> bool:
    """True = seguir. Sem avisos, segue direto; com avisos, pergunta."""
    if not avisos:
        return True
    caixa = QMessageBox(parent)
    caixa.setWindowTitle(f"Pré-voo — {len(avisos)} pendência(s)")
    caixa.setIcon(QMessageBox.Icon.Warning)
    caixa.setText(f"Encontrei {len(avisos)} pendência(s) antes de "
                  f"{acao.lower()}:")
    caixa.setInformativeText("\n".join(f"• {a}" for a in avisos[:12])
                             + ("\n…" if len(avisos) > 12 else ""))
    seguir = caixa.addButton(f"{acao} mesmo assim",
                             QMessageBox.ButtonRole.AcceptRole)
    cancelar = caixa.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
    # F13/B3 (CF-01): o docstring do módulo sempre prometeu que "seguir
    # mesmo assim" nunca é o padrão — agora o código DECLARA isso: Enter
    # e Esc caem no Cancelar (parar e ler é o caminho de menor energia).
    caixa.setDefaultButton(cancelar)
    caixa.setEscapeButton(cancelar)
    caixa.exec()
    return caixa.clickedButton() is seguir
