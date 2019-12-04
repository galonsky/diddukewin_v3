import os

from celery.schedules import crontab

broker_url = os.environ["REDIS_URL"]
result_backend = os.environ["REDIS_URL"]
redbeat_redis_url = os.environ["REDIS_URL"]

beat_schedule = {
    "run_update": {
        "task": "run_update",
        "schedule": crontab(minute="*/5"),
        "options": {"expires": 60},
    }
}

REDBEAT_REDIS_OPTIONS = {"retry_period": -1}
