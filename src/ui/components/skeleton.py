"""
AutoTabloide AI - Skeleton Loading Components
==============================================
Implementação conforme Vol. VI, Cap. 8.1.

Componentes de skeleton loading para feedback visual durante carregamento.
Evita sensação de "travamento" ao carregar dados.
"""

import flet as ft
from typing import Optional


class SkeletonBox(ft.Container):
    """
    Box de skeleton básico.
    Pulsa suavemente para indicar carregamento.
    """
    
    def __init__(
        self,
        width: int = 100,
        height: int = 20,
        border_radius: int = 4,
        **kwargs
    ):
        super().__init__(
            width=width,
            height=height,
            border_radius=border_radius,
            bgcolor=ft.colors.with_opacity(0.1, ft.colors.WHITE),
            animate=ft.animation.Animation(800, ft.AnimationCurve.EASE_IN_OUT),
            **kwargs
        )


class SkeletonText(ft.Container):
    """
    Skeleton para texto - linha horizontal com altura variável.
    """
    
    def __init__(
        self,
        width: int = 200,
        height: int = 16,
        margin: int = 4,
        **kwargs
    ):
        super().__init__(
            width=width,
            height=height,
            border_radius=2,
            bgcolor=ft.colors.with_opacity(0.08, ft.colors.WHITE),
            margin=ft.margin.only(bottom=margin),
            **kwargs
        )


class SkeletonAvatar(ft.Container):
    """
    Skeleton circular para avatares/ícones.
    """
    
    def __init__(
        self,
        size: int = 40,
        **kwargs
    ):
        super().__init__(
            width=size,
            height=size,
            border_radius=size // 2,
            bgcolor=ft.colors.with_opacity(0.1, ft.colors.WHITE),
            **kwargs
        )


class SkeletonCard(ft.Container):
    """
    Skeleton para card de produto/item completo.
    Simula layout típico: imagem + título + descrição.
    """
    
    def __init__(
        self,
        width: int = 200,
        height: int = 280,
        **kwargs
    ):
        # Imagem placeholder
        image = SkeletonBox(
            width=width - 20,
            height=140,
            border_radius=8
        )
        
        # Título
        title = SkeletonText(width=width - 30, height=18)
        
        # Descrição (2 linhas)
        desc1 = SkeletonText(width=width - 30, height=14)
        desc2 = SkeletonText(width=width - 60, height=14)
        
        # Preço
        price = SkeletonBox(width=80, height=24, border_radius=4)
        
        super().__init__(
            width=width,
            height=height,
            border_radius=12,
            bgcolor=ft.colors.with_opacity(0.05, ft.colors.WHITE),
            padding=10,
            content=ft.Column([
                image,
                ft.Container(height=12),
                title,
                desc1,
                desc2,
                ft.Container(expand=True),
                price
            ], spacing=4),
            **kwargs
        )


class SkeletonTable(ft.Container):
    """
    Skeleton para tabela de dados.
    """
    
    def __init__(
        self,
        rows: int = 5,
        columns: int = 4,
        row_height: int = 48,
        **kwargs
    ):
        table_rows = []
        
        for _ in range(rows):
            row_cells = []
            for i in range(columns):
                width = 150 if i == 0 else 100  # Primeira coluna maior
                row_cells.append(
                    SkeletonText(width=width, height=16)
                )
            
            table_rows.append(
                ft.Container(
                    content=ft.Row(row_cells, spacing=20),
                    height=row_height,
                    border=ft.border.only(
                        bottom=ft.BorderSide(1, ft.colors.with_opacity(0.1, ft.colors.WHITE))
                    )
                )
            )
        
        super().__init__(
            content=ft.Column(table_rows, spacing=0),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            **kwargs
        )


class SkeletonGrid(ft.Container):
    """
    Grid de skeleton cards para galeria.
    """
    
    def __init__(
        self,
        items: int = 6,
        card_width: int = 200,
        card_height: int = 280,
        spacing: int = 16,
        **kwargs
    ):
        cards = [
            SkeletonCard(width=card_width, height=card_height)
            for _ in range(items)
        ]
        
        super().__init__(
            content=ft.GridView(
                controls=cards,
                runs_count=3,
                spacing=spacing,
                run_spacing=spacing,
                expand=True
            ),
            **kwargs
        )


class SkeletonLoader(ft.UserControl):
    """
    Wrapper que mostra skeleton enquanto carrega e depois exibe conteúdo real.
    
    Uso:
        loader = SkeletonLoader(
            skeleton=SkeletonTable(rows=5),
            content=meu_conteudo_real
        )
        
        # Após carregar dados:
        loader.show_content()
    """
    
    def __init__(
        self,
        skeleton: ft.Control,
        content: ft.Control = None,
        loading: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._skeleton = skeleton
        self._content = content or ft.Container()
        self._loading = loading
    
    @property
    def is_loading(self) -> bool:
        return self._loading
    
    def show_content(self):
        """Exibe o conteúdo real e oculta skeleton."""
        self._loading = False
        self.update()
    
    def show_skeleton(self):
        """Volta a exibir skeleton."""
        self._loading = True
        self.update()
    
    def set_content(self, content: ft.Control):
        """Define novo conteúdo."""
        self._content = content
        self.update()
    
    def build(self):
        return ft.AnimatedSwitcher(
            content=self._skeleton if self._loading else self._content,
            duration=300,
            transition=ft.AnimatedSwitcherTransition.FADE
        )


# =============================================================================
# FACTORY FUNCTIONS (atalhos convenientes)
# =============================================================================

def create_card_skeleton(count: int = 6) -> ft.Control:
    """Cria grid de card skeletons."""
    return SkeletonGrid(items=count)


def create_table_skeleton(rows: int = 5, cols: int = 4) -> ft.Control:
    """Cria skeleton de tabela."""
    return SkeletonTable(rows=rows, columns=cols)


def create_list_skeleton(items: int = 8) -> ft.Control:
    """Cria skeleton de lista."""
    rows = []
    for _ in range(items):
        rows.append(
            ft.Container(
                content=ft.Row([
                    SkeletonAvatar(size=40),
                    ft.Column([
                        SkeletonText(width=200, height=16),
                        SkeletonText(width=150, height=12),
                    ], spacing=4)
                ], spacing=12),
                height=60,
                padding=ft.padding.symmetric(horizontal=16, vertical=8)
            )
        )
    return ft.Column(rows, spacing=4)
