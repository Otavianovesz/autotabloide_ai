"""Init for widgets package."""
from .dashboard import DashboardWidget, StatCard
from .estoque import EstoqueWidget, ProductTableModel
from .atelier import AtelierWidget, LayoutCanvas, ProductShelf
from .factory import FactoryWidget
from .settings import SettingsWidget
from .cofre import CofreWidget

__all__ = [
    "DashboardWidget", "StatCard",
    "EstoqueWidget", "ProductTableModel", 
    "AtelierWidget", "LayoutCanvas", "ProductShelf",
    "FactoryWidget",
    "SettingsWidget",
    "CofreWidget",
]
