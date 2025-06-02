from .make_celery import make_celery
from . import create_app

app = create_app()
celery = make_celery(app)

celery.autodiscover_tasks(['app.tasks'])