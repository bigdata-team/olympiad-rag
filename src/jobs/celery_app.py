from celery import Celery

from src.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

celery = Celery(
    "jobs",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

celery.autodiscover_tasks(["src.jobs"])
