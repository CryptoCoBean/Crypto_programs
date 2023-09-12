import ccxt
import math

exchange_id = 'binanceusdm'
exchange_class = getattr(ccxt, exchange_id)
binance = exchange_class({
    'apiKey': 'apikey',
    'secret': 'secretkey',
    'enableRateLimit': True,
})

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
    pos_size_equiv = pos_size_value/min_ticker_size
    pos_size_value_rounded = round_decimals_down(pos_size_equiv,0)
    pos_size_final = pos_size_value_rounded * min_ticker_size
    return pos_size_final
    

def params_unknown():
    symbol = str(input("What coin do you want to market order?  "))
    symbol = symbol.upper()
    pos_size = position_size(symbol)
    # params = {'timeInForce': 'PostOnly',}
    direction = input("buy or sell? ")
    nothing = input("press any key to fill order")
    if direction == "buy":
        binance.create_market_buy_order(symbol, pos_size)
        print("your order is now filled")
    if direction == "sell":
        binance.create_market_sell_order(symbol, pos_size)
        print("your order is now filled")
    else:
        print("you have enetered wrong")

def params_known():
    symbol = 'ethusdt'
    symbol = symbol.upper()
    pos_size = position_size(symbol)
    nothing = input("press any key to fill order")
    binance.create_market_buy_order(symbol, pos_size)    # BUY
    # binance.create_market_sell_order(symbol, pos_size)   # SELL
    print("your order is now filled")

# params_known()
params_unknown()
