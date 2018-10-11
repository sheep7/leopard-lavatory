from flask import Flask
from leopard_lavatory.web.celery_factory import make_celery
from leopard_lavatory.storage.database import get_all_watchjobs, add_user_watchjob

flask_app = Flask(__name__)
flask_app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = make_celery(flask_app)

@celery.on_after_configure.connect
def setup_periodic_task(sender, **kwargs):
    sender.add_periodic_task(10.0, print_all_watchjobs.s(), name="print_all_watchjobs")
    sender.add_periodic_task(15.0, b.s('test@example.com', {'a':'b'}),
                             name="add_user_watchjob")

@celery.task()
def print_all_watchjobs():
    print('Running all watch jobs... (not actually implemented yet)')
    watchjobs = get_all_watchjobs()
    for watchjob in watchjobs:
        print(watchjob)

@celery.task()
def b(email, query):
    print(f'Add user {email} and watchjob with query {query}')

    add_user_watchjob(email, query)
