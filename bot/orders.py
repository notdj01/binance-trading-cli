from bot.client import BinanceFuturesClient
from bot.logging_config import logger


def place_order(symbol: str, side: str, order_type: str, quantity: float, price: float = None):
    """Constructs the order payload and sends it via the client."""
    client = BinanceFuturesClient()
    endpoint = "/fapi/v1/order"

    payload = {
        "symbol": symbol.upper(),
        "side": side.upper(),
        "type": order_type.upper(),
        "quantity": quantity,
        "newOrderRespType": "RESULT"
    }

    if order_type.upper() == "LIMIT":
        payload["price"] = price
        payload["timeInForce"] = "GTC"

    logger.info(
        f"Attempting to place {order_type} order for {quantity} {symbol} ({side})")

    response = client.send_signed_request("POST", endpoint, payload)

    if response and 'orderId' in response:
        logger.info("Order successful!")
        logger.info(f"Order ID: {response['orderId']}")
        logger.info(f"Status: {response['status']}")
        logger.info(f"Executed Qty: {response.get('executedQty', '0')}")
        if response.get('avgPrice') and float(response.get('avgPrice')) > 0:
            logger.info(f"Average Price: {response['avgPrice']}")
    else:
        logger.error("Order failed. See logs above for details.")
