import kalshi_python
import numpy as np

class PortfolioModule:

    def __init__(self, api: kalshi_python.ApiInstance):
        self.api = api

    def get_inventory(self, ticker: str) -> int:
        return np.random.randint(-10, 10)

    def get_open_orders(self, ticker: str) -> list:
        return []