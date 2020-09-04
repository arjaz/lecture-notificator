from telegram.ext import Updater, InlineQueryHandler, CommandHandler
import requests
import re
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)


def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
        "I will provide notification before your lectures. Feel free to contact @arjaz for any help."
    )


def bop_command(update, context):
    def get_url():
        contents = requests.get('https://random.dog/woof.json').json()
        url = contents['url']
        return url

    url = get_url()
    chat_id = update.message.chat_id
    context.bot.send_photo(chat_id=update.message.chat_id, photo=url)


def main():
    '''Start the bot'''
    # Create the Updater and pass it your bot's token.
    updater = Updater('1265390639:AAHrUXDmTx-So3HJlM_s8ZL_zlcoFAiaErY',
                      use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add commands handling
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('bop', bop_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
