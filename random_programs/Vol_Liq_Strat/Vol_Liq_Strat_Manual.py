import ccxt
import datetime
import schedule
import time
import pandas as pd
import numpy as np
import pandas_ta as ta
import matplotlib.pyplot as plt
from pandas_ta.volatility import atr
from pandas_ta.utils import get_offset, verify_series
from pandas import DataFrame
import math
import openpyxl
import matplotlib.dates as mdates
from mplfinance.original_flavor import candlestick_ohlc
# import sizing_hl
import ps
from fetch_ochlv_for_hl import *
from pprint import pprint

print("BOT Starting...")
exchange = ccxt.hyperliquid({
    "walletAddress": ps.WALLET,  
    "privateKey": ps.PRIVATE_KEY,
    "enableRateLimit": True,
    "timeout": 10000,
    "options": {
        "defaultSlippage": 0.01,  # 1% slippage buffer
        }
})

exchange.load_markets()
total_account = 50
risk = 0.2
number_of_bars_to_wait = 3
# tf = '1m'

def params():
    limits = 1000
    symbol_short = 'HYPE'
    symbol = f'{symbol_short}/USDC:USDC'
    # total_account = 1000
    # risk = 0.5 #(%)
    # number_of_bars_to_wait = 2
    tf = "1w" # options: '1m','3m', '5m', '15m, '30m, '1h', '2h', '4h', '6h', '8h', '12h, '1d', '3d', '1w', '1M'
    return limits, symbol, tf, symbol_short # total_account, risk, number_of_bars_to_wait,

def data(symbol, limits, tf):
    bars = (fetch_ohlcv_hl_adaptation(symbol, timeframe=tf, limit=limits))
    ccxt_df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    # print(ccxt_df)
    # print(datetime.datetime.now())
    return ccxt_df

def cksp(high, low, close, p=None, x=None, q=None, tvmode=None, offset=None, **kwargs):
    """Indicator: Chande Kroll Stop (CKSP)"""
    # Validate Arguments
    # TV defaults=(14,2,9), book defaults = (14,3,20)
    p = int(p) if p and p > 0 else 14
    x = float(x) if x and x > 0 else 2 if tvmode is True else 3
    q = int(q) if q and q > 0 else 9 if tvmode is True else 20
    _length = max(p, q, x)

    high = verify_series(high, _length)
    low = verify_series(low, _length)
    close = verify_series(close, _length)
    if high is None or low is None or close is None: return

    offset = get_offset(offset)
    tvmode = tvmode if isinstance(tvmode, bool) else True
    mamode = "rma" if tvmode is True else "sma"

    # Calculate Result
    atr_ = atr(high=high, low=low, close=close, length=p, mamode=mamode)

    long_stop_ = close.rolling(p).max() - x * atr_ # this line was changed
    long_stop = long_stop_.rolling(q).max()

    short_stop_ = close.rolling(p).min() + x * atr_ # this line was also changed
    short_stop = short_stop_.rolling(q).min()

    # Offset
    if offset != 0:
        long_stop = long_stop.shift(offset)
        short_stop = short_stop.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        long_stop.fillna(kwargs["fillna"], inplace=True)
        short_stop.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        long_stop.fillna(method=kwargs["fill_method"], inplace=True)
        short_stop.fillna(method=kwargs["fill_method"], inplace=True)

    # Name and Categorize it
    _props = f"_{p}_{x}_{q}"
    long_stop.name = f"CKSPl{_props}"
    short_stop.name = f"CKSPs{_props}"
    long_stop.category = short_stop.category = "trend"

    # Prepare DataFrame to return
    ckspdf = DataFrame({long_stop.name: long_stop, short_stop.name: short_stop})
    ckspdf.name = f"CKSP{_props}"
    ckspdf.category = long_stop.category

    return ckspdf

def vol_stops(ccxt_df):
    chande_kroll_stop = cksp(ccxt_df['high'], ccxt_df['low'], ccxt_df['close'], p=14, x=2, q=9, tvmode=True, offset=None)
    ccxt_df['CKSP_longs'] = chande_kroll_stop['CKSPl_14_2.0_9']
    ccxt_df['CKSP_shorts'] = chande_kroll_stop['CKSPs_14_2.0_9']

    ccxt_df['vol_stop_longs'] = np.where(ccxt_df['CKSP_longs'] < ccxt_df['close'], ccxt_df['CKSP_longs'], ccxt_df['CKSP_shorts'])
    return ccxt_df

