import celery
import os

from ddw import app


celery_app = celery.Celery(
    "ddw", broker=os.environ["REDIS_URL"], backend=os.environ["REDIS_URL"]
)


@celery_app.task
def run_update():
    app.run_update()
