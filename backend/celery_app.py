from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery("rulescope", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_routes = {"worker.*": {"queue": "rulescope"}}
celery_app.autodiscover_tasks(["worker"])

if settings.celery_task_always_eager:
    # Local/dev-only: run jobs synchronously in-process, no Redis/worker required.
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    celery_app.conf.broker_url = "memory://"
    celery_app.conf.result_backend = "cache+memory://"
