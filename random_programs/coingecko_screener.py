from pycoingecko import CoinGeckoAPI
import json
import requests

print("")
cg = CoinGeckoAPI()
trending = cg.get_search_trending()
response = requests.get("https://api.coingecko.com/api/v3/search/trending").text
response_info = json.loads(response)
#print(response_info)
Trending_Coins1 = []
Trending_names = []
#print(response_info)

for coins in response_info['coins']:
    Trending_Coins1.append([coins['item']]) #, country_info[‘TotalConfirmed’]])
#print(Trending_Coins1)

for x in range (0,6):
    for names in Trending_Coins1[x]:
        Trending_names.append([names['id']]) # ,names['score'], names['market_cap_rank']))
#print(Trending_names)

info_list = []
for x in range(0,6):
    info = cg.get_price(ids=Trending_names[x], vs_currencies='usd') #, include_market_cap=True), include_24hr_vol=True, include_24hr_change=True)
    info_list.append(info)

#print(info_list)
for x in range(0,6):
    y = info_list[x]
    print(y)


#trending_df = pd.PandasRequest(data=info_list, columns=['Coin', 'price_usd']) #,'usd_market_cap', 'usd_24h_vol', 'usd_24h_change'])
#print(info_list)