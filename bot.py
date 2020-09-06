import logging
import sqlalchemy
import time

from db import Listener, Group


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

        if (current_day == lecture.day and current_minute + 10 == lecture.time
                and current_week == lecture.week):
            context.bot.send_message(
                chat_id=context.job.context['chat_id'],
                text=f'Your lecture "{lecture.name}" will start in 10 minutes.'
                'Be ready.')
            logging.info(f'Notifying {listener.username} about {lecture.name}')


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


# TODO: add help messages
def help(database, update, context):
    '''Gives detailed information about the bot and its commands'''
    pass


def unsubscribe(database, update, context):
    '''Unsubscribe the user from a group'''
    # Get the user from the database
    try:
        listener = database.session.query(Listener).get(
            update.effective_chat.id)
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
