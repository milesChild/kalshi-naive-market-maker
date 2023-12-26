import kalshi_python

class MarketDataModule:

    def __init__(self, api: kalshi_python.ApiInstance):
        self.api = api

    def get_last(self, ticker: str) -> int:
        return 50

    def get_orderbook(self, ticker: str) -> dict:
        return {}