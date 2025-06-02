from app import create_app
from app.celery_app import celery

app = create_app()
app.app_context().push()

if __name__ == '__main__':
    celery.start() 