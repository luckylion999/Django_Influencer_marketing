from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shoutourbiz.prod_settings')

broker_url = 'redis://{}:{}/{}'.format(settings.REDIS_HOST, settings.REDIS_PORT,
                                       settings.REDIS_DB)
app = Celery('shoutourbiz', broker=broker_url)

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()