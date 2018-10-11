from flask import Blueprint, flash, render_template, request, url_for
from werkzeug.utils import redirect

from leopard_lavatory.storage.database import add_request, get_all_requests

bp = Blueprint('home', __name__)


@bp.route('/', methods=('GET', 'POST'))
def home():
    if request.method == 'POST':
        address = request.form['address']
        email = request.form['email']
        # TODO: filter for invalid characters on both inputs and do street/fastighet distinction
        add_request(email, watchjob_query={'street': address})
        flash(f'Tagit emot bevakningsförfrågan. Aktivera den med länken som skickades till '
              f'{email}.')
        print('All requests in database:')
        for user_request in get_all_requests():
            print(user_request)
        return redirect(url_for('home.home'))

    if request.method == 'GET':
        return render_template('index.html')
