from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oscar.settings')

app = Celery('oscar')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Broker settings
app.conf.broker_url = 'amqp://oscar:oscar@localhost:5672/oscarRabbit'

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
