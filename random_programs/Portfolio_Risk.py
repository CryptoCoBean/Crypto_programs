import pandas
positions = int(input("How many positions are you in?"))
number1 = 3- positions
number2 = positions - 3
if positions > 3:
    print("time to derisk {0} of your positions".format(number2))
else:
    print("You have {0} more positions that you can take".format(number1))

total_risk = 0
for x in range (1,positions+1):
    risk = float(input("What is the risk of your {0} trade".format(x)))
    total_risk = total_risk + risk

print("Your total risk to your portfolio is: {0}".format(total_risk))

if total_risk > 5:
    print("you should derisk by {0} in either of your {1} trades".format((5-total_risk),positions))
else:
    print("you are under or at the current risk tolerance")
