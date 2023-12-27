import kalshi_python

class OrderingModule():

    def __init__(self, api: kalshi_python.ApiInstance):
        self.api = api

    def place_order(self, order: dict) -> None:
        _ = self.api.create_order(order)

    def cancel_order(self, order_id: str) -> None:
        _ = self.api.cancel_order(order_id)