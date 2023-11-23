import requests
from django.core.management.base import BaseCommand
from telegram import Bot
from urllib.parse import urlencode
from django_app.models import Product
from django_app.serializers import ProductSerializer
import schedule
import time

def send_message():
    # Замените 'YOUR_BOT_TOKEN' на токен вашего бота
    TOKEN = '6803088063:AAFAPtBq7NVjh8z-N9-wBi6V-oSXid0yFWM'

    # Создаем объект бота
    bot = Bot(token=TOKEN)

    # Замените 'YOUR_CHAT_ID' на идентификатор чата с вашим ботом
    chat_id = '968388749'

    new_products = Product.objects.all()
    serializer = ProductSerializer(new_products, many=True)

    message_text = '\n'.join(
        [f"{index + 1}. {item['name']} - {item['price']}" for index, item in enumerate(serializer.data)])

    # Формируем URL для отправки сообщения
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'

    # Параметры запроса
    params = {
        'chat_id': chat_id,
        'text': message_text
    }
    full_url = f'{url}?{urlencode(params)}'

    # Отправляем синхронный запрос
    response = requests.post(full_url)


    print(response.json())


class Command(BaseCommand):
    help = ('Telegram-Bot')

    def handle(self, *args, **options):
        schedule.every().hour.do(send_message)

        # Запускаем бесконечный цикл для выполнения задачи каждый час
        while True:
            schedule.run_pending()
            time.sleep(1)