def vol_stop_pine_secondary(df, length=14, factor=2.0, src_col='close'):
    """
    Replicates TradingView's volStop() (PineScript) logic exactly:
    - returns (stop_series, uptrend_series)
    - df must have 'open','high','low','close' columns; index preserved
    - uses pandas_ta.atr for ATR calculation (same length), multiplied by factor
    """
    df = df.copy()
    n = len(df)
    stop = pd.Series(index=df.index, dtype=float)
    uptrend = pd.Series(index=df.index, dtype=bool)

    # compute ATR (use rma style if you want exact smoothing like TV)
    # pandas_ta.atr returns NaN for first periods; that's OK
    atr_series = atr(high=df['high'], low=df['low'], close=df['close'], length=length, mamode="rma")

    # initialize scalars
    if n == 0:
        return stop, uptrend

    # initial values: follow Pine's nz defaults -> use first src
    src = df[src_col].iloc[0]
    stop.iloc[0] = src
    uptrend.iloc[0] = True
    max_src = src
    min_src = src

    # iterate row-by-row (this preserves the recursive reset behaviour)
    for i in range(1, n):
        idx = df.index[i]
        src = df[src_col].iloc[i]
        atrM = (atr_series.iloc[i] * factor) if not pd.isna(atr_series.iloc[i]) else 0.0

        # if previous state was uptrend -> update max and candidate stop accordingly
        if uptrend.iloc[i - 1]:
            max_src = max(max_src, df[src_col].iloc[i])  # Pine uses src for max/min, here src == close
            # candidate stop cannot be less than previous stop (Pine: stop := nz(uptrend ? math.max(stop, max - atrM) ...)
            prev_stop = stop.iloc[i - 1] if not pd.isna(stop.iloc[i - 1]) else max_src - atrM
            candidate_stop = max(prev_stop, max_src - atrM)
        else:
            # previous was downtrend -> update min and candidate stop
            min_src = min(min_src, df[src_col].iloc[i])
            prev_stop = stop.iloc[i - 1] if not pd.isna(stop.iloc[i - 1]) else min_src + atrM
            candidate_stop = min(prev_stop, min_src + atrM)

        # decide uptrend for current bar using same rule: uptrend := src - stop >= 0.0
        curr_uptrend = (src - candidate_stop) >= 0.0

        # If trend flips compared to previous bar, Pine resets max/min and recomputes stop
        if curr_uptrend != uptrend.iloc[i - 1]:
            # reset max/min to current src and recompute stop accordingly
            max_src = src
            min_src = src
            candidate_stop = max_src - atrM if curr_uptrend else min_src + atrM

        stop.iloc[i] = candidate_stop
        uptrend.iloc[i] = curr_uptrend

    return stop, uptrend

def vol_stops_pine_main(ccxt_df, length=14, factor=2.0): # chatgpt
    # compute vol stop using Pine-like recursion
    stops, up = vol_stop_pine_secondary(ccxt_df, length=length, factor=factor, src_col='close')
    ccxt_df = ccxt_df.copy()
    ccxt_df['vol_stop'] = stops
    ccxt_df['vol_uptrend'] = up
    # Keep your scatter plotting using vol_stop; color by uptrend if you like:
    # e.g., in plotting: color = ccxt_df['vol_uptrend'].map({True:'limegreen', False:'red'})
    return ccxt_df

