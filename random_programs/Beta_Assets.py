import os
import pandas_datareader as w
import pandas as pd

s = ['^GSPC', 'ETH-USD']
d1 = '2022-01-01'
d2 =  '2022-10-12'

spx = w.get_data_yahoo(s[0], start=d1, end=d2)
eth = w.get_data_yahoo(s[0], start=d1, end=d2)

spx_daily = spx['Adj Close'].pct_change()
eth_daily = eth['Adj Close'].pct_change()

spx_daily = spx_daily[1:]
eth_daily = eth_daily[1:]

covariance_var = eth_daily.cov(spx_daily)
variance_var = spx_daily.var()
beta = covariance_var / variance_var

print('The beta of eth relative to is ' + str(beta))