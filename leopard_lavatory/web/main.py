"""Main web blueprint."""

import logging
import urllib.parse

from flask import Blueprint, flash, render_template, request, url_for, request
from flask_mail import Mail, Message
from werkzeug.utils import redirect

from leopard_lavatory.storage.database import add_request, get_all_requests, database_session, confirm_request
from leopard_lavatory.utils import valid_email, valid_address, log_safe
from leopard_lavatory.celery.tasks import send_confirm_email

from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm.exc import NoResultFound

LOG = logging.getLogger(__name__)

bp = Blueprint('main', __name__)


def handle_new_request(email, address):
    """Handle new watchjob requests submitted to the website.

    This checks the untrusted user input `email` and `address` and, if valid, creates a
    new database UserRequest record.
    Args:
        email (str): untrusted user input string for the email address
        address (str): untrusted user input string for the address
    """
    LOG.info(f'Received new request for address: {log_safe(address)}, email: {log_safe(email)}')
    with database_session() as dbs:
        try:
            assert valid_address(address), f'Got invalid address: {log_safe(address)}'
            assert valid_email(email), f'Got invalid email: {log_safe(email)}'

            # TODO:  do street/fastighet distinction
            request_token = add_request(dbs, email, watchjob_query={'street': address})
            LOG.debug(f'Request stored in database (token: {request_token}).')

            send_confirm_email.apply_async(args=[email, request_token])

            flash(f'Tagit emot bevakningsförfrågan. '
                  f'Aktivera den med länken som skickades till {email}.')
        except AssertionError as error:
            LOG.error(str(error))
            flash('Någonting har gått fel, tyvärr.')


def handle_confirm_request(token):
    """Handle confirm requests.

    Check whether the token corresponds to a user request, and if yes, create the relevant user and watchjob.
    Args:
        token (str): the given token
    """
    LOG.info(f'Received confirm request with token {log_safe(token)}')

    with database_session() as dbs:
        try:
            # TODO make sure token is valid, ie not empty

            user = confirm_request(dbs, token)
            LOG.debug(f'Created user {user.email}')

            flash('Bevakningsförfrågan aktiverades!', f'Framöver kommer du att få mejl på {user.email} när ärenden om din adress dyker upp.')
        except NoResultFound as err:
            LOG.error(str(err))
            flash('Ogiltigt token')
        # TODO do not reveal that the user already exists
        except IntegrityError as err:
            # most likely adding the user violated the unique constraint
            LOG.error(str(err))
            flash('Användare redan existerar')
        # TODO more error handling

@bp.route('/', methods=('GET', 'POST'))
def index():
    """Render the landing page and handle posted requests.
    Returns:
        Union[str, werkzeug.wrappers.Response]: a rendered template or a werkzeug Response object
    """
    if request.method == 'POST':
        handle_new_request(email=request.form['email'],
                           address=request.form['address'])
        return redirect(url_for('main.index'))

    if request.method == 'GET':
        return render_template('index.html')

@bp.route('/confirm', methods=('GET', 'POST'))
def confirm():
    """Render the confirmation page and confirm user requests (ie create a user).
    Returns:
        Union[str, werkzeug.wrappers.Response]: a rendered template or a werkzeug Response object
    """
    if request.method == 'POST':
        # TODO what if token isn't in form?
        handle_confirm_request(request.form['token'])

        return redirect(url_for('main.index'))

    if request.method == 'GET':
        return render_template('confirm.html', token=request.args.get('t', ''))