def processing_logic_block(ccxt_df):
    # candle colour (up candle or a down candle)
    ccxt_df['candle_colour'] = np.where(ccxt_df['close'] > ccxt_df['open'], 'green', 'red') 
    
    # if its an up wick based on the colour of the candle than the difference in the 
    # ccxt_df['up_wick'] = np.where(ccxt_df['candle_colour'] == 'green', (ccxt_df['high'] - ccxt_df['close']), (ccxt_df['high']- ccxt_df['open']))
    # ccxt_df['down_wick'] = np.where(ccxt_df['candle_colour'] == 'red', (ccxt_df['open'] - ccxt_df['low']), (ccxt_df['close']- ccxt_df['low']))
    
    
    # Getting the count of consecutive vol liqs and taking the last row of each of the groups as a new df
    ccxt_df['group'] = (ccxt_df['vol_stop'] != ccxt_df['vol_stop'].shift()).cumsum()
    ccxt_df['count'] = ccxt_df.groupby('group')['vol_stop'].transform('size')
    valid_vol_stops = ccxt_df.copy()
    
    # checks if there is a wick into the vol stop within the valid_vol_stop groups so that they can be disregarded
    for group_id, group_data in valid_vol_stops.groupby('group'):
        vol_stop_value = group_data['vol_stop'].iloc[0]
        uptrend = group_data['vol_uptrend'].iloc[0]

        # Check for violation within the group itself
        if uptrend:
            violated = (group_data['low'] < vol_stop_value).any()
        else:
            violated = (group_data['high'] > vol_stop_value).any()

        # If any candle in that group violates the stop → drop all rows for that group
        if violated:
            valid_vol_stops = valid_vol_stops[valid_vol_stops['group'] != group_id]
        
    valid_vol_stops = valid_vol_stops.groupby('group', as_index=False).head(1) #tail(1)
    ccxt_df = ccxt_df.drop(columns='group')
    valid_vol_stops = valid_vol_stops.drop(columns='group')
    

    # keeping only the rows with valid vol stops (are 3 or 4) in a separate dataframe for manipulation
    valid_vol_stops = valid_vol_stops[valid_vol_stops['count'].between(3, 5)]
    valid_vol_stops = valid_vol_stops.reset_index(drop=True)
    
    valid_vol_stops['hit'] = None
    valid_vol_stops['end_time'] = None
    
    # Recursivly checking if the close / high / low has crossed any of the vol stops in the valid vol_stop df depending on if the vol stop uptrend is True or False get the time stamp of when the candle it does touch and add it to the valid vol stops df
    for i, row in enumerate(valid_vol_stops.itertuples(index=False)):
        time_valid_vol_stops = row.time
        vol_stop_valid_vol_stops = row.vol_stop
        close_valid_vol_stops = row.close
        open_valid_vol_stops = row.open
        low_valid_vol_stops = row.low
        vol_uptrend_valid_vol_stops = row.vol_uptrend
        candle_colour_valid_vol_stops = row.candle_colour
        # up_wick_valid_vol_stops = row.up_wick
        # down_wick_valid_vol_stops = row.down_wick
        for row_2 in ccxt_df.itertuples(index=False):
            time_ccxt_df = row_2.time
            vol_stop_ccxt_df = row_2.vol_stop
            close_ccxt_df = row_2.close
            open_ccxt_df = row_2.open
            high_ccxt_df = row_2.high
            low_ccxt_df = row_2.low
            vol_uptrend_ccxt_df = row_2.vol_uptrend
            candle_colour_ccxt_df = row_2.candle_colour
            # up_wick_ccxt_df = row_2.up_wick
            # down_wick_ccxt_df = row_2.down_wick
            if time_ccxt_df <= time_valid_vol_stops:
                continue
            else:
                if vol_uptrend_valid_vol_stops:
                    if (close_ccxt_df < vol_stop_valid_vol_stops):
                        valid_vol_stops.at[i, 'hit'] = 'L'
                        valid_vol_stops.at[i,'end_time'] = time_ccxt_df
                        break
                    else:
                        if (low_ccxt_df < vol_stop_valid_vol_stops):
                            valid_vol_stops.at[i,'hit'] = 'W'
                            valid_vol_stops.at[i,'end_time'] = time_ccxt_df
                            break
                else:
                    if (close_ccxt_df > vol_stop_valid_vol_stops):
                        valid_vol_stops.at[i,'hit'] = 'L'
                        valid_vol_stops.at[i,'end_time'] = time_ccxt_df
                        break
                    if (high_ccxt_df > vol_stop_valid_vol_stops):
                        valid_vol_stops.at[i,'hit'] = 'W'
                        valid_vol_stops.at[i,'end_time'] = time_ccxt_df
                        break
                    
                
    print(ccxt_df)
    print("Valid vol stop prices are below: \n")
    print(valid_vol_stops)
    return ccxt_df, valid_vol_stops

def stats(valid_vol_stops):
    wins = (valid_vol_stops['hit'] == 'W').sum()
    losses = (valid_vol_stops['hit'] == 'L').sum()
    no_hits = valid_vol_stops['hit'].isna().sum()
    total = wins + losses
    winrate = ((wins / total) * 100)
    print(f"wins: {wins}")   
    print(f"losses: {losses}")   
    print(f"no_hits: {no_hits}")
    print(f"total: {total}")
    print(f"winrate: {winrate}")

