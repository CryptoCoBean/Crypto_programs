import ccxt
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
exchange = ccxt.bybit()
bars = exchange.fetch_ohlcv('BTCUSDT',timeframe="D", limit=500)
ccxt_df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])

#ADX using pandas_ta (THIS IS 100 TIMES EASIER)
#adx = ta.adx(['high'], ccxt_df['low'], ccxt_df['close'], length=14, lensig=14, mamode='rma')
adx = ccxt_df.ta.adx(length=14,lensig=14, mamode='rma')

# Displays ADX on a graph 
fig , axis = plt.subplots(2,1)
axis[0].plot(ccxt_df['close'], linewidth="1.5")
axis[1].plot(adx['ADX_14'], label = 'ADX', linewidth="1.5")

min_valuex = [0,199]
min_valuey = [20,20]
plt.plot(min_valuex,min_valuey, color="green", linewidth="1.5")

max_valuex = [0,199]
max_valuey = [50,50]
plt.plot(max_valuex,max_valuey, color="red", linewidth="1.5")

mid_valuex = [0,199]
mid_valuey = [35,35]
plt.plot(mid_valuex,mid_valuey, linestyle="--", linewidth="1", color="black")
plt.legend()
plt.show()
