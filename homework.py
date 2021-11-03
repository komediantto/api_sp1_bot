import logging
import os
import time
from json import JSONDecodeError

import requests
import telegram
from dotenv import load_dotenv
from telegram import TelegramError

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)

PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
API = 'https://praktiсum.yandex.ru/api/user_api/homework_statuses/'


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    if homework_name is None:
        logging.error(f'В ответе сервера нет имени домашки: {homework_name}')
        return 'В ответе сервера нет имени домашки'
    status = homework.get('status')
    if status is None:
        logging.error(f'В ответе сервера нет статуса домашки: {status}')
        return 'В ответе сервера нет статуса домашки'
    homework_statuses = {
        'rejected': 'К сожалению в работе нашлись ошибки.',
        'reviewing': 'Работа ушла на ревью',
        'approved':
        'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
    }
    verdict = homework_statuses[status]
    try:
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'
    except KeyError:
        logging.exception('Неизвестный статус')
        raise


def get_homework_statuses(current_timestamp):
    params = {'from_date': current_timestamp}
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    try:
        homework_statuses = requests.get(API, params=params, headers=headers)
        return homework_statuses.json()
    except requests.RequestException:
        logging.error('Ошибка при обращении к API')
    except JSONDecodeError:
        logging.info('Ошибка JSON')


def send_message(message, bot_client):
    logging.info('Отправка сообщения пользователю. '
                 f'ID пользователя: {CHAT_ID}.'
                 f'Сообщение: {message}')
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    try:
        bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    except TelegramError as e:
        logging.error(f'Бот не запущен: {e}')
        return
    logging.debug('Бот запущен')
    current_timestamp = int(time.time())
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(
                        new_homework.get('homeworks')[0]
                    ),
                    bot_client
                )
            current_timestamp = new_homework.get(
                'current_date', current_timestamp
            )
            time.sleep(300)

        except Exception as e:
            print(f'Бот столкнулся с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
