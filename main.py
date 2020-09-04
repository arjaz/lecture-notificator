import requests
import re
import logging
import sqlalchemy

from functools import partial
from telegram.ext import Updater, InlineQueryHandler, CommandHandler

import db


def start(database, update, context):
    '''Print starting message'''
    logging.info(f'{update.effective_chat.username} started the bot')

    listener = db.Listener(id=update.effective_chat.id)

    try:
        database.session.add(listener)
        database.session.commit()
    except sqlalchemy.exc.IntegrityError:
        pass

    update.message.reply_text(
        'I will provide notification before your lectures. Feel free to contact @arjaz for any help.'
    )


def help(database, update, context):
    '''Gives detailed information about the bot and its commands'''
    pass


def subscribe(database, update, context):
    '''Subscribe the user to a group'''
    try:
        group_name = context.args[0]
    except IndexError:
        update.message.reply_text('No group specified')
        return

    try:
        group = database.session.query(
            db.Group).filter(db.Group.name == group_name).one()
    except sqlalchemy.orm.exc.NoResultFound:
        update.message.reply_text('No group found with the specified name')
        return

    try:
        listener = database.session.query(db.Listener).filter(
            db.Listener.id == update.effective_chat.id).one()
    except sqlalchemy.orm.exc.NoResultFound:
        update.message.reply_text(
            'Please, use the /start command so that the bot can remember you')
        return

    listener.group_id = group.id
    database.session.commit()


def bop(database, update, context):
    '''Fetch a random dog image and serve it to the client'''
    logging.info(f'{update.effective_chat.id} bops')

    def get_url():
        contents = requests.get('https://random.dog/woof.json').json()
        url = contents['url']
        return url

    url = get_url()
    context.bot.send_photo(chat_id=update.message.chat_id, photo=url)


def main():
    '''Start the bot'''
    # Handle the database
    database = db.Database()

    # Create the Updater and pass it your bot's token.
    updater = Updater('1265390639:AAHrUXDmTx-So3HJlM_s8ZL_zlcoFAiaErY',
                      use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add commands handling
    callbacks = [
        ('start', start),
        ('bop', bop),
        ('subscribe', subscribe),
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
