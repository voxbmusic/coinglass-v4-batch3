import os
from batch2_engine.coinglass import CoinGlassAPI
from batch2_engine.providers.binance_public import BinancePublicAPI


def get_api():
    mode = os.getenv("DATA_MODE", "").strip().lower()
    if mode == "free":
        return BinancePublicAPI()
    api_key = os.getenv("COINGLASS_API_KEY", "")
    return CoinGlassAPI(api_key=api_key)

