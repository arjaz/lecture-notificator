import requests
import re
import logging
import sqlalchemy
import time
import datetime

from functools import partial
from telegram.ext import Updater, InlineQueryHandler, CommandHandler

from db import Database, Listener, Group


# TODO: come up with a way to get the notifications be persistent
def check_notify(context):
    job = context.job

    database = context.job.context['database']
    listener = context.job.context['listener']

    t = time.time()

    if 'last_time' not in job.__dict__:
        job.last_time = t
    elif t - job.last_time < (60 * 60):
        return

    # Get current date and time
    current_time = time.localtime(t)

    # Check if the listener is subscribed to a group
    if listener.group_id is None:
        return

    group = database.session.query(Group).get(listener.group_id)

    for lecture in group.lectures:
        current_day = current_time.tm_wday
        current_minute = current_time.tm_hour * 60 + current_time.tm_min
        # TODO: check the current week against the lecture's one
        current_week = 1

        if current_day == lecture.day and current_minute + 10 == lecture.time and current_week == lecture.week:
            context.bot.send_message(
                chat_id=context.job.context['chat_id'],
                text=
                f'Your lecture "{lecture.name}" will start in 10 minutes. Be ready.'
            )
            logging.info(
                f'NOTIFICATION TO USER {listener.id} ABOUT LECTURE {lecture.name}'
            )


def start(database, update, context):
    '''Print starting message'''
    logging.info(f'{update.effective_chat.username} started the bot')

    listener = Listener(id=update.effective_chat.id,
                        username=update.effective_chat.username)

    try:
        database.session.add(listener)
        database.session.commit()
    except sqlalchemy.exc.IntegrityError:
        pass

    update.message.reply_text(
        'I will provide notification before your lectures.'
        'Feel free to contact @arjaz for any help.')


def help(database, update, context):
    '''Gives detailed information about the bot and its commands'''
    pass


def unsubscribe(database, update, context):
    '''Unsubscribe the user from a group'''
    # Get the user from the database
    try:
        listener = database.session.query(Listener).filter(
            Listener.id == update.effective_chat.id).one()
    except sqlalchemy.orm.exc.NoResultFound:
        logging.info('No listener found')
        return
        # listener = Listener(id=update.effective_chat.id)

    listener.group_id = None
    database.session.commit()


def subscribe(database, update, context):
    '''Subscribe the user to a group'''

    # Get the group name
    try:
        group_name = context.args[0]
    except IndexError:
        update.message.reply_text('No group specified')
        return

    # Get the group from the database
    try:
        logging.info(f'Getting group {group_name}')
        group = database.session.query(Group).filter(
            Group.name == group_name).one()
    except sqlalchemy.orm.exc.NoResultFound:
        update.message.reply_text('No group found with the specified name')
        return

    # Get the user from the database
    try:
        listener = database.session.query(Listener).filter(
            Listener.id == update.effective_chat.id).one()
    except sqlalchemy.orm.exc.NoResultFound:
        listener = Listener(id=update.effective_chat.id,
                            user=update.effective_chat.username)

    listener.group_id = group.id
    logging.info(
        f'Subscribing {update.effective_chat.username} to group {group.name}')
    database.session.commit()

    update.message.reply_text('You will be notified about your lectures')

    # start the notification job
    if 'job' in context.chat_data:
        old_job = context.chat_data['job']
        old_job.schedule_removal()

    WAIT_TIME = 30
    new_job = context.job_queue.run_repeating(check_notify,
                                              context={
                                                  'database':
                                                  database,
                                                  'listener':
                                                  listener,
                                                  'chat_id':
                                                  update.effective_chat.id
                                              },
                                              interval=WAIT_TIME,
                                              first=0)
    context.chat_data['job'] = new_job


def beep(database, update, context):
    if 'job' in context.chat_data:
        old_job = context.chat_data['job']
        old_job.schedule_removal()
    new_job = context.job_queue.run_once(alarm,
                                         5,
                                         context=update.effective_chat.id)
    context.chat_data['job'] = new_job
    update.message.reply_text('Job scheduled')


def alarm(context):
    job = context.job
    context.bot.send_message(job.context, text='Beep')


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
    database = Database()

    # Create the Updater and pass it your bot's token.
    updater = Updater('1265390639:AAHrUXDmTx-So3HJlM_s8ZL_zlcoFAiaErY',
                      use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add commands handling
    callbacks = [
        ('start', start),
        ('bop', bop),
        ('beep', beep),
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
