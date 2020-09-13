import logging
import sqlalchemy
import time
import asyncio

from db import Listener, Group, Database


def start(database, update, context):
    '''Print starting message'''
    logging.info(f'{update.effective_chat.username} started the bot')

    # Check if the listener already exists in the database
    # and add him if not
    if not database.session.query(sqlalchemy.exists().where(
            Listener.id == update.effective_chat.id)).scalar():
        listener = Listener(id=update.effective_chat.id,
                            username=update.effective_chat.username)
        database.session.add(listener)
        database.session.commit()

    update.message.reply_text(
        'I will provide notification before your lectures. '
        'Feel free to contact @arjaz for any help.')


def help(database, update, context):
    '''Gives detailed information about the bot and its commands'''

    update.message.reply_text('/start - register yourself in the database\n'
                              '/subscribe <group> - subscribe to a group\n'
                              '/unsubscribe - unsubscribe from your group\n'
                              '/stop - unsubscribe from your group')


def unsubscribe(database, update, context):
    '''Unsubscribe the user from a group'''
    # Get the user from the database
    try:
        listener = database.session.query(Listener).get(
            update.effective_chat.id)
        logging.info(f'Unsubscribing {listener.username} from his group')
    except sqlalchemy.orm.exc.NoResultFound:
        logging.info('No listener found')
        return

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
        listener = database.session.query(Listener).get(
            update.effective_chat.id)
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


async def check_notify_all(updater):
    while True:
        database = Database()

        t = time.time()
        current_time = time.localtime(t)

        for listener in database.session.query(Listener).filter(
                Listener.group_id is not None):
            group = database.session.query(Group).get(listener.group_id)

            for lecture in group.lectures:
                current_day = current_time.tm_wday
                current_minute = current_time.tm_hour * 60 + current_time.tm_min
                # TODO: check the current week against the lecture's one
                current_week = 1

                if (current_day == lecture.day
                        and current_minute + 10 == lecture.time
                        and current_week == lecture.week):
                    updater.bot.send_message(
                        chat_id=listener.id,
                        text=f'Your lecture "{lecture.name}" '
                        'will start in 10 minutes. '
                        'Be ready.')
                    logging.info(
                        f'Notifying {listener.username} about {lecture.name}')
        # Wait for some time before the next check
        WAIT_TIME = 5
        await asyncio.sleep(WAIT_TIME)
