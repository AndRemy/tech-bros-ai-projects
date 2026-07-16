from __future__ import annotations

from .models import ApartmentResult, RankedResult, SearchFilters, SortOption


def _relevance_score(apartment: ApartmentResult, filters: SearchFilters) -> float:
    """Cuenta cuántos criterios pedidos por el usuario coincide este departamento.
    Aproximación determinista de "qué tanto se acomoda a la descripción" sin
    necesitar búsqueda semántica/embeddings sobre la base SQLite actual."""
    score = 0.0
    if filters.zona and filters.zona.lower() == apartment.zona.lower():
        score += 1
    if filters.operacion and filters.operacion == apartment.operacion:
        score += 1
    if filters.tipo and filters.tipo == apartment.tipo:
        score += 1
    if filters.precio_max is not None and apartment.precio <= filters.precio_max:
        score += 1
    if filters.precio_min is not None and apartment.precio >= filters.precio_min:
        score += 1
    if filters.habitaciones is not None and apartment.habitaciones == filters.habitaciones:
        score += 1
    if filters.banos is not None and apartment.banos == filters.banos:
        score += 1
    if filters.area_min_m2 is not None and apartment.area_m2 >= filters.area_min_m2:
        score += 1
    if filters.amenities:
        matched = {a.lower() for a in filters.amenities} & {a.lower() for a in apartment.amenities}
        score += len(matched)
    return score


def rank(apartments: list[ApartmentResult], filters: SearchFilters) -> list[RankedResult]:
    ranked = [RankedResult(apartment=a, relevance_score=_relevance_score(a, filters)) for a in apartments]

    if filters.sort == SortOption.PRICE_ASC:
        ranked.sort(key=lambda r: r.apartment.precio)
    elif filters.sort == SortOption.PRICE_DESC:
        ranked.sort(key=lambda r: r.apartment.precio, reverse=True)
    elif filters.sort == SortOption.OLDEST_FIRST:
        ranked.sort(key=lambda r: r.apartment.fecha_publicacion)
    elif filters.sort == SortOption.NEWEST_FIRST:
        ranked.sort(key=lambda r: r.apartment.fecha_publicacion, reverse=True)
    else:
        # Por defecto: relevancia a la descripción y, como desempate,
        # fecha de publicación descendente (más recientes primero).
        ranked.sort(key=lambda r: (r.relevance_score, r.apartment.fecha_publicacion), reverse=True)

    return ranked
