#This program is used to calculate the total profit probable with arbing funding rates on a single exchange
import time
def main():
    amount = int(input("Total amount available for Arbing:  "))
    tradeamount = amount/2
    time.sleep(1)
    print(" ")
    pair = input("What is the pair you are aiming to arb (enter only asset name):   ")
    time.sleep(1)
    print(" ")
    print("You will use ${0} to short on {1}PERP, and buy ${0} worth of {1} on the spot market".format(tradeamount,pair))
    time.sleep(1)
    print(" ")
    price = float(input("What is the price of {0} currently:    ".format(pair)))
    time.sleep(1)
    print(" ")
    one_day_FR = float(input("What is the 1day cumulative funding rate(%):  "))
    APR = (365/6) * (one_day_FR) 
    # 4 total trades for entering and exiting the 2 trades (used bybit taker percentage as its the highest fees for the sake of the calculation) 
    fees = ((0.01/100 * tradeamount) *2) + ((0.1/100*tradeamount)*2)
    funding_position = False
    if one_day_FR < 0:
        funding_position = False
    else:
        funding_position = True
    return amount, tradeamount, pair, one_day_FR, funding_position, price, APR, fees


def positive_funding(tradeamount, pair, one_day_FR, price, APR, fees):
    time.sleep(1)
    print(" ")
    print("The yearly APR percentage is:    {0}%".format(APR))
    time.sleep(1)
    print(" ")
    print("Calculating potential profit...  ")
    time.sleep(1)
    print(" ")
    print("Shorting ${0} worth of {1} perp...".format(tradeamount,pair))
    time.sleep(1)
    print(" ")
    # 4 total trades for entering and exiting the 2 trades (used bybit taker percentage as its the highest fees for the sake of the calculation) 
    print("The total fees of the trades will be {0}".format(fees))
    time.sleep(1)
    print(" ")
    potentialprofit_oneday = (((((one_day_FR/100) + 1)*tradeamount)-tradeamount)/2)-fees
    print("The total potential is ${0} over 1 day with fees".format(potentialprofit_oneday))
    potentialprofit_fivedays = potentialprofit_oneday*5+(4*fees)
    print(" ")
    print("The total potential is ${0} over 5 days with fees".format(potentialprofit_fivedays))
    time.sleep(1)
    print(" ")
    #Need to incorporate enter and exit market fees
    liquidation_pos_FR = price * 2
    print("The liquidation price of your position is: ${0}".format(liquidation_pos_FR))
    time.sleep(1)

def negative_funding(one_day_FR,tradeamount,pair, APR, fees):
    one_day_FR = abs(one_day_FR)
    time.sleep(1)
    print(" ")
    APR = abs(APR)
    print("The yearly APR percentage is:    {0}%".format(APR))
    time.sleep(1)
    print(" ")
    print("Calculating potential profit...  ")
    time.sleep(1)
    print(" ")
    print("Longing ${0} worth of {1} perp...".format(tradeamount,pair))
    print("Borrowing and selling ${0} worth of {1} on the spot market ".format(tradeamount,pair))
    time.sleep(1)
    print(" ")
    print("total fees is: {0}".format(fees))

if __name__ == "__main__":
    amount, tradeamount, pair, one_day_FR, funding_position, price, APR, fees = main()
    if funding_position == True:
        positive_funding(tradeamount, pair, one_day_FR, price, APR, fees)
    else:
        negative_funding(one_day_FR, tradeamount,pair, APR, fees)

    print(" ")
    print("All Calculations are Done... ")