from bot.logging_config import logger


def get_order_validation_error(symbol: str, side: str, order_type: str, quantity: float, price: float = None):
    """Returns a human-readable validation error, or None if the order is valid."""

    if side.upper() not in ["BUY", "SELL"]:
        return f"Invalid side '{side}'. Must be BUY or SELL."

    if order_type.upper() not in ["MARKET", "LIMIT"]:
        return f"Invalid order type '{order_type}'. Must be MARKET or LIMIT."

    if quantity <= 0:
        return "Quantity must be greater than 0."

    if order_type.upper() == "LIMIT" and (price is None or price <= 0):
        return "LIMIT orders require a price greater than 0."

    return None


def validate_order_inputs(symbol: str, side: str, order_type: str, quantity: float, price: float = None):
    """Validates user inputs before hitting the API."""
    error = get_order_validation_error(
        symbol, side, order_type, quantity, price)
    if error:
        logger.error(f"Validation Error: {error}")
        return False
    return True
