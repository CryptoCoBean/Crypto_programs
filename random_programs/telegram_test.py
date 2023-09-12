# telegram bot name: pytelesample_bot, can be found here t.me/pytelesample_bot
# telegram bot HTTP API key "5845725471:AAHcEIk_2i8tIEKR80DWTLuvtbESWLSy0vU"

from telegram.ext import *
from telegram.update import Update

API = "telegram api"

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hello this is a test bot")

def help(update: Update, context: CallbackContext):
    update.message.reply_text("contact Rahul")

def unknown_text(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Sorry I can't recognize you , you said '%s'" % update.message.text)

def definition_of_stupid(update: Update, context: CallbackContext):
    update.message.reply_text("Liam")

def unknown(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Sorry '%s' is not a valid command" % update.message.text)

updater = Updater(API, use_context=True)
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('help', help))
updater.dispatcher.add_handler(CommandHandler('definition_of_stupid', definition_of_stupid))
updater.dispatcher.add_handler(MessageHandler(Filters.text, unknown))
updater.dispatcher.add_handler(MessageHandler(Filters.command, unknown))  # Filters out unknown commands
print("Bot Started...")

# Filters out unknown messages.
updater.dispatcher.add_handler(MessageHandler(Filters.text, unknown_text))
  
updater.start_polling()
