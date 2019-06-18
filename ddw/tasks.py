import celery
from ddw import celeryconfig

from ddw import app


celery_app = celery.Celery("ddw")
celery_app.config_from_object(celeryconfig)


@celery_app.task(name="run_update")
def run_update():
    app.run_update()
