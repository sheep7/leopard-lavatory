"""Main web blueprint."""

import logging

from flask import Blueprint, flash, render_template, request, url_for
from flask_mail import Mail, Message
from werkzeug.utils import redirect

from leopard_lavatory.storage.database import add_request, get_all_requests
from leopard_lavatory.utils import valid_email, valid_address, log_safe
from leopard_lavatory.celery.tasks import send_confirm_email

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
    try:
        assert valid_address(address), f'Got invalid address: {log_safe(address)}'
        assert valid_email(email), f'Got invalid email: {log_safe(email)}'

        # TODO:  do street/fastighet distinction
        request_token = add_request(email, watchjob_query={'street': address})
        LOG.debug(f'Request stored in database (token: {request_token}).')

        send_confirm_email.apply_async(args=[email, request_token])

        flash(f'Tagit emot bevakningsförfrågan. '
              f'Aktivera den med länken som skickades till {email}.')
    except AssertionError as error:
        LOG.error(str(error))
        flash('Någonting har gått fel, tyvärr.')

    LOG.debug('All requests in database:\n  %s', '\n  '.join([str(r) for r in get_all_requests()]))


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
