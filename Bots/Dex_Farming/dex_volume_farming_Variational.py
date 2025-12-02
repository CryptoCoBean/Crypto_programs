import random
import time
from pprint import pprint

# def open_trade(wallet,coin, size): # size, direction, postonly
#     open_trade


def open_trade(wallet, coin, size, direction):
    """
    Dummy open_trade function placeholder.
    Replace this with your actual trading logic.
    """
    print(f"[TRADE] {wallet} → {direction.upper()} {coin} @ {size}")


def execute_pair_trades(pairs_dict, coin):
    """
    Executes two trades for each wallet pair:
      - First wallet goes LONG
      - Second wallet goes SHORT

    Args:
        pairs_dict (dict): output from generate_wallet_pairs()
        coin (str): coin symbol to trade (e.g. "ETH", "BTC")
    """
    pairs = pairs_dict.get("pairs", [])

    for pair in pairs:
        wallets = pair["wallets"]
        size = pair["size"]

        if len(wallets) == 2:
            wallet_long, wallet_short = wallets

            # Open long for first wallet
            open_trade(wallet_long, coin, size, direction="long")
            
                # # Simulate random pause
                # sleep_time = round(random.uniform(min_sleep, max_sleep), 2)
                # time.sleep(sleep_time)

            # Open short for second wallet
            open_trade(wallet_short, coin, size, direction="short")

    # Optional: handle leftover wallet (if any)
    leftover = pairs_dict.get("leftover")
    if leftover:
        print(f"[INFO] Leftover wallet with no pair: {leftover}")

    # print(f"[SLEEP] Delay was {pairs_dict['sleep']} seconds")


def generate_wallet_pairs(data, number_min=0.05, number_max=0.1, min_sleep=1, max_sleep=3):
    """
    Generate randomized wallet pairs with random sizes (single run).

    Args:
        data (dict): Dictionary of wallets (keys) and IDs (values)
        number_min (float): Minimum random size value
        number_max (float): Maximum random size value
        min_sleep (float): Minimum delay between runs (seconds)
        max_sleep (float): Maximum delay between runs (seconds)
    """
    
    keys = list(data.keys())
    random.shuffle(keys)

    pairs = []
    leftover = None

    # Generate random pairs
    for i in range(0, len(keys) - 1, 2):
        k1, k2 = keys[i], keys[i + 1]
        rand_num = round(random.uniform(number_min, number_max), 3)
        pairs.append({
            "wallets": [k1, k2],
            "size": rand_num
        })

    # Handle leftover wallet (if odd count)
    if len(keys) % 2 == 1:
        leftover = keys[-1]



    # Return results
    return {
        "pairs": pairs,
        "leftover": leftover,
    }
    
    
data = {
    "wlt 1": 1,
    "wlt 2": 2,
    "wlt 3": 3,
    "wlt 4": 4,
    "wlt 5": 5,
    "wlt 6": 6
}

pairs_dict = generate_wallet_pairs(data)
pprint(pairs_dict)
execute_pair_trades(pairs_dict, coin="ETH")

# from pprint import pprint
# pprint(pairs_dict)
