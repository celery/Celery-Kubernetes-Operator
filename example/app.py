from celery import Celery
from flask import Flask


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


flask_app = Flask(__name__)
flask_app.config.update(
    CELERY_BROKER_URL='redis://redis-master/1',
    CELERY_RESULT_BACKEND='redis://redis-master/1'
)
celery_app = make_celery(flask_app)


@celery_app.task()
def add(a, b):
    return a + b
