import random
import time
from datetime import datetime
from pprint import pprint
from fetch_ochlv_for_hl import *
import ccxt
from dex_volume_farming_wallets import *

def open_trade(wallet_name, coin, size, direction):
    
    """
    Opens a real trade on Hyperliquid using the wallet that belongs
    to this wallet_name.
    """
    wallet_info = WALLETS[wallet_name]
    wallet_address = wallet_info["address"]

    exchange = ccxt.hyperliquid({
        "walletAddress": wallet_info["address"],
        "privateKey": wallet_info["private_key"],
        "enableRateLimit": True,
        "timeout": 10000,
        "options": {"defaultSlippage": 0.01}
    })

    exchange.load_markets()

    market = coin
    
    if direction == "long":
        orderbook = exchange.fetch_order_book(coin)
        best_bid = orderbook['asks'][0][0]
        price_bid = best_bid * 0.998  # allow 0.2% slippage
        buy_orders = [
                    {
                    'symbol': coin,
                    'type': "market",
                    'side': "buy",
                    'amount': size,
                    'price': price_bid,
                    'params': {"postOnly": False}
                }]
        
        order = exchange.create_orders(buy_orders)
        print(buy_orders)
        print(f"[TRADE] {wallet_name} → {datetime.now()} {direction.upper()} {coin} size={size}")
    else:
        orderbook = exchange.fetch_order_book(coin)
        best_ask = orderbook['bids'][0][0]
        price_ask = best_ask * 1.002  # allow 0.2% slippage
        sell_orders = [
                    {
                    'symbol': coin,
                    'type': "market",
                    'side': "sell",
                    'amount': size,
                    'price': price_ask,
                    'params': {"postOnly": False}
                }]
        print(sell_orders)
        order = exchange.create_orders(sell_orders)
        print(f"[TRADE] {wallet_name} → {datetime.now()} {direction.upper()} {coin} size={size}")

def close_trade(wallet_name, coin):
        
    """
    Opens a real trade on Hyperliquid using the wallet that belongs
    to this wallet_name.
    """
    wallet_info = WALLETS[wallet_name]
    wallet_address = wallet_info["address"]

    exchange = ccxt.hyperliquid({
        "walletAddress": wallet_info["address"],
        "privateKey": wallet_info["private_key"],
        "enableRateLimit": True,
        "timeout": 10000,
        "options": {"defaultSlippage": 0.01}
    })

    exchange.load_markets()
    
    symbol = coin
    if (exchange.fetch_positions()):
        print("There is a trade open on this wallet")
        size = float(exchange.fetch_positions()[0]['info']['position']['szi'])
        if (exchange.fetch_positions()[0]['info']['position']['szi'] > "0"):
            print("Current trade open is a long")
            close_direction = "sell"
            orderbook = exchange.fetch_order_book(coin)
            best_ask = orderbook['bids'][0][0]
            price_ask = best_ask * 1.002  # allow 0.2% slippage
            size = abs(size)
            close_long_order = exchange.create_order(symbol=symbol,type="market", side="sell", amount=size, price=price_ask, params={"reduceOnly": True})
            print(close_long_order)
        else:
            pass
            
        if (exchange.fetch_positions()[0]['info']['position']['szi'] < "0"):
            print("Current trade open is a short")
            close_direction = "buy"
            orderbook = exchange.fetch_order_book(coin)
            best_bid = orderbook['asks'][0][0]
            price_bid = best_bid * 0.998  # allow 0.2% slippage
            size = abs(size)
            close_short_order = exchange.create_order(symbol=symbol,type="market", side="buy", amount=size, price=price_bid, params={"reduceOnly": True})
            print(close_short_order)
        else:
            pass

        print(f"[CLOSE TRADE] {wallet_name} → {datetime.now()} {close_direction.upper()} {coin} size={size}")
    else:
        print("No open trade for this wallet")
 
def execute_pair_trades(pairs_dict, coin, min_sleep=0, max_sleep=10):
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
            
            rand_num_sleep = round(random.uniform(min_sleep, max_sleep), 2)

            # Open long for first wallet
            open_trade(wallet_long, coin, size, direction="long")
            print(f"{wallet_long}, {size}, long")
            time.sleep(rand_num_sleep)

            # Open short for second wallet
            open_trade(wallet_short, coin, size, direction="short")
            print(f"{wallet_short}, {size}, short")
            time.sleep(rand_num_sleep)

    # Optional: handle leftover wallet (if any)
    leftover = pairs_dict.get("leftover")
    if leftover:
        print(f"[INFO] Leftover wallet with no pair: {leftover}")

def generate_wallet_pairs(data, number_min=0.004, number_max=0.01, min_sleep=1, max_sleep=3):
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
        # rand_num_sleep = round(random.uniform(min_sleep, max_sleep), 2)
        pairs.append({
            "wallets": [k1, k2],
            "size": rand_num
            # "sleep": rand_num_sleep
        })

    # Handle leftover wallet (if odd count)
    if len(keys) % 2 == 1:
        leftover = keys[-1]



    # Return results
    return {
        "pairs": pairs,
        "leftover": leftover,
    }

def close_all_trades(coin):
    """
    Loops through every wallet and closes the first open trade.
    """
    for wallet_name in WALLETS.keys():
        print(f"\n--- Closing trade for {wallet_name} ---")
        try:
            print("Running code block")
            close_trade(wallet_name, coin)
        except Exception as e:
            print(f"[ERROR] Could not close trade for {wallet_name}: {e}")

def all_positions():
    for wallet_name in WALLETS.keys():
        print(f"\n--- Positions on {wallet_name} ---")
        try:
            wallet_info = WALLETS[wallet_name]
            wallet_address = wallet_info["address"]

            exchange = ccxt.hyperliquid({
                "walletAddress": wallet_info["address"],
                "privateKey": wallet_info["private_key"],
                "enableRateLimit": True,
                "timeout": 10000,
                "options": {"defaultSlippage": 0.01}
            })

            exchange.load_markets()
    
            if (exchange.fetch_positions()):
                print("There is a trade open on this wallet")
                print()
                print("size:", exchange.fetch_positions()[0]['info']['position']['szi'])
                print("positionValue: ", exchange.fetch_positions()[0]['info']['position']['positionValue'])
                print("pnl: ", exchange.fetch_positions()[0]['info']['position']['unrealizedPnl'])
            else:
                print("There is no trade open on this wallet")
            
        except Exception as e:
            print(f"[ERROR] Could not close trade for {wallet_name}: {e}")
    


coin = "ETH/USDC:USDC"

# Open trades:
# pairs_dict = generate_wallet_pairs(WALLETS)
# pprint(pairs_dict)
# execute_pair_trades(pairs_dict, coin)


# Close all trades at once
# close_all_trades(coin)


# Show all trades at once
all_positions()