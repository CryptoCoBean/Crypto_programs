import ccxt
import pandas as pd
import matplotlib.pyplot as plt
import time
import math


exchange_id = 'binanceusdm'
exchange_class = getattr(ccxt, exchange_id)
binance = exchange_class({
    'apiKey': 'APIKEY',
    'secret': 'Secretkey',
    'enableRateLimit': True,
})

# # inital_balance()
# print(binance.fetch_balance()['total']['USDT'])

def order_book():
#order book
    binance_book = binance.fetch_order_book('ETHUSDT')
    bid = binance_book['bids'][0][0]
    ask = binance_book['asks'][0][0]
    print("Got the order book")

def position_size(symbol):
    #dollar size to position size
    def round_decimals_down(number:float, decimals:int=2):
        """
        Returns a value rounded down to a specific number of decimal places.
        """
        if not isinstance(decimals, int):
            raise TypeError("decimal places must be an integer")
        elif decimals < 0:
            raise ValueError("decimal places has to be 0 or more")
        elif decimals == 0:
            return math.floor(number)

        factor = 10 ** decimals
        return math.floor(number * factor) / factor

    dollar_size = int(input("How much do you want to buy"))
    price = binance.fetch_ticker(symbol)['info']['lastPrice']
    price = float(price)
    pos_size_value = dollar_size/price

    market = binance.market(symbol)
    min_ticker_size = float(market['limits']['market']['min'])
    print(min_ticker_size)
    pos_size_equiv = pos_size_value/min_ticker_size
    pos_size_value_rounded = round_decimals_down(pos_size_equiv,0)
    pos_size_final = pos_size_value_rounded * min_ticker_size
    print("total position size in asset size: {0}, which is {1} usdt".format(pos_size_final, (pos_size_final * price)))
    return pos_size_final
    

def market_buy():
    #market buy
    symbol = str(input("What coin do you want to market buy?  "))
    symbol = symbol.upper()
    pos_size = position_size(symbol)
    params = {'timeInForce': 'PostOnly',}
    time.sleep(1)
    binance.create_market_buy_order(symbol, pos_size)
    time.sleep(3)
    binance.create_market_sell_order(symbol, pos_size)

market_buy()
