from celery import Celery
from myapp.config.config_loader import config_loader  # Import the ConfigLoader instance

# Retrieve the broker URL and result backend from the config
CELERY_BROKER_URL = config_loader.get_celery_broker_url()
CELERY_RESULT_BACKEND = config_loader.get_celery_result_backend()

# Initialize the Celery app using the values from the configuration
app = Celery('myapp',
             broker=CELERY_BROKER_URL,
             backend=CELERY_RESULT_BACKEND,
             include=['myapp.tasks.text_batch_processor', 'myapp.tasks.image_batch_processor'])

app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    app.start()
