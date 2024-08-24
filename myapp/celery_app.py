from celery import Celery
from myapp.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

app = Celery('myapp',
             broker=CELERY_BROKER_URL,
             backend=CELERY_RESULT_BACKEND,
             include=['myapp.tasks'])

app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    app.start()
