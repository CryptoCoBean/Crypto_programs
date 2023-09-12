import ccxt
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
exchange = ccxt.bybit()
bars = exchange.fetch_ohlcv('BTCUSDT',timeframe="D", limit=500)
ccxt_df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])

#EMA's 12 and 21 stored within the ccxt_df dataframe
ccxt_df['EMA12'] = ccxt_df.ta.ema(length=12)
ccxt_df['EMA21'] = ccxt_df.ta.ema(length=21)

# Displays EMA's on a graph 
ccxt_df['close'].plot(linewidth="1", color='black')
ccxt_df['EMA12'].plot(label = 'EMA 12', color='red')
ccxt_df['EMA21'].plot(label = 'EMA 21', color='blue')  
plt.legend()
plt.show()