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
    limits = 2000
    symbol_short = 'BTC'
    symbol = f'{symbol_short}/USDC:USDC'
    # total_account = 1000
    # risk = 0.5 #(%)
    # number_of_bars_to_wait = 2
    tf = "1d" # options: '1m','3m', '5m', '15m, '30m, '1h', '2h', '4h', '6h', '8h', '12h, '1d', '3d', '1w', '1M'
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

# def vol_stops(ccxt_df):
#     chande_kroll_stop = cksp(ccxt_df['high'], ccxt_df['low'], ccxt_df['close'], p=14, x=2, q=9, tvmode=True, offset=None)
#     ccxt_df['CKSP_longs'] = chande_kroll_stop['CKSPl_14_2.0_9']
#     ccxt_df['CKSP_shorts'] = chande_kroll_stop['CKSPs_14_2.0_9']

#     ccxt_df['vol_stop_longs'] = np.where(ccxt_df['CKSP_longs'] < ccxt_df['close'], ccxt_df['CKSP_longs'], ccxt_df['CKSP_shorts'])
#     return ccxt_df



def vol_stop_pine(df, length=14, factor=2.0, src_col='close'):
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


def vol_stops(ccxt_df, length=14, factor=2.0): # chatgpt
    # compute vol stop using Pine-like recursion
    stops, up = vol_stop_pine(ccxt_df, length=length, factor=factor, src_col='close')
    ccxt_df = ccxt_df.copy()
    ccxt_df['vol_stop'] = stops
    ccxt_df['vol_uptrend'] = up
    # Keep your scatter plotting using vol_stop; color by uptrend if you like:
    # e.g., in plotting: color = ccxt_df['vol_uptrend'].map({True:'limegreen', False:'red'})
    return ccxt_df


# def extended_plot(ccxt_df):
#     plt.figure(figsize=(20,6))
#     plt.tick_params(axis = 'both', labelsize = 10)
#     # plot close price, short-term and long-term moving averages 
#     ccxt_df['close'].plot(label = 'Closes')  
#     plt.scatter(ccxt_df.index, ccxt_df['vol_stop_longs'], label="Vol Stop", color='green',s = 1) 

#     plt.xlabel("Days")
#     plt.ylabel("Price")
#     plt.title('12 & 21 EMA Crossover', fontsize = 20)
#     plt.legend()
#     plt.grid()
#     plt.show()


def extended_plot(ccxt_df): # chatgpt ver
    # --- prepare ohlc for mplfinance candlestick_ohlc (numeric times) ---
    ohlc = ccxt_df[['time', 'open', 'high', 'low', 'close']].copy()
    # ensure datetime
    if not np.issubdtype(ohlc['time'].dtype, np.datetime64):
        ohlc['time'] = pd.to_datetime(ohlc['time'], unit='ms', errors='coerce')
    # convert to matplotlib numeric dates
    ohlc['time'] = mdates.date2num(ohlc['time'])
    
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

    ax.scatter(ohlc['time'], ccxt_df['vol_stop'], label="Vol Stop", c=colors, s=8, zorder=3)

    # --- find runs of identical vol_stop values ---
    vol_stops = ccxt_df['vol_stop']  # reduce float noise
    run_ids = (vol_stops != vol_stops.shift()).cumsum()
    grouped = ccxt_df.groupby(run_ids)

    horizontal_lines = []

    for _, group in grouped:
        price = group['vol_stop'].iloc[0]

        # require count between 3 and 4 only (ignore runs >4)
        count = len(group)
        if 3 <= count <= 4 and not pd.isna(price):
        # if len(group) >= 3 and not pd.isna(price):
            start_label = group.index[0]
            last_label = group.index[-1]
            count = len(group)

            # find positional index of the last label to slice after it safely
            last_pos = ccxt_df.index.get_loc(last_label)
            after_run = ccxt_df.iloc[last_pos + 1 :]

            # if there are no candles after the run -> unbroken (extend to last candle)
            if after_run.empty:
                end_label = ccxt_df.index[-1]
                color = 'green'
                label_flag = True
            else:
                # wick touch: any candle whose wick spans the price
                wick_cross = (after_run['high'] >= price) & (after_run['low'] <= price)

                if wick_cross.any():
                    # first cross index label
                    first_cross_label = wick_cross[wick_cross].index[0]
                    end_label = first_cross_label
                    color = 'red'
                    label_flag = False
                else:
                    end_label = ccxt_df.index[-1]
                    color = 'green'
                    label_flag = True

            horizontal_lines.append((start_label, end_label, price, color, count, label_flag))
            
    # --- compute trade outcomes: win/loss per green line ---
