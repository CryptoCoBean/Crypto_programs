from pybit import usdt_perpetual
import time
from telegram.ext import *
from telegram.update import Update

API = "telegram api"

session = usdt_perpetual.HTTP(endpoint='https://api.bybit.com', 
    api_key='apikey',
    api_secret='api secret')


def alarm(update: Update, context: CallbackContext):
    coin = str(input("What coin do you want to create an alert for? "))
    target = float(input("What is your target price for {0}USDT_perp? ".format(coin)))
    response = True

    while response:
        higher_or_lower = input("Do you want to know if {0} price is higher or lower than {1}? ".format(coin,target))
        if higher_or_lower == "higher" or "lower":
            response = False
        else:
            response = True
    alert = True

    if higher_or_lower == "higher":
        while alert == True:
            time.sleep(1)
            information = session.latest_information_for_symbol(symbol="{0}USDT".format(coin))
            information = information.get('result')
            information = information[0]
            price = information.get("last_price")
            price = float(price)
            #print(price)
            #print("the price of BTCUSDT is: {0}".format(price))
            if (price == target) or (price > target):
                print("{0}USDT has hit the target price of {1}".format(coin, target))
                update.message.reply_text("{0}USDT has hit the target price of {1}".format(coin, target))
                #print("the market price is {0}".format(information))
                alert = False
            else:
                pass

    else:
        while alert == True:
            time.sleep(1)
            information = session.latest_information_for_symbol(symbol="{0}USDT".format(coin))
            information = information.get('result')
            information = information[0]
            price = information.get("last_price")
            price = float(price)
            #print(price)
            #print("the price of BTCUSDT is: {0}".format(price))
            if (price == target) or (price < target):
                print("{0}USDT has hit the target price of {1}".format(coin, target))
                update.message.reply_text("{0}USDT has hit the target price of {1}".format(coin, target))
                alert = False
            else:
                pass

updater = Updater(API, use_context=True)
updater.dispatcher.add_handler(CommandHandler('alarm', alarm))
print("Bot Started...")

updater.start_polling()

# need to get inputs and ask questions from within telegram that way user won't have to go back and forth
