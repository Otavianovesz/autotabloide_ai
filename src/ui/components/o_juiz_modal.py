"""
AutoTabloide AI - Modal "O Juiz" (Fuzzy Match Conciliation)
============================================================
Implementação conforme Vol. VI, Cap. 4.2.

Modal de conciliação para matching fuzzy durante importação Excel.
Apresenta semáforo visual (Verde/Amarelo/Vermelho) e bloqueia até resolução.
"""

import flet as ft
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum


class MatchConfidence(Enum):
    """Níveis de confiança do match fuzzy."""
    HIGH = "high"      # >= 90% - Verde ✓ Auto-aceito
    MEDIUM = "medium"  # 70-89% - Amarelo ⚠ Revisão recomendada
    LOW = "low"        # < 70%  - Vermelho ✗ Ação obrigatória


@dataclass
class FuzzyMatchCandidate:
    """Candidato de match fuzzy."""
    id: int
    name: str
    score: float
    source: str = "database"
    metadata: Dict[str, Any] = None
    
    @property
    def confidence(self) -> MatchConfidence:
        if self.score >= 90:
            return MatchConfidence.HIGH
        elif self.score >= 70:
            return MatchConfidence.MEDIUM
        return MatchConfidence.LOW
    
    @property
    def semaphore_color(self) -> str:
        """Cor do semáforo baseada na confiança."""
        colors = {
            MatchConfidence.HIGH: "#34C759",    # Verde
            MatchConfidence.MEDIUM: "#FF9500",  # Amarelo/Laranja
            MatchConfidence.LOW: "#FF3B30"      # Vermelho
        }
        return colors[self.confidence]


@dataclass
class ConflictItem:
    """Item de conflito a ser resolvido."""
    excel_row: int
    excel_value: str
    candidates: List[FuzzyMatchCandidate]
    resolved: bool = False
    selected_candidate_id: Optional[int] = None
    is_new_entry: bool = False  # Se usuário decidiu criar novo


class OJuizModal(ft.AlertDialog):
    """
    Modal "O Juiz" - Conciliação de Matches Fuzzy.
    
    Apresenta conflitos de matching para resolução humana.
    Bloqueia progressão até que todos os conflitos sejam resolvidos.
    
    Vol. VI, Cap. 4.2:
    - Semáforo: Verde (auto-aceito), Amarelo (revisão), Vermelho (obrigatório)
    - Lista de pendências com contagem
    - Ações: Aceitar match, Criar novo, Ignorar linha
    """
    
    def __init__(
        self,
        conflicts: List[ConflictItem],
        on_resolve: Callable[[List[ConflictItem]], None] = None,
        on_cancel: Callable[[], None] = None,
        **kwargs
    ):
        self.conflicts = conflicts
        self.on_resolve = on_resolve
        self.on_cancel = on_cancel
        self.current_index = 0
        
        # Conta por tipo de confiança
        self._count_by_confidence = self._calculate_counts()
        
        super().__init__(
            modal=True,
            title=self._build_title(),
            content=self._build_content(),
            actions=[
                ft.Row([
                    ft.TextButton("Cancelar Importação", on_click=self._handle_cancel),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Criar Novo Produto",
                        icon=ft.icons.ADD,
                        on_click=self._handle_create_new,
                        color=ft.colors.WHITE,
                        bgcolor="#FF9500"
                    ),
                    ft.ElevatedButton(
                        "Aceitar Match",
                        icon=ft.icons.CHECK,
                        on_click=self._handle_accept,
                        color=ft.colors.WHITE,
                        bgcolor="#34C759"
                    )
                ], width=700)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            **kwargs
        )
    
    def _calculate_counts(self) -> Dict[MatchConfidence, int]:
        """Calcula contagem por nível de confiança."""
        counts = {c: 0 for c in MatchConfidence}
        for conflict in self.conflicts:
            if conflict.candidates:
                best = conflict.candidates[0]
                counts[best.confidence] += 1
        return counts
    
    def _build_title(self) -> ft.Control:
        """Constrói título com semáforo resumo."""
        pending = len([c for c in self.conflicts if not c.resolved])
        
        return ft.Row([
            ft.Icon(ft.icons.GAVEL, size=28, color="#FF9500"),
            ft.Text("O Juiz", size=22, weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            # Sumário semafórico
            self._semaphore_badge(MatchConfidence.HIGH, self._count_by_confidence[MatchConfidence.HIGH]),
            self._semaphore_badge(MatchConfidence.MEDIUM, self._count_by_confidence[MatchConfidence.MEDIUM]),
            self._semaphore_badge(MatchConfidence.LOW, self._count_by_confidence[MatchConfidence.LOW]),
            ft.Container(width=20),
            ft.Text(f"Pendentes: {pending}/{len(self.conflicts)}", size=14, color=ft.colors.GREY_400)
        ])
    
    def _semaphore_badge(self, confidence: MatchConfidence, count: int) -> ft.Container:
        """Badge circular colorida com contagem."""
        colors = {
            MatchConfidence.HIGH: "#34C759",
            MatchConfidence.MEDIUM: "#FF9500",
            MatchConfidence.LOW: "#FF3B30"
        }
        return ft.Container(
            content=ft.Text(str(count), size=12, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
            width=28,
            height=28,
            border_radius=14,
            bgcolor=colors[confidence],
            alignment=ft.alignment.center
        )
    
    def _build_content(self) -> ft.Control:
        """Constrói conteúdo principal do modal."""
        if not self.conflicts:
            return ft.Text("Nenhum conflito a resolver!", size=16)
        
        conflict = self.conflicts[self.current_index]
        
        return ft.Container(
            width=800,
            height=450,
            content=ft.Column([
                # Navegação entre conflitos
                self._build_navigation_bar(),
                ft.Divider(height=1),
                
                # Valor do Excel
                self._build_excel_section(conflict),
                
                # Lista de candidatos
                ft.Text("Candidatos Encontrados:", size=14, weight=ft.FontWeight.BOLD),
                self._build_candidates_list(conflict),
                
            ], spacing=12, scroll=ft.ScrollMode.AUTO)
        )
    
    def _build_navigation_bar(self) -> ft.Control:
        """Barra de navegação entre conflitos."""
        return ft.Row([
            ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self._nav_prev,
                disabled=self.current_index == 0
            ),
            ft.Text(
                f"Conflito {self.current_index + 1} de {len(self.conflicts)}",
                size=14
            ),
            ft.IconButton(
                icon=ft.icons.ARROW_FORWARD,
                on_click=self._nav_next,
                disabled=self.current_index >= len(self.conflicts) - 1
            ),
            ft.Container(expand=True),
            # Status do conflito atual
            self._conflict_status_badge(self.conflicts[self.current_index])
        ])
    
    def _conflict_status_badge(self, conflict: ConflictItem) -> ft.Container:
        """Badge de status do conflito."""
        if conflict.resolved:
            return ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.CHECK_CIRCLE, color="#34C759", size=16),
                    ft.Text("Resolvido", color="#34C759", size=12)
                ], spacing=4),
                padding=ft.padding.symmetric(horizontal=12, vertical=4),
                border_radius=12,
                bgcolor=ft.colors.with_opacity(0.15, "#34C759")
            )
        else:
            if conflict.candidates and conflict.candidates[0].confidence == MatchConfidence.LOW:
                return ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.WARNING, color="#FF3B30", size=16),
                        ft.Text("Ação Obrigatória", color="#FF3B30", size=12)
                    ], spacing=4),
                    padding=ft.padding.symmetric(horizontal=12, vertical=4),
                    border_radius=12,
                    bgcolor=ft.colors.with_opacity(0.15, "#FF3B30")
                )
            return ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.PENDING, color="#FF9500", size=16),
                    ft.Text("Pendente", color="#FF9500", size=12)
                ], spacing=4),
                padding=ft.padding.symmetric(horizontal=12, vertical=4),
                border_radius=12,
                bgcolor=ft.colors.with_opacity(0.15, "#FF9500")
            )
    
    def _build_excel_section(self, conflict: ConflictItem) -> ft.Control:
        """Seção com valor original do Excel."""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.TABLE_CHART, size=18, color="#007AFF"),
                    ft.Text(f"Linha {conflict.excel_row} do Excel:", size=14),
                ], spacing=8),
                ft.Container(
                    content=ft.Text(
                        conflict.excel_value,
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        selectable=True
                    ),
                    padding=ft.padding.all(16),
                    bgcolor=ft.colors.with_opacity(0.1, ft.colors.BLUE),
                    border_radius=8,
                    border=ft.border.all(1, ft.colors.BLUE_700)
                )
            ], spacing=8),
            margin=ft.margin.only(bottom=12)
        )
    
    def _build_candidates_list(self, conflict: ConflictItem) -> ft.Control:
        """Lista de candidatos com radio buttons."""
        if not conflict.candidates:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.SEARCH_OFF, size=48, color=ft.colors.GREY_500),
                    ft.Text("Nenhum candidato encontrado", color=ft.colors.GREY_500)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                height=150,
                alignment=ft.alignment.center
            )
        
        # Radio group para seleção
        selected_id = conflict.selected_candidate_id or (
            conflict.candidates[0].id if conflict.candidates else None
        )
        
        items = []
        for candidate in conflict.candidates:
            is_selected = candidate.id == selected_id
            
            item = ft.Container(
                content=ft.Row([
                    # Semáforo
                    ft.Container(
                        width=12,
                        height=12,
                        border_radius=6,
                        bgcolor=candidate.semaphore_color
                    ),
                    # Score
                    ft.Text(
                        f"{candidate.score:.0f}%",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=candidate.semaphore_color,
                        width=50
                    ),
                    # Nome
                    ft.Text(
                        candidate.name,
                        size=14,
                        weight=ft.FontWeight.W_500 if is_selected else ft.FontWeight.NORMAL,
                        expand=True
                    ),
                    # Fonte
                    ft.Text(
                        candidate.source,
                        size=12,
                        color=ft.colors.GREY_500
                    ),
                    # Checkbox de seleção
                    ft.Radio(
                        value=str(candidate.id),
                        label="",
                    )
                ], spacing=12),
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                bgcolor=ft.colors.with_opacity(0.1, candidate.semaphore_color) if is_selected else None,
                border_radius=8,
                on_click=lambda e, cid=candidate.id: self._select_candidate(cid)
            )
            items.append(item)
        
        return ft.Container(
            content=ft.RadioGroup(
                value=str(selected_id) if selected_id else None,
                on_change=lambda e: self._select_candidate(int(e.data)),
                content=ft.Column(items, spacing=4)
            ),
            height=200,
            padding=ft.padding.only(right=8)
        )
    
    def _select_candidate(self, candidate_id: int):
        """Seleciona um candidato."""
        conflict = self.conflicts[self.current_index]
        conflict.selected_candidate_id = candidate_id
        conflict.is_new_entry = False
        self._update_content()
    
    def _nav_prev(self, e):
        """Navega para conflito anterior."""
        if self.current_index > 0:
            self.current_index -= 1
            self._update_content()
    
    def _nav_next(self, e):
        """Navega para próximo conflito."""
        if self.current_index < len(self.conflicts) - 1:
            self.current_index += 1
            self._update_content()
    
    def _update_content(self):
        """Atualiza conteúdo do modal."""
        self.title = self._build_title()
        self.content = self._build_content()
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def _handle_accept(self, e):
        """Aceita o match selecionado."""
        conflict = self.conflicts[self.current_index]
        
        if not conflict.selected_candidate_id and conflict.candidates:
            # Se nada selecionado, usa o primeiro
            conflict.selected_candidate_id = conflict.candidates[0].id
        
        conflict.resolved = True
        
        # Avança para próximo não resolvido ou finaliza
        self._advance_or_finish()
    
    def _handle_create_new(self, e):
        """Marca para criar novo produto."""
        conflict = self.conflicts[self.current_index]
        conflict.is_new_entry = True
        conflict.selected_candidate_id = None
        conflict.resolved = True
        
        self._advance_or_finish()
    
    def _advance_or_finish(self):
        """Avança para próximo conflito ou finaliza."""
        # Procura próximo não resolvido
        for i, conflict in enumerate(self.conflicts):
            if not conflict.resolved:
                self.current_index = i
                self._update_content()
                return
        
        # Todos resolvidos - finaliza
        if self.on_resolve:
            self.on_resolve(self.conflicts)
        
        self.open = False
        if hasattr(self, 'page') and self.page:
            self.page.update()
    
    def _handle_cancel(self, e):
        """Cancela toda a importação."""
        if self.on_cancel:
            self.on_cancel()
        
        self.open = False
        if hasattr(self, 'page') and self.page:
            self.page.update()


def show_juiz_modal(
    page: ft.Page,
    conflicts: List[ConflictItem],
    on_resolve: Callable[[List[ConflictItem]], None] = None,
    on_cancel: Callable[[], None] = None
) -> OJuizModal:
    """
    Exibe o modal O Juiz.
    
    Args:
        page: Página Flet
        conflicts: Lista de conflitos a resolver
        on_resolve: Callback quando todos conflitos resolvidos
        on_cancel: Callback quando usuário cancela
    
    Returns:
        Instância do modal
    """
    modal = OJuizModal(
        conflicts=conflicts,
        on_resolve=on_resolve,
        on_cancel=on_cancel
    )
    
    page.dialog = modal
    modal.open = True
    page.update()
    
    return modal
