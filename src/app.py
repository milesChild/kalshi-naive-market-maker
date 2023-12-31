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
from util import order_diff, JsonFormatter, yes_safety_check, no_safety_check

def loop(mdp: MarketDataModule, oms: OrderingModule, pf: PortfolioModule, sm: SpreadModule, ticker: str):

    global INVENTORY, BID, ASK

    cur_inv = pf.get_inventory(ticker)
    open_orders = pf.get_open_orders(ticker)
    last_px = mdp.get_last(ticker)
    best_bid, best_offer = mdp.get_bbo(ticker)
    orderbook = mdp.get_orderbook(ticker)
    yes_check = yes_safety_check(orderbook, open_orders)
    no_check = no_safety_check(orderbook, open_orders)
    bid, ask = sm.update_spread(last_px, cur_inv)
    orders, cancels = order_diff(bid, ask, open_orders, best_bid, best_offer, ticker, trade_qty, yes_check, no_check)
    for cancel in cancels:
        logging.info({"message_type": "OrderCancel", "message_value": cancel})
        oms.cancel_order(cancel)

    for order in orders:
        logging.info({"message_type": "OrderPlace", "message_value": order})
        oms.place_order(order)
    
    # logging
    if cur_inv != INVENTORY:
        logging.info({"message_type": "InventoryDelta", "message_value": cur_inv - INVENTORY})
        INVENTORY = cur_inv
    if bid != BID:
        logging.info({"message_type": "BidDelta", "message_value": bid - BID})
        BID = bid
    if ask != ASK:
        logging.info({"message_type": "AskDelta", "message_value": ask - ASK})
        ASK = ask
    
    time.sleep(2)  # sleeping is necessary because kalshi portfolio endpoint is slow to update after placing orders

if __name__ == "__main__":

    # set up logging
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    ticker = sys.argv[1]
    logfilepath = log_file_path+ticker+str(date)+".log"

    # Set up JSON logging
    logging.basicConfig(filename=logfilepath, level=logging.INFO)
    logger = logging.getLogger()
    handler = logger.handlers[0]
    handler.setFormatter(JsonFormatter())

    logging.info({"message_type": "ProgramInfo", "message_value": f"Initializing Naive Market Maker with ticker {ticker}..."})

    # initialize kalshi api
    config = kalshi_python.Configuration()
    config.host = "https://trading-api.kalshi.com/trade-api/v2"

    kalshi_api = kalshi_python.ApiInstance(
    email=EMAIL,
    password=PW,
    configuration=config,
    )

    logging.info({"message_type": "ProgramInfo", "message_value": f"Successfully logged in to Kalshi API. Beginning trading..."})

    # create modules
    mdp = MarketDataModule(kalshi_api)
    oms = OrderingModule(kalshi_api)
    pf = PortfolioModule(kalshi_api)
    sm = SpreadModule(spread_module_config)

    # initialize global variables
    global INVENTORY, BID, ASK
    INVENTORY = 0
    BID = 0
    ASK = 0

    while True:

        # provide liquidity until your computer dies
        try:
            loop(mdp, oms, pf, sm, ticker)
        except Exception as e:
            logging.error({"message_type": "ProgramError", "message_value": f"Error: {e}"})