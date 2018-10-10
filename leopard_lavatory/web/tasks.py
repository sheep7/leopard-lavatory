from flask import Flask
from leopard_lavatory.web.celery_factory import make_celery

flask_app = Flask(__name__)
flask_app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = make_celery(flask_app)

@celery.on_after_configure.connect
def setup_periodic_task(sender, **kwargs):
    sender.add_periodic_task(10.0, add_together.s(1, 2), name="Aman")

@celery.task()
def run_watch_job():
    print('Running all watch jobs... (not actually implemented yet)')

    # TODO read jobs from database

    # 
    return a + b
