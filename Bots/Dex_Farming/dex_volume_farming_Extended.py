import random
import asyncio
import sys
from datetime import datetime
from pprint import pprint

from dex_volume_farming_wallets import *

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    
from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.trading_client import PerpetualTradingClient
from x10.perpetual.configuration import MAINNET_CONFIG
from x10.perpetual.orders import OrderSide
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from x10.perpetual.markets import TradingConfigModel
# -------------------------------------------------------------
#  Helper: create a connected X10 client for a specific wallet
# -------------------------------------------------------------
async def get_client(wallet_name):
    wallet_info = WALLETS_10X[wallet_name]

    account = StarkPerpetualAccount(
        vault  = wallet_info["VAULT_ID"],
        private_key= wallet_info["PRIVATE_KEY"],
        public_key= wallet_info["PUBLIC_KEY"],
        api_key= wallet_info["API_KEY"]
    )

    client = PerpetualTradingClient(
        endpoint_config=MAINNET_CONFIG,
        stark_account=account,
    )
    return client
    
# -------------------------------------------------------------
#  Async open trade
# -------------------------------------------------------------
async def open_trade(wallet_name, market, size, direction):
    client = await get_client(wallet_name)
    
    size = Decimal(size)
    symbol = market
    
    def get_adjust_price_by_pct(config: TradingConfigModel):
        def adjust_price_by_pct(price: Decimal, pct: int):
            return config.round_price(price + price * Decimal(pct) / 100)

        return adjust_price_by_pct
    
    markets_dict = await client.markets_info.get_markets_dict()

    market = markets_dict[symbol]
    # print(market)
    adjust_price_by_pct = get_adjust_price_by_pct(market.trading_config)
    order_size = market.trading_config.min_order_size
    
    if direction == "long":
        order_price = adjust_price_by_pct(market.market_stats.ask_price, 0.02)
        side = OrderSide.BUY
    else:
        order_price = adjust_price_by_pct(market.market_stats.bid_price, -0.02)
        side = OrderSide.SELL
    
    # print(order_size)
    # print(order_price)
    
    def round_size(size: Decimal, tick: Decimal, side: OrderSide):
        """
        Round order size to the nearest allowed tick.
        BUY: ROUND_DOWN (so you don't exceed funds)
        SELL: ROUND_DOWN (so you don't oversell)
        """
        return (size / tick).quantize(0, rounding=ROUND_DOWN) * tick

    size = size / order_price
    size = round_size(size, order_size, side)

    print(f"[OPEN] {wallet_name} {direction.upper()} {symbol} size={size} price={order_price}")

    await client.place_order(
        market_name=symbol,
        amount_of_synthetic=Decimal(str(size)),
        price=order_price,
        side=side,
        post_only=False,
        # reduce_only=False,
    )   
    await client.close()

# -------------------------------------------------------------
#  Async close trade
# -------------------------------------------------------------
async def close_trade(wallet_name, market):
    client = await get_client(wallet_name)
    
    def get_adjust_price_by_pct(config: TradingConfigModel):
        def adjust_price_by_pct(price: Decimal, pct: int):
            return config.round_price(price + price * Decimal(pct) / 100)

        return adjust_price_by_pct

    positions = await client.account.get_positions()
    if not positions:
        print(f"[NO POSITION] {wallet_name}")
        await client.close()
        return

    markets_dict = await client.markets_info.get_markets_dict()  # symbol -> market object
    # Take the first position (or loop through all positions if multiple)
    for position in positions.data:
        symbol = position.market
        side = position.side
        size = Decimal(position.size)
        print(side)
        
        # Get the full market object
        market = markets_dict.get(symbol)
        
        adjust_price_by_pct = get_adjust_price_by_pct(market.trading_config)
        
        if side.upper() == "LONG":
            order_price = adjust_price_by_pct(market.market_stats.ask_price, -0.02)
            side = OrderSide.SELL
        else:
            order_price = adjust_price_by_pct(market.market_stats.bid_price, 0.02)
            side = OrderSide.BUY      
                
        await client.place_order(
            market_name=symbol,
            amount_of_synthetic=size,
            price=order_price,
            side=side,
            reduce_only=True
        )

    await client.close()


# -------------------------------------------------------------
#  Async paired trading (long + short)
# -------------------------------------------------------------
async def execute_pair_trades(pairs_dict, market, min_sleep=0, max_sleep=3):
    pairs = pairs_dict.get("pairs", [])

    for pair in pairs:
        w1, w2 = pair["wallets"]
        size = pair["size"]

        print(f"\nPAIR: {w1} LONG | {w2} SHORT | size={size}")
        await open_trade(w1, market, size, "long")

        await asyncio.sleep(random.uniform(min_sleep, max_sleep))

        await open_trade(w2, market, size, "short")

        await asyncio.sleep(random.uniform(min_sleep, max_sleep))


# -------------------------------------------------------------
#  Generate wallet pairs (unchanged)
# -------------------------------------------------------------
def generate_wallet_pairs(data, number_min=35, number_max=200): # size is in $ amounts
    keys = list(data.keys())
    random.shuffle(keys)

    pairs = []
    leftover = None

    for i in range(0, len(keys) - 1, 2):
        k1, k2 = keys[i], keys[i + 1]
        size = round(random.uniform(number_min, number_max), 3)
        pairs.append({"wallets": [k1, k2], "size": size})

    if len(keys) % 2 == 1:
        leftover = keys[-1]

    return {"pairs": pairs, "leftover": leftover}


# -------------------------------------------------------------
#  CLOSE ALL TRADES ASYNC
# -------------------------------------------------------------
async def close_all_trades(market):
    for wallet_name in WALLETS_10X.keys():
        print(f"\n-- Closing {wallet_name}")
        try:
            await close_trade(wallet_name, market)
        except Exception as e:
            print(f"[ERROR] {wallet_name}: {e}")


# -------------------------------------------------------------
#  SEE ALL WALLET POSITIONS
# -------------------------------------------------------------
async def all_positions():

    for wallet_name in WALLETS_10X.keys():
        print(f"\n--- Positions on {wallet_name} ---")

        try:
            wallet_info = WALLETS_10X[wallet_name]

            stark_account = StarkPerpetualAccount(
                vault=wallet_info["VAULT_ID"],
                private_key=wallet_info["PRIVATE_KEY"],
                public_key=wallet_info["PUBLIC_KEY"],
                api_key=wallet_info["API_KEY"]
            )

            exchange = PerpetualTradingClient(
                endpoint_config=MAINNET_CONFIG,
                stark_account=stark_account,
            )
            
            positions = await exchange.account.get_positions()
            await exchange.close()  # IMPORTANT
            
            if len(positions.data) == 0:
                print("There is no trade on this wallet")
            else:
                for position in positions.data:
                    print(
                        f"market: {position.market} \
                        side: {position.side} \
                        size: {position.size} \
                        mark_price: ${position.mark_price} \
                        leverage: {position.leverage}"
                    )
                    print(f"consumed im: ${round((position.size * position.mark_price) / position.leverage, 2)}")

        except Exception as e:
            print(f"[ERROR] Could not see any trade for {wallet_name}: {e}")


# -------------------------------------------------------------
#  MAIN EXECUTION
# -------------------------------------------------------------
async def main():
    market = "ETH-USD"   # correct format for Extended

    pairs_dict = generate_wallet_pairs(WALLETS_10X)
    pprint(pairs_dict)

    # await execute_pair_trades(pairs_dict, market)

    # await close_all_trades(market)
    
    await all_positions()


asyncio.run(main())
