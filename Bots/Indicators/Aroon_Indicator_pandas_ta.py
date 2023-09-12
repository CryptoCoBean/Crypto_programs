import ccxt
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
exchange = ccxt.bybit()
bars = exchange.fetch_ohlcv('BTCUSDT',timeframe="D", limit=500)
ccxt_df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])

#Aroon with the upper and lower lines stored within the ccxt dataframe
ccxt_df['AroonU'] = ccxt_df.ta.aroon(length=14)['AROONU_14']
ccxt_df['AroonD'] = ccxt_df.ta.aroon(length=14)['AROOND_14']


# Displays Aroon on a graph 
fig , axis = plt.subplots(2,1)
axis[0].plot(ccxt_df['close'], linewidth="1", color='black')
axis[1].plot(ccxt_df['AroonU'], label='A Upper', color='orange', linewidth='1')
axis[1].plot(ccxt_df['AroonD'], label='A Lower', color='blue', linewidth='1')
#plt.legend()
plt.show()