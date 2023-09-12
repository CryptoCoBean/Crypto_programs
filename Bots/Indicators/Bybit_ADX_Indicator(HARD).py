#Basic Bybit API Initilisation
import pandas as pd
import numpy as np
from pybit import usdt_perpetual
from datetime import datetime
import calendar
import matplotlib.pyplot as plt

session_auth = usdt_perpetual.HTTP(endpoint='https://api.bybit.com', api_key='api key', api_secret='api secret')

now = datetime.utcnow()
unixtime = calendar.timegm(now.utctimetuple())
since = unixtime #time elapsed Jan 1st 1970 in seconds
start=str(since-(1*86400))
Days_5_back = str(since-(86400*200)) #86400 seconds in a day (2 means yesterday and today etc) (1st number is number of seconds, 2nd is number of data points)

response = (session_auth.query_kline(symbol="BTCUSDT", interval="D",from_time=Days_5_back))['result'] # the current candle is given as the last data point
git = pd.DataFrame(response)
adx_only = git.copy()

### Actual Indicator

#From Github ADX
interval  = 14 #look back period (usually set at 14)

git['-DM'] = git['low'].shift(1) - git['low']
git['+DM'] = git['high'] - git['high'].shift(1)
git['+DM'] = np.where((git['+DM'] > git['-DM']) & (git['+DM']>0), git['+DM'], 0.0)
git['-DM'] = np.where((git['-DM'] > git['+DM']) & (git['-DM']>0), git['-DM'], 0.0)
git['TR_TMP1'] = git['high'] - git['low']
git['TR_TMP2'] = np.abs(git['high'] - git['close'].shift(1)) # not original code
git['TR_TMP3'] = np.abs(git['low'] - git['close'].shift(1))  
git['TR'] = git[['TR_TMP1', 'TR_TMP2', 'TR_TMP3']].max(axis=1)

for i in range(interval-1 , len(git['close'])):
    if(i == interval - 1):
        git.loc[i,'TR_smt'] = git.loc[0:interval, 'TR'].mean()
        git.loc[i,'+DM_smt'] = git.loc[0:interval, '+DM'].mean()
        git.loc[i,'-DM_smt'] = git.loc[0:interval, '-DM'].mean()
    else:
        git.loc[i,'TR_smt'] = ( (git.loc[i-1,'TR_smt'] * (13)) + git.loc[i,'TR'] )/14
        git.loc[i,'+DM_smt'] = ( (git.loc[i-1,'+DM_smt'] * (13)) + git.loc[i,'+DM'] )/14
        git.loc[i,'-DM_smt'] = ( (git.loc[i-1,'-DM_smt'] * (13)) + git.loc[i,'-DM'] )/14


git['+DI'] = ( git['+DM_smt'] / git['TR_smt'] )*100
git['-DI'] = ( git['-DM_smt'] / git['TR_smt'] )*100

git['DX'] = ( abs(git['+DI'] - git['-DI']) / abs(git['+DI'] + git['-DI']) )*100

for i in range(2*(interval-1) , len(git['close'])):
    if(i == 2*(interval - 1)):
        git.loc[i,'ADX'] = git.loc[(interval - 1) : 2*(interval - 1), 'DX'].mean()
    else:
        git.loc[i,'ADX'] = ( (git.loc[i-1,'ADX'] * 13) + git.loc[i,'DX'] )/14

adx_only['ADX'] = git['ADX'] #Starts to get accurate after 5 runs through data (14*5 = 70 data points minimum) (5 standard deviations)

# Displays ADX on a graph 
fig , axis = plt.subplots(2,1)
axis[0].plot(git['close'], linewidth="1.5")
axis[1].plot(git['ADX'] , label = 'ADX', linewidth="1.5")

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
