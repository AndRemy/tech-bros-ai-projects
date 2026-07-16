from __future__ import annotations

from urllib.parse import urlparse

from ..core.repository import ApartmentsRepository
from .apartments_repository import PostgresApartmentsRepository

_SCHEME_TO_REPOSITORY: dict[str, type[ApartmentsRepository]] = {
    "postgresql": PostgresApartmentsRepository,
    "postgres": PostgresApartmentsRepository,
}


def create_apartments_repository(database_url: str) -> ApartmentsRepository:
    """Puerto -> adaptador: decide qué implementación de ApartmentsRepository
    instanciar según el esquema de DATABASE_URL, sin que el llamador conozca
    las clases concretas."""
    scheme = urlparse(database_url).scheme.split("+")[0]  # postgresql+psycopg2 -> postgresql
    repository_cls = _SCHEME_TO_REPOSITORY.get(scheme)
    if repository_cls is None:
        disponibles = ", ".join(sorted(set(_SCHEME_TO_REPOSITORY)))
        raise ValueError(f"No hay un ApartmentsRepository para el esquema '{scheme}'. Disponibles: {disponibles}")
    return repository_cls(database_url)
