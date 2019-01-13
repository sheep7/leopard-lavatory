import json
import logging
import os

from celery.schedules import crontab
from flask import Flask
from flask_mail import Mail, Message

from leopard_lavatory.celery.celery_factory import make_celery
from leopard_lavatory.emailer import create_email_bodies
from leopard_lavatory.readers.sthlm_sbk import SBKReader
from leopard_lavatory.storage.database import get_all_watchjobs, get_watchjob, database_session

LOG = logging.getLogger(__name__)

# TODO separate email tasks in separate file
flask_app = Flask(__name__)
flask_app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379',
    MAIL_SERVER=os.environ.get('FLASK_MAIL_SERVER'),
    MAIL_PORT=587,
    MAIL_DEBUG=True,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME=os.environ.get('FLASK_MAIL_USERNAME'),
    MAIL_PASSWORD=os.environ.get('FLASK_MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=os.environ.get('FLASK_MAIL_DEFAULT_SENDER'),
)
celery = make_celery(flask_app)

mail = Mail(flask_app)

mail.debug = True


@celery.on_after_configure.connect
def setup_periodic_task(sender, **kwargs):
    sender.add_periodic_task(
        # run jobs once an hour, every day between 8 in the morning and 8 in the evening
        crontab(hour=list(range(8 - 20)), minute=-0),
        run_all_watchjobs.s(),
        name="Run watchjobs")


@celery.task
def run_all_watchjobs():
    with database_session() as dbs:
        LOG.info('Running all watch jobs...')
        watchjobs = get_all_watchjobs(dbs)
        for watchjob in watchjobs:
            LOG.debug(watchjob)

            (check_watchjob.s(watchjob.id, watchjob.query, watchjob.last_case_id) | notify_users.s(watchjob.id)). \
                apply_async()


@celery.task
def check_watchjob(watchjob_id, query_json, last_case_id):
    with database_session() as dbs:
        reader = SBKReader()

        try:
            query = json.loads(query_json)
        except ValueError:
            # JSON parsing error, just return nothing
            LOG.exception('Error parsing query JSON')
            return []

        if 'street' in query:
            address = query['street']
            newer_than_case = last_case_id

            LOG.debug('Getting all results for address {}, newer than case {}'.format(address, newer_than_case))
            new_cases = reader.get_cases(address, newer_than_case)

            LOG.debug('Found {} results'.format(len(new_cases)))
            # LOG.debug(json.dumps(new_cases, indent=2, ensure_ascii=False))

            if len(new_cases):
                new_last_case_id = new_cases[0]['id']

                watchjob = get_watchjob(dbs, watchjob_id)

                LOG.debug('The new last_case_id is {}, write it to the database'.format(new_last_case_id))

                watchjob.last_case_id = new_last_case_id
            else:
                LOG.debug('No new cases found.')

            return new_cases
        else:
            return []


@celery.task
def notify_users(new_cases, watchjob_id):
    with database_session() as dbs:
        if new_cases:
            LOG.debug('There\'s new cases, get the users for watch job %s and notify them!', watchjob_id)

            watchjob = get_watchjob(dbs, watchjob_id)

            # TODO send actual emails
            LOG.debug('Sending notifications to %s', [user.email for user in watchjob.users])
        else:
            LOG.debug('Nothing to do.')

        return len(new_cases)


@celery.task
def send_confirm_email(email_address, confirm_link):
    text_body, html_body = create_email_bodies('activation', {'button_href': confirm_link})
    msg = Message("Bekräfta bevakning av byggärende", recipients=[os.environ['FLASK_MAIL_RECIPIENT']])
    msg.body = text_body
    msg.html = html_body

    mail.send(msg)
