import os
import logging

from functools import partial
from telegram.ext import Updater, CommandHandler

from db import Database
from bot import start, subscribe, unsubscribe


def main():
    '''Start the bot'''

    # Handle the database
    database = Database()

    # Create the Updater and pass it your bot's token.
    token = os.environ.get('TELEGRAM_TOKEN')
    updater = Updater(token, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add commands handling
    callbacks = [
        ('start', start),
        ('subscribe', subscribe),
        ('unsubscribe', unsubscribe),
        ('stop', unsubscribe),
    ]
    for callback in callbacks:
        (name, handler) = callback
        handler_with_database = partial(handler, database)
        dp.add_handler(CommandHandler(name, handler_with_database))

    logging.info('Starting the bot...')

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

    logging.info('Finishing the bot...')

    database.session.commit()


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

    main()
