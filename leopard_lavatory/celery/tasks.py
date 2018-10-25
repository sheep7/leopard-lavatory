import json

from flask import Flask
from leopard_lavatory.celery.celery_factory import make_celery
from leopard_lavatory.storage.database import get_all_watchjobs, add_user_watchjob, update_last_case_id
from leopard_lavatory.readers.sthlm_sbk import SBKReader

flask_app = Flask(__name__)
flask_app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = make_celery(flask_app)

@celery.on_after_configure.connect
def setup_periodic_task(sender, **kwargs):
    #sender.add_periodic_task(10.0, print_all_watchjobs.s(), name="print_all_watchjobs")
    #sender.add_periodic_task(15.0, b.s('test@example.com', {'a':'b'}),
    #                         name="add_user_watchjob")
    sender.add_periodic_task(10.0, check_watchjob.s("Brunnsgatan 1", '2008-09960'), name="Check Brunnsgatan 1")

@celery.task()
def print_all_watchjobs():
    print('Running all watch jobs...')
    watchjobs = get_all_watchjobs()
    for watchjob in watchjobs:
        print(watchjob)
        check_watchjob(watchjob)

@celery.task
def check_watchjob(watchjob):
    reader = SBKReader()

    try:
        q = json.loads(watchjob.query)
    except ValueError as e:
        # JSON parsing error, just return nothing
        print('Error parsing JSON: %s' % e)
        return []

    if 'street' in q:
        address = q['street']
        newer_than_case = watchjob.last_case_id

        print('Getting all results for address {}, newer than case {}'.format(address, newer_than_case))
        test_cases = reader.get_cases(address, newer_than_case)

        print('Found {} results'.format(len(test_cases)))
        # print(json.dumps(test_cases, indent=2, ensure_ascii=False))

        if len(test_cases):
            new_last_case_id = test_cases[0]['id']

            print('The new last_case_id is {}, write it to the database'.format(new_last_case_id))

            update_last_case_id(watchjob, new_last_case_id)
        else:
            print('No new cases found.')

        return test_cases
    else:
        return []

@celery.task()
def b(email, query):
    print(f'Add user {email} and watchjob with query {query}')

    add_user_watchjob(email, query)
