import celery
import os
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration

from ddw import celeryconfig

from ddw import app


SENTRY_DSN = os.environ.get("SENTRY_DSN", None)
if SENTRY_DSN:
    sentry_sdk.init(SENTRY_DSN, integrations=[CeleryIntegration()])

celery_app = celery.Celery("ddw")
celery_app.config_from_object(celeryconfig)


@celery_app.task(name="run_update")
def run_update():
    app.run_update()
