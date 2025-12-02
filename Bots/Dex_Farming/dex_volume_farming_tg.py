import threading
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import dex_volume_farming_Hyperliquid as dex_volume_farming

TELEGRAM_TOKEN = ""
AUTHORIZED_USER_ID = 1943535732  # Telegram numeric ID (Crytcobean)


# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "Welcome to the Trading Bot 🤖\n\n"
        "Commands:\n"
        "/open {direction} {coin} {size}\n"
        "/close {direction} {coin} {size}\n"
        "/balance"
    )
    await update.message.reply_text(msg)


# === /open ===
async def open_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        direction, coin, size = context.args
        size = float(size)

        result = dex_volume_farming.open_trade_wlt_1(direction, coin, size)
        await update.message.reply_text(f"✅ {result}")

    except ValueError:
        await update.message.reply_text("❌ Usage: /open {direction} {coin} {size}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


# === /close ===
async def close_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        direction, coin, size = context.args
        size = float(size)

        result = dex_volume_farming.close_trade_wlt_1(direction, coin, size)
        await update.message.reply_text(f"✅ {result}")

    except ValueError:
        await update.message.reply_text("❌ Usage: /close {direction} {coin} {size}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# === /balance ===
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        balances = dex_volume_farming.get_balance()
        text = "\n".join([f"{k}: {v}" for k, v in balances.items()])
        await update.message.reply_text(f"💰 Balances:\n{text}")

    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching balance: {e}")



# === Run the bot ===
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("open", open_command))
    app.add_handler(CommandHandler("close", close_command))
    app.add_handler(CommandHandler("balance", balance_command))

    print("🤖 Telegram bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()