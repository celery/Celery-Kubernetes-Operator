from celery import Celery
from flask import Flask


def make_celery(app, celery_config):
    celery = Celery(app.import_name)
    celery.config_from_object(celery_config)
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


flask_app = Flask(__name__)
celery_app = make_celery(flask_app, 'celeryconfig')


@celery_app.task()
def add(a, b):
    return a + b
