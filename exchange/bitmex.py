import pandas as pd
import ccxt

from exchange.exchange import Exchange


class Bitmex(Exchange):
    def __init__(self):
        super().__init__("bitmex")
        self.exchange = ccxt.bitmex()


    def get_30days_avd(self, symbol):
        timeframe = '1d'
        ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=30)
        total_volume = sum(c[5]/c[2] for c in ohlcv)
        length = len(ohlcv)
        return total_volume/ length

    def analyse_order_book(self, symbol):
        order_book = self.exchange.fetch_order_book(symbol)
        bids = pd.DataFrame([e[:2] for e in order_book['bids']], columns=["price", "amount"])
        asks = pd.DataFrame([e[:2] for e in order_book['asks']], columns=["price", "amount"])
        asks['amount'] = asks['amount']/ asks['price']
        bids['amount'] = bids['amount']/ bids['price']
        # Bid-Ask Spread 계산
        bid_price = bids['price'].max()
        ask_price = asks['price'].min()
        spread = (ask_price - bid_price) / bid_price

        # Market Depth 계산
        market_depth = {
            'total_bids': bids['amount'].sum(),
            'total_asks': asks['amount'].sum()
        }

        # Cumulative Volume 계산
        bids['cumulative_volume'] = bids['amount'].cumsum()
        asks['cumulative_volume'] = asks['amount'].cumsum()

        # Order Book Imbalance 계산
        total_bids_volume = bids['amount'].sum()
        total_asks_volume = asks['amount'].sum()
        order_book_imbalance = (total_bids_volume - total_asks_volume) / (total_bids_volume + total_asks_volume)
        return spread, market_depth, order_book_imbalance


