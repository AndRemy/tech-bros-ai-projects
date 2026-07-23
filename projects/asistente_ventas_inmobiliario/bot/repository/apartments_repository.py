from __future__ import annotations

from sqlalchemy import MetaData, Table, and_, create_engine, or_, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import SQLAlchemyError

from ..core.exceptions import DatabaseUnavailableError
from ..core.models import ApartmentResult, SearchFilters
from ..core.repository import ApartmentsRepository
from ..core.text_utils import strip_accents

# Schema confirmado contra la base Postgres (Neon) real: tabla `apartments` con
# id, zona, precio, habitaciones, banos, area_m2, amenities, fecha_publicacion,
# descripcion, url, operacion, tipo.
_TABLE_NAME = "apartments"


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class PostgresApartmentsRepository(ApartmentsRepository):
    def __init__(self, database_url: str) -> None:
        try:
            self._engine = create_engine(database_url)
            self._metadata = MetaData()
            self._table = Table(_TABLE_NAME, self._metadata, autoload_with=self._engine)
        except SQLAlchemyError as exc:
            raise DatabaseUnavailableError(str(exc)) from exc

    def search(self, filters: SearchFilters, offset: int, limit: int) -> tuple[list[ApartmentResult], bool]:
        conditions = []
        if filters.zonas:
            # ilike con comodines (case/tilde-insensitive) porque el NLU suele
            # extraer la forma coloquial que usó el usuario, no el nombre
            # completo tal como está en la base — ej. "Surco" en vez de
            # "Santiago de Surco" (con igualdad exacta, cero resultados aunque
            # sí había datos). OR entre zonas: el usuario puede pedir varias
            # alternativas ("Barranco o San Isidro"), cualquiera es un match válido.
            conditions.append(
                or_(*(self._table.c.zona.ilike(f"%{_escape_like(strip_accents(z))}%", escape="\\") for z in filters.zonas))
            )
        # operacion/tipo son columnas opcionales; se filtran solo si existen en la tabla.
        if filters.operacion and "operacion" in self._table.c:
            conditions.append(self._table.c.operacion.ilike(filters.operacion))
        if filters.tipo and "tipo" in self._table.c:
            conditions.append(self._table.c.tipo.ilike(filters.tipo))
        if filters.precio_min is not None:
            conditions.append(self._table.c.precio >= filters.precio_min)
        if filters.precio_max is not None:
            conditions.append(self._table.c.precio <= filters.precio_max)
        if filters.habitaciones is not None:
            conditions.append(self._table.c.habitaciones == filters.habitaciones)
        if filters.banos is not None:
            conditions.append(self._table.c.banos == filters.banos)
        if filters.area_min_m2 is not None:
            conditions.append(self._table.c.area_m2 >= filters.area_min_m2)
        if filters.direccion:
            # No hay columna de dirección; se busca como substring dentro de
            # descripcion, donde el scraper suele incluir la calle/avenida.
            escaped = _escape_like(strip_accents(filters.direccion))
            conditions.append(self._table.c.descripcion.ilike(f"%{escaped}%", escape="\\"))

        # Se pide un resultado extra (limit + 1) para saber si hay página
        # siguiente sin hacer un COUNT(*) aparte.
        stmt = select(self._table)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.offset(offset).limit(limit + 1)

        try:
            with self._engine.connect() as conn:
                rows = conn.execute(stmt).mappings().all()
        except SQLAlchemyError as exc:
            raise DatabaseUnavailableError(str(exc)) from exc

        has_more = len(rows) > limit
        results = [self._row_to_apartment(row) for row in rows[:limit]]
        return results, has_more

    @staticmethod
    def _row_to_apartment(row: RowMapping) -> ApartmentResult:
        amenities_raw = row.get("amenities") or ""
        amenities = [a.strip() for a in amenities_raw.split(",") if a.strip()]
        return ApartmentResult(
            id=str(row["id"]),
            zona=row["zona"],
            precio=row["precio"],
            habitaciones=row["habitaciones"],
            banos=row["banos"],
            area_m2=row["area_m2"],
            amenities=amenities,
            fecha_publicacion=row["fecha_publicacion"],
            descripcion=row["descripcion"],
            url=row["url"],
            operacion=row.get("operacion"),
            tipo=row.get("tipo"),
        )