# --- compute trade outcomes for ALL lines regardless of plotted line colour ---
    results = []

    # --- compute trade outcomes for ALL lines regardless of plotted line colour ---

    for (start_lbl, end_lbl, price, line_color, count, label_flag) in horizontal_lines:
        # get the run group's origin uptrend using the group slice (more robust)
        # attempt to use the group's majority (mode); fallback to first element
        try:
            group_slice = ccxt_df.loc[start_lbl:end_lbl]  # inclusive slice of the run
            if 'vol_uptrend' in group_slice.columns:
                mode_vals = group_slice['vol_uptrend'].mode()
                if not mode_vals.empty:
                    origin_uptrend = bool(mode_vals.iloc[0])
                else:
                    origin_uptrend = bool(group_slice['vol_uptrend'].iloc[0])
            else:
                origin_uptrend = True
        except Exception:
            # fallback: try end_lbl, then start_lbl, then True
            try:
                origin_uptrend = bool(ccxt_df.loc[end_lbl, 'vol_uptrend'])
            except Exception:
                try:
                    origin_uptrend = bool(ccxt_df.loc[start_lbl, 'vol_uptrend'])
                except Exception:
                    origin_uptrend = True

        # slice candles after the run end
        last_pos = ccxt_df.index.get_loc(end_lbl)
        after_run = ccxt_df.iloc[last_pos + 1 :]

        if after_run.empty:
            results.append({
                "price": price,
                "count": count,
                "start_idx": start_lbl,
                "end_idx": end_lbl,
                "origin_uptrend": origin_uptrend,
                "outcome": "no_data",
                "outcome_idx": None,
                "outcome_time": None,
            })
            continue

        # wick touch: any candle whose wick spans the price
        wick_mask = (after_run['high'] >= price) & (after_run['low'] <= price)
        wick_hits = wick_mask[wick_mask].index.tolist()

        # close breach depends on origin_uptrend:
        # - support (uptrend True): 'loss' if close < price
        # - resistance (uptrend False): 'loss' if close > price
        if origin_uptrend:
            close_mask = after_run['close'] < price
        else:
            close_mask = after_run['close'] > price
        close_hits = close_mask[close_mask].index.tolist()

        # find the earliest event among wick_hits and close_hits (by position in after_run)
        first_wick_pos = None
        first_close_pos = None
        first_wick_idx = None
        first_close_idx = None

        if wick_hits:
            first_wick_idx = wick_hits[0]
            first_wick_pos = after_run.index.get_loc(first_wick_idx)
        if close_hits:
            first_close_idx = close_hits[0]
            first_close_pos = after_run.index.get_loc(first_close_idx)

        # determine outcome by which occurs first (lower position index)
        if (first_wick_pos is not None) and (first_close_pos is not None):
            if first_wick_pos < first_close_pos:
                outcome = "win"
                outcome_idx = first_wick_idx
            elif first_close_pos < first_wick_pos:
                outcome = "loss"
                outcome_idx = first_close_idx
            else:
                # SAME CANDLE tie: prefer wick as WIN per your rule (change if you want close to win)
                outcome = "win"
                outcome_idx = first_wick_idx
        elif first_wick_pos is not None:
            outcome = "win"
            outcome_idx = first_wick_idx
        elif first_close_pos is not None:
            outcome = "loss"
            outcome_idx = first_close_idx
        else:
            outcome = "no_hit"
            outcome_idx = None

        results.append({
            "price": price,
            "count": count,
            "start_idx": start_lbl,
            "end_idx": end_lbl,
            "origin_uptrend": origin_uptrend,
            "outcome": outcome,
            "outcome_idx": outcome_idx,
            "outcome_time": ccxt_df.loc[outcome_idx, "time"] if outcome_idx is not None else None,
        })

    # create dataframe and print stats (same as you had)
    results_df = pd.DataFrame(results)

    total_lines = len(results_df)
    wins = (results_df['outcome'] == 'win').sum()
    losses = (results_df['outcome'] == 'loss').sum()
    no_hits = (results_df['outcome'] == 'no_hit').sum()
    no_data = (results_df['outcome'] == 'no_data').sum()
    decisive = wins + losses
    winrate = (wins / decisive * 100) if decisive > 0 else float('nan')

    print("\n📊 Vol-Liq Strategy Results (all lines evaluated)")
    print(f"Total lines detected (>=3 repeats): {total_lines}")
    print(f"✅ Wins (wick hit before close-breach): {wins}")
    print(f"❌ Losses (close-breach before wick hit): {losses}")
    print(f"⏸️  No hit during available data: {no_hits}")
    print(f"📭 No after-run data (can't evaluate): {no_data}")
    print(f"🏆 Win rate (wins / (wins+losses)): {winrate:.2f}%")


    # optional: show a small results table
    if not results_df.empty:
        display_cols = ['price','count','origin_uptrend','outcome','outcome_time']
        print("\nSample of results:")
        print(results_df[display_cols].head(20).to_string(index=False))

    # results_df is available if you want to save/export for further analysis
    results_df.to_csv('vol_liq_results.csv', index=False)


    # --- helper: convert original index label -> numeric time for plotting ---
    def time_for_label(lbl):
        return ohlc.loc[lbl, 'time']
    

# --- annotate wins/losses UNDER each line, centered horizontally ---
    if 'results_df' in locals() and not results_df.empty:
        for _, row in results_df.iterrows():
            if row['outcome'] not in ['win', 'loss']:
                continue

            price = row['price']
            outcome = row['outcome']

            # Text + color
            if outcome == 'win':
                text = "W"
                color = "limegreen"
            else:
                text = "L"
                color = "red"

            # Find the time span of the horizontal line
            try:
                start_lbl = row['start_idx']
                end_lbl = row['end_idx']
                start_time = ohlc.loc[start_lbl, 'time']
                end_time = ohlc.loc[end_lbl, 'time']
            except Exception:
                # fallback: center under visible chart if missing data
                start_time = ohlc['time'].iloc[0]
                end_time = ohlc['time'].iloc[-1]

            # Center of the line
            center_time = (start_time + end_time) / 2

            # Slightly below the line for visibility
            y_offset = (ohlc['close'].max() - ohlc['close'].min()) * 0.01
            label_y = price - y_offset

            ax.text(
                center_time,
                label_y,
                text,
                color=color,
                fontsize=11,
                fontweight='bold',
                va='top',      # position text just below line
                ha='center',   # horizontally centered under line
                zorder=6,
            )



    # --- plot horizontal lines and labels (only for green ones) ---
    for (start_lbl, end_lbl, price, color, count, label_flag) in horizontal_lines:
        start_time = time_for_label(start_lbl)
        end_time = time_for_label(end_lbl)
        lw = 1.6 if color == 'green' else 1.0
        ax.hlines(price, xmin=start_time, xmax=end_time, colors=color, linestyles='--', linewidth=lw, zorder=2)

        if label_flag:
            # place label slightly beyond the rightmost plotted candle for clarity
            if len(ohlc) >= 2:
                time_step = ohlc['time'].iloc[-1] - ohlc['time'].iloc[-2]
                label_x = ohlc['time'].iloc[-1] + time_step * 2
            else:
                label_x = ohlc['time'].iloc[-1] + 1.0

            label_text = f"{price:.2f} ({count}x)"
            ax.text(label_x, price, label_text, color='black', fontsize=9, va='center', ha='left', zorder=4)

    # --- beautify axes ---
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d\n%H:%M'))
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.title("Vol Stops with Candles and Persistent Levels (Wick-aware)", fontsize=16)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


# def Execution_long_entry(symbol, size, latest_data):
#     print("Long Entry")
#     if not (exchange.fetch_positions()):
#         print("not in a position")
#         orderbook = exchange.fetch_order_book(symbol)
#         best_ask = orderbook['asks'][0][0]
#         print("Best Ask: ", best_ask)
#         price = best_ask * 1.002  # allow 0.2% slippage
#         stop = latest_data['vol_stop_longs'].iloc[1]
#         buy_orders = [
#                 {
#                 'symbol': symbol,
#                 'type': "market",
#                 'side': "buy",
#                 'amount': size,
#                 'price': price,
#                 'params': {"postOnly": False}
#             },
#             {
#                 'symbol': symbol,
#                 'type':'market',
#                 'side': "sell",
#                 'amount':size,
#                 'price':stop,
#                 'params':{
#                     'triggerPrice': stop,
#                     'reduceOnly': True
#                     }
#             }
#             ]  
#         order = exchange.create_orders(buy_orders)
#         print("Enter order", order) 
#         print("filled")
#     else:
#         print("you are in a position")

# def Execution_Short_entry(symbol, size, latest_data):
#     print("Short Entry")
#     if not (exchange.fetch_positions()):
#         print("not in a position")
#         orderbook = exchange.fetch_order_book(symbol)
#         best_bid = orderbook['bids'][0][0]
#         print("Best bid: ", best_bid)
#         price = best_bid * 0.998  # allow 0.2% slippage
#         stop = latest_data['vol_stop_longs'].iloc[1]
#         sell_orders = [
#                 {
#                 'symbol': symbol,
#                 'type': "market",
#                 'side': "sell",
#                 'amount': size,
#                 'price': price,
#                 'params': {"postOnly": False}
#             },
#             {
#                 'symbol': symbol,
#                 'type':'market',
#                 'side': "buy",
#                 'amount':size,
#                 'price':stop,
#                 'params':{
#                     'triggerPrice': stop,
#                     'reduceOnly': True
#                     }
#             }
#             ]  
#         order = exchange.create_orders(sell_orders)
#         print("Enter order", order) 
#         print("filled")
#     else:
#         print("you are in a position")

# def exit_longs(symbol,size, number_of_bars_to_wait):
#     if exchange.fetch_positions():
#         if (exchange.fetch_positions()[0]['info']['position']['szi'] > "0"):
#             wait_after_loss_close(symbol, number_of_bars_to_wait)
#             size = float(exchange.fetch_positions()[0]['info']['position']['szi'])
#             orderbook = exchange.fetch_order_book(symbol)
#             best_ask = orderbook['asks'][0][0]
#             print("Best Ask: ", best_ask)
#             price = best_ask * 1.002  # allow 0.2% slippage
#             exchange.create_order(symbol=symbol,type="market", side="sell", amount=size, price=price,params={"reduceOnly": True})
#             print("you are now flat and there are no open orders")
#         else:
#             print("position is already short (no long position)")
#     else:
#         print("there is no active long position")

# # def exit_shorts(symbol,size, number_of_bars_to_wait):
#     if exchange.fetch_positions():
#         if (exchange.fetch_positions()[0]['info']['position']['szi'] < "0"):
#             size = float(exchange.fetch_positions()[0]['info']['position']['szi']) * -1
#             wait_after_loss_close(symbol, number_of_bars_to_wait)
#             orderbook = exchange.fetch_order_book(symbol)
#             best_bid = orderbook['bids'][0][0]
#             print("Best Bid: ", best_bid)
#             price = best_bid * 0.998  # allow 0.2% slippage
#             exchange.create_order(symbol=symbol,type="market", side="buy", amount=size, price=price,params={"reduceOnly": True})
#             print("you are now flat and there are no open orders")
#         else:
#             print("position is already long (no short positions)")
#     else:
#         print("there is no active short position")




def run():
    while True:
        # try:
        print("######################################## Start: {0} ########################################".format(datetime.datetime.now()))
        limits, symbol, tf, symbol_short  = params() # total_account, risk, number_of_bars_to_wait,
        print("recieved parameters")
        ccxt_df = data(symbol_short, limits, tf)
        print("Recieved candlestick data")
        # ccxt_df = vol_stops(ccxt_df)
        ccxt_df = vol_stops(ccxt_df, length=14, factor=2.0)
        print("Added vol stop info")
        extended_plot(ccxt_df)
        print()
        print("######################################## Completed: {0} ########################################".format(datetime.datetime.now()))
        break

        # # Exceptions
        # except ccxt.NetworkError as e:
        #     print("network error")
        # except ccxt.ExchangeError as e:
        #     print("exchange error: ",e)
        # except Exception as e:
        #     print("unknown error: ",e)
    print("")

run()



# tf_to_minutes = {
#     "1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30,
#     "1h": 60, "2h": 120, "4h": 240, "6h": 360, "8h": 480,
#     "12h": 720, "1d": 1440, "3d": 4320, "1w": 10080, "1M": 43200
# }
# interval_minutes = tf_to_minutes[tf]

# #run starts from here
# try:
#     while True:
#         now = datetime.datetime.now(datetime.timezone.utc)
#         seconds_since_midnight = now.hour * 3600 + now.minute * 60 + now.second
#         interval_seconds = interval_minutes * 60

#         # If the current time is within 2 seconds of an aligned interval
#         if seconds_since_midnight % interval_seconds < 2:
#             run()
#             time.sleep(2)
#         time.sleep(1)
#         print()
#         time.sleep(1)
        
# except KeyboardInterrupt:
#     print("The bot has ended")