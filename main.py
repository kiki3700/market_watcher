# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import os

import pandas as pd

from const import RESOURCE_DIR
from exchange.exchange import Exchange

if __name__ == "__main__":

    names = ["okx","bitmex","bybit", "deribit", 'binance', "bitget"]
    exchanges = [Exchange(n) for n in names ]
    data = []
    for exchange in exchanges:
        data += exchange.get_instruments_data(exchange.group_a, "group_a")
        data+= exchange.get_instruments_data(exchange.group_b, "group_b")
        data += exchange.get_instruments_data(exchange.group_c, "group_c")
    df = pd.DataFrame(data)
    df.to_csv(os.path.join(RESOURCE_DIR, f"{'instrument'}.csv"), index=False)

