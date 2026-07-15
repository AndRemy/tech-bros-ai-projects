from __future__ import annotations

from abc import ABC, abstractmethod

from .models import ApartmentResult, SearchFilters


class ApartmentsRepository(ABC):
    """Puerto de acceso a los departamentos disponibles. La implementación
    concreta es la única pieza que sabe qué motor de base de datos hay detrás."""

    @abstractmethod
    def search(self, filters: SearchFilters, offset: int, limit: int) -> tuple[list[ApartmentResult], bool]:
        """Devuelve (resultados_de_esta_pagina, hay_mas_paginas)."""
