import logging
import json
import datetime
import uuid

class JsonFormatter(logging.Formatter):
    def format(self, record):
        message = record.msg
        log_record = {
            "message_type": message.get("message_type", "Unknown"),
            "message_value": message.get("message_value", ""),
            "timestamp": datetime.datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        }
        return json.dumps(log_record)
    
def order_diff(bid: int, ask: int, orders: list, best_bid: int, best_offer: int, ticker: str, trade_qty: int) -> tuple:
    yes_price = bid
    no_price = 100 - ask
    to_cancel = [] # list of order ids to cancel
    to_order = [] # list of orders to place
    existing_yes = False
    existing_no = False

    # check for stale prices
    for order in orders:
        # yes checks
        if order["side"] == "yes":  # we already have an order out at this price
            if order["yes_price"] == yes_price:
                existing_yes = True
            elif order["yes_price"] != yes_price:  # stale price
                to_cancel.append(order["order_id"])
        # no checks
        elif order["side"] == "no":
            if order["no_price"] == no_price:
                existing_no = True
            elif order["no_price"] != no_price:
                to_cancel.append(order["order_id"])
    
    # generate orders
    if not existing_yes:
        if bid >= best_offer:
            to_order.append({'action': 'buy', 'type': 'limit', 'ticker': ticker, 'count': trade_qty, 'side': 'yes', 'yes_price': int(best_offer-1), 'client_order_id': str(uuid.uuid4())})
        else:
            to_order.append({'action': 'buy', 'type': 'limit', 'ticker': ticker, 'count': trade_qty, 'side': 'yes', 'yes_price': int(bid), 'client_order_id': str(uuid.uuid4())})
    if not existing_no:
        if ask <= best_bid:
            to_order.append({'action': 'buy', 'type': 'limit', 'ticker': ticker, 'count': trade_qty, 'side': 'no', 'no_price': int(100 - best_bid+1), 'client_order_id': str(uuid.uuid4())})
        else:
            to_order.append({'action': 'buy', 'type': 'limit', 'ticker': ticker, 'count': trade_qty, 'side': 'no', 'no_price': int(100 - ask), 'client_order_id': str(uuid.uuid4())})
    
    return to_order, to_cancel