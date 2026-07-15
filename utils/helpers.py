from typing import Dict, Any, Optional

def calculate_price_m2(price_usd: float, area_m2: float) -> float:
    """Calculates the price per square meter in USD."""
    if area_m2 <= 0:
        return 0.0
    return round(price_usd / area_m2, 2)

def compare_to_average(price_m2: float, avg_price_m2: float) -> Dict[str, Any]:
    """
    Compares a property's price per square meter with the district average.
    Returns deviation percentage and evaluation category.
    """
    if avg_price_m2 <= 0:
        return {
            "deviation_pct": 0.0,
            "evaluation": "Desconocido (sin datos históricos)",
            "color": "gray"
        }
    
    deviation_pct = round(((price_m2 - avg_price_m2) / avg_price_m2) * 100, 2)
    
    if deviation_pct <= -10.0:
        evaluation = "Subvalorado (¡Gran Oportunidad!)"
        color = "green"
    elif deviation_pct <= -3.0:
        evaluation = "Buen precio (Ligera oportunidad)"
        color = "light-green"
    elif deviation_pct <= 5.0:
        evaluation = "Precio de mercado"
        color = "blue"
    elif deviation_pct <= 15.0:
        evaluation = "Sobrevalorado"
        color = "orange"
    else:
        evaluation = "Muy sobrevalorado"
        color = "red"
        
    return {
        "deviation_pct": deviation_pct,
        "evaluation": evaluation,
        "color": color
    }

def format_currency(amount: float, currency: str = "USD") -> str:
    """Formats an amount into a readable currency string."""
    if currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "PEN":
        return f"S/. {amount:,.2f}"
    return f"{amount:,.2f} {currency}"
