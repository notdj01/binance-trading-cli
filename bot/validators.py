from bot.logging_config import logger


def validate_order_inputs(symbol: str, side: str, order_type: str, quantity: float, price: float = None):
    """Validates user inputs before hitting the API."""

    if side.upper() not in ["BUY", "SELL"]:
        logger.error(
            f"Validation Error: Invalid side '{side}'. Must be BUY or SELL.")
        return False

    if order_type.upper() not in ["MARKET", "LIMIT"]:
        logger.error(
            f"Validation Error: Invalid order type '{order_type}'. Must be MARKET or LIMIT.")
        return False

    if quantity <= 0:
        logger.error("Validation Error: Quantity must be greater than 0.")
        return False

    if order_type.upper() == "LIMIT" and (price is None or price <= 0):
        logger.error(
            "Validation Error: LIMIT orders require a price greater than 0.")
        return False

    return True
