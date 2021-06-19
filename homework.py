import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv
from telegram.ext import Filters, Updater
from telegram.ext.messagehandler import MessageHandler

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)

PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
API = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    elif status == 'reviewing':
        verdict = 'Работа ушла на ревью'
    else:
        verdict = (
            'Ревьюеру всё понравилось, можно приступать к следующему уроку.')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    params = {'from_date': current_timestamp}
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    homework_statuses = requests.get(API, params=params, headers=headers)
    return homework_statuses.json()


def send_message(message, bot_client):
    log = message.replace('\n', '')
    logging.info(f"Отправка сообщения в телеграм: {log}")
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    updater = Updater(bot=bot, use_context=True)
    updater.dispatcher.add_handler(MessageHandler(Filters.text, send_message))
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler('logs.log')
    logger.addHandler(handler)  # проинициализировать бота здесь
    current_timestamp = int(time.time())  # начальное значение timestamp

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(
                    new_homework.get('homeworks')[0]))
            current_timestamp = new_homework.get(
                'current_date', current_timestamp)  # обновить timestamp
            time.sleep(300)  # опрашивать раз в пять минут

        except Exception as e:
            print(f'Бот столкнулся с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
