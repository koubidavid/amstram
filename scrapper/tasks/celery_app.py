import os

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = Celery("amstram", broker=REDIS_URL, backend=REDIS_URL)
app.config_from_object("tasks.beat_schedule")
app.autodiscover_tasks(["tasks"])
