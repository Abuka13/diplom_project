import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_settings.settings')
app = Celery('django_settings')
app.config_from_object('django.conf:settings', namespace='CELERY')  # CELERY_Name
app.conf.beat_schedule = {
    'schedule_generate_and_email_pdf': {
        'task': 'path.to.generate_and_email_pdf',
        'schedule': crontab(hour=0, minute=0),
    },
}
app.conf.timezone = 'UTC'
app.autodiscover_tasks()