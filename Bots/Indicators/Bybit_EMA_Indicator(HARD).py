#Basic BYBIT API Initilisation
import pandas as pd
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
df = pd.DataFrame(response)


#EMA Indicator starts from here for both 12 and 21 EMAs 
#12 EMA
ema1 = 12
df['12EMA'] = df['close'].ewm(alpha=(2/float(ema1 + 1)), adjust=False).mean()
#21 EMA
ema2 = 21
df['21EMA'] = df['close'].ewm(alpha=(2/float(ema2 +1)), adjust=False).mean()

#Plotting the chart with the EMAs


plt.tick_params(axis = 'both', labelsize = 10)
# plot close price, short-term and long-term moving averages 
df['close'].plot(label = 'Closes')  
df['12EMA'].plot(label = '12-day EMA') 
df['21EMA'].plot(label = '21-day EMA') 

plt.xlabel("Days")
plt.ylabel("Price")
plt.title('12 & 21 EMA Crossover', fontsize = 20)
plt.legend()
plt.grid()
plt.show()
