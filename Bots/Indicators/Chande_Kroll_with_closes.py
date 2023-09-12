# -*- coding: utf-8 -*-
from pandas import DataFrame
from pandas_ta.volatility import atr
from pandas_ta.utils import get_offset, verify_series

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