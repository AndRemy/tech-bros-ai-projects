from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class SortOption(str, Enum):
    RELEVANCE = "relevance"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    NEWEST_FIRST = "newest_first"
    OLDEST_FIRST = "oldest_first"


class SearchFilters(BaseModel):
    zona: str | None = None
    operacion: str | None = None  # "alquiler" | "venta"
    tipo: str | None = None  # "departamento" | "casa"
    precio_min: float | None = None
    precio_max: float | None = None
    habitaciones: int | None = None
    banos: int | None = None
    area_min_m2: float | None = None
    amenities: list[str] = []
    sort: SortOption = SortOption.RELEVANCE


class ApartmentResult(BaseModel):
    id: str
    zona: str
    precio: float
    habitaciones: int
    banos: int
    area_m2: float
    amenities: list[str] = []
    fecha_publicacion: datetime
    descripcion: str
    url: str | None = None  # NULL en ~98% de las filas cargadas por los loaders manuales (load_*.py)
    operacion: str | None = None  # "alquiler" | "venta"
    tipo: str | None = None  # "departamento" | "casa"


class RankedResult(BaseModel):
    apartment: ApartmentResult
    relevance_score: float


class ResultPage(BaseModel):
    items: list[RankedResult]
    offset: int
    page_size: int
    has_more: bool
