from bdis.core.config import settings

def get_fx_rate(currency: str) -> float:
    """
    Returns the exchange rate to normalize the given currency to the BASE_CURRENCY (USD).
    """
    if not currency:
        return 1.0
    return settings.FIXED_FX_RATES.get(currency.upper(), 1.0)

def convert_to_usd(amount: float, currency: str) -> float:
    """
    Normalizes a monetary amount to USD using centralized FX rates.
    """
    rate = get_fx_rate(currency)
    return amount * rate

def format_currency(amount: float, currency: str) -> str:
    """
    Standardized formatting for currency display.
    """
    return f"{currency.upper()} {amount:,.2f}"
