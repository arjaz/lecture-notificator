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
    updater = Updater('1265390639:AAHrUXDmTx-So3HJlM_s8ZL_zlcoFAiaErY',
                      use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('bop', bop_command))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
