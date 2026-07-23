from __future__ import annotations

from .models import ApartmentResult, RankedResult, SearchFilters
from .text_utils import strip_accents

# ---------------------------------------------------------------------------
# Plantilla del mensaje de resultados. Todo el formato vive en este archivo:
# cambiar el look (emojis, orden de campos, separadores, textos) es editar aquí,
# sin tocar el pipeline ni los proveedores de LLM. El LLM solo aporta la lista de
# características por departamento (bot/core/features.py); el resto es determinista.
# ---------------------------------------------------------------------------

NO_RESULTS_MESSAGE = (
    "No encontramos departamentos que coincidan con esos criterios. "
    "¿Quieres ajustar el rango de precio o la zona?"
)

_SEP = "━" * 14
_NUMBER_EMOJI = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

# Palabra clave (sin tildes, minúscula) -> emoji, evaluadas en orden: la primera
# que aparezca como substring de la característica define el emoji.
_FEATURE_EMOJI: list[tuple[str, str]] = [
    ("piscina", "🏊"),
    ("parrilla", "🍖"),
    ("estacionamiento", "🚗"),
    ("cochera", "🚗"),
    ("garaje", "🚗"),
    ("gimnasio", "🏋️"),
    ("gym", "🏋️"),
    ("amoblado", "🛋️"),
    ("ascensor", "🛗"),
    ("vista al mar", "🌊"),
    ("vista", "🌇"),
    ("balcon", "🪟"),
    ("terraza", "🌿"),
    ("jardin", "🌳"),
    ("estreno", "✨"),
    ("nuevo", "✨"),
    ("remodelado", "🔨"),
    ("seguridad", "🛡️"),
    ("vigilancia", "🛡️"),
    ("mascota", "🐾"),
    ("pet", "🐾"),
    ("lavanderia", "🧺"),
    ("deposito", "📦"),
    ("piso", "🏢"),
]
_DEFAULT_FEATURE_EMOJI = "✅"

_CONNECTORES = {"de", "del", "la", "las", "los", "y", "o", "en"}

# Sinónimos frecuentes -> forma canónica, solo para deduplicar (ej. si una fila
# trae "Estacionamiento" en amenities y el LLM extrae "Cochera" de la descripción,
# no queremos mostrar ambos). No cambia el texto que se muestra, solo la clave.
_SINONIMOS = {"cochera": "estacionamiento", "garaje": "estacionamiento"}


def _dedup_key(label: str) -> str:
    clave = strip_accents(label).lower().strip()
    return _SINONIMOS.get(clave, clave)


def _titlecase(texto: str) -> str:
    palabras = texto.split()
    return " ".join(
        p if (i > 0 and p.lower() in _CONNECTORES) else p.capitalize() for i, p in enumerate(palabras)
    )


def _emoji_for(feature: str) -> str:
    normal = strip_accents(feature).lower()
    for clave, emoji in _FEATURE_EMOJI:
        if clave in normal:
            return emoji
    return _DEFAULT_FEATURE_EMOJI


def _format_price(precio: float) -> str:
    return f"S/ {precio:,.0f}"


def _price_line(apartment: ApartmentResult) -> str:
    precio = _format_price(apartment.precio)
    if (apartment.operacion or "").lower() == "alquiler":
        return f"💰 {precio}/mes"
    return f"💰 {precio}"


def _area(area_m2: float) -> str:
    return f"{area_m2:g}"


def _specs_line(a: ApartmentResult) -> str:
    banos = "baño" if a.banos == 1 else "baños"
    return f"🛏️ {a.habitaciones} hab | 🚿 {a.banos} {banos} | 📐 {_area(a.area_m2)} m²"


def _merged_features(apartment: ApartmentResult, extracted: list[str]) -> list[str]:
    """amenities estructurado (base garantizada) + características extraídas de la
    descripción, deduplicando sin distinguir tildes/mayúsculas y con tope de 6."""
    salida: list[str] = []
    vistos: set[str] = set()
    for label in [*apartment.amenities, *extracted]:
        clave = _dedup_key(label)
        if clave and clave not in vistos:
            vistos.add(clave)
            salida.append(label.strip())
        if len(salida) >= 6:
            break
    return salida


def _result_block(index: int, apartment: ApartmentResult, extracted: list[str]) -> str:
    numero = _NUMBER_EMOJI[index] if index < len(_NUMBER_EMOJI) else f"{index + 1}."
    lineas = [
        f"{numero} {apartment.zona}",
        _price_line(apartment),
        _specs_line(apartment),
    ]
    lineas += [f"{_emoji_for(f)} {f}" for f in _merged_features(apartment, extracted)]
    if apartment.url:
        lineas.append(f"🔗 [Ver publicación]({apartment.url})")
    return "\n".join(lineas)


def _buscabas_block(filters: SearchFilters) -> str | None:
    lineas: list[str] = []
    if filters.zonas:
        lineas.append("• " + " o ".join(_titlecase(z) for z in filters.zonas))
    if filters.operacion:
        lineas.append(f"• En {filters.operacion.lower()}")
    if filters.tipo:
        lineas.append(f"• {filters.tipo.capitalize()}")
    if filters.habitaciones:
        unidad = "habitación" if filters.habitaciones == 1 else "habitaciones"
        lineas.append(f"• {filters.habitaciones} {unidad}")
    if filters.banos:
        unidad = "baño" if filters.banos == 1 else "baños"
        lineas.append(f"• {filters.banos} {unidad}")
    if filters.precio_min is not None and filters.precio_max is not None:
        lineas.append(f"• Entre {_format_price(filters.precio_min)} y {_format_price(filters.precio_max)}")
    elif filters.precio_max is not None:
        lineas.append(f"• Hasta {_format_price(filters.precio_max)}")
    elif filters.precio_min is not None:
        lineas.append(f"• Desde {_format_price(filters.precio_min)}")
    if filters.area_min_m2 is not None:
        lineas.append(f"• Desde {_area(filters.area_min_m2)} m²")
    if filters.direccion:
        lineas.append(f"• Cerca de: {filters.direccion}")
    if not lineas:
        return None
    return "📍 Buscabas:\n" + "\n".join(lineas)


def _noun(tipo: str | None, n: int) -> str:
    base = {"departamento": "departamento", "casa": "casa"}.get((tipo or "").lower(), "inmueble")
    return base if n == 1 else base + "s"


def format_search_results(
    filters: SearchFilters,
    results: list[RankedResult],
    features: list[list[str]],
    has_more: bool,
) -> str:
    """Arma el mensaje final de forma 100% determinista a partir de los campos
    estructurados de cada resultado y de las características ya extraídas por el
    FeatureExtractor. `features` está alineado por índice con `results`."""
    if not results:
        return NO_RESULTS_MESSAGE

    n = len(results)
    partes = [f"🏠 Encontré {n} {_noun(filters.tipo, n)} que coinciden con tu búsqueda"]

    buscabas = _buscabas_block(filters)
    if buscabas:
        partes.append(buscabas)

    for i, ranked in enumerate(results):
        extracted = features[i] if i < len(features) else []
        partes.append(_SEP)
        partes.append(_result_block(i, ranked.apartment, extracted))

    if has_more:
        partes.append(_SEP)
        partes.append('➡️ Escribe "más" para ver la siguiente página.')

    return "\n".join(partes)
