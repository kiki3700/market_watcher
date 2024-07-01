import os.path
from dataclasses import dataclass, asdict

import pandas as pd
import ccxt

from const import RESOURCE_DIR


@dataclass
class Instrument:
    id: str
    symbol: str
    base: str
    quote: str
    settle: str
    type: str
    active: bool
    linear: bool
    inverse: bool
    subType: str
    group: str
    exchange: str
    volume: float = 0
    spread:float = 0
    volume_imbalance: float = 0

    @staticmethod
    def of_basic(
            id: str,
    symbol: str,
    base: str,
    quote: str,
    settle: str,
    type: str,
    active: bool,
    linear: bool,
    inverse: bool,
    subType: str,
    group: str,
    exchange: str
    ):
        return Instrument(
            id,
            symbol,
            base,
            quote,
            settle,
            type,
            active,
            linear,
            inverse,
            subType,
            group,
            exchange,
        )

    def set_market_data(self,
                        volume,
                        spread,
                        volume_imbalance):
        self.volume= volume
        self.spread = spread
        self.volume_imbalance = volume_imbalance


    @property
    def is_linear(self):
        return self.linear

    @property
    def is_inverse(self):
        return self.inverse

    @property
    def is_quanto(self):
        return not self.inverse and not self.linear

    @property
    def is_bitmex(self):
        return self.exchange == "bitmex"


class Exchange:
    group_a =['BTC/USD:BTC',
              'BTC/USDT:USDT',
              'ETH/USD:BTC',
              'ETH/USDT:USDT',
              ]
    group_b = [
        'BTC/EUR:BTC',
        'DOGE/USD:BTC',
        'DOGE/USDT:USDT',
        'SOL/USD:BTC',
        'SOL/USDT:USDT']

    group_c = [
        'LTC/USD:BTC',
        'LTC/USDT:USDT',
        'LINK/USD:BTC',
        'ADA/USD:BTC',
        'ADA/USDT:USDT',
        'DOT/USD:BTC',
        'DOT/USDT:USDT',
        'XRP/USD:BTC',
        'XRP/USDT:USDT',
        'AVAX/USD:BTC',
        'AVAX/USDT:USDT',
        'MATIC/USDT:USDT',
        'BCH/USD:BTC',
        'BCH/USDT:USDT',
        'SUI/USD:BTC',
        'SUI/USDT:USDT',
        'BNB/USD:BTC',
        'BNB/USDT:USDT']
    markets = ccxt.bitmex().load_markets()

    for m in markets.values():
        if m["active"] and m["future"] and (m["base"] == "BTC" or m["base"] == "ETH"):
            group_b.append(m["symbol"])
    all_groups = group_a + group_b + group_c


    def __init__(self, exchange):
        if exchange == "kucoin":
            self.exchange = ccxt.kucoinfutures()
        elif exchange == "kraken":
            self.exchange = ccxt.krakenfutures()
        else:
            self.exchange = getattr(ccxt, exchange)()
        self.name = exchange

        self.markets = self.exchange.load_markets()

    def analyse_order_book(self, instrument: Instrument):
        order_book = self.exchange.fetch_order_book(instrument.symbol)
        # 데이터프레임으로 변환
        bids = pd.DataFrame([e[:2] for e in order_book['bids']], columns=["price", "amount"])
        asks = pd.DataFrame([e[:2] for e in order_book['asks']], columns=["price", "amount"])
        # Bid-Ask Spread 계산
        bid_price = bids['price'].max()
        ask_price = asks['price'].min()
        spread = (ask_price - bid_price) / bid_price
        # Order Book Imbalance 계산
        total_bids_volume = bids['amount'].sum()
        total_asks_volume = asks['amount'].sum()
        volume_imbalance = (total_bids_volume / total_asks_volume) /(total_bids_volume + total_asks_volume)
        return spread,  volume_imbalance

    def get_instruments_data(self, symbols, group=""):
        def process_instrument(symbol, info):
            data = self.get_instrument_data(symbol)
            instrument = self._to_instrument(info, group)
            spread, volume_imbalance = self.analyse_order_book(instrument)
            volume = self.quote_volume_as_dollar(data, instrument)
            instrument.set_market_data(volume, spread, volume_imbalance)
            return asdict(instrument)

        result = []
        for s in symbols:
            if s in self.markets:
                info = self.markets[s]
                result.append(process_instrument(s, info))
                # result.append(self.get_instrument_data(s))
            elif s.endswith("USD:BTC"):
                symbol = self.replace_symbol(s)
                if symbol in self.markets:
                    info = self.markets[symbol]
                    result.append(process_instrument(symbol, info))
                    # result.append(self.get_instrument_data(symbol))
        return result

    def replace_symbol(self, symbol):
        # '/'로 나누어 앞부분을 추출
        base_currency_pair = symbol.split(':')[0]
        # '/'로 나누어 base_currency를 추출
        base_currency = base_currency_pair.split('/')[0]
        # 새로운 심볼 조합
        return f"{base_currency_pair}:{base_currency}"


    def quote_volume_as_dollar(self, data, instrument: Instrument ):
        quote_volume = float(data["quoteVolume"]) if data["quoteVolume"] else 0
        if self.name == "bybit":
            if instrument.is_linear:
                return data['info.turnover24h']
            else:
                return data['info.volume24h']
        elif self.name == "deribit":
            return data['info.stats.volume_usd']
        elif self.name == "okx":
            return  data['info.volCcy24h']
        elif self.name == "bitget":
            return data['info.quoteVolume']
        elif self.name =="bitmex":
            return data["info.foreignNotional24h"]
        elif self.name == "binance":
            if instrument.is_inverse and instrument.base == "BTC":
                return quote_volume * 100
            elif instrument.is_inverse:
                return quote_volume * 10
            return quote_volume
        elif self.name =="kraken":
            return float(data['info.volumeQuote'])
        return quote_volume

    def _to_instrument(self, data, group):
        id = data["id"]
        symbol = data["symbol"]
        base = data["base"]
        quote = data["quote"]
        settle = data["settle"]
        type = data["type"]
        active = data["active"]
        linear = data["linear"]
        inverse = data["inverse"]
        subType = data["subType"]
        return Instrument.of_basic(
            id,
            symbol,
            base,
            quote,
            settle,
            type,
            active,
            linear,
            inverse,
            subType,
            group,
            self.name,
        )

    def get_instrument_data(self, symbol):
        ins = self.exchange.fetch_ticker(symbol)
        return pd.json_normalize(ins, sep='.').to_dict(orient='records')[0]

    def update_data(self, data):
        file = os.path.join(RESOURCE_DIR, "instrument.csv")
        df = pd.read_csv(file)
        df_dict ={row["exchange"]+ row["symbol"]: row for _, row in df.iterrows()}
        if type(data) == list:
           for d in data:
               key = d["exchange"] + d["symbol"]
               df_dict[key] = d
        else:
            key = data["exchange"] + data["symbol"]
            df_dict[key]=data
        df = pd.DataFrame([r for r in df_dict.values()])
        df.to_csv(file, index=False)
