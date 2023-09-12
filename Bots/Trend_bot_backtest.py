import ccxt
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
import numpy as np

exchange_id = 'binanceusdm'
exchange_class = getattr(ccxt, exchange_id)
binance = exchange_class({
    'apiKey': '09wqPd4c8YPO8oxj0mTStbzQwh5MPtGVKvDHsk6PoaTTUxTAGWkSmfeMfrqBzRYk',
    'secret': '7ROIHEI6bUXAkXRjH1WvyAebLnlpuXOKznh2ebqSzv7oDNnx4GwbA6JsH0q8583b',
    'enableRateLimit': True,
})

def data():
    limits = 300
    bars = binance.fetch_ohlcv('BTCUSDT',timeframe="1d", limit=limits)
    ccxt_df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    return ccxt_df, limits


def ADX(ccxt_df):
    ccxt_df['ADX'] = ccxt_df.ta.adx(length=14,lensig=14, mamode='rma')['ADX_14']
    return ccxt_df

def EMAs(ccxt_df):
    ccxt_df['EMA12'] = ccxt_df.ta.ema(length=12)
    ccxt_df['EMA21'] = ccxt_df.ta.ema(length=21)
    return ccxt_df

def Aroon(ccxt_df):
    ccxt_df['AroonU'] = ccxt_df.ta.aroon(length=14)['AROONU_14']
    ccxt_df['AroonD'] = ccxt_df.ta.aroon(length=14)['AROOND_14']
    return ccxt_df

def plotting(ccxt_df,limits):
    fig , axis = plt.subplots(3,1)
    axis[0].plot(ccxt_df['close'], linewidth="1", color='black')
    axis[0].plot(ccxt_df['EMA12'], label = 'EMA 12', color='red')
    axis[0].plot(ccxt_df['EMA21'], label = 'EMA 21', color='blue')  
    axis[1].plot(ccxt_df['ADX'], label = 'ADX', linewidth="1.5")
    axis[2].plot(ccxt_df['AroonU'], label='Upper', color='orange', linewidth='1')
    axis[2].plot(ccxt_df['AroonD'], label='Lower', color='blue', linewidth='1')

    min_valuex = [0,limits]
    min_valuey = [20,20]
    axis[1].plot(min_valuex,min_valuey, color="green", linewidth="1.5")

    max_valuex = [0,limits]
    max_valuey = [50,50]
    axis[1].plot(max_valuex,max_valuey, color="red", linewidth="1.5")

    mid_valuex = [0,limits]
    mid_valuey = [35,35]
    axis[1].plot(mid_valuex,mid_valuey, linestyle="--", linewidth="1", color="black")
    #plt.legend()
    plt.show()

def signals(ccxt_df):
    ccxt_df['Trend_buys'] = np.where((ccxt_df['EMA12'] > ccxt_df['EMA21']) & (ccxt_df['AroonU'] >= ccxt_df['AroonD']) , 1.0, 0.0) # buy signals and closes

    ccxt_df['Trend_sells'] = np.where((ccxt_df['EMA12'] < ccxt_df['EMA21']) & (ccxt_df['AroonU'] < ccxt_df['AroonD']) , 1.0, 0.0) # sell signals and closes

    # create a new column 'trend signal buys' which is a day-to-day difference of the 'trend reversal buys' column. 
    ccxt_df['Trend_Signal_buys'] = ccxt_df['Trend_buys'].diff()

    # create a new column 'trend signal sells' which is a day-to-day difference of the 'trend reversal sells' column.
    ccxt_df['Trend_Signal_sells'] = ccxt_df['Trend_sells'].diff()
    return ccxt_df

def extended_plot(ccxt_df):
    plt.figure(figsize=(20,6))
    plt.tick_params(axis = 'both', labelsize = 10)
    # plot close price, short-term and long-term moving averages 
    ccxt_df['close'].plot(label = 'Closes')  
    ccxt_df['EMA12'].plot(label = '12-day EMA') 
    ccxt_df['EMA21'].plot(label = '21-day EMA') 

    # plot 'buy' signals
    plt.plot(ccxt_df[ccxt_df['Trend_Signal_buys'] == 1].index, ccxt_df['EMA12'][ccxt_df['Trend_Signal_buys'] == 1], '^', markersize = 8, color = 'g', label = 'buy') # buy signals

    # # plot 'buy close' signals
    plt.plot(ccxt_df[ccxt_df['Trend_Signal_buys'] == -1].index, ccxt_df['EMA12'][ccxt_df['Trend_Signal_buys'] == -1], 'v', markersize = 8, color = 'pink', label = ' buy closes')


    # plot 'sell' signals
    plt.plot(ccxt_df[ccxt_df['Trend_Signal_sells'] == 1].index, ccxt_df['EMA12'][ccxt_df['Trend_Signal_sells'] == 1], 'v', markersize = 8, color = 'r', label = 'sell') # buy signals

    # # plot 'sell close' signals
    plt.plot(ccxt_df[ccxt_df['Trend_Signal_sells'] == -1].index, ccxt_df['EMA12'][ccxt_df['Trend_Signal_sells'] == -1], '^', markersize = 8, color = 'blue', label = 'sell closes')

    plt.xlabel("Days")
    plt.ylabel("Price")
    plt.title('12 & 21 EMA Crossover', fontsize = 20)
    plt.legend()
    plt.grid()
    plt.show()

def run():
    ccxt_df, limits = data()
    ccxt_df = ADX(ccxt_df)
    ccxt_df = EMAs(ccxt_df)
    ccxt_df = Aroon(ccxt_df)
    # plotting(ccxt_df, limits)
    ccxt_df = signals(ccxt_df)
    extended_plot(ccxt_df)

run()