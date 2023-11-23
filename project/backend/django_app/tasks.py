import time

from celery import shared_task
import celery
from celery import shared_task
from django.core.mail import EmailMessage
from reportlab.pdfgen import canvas
from io import BytesIO
from .models import Product

from celery.schedules import crontab
from .serializers import ProductSerializer

@shared_task
def generate_and_email_pdf():
    # Получение списка всех товаров с использованием DRF сериализатора
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    data = serializer.data

    # Создание PDF-документа
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 100, "Список товаров:")

    y_position = 80
    for product_data in data:
        y_position -= 15
        product_info = ", ".join(f"{key}: {value}" for key, value in product_data.items())
        p.drawString(100, y_position, product_info)

    p.showPage()
    p.save()

    # Отправка PDF по почте
    subject = 'Список товаров'
    message = 'Ваш список товаров в виде PDF-документа.'
    email = EmailMessage(subject, message, 'abukaozbekbay@gmail.com', ['akezhanabuka@gmail.com'])
    email.attach('product_list.pdf', buffer.getvalue(), 'application/pdf')
    email.send()

@shared_task
def schedule_generate_and_email_pdf():
    generate_and_email_pdf()