def extended_plot(ccxt_df, valid_vol_stops, tf, symbol_short):
    # --- prepare ohlc for mplfinance candlestick_ohlc (numeric times) ---
    ohlc = ccxt_df[['time', 'open', 'high', 'low', 'close']].copy()
    
    # ensure datetime
    if not np.issubdtype(ohlc['time'].dtype, np.datetime64):
        ohlc['time'] = pd.to_datetime(ohlc['time'], unit='ms', errors='coerce')
    # convert to matplotlib numeric dates
    ohlc['time'] = mdates.date2num(ohlc['time'])
    
    
    ohlc_2 = valid_vol_stops[['time', 'open', 'high', 'low', 'close']].copy()
    # ensure datetime
    if not np.issubdtype(ohlc_2['time'].dtype, np.datetime64):
        ohlc_2['time'] = pd.to_datetime(ohlc_2['time'], unit='ms', errors='coerce')
    # convert to matplotlib numeric dates
    ohlc_2['time'] = mdates.date2num(ohlc_2['time'])
    
    
    fig, ax = plt.subplots(figsize=(20, 6))
    plt.tick_params(axis='both', labelsize=10)
    
    # candlestick width -> base it on the median spacing between times (safe)
    if len(ohlc) >= 2:
        dt = np.median(np.diff(ohlc['time'].values))
        bar_width = float(dt) * 0.6
    else:
        dt = 1.0
        bar_width = 0.6

    candlestick_ohlc(
        ax,
        ohlc[['time', 'open', 'high', 'low', 'close']].values,
        width=bar_width,
        colorup='limegreen',
        colordown='red',
        alpha=0.9
    )
    
    # --- use the new column names: 'vol_stop' and 'vol_uptrend' ---
    if 'vol_stop' not in ccxt_df.columns:
        raise KeyError("DataFrame missing 'vol_stop' column. Run vol_stops(...) first.")

    # color vol stop dots by uptrend flag (green when uptrend True, red when False)
    if 'vol_uptrend' in ccxt_df.columns:
        colors = ccxt_df['vol_uptrend'].map({True: 'limegreen', False: 'red'}).values
    else:
        colors = ['green'] * len(ccxt_df)

    ax.scatter(ohlc['time'], ccxt_df['vol_stop'], label="Vol Stop", c=colors, s=2, zorder=3)
    
    # ensure datetime
    valid_vol_stops['time'] = pd.to_datetime(valid_vol_stops['time'], unit='ms', errors='coerce', utc=True)
    valid_vol_stops['end_time'] = pd.to_datetime(valid_vol_stops['end_time'], unit='ms', errors='coerce', utc=True)
    # convert to matplotlib numeric dates
    valid_vol_stops['time_num'] = mdates.date2num(valid_vol_stops['time'])
    valid_vol_stops['time_end_num'] = mdates.date2num(valid_vol_stops['end_time'].fillna(pd.Timestamp.utcnow()))
    
    for row in valid_vol_stops.itertuples(index=False):
        time = row.time_num
        vol_stop = row.vol_stop
        start_time = time
        end_time = row.time_end_num
        count = row.count
        hit = row.hit
        if (hit == 'W'):
            color = 'limegreen'
        elif (hit == 'L'):
            color = 'red'
        else:
            color = 'black'
            if len(ohlc) >= 2:
                time_step = ohlc['time'].iloc[-1] - ohlc['time'].iloc[-2]
                label_x = ohlc['time'].iloc[-1] + time_step * 2
            else:
                label_x = ohlc['time'].iloc[-1] + 1.0

            label_text = f"{vol_stop:.2f} ({count}x)"
            ax.text(label_x, vol_stop, label_text, color='black', fontsize=9, va='center', ha='left', zorder=4)
            
        ax.hlines(vol_stop, xmin=start_time, xmax=end_time, colors=color, linestyles='--',linewidth = 0.5, zorder=2)
        
        
    # Plot everything onto a chart using matplotlib
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d\n%H:%M'))
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.title("Vol Stops with Candles and Persistent Levels (Wick-aware)", fontsize=16)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    # plt.show() 
    plt.savefig(rf"D:/Documents/Python Programs/CryptoStuff/RandomPrograms/Vol_Liq_Strat/{tf}_{symbol_short}.png", dpi=800)

def run(limits, symbol_short, tf):
    # while True:
        # try:
    print("######################################## Start: {0} ########################################".format(datetime.datetime.now()))
    # limits, symbol, tf, symbol_short  = params() # total_account, risk, number_of_bars_to_wait,
    print("recieved parameters")
    ccxt_df = data(symbol_short, limits, tf)
    print("Recieved candlestick data")
    # ccxt_df = vol_stops(ccxt_df)
    ccxt_df = vol_stops_pine_main(ccxt_df, length=14, factor=2.0)
    print("Added vol stop info")
    # add in all processing logic
    print("starting processing main logic")
    ccxt_df, valid_vol_stops = processing_logic_block(ccxt_df)
    stats(valid_vol_stops)
    extended_plot(ccxt_df,valid_vol_stops, tf, symbol_short) # plot
    print()
    print("######################################## Completed: {0} ########################################".format(datetime.datetime.now()))
        # break

        # # Exceptions
        # except ccxt.NetworkError as e:
        #     print("network error")
        # except ccxt.ExchangeError as e:
        #     print("exchange error: ",e)
        # except Exception as e:
        #     print("unknown error: ",e)
    # print("")




limits = 1000
symbol_short = 'BTC'
symbol = f'{symbol_short}/USDC:USDC'
tf = "1w" 
run(limits, symbol_short, tf)

limits = 1000
symbol_short = 'BTC'
symbol = f'{symbol_short}/USDC:USDC'
tf = "1d" 
run(limits, symbol_short, tf)

limits = 1000
symbol_short = 'SOL'
symbol = f'{symbol_short}/USDC:USDC'
tf = "1w" 
run(limits, symbol_short, tf)

limits = 1000
symbol_short = 'SOL'
symbol = f'{symbol_short}/USDC:USDC'
tf = "1d" 
run(limits, symbol_short, tf)