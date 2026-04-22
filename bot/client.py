import os
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
from bot.logging_config import logger


class BinanceFuturesClient:
    def __init__(self):
        self.base_url = "https://testnet.binancefuture.com"
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_API_SECRET")

        if not self.api_key or not self.api_secret:
            logger.error(
                "API credentials missing. Please check your .env file.")
            raise ValueError("Missing API Keys")

    def get_account_balance(self):
        return self.send_signed_request("GET", "/fapi/v2/balance", {})

    def get_price(self, symbol="BTCUSDT"):
        return self.send_signed_request("GET", "/fapi/v1/ticker/price", {"symbol": symbol.upper()})

    def get_klines(self, symbol="BTCUSDT", interval="1h", limit=24):
        return self.send_signed_request("GET", "/fapi/v1/klines", {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit
        })

    def _generate_signature(self, query_string: str) -> str:
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def send_signed_request(self, method: str, endpoint: str, payload: dict):
        payload['timestamp'] = int(time.time() * 1000)

        query_string = urlencode(payload)
        signature = self._generate_signature(query_string)

        url = f"{self.base_url}{endpoint}?{query_string}&signature={signature}"
        headers = {
            "X-MBX-APIKEY": self.api_key
        }

        logger.info(f"Sending {method} request to {endpoint}")

        try:
            if method == "POST":
                response = requests.post(url, headers=headers, timeout=10)
            else:
                response = requests.get(url, headers=headers, timeout=10)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as http_err:
            logger.error(
                f"API Error: {response.status_code} - {response.text}")
            return None
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Network/Request Error: {req_err}")
            return None
