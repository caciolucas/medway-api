import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medway_api.settings")

app = Celery("medway-api")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
