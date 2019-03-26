"""Main web blueprint."""

import logging
import urllib.parse

from flask import Blueprint, flash, render_template, url_for, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.utils import redirect

from leopard_lavatory.celery.tasks import send_confirm_email, send_welcome_email
from leopard_lavatory.storage.database import add_request, database_session, confirm_request, delete_user
from leopard_lavatory.utils import valid_email, valid_address, log_safe

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

            confirm_link = urllib.parse.urljoin(request.url_root, url_for('main.confirm', t=request_token))

            send_confirm_email.apply_async(args=[email, confirm_link, address])

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
            if len(user.watchjobs) == 1:
                # user just created, send them an email
                LOG.debug(f'Created user {user.email}')

                delete_link = urllib.parse.urljoin(request.url_root, url_for('main.delete', t=user.delete_token))

                send_welcome_email.apply_async(args=[user.email, delete_link])
            else:
                LOG.debug('Added watchjob to existing user {user.email}')

            flash('Bevakningsförfrågan aktiverades!',
                  f'Framöver kommer du att få mejl på {user.email} när ärenden om din adress dyker upp.')
        except (NoResultFound, IntegrityError) as err:
            # most likely adding the user violated the unique constraint, or the token was invalid
            LOG.error(str(err))
            flash('Ogiltigt token eller något annat gick fel')


def handle_delete_request(token):
    """Handle delete requsts.

    Check whether the token corresponds to a user account, and if yes, delete the relevant user and all of the associated rows.
    Args:
        token (str): the delete token
    """
    LOG.info(f'Received delete request with token {log_safe(token)}')

    with database_session() as dbs:
        try:
            # TODO make sure token is valid, ie not empty

            user = delete_user(dbs, token)

            flash('Användarkontot raderades!',
                  f'Du kommer inte få mejl om dina bevakningar längre.')
        except (NoResultFound, IntegrityError) as err:
            # most likely adding the user violated the unique constraint, or the token was invalid
            LOG.error(str(err))
            flash('Ogiltigt token eller något annat gick fel')


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
        handle_confirm_request(request.form['token'])

        return redirect(url_for('main.index'))

    if request.method == 'GET':
        return render_template('confirm.html', token=request.args.get('t', ''))


@bp.route('/delete', methods=('GET', 'POST'))
def delete():
    """Render the deletion page and delete users.
    Returns:
        Union[str, werkzeug.wrappers.Response]: a rendered template or a werkzeug Response object
    """
    LOG.debug(request)
    if request.method == 'POST':
        handle_delete_request(request.form['token'])

        return redirect(url_for('main.index'))

    if request.method == 'GET':
        return render_template('delete.html', token=request.args.get('t', ''))
