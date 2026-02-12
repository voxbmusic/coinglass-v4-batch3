import json
import time
import urllib.parse
import urllib.request


class BinancePublicAPI:
    def __init__(self, base_url: str = "https://api.binance.com", timeout: int = 20):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def fetch(self, path: str, params: dict | None = None):
        params = params or {}
        q = urllib.parse.urlencode(params, doseq=True)
        url = f"{self.base_url}{path}"
        if q:
            url = f"{url}?{q}"
        req = urllib.request.Request(url, headers={"User-Agent": "coinglass-v4-batch3"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            body = r.read().decode("utf-8")
        return json.loads(body)


def klines_symbol(symbol: str):
    s = symbol.upper().replace("-", "").replace("/", "")
    return s
