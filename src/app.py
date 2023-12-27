# imports
import kalshi_python
import sys
import logging
import datetime
import uuid
import time
from v1.market_data import MarketDataModule
from v1.ordering import OrderingModule
from v1.portfolio import PortfolioModule
from v1.spread import SpreadModule
from credentials import EMAIL, PW
from config import spread_module_config, log_file_path, trade_qty

def order_diff(bid: int, ask: int, orders: list, best_bid: int, best_offer: int) -> tuple:
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

def loop(mdp: MarketDataModule, oms: OrderingModule, pf: PortfolioModule, sm: SpreadModule, ticker: str):

    cur_inv = pf.get_inventory(ticker)
    open_orders = pf.get_open_orders(ticker)
    last_px = mdp.get_last(ticker)
    best_bid, best_offer = mdp.get_bbo(ticker)
    bid, ask = sm.update_spread(last_px, cur_inv)
    orders, cancels = order_diff(bid, ask, open_orders, best_bid, best_offer)
    for cancel in cancels:
        logging.info(f"Cancelling order {cancel}")
        oms.cancel_order(cancel)

    for order in orders:
        logging.info(f"Placing order {order}")
        oms.place_order(order)
    
    time.sleep(2)  # sleeping is necessary because kalshi portfolio endpoint is slow to update after placing orders

if __name__ == "__main__":

    # set up logging
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    ticker = sys.argv[1]
    logging.basicConfig(filename=log_file_path+ticker+str(date)+".log", level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')    

    logging.info(f"Initializing Naive Market Maker with ticker {ticker}...")

    # initialize kalshi api
    config = kalshi_python.Configuration()
    config.host = "https://trading-api.kalshi.com/trade-api/v2"

    kalshi_api = kalshi_python.ApiInstance(
    email=EMAIL,
    password=PW,
    configuration=config,
    )

    logging.info("Successfully logged in to Kalshi API. Beginning trading...")

    # create modules
    mdp = MarketDataModule(kalshi_api)
    oms = OrderingModule(kalshi_api)
    pf = PortfolioModule(kalshi_api)
    sm = SpreadModule(spread_module_config)

    while True:

        # provide liquidity until your computer dies
        try:
            loop(mdp, oms, pf, sm, ticker)
        except Exception as e:
            logging.error(f"Error: {e}")